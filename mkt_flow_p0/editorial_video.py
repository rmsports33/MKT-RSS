"""Bloco de review em video — portado do gerador legado para o motor MKT-RSS.

Regras (docs/site/politica-curadoria-video.md):
- so ID do YouTube de 11 caracteres;
- titulo e canal reais, nunca inventados;
- player oficial youtube-nocookie, credito visivel e link direto;
- o video e SECAO do artigo, nunca o artigo inteiro;
- sem dado valido nao ha bloco; dado presente porem invalido reprova o pacote.

Dois formatos de entrada sao suportados, e apenas esses:
- a ficha canonica com campos `youtube_*` (redator-artigo-blogs);
- o dicionario curto ja convertido: `youtube_id`, `titulo`, `canal`, `resumo`,
  `pontos`, `duracao`, `uploadDate`, `duracao_iso`.

A validacao e a MESMA em qualquer localizacao do payload (`video`, `article`,
`metadata` ou raiz), e acontece ANTES da normalizacao:

- campo `youtube_*` desconhecido e recusado em qualquer lugar;
- no container `video` qualquer campo desconhecido e recusado; na raiz e na
  ficha (`article`/`metadata`) so os campos de video sao considerados, pois o
  resto do dicionario pertence ao pacote/artigo;
- ficha canonica (`article`/`metadata`) nao ignora `youtube_*` desconhecido nem
  mistura `youtube_*` com campos curtos; nela so `youtube_*` declara video,
  para nao confundir campo do artigo com video;
- o dicionario curto vale em bloco explicito, nunca como ficha de artigo;
- bloco incompleto, ambiguo ou com tipo errado reprova o pacote inteiro, em vez
  de virar video parcial;
- mais de uma origem de video no mesmo payload e conflito declarado.

Nenhuma chamada de rede e nenhuma escolha automatica de video: a curadoria e
humana. A chave YOUTUBE_API_KEY, quando usada, fica so no ambiente.
"""
import html
import json
import re
from datetime import date, datetime

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

# Campos que so existem no formato curto (youtube_id e comum aos dois).
CAMPOS_CURTOS = tuple(k for k in CAMPOS_VIDEO if k not in CAMPOS_FICHA)
LOCAIS_ARTIGO = ("article", "metadata")
LOCAIS_EXPLICITOS = ("video",)

# O bloco visivel mostra no maximo 4 pontos (politica do gerador legado).


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
    if m >= 60 or s >= 60:
        return ""
    partes = "PT"
    if h:
        partes += str(h) + "H"
    if m:
        partes += str(m) + "M"
    if s or not (h or m):
        partes += str(s) + "S"
    return partes


def _tem_campo_video(dados):
    """True quando o dicionario declara algum campo do contrato de video."""
    return any(isinstance(k, str) and (k.startswith("youtube_") or k in CAMPOS_VIDEO)
               for k in dados)


def _declara_video_canonico(dados):
    """Ficha de artigo so declara video por `youtube_*` (inclusive desconhecido)."""
    return any(isinstance(k, str) and k.startswith("youtube_") for k in dados)


def _eh_canonico(dados):
    """Formato canonico = presenca de `youtube_*` alem do id compartilhado."""
    return any(k in dados for k in CAMPOS_FICHA if k != "youtube_id")


def _rejeitar_youtube_desconhecido(dados, local):
    estranhos = sorted(k for k in dados
                       if isinstance(k, str) and k.startswith("youtube_")
                       and k not in CAMPOS_FICHA)
    if estranhos:
        raise ValueError("campo youtube_ desconhecido em %s: %s"
                         % (local, ", ".join(estranhos)))


def _validar_bloco(dados, local):
    """Aplica as mesmas regras a qualquer bloco; devolve se e canonico.

    O container `video` nao aceita campo fora do contrato. Raiz e ficha
    (`article`/`metadata`) carregam outros campos do pacote/artigo, mas seguem
    proibidas de ter `youtube_*` desconhecido ou mistura de formatos.
    """
    _rejeitar_youtube_desconhecido(dados, local)
    if local in LOCAIS_EXPLICITOS:
        desconhecidos = sorted(str(k) for k in dados
                              if not isinstance(k, str)
                              or (k not in CAMPOS_VIDEO and k not in CAMPOS_FICHA))
        if desconhecidos:
            raise ValueError("campo de video desconhecido em %s: %s"
                             % (local, ", ".join(desconhecidos)))
    canonico = _eh_canonico(dados)
    if canonico:
        mistos = sorted(k for k in dados if k in CAMPOS_CURTOS)
        if mistos:
            raise ValueError("nao misture youtube_* com campos curtos em %s: %s"
                             % (local, ", ".join(mistos)))
    return canonico


