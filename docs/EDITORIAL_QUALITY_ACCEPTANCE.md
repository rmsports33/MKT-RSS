# Homologação de qualidade editorial — protocolo de aceite

Este documento não declara que os artigos atingiram qualidade acima da média. O PR #78
integrou briefing, redação/adaptação, crítica e prontidão, mas avaliações assistidas
pelo mesmo modelo não são verificação independente.

## Correção adicional

O detector de repetição em `editorial_substance.py` agora inclui parágrafos
longos quase duplicados por pequenas trocas de palavras, mesmo quando um
parecer automatizado informa notas altas. A decisão é um **bloqueio
determinístico limitado**: não substitui revisão de fatos, relevância nem
voz editorial humana. Testes positivos e negativos cobrem esse cenário.

## Aceite obrigatório antes da declaração de qualidade

1. Obter uma execução real documentada do Groq, registrando link do Action,
   resultado da etapa, versão/hash, estado de briefing, redação/crítica e erros.
   Um PR integrado não é evidência de que a execução aconteceu. Não copiar
   texto editorial não revisado nem segredos para repositório público.
2. Selecionar **três pautas de gêneros diferentes** (notícia, guia e
   análise/comparativo) com fontes conferidas. Preservar os mesmos insumos e
   as mesmas condições para a versão de referência e a versão corrigida.
3. Entregar ao revisor humano as versões A/B em ordem aleatória, sem indicar
   o autor nem o executor. Aplicar notas 0–4 separadamente para necessidade
   do leitor, recorte, contribuição, voz e limites das fontes. Registrar
   justificativas e exemplos concretos; comparar cada par, não apenas
   pontuações absolutas.
4. Considerar aprovado o piloto **somente** se as três versões corrigidas
   melhorarem em contribuição e voz sem regressão factual; caso contrário,
   registrar a falha por etapa e voltar à redação com o feedback específico.
   Uma nota do próprio modelo não satisfaz esse critério.
5. Não promover automaticamente a publicação. Fatos, fonte, direitos da
   imagem, SEO, aprovação humana vinculada à versão e bloqueio real do
   WordPress/Gate Editorial são controles separados.

## Lacunas que ainda precisam de evidências

- Não foi comprovada nesta alteração uma comparação A/B cega real.
- Não foi comprovada aqui execução autenticada ou resultado do Action de
  handoff único do PR #79; consultar job, logs saneados e manifesto.
- Não foi comprovado que três gêneros atingem o padrão final em produção.
- Não ativar staging, cron, execução repetitiva paga, WordPress nem publicação
  para conseguir essa evidência.
