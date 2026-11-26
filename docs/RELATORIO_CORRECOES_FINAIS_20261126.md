# RELATÓRIO DE CORREÇÕES — PRs #135 e #136 (26/11/2026)

## PR #135 — Gate V1

- HEAD reportado: `cd92a5b9ff97d492d243b901b90ee144cf953dbe`.
- Layout nativo, listagem, preview e ações ligadas ao formulário nativo.
- Os 13 critérios humanos e suas evidências não são preenchidos automaticamente.
- O carregamento está documentado no ponto `cxeg_standard_boot()`; a aplicação no plugin instalado ainda depende de autorização de upload/deploy.
- Testes reportados pelo executor: 20 Python e 14 PHP.
- Core RC10.4 e MU-plugins preservados.

## PR #136 — MKT-RSS: correções implementadas nesta rodada

1. **Credenciais do destino:** argumentos do broker são comparados com o destino resolvido. Divergências bloqueiam antes de qualquer GET/POST. Após a comparação, as chamadas utilizam as credenciais e o `auth` do destino validado.
2. **Chaves distintas:** o provisionador rejeita chaves fracas ou repetidas; o verificador independente também recusa reutilização da mesma chave.
3. **Post completo na guarda:** E1 autenticado fornece ID, status, título bruto, conteúdo bruto, slug, categorias e imagem destacada. O broker passa esse post completo ao Revisor Único. A guarda ocorre depois das leituras e antes do único POST.
4. **Hash correto:** E1 compara o SHA-256 do conteúdo bruto do pacote com o conteúdo realmente lido. O `snapshot_sha256` do Gate permanece separado e continua sendo usado no contrato de escrita; não é confundido com o hash do corpo.
5. **Fail-closed:** falta de certificado, chaves inválidas/iguais, divergência de credenciais ou falha de leitura/correlação impedem a escrita.

## Testes adicionados/ajustados

- Rejeição de chaves iguais.
- E1 devolve os campos completos necessários à vinculação do certificado.
- Teste do broker verifica que a guarda recebe o post autenticado completo.
- Teste do broker distingue hash do conteúdo e hash do snapshot.
- Teste de divergência entre credenciais fornecidas e destino validado.
- Fixtures legadas do broker passam a modelar E1/E2 e a guarda obrigatória.

**Execução:** os testes foram atualizados no branch; a suíte Python e os logs de CI ainda precisam ser executados/confirmados. Não declarar PASS para os novos testes sem essa evidência.

## Evidência operacional reportada anteriormente

- WordPress #9906: E1 `context=edit` e E2 `context=view` retornaram HTTP 200.
- Mesmo ID/status draft e correlação de conteúdo foram reportados como verificados.
- A chave separada `CONEXO_REVIEW_REGISTRY_KEY` estava ausente na última verificação.
- A leitura isolada não prova a execução integrada da guarda com o registro real.

## Pendências

| Item | Estado |
|---|---|
| Provisionar `CONEXO_REVIEW_REGISTRY_KEY` por canal seguro | PENDENTE |
| Executar a suíte atualizada em Python 3.11 | PENDENTE DE EXECUÇÃO |
| Confirmar workflow CI/manual | PENDENTE |
| Aplicar o layout no plugin Gate V1 instalado | PENDENTE DE AUTORIZAÇÃO |
| Publicação real e readback pós-escrita | PENDENTE DE AUTORIZAÇÃO ESPECÍFICA |

## Limites

- Sem merge, deploy ou upload.
- Sem POST/escrita/publicação no WordPress ou Turso.
- Sem SSH em produção.
- Sem exclusão de plugins, novo Gate ou alteração do core RC10.4/MU-plugins.
