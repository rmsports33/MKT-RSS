"""Avaliador de qualidade editorial do MKT-RSS (nota 0–100).

Lê o contrato único copiado para data/editorial-quality-v1.json e combina:
- nota assistida (rubrica 0–4 convertida, cinco critérios de 20 pontos);
- checagens determinísticas (fontes, links, imagem, voz, SEO, público BR);
- comparação com o mapa de raciocínio da referência Canaltech salva no projeto.

Nada aqui aprova publicação nem prova fatos. Um bloqueio limita a nota a 69.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from mkt_flow_p0.editorial_substance import (
    GENRES, assess_substance, content_hash, normalize_brief,
)

CONTRATO_PADRAO = Path(__file__).resolve().parent.parent / "data" / "editorial-quality-v1.json"
SITE = "conexotech.com.br"
LIMITE_COM_BLOQUEIO = 69
PESO_ASSISTIDA = 0.7
PESO_ESTRUTURA = 0.3
BR_PADRAO = re.compile(
    r"\b(brasil|brasileir\w*|reais?|anatel|gov\.br|com\.br|s[aã]o paulo|rio de janeiro)\b",
    re.I)


def _digest(dados):
    return hashlib.sha256(json.dumps(
        dados, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


def carregar_contrato(path=None):
    """Carrega e valida a cópia operacional do contrato canônico."""
    destino = Path(path) if path else CONTRATO_PADRAO
    dados = json.loads(destino.read_text(encoding="utf-8"))
    declarado = dados.get("contract_sha256")
    if not declarado or declarado != _digest(
            {k: v for k, v in dados.items() if k != "contract_sha256"}):
        raise ValueError("CONTRATO_HASH_INVALIDO")
    return dados


def _dominio(url):
    try:
        return (urlsplit(str(url or "")).hostname or "").lower()
    except ValueError:
        return ""


def _fontes(sources):
    if not isinstance(sources, dict):
        return []
    out = []
    for src in sources.get("sources") or []:
        if isinstance(src, dict) and isinstance(src.get("url"), str):
            out.append(src)
    return out


def _tem_br(texto):
    return bool(BR_PADRAO.search(str(texto or "")))


def _br_afirmativo(texto):
    """Só conta menção brasileira afirmativa; limite explicito não é invenção."""
    for frase in re.split(r"(?<=[.!?])\s+", str(texto or "")):
        if not BR_PADRAO.search(frase):
            continue
        if re.search(r"\b(sem|n[aã]o h[aá]|nao ha|falta|ausente|pendente|n[aã]o existe)\b",
                     frase, re.I):
            continue
        return True
    return False


def padrao_canaltech(markdown, *, genero=None):
    """Compara apenas gêneros compatíveis com o mapa de raciocínio de reviews.

    A referência é um mapa de raciocínio, não um template universal. Para
    notícia, guia, análise e nota breve, retorna diagnóstico não aplicável e
    não deve reduzir a nota estrutural. Títulos em forma de pergunta são
    informativos, nunca requisito de qualidade.
    """
    if genero is not None and genero not in {"comparativo", "review"}:
        return {
            "aplicavel": False,
            "genero": genero,
            "checagens": {},
            "cobertura": None,
            "total": 0,
            "motivo": "referencia_especifica_para_comparativos_e_reviews",
        }

    texto = str(markdown or "")
    titulos = [linha for linha in texto.splitlines() if linha.lstrip().startswith("#")]
    padroes = {
        "tese_condicional": r"\b(depende|condi[çc][aã]o|desde que|desde que saiba|vale a pena se|só compensa)\b",
        "perfis_de_leitor": r"\b(para quem|perfil|quem deve|quem não deve)\b",
        "consequencia_pratica": r"\b(significa|implica|impacta|afeta|consequ[êe]ncia|na prática)\b",
        "concessoes": r"\b(mas|porém|limitação|ressalva|por outro lado)\b",
        "procedencia": r"\b(segundo|fonte|estudo|medição|teste de terceiros|documentação)\b",
        "veredito_proporcional": r"\b(veredito|conclusão|em síntese|recomendação)\b",
    }
    # Preço/estoque só é avaliado quando o próprio artigo aborda esses temas.
    if re.search(r"\b(preço|disponibilidade)\b", texto, re.I):
        padroes["preco_datado"] = r"\b(preço|disponibilidade)\b.{0,80}\b(20\d\d|hoje|atual)\b"

    avaliado = {nome: bool(re.search(padrao, texto, re.I)) for nome, padrao in padroes.items()}
    # Questões nos títulos podem ajudar a navegação, mas não são obrigatórias.
    avaliado["secoes_orientadas"] = any("?" in titulo for titulo in titulos)
    total = len(padroes)
    return {
        "aplicavel": True,
        "genero": genero or "comparativo_ou_review",
        "checagens": avaliado,
        "cobertura": round(sum(avaliado[nome] for nome in padroes) / total, 2),
        "total": total,
    }

def checagens_deterministicas(*, markdown, sources, genero, title, meta,
                               image_rights, review_status, video_id=None):
    fontes = _fontes(sources)
    dominios = {_dominio(f.get("url")) for f in fontes}
    dominios.discard("")
    texto = str(markdown or "")
    internos = [u for u in re.findall(r"https?://[^\s)\]\"'>]+", texto)
                if SITE in _dominio(u)]
    br_texto = _br_afirmativo(texto)
    checagens = []

    def add(id_, ok, evidencia, severidade="blocker"):
        checagens.append({"id": id_, "status": "PASS" if ok else "FAIL",
                          "severidade": severidade, "evidencia": evidencia})

    add("multifonte", len(dominios) >= 2 or genero == "nota_breve",
        f"dominios_distintos={len(dominios)}")
    # Três é uma recomendação editorial suave, nunca quota ou bloqueio.
    add("links_internos", len(internos) <= 3,
        f"links_internos={len(internos)}; recomendacao_maxima=3", "warning")
    add("imagem_direitos", bool(image_rights), "direitos_confirmados=" + str(bool(image_rights)))
    if genero == "review":
        add("video_review", bool(video_id) and len(str(video_id)) == 11,
            "youtube_id=" + str(video_id or "ausente"))
    else:
        add("video_review", True, "nao_aplicavel", "warning")
    add("voz", str(review_status or "") in {"PROMPT_APPLIED", "ASSISTED_ADAPTED", "HUMAN_ADAPTED"},
        "status=" + str(review_status or "ausente"))
    add("seo", bool(title) and bool(meta) and len(str(meta)) >= 60,
        f"titulo={bool(title)} descricao_chars={len(str(meta or ''))}")
    palavras = len(texto.split())
    add("tamanho", palavras >= 400, f"palavras={palavras}", "warning")
    # A presença de Brasil no texto e de domínio .br na bibliografia não
    # demonstra suporte semântico da fonte à afirmação. Exigir conferência
    # por claim no dossiê/humano; não bloquear nem atribuir PASS automaticamente.
    if br_texto:
        checagens.append({
            "id": "publico_brasileiro",
            "status": "REVIEW_REQUIRED",
            "severidade": "advisory",
            "evidencia": "contexto_brasileiro_detectado; verificar suporte por claim no dossie",
        })
    else:
        add("publico_brasileiro", True, "nenhuma_afirmacao_brasileira_detectada", "advisory")
    add("pesquisa_fallback", len(dominios) >= 2 or genero == "nota_breve",
        "fonte_br_ausente_e_artigo_multifonte" if not br_fontes else "contexto_br_presente",
        "warning")
    return checagens


def _nota_assistida(review, brief, markdown):
    if not isinstance(review, dict):
        return 0, {}, "ausente"
    try:
        avaliacao = assess_substance(markdown, brief, review)
    except Exception:
        return 0, {}, "invalida"
    if not avaliacao.get("review_valid"):
        return 0, {}, "invalida"
    criterios = {k: int(v["score"]) for k, v in (review.get("criteria") or {}).items()
                 if isinstance(v, dict) and isinstance(v.get("score"), int)}
    return sum(min(4, max(0, s)) * 5 for s in criterios.values()), criterios, "valida"


def avaliar_artigo(markdown, *, brief=None, review=None, sources=None,
                   genero="analise", title="", meta="", image_rights=False,
                   review_status=None, video_id=None, contract_path=None):
    """Devolve um recibo 0–100. Nunca autoriza publicação nem prova fatos."""
    contrato = carregar_contrato(contract_path)
    if genero not in GENRES:
        raise ValueError("GENERO_INVALIDO")
    brief = normalize_brief(brief) if brief is not None else None
    checks = checagens_deterministicas(
        markdown=markdown, sources=sources, genero=genero, title=title, meta=meta,
        image_rights=image_rights, review_status=review_status, video_id=video_id)
    bloqueios = [c["id"] for c in checks if c["status"] == "FAIL" and c["severidade"] == "blocker"]
    pendencias = [c["id"] for c in checks if c["status"] == "FAIL" and c["severidade"] == "warning"]
    padrao = padrao_canaltech(markdown, genero=genero)
    penalidade = sum(25 for c in checks if c["status"] == "FAIL" and c["severidade"] == "blocker")
    penalidade += sum(5 for c in checks if c["status"] == "FAIL" and c["severidade"] == "warning")
    if padrao["aplicavel"]:
        penalidade += round((1 - padrao["cobertura"]) * 20)
    estrutural = max(0, 100 - penalidade)
    assistida, criterios, estado_revisao = _nota_assistida(review, brief, markdown)
    nota = round(PESO_ASSISTIDA * assistida + PESO_ESTRUTURA * estrutural)
    if bloqueios:
        nota = min(nota, LIMITE_COM_BLOQUEIO)
    return {
        "schema": "conexo-editorial-quality-receipt/1",
        "contract_sha256": contrato["contract_sha256"],
        "content_sha256": content_hash(markdown),
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "genero": genero,
        "nota": nota,
        "nota_assistida": assistida,
        "nota_estrutural": estrutural,
        "estado_revisao": estado_revisao,
        "criterios": criterios,
        "checks": checks,
        "padrao_canaltech": padrao,
        "bloqueios": bloqueios,
        "pendencias": pendencias,
        "nota_humana": None,
        "factual_approval": False,
        "publication_authorized": False,
    }
