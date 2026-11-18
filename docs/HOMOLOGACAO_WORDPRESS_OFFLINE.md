# Homologação WordPress sem dependência de credenciais durante a validação

## Objetivo

Separar a validação automatizada do MKT-RSS da consulta ao WordPress. Testes, replay de evidências e comparação de versões devem ser reproduzíveis em checkout local/OpenCode sem login, token, rede ou escrita no WordPress.

## Níveis de evidência

1. **Contrato offline (obrigatório no PR):** validação do adaptador e dos snapshots JSON com respostas `edit` e `view` determinísticas. Não prova que o WordPress real persistiu o conteúdo.
2. **Readback real (evidência complementar):** captura somente GET de um mesmo post nos contextos `edit` e `view`. É necessária apenas para afirmar persistência real e comportamento do sanitizador/plugin no site consultado.
3. **Publicação:** fora do escopo desta homologação. Nenhum teste ou readback autoriza POST/PUT, aprovação, agendamento, publicação, Gate, cron, merge ou deploy.

A falta de credencial não pode reprovar o nível 1 nem bloquear a execução da suíte. Também não pode ser apresentada como PASS do nível 2.

## Formato do snapshot

Guardar fora do repositório, em arquivo local protegido, um JSON com duas respostas do mesmo post:

- `edit_post`: resposta de GET `context=edit`, contendo conteúdo bruto;
- `view_post`: resposta de GET `context=view`, contendo conteúdo renderizado.

Os dois objetos devem ter o mesmo `id`, `status` e `modified`. Não versionar snapshots de produção, conteúdo editorial, cookies, tokens ou credenciais. Para compartilhar evidência, registrar somente ID, status, modified, tamanhos, hashes, IDs de vídeo, flags e bloqueios.

## Reproduzir sem WordPress

No checkout isolado, com as dependências de desenvolvimento já instaladas:

```bash
python -m pytest -q tests/test_editorial_wordpress_adapter.py tests/test_validate_wordpress_snapshot.py
python tools/validate_wordpress_snapshot.py /caminho/local/wordpress-readback.json
```

O utilitário é estritamente offline: lê um JSON local, não faz chamadas de rede e imprime apenas metadados, hashes, IDs de vídeo e bloqueios. Código de saída 0 significa que o snapshot satisfaz o contrato; código 2 indica snapshot inválido ou incompleto.

## Critério de conclusão

- O PR pode receber **PASS na homologação automatizada offline** quando os testes acima passam no SHA registrado.
- O readback real fica **PENDENTE** até existir snapshot legítimo de um post persistido que contenha proveniência íntegra, iframe YouTube nocookie e `VideoObject` correspondente.
- Um snapshot sintético comprova o contrato do adaptador, não a persistência no WordPress.
- Não criar conteúdo de teste na produção. Se não houver conteúdo preexistente adequado, a evidência real exige ambiente WordPress isolado ou fixture exportada de homologação anterior.

## Segurança

O utilitário não recebe credenciais, não faz requests HTTP e não escreve no WordPress. Manter snapshots fora do Git e restringir permissões do arquivo local, pois podem conter conteúdo editorial.
