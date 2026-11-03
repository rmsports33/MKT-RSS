"""
mkt_flow_p0.price_collector — Coleta de preços em marketplaces (M04.17E).

Por que existe: o gate de valor (M04.17D) exige `price_history` com:
  - preço no formato que o gate lê (R$ X.XXX,XX)
  - data de captura válida (DD/MM/AAAA)
  - link do marketplace (fonte verificável)
  - vínculo inequívoco com o produto

Hoje o redator NÃO produz price_history — os coletores dele BLOQUEIAM
marketplaces, e no MKT-RSS o marketplaces.json não é usado por nenhum .py.

Mercado Livre: cliente mínimo com access token OAuth autorizado.
Amazon e Shopee: indisponíveis; sem coleta ou fallback para scraping.
Persistência exige opt-in por chamada. Sem credenciais não há HTTP.
"""
import os
import json
import time
import hashlib
import logging
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, urlsplit
import re

import requests

logger = logging.getLogger("price_collector")

# --- Configuração de credenciais (lidas uma vez) ---------------------------

class _Credenciais:
    """Carrega credenciais do ambiente uma única vez."""
    
    def __init__(self):
        self.amazon = {
            "access_key": os.getenv("AMAZON_PA_API_ACCESS_KEY", "").strip(),
            "secret_key": os.getenv("AMAZON_PA_API_SECRET_KEY", "").strip(),
            "associate_tag": os.getenv("AMAZON_PA_API_ASSOCIATE_TAG", "").strip(),
            "region": os.getenv("AMAZON_PA_API_REGION", "BR").strip().upper(),
        }
        self.mercadolivre = {
            "app_id": os.getenv("MERCADOLIVRE_APP_ID", "").strip(),
            "client_secret": os.getenv("MERCADOLIVRE_CLIENT_SECRET", "").strip(),
            "access_token": os.getenv("MERCADOLIVRE_ACCESS_TOKEN", "").strip(),
        }
        self.shopee = {
            "partner_id": os.getenv("SHOPEE_PARTNER_ID", "").strip(),
            "partner_key": os.getenv("SHOPEE_PARTNER_KEY", "").strip(),
        }
    
    def tem_amazon(self) -> bool:
        return all(self.amazon.values())
    
    def tem_mercadolivre(self) -> bool:
        return bool(self.mercadolivre["access_token"])
    
    def tem_shopee(self) -> bool:
        return all(self.shopee.values())
    
    def marketplaces_disponiveis(self) -> list[str]:
        disp = []
        if self.tem_mercadolivre(): disp.append("mercadolivre")
        return disp


_CREDS = _Credenciais()


def _tem_credencial(marketplace: str) -> bool:
    return getattr(_CREDS, f"tem_{marketplace.lower()}")()


# --- Normalizadores ---------------------------------------------------------

def normalizar_preco(valor) -> str:
    """1500.5 -> 'R$ 1.500,50'; '1.600,00' -> 'R$ 1.600,00'; inválido -> ''."""
    if valor is None or isinstance(valor, bool):
        return ""
    texto = str(valor).strip().removeprefix("R$").strip()
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    try:
        valor_decimal = Decimal(texto)
        if not valor_decimal.is_finite() or not 0 < valor_decimal <= Decimal("1000000000"):
            return ""
        return "R$ " + f"{valor_decimal:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ArithmeticError, ValueError):
        return ""


def normalizar_data_captura(valor) -> str:
    """'2026-09-01' -> '01/09/2026'. Data inexistente -> ''."""
    texto = str(valor or "").strip()
    if not texto:
        return ""
    texto = texto.split("T")[0].split(" ")[0]
    for formato in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(texto, formato).strftime("%d/%m/%Y")
        except ValueError:
            continue
    return ""


def _eh_url(valor) -> bool:
    """Rejeita URL sem HTTPS, host, caminho ou com credenciais embutidas."""
    try:
        parsed = urlsplit(valor if isinstance(valor, str) else "")
        return (parsed.scheme == "https" and bool(parsed.hostname)
                and not parsed.username and not parsed.password
                and parsed.port in (None, 443) and parsed.path not in ("", "/"))
    except ValueError:
        return False


def _eh_url_mercadolivre(valor) -> bool:
    """Não confia apenas no transporte injetado para validar a origem."""
    return (_eh_url(valor) and urlsplit(valor).hostname in {
        "mercadolivre.com.br", "www.mercadolivre.com.br",
        "produto.mercadolivre.com.br",
    })


# --- Persistência local de evidência ----------------------------------------

_DB_PATH = Path(__file__).parent / "price_evidence.sqlite"


