# Controle remoto editorial — Hostinger + GitHub (2026-11-14)

## Estado observado
- Hostinger: conta `u401421381`, site `conexotech.com.br`; Cron da conta estava vazio antes da configuração.
- Um Cron exclusivo, sem acesso HTTP público, foi cadastrado para executar `ops/hostinger/remote_controller.py` em `~/mkt-rss-runner`.
- Agendamento ativo de cinco em cinco minutos: UID `ZiA0KZ9rPW`. O Cron transitório de 1 minuto (`7Jo5gcqFg9`) foi removido. A execução real da solicitação ainda exige consulta ao recibo; o cadastro não é prova de sucesso.
- **Não é o Cron do coletor RSS**. `run_rss_queue.sh` permanece protegido com `CONEXO_RSS_CRON_ACTIVE` e com a regra de escritor único. O workflow diário do GitHub Actions permanece programado; não alterar sem corte seguro.
- Ações do controlador, somente por allowlist: `image_technical_check`, `binance_image_review_package`. Não há ação para publicar, editar WP, executar código livre, criar contas ou cobrar serviços.
- Comando remoto é um arquivo de dados JSON no GitHub, validado, controlado por `job_id`; o Cron consulta apenas dados da branch confiável, **sem executar scripts remotos**.
- O próprio código do controlador é carregado somente do checkout previamente instalado, exceto no bootstrap inicial do Cron.
- Recibo privado `~/.local/state/conexo-os/remote-control-receipt.json`; todo `job_id` é de execução única (inclusive quando há falha). Não repetir operações falhas automaticamente.

## Solicitação inicial
`ops/hostinger/remote_request.json`:
```json
{"schema":"conexo-remote-request/1","job_id":"binance-image-review-20261114-v1","action":"binance_image_review_package","article_ref":"binance-revisao-6e8da0b05713"}
```
Ação: validar manifesto da fotografia Unsplash previamente conferida em 1440/390; gerar **nova versão privada** do pacote Binance, com recursos de imagem e prévia local. **Nenhuma escrita no WordPress**. Não consumir Groq nem Turso. O hash novo substitui a versão anterior apenas para futuras decisões; não sobrescreve o arquivo anterior.

## Segurança e verificação mínima
1. O controlador confere origem Git, formato de solicitação, artigo e ação permitida, usa `flock` e salva recibo restrito em 0600.
2. Para verificar se o Cron foi realmente executado, consultar a operação **hosting_cron-jobs_output** da Hostinger por UID. **Agendamento criado não equivale a tarefa executada.**
3. Resultado esperado no recibo: `status=PASS` e duas operações bem-sucedidas. Em falha: apenas novo job id após corrigir a causa, sem regenerar o artigo.
4. Se houve `PASS`, inspecionar `preview_path` do novo pacote, conferência visual da **página completa** de 390 e 1440 ainda necessária, não apenas recorte da capa.
5. Para suspender tudo: apagar somente o Cron UID do controlador. Não tocar no workflow de coleta RSS existente nem na produção WordPress.
6. Aprovação humana final, licenças particulares e Gate editorial continuam necessários. Nenhuma conclusão 100% sem recibo real.

## Operação futura sem terminal
- O ChatGPT com conector GitHub altera somente `remote_request.json` com **novo job_id** e ação permitida.
- Hostinger Cron lê o comando e executa em ambiente privado; ChatGPT consulta o recibo do Cron no conector Hostinger.
- Isso resolve **o acionamento remoto dessas duas ações**, não ainda toda a orquestração editorial, que requer integração segura com os passos de Gate e WordPress.

## Evidência operacional recebida em 14/11/2026

O operador executou na Hostinger `git pull --ff-only` e depois
`.venv/bin/python ops/hostinger/remote_controller.py`.
O terminal retornou:

```json
{"job_id":"binance-image-review-20261114-v1","status":"PASS","steps":2,"receipt":"/home/u401421381/.local/state/conexo-os/remote-control-receipt.json"}
```

**Comprovado:** controlador executado manualmente até concluir as duas ações permitidas e registrar recibo privado. **Ainda não comprovado:** que o Cron automático tenha executado, pois a API oficial `hosting_cron-jobs_output` retornou saída vazia mesmo após cadastro. Os detalhes internos do recibo (hash do novo pacote e caminho da prévia) ainda não foram inspecionados nesta sessão. Não equivale a revisão humana de layout ou autorização para WordPress.
