# Pautas paradas na fila — triagem de 17/11/2026

**Somente leitura.** Nenhuma pauta foi selecionada, rejeitada ou alterada.
Ferramenta: `tools/triagem_pautas_readonly.py` (token de leitura do Turso).

## O gargalo real: a esteira não anda

| Medição | Valor |
|---|---|
| Pautas no banco | 24 |
| Pautas em `DESCOBERTA` | **24 (100%)** |
| Pautas em `SELECIONADA`, `EM_PRODUCAO`, `EM_REVISAO` | 0 |
| Notas editoriais registradas | **0** |
| Coleta diária funcionando | sim (2 a 4 por dia, de 06/11 a 17/11) |

Ou seja: a coleta entra, e nada consome. O `daily.yml` roda `--queue-only`,
grava a descoberta e para. Não existe etapa automática que selecione, produza ou
descarte — e a pauta mais antiga já tem 11 dias.

Isso explica por que o site não recebe artigo novo há semanas, mesmo com o motor
inteiro construído: o problema não é redação, é que ninguém decide o que redigir.

## Triagem automática das 24

Regra aplicada (somente título e URL, sem IA):

- **Rumor** (vazamento, "pode ter revelado") → rejeitar
- **Oferta** com mais de 7 dias → rejeitar (o preço da matéria já mudou)
- **Notícia** com mais de 10 dias → rejeitar (perdeu atualidade)
- **Guia** perene → selecionar
- **Fonte estrangeira em inglês** → rejeitar (exigiria tradução e apuração)

| Recomendação | Quantidade |
|---|---|
| Selecionar | 18 |
| Rejeitar | 6 |

### Os 5 com melhor relação esforço/retorno

| Pauta | Tipo | Por quê |
|---|---|---|
| Melhor TV 65 polegadas: 13 modelos | Guia | Perene, alta intenção de compra, não envelhece |
| Anatel manda TIM desligar bloqueio de telemarketing | Notícia BR | Fato nacional, fonte oficial, interesse direto do leitor |
| Claro fornece iPhones ao Senado (R$ 4,96 mi) | Notícia BR | Números concretos, pauta de serviço público |
| Microsoft encerra suporte a documentos antigos do Word | Notícia | Afeta usuário comum, consequência prática clara |
| Onde roda GTA 6: requisitos | Guia | Busca alta, resposta objetiva, sem preço |

### Os 6 recomendados para rejeição

| Pauta | Motivo |
|---|---|
| Vazamento de tela do iPhone comemorativo | Rumor, sem fonte primária |
| Motorola Signature 27 (GSMArena) | Título e fonte em inglês |
| Galaxy Tab S10 Lite (oferta) | Oferta de 8 dias |
| Galaxy Tab S10 FE 41% OFF | Oferta de 8 dias |
| Microsoft Paint com falha grave | 11 dias, já corrigido na prática |
| Hackers em freezers de bancos de sangue | 11 dias |

Nenhuma dessas é julgamento final: é recomendação com critério declarado. O
texto do artigo e o aceite continuam humanos.

## Como aplicar (não executado)

O caminho sancionado é `mkt_flow_p0/triagem_decisoes.decidir`, que exige
`confirmado=True`, grava auditoria imutável na mesma transação e só aceita
pauta em `DESCOBERTA`:

```python
from mkt_flow_p0 import triagem_decisoes
triagem_decisoes.decidir(
    "822ec1e30a47da5b90e13df1857a6d30", "rejeitar",
    "rumor sem fonte primária", operador, confirmado=True)
```

Isso escreve no Turso com o token de escrita — por isso **não foi executado**.
Decidir o que o site publica é ato editorial, não de infraestrutura.

## Achado colateral

Duas listas diferentes contam a mesma coisa com números diferentes:

- a fila de **rascunhos** no WordPress tem 37 itens (`conexo/v1/editorial/remediation/queue`);
- a fila de **pautas** no Turso tem 24 itens, todos parados.

São estágios distintos do mesmo funil. Nenhum dos dois tem consumidor
automático. Fechar um sem o outro não resolve nada.

## Como repetir

```
python tools/triagem_pautas_readonly.py
python tools/triagem_pautas_readonly.py --json pautas.json
```

Precisa de `TURSO_DATABASE_URL` + `TURSO_AUTH_TOKEN` (leitura). No servidor os
arquivos `~/.config/conexo-os/rss-queue.env` e `turso-readonly.token` são
encontrados automaticamente.
