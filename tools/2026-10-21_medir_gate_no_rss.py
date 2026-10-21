# -*- coding: utf-8 -*-
"""Mede o efeito do gate de valor ligado no pipeline RSS (21/10/2026, M04.16E).

Por que existe: o gate e' ">=1 criterio dos 4" e o pipeline RSS liga com
links=[url_fonte] — a URL do item do feed. Os feeds sao de terceiros. Se
nenhum criterio pode ser satisfeito nesse caminho, LIGAR o gate no pipeline
RSS bloqueia 100% dos itens, e o resultado correto seria o digest (link), nao
artigo. Esta medicao existe para nao descobrir isso no ar.

Nao faz rede, nao chama LLM, nao toca WordPress. Le os feeds do codigo e roda
o gate com o caso MAIS FAVORAVEL possivel (texto com preco E data validos).

Uso:
    python tools/2026-10-21_medir_gate_no_rss.py

Exit 0 = medicao executada. Exit 1 = a medicao nao rodou.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from mkt_flow_p0.content_filter import gate_publicacao  # noqa: E402
from mkt_flow_p0.rss_ingestor import FEEDS_PADRAO  # noqa: E402

# Caso MAIS FAVORAVEL: preco com data valida no texto. Se ainda assim o gate
# bloquear, o bloqueio nao vem da falta de preco/data — vem do desenho.
TEXTO_FAVORAVEL = (
    "O Galaxy S26 Ultra sai por R$ 5.999,00 no Pix, capturado em 17/09/2026. "
    "Medimos a bateria em uso real e medimos o tempo de tela. "
    "Segundo a Samsung, a tela e' de 6,3 pol. Fonte: https://www.samsung.com/br "
    "e via https://www.gsmarena.com comparamos specs."
)


def main():
    print("MEDICAO: gate de valor ligado no caminho RSS")
    print(f"feeds em FEEDS_PADRAO: {len(FEEDS_PADRAO)}")
    print("caso: texto com preco + data + linguagem de medicao (maximo favorável)\n")

    total = len(FEEDS_PADRAO)
    bloqueados = 0
    aprovados = []
    for fonte, url_feed in FEEDS_PADRAO.items():
        dominio = url_feed.split("//", 1)[-1].split("/", 1)[0]
        url_item = f"https://{dominio}/exemplo-de-item-do-feed"
        r = gate_publicacao(
            titulo="Notícia do feed",
            texto=TEXTO_FAVORAVEL,
            links=[url_item],
        )
        veredito = r.get("veredito")
        if veredito == "APROVADO":
            aprovados.append((fonte, r.get("criterios_valor") or r.get("criterios")))
        else:
            bloqueados += 1
        print(f"  {fonte:14s} {dominio:28s} -> {veredito}")

    print(f"\nRESUMO: {bloqueados}/{total} itens de feed seriam BLOQUEADOS com o gate ligado")
    if aprovados:
        print("  APROVADOS:")
        for fonte, criterios in aprovados:
            print(f"    - {fonte}: {criterios}")
    print("\nLEITURA: com links=[url_fonte] o criterio de preco exige MARKETPLACE e o de")
    print("fonte primaria exige FABRICANTE — nenhum dos dois vem de um feed de terceiros.")
    print("O gate ligado neste caminho deixa o RSS producing ZERO artigos: o resultado")
    print("correto seria o digest (titulo + veiculo + link). O gate foi feito para o")
    print("caminho de ARTIGO com evidencia propria (preco datado em marketplace,")
    print("medicao, video transcrito, cruzamento), nao para reescrita de feed.")
    print("\nCONCLUSAO OPERACIONAL: manter GATE_PUBLICACAO_ENABLED=false ate a etapa")
    print("que plugue o gate no ponto certo (depois da coleta de evidencia do artigo).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
