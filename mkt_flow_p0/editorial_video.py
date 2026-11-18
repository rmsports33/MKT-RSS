"""Bloco de review em vídeo — portado do gerador legado para o motor MKT-RSS.

Regras (docs/site/politica-curadoria-video.md):
- só ID do YouTube de 11 caracteres;
- título e canal reais, nunca inventados;
- player oficial youtube-nocookie, crédito visível e link direto;
- o vídeo é SEÇÃO do artigo, nunca o artigo inteiro;
- sem dados válidos, nada é inserido.

Nenhuma chamada de rede e nenhuma escolha automática de vídeo: a curadoria é
humana. A chave YOUTUBE_API_KEY, quando usada, fica só no ambiente.
"""
import html
import json
import re

ID_YOUTUBE = re.compile(r"^[A-Za-z0-9_-]{11}$")
OBRIGATORIOS = ("youtube_id", "youtube_titulo", "youtube_canal")
OPCIONAIS = ("youtube_resumo", "youtube_pontos", "youtube_duracao",
             "youtube_uploadDate", "youtube_duracao_iso")


def extrair_video(payload):
    """Lê `video` do payload canônico; aceita também youtube_* na raiz."""
    dados = payload.get("video") if isinstance(payload, dict) else None
    if not isinstance(dados, dict):
        dados = {k: v for k, v in (payload or {}).items()
                 if k in OBRIGATORIOS + OPCIONAIS}
    if not all(isinstance(dados.get(k), str) and dados[k].strip()
               for k in OBRIGATORIOS):
        return None
    vid = dados["youtube_id"].strip()
    if not ID_YOUTUBE.match(vid):
        return None
    video = {"youtube_id": vid,
             "titulo": dados["youtube_titulo"].strip(),
             "canal": dados["youtube_canal"].strip()}
    for chave in OPCIONAIS:
        valor = dados.get(chave)
        if chave == "youtube_pontos":
            if isinstance(valor, list) and valor:
                video["pontos"] = [str(x).strip() for x in valor[:4]
                                   if str(x).strip()]
        elif isinstance(valor, str) and valor.strip():
            video[chave[8:]] = valor.strip()
    return video


def bloco_video(video):
    vid = video["youtube_id"]
    titulo = html.escape(video["titulo"], quote=True)
    canal = html.escape(video["canal"])
    partes = [
        '<section class="cx-video-review">',
        '<h2>O que dizem os reviews em vídeo</h2>',
        f'<iframe src="https://www.youtube-nocookie.com/embed/{vid}?rel=0" '
        f'title="{titulo}" loading="lazy" allowfullscreen '
        'allow="accelerometer; autoplay; clipboard-write; encrypted-media; '
        'gyroscope; picture-in-picture"></iframe>',
        f'<p><strong>Canal:</strong> {canal}</p>',
    ]
    if video.get("resumo"):
        partes.append("<p>" + html.escape(video["resumo"]) + "</p>")
    if video.get("pontos"):
        partes.append("<ul>" + "".join("<li>" + html.escape(p) + "</li>"
                                       for p in video["pontos"]) + "</ul>")
    partes.append(
        f'<p class="cx-video-credito">Crédito: {canal} · '
        f'<a href="https://www.youtube.com/watch?v={vid}" rel="noopener" '
        'target="_blank">Assistir no YouTube</a></p>')
    partes.append("</section>")
    return "\n".join(partes)


def videoobject_jsonld(video):
    dados = {
        "@context": "https://schema.org",
        "@type": "VideoObject",
        "name": video["titulo"],
        "description": video.get("resumo") or video["titulo"],
        "thumbnailUrl": f"https://i.ytimg.com/vi/{video['youtube_id']}/hqdefault.jpg",
        "uploadDate": video.get("uploadDate") or "",
        "duration": video.get("duracao_iso") or "",
        "embedUrl": f"https://www.youtube-nocookie.com/embed/{video['youtube_id']}",
    }
    dados = {k: v for k, v in dados.items() if v}
    return '<script type="application/ld+json">' + json.dumps(
        dados, ensure_ascii=False) + "</script>"
