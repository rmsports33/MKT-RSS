"""Constrói um prompt de geração de imagem a partir da matéria real do artigo.

O prompt é derivado do conteúdo do MKT-RSS — não de palavras-chave soltas —
para evitar imagens visualmente enganosas. Respeita o protocolo de direitos:
não inventa marcas, logs, interfaces ou fatos que não estejam no texto.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit


# Temas visuais seguros, por palavras presentes na matéria (pt-BR).
_TEMAS = (
    ("telemarketing", "Um smartphone tocando, com sugestão visual de chamada indesejada; sem marca, sem logo, sem texto na imagem."),
    ("patente", "Documentos e silhuetas de aparelhos sobre uma mesa, simbolizando disputa legal tecnológica; sem logos."),
    ("bateria", "Um aparelho com indicação visual de carga em ambiente neutro; sem marcas."),
    ("inteligencia artificial", "Abstração geométrica de redes e fluxos de dados, cores sóbrias, sem rostos ou marcas."),
    ("governo", "Prédio institucional genérico e documento oficial sem brasão, sem símbolos oficiais."),
    ("preco", "Etiquetas de preço genéricas e um produto sem marca em fundo neutro."),
    ("tv", "Televisão moderna sem marca em sala neutra, com imagem abstrata na tela."),
    ("celular", "Smartphone genérico sem marca, em fundo neutro, sem interface falsa."),
    ("seguranca", "Cadeado digital abstrato e camadas de proteção, estilo editorial, sem marcas."),
)


def _texto_do_artigo(artigo: dict) -> str:
    partes = []
    for chave in ("titulo", "subtitulo", "titulo_seo", "meta_description"):
        valor = artigo.get(chave)
        if isinstance(valor, str):
            partes.append(valor)
    corpo = artigo.get("conteudo_markdown") or artigo.get("content") or ""
    if isinstance(corpo, dict):
        corpo = corpo.get("raw") or corpo.get("rendered") or ""
    if isinstance(corpo, str):
        # Remove HTML para extrair apenas o texto da matéria.
        partes.append(re.sub(r"<[^>]+>", " ", corpo))
    return " ".join(partes)


def _temas(texto: str) -> list[str]:
    baixo = texto.lower()
    encontrados = []
    for termo, descricao in _TEMAS:
        if termo in baixo and descricao not in encontrados:
            encontrados.append(f"{termo}: {descricao}")
        if len(encontrados) >= 2:
            break
    return encontrados


def construir_prompt_imagem(artigo: dict, *, idioma: str = "português") -> dict:
    """Devolve {prompt, base_do_artigo, fontes} pronto para a ferramenta de imagem."""
    if not isinstance(artigo, dict):
        raise ValueError("ARTIGO_INVALIDO")

    titulo = (artigo.get("titulo_seo") or artigo.get("titulo") or "").strip()
    subtitulo = (artigo.get("meta_description") or artigo.get("subtitulo") or "").strip()
    if not titulo:
        raise ValueError("ARTIGO_SEM_TITULO")

    texto = _texto_do_artigo(artigo)
    temas = _temas(texto)
    fontes = artigo.get("fontes") or []
    if not isinstance(fontes, list):
        fontes = [fontes]
    fontes_validas = []
    for f in fontes:
        if isinstance(f, str) and f.startswith("https://"):
            fontes_validas.append(f)
        elif isinstance(f, dict):
            u = f.get("url")
            if isinstance(u, str) and u.startswith("https://"):
                fontes_validas.append(u)

    cenario = " ".join(temas) if temas else (
        "Cena editorial abstrata e sóbria relacionada ao tema do artigo, "
        "sem elementos que não possam ser comprovados pelo texto."
    )

    prompt = (
        f"Crie uma imagem de capa editorial em {idioma}, no estilo ConexoTech: "
        f"técnica porém acessível, cores sóbrias com um ponto de destaque, "
        f"composição limpa para miniatura de artigo (proporção 16:9). "
        f"Tema do artigo: {titulo}. "
        f"Contexto: {subtitulo or 'sem subtítulo disponível'}. "
        f"Elementos visuais permitidos pela matéria: {cenario}. "
        f"NÃO inclua logos, marcas, nomes de empresas, screenshots de interfaces, "
        f"texto dentro da imagem, dados inventados, pessoas identificáveis ou "
        f"elementos que o artigo não menciona. "
        f"Se o texto não permitir uma cena concreta, prefira abstração geométrica."
    )

    return {
        "prompt": prompt,
        "base_do_artigo": {
            "titulo": titulo,
            "subtitulo": subtitulo,
            "temas_detectados": temas,
        },
        "fontes": fontes_validas,
        "constraints": [
            "derivado_da_materia",
            "sem_logos_ou_marcas",
            "sem_interface_falsa",
            "sem_texto_na_imagem",
            "sem_fatos_inventados",
        ],
    }
