"""
mkt_flow_p0.content_filter — Blindagem AdSense + compliance editorial (P0).
Roda ANTES do LLM (barato, sem custo de API): descarta pauta problemática
antes de gastar reescrita. Depois do LLM, revalida o texto final.

Benchmark: GeraNews (Filtros inteligentes/Compliance), ScriptNews e
AutoBlog Pro vendem isso como diferencial pago — aqui é nativo e grátis.
Vereditos: APROVADO | REVISAR (humano decide) | BLOQUEADO (descarta).
"""
import logging
import re
import unicodedata

logger = logging.getLogger("content_filter")

# --- Filtro de tema (whitelist/blacklist do ConexoTech) ---
# Arquivo editável sem mexer em código: mkt_flow_p0/tema_keywords.json
import json as _json
from pathlib import Path as _Path
_TEMA_PATH = _Path(__file__).parent / "tema_keywords.json"
try:
    _TEMA = _json.loads(_TEMA_PATH.read_text(encoding="utf-8"))
except Exception:
    _TEMA = {"incluir": [], "excluir": []}


def filtrar_por_tema(titulo: str = "", texto: str = "") -> dict:
    """Whitelist/blacklist de tema. Retorna {veredito, motivo, termos_encontrados}."""
    alvo = _norm(f"{titulo or ''} {texto or ''}")
    incluir = [t.lower() for t in (_TEMA.get("incluir") or [])]
    excluir = [t.lower() for t in (_TEMA.get("excluir") or [])]
    # Excluir tem prioridade
    for termo in excluir:
        if termo and termo in alvo:
            return {"veredito": "BLOQUEADO", "motivo": "off_topic", "termo": termo, "lista": "excluir"}
    if incluir:
        for termo in incluir:
            if termo and termo in alvo:
                return {"veredito": "APROVADO", "motivo": "tema_ok", "termo": termo, "lista": "incluir"}
        return {"veredito": "BLOQUEADO", "motivo": "off_topic", "termo": "", "lista": "incluir",
                "aviso": "nenhum termo da whitelist encontrado"}
    return {"veredito": "APROVADO", "motivo": "sem_filtro", "termo": ""}


# Categorias que BLOQUEIAM (políticas AdSense + programa de afiliados)
PADROES_BLOQUEIO = {
    "apostas": [r"bet365", r"\bbet\b", r"aposta(s)? (esportiva|online)", r"cassino", r"tigrinho",
                r"jogo do bicho", r"bônus de boas-vindas.*aposta", r"odd(s)? (de|para)"],
    "adulto": [r"pornografia", r"conteúdo adulto", r"acompanhantes?", r"sexo explícito",
               r"onlyfans", r"vazou.*privacy", r"privacy.*vazad"],
    "violencia_grafica": [r"decapita", r"esquarteja", r"corpo carbonizado", r"chacina com fotos",
                          r"vídeo do assassinato"],
    "golpe_financeiro": [r"dinheiro fácil", r"renda garantida", r"pirâmide financeira",
                         r"empréstimo imediato sem consulta", r"dobrar seu dinheiro"],
}

# Categorias que pedem REVISÃO humana (não bloqueiam sozinhas)
PADROES_REVISAO = {
    "politica": [r"eleiç", r"ministro", r"presidente lula", r"bolsonaro", r"deputad[oa]", r"senado"],
    "saude_milagre": [r"cura (definitiva|milagrosa|garantida)", r"tratamento milagroso", r"emagreça .* dias"],
    "urgencia_suspeita": [r"\d{2}% de desconto", r"últim[oa]s? \d+ unidades", r"saia do ar em"],
    "off_topic": [r"fase da lua", r"calendário lunar", r"horóscopo", r"signo", r"receita culinária", r"futebol"],
}

_COMPILADOS = None


def _norm(texto: str) -> str:
    """Minúsculas sem acento para matching robusto em PT-BR."""
    t = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", t.lower()).strip()


def _compilar():
    global _COMPILADOS
    if _COMPILADOS is None:
        _COMPILADOS = {
            "bloqueio": {cat: [re.compile(p, re.IGNORECASE) for p in pads] for cat, pads in PADROES_BLOQUEIO.items()},
            "revisao": {cat: [re.compile(p, re.IGNORECASE) for p in pads] for cat, pads in PADROES_REVISAO.items()},
        }
    return _COMPILADOS


def filtrar_conteudo(titulo: str = "", texto: str = "", categorias_extras: dict = None) -> dict:
    """Classifica pauta/texto. Retorna {veredito, categorias, trechos, total_sinais}."""
    comp = _compilar()
    original = f"{titulo or ''}\n{texto or ''}"
    alvo = _norm(original)
    categorias, trechos = [], []
    for cat, regs in comp["bloqueio"].items():
        for rgx in regs:
            m = rgx.search(alvo)
            if m:
                categorias.append(cat)
                trechos.append({"categoria": cat, "trecho": m.group(0)[:80]})
                break
    if categorias_extras:
        for cat, pads in categorias_extras.items():
            for p in pads or []:
                try:
                    m = re.search(p, alvo, re.IGNORECASE)
                except re.error:
                    continue
                if m:
                    categorias.append(cat)
                    trechos.append({"categoria": cat, "trecho": m.group(0)[:80]})
                    break
    revisoes = []
    for cat, regs in comp["revisao"].items():
        for rgx in regs:
            m = rgx.search(alvo)
            if m:
                revisoes.append(cat)
                trechos.append({"categoria": cat, "trecho": m.group(0)[:80], "nivel": "revisao"})
                break
    if categorias:
        veredito = "BLOQUEADO"
    elif revisoes:
        veredito = "REVISAR"
        categorias = revisoes
    else:
        veredito = "APROVADO"
    return {"veredito": veredito, "categorias": sorted(set(categorias)),
            "trechos": trechos, "total_sinais": len(trechos)}


def filtrar_item_rss(item: dict) -> dict:
    """Gate de pauta: filtra título+resumo do feed antes de extrair/reescrever."""
    item = item or {}
    r = filtrar_conteudo(item.get("titulo", ""), item.get("resumo", ""))
    r["link"] = item.get("link", "")
    r["fonte"] = item.get("fonte", "")
    return r
