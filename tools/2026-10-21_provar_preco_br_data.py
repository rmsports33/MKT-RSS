# -*- coding: utf-8 -*-
"""Prova: o criterio preco_br_data e' alcancavel ou nao pela cadeia real.

Cadeia real: price_history (float) -> construir_contrato -> normalizar_preco
-> gate (filtrar_valor_acrescentado com produtos=).

O gate le o preco com a regex _PRECO_BR, que EXIGE o simbolo "R$". Se o
contrato guardar o preco sem o simbolo, o criterio fica inalcancavel.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from mkt_flow_p0.comparativo_contract import construir_contrato  # noqa: E402
from mkt_flow_p0.content_filter import _PRECO_BR, filtrar_valor_acrescentado  # noqa: E402

AMAZON = "https://www.amazon.com.br/dp/B0XXX"
SAMSUNG = "https://news.samsung.com/br/galaxy-s26"

print("regex do gate:", _PRECO_BR.pattern)
print('  "R$ 5.999,00" casa?', bool(_PRECO_BR.search("R$ 5.999,00")))
print('  "5.999,00"    casa?', bool(_PRECO_BR.search("5.999,00")))
print()

contrato = construir_contrato(
    modelos=[{"nome": "Galaxy S26", "specs": {}, "fonte": SAMSUNG}],
    price_history={"Galaxy S26": [{"data": "2026-09-17", "preco": 5999.00, "fonte": AMAZON}]},
    conteudo_html="<p>c</p>",
    titulo="Galaxy S26",
    notas={"Galaxy S26": 9.0},
    compras={"Galaxy S26": AMAZON},
    criterios=[{"label": "Bateria", "vals": ["5000 mAh"], "win": 0}],
)
produto = contrato["produtos"][0]
print("preco guardado no contrato:", repr(produto["preco"]))
print("data_captura:", repr(produto["data_captura"]))
print("fonte_preco:", repr(produto["fonte_preco"]))

gate = filtrar_valor_acrescentado(
    titulo=contrato["titulo"], texto="", produtos=[{
        "nome": produto["nome"], "preco": produto["preco"],
        "data_captura": produto["data_captura"], "fonte_preco": produto["fonte_preco"],
        "links": [produto["fonte_preco"], produto["fonte"]],
        "tem_cruzamento": True,
    }],
)
print("criterios do gate:", gate.get("criterios"))
print("preco_br_data alcancavel?", "preco_br_data" in (gate.get("criterios") or []))
