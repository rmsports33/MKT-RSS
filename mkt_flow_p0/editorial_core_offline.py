"""Conexo editorial core: importacao segura, SEO e HTML offline, sem API nem WP."""
import argparse
import hashlib
import html
import json
import re
from pathlib import Path
from urllib.parse import urlparse

from mkt_flow_p0.format import markdown_para_html
from mkt_flow_p0.seo import validar_artigo_wordpress
from mkt_flow_p0.seo_contract_native import contrato_seo_nativo
from mkt_flow_p0.adaptador_contrato_editorial import normalizar_snapshot_editorial, avaliar_snapshot_editorial

MAX_BYTES = 1024 * 1024
VALID_STATES = {"aguardando_revisao", "revisado"}
REQUIRED = ("schema_version", "article_id", "status", "title", "seo", "sources", "claims", "review")


def _safe_url(value):
    if not isinstance(value, str) or any(ord(c) < 32 for c in value):
        return False
    u = urlparse(value)
    try:
        return (u.scheme == "https" and bool(u.hostname) and not u.username and not u.password
                and not any(c.isspace() for c in value) and u.port in (None, 443)
                and not u.hostname.endswith(".") and "." in u.hostname)
    except ValueError:
        return False


def _safe_slug(value):
    return isinstance(value, str) and bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value))


def _string(value):
    return isinstance(value, str) and bool(value.strip())


def _escape_links(markdown):
    """Rejeita links potencialmente ativos antes de delegar ao renderizador legado."""
    # O conversor legado escapa o texto HTML; para a pre-visualizacao,
    # recusar qualquer HTML bruto evita ambiguidades e usos indevidos.
    if re.search(r"<\s*/?\s*[a-z][^>]*>", markdown, re.I):
        raise ValueError("HTML bruto nao permitido")
    for url in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", markdown):
        if not _safe_url(url):
            raise ValueError("Link Markdown deve usar HTTPS valido")
    if re.search(r"(?i)\b(?:javascript|data|vbscript)\s*:", markdown):
        raise ValueError("Esquema perigoso no artigo")


def validar_pacote(article, markdown):
    erros = []
    if not isinstance(article, dict):
        return ["Metadados devem ser objeto JSON"]
    for key in REQUIRED:
        if key not in article:
            erros.append("Campo ausente: " + key)
    if article.get("schema_version") != "1.0":
        erros.append("Versao incompatível")
    if not _string(article.get("article_id")) or not re.fullmatch(r"[a-zA-Z0-9_-]{3,64}", article.get("article_id") or ""):
        erros.append("ID invalido")
    if article.get("status") not in VALID_STATES:
        erros.append("Estado editorial invalido")
    if not _string(article.get("title")):
        erros.append("Titulo ausente")
    seo = article.get("seo")
    if not isinstance(seo, dict):
        erros.append("SEO invalido")
    else:
        if not _string(seo.get("title")) or not _string(seo.get("description")):
            erros.append("Titulo ou descricao SEO ausente")
        if not _safe_slug(seo.get("slug")):
            erros.append("Slug invalido")
    sources = article.get("sources")
    if not isinstance(sources, list) or not sources or any(not isinstance(s, dict) or not _safe_url(s.get("url")) for s in sources):
        erros.append("Fontes HTTPS obrigatorias")
    if not isinstance(article.get("claims"), list):
        erros.append("Claims invalidas")
    contract = article.get("contrato_editorial")
    if contract is not None and normalizar_snapshot_editorial(contract) is None:
        erros.append("Contrato editorial canonico invalido")
    review = article.get("review")
    if not isinstance(review, dict) or review.get("approved") is not False:
        erros.append("Pacote de pre-visualizacao exige approved=false")
    if not isinstance(markdown, str) or len(markdown.split()) < 100:
        erros.append("Texto editorial insuficiente")
    related = article.get("related_articles", [])
    if not isinstance(related, list) or len(related) > 3 or any(not isinstance(r, dict) or not _safe_url(r.get("url")) for r in related):
        erros.append("Links relacionados invalidos")
    try:
        _escape_links(markdown)
    except ValueError as exc:
        erros.append(str(exc))
    return erros


