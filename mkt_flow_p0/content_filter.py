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
    # M04.16C: extensão .pdf NÃO confere origem. Qualquer domínio pode publicar
    # um PDF; antes, `https://blog-qualquer.example/paper.pdf` virava fonte
    # primária. O formato só é aceito se o domínio já for confiável.
    return (_dominio_em(dominio, _SUFIXOS_OFICIAIS)
            or _dominio_em(dominio, _DOMINIOS_CIENTIFICOS)
            or _dominio_em(dominio, _FONTES_PRIMARIAS))

# Preço brasileiro e data são evidências separadas. O critério só passa quando
# ambos existem, a data é válida, está vinculada ao preço e há URL de uma fonte
# comercial conhecida.
_PRECO_BR = re.compile(
    r"R\$\s?(?:\d{1,3}(?:\.\d{3})+|\d+)(?:,\d{2})?\b",
    re.IGNORECASE,
)
_DATA_CAPTURA = re.compile(r"\b\d{1,2}/\d{1,2}/20\d{2}\b")

# Janela máxima (caracteres) entre o preço e a data de captura. Fora disso, a
# data não é considerada "deste preço".
_JANELA_PRECO_DATA = 120

# Mínimos para evidência de primeira mão. Sem isso, `tem_video=True`,
# `tem_mediacao=True` e a simples palavra "testamos" aprovavam sozinhos.
_MIN_PALAVRAS_TRANSCRICAO = 60
_MIN_CHARS_METODO = 20
_MIN_MEDICOES = 2

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
    return bool(_datas_validas(texto))


def _datas_validas(texto: str) -> list:
    datas = []
    for match in _DATA_CAPTURA.finditer(texto):
        try:
            datetime.strptime(match.group(0), "%d/%m/%Y")
        except ValueError:
            continue
        datas.append(match)
    return datas


def _distancia(a, b) -> int:
    """Distância em caracteres entre dois matches (0 se se sobrepõem)."""
    if b.start() >= a.end():
        return b.start() - a.end()
    if a.start() >= b.end():
        return a.start() - b.end()
    return 0


def _pares_preco_data(texto: str) -> list:
    """Pares (preço, data) em que a data está perto do preço.

    M04.16C: antes bastava preço em um parágrafo e data em outro, sem vínculo.
    Agora a data precisa estar a no máximo _JANELA_PRECO_DATA caracteres do
    preço, para que "capturado em" pertença àquele valor.
    """
    datas = _datas_validas(texto)
    if not datas:
        return []
    pares = []
    for preco in _PRECO_BR.finditer(texto):
        for data in datas:
            if _distancia(preco, data) <= _JANELA_PRECO_DATA:
                pares.append((preco.group(0), data.group(0)))
    return pares


def _validar_evidencia_video(evidencia) -> tuple[bool, str]:
    """Vídeo só conta com URL válida E transcrição com corpo."""
    if not isinstance(evidencia, dict):
        return False, "evidencia_video ausente"
    if not _dominio(evidencia.get("url")):
        return False, "evidencia_video.url ausente ou inválida"
    palavras = re.findall(r"\w+", str(evidencia.get("transcricao") or ""))
    if len(palavras) < _MIN_PALAVRAS_TRANSCRICAO:
        return False, (f"transcrição com {len(palavras)} palavras "
                       f"(mínimo {_MIN_PALAVRAS_TRANSCRICAO})")
    return True, ""


def _validar_evidencia_medicao(evidencia) -> tuple[bool, str]:
    """Medição só conta com método descrito e >=2 medições com valor e unidade."""
    if not isinstance(evidencia, dict):
        return False, "evidencia_medicao ausente"
    metodo = str(evidencia.get("metodo") or "").strip()
    if len(metodo) < _MIN_CHARS_METODO:
        return False, f"método ausente ou com menos de {_MIN_CHARS_METODO} caracteres"
    medicoes = evidencia.get("medicoes")
    if not isinstance(medicoes, list):
        return False, "lista de medições ausente"
    completas = [
        m for m in medicoes
        if isinstance(m, dict)
        and str(m.get("metrica") or "").strip()
        and str(m.get("valor") or "").strip()
        and str(m.get("unidade") or "").strip()
    ]
    if len(completas) < _MIN_MEDICOES:
        return False, (f"{len(completas)} medição(ões) completa(s) "
                       f"(mínimo {_MIN_MEDICOES} com métrica, valor e unidade)")
    return True, ""


