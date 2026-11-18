"""Fronteira de escrita: so o transporte canonico pode POSTar em wp/v2/posts.

Qualquer novo modulo que tente escrever diretamente no WordPress deve entrar
na allowlist explicita com justificativa. Isso impede que um agente (pago ou
gratuito) crie um atalho de geracao fora do motor editorial.
"""
import pathlib
import re

import pytest

RAIZ = pathlib.Path(__file__).resolve().parents[1]

# Unicos lugares autorizados a enviar POST para /wp/v2/posts.
PERMITIDOS = frozenset({
    "mkt_flow_p0/editorial_transport.py",
    "mkt_flow_p0/editorial_broker_transport.py",
    "mkt_flow_p0/wp_draft_staging.py",
})

PADRAO_POST = re.compile(
    r"requests\.post|\.post\(|method\s*=\s*['\"]POST['\"]|urlopen\([^\n]*data\s*=",
    re.I,
)


def _arquivos():
    pastas = ("mkt_flow_p0", "tools", "scripts")
    for pasta in pastas:
        base = RAIZ / pasta
        if not base.is_dir():
            continue
        for arquivo in base.rglob("*.py"):
            yield arquivo


@pytest.mark.parametrize("arquivo", sorted(_arquivos()), ids=lambda p: str(p.relative_to(RAIZ)))
def test_nenhum_modulo_fora_da_allowlist_escreve_no_wordpress(arquivo):
    relativo = arquivo.relative_to(RAIZ).as_posix()
    texto = arquivo.read_text(encoding="utf-8", errors="replace")
    if "wp/v2/posts" not in texto:
        return
    if relativo in PERMITIDOS:
        return
    assert not PADRAO_POST.search(texto), (
        f"{relativo}: escrita direta em wp/v2/posts fora do transporte canonico"
    )


def test_regra_de_proveniencia_esta_no_contrato_do_repositorio():
    """A regra deve viver em arquivo versionado, nao so em memoria da IA."""
    candidatos = (
        RAIZ / "AGENTS.md",
        RAIZ / "docs" / "EDITORIAL_ORCHESTRATION_GATE_20261110.md",
    )
    textos = [p.read_text(encoding="utf-8", errors="replace")
              for p in candidatos if p.is_file()]
    assert textos, "contrato editorial versionado ausente"
    assert any("Gate" in t or "gate" in t for t in textos)
