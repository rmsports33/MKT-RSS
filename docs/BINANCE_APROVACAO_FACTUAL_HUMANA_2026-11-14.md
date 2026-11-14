# Aprovação factual humana — Binance — versão imutável

**Estado:** AGUARDANDO APROVAÇÃO HUMANA — não autoriza publicação.

**Versão do handoff:** `d2ccb99e2dbe0dbc999a4b8e1fdd49d089c9299c679f5cb6200edc5db6e00fd2`  
**SHA256 do corpo:** `1969799ce2c4a1b6ad629eec62c39095ac58418695bab2f3f53efefe57448b60`  
**Texto integral:** [Artigo Binance de revisão](ARTIGO_BINANCE_REVISAO_2026-11-14.md)  
**Evidências pré-assistidas:** [quatro vínculos exatos](BINANCE_CANDIDATOS_EVIDENCIA_FINAL_2026-11-14.json)  
**Capa cadastrada:** mídia WordPress **9892**, Kevin Ache/Unsplash. A biblioteca de mídia contém a imagem, mas ela não foi associada a rascunho.

## Verificação obrigatória pelo revisor autorizado

| Claim | Ponto que requer aceite factual | Evidência publicada |
|---|---|---|
| extra_1_1 | Reuters 14/11: 95% declarado, saques normalizados progressivamente; **não confundir com restituição** | https://www.reuters.com/legal/government/binance-targets-full-reopening-withdrawals-by-next-week-2026-11-14/ |
| extra_2_1 | Reuters 31/10: empresa repôs aproximadamente 90% e aguardava aquisição de ativos menos líquidos; evitar extrapolação a todas as carteiras | https://www.fidelity.com/news/article/company-news/202610311134RTRSNEWSCOMBINED_L6N46H03L_1 |
| extra_3_1 | AP 12/11: mais de US$ 2,7 bi congelados, **dos quais** mais de US$ 1,2 bi com ordem judicial; **não somar nem anunciar devolução** | https://apnews.com/article/41be4834083e596a8facfd719f851cae |
| extra_4_1 | Tecnoblog 14/11: 100% de cobertura *declarada pela empresa*, não recuperação judicial de 100% dos fundos roubados | https://tecnoblog.net/noticias/r-34-bilhoes-binance-cobriu-100-do-prejuizo-do-maior-roubo-de-cripto-da-historia/ |

## Decisão humana — somente para a versão acima

O responsável editorial deve examinar **o artigo completo e os quatro vínculos fonte→alegação** e escolher, em sessão autenticada do sistema de revisão:

- **Aprovar factual e editorialmente a versão identificada** para preparar um rascunho *não publicado* por `intent=stage` pelo Gate; ou
- **Devolver para correção**, indicando quais dos quatro claims e trechos não são aceitos.

Essa decisão em linguagem natural **não substitui** `cxeg_review_identity_valid`, a emissão legítima de `receipt` e `signature`, as verificações de qualidade e a autorização autenticada de escrita do Gate.

**Não criar aprovação sintética neste documento, não inscrever `approved=true` no JSON por inferência, não reutilizar assinaturas, não revelar chaves e não publicar.** Se houver alteração textual, a versão deverá ser reconciliada antes do aceite.

## Condições da única criação de rascunho

1. Identificar o emissor autorizado do recibo no plugin instalado.
2. Obter aceite do revisor legítimo e recibo verificável correspondente à versão imutável.
3. Executar a rota canônica `/wp-json/conexo/v1/editorial/write`, exclusivamente `intent=stage`, sem fallback para `wp/v2/posts`.
4. Conferir `post_status=draft`, novo ID, `featured_media=9892` e ausência de alteração dos posts 9708 e 9744.
5. Manter agendamento/publicação bloqueados até autorização própria.

**Registro deste arquivo é preparação para revisão humana, não aprovação factual.**