# --- M04.17A: evidência POR PRODUTO ---------------------------------------
# A lacuna que o Issue #9 pedia: `filtrar_valor_acrescentado` recebia o texto
# inteiro, e um ÚNICO preço com data no texto approveva um comparativo de
# vários produtos. Exemplo do defeito: comparativo "Galaxy S26 vs Pixel 11"
# com o preço do S26 e sem o do Pixel passava com `preco_br_data`.
#
# A regra que este bloco implementa: **evidência de um produto nunca aprova
# outro**. Cada produto é avaliado ISOLADAMENTE, com o próprio preço, a
# própria data, os próprios links, a própria medição e o próprio vídeo. Nada
# é herdado do texto geral nem de outro produto da lista.
#
# No modo por produto, o texto geral NÃO participa do veredito: se o texto
# trouxer um preço que não está em nenhum produto, esse preço não aprova
# ninguém. Sem isso, a contaminação voltaria pela porta do texto.
_CAMPOS_PRODUTO = (
    "nome", "preco", "data_captura", "fonte_preco", "links",
    "fontes_cruzadas", "tem_cruzamento", "evidencia_video",
    "evidencia_medicao", "texto",
)


def _links_do_produto(produto: dict) -> list:
    """URLs que pertencem a ESTE produto: fonte_preco + links + cruzadas."""
    links = []
    fonte = produto.get("fonte_preco")
    if fonte:
        links.append(fonte)
    for lista in (produto.get("links") or [], produto.get("fontes_cruzadas") or []):
        for item in lista:
            if item:
                links.append(item)
    return links


def _criterios_do_produto(produto: dict) -> tuple[list, list]:
    """Critérios de UM produto, usando SÓ a evidência desse produto.

    Devolve (criterios, avisos). Lista vazia de critérios = este produto não
    tem valor acrescentado próprio, e o item inteiro tem de ser bloqueado.
    """
    if not isinstance(produto, dict):
        return [], ["produto inválido: esperado dicionário"]

    criterios: list[str] = []
    avisos: list[str] = []
    links = _links_do_produto(produto)

    # 1) preço brasileiro + data de captura válida, com marketplace conhecido
    preco = str(produto.get("preco") or "").strip()
    data = str(produto.get("data_captura") or "").strip()
    tem_comercial = any(_e_fonte_comercial(link) for link in links)
    if preco and data:
        # Preço e data declarados no MESMO produto: o vínculo é explícito.
        if not _datas_validas(data):
            avisos.append(f"data de captura inválida: {data!r} (não conta como evidência)")
        elif not _PRECO_BR.search(preco):
            avisos.append(f"preço sem formato recognized: {preco!r}")
        elif not tem_comercial:
            avisos.append("preço sem link de marketplace conhecido (não é fonte comercial)")
        else:
            criterios.append("preco_br_data")
    else:
        # Fallback: o próprio texto do produto traz "R$ X ... em DD/MM/AAAA".
        corpus = " ".join(x for x in [preco, data, str(produto.get("texto") or "")] if x)
        if _pares_preco_data(corpus) and tem_comercial:
            criterios.append("preco_br_data")
        elif preco or data:
            avisos.append("preço e data de captura precisam ser declarados juntos")

    # 2) fonte primária oficial entre os links DESTE produto
    if any(_e_fonte_primaria(link) for link in links):
        criterios.append("fonte_primaria")

    # 3) e 4) primeira mão comprovada, evidência estruturada deste produto
    video_ok, video_motivo = _validar_evidencia_video(produto.get("evidencia_video"))
    if video_ok:
        criterios.append("video_transcrito")
    else:
        avisos.append(f"video_transcrito não comprovado: {video_motivo}")

    medicao_ok, medicao_motivo = _validar_evidencia_medicao(produto.get("evidencia_medicao"))
    if medicao_ok:
        criterios.append("medicao_propria")
    else:
        avisos.append(f"medicao_propria não comprovada: {medicao_motivo}")

    # 5) cruzamento declarado, com >=2 domínios independentes DESTE produto
    dominios = {_dominio(link) for link in links if _dominio(link)}
    if produto.get("tem_cruzamento"):
        if len(dominios) >= 2:
            criterios.append("cruzamento_2fontes")
        else:
            avisos.append(
                f"cruzamento_2fontes não comprovado: {len(dominios)} domínio(s) "
                "independente(s) de 2 exigidos"
            )

    return sorted(set(criterios)), avisos


