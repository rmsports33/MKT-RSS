"""
mkt_flow_p0.comparativo_contract — contrato estruturado de comparativo e
adaptador para o MCP `create_comparativo` (M04.17B, 21/10/2026).

O PROBLEMA que este módulo resolve
---------------------------------
O redator (`bot-redator-artigo`, `gerar_comparativo`) devolve uma **página
HTML completa** (`<!DOCTYPE>`, `<html>`, `<head>` com JSON-LD, `<body>`). O
`wp_publisher` do MKT-RSS mandava esse documento inteiro no `content`, e o
criava como `post_type=post` — não como `comparativo`. O lado WordPress
(MCP `create_comparativo`) espera outra coisa: campos estruturados.

Pior: no caminho antigo, as **evidências se perdiam**. O preço, a data de
captura e a fonte de cada produto ficavam espalhados no HTML, e o gate de
valor (M04.17A) não conseguia provar nada por produto. Um comparativo com
preço de um produto só era aprovado por inteiro.

O CONTRATO
-----------
`construir_contrato` transforma a entrada estruturada do redator
(`modelos` + `price_history`) em um **contrato** que carrega a evidência de
CADA produto, e esse contrato:

1. `validar_contrato` — valida a estrutura (fail-closed);
2. `avaliar_contrato` — roda o gate de valor **por produto** (M04.17A);
3. `contrato_para_mcp` — vira os parâmetros exatos de `create_comparativo`.

O contrato é a ponte: a evidência que o gate aprova é a mesma evidência que
chega ao WordPress. Se um produto não tem evidência própria, o comparativo
não é publicado — nem inteiro, nem pela metade.

Sem dependência fora da biblioteca padrão (o CI instala `requirements/base.txt`,
que não traz bs4 nem lxml).
"""
import re
from datetime import datetime

# Limites do lado WordPress (`conexo_mcp_tool_create_comparativo`):
# products/notas/buys são truncados em 3 e crits em 6. Truncar em SILÊNCIO
# perderia a evidência de um produto — por isso aqui o excesso é ERRO.
MAX_PRODUTOS_MCP = 3
MAX_CRITERIOS_MCP = 6

# Critérios que PROVAM valor acrescentado dentro de um COMPARATIVO.
#
# O criterion 2 do gate (`fonte_primaria`) é fraco para comparativo: a ficha
# de quase todo produto tem link do fabricante, então `fonte_primaria` approves
# qualquer comparativo que só reúna ficha de fabricante — que é exatamente o
# cenário "replicated content" da SQRG 4.6.6. Num comparativo, o valor vem
# do PREÇO datado, da MEDIÇÃO própria, do VÍDEO transcrito ou do CRUZAMENTO
# de fontes — não de repetir a ficha que o fabricante já publicou.
CRITERIOS_COMPARATIVOS = frozenset({
    "preco_br_data", "video_transcrito", "medicao_propria", "cruzamento_2fontes",
})

