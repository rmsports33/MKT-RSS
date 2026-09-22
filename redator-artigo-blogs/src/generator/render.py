"""src.generator.render — montagem do comparativo no formato publicado.

Pipeline: LLM (seções) -> sanitiza -> remove alusão a teste -> detecta
alucinação contra specs_PASS -> monta página (head/meta/JSON-LD/tabela/
Chart.js/AdSense) + .json de auditoria.
Formato espelha o sample publicado (artigo-a54-vs-redmi.html).
"""
import html
import json
import re
from datetime import datetime, timezone

ALUSOES_TESTE = [
    r"testamos em bancada", r"nossos testes mostram", r"medimos em ",
    r"mediç[ãa]o própria", r"em nossos laborat", r"unidade que testamos",
]
VALOR_NUMERICO = re.compile(r"\d[\d.,]*\s?(GB|MB|mAh|Hz|g\b|px|ppi|pol(?:egadas)?|nits?|min\b|horas?|dias?|%|R\$|x\d+)", re.IGNORECASE)
# Tokens de spec (chipset, GPU, padrão, certificação): "Adreno 618", "UFS 3.0", "IP67",
# "GPU 4-core" (núcleos fora da ficha NUNCA são legítimos — ver gate em gerar_comparativo).
TOKEN_SPEC = re.compile(r"\b(?:Adreno|Snapdragon|Exynos|Mali|Dimensity|Helio|Tensor|Oryon|Cortex|Kryo|UFS|eMMC|LPDDR|IP|Gorilla|Wi-?Fi|Bluetooth|USB)\s?[\w.-]*\d[\w.-]*|(?:GPU|CPU|NPU)\s+\d+\s*-?cores?", re.IGNORECASE)
# Placeholders em prosa (o sanitizer de [CAIXA ALTA] não pega estes).
PROSE_PLACEHOLDERS = [
    r"ser[áa] inserid[oa]s? automaticamente",
    r"tabela (comparativa )?abaixo",
    r"conforme tabela abaixo",
    r"nesta se[çc][aã]o em breve",
    r"em breve nesta se[çc][aã]o",
]
# Chaves de metadado que vivem em specs mas NUNCA viram linha de tabela.
META_SPEC_KEYS = {"youtube_id"}
# ID de vídeo YouTube: exatamente 11 chars [A-Za-z0-9_-].
YOUTUBE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def _eh_separador_tabela(s: str) -> bool:
    cels = [c.strip() for c in s.strip().strip("|").split("|")]
    return bool(cels) and all(c and set(c) <= set("-: ") for c in cels)


def _tabela_html(linhas: list) -> str:
    """Bloco de linhas '|' -> 1 <table> (primeira linha vira th)."""
    uteis = [ln for ln in linhas if not _eh_separador_tabela(ln)]
    if not uteis:
        return ""
    head = [c.strip() for c in uteis[0].strip().strip("|").split("|")]
    thead = "<thead><tr>" + "".join(f"<th>{html.escape(c)}</th>" for c in head) + "</tr></thead>"
    corpo = ""
    for ln in uteis[1:]:
        cels = [c.strip() for c in ln.strip().strip("|").split("|")]
        corpo += "<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in cels) + "</tr>"
    return f'<table class="compare-table">\n{thead}\n<tbody>{corpo}</tbody>\n</table>'


