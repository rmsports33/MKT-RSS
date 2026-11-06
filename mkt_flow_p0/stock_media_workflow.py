"""Fluxo supervisionado gratuito: candidato licenciado -> WP draft.

Não publica, não cria artigo, não altera conteúdo ou aprovação editorial.
Não usa imagens RSS, IA ou links genéricos. Sem confirmação humana de direitos e
de adequação visual, não faz solicitações autenticadas nem baixa mídia.
"""
import io
import re
from urllib.parse import urlsplit

import requests

from mkt_flow_p0.image_handler import processar_capa, MAX_BYTES
from mkt_flow_p0.wp_publisher import _auth_header

ORIGEM_LICENCA = "https://unsplash.com/license"


def _https_host(url, host, path_prefix="/"):
    if not isinstance(url, str) or len(url) > 2048 or any(c.isspace() for c in url):
        return False
    try:
        parts = urlsplit(url)
        return (parts.scheme == "https" and parts.hostname == host and
                parts.port in (None, 443) and not parts.username and
                not parts.password and not parts.fragment and
                parts.path.startswith(path_prefix))
    except ValueError:
        return False


def validar_escolha(foto):
    """Ficha auditável: não equipara metadados da API à autorização de uso."""
    required = {"url", "pagina_origem", "autor", "licenca_url",
                "revisao_direitos", "revisao_visual", "alt_text",
                "approved_post_id", "approved_post_modified_gmt"}
    if not isinstance(foto, dict) or not required.issubset(foto):
        raise ValueError("ficha de mídia incompleta")
    if (not _https_host(foto["url"], "images.unsplash.com", "/photo-")
            or not _https_host(foto["pagina_origem"], "unsplash.com", "/photos/")
            or foto["licenca_url"] != ORIGEM_LICENCA
            or not isinstance(foto["autor"], str) or not foto["autor"].strip()
            or not isinstance(foto["alt_text"], str) or not foto["alt_text"].strip()
            or foto["revisao_direitos"] != "APROVADO_PELO_EDITOR"
            or foto["revisao_visual"] != "APROVADO_PELO_EDITOR"
            or type(foto["approved_post_id"]) is not int
            or foto["approved_post_id"] <= 0
            or not isinstance(foto["approved_post_modified_gmt"], str)
            or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", foto["approved_post_modified_gmt"])):
        raise ValueError("direitos/visual não aprovados ou URL insegura")
    return True


def associar_foto_gratuita_a_rascunho(foto, *, post_id, wp_url, wp_user,
                                     wp_app_password, request_client=requests,
                                     timeout=15):
    """Escreve só a imagem destacada de um draft existente, após aprovação.

    A resposta de transporte indeterminado impede retry automático porque o
    upload talvez tenha ocorrido. Não cria novo post nem promove publicação.
    """
    try:
        validar_escolha(foto)
    except (ValueError, TypeError) as exc:
        return {"status": "BLOQUEADO", "motivo": str(exc), "escreveu": False}
    if (type(post_id) is not int or post_id <= 0 or
            foto["approved_post_id"] != post_id or
            not _https_host(wp_url.rstrip("/"), "conexotech.com.br", "") or
            not wp_user or not wp_app_password):
        return {"status": "BLOQUEADO", "motivo": "destino ou credenciais inválidos",
                "escreveu": False}
    api = "https://conexotech.com.br/wp-json/wp/v2"
    auth = {"Authorization": _auth_header(wp_user, wp_app_password)}
    try:
        before = request_client.get(api + "/posts/" + str(post_id),
                                    headers=auth, params={"context": "edit"},
                                    timeout=timeout, allow_redirects=False)
        if before.status_code != 200:
            return {"status": "BLOQUEADO", "motivo": "preflight_wp_inacessivel",
                    "escreveu": False}
        post = before.json()
        if (post.get("status") != "draft" or post.get("id") != post_id
                or post.get("modified_gmt") != foto["approved_post_modified_gmt"]):
            return {"status": "BLOQUEADO", "motivo": "post_nao_e_draft",
                    "escreveu": False}
        if isinstance(post.get("featured_media"), int) and post["featured_media"] > 0:
            return {"status": "BLOQUEADO", "motivo": "post_ja_possui_imagem",
                    "media_id": post["featured_media"], "escreveu": False}
        # Só imagens.unsplash.com; proíbe redirecionamentos e mídia arbitrária.
        downloaded = request_client.get(foto["url"], timeout=timeout,
                                        stream=True, allow_redirects=False)
        if downloaded.status_code != 200 or not (
                downloaded.headers.get("Content-Type", "").split(";")[0].strip().lower()
                in ("image/jpeg", "image/png", "image/webp")):
            return {"status": "BLOQUEADO", "motivo": "imagem_invalida",
                    "escreveu": False}
        data = io.BytesIO()
        for chunk in downloaded.iter_content(64 * 1024):
            data.write(chunk)
            if data.tell() > MAX_BYTES:
                return {"status": "BLOQUEADO", "motivo": "imagem_maior_que_8mb",
                        "escreveu": False}
        capa = processar_capa(data.getvalue())
        if "bytes" not in capa:
            return {"status": "BLOQUEADO", "motivo": "imagem_nao_processavel",
                    "escreveu": False}
        # Última conferência do status imediatamente antes do primeiro write.
        recheck = request_client.get(api + "/posts/" + str(post_id),
                                     headers=auth, params={"context": "edit"},
                                     timeout=timeout, allow_redirects=False)
        if (recheck.status_code != 200 or
                recheck.json().get("status") != "draft" or
                recheck.json().get("featured_media") not in (None, 0) or
                recheck.json().get("modified_gmt") != foto["approved_post_modified_gmt"]):
            return {"status": "BLOQUEADO", "motivo": "estado_do_draft_mudou",
                    "escreveu": False}
        caption = "Foto: " + foto["autor"].strip() + " / Unsplash"
        description = ("Origem: " + foto["pagina_origem"] +
                       " | Licença: " + ORIGEM_LICENCA +
                       " | Uso editorial aprovado pelo editor; imagem ilustrativa.")
        upload = request_client.post(
            api + "/media",
            headers={**auth, "Content-Disposition":
                     'attachment; filename="conexotech-unsplash-cover.jpg"',
                     "Content-Type": "image/jpeg"},
            data=capa["bytes"], timeout=timeout, allow_redirects=False)
        if (upload.status_code != 201 or
                type(upload.json().get("id")) is not int or
                upload.json()["id"] <= 0):
            return {"status": "INSPECIONAR", "motivo": "upload_wp_indeterminado",
                    "escrita_indeterminada": True, "retry_automatico": False}
        media_id = upload.json()["id"]
        metadata = request_client.post(
            api + "/media/" + str(media_id), headers=auth,
            json={"alt_text": foto["alt_text"],
                  "caption": caption, "description": description},
            timeout=timeout, allow_redirects=False)
        if metadata.status_code != 200:
            return {"status": "INSPECIONAR", "motivo": "metadados_nao_confirmados",
                    "media_id": media_id, "escreveu": True,
                    "retry_automatico": False}
        media_readback = request_client.get(
            api + "/media/" + str(media_id), headers=auth,
            params={"context": "edit"}, timeout=timeout, allow_redirects=False)
        if media_readback.status_code != 200:
            return {"status": "INSPECIONAR", "motivo": "media_readback_inacessivel",
                    "media_id": media_id, "escreveu": True, "retry_automatico": False}
        media = media_readback.json()
        raw_caption = media.get("caption", {})
        raw_description = media.get("description", {})
        if isinstance(raw_caption, dict):
            raw_caption = raw_caption.get("raw", "")
        if isinstance(raw_description, dict):
            raw_description = raw_description.get("raw", "")
        if (media.get("id") != media_id or media.get("alt_text") != foto["alt_text"]
                or caption not in str(raw_caption)
                or foto["pagina_origem"] not in str(raw_description)
                or ORIGEM_LICENCA not in str(raw_description)):
            return {"status": "INSPECIONAR", "motivo": "media_metadados_divergentes",
                    "media_id": media_id, "escreveu": True, "retry_automatico": False}
        last_check = request_client.get(
            api + "/posts/" + str(post_id), headers=auth,
            params={"context": "edit"}, timeout=timeout, allow_redirects=False)
        if (last_check.status_code != 200 or
                last_check.json().get("status") != "draft" or
                last_check.json().get("featured_media") not in (None, 0) or
                last_check.json().get("modified_gmt") != foto["approved_post_modified_gmt"]):
            return {"status": "INSPECIONAR",
                    "motivo": "concorrencia_antes_da_associacao",
                    "media_id": media_id, "escreveu": True,
                    "retry_automatico": False}
        attached = request_client.post(
            api + "/posts/" + str(post_id), headers=auth,
            json={"featured_media": media_id}, timeout=timeout,
            allow_redirects=False)
        if attached.status_code != 200:
            return {"status": "INSPECIONAR", "motivo": "associacao_indeterminada",
                    "media_id": media_id, "escreveu": True,
                    "retry_automatico": False}
        readback = request_client.get(
            api + "/posts/" + str(post_id), headers=auth,
            params={"context": "edit"}, timeout=timeout, allow_redirects=False)
        if (readback.status_code != 200 or
                readback.json().get("status") != "draft" or
                readback.json().get("featured_media") != media_id):
            return {"status": "INSPECIONAR", "motivo": "readback_divergente",
                    "media_id": media_id, "escreveu": True,
                    "retry_automatico": False}
        return {"status": "CAPA_ASSOCIADA_A_DRAFT", "post_id": post_id,
                "media_id": media_id, "escreveu": True,
                "credito": caption, "licenca_url": ORIGEM_LICENCA,
                "origem_url": foto["pagina_origem"], "retry_automatico": False}
    except (requests.RequestException, ValueError, TypeError, KeyError):
        # A falha pode ocorrer depois de upload ou vínculo: nunca retry cego.
        return {"status": "INSPECIONAR", "motivo": "transporte_indeterminado",
                "escrita_indeterminada": True, "retry_automatico": False}

def main(argv=None):
    """CLI manual com arquivo de aprovação e confirmação específica do post."""
    import argparse
    import json
    import os
    from pathlib import Path
    parser = argparse.ArgumentParser(description="Associar foto gratuita APROVADA a draft WordPress")
    parser.add_argument("--approved-photo-json", type=Path, required=True)
    parser.add_argument("--post-id", type=int, required=True)
    parser.add_argument("--confirm-draft-media", action="store_true", required=True)
    args = parser.parse_args(argv)
    photo = json.loads(args.approved_photo_json.read_text(encoding="utf-8"))
    result = associar_foto_gratuita_a_rascunho(
        photo, post_id=args.post_id, wp_url=os.getenv("WP_URL", ""),
        wp_user=os.getenv("WP_USER", ""),
        wp_app_password=os.getenv("WP_APP_PASSWORD", ""))
    # A resposta nunca contém credenciais nem bytes da imagem.
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result.get("status") == "CAPA_ASSOCIADA_A_DRAFT" else 2


if __name__ == "__main__":
    raise SystemExit(main())