def _avaliar_por_produto(produtos: list, exigir_produtos: bool = False) -> dict:
    """Veredito por produto: TODOS os produtos precisam ter valor próprio.

    Um produto sem nenhum critério reprova o item inteiro — é o oposto de
    "um preço no texto salva o comparativo inteiro".
    """
    if not produtos:
        return {
            "veredito": "BLOQUEADO", "criterios": [], "total_criterios": 0,
            "motivo": "produtos_ausentes",
            "ficha_tecnica": False,
            "aviso": ("Validação por produto exigida, mas nenhuma lista de produtos "
                      "foi informada. Sem produtos não há como garantir que a "
                      "evidência de um não aprove outro."),
            "avisos": [],
            "evidencia_por_produto": "exigida_nao_aplicada",
            "criterios_por_produto": {},
            "produtos_sem_valor": [],
        }

    avaliacoes = []
    sem_valor = []
    avisos = []
    criterios_gerais = set()
    for indice, produto in enumerate(produtos):
        nome_bruto = produto.get("nome") if isinstance(produto, dict) else None
        nome = str(nome_bruto or "").strip() or f"produto #{indice + 1}"
        criterios, avisos_produto = _criterios_do_produto(produto)
        avaliacoes.append({"produto": nome, "criterios": criterios})
        criterios_gerais.update(criterios)
        if not criterios:
            sem_valor.append(nome)
        for aviso in avisos_produto:
            avisos.append(f"[{nome}] {aviso}")

    if sem_valor:
        return {
            "veredito": "BLOQUEADO",
            "criterios": sorted(criterios_gerais),
            "total_criterios": len(criterios_gerais),
            "motivo": "produto_sem_valor",
            "ficha_tecnica": False,
            "aviso": ("Produto(s) sem valor acrescentado próprio: "
                      + ", ".join(sem_valor)
                      + ". A evidência de um produto não aprova outro."),
            "avisos": avisos,
            "evidencia_por_produto": "aplicada",
            "criterios_por_produto": {a["produto"]: a["criterios"] for a in avaliacoes},
            "produtos_sem_valor": sem_valor,
        }

    return {
        "veredito": "APROVADO",
        "criterios": sorted(criterios_gerais),
        "total_criterios": len(criterios_gerais),
        "motivo": "valor_acrescentado_por_produto",
        "ficha_tecnica": False,
        "aviso": "",
        "avisos": avisos,
        "evidencia_por_produto": "aplicada",
        "criterios_por_produto": {a["produto"]: a["criterios"] for a in avaliacoes},
        "produtos_sem_valor": [],
    }