def _sanitizar_llm_html(texto: str, fontes_permitidas: list = None) -> str:
    """Markdown residual -> HTML; mantém [fonte: X] só de fonte permitida.

    Remove marcadores de placeholder em caixa alta (ex.: [TABELA INSERIDA],
    [FOTO: X]) para nenhum rastro do prompt vazar para o leitor.
    """
    t = html.escape(texto or "")
    # Placeholders de caixa alta (ex.: [TABELA INSERIDA], [FOTO: galeria])
    # nunca chegam ao leitor. [fonte: X] fica de fora (convertido adiante).
    t = re.sub(r"\[(?!fonte:)[^\]]+\]", "", t, flags=re.IGNORECASE)
    # Placeholders em prosa (ex.: "a tabela será inserida automaticamente").
    for p in PROSE_PLACEHOLDERS:
        t = re.sub(p, "", t, flags=re.IGNORECASE)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    linhas, out, lista, tbl = t.split("\n"), [], None, []

    def _descarrega_tabela():
        if tbl:
            out.append(_tabela_html(tbl))
            tbl.clear()

    for ln in linhas:
        s = ln.strip()
        if not s:
            if lista:
                out.append(f"</{lista}>")
                lista = None
            _descarrega_tabela()
            continue
        if s in ("---", "***", "___", "—", "–"):
            if lista:
                out.append(f"</{lista}>")
                lista = None
            _descarrega_tabela()
            out.append("<hr>")
            continue
        if s.startswith("|"):
            if lista:
                out.append(f"</{lista}>")
                lista = None
            tbl.append(s)
            continue
        _descarrega_tabela()
        m = re.match(r"^(#{1,3})\s+(.*)$", s)
        if m:
            if lista:
                out.append(f"</{lista}>")
                lista = None
            nivel = 2 if len(m.group(1)) <= 2 else 3
            out.append(f"<h{nivel}>{m.group(2)}</h{nivel}>")
        elif re.match(r"^(\d+[.)]|[-*])\s+", s):
            tag = "ol" if re.match(r"^\d", s) else "ul"
            if lista != tag:
                if lista:
                    out.append(f"</{lista}>")
                out.append(f"<{tag}>")
                lista = tag
            out.append("<li>" + re.sub(r"^(\d+[.)]|[-*])\s+", "", s) + "</li>")
        elif s:
            if lista:
                out.append(f"</{lista}>")
                lista = None
            out.append(f"<p>{s}</p>")
    if lista:
        out.append(f"</{lista}>")
    _descarrega_tabela()
    t = "\n".join(out)
    if fontes_permitidas is not None:
        permitidas = {f.strip().lower(): f.strip() for f in fontes_permitidas}
        ordem = []

        def _fonte(m):
            chave = m.group(1).strip().lower()
            if chave not in permitidas:
                return ""
            if chave not in ordem:
                ordem.append(chave)
            return f'<sup class="fonte-ref">[{ordem.index(chave) + 1}]</sup>'

        t = re.sub(r"\[fonte:\s*([^\]]+)\]", _fonte, t, flags=re.IGNORECASE)
        if ordem:
            lis = "".join(f'<li id="fonte-{i + 1}">{html.escape(permitidas[c])}</li>' for i, c in enumerate(ordem))
            t += f'\n<section class="fonte-list"><h3>Fontes</h3><ol>{lis}</ol></section>'
    return t


def _remover_alusao_teste(texto: str) -> str:
    """Nunca testamos nada: remove frases de bancada/uso real."""
    t = texto or ""
    for p in ALUSOES_TESTE:
        t = re.sub(p, "", t, flags=re.IGNORECASE)
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def _tokens_spec_suspeitos(texto: str, specs_pass: dict) -> list:
    """Subconjunto duro da detecção: tokens de spec (chip/GPU/padrão) ausentes
    da ficha. Um token desses fora da ficha NUNCA é legítimo (alucinação ou
    variante errada) — por isso alimenta o gate de bloqueio em gerar_comparativo.
    """
    vals = []
    for v in (specs_pass or {}).values():
        vals.extend(v if isinstance(v, list) else [v])
    base_token = re.sub(r"[^a-z0-9]", "", " ".join(str(x) for x in vals).lower())
    achados = []
    for m in TOKEN_SPEC.finditer(texto or ""):
        norm = re.sub(r"[^a-z0-9]", "", m.group(0).lower())
        if norm and norm not in base_token:
            achados.append(m.group(0).strip())
    return sorted(set(achados))


def _detectar_hallucination(texto: str, specs_pass: dict) -> list:
    """Valores numéricos E tokens de spec do texto que NÃO constam em specs_PASS.

    Limite honesto: detecta token desconhecido ("Adreno 618" com specs dizendo
    "Adreno 610"), mas não má-atribuição ("ambos têm IP67" quando só um tem).
    Aceita specs como {chave: valor} ou {chave: [valores]} (multi-modelo).
    Números (preços etc.) são SÓ aviso — o bloqueio usa _tokens_spec_suspeitos.
    """
    vals = []
    for v in (specs_pass or {}).values():
        vals.extend(v if isinstance(v, list) else [v])
    base = " ".join(str(x) for x in vals)
    base_num = re.sub(r"[^\d ]", " ", base)
    base_flat = re.sub(r"\D", "", base)  # "188,5" do texto vira 1885; "188.5" da ficha também
    base_token = re.sub(r"[^a-z0-9]", "", base.lower())
    suspeitas = []
    for m in VALOR_NUMERICO.finditer(texto or ""):
        val = m.group(0).strip()
        numero = re.sub(r"[^\d]", "", val)
        if numero and numero not in base_num and numero not in base_flat:
            suspeitas.append(f"{val} não consta em specs_PASS")
    for m in TOKEN_SPEC.finditer(texto or ""):
        tok, norm = m.group(0).strip(), re.sub(r"[^a-z0-9]", "", m.group(0).lower())
        if norm and norm not in base_token:
            suspeitas.append(f"{tok} não consta em specs_PASS")
    return sorted(set(suspeitas))


