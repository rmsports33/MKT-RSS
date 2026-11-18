# Credencial do motor editorial — 17/11/2026

## Correção de uma instrução anterior

Eu havia dito para cadastrar o UUID da senha do **motor** em
`Ferramentas → MKT-RSS: correção`. Estava **errado**: o plugin `cxrm` permite
à credencial vinculada apenas `GET /remediation/queue` e
`POST /remediation/excerpt`. Vincular a senha do motor a ele **bloquearia o
próprio motor**. O UUID vinculado deve ser o da credencial de **correção**, e
o motor usa uma senha separada, sem vínculo.

## Estado atual (executado e verificado)

| Credencial | UUID | Papel | Teste |
|---|---|---|---|
| `Conexo MKT-RSS` (`wp-editorial.token`) | `6b060cb4-00e7-4453-878d-037fbf7648e8` | somente correção de rascunhos | `users/me` → **403** `cxrm_scope_denied` |
| `MKT-RSS Engine 20261117` (`wp-engine.token`) | `3a7fac3b-ae03-46be-8b92-daf3ca8d7552` | criação de rascunhos pelo motor | `users/me` → **200**, ID 4, role `editor` |

A criação foi feita pela própria API REST do WordPress e a senha foi gravada
apenas em `~/.config/conexo-os/wp-engine.token`, com permissão `600`. O UUID
foi fixado por WP-CLI:

```
wp option update cxrm_editor_app_password_uuid 6b060cb4-00e7-4453-878d-037fbf7648e8
```

Leitura de conferência: `wp option get cxrm_editor_app_password_uuid` devolve
o mesmo UUID. Nenhuma senha foi exibida no chat.

## Consequência

Voltou a existir separação de funções:

- agente/ferramenta que tentar usar `wp-editorial.token` **não cria rascunho**;
- o motor usa `wp-engine.token` e ainda precisa gerar o manifesto de
  proveniência para que o Gate aceite o rascunho — as duas travas são
  complementares.

## Pendente

O plugin com a trava de proveniência está na branch
`fix/gate-provenance-20261117` do repo do site (commit `6fef067`), **ainda não
implantado**. Enquanto isso, os rascunhos 9899/9900 seguem sem manifesto.
