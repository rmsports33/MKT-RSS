"""Transferência supervisionada de evidências para ChatGPT Work/Codex, sem API.

Não executa modelos, não autentica fontes e não concede autorização WordPress.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from mkt_flow_p0.contrato_evidencias_noticia import avaliar_evidencias
from mkt_flow_p0.lastro_offline_noticia import auditar_lastro_offline
from mkt_flow_p0.gate_editorial_pos_ia import validar_saida


def _canonical(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def preparar_pacote(contrato, capturas):
    """Somente evidências previamente verificadas podem integrar a transferência."""
    if avaliar_evidencias(contrato).get("veredito") != "EVIDENCIAS_ESTRUTURADAS":
        raise ValueError("Contrato editorial não aprovado")
    if auditar_lastro_offline(contrato, capturas).get("veredito") != "LASTRO_LITERAL":
        raise ValueError("Capturas sem lastro literal")
    payload = {"schema": "conexo-work-handoff/1", "contrato": contrato,
               "capturas": capturas}
    digest = hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()
    return {"payload": payload, "sha256": digest,
            "instructions": ("Redija em PT-BR com voz inteligente e acessível. "
                             "Use somente os trechos e URLs fornecidos. "
                             "Não invente preços, testes, datas ou especificações. "
                             "Devolva apenas JSON: {texto_markdown: string}. "
                             "Isto é uma prévia; não publique nem acesse WordPress.")}


def avaliar_retorno(pacote, resposta):
    """Analisa retorno colado/exportado do Work. Falha fechado em todos os casos."""
    try:
        payload = pacote["payload"]
        digest = hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()
        if digest != pacote["sha256"]:
            raise ValueError("digest divergente")
        contrato, capturas = payload["contrato"], payload["capturas"]
        if avaliar_evidencias(contrato).get("veredito") != "EVIDENCIAS_ESTRUTURADAS":
            raise ValueError("contrato inválido")
        if auditar_lastro_offline(contrato, capturas).get("veredito") != "LASTRO_LITERAL":
            raise ValueError("capturas inválidas")
        texto = resposta["texto_markdown"]
        if not isinstance(texto, str) or not texto.strip():
            raise ValueError("texto vazio")
        from mkt_flow_p0.auditoria_cobertura_pos_ia import auditar_cobertura_pos_ia
        cobertura = auditar_cobertura_pos_ia(texto, contrato, capturas)
        corpus = "\n".join(str(v.get("texto", "")) for v in capturas.values())
        alertas = validar_saida(corpus, texto)
        return {"acao": "bloqueado", "escreveu": False,
                "verificacao_factual": "NAO_VERIFICADO",
                "auditoria_cobertura": cobertura, "auditoria_pos_ia": alertas,
                "revisao_humana_pendente": True}
    except (KeyError, TypeError, ValueError, AttributeError) as e:
        return {"acao": "bloqueado", "escreveu": False,
                "verificacao_factual": "NAO_VERIFICADO",
                "auditoria_cobertura": {"veredito": "BLOQUEADO",
                                        "motivos": ["pacote_ou_retorno_invalido"]},
                "revisao_humana_pendente": True}


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("export", "review"))
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--captures", type=Path)
    parser.add_argument("--package", type=Path)
    parser.add_argument("--response", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.mode == "export":
        if not args.contract or not args.captures:
            parser.error("export requer --contract e --captures")
        result = preparar_pacote(json.loads(args.contract.read_text(encoding="utf-8")),
                                 json.loads(args.captures.read_text(encoding="utf-8")))
    else:
        if not args.package or not args.response:
            parser.error("review requer --package e --response")
        result = avaliar_retorno(json.loads(args.package.read_text(encoding="utf-8")),
                                 json.loads(args.response.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