def _coletar_origens(fonte):
    """Localiza TODAS as origens de video; nao escolhe uma em silencio."""
    if not isinstance(fonte, dict):
        raise ValueError("payload de video deve ser dicionario")
    origens = []
    if "video" in fonte:
        bloco = fonte["video"]
        if not isinstance(bloco, dict):
            raise ValueError("video deve ser dicionario")
        if not bloco:
            raise ValueError("video vazio: informe os campos ou omita a chave")
        origens.append(("video", bloco))
    for local in LOCAIS_ARTIGO:
        if local not in fonte:
            continue
        bloco = fonte[local]
        if bloco is None:
            continue
        if not isinstance(bloco, dict):
            raise ValueError("%s deve ser dicionario" % local)
        if _declara_video_canonico(bloco):
            origens.append((local, bloco))
    if _tem_campo_video(fonte):
        origens.append(("root", fonte))
    return origens


def _normalizar(dados, canonico):
    """Converte ficha `youtube_*` ou dict curto para o formato interno.

    So roda depois da validacao: nenhum campo desconhecido chega aqui.
    """
    if canonico:
        return {CAMPOS_FICHA[k]: dados[k] for k in CAMPOS_FICHA if k in dados}
    return {k: dados[k] for k in CAMPOS_VIDEO if k in dados}


def _texto_obrigatorio(dados, chave, local):
    valor = dados.get(chave)
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError("video incompleto ou invalido em %s: %s" % (local, chave))
    return valor.strip()


def _opcionais(dados, local):
    for chave in ("resumo", "duracao", "uploadDate", "duracao_iso"):
        valor = dados.get(chave)
        if valor is None:
            dados.pop(chave, None)
            continue
        if not isinstance(valor, str):
            raise ValueError("campo de video invalido em %s: %s" % (local, chave))
        texto = valor.strip()
        if texto:
            dados[chave] = texto
        else:
            dados.pop(chave)


def _upload_date_valida(valor):
    """Accept Schema.org date or timezone-qualified ISO-8601 dateTime only."""
    if not isinstance(valor, str):
        return False
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", valor):
        try:
            date.fromisoformat(valor)
            return True
        except ValueError:
            return False
    if not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
            r"(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})", valor):
        return False
    try:
        parsed = datetime.fromisoformat(valor.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _pontos(dados, local):
    pontos = dados.get("pontos")
    if pontos is None:
        return
    if not isinstance(pontos, list):
        raise ValueError("youtube_pontos deve ser lista em %s" % local)
    itens = []
    for item in pontos:
        if item is None or isinstance(item, (dict, list, bool)):
            raise ValueError("youtube_pontos invalido em %s" % local)
        texto = str(item).strip()
        if not texto:
            raise ValueError("youtube_pontos com item vazio em %s" % local)
        itens.append(texto)
    if itens:
        dados["pontos"] = itens[:4]
    else:
        dados.pop("pontos")


def extrair_video(fonte):
    """Le o video do payload; None apenas quando nao ha campo de video algum.

    Qualquer video declarado e validado por inteiro: entrada invalida levanta
    ValueError e reprova o pacote, em vez de gerar bloco parcial.
    """
    origens = _coletar_origens(fonte)
    if not origens:
        return None
    if len(origens) > 1:
        raise ValueError("video definido em mais de uma origem: %s"
                         % ", ".join(local for local, _ in origens))
    local, bloco = origens[0]
    dados = _normalizar(bloco, _validar_bloco(bloco, local))
    for chave in OBRIGATORIOS:
        dados[chave] = _texto_obrigatorio(dados, chave, local)
    if not ID_YOUTUBE.match(dados["youtube_id"]):
        raise ValueError("youtube_id invalido em %s: %r" % (local, dados["youtube_id"]))
    _opcionais(dados, local)
    if dados.get("uploadDate") is not None and not _upload_date_valida(dados["uploadDate"]):
        raise ValueError("youtube_uploadDate deve ser data ISO-8601 valida com fuso quando houver horario")
    _pontos(dados, local)
    if "duracao_iso" in dados:
        iso = duracao_para_iso(dados["duracao_iso"])
        if not iso:
            raise ValueError("youtube_duracao_iso invalida em %s" % local)
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
                                       for p in video["pontos"][:4]) + "</ul>")
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