LABEL_SPEC = {
    "tela.polegadas": "Tela (pol)",
    "tela.resolucao": "Resolução",
    "tela.tipo": "Tipo de tela",
    "tela.painel": "Tipo de tela",
    "tela.hz": "Taxa de atualização (Hz)",
    "tela.brilho.nits": "Brilho (nits)",
    "tela.contraste": "Contraste",
    "tela.protecao": "Proteção da tela",
    "armazenamento.gb": "Armazenamento (GB)",
    "armazenamento.tipo": "Tipo de armazenamento",
    "ram.gb": "RAM (GB)",
    "chipset.modelo": "Chipset",
    "gpu": "GPU",
    "cpu.nucleos": "CPU núcleos",
    "so": "Sistema operacional",
    "bateria.mah": "Bateria (mAh)",
    "bateria.carregamento_w": "Carregamento (W)",
    "carregamento.w": "Carregamento com fio (W)",
    "carregamento.sem_fio.w": "Carregamento sem fio (W)",
    "peso.g": "Peso (g)",
    "dimensoes": "Dimensões (mm)",
    "dimensoes.mm": "Dimensões (mm)",
    "certificacao": "Certificação",
    "resistencia.agua": "Resistência à água",
    "protecao_agua": "Proteção",
    "expansao": "Expansão de armazenamento",
    "camera.traseira.mp": "Câmera traseira (MP)",
    "camera.frontal.mp": "Câmera frontal (MP)",
    "camera.traseira_mp": "Câmera traseira (MP)",
    "camera.frontal_mp": "Câmera frontal (MP)",
    "camera.zoom.optico": "Zoom óptico",
    "video.max": "Vídeo máximo",
    "video.resolucao": "Resolução de vídeo",
    "rede.5g": "5G",
    "wifi.padrao": "Wi-Fi",
    "bluetooth.versao": "Bluetooth",
    "nfc": "NFC",
    "usb": "USB",
    "conectividade": "Conectividade",
    "construcao": "Construção",
    "antutu": "AnTuTu (pontos)",
}


def _video_valido(video: dict) -> bool:
    """Só aceita dict com youtube_id de 11 chars; resto nunca quebra a página."""
    return bool(video) and bool(YOUTUBE_ID_RE.match(str(video.get("youtube_id", ""))))


def montar_bloco_video(video: dict) -> str:
    """Seção 'review em vídeo' com facade: player só carrega após o clique.

    video: {youtube_id (obrigatório, 11 chars), titulo, canal,
            resumo?, pontos? (lista, máx 4), duracao? (texto, ex. '8:32')}.
    ID inválido/ausente -> "" (sem iframe, sem schema, sem erro).
    """
    if not _video_valido(video):
        return ""
    vid = str(video["youtube_id"])
    titulo = str(video.get("titulo") or "Review em vídeo").strip()
    canal = str(video.get("canal") or "").strip()
    resumo = str(video.get("resumo") or "").strip()
    pontos = [str(p).strip() for p in (video.get("pontos") or []) if str(p).strip()][:4]
    duracao = str(video.get("duracao") or "").strip()
    thumb = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
    watch = f"https://www.youtube.com/watch?v={vid}"
    if resumo:
        paras = f"<p>{html.escape(resumo)}</p>"
    elif canal:
        paras = f"<p>Review em vídeo do canal {html.escape(canal)}: {html.escape(titulo)}.</p>"
    else:
        paras = f"<p>{html.escape(titulo)}.</p>"
    ul = "".join(f"<li>{html.escape(p)}</li>" for p in pontos)
    ul = f"<ul>{ul}</ul>" if ul else ""
    credito_nome = f"canal {html.escape(canal)}" if canal else "YouTube"
    dur = f" ({html.escape(duracao)})" if duracao else ""
    return f"""<section class="video-review">
      <h2>O que dizem os reviews em vídeo</h2>
      {paras}
      {ul}
      <div class="cxaf-video" data-video-id="{vid}">
        <button type="button" class="cxaf-video-play" aria-label="Carregar e reproduzir {html.escape(titulo)}">
          <img src="{thumb}" alt="{html.escape(titulo)}" loading="lazy" width="480" height="360">
          <span class="cxaf-video-ico" aria-hidden="true">▶</span>
        </button>
        <p class="cxaf-video-credito">Vídeo: {html.escape(titulo)}{dur} — <a href="{watch}" target="_blank" rel="noopener">Assistir no YouTube ({credito_nome})</a></p>
      </div>
      <script>
      if (!window.__cxafVideo) {{ window.__cxafVideo = true;
        document.addEventListener("click", function (ev) {{
          var btn = ev.target.closest ? ev.target.closest(".cxaf-video-play") : null;
          if (!btn) return;
          var box = btn.closest(".cxaf-video");
          var id = box && box.getAttribute("data-video-id");
          if (!id) return;
          var frame = document.createElement("iframe");
          frame.setAttribute("src", "https://www.youtube-nocookie.com/embed/" + id + "?autoplay=1&rel=0");
          frame.setAttribute("title", btn.getAttribute("aria-label") || "Vídeo do YouTube");
          frame.setAttribute("allow", "accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture");
          frame.setAttribute("allowfullscreen", "");
          frame.setAttribute("loading", "lazy");
          frame.style.cssText = "position:absolute;top:0;left:0;width:100%;height:100%;border:0";
          btn.replaceWith(frame);
        }});
      }}
      </script>
    </section>"""


