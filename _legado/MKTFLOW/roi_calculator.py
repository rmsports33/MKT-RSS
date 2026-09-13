"""MKTFLOW.roi_calculator — ROI clássico (v3.11 congelado).
Núcleo ativo equivalente: mkt_flow_p0.roi (com deducao_pct)."""
import logging

logger = logging.getLogger("mktflow.roi")


def calcular_roi_afiliado(cpc: float, cliques: int, taxa_conversao: float,
                          valor_medio_produto: float, comissao_pct: float,
                          deducao_pct: float = 0.0) -> dict:
    custo = (cpc or 0) * (cliques or 0)
    vendas = (cliques or 0) * ((taxa_conversao or 0) / 100.0)
    bruta = vendas * (valor_medio_produto or 0) * ((comissao_pct or 0) / 100.0)
    liquida = bruta * (1 - (deducao_pct or 0) / 100.0)
    lucro = liquida - custo
    roi = (lucro / custo * 100) if custo > 0 else 0.0
    return {
        "custo_ads_brl": round(custo, 2),
        "vendas_estimadas": round(vendas, 1),
        "comissao_bruta_brl": round(bruta, 2),
        "comissao_liquida_brl": round(liquida, 2),
        "lucro_liquido_brl": round(lucro, 2),
        "roi_pct": round(roi, 2),
    }


def calcular_roi_por_categoria(categoria: str, cpc: float, cliques: int, taxa_conversao: float,
                              valor_medio_produto: float, comissao_pct: float,
                              deducao_pct: float = 0.0) -> dict:
    """Mesmo cálculo, rotulado por categoria (comissão vem de fonte — nunca inventada aqui)."""
    r = calcular_roi_afiliado(cpc, cliques, taxa_conversao, valor_medio_produto, comissao_pct, deducao_pct)
    r["categoria"] = (categoria or "geral").lower()
    return r
