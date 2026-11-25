<!-- Status consolidado: docs/REGISTRO_UNICO_20261118.md -->

# Duas pautas escolhidas â€” briefing e conferÃªncia â€” 17/11/2026

> **AtualizaÃ§Ã£o 25/11/2026:** a pauta **Anatel/TIM** foi **excluÃ­da** pelo
> proprietÃ¡rio por falta de documentaÃ§Ã£o oficial que comprove a matÃ©ria. O post
> #9900 estÃ¡ na lixeira (conteÃºdo preservado, aÃ§Ã£o reversÃ­vel). EvidÃªncia:
> `docs/editorial-evidence/9900/exclusion-20261125.json`.

Escolha do proprietÃ¡rio em 17/11: **Anatel/TIM** e **Claro/Senado**.
Nada foi publicado, nada foi aprovado, nenhuma imagem foi baixada.

## AtualizaÃ§Ã£o 17/11 (fim do dia)

O bloqueio foi resolvido. A tabela `rss_triage_audit` e os trÃªs triggers foram
provisionados no Turso de produÃ§Ã£o, e as **duas pautas foram gravadas como
`SELECIONADA`** com auditoria imutÃ¡vel:

| Pauta | Evento |
|---|---|
| Anatel/TIM | `ba4bc9eeee224279a4b25f785780629b` |
| Claro/Senado | `41454622c4c041d5b231926279314a2c` |

Fila agora: 22 em `DESCOBERTA`, 2 em `SELECIONADA`. Nenhuma alteraÃ§Ã£o em
artigo, WordPress ou publicaÃ§Ã£o. Detalhes do mecanismo:
`docs/TRIAGE_MECANISMO_CHATGPT_VS_OPENCODE_20261117.md`.

Os artigos das duas pautas foram escritos em `artigos-pendentes/2026-11-17/`
(pasta fora do repositÃ³rio pÃºblico, via `.gitignore`), com as pendÃªncias de
fonte primÃ¡ria, imagem e aceite ainda abertas.

---

## Primeiro, o bloqueio (importante)

A decisÃ£o **nÃ£o pÃ´de ser gravada na fila**. Motivo real:

| VerificaÃ§Ã£o | Resultado |
|---|---|
| Tabela `rss_triage_audit` no Turso de produÃ§Ã£o | **nÃ£o existe** |
| Triggers de auditoria | **nenhum** |
| Tentativa de `triagem_decisoes.decidir(..., confirmado=True)` | `SQLITE_AUTH: not authorized` |

O token de escrita da fila nÃ£o tem permissÃ£o de criar tabela, e o caminho
sancionado exige gravar a auditoria na mesma transaÃ§Ã£o. O cÃ³digo **falhou
fechado**, que Ã© o comportamento correto. As 24 pautas continuam em
`DESCOBERTA` â€” nenhuma foi alterada por engano.

Para destravar: rodar `tools/provision_triage_audit.py --confirmar` com um token
do Turso que tenha permissÃ£o de schema. O script sÃ³ executa os quatro
`CREATE ... IF NOT EXISTS` do mÃ³dulo, sem tocar em dados. Depois disso a decisÃ£o
das duas pautas Ã© uma linha.

## Pauta A â€” Anatel manda TIM desligar bloqueio de telemarketing

**Leitor:** quem recebe ligaÃ§Ã£o de telemarketing e nÃ£o entende por que o bloqueio
do celular Ã s vezes falha â€” ou por que parou.

**Necessidade:** saber se a ferramenta antispam da TIM continua valendo, o que
muda na prÃ¡tica e o que fazer enquanto isso.

**Recorte:** a decisÃ£o cautelar da Anatel, o prazo de 24 horas, o motivo
(falta de transparÃªncia), o histÃ³rico de setembro (bloqueio indevido de serviÃ§os
pÃºblicos) e o que o consumidor pode fazer hoje.

**Limite:** nÃ£o afirmar que o serviÃ§o estÃ¡ desligado â€” a ordem tem prazo e a TIM
nÃ£o se manifestou atÃ© a publicaÃ§Ã£o da fonte.

### AfirmaÃ§Ãµes e prova

| # | AfirmaÃ§Ã£o | Trecho literal da fonte | SituaÃ§Ã£o |
|---|---|---|---|
| 1 | Anatel determinou em 13/11, em carÃ¡ter cautelar, que a TIM desligue a ferramenta antispam | "determinou nesta sexta-feira (13/11), de forma cautelar, que a TIM desligue a ferramenta antispam que bloqueia chamadas de telemarketing abusivo" | **confirmado** (Tecnoblog) |
| 2 | Prazo de 24 horas a partir do recebimento do ofÃ­cio | "A agÃªncia deu prazo de 24 horas para o cumprimento da decisÃ£o, a partir do recebimento do ofÃ­cio" | **confirmado** |
| 3 | Motivo: falta de transparÃªncia / informaÃ§Ãµes insuficientes | "nÃ£o forneceu as informaÃ§Ãµes necessÃ¡rias para assegurar as condiÃ§Ãµes mÃ­nimas de funcionamento da ferramenta sem prejuÃ­zo ao consumidor" | **confirmado** (nota da Anatel citada) |
| 4 | Em setembro a Anatel atuou contra bloqueio indevido de serviÃ§os pÃºblicos, inclusive saÃºde | "precisou atuar em setembro para desfazer o 'bloqueio indevido' de serviÃ§os essenciais prestados por Ã³rgÃ£os pÃºblicos, incluindo os de urgÃªncia e emergÃªncia relacionados Ã  saÃºde" | **confirmado** |
| 5 | ServiÃ§o Ã© gratuito, ativo por padrÃ£o, e a TIM nunca anunciou oficialmente | "O serviÃ§o Ã© gratuito para todos os clientes, e estÃ¡ ativo por padrÃ£o" + "A TIM nunca chegou a divulgar oficialmente para a imprensa a ativaÃ§Ã£o da tecnologia" | **confirmado** |

