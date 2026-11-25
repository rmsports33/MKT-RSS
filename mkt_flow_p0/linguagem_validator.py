"""mkt_flow_p0.linguagem_validator — Detecção de erros de linguagem em texto editorial.

Detecta (sem corrigir automaticamente, salvo onde seguro):
- ortografia (dicionário PT-BR offline)
- tipografia (aspas, traços, espaços, números)
- caracteres suspeitos / de outros sistemas de escrita
- gramática simples (concordância nominal básica, crase)
- HTML estrutural (reaproveita html_paragrafos quando disponível)

Tudo é detecção; nenhuma alteração muda o sentido do texto sem revisão humana.
"""
from __future__ import annotations

import html as _html
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable

__all__ = [
    "ErroLinguagem",
    "RelatorioLinguagem",
    "validar_texto",
    "validar_html_estrutural",
    "detectar_caracteres_suspeitos",
    "detectar_tipografia",
    "detectar_ortografia_simples",
    "detectar_crase",
    "detectar_repeticao",
    "detectar_maiusculas_excesso",
    "detectar_tamanho_frase",
    "detectar_voz_passiva",
    "detectar_concordancia_simples",
    "detectar_redundancia",
    "detectar_subject_verb_agreement",
    "detectar_cliches_jargao",
    "detectar_linguagem_inclusiva",
    "detectar_urls_em_texto",
    "detectar_metacomentarios",
    "RelatorioVozEditorialMDA",
    "verificar_voz_editorial_mda",
]

# ---------------------------------------------------------------------------
# Constantes de idioma
# ---------------------------------------------------------------------------

VOGAIS_ABERTAS = "áâãàéêíîïóôõöúûüç"
VOGAIS_FECHADAS = "aàeèiìoòuù"
CONSOANTES = "bcdfghjklmnpqrstvwxyz"

# Letras do alfabeto latino estendido usado em PT-BR
LETRAS_PT = set(
    "abcdefghijklmnopqrstuvwxyz"
    "àáâãäåæçèéêëìíîïðñòóôõöøùúûüýÿ"
    "ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝŸ"
)

# Alfabetos "de outro sistema" suspeitos quando aparecem em texto editorial PT-BR
ALFABETOS_SUSPEITOS = {
    "cyrillic": ("\u0400-\u04FF", "cirílico"),
    "greek": ("\u0370-\u03FF", "grego"),
    "cjk": ("\u4E00-\u9FFF", "chinês/japonês (CJK unificado)"),
    "arabic": ("\u0600-\u06FF", "árabe"),
    "devanagari": ("\u0900-\u097F", "dévanagari"),
    "thai": ("\u0E00-\u0E7F", "tailandês"),
    "hangul": ("\uAC00-\uD7AF", "coreano (hangul)"),
    "hebrew": ("\u0590-\u05FF", "hebraico"),
    "georgian": ("\u10A0-\u10FF", "georgiano"),
    "armenian": ("\u0530-\u058F", "armênio"),
}

# Palavras masculinas que terminam em 'a' (exceção à regra simplificada)
MASCULINAS_TERMINADAS_A = {
    "problema", "sistema", "idioma", "programa", "drama", "poema",
    "clima", "tema", "dilema", "esquema", "diagrama", "planeta",
    "fanfarrão", "milagre", "rei", "mapa", "papa",
}

# Palavras femininas que terminam em 'o' (exceção)
FEMININAS_TERMINADAS_O = {"foto", "moto", "foto", "radio"}