def _init_db():
    import sqlite3
    con = sqlite3.connect(_DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS price_evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto TEXT NOT NULL,
            marketplace TEXT NOT NULL,
            preco_br TEXT NOT NULL,
            data_captura TEXT NOT NULL,
            url_oferta TEXT NOT NULL,
            url_canonica TEXT,
            payload_bruto TEXT,
            hash_evidencia TEXT NOT NULL,
            coletado_em TEXT NOT NULL,
            UNIQUE(produto, marketplace, hash_evidencia)
        )
    """)
    con.commit()
    con.close()


def _salvar_evidencia(
    produto: str,
    marketplace: str,
    preco_br: str,
    data_captura: str,
    url_oferta: str,
    payload_bruto: dict,
) -> bool:
    """Salva evidência no SQLite local. Retorna True se inseriu (não duplicado)."""
    import sqlite3
    _init_db()
    # Hash do conteúdo para deduplicação exata
    conteudo = f"{produto}|{marketplace}|{preco_br}|{data_captura}|{url_oferta}"
    hash_ev = hashlib.sha256(conteudo.encode("utf-8")).hexdigest()[:16]
    
    con = sqlite3.connect(_DB_PATH)
    try:
        con.execute("""
            INSERT INTO price_evidence (produto, marketplace, preco_br, data_captura,
                                        url_oferta, url_canonica, payload_bruto, hash_evidencia, coletado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            produto, marketplace, preco_br, data_captura,
            url_oferta, urlparse(url_oferta).netloc if _eh_url(url_oferta) else "",
            json.dumps({k: payload_bruto[k] for k in ("marketplace", "item_id", "data_captura") if k in payload_bruto}, ensure_ascii=False),
            hash_ev,
            datetime.now().isoformat(timespec="seconds"),
        ))
        con.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        con.close()


# --- Coletores por marketplace ----------------------------------------------

def _coletar_amazon(asin: str) -> Optional[dict]:
    """Coleta preço via Amazon PA-API 5.0 (GetItems). Requer credenciais."""
    if not _CREDS.tem_amazon():
        return None
    # TODO: implementar chamada assinada PA-API 5.0 (GetItems)
    # Requer assinatura V4 AWS. Fora do escopo MVP sem credenciais.
    logger.debug("Amazon PA-API não implementada (sem credenciais ou SDK)")
    return None


def _coletar_mercadolivre(item_id: str) -> Optional[dict]:
    """Coleta preço via Mercado Livre API (Items). Requer credenciais."""
    if not _CREDS.tem_mercadolivre():
        return None
    from mkt_flow_p0.price_api_clients import MercadoLivreClient
    return MercadoLivreClient(_CREDS.mercadolivre["access_token"]).get_item(item_id)



def _coletar_shopee(item_id: str, shop_id: str) -> Optional[dict]:
    """Coleta preço via Shopee Affiliate API. Requer credenciais."""
    if not _CREDS.tem_shopee():
        return None
    # TODO: implementar Shopee Affiliate API
    logger.debug("Shopee Affiliate API não implementada (sem credenciais)")
    return None


# --- API pública ------------------------------------------------------------

def coletar_preco_produto(
    nome_produto: str,
    asin: Optional[str] = None,
    ml_item_id: Optional[str] = None,
    shopee_item_id: Optional[str] = None,
    shopee_shop_id: Optional[str] = None,
    *, persistir: bool = False, client=None,
) -> dict:
    """Coleta preço do produto nos marketplaces configurados.
    
    Retorna dict com:
      - ok: bool
      - marketplace: str
      - preco_br: str (formato gate: R$ X.XXX,XX)
      - data_captura: str (DD/MM/AAAA)
      - url_oferta: str
      - marketplace: str
      - erro: str (se ok=False)
    """
    resultados = []
    erros = []
    
    # Amazon
    if asin and _CREDS.tem_amazon():
        r = _coletar_amazon(asin)
        if r:
            resultados.append({"marketplace": "amazon", **r})
        elif r is None:
            erros.append("amazon: credenciais configuradas mas coleta não implementada")
        else:
            erros.append("amazon: falha na coleta")
    elif asin:
        erros.append("amazon: ASIN fornecido mas credenciais não configuradas")
    
    # Mercado Livre
    if ml_item_id and (client is not None or _CREDS.tem_mercadolivre()):
        from mkt_flow_p0.price_api_clients import PriceAPIError
        try:
            r = client.get_item(ml_item_id) if client is not None else _coletar_mercadolivre(ml_item_id)
        except PriceAPIError as erro:
            erros.append("mercadolivre: " + str(erro))
            r = None
        if isinstance(r, dict):
            if (r.get("item_id") != ml_item_id
                    or r.get("marketplace") != "mercadolivre"
                    or not _eh_url_mercadolivre(r.get("url") or r.get("link"))):
                erros.append("mercadolivre: identidade ou fonte nao verificavel")
            else:
                resultados.append({"marketplace": "mercadolivre", **r})
        elif r is None:
            if not erros:
                erros.append("mercadolivre: coleta indisponivel")
        else:
            erros.append("mercadolivre: resposta invalida")
    elif ml_item_id:
        erros.append("mercadolivre: item_id fornecido mas credenciais não configuradas")
    
    # Shopee
    if shopee_item_id and shopee_shop_id and _CREDS.tem_shopee():
        r = _coletar_shopee(shopee_item_id, shopee_shop_id)
        if r:
            resultados.append({"marketplace": "shopee", **r})
        elif r is None:
            erros.append("shopee: credenciais configuradas mas coleta não implementada")
        else:
            erros.append("shopee: falha na coleta")
    elif shopee_item_id or shopee_shop_id:
        erros.append("shopee: IDs fornecidos mas credenciais não configuradas")
    
    if not resultados:
        return {"ok": False, "erros": erros or ["nenhum marketplace configurado com credenciais válidas"]}
    
    # Pega o primeiro resultado válido (melhor preço poderia ser lógica futura)
    r = resultados[0]
    preco_br = normalizar_preco(r.get("preco"))
    data_captura = normalizar_data_captura(r.get("data_captura"))
    url_oferta = r.get("url") or r.get("link") or ""
    
    if not preco_br or not data_captura or not _eh_url(url_oferta):
        return {"ok": False, "erro": "dados insuficientes do marketplace"}
    
    # Persistência opcional: não grava no dry-run padrão.
    payload_bruto = {k: v for k, v in r.items() if k not in ("preco", "data", "url", "link")}
    if persistir:
        _salvar_evidencia(
            produto=nome_produto,
            marketplace=r.get("marketplace", "desconhecido"),
            preco_br=preco_br,
            data_captura=data_captura,
            url_oferta=url_oferta,
            payload_bruto=payload_bruto,
        )
    
    return {
        "ok": True,
        "marketplace": r.get("marketplace"),
        "preco_br": preco_br,
        "data_captura": data_captura,
        "url_oferta": url_oferta,
    }


