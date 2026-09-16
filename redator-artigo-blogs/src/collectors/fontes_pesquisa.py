# -*- coding: utf-8 -*-
"""fontes_pesquisa.py — descoberta + extração de specs de FABRICANTES.

Camada honesta do pipeline: SOMENTE domínios de fabricante. Varejo,
marketplaces e agregadores são RECUSADOS com erro explícito (regra ML/ToS).
Sem chave, sem dependência: apenas stdlib. Baixo volume (por artigo).

Uso:
    python fontes_pesquisa.py "Galaxy A54" --marca Samsung
    python fontes_pesquisa.py "Redmi Note 13" --marca Xiaomi --categoria celular

Saída: JSON com candidato + fonte + nível B-pendente (humano confirma
antes de virar curado). Preços: FORA do escopo (rotina manual).
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

UA = {"User-Agent": "Mozilla/5.0 (pesquisa editorial; baixo volume)"}
CACHE = Path(__file__).parent / "fontes_cache.json"


def _carregar_env():
    """Lê .env (pasta do script + pasta atual) p/ uso local.
    No Actions, valem os Secrets. Nunca commita (.env é ignorado)."""
    for base in (Path(__file__).parent, Path.cwd()):
        f = base / ".env"
        if not f.exists():
            continue
        try:
            for ln in f.read_text(encoding="utf-8").splitlines():
                ln = ln.strip()
                if not ln or ln.startswith("#") or "=" not in ln:
                    continue
                k, v = ln.split("=", 1)
                k, v = k.strip(), v.strip().strip("'\"")
                if k and k not in os.environ:
                    os.environ[k] = v
        except Exception:
            pass

BLOQUEADOS = ["mercadolivre.", "amazon.", "shopee.", "aliexpress.",
              "magazineluiza.", "americanas.", "casasbahia.", "banggood.",
              "gearbest.", "ebay.", "buscape.", "zoom.", "bondfaro."]

FABRICANTES = ["samsung.com", "motorola.com", "mi.com", "xiaomi.com",
               "lg.com", "apple.com", "asus.com", "lenovo.com", "dell.com",
               "hp.com", "acer.com", "sony.", "philips.", "tcl.com",
               "hisense.", "positivo.", "multilaser.", "philco.", "aoc.",
               "mibrasil.", "shop.samsung.",
               "nokia.com", "realme.com", "infinixmobility.", "honor.com"]

MARCAS_DOMINIOS = {"samsung": ["samsung.com"], "xiaomi": ["mi.com", "mibrasil.com.br"],
                   "redmi": ["mi.com", "mibrasil.com.br"], "motorola": ["motorola.com"],
                   "lg": ["lg.com"], "apple": ["apple.com"], "asus": ["asus.com"],
                   "lenovo": ["lenovo.com"], "dell": ["dell.com"], "hp": ["hp.com"],
                   "acer": ["acer.com"], "sony": ["sony.com", "sony.com.br"],
                   "philips": ["philips.com", "philips.com.br"], "tcl": ["tcl.com"],
                   "hisense": ["hisense.com"], "nokia": ["nokia.com", "hmd.com"],
                   "realme": ["realme.com"], "infinix": ["infinixmobility.com"],
                   "honor": ["honor.com"]}


def _get(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def eh_fabricante(url):
    dom = urllib.parse.urlparse(url).netloc.lower()
    if any(b in dom for b in BLOQUEADOS):
        return False, "dominio bloqueado (varejo/marketplace/ToS)"
    if any(f in dom for f in FABRICANTES):
        return True, "fabricante"
    return False, "fora da lista de fabricantes (revisar manualmente)"


def _get_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8"))


def descobrir_oficial(modelo, marca=""):
    """Wikidata (sem chave): entidade -> P856 site oficial. Sem chute de URL.
    DuckDuckGo foi testado e REMOVIDO: serve captcha para fetch automatizado.
    Retorna (oficiais_na_lista, oficiais_revisar, descartados)."""
    oficiais, revisar, descartados = [], [], []
    exa_key = (os.getenv("EXA_API_KEY", "") or "").strip()
    if exa_key:
        try:
            doms = []
            for tok in re.split(r"\W+", (marca + " " + modelo).lower()):
                if tok in MARCAS_DOMINIOS:
                    doms.extend(MARCAS_DOMINIOS[tok])
            payload = json.dumps({"query": "ficha oficial %s %s Brasil fabricante especificacoes"
                                  % (marca, modelo), "numResults": 8,
                                  **({"includeDomains": sorted(set(doms))} if doms else {})}).encode("utf-8")
            req = urllib.request.Request(
                "https://api.exa.ai/search", data=payload,
                headers={"x-api-key": exa_key, "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                res = json.loads(r.read().decode("utf-8"))
            for it in res.get("results", []):
                url = it.get("url", "")
                if not url.startswith("http"):
                    continue
                ok, _ = eh_fabricante(url)
                if ok and url not in oficiais:
                    oficiais.append(url)
                time.sleep(0.2)
        except Exception:
            pass
    try:
        q = urllib.parse.quote(("%s %s" % (marca, modelo)).strip())
        s = _get_json("https://www.wikidata.org/w/api.php?action=wbsearchentities"
                      "&search=%s&language=pt&format=json&limit=6" % q)
    except Exception as e:
        return [], [], []
    for ent in s.get("search", [])[:6]:
        try:
            e = _get_json("https://www.wikidata.org/w/api.php?action=wbgetentities"
                          "&ids=%s&props=claims&format=json" % ent["id"])
            claims = e["entities"][ent["id"]].get("claims", {})
            for stmt in claims.get("P856", []):
                url = (stmt.get("mainsnak", {}).get("datavalue", {}).get("value", "") or "")
                if not url.startswith("http") or url in oficiais + revisar:
                    continue
                ok, _ = eh_fabricante(url)
                if ok:
                    oficiais.append(url)
                elif not any(b in urllib.parse.urlparse(url).netloc.lower() for b in BLOQUEADOS):
                    revisar.append(url)
                else:
                    descartados.append(url)
        except Exception:
            continue
        time.sleep(1)
    return oficiais, revisar, descartados


def extrair_estruturado(url, jina_key=""):
    """Fabricante: JSON-LD + OpenGraph + titulo. Erro nunca é silencioso."""
    jina_key = (jina_key or os.getenv("JINA_API_KEY", "") or "").strip()
    ok, motivo = eh_fabricante(url)
    if not ok:
        return {"erro": motivo, "url": url}
    via = "direto"
    try:
        html = _get(url)
    except Exception as e:
        err_direct = str(e)[:100]
        try:
            jreq = urllib.request.Request(
                "https://r.jina.ai/" + url,
                headers={"User-Agent": UA["User-Agent"],
                         **({"Authorization": "Bearer " + jina_key} if jina_key else {})})
            with urllib.request.urlopen(jreq, timeout=40) as r:
                html = r.read().decode("utf-8", "replace")
            via = "jina"
        except Exception as e2:
            return {"erro": "fetch direto falhou (%s); Jina falhou (%s)%s" % (
                err_direct, str(e2)[:100],
                "" if jina_key else " — crie JINA_API_KEY grátis p/ mais cota"), "url": url}
        time.sleep(2)
    if via == "jina":
        jan = _janelas_specs(html)
        fotos = []
        ALT_RUIM = ("logo", "icon", "seal", "selo", "avatar", "placeholder", "thumb", "sprite",
                    "google", "facebook", "twitter", "instagram", "youtube", "pinterest", "linkedin",
                    "tiktok", "whatsapp", "telegram", "social", "share", "follow", "newsletter")
        URL_RUIM = ("banner", "/ads/", "pixel", "tracking", "analytics", "promo",
                    "click?bid", "doubleclick")
        for alt, link, _full, outer in re.findall(
                r"!\[([^\]]{0,80})\]\((https?://[^)]+)\)(\]\((https?://[^)]+)\))?", html):
            juntos = (alt + " " + link + " " + (outer or "")).lower()
            if link.lower().split("?")[0].endswith((".jpg", ".jpeg", ".png", ".webp")) and not any(
                    k in juntos for k in ALT_RUIM + URL_RUIM):
                if link not in fotos:
                    fotos.append(link)
                if len(fotos) >= 6:
                    break
        return {"url": url, "fonte": "fabricante via Jina Reader (texto parcial)",
                "texto_specs": jan,
                "texto_busca": jan[:2000],
                "json_ld": [], "og_image": fotos[0] if fotos else "",
                "og_generica": (not fotos),
                "fotos_candidatas": fotos[1:],
                "nota": "extracao parcial — curadoria humana necessaria"}
    time.sleep(2)
    blocos = []
    for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)[:8]:
        try:
            d = json.loads(b.strip())
        except Exception:
            continue
        items = d if isinstance(d, list) else [d]
        for it in items:
            if isinstance(it, dict) and "@type" in it:
                blocos.append({"tipo": it.get("@type"),
                               "campos": {k: (str(v)[:300]) for k, v in it.items()
                                          if not k.startswith("@")}})
    og = dict(re.findall(r'<meta property="og:([^"]+)" content="([^"]+)"', html))
    t = re.search(r"<title>(.*?)</title>", html, re.S)
    titulo = (t.group(1).strip()[:160] if t else "")
    desc = og.get("description", "")[:400]
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<nav.*?</nav>|<footer.*?</footer>|<header.*?</header>", " ", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    vis = re.sub(r"\s+", " ", vis).strip()
    img = og.get("image", "")
    return {"url": url, "fonte": "fabricante (página oficial)",
            "titulo_pagina": titulo,
            "texto_busca": (titulo + "\n" + desc)[:2000],
            "texto_specs": _janelas_specs(vis) or vis[:1500],
            "json_ld": blocos,
            "og_image": img,
            "og_generica": ("logo" in img.lower()),
            "og_description": desc}


def _heuristica(ret):
    """Pistas planas claramente marcadas como heurística (confirmar!)."""
    txt = (ret.get("texto_specs") or "") + "\n" + (ret.get("texto_busca") or "")
    out = {}
    m = re.search(r"(\d{3,5})\s*mAh", txt)
    if m:
        out["bateria.mah?"] = m.group(1)
    m = re.search(r"(\d{2,3})\s*MP", txt)
    if m:
        out["camera.mp?"] = m.group(1)
    m = re.search(r'(\d[,.]\d+)\s*(?:"|polegadas|inches|inch|pol\.?)', txt, re.I)
    if m:
        out["tela.polegadas?"] = m.group(1)
    return out


def pesquisar(modelo, marca="", categoria="geral"):
    _carregar_env()
    oficiais, revisar, descartados = descobrir_oficial(modelo, marca)
    if not oficiais:
        return {"modelo": modelo, "erro": "nenhuma URL oficial encontrada (Wikidata)",
                "revisar_manualmente": revisar[:4],
                "dica": "cole a URL oficial (modo recuperacao MCA)"}
    tokens = [t.lower() for t in re.split(r"\W+", modelo) if len(t) >= 3]
    tentadas, melhor, melhor_pts = [], None, -1
    for url in oficiais[:4]:
        tentadas.append(url)
        r = extrair_estruturado(url)
        if "erro" in r:
            continue
        texto = ((r.get("titulo_pagina") or "") + " " + url).lower()
        tem_modelo = all(t in texto for t in tokens) if tokens else False
        tem_produto = any(b.get("tipo") == "Product" for b in r.get("json_ld", []))
        uu = url.lower()
        br = (urllib.parse.urlparse(uu).netloc.endswith(".br") or "/br/" in uu)
        suporte = any(k in uu for k in ("/support", "/suporte", "/download", "/manual", "/blog", "/news"))
        rota_produto = any(k in uu for k in ("/smartphone", "/product", "/specs", "/especific", "/celular", "/p/"))
        listagem = any(k in (r.get("titulo_pagina") or "").lower() for k in ("ofertas", "lancamentos", "lançamentos", "compare", "todos os", "catalogo", "catálogo", "linha completa", "encontre o modelo"))
        pts = ((2 if br else 0) + (2 if tem_modelo else 0) + (1 if tem_produto else 0)
               + (1 if rota_produto else 0) - (3 if suporte else 0) - (4 if listagem else 0))
        if pts > melhor_pts:
            melhor, melhor_pts = r, pts
    if melhor is None or melhor_pts < 2:
        return {"modelo": modelo, "erro": "nenhuma candidata com sinal de produto",
                "tentadas": tentadas,
                "dica": "cole a URL oficial (modo recuperacao MCA)"}
    ret = melhor
    ret["modelo_pedido"] = modelo
    ret["confianca"] = "B-pendente (humano confirma antes de curar)"
    ret["candidatas"] = extrair_candidatas(ret)
    return ret


CHAVES_SPECS = ["bateria", "mah", "camera", "câmera", "processador", "chipset",
                "snapdragon", "dimensity", "exynos", "tela", "display", "polegadas",
                "memoria", "memória", "ram", "armazenamento", "carregamento", "watt"]


def _janelas_specs(texto, raio=700, teto=6000):
    """Fatia trechos ao redor de palavras-chave de specs.
    Páginas são 90% menu/navegação — o dado mora no fundo."""
    if not texto:
        return ""
    baixo = texto.lower()
    cortes = []
    for kw in CHAVES_SPECS:
        i = 0
        while True:
            i = baixo.find(kw, i)
            if i < 0 or len(cortes) >= 24:
                break
            cortes.append((max(0, i - raio), i + len(kw) + raio))
            i += len(kw)
    cortes.sort()
    fundidas, ini, fim = [], None, None
    for a, b in cortes:
        if ini is None:
            ini, fim = a, b
        elif a <= fim:
            fim = max(fim, b)
        else:
            fundidas.append((ini, fim))
            ini, fim = a, b
    if ini is not None:
        fundidas.append((ini, fim))
    saida = " [...] ".join(texto[a:b] for a, b in fundidas)
    return re.sub(r"\s+", " ", saida).strip()[:teto]


def extrair_candidatas(ret):
    return _heuristica(ret)


def _checar_chaves():
    """Testa EXA_API_KEY e JINA_API_KEY sem exibir valores. Retorna dict."""
    _carregar_env()
    res = {}
    exa = (os.getenv("EXA_API_KEY", "") or "").strip()
    if exa:
        try:
            payload = json.dumps({"query": "teste", "numResults": 1}).encode("utf-8")
            req = urllib.request.Request(
                "https://api.exa.ai/search", data=payload,
                headers={"x-api-key": exa, "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                ok = json.loads(r.read().decode("utf-8")).get("results") is not None
            res["EXA_API_KEY"] = "OK" if ok else "FALHA (resposta inesperada)"
        except Exception as e:
            res["EXA_API_KEY"] = "FALHA (%s)" % str(e)[:90]
    else:
        res["EXA_API_KEY"] = "ausente (.env ou Secrets)"
    jina = (os.getenv("JINA_API_KEY", "") or "").strip()
    if jina:
        try:
            req = urllib.request.Request(
                "https://r.jina.ai/https://example.com",
                headers={"User-Agent": UA["User-Agent"],
                         "Authorization": "Bearer " + jina})
            with urllib.request.urlopen(req, timeout=40) as r:
                txt = r.read().decode("utf-8", "replace")
            res["JINA_API_KEY"] = "OK" if len(txt) > 200 else "FALHA (resposta curta)"
        except Exception as e:
            res["JINA_API_KEY"] = "FALHA (%s)" % str(e)[:90]
    else:
        res["JINA_API_KEY"] = "ausente (modo demo 20 RPM)"
    return res


def main():
    ap = argparse.ArgumentParser(description="Specs de fabricantes (honesto)")
    ap.add_argument("modelo", nargs="?")
    ap.add_argument("--marca", default="")
    ap.add_argument("--categoria", default="geral")
    ap.add_argument("--checar-chaves", action="store_true",
                    help="testa as chaves sem exibir valores")
    a = ap.parse_args()
    if a.checar_chaves or not a.modelo:
        print(json.dumps(_checar_chaves(), ensure_ascii=False, indent=2))
        return
    print(json.dumps(pesquisar(a.modelo, a.marca, a.categoria),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
