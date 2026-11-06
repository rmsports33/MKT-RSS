"""
mkt_flow_p0.image_handler — Pipeline de capa (P0).
Padrão ConexoTech 1200x675 JPEG. Ordem: banco gratuito licenciado,
depois encaminhamento para imagem IA se banco não for adequado.
Imagem original RSS não é prova de direitos. Apenas prévia; nunca publica mídia.

Benchmark: AINP/AutoBlog cobram Pro por "AI image/Imagen"; DALL-E custa
$0.04-0.08/foto. Aqui: Pillow local (grátis) + upload via wp/v2/media.
Env lido sob demanda (sem side-effect no import).
"""
import io
import logging
import os
from urllib.parse import quote_plus

import requests

logger = logging.getLogger("image_handler")

CAPA_LARGURA, CAPA_ALTURA = 1200, 675
QUALIDADE_JPEG = 82
HEADERS = {"User-Agent": "Mozilla/5.0 (MKT-Flow-P0 imagens)"}
MAX_BYTES = 8 * 1024 * 1024


def baixar_imagem(url: str, timeout: int = 15) -> dict:
    """Baixa imagem. Retorna {bytes, content_type} ou {"erro":...}. Teto 8MB."""
    url = (url or "").strip()
    if not url.startswith("http"):
        return {"erro": "URL de imagem inválida"}
    try:
        r = requests.get(url, timeout=timeout, headers=HEADERS, stream=True)
        r.raise_for_status()
        ctype = (r.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        if ctype and not ctype.startswith("image/"):
            return {"erro": f"URL não é imagem (Content-Type: {ctype})"}
        buf = io.BytesIO()
        total = 0
        for chunk in r.iter_content(256 * 1024):
            total += len(chunk)
            if total > MAX_BYTES:
                return {"erro": "Imagem acima de 8MB — ignorada"}
            buf.write(chunk)
        return {"bytes": buf.getvalue(), "content_type": ctype or "image/jpeg"}
    except requests.Timeout:
        return {"erro": f"Download timeout após {timeout}s"}
    except Exception as e:
        return {"erro": f"Falha no download: {str(e)[:120]}"}


def processar_capa(imagem_bytes: bytes, largura: int = CAPA_LARGURA, altura: int = CAPA_ALTURA,
                   qualidade: int = QUALIDADE_JPEG) -> dict:
    """Cover crop centralizado + JPEG. Retorna {bytes, largura, altura} ou {"erro":...}."""
    try:
        from PIL import Image
    except ImportError:
        return {"erro": "Pillow não instalado — rode: pip install Pillow"}
    try:
        img = Image.open(io.BytesIO(imagem_bytes)).convert("RGB")
    except Exception as e:
        return {"erro": f"Imagem ilegível: {str(e)[:100]}"}
    # Cover: escala para cobrir e corta centro
    proporcao = max(largura / img.width, altura / img.height)
    nova = img.resize((round(img.width * proporcao), round(img.height * proporcao)))
    x = (nova.width - largura) // 2
    y = (nova.height - altura) // 2
    capa = nova.crop((x, y, x + largura, y + altura))
    buf = io.BytesIO()
    capa.save(buf, format="JPEG", quality=qualidade, optimize=True)
    return {"bytes": buf.getvalue(), "largura": largura, "altura": altura, "content_type": "image/jpeg"}


def buscar_fallback(consulta: str, timeout: int = 10) -> dict:
    """Banco gratuito (Unsplash com key free). Sem key → erro orientando a colar imagem."""
    try:
        from dotenv import load_dotenv
        from pathlib import Path
        _r = Path(__file__).parent.parent
        for _p in [_r / ".env", Path.cwd() / ".env"]:
            if _p.exists():
                load_dotenv(_p, override=False)
    except Exception:
        pass
    key = (os.getenv("UNSPLASH_ACCESS_KEY") or "").strip()
    if not key:
        return {"erro": "Sem imagem original e sem UNSPLASH_ACCESS_KEY — cole a imagem manualmente"}
    try:
        r = requests.get("https://api.unsplash.com/search/photos",
                         params={"query": consulta, "per_page": 5, "orientation": "landscape"},
                         headers={"Authorization": f"Client-ID {key}"}, timeout=timeout)
        r.raise_for_status()
        resultados = (r.json().get("results") or [])
        if not resultados:
            return {"erro": f"Unsplash sem resultado para '{consulta}'"}
        # Não promover automaticamente a primeira foto a imagem licenciada.
        # O editor confere a página individual, a licença e o enquadramento.
        candidatos = []
        for foto in resultados:
            link = (foto.get("links") or {}).get("html", "")
            url = (foto.get("urls") or {}).get("regular", "")
            autor = ((foto.get("user") or {}).get("name") or "")
            w, h = foto.get("width", 0), foto.get("height", 0)
            if (isinstance(link, str) and link.startswith("https://unsplash.com/")
                    and isinstance(url, str) and url.startswith("https://")
                    and type(w) is int and type(h) is int and w >= 1200 and h >= 675):
                candidatos.append({"url": url, "pagina_origem": link,
                    "autor": autor, "origem": "unsplash",
                    "licenca_url": "https://unsplash.com/license",
                    "largura_original": w, "altura_original": h,
                    "revisao_direitos": "PENDENTE", "revisao_visual": "PENDENTE"})
        if not candidatos:
            return {"erro": "Nenhuma imagem gratuita atende à resolução mínima",
                    "proxima_etapa": "AVALIAR_GERACAO_IA"}
        return {"candidatos": candidatos, "proxima_etapa": "REVISAO_HUMANA_DE_MIDIA"}
    except Exception as e:
        return {"erro": f"Unsplash falhou: {str(e)[:120]}"}


def preparar_capa(url_original: str = "", consulta_fallback: str = "", timeout: int = 15,
                   *, direitos_original_confirmados: bool = False) -> dict:
    """Seleção segura: banco gratuito primeiro, imagem IA somente se inadequado.

    Nunca confunde uma foto candidata com autorização de uso. Não associa
    mídia ao WordPress. A imagem RSS somente pode ser usada após prova de direitos.
    O chamador deve conferir licença, autoria e recorte em 1440/390 px.
    """
    if consulta_fallback:
        result = buscar_fallback(consulta_fallback, timeout=timeout)
        if result.get("candidatos"):
            return {"origem": "banco_gratuito", "candidatos": result["candidatos"],
                    "status": "REVISAO_HUMANA_DE_MIDIA",
                    "proxima_etapa": "VALIDAR_LICENCA_E_VISUAL_1440_390"}
    # Nunca usar automaticamente a imagem extraída do feed sem licença.
    if url_original and direitos_original_confirmados is True:
        dl = baixar_imagem(url_original, timeout=timeout)
        if "bytes" in dl:
            capa = processar_capa(dl["bytes"])
            if "bytes" in capa:
                capa["origem"] = "fonte_com_direitos_confirmados"
                capa["status"] = "PREVIA_PENDENTE_DE_REVISAO_VISUAL"
                return capa
    return {"status": "IMAGEM_PENDENTE", "proxima_etapa": "AVALIAR_GERACAO_IA",
            "erro": "Banco gratuito não forneceu candidata adequada; nenhuma mídia foi aprovada."}
