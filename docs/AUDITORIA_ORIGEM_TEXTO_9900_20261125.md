# Auditoria da origem e das diretrizes do texto do post #9900 — 25/11/2026

**Pergunta do proprietário:** qual módulo/ferramenta de IA redigiu o texto
"Anatel manda TIM desligar bloqueio de telemarketing; entenda o que muda" e as
diretrizes/parâmetros foram aplicados? O texto foi avaliado como vago,
sonolento, desconexo, com pontuação mal aplicada e afirmações sem documentos.

**Escopo:** somente leitura. Nenhuma alteração no post, nenhuma aprovação,
nenhuma publicação.

---

## 1. Respota direta

| Pergunta | Resposta com evidência |
|---|---|
| Quem escreveu o texto **atual** do #9900? | **Correção após mapeamento de código (25/11):** o documento diz "regerado pelo motor", mas o runtime do servidor estava em branch antiga e **foram copiados apenas `editorial_import.py` e `editorial_provenance.py`** (`docs/REGENERACAO_MOTOR_20261117.md:60-63`). Portanto o caminho executado foi o de **importação com runtime parcial**, não a geração completa com o redator. O corpo contém a marca `cxeg-package:v1` com `version_sha256=34d79ca353fe4f15fb3b36c2c9571045e91a5409af58c6841eae4ab38f32d63c` e `content_sha256=d814a82573834d2990c9610f541e97cd10687f2fb1bf0dba07c1f06d9b30e2e7`. |
| Qual módulo? | O caminho de importação usa `mkt_flow_p0/editorial_import.py` e `editorial_provenance.py`; o redator `mkt_flow_p0/rewriter.py` (Groq) **não fez parte dessa execução parcial**. A marca registra os módulos `editorial_identity`, `editorial_core_offline`, `seo`, `editorial_readiness` e `editorial_substance` como `EXECUTED`. `editorial_identity.py:47-48` normaliza texto sem prova de voz para `NOT_APPLIED` — exatamente o que a marca mostra. |
| Qual modelo de IA exato? | **Não comprovado.** O redator usa Groq; o código tem default `llama-3.3-70b-versatile` e o `.env.example` sugere `openai/gpt-oss-120b`. A marca do pacote **não registra provedor nem modelo**, e não há log do run com o modelo usado. Afirmar um modelo específico seria inventar dado. |
| E a versão anterior ao dia 17? | `docs/REGENERACAO_MOTOR_20261117.md` diz: "Antes: texto escrito fora do motor, sem manifesto". Não há registro que identifique a ferramenta/author dessa primeira versão. |

## 2. As diretrizes existiram — mas o resultado não as comprova

**O briefing existia:** `docs/PAUTAS_SELECIONADAS_20261117.md` define leitor, necessidade, recorte, limite ("não afirmar que o serviço está desligado"), 5 afirmações com trecho literal da fonte e lacunas declaradas (despacho da Anatel não localizado; TIM sem manifestação).

**O que a execução registrou, porém:**

```
"voice_status": "NOT_APPLIED"
"substance_status": "PENDING"
"image_rights_confirmed": false
"modules": { ... "EXECUTED" ... }
```

Interpretação correta:
- `EXECUTED` **não** é `PASS` — significa que o módulo rodou, não que aprovou.
- `NOT_APPLIED` = não há prova verificável de aplicação do DNA/voz editorial.
- `substance_status: PENDING` = avaliação substantiva não fechada.
- Nada disso é aprovação humana; o Gate não tem parecer para o #9900.

Conclusion: **as diretrizes foram escritas, mas não há evidência de que tenham sido aplicadas ao texto final.** O próprio documento de regeneração diz que o motor reportou `ENRIQUECIMENTO_PENDENTE` e que "nenhum desses itens virou PASS".

## 3. As queixas do proprietário — verificação

| Queixa | Evidência encontrada |
|---|---|
| Texto "desconexo" e "pontuação mal aplicada" | **Confirmado como defeito de renderização.** O corpo no WordPress tem um `<p>` por linha do Markdown: "A Anatel determinou, em caráter cautelar," / "que a TIM desligue a ferramenta antispam..." — a frase está cortada em vários parágrafos. Itens de lista também foram partidos: `<li>Garantir atendimento</li>` vem seguido de `<p>feitas pela própria agência.</p>` fora da lista. `mkt_flow_p0/html_paragrafos.py` e `tests/unit/test_html_paragrafos.py` documentam esse defeito desde 22/11 e trazem reparo, **mas o reparo não foi aplicado ao rascunho vivo**. `REGISTRO_UNICO` registra 75 alertas (50 tipografia, 25 gramática) no #9900. |
| "Afirmações sem documentos que possam comprovar" | **Parcialmente confirmado.** A tabela de fontes do próprio artigo lista apenas nomes — **nenhum URL**. Afirmações como "a Anatel já publicou regras para esses sistemas, inclusive exigindo que o bloqueio seja gratuito e possa ser desativado", "cadastro Não Me Perturbe, mantido pela Anatel" e "o Tecnoblog noticiou em setembro..." não estão entre as 5 afirmações com trecho literal da fonte e não têm link. O texto é honesto ao declarar que o despacho não foi localizado, mas preenche outras lacunas por dedução. |
| "Vago, sem inspiração, sonolento" | Julgamento subjetivo, não verificável como fato. É compatível com `voice_status: NOT_APPLIED`, mas **não** é prova de que nenhum prompt tenha sido usado. |

## 4. Conclusão e recomendação

O #9900 **não está pronto para aprovação nem para a cadeia CAS**:

1. voz/dna sem aplicação verificável;
2. avaliação substantiva pendente;
3. parágrafos e listas quebrados no HTML publicado (reparo existe, não aplicado);
4. afirmações sem link de documento;
5. direitos de imagem não confirmados;
6. nenhum parecer humano no Gate.

Recomendação: **não aprovar o #9900 no estado atual.** Regenerar com a voz aplicada e o reparo de parágrafos, ou descartar a pauta. A crítica do proprietário é procedente nos pontos verificáveis (itens 1 a 5).

Nada nesta auditoria alterou o post, aprovou conteúdo ou autorizou publicação.