def _renderizar_markdown_editorial(markdown):
    """Renderiza tabelas Markdown com escape de HTML, preservando a ordem dos blocos."""
    out, buffer, lines = [], [], markdown.splitlines()

    def flush():
        if buffer:
            out.append(markdown_para_html("\n".join(buffer)))
            buffer.clear()

    i = 0
    while i < len(lines):
        if (i + 1 < len(lines) and lines[i].strip().startswith("|")
                and re.fullmatch(r"[|:\-\s]+", lines[i + 1].strip() or "x")):
            header = [x.strip() for x in lines[i].strip().strip("|").split("|")]
            divider = [x.strip() for x in lines[i + 1].strip().strip("|").split("|")]
            if (len(header) > 1 and len(header) == len(divider)
                    and all(re.fullmatch(r":?-{3,}:?", x) for x in divider)):
                flush()
                out.append("<table><thead><tr>" + "".join(
                    "<th>" + html.escape(x) + "</th>" for x in header
                ) + "</tr></thead><tbody>")
                i += 2
                while i < len(lines) and lines[i].strip().startswith("|"):
                    cells = [x.strip() for x in lines[i].strip().strip("|").split("|")]
                    if len(cells) != len(header):
                        raise ValueError("Tabela Markdown com colunas inconsistentes")
                    out.append("<tr>" + "".join(
                        "<td>" + html.escape(x) + "</td>" for x in cells
                    ) + "</tr>")
                    i += 1
                out.append("</tbody></table>")
                continue
        buffer.append(lines[i])
        i += 1
    flush()
    return "\n".join(out)


def gerar_corpo_wordpress(article, markdown):
    """Fragmento editorial sem <head>, <h1> duplicado ou noindex de pre-visualizacao.

    Somente gera HTML; nao autoriza escrita e nao confere fatos automaticamente.
    """
    erros = validar_pacote(article, markdown)
    if erros:
        raise ValueError("; ".join(erros))
    body = _renderizar_markdown_editorial(markdown)
    fontes = "\n".join(
        '<li><a rel="noopener noreferrer" href="' + html.escape(s["url"], quote=True) +
        '">' + html.escape(s.get("name") or s["url"]) + '</a></li>' for s in article["sources"]
    )
    related = "\n".join(
        '<li><a rel="noopener noreferrer" href="' + html.escape(r["url"], quote=True) +
        '">' + html.escape(r.get("title") or r["url"]) + '</a></li>' for r in article.get("related_articles", [])
    )
    items = [body, "<h2>Fontes</h2><ul>" + fontes + "</ul>"]
    if related:
        items.append("<h2>Leia também</h2><ul>" + related + "</ul>")
    return "\n".join(items)


def gerar_html(article, markdown):
    """Documento completo SOMENTE para pre-visualizacao offline, sempre noindex."""
    fragmento = gerar_corpo_wordpress(article, markdown)
    seo = article["seo"]
    return "\n".join([
        "<!doctype html>",
        '<html lang="pt-BR"><head><meta charset="utf-8">',
        '<meta name="robots" content="noindex,nofollow">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        "<title>" + html.escape(seo["title"]) + "</title>",
        '<meta name="description" content="' + html.escape(seo["description"], quote=True) + '">',
        "</head><body><main><article>",
        "<h1>" + html.escape(article["title"]) + "</h1>",
        fragmento,
        "</article></main></body></html>",
    ])