def videoobject_jsonld(video: dict) -> str:
    """JSON-LD VideoObject só com dados conhecidos (nunca inventa uploadDate/duração)."""
    if not _video_valido(video):
        return ""
    vid = str(video["youtube_id"])
    titulo = str(video.get("titulo") or "Review em vídeo").strip()
    desc = str(video.get("resumo") or titulo).strip()
    campos = [f'"name": "{html.escape(titulo)}"',
              f'"description": "{html.escape(desc)}"',
              f'"thumbnailUrl": "https://i.ytimg.com/vi/{vid}/hqdefault.jpg"',
              f'"embedUrl": "https://www.youtube-nocookie.com/embed/{vid}"']
    if str(video.get("uploadDate") or "").strip():
        campos.append(f'"uploadDate": "{html.escape(str(video["uploadDate"]).strip())}"')
    if str(video.get("duracao_iso") or "").strip():
        campos.append(f'"duration": "{html.escape(str(video["duracao_iso"]).strip())}"')
    inner = ",\n".join(campos)
    return f'<script type="application/ld+json">{{"@context": "https://schema.org", "@type": "VideoObject",\n{inner}}}</script>'


def montar_tabela_specs(modelos: list) -> str:
    """Tabela comparativa a partir das chaves de specs (só dados verificados).

    Chave conhecida vira rótulo pt-BR (LABEL_SPEC); chave desconhecida é
    exibida como está para não inventar nome. Valor ausente sai '—'.
    Metadados (META_SPEC_KEYS, ex. youtube_id) nunca viram linha.
    """
    chaves = []
    for m in modelos:
        for k in (m.get("specs") or {}):
            if k in META_SPEC_KEYS or k.startswith("youtube_"):
                continue
            if k not in chaves:
                chaves.append(k)
    if not chaves:
        return ""
    th = "".join(f'<th scope="col">{html.escape(m.get("nome", ""))}</th>' for m in modelos)
    trs = "".join(
        f'<tr><th scope="row">{html.escape(LABEL_SPEC.get(k, k))}</th>'
        + "".join(f"<td>{html.escape(str((m.get('specs') or {}).get(k, '—')))}</td>" for m in modelos)
        + "</tr>"
        for k in chaves
    )
    return (f'<table class="compare-table" border="1" cellpadding="8" cellspacing="0">\n'
            f'  <thead><tr><th scope="col">Especificação</th>{th}</tr></thead>\n  <tbody>{trs}\n</tbody>\n</table>')


def _preco_br(valor) -> str:
    """Formata preço em pt-BR (R$ 1.500,50). Ausente/inválido -> ''.

    Aceita número (int/float) ou string ('1600', '1.600,00', '1500.5',
    'R$ 1.600,00'). Valor nulo/None nunca vira 'R$ None'.
    """
    if valor is None:
        return ""
    if isinstance(valor, (int, float)):
        return f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    s = str(valor).strip().replace("R$", "").replace("\xa0", "").replace(" ", "")
    if not s:
        return ""
    s = re.sub(r"(?<=\d)\.(?=\d{3}(?:[.,]|$))", "", s)  # tira ponto de milhar
    s = s.replace(",", ".")
    try:
        return _preco_br(float(s))
    except ValueError:
        return str(valor).strip()


