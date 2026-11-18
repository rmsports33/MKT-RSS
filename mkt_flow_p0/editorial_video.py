"""Bloco de review em video — portado do gerador legado para o motor MKT-RSS.

Regras (docs/site/politica-curadoria-video.md):
- so ID do YouTube de 11 caracteres;
- titulo e canal reais, nunca inventados;
- player oficial youtube-nocookie, credito visivel e link direto;
- o video e SECAO do artigo, nunca o artigo inteiro;
- sem dados validos, nada e inserido.

Aceita os dois formatos que o fluxo realmente produz:
- a ficha canonica com campos `youtube_*` (redator-artigo-blogs);
- o dict curto ja convertido: `youtube_id`, `titulo`, `canal`, `resumo`,
  `pontos`, `duracao`, `uploadDate`, `duracao_iso`.
Campos desconhecidos sao rejeitados: nada e inventado nem descartado em silencio.

Nenhuma chamada de rede e nenhuma escolha automatica de video: a curadoria e
humana. A chave YOUTUBE_API_KEY, quando usada, fica so no ambiente.
"""
import html
import json
import re

ID_YOUTUBE = re.compile(r"^[A-Za-z0-9_-]{11}$")
DURACAO_TEXTO = re.compile(r"^(?:(\d{1,2}):)?(\d{1,2}):(\d{2})$")
DURACAO_ISO = re.compile(
    r"^P(?!$)(?:\d+Y)?(?:\d+M)?(?:\d+D)?"
    r"(?:T(?=\d)(?:\d+H)?(?:\d+M)?(?:\d+S)?)?$")

# Formato interno (curto), identico ao produzido pelo gerador legado.
OBRIGATORIOS = ("youtube_id", "titulo", "canal")
OPCIONAIS = ("resumo", "pontos", "duracao", "uploadDate", "duracao_iso")
CAMPOS_VIDEO = OBRIGATORIOS + OPCIONAIS

# Ficha canonica (youtube_*) -> chave interna.
CAMPOS_FICHA = {
    "youtube_id": "youtube_id",
    "youtube_titulo": "titulo",
    "youtube_canal": "canal",
    "youtube_resumo": "resumo",
    "youtube_pontos": "pontos",
    "youtube_duracao": "duracao",
    "youtube_uploadDate": "uploadDate",
    "youtube_duracao_iso": "duracao_iso",
}


def duracao_para_iso(valor):
    """Converte '8:32'/'1:02:03' em 'PT8M32S'/'PT1H2M3S'.

    Duracao ISO 8601 ja valida passa direto. Texto irreconhecivel devolve ""
    (a duracao textual continua preservada no bloco visivel).
    """
    if not isinstance(valor, str):
        return ""
    texto = valor.strip()
    if not texto:
        return ""
    if DURACAO_ISO.fullmatch(texto):
        return texto
    achado = DURACAO_TEXTO.fullmatch(texto)
    if not achado:
        return ""
    horas, minutos, segundos = achado.groups()
    h = int(horas) if horas else 0
    m = int(minutos)
    s = int(segundos)
    if not horas and (m >= 60 or s >= 60):
        return ""
    if horas and (m >= 60 or s >= 60):
        return ""
    partes = "PT"
    if h:
        partes += str(h) + "H"
    if m:
        partes += str(m) + "M"
    if s or not (h or m):
        partes += str(s) + "S"
    return partes


def _candidato(fonte):
    """Escolhe a origem do video e recusa campos `youtube_*` desconhecidos."""
    if not isinstance(fonte, dict):
        return None
    video = fonte.get("video")
    if isinstance(video, dict):
        return video
    for chave in ("article", "metadata"):
        artigo = fonte.get(chave)
        if not isinstance(artigo, dict):
            continue
        _rejeitar_youtube_desconhecido(artigo)
        if any(k in artigo for k in CAMPOS_FICHA):
            return {k: artigo[k] for k in CAMPOS_FICHA if k in artigo}
    _rejeitar_youtube_desconhecido(fonte)
    if any(k in fonte for k in CAMPOS_FICHA):
        return {k: fonte[k] for k in CAMPOS_FICHA if k in fonte}
    return None