### Lacunas declaradas

- **Falta a fonte primÃ¡ria**: o despacho da Anatel nÃ£o foi localizado. O artigo
  citaria a agÃªncia por meio do Tecnoblog, o que Ã© aceitÃ¡vel mas mais fraco.
- A TIM nÃ£o se manifestou atÃ© 14/11 â€” frase obrigatÃ³ria: "procurada, a TIM nÃ£o
  havia se manifestado atÃ© a publicaÃ§Ã£o desta reportagem".
- **Zero link interno possÃ­vel**: o site nÃ£o tem nenhum conteÃºdo sobre Anatel ou
  telemarketing. NÃ£o preencher cota com link irrelevante (regra do projeto).
  Isso Ã© uma lacuna de cobertura, nÃ£o um defeito do artigo.

## Pauta B â€” Claro vence pregÃ£o de R$ 4,96 milhÃµes no Senado

**Leitor:** quem quer entender se o Senado "comprou iPhones" com dinheiro
pÃºblico â€” a pergunta que viralizou.

**Necessidade:** separar compra de comodato, entender o custo real e o que muda
para o cidadÃ£o.

**Recorte:** o que foi contratado, quanto custa, por que Ã© comodato, a reaÃ§Ã£o
polÃ­tica e o que ainda falta (homologaÃ§Ã£o).

**Limite:** nÃ£o tratar a proposta vencedora como contrato assinado â€” o Senado
ainda precisa homologar.

### AfirmaÃ§Ãµes e prova

| # | AfirmaÃ§Ã£o | Trecho literal da fonte | SituaÃ§Ã£o |
|---|---|---|---|
| 1 | Claro venceu o PregÃ£o 290/2026, com proposta de R$ 4.957.905,60 | "A operadora serÃ¡ responsÃ¡vel pelos iPhones 18 Proâ€¦ a proposta da Claro dÃ¡ conta de R$ 4.957.905,60" | **confirmado** (Tecnoblog) |
| 2 | Estimativa do pregÃ£o era de aproximadamente R$ 6 milhÃµes, para quatro anos | "O valor de aproximadamente R$ 6 milhÃµes corresponde Ã  estimativa da contrataÃ§Ã£oâ€¦ para quatro anos de serviÃ§o. O custo anual seria em torno de R$ 1,5 milhÃ£o" | **confirmado** (AgÃªncia Senado) |
| 3 | Aparelhos sÃ£o comodato (emprÃ©stimo), nÃ£o compra | "hÃ¡ um contrato na modalidade de comodato, ou seja, nÃ£o hÃ¡ compra por parte do Senado" â€” Davi Alcolumbre | **confirmado** (AgÃªncia Senado, 11/11) |
| 4 | Contrato atual (2022) custa R$ 1,1 milhÃ£o | "O contrato em vigor desde 2022 (CT 170/2022) tem o custo de R$ 1,1 milhÃ£o" | **confirmado** (AgÃªncia Senado) |
| 5 | 425 celulares, sendo 95 iPhones 18 Pro e 330 Android | "425 celulares e planos" / "outros 330 servidores receberÃ£o dispositivos Android" | **parcial â€” ver divergÃªncia** |
| 6 | VigÃªncia a partir de 1Âº de janeiro de 2027, se homologado | "O acordo passa a valer em 1Âº de janeiro de 2027, caso aprovado" | **confirmado**, condicionado |

### DivergÃªncia que precisa de decisÃ£o antes de publicar

| Fonte | Quantos senadores |
|---|---|
| AgÃªncia Senado (oficial) | **81 senadores** e alguns servidores com cargos de direÃ§Ã£o |
| Tecnoblog / UOL | **95 iPhones** para senadores |

O Senado tem 81 senadores. Os "95" provavelmente incluem direÃ§Ã£o e presidÃªncia,
mas **nenhuma fonte primÃ¡ria confirma isso**. Publicar "95 iPhones para
senadores" repete um nÃºmero que a fonte oficial nÃ£o sustenta.

SaÃ­das possÃ­veis: (a) escrever "95 aparelhos, entre senadores e servidores com
cargo de direÃ§Ã£o" **se** houver confirmaÃ§Ã£o; (b) usar apenas o que Ã© oficial:
81 senadores + 425 aparelhos no total. A opÃ§Ã£o (b) Ã© segura e nÃ£o enfraquece a
matÃ©ria.

### Link interno possÃ­vel

- `/iphone-18-pro-brasil-precos-disponibilidade/` â€” relaÃ§Ã£o real: o aparelho do
  contrato Ã© o iPhone 18 Pro. Um link, nÃ£o trÃªs.

## O que falta para virar artigo

| Item | SituaÃ§Ã£o |
|---|---|
| Fatos principais | conferidos nas duas pautas |
| Fonte primÃ¡ria da Anatel | **pendente** (nÃ£o localizada) |
| DivergÃªncia 81 Ã— 95 | **exige decisÃ£o** |
| Imagens com direito | **pendente** â€” nenhuma imagem do Tecnoblog pode ser reutilizada |
| Links internos | 1 para a pauta B, 0 para a pauta A |
| Pauta gravada como SELECIONADA | **bloqueada** atÃ© provisionar a auditoria |

Nenhuma das duas foi escrita, e nenhuma passa ao estÃ¡gio de revisÃ£o enquanto os
itens pendentes acima nÃ£o forem resolvidos. Isso Ã© o Gate funcionando.
