# -*- coding: utf-8 -*-
"""Auditor adversarial do gate de valor (regra 14) — 21/10/2026, M04.16E.

Por que existe: a suite de testes prova que o codigo novo passa. Nao prova que
o gate BLOQUEIA o que deve bloquear. Este auditor roda a matriz adversaria
contra uma implementacao qualquer e falha se ela aprovar o que nao deve.

Uso:
    python tools/2026-10-21_auditar_gate_valor.py
    python tools/2026-10-21_auditar_gate_valor.py --contra <arquivo content_filter.py>

Exit 0 = todos os casos bateram. Exit 1 = algum caso divergiu.
Exit 2 = a implementacao auditada nao existe/nao carrega.

Disciplina (regra 19, obrigacao 4): antes de confiar num verificador, prove
que ele REPROVA. Rode contra a versao fail-open e veja o exit 1.
"""
import argparse
import importlib.util
import shutil
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def carregar(modulo_caminho: Path):
    """Carrega um content_filter.py de fora da raiz, isolado em tempdir.

    Copia o tema_keywords.json junto porque o modulo o le do proprio diretorio
    (Path(__file__).parent); sem o arquivo ele cai na lista vazia, o que nao
    afeta os casos de valor — e o auditor nao testa o filtro de tema.
    """
    alvo = Path(modulo_caminho).resolve()
    if not alvo.is_file():
        raise FileNotFoundError(str(alvo))
    tempdir = Path(tempfile.mkdtemp(prefix="auditoria_gate_"))
    destino = tempdir / "content_filter.py"
    shutil.copy2(alvo, destino)
    tema = alvo.parent / "tema_keywords.json"
    if tema.is_file():
        shutil.copy2(tema, tempdir / "tema_keywords.json")
    spec = importlib.util.spec_from_file_location("content_filter_auditado", destino)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = modulo
    spec.loader.exec_module(modulo)
    return modulo, tempdir


# (nome, kwargs, assercoes)
# Assercoes sao contratos do gate, nao palpite:
#   "bloqueado"                  -> o veredito tem que ser BLOQUEADO
#   "aprovado"                   -> o veredito tem que ser APROVADO
#   "sem:<criterio>"             -> o criterio NAO pode aparecer
#   "com:<criterio>"             -> o criterio tem que aparecer
#
# DISTINCAO IMPORTANTE (erro do autor deste arquivo em 21/10, corrigido):
# o gate e' ">=1 criterio dos 4". Logo, texto com preco+data e link de
# FABRICANTE tem que ser APROVADO pelo criterio 2 (fonte_primaria) — o que
# nao pode e' o criterio 1 (preco_br_data) ser concedido sem marketplace.
# Asserção "tem que ser BLOQUEADO" nesse cenario seria um FALSO POSITIVO do
# auditor, nao um defeito do gate.
CASOS_ADVERSARIAIS = [
    ("preco sem data + marketplace",
     dict(titulo="Galaxy S26", texto="Sai por R$ 9.999,00.",
          links=["https://www.amazon.com.br/dp/B0XXX"]),
     ["bloqueado", "sem:preco_br_data", "sem:fonte_primaria"]),
    ("data sem preco + marketplace",
     dict(titulo="Galaxy S26", texto="Oferta capturada em 17/09/2026.",
          links=["https://www.amazon.com.br/dp/B0XXX"]),
     ["bloqueado", "sem:preco_br_data"]),
    ("cruzamento declarado com 1 fonte",
     dict(titulo="S26 vs Pixel", texto="Comparamos.",
          links=["https://www.gsmarena.com/x"], tem_cruzamento=True),
     ["bloqueado", "sem:cruzamento_2fontes"]),
    ("preco+data de fonte NAO comercial",
     dict(titulo="Galaxy S26", texto="R$ 9.999,00 em 17/09/2026.",
          links=["https://www.samsung.com/br/produto"]),
     ["sem:preco_br_data", "com:fonte_primaria"]),
    ("data de calendario invalida (31/02/2026)",
     dict(titulo="Galaxy S26", texto="R$ 9.999,00 em 31/02/2026.",
          links=["https://www.amazon.com.br/dp/B0XXX"]),
     ["bloqueado", "sem:preco_br_data"]),
    ("marketplace NAO e' fonte primaria",
     dict(titulo="Oferta", texto="R$ 9.999,00 em 17/09/2026.",
          links=["https://www.amazon.com.br/dp/B0XXX"]),
     ["sem:fonte_primaria", "com:preco_br_data"]),
    ("dominio desconhecido como fonte primaria",
     dict(titulo="Noticia", texto="Sem nada proprio.",
          links=["https://blog-qualquer.example/post"]),
     ["bloqueado", "sem:fonte_primaria"]),
    ("marketplace disfarado",
     dict(titulo="Galaxy S26", texto="R$ 9.999,00 em 17/09/2026.",
          links=["https://amazon.com.br.evil.example/dp/B0XXX"]),
     ["bloqueado", "sem:preco_br_data"]),
    ("fabricante disfarcado",
     dict(titulo="Anuncio", texto="Anunciado hoje.",
          links=["https://samsung.com.evil.example/news/x"]),
     ["bloqueado", "sem:fonte_primaria"]),
    ("tem_video sem evidencia estruturada",
     dict(titulo="Review", texto="Analise.", links=[], tem_video=True),
     ["bloqueado", "sem:video_transcrito"]),
    ("tem_mediacao sem evidencia estruturada",
     dict(titulo="Review", texto="Analise.", links=[], tem_mediacao=True),
     ["bloqueado", "sem:medicao_propria"]),
    ("'testamos' no texto sem prova",
     dict(titulo="Testamos o Galaxy", texto="Testamos por 30 dias. Medimos tudo.",
          links=[]),
     ["bloqueado", "sem:medicao_propria"]),
    ("pdf em dominio desconhecido",
     dict(titulo="Estudo", texto="Sem nada proprio.",
          links=["https://blog-qualquer.example/paper.pdf"]),
     ["bloqueado", "sem:fonte_primaria"]),
    ("cruzamento com 2 URLs do mesmo dominio",
     dict(titulo="S26 vs Pixel", texto="Comparativo.",
          links=["https://www.gsmarena.com/x", "https://m.gsmarena.com/y"],
          tem_cruzamento=True),
     ["bloqueado", "sem:cruzamento_2fontes"]),
    ("video com transcricao curta",
     dict(titulo="Review", texto="Analise.", links=[],
          evidencia_video={"url": "https://youtu.be/abc", "transcricao": "muito bom"}),
     ["bloqueado", "sem:video_transcrito"]),
    ("medicao sem metodo",
     dict(titulo="Review", texto="Analise.", links=[],
          evidencia_medicao={"metodo": "curto",
                             "medicoes": [{"metrica": "a", "valor": 1, "unidade": "h"},
                                          {"metrica": "b", "valor": 2, "unidade": "h"}]}),
     ["bloqueado", "sem:medicao_propria"]),
    ("esquema de URL invalido",
     dict(titulo="Galaxy", texto="R$ 9.999,00 em 17/09/2026.",
          links=["javascript:alert(1)"]),
     ["bloqueado", "sem:preco_br_data"]),
]