def auditar_precos_para_comparativo(modelos: list, price_history: dict) -> dict:
    """Valida se o price_history tem evidências suficientes para o gate.
    
    Não faz coleta — apenas valida o que já existe.
    Retorna estrutura compatível com comparativo_flow.auditar_precos.
    """
    # Reusa a lógica do comparativo_flow.auditar_precos
    from mkt_flow_p0.comparativo_flow import auditar_precos
    return auditar_precos(modelos, price_history)


def gerar_price_history_para_modelos(modelos: list, marketplace: str = "mercadolivre", *, persistir=False, client=None) -> dict:
    """Helper para gerar price_history a partir de modelos com ASIN/ML_ID.
    
    Útil para testes e para o redator chamar antes de gerar o comparativo.
    
    Retorna price_history no formato esperado pelo contrato:
    {nome_produto: [{"data": "DD/MM/AAAA", "preco": "X.XXX,XX", "fonte": "url"}]}
    """
    if marketplace not in {"amazon", "mercadolivre", "shopee"}:
        raise ValueError("marketplace desconhecido")
    if marketplace == "mercadolivre" and client is None and _CREDS.tem_mercadolivre():
        from mkt_flow_p0.price_api_clients import MercadoLivreClient
        client = MercadoLivreClient(_CREDS.mercadolivre["access_token"])
    nomes = [str(m.get("nome") or "").strip().casefold() for m in modelos if isinstance(m, dict)]
    if len(nomes) != len(set(nomes)):
        raise ValueError("nomes de produtos duplicados")
    ph = {}
    for modelo in modelos:
        if not isinstance(modelo, dict):
            continue
        nome = (modelo.get("nome") or "").strip()
        if not nome:
            continue
        # Mapeia identificadores
        asin = modelo.get("asin")
        ml_id = modelo.get("ml_item_id") or modelo.get("ml_id")
        shopee_item = modelo.get("shopee_item_id") or modelo.get("shopee_item")
        shopee_shop = modelo.get("shopee_shop_id") or modelo.get("shopee_shop")
        
        r = coletar_preco_produto(nome,
                                  asin=asin if marketplace == "amazon" else None,
                                  ml_item_id=ml_id if marketplace == "mercadolivre" else None,
                                  shopee_item_id=shopee_item if marketplace == "shopee" else None,
                                  shopee_shop_id=shopee_shop if marketplace == "shopee" else None,
                                  persistir=persistir, client=client)
        if r.get("ok"):
            ph[nome] = [{
                "data": r["data_captura"],
                "preco": r["preco_br"].replace("R$ ", ""),  # salva sem R$ no histórico
                "fonte": r["url_oferta"],
            }]
    return ph


# --- CLI --------------------------------------------------------------------

def _main_cli(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="Coleta de preço em marketplaces (M04.17E).")
    ap.add_argument("--produto", required=True, help="Nome do produto")
    ap.add_argument("--asin", help="ASIN Amazon")
    ap.add_argument("--ml-id", dest="ml_id", help="Item ID Mercado Livre")
    ap.add_argument("--shopee-id", dest="shopee_id", help="Item ID Shopee")
    ap.add_argument("--shopee-shop", dest="shopee_shop", help="Shop ID Shopee")
    args = ap.parse_args(argv)
    
    r = coletar_preco_produto(args.produto, asin=args.asin, ml_item_id=args.ml_id,
                              shopee_item_id=args.shopee_id, shopee_shop_id=args.shopee_shop)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    import sys
    sys.exit(_main_cli())
