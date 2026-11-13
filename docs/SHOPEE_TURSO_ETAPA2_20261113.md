# Shopee → SQLite → Turso: etapa 2 isolada (13/11/2026)

## Estado verificável
- Shopee Explorer respondeu HTTP 200 em consulta read-only.
- Proprietário executou `scripts/shopee_readonly_preflight.py --save-evidence` via Hostinger e confirmou `API_SHOPEE_READBACK_OK`, `novo_registro=true`, `Banco existe: True`, `Evidencias Shopee: 1`.
- SQLite está em `~/.local/share/mkt-rss/price_evidence.sqlite`, fora de public_html.
- Sincronizador desenvolvido em `mkt_flow_p0/price_evidence_turso.py` e `scripts/shopee_turso_homolog_sync.py`.
- Oito testes de regressão, isolados e sem rede, PASS; análise sintática compatível com Python 3.6 PASS.
- **Ainda não há prova de conexão real MKT-RSS → Turso ou criação da tabela remota**. Código no GitHub não equivale a deploy no servidor.

## Proteções obrigatórias
- Destino único permitido: `mkt-rss-homolog-rmsports33.aws-ap-northeast-1.turso.io`; recusa URLs de produção, outros hosts, parâmetros e caminhos.
- Apenas tabela nova `conexo_price_evidence_v1`, no banco já existente `mkt-rss-homolog`. Nunca modifica tabelas RSS, editorial, produtos ou WordPress.
- Leitura SQLite exclusivamente read-only; valida hash local registrado, data, marketplace Shopee e URL.
- ID remoto sha256 determinístico (produto, loja via URL, marketplace, preço, data, fonte e hash local); `INSERT OR IGNORE` e conferência exata no mesmo banco.
- Uma resposta de falha/timeout nunca é tratada como confirmação; usar `--verify` antes de reexecutar `--apply`.
- Banco principal `mkt-rss` intocado; não executar cron, Actions, publicação ou atualização de preços no WordPress.
- Credencial do Turso deve ser token **individual do banco mkt-rss-homolog**, fornecido em `getpass` no terminal privado. Não colar em chat, logs, argumentos ou histórico de shell. Não reutilizar token do banco de produção. O script mantém token apenas em variável de ambiente do processo e a remove após operação.

## Homologação real: três comandos separados
No terminal SSH privado da Hostinger:

```sh
cd ~/mkt-rss-shopee-check
git pull --ff-only
python3 -m py_compile mkt_flow_p0/price_evidence_turso.py scripts/shopee_turso_homolog_sync.py
python3 scripts/shopee_turso_homolog_sync.py --check
```

`--check` não conecta a Turso, não solicita token e deve exibir `{"ok":true,"local_records":1,...}` (a contagem pode ser maior após mais coletas).

Somente depois do `--check` e da confirmação de um token de banco individual no painel Turso:

```sh
python3 scripts/shopee_turso_homolog_sync.py --apply
```

O programa solicita **URL do banco de homologação** (exatamente `libsql://mkt-rss-homolog-rmsports33.aws-ap-northeast-1.turso.io`) e token **oculto**. Resultado de aceite: `ok=true`, `total_local>=1`, `exact_readback=total_local`, `new_remote_rows` conforme necessário.

Encerrar o processo; em uma **segunda execução independente**, validar sem reescrever:

```sh
python3 scripts/shopee_turso_homolog_sync.py --verify
```

Reinformar URL e token localmente. Aceitar somente `ok=true`, `exact_readback=total_local`, `new_remote_rows=0`. Se `--apply` falhar depois de tentar gravar, executar primeiro `--verify` para reconciliar o estado, não repetir escrita cegamente.

## Pendências após homologação Turso
1. Homologar primeira gravação `--apply` no banco `mkt-rss-homolog` com credencial limitada a esse banco.
2. Executar readback `--verify` separado e registrar somente o JSON sanitizado.
3. Verificar política de backup/restauração e limites gratuitos do Turso antes de ativar coleta periódica.
4. Integrar leitura read-only no Gate Editorial **sem permitir publicação ou atualização automática**.
5. Migrar operação para Python suportado, confirmar agendador único e segredo protegido; só então avaliar banco central principal por migração revisada.