def _precos_em_texto(price_history: dict) -> str:
    """Fallback textual do gráfico de preço (a informação não some sem Chart.js).

    Ponto sem preço válido (None/vazio) é ignorado — nunca vira 'R$ None'.
    """
    itens = []
    for modelo, pontos in (price_history or {}).items():
        if not pontos:
            continue
        pedacos = []
        for p in pontos:
            pr = _preco_br(p.get("preco"))
            if not pr:
                continue
            pedacos.append(f"{p.get('data', '?')}: R$ {pr}")
        if pedacos:
            itens.append(f"<li><b>{html.escape(modelo)}</b>: {html.escape(', '.join(pedacos))}</li>")
    if not itens:
        return ""
    return (f'<details class="price-fallback"><summary>Ver histórico em texto</summary>'
            f'<ul>{"".join(itens)}</ul></details>')


def montar_pagina(titulo: str, descricao: str, modelos: list, categoria: str,
                  secoes_html: str, price_history: dict = None, data_iso: str = "",
                  video: dict = None) -> str:
    """Página completa no padrão publicado (head/meta/JSON-LD/Chart/AdSense).

    video: dict do bloco de review em vídeo (ver montar_bloco_video) ou None.
    """
    data_iso = data_iso or datetime.now(timezone.utc).isoformat()
    nomes = " vs ".join(m.get("nome", "") for m in modelos)
    about = ",\n".join(
        f'    {{"@type": "Product", "name": "{html.escape(m.get("nome", ""))}", "category": "{html.escape(categoria)}"}}'
        for m in modelos
    )
    tabela = montar_tabela_specs(modelos)
    bloco_video = montar_bloco_video(video)
    video_ld = videoobject_jsonld(video)
    hist_json = json.dumps(price_history or {}, ensure_ascii=False)
    grafico = ""
    if price_history and any(pts for pts in price_history.values()) and _precos_em_texto(price_history):
        grafico = f"""
    <section id="price-history">
      <h2>Variação de preço (30 dias)</h2>
      <canvas id="priceChart" width="600" height="300"></canvas>
      {_precos_em_texto(price_history)}
      <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
      <script>
        const hist = {hist_json};
        const ctx = document.getElementById('priceChart');
        if (ctx) {{
          const datasets = Object.entries(hist).map(([modelo, pontos], i) => ({{
            label: modelo, data: pontos.map(p => p.preco),
            borderColor: ['#1976d2','#d32f2f','#388e3c'][i%3], fill: false }}));
          const labels = hist[Object.keys(hist)[0]]?.map(p => p.data) || [];
          new Chart(ctx, {{type:'line', data: {{labels, datasets}}, options: {{responsive:true}}}});
        }}
      </script>
    </section>"""
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(titulo)} | ConexoTech</title>
  <meta name="description" content="{html.escape(descricao)}">
  <script type="application/ld+json">{{"@context": "https://schema.org", "@type": "Article",
"headline": "{html.escape(nomes)}", "datePublished": "{data_iso}", "dateModified": "{data_iso}",
"author": {{"@type": "Organization", "name": "Redação ConexoTech"}},
"about": [{about}]}}</script>
{video_ld}
</head>
<body>
  <article>
    <h1>{html.escape(titulo)}</h1>
{secoes_html}
    {bloco_video}
    <section id="tabela-comparativa">
      <h2>Tabela comparativa</h2>
      {tabela}
    </section>
    {grafico}
    <div class="adsense"><!-- adsense-top --></div>
    <div class="adsense"><!-- adsense-middle --></div>
    <div class="adsense"><!-- adsense-bottom --></div>
  </article>