def _rejeitar_youtube_desconhecido(dados):
    estranhos = sorted(k for k in dados
                       if isinstance(k, str) and k.startswith("youtube_")
                       and k not in CAMPOS_FICHA)
    if estranhos:
        raise ValueError("campo youtube_ desconhecido: " + ", ".join(estranhos))


def _normalizar(dados):
    """Converte ficha `youtube_*` ou dict curto para o formato interno."""
    if any(k in dados for k in CAMPOS_FICHA if k != "youtube_id"):
        mistos = sorted(k for k in dados
                        if k in CAMPOS_VIDEO and k not in CAMPOS_FICHA)
        if mistos:
            raise ValueError("nao misture youtube_* com campos curtos: "
                             + ", ".join(mistos))
        return {CAMPOS_FICHA[k]: v for k, v in dados.items() if k in CAMPOS_FICHA}
    desconhecidos = sorted(set(dados) - set(CAMPOS_VIDEO))
    if desconhecidos:
        raise ValueError("campo de video desconhecido: " + ", ".join(desconhecidos))
    return dict(dados)


def extrair_video(fonte):
    """Le o video do payload canonico; devolve None quando nao ha dado valido."""
    dados = _candidato(fonte)
    if dados is None:
        return None
    dados = _normalizar(dados)
    for chave in OBRIGATORIOS:
        valor = dados.get(chave)
        if valor is None or (isinstance(valor, str) and not valor.strip()):
            return None
        if not isinstance(valor, str):
            raise ValueError("campo de video invalido: " + chave)
        dados[chave] = valor.strip()
    if not ID_YOUTUBE.match(dados["youtube_id"]):
        # Politica: sem ID valido, nenhum bloco e criado.
        return None
    for chave in ("resumo", "duracao", "uploadDate", "duracao_iso"):
        valor = dados.get(chave)
        if valor is None:
            continue
        if not isinstance(valor, str):
            raise ValueError("campo de video invalido: " + chave)
        texto = valor.strip()
        if texto:
            dados[chave] = texto
        else:
            dados.pop(chave)
    pontos = dados.get("pontos")
    if pontos is not None:
        if not isinstance(pontos, list):
            raise ValueError("youtube_pontos deve ser lista")
        itens = []
        for item in pontos:
            if item is None or isinstance(item, (dict, list)):
                raise ValueError("youtube_pontos invalido")
            texto = str(item).strip()
            if texto:
                itens.append(texto)
        if itens:
            dados["pontos"] = itens[:4]
        else:
            dados.pop("pontos")
    if "duracao_iso" in dados:
        iso = duracao_para_iso(dados["duracao_iso"])
        if not iso:
            raise ValueError("youtube_duracao_iso invalida")
        dados["duracao_iso"] = iso
    elif dados.get("duracao"):
        iso = duracao_para_iso(dados["duracao"])
        if iso:
            dados["duracao_iso"] = iso
    return dados


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
    if video.get("duracao"):
        partes.append('<p class="cx-video-duracao">Duração: '
                      + html.escape(video["duracao"]) + "</p>")
    partes.append(
        f'<p class="cx-video-credito">Crédito: {canal} · '
        f'<a href="https://www.youtube.com/watch?v={vid}" rel="noopener" '
        'target="_blank">Assistir no YouTube</a></p>')
    partes.append("</section>")
    return "\n".join(partes)


def _json_para_script(dados):
    """JSON valido e seguro dentro de <script>.

    `<`, `>` e `&` viram escapes unicode: fecham qualquer tentativa de
    `</script>`/`<!--` sem corromper o texto (o consumidor decodifica igual).
    """
    texto = json.dumps(dados, ensure_ascii=False)
    return (texto.replace("<", "\\u003c").replace(">", "\\u003e")
                 .replace("&", "\\u0026")
                 .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


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
    return ('<script type="application/ld+json">'
            + _json_para_script(dados) + "</script>")
