# -*- coding: utf-8 -*-
"""ponte_redator.py — liga fontes_pesquisa ao redator-artigo-blogs.

O redator espera `fetcher(modelo, categoria)` devolvendo dict de specs.
Esta ponte adapta a saída rica do módulo fontes para esse contrato,
SEM inventar: só repassa o que veio com fonte; o resto fica vazio
e o redator escreve "— não informado" (regra dele, preservada).

Uso no redator (3 linhas, pelo dono/dev):
    import sys; sys.path.insert(0, "/caminho/para/tools")
    from ponte_redator import buscar_specs
    specs = buscar_specs("Galaxy A54", "celular", marca="Samsung")
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from fontes_pesquisa import pesquisar


def buscar_specs(modelo, categoria="geral", marca=""):
    """Retorna {"specs": {...}, "fonte": "url ou ''"}.

    Mapeia candidatas (chaves com '?' viram dotted sem '?') e anexa
    texto_specs + url para curadoria. Nunca preenche o que não veio.
    """
    r = pesquisar(modelo, marca, categoria)
    if "erro" in r:
        return {"specs": {}, "fonte": "",
                "aviso": r.get("erro", ""), "tentadas": r.get("tentadas", [])}
    specs = {}
    for k, v in (r.get("candidatas") or {}).items():
        if v:
            specs[k.replace("?", "")] = v
    return {"specs": specs,
            "fonte": r.get("url", ""),
            "texto_specs": r.get("texto_specs", "")[:3000],
            "og_image": r.get("og_image", ""),
            "fotos": r.get("fotos_candidatas", [])[:4],
            "confianca": r.get("confianca", ""),
            "modelo": modelo}


def modelo_para_redator(modelo, marca="", categoria="celular"):
    """Um modelo -> dict pronto p/ gerar_comparativo([{nome, specs, fonte}]).
    Mapeia candidatas '?'-sufixadas p/ chaves dotted; sem dado, specs={}.
    (redator escreve '— não informado' — regra dele, preservada)."""
    import fontes_pesquisa
    r = fontes_pesquisa.pesquisar(modelo, marca, categoria)
    if "erro" in r:
        return {"nome": modelo, "specs": {}, "fonte": "",
                "aviso": r.get("erro", ""), "tentadas": r.get("tentadas", [])}
    specs = {}
    for k, v in (r.get("candidatas") or {}).items():
        if v:
            specs[k.replace("?", "")] = v
    return {"nome": modelo, "specs": specs, "fonte": r.get("url", ""),
            "texto_specs": r.get("texto_specs", "")[:3000],
            "og_image": r.get("og_image", ""),
            "fotos": r.get("fotos_candidatas", [])[:4],
            "confianca": r.get("confianca", "")}


def modelos_para_redator(pares, categoria="celular"):
    """Vários (modelo, marca) -> lista pronta p/ gerar_comparativo."""
    return [modelo_para_redator(m, marca, categoria) for m, marca in pares]


if __name__ == "__main__":
    import json
    demo = {"specs": {"bateria.mah": "5000"},
            "fonte": "https://exemplo/oficial",
            "texto_specs": "", "og_image": "", "fotos": [],
            "confianca": "B-pendente", "modelo": "Demo"}
    print(json.dumps(demo, ensure_ascii=False, indent=2)[:400])
    print("ponte OK (contrato válido; vivo só com rede + chaves)")
