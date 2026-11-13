# MKT-RSS → Conexo Gate: execução existente (sem novo agendador)

## Inventário verificado em 13/11/2026
- **Hostinger:** servidor SSH `br-asc-web893`, conta `u401421381`, checkout informado: `~/mkt-rss-shopee-check`. Esse ambiente já executou uma integração de teste da Shopee, mas **não existe comprovação de processo MKT-RSS contínuo**.
- Hostinger API: lista de cron jobs e de repositórios associados ao domínio `conexotech.com.br` vazia.
- Vercel: entre seis projetos acessíveis não foi identificado um serviço MKT-RSS em execução.
- `conexo-os-runner` é um protótipo offline, não um executor editorial hospedado.
- Turso é banco de dados, não executor de processos.
- GitHub Actions já executou o MKT-RSS anteriormente, mas **não será utilizado** nesta integração.

## Código já pronto
- Gate `0.1.0-rc10.3`: `/wp-json/conexo/v1/editorial/remediation/queue` e `/excerpt`, com autorização vinculada a senha de aplicativo exclusiva.
- `mkt_flow_p0/conexo_remediation.py`: cliente de correções limitadas.
- `mkt_flow_p0/wp_draft_staging.py`: hook pós-gravação **opt-in**; por padrão está desligado.
- Conta WordPress: `Bot.editor`, ID 4. Aprovação humana continua exclusiva do proprietário no Gate.

## Pré-requisitos no checkout existente
Executar pelo terminal SSH Hostinger, **sem colocar senhas no chat, GitHub, arquivos públicos ou histórico de comandos**:

```bash
cd ~/mkt-rss-shopee-check
pwd
git remote -v
git status --short
python3 --version
command -v python3.11 || command -v python3.12 || true
```

Não fazer `git pull` em árvore com mudanças não salvas. A instalação conhecida usa Python 3.6.8; **não executar o cliente moderno nessa versão**. Escolher um Python >=3.10 existente no host/venv. Se não houver, parar e informar indisponibilidade: não criar serviço alternativo.

## Teste único, sem publicação
Depois de conferir a versão e atualizar o checkout de forma segura para incluir `conexo_remediation.py`, carregar a credencial **somente no terminal**:

```bash
export CONEXO_WP_USER='Bot.editor'
read -r -s -p 'Senha de aplicativo Conexo MKT-RSS: ' CONEXO_WP_APP_PASSWORD
printf '\\n'
export CONEXO_WP_APP_PASSWORD
python3.11 -m mkt_flow_p0.conexo_remediation --post-id 9708
```

O primeiro comando do cliente **não grava** nada. Conferir o diagnóstico, garantindo que o post ainda é um rascunho e que o resumo está vazio. Para um único ensaio controlado:

```bash
python3.11 -m mkt_flow_p0.conexo_remediation --apply --post-id 9708 --max-changes 1
unset CONEXO_WP_APP_PASSWORD CONEXO_WP_USER
```

Use o executável correto do ambiente (pode ser `python` dentro de um venv), não suponha que `python3.11` exista. O comando tem de terminar com `draft_excerpt_saved`, gravação confirmada e nenhum efeito na publicação. Se houver 401/403/429, **parar** e investigar autorização, credencial, rate limit ou WAF; não repetir automaticamente.

### Após o ensaio
Verificar no WordPress que o artigo permanece `draft`, que o resumo foi persistido e que o Gate removeu apenas a pendência correspondente. Validar também que o robô **não** pode aprovar ou publicar. Só então habilitar `CONEXO_GATE_REMEDIATION_AUTO=1` no **processo existente que já cria rascunhos**, sem instalar cron, Actions ou novo runner.

## Limite de conclusão
Sem acesso de comando ao shell Hostinger e sem a senha de aplicativo disponível ao executor, a execução do ensaio e o carregamento de segredos **não podem ser declarados concluídos**. Este documento é um procedimento e não prova implantação automática.
