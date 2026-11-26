<!-- Status consolidado: docs/REGISTRO_UNICO_20261118.md -->

# Gargalo entre geraÃ§Ã£o e WordPress â€” diagnÃ³stico e soluÃ§Ã£o â€” 17/11/2026

## DiagnÃ³stico (tudo verificado, nada presumido)

| Caminho tentado | Resultado real |
|---|---|
| `wp-editorial.token` (Bot.editor ID4) em qualquer rota de escrita | **403** `cxrm_scope_denied` â€” "Credencial MKT-RSS limitada a correcao de rascunhos" |
| Rotas testadas | `/wp/v2/posts`, `/conexo/v1/editorial/write`, `/conexo/v1/editorial/broker/write`, `/conexo/v1/editorial/seo-finalize` |
| Broker do Gate RC2 | sÃ³ aceita `publish`/`schedule`, e exige referÃªncia humana â€” **nÃ£o cria rascunho** |
| HMAC local (`CONEXO_EDITORIAL_GATE_KEY`) | **nÃ£o existe** no servidor |
| Plugin Gate (`conexo-gate-agenda-nativa.php`) | `get_posts(post_status=draft/pending)` â€” **sÃ³ lÃª rascunhos que jÃ¡ existem**; preview via `get_preview_post_link()` |
| Navegador do OpenCode | sem sessÃ£o autenticada no WordPress (vai para `wp-login.php`) |
| GitHub Actions | secretos `WP_USER`/`WP_APP_PASSWORD` existem, mas nÃ£o hÃ¡ fluxo de criaÃ§Ã£o de rascunho; criar um exigiria push na master, fora do escopo |

ConclusÃ£o: **nÃ£o falta cÃ³digo, falta uma credencial com permissÃ£o de criar rascunho.**
Nenhuma soluÃ§Ã£o alternativa contorna isso sem expor senha ou fabricar aprovaÃ§Ã£o.

## SoluÃ§Ã£o inteligente e simples

Uma credencial nova, **somente para criar rascunhos**, criada uma vez pelo
proprietÃ¡rio no WordPress e guardada em arquivo privado no servidor. Depois disso
o caminho Ã© inteiramente automÃ¡tico atÃ© a tela do Gate.

Por que essa Ã© a melhor opÃ§Ã£o:

- nÃ£o mexe em master, nÃ£o cria workflow, nÃ£o usa Actions;
- nÃ£o pede senha de administrador â€” a conta pode ser a prÃ³pria ID4 com uma
  Application Password **sem escopo de correÃ§Ã£o**, ou outro editor;
- o plugin `wp_draft_staging.py` jÃ¡ faz idempotÃªncia por slug, readback e
  `POST` Ãºnico (nÃ£o repete escrita em caso de incerteza);
- o ponto que **continua humano** Ã© exatamente o que deve continuar: conferir o
  layout no Gate e aprovar a versÃ£o.

### Etapa Ãºnica do proprietÃ¡rio (2 minutos)

1. WordPress â†’ **Seu perfil** â†’ **Application Passwords**.
2. Nome: `MKT-RSS Draft Writer` â†’ **Add New Application Password**.
3. Copiar a senha gerada para o arquivo privado no servidor:

> **COMANDO PARA VOCÃŠ EXECUTAR** (senha vai no arquivo, nunca no chat):

```
nano ~/.config/conexo-os/wp-draft-writer.env
```

ConteÃºdo:

```
WP_URL=https://conexotech.com.br
WP_USER=<login do editor>
WP_APP_PASSWORD=<senha de aplicativo gerada>
```

Se a conta for a Bot.editor, Ã© necessÃ¡rio que o administrador remova a
restriÃ§Ã£o `cxrm` dessa nova senha â€” caso contrÃ¡rio o WordPress continuarÃ¡
respondendo 403. Por isso uma conta de editor separada Ã© mais simples.

## Depois disso (automÃ¡tico)

```
python tools/stage_artigo_draft.py \
  --html artigos-pendentes/2026-11-17/preview/senado-claro-comodato.fragment.html \
  --titulo "Senado nÃ£o comprou iPhones: entenda o contrato de R$ 4,96 milhÃµes com a Claro" \
  --fonte https://tecnoblog.net/noticias/quase-r-5-milhoes-claro-vai-fornecer-iphones-e-mais-celulares-para-senado \
  --confirmar
```

O tool grava **rascunho**, faz readback e devolve:

- link de ediÃ§Ã£o;
- link de prÃ©via;
- link do Gate `conexo-gate-revisar-lote`.

Se a credencial estiver errada, o WordPress recusa e nada Ã© criado â€” fail closed.

## PrÃ©via disponÃ­vel agora, sem credencial

Os corpos HTML dos dois artigos foram gerados em
`artigos-pendentes/2026-11-17/preview/`, com o CSS do tema ConexoTech. Eles
podem ser abertos no painel de revisÃ£o do OpenCode para conferir tÃ­tulos,
tabelas,blockquote e quebras â€” antes mesmo de existir rascunho no WordPress.

## ResoluÃ§Ã£o em 17/11 (executado)

O proprietÃ¡rio revogou a restriÃ§Ã£o em
`wp-admin/tools.php?page=cxrm-credential` ("Revogar correÃ§Ã£o"). NÃ£o foi preciso
colar senha nova: a senha de aplicativo jÃ¡ existente passou a ter permissÃ£o
normal de editor. PrÃ©-voo autenticado: `users/me` â†’ ID 4, role `editor`, HTTP
200; `wp/v2/posts` â†’ HTTP 200.

O arquivo `~/.config/conexo-os/wp-draft-writer.env` foi criado no servidor a
partir do token jÃ¡ presente, com permissÃ£o `600` e sem exibir a senha.

Rascunhos criados e confirmados por readback autenticado:

| Post | TÃ­tulo | Corpo |
|---|---|---|
| **9899** | Senado nÃ£o comprou iPhones: entenda o contrato de R$ 4,96 milhÃµes com a Claro | 6.314 chars |
| **9900** | Anatel manda TIM desligar bloqueio de telemarketing; entenda o que muda | 5.346 chars |

Um rascunho duplicado (9898, tÃ­tulo com barra invertida por escape de shell)
foi movido para lixeira. Estado final: apenas 9899 e 9900 como rascunhos.

- Gate: https://conexotech.com.br/wp-admin/tools.php?page=conexo-gate-revisar-lote
- EdiÃ§Ã£o: `/wp-admin/post.php?post=9899&action=edit` e `...post=9900&action=edit`
- PrÃ©via: `/?p=9899&preview=true` e `/?p=9900&preview=true`

Nenhum dos dois foi publicado, agendado ou aprovado. O Gate ainda deve apontar
capa e links internos como pendÃªncias â€” isso Ã© revisÃ£o, nÃ£o bloqueio de preview.

## O que continua fora da automaÃ§Ã£o (de propÃ³sito)

- aprovaÃ§Ã£o no Gate por pessoa (hash da versÃ£o, revisor diferente do autor);
- direitos de imagem de capa;
- publicaÃ§Ã£o propriamente dita â€” ocorre na confirmaÃ§Ã£o humana do Gate, via
  writer assinado, imediatamente (sem agendamento).
