"""Integração: o prompt derivado da matéria chega ao generation_request."""
from mkt_flow_p0.image_protocol import plan_image


def test_prompt_da_materia_chega_no_generation_request():
    artigo = {
        "titulo": "iPhone ganha teclado físico",
        "meta_description": "Decisão cautelar dá 24 horas.",
        "conteudo_markdown": "<p>Bloqueio de telemarketing abusivo pela TIM.</p>",
        "fontes": ["https://tecnoblog.net/exemplo"],
    }
    # Título com match no catálogo + content_fit INCONGRUENT => generation_request
    out = plan_image(
        "iPhone ganha teclado físico", offline=True,
        content_fit="INCONGRUENT", artigo=artigo)
    assert out["status"] == "AI_GENERATION_REQUIRED"
    gen = out["generation_request"]
    assert "iPhone ganha teclado físico" in gen["prompt"]
    assert gen["base_do_artigo"]["titulo"] == "iPhone ganha teclado físico"
    assert "sem_fatos_inventados" in gen["constraints"]


def test_sem_artigo_usa_prompt_generico():
    out = plan_image(
        "iPhone ganha teclado físico", offline=True, content_fit="INCONGRUENT")
    gen = out["generation_request"]
    assert "Create a relevant editorial image" in gen["prompt"]
    assert gen["base_do_artigo"]["temas_detectados"] == []
