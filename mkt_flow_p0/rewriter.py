"""
mkt_flow_p0.rewriter — Reescrita própria via Groq (P0)
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
    return os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


def _custos() -> tuple:
    try:
        cin = float(os.getenv("GROQ_COST_PER_1K_INPUT", "0.00015"))
    except ValueError:
        cin = 0.00015
    try:
        cout = float(os.getenv("GROQ_COST_PER_1K_OUTPUT", "0.00075"))
    except ValueError:
        cout = 0.00075
    return cin, cout


MIN_PALAVRAS_ENTRADA = 100
META_TITULO_MAX = 60
META_DESC_MIN, META_DESC_MAX = 145, 160

SYSTEM_PROMPT = (
    "Você auxilia a redação do ConexoTech em PT-BR, com voz inteligente e acessível. "
    "Reinaldo Mendes é o autor humano; Conexo Insight é a voz interna, não uma pessoa. "
    "Explique o fato, sua relevância e o impacto para o leitor brasileiro com síntese própria. "
    "REGRAS DURAS: não invente fatos, números, specs ou datas; mantenha só o que está no texto original; "
    "não copie frases; não opine como se tivesse testado o produto; "
    "Separe fato, interpretação e incerteza; não acrescente contexto factual sem fonte. "
    "Use Markdown, fatos principais primeiro e subtítulos quando úteis. "
    "Adapte o comprimento à pauta e às evidências, sem enchimento nem conclusão obrigatória. "
    "Responda SOMENTE um JSON válido com as chaves: titulo_seo, meta_description, slug, tags, texto_markdown."
)


def _get_client():
    _ensure_env()
    try:
        from groq import Groq
    except ImportError:
        return None, "groq não instalado — rode: pip install groq"
    api_key = (os.getenv("GROQ_API_KEY") or "").strip()
    if not api_key:
        return None, "GROQ_API_KEY ausente no .env — obtenha em https://console.groq.com"
    try:
        return Groq(api_key=api_key), ""
    except Exception as e:
        return None, f"Falha ao inicializar Groq: {str(e)[:120]}"


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




def _validar_orcamento_piloto(max_tokens: int, prompt: str) -> str:
    """Bloqueia chamadas do piloto cloud sem teto explicito e precificacao valida.

    O gate vale apenas quando CONEXO_CLOUD_PILOT=1, para preservar integrações
    legadas até uma migração supervisionada separada.
    """
    if os.getenv("CONEXO_CLOUD_PILOT") != "1":
        return ""
    try:
        limite = float(os.environ["CONEXO_CLOUD_BUDGET_USD"])
        max_saida = int(os.environ["CONEXO_CLOUD_MAX_OUTPUT_TOKENS"])
        max_entrada = int(os.environ["CONEXO_CLOUD_MAX_INPUT_TOKENS"])
        modelo_permitido = os.environ["CONEXO_CLOUD_ALLOWED_MODEL"].strip()
        custo_entrada = float(os.environ["GROQ_COST_PER_1K_INPUT"])
        custo_saida = float(os.environ["GROQ_COST_PER_1K_OUTPUT"])
        if not all(__import__("math").isfinite(x) and x >= 0 for x in
                   (limite, custo_entrada, custo_saida)):
            raise ValueError("valor financeiro invalido")
        if not (0 < max_saida <= max_tokens and max_tokens > 0):
            raise ValueError("limite de saida insuficiente")
        if not (0 < max_entrada <= 20000 and modelo_permitido == _modelo()):
            raise ValueError("limite de entrada/modelo invalido")
        # Limite conservador: caracteres nao podem superar o teto informado
        # (nao e um tokenizador; evita estimar tokens a menor).
        if len(SYSTEM_PROMPT) + len(prompt) > max_entrada:
            raise ValueError("prompt excede teto conservador de entrada")
        custo_maximo = (max_entrada * custo_entrada + max_saida * custo_saida) / 1000
        if custo_maximo > limite:
            raise ValueError("custo maximo excede orcamento")
    except (KeyError, ValueError, OverflowError) as exc:
        return f"Piloto cloud bloqueado antes da IA: {exc}"
    return ""

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

    prompt_usuario = montar_prompt(titulo_original, texto_original, fonte_nome, keywords)
    erro_orcamento = _validar_orcamento_piloto(max_tokens, prompt_usuario)
    if erro_orcamento:
        return {"erro": erro_orcamento}

    if os.getenv("CONEXO_CLOUD_PILOT") == "1":
        from mkt_flow_p0.cloud_budget_ledger import reservar
        cin = float(os.environ["GROQ_COST_PER_1K_INPUT"])
        cout = float(os.environ["GROQ_COST_PER_1K_OUTPUT"])
        entrada = int(os.environ["CONEXO_CLOUD_MAX_INPUT_TOKENS"])
        saida = int(os.environ["CONEXO_CLOUD_MAX_OUTPUT_TOKENS"])
        custo_reservado = (entrada * cin + saida * cout) / 1000
        erro_ledger = reservar(custo_reservado)
        if erro_ledger:
            return {"erro": f"Piloto cloud bloqueado: {erro_ledger}"}

    client, erro = _get_client()
    if erro:
        return {"erro": erro}

    modelo = _modelo()
    try:
        resp = client.chat.completions.create(
            model=modelo,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt_usuario},
            ],
            temperature=temperature,
            max_tokens=(int(os.environ["CONEXO_CLOUD_MAX_OUTPUT_TOKENS"])
                        if os.getenv("CONEXO_CLOUD_PILOT") == "1" else max_tokens),
            timeout=timeout,
            response_format={"type": "json_object"},
        )
    except Exception as e:
        msg = str(e)
        if "401" in msg or "invalid_api_key" in msg.lower():
            return {"erro": "GROQ_API_KEY inválida — gere outra em console.groq.com"}
        if "429" in msg or "rate" in msg.lower():
            return {"erro": "Limite Groq atingido (429) — aguarde 1-2 min e tente de novo (tier grátis)."}
        logger.warning(f"rewriter groq falhou: {msg[:200]}")
        return {"erro": f"Falha Groq: {msg[:150]}"}

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

