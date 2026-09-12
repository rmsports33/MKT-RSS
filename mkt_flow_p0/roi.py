"""
mkt_flow_p0.roi — Calculadora de ROI/Margem com dedução de taxas.
Pré-processamento externo: roda ANTES do LLM (nunca estima no modelo).
"""
import logging

logger = logging.getLogger("roi")


def calcular_roi_afiliado(cpc: float, cliques: int, taxa_conversao: float,
                          valor_medio_produto: float, comissao_pct: float,
                          deducao_pct: float = 0.0) -> dict:
    """
    deducao_pct: percentual de deduções sobre a comissão bruta (impostos retidos +
    tarifas administrativas + taxa de cartão, cláusula 3.1 dos Termos). Os Termos não
    especificam o percentual exato — preencher com o valor real observado nos extratos.
    """
    custo_total_ads = cpc * cliques
    vendas_estimadas = cliques * (taxa_conversao / 100.0)
    receita_comissao_bruta = vendas_estimadas * valor_medio_produto * (comissao_pct / 100.0)
    receita_comissao_liquida = receita_comissao_bruta * (1 - deducao_pct / 100.0)
    lucro_liquido = receita_comissao_liquida - custo_total_ads
    roi = (lucro_liquido / custo_total_ads * 100) if custo_total_ads > 0 else 0.0

    return {
        "custo_ads_brl": round(custo_total_ads, 2),
        "vendas_estimadas": round(vendas_estimadas, 1),
        "comissao_bruta_brl": round(receita_comissao_bruta, 2),
        "comissao_liquida_brl": round(receita_comissao_liquida, 2),
        "lucro_liquido_brl": round(lucro_liquido, 2),
        "roi_pct": round(roi, 2)
    }