# Palavras comuns PT-BR para verificação ortográfica offline (mínima, expansível)
PALAVRAS_PT_COMUNS = {
    "a", "o", "as", "os", "um", "uma", "uns", "umas", "de", "do", "da", "dos",
    "das", "em", "no", "na", "nos", "nas", "por", "pelo", "pela", "pelos",
    "pelas", "com", "sem", "sobre", "entre", "para", "per", "pro", "e", "ou",
    "mas", "porém", "contudo", "entretanto", "todavia", "no entanto", "logo",
    "portanto", "assim", "então", "logo", "pois", "como", "quando", "onde",
    "que", "qual", "quem", "qualquer", "todo", "toda", "todos", "todas",
    "muito", "muitos", "pouco", "poucos", "mais", "menos", "muito",
    "bem", "mal", "melhor", "pior", "grande", "pequeno", "alto", "baixo",
    "novo", "velho", "antigo", "moderno", "fácil", "difícil", "rápido", "lento",
    "dia", "noite", "hoje", "ontem", "amanhã", "sempre", "nunca", "às vezes",
    "aqui", "ali", "lá", "cá", "acima", "abaixo", "dentro", "fora", "perto",
    "longe", "sim", "não", "talvez", "quase", "já", "ainda", "agora", "então",
    "ser", "estar", "ter", "haver", "fazer", "ir", "vir", "querer", "poder",
    "dever", "saber", "conhecer", "dar", "ficar", "chegar", "sair", "entrar",
    "passar", "ficar", "deixar", "parecer", "tornar", "começar", "terminar",
    "continuar", "esperar", "desejar", "precisar", "gostar", "odiar", "amar",
    "achar", "pensar", "crer", "acreditar", "duvidar", "esquecer", "lembrar",
    "saber", "conhecer", "entender", "compreender", "aprender", "ensinar",
    "dizer", "falar", "contar", "narrar", "relatar", "explicar", "descrever",
    "mostrar", "indic", "apontar", "informar", "comunicar",
    "anunciar", "declarar", "afirmar", "neg", "repetir", "responder", "perguntar",
    "pedir", "ordenar", "sugerir", "recomendar", "avisar", "alertar",
    "lembrar", "esquecer", "perdoar", "agradecer", "saudar", "cumprimentar",
    "abraçar", "beijar", "receber", "entregar", "levar", "trazer",
    "buscar", "procurar", "encontrar", "achar", "descobrir", "inventar", "criar",
    "fazer", "construir", "montar", "desmontar", "abrir", "fechar", "ligar",
    "desligar", "acender", "apagar", "subir", "descer", "entrar", "sair", "voltar",
    "ficar", "partir", "chegar", "sair", "viajar", "caminhar", "correr", "andar",
    "parar", "esperar", "sentar", "deitar", "levantar", "dormir", "acordar",
    "comer", "beber", "fumar", "cozinhar", "limpar", "lavar", "passar",
    "dobrar", "cortar", "colar", "unir", "separar", "misturar", "dividir",
    "multiplicar", "somar", "subtrair", "calcular", "medir", "pesar", "contar",
    "ler", "escrever", "desenhar", "pintar", "tocar", "ouvir", "ver", "olhar",
    "observar", "assistir", "prestar atenção", "sentir", "cheirar", "provar",
    "experimentar", "testar", "verificar", "checar", "confirmar", "negar",
    "aceitar", "recusar", "permitir", "proibir", "autorizar", "mandar", "pedir",
    "solicitar", "exigir", "exigência", "necessidade", "precisão", "importância",
    "valor", "custo", "preço", "dinheiro", "pagamento", "receita", "despesa",
    "lucro", "prejuízo", "ganho", "perda", "investimento", "economia", "finança",
    "banco", "moeda", "real", "dólar", "euro", "centavo", "nota", "moeda",
    "cheque", "cartão", "crédito", "débito", "empréstimo", "financiamento",
    "juros", "taxa", "imposto", "tarifa", "multa", "salário", "vencimento",
    "pagamento", "recebimento", "fatura", "boleto", "recibo", "comprovante",
    "contrato", "acordo", "convênio", "lei", "regra", "norma", "direito",
    "dever", "obrigação", "responsabilidade", "culpa", "erro", "acerto",
    "verdade", "mentira", "fato", "opinião", "ideia", "pensamento", "conceito",
    "teoria", "hipótese", "prova", "evidência", "argumento", "razão", "causa",
    "efeito", "consequência", "resultado", "objetivo", "meta", "plano",
    "estratégia", "tática", "método", "processo", "procedimento", "passo",
    "etapa", "fase", "momento", "tempo", "hora", "minuto", "segundo", "dia",
    "semana", "mês", "ano", "século", "milenio", "era", "época", "idade",
    "período", "tempo", "dur", "duração", "início", "fim", "começo", "término",
    "prazo", "limite", "fronteira", "borda", "margem", "centro", "meio",
    "interior", "exterior", "superfície", "fundo", "topo", "base", "lado",
    "esquerda", "direita", "cima", "baixo", "frente", "trás", "perto", "longe",
    "perto", "próximo", "distante", "adianto", "atrás", "antes", "depois",
    "durante", "enquanto", "até", "desde", "após", "antes", "contra", "sem",
    "com", "conforme", "segundo", "de acordo com", "graças a", "devido a",
    "por causa de", "graças", "mediante", "por meio de", "através de", "via",
    "por", "para", "per", "pro", "sobre", "em", "no", "na", "nos", "nas",
    "de", "do", "da", "dos", "das", "a", "à", "ao", "aos", "às",
}

# Palavras que devem ter acento (exemplos comuns de erro)
ACENTO_OBRIGATORIO = {
    # Chave = palavra sem acento (erro provável), Valor = forma correta
    "so": "só",           # advérbio: "só" (apenas) precisa de acento
    "só": None,           # já tem acento — não marcar como erro
    "péra": "pera",       # já tem acento — não marcar como erro
    "avó": None,          # já tem acento — não marcar como erro
}

# ---------------------------------------------------------------------------
# Estrutura de resultado
# ---------------------------------------------------------------------------


@dataclass
class ErroLinguagem:
    codigo: str
    tipo: str  # ortografia | tipografia | caractere | gramática | html
    severidade: str  # crítica | alta | média | baixa
    trecho: str
    posicao: int
    descricao: str
    sugestao: str | None = None


@dataclass
class RelatorioLinguagem:
    texto: str
    erros: list[ErroLinguagem] = field(default_factory=list)
    total_palavras: int = 0
    total_caracteres: int = 0
    palavras_desconhecidas: list[str] = field(default_factory=list)

    @property
    def tem_erro_critico(self) -> bool:
        return any(e.severidade == "crítica" for e in self.erros)

    @property
    def contagem_por_tipo(self) -> dict[str, int]:
        cont: dict[str, int] = {}
        for e in self.erros:
            cont[e.tipo] = cont.get(e.tipo, 0) + 1
        return cont

    @property
    def contagem_por_severidade(self) -> dict[str, int]:
        cont: dict[str, int] = {}
        for e in self.erros:
            cont[e.severidade] = cont.get(e.severidade, 0) + 1
        return cont


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------

def _limpar_texto_html(texto: str) -> str:
    """Remove tags HTML e decodifica entidades para análise de linguagem."""
    if not texto:
        return ""
    sem_tags = re.sub(r"<[^>]+>", " ", texto)
    return _html.unescape(sem_tags)


def _palavras(texto: str) -> list[str]:
    """Extrai palavras (sequências de letras) do texto."""
    return re.findall(r"[A-Za-zÀ-ÿ]+", texto)


def _tem_caractere_suspeito(caractere: str) -> tuple[bool, str | None]:
    """Verifica se caractere pertence a alfabeto suspeito."""
    cp = ord(caractere)
    for chave, (intervalo, nome) in ALFABETOS_SUSPEITOS.items():
        inicio, fim = intervalo.split("-")
        if ord(inicio) <= cp <= ord(fim):
            return True, nome
    return False, None


