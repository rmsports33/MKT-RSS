---
name: pesquisa-conexotech
description: Pesquisa comercial para reviews e afiliados ConexoTech com níveis de confiança, disclosure e placeholders de link
---

# Pesquisa ConexoTech (reviews + afiliados)

Use quando for levantar dados de produto, preço ou notícia para o ConexoTech.
Complementa o padrão global (`achar → ler`, fonte primária); aqui vão as regras comerciais.

## Níveis de confiança (nunca afirmar acima da evidência)

- **A** — fabricante + confirmação cruzada: uso livre
- **B** — fabricante OU medição própria: uso liberado
- **C** — terceiros confiáveis: só com atribuição ("segundo reviews verificados")
- **D** — inferência: só marcada como opinião/estimativa
- **E** — sem evidência: bloqueado, não entra

## Proibições duras

- NUNCA buscar/extrair páginas do Mercado Livre (ToS proíbe automação)
- NUNCA gerar URL real de afiliado: sempre `[LINK AFILIADO: loja — produto]`
- NUNCA afirmar preço sem data de captura; revalidar após ~7 dias
- Peça com link de afiliado SAI com aviso de disclosure visível (regra inegociável)

## Formato de saída (campos do tema)

`titulo, conteudo (H2s pergunta + resposta direta 40-50 palavras), resumo,
nota (0-10 vírgula), specs (RÓTULO | Valor), benchs (Rótulo | Detalhe | 0-100),
pros/contras (1 por linha), veredito 1 frase, lojas (nome+preço+data),
categoria (slug), seo (title ≤60 + description ≤160), entidade consistente`

## Auditoria antes de entregar

1. Número tem fonte? 2. Contras reais presentes? 3. Nota coerente com veredito?
4. Preço dentro da validade? 5. Links são placeholders? 6. Sem keyword stuffing?
7. Sem drift semântico (limite virou absoluto? dado neutro ganhou adjetivo)?
