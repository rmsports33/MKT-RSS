"""Fluxo supervisionado gratuito: candidato licenciado -> WP draft.

Não publica, não cria artigo, não altera conteúdo ou aprovação editorial.
Não usa imagens RSS, IA ou links genéricos. Sem confirmação humana de direitos e
de adequação visual, não faz solicitações autenticadas nem baixa mídia.
"""
import io
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
                "revisao_direitos", "revisao_visual", "alt_text"}
    if not isinstance(foto, dict) or not required.issubset(foto):
        raise ValueError("ficha de mídia incompleta")
    if (not _https_host(foto["url"], "images.unsplash.com", "/photo-")
            or not _https_host(foto["pagina_origem"], "unsplash.com", "/photos/")
            or foto["licenca_url"] != ORIGEM_LICENCA
            or not isinstance(foto["autor"], str) or not foto["autor"].strip()
            or not isinstance(foto["alt_text"], str) or not foto["alt_text"].strip()
            or foto["revisao_direitos"] != "APROVADO_PELO_EDITOR"
            or foto["revisao_visual"] != "APROVADO_PELO_EDITOR"):
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
            not _https_host(wp_url.rstrip("/"), "conexotech.com.br") or
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
        if post.get("status") != "draft" or post.get("id") != post_id:
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
                recheck.json().get("featured_media") not in (None, 0)):
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
        if upload.status_code != 201 or type(upload.json().get("id")) is not int:
            return {"status": "INSPECIONAR", "motivo": "upload_wp_indeterminado",
                    "escreveu": False, "retry_automatico": False}
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
        return {"status": "INSPECIONAR", "motivo": "transporte_indeterminado",
                "escreveu": False, "retry_automatico": False}