# ---------------------------------------------------------------------------
# Detecções
# ---------------------------------------------------------------------------

def detectar_caracteres_suspeitos(texto: str) -> list[ErroLinguagem]:
    """Caracteres de alfabetos não latinos, emoji, zero/letra O, full-width."""
    erros: list[ErroLinguagem] = []
    for i, ch in enumerate(texto):
        suspeito, nome = _tem_caractere_suspeito(ch)
        if suspeito:
            erros.append(ErroLinguagem(
                codigo="CHAR-SUSPEITO",
                tipo="caractere",
                severidade="alta",
                trecho=ch,
                posicao=i,
                descricao=f"Caractere de alfabeto {nome} fora do contexto PT-BR",
                sugestao="Remover ou substituir por equivalente latino",
            ))
        # Emoji e símbolos fora do esperado
        cat = unicodedata.category(ch)
        if cat.startswith("So"):  # Símbolo outro (inclui emoji)
            erros.append(ErroLinguagem(
                codigo="CHAR-EMOJI",
                tipo="caractere",
                severidade="média",
                trecho=ch,
                posicao=i,
                descricao="Emoji ou símbolo não texto detectado",
                sugestao="Remover",
            ))
        # Zero vs letra O (suspeito quando o dígito 0 aparece entre letras)
        if ch == "0":
            inicio = max(0, i - 1)
            fim = min(len(texto), i + 2)
            contexto = texto[inicio:fim]
            if re.search(r"[A-Za-zÀ-ÿ]", contexto):
                erros.append(ErroLinguagem(
                    codigo="CHAR-ZERO-O",
                    tipo="caractere",
                    severidade="baixa",
                    trecho=ch,
                    posicao=i,
                    descricao="Dígito zero (0) próximo a letras (possível confusão com letra O)",
                    sugestao="Verificar se é número ou letra",
                ))
        # Caractere de largura plena (full-width)
        if "\uFF00" <= ch <= "\uFFEF":
            erros.append(ErroLinguagem(
                codigo="CHAR-FULLWIDTH",
                tipo="caractere",
                severidade="média",
                trecho=ch,
                posicao=i,
                descricao="Caractere de largura plena (full-width)",
                sugestao="Converter para caractere meia largura",
            ))
    return erros


