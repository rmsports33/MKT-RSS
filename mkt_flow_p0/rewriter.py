"""
mkt_flow_p0.rewriter — Reescrita via OpenAI API (execução opt-in)
Substitui reescrita fechada dos plugins (AINP/AutoBlog/GeraNews).
Roda DEPOIS do extractor e ANTES do wp_publisher.

Benchmark: grátis Groq Llama (8b instant / 70b versatile) para volume;
pago GPT-4o-mini/Claude Haiku só quando precisar seguir prompt longo
sem alucinar (reviews afiliados). Prompt aqui é heavy-rewrite PT-BR
com firewall anti-invenção + atribuição de fonte (padrão AIWU/WP Aggregator).
"""
import json
import logging
import os
import re
from pathlib import Path

logger = logging.getLogger("rewriter")

# NOTA: sem load_dotenv no import (efeito colateral global quebrava
# test_landing_p0::test_xss_escape: GA_MEASUREMENT_ID do .env injetava
# <script> no teste). Env é carregado sob demanda em _ensure_env().
_ENV_LOADED = False


def _ensure_env():
    """Carrega .env só quando necessário (lazy) — import sem side-effect."""
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    try:
        from dotenv import load_dotenv
        _ROOT = Path(__file__).parent.parent
        for _p in [_ROOT / ".env", _ROOT / "MKTFLOW" / ".env", Path.cwd() / ".env"]:
            if _p.exists():
                load_dotenv(_p, override=False)
    except Exception:
        pass
    _ENV_LOADED = True


def _modelo() -> str:
    # Model name is explicit to avoid silently choosing an unavailable/paid model.
    return os.getenv("OPENAI_MODEL", "").strip()


def _custos() -> tuple:
    # Do not invent rates; optional explicit account-configured USD prices.
    try:
        cin = float(os.getenv("OPENAI_COST_PER_1K_INPUT", "0"))
        cout = float(os.getenv("OPENAI_COST_PER_1K_OUTPUT", "0"))
        return cin, cout
    except ValueError:
        return 0.0, 0.0


def _get_client():
    # Both explicit opt-in and a separate OpenAI API key are mandatory.
    if os.getenv("CONEXO_OPENAI_API_ENABLED", "").strip().lower() != "true":
        return None, "OpenAI API desativada: CONEXO_OPENAI_API_ENABLED != true"
    _ensure_env()
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        return None, "OPENAI_API_KEY ausente; assinatura ChatGPT não inclui API"
    if not _modelo():
        return None, "OPENAI_MODEL ausente; escolha explicitamente um modelo disponível"
    try:
        from openai import OpenAI
    except ImportError:
        return None, "Biblioteca openai não instalada"
    try:
        return OpenAI(api_key=api_key), ""
    except Exception as e:
        return None, f"Falha ao inicializar cliente OpenAI: {str(e)[:120]}"