</body>
</html>"""


CAMPOS_VIDEO_FICHA = {
    "youtube_id": "youtube_id", "youtube_titulo": "titulo", "youtube_canal": "canal",
    "youtube_resumo": "resumo", "youtube_pontos": "pontos", "youtube_duracao": "duracao",
    "youtube_uploadDate": "uploadDate", "youtube_duracao_iso": "duracao_iso",
}


def _video_da_ficha(modelos: list) -> dict:
    """Monta o dict do bloco de vídeo a partir dos campos youtube_* da ficha.

    Primeiro modelo com youtube_id válido vence. Sem campo válido -> {}.
    """
    for m in modelos or []:
        specs = m.get("specs") or {}
        vid = str(specs.get("youtube_id", ""))
        if not YOUTUBE_ID_RE.match(vid):
            continue
        video = {"youtube_id": vid}
        for campo_ficha, chave in CAMPOS_VIDEO_FICHA.items():
            if chave == "youtube_id":
                continue
            valor = specs.get(campo_ficha)
            if isinstance(valor, list):
                itens = [str(p).strip() for p in valor if str(p).strip()]
                if itens:
                    video[chave] = itens
            elif valor is not None and str(valor).strip():
                video[chave] = str(valor).strip()
        return video
    return {}


def gerar_comparativo(modelos: list, categoria: str = "celular", price_history: dict = None,
                      chamar_llm=None, unknown_fields: list = None, video: dict = None,
                      forcar: bool = False) -> dict:
    """Orquestra: prompt -> LLM (injetável p/ testes) -> travas -> página + auditoria.

    modelos: [{nome, specs:{...}, fonte, data_lancamento?}]. chamar_llm(system, user_payload) -> str.
    data_lancamento (AAAA-MM) vai ao payload p/ a regra de recência do prompt.
    video: dict do bloco de review em vídeo (ver montar_bloco_video); quando None,
    é montado automaticamente dos campos youtube_* da ficha (ver _video_da_ficha).
    Nunca inventa: sem specs, seções saem com '— não informado'.
    Gate: spec fora da ficha (chip/GPU/padrão) BLOQUEIA a saída, salvo forcar=True
    (override explícito humano, registrado na auditoria).
    """
    from .prompt import montar_system_prompt
    specs_pass = {m.get("nome", ""): dict(m.get("specs") or {}) for m in modelos}
    fontes = sorted({m.get("fonte", "") for m in modelos if m.get("fonte")})
    datas_lancamento = {m.get("nome", ""): m.get("data_lancamento", "") for m in modelos
                        if m.get("data_lancamento")}
    if video is None:
        video = _video_da_ficha(modelos)
    system = montar_system_prompt(categoria)
    payload = {"modelos": [m.get("nome") for m in modelos], "categoria": categoria,
               "specs_PASS": specs_pass, "price_history": price_history or {},
               "unknown_fields": unknown_fields or [], "video_review": video or {},
               "datas_lancamento": datas_lancamento}
    if chamar_llm is None:
        from src.evergreen import gerar_texto
        import json as _j
        r = gerar_texto(system, _j.dumps(payload, ensure_ascii=False))
        if "erro" in r:
            return {"erro": r["erro"]}
        texto_llm = r["texto"]
        provedor = r.get("provedor", "?")
    else:
        texto_llm = chamar_llm(system, payload)
        provedor = "injetado"
    texto_llm = _remover_alusao_teste(texto_llm)
    # Une specs dos modelos SEM sobrescrever (mesma chave, valores diferentes)
    uniao_specs: dict = {}
    for s in specs_pass.values():
        for k, v in (s or {}).items():
            uniao_specs.setdefault(k, []).append(v)
    suspeitas = _detectar_hallucination(texto_llm, uniao_specs)
    duras = _tokens_spec_suspeitos(texto_llm, uniao_specs)
    if duras and not forcar:
        return {"erro": "BLOQUEADO: spec fora da ficha: " + "; ".join(duras[:8]),
                "suspeitas_hallucination": suspeitas, "bloqueio_specs": duras,
                "auditoria": {"specs_usadas": list(uniao_specs), "fontes": fontes,
                              "unknown_fields": unknown_fields or [],
                              "video_id": (video or {}).get("youtube_id", ""),
                              "forcar": False}}
    secoes = _sanitizar_llm_html(texto_llm, fontes)
    nomes = " vs ".join(m.get("nome", "") for m in modelos)
    titulo = f"{nomes} — Comparativo completo ({categoria})"
    html_pag = montar_pagina(titulo, f"Comparativo {nomes}: ficha técnica, prós e contras verificados e veredito para {categoria}.",
                             modelos, categoria, secoes, price_history, video=video)
    return {"titulo": titulo, "html": html_pag, "provedor": provedor,
            "suspeitas_hallucination": suspeitas,
            "auditoria": {"specs_usadas": list(uniao_specs), "fontes": fontes,
                          "unknown_fields": unknown_fields or [],
                          "video_id": (video or {}).get("youtube_id", ""),
                          "forcar": forcar}}
