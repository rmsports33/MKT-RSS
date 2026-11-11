# Validar a credencial existente do MKT-RSS

Objetivo: comprovar autenticacao do proprio executor como Bot.editor ID 4, sem usar a identidade do conector ChatGPT e sem publicar.

## Checagem preparada

Workflow `WordPress MKT-RSS identity - read only`, arquivo `.github/workflows/wp-identity-preflight-manual.yml`. Manual, somente proprietario `rmsports33`, branch `master`, ambiente protegido existente `rss-homolog`. Usa os segredos ja configurados `WP_URL`, `WP_USER` e `WP_APP_PASSWORD`. Nao cria ou move segredos, nem altera regras do ambiente.

Executa um GET HTTPS `/wp-json/wp/v2/users/me?context=edit&_fields=id,roles,capabilities`. Aceita somente origem exata ConexoTech, ID inteiro 4, perfil editor e permissoes read/edit_posts/publish_posts; recusa administrador/manage_options, outra identidade, redirecionamentos e respostas invalidas. Sem retentativa ou escrita. Nao consulta artigos, nao usa Groq/Turso e nao imprime corpo de resposta, cabecalho de autenticacao ou credencial. Apenas Python padrao; nenhuma instalacao pip.

## Execucao pelo celular

1. Abrir GitHub > rmsports33/MKT-RSS > Actions > WordPress MKT-RSS identity - read only.
2. Clicar Run workflow, selecionar master e confirmar Run workflow.
3. Se aparecer aprovacao do ambiente rss-homolog, revisar e aprovar essa execucao conforme a politica existente; nao afrouxar protecoes.
4. Abrir a execucao e conferir o resumo. Sucesso esperado: `PASS: MKT-RSS WordPress credential authenticated as editor ID 4; no writes or publication.`

| Resultado | Acao |
| --- | --- |
| WP_CREDENTIAL_MISSING | Conferir presenca de WP_USER e WP_APP_PASSWORD nos secrets acessiveis ao ambiente; nao colar valores no chat. |
| WP_ORIGIN_NOT_ALLOWED | Conferir WP_URL=https://conexotech.com.br nos secrets. |
| WP_AUTH_REJECTED | Credencial recusada: revisar a Application Password de Bot.editor no canal seguro. |
| WP_IDENTITY_MISMATCH | A credencial autentica outra identidade; nao promover privilegios nem reutilizar conta administradora. |
| WP_PRIVILEGE_DENIED / WP_PERMISSION_MISSING | Conferir o papel da conta; o teste nao modifica permissoes. |
| WP_REDIRECT_BLOCKED / WP_READ_FAILED | Investigar a rota HTTPS/autenticacao; nao enviar credencial a outro host. |

## Evidencias e limites

PASSOU: 11 testes especificos com rede simulada, mais regressao broker/trace/SEO, 36 testes no conjunto local. A contraprova executada no Cloud sem secrets retorna BLOCKED e codigo de saida 1. Isso nao valida uma credencial real.

NAO EXECUTADO: GET autenticado real usando os segredos de Actions. O Cloud nao tem bindings WP, o conector GitHub nao oferece workflow_dispatch e as ferramentas de desktop compartilhado nao foram disponibilizadas nesta sessao. A API WordPress conectada usa outra autenticacao e nao prova a credencial do MKT-RSS.

Proximo passo: executar esse workflow uma vez na master e conferir o codigo seguro no resumo; nao extrair segredos de Actions. Mesmo com PASS, instalacao RC3, allowlist do broker e aprovacao da materia continuam criterios separados.