def detectar_tipografia(texto: str) -> list[ErroLinguagem]:
    """Aspas retas, traços, espaços duplos, espaço antes de pontuação, números."""
    erros: list[ErroLinguagem] = []

    # Aspas retas "
    for m in re.finditer(r'"', texto):
        erros.append(ErroLinguagem(
            codigo="TIPO-ASPAS-RETAS",
            tipo="tipografia",
            severidade="baixa",
            trecho='"',
            posicao=m.start(),
            descricao="Aspas retas detectadas (uso aspas curvas “ ” em texto editorial)",
            sugestao='Substituir por “ ”',
        ))

    # Traço hífen usado como travessão ( - entre espaços )
    for m in re.finditer(r"\s-\s", texto):
        erros.append(ErroLinguagem(
            codigo="TIPO-HIFEN-TRAVESSAO",
            tipo="tipografia",
            severidade="baixa",
            trecho="-",
            posicao=m.start(),
            descricao="Hífen usado como travessão (use — ou –)",
            sugestao='Substituir por " — "',
        ))

    # Espaço duplo
    for m in re.finditer(r"  +", texto):
        erros.append(ErroLinguagem(
            codigo="TIPO-ESPACO-DUPLO",
            tipo="tipografia",
            severidade="baixa",
            trecho=m.group(0),
            posicao=m.start(),
            descricao="Espaço duplo ou mais",
            sugestao="Usar um único espaço",
        ))

    # Espaço antes de pontuação final
    for m in re.finditer(r"\s+([.!?,:;])", texto):
        erros.append(ErroLinguagem(
            codigo="TIPO-ESPACO-PONTUACAO",
            tipo="tipografia",
            severidade="média",
            trecho=m.group(0),
            posicao=m.start(),
            descricao="Espaço antes de pontuação",
            sugestao="Remover espaço antes da pontuação",
        ))

    # Número com ponto como milhar (padrão PT-BR usa ponto) ou vírgula decimal
    for m in re.finditer(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?", texto):
        # Isso é padrão PT-BR, não é erro por si só. Só marca se houver mistura.
        pass

    # Número decimal com ponto (padrão EN) em texto PT-BR
    for m in re.finditer(r"\d+\.\d+(?!\d)", texto):
        erros.append(ErroLinguagem(
            codigo="TIPO-NUMERO-PONTO-DECIMAL",
            tipo="tipografia",
            severidade="baixa",
            trecho=m.group(0),
            posicao=m.start(),
            descricao="Número decimal com ponto (padrão PT-BR usa vírgula)",
            sugestao="Usar vírgula como separador decimal (ex: 10,50)",
        ))

    return erros


def detectar_ortografia_simples(texto: str) -> list[ErroLinguagem]:
    """Verificação ortográfica básica contra dicionário offline mínimo."""
    erros: list[ErroLinguagem] = []
    palavras_vistas: set[str] = set()

    for palavra in _palavras(texto):
        palavra_lower = palavra.lower()
        if palavra_lower in palavras_vistas:
            continue
        palavras_vistas.add(palavra_lower)

        # Ignorar siglas (tudo maiúsculo, 2+ letras)
        if len(palavra) >= 2 and palavra.isupper():
            continue
        # Ignorar números misturados
        if re.search(r"\d", palavra):
            continue
        # Ignorar URLs
        if palavra.startswith(("http", "www")):
            continue
        # Ignorar prováveis nomes próprios (inicial maiúscula, resto minúsculo)
        if len(palavra) >= 3 and palavra[0].isupper() and palavra[1:].islower():
            continue

        # Verificar acento obrigatório óbvio (ex: "so" vs "só")
        if palavra_lower in ACENTO_OBRIGATORIO:
            sugestao = ACENTO_OBRIGATORIO[palavra_lower]
            if sugestao is None:
                continue  # já tem acento correto
            erros.append(ErroLinguagem(
                codigo="ORTO-ACENTO",
                tipo="ortografia",
                severidade="média",
                trecho=palavra,
                posicao=texto.find(palavra),
                descricao=f"Palavra '{palavra}' provavelmente precisa de acento",
                sugestao=ACENTO_OBRIGATORIO[palavra_lower],
            ))
            continue

        # Palavra não está no dicionário mínimo
        if palavra_lower not in PALAVRAS_PT_COMUNS:
            suspeita = False
            # Letra triplicada (ex: "comemmo")
            if re.search(r"(.)\1{2,}", palavra_lower):
                suspeita = True
            # Consoante dupla no meio da palavra (ex: "nn", "ll")
            # Só marca se NÃO for dupla válida do português (cc, rr, ss, ll, nn)
            duplas_validas = {"cc", "rr", "ss", "ll", "nn"}
            if re.search(r"[bcdfghjklmnpqrstvwxyz]{2}", palavra_lower):
                for i in range(1, len(palavra_lower) - 1):
                    par = palavra_lower[i:i + 2]
                    if (
                        palavra_lower[i] == palavra_lower[i + 1]
                        and palavra_lower[i] in "bcdfghjklmnpqrstvwxyz"
                        and par not in duplas_validas
                    ):
                        suspeita = True
                        break
            # Consoantes consecutivas > 3 (vogal faltando)
            if re.search(r"[bcdfghjklmnpqrstvwxyz]{4,}", palavra_lower):
                suspeita = True
            # Número misturado dentro da palavra
            if re.search(r"[A-Za-zÀ-ÿ]\d[A-Za-zÀ-ÿ]", palavra):
                suspeita = True
            if suspeita:
                erros.append(ErroLinguagem(
                    codigo="ORTO-PALAVRA-DESCONHECIDA",
                    tipo="ortografia",
                    severidade="média",
                    trecho=palavra,
                    posicao=texto.find(palavra),
                    descricao="Padrão de erro ortográfico suspeito",
                    sugestao="Verificar ortografia",
                ))

    return erros


def detectar_crase(texto: str) -> list[ErroLinguagem]:
    """Detecta crase ausente antes de substantivo feminino após preposição 'a'."""
    erros: list[ErroLinguagem] = []
    # Padrão simples: " a " seguido de palavra feminina (termina em 'a')
    for m in re.finditer(r"\ba\s+([a-zà-ÿ]+)", texto, re.I):
        palavra = m.group(1)
        if len(palavra) < 3:
            continue
        # Não é crase se a palavra começa com vogal
        if palavra[0] in "aeiouàáâãäåèéêëìíîïòóôõöùúûü":
            continue
        # Não é crase se for nome próprio (inicial maiúscula no texto original)
        # (a Agência, a Anatel — não leva crase)
        trecho_original = m.group(0)
        if any(c.isupper() for c in palavra):
            continue
        if palavra.endswith("a") and palavra not in MASCULINAS_TERMINADAS_A:
            erros.append(ErroLinguagem(
                codigo="GRAM-CRASE",
                tipo="gramática",
                severidade="média",
                trecho=m.group(0),
                posicao=m.start(),
                descricao=f"Possível crase ausente antes de '{palavra}'",
                sugestao=f"Usar 'à {palavra}' se for crase correta",
            ))
    return erros


_METACOMENTARIOS = re.compile(
    r"\b(?:este\s+texto\s+segue\s+o\s+briefing\s+editorial|"
    r"como\s+modelo\s+de\s+linguagem|"
    r"este\s+artigo\s+foi\s+(?:gerado|produzido)\s+(?:por|com)\s+(?:um\s+)?prompt|"
    r"como\s+assistente\s+de\s+ia|"
    r"como\s+ia\s+assistente|"
    r"este\s+conteúdo\s+foi\s+(?:criado|elaborado)\s+(?:por|com)\s+ia|"
    r"observação\s+do\s+editor|"
    r"nota\s+editorial|"
    r"pendente\s+de\s+revisão\s+humana\b)",
    re.IGNORECASE,
)

_PLACEHOLDER_MARCADORES = re.compile(
    r"\[(?:\s*(?:jogo|produto|modelo|marca|nome|empresa|autor|cidade|"
    r"pre[cç]o|dado|n[uú]mero|fonte|link|imagem|data)"
    r"(?:\s+(?:x|y|z|a\s+definir|a\s+confirmar))?\s*|"
    r"(?:inserir|preencher|adicionar|substituir|todo|tbd|xxx)"
    r"[^]\n]{0,80}|link\s+afiliado)\]",
    re.IGNORECASE,
)


def detectar_metacomentarios(texto: str) -> list[ErroLinguagem]:
    """Metacomentários e marcadores editoriais que não devem ir ao artigo publicado."""
    erros: list[ErroLinguagem] = []

    for m in _METACOMENTARIOS.finditer(texto):
        erros.append(ErroLinguagem(
            codigo="META-COMENTARIO",
            tipo="metacomentario",
            severidade="alta",
            trecho=m.group(0)[:80],
            posicao=m.start(),
            descricao="Metacomentário sobre produção/briefing encontrado no corpo do texto",
            sugestao="Remover o metacomentário; manter apenas o conteúdo editorial",
        ))

    for m in _PLACEHOLDER_MARCADORES.finditer(texto):
        erros.append(ErroLinguagem(
            codigo="META-PLACEHOLDER",
            tipo="metacomentario",
            severidade="crítica",
            trecho=m.group(0)[:80],
            posicao=m.start(),
            descricao="Marcador editorial não resolvido (ex: [fonte], [inserir X], TODO)",
            sugestao="Resolver o marcador com informação real ou retirar o trecho",
        ))

    return erros


def validar_texto(texto: str, html_original: str | None = None) -> RelatorioLinguagem:
    """Executa todas as detecções de linguagem sobre o texto."""
    texto_limpo = _limpar_texto_html(texto)
    erros: list[ErroLinguagem] = []

    erros.extend(detectar_caracteres_suspeitos(texto_limpo))
    erros.extend(detectar_tipografia(texto_limpo))
    erros.extend(detectar_ortografia_simples(texto_limpo))
    erros.extend(detectar_crase(texto_limpo))
    erros.extend(detectar_metacomentarios(texto_limpo))  # deteccao de metacomentarios e placeholders
    erros.extend(detectar_repeticao(texto_limpo))
    erros.extend(detectar_maiusculas_excesso(texto_limpo))
    erros.extend(detectar_tamanho_frase(texto_limpo))
    erros.extend(detectar_voz_passiva(texto_limpo))
    erros.extend(detectar_concordancia_simples(texto_limpo))
    erros.extend(detectar_redundancia(texto_limpo))
    erros.extend(detectar_subject_verb_agreement(texto_limpo))
    erros.extend(detectar_cliches_jargao(texto_limpo))
    erros.extend(detectar_linguagem_inclusiva(texto_limpo))
    erros.extend(detectar_urls_em_texto(texto_limpo))

    if html_original:
        erros.extend(validar_html_estrutural(html_original))

    return RelatorioLinguagem(
        texto=texto,
        erros=erros,
        total_palavras=len(_palavras(texto_limpo)),
        total_caracteres=len(texto_limpo),
        palavras_desconhecidas=[
            e.trecho for e in erros if e.codigo == "ORTO-PALAVRA-DESCONHECIDA"
        ],
    )


def detectar_repeticao(texto: str) -> list[ErroLinguagem]:
    """Palavra repetida em sequência ou excessiva em curta janela."""
    erros: list[ErroLinguagem] = []
    palavras = _palavras(texto)

    # Repetição imediata: "o o", "que que"
    for i in range(len(palavras) - 1):
        if palavras[i].lower() == palavras[i + 1].lower():
            erros.append(ErroLinguagem(
                codigo="ORTO-PALAVRA-REPETIDA",
                tipo="ortografia",
                severidade="média",
                trecho=f"{palavras[i]} {palavras[i+1]}",
                posicao=texto.find(palavras[i]),
                descricao="Palavra repetida em sequência",
                sugestao=f"Remover a segunda ocorrência de '{palavras[i]}'",
            ))

    # Palavra muito frequente em janela de 50 palavras (excluindo artigos/preposições)
    stopwords = {
        "a", "o", "as", "os", "um", "uma", "uns", "umas", "de", "do", "da",
        "dos", "das", "em", "no", "na", "nos", "nas", "por", "pelo", "pela",
        "e", "ou", "mas", "que", "com", "sem", "para", "porque", "por que",
    }
    janela = 50
    for i in range(0, len(palavras) - janela, 10):
        bloco = [p.lower() for p in palavras[i:i + janela] if p.lower() not in stopwords]
        from collections import Counter
        contagem = Counter(bloco)
        for palavra, qtd in contagem.items():
            if qtd >= 5 and len(palavra) > 3:
                erros.append(ErroLinguagem(
                    codigo="ORTO-PALAVRA-EXCESSIVA",
                    tipo="ortografia",
                    severidade="baixa",
                    trecho=palavra,
                    posicao=i,
                    descricao=f"Palavra '{palavra}' aparece {qtd}x em curta janela",
                    sugestao="Usar sinônimo ou reestruturar frase",
                ))
                break  # um alerta por janela

    return erros


def detectar_maiusculas_excesso(texto: str) -> list[ErroLinguagem]:
    """Palavras inteiras em maiúscula (grito) ou título caso inadequado."""
    erros: list[ErroLinguagem] = []
    for m in re.finditer(r"\b[A-ZÀ-Ü]{4,}\b", texto):
        palavra = m.group(0)
        # Ignorar siglas conhecidas e URLs
        if palavra in {"HTML", "CSS", "API", "SEO", "XML", "JSON", "HTTP", "HTTPS",
                       "WP", "CC", "BY", "SA", "NC", "ND", "TIM", "VIVO", "OI",
                       "CLARO", "ANATEL", "SENADO", "BRASIL"}:
            continue
        erros.append(ErroLinguagem(
            codigo="TIPO-MAIUSCULAS-EXCESSO",
            tipo="tipografia",
            severidade="baixa",
            trecho=palavra,
            posicao=m.start(),
            descricao="Palavra inteira em maiúscula (pode ser interpretado como grito)",
            sugestao="Usar maiúscula e minúscula normalmente",
        ))
    return erros


def detectar_tamanho_frase(texto: str) -> list[ErroLinguagem]:
    """Frases muito longas (possível falta de pontuação)."""
    erros: list[ErroLinguagem] = []
    # Divide por ponto, exclamação, interrogação
    frases = re.split(r"[.!?]+", texto)
    for frase in frases:
        frase = frase.strip()
        if not frase:
            continue
        qtd = len(_palavras(frase))
        if qtd > 60:
            erros.append(ErroLinguagem(
                codigo="GRAM-FRASE-MUITO-LONGA",
                tipo="gramática",
                severidade="baixa",
                trecho=frase[:80],
                posicao=texto.find(frase[:30]) if frase[:30] in texto else 0,
                descricao=f"Frase com {qtd} palavras (acima de 60)",
                sugestao="Dividir em frases menores",
            ))
    return erros


def detectar_voz_passiva(texto: str) -> list[ErroLinguagem]:
    """Construções de voz passiva excessivas (ser/estar + particípio)."""
    erros: list[ErroLinguagem] = []
    padrao = re.compile(
        r"\b(?:são|era|eram|será|seriam|foi|foram|sendo|estado|está|estão|"
        r"estava|estavam|esteve|estejam|ser|estar|ter sido|ter estado|"
        r"seriam|sendo)\s+"
        r"(?:[a-zà-ÿ]+(?:ado|ido|to|so|cho|to))",
        re.I,
    )
    for m in padrao.finditer(texto):
        erros.append(ErroLinguagem(
            codigo="GRAM-VOZ-PASSIVA",
            tipo="gramática",
            severidade="baixa",
            trecho=m.group(0),
            posicao=m.start(),
            descricao="Possível voz passiva (ser/estar + particípio)",
            sugestao="Considerar voz ativa para maior clareza",
        ))
    return erros


def detectar_concordancia_simples(texto: str) -> list[ErroLinguagem]:
    """Concordância nominal básica: artigo + adjetivo/ substantivo próximo."""
    erros: list[ErroLinguagem] = []
    # Padrão muito simples: "o/os" + palavra feminina (termina em 'a') ou
    # "a/as" + palavra masculina (termina em 'o')
    padrao_artigo = re.compile(
        r"\b(o|os|a|as|um|uma|uns|umas)\s+([a-zà-ÿ]+)",
        re.I,
    )
    femininas_terminais = {"a", "ão", "ade", "ice", "ez", "oz", "ura", "eza"}
    masculinas_terminais = {"o", "e", "l", "r", "n", "s"}

    for m in padrao_artigo.finditer(texto):
        artigo = m.group(1).lower()
        palavra = m.group(2).lower()
        if len(palavra) < 3:
            continue
        artigo_feminino = artigo in ("a", "as", "uma", "umas")
        palavra_feminina = (
            any(palavra.endswith(t) for t in femininas_terminais)
            and palavra not in MASCULINAS_TERMINADAS_A
        )
        palavra_masculina = (
            any(palavra.endswith(t) for t in masculinas_terminais)
            or palavra in MASCULINAS_TERMINADAS_A
        )

        if artigo_feminino and palavra_masculina and not palavra_feminina:
            erros.append(ErroLinguagem(
                codigo="GRAM-CONCORDANCIA-ARTIGO",
                tipo="gramática",
                severidade="média",
                trecho=m.group(0),
                posicao=m.start(),
                descricao=f"Possível discordância: '{artigo}' (feminino) com '{palavra}' (masculino)",
                sugestao="Verificar gênero do artigo ou do substantivo",
            ))
        elif not artigo_feminino and palavra_feminina and not palavra_masculina:
            erros.append(ErroLinguagem(
                codigo="GRAM-CONCORDANCIA-ARTIGO",
                tipo="gramática",
                severidade="média",
                trecho=m.group(0),
                posicao=m.start(),
                descricao=f"Possível discordância: '{artigo}' (masculino) com '{palavra}' (feminino)",
                sugestao="Verificar gênero do artigo ou do substantivo",
            ))

    return erros


def detectar_redundancia(texto: str) -> list[ErroLinguagem]:
    """Pleonasmos e expressões redundantes comuns em PT-BR."""
    erros: list[ErroLinguagem] = []
    redundantes = [
        (r"\bsubir para cima\b", "subir para cima", "subir"),
        (r"\bdescer para baixo\b", "descer para baixo", "descer"),
        (r"\bentrar para dentro\b", "entrar para dentro", "entrar"),
        (r"\bsair para fora\b", "sair para fora", "sair"),
        (r"\brepetir novamente\b", "repetir novamente", "repetir"),
        (r"\bvoltar novamente\b", "voltar novamente", "voltar"),
        (r"\bassistir presencialmente\b", "assistir presencialmente", "assistir"),
        (r"\bacordo prévio\b", "acordo prévio", "acordo"),
        (r"\bplanejamento antecipado\b", "planejamento antecipado", "planejamento"),
        (r"\bresultados finais\b", "resultados finais", "resultados"),
        (r"\bhora certa\b", "hora certa", "hora"),
        (r"\bpessoas físicas pessoas\b", "pessoas físicas", "pessoas"),
        (r"\banálise detalhada\b", "análise detalhada", "análise"),
        (r"\bproblema complexo\b", "problema complexo", "problema"),
        (r"\bsolução inovadora\b", "solução inovadora", "solução"),
    ]
    for padrao, achado, substituto in redundantes:
        for m in re.finditer(padrao, texto, re.I):
            erros.append(ErroLinguagem(
                codigo="ORTO-REDUNDANCIA",
                tipo="ortografia",
                severidade="baixa",
                trecho=achado,
                posicao=m.start(),
                descricao=f"Expressão redundante: '{achado}'",
                sugestao=f"Usar apenas '{substituto}'",
            ))
    return erros


def detectar_subject_verb_agreement(texto: str) -> list[ErroLinguagem]:
    """Concordância sujeito-verbo simples (terceira pessoa singular/plural)."""
    erros: list[ErroLinguagem] = []
    # Padrão muito heurístico: sujeito plural seguido de verbo em 3a pessoa singular
    sujeitos_plurais = {
        "eles", "elas", "nós", "vocês", "os", "as", "os pais", "as mães",
        "os filhos", "as filhas", "os dados", "as informações", "os artigos",
        "as notícias", "os relatórios", "as pesquisas", "os testes",
    }
    verbos_singular = {
        "é", "está", "tem", "faz", "diz", "vai", "vem", "quer", "pode",
        "deve", "sabe", "conhece", "dá", "fica", "chega", "sai", "entra",
        "passa", "deixa", "parece", "torna", "começa", "termina",
    }
    # Busca "eles/elas/nós/vocês" seguido de verbo singular próximo
    padrao = re.compile(
        r"\b(eles|elas|nós|vocês)\s+(\w+)",
        re.I,
    )
    for m in padrao.finditer(texto):
        sujeito = m.group(1).lower()
        verbo = m.group(2).lower()
        if verbo in verbos_singular:
            erros.append(ErroLinguagem(
                codigo="GRAM-CONCORDANCIA-SUJEITO-VERBO",
                tipo="gramática",
                severidade="alta",
                trecho=m.group(0),
                posicao=m.start(),
                descricao=f"Possível discordância sujeito-verbo: '{sujeito}' (plural) com '{verbo}' (singular)",
                sugestao=f"Usar forma plural do verbo para '{sujeito}'",
            ))
    return erros


def detectar_cliches_jargao(texto: str) -> list[ErroLinguagem]:
    """Clichês e jargões de negócio/técnico excessivos."""
    erros: list[ErroLinguagem] = []
    cliches = [
        "pensar fora da caixa",
        "colocar a mão na massa",
        "fazer a diferença",
        "em última análise",
        "no final das contas",
        "a longo prazo",
        "a curto prazo",
        "de maneira geral",
        "em termos gerais",
        "bom senso",
        "boa prática",
        "melhor prática",
        "ecossistema",
        "disruptivo",
        "escalável",
        "sinergia",
        "alavancar",
        "pain point",
        "insight",
        "benchmark",
        "case",
        "briefing",
        "deadline",
        "feedback",
        "hype",
        "rollout",
        "sprint",
        "workflow",
        "pipeline",
    ]
    for cliche in cliches:
        for m in re.finditer(re.escape(cliche), texto, re.I):
            erros.append(ErroLinguagem(
                codigo="TIPO-CLIQUE-JARGAO",
                tipo="tipografia",
                severidade="baixa",
                trecho=cliche,
                posicao=m.start(),
                descricao=f"Clichê ou jargão: '{cliche}'",
                sugestao="Substituir por expressão mais direta",
            ))
    return erros


def detectar_linguagem_inclusiva(texto: str) -> list[ErroLinguagem]:
    """Termos que podem não ser inclusivos (alerta apenas, não erro crítico)."""
    erros: list[ErroLinguagem] = []
    termos = [
        ("mankind", "humanidade"),
        ("guys", "pessoas / time"),
        ("manpower", "mão de obra / equipe"),
        ("blacklist", "lista de bloqueio"),
        ("whitelist", "lista de permissão"),
        ("master/slave", "primário/secundário"),
        ("consumidor médio", "consumidor típico"),
    ]
    for termo, substituto in termos:
        for m in re.finditer(re.escape(termo), texto, re.I):
            erros.append(ErroLinguagem(
                codigo="TIPO-LINGUAGEM-INCLUSIVA",
                tipo="tipografia",
                severidade="baixa",
                trecho=termo,
                posicao=m.start(),
                descricao=f"Termo pode não ser inclusivo: '{termo}'",
                sugestao=f"Considerar '{substituto}'",
            ))
    return erros


def detectar_urls_em_texto(texto: str) -> list[ErroLinguagem]:
    """URLs soltas no corpo do texto sem formatação de link."""
    erros: list[ErroLinguagem] = []
    padrao = re.compile(
        r"https?://[^\s<>\"]+",
        re.I,
    )
    for m in padrao.finditer(texto):
        erros.append(ErroLinguagem(
            codigo="HTML-URL-SOLTA",
            tipo="html",
            severidade="média",
            trecho=m.group(0)[:60],
            posicao=m.start(),
            descricao="URL solta no texto (não formatada como link)",
            sugestao="Formatar como link HTML ou Markdown",
        ))
    return erros


def validar_texto(texto: str, html_original: str | None = None) -> RelatorioLinguagem:
    """Executa todas as detecções de linguagem sobre o texto."""
    texto_limpo = _limpar_texto_html(texto)
    erros: list[ErroLinguagem] = []

    erros.extend(detectar_caracteres_suspeitos(texto_limpo))
    erros.extend(detectar_tipografia(texto_limpo))
    erros.extend(detectar_ortografia_simples(texto_limpo))
    erros.extend(detectar_crase(texto_limpo))
    erros.extend(detectar_repeticao(texto_limpo))
    erros.extend(detectar_maiusculas_excesso(texto_limpo))
    erros.extend(detectar_tamanho_frase(texto_limpo))
    erros.extend(detectar_voz_passiva(texto_limpo))
    erros.extend(detectar_concordancia_simples(texto_limpo))
    erros.extend(detectar_redundancia(texto_limpo))
    erros.extend(detectar_subject_verb_agreement(texto_limpo))
    erros.extend(detectar_cliches_jargao(texto_limpo))
    erros.extend(detectar_linguagem_inclusiva(texto_limpo))
    erros.extend(detectar_urls_em_texto(texto_limpo))

    if html_original:
        erros.extend(validar_html_estrutural(html_original))

    return RelatorioLinguagem(
        texto=texto,
        erros=erros,
        total_palavras=len(_palavras(texto_limpo)),
        total_caracteres=len(texto_limpo),
        palavras_desconhecidas=[
            e.trecho for e in erros if e.codigo == "ORTO-PALAVRA-DESCONHECIDA"
        ],
    )


def validar_html_estrutural(html: str) -> list[ErroLinguagem]:
    """Reaproveita detecção estrutural se html_paragrafos estiver disponível."""
    try:
        from mkt_flow_p0.html_paragrafos import listas_seguidas
    except Exception:
        return []

    erros: list[ErroLinguagem] = []
    if listas_seguidas(html) > 0:
        erros.append(ErroLinguagem(
            codigo="HTML-LISTAS-SEGUIDAS",
            tipo="html",
            severidade="alta",
            trecho="",
            posicao=0,
            descricao="Listas do mesmo tipo encostadas (sintoma de fragmentação)",
            sugestao="Executar reparo de parágrafos",
        ))
    return erros


def bloqueios_para_rascunho(relatorio) -> list[dict]:
    """Erros que impedem oferecer o rascunho para análise humana.

    Conservador: bloqueia apenas severidade crítica e problemas estruturais ou
    de caractere de severidade alta. Tipografia/gramática continuam como
    pendências sinalizadas, porque são heurísticas com falso positivo.
    """
    erros = relatorio.get("erros", []) if isinstance(relatorio, dict) else relatorio.erros
    bloqueios = []
    for erro in erros:
        item = erro if isinstance(erro, dict) else {
            "codigo": erro.codigo, "tipo": erro.tipo,
            "severidade": erro.severidade, "descricao": erro.descricao,
        }
        severidade = item.get("severidade")
        tipo = item.get("tipo")
        if severidade == "crítica" or (tipo in ("html", "caractere")
                                       and severidade in ("alta", "crítica")):
            bloqueios.append({
                "codigo": item.get("codigo"), "tipo": tipo,
                "severidade": severidade, "descricao": item.get("descricao"),
            })
    return bloqueios


# ---------------------------------------------------------------------------
# Integração com o módulo MDA (voz editorial e estilística)
# ---------------------------------------------------------------------------

@dataclass
class RelatorioVozEditorialMDA:
    """Relatório de voz editorial e estilística via módulo MDA (apenas diagnóstico)."""
    brief_sha256: str | None = None
    genero: str | None = None
    lente: str | None = None
    lente_nome: str | None = None
    plano_abertura: str | None = None
    plano_desenvolvimento: str | None = None
    plano_desfecho: str | None = None
    movimento_tese: str | None = None
    movimento_prova: str | None = None
    movimento_consequencia: str | None = None
    movimento_contrapeso: str | None = None
    movimento_veredito: str | None = None
    sinais_placeholder: list[str] = field(default_factory=list)
    sinais_estilo: list[str] = field(default_factory=list)
    sinais_tabela: list[str] = field(default_factory=list)
    status_substancia: str | None = None
    pendencias_substancia: list[str] = field(default_factory=list)
    scores_substancia: dict = field(default_factory=dict)
    recibos_faltantes: list[str] = field(default_factory=list)
    factual_approval: bool = False
    publication_authorized: bool = False


def verificar_voz_editorial_mda(
    markdown: str,
    brief: dict | None = None,
    review: dict | None = None,
    receipts: dict | None = None,
) -> RelatorioVozEditorialMDA:
    """Verifica voz editorial e estilística via módulo MDA (apenas diagnóstico).

    Usa `editorial_voice_adapter` (plano de voz, sinais de placeholder/estilo/tabela)
    e `editorial_substance` (avaliação substantiva e prontidão editorial).
    Nunca autoriza publicação; apenas sinaliza pendências para revisão humana.
    """
    relatorio = RelatorioVozEditorialMDA()

    # --- Plano de voz editorial (lente MDA por gênero) ---
    if brief is not None:
        try:
            from mkt_flow_p0.editorial_voice_adapter import (
                editorial_voice_plan,
                editorial_argument_plan,
                surface_style_signals,
                editorial_placeholder_signals,
                markdown_table_structure_signals,
            )
            plano = editorial_voice_plan(brief)
            argumento = editorial_argument_plan(brief)
            movimentos = argumento["moves"]

            relatorio.brief_sha256 = plano["brief_sha256"]
            relatorio.genero = plano["genre"]
            relatorio.lente = plano["lens"]
            relatorio.lente_nome = plano["lens_name"]
            relatorio.plano_abertura = plano["opening"]
            relatorio.plano_desenvolvimento = plano["development"]
            relatorio.plano_desfecho = plano["ending"]
            relatorio.movimento_tese = movimentos.get("thesis")
            relatorio.movimento_prova = movimentos.get("evidence")
            relatorio.movimento_consequencia = movimentos.get("consequence")
            relatorio.movimento_contrapeso = movimentos.get("tradeoff")
            relatorio.movimento_veredito = movimentos.get("closing")

            # Sinais de estilo (conectivos mecânicos, fechamento)
            estilo = surface_style_signals(markdown)
            relatorio.sinais_estilo = list(estilo.get("signals", []))

            # Sinais de placeholder / metacomentário
            placeholders = editorial_placeholder_signals(markdown)
            relatorio.sinais_placeholder = list(placeholders.get("signals", []))

            # Sinais de estrutura de tabela
            tabelas = markdown_table_structure_signals(markdown)
            relatorio.sinais_tabela = list(tabelas.get("signals", []))

        except Exception as exc:  # diagnóstico nunca bloqueia o pipeline
            relatorio.sinais_estilo.append(f"erro_mda_voz:{exc}")

    # --- Avaliação substantiva (MDA) ---
    if markdown and brief is not None:
        try:
            from mkt_flow_p0.editorial_substance import assess_editorial_release
            release = assess_editorial_release(markdown, brief=brief, review=review, receipts=receipts)
            relatorio.status_substancia = release.get("status")
            relatorio.pendencias_substancia = list(release.get("blockers", []))
            sub = release.get("substance", {})
            relatorio.scores_substancia = dict(sub.get("scores", {}))
            relatorio.factual_approval = bool(release.get("factual_approval"))
            relatorio.publication_authorized = bool(release.get("publication_authorized"))

            read = release.get("readiness", {})
            relatorio.recibos_faltantes = list(read.get("missing_receipts", []))

        except Exception as exc:
            relatorio.pendencias_substancia.append(f"erro_mda_substancia:{exc}")

    return relatorio
