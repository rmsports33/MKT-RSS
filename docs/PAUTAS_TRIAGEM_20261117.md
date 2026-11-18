<!-- Status consolidado: docs/REGISTRO_UNICO_20261118.md -->

# Pautas paradas na fila â€” triagem de 17/11/2026

**Somente leitura.** Nenhuma pauta foi selecionada, rejeitada ou alterada.
Ferramenta: `tools/triagem_pautas_readonly.py` (token de leitura do Turso).

## O gargalo real: a esteira nÃ£o anda

| MediÃ§Ã£o | Valor |
|---|---|
| Pautas no banco | 24 |
| Pautas em `DESCOBERTA` | **24 (100%)** |
| Pautas em `SELECIONADA`, `EM_PRODUCAO`, `EM_REVISAO` | 0 |
| Notas editoriais registradas | **0** |
| Coleta diÃ¡ria funcionando | sim (2 a 4 por dia, de 06/11 a 17/11) |

Ou seja: a coleta entra, e nada consome. O `daily.yml` roda `--queue-only`,
grava a descoberta e para. NÃ£o existe etapa automÃ¡tica que selecione, produza ou
descarte â€” e a pauta mais antiga jÃ¡ tem 11 dias.

Isso explica por que o site nÃ£o recebe artigo novo hÃ¡ semanas, mesmo com o motor
inteiro construÃ­do: o problema nÃ£o Ã© redaÃ§Ã£o, Ã© que ninguÃ©m decide o que redigir.

## Triagem automÃ¡tica das 24

Regra aplicada (somente tÃ­tulo e URL, sem IA):

- **Rumor** (vazamento, "pode ter revelado") â†’ rejeitar
- **Oferta** com mais de 7 dias â†’ rejeitar (o preÃ§o da matÃ©ria jÃ¡ mudou)
- **NotÃ­cia** com mais de 10 dias â†’ rejeitar (perdeu atualidade)
- **Guia** perene â†’ selecionar
- **Fonte estrangeira em inglÃªs** â†’ rejeitar (exigiria traduÃ§Ã£o e apuraÃ§Ã£o)

| RecomendaÃ§Ã£o | Quantidade |
|---|---|
| Selecionar | 18 |
| Rejeitar | 6 |

### Os 5 com melhor relaÃ§Ã£o esforÃ§o/retorno

| Pauta | Tipo | Por quÃª |
|---|---|---|
| Melhor TV 65 polegadas: 13 modelos | Guia | Perene, alta intenÃ§Ã£o de compra, nÃ£o envelhece |
| Anatel manda TIM desligar bloqueio de telemarketing | NotÃ­cia BR | Fato nacional, fonte oficial, interesse direto do leitor |
| Claro fornece iPhones ao Senado (R$ 4,96 mi) | NotÃ­cia BR | NÃºmeros concretos, pauta de serviÃ§o pÃºblico |
| Microsoft encerra suporte a documentos antigos do Word | NotÃ­cia | Afeta usuÃ¡rio comum, consequÃªncia prÃ¡tica clara |
| Onde roda GTA 6: requisitos | Guia | Busca alta, resposta objetiva, sem preÃ§o |

### Os 6 recomendados para rejeiÃ§Ã£o

| Pauta | Motivo |
|---|---|
| Vazamento de tela do iPhone comemorativo | Rumor, sem fonte primÃ¡ria |
| Motorola Signature 27 (GSMArena) | TÃ­tulo e fonte em inglÃªs |
| Galaxy Tab S10 Lite (oferta) | Oferta de 8 dias |
| Galaxy Tab S10 FE 41% OFF | Oferta de 8 dias |
| Microsoft Paint com falha grave | 11 dias, jÃ¡ corrigido na prÃ¡tica |
| Hackers em freezers de bancos de sangue | 11 dias |

Nenhuma dessas Ã© julgamento final: Ã© recomendaÃ§Ã£o com critÃ©rio declarado. O
texto do artigo e o aceite continuam humanos.

## Como aplicar (nÃ£o executado)

O caminho sancionado Ã© `mkt_flow_p0/triagem_decisoes.decidir`, que exige
`confirmado=True`, grava auditoria imutÃ¡vel na mesma transaÃ§Ã£o e sÃ³ aceita
pauta em `DESCOBERTA`:

```python
from mkt_flow_p0 import triagem_decisoes
triagem_decisoes.decidir(
    "822ec1e30a47da5b90e13df1857a6d30", "rejeitar",
    "rumor sem fonte primÃ¡ria", operador, confirmado=True)
```

Isso escreve no Turso com o token de escrita â€” por isso **nÃ£o foi executado**.
Decidir o que o site publica Ã© ato editorial, nÃ£o de infraestrutura.

## Achado colateral

Duas listas diferentes contam a mesma coisa com nÃºmeros diferentes:

- a fila de **rascunhos** no WordPress tem 37 itens (`conexo/v1/editorial/remediation/queue`);
- a fila de **pautas** no Turso tem 24 itens, todos parados.

SÃ£o estÃ¡gios distintos do mesmo funil. Nenhum dos dois tem consumidor
automÃ¡tico. Fechar um sem o outro nÃ£o resolve nada.

## Como repetir

```
python tools/triagem_pautas_readonly.py
python tools/triagem_pautas_readonly.py --json pautas.json
```

Precisa de `TURSO_DATABASE_URL` + `TURSO_AUTH_TOKEN` (leitura). No servidor os
arquivos `~/.config/conexo-os/rss-queue.env` e `turso-readonly.token` sÃ£o
encontrados automaticamente.
