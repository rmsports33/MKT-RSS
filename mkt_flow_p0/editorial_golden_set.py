"""Padrão vivo de qualidade editorial.

Artigos com nota humana alta e fatos conferidos viram referência de ESTRUTURA
por gênero. O texto do artigo nunca é copiado para o prompt: só características
(abertura, seções, movimentos, evidência, veredito).
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from mkt_flow_p0.editorial_quality_score import carregar_contrato, padrao_canaltech

SCHEMA = "conexo-editorial-golden-set/1"
LIMITE_PROVISORIO = 70
MAX_POR_GENERO = 3


def _caminho():
    return Path(os.getenv("CONEXO_GOLDEN_SET_PATH") or
                (Path(__file__).resolve().parent.parent / "data" / "editorial_golden_set.json"))


def _novo():
    return {"schema": SCHEMA, "contract_sha256": carregar_contrato()["contract_sha256"],
            "limite_nota_humana": None, "generos": {}}


def carregar():
    caminho = _caminho()
    if not caminho.exists():
        return _novo()
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    if dados.get("schema") != SCHEMA:
        raise ValueError("GOLDEN_SET_SCHEMA_INVALIDO")
    if dados.get("contract_sha256") != carregar_contrato()["contract_sha256"]:
        raise ValueError("GOLDEN_SET_CONTRATO_DESATUALIZADO")
    return dados


def salvar(dados):
    caminho = _caminho()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = Path(tempfile.gettempdir()) / ("golden-" + hashlib.sha256(
        str(caminho).encode("utf-8")).hexdigest()[:12] + ".json")
    temporario.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
    os.replace(temporario, caminho)
    try:
        os.chmod(caminho, 0o600)
    except OSError:
        pass
    return caminho


def _caracteristicas(markdown, genero, nota_humana, nota_assistida, artigo_id):
    titulos = [l.strip().lstrip("#").strip()
               for l in str(markdown).splitlines() if l.lstrip().startswith("#")]
    corpo = str(markdown)
    primeira = next((p.strip() for p in corpo.split("\n\n") if p.strip()), "")
    tipo_abertura = ("pergunta" if "?" in primeira[:220] else
                     "tese" if any(x in primeira[:220].casefold()
                                   for x in ("depende", "mas", "porém", "contudo")) else "dado")
    padrao = padrao_canaltech(corpo)
    return {
        "artigo_id": str(artigo_id),
        "genero": genero,
        "content_sha256": hashlib.sha256(corpo.encode("utf-8")).hexdigest(),
        "nota_humana": int(nota_humana),
        "nota_assistida": int(nota_assistida),
        "tipo_abertura": tipo_abertura,
        "quantidade_secoes": len(titulos),
        "secoes_por_funcao": [t[:70] for t in titulos[:8]],
        "movimentos_canaltech": padrao["checagens"],
        "cobertura_canaltech": padrao["cobertura"],
        "registrado_em": datetime.now(timezone.utc).isoformat(),
        "aprovado_por_humano": True,
        "fato_conferido": True,
    }


def registrar(markdown, *, genero, nota_humana, nota_assistida, artigo_id,
              aprovado_por_humano=False, fato_conferido=False):
    """Só registra com nota humana, aprovação e conferência fatorial explícitas."""
    if not isinstance(nota_humana, int) or not 0 <= nota_humana <= 100:
        raise ValueError("NOTA_HUMANA_INVALIDA")
    if not aprovado_por_humano or not fato_conferido:
        raise ValueError("PADRAO_EXIGE_APROVACAO_E_FATO")
    dados = carregar()
    limite = dados.get("limite_nota_humana") or LIMITE_PROVISORIO
    if nota_humana < limite:
        raise ValueError("NOTA_ABAIXO_DO_LIMITE")
    caracteristicas = _caracteristicas(markdown, genero, nota_humana, nota_assistida, artigo_id)
    lista = dados["generos"].setdefault(genero, [])
    lista[:] = [item for item in lista if item["content_sha256"] != caracteristicas["content_sha256"]]
    lista.append(caracteristicas)
    lista.sort(key=lambda item: (item["nota_humana"], item["cobertura_canaltech"]), reverse=True)
    del lista[MAX_POR_GENERO:]
    salvar(dados)
    return caracteristicas


def selecionar(genero):
    dados = carregar()
    lista = dados["generos"].get(genero) or []
    return lista[0] if lista else None


def bloco_prompt(genero):
    """Descritores de forma; nunca trecho do artigo original."""
    padrao = selecionar(genero)
    if not padrao:
        return ""
    movimentos = [nome for nome, ok in padrao["movimentos_canaltech"].items() if ok]
    return (
        "\nPADRÃO EDITORIAL DE ALTA NOTA (estrutura apenas; não copiar frases do artigo de referência):\n"
        f"Gênero: {padrao['genero']}; nota humana {padrao['nota_humana']}/100.\n"
        f"Abertura observada: {padrao['tipo_abertura']}.\n"
        f"Seções observadas (função, não texto): {', '.join(padrao['secoes_por_funcao'][:6])}.\n"
        f"Movimentos presentes: {', '.join(movimentos)}.\n"
        "Evidência com procedência explícita e veredito condicionado aos fatos.\n"
    )


def resumo():
    dados = carregar()
    return {"schema": SCHEMA, "contrato": dados["contract_sha256"],
            "limite": dados.get("limite_nota_humana") or LIMITE_PROVISORIO,
            "por_genero": {g: len(v) for g, v in dados["generos"].items()}}