def gerar_slug(titulo: str) -> str:
    s = (titulo or "materia").strip().lower()
    s = re.sub(r"[^a-z0-9\s\-]+", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")[:80] or "materia"


def montar_prompt(titulo_original: str, texto_original: str, fonte_nome: str = "",
                   keywords: list = None) -> str:
    fonte = f"\nFonte original: {fonte_nome}" if fonte_nome else ""
    kws = ", ".join([str(k) for k in (keywords or []) if str(k).strip()][:8])
    linha_kw = (f"\nPalavras-chave reais de busca (use no titulo_seo, texto e tags quando couber): {kws}."
                if kws else "")
    return (
        f"Título original: {titulo_original[:200]}\n{fonte}\n\n"
        f"Texto original (Markdown):\n{texto_original[:9000]}\n\n"
        "Escreva TUDO em português brasileiro (se o original estiver em outro idioma, "
        "traduza integralmente; mantenha nomes próprios, modelos e specs em inglês quando for nome oficial). "
        "Números, specs, preços e datas: copie exatos, nunca converta nem arredonde."
        f"{linha_kw}\n"
        "Gere o JSON com: titulo_seo (até 60 chars, com palavra-chave), "
        "meta_description (145-160 chars, persuasiva), slug (url, minúsculas, hífens), "
        "tags (até 5, minúsculas, em português), texto_markdown (comprimento proporcional às evidências, "
        "subtítulos quando úteis; a atribuição será acrescentada pelo pipeline)."
    )


def _parse_json_resposta(raw: str) -> dict:
    """Extrai JSON mesmo se vier com ```json cerca ou texto extra."""
    raw = (raw or "").strip()
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if m:
        raw = m.group(1)
    else:
        i, j = raw.find("{"), raw.rfind("}")
        if i >= 0 and j > i:
            raw = raw[i:j + 1]
    return json.loads(raw)


def _estimar_custo(prompt_tok: int, completion_tok: int) -> float:
    cin, cout = _custos()
    return round(prompt_tok / 1000 * cin + completion_tok / 1000 * cout, 6)


def reescrever_materia(
    titulo_original: str,
    texto_original: str,
    fonte_nome: str = "",
    url_fonte: str = "",
    temperature: float = 0.5,
    max_tokens: int = 2500,
    timeout: int = 60,
    keywords: list = None,
    evidencias_aprovadas: dict = None,
) -> dict:
    """
    Reescreve 1 matéria. Gate de entrada: texto <100 palavras = {"erro"}
    (não reescreve excerpt — mesma trava do fiscal AINP manual).
    Retorna dict com titulo_seo/meta_description/slug/tags/texto_markdown/
    palavras/modelo/uso_tokens/custo_usd_estimado ou {"erro":...}.
    Atribuição de fonte é adicionada pelo chamador no WP (não no corpo).
    """
    palavras_in = len(re.findall(r"\S+", texto_original or ""))
    if palavras_in < MIN_PALAVRAS_ENTRADA:
        return {"erro": f"Texto curto demais ({palavras_in} palavras, mínimo {MIN_PALAVRAS_ENTRADA}) — extraia o corpo completo antes."}

    client, erro = _get_client()
    if erro:
        return {"erro": erro}

    modelo = _modelo()
    try:
        resp = client.chat.completions.create(
            model=modelo,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": montar_prompt(titulo_original, texto_original, fonte_nome, keywords)},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            response_format={"type": "json_object"},
        )
    except Exception as e:
        msg = str(e)
        if "401" in msg or "invalid_api_key" in msg.lower():
            return {"erro": "OPENAI_API_KEY inválida"}
        if "429" in msg or "rate" in msg.lower():
            return {"erro": "Limite ou quota da API OpenAI atingido (429)"}
        logger.warning("rewriter OpenAI falhou: %s", msg[:200])
        return {"erro": f"Falha OpenAI: {msg[:150]}"}

    try:
        raw = resp.choices[0].message.content or ""
        uso = getattr(resp, "usage", None)
        pt = int(getattr(uso, "prompt_tokens", 0) or 0)
        ct = int(getattr(uso, "completion_tokens", 0) or 0)
        dados = _parse_json_resposta(raw)
    except Exception as e:
        return {"erro": f"Resposta IA fora do JSON esperado: {str(e)[:120]}"}

    titulo_seo = str(dados.get("titulo_seo") or titulo_original)[:META_TITULO_MAX]
    meta = str(dados.get("meta_description") or "")[:META_DESC_MAX]
    slug = gerar_slug(str(dados.get("slug") or titulo_seo))
    tags = [str(t).lower().strip()[:30] for t in (dados.get("tags") or []) if str(t).strip()][:5]
    texto = str(dados.get("texto_markdown") or "").strip()
    palavras_out = len(re.findall(r"\S+", texto))
    if palavras_out < 200:
        return {"erro": f"Reescrita curta demais ({palavras_out} palavras) — rode de novo."}

    # C19: o rewriter nao possui evidencias aprovadas por claim.
    # Nunca atribuir PASS a partir de um JSON gerado pela propria IA.
    contrato_editorial = None
    if evidencias_aprovadas is not None:
        from mkt_flow_p0.produtor_evidencias_noticia import produzir_contrato_noticia
        contrato_editorial = produzir_contrato_noticia(evidencias_aprovadas, texto)

    return {
        "titulo_seo": titulo_seo,
        "contrato_editorial": contrato_editorial,
        "meta_description": meta,
        "slug": slug,
        "tags": tags,
        "texto_markdown": texto,
        "palavras": palavras_out,
        "palavras_origem": palavras_in,
        "fonte_nome": fonte_nome,
        "url_fonte": url_fonte,
        "modelo": modelo,
        "uso_tokens": {"prompt": pt, "completion": ct, "total": pt + ct},
        "custo_usd_estimado": _estimar_custo(pt, ct),
    }


def adicionar_atribuicao(texto_markdown: str, fonte_nome: str, url_fonte: str) -> str:
    """Rodapé de atribuição ética (padrão AIBlogMax/WP Aggregator)."""
    if not url_fonte:
        return texto_markdown
    nome = fonte_nome or url_fonte
    return texto_markdown.rstrip() + f"\n\n---\n*Fonte original: [{nome}]({url_fonte})*"

