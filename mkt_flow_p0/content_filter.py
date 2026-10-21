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
from datetime import datetime
from urllib.parse import urlsplit

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
    "apostas": [r"bet365", r"\bbet\b", r"aposta(s)? (esportiva|online)", r"cassino", r"casino",
                r"jogo do bicho", r"tigrinho", r"bônus de boas-vindas.*aposta", r"odd(s)? (de|para)",
                r"free spins", r"spins grátis", r"no deposit", r"sem depósito",
                r"blackjack", r"jackpot", r"roulette"],
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


# --- Gate de VALOR acrescentado (regra 14 do AGENTS.md, 28/09/2026) ---
# Por que existe: o Google (SQRG 4.6.6, 11/09/2025) diz que conteúdo de
# terceiro parafraseado e SEM valor acrescentado é "Lowest", "even if the page
# assigns credit for the content to another source". Creditar não salva. Logo,
# reescrever UMA fonte e publicar é fabricar "replicated content" — proibido pela
# política do AdSense. Este gate barra isso ANTES de gastar token na reescrita.
# Fonte primária: AGENTS.md regra 14. Ferramenta de medição: 9160 (0 números novos).

# Domínios de onde NÃO vem valor acrescentado (matéria de terceiro sobre a notícia).
_DOMINIO_TERCEIRO = re.compile(
    r"(canaltech|tecnoblog|olhardigital|adrenaline|zoom\.com\.br|terra|uol|globo|g1|"
    r"folha|estadao|metropoles|infomoney|valor\.globo|moneytimes|techtudo|showmetech|"
    r"9to5mac|9to5google|androidauthority|macrumors|appleinsider|androidpolice|"
    r"theverge|arstechnica|techcrunch|engadget|wired|theregister|zdnet|gsmarena|"
    r"tomshardware|tomsguide|tom's hardware|notebookcheck|techpowerup|anandtech|"
    r"pcmag|cnet|phonearena|slashdot|lobste\.rs|thehackernews|hackernews|"
    r"bleepingcomputer|darkreading|krebsonsecurity|schneier|sixcolors|macstories|"
    r"liliputing|androidheadlines|phonearena|eurogamer|pcgamer|polygon|ign\.com|"
    r"kotaku|nme\.com|rockpapershotgun|gamespot|ign|howtogeek|lifehacker|makeuseof|"
    r"techmeme|quantamagazine|technologyreview|huggingface|sammobile|xdaforums|"
    r"telesintese|canalnews|feedburner|rss\.|news\.ycombinator)",
    re.IGNORECASE,
)

# Fonte primária oficial: onde a notícia NASCEU (marca, fabricante, estudo, docs).
# M04.16: a lógica anterior era por EXCLUSÃO ("se não é veículo conhecido, é
# primário"). Isso aprovava qualquer link — inclusive domínio inventado — e
# anulava o gate: `links=["https://blog-qualquer.example/x"]` bastava para
# APROVAR preço sem data. Agora é lista positiva (fail-closed): domínio
# desconhecido NÃO é fonte primária.
_NAO_PRIMARIO = re.compile(
    r"(facebook|instagram|twitter|x\.com|tiktok|linkedin|youtube|reddit|"
    r"medium|substack|quora|wikipedia|wikimedia|discord|telegram|4chan|"
    r"news\.ycombinator|lobste\.rs|slashdot)",
    re.IGNORECASE,
)

# Fontes oficiais por formato: não dependem de marca conhecida.
_SUFIXOS_OFICIAIS = (".gov", ".gov.br", ".edu", ".edu.br", ".int")
_DOMINIOS_CIENTIFICOS = ("arxiv.org", "doi.org")

_DOMINIOS_COMERCIAIS = (
    "amazon.com.br",
    "amazon.com",
    "mercadolivre.com.br",
    "shopee.com.br",
    "kabum.com.br",
    "magazineluiza.com.br",
    "fastshop.com.br",
    "casasbahia.com.br",
    "pontofrio.com.br",
    "extra.com.br",
    "carrefour.com.br",
)