_RE_BODY = re.compile(r"<body\b[^>]*>(.*?)</body>", re.IGNORECASE | re.DOTALL)
_RE_HEAD = re.compile(r"<head\b[^>]*>.*?</head>", re.IGNORECASE | re.DOTALL)
_RE_SCRIPT = re.compile(r"<script\b[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL)
_RE_DOCTYPE = re.compile(r"<!doctype[^>]*>", re.IGNORECASE)
_RE_TAG_HTML = re.compile(r"</?html\b[^>]*>", re.IGNORECASE)
_RE_TAG_HEAD = re.compile(r"</?head\b[^>]*>", re.IGNORECASE)
_RE_TAG_BODY = re.compile(r"</?body\b[^>]*>", re.IGNORECASE)
_RE_URL = re.compile(r"^https?://", re.IGNORECASE)
_RE_PRECO_PTBR = re.compile(r"^\d{1,3}(\.\d{3})*,\d{2}$")


class ContratoInvalido(ValueError):
    """Contrato que não pode virar parâmetro de MCP. Carrega os erros."""

    def __init__(self, erros, avisos=None):
        self.erros = list(erros)
        self.avisos = list(avisos or [])
        super().__init__("; ".join(self.erros) if self.erros else "contrato invalido")


# --- Normalizadores ---------------------------------------------------------

def normalizar_data_captura(valor) -> str:
    """'2026-09-01' -> '01/09/2026'. Data inexistente -> ''.

    O redator grava a data em ISO; o gate (M04.17A) só reconhece
    DD/MM/AAAA. A conversão é feita AQUI, num lugar só, e a data é validada
    de verdade: '31/02/2026' e '2026-02-31' não viram evidência.
    """
    texto = str(valor or "").strip()
    if not texto:
        return ""
    texto = texto.split("T")[0].split(" ")[0]
    for formato in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(texto, formato).strftime("%d/%m/%Y")
        except ValueError:
            continue
    return ""


def normalizar_preco(valor) -> str:
    """1500.5 -> '1.500,50'; '1.600,00' -> '1.600,00'; inválido -> ''."""
    if valor is None or isinstance(valor, bool):
        return ""
    if isinstance(valor, (int, float)):
        try:
            inteiro = f"{float(valor):,.2f}"
        except (TypeError, ValueError):
            return ""
        return inteiro.replace(",", "X").replace(".", ",").replace("X", ".")
    texto = str(valor).strip()
    if not texto:
        return ""
    texto = re.sub(r"^R\$", "", texto, flags=re.IGNORECASE).strip()
    if _RE_PRECO_PTBR.match(texto):
        return texto
    numero = texto.replace(".", "").replace(",", ".")
    try:
        return f"{float(numero):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return ""


def _eh_url(valor) -> bool:
    return bool(_RE_URL.match(str(valor or "").strip()))


# --- HTML -------------------------------------------------------------------

def extrair_corpo_html(html: str) -> str:
    """Tira documento completo e devolve só o corpo.

    O redator devolve página inteira; mandar isso no `content` reproduziu em
    produção o defeito que a auditoria do M04.16 encontrou (`</button></p>`
    dentro de `<nav>`, `<p>      <script>`). O `wp_kses_post` do WP joga
    `<script>` fora, mas deixa o HTML quebrado — então o script é removido
    aqui, antes.
    """
    texto = str(html or "")
    corpo = _RE_BODY.search(texto)
    trecho = corpo.group(1) if corpo else texto
    trecho = _RE_HEAD.sub("", trecho)
    trecho = _RE_SCRIPT.sub("", trecho)
    trecho = _RE_DOCTYPE.sub("", trecho)
    trecho = _RE_TAG_HEAD.sub("", trecho)
    trecho = _RE_TAG_BODY.sub("", trecho)
    trecho = _RE_TAG_HTML.sub("", trecho)
    return trecho.strip()


# --- Construção do contrato -------------------------------------------------

def _preco_do_historico(price_history, nome):
    """Último ponto válido de preço do produto: (preço, data, fonte).

    O ponto do redator é {"data": "2026-09-01", "preco": 1500.5}. A fonte
    (link do marketplace) é OPCIONAL no histórico: sem ela, o preço e a data
    existem mas não provam de onde vieram — e o gate não aceita como
    evidência. A ausência vira aviso, nunca aprovação silenciosa.

    M04.17D: o preço é guardado **no formato que o gate lê**. A regex do gate
    (`_PRECO_BR`) exige o símbolo "R$" — "5.999,00" sem o símbolo NÃO casa, e
    o critério `preco_br_data` ficava INALCANÇÁVEL pela cadeia real (achado no
    dry-run do M04.17D, com preço float de verdade). O gate NÃO foi
    afrouxado: quem mudou de lado foi o produtor, que agora entrega o preço
    como o gate espera.
    """
    pontos = (price_history or {}).get(nome) or []
    melhor = None
    for ponto in pontos:
        if not isinstance(ponto, dict):
            continue
        preco = normalizar_preco(ponto.get("preco"))
        data = normalizar_data_captura(ponto.get("data"))
        if not preco or not data:
            continue
        fonte = ""
        for chave in ("fonte", "url", "link", "fonte_preco"):
            if _eh_url(ponto.get(chave)):
                fonte = str(ponto.get(chave)).strip()
                break
        melhor = ("R$ " + preco, data, fonte)
    return melhor or ("", "", "")


def construir_contrato(
    modelos: list,
    price_history: dict = None,
    conteudo_html: str = "",
    titulo: str = "",
    categoria: str = "",
    cat_slug: str = "",
    veredito: str = "",
    notas: dict = None,
    compras: dict = None,
    criterios: list = None,
    evidencia_video: dict = None,
    evidencia_medicao: dict = None,
) -> dict:
    """Monta o contrato estruturado a partir da entrada do redator.

    modelos: [{nome, specs:{...}, fonte, ...}] — a mesma lista que o redator
    recebe. price_history: {nome: [{"data": "2026-09-01", "preco": 1500.5}]}.
    notas/compras: {nome: nota} e {nome: url_de_compra}.
    evidencia_video/evidencia_medicao: {nome: evidencia}.
    """
    produtos = []
    for modelo in (modelos or []):
        if not isinstance(modelo, dict):
            continue
        nome = str(modelo.get("nome") or "").strip()
        preco, data_captura, fonte_preco = _preco_do_historico(price_history, nome)
        fonte = str(modelo.get("fonte") or "").strip()
        produtos.append({
            "nome": nome,
            "nota": (notas or {}).get(nome),
            "compra": (compras or {}).get(nome),
            "ficha": dict(modelo.get("specs") or {}),
            "preco": preco,
            "data_captura": data_captura,
            "fonte_preco": fonte_preco,
            "fonte": fonte if _eh_url(fonte) else "",
            "evidencia_video": (evidencia_video or {}).get(nome),
            "evidencia_medicao": (evidencia_medicao or {}).get(nome),
        })

    return {
        "titulo": str(titulo or "").strip(),
        "categoria": str(categoria or "").strip(),
        "cat_slug": str(cat_slug or "").strip(),
        "conteudo_html": extrair_corpo_html(conteudo_html),
        "veredito": str(veredito or "").strip(),
        "produtos": produtos,
        "criterios": list(criterios or []),
    }


# --- Validação ---------------------------------------------------------------

def validar_contrato(contrato: dict) -> dict:
    """Validação estrutural, fail-closed. Devolve {ok, erros, avisos}."""
    erros = []
    avisos = []

    if not isinstance(contrato, dict):
        return {"ok": False, "erros": ["contrato invalido: esperado dicionario"], "avisos": []}

    if not contrato.get("titulo"):
        erros.append("titulo vazio")

    produtos = contrato.get("produtos") or []
    if len(produtos) < 2:
        erros.append(f"comparativo precisa de 2 ou 3 produtos (recebido: {len(produtos)})")
    if len(produtos) > MAX_PRODUTOS_MCP:
        erros.append(
            f"{len(produtos)} produtos: o MCP trunca em {MAX_PRODUTOS_MCP} e o excedente "
            "perderia a evidencia em silencio")

    nomes = []
    for indice, produto in enumerate(produtos):
        if not isinstance(produto, dict):
            # Entrada malformada vira ERRO, nunca exceção: exceção num gate
            # fail-closed vira passage indevida (ou queda) em quem chama.
            erros.append(f"produto #{indice + 1} invalido: esperado dicionario")
            continue
        nome = str(produto.get("nome") or "").strip()
        if not nome:
            erros.append(f"produto #{indice + 1} sem nome")
            continue
        nomes.append(nome)
        nota = produto.get("nota")
        if nota is None or nota == "":
            erros.append(f"produto '{nome}' sem nota")
        else:
            try:
                valor = float(str(nota).replace(",", "."))
            except (TypeError, ValueError):
                erros.append(f"produto '{nome}' com nota invalida: {nota!r}")
            else:
                if not 0 <= valor <= 10:
                    erros.append(f"produto '{nome}' com nota fora de 0-10: {valor}")
        compra = produto.get("compra")
        if compra and not _eh_url(compra):
            erros.append(f"produto '{nome}' com link de compra invalido: {compra!r}")
        if produto.get("preco") and not produto.get("fonte_preco"):
            avisos.append(
                f"produto '{nome}' tem preco e data, mas sem link de marketplace: "
                "o gate nao vai aceitar isso como evidencia")

    conteudo = contrato.get("conteudo_html") or ""
    if not conteudo.strip():
        erros.append("conteudo_html vazio")
    else:
        if _RE_DOCTYPE.search(conteudo) or _RE_TAG_HTML.search(conteudo) or _RE_TAG_HEAD.search(conteudo):
            erros.append(
                "conteudo_html ainda tem documento completo (doctype/html/head): "
                "o post receberia o documento inteiro")

    criterios = contrato.get("criterios") or []
    if not criterios:
        # M04.17D: um comparativo sem NENHUM criterio de comparação é um post
        # sem tabela — o `create_comparativo` gravaria `_conexo_crit_*` vazios
        # e o single-comparativo.php renderizaria uma página sem comparação.
        erros.append("comparativo sem nenhum criterio de comparacao: "
                     "a tabela de comparacao ficaria vazia")
    if len(criterios) > MAX_CRITERIOS_MCP:
        erros.append(
            f"{len(criterios)} criterios: o MCP trunca em {MAX_CRITERIOS_MCP}")
    vistos = set()
    for indice, criterio in enumerate(criterios):
        if not isinstance(criterio, dict):
            erros.append(f"criterio #{indice + 1} invalido: esperado dicionario")
            continue
        label = str(criterio.get("label") or "").strip()
        if not label:
            erros.append(f"criterio #{indice + 1} sem label")
        elif label in vistos:
            erros.append(f"criterio repetido: {label!r}")
        else:
            vistos.add(label)
        vals = criterio.get("vals")
        if not isinstance(vals, list):
            erros.append(f"criterio '{label or indice + 1}' sem lista de valores")
        elif len(vals) != len(produtos):
            erros.append(
                f"criterio '{label or indice + 1}' tem {len(vals)} valor(es) para "
                f"{len(produtos)} produto(s): a tabela ficaria desalinhada")
        win = criterio.get("win", -1)
        try:
            win_num = int(win)
        except (TypeError, ValueError):
            win_num = -1
        if win_num < -1 or win_num > max(len(produtos) - 1, 0):
            erros.append(f"criterio '{label or indice + 1}' com vencedor fora da faixa: {win!r}")

    return {"ok": not erros, "erros": erros, "avisos": avisos}


def avaliar_contrato(contrato: dict, exigir_comparativo: bool = True) -> dict:
    """Validação estrutural + gate de valor POR PRODUTO (M04.17A).

    É aqui que o contrato e a evidência se cruzam: os produtos do contrato
    viram os produtos do gate, e o gate decide se cada um tem valor próprio.

    `exigir_comparativo=True` (padrão) adiciona a regra do COMPARATIVO: cada
    produto precisa de um critério que prove valor acrescentado de verdade
    (preço datado, medição, vídeo ou cruzamento). Só `fonte_primaria` não
    basta — a ficha do fabricante já existe, e repetir ela não é valor.
    """
    from mkt_flow_p0.content_filter import filtrar_valor_acrescentado

    estrutura = validar_contrato(contrato)
    produtos = (contrato or {}).get("produtos") or []
    tem_cruzamento = bool((contrato or {}).get("criterios"))

    gate = filtrar_valor_acrescentado(
        titulo=(contrato or {}).get("titulo", ""),
        texto="",
        produtos=[
            {
                "nome": p.get("nome"),
                "preco": p.get("preco"),
                "data_captura": p.get("data_captura"),
                "fonte_preco": p.get("fonte_preco"),
                # Os links do PRODUTO: o marketplace do preço e a fonte da
                # ficha. São os dois independentes que provam o cruzamento.
                "links": [l for l in (p.get("fonte_preco"), p.get("fonte")) if l],
                "tem_cruzamento": tem_cruzamento,
                "evidencia_video": p.get("evidencia_video"),
                "evidencia_medicao": p.get("evidencia_medicao"),
            }
            for p in produtos
            if isinstance(p, dict)
        ],
    )
    erros = list(estrutura["erros"])
    if gate.get("veredito") != "APROVADO":
        for nome in gate.get("produtos_sem_valor") or []:
            erros.append(f"produto '{nome}' sem valor acrescentado proprio")
        if not gate.get("produtos_sem_valor"):
            erros.append(f"gate reprovou: {gate.get('motivo')}")

    if exigir_comparativo:
        por_produto = gate.get("criterios_por_produto") or {}
        for produto in produtos:
            if not isinstance(produto, dict):
                continue
            nome = str(produto.get("nome") or "").strip()
            criterios = set(por_produto.get(nome) or [])
            if not criterios:
                continue
            if not (criterios & CRITERIOS_COMPARATIVOS):
                erros.append(
                    f"produto '{nome}' so tem {sorted(criterios)}: em comparativo, "
                    "fonte primaria sozinha nao prova valor acrescentado (a ficha do "
                    "fabricante ja existe)")

    return {
        "ok": not erros,
        "erros": erros,
        "avisos": list(estrutura["avisos"]) + list(gate.get("avisos") or []),
        "gate": gate,
    }


# --- Adaptador para o MCP ----------------------------------------------------

def contrato_para_mcp(contrato: dict, exigir_evidencia: bool = True) -> dict:
    """Converte o contrato nos parâmetros exatos de `create_comparativo`.

    As três listas (`products`, `notas`, `buys`) saem do MESMO `produtos`, na
    mesma ordem — é isso que impede a dessincronia entre produto, nota e link
    de compra que o `array_slice` do WordPress não avisa.

    Levanta `ContratoInvalido` se o contrato não passar na validação (ou, com
    `exigir_evidencia=True`, se o gate de valor por produto reprovar).
    """
    if exigir_evidencia:
        avaliacao = avaliar_contrato(contrato)
        if not avaliacao["ok"]:
            raise ContratoInvalido(avaliacao["erros"], avaliacao["avisos"])
    else:
        estrutura = validar_contrato(contrato)
        if not estrutura["ok"]:
            raise ContratoInvalido(estrutura["erros"], estrutura["avisos"])

    produtos = (contrato or {}).get("produtos") or []
    crits = []
    for criterio in (contrato or {}).get("criterios") or []:
        if not isinstance(criterio, dict):
            continue
        label = str(criterio.get("label") or "").strip()
        if not label:
            continue
        vals = list(criterio.get("vals") or [])
        while len(vals) < len(produtos):
            vals.append("")
        crits.append({
            "label": label,
            "vals": [str(v) for v in vals[:MAX_PRODUTOS_MCP]],
            "win": int(criterio.get("win", -1)) if str(criterio.get("win", -1)).lstrip("-").isdigit() else -1,
        })

    return {
        "title": (contrato or {}).get("titulo", ""),
        "content": (contrato or {}).get("conteudo_html", ""),
        "products": [str(p.get("nome") or "") for p in produtos
                     if isinstance(p, dict)][:MAX_PRODUTOS_MCP],
        "notas": [p.get("nota") for p in produtos
                  if isinstance(p, dict)][:MAX_PRODUTOS_MCP],
        "buys": [str(p.get("compra") or "") for p in produtos
                 if isinstance(p, dict)][:MAX_PRODUTOS_MCP],
        "crits": crits[:MAX_CRITERIOS_MCP],
        "veredito": (contrato or {}).get("veredito", ""),
        "cat_slug": (contrato or {}).get("cat_slug", ""),
    }