def processar(metadata_file, markdown_file, output_dir):
    metadata_file, markdown_file = Path(metadata_file), Path(markdown_file)
    if metadata_file.stat().st_size > MAX_BYTES or markdown_file.stat().st_size > MAX_BYTES:
        raise ValueError("Arquivo muito grande")
    article = json.loads(metadata_file.read_text(encoding="utf-8"))
    markdown = markdown_file.read_text(encoding="utf-8")
    rendered = gerar_html(article, markdown)
    wordpress_body = gerar_corpo_wordpress(article, markdown)
    seo_preflight = validar_artigo_wordpress(article["title"], wordpress_body,
                                           tem_capa=bool(article.get("featured_image")))
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    path = output / (article["seo"]["slug"] + ".html")
    path.write_text(rendered, encoding="utf-8")
    body_path = output / (article["seo"]["slug"] + ".wordpress-body.html")
    body_path.write_text(wordpress_body, encoding="utf-8")
    snapshot = article.get("contrato_editorial")
    contract_check = (avaliar_snapshot_editorial(snapshot) if snapshot is not None
                      else {"veredito": "BLOQUEADO", "motivos": ["contrato_editorial_ausente"]})
    # Vinculo consultivo, nao certificado: aponta exatamente quais claims do
    # pacote possuem IDs de fonte rastreaveis no snapshot canonico.
    fontes_can = {x.get("id"): x for x in (snapshot or {}).get("sources", [])
                   if isinstance(x, dict) and isinstance(x.get("id"), str)}
    rastreio = []
    for claim in article.get("claims", []):
        if not isinstance(claim, dict):
            rastreio.append({"claim_id": None, "status": "PENDENTE", "motivo": "claim_invalida"})
            continue
        refs = claim.get("evidence_ids")
        refs = refs if isinstance(refs, list) else []
        validas = [i for i in refs if isinstance(i, str) and i in fontes_can]
        urls = claim.get("source_urls")
        urls = urls if isinstance(urls, list) else []
        fontes_pacote = {f["url"] for f in article["sources"]}
        urls_validas = [u for u in urls if isinstance(u, str) and u in fontes_pacote]
        texto = claim.get("text") or claim.get("texto") or ""
        texto_plano = re.sub(r"!?\[([^\]]+)\]\(https://[^)]+\)", r"\1", markdown)
        no_corpo = bool(isinstance(texto, str) and texto.strip() and texto.strip() in texto_plano)
        rastreio.append({"claim_id": claim.get("id"), "status": "PENDENTE_REVISAO",
                         "evidence_ids": validas, "source_urls": urls_validas,
                         "texto_localizado": no_corpo,
                         "vinculo_completo": bool(validas and no_corpo and len(validas) == len(refs)),
                         "evidencia_aprovada": False})
    fontes_sem_vinculo = [i for i in range(len(article["sources"]))
                         if not any(article["sources"][i]["url"] == src.get("url")
                                    for src in fontes_can.values())]
    manifest = {"article_id": article["article_id"], "status": "aguardando_revisao",
                "aprovacao_publicacao": False, "contrato_editorial": contract_check,
                "rastreabilidade_claims": rastreio,
                "fontes_sem_vinculo_canonico": fontes_sem_vinculo,
                "revisao_factual_humana_pendente": True,
                "html": str(path), "wordpress_body": str(body_path),
                "wordpress_written": False, "factual_review": "NAO_VERIFICADO",
                "seo_preflight": seo_preflight,
                "seo_native_contract": contrato_seo_nativo(article),
                "content_sha256": hashlib.sha256((json.dumps(article, sort_keys=True, ensure_ascii=False) + "\\n" + markdown).encode("utf-8")).hexdigest(),
                "seo": article["seo"], "source_count": len(article["sources"])}
    (output / (article["seo"]["slug"] + ".report.json")).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main():
    p = argparse.ArgumentParser(description="Renderizador editorial offline, sem WordPress")
    p.add_argument("--metadata", required=True)
    p.add_argument("--markdown", required=True)
    p.add_argument("--output-dir", required=True)
    args = p.parse_args()
    print(json.dumps(processar(args.metadata, args.markdown, args.output_dir), ensure_ascii=False))


if __name__ == "__main__":
    main()