# Lista positiva de fabricantes/marcas. Editável sem mexer em código em
# mkt_flow_p0/fontes_primarias.json (mesmo padrão de tema_keywords.json).
_FONTES_PRIMARIAS_EMBUTIDAS = (
    "samsung.com",
    "apple.com",
    "google.com",
    "microsoft.com",
    "meta.com",
    "openai.com",
    "anthropic.com",
    "qualcomm.com",
    "intel.com",
    "nvidia.com",
    "amd.com",
    "sony.com",
    "playstation.com",
    "xbox.com",
    "nintendo.com",
    "lg.com",
    "xiaomi.com",
    "oneplus.com",
    "oppo.com",
    "realme.com",
    "honor.com",
    "huawei.com",
    "motorola.com",
    "lenovo.com",
    "dell.com",
    "hp.com",
    "asus.com",
    "acer.com",
    "tcl.com",
    "philips.com.br",
    "jbl.com",
    "logitech.com",
    "razer.com",
    "corsair.com",
    "hyperx.com",
    "redragon.com.br",
    "elgato.com",
    "gopro.com",
    "dji.com",
    "anker.com",
    "tp-link.com",
    "kingston.com",
    "seagate.com",
    "westerndigital.com",
    "crucial.com",
    "positivo.com.br",
    "multilaser.com.br",
)
_FONTES_PRIMARIAS_PATH = _Path(__file__).parent / "fontes_primarias.json"