CASOS_POSITIVOS = [
    ("preco com data + marketplace",
     dict(titulo="Galaxy S26", texto="R$ 9.999,00 capturado em 17/09/2026.",
          links=["https://www.amazon.com.br/dp/B0XXX"]),
     ["aprovado", "com:preco_br_data"]),
    ("fonte primaria de fabricante",
     dict(titulo="Anthropic lanca modelo", texto="Anunciado hoje.",
          links=["https://www.anthropic.com/news/x"]),
     ["aprovado", "com:fonte_primaria"]),
    ("fonte oficial por formato (.gov.br)",
     dict(titulo="Anatel", texto="Publicado.",
          links=["https://www.gov.br/anatel/pt-br/noticias/x"]),
     ["aprovado", "com:fonte_primaria"]),
    ("medicao propria comprovada",
     dict(titulo="Testamos o Galaxy", texto="Medimos a bateria.",
          links=[],
          evidencia_medicao={"metodo": "Loop de video 4K, brilho 200 nits",
                             "medicoes": [{"metrica": "video4k", "valor": 7.2, "unidade": "h"},
                                          {"metrica": "misto", "valor": 11.4, "unidade": "h"}]}),
     ["aprovado", "com:medicao_propria"]),
    ("video transcrito",
     dict(titulo="Review do Galaxy", texto="Analise.", links=[],
          evidencia_video={"url": "https://www.youtube.com/watch?v=abc123",
                           "transcricao": " ".join(["palavra"] * 80)}),
     ["aprovado", "com:video_transcrito"]),
    ("cruzamento com 2 dominios independentes",
     dict(titulo="S26 vs Pixel", texto="Comparamos.",
          links=["https://www.gsmarena.com/x", "https://www.apple.com/y"],
          tem_cruzamento=True),
     ["aprovado", "com:cruzamento_2fontes"]),
]

