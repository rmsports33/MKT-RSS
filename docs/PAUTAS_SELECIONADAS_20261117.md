# Duas pautas escolhidas — briefing e conferência — 17/11/2026

Escolha do proprietário em 17/11: **Anatel/TIM** e **Claro/Senado**.
Nada foi publicado, nada foi aprovado, nenhuma imagem foi baixada.

## Atualização 17/11 (fim do dia)

O bloqueio foi resolvido. A tabela `rss_triage_audit` e os três triggers foram
provisionados no Turso de produção, e as **duas pautas foram gravadas como
`SELECIONADA`** com auditoria imutável:

| Pauta | Evento |
|---|---|
| Anatel/TIM | `ba4bc9eeee224279a4b25f785780629b` |
| Claro/Senado | `41454622c4c041d5b231926279314a2c` |

Fila agora: 22 em `DESCOBERTA`, 2 em `SELECIONADA`. Nenhuma alteração em
artigo, WordPress ou publicação. Detalhes do mecanismo:
`docs/TRIAGE_MECANISMO_CHATGPT_VS_OPENCODE_20261117.md`.

Os artigos das duas pautas foram escritos em `artigos-pendentes/2026-11-17/`
(pasta fora do repositório público, via `.gitignore`), com as pendências de
fonte primária, imagem e aceite ainda abertas.

---

## Primeiro, o bloqueio (importante)

A decisão **não pôde ser gravada na fila**. Motivo real:

| Verificação | Resultado |
|---|---|
| Tabela `rss_triage_audit` no Turso de produção | **não existe** |
| Triggers de auditoria | **nenhum** |
| Tentativa de `triagem_decisoes.decidir(..., confirmado=True)` | `SQLITE_AUTH: not authorized` |

O token de escrita da fila não tem permissão de criar tabela, e o caminho
sancionado exige gravar a auditoria na mesma transação. O código **falhou
fechado**, que é o comportamento correto. As 24 pautas continuam em
`DESCOBERTA` — nenhuma foi alterada por engano.

Para destravar: rodar `tools/provision_triage_audit.py --confirmar` com um token
do Turso que tenha permissão de schema. O script só executa os quatro
`CREATE ... IF NOT EXISTS` do módulo, sem tocar em dados. Depois disso a decisão
das duas pautas é uma linha.

## Pauta A — Anatel manda TIM desligar bloqueio de telemarketing

**Leitor:** quem recebe ligação de telemarketing e não entende por que o bloqueio
do celular às vezes falha — ou por que parou.

**Necessidade:** saber se a ferramenta antispam da TIM continua valendo, o que
muda na prática e o que fazer enquanto isso.

**Recorte:** a decisão cautelar da Anatel, o prazo de 24 horas, o motivo
(falta de transparência), o histórico de setembro (bloqueio indevido de serviços
públicos) e o que o consumidor pode fazer hoje.

**Limite:** não afirmar que o serviço está desligado — a ordem tem prazo e a TIM
não se manifestou até a publicação da fonte.

### Afirmações e prova

| # | Afirmação | Trecho literal da fonte | Situação |
|---|---|---|---|
| 1 | Anatel determinou em 13/11, em caráter cautelar, que a TIM desligue a ferramenta antispam | "determinou nesta sexta-feira (13/11), de forma cautelar, que a TIM desligue a ferramenta antispam que bloqueia chamadas de telemarketing abusivo" | **confirmado** (Tecnoblog) |
| 2 | Prazo de 24 horas a partir do recebimento do ofício | "A agência deu prazo de 24 horas para o cumprimento da decisão, a partir do recebimento do ofício" | **confirmado** |
| 3 | Motivo: falta de transparência / informações insuficientes | "não forneceu as informações necessárias para assegurar as condições mínimas de funcionamento da ferramenta sem prejuízo ao consumidor" | **confirmado** (nota da Anatel citada) |
| 4 | Em setembro a Anatel atuou contra bloqueio indevido de serviços públicos, inclusive saúde | "precisou atuar em setembro para desfazer o 'bloqueio indevido' de serviços essenciais prestados por órgãos públicos, incluindo os de urgência e emergência relacionados à saúde" | **confirmado** |
| 5 | Serviço é gratuito, ativo por padrão, e a TIM nunca anunciou oficialmente | "O serviço é gratuito para todos os clientes, e está ativo por padrão" + "A TIM nunca chegou a divulgar oficialmente para a imprensa a ativação da tecnologia" | **confirmado** |

