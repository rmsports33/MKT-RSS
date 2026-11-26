<!-- Status consolidado: docs/REGISTRO_UNICO_20261118.md -->

# Credencial do motor editorial â€” 17/11/2026

## CorreÃ§Ã£o de uma instruÃ§Ã£o anterior

Eu havia dito para cadastrar o UUID da senha do **motor** em
`Ferramentas â†’ MKT-RSS: correÃ§Ã£o`. Estava **errado**: o plugin `cxrm` permite
Ã  credencial vinculada apenas `GET /remediation/queue` e
`POST /remediation/excerpt`. Vincular a senha do motor a ele **bloquearia o
prÃ³prio motor**. O UUID vinculado deve ser o da credencial de **correÃ§Ã£o**, e
o motor usa uma senha separada, sem vÃ­nculo.

## Estado atual (executado e verificado)

| Credencial | UUID | Papel | Teste |
|---|---|---|---|
| `Conexo MKT-RSS` (`wp-editorial.token`) | `6b060cb4-00e7-4453-878d-037fbf7648e8` | somente correÃ§Ã£o de rascunhos | `users/me` â†’ **403** `cxrm_scope_denied` |
| `MKT-RSS Engine 20261117` (`wp-engine.token`) | `3a7fac3b-ae03-46be-8b92-daf3ca8d7552` | criaÃ§Ã£o de rascunhos pelo motor | `users/me` â†’ **200**, ID 4, role `editor` |

A criaÃ§Ã£o foi feita pela prÃ³pria API REST do WordPress e a senha foi gravada
apenas em `~/.config/conexo-os/wp-engine.token`, com permissÃ£o `600`. O UUID
foi fixado por WP-CLI:

```
wp option update cxrm_editor_app_password_uuid 6b060cb4-00e7-4453-878d-037fbf7648e8
```

Leitura de conferÃªncia: `wp option get cxrm_editor_app_password_uuid` devolve
o mesmo UUID. Nenhuma senha foi exibida no chat.

## ConsequÃªncia

Voltou a existir separaÃ§Ã£o de funÃ§Ãµes:

- agente/ferramenta que tentar usar `wp-editorial.token` **nÃ£o cria rascunho**;
- o motor usa `wp-engine.token` e ainda precisa gerar o manifesto de
  proveniÃªncia para que o Gate aceite o rascunho â€” as duas travas sÃ£o
  complementares.

## Pendente

O plugin com a trava de proveniÃªncia estÃ¡ na branch
`fix/gate-provenance-20261117` do repo do site (commit `6fef067`), **ainda nÃ£o
implantado**. Enquanto isso, os rascunhos 9899/9900 seguem sem manifesto.
