# Especificação técnica das operações de produção — 28/11/2026

Documento de preparação. **Nada aqui foi implementado ou executado.** Toda operação de produção depende de autorização específica posterior.

## 1. Recibo assinado do Gate V1

Situação: o adaptador espera envelope `{record, signature}`, mas o artefato RC10.4 instalado retorna `{post_id, report, valid_for_current_version}`; não há recibo assinado vigente.

Sequência prevista:

1. conferir a versão exata do artigo e seu hash;
2. obter o hash do conteúdo efetivamente lido do WordPress;
3. gerar o registro assinado pelo mecanismo **existente** do Gate V1, sem criar novo sistema;
4. verificar assinatura, identidade do produtor, versão e hash;
5. confirmar `valid_for_current_version=True` com readback autenticado.

Critério: nenhuma aprovação ou publicação sem assinatura válida para a versão exata.

## 2. Escrita atômica `commit_if_unchanged`

Situação: é requisito em `docs/EDITORIAL_WORDPRESS_PUBLISH_GATE.md`; o backend não existe na integração atual.

Fluxo previsto:

1. ler o rascunho e registrar o hash;
2. preparar a alteração;
3. comparar o hash atual com o original imediatamente antes de gravar;
4. se mudou, cancelar a escrita;
5. se não mudou, realizar a operação protegida;
6. fazer readback e verificar o conteúdo gravado.

Testes obrigatórios antes de homologar: concorrência entre duas escritas, falha parcial, repetição da mesma operação (idempotência) e confirmação de que versão alterada jamais é sobrescrita. Não basta criar uma função com esse nome.

## 3. Provisionamento condicional do Gate

**Somente se** houver autorização explícita para ativar as rotas de remediação:

- chaves distintas para registro e revisto; nunca a mesma chave;
- usuário de serviço configurado fora do repositório;
- UUID autorizado da Application Password configurado fora do repositório;
- opções exigidas configuradas fora do repositório;
- teste primeiro em ambiente isolado;
- validação das restrições de identidade já cobertas no PR #91.

Se as rotas continuarem desativadas, **não provisionar nada**. Constantes, opções e UUID permanecem ausentes.

## Limites

- Sem escrita em WordPress ou Turso de produção.
- Sem publicação, aprovação ou agendamento.
- Sem ativação de plugin ou rotas.
- Sem Actions ou CircleCI.
- Sem segredo no repositório.

## Estado da etapa

**NOT STARTED** — especificação pronta; implementação e execução dependem de autorização posterior.