def _carregar_fontes_primarias() -> tuple[str, ...]:
    """Lê a lista positiva; JSON ausente ou inválido cai na lista embutida."""
    try:
        dados = _json.loads(_FONTES_PRIMARIAS_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        logger.warning("fontes_primarias.json indisponível (%s); usando lista embutida", e)
        return _FONTES_PRIMARIAS_EMBUTIDAS
    oficiais = dados.get("oficiais") if isinstance(dados, dict) else None
    limpos = tuple(
        item.strip().lower()
        for item in (oficiais or [])
        if isinstance(item, str) and item.strip()
    )
    return limpos or _FONTES_PRIMARIAS_EMBUTIDAS


_FONTES_PRIMARIAS = _carregar_fontes_primarias()


def _dominio_em(dominio: str, lista: tuple[str, ...]) -> bool:
    """Casa domínio exato ou subdomínio, sem aceitar sufixo colado (evil.com.br)."""
    for item in lista:
        base = item.strip().lower().lstrip(".")
        if base and (dominio == base or dominio.endswith(f".{base}")):
            return True
    return False


def _e_fonte_primaria(url: str) -> bool:
    """True se a URL parece ser a ORIGEM da informação (fabricante/estudo/oficial)."""
    dominio = _dominio(url)
    if not dominio:
        return False
    if (_DOMINIO_TERCEIRO.search(dominio) or _NAO_PRIMARIO.search(dominio)
            or _e_fonte_comercial(url)):
        return False
    # Documento oficial publicado como PDF (checa só o caminho, não a query).
    try:
        caminho = urlsplit(url).path.lower()
    except (TypeError, ValueError):
        caminho = ""
    if caminho.endswith(".pdf"):
        return True
    return (_dominio_em(dominio, _SUFIXOS_OFICIAIS)
            or _dominio_em(dominio, _DOMINIOS_CIENTIFICOS)
            or _dominio_em(dominio, _FONTES_PRIMARIAS))

# Preço brasileiro e data são evidências separadas. O critério só passa quando
# ambos existem, a data é válida e há URL de uma fonte comercial conhecida.
_PRECO_BR = re.compile(
    r"R\$\s?(?:\d{1,3}(?:\.\d{3})+|\d+)(?:,\d{2})?\b",
    re.IGNORECASE,
)
_DATA_CAPTURA = re.compile(r"\b\d{1,2}/\d{1,2}/20\d{2}\b")

# Medição PRÓPRIA = apenas linguagem de primeira mão. Bug de 28/09: a 1ª versão
# aceitava qualquer spec com unidade (6,2 pol / 120 Hz / 4.000 mAh) e a palavra
# "medida" (que em PT significa decisão, não medição). Errado nos dois casos:
# ficha de fabricante repetida é justamente o cenário "Low" da SQRG 5.2.1
# ("content from other sources with little additional comment"), não valor.
_MEDICAO_PROPRIA = re.compile(
    r"(\btestamos\b|\btestei\b|\bmedi[rm]os\b|\bmedi[rm]e[im]?\b|"
    r"\bno nosso teste\b|\bem uso (?:real|di[aá]rio|por \d+)\b|"
    r"\bno lab(?:orat[oó]rio)?\b|\bnos nossos (?:dias|meses)\b|"
    r"\b(\d+)\s?(?:dias|semanas) de (?:uso|teste|autonomia)\b)",
    re.IGNORECASE,
)

# Ficha de fabricante: sinal fraco, NÃO conta como valor (só é reportado).
_FICHA_TECNICA = re.compile(
    r"\b\d+[.,]?\d*\s?(mAh|Wh|kWh|GB|TB|MP|Hz|GHz|MHz|W|nm|dB|"
    r"pol|polegadas|px|led|mAh)\b",
    re.IGNORECASE,
)

# Tabela com critério explícito: 2+ fontes citadas + marcador de comparação.
_CRUZAMENTO = re.compile(
    r"(fonte[s]?|via|segundo)\s*:?\s*(https?://|\w+\.\w+)", re.IGNORECASE
)


def _dominio(url: str) -> str:
    try:
        parsed = urlsplit(url or "")
    except (TypeError, ValueError):
        return ""
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        return ""
    dominio = parsed.hostname.lower().rstrip(".")
    return re.sub(r"^(?:www|m|mobile|amp)\.", "", dominio)


def _e_fonte_comercial(url: str) -> bool:
    return _dominio_em(_dominio(url), _DOMINIOS_COMERCIAIS)


def _tem_data_valida(texto: str) -> bool:
    for match in _DATA_CAPTURA.finditer(texto):
        try:
            datetime.strptime(match.group(0), "%d/%m/%Y")
        except ValueError:
            continue
        return True
    return False


def filtrar_valor_acrescentado(
    titulo: str = "",
    texto: str = "",
    links: list = None,
    tem_video: bool = False,
    tem_mediacao: bool = False,
    tem_cruzamento: bool = False,
    fontes_cruzadas: list = None,
) -> dict:
    """
    Gate de VALOR (regra 14): só vira ARTIGO se tiver >=1 destes 4:
      1. preço brasileiro capturado em marketplace COM DATA
      2. link de fonte primária oficial (nunca matéria de terceiro sobre ela)
      3. medição própria ou vídeo transcrito
      4. cruzamento de >=2 fontes com critério de pontuação explícito

    Vereditos: APROVADO (tem >=1 critério) | BLOQUEADO (nenhum — não há artigo;
    o item sai como link no digest, que é o produto correto para esse conteúdo).
    """
    alvo = f"{titulo or ''} {texto or ''}"
    links = [l for l in (links or []) if l]
    criterios = []

    # 1) preço BR + data de calendário válida + fonte comercial verificável.
    if (_PRECO_BR.search(alvo) and _tem_data_valida(alvo)
            and any(_e_fonte_comercial(link) for link in links)):
        criterios.append("preco_br_data")

    # 2) fonte primária oficial entre os links
    if any(_e_fonte_primaria(l) for l in links):
        criterios.append("fonte_primaria")

    # 3) medição própria (1ª mão) OU vídeo transcrito — são sinais distintos e
    #    merecem rótulos distintos, senão o relatório mente sobre o que salvou.
    if tem_video:
        criterios.append("video_transcrito")
    if tem_mediacao or _MEDICAO_PROPRIA.search(alvo):
        criterios.append("medicao_propria")

    # 4) cruzamento declarado e comprovado por >=2 domínios independentes.
    fontes = [*links, *(fontes_cruzadas or [])]
    dominios = {_dominio(fonte) for fonte in fontes if _dominio(fonte)}
    if tem_cruzamento and len(dominios) >= 2:
        criterios.append("cruzamento_2fontes")

    if criterios:
        return {"veredito": "APROVADO", "criterios": sorted(set(criterios)),
                "total_criterios": len(set(criterios)),
                "motivo": "valor_acrescentado",
                "ficha_tecnica": bool(_FICHA_TECNICA.search(alvo)),
                "aviso": ""}

    return {
        "veredito": "BLOQUEADO", "criterios": [], "total_criterios": 0,
        "motivo": "sem_valor_acrescentado",
        "ficha_tecnica": bool(_FICHA_TECNICA.search(alvo)),
        "aviso": ("Nenhum dos 4 critérios da regra 14. Reescrever a fonte e publicar "
                  "= 'replicated content' (SQRG 4.6.6: 'Lowest, even if the page assigns "
                  "credit'). O item deve sair como link no digest, não como artigo."),
    }


def gate_publicacao(titulo: str = "", texto: str = "", links: list = None,
                    tem_video: bool = False, tem_mediacao: bool = False,
                    tem_cruzamento: bool = False, fontes_cruzadas: list = None) -> dict:
    """Atalho: roda compliance + valor. BLOQUEADO se qualquer um dos dois barrar."""
    comp = filtrar_conteudo(titulo, texto)
    val = filtrar_valor_acrescentado(titulo, texto, links, tem_video,
                                     tem_mediacao, tem_cruzamento, fontes_cruzadas)
    if comp["veredito"] == "BLOQUEADO":
        return comp
    if val["veredito"] == "BLOQUEADO":
        return val
    out = dict(comp)
    out["criterios_valor"] = val["criterios"]
    return out
