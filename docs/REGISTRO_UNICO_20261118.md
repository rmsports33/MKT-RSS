# Registro único de funcionalidades e status — 18/11/2026

Fonte única para auditorias. Evita reler documentação dispersa.
Detalhes por tema permanecem nos documentos citados.

## 1. WordPress (plugins)

| Plugin | Versão | Status | Observação |
|---|---|---|---|
| conexo-editorial-gate | 0.1.0-rc10.4 | **ativo** | Gate Único; recebeu trava de proveniência |
| conexo-hmac-vault | 0.1.0 | ativo | Assinatura HMAC, chave no WP Vault |
| conexo-native-seo | 0.5.2 | ativo | — |
| conexo-native-seo (mu) | 0.5.1 | inativo | duplicado |
| conexotech-affiliates | 1.11.1 | ativo | class-checker via oEmbed |
| git-installer | 1.3.4 | ativo | — |
| hostinger-affiliate-plugin | 3.0.57 | ativo | — |
| jetpack | 16.3.1 | ativo | — |
| litespeed-cache | 7.9.2 | ativo | — |
| mailpoet | 5.44.0 | ativo | — |
| post-type-switcher | 4.1.1 | ativo | — |
| seo-by-rank-math | 1.0.280 | ativo | SEO público |
| google-site-kit | 1.190.0 | ativo | — |
| updraftplus | 1.26.14 | ativo | — |
| wordpress-importer | 0.9.7 | ativo | — |
| wp-consent-api | 2.1.0 | ativo | — |
| conexo-gate-agenda-nativa | 0.3.3 | **inativo** | legado; causa fatal se ativado (função duplicada) |
| hostinger-preview-domain | — | must-use | reescrita de host em XML-RPC/REST |

## 2. Módulos do motor MKT-RSS

| Módulo | Status | Observação |
|---|---|---|
| `editorial_import.py` | ativo | entrada canônica; gera manifesto e marca de proveniência |
| `editorial_provenance.py` | ativo | marca + validação do pacote |
| `editorial_video.py` | ativo | bloco de vídeo, curadoria humana obrigatória |
| `editorial_transport.py` | ativo | transporte assinado HMAC |
| `editorial_broker_transport.py` | ativo | publicação via broker, só publish/schedule |
| `wp_draft_staging.py` | ativo | cria rascunho com readback |
| `seo.py` / `seo_contract_native.py` / `seo_delivery_signing.py` | ativo | SEO nativo; assinatura bloqueada por chave ausente |
| `editorial_substance.py` | ativo | avaliação substantiva por critérios |
| `image_protocol.py` | ativo | protocolo de imagem |
| `editorial_readiness.py` | ativo | prontidão editorial |
| `release_guard.py` / `origins.py` | ativo | unificados |
| `triagem_decisoes.py` | ativo | decisão supervisionada, auditoria imutável |
| `conexo_remediation.py` | opt-in | `CONEXO_GATE_REMEDIATION_AUTO` desligado |
| Gate de valor M04.16D | opt-in | desligado |
| Publicação de comparativos | opt-in | desligado |
| `CONEXO_RSS_CRON_ACTIVE` | 0 | coleta manual |
| `CONEXO_ACTIONS_WRITER_DISABLED` | 1 | Actions writer desabilitado (política) |

## 3. SEO / GEO / AEO

| Item | Estado |
|---|---|
| Rank Math | ativo, 1.0.280 |
| Native SEO | ativo, 0.5.2, não assinado (falta chave) |
| Title da home | ❌ quebrado: `ConexoTech -` |
| Canonical / OG / Twitter / noindex | ✅ OK |
| Sitemaps | 5 no índice |
| Schema A57 | ❌ duplicação: Person×2, Rating×8, Review×21 |
| `llms.txt` | ✅ publicado (3.197 bytes) |
| GEO dashboard | parado em 04/10, scores 0 |
| Ferramentas GEO/AEO | scripts pontuais, nenhuma integrada ao fluxo |
| Regra 15 | AEO/GEO não é disciplina separada; `llms.txt` não muda Google |

## 4. Credenciais (somente nomes/estado — sem valores)

| Arquivo / origem | Estado |
|---|---|
| `wp-editorial.token` (24 chars) | conta Bot.editor, restrita a correção (403 em escrita) |
| `wp-engine.token` (24 chars) | conta Bot.editor, cria rascunhos (200), UUID `3a7fac3b…` |
| `wp-draft-writer.env` | criado, `600` |
| `cxrm_editor_app_password_uuid` | `6b060cb4…` (Conexo MKT-RSS) |
| `turso-readonly.token` / `turso-rss-writer.token` | válidos, expiram 20/11, permissão `rw` (API não gerou `ro`) |
| `rss-queue.env` | `CONEXO_ACTIONS_WRITER_DISABLED=1`, `CONEXO_RSS_CRON_ACTIVE=0`, `CONEXO_PRODUCT_LINKS_ENABLED=1` |
| `ai-keys.env` | GEMINI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY, GEMINI_MODEL, OPENROUTER_MODEL, AI_FREE_ONLY_ALLOWLIST |
| `groq-editorial.token` | presente (56 bytes) |
| GitHub MKT-RSS | 13 secrets (Groq, Turso, WP, Unsplash, EXA, Jina, Sheets, Telegram) |
| GitHub site | 36 secrets, incluindo `YOUTUBE_API_KEY`, `WP_USER_ADMIN`, FTP/SFTP, Hostinger, Drive, Notion, OpenCode |
| `CONEXO_EDITORIAL_GATE_KEY` | **ausente** — SEO nativo assinado indisponível |

## 5. Rascunhos e pautas

| Item | Estado |
|---|---|
| Post 9899 (Senado) | lixeira |
| Post 9900 (Anatel/TIM) | draft, manifesto presente, capa 0, sem vídeo |
| Post 9906 (TV 65″) | draft, manifesto presente, capa 0, sem vídeo |
| Fila Turso | 22 em `DESCOBERTA`, 3 em `SELECIONADA` |
| 37 rascunhos antigos | fila de correção, imagem licenciada pendente |

## 6. Pendências abertas (não executadas)

- Vídeo review: módulo portado, mas sem chave no servidor e sem vídeo curado
- Capa: sem imagem com direito verificado
- Token Turso `ro`: não gerado pela API
- SEO nativo assinado: falta chave
- Opt-ins: remediação, gate de valor, comparativos
- Aceite humano no Gate: nenhum artigo aprovado/publicado

## 7. Validação do readback dual-context — PR #127 (18/11/2026)

| Item | Status |
|---|---|
| SHA validado | `426a5662a55a4d68ba3c0367b2886bfe7d20bf2a` (bateria completa) e `72c3b9d253b95edc338b2846262d00815a0d5b2d` (HEAD atual do PR, reconfirmado); Python 3.14.7 |
| Validação automatizada do adaptador | **PASS** — 17, 37 e 171 testes nos três comandos; bateria relevante executada nos dois SHAs: 296 PASS + 10 subtests + 6 falhas de Windows (`os.getuid`/modo `0o600`), 302 testes no total — não executada em Linux; no HEAD atual, 17/37/171 e 3 testes novos do snapshot offline |
| Correlação real edit/view | **PASS (dados informados pelo proprietário)** — #9894 (11.435/11.447), #9900 (6.172/6.207) e #9906 (6.601/6.609): mesmo ID, status `draft`/`pending` e `modified` nos dois contextos; o agente não executou essas leituras autenticadas |
| Readback marcador + iframe + `VideoObject` | **PENDENTE** — #9900 e #9906 têm marcador no bruto, mas sem iframe nem `VideoObject`; nenhum post consultado reúne os três critérios; `_conexo_mkt_rss_run_id` ausente no `meta` do conector não prova ausência do metadado |
| Registro detalhado | comentário no PR #127 (atualizado com o complemento de 18/11) e `docs/WORDPRESS_GATE_PROVENANCE_READBACK_20261118.md` |

Não houve escrita WordPress/Turso, Gate, cron, Actions, merge, deploy nem publicação. Nenhum post de teste foi criado.

## 8. Patch kit Gate RC10.5 — PR #79 do site (18/11/2026)

