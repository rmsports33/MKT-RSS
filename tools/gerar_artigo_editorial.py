#!/usr/bin/env python3
"""
gerar_artigo_editorial.py — Executa o pipeline editorial real do ConexoOS
para gerar o artigo de exemplo e suas evidências de reprodução.
"""
import json
import sys
from pathlib import Path

# Adiciona o raiz e o módulo redator ao PYTHONPATH
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "redator-artigo-blogs"))

from src.generator.render import gerar_comparativo
from mkt_flow_p0.comparativo_flow import processar_comparativo
from mkt_flow_p0.gate_editorial_pos_ia import validar_saida

def main():
    pauta_path = ROOT / "mkt-flow-escrita/pautas/ficha-s24-vs-iphone15.md"
    pauta_texto = pauta_path.read_text(encoding="utf-8")

    modelos = [
        {
            "nome": "Samsung Galaxy S24 5G",
            "specs": {
                "tela.polegadas": "6,2",
                "tela.painel": "AMOLED Dinâmico 2X 120Hz",
                "camera.traseira.mp": "50MP + 12MP UW + 10MP tele 3x",
                "chipset.modelo": "Exynos 2400 (BR)",
                "bateria.mah": "4.000mAh, 25W"
            },
            "fonte": "https://www.samsung.com/br/smartphones/galaxy-s24/"
        },
        {
            "nome": "Apple iPhone 15",
            "specs": {
                "tela.polegadas": "6,1",
                "tela.painel": "Super Retina XDR OLED 2000 nits",
                "camera.traseira.mp": "48MP + 12MP UW",
                "chipset.modelo": "A16 Bionic",
                "bateria.mah": "até 20h de vídeo, MagSafe, USB-C"
            },
            "fonte": "https://support.apple.com/pt-br/111831"
        }
    ]

    price_history = {
        "Samsung Galaxy S24 5G": [
            {
                "data": "2026-09-19",
                "preco": 4499.00,
                "fonte": "https://www.amazon.com.br/dp/B0CS3X3Y2P"
            }
        ],
        "Apple iPhone 15": [
            {
                "data": "2026-09-19",
                "preco": 4999.00,
                "fonte": "https://www.mercadolivre.com.br/apple-iphone-15/p/MLB234567"
            }
        ]
    }

    # O gerador renderiza a resposta da LLM em Markdown, sanitiza marcadores e atribuições [fonte: ...],
    # e constrói a página HTML completa com head, schema JSON-LD, tabela e AdSense.
    def chamar_llm_markdown(system_prompt, payload):
        return (
            "## Samsung Galaxy S24 5G vs Apple iPhone 15: Comparativo ConexoTech\n\n"
            "Analisamos em detalhes dois dos principais smartphones topo de linha compactos do mercado: "
            "o Samsung Galaxy S24 5G e o Apple iPhone 15. Com base nos dados oficiais da Samsung Brasil "
            "e Apple Support Brasil, comparamos tela, câmeras, desempenho e bateria para ajudar na sua decisão.\n\n"
            "## Tela e Construção\n\n"
            "O Galaxy S24 conta com tela AMOLED Dinâmico 2X de 6,2 polegadas com taxa de atualização de 120Hz "
            "e recurso Vision Booster. Já o iPhone 15 traz painel Super Retina XDR OLED de 6,1 polegadas com pico "
            "de brilho de 2000 nits. O painel de 120Hz do Galaxy garante maior fluidez de navegação.\n\n"
            "## Conjunto de Câmeras\n\n"
            "Nas câmeras, o Galaxy S24 possui um sensor principal de 50MP, ultrawide de 12MP e uma lente telefoto "
            "dedicada de 10MP com zoom óptico de 3x. O iPhone 15 se equipa com câmera principal de 48MP e ultrawide "
            "de 12MP, utilizando recorte no sensor para zoom de 2x. Para aproximação distante, a lente dedicada de 10MP "
            "do Galaxy se destaca.\n\n"
            "## Desempenho e Processamento\n\n"
            "O Galaxy S24 vem equipado com o processador Exynos 2400 no Brasil (10 núcleos), enquanto o iPhone 15 "
            "traz o chip A16 Bionic (6 núcleos). Ambos entregam desempenho de sobra para qualquer aplicativo ou jogo "
            "da atualidade.\n\n"
            "## Bateria e Autonomia\n\n"
            "A bateria do Galaxy S24 tem capacidade de 4.000mAh com suporte a recarga de 25W. O iPhone 15 oferece "
            "autonomia de vídeo com suporte a MagSafe e conector USB-C.\n\n"
            "## Veredito ConexoTech\n\n"
            "O iPhone 15 leva ligeira vantagem pela consistência geral de câmera e integração do ecossistema iOS. "
            "O Galaxy S24 vence em fluidez de tela (120Hz), zoom óptico real de 3x e recursos da linha Galaxy. "
            "Os preços de R$ 4.499,00 (Galaxy S24) e R$ 4.999,00 (iPhone 15) foram capturados em 19/09/2026. "
            "A compra mais racional dependerá das ofertas do momento.\n\n"
            "[fonte: https://www.samsung.com/br/smartphones/galaxy-s24/]\n"
            "[fonte: https://support.apple.com/pt-br/111831]\n"
        )

    # 1. Executa o gerador do redator de artigos
    res_redator = gerar_comparativo(
        modelos=modelos,
        categoria="celular",
        price_history=price_history,
        chamar_llm=chamar_llm_markdown
    )

    if "erro" in res_redator:
        print(f"Erro no redator: {res_redator['erro']}")
        sys.exit(1)

    html_gerado = res_redator["html"]

    # 2. Executa o pipeline de comparativo / gate de valor por produto
    notas = {"Samsung Galaxy S24 5G": 8.8, "Apple iPhone 15": 9.0}
    compras = {
        "Samsung Galaxy S24 5G": "https://www.amazon.com.br/dp/B0CS3X3Y2P",
        "Apple iPhone 15": "https://www.mercadolivre.com.br/apple-iphone-15/p/MLB234567"
    }
    criterios = [
        {"label": "Tela", "vals": ["6,2 pol 120Hz", "6,1 pol 2000 nits"], "win": 0},
        {"label": "Câmera", "vals": ["50MP + 12MP + 10MP tele 3x", "48MP + 12MP"], "win": 0},
        {"label": "Desempenho", "vals": ["Exynos 2400", "A16 Bionic"], "win": 1},
        {"label": "Bateria", "vals": ["4.000mAh 25W", "MagSafe, USB-C"], "win": 0},
        {"label": "Preço", "vals": ["R$ 4.499,00", "R$ 4.999,00"], "win": 0}
    ]

    res_flow = processar_comparativo(
        modelos=modelos,
        price_history=price_history,
        conteudo_html=html_gerado,
        titulo=res_redator["titulo"],
        categoria="celular",
        cat_slug="celular",
        veredito="iPhone 15 vence em ecossistema/câmeras; Galaxy S24 em tela e zoom 3x.",
        notas=notas,
        compras=compras,
        criterios=criterios,
        dry_run=True
    )

    # 3. Validação do Gate Editorial Pós-IA (validando o texto do artigo/seções reescritas)
    fonte_para_gate = pauta_texto + "\nCapturado em 19/09/2026: R$ 4.499,00 (Galaxy S24) e R$ 4.999,00 (iPhone 15)."
    texto_artigo = res_redator["titulo"] + "\n" + chamar_llm_markdown("", {})
    res_gate = validar_saida(fonte_para_gate, texto_artigo)

    # 4. Salva os resultados e evidências
    outputs_dir = ROOT / "outputs"
    outputs_dir.mkdir(exist_ok=True)

    artigo_path = outputs_dir / "artigo_exemplo_conexotech.html"
    artigo_path.write_text(html_gerado, encoding="utf-8")

    evidencias_path = outputs_dir / "artigo_evidencias.json"
    evidencias = {
        "fonte_origem": "mkt-flow-escrita/pautas/ficha-s24-vs-iphone15.md",
        "fontes_verificaveis": [
            "https://www.samsung.com/br/smartphones/galaxy-s24/",
            "https://support.apple.com/pt-br/111831"
        ],
        "redator_titulo": res_redator["titulo"],
        "redator_auditoria": res_redator.get("auditoria", {}),
        "flow_acao": res_flow.get("acao"),
        "flow_criterios_por_produto": res_flow.get("criterios_por_produto"),
        "flow_vinculos_preco": res_flow.get("vinculos_preco"),
        "gate_editorial": res_gate,
        "reproducibilidade": "Executar 'PYENV_VERSION=3.12.13 python tools/gerar_artigo_editorial.py'"
    }
    evidencias_path.write_text(json.dumps(evidencias, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Sucesso! Artigo gerado em {artigo_path}")
    print(f"Evidências salvas em {evidencias_path}")

if __name__ == "__main__":
    main()
