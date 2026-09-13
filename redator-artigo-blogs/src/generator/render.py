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
# Tokens de spec (chipset, GPU, padrão, certificação): "Adreno 618", "UFS 3.0", "IP67"
TOKEN_SPEC = re.compile(r"\b(?:Adreno|Snapdragon|Exynos|Mali|Dimensity|Helio|Tensor|Oryon|Cortex|Kryo|UFS|eMMC|LPDDR|IP|Gorilla|Wi-?Fi|Bluetooth|USB)\s?[\w.-]*\d[\w.-]*", re.IGNORECASE)


def _sanitizar_llm_html(texto: str, fontes_permitidas: list = None) -> str:
    """Markdown residual -> HTML; mantém [fonte: X] só de fonte permitida."""
    t = html.escape(texto or "")
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    linhas, out, lista = t.split("\n"), [], None
    for ln in linhas:
        s = ln.strip()
        m = re.match(r"^(#{1,3})\s+(.*)$", s)
        if m:
            if lista:
                out.append(f"</{lista}>")
                lista = None
            out.append(f"<h{min(len(m.group(1)) + 1, 3)}>{m.group(2)}</h{min(len(m.group(1)) + 1, 3)}>")
        elif re.match(r"^(\d+[.)]|[-*])\s+", s):
            tag = "ol" if re.match(r"^\d", s) else "ul"
            if lista != tag:
                if lista:
                    out.append(f"</{lista}>")
                out.append(f"<{tag}>")
                lista = tag
            out.append(f"<li>{re.sub(r'^(\d+[.)]|[-*])\s+', '', s)}</li>")
        elif s:
            if lista:
                out.append(f"</{lista}>")
                lista = None
            out.append(f"<p>{s}</p>")
    if lista:
        out.append(f"</{lista}>")
    t = "\n".join(out)
    if fontes_permitidas is not None:
        permitidas = {f.lower() for f in fontes_permitidas}
        def _fonte(m):
            return m.group(0) if m.group(1).strip().lower() in permitidas else ""
        t = re.sub(r"\[fonte:\s*([^\]]+)\]", _fonte, t)
    return t


def _remover_alusao_teste(texto: str) -> str:
    """Nunca testamos nada: remove frases de bancada/uso real."""
    t = texto or ""
    for p in ALUSOES_TESTE:
        t = re.sub(p, "", t, flags=re.IGNORECASE)
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def _detectar_hallucination(texto: str, specs_pass: dict) -> list:
    """Valores numéricos E tokens de spec do texto que NÃO constam em specs_PASS.

    Limite honesto: detecta token desconhecido ("Adreno 618" com specs dizendo
    "Adreno 610"), mas não má-atribuição ("ambos têm IP67" quando só um tem).
    """
    base = " ".join(str(v) for v in (specs_pass or {}).values())
    base_num = re.sub(r"[^\d ]", " ", base)
    base_token = re.sub(r"[^a-z0-9]", "", base.lower())
    suspeitas = []
    for m in VALOR_NUMERICO.finditer(texto or ""):
        val = m.group(0).strip()
        numero = re.sub(r"[^\d]", "", val)
        if numero and numero not in base_num:
            suspeitas.append(f"{val} não consta em specs_PASS")
    for m in TOKEN_SPEC.finditer(texto or ""):
        tok, norm = m.group(0).strip(), re.sub(r"[^a-z0-9]", "", m.group(0).lower())
        if norm and norm not in base_token:
            suspeitas.append(f"{tok} não consta em specs_PASS")
    return sorted(set(suspeitas))


def montar_tabela_specs(modelos: list) -> str:
    """Tabela comparativa a partir das chaves de specs (só dados verificados)."""
    chaves = []
    for m in modelos:
        for k in (m.get("specs") or {}):
            if k not in chaves:
                chaves.append(k)
    if not chaves:
        return ""
    th = "".join(f"<th>{html.escape(m.get('nome', ''))}</th>" for m in modelos)
    trs = "".join(
        f"<tr><th>{html.escape(k)}</th>"
        + "".join(f"<td>{html.escape(str((m.get('specs') or {}).get(k, '— não informado')))}</td>" for m in modelos)
        + "</tr>"
        for k in chaves
    )
    return (f'<table class="compare-table" border="1" cellpadding="8" cellspacing="0">\n'
            f"  <thead><tr><th>Especificação</th>{th}</tr></thead>\n  <tbody>{trs}\n</tbody>\n</table>")


def montar_pagina(titulo: str, descricao: str, modelos: list, categoria: str,
                  secoes_html: str, price_history: dict = None, data_iso: str = "") -> str:
    """Página completa no padrão publicado (head/meta/JSON-LD/Chart/AdSense)."""
    data_iso = data_iso or datetime.now(timezone.utc).isoformat()
    nomes = " vs ".join(m.get("nome", "") for m in modelos)
    about = ",\n".join(
        f'    {{"@type": "Product", "name": "{html.escape(m.get("nome", ""))}", "category": "{html.escape(categoria)}"}}'
        for m in modelos
    )
    tabela = montar_tabela_specs(modelos)
    hist_json = json.dumps(price_history or {}, ensure_ascii=False)
    grafico = ""
    if price_history:
        grafico = f"""
    <section id="price-history">
      <h2>Variação de preço (30 dias)</h2>
      <canvas id="priceChart" width="600" height="300"></canvas>
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
  <title>{html.escape(titulo)} | Redator</title>
  <meta name="description" content="{html.escape(descricao)}">
  <script type="application/ld+json">{{"@context": "https://schema.org", "@type": "Article",
"headline": "{html.escape(nomes)}", "datePublished": "{data_iso}", "dateModified": "{data_iso}",
"author": {{"@type": "Organization", "name": "Equipe Redator"}},
"about": [{about}]}}</script>
</head>
<body>
  <article>
    <h1>{html.escape(titulo)}</h1>
{secoes_html}
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


def gerar_comparativo(modelos: list, categoria: str = "celular", price_history: dict = None,
                      chamar_llm=None, unknown_fields: list = None) -> dict:
    """Orquestra: prompt -> LLM (injetável p/ testes) -> travas -> página + auditoria.

    modelos: [{nome, specs:{...}, fonte}]. chamar_llm(system, user_payload) -> str.
    Nunca inventa: sem specs, seções saem com '— não informado'.
    """
    from .prompt import montar_system_prompt
    specs_pass = {m.get("nome", ""): dict(m.get("specs") or {}) for m in modelos}
    fontes = sorted({m.get("fonte", "") for m in modelos if m.get("fonte")})
    system = montar_system_prompt(categoria)
    payload = {"modelos": [m.get("nome") for m in modelos], "categoria": categoria,
               "specs_PASS": specs_pass, "price_history": price_history or {},
               "unknown_fields": unknown_fields or []}
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
    uniao_specs = {}
    for s in specs_pass.values():
        uniao_specs.update(s)
    suspeitas = _detectar_hallucination(texto_llm, uniao_specs)
    secoes = _sanitizar_llm_html(texto_llm, fontes)
    nomes = " vs ".join(m.get("nome", "") for m in modelos)
    titulo = f"{nomes} — Comparativo completo ({categoria})"
    html_pag = montar_pagina(titulo, f"Comparativo {nomes}: ficha técnica, prós e contras verificados e veredito para {categoria}.",
                             modelos, categoria, secoes, price_history)
    return {"titulo": titulo, "html": html_pag, "provedor": provedor,
            "suspeitas_hallucination": suspeitas,
            "auditoria": {"specs_usadas": list(uniao_specs), "fontes": fontes,
                          "unknown_fields": unknown_fields or []}}