def filtrar_valor_acrescentado(
    titulo: str = "",
    texto: str = "",
    links: list = None,
    tem_video: bool = False,
    tem_mediacao: bool = False,
    tem_cruzamento: bool = False,
    fontes_cruzadas: list = None,
    evidencia_video: dict = None,
    evidencia_medicao: dict = None,
    produtos: list = None,
    exigir_produtos: bool = False,
) -> dict:
    """
    Gate de VALOR (regra 14): só vira ARTIGO se tiver >=1 destes 4:
      1. preço brasileiro COM data de captura vinculada (mesma janela) em
         marketplace conhecido
      2. link de fonte primária oficial (nunca matéria de terceiro sobre ela)
      3. medição própria comprovada (método + >=2 medições) ou vídeo com
         transcrição verificável
      4. cruzamento declarado com >=2 domínios independentes

    M04.16C: declarações sem prova não aprovam. `tem_video` e `tem_mediacao`
    são apenas intenção; a aprovação exige `evidencia_video`/`evidencia_medicao`
    estruturadas. A palavra "testamos" no texto é sinal, nunca prova. Toda
    declaração não comprovada volta em `avisos`.

    M04.17A: `produtos` liga a validação POR PRODUTO. Com ela, o veredito vem
    só da evidência de cada produto — o texto geral não participa, e evidência
    de um produto nunca aprova outro. `exigir_produtos=True` bloqueia quando a
    lista não vem (para fluxos comparativos, onde a lista é obrigatória).

    Vereditos: APROVADO (tem >=1 critério) | BLOQUEADO (nenhum — não há artigo;
    o item sai como link no digest, que é o produto correto para esse conteúdo).
    """
    if produtos or exigir_produtos:
        return _avaliar_por_produto(produtos or [], exigir_produtos)

    alvo = f"{titulo or ''} {texto or ''}"
    links = [l for l in (links or []) if l]
    criterios: list[str] = []
    avisos: list[str] = []

    # 1) preço BR vinculado a data válida + fonte comercial verificável.
    if _pares_preco_data(alvo) and any(_e_fonte_comercial(l) for l in links):
        criterios.append("preco_br_data")

    # 2) fonte primária oficial entre os links
    if any(_e_fonte_primaria(l) for l in links):
        criterios.append("fonte_primaria")

    # 3) primeira mão comprovada — vídeo e medição são sinais distintos.
    video_ok, video_motivo = _validar_evidencia_video(evidencia_video)
    if video_ok:
        criterios.append("video_transcrito")
    elif tem_video or evidencia_video is not None:
        avisos.append(f"video_transcrito não comprovado: {video_motivo}")

    medicao_ok, medicao_motivo = _validar_evidencia_medicao(evidencia_medicao)
    if medicao_ok:
        criterios.append("medicao_propria")
    elif tem_mediacao or evidencia_medicao is not None:
        avisos.append(f"medicao_propria não comprovada: {medicao_motivo}")
    if _MEDICAO_PROPRIA.search(alvo) and not medicao_ok:
        avisos.append(
            "texto afirma teste/medição em primeira mão, mas não há "
            "evidencia_medicao estruturada; a afirmação não vale como prova"
        )

    # 4) cruzamento declarado e comprovado por >=2 domínios independentes.
    fontes = [*links, *(fontes_cruzadas or [])]
    dominios = {_dominio(fonte) for fonte in fontes if _dominio(fonte)}
    if tem_cruzamento and len(dominios) >= 2:
        criterios.append("cruzamento_2fontes")
    elif tem_cruzamento:
        avisos.append(
            f"cruzamento_2fontes não comprovado: {len(dominios)} domínio(s) "
            "independente(s) de 2 exigidos"
        )

    if criterios:
        return {"veredito": "APROVADO", "criterios": sorted(set(criterios)),
                "total_criterios": len(set(criterios)),
                "motivo": "valor_acrescentado",
                "ficha_tecnica": bool(_FICHA_TECNICA.search(alvo)),
                "aviso": "", "avisos": avisos,
                "evidencia_por_produto": "nao_aplicada"}

    return {
        "veredito": "BLOQUEADO", "criterios": [], "total_criterios": 0,
        "motivo": "sem_valor_acrescentado",
        "ficha_tecnica": bool(_FICHA_TECNICA.search(alvo)),
        "aviso": ("Nenhum dos 4 critérios da regra 14. Reescrever a fonte e publicar "
                  "= 'replicated content' (SQRG 4.6.6: 'Lowest, even if the page assigns "
                  "credit'). O item deve sair como link no digest, não como artigo."),
        "avisos": avisos,
        "evidencia_por_produto": "nao_aplicada",
    }


def gate_publicacao(titulo: str = "", texto: str = "", links: list = None,
                    tem_video: bool = False, tem_mediacao: bool = False,
                    tem_cruzamento: bool = False, fontes_cruzadas: list = None,
                    evidencia_video: dict = None,
                    evidencia_medicao: dict = None,
                    produtos: list = None,
                    exigir_produtos: bool = False) -> dict:
    """Atalho: roda compliance + valor. BLOQUEADO se qualquer um dos dois barrar."""
    comp = filtrar_conteudo(titulo, texto)
    val = filtrar_valor_acrescentado(titulo, texto, links, tem_video,
                                     tem_mediacao, tem_cruzamento, fontes_cruzadas,
                                     evidencia_video, evidencia_medicao,
                                     produtos=produtos,
                                     exigir_produtos=exigir_produtos)
    if comp["veredito"] == "BLOQUEADO":
        return comp
    if val["veredito"] == "BLOQUEADO":
        return val
    out = dict(comp)
    out["criterios_valor"] = val["criterios"]
    out["avisos_valor"] = val.get("avisos", [])
    out["evidencia_por_produto"] = val.get("evidencia_por_produto", "nao_aplicada")
    out["criterios_por_produto"] = val.get("criterios_por_produto", {})
    out["produtos_sem_valor"] = val.get("produtos_sem_valor", [])
    return out
