"""Assistant-performed, text-bound Binance editorial adaptation and substantive critique.

This record applies ONLY to the exact 2026-11-14 manuscript SHA below.
It is NOT human approval, source verification, ownership of third-party rights,
Gate authorization or permission to publish.
"""
from mkt_flow_p0.editorial_identity import DNA_PROMPT_SHA256
from mkt_flow_p0.editorial_substance import content_hash, brief_hash, assess_substance

MANUSCRIPT_SHA = "1969799ce2c4a1b6ad629eec62c39095ac58418695bab2f3f53efefe57448b60"
BRIEF = {
    "genre": "noticia",
    "reader": "Leitor brasileiro que guarda criptomoedas em corretora e precisa distinguir a segurança operacional da simples promessa de ressarcimento.",
    "need": "Entender se a cobertura anunciada depois de um ataque significa ativos devolvidos, clientes ressarcidos e retiradas efetivamente normalizadas.",
    "angle": "Confrontar percentuais 95% e 100% sem somá-los nem escolher um como verdade definitiva; separar três operações financeiras distintas.",
    "contribution": "Explicar o mecanismo de recomposição, os limites da prova de reservas, a repercussão prática para o usuário e os documentos ainda necessários.",
    "limits": "Não há auditoria financeira independente nem comprovação de restituição integral a todos os clientes; atribuições criminais e ativos congelados exigem ressalvas.",
}
CRITIQUE = {
    "reader_need": {
        "score": 4,
        "excerpt": "Para quem mantém criptoativos sob custódia de uma exchange, a principal questão prática não é apenas a promessa de ressarcimento.",
        "reason": "A seção destinada ao usuário distingue redes e disponibilidade de saques; a atualização da AP esclarece que congelamento, autorização judicial e devolução não são equivalentes.",
    },
    "editorial_angle": {
        "score": 4,
        "excerpt": "cobertura de prejuízo**, **congelamento de ativos** e **recuperação jurídica e financeira",
        "reason": "A matéria diferencia processos econômicos e jurídicos que são frequentemente confundidos; não se limita a empilhar declarações das fontes.",
    },
    "decision_support": {
        "score": 3,
        "excerpt": "Vale consultar a metodologia, a data da apuração e a possibilidade de validação externa antes de transformar o indicador em garantia ampla.",
        "reason": "Há critério útil de leitura da prova de reservas e orientação sobre disponibilidade por rede, mas faltam comprovantes primários e verificação operacional no WordPress.",
    },
    "voice": {
        "score": 3,
        "excerpt": "A diferença não é apenas contábil. Um usuário pode ter saldo recomposto pela exchange mesmo que os tokens originalmente desviados nunca voltem à carteira de origem.",
        "reason": "A reformulação da abertura conecta a notícia à dúvida prática do leitor e a narrativa mantém uma voz analítica e documental; o julgamento editorial assistido não é atestado humano.",
    },
    "source_limits": {
        "score": 4,
        "excerpt": "Sem esclarecer o momento e o critério de cada percentual, não é possível tratar ambos como uma mesma medição.",
        "reason": "O texto assinala lacunas entre 95% e 100%, e separa os US$ 2,7 bilhões congelados dos US$ 1,2 bilhão autorizados judicialmente, sem afirmar devolução aos clientes. O Gate ainda exige revisão factual independente.",
    },
}


def enrich_review_payload(payload):
    body = payload["article"]["texto_markdown"]
    if content_hash(body) != MANUSCRIPT_SHA:
        raise ValueError("BLOCKED: Binance manuscript differs from assistant-reviewed version")
    review = {
        "method": "assisted",
        "reviewer": "ChatGPT editorial assessment 2026-11-14",
        "content_sha256": MANUSCRIPT_SHA,
        "brief_sha256": brief_hash(BRIEF),
        "criteria": CRITIQUE,
    }
    result = assess_substance(body, BRIEF, review)
    if not result["review_valid"] or result["status"] != "PASS":
        raise ValueError("BLOCKED: text-bound substantive critique inconsistent")
    # Document every supplied source and claim as PENDING, not as verified.
    # This eliminates the *missing-contract* error without granting the
    # source/claim PASS bits that only a trusted editorial review can provide.
    supplied_sources = payload["research"]["sources"]
    pending_contract = {
        "contract_version": "1.0",
        "content_type": "noticia",
        "status": "PENDING",
        "sources": [
            {
                "id": "binance-src-" + str(i),
                "url": source["url"],
                "status": "PENDING",
                "pending": True,
                "retrieved_at": None,
            }
            for i, source in enumerate(supplied_sources, 1)
        ],
        "claims": [
            {
                "id": "extra_" + str(i) + "_" + str(j),
                "text": fact,
                "status": "PENDING",
                "pending": True,
                "heuristic": False,
                "evidence_ids": [],
            }
            for i, source in enumerate(supplied_sources, 1)
            for j, fact in enumerate(source["facts"], 1)
        ],
    }
    payload.update({
        "editorial_contract": pending_contract,
        "editorial_brief": dict(BRIEF),
        "editorial_substance_review": review,
        "editorial_voice_application": {
            "status": "ASSISTED_ADAPTED",
            "method": "assisted_editorial_adaptation",
            "dna_prompt_sha256": DNA_PROMPT_SHA256,
            "content_sha256": MANUSCRIPT_SHA,
            "provider_id": "chatgpt-editorial-assist",
        },
    })
    return payload
