#!/usr/bin/env python3
"""Preflight Shopee Affiliate API com código MKT-RSS, UMA leitura, sem escrita.

Uso em terminal interativo confiável (não em Actions):
 python scripts/shopee_readonly_preflight.py --item-id 58217601055 --shop-id 728389176

Credenciais são digitadas localmente sem eco, mantidas em RAM só nesta execução.
Não usar --env, flags de CLI nem logs para credenciais.
"""
import argparse
import getpass
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main(argv=None):
    cli = argparse.ArgumentParser(description="Preflight seguro Shopee → MKT-RSS")
    cli.add_argument("--item-id", required=True, help="ID numérico público do produto")
    cli.add_argument("--shop-id", required=True, help="ID numérico público da loja")
    args = cli.parse_args(argv)
    if not (args.item_id.isdecimal() and args.shop_id.isdecimal()):
        print("BLOQUEADO: IDs devem ser numéricos")
        return 2
    if not (sys.stdin.isatty() and sys.stderr.isatty()):
        print("BLOQUEADO: requer terminal interativo (não cole segredos em pipelines)")
        return 2

    # O módulo importa requests, mas NÃO executa rede no import.
    from mkt_flow_p0 import price_collector as pc
    app_id = getpass.getpass("App ID Shopee (não aparece no terminal): ").strip()
    secret = getpass.getpass("Senha API Shopee (não aparece no terminal): ").strip()
    if not app_id.isdecimal() or not secret:
        print("BLOQUEADO: credenciais ausentes ou App ID inválido")
        return 2

    # Atualiza credenciais da instância existente somente em memória, sem .env.
    pc._CREDS.shopee = {"partner_id": app_id, "partner_key": secret}
    del app_id, secret
    try:
        response = pc._coletar_shopee(args.item_id, args.shop_id)
    finally:
        pc._CREDS.shopee = {"partner_id": "", "partner_key": ""}
    if not response:
        print(json.dumps({"resultado":"NAO_HOMOLOGADO",
             "motivo":"sem oferta inequívoca ou consulta rejeitada",
             "item_id":args.item_id,"shop_id":args.shop_id},ensure_ascii=False))
        return 1

    # Apenas campos públicos da oferta, sem header, senha ou token.
    print(json.dumps({
        "resultado":"API_SHOPEE_READBACK_OK",
        "origem":response.get("origem"),"item_id":response.get("item_id"),
        "shop_id":response.get("shop_id"),"produto":response.get("nome"),
        "vendedor":response.get("vendedor"),"preco":response.get("preco"),
        "moeda":response.get("moeda"),"url":response.get("url"),
        "data_captura":response.get("data_captura"),
        "escrita_wordpress":False,"escrita_banco":False,
    },ensure_ascii=False,indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