| Item | Status |
|---|---|
| Escopo | **CONCLUÍDO EM CÓPIA ISOLADA** — validação controlada do kit `ops/gate-provenance-rc10.5/`; nenhuma alteração na instalação WordPress ativa |
| HEAD validado (kit) | `aa5085014696623e971c1ed75681f9defdc43b1f` (`-site-conexotech`, PR #79; correção do teste em commit separado) |
| Ambiente | PHP CLI 8.3.36 no Hostinger (o registro anterior citava 8.4.24, não disponível neste host); Python 3.11.18 do venv existente |
| Suíte sintética do aplicador | **FALHA INICIAL** — 2 passed, 1 failed (`exit(14)`): o teste marcava o post 1 como MKT-RSS e esperava `cxeg_quality_valid(1) === true` sem marca. Diagnóstico confirmado por harness PHP: `marker_missing`. Corrigida a expectativa (legacy passa; MKT-RSS sem marca bloqueia) sem enfraquecer assertivas |
| Suíte sintética final | **PASS** — 3 testes (`python -m unittest -v test_apply_gate_patch`) |
| Contrato PHP | **PASS** — 17 casos antes e depois do patch; `php -l` passa em helper, core e review-publisher |
| Cópia integral RC10.4 | **PASS** — dry-run com âncoras exatas; aplicação somente na cópia; idempotente; diff mostra só helper novo + core + review-publisher; hashes registrados |
| Comportamento na cópia integral | **PASS** — harness isolado com 11 checagens: legado sem run id segue fluxo humano; MKT-RSS sem marca bloqueia em `quality_valid`, `quality_record` e fila; com marca válida passa, sem eliminar aprovação humana |
| Limites | Não houve upload, ativação, deploy, escrita WordPress/Turso, Gate, cron, publicação nem alteração no plugin ativo; a cópia permanece fora do document root com sentinel |
| Detalhes | Comentário no PR #79 do `-site-conexotech`; evidências com hashes, comandos e saídas no próprio comentário |
| Plano de integração | **PLANEJADO, NÃO EXECUTADO** — `ops/gate-provenance-rc10.5/INTEGRATION_ROLLBACK_PLAN.md` no `-site-conexotech` (pré-condições, sequência, rollback e critérios de encerramento); PR #79 permanece em draft; nenhuma escrita em produção autorizada |

## 9. Validação da versão do contrato — SHAs fixados (18/11/2026)

| Item | Status |
|---|---|
| MKT-RSS #127 | **PASS** no SHA fixado `caef2eef41764d49a99cc4b25bb34d95167ec554` — 43 + 40 + 10 testes; exportador da fixture falhou na forma documentada por falta de `sys.path`, corrigido no commit `5406b07` e reexecutado com sucesso |
| Fingerprint compartilhado | `version_sha256` = `80d09ee7c49505560862a0364c1af8b4aa5b694f9db954b52b35f26b82bdbfaa`; `content_sha256` = `2d2c56ef81a5d943be99b486be49e59130fa1b76391e021905e33c0b0e337e49`; fixture 600 bytes, SHA-256 `676b674f7fc395f00e5fe4aa1b7ac897fb637c5de629cd88d2f3ae6e224a323f` |
| Gate RC10.5 #79 | **PASS** no SHA fixado `040c3bb7a1d9b4cde9b8632e318d6077df9b5445` — 20 asserções contratuais PHP, `php -l` OK, aplicador 3/3 OK (PHP 8.3.36; Python 3.11.18 do venv; `python3` do sistema é 3.6.8 e não atende ao kit) |
| Fixture cruzada | **PASS** — 20 asserções contratuais + 2 cruzadas: fixture real aceita; variante com digest divergente rejeitada com `version_hash_mismatch` |
| Harness integral RC10.4 | **PASS** — 11 checagens na cópia integral com sentinel, fora do document root; hashes/diff registrados; rollback testado em outra cópia com restauração dos dois arquivos e remoção do helper, hashes iguais aos pré-mudança, lint OK |
| Ambiente/limites | PHP 8.3.36, Python 3.11.18; sem Actions, rede, WordPress/Turso, cron, publicação, aprovação, upload, ativação, merge, deploy ou alteração do plugin ativo |
| Detalhes | Comentários nos PRs #127 (MKT-RSS) e #79 (`-site-conexotech`) |

## 10. Suite Hostinger do PR #127 — 19/11/2026

| Item | Status |
|---|---|
| Execução exata do bloco do operador | **PASS** — checkout operacional preservado; Python 3.11.18; worktree isolado em `~/tmp/p127`; suíte `ops/hostinger/validate_pr127_suite.sh` |
| Primeira execução | **FALHA** no head `a81b9c6` — `test_upload_date_nula_permanece_opcional` (1 failed, 196 passed, 3 subtests) |
| Causa e correção | `uploadDate: None` era preservado como chave no vídeo normalizado; corrigido em `1c84696014018bb8ae6d0eba4669ed608630e6b7` (`fix(video): tratar uploadDate nulo como campo ausente`), sem enfraquecer o teste |
| Execução final | **PASS** no head `1c84696` — **197 passed, 3 subtests, 0 failed**, `PR127_TEST_EXIT=0` |
| Limites | Sem GitHub Actions, WordPress/Turso, cron, publicação, aprovação, merge ou deploy; worktree temporário removido pelo próprio script |

## 11. Integração do PR #127 na branch de runtime — 19/11/2026

| Item | Status |
|---|---|
| Escopo | **EM EXECUÇÃO** — consolidação somente na branch `feat/hostinger-runtime-independente-20261113`; sem master, cron, produção, WordPress/Turso ou publicação |
| SHAs remotos | runtime `3901ca0802d500381d7b0372b4d75dc6fc2ec40e`; PR `1c84696014018bb8ae6d0eba4669ed608630e6b7` |
| Ancestralidade | runtime é ancestral do PR (0 commits à frente, 105 atrás); integração por fast-forward, sem reescrita nem force push |
| Suíte e diff | **PASS** — suíte Hostinger em Python 3.11.18: 197 passed, 3 subtests, 0 failed; diff de 24 arquivos revisado, sem workflows/cron/wp-content/public_html, sem segredos e sem módulos duplicados |
| Integração | **CONCLUÍDA** — runtime avançou por fast-forward, sem force push, de `3901ca0` para `1c84696` (passou por `50d8435` num primeiro push de ref local desatualizado, corrigido com novo fast-forward). PR #127 aparece como `MERGED` na base; `master` permaneceu em `101fe18` e não foi tocado |
| Reexecução na runtime | **PASS** — worktree isolado `~/tmp/runtime-verify` no SHA `1c84696`: 197 passed, 3 subtests, `RUNTIME_TEST_EXIT=0`; 0 GitHub Actions de push |
| Reversão | Não reescrever histórico: criar commits de `git revert` na própria runtime (ou apontar o deploy para tag/branch separada no SHA pré-integração `3901ca0`); não usar `--force`, não tocar posts, banco, cron, WordPress/Turso nem produção. Backup lógico = o próprio commit `3901ca0` permanece no histórico |
| Limites | Nenhuma alteração em master, cron, produção, WordPress, Turso, publicação, agendamento ou checkout operacional |

## 12. Auditoria e fechamento do readback nativo e do Revisor Único — 19/11/2026

| Item | Status |
|---|---|
| Escopo | **EM EXECUÇÃO** — rastrear produtor → WordPress → REST nativo → comparação raw/rendered → adaptador → Revisor Único → Gate RC10.4/RC10.5 |
| Restrições | Sem novo Gate, sem Revisor duplicado, sem string do conector como prova de `content.raw`, sem HTTP 200 como validação semântica, sem parecer sem hash/versão exatos, sem autorização de publicação pelo Revisor, fail-closed preservado |
| Resultado | **CONCLUÍDO (simulado + leitura real somente leitura)** — branch `fix/readback-native-reviewer-contract-20261119`, commit `d50344db52ad82acfc9b043fd0a790883ce780c5`; sem novo Gate, sem Revisor duplicado, sem escrita/autorização/publicação |
| Arquivos alterados | `editorial_wordpress_adapter.py`; `tests/test_editorial_wordpress_adapter.py`; `tests/test_gate_local_unification.py`; `tests/test_readback_gate_parecer_e2e.py` (novo) |
| Contrato REST nativo | `content.raw` só é aceito quando vem de objeto `content` com chave `raw` em resposta `context=edit`; string achatada do conector é rejeitada em `assemble_wordpress_context_readback` e na validação de leitura. ID, status, `modified` e `meta._conexo_mkt_rss_run_id` (quando presentes nos dois contextos) devem coincidir |
| Ponta a ponta simulada | Produtor (`marcar` com fingerprint canônico) → REST edit/view → `validate_wordpress_content_readback` → Revisor Único existente (`verify_independent_review`) → pacote `conexo-owner-release/1` validado → `authorize_publish`. HTTP 200 com pacote inválido é bloqueado; parecer sem `owner_release` não autoriza; `readiness_overview.publication_authorized` continua `False`; release com conteúdo/post divergentes gera `remote_version_mismatch` / `gate_owner_release_post_mismatch` |
| Testes | Local Python 3.14: 41 passed nos arquivos diretamente afetados; Hostinger Python 3.11.18: **152 passed, 3 subtests, `READBACK_TEST_EXIT=0`** na suíte de 10 arquivos relevantes |
| Evidência real | GET autenticado somente leitura em `wp-json/wp/v2/posts/9900` com token local existente (valor nunca impresso): edit 200 com `content.raw`/`content.rendered`, view 200 somente `rendered`, mesmo ID 9900, mesmo `status=draft`, mesmo `modified=2026-11-19T06:47:48`; `raw_sha256=4c54c89200ec0ae237f3a0454b699ae3c141e71415041683aa60eebcb8a9abba`, `rendered_sha256=5cd9696c26e63c91f188e4ccdbf8b7d4594a67eb9bfaf7619392c28f59fb50f0`; montagem nativa retornou `valid=true`, `blockers=[]` |
| Ainda exige WordPress real | Aprovação humana pelo proprietário no Gate com identidade/revisor distintos; emissão autêntica do `owner-release` assinado/vinculado à versão; persistência de vídeo curado com iframe+`VideoObject` sobrevivendo ao `rendered`; publicação/agendamento e cron; configuração `cxeg_broker_authorized_actors`; prova de que `meta` ausente no conector reflete ausência real no servidor |

## 13. Auditoria pré-implantação do tema ConexoTech 1.7.0 — 19/11/2026

| Item | Status |
|---|---|
| Escopo | **EM EXECUÇÃO** — somente auditoria e preparação; sem ativação de tema, atualização de plugins, upload ou alteração de produção |
| Regras | ZIP de tema, registro de plugin, backup sem data/tamanho/integridade ou sem procedimento de restauração não contam como backup válido |
| Resultado | **NÃO IMPLANTAR** — tema ativo `conexotech` 1.6.9; pacote 1.7.0 identificado no commit `7cc710fa0727a64831d3057f6068cc75cd384979` (árvore `75f97410c2c281f13a70c852017d25895ddb16f7`); existe conjunto UpdraftPlus integral de 17/11 com checksums, mas sem download/verificação e sem restauração isolada provada |
| Backup integral | Conjunto `12723a7e7b3e` (17/11 17:32) com db + themes + plugins + uploads + mu-plugins + others, SHA-256 declarados; storage Google Drive e `updraft_delete_local=1`. Conjuntos de 18/11 são somente banco ou somente arquivos; ZIP local de 18/09 é só tema |
| Restauração | RUNBOOK descreve restauração pelo painel UpdraftPlus, mas ela substitui produção; não há rclone/gdrive/addon de clonagem nem prova de restore isolado. Versão anterior é restaurável via conjunto integral; commit `5bfbf28` tem 1.6.9 mas difere do servidor |
| Documento e branch | `docs/PRE_DEPLOY_TEMA_1_7_0_20261119.md` em `rmsports33/-site-conexotech`, commit `57ac4a303b55d211f4bbfd50757068bc52f8780e`, branch `docs/theme-1.7.0-predeploy-audit-20261119` |
| Falta | Baixar/verificar o conjunto integral, restaurar em cópia isolada, gerar backup novo na janela, autorização operacional; nada foi ativado, publicado ou alterado em produção |

## 14. Tentativa de atualização do checkout operacional — 19/11/2026

| Item | Status |
|---|---|
| Comando | Bloco do operador com `git switch`, `git pull --ff-only`, `git merge --ff-only` e testes no `~/mkt-rss-runner` |
| Resultado | **BLOQUEADO COM SEGURANÇA** — Git recusou `pull` e `merge` porque `mkt_flow_p0/editorial_import.py` está modificado localmente e `editorial_provenance.py`/`editorial_video.py` são não rastreados e seriam sobrescritos |
| Estado preservado | HEAD continua `3901ca0802d500381d7b0372b4d75dc6fc2ec40e`; alterações e 31 arquivos não rastreados intactos; nenhum `stash`, `checkout -f` ou remoção foi executado |
| Testes | Não rodaram no checkout antigo porque `tests/test_readback_gate_parecer_e2e.py` não existe na baseline; a validação real já está registrada na seção 12, em worktree isolado |
| Próxima ação | Não forçar. Preservar o operacional; se a atualização local for desejada, mover as alterações preexistentes para cópia nomeada com autorização explícita e repetir o fast-forward |

## 15. Validação isolada do readback no operacional — 19/11/2026

| Item | Status |
|---|---|
| Worktree | `~/mkt-rss-readback-validation`, criado em `d50344db52ad82acfc9b043fd0a790883ce780c5`, fora do checkout operacional |
| Comando do bloco | `python3.11` não existe no PATH do host; a suíte não rodou na primeira execução do bloco |
| Reexecução | Com Python 3.11.18 do venv existente: **38 passed, 0 failed** nos três arquivos pedidos |
| Checkout original | HEAD `3901ca0` e alterações preexistentes intactos; nenhuma integração foi forçada |

## 16. Suíte completa no worktree isolado — 19/11/2026

| Item | Status |
|---|---|
| Ambiente | Worktree `~/mkt-rss-readback-validation` em `d50344d`, Python 3.11.18 do venv do runner |
| Suíte completa solicitada | **BLOQUEADA NA COLETA** — `ModuleNotFoundError: No module named 'cryptography'` em `tests/test_live_handoff_quality_audit.py`; `PYTEST_EXIT=2`, HEAD e árvore inalterados |
| Causa | `cryptography>=42.0.0` está declarado em `requirements/base.txt` e `requirements/rss.txt`, mas não está instalado nesse venv |
| Diagnóstico extra | Ignorando apenas esse módulo: **1606 passed, 4 failed, 12 skipped, 52 subtests**; as quatro falhas em `test_produce_bank_article.py` também são `ENCRYPTION_UNAVAILABLE_NO_RAW_EXPORT` pela mesma dependência ausente |
| Conclusão | Falha de ambiente, não regressão do código de readback; a suíte focal do readback passou 38/38 na seção 15 |

## 17. Suíte completa com dependência isolada — 19/11/2026

| Item | Status |
|---|---|
| Comando | Bloco do operador instalando `cryptography>=42.0.0` em diretório próprio e rodando a suíte no worktree `~/mkt-rss-readback-validation` |
| Instalação | `pip install --target ~/mkt-rss-readback-validation-deps` → `cryptography 50.0.2`, `cffi 2.1.1`, `pycparser 3.12`. O venv do runner **não foi alterado** |
| Ambiente | Python 3.11.18, HEAD `d50344db52ad82acfc9b043fd0a790883ce780c5`, árvore limpa antes e depois |
| Resultado | **1619 passed, 11 skipped, 52 subtests passed, PYTEST_EXIT=0** |
| Leitura | Com a dependência presente a suíte completa passa; as 4 falhas e o erro de coleta da seção 16 eram só ambiente ausente, não regressão do readback |
| Resíduo | Diretório `~/mkt-rss-readback-validation-deps` permanece no host apenas para reprodução; pode ser removido sem afetar o checkout operacional |

## 18. Reverificação de fast-forward antes de integrar — 19/11/2026

| Item | Status |
|---|---|
| Comando | Bloco do operador somente leitura no worktree `~/mkt-rss-readback-validation` |
| Referências | `origin/feat/hostinger-runtime-independente-20261113` = `1c84696014018bb8ae6d0eba4669ed608630e6b7`; readback = `d50344db52ad82acfc9b043fd0a790883ce780c5` |
| Ancestralidade | `merge-base --is-ancestor` retornou 0 → **FAST_FORWARD_SEGURO** |
| Master | `101fe18ddfcfdd6ee7dfaf356f860be1db54b9ff`, apenas lido |
| Worktree | Árvore limpa no readback; nenhuma integração executada |

## 19. Fast-forward da runtime para o readback — 19/11/2026

| Item | Status |
|---|---|
| Alvo | `feat/hostinger-runtime-independente-20261113`: `1c84696014018bb8ae6d0eba4669ed608630e6b7` → `d50344db52ad82acfc9b043fd0a790883ce780c5` |
| Verificações prévias | Worktree no alvo e limpo; runtime remota conferida em `1c84696`; `merge-base --is-ancestor` OK (fast-forward) |
| Bloqueio encontrado | O push pelo host falhou: `could not read Username for 'https://github.com'` — o Hostinger não tem credencial de push |
| Execução real | Push não forçado feito do clone Windows: `1c84696..d50344d`, exit 0 |
| Resultado remoto | `git ls-remote` confirma runtime em `d50344db52ad82acfc9b043fd0a790883ce780c5` |
| Master | `101fe18ddfcfdd6ee7dfaf356f860be1db54b9ff`, inalterado |
| Checkout operacional | `~/mkt-rss-runner` segue em `3901ca0`, alterações preexistentes intactas; nada foi atualizado ali |
| Actions | `gh run list` vazio para a branch — nenhuma execução disparada |

## 20. Backup UpdraftPlus 17/11 (`12723a7e7b3e`) — auditoria de restauração — 19/11/2026

| Item | Status |
|---|---|
| Escopo | Comprovar integridade e restaurabilidade; sem tocar produção, sem implantar tema 1.7.0, sem mover/apagar arquivos |
| Manifesto | Localizado: opção `updraft_backup_history`, conjunto `12723a7e7b3e`, 17/11/2026 17:32:39, `created_by_version` 1.26.14, storage `googledrive`. Log `log.12723a7e7b3e.txt` termina com `The backup succeeded and is now complete` |
| Arquivos | Seis componentes declarados (`db.gz` 1.102.023 B; `themes.zip` 24.420.411; `plugins.zip` 64.842.334; `uploads.zip` 260.493.677; `mu-plugins.zip` 9.853; `others.zip` 4.093.444), ≈355,6 MB, com SHA-256 declarados |
| SHA-256 verificado | **NÃO** — nenhum arquivo acessível; nada foi baixado nem medido |
| Acesso ao Drive | **BLOQUEADO**: `rclone`/`gdrive`/`gsutil` ausentes; sem credencial em disco; `tmp_access_token.refresh_token` vazio; access token expirado respondeu HTTP 401 `UNAUTHENTICATED`; sem pasta do Drive sincronizada no Windows |
| Cópias locais | Nenhuma no servidor (só o log) nem nas pastas pessoais do Windows |
| Restauração isolada | **NÃO EXECUTADA**. Banco separado indisponível: usuário MySQL tem `ALL PRIVILEGES` só em `u401421381_p5HTW`, `SHOW DATABASES` lista apenas `information_schema` e o banco de produção; Docker instalado no Windows mas com daemon parado; sem MySQL/PHP locais |
| Rollback | Procedimento documentado; produção intacta. Ambiente isolado = descartar container/banco de teste |
| Evidência | `docs/BACKUP_RESTORE_AUDIT_20261119.md` em `rmsports33/-site-conexotech`, commit `fb9a5a5d6a62ad7cdf6808c22ea282d5ea4c59ec`, branch `docs/theme-1.7.0-predeploy-audit-20261119` |
| Falta | (1) credencial de Drive válida ou download manual dos seis arquivos; (2) banco isolado (Docker iniciado ou MySQL separado). Só então executar verificação de hashes e restauração de teste |

## 21. Verificação do download do conjunto 19/11 (`02e0bbf55cbc`) — 19/11/2026

| Item | Status |
|---|---|
| Comando | Bloco PowerShell do operador apontando para `C:\Backups\ConexoTech-2026-11-19`, com seis SHA-256 esperados |
| Resultado | **6 de 6 AUSENTE** — a pasta `C:\Backups\ConexoTech-2026-11-19` **não existe**; `C:\Backups` também não existe; nenhum dos seis arquivos foi encontrado no perfil do usuário. Bloco reexecutado após nova tentativa de download: mesmo resultado (6 ausente). Pasta de destino criada vazia em 19/11 11:56 |
| Único arquivo baixado | `C:\Users\LIVE2PC\Downloads\log.02e0bbf55cbc.txt` (108.783 bytes, 19/11 11:09) |
| Hashes esperados | Conferem exatamente com o manifesto do WordPress para `02e0bbf55cbc` (os seis `checksums.sha256`), ou seja, a lista de referência está correta; falta o conteúdo |
| Conjunto de 17/11 | **DELETADO**: o log de 19/11 registra `Google Drive: … 12723a7e7b3e-plugins/themes/uploads/mu-plugins/others.zip: Deletion successful` por limite de retenção; o conjunto saiu do `updraft_backup_history`. Não é mais restaurável |
| Conjunto de 19/11 | Manifesto completo: db 1.133.806 B, themes 24.420.411, plugins 64.846.048, uploads 267.511.115, mu-plugins 9.853, others 4.093.529; log confirma upload `OK` e `The backup succeeded and is now complete` |
| Retenção | `weekly` para arquivos, `daily` para banco, `retain=3`, `retain_db=3`, `delete_local=1` — o conjunto de 19/11 pode ser apagado automaticamente antes de uma janela de deploy |
| Evidência | `docs/BACKUP_RESTORE_AUDIT_20261119.md` atualizado (seção 8), commit `084b216a7539f0b23b7db82b9436510b62250771` |
| Falta | Baixar os seis arquivos do conjunto `02e0bbf55cbc` do Google Drive para um diretório local e repetir a verificação de SHA-256; restauração isolada continua dependendo de banco separado |

## 22. Preservação das versões manuais do operacional — 19/11/2026

| Item | Status |
|---|---|
| Comando | Bloco do operador copiando `editorial_import.py`, `editorial_provenance.py` e `editorial_video.py` do runner para `~/mkt-rss-manual-code-preserved-20261119` |
| Resultado do bloco | **BLOQUEADO na guarda** (`exit 11`): o diretório de preservação **já existia** (criado 19/11 15:53). Nada foi criado, copiado ou sobrescrito |
| Conteúdo já presente | Os três arquivos, byte a byte iguais aos do runner (comparação `cmp`): `import` `d99b05eb8eaa0dc8…`, `provenance` `854c8e7deb1234…`, `video` `1c3dfa9e2fe060…` |
| Comparação com o candidato `d50344d` | Nenhum símbolo exclusivo do preservado: `def`/`class` e constantes do preservado são subconjunto do candidato. Candidato tem mais: `editorial_provenance.py` 195 vs 65 linhas, `editorial_video.py` 338 vs 88, `editorial_import.py` 289 vs 237 |
| Leitura | Atualizar o runner não descartaria código manual exclusivo; as versões manuais são anteriores e menores que as do candidato |
| Estados | Runner em `3901ca0`, 106 atrás do remoto, com as mesmas alterações locais; candidato limpo em `d50344db52ad82acfc9b043fd0a790883ce780c5` |
| Ambientes Python | Runner: `.venv` com Python 3.11.18, sem `cryptography`; candidato: **sem `.venv` próprio** |
| Configuração operacional | Busca por `.env`, `*.token` e `*credential*` na raiz e nível 1 do runner: nenhum arquivo encontrado |

## 23. Checkout preparado e isolado do candidato — 19/11/2026

| Item | Status |
|---|---|
| Comando | Bloco do operador: validar candidato, listar dependências, clonar para `~/mkt-rss-runtime-prepared-20261119` e fixar em `d50344d` |
| Pré-condições | Candidato conferido em `d50344db52ad82acfc9b043fd0a790883ce780c5` e limpo; destino ainda inexistente |
| Dependências encontradas | `requirements.txt` na raiz e `redator-artigo-blogs/requirements.txt` |
| Clone | `git clone --no-hardlinks` concluído; `checkout --detach d50344d` → HEAD `d50344db52ad82acfc9b043fd0a790883ce780c5`, árvore limpa, com `.git` próprio (isolado do runner) |
| Runner | `3901ca0` e alterações preexistentes intactas |
| Falta | Criar virtualenv próprio do checkout preparado e instalar dependências antes de qualquer teste; não feito nesta etapa |
| Dependências detalhadas | `requirements.txt` apenas inclui `-r base.txt`; `base.txt` tem core (dotenv, requests, httpx, pydantic, tenacity), LLM (groq, openai, tiktoken, langdetect), API (fastapi, uvicorn, redis), Google (google-api-python-client, google-auth, gspread), RSS (feedparser, trafilatura), Pillow, idna, testes (`cryptography>=42.0.0`, pytest, pytest-asyncio) e streamlit opcional; `requirements/rss.txt` tem versões fixas do pipeline diário; `redator-artigo-blogs/requirements.txt` tem openai, python-dotenv, requests, pytest. Não há `pyproject.toml`, `setup.cfg` nem `tox.ini` |
| Observação de caminho | O bloco consultou `~/mkt-rss-runtime-prepared` (inexistente); o clone real é `~/mkt-rss-runtime-prepared-20261119` |
| Venv do preparado | Criado em 19/11 com Python 3.11.18; instalados cryptography 50.0.2, pytest 9.2.0, pytest-asyncio 1.5.0, requests 2.34.2, python-dotenv 1.2.4, pydantic 2.14.4, tenacity 9.2.1, Pillow 13.0.0, feedparser 6.0.14, trafilatura 2.3.1 (36 pacotes). `pip check`: sem dependências quebradas |
| Ajuste de trabalho | `.venv/` adicionado ao `.git/info/exclude` do clone (arquivo local, não versionado) para o `git status` continuar vazio; HEAD segue `d50344d` |
| Coleta de testes | `pytest --collect-only -q` no preparado: **1629 testes coletados em 3,03s, sem erro de coleta**; checkout conferido em `d50344d` e limpo antes |
| Suíte completa | `pytest -q --tb=short` no preparado: **1619 passed, 11 skipped, 52 subtests, EXIT_CODE=0**, 17,13s; `git status` vazio e HEAD `d50344d` depois. Resultado coincide com a validação de 19/11 do worktree de readback |

## 24. Auditoria de pontos de entrada, contratos e testes do Revisor Único e do Gate — 19/11/2026

| Item | Status |
|---|---|
| Escopo | Leitura do código em `d50344db52ad82acfc9b043fd0a790883ce780c5` (mesmo conteúdo do checkout preparado); sem rede, sem escrita em produção, sem alterar código ou Gate |
| Documento e branch | `docs/AUDITORIA_REVISOR_GATE_D50344D_20261119.md` em `rmsports33/MKT-RSS`, commit `a1b348ad25aa69fe4296f901f0d3d25b0abb57ee`, branch `docs/auditoria-revisor-gate-20261119` |
| Pontos de entrada do Revisor | `editorial_trusted_review.verify_independent_review` (única função do módulo) sobre `editorial_factual_certificate.verify_factual_certificate`/`draft_digest`; **não existe implementação de `lookup_review`** no repositório — a consulta é sempre injetada |
| Pontos de entrada do Gate | `authorize_publish`/`require_publish_authorization` (`editorial_publish_gate.py`), `inspect_wordpress_draft`/`assemble_wordpress_context_readback`/`validate_wordpress_content_readback` (`editorial_wordpress_adapter.py`), `validate_owner_release`/`read_owner_release`/`advisory_gate_receipt`/`build_release_trace` (`mkt_flow_p0/gate_unified.py`), `publish_via_broker`, CLI `tools/publish_owner_approved.py`, `pipeline_rss.py:469-470`; plugin PHP do Gate não está no repositório |
| Contratos conferidos | `content.raw` como única fonte de versão; pareamento edit/view com mesmo `id`/`modified`/`status`; `_conexo_mkt_rss_run_id` divergente bloqueia; `owner_id == 3` + `review_mode == "owner"` + 13 checks; versão vinda do servidor; HTTP 200 não valida sozinho — todos implementados |
| Achado A1 (alto) | **O Revisor Único não está ligado ao caminho de publicação**: `verify_independent_review` não é chamado por `authorize_publish`, broker, pipeline nem CLIs; ocorre só na definição, em testes e em documento. O elo da seção 12 é feito pelo teste ponta a ponta, não pelo código de produção |
| Achado A2 (alto) | `factual_review` é aceito e **ignorado quando existe pacote canônico**: em `authorize_publish`, o parâmetro só produz bloqueio no ramo em que `package`/`core_root` faltam (`editorial_publish_gate.py:96-100`); o teste `test_readback_gate_parecer_e2e.py:135-147` passa `{"verified": True}` sem validação |
| Achado A3 (médio) | `trusted_factual_review_missing` é emitido por ausência do pacote, não por revisão reprovada — o nome pode mascarar A2 em logs e pareceres |
| Achado A4 (médio) | Nenhum teste monta pacote+recibo válidos com parecer **reprovado** para provar bloqueio, porque esse caminho não existe hoje |
| Achado A5 (baixo) | `editorial_publish_transition.plan_publish_transition` sempre devolve `allowed: False` (fail-closed por desenho), duplicando a regra do guard oficial |
| Achado A6 (baixo) | `content_digest` (gate_unified) e o SHA-256 inline de `validate_wordpress_content_readback` calculam o mesmo digest em implementações separadas |
| Testes mapeados | `test_editorial_trusted_review` 6, `test_readback_gate_parecer_e2e` 6, `test_gate_unified` 24, `test_gate_local_unification` 10, `test_editorial_publish_gate` 17, `test_editorial_wordpress_adapter` 22; suíte completa no checkout preparado 1619 passed / 11 skipped / 0 failed |
| Ações | Nenhuma correção aplicada nesta etapa; recomendações registradas no documento. Não altera Gate, não autoriza publicação, não implanta nada |

## 25. Correção do parecer do Revisor Único no guard local — 19/11/2026

| Item | Status |
|---|---|
| Branch e commit | `fix/revisor-unico-gate-verificacao-20261119` @ `a1de816bf33524f5da0ab2f977daa33533efcf14`, publicada no GitHub (`git ls-remote` confirma); base `d50344d` |
| Origem | Achados A1–A4 da seção 24 |
| Mudança principal | `authorize_publish` agora recebe `review_certificate`, `review_signing_key`, `lookup_review` e `now`; confere o parecer com `verify_independent_review` contra o registro confiável do chamador e bloqueia quando faltam argumentos ou quando a verificação falha |
| Códigos de bloqueio | `trusted_factual_review_missing` (sem certificado/chave/consulta), `trusted_factual_review_<motivo>` (motivo vindo do Revisor: `certificate_invalid`, `review_record_mismatch`, `trusted_review_unavailable`, `review_record_missing`, `trusted_review_store_missing`) e `trusted_factual_review_verification_unavailable` em exceção |
| A2 corrigido | `factual_review` continua aceito por compatibilidade, mas é documentado como autodeclarado e nunca conta como verificação; o dicionário `{"verified": True}` do teste antigo passou a ser comprovadamente insuficiente |
| A3 corrigido | O bloqueio deixou de depender da ausência do pacote: a verificação do Revisor roda sempre, com ou sem pacote canônico |
| A4 corrigido | Quatro testes novos em `tests/test_readback_gate_parecer_e2e.py`: (1) pacote + recibo válidos + parecer verificado autorizam a transição simulada (`autorizado: True`, `bloqueios: []`); (2) sem parecer → `trusted_factual_review_missing`; (3) parecer revogado → `trusted_factual_review_review_record_mismatch`; (4) dicionário autodeclarado nunca verifica |
| Propagação | `pipeline_rss.autorizar_transicao_publicacao` repassa os quatro novos parâmetros; nenhum caminho ficou com verificação implícita. O Revisor continua sem autorizar publicação sozinho |
| Teste local (Windows) | 68 passed nos seis arquivos de Gate/Revisor/readback; suíte ampla com 34 falhas preexistentes idênticas à baseline `d50344d` (ambiente Windows: `fcntl`, sqlite e caminhos), sem regressão atribuível à mudança |
| Teste no checkout preparado (Hostinger) | Commit exato `a1de816` via `git fetch` do GitHub; **1623 passed, 11 skipped, 52 subtests, EXIT_CODE=0** em 39,53s; `git status` limpo depois |
| Limites | Nenhuma alteração em master, runtime `d50344d`, produção, WordPress, Turso, Gate RC10.5, cron ou publicação; nenhuma implantação; A5 (`plan_publish_transition` duplicado) e A6 (digest duplicado) seguem abertos |

## 26. Registro do Revisor assinado e adequação dos testes de ponta a ponta — 19/11/2026

| Item | Status |
|---|---|
| Branch | `fix/revisor-unico-gate-verificacao-20261119`; head final `fb96e0c1f9f34d86bd40fcd433ef17e827d0dc30`, conferido por `git ls-remote` |
| Commit próprio | `a1de816` (seção 25) continua ancestral do head; nenhum histórico foi reescrito |
| Commits de outra sessão | `951c555`, `c6b70ae`, `7efa562`, `a674bbf`, `edff6da` (autoria rmsports33, 19/11 14:07–14:08), empilhados sobre `a1de816`: exigem que o registro do Revisor venha assinado com chave **distinta** da do certificado e propagam `registry_verification_key` pelo guard e pelo pipeline |
| Efeito nos testes da seção 25 | Quatro testes de ponta a ponta falharam no checkout preparado (`4 failed, 1632 passed`) porque usavam o envelope sem assinatura e a assinatura antiga de `verify_independent_review`; não era regressão de produção, era contrato novo |
| Correção desta etapa | Somente `tests/test_readback_gate_parecer_e2e.py`: envelope assinado com `sign_registry_record`, chave de registro separada e `registry_verification_key` nas chamadas; novo teste de envelope assinado com chave errada → `trusted_factual_review_review_record_signature_invalid` |
| Commit da correção | `fb96e0c` — “test(readback): assinar registro do Revisor e cobrir chave divergente” |
| Testes focados (Hostinger) | `test_editorial_trusted_review`, `test_editorial_publish_gate`, `unit/test_pipeline_rss_gate_p0`, `test_editorial_publish_transition`: **65 passed, 0 failed** |
| Suíte completa (Hostinger) | **1637 passed, 11 skipped, 52 subtests, 0 failed** em 15,39s; `git status` limpo no commit `fb96e0c` |
| Teste local (Windows) | 34 falhas preexistentes idênticas à baseline `d50344d` (ambiente Windows) e 1549 passed com os commits novos; nenhuma falha nova |
| Limites | Nenhuma alteração em master, runtime, produção, WordPress, Turso, cron, Gate RC10.5 ou publicação; 0 GitHub Actions disparadas pelos pushes |

## 27. Correção dos dois testes de broker desatualizados — 19/11/2026

| Item | Status |
|---|---|
| Branch e commit | `fix/broker-revisor-guard-tests-20261119` @ `e1c33a535233decd48770598c623c90fe2846eb9`, criada de `e4276c2`; publicada no GitHub |
| Restrições honradas | `fix/revisor-gate-publish-path-20261119` e o checkout compartilhado `~/mkt-rss-runtime-prepared-20261119` **intactos**: seguem em `e4276c2`, limpos. Validação feita em clone isolado `~/mkt-rss-broker-tests-20261119` |
| Causa | `e9e08fd` desabilitou de propósito a publicação pelo broker (`trusted_factual_review_broker_guard_not_integrated`) enquanto o broker não expõe o contrato do Revisor; dois testes antigos ainda esperavam o comportamento clássico |
| Correção | Somente `tests/test_editorial_broker_transport.py`. O teste de encaminhamento virou `test_transport_refuses_broker_publish_before_any_write` (subTest publish/schedule): recusa antes de broker, de `requests.get/post` e de `load_core`, com `erro: fluxo editorial bloqueado` e `reason` contendo `trusted_factual_review_broker_guard_not_integrated`. O teste de retomada virou `test_broker_resume_with_nonce_is_refused_before_any_write`: mesmo bloqueio, `broker.assert_not_called()`, sem POST/GET no WordPress, sem consumir nonce |
| Cobertura preservada | `require_signed_seo` no caminho direto `publish_via_broker` continua coberto por `test_strict_broker_checks_readiness_and_finishes_without_external_key` (assert `sent['require_signed_seo'] is True`), `test_strict_broker_unready_never_publishes` e `test_seo_failure_after_publication_returns_identity_without_retry` |
| Código de produção | Nenhum alterado; nenhum comportamento restaurado; o bloqueio do broker permanece |
| Testes focados | 74 passed, 1 warning, 2 subtests, EXIT 0 |
| Suíte completa | **1637 passed, 11 skipped, 54 subtests, 0 failed** em 21,65s |
| Teste local (Windows) | 13 passed no arquivo afetado; suíte ampla: 34 falhas preexistentes idênticas à baseline `d50344d`; nenhuma regressão nova |
| Limites | 0 GitHub Actions; nenhuma escrita no WordPress, merge ou deploy; a integração real do contrato autenticado do Revisor com o broker segue pendente — suíte verde **não** autoriza publicação nem completa a integração |

## 28. Especificação do contrato Broker–Revisor–Gate — 19/11/2026

| Item | Status |
|---|---|
| Documento e branch | `docs/BROKER_REVISOR_GATE_CONTRACT_20261119.md` em `rmsports33/MKT-RSS`, commit `9c5b596cd8aaa5fc97b7cb9b189f8ac2d849d284`, branch `docs/broker-revisor-gate-contract-20261119`, base master `101fe18` |
| Objetivo | Um contrato verificável entre MKT-RSS (cliente), o registro confiável do Revisor, o Gate RC10.5 e o broker Conexo, antes de qualquer retirada do bloqueio do broker |
| Conteúdo | Atores e fronteiras de confiança; quatro chaves separadas (emissor, registro, Gate, broker); mensagens M1 certificado, M2 envelope endurecido (`registry_seq`, `served_at`, TTL 3600s), M3 owner-release, M4 readback edit/view correlacionado, M5 recibo informativo; ordem de 9 etapas de verificação no broker; 26 códigos de bloqueio |
| Testes de segurança | 28 casos `SEC-01` … `SEC-28` (certificado forjado/revogado/expirado, registro adulterado/stale/replay/revogado, readback divergente, owner-release errado, pacote adulterado, nonce repetido, rede indisponível) + 5 positivos e prova de 1 escrita no máximo; nenhum com escrita real no WordPress |
| Critérios de aceitação | 7 itens (28/28 SEC + positivos verdes; suíte completa; rollback/restauração comprovados; chaves só no servidor; revisão humana do proprietário; PR #130 sem merge/deploy automático; homologação registrada) |
| Limites | **Especificação apenas.** Não altera código, não retira `trusted_factual_review_broker_guard_not_integrated`, não autoriza publicação, não cria PR nem implanta nada; PR #130 continua draft e não está pronto para integração final; 0 GitHub Actions |

## 29. Revisão 2 do contrato Broker–Revisor–Gate — 19/11/2026

| Item | Status |
|---|---|
| Documento e branch | Mesmo caminho `docs/BROKER_REVISOR_GATE_CONTRACT_20261119.md`, agora revisão 2.0, em `docs/broker-revisor-gate-contract-rev2-20261119`, commit `5b15c719e651f4b467c87954b9da2c7163a52d23` |
| Histórico preservado | A v1 permanece **intacta** em `docs/broker-revisor-gate-contract-20261119` @ `9c5b596cd8aaa5fc97b7cb9b189f8ac2d849d284`; `git ls-remote` confirma os dois SHAs |
| Crítica C1 | M1 passa a exigir Ed25519 com chave pública no verificador; HMAC legado só em servidor de confiança e com migração obrigatória antes da homologação |
| Crítica C2 | M2 assina o envelope inteiro (`protocol_version`, `alg`, `kid`, `record`, `served_at`, `registry_seq`); `registry_seq_floor` removido e sequência passa a ser autoritativa no servidor |
| Crítica C3 | Allowlist explícita em `CONEXO_BROKER_ALLOWED_ORIGINS`; produção proibida em perfil `staging`; `SEC-29` |
| Crítica C4 | Definição formal de `draft_digest` (JSON canônico de campos do REST edit) e `content_digest` (SHA-256 de bytes UTF-8 de `content.raw`); comparação cruzada proibida, ponte por igualdade byte a byte |
| Alta A1 | E1 (`context=edit`, autenticado), E2 (`context=view`, autenticado) e E3 (página pública) separados, com campos próprios e correlação explícita |
| Alta A2 | M1–M4 são pré-condições; M5 é recibo **pós-escrita** |
| Alta A3 | Três classes de repetição (segura, conflitante, versão já consumida) e nonce atômico com transação, estado e recuperação pós-falha |
| Alta A4 | `BLOCK-TEMP-01` separado dos testes do contrato implementado; só é removido no commit que prova `CONTRACT-01…` |
| Outros | Cinco positivos `POS-01`…`POS-05` com entrada/pré-condição/resultado; M3 com assinatura Ed25519, `kid`, rotação e lista de revogação; skew medido com `Date` e janelas reavaliadas; OFFLINE × homologação × restauração com evidências distintas |
| Limites | Nenhum código tocado, nenhuma fase B executada, nenhuma chave provisionada, nenhum merge/deploy, 0 GitHub Actions; a retirada do bloqueio depende dos 8 critérios da revisão 2 |

## 30. Revisão 2.1 do contrato Broker–Revisor–Gate — 19/11/2026

| Item | Status |
|---|---|
| Documento e branch | Mesmo caminho, revisão **2.1**, em `docs/broker-revisor-gate-contract-rev21-20261119`, commit `0f052da7b2543e2378a38e133e7612bc65ce415d` |
| Histórico preservado | v1 `9c5b596…` e v2.0 `5b15c71…` intactas; `git ls-remote` confirma os três SHAs |
| Crítica replay | §3.2: broker persiste `max_seq_accepted` por `review_record_url` em `conexo_registry_sequences`, com atualização `CAS`; `seq <= aceito` → `review_record_replay_detected` mesmo com assinatura válida e frescura; `SEC-36` cobre reapresentação após reinício |
| Crítica atomicidade | §6.2: não alega atomicidade distribuída; reserva persistente, estado `IN_FLIGHT` antes do POST, idempotência no endpoint WordPress (nonce em `meta._conexo_editorial_operation_nonce`), reconciliação por E1 |
| Crítica concorrência | Restrição única em `(post_id, version_sha256)` para estados ativos, `INSERT ... ON CONFLICT DO NOTHING`; `SEC-38` |
| Crítica ausência × desconhecido | `SEC-32a` (ausência confirmada → `FAILED`), `SEC-32b` (leitura inconclusiva → `UNKNOWN`/`transport_unknown_inspect`), `SEC-37` (meta ausente/divergente nunca é `FAILED`) |
| Complementar readback | E1 passa a listar `meta._conexo_editorial_operation_nonce` e exige leitura autenticada desse meta na recuperação |
| Complementar M5 | Quatro estados: `published`, `scheduled`, `idempotent`, `transport_unknown_inspect`; `verified` rebaixado a sinal interno, nunca status de publicação; positivos ajustados |
| Limites | Somente documentação; nenhum código, nenhuma fase B/C/D, nenhum merge/deploy/cron, nenhuma escrita em produção; bloqueio `trusted_factual_review_broker_guard_not_integrated` e PR #130 draft mantidos; 0 GitHub Actions |

## 31. Revisão 2.2 do contrato Broker–Revisor–Gate — 19/11/2026

| Item | Status |
|---|---|
| Documento e branch | Mesmo caminho, revisão **2.2**, em `docs/broker-revisor-gate-contract-rev22-20261119`, commit `601faec7663c3eb06c5726b741449e0e266f2684` |
| Histórico preservado | v1 `9c5b596…`, v2.0 `5b15c71…`, v2.1 `0f052da…` intactas; `git ls-remote` confirma os quatro SHAs |
| E3 reposicionado | Antes do POST só E1+E2 autenticados; depois de `publish`, E1/E2 confirmam estado e E3 conferir apresentação pública; para `schedule`, E1/E2 confirmam `future` e `post_date_gmt`, **sem E3**; POS-01 e POS-02 ajustados |
| Idempotência do WordPress | Nova §6.3: reserva em tabela própria **antes** de alterar o post; segunda requisição com mesmo nonce devolve resultado sem nova escrita; `IN_FLIGHT` inconclusivo sem retry; recuperação por idempotência + post autenticado; meta ausente não prova ausência da escrita |
| CAS fechado | §3.2: inicialização da linha com `max_seq_accepted=0` na mesma transação, `SELECT ... FOR UPDATE`, e CAS + reserva da operação na **mesma** transação do broker; `SEC-39` para disputa concorrente com o mesmo `registry_seq` |
| Versão executável | §6.2: `conexo_editorial_version_claims` com `PRIMARY KEY (post_id, version_sha256)` e `UNIQUE (nonce)`; `FAILED` excluído na mesma transação da mudança de estado; `WRITTEN` é versão consumida, sem repetição com outro nonce |
| Limites | Somente documentação; nenhum código, nenhuma fase B autorizada, nenhum merge/deploy/cron, nenhuma escrita em produção; bloqueio e PR #130 draft mantidos; 0 GitHub Actions |

## 32. Revisão 2.3 do contrato Broker–Revisor–Gate — 19/11/2026

| Item | Status |
|---|---|
| Documento e branch | Mesmo caminho, revisão **2.3**, em `docs/broker-revisor-gate-contract-rev23-20261119`, commit `0979579b4d680630c89ca99e5d371db02e3e41e4` |
| Histórico preservado | v1 `9c5b596…`, v2.0 `5b15c71…`, v2.1 `0f052da…`, v2.2 `601faec…` intactos; `git ls-remote` confirma os cinco SHAs |
| `IN_FLIGHT` persistente | Nova §6.3 com **duas** transações no WordPress: T1 insere e **faz COMMIT** da reserva `IN_FLIGHT` antes de tocar em `wp_posts`; T2 faz `SELECT ... FOR UPDATE`, altera post+`wp_postmeta` e marca `WRITTEN` com COMMIT único. Queda entre T1 e T2 preserva `IN_FLIGHT` → `UNKNOWN`, sem retry |
| Engines | `wp_posts`, `wp_postmeta` e a tabela de idempotência no mesmo schema, todos **InnoDB**; qualquer engine não transacional → `IDEMPOTENCY_ENGINE_UNSUPPORTED` (`SEC-40`) |
| Dialeto SQL | Nova §6.4: MySQL 8/MariaDB 10.6+; `INSERT` simples + erro `1062` (SQLSTATE `23000`) com releitura e mapeamento para bloqueio; proibidos `ON CONFLICT DO NOTHING`, `INSERT IGNORE` e `ON DUPLICATE KEY UPDATE`. Corrigido também o CAS de `registry_seq` (§3.2) |
| Testes | `SEC-40` (engine), `SEC-41` (queda entre T1/T2 com `IN_FLIGHT` persistido), `SEC-42` (`1062` na inicialização da sequência); faixa total `SEC-01`…`SEC-42` |
| Limites | Somente documentação; nenhum código, nenhuma fase B executada, nenhum merge/deploy/cron, nenhuma escrita em produção; bloqueio e PR #130 draft mantidos; 0 GitHub Actions |

## 33. Fase B restrita — Ed25519 e fronteira autenticada do registro — 19/11/2026

| Item | Status |
|---|---|
| Autorização | Proprietário autorizou explicitamente iniciar a Fase B **restrita** ao protocolo Ed25519 e à fronteira autenticada do registro, em branch isolada e testes OFFLINE |
| Branch e commits | `fix/ed25519-review-registry-boundary-20261119`, base `fb96e0c`; código `8611b299617d4c20d00c9a02a5ff8d8769aaaa19`; rastreabilidade `a971a59e9e08425e9e68b0fd54c50e183c48f1c0` |
| Código alterado | `editorial_factual_certificate.py` (M1 Ed25519 com `alg`/`kid`, caminho HMAC legado só por compatibilidade), `editorial_trusted_review.py` (despacho M1/M2, sequência injetada), novo `editorial_review_registry.py` (envelope M2 assinado por inteiro, frescura, revogação,CAS e sequência), novo `tests/test_ed25519_review_contract.py` (20 testes) |
| Fora do escopo | Broker, Gate PHP/M3, WordPress, homologação real, allowlist, nonce/idempotência, skew, bloqueio e publicação — **nenhum tocado** |
| Testes focados | Hostinger, clone isolado `~/mkt-rss-ed25519-phaseb-20261119` com venv do preparado: **69 passed, 0 failed**; checkout compartilhado permanece em `e4276c2`, limpo |
| Suíte completa | **1657 passed, 11 skipped, 52 subtests, 0 failed** (1637 anteriores + 20 novos) |
| Rastreabilidade | `docs/SEC_TEST_TRACEABILITY_20261119.md`: 16 requisitos NOVOS, 12 PREEXISTENTES, 1 PARCIAL (SEC-18) e 13 PENDENTES; POS-01…POS-05 pendentes; nenhuma suíte verde foi apresentada como contrato completo |
| Correções pendentes da revisão adversarial | `IN_FLIGHT` não prova ausência; T2 com uma única conexão `$wpdb`; matriz requisito→teste agora materializada |
| Limites | 0 GitHub Actions; nenhuma escrita em produção, merge, deploy, cron ou publicação; PRs #129/#130 draft; bloqueio `trusted_factual_review_broker_guard_not_integrated` ativo |

## 34. Fechamento de SEC-18, limite HMAC e custódia de chaves — 19/11/2026

| Item | Status |
|---|---|
| Autorização | Orientação do proprietário: fechar SEC-18, definir custódia/rotação e verificar o HMAC legado antes de qualquer integração do broker |
| Commit | `de5498cfe1515c33df58620962bf34d978392864` na branch `fix/ed25519-review-registry-boundary-20261119` (fast-forward a partir de `a971a59`) |
| SEC-18 | Teste nominal `test_SEC_18_envelope_without_expiry_is_rejected`: ausência de `expires_at` e TTL > 3600s → `review_record_evidence_missing`; matriz atualizada (17 novos, 12 preexistentes, 13 pendentes) |
| Testes | Hostinger, clone isolado: **70 passed** nos focados e **1658 passed, 11 skipped, 52 subtests, 0 failed** na suíte completa; `git status` limpo; checkout compartilhado segue em `e4276c2` |
| HMAC legado | Verificação: master `101fe18` não contém Ed25519; código novo está só em branch não mesclada. Porém `verify_independent_review` ainda aceita envelope HMAC sem `alg` por compatibilidade de testes — **proibição efetiva por `alg` fica pendente da Fase C**; não foi afirmado bloqueio que não existe |
| Custódia de chaves | Proposta registrada em `docs/SEC_TEST_TRACEABILITY_20261119.md`, **sem inventar mecanismo**: emissor/cofre de `K_ISS`, operador/distribuição da pública de `K_REG`, segredo `K_BROKER`, rotação com `kid` e sobreposição de 24h, revogação de emergência, recuperação e auditoria — todos exigem decisão do proprietário |
| Limites | Nada de broker, WordPress/Gate PHP, M3, homologação, produção, merge ou deploy; 0 GitHub Actions |

## 35. Decisão de governança — identidade emissora de `K_ISS` — 19/11/2026

| Item | Status |
|---|---|
| Decisão do proprietário | Confirmada: a identidade institucional **ConexoTech / Conexo OS** é a emissora dos certificados factuais, com **Reinaldo Mendes** como responsável humano final (`owner_id = 3` do Gate; autor humano definido nas regras do projeto) |
| Ferramentas | ChatGPT/Codex/OpenCode ou qualquer provedor de IA são apenas **operadores técnicos** da assinatura; nenhum é proprietário da identidade nem emissor por direito próprio |
| Separação de papéis | `issuer` da identidade institucional ≠ aprovador humano ≠ `reviewer_id` do Revisor Único; emissão de certificado não é aprovação de publicação |
| Fora da decisão | Local/cofre da chave privada, controle de acesso, auditoria, rotação, revogação e recuperação **não foram decididos nem provisionados**; nenhuma chave foi gerada ou instalada |
| Limites | Somente decisão registrada; nenhum código, broker, WordPress, Gate PHP, produção, merge, deploy, cron ou publicação; 0 GitHub Actions |

## 36. Decisão de governança — identidade de `K_REG` — 19/11/2026

| Item | Status |
|---|---|
| Decisão do proprietário | Confirmada: o registro confiável do Revisor é operado pela identidade institucional **Conexo OS**, como serviço e chave **distintos** de `K_ISS` |
| Distribuição | A chave **pública** de `K_REG` deve ser distribuída aos verificadores (cliente e futuro broker); a privada permanece no serviço de registro |
| Separação | `K_ISS` emite o certificado, `K_REG` assina o envelope do registro; nenhuma das duas identidades se substitui nem vira aprovador |
| Fora da decisão | Cofre, distribuição efetiva, rotação, revogação, recuperação e provisionamento **não foram decididos nem executados**; nenhuma chave foi gerada ou instalada |
| Limites | Somente decisão registrada; nenhum código, broker, WordPress, Gate PHP, produção, merge ou deploy; 0 GitHub Actions |

## 37. Fronteira protegida anti-HMAC — 19/11/2026

| Item | Status |
|---|---|
| Autorização | Proprietário autorizou rejeitar `alg` ausente, HMAC e algoritmo desconhecido nos caminhos protegidos, com testes em branch isolada |
| Commits | `ed616f03260b2dbdcbbfbf642a02b845108f1ad9` (código), `382506a57b417b4e820ad8357bd6e834f9545951` (matriz), na branch `fix/ed25519-review-registry-boundary-20261119` |
| Implementação | Novo `verify_independent_review_contract` exige `alg=Ed25519` em M1 e M2; `authorize_publish(require_contract_v23=True, review_sequence_store=...)` usa esse caminho. Códigos: `certificate_algorithm_missing/_legacy_hmac/_unsupported` e `review_record_algorithm_missing/_legacy_hmac/_unsupported` |
| Compatibilidade | Modo padrão continua aceitando HMAC **somente** para fixtures legadas isoladas; não é o caminho protegido e não é usado por consumo de produção algum |
| Testes | 10 testes em `tests/test_hmac_boundary.py`, incluindo downgrade (certificado Ed25519 + envelope legado) e bloqueio pelo gate no modo protegido. Hostinger, clone isolado: **10 passed**, focados **80 passed**, suíte completa **1668 passed, 11 skipped, 52 subtests, 0 failed** |
| Matriz | `docs/SEC_TEST_TRACEABILITY_20261119.md` atualizada: verificação HMAC agora PASS no caminho protegido; obrigatoriedade nos consumidores de produção segue PENDENTE (Fase C) |
| Custódia | Identidades `K_ISS` e `K_REG` decididas nas seções 35 e 36; cofre, rotação, revogação, recuperação e `K_BROKER` permanecem sem decisão |
| Limites | Nenhum broker, WordPress, Gate PHP, M3, homologação, produção, merge, deploy, cron ou publicação; checkout compartilhado em `e4276c2`; 0 GitHub Actions |

## 38. Ordem de pendências para qualidade e publicação — 22/11/2026

Triagem por relevância até o primeiro artigo publicado. Nenhuma execução de
produção nesta rodada; estados vêm das seções 1–37 e da API do GitHub.

| # | Pendência | Bloqueia | Quem resolve | Próxima ação |
|---|---|---|---|---|
| 1 | Nenhuma versão com aprovação humana + aceite explícito (`owner_id=3`) | Publicação | Proprietário | Escolher a versão-alvo (#9900, #9906 ou pauta nova) e aprovar no Gate |
| 2 | Capa: #9900 e #9906 com `capa 0`; nenhuma imagem com direito verificado | Rascunho completo | Proprietário + `image_protocol.py` | Escolher candidata, registrar licença/atribuição, conferir 1440/390 px |
| 3 | Vídeo curado ausente; sem chave no servidor | Readback marcador + iframe + `VideoObject` | Proprietário (chave) + curadoria | Provar `VideoObject` sobrevivendo ao `rendered` |
| 4 | Broker bloqueado por `trusted_factual_review_broker_guard_not_integrated`; PR #130 draft | Publicação pelo broker | Engenharia (8 critérios da rev2.3 + SEC/POS) | Caminho alternativo já existente: `tools/publish_owner_approved.py` |
| 5 | Gate de valor M04.16D desligado e sem `price_history` autenticado | Qualidade/valor acrescentado | Engenharia + fonte de preço | Coletar preço com origem e data no formato do gate antes de ligar |
| 6 | SEO nativo assinado sem `CONEXO_EDITORIAL_GATE_KEY` | SEO assinado | Proprietário | Provisionar a chave no servidor |
| 7 | `lookup_review` não implementado (consulta sempre injetada) | Uso real do Revisor Único | Engenharia | Implementar consulta ao registro assinado de `K_REG` |
| 8 | 37 rascunhos antigos com imagem licenciada pendente (PR #124 draft) | Qualidade do acervo | Curadoria | Priorizar por tráfego e corrigir em lote |
| 9 | ~24 PRs antigos em Draft sem decisão (lista em `gh pr list`) | Organização | Proprietário | Arquivar ou retomar, um a um |
| 10 | Token Turso `ro` não gerado pela API | Leitura segregada | Proprietário | Recriar token com permissão de leitura |
| 11 | Backup/restore nunca provado; conjunto de 19/11 pode expirar por retenção | Deploy do tema 1.7.0 | Proprietário (Drive) | Baixar os 6 arquivos e conferir SHA-256 |
| 12 | Alterações do registro único estavam não commitadas nesta branch | Rastreabilidade | Agente | **FEITO** — commit desta seção registra as seções 7–38; sem push |

Ordem: 1–4 formam o caminho mínimo até o primeiro artigo publicado; 5–7 são
qualidade de texto e SEO; 8–12 são higiene operacional.

Correção de registro: os PRs #7, #8, #9 e #10 estão **MERGED** (verificado na API
nesta data), e não pendentes como constava em anotação anterior de sessão. O PR
#85 também está **MERGED** (`fix/independent-source-domain-20261110`). PRs #129 e
#130 permanecem **draft** e são o material do Revisor Único/Gate.

## Referência por tema

- SEO/GEO/AEO: `docs/REGRA15_NOTAS.md`, `docs/PENDENCIAS_2026-10-03.md`, `docs/CLOUD_EDITORIAL_20261109.md`
- Credenciais: `docs/CREDENCIAL_MOTOR_20261117.md`
- Mecanismo triagem: `docs/TRIAGE_MECANISMO_CHATGPT_VS_OPENCODE_20261117.md`
- Gargalo WordPress: `docs/GARGALO_RASCUNHO_WORDPRESS_20261117.md`
- Regeneração: `docs/REGENERACAO_MOTOR_20261117.md`
- Auditoria módulos: `docs/AUDITORIA_MODULOS_CREDENCIAIS_20261118.md`
- Pautas: `docs/PAUTAS_TRIAGEM_20261117.md`, `docs/PAUTAS_SELECIONADAS_20261117.md`
- M11 Binance: `docs/M11_FICHA_REVISAO_20261117.md`
- M14 preços: `docs/M14_AUDITORIA_PRECOS_20261117.md`
- M07 fila: `docs/M07_FILA_CORRECAO_20261117.md`
- M19 SEO: `docs/M19_INVENTARIO_SEO_20261117.md`
- Gate política: `docs/EDITORIAL-IMMEDIATE-PUBLICATION-POLICY-20261113.md`
- Vídeo: `docs/site/politica-curadoria-video.md`

<!-- registro-unico:auto:start -->

## Documentos de auditoria reconhecidos (atualizado automaticamente)

- `docs/AUDITORIA_MODULOS_CREDENCIAIS_20261118.md` — Auditoria de mÃ³dulos desligados e credenciais â€” 18/11/2026
- `docs/CREDENCIAL_MOTOR_20261117.md` — Credencial do motor editorial â€” 17/11/2026
- `docs/GARGALO_RASCUNHO_WORDPRESS_20261117.md` — Gargalo entre geraÃ§Ã£o e WordPress â€” diagnÃ³stico e soluÃ§Ã£o â€” 17/11/2026
- `docs/M07_FILA_CORRECAO_20261117.md` — M07 â€” Fila de correÃ§Ã£o de rascunhos â€” 17/11/2026
- `docs/M14_AUDITORIA_PRECOS_20261117.md` — M14 â€” Auditoria de preÃ§os publicados â€” 17/11/2026
- `docs/PAUTAS_SELECIONADAS_20261117.md` — Duas pautas escolhidas â€” briefing e conferÃªncia â€” 17/11/2026
- `docs/PAUTAS_TRIAGEM_20261117.md` — Pautas paradas na fila â€” triagem de 17/11/2026
- `docs/REGENERACAO_MOTOR_20261117.md` — RegeneraÃ§Ã£o dos dois artigos pelo motor â€” 17/11/2026
- `docs/TRIAGE_MECANISMO_CHATGPT_VS_OPENCODE_20261117.md` — Como a triagem era feita e como ficou no OpenCode â€” 17/11/2026

<!-- registro-unico:auto:end -->
