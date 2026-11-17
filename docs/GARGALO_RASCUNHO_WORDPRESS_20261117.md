# Gargalo entre geração e WordPress — diagnóstico e solução — 17/11/2026

## Diagnóstico (tudo verificado, nada presumido)

| Caminho tentado | Resultado real |
|---|---|
| `wp-editorial.token` (Bot.editor ID4) em qualquer rota de escrita | **403** `cxrm_scope_denied` — "Credencial MKT-RSS limitada a correcao de rascunhos" |
| Rotas testadas | `/wp/v2/posts`, `/conexo/v1/editorial/write`, `/conexo/v1/editorial/broker/write`, `/conexo/v1/editorial/seo-finalize` |
| Broker do Gate RC2 | só aceita `publish`/`schedule`, e exige referência humana — **não cria rascunho** |
| HMAC local (`CONEXO_EDITORIAL_GATE_KEY`) | **não existe** no servidor |
| Plugin Gate (`conexo-gate-agenda-nativa.php`) | `get_posts(post_status=draft/pending)` — **só lê rascunhos que já existem**; preview via `get_preview_post_link()` |
| Navegador do OpenCode | sem sessão autenticada no WordPress (vai para `wp-login.php`) |
| GitHub Actions | secretos `WP_USER`/`WP_APP_PASSWORD` existem, mas não há fluxo de criação de rascunho; criar um exigiria push na master, fora do escopo |

Conclusão: **não falta código, falta uma credencial com permissão de criar rascunho.**
Nenhuma solução alternativa contorna isso sem expor senha ou fabricar aprovação.

## Solução inteligente e simples

Uma credencial nova, **somente para criar rascunhos**, criada uma vez pelo
proprietário no WordPress e guardada em arquivo privado no servidor. Depois disso
o caminho é inteiramente automático até a tela do Gate.

Por que essa é a melhor opção:

- não mexe em master, não cria workflow, não usa Actions;
- não pede senha de administrador — a conta pode ser a própria ID4 com uma
  Application Password **sem escopo de correção**, ou outro editor;
- o plugin `wp_draft_staging.py` já faz idempotência por slug, readback e
  `POST` único (não repete escrita em caso de incerteza);
- o ponto que **continua humano** é exatamente o que deve continuar: conferir o
  layout no Gate e aprovar a versão.

### Etapa única do proprietário (2 minutos)

1. WordPress → **Seu perfil** → **Application Passwords**.
2. Nome: `MKT-RSS Draft Writer` → **Add New Application Password**.
3. Copiar a senha gerada para o arquivo privado no servidor:

> **COMANDO PARA VOCÊ EXECUTAR** (senha vai no arquivo, nunca no chat):

```
nano ~/.config/conexo-os/wp-draft-writer.env
```

Conteúdo:

```
WP_URL=https://conexotech.com.br
WP_USER=<login do editor>
WP_APP_PASSWORD=<senha de aplicativo gerada>
```

Se a conta for a Bot.editor, é necessário que o administrador remova a
restrição `cxrm` dessa nova senha — caso contrário o WordPress continuará
respondendo 403. Por isso uma conta de editor separada é mais simples.

## Depois disso (automático)

```
python tools/stage_artigo_draft.py \
  --html artigos-pendentes/2026-11-17/preview/senado-claro-comodato.fragment.html \
  --titulo "Senado não comprou iPhones: entenda o contrato de R$ 4,96 milhões com a Claro" \
  --fonte https://tecnoblog.net/noticias/quase-r-5-milhoes-claro-vai-fornecer-iphones-e-mais-celulares-para-senado \
  --confirmar
```

O tool grava **rascunho**, faz readback e devolve:

- link de edição;
- link de prévia;
- link do Gate `conexo-gate-revisar-lote`.

Se a credencial estiver errada, o WordPress recusa e nada é criado — fail closed.

## Prévia disponível agora, sem credencial

Os corpos HTML dos dois artigos foram gerados em
`artigos-pendentes/2026-11-17/preview/`, com o CSS do tema ConexoTech. Eles
podem ser abertos no painel de revisão do OpenCode para conferir títulos,
tabelas,blockquote e quebras — antes mesmo de existir rascunho no WordPress.

## Resolução em 17/11 (executado)

O proprietário revogou a restrição em
`wp-admin/tools.php?page=cxrm-credential` ("Revogar correção"). Não foi preciso
colar senha nova: a senha de aplicativo já existente passou a ter permissão
normal de editor. Pré-voo autenticado: `users/me` → ID 4, role `editor`, HTTP
200; `wp/v2/posts` → HTTP 200.

O arquivo `~/.config/conexo-os/wp-draft-writer.env` foi criado no servidor a
partir do token já presente, com permissão `600` e sem exibir a senha.

Rascunhos criados e confirmados por readback autenticado:

| Post | Título | Corpo |
|---|---|---|
| **9899** | Senado não comprou iPhones: entenda o contrato de R$ 4,96 milhões com a Claro | 6.314 chars |
| **9900** | Anatel manda TIM desligar bloqueio de telemarketing; entenda o que muda | 5.346 chars |

Um rascunho duplicado (9898, título com barra invertida por escape de shell)
foi movido para lixeira. Estado final: apenas 9899 e 9900 como rascunhos.

- Gate: https://conexotech.com.br/wp-admin/tools.php?page=conexo-gate-revisar-lote
- Edição: `/wp-admin/post.php?post=9899&action=edit` e `...post=9900&action=edit`
- Prévia: `/?p=9899&preview=true` e `/?p=9900&preview=true`

Nenhum dos dois foi publicado, agendado ou aprovado. O Gate ainda deve apontar
capa e links internos como pendências — isso é revisão, não bloqueio de preview.

## O que continua fora da automação (de propósito)

- aprovação no Gate por pessoa (hash da versão, revisor diferente do autor);
- direitos de imagem de capa;
- publicação propriamente dita — ocorre na confirmação humana do Gate, via
  writer assinado, imediatamente (sem agendamento).