### Lacunas declaradas

- **Falta a fonte primária**: o despacho da Anatel não foi localizado. O artigo
  citaria a agência por meio do Tecnoblog, o que é aceitável mas mais fraco.
- A TIM não se manifestou até 14/11 — frase obrigatória: "procurada, a TIM não
  havia se manifestado até a publicação desta reportagem".
- **Zero link interno possível**: o site não tem nenhum conteúdo sobre Anatel ou
  telemarketing. Não preencher cota com link irrelevante (regra do projeto).
  Isso é uma lacuna de cobertura, não um defeito do artigo.

## Pauta B — Claro vence pregão de R$ 4,96 milhões no Senado

**Leitor:** quem quer entender se o Senado "comprou iPhones" com dinheiro
público — a pergunta que viralizou.

**Necessidade:** separar compra de comodato, entender o custo real e o que muda
para o cidadão.

**Recorte:** o que foi contratado, quanto custa, por que é comodato, a reação
política e o que ainda falta (homologação).

**Limite:** não tratar a proposta vencedora como contrato assinado — o Senado
ainda precisa homologar.

### Afirmações e prova

| # | Afirmação | Trecho literal da fonte | Situação |
|---|---|---|---|
| 1 | Claro venceu o Pregão 290/2026, com proposta de R$ 4.957.905,60 | "A operadora será responsável pelos iPhones 18 Pro… a proposta da Claro dá conta de R$ 4.957.905,60" | **confirmado** (Tecnoblog) |
| 2 | Estimativa do pregão era de aproximadamente R$ 6 milhões, para quatro anos | "O valor de aproximadamente R$ 6 milhões corresponde à estimativa da contratação… para quatro anos de serviço. O custo anual seria em torno de R$ 1,5 milhão" | **confirmado** (Agência Senado) |
| 3 | Aparelhos são comodato (empréstimo), não compra | "há um contrato na modalidade de comodato, ou seja, não há compra por parte do Senado" — Davi Alcolumbre | **confirmado** (Agência Senado, 11/11) |
| 4 | Contrato atual (2022) custa R$ 1,1 milhão | "O contrato em vigor desde 2022 (CT 170/2022) tem o custo de R$ 1,1 milhão" | **confirmado** (Agência Senado) |
| 5 | 425 celulares, sendo 95 iPhones 18 Pro e 330 Android | "425 celulares e planos" / "outros 330 servidores receberão dispositivos Android" | **parcial — ver divergência** |
| 6 | Vigência a partir de 1º de janeiro de 2027, se homologado | "O acordo passa a valer em 1º de janeiro de 2027, caso aprovado" | **confirmado**, condicionado |

### Divergência que precisa de decisão antes de publicar

| Fonte | Quantos senadores |
|---|---|
| Agência Senado (oficial) | **81 senadores** e alguns servidores com cargos de direção |
| Tecnoblog / UOL | **95 iPhones** para senadores |

O Senado tem 81 senadores. Os "95" provavelmente incluem direção e presidência,
mas **nenhuma fonte primária confirma isso**. Publicar "95 iPhones para
senadores" repete um número que a fonte oficial não sustenta.

Saídas possíveis: (a) escrever "95 aparelhos, entre senadores e servidores com
cargo de direção" **se** houver confirmação; (b) usar apenas o que é oficial:
81 senadores + 425 aparelhos no total. A opção (b) é segura e não enfraquece a
matéria.

### Link interno possível

- `/iphone-18-pro-brasil-precos-disponibilidade/` — relação real: o aparelho do
  contrato é o iPhone 18 Pro. Um link, não três.

## O que falta para virar artigo

| Item | Situação |
|---|---|
| Fatos principais | conferidos nas duas pautas |
| Fonte primária da Anatel | **pendente** (não localizada) |
| Divergência 81 × 95 | **exige decisão** |
| Imagens com direito | **pendente** — nenhuma imagem do Tecnoblog pode ser reutilizada |
| Links internos | 1 para a pauta B, 0 para a pauta A |
| Pauta gravada como SELECIONADA | **bloqueada** até provisionar a auditoria |

Nenhuma das duas foi escrita, e nenhuma passa ao estágio de revisão enquanto os
itens pendentes acima não forem resolvidos. Isso é o Gate funcionando.