# --- M04.17A: evidencia POR PRODUTO ---
# A lacuna estrutural do Issue #9 (2o requisito) era: comparativo de 2
# produtos com preco de UM so passava. Ate M04.16C isso ficava documentado
# aqui como "LACUNA CONHECIDA" e o auditor NAO reprovava por causa dela.
# A partir de M04.17A a lacuna vira CHECK: o auditor reprova se a evidencia
# de um produto aprovar outro.
CASOS_POR_PRODUTO = [
    ("comparativo: preco de um so nao aprova o outro",
     dict(titulo="Galaxy S26 vs Pixel 11",
          texto="O S26 sai por R$ 5.999,00 em 17/09/2026. O Pixel 11 sem preco.",
          produtos=[
              {"nome": "Galaxy S26", "preco": "R$ 5.999,00", "data_captura": "17/09/2026",
               "fonte_preco": "https://www.amazon.com.br/dp/B0XXX"},
              {"nome": "Pixel 11"},
          ]),
     ["bloqueado"]),
    ("comparativo: preco dos dois aprova",
     dict(titulo="Galaxy S26 vs Pixel 11",
          texto="Precos capturados em 17/09/2026.",
          produtos=[
              {"nome": "Galaxy S26", "preco": "R$ 5.999,00", "data_captura": "17/09/2026",
               "fonte_preco": "https://www.amazon.com.br/dp/B0XXX"},
              {"nome": "Pixel 11", "preco": "R$ 4.299,00", "data_captura": "17/09/2026",
               "fonte_preco": "https://www.mercadolivre.com.br/pixel-11/p/MLB123"},
          ]),
     ["aprovado"]),
    ("preco no texto geral nao salva produto sem evidencia",
     dict(titulo="Comparativo",
          texto="Sai por R$ 5.999,00 em 17/09/2026.",
          links=["https://www.amazon.com.br/dp/B0XXX"],
          produtos=[{"nome": "Produto A"}, {"nome": "Produto B"}]),
     ["bloqueado"]),
    ("video de um produto nao aprova o outro",
     dict(titulo="Comparativo", texto="Analisamos os dois.",
          produtos=[
              {"nome": "Produto A",
               "evidencia_video": {"url": "https://www.youtube.com/watch?v=abc123",
                                    "transcricao": " ".join(["palavra"] * 80)}},
              {"nome": "Produto B"},
          ]),
     ["bloqueado"]),
    ("exigir produtos sem lista bloqueia",
     dict(titulo="Comparativo", texto="x", exigir_produtos=True),
     ["bloqueado"]),
]


def rodar(módulo, casos, titulo_bloco):
    falhas = []
    print(f"\n{titulo_bloco}")
    for nome, kwargs, assercoes in casos:
        try:
            r = módulo.filtrar_valor_acrescentado(**kwargs)
            veredito = r.get("veredito")
            criterios = r.get("criterios") or []
        except Exception as erro:  # noqa: BLE001 - o auditor nao pode quebrar
            print(f"  ERRO   {nome}: {erro}")
            falhas.append(nome)
            continue
        problemas = []
        for assercao in assercoes:
            if assercao == "bloqueado":
                if veredito != "BLOQUEADO":
                    problemas.append(f"veredito={veredito} (esperado BLOQUEADO)")
            elif assercao == "aprovado":
                if veredito != "APROVADO":
                    problemas.append(f"veredito={veredito} (esperado APROVADO)")
            elif assercao.startswith("sem:"):
                criterio = assercao[4:]
                if criterio in criterios:
                    problemas.append(f"criterio '{criterio}' concedido (nao devia)")
            elif assercao.startswith("com:"):
                criterio = assercao[4:]
                if criterio not in criterios:
                    problemas.append(f"criterio '{criterio}' ausente (devia estar)")
            else:
                problemas.append(f"assercao desconhecida: {assercao}")
        if problemas:
            falhas.append(nome)
        marca = "OK   " if not problemas else "FALHA"
        extra = f" criterios={criterios}" if criterios else ""
        detalhe = "" if not problemas else " | " + "; ".join(problemas)
        print(f"  {marca} {nome}: {veredito} (esperado {assercoes[0]}){extra}{detalhe}")
    return falhas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--contra", default=str(RAIZ / "mkt_flow_p0" / "content_filter.py"),
                    help="content_filter.py a auditar")
    args = ap.parse_args()

    print(f"AUDITOR ADVERSARIAL DO GATE DE VALOR")
    print(f"implementacao: {args.contra}")
    try:
        modulo, tempdir = carregar(Path(args.contra))
    except FileNotFoundError:
        print(f"ERRO: implementacao nao encontrada: {args.contra}")
        return 2
    except Exception as erro:  # noqa: BLE001
        print(f"ERRO: nao foi possivel carregar a implementacao: {erro}")
        return 2

    try:
        falhas = rodar(modulo, CASOS_ADVERSARIAIS, "ADVERSARIAIS (tem que BLOQUEAR)")
        falhas += rodar(modulo, CASOS_POSITIVOS, "POSITIVOS (tem que APROVAR)")
        falhas += rodar(modulo, CASOS_POR_PRODUTO, "POR PRODUTO (M04.17A)")

        print()
        if falhas:
            print(f"RESULTADO: FALHOU — {len(falhas)} caso(s) divergiu(ram):")
            for f in falhas:
                print(f"  - {f}")
            return 1
        print("RESULTADO: PASSOU — gate falha fechado nos casos adversariais "
              "e aprova os controles positivos")
        return 0
    finally:
        shutil.rmtree(tempdir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
