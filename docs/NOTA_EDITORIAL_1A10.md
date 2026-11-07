# Nota editorial de 1 a 10 — fila MKT-RSS / ConexoTech

Status: **implementação em branch, sem ativação em produção**.
Padrão: nota-editorial/1. O módulo substitui a priorização; não substitui o Gate Editorial.

## Cálculo

| Critério | Peso |
|---|---:|
| Afinidade com IA, segurança, software, conectividade e tecnologia | 30% |
| Relevância para público brasileiro | 25% |
| Utilidade e intenção de busca | 20% |
| Atualidade e oportunidade | 15% |
| Valor duradouro / evergreen | 10% |

Cada eixo recebe um inteiro 1..10. A nota final é a média ponderada com arredondamento meio para cima.
Faixas: 9–10 máxima, 7–8 alta, 5–6 intermediária, 1–4 baixa.

## Fontes e confiança

- HEURISTICA_PROVISORIA: sugestão por título, descrição e data. Não mede audiência nem comprova interesse de pesquisa.
- REVISAO_EDITORIAL: cinco avaliações explícitas do editor, corrigidas com justificativa e data. Não substitui revisão factual.

Google Trends, Search Console e Jetpack só devem alterar parâmetros de público quando houver dados efetivamente obtidos e datas documentadas; não inventar visitas, volume de buscas ou receita.

## Compatibilidade técnica

A tabela rss_pautas conserva o campo pontuacao (0..100). Novas pautas usam pontuacao = nota x 10.
A listagem contém nota e origem_nota e ordena pela nota humana quando houver; caso contrário usa a heurística.
A tabela adicional rss_notas_editoriais registra correção manual, justificativa e horário. O motivo de transição da fila não é modificado.

Registros anteriores: reavaliar_descobertas(limite=100) é execução **explícita**, idempotente, restrita a DESCOBERTA e preserva nota humana. Não rodar no Turso antes de verificar ambiente e backup.

Rascunhos WordPress: ler id, title, excerpt, modified, status; avaliar com prioridade_editorial.avaliar_pauta; conferir duplicidade, fontes e risco de desatualização; armazenar em relatório privado até se decidir mecanismo autenticado de metadados. **Não modificar posts em lote, instalar plugins nem gerar publicações.**

## Operação

1. MKT-RSS coleta, deduplica e atribui nota provisória às novas pautas.
2. A fila aponta os assuntos mais importantes; editor pode refinar cada eixo e registrar nota humana.
3. A diretriz de composição 60% comercial / 40% informativo é independente da nota; usar janela móvel de dez artigos, não manipular a rubrica para atingir a meta.
4. Antes da redação, conferir status, duplicação e atualidade. A nota 10 não dá permissão de publicação.
5. O Gate Editorial continua exigindo evidência factual, imagem licenciada, links internos e aprovação por versão.
6. Reavaliar rapidamente notícias urgentes e descontos vencidos, evitando publicar uma boa pauta com dados desatualizados.

## Exemplos offline

Use a função avaliar_pauta do módulo mkt_flow_p0.prioridade_editorial. Sem parâmetros extras, ela retorna critérios provisórios.
Com o argumento criterios, recebe um dicionário com afinidade, publico_brasileiro, utilidade, atualidade e evergreen (cada um 1..10).
Na fila, atribuir_nota(pauta_id, nota, justificativa) altera somente a prioridade, sem mudar estado.

Testes: python -m unittest tests.test_prioridade_editorial tests.test_fila_pautas -v.
Estes testes não comprovam persistência Turso real, migração de rascunhos WordPress ou implantação em produção.
