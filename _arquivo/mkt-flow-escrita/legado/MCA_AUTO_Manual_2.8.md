# MCA AUTO — Manual de Instruções

Guia prático de uso. Não repete a arquitetura interna do prompt — foca no que você precisa fazer para operar a ferramenta.

---

## 1. Como instalar

O MCA AUTO é um *system prompt*: um texto que você cola nas instruções da IA que for usar.

- **Claude.ai / ChatGPT com Projetos:** crie um Projeto, cole o conteúdo do arquivo `MCA_AUTO_2.8.md` (ou versão mais recente) inteiro no campo de instruções do projeto. Toda conversa dentro desse projeto já carrega as regras.
- **Uso avulso (sem projeto):** cole o prompt inteiro como a primeira mensagem de uma conversa nova, antes de pedir qualquer peça.
- **Ferramenta de navegação/busca:** se a plataforma tiver essa opção (ex.: "Search" no Claude, "Browse" no ChatGPT), deixe ativada — isso habilita a Resolução de Fonte automática (item 3) **para produtos que não são do Mercado Livre**. Para Mercado Livre, o sistema nunca busca sozinho, mesmo com a ferramenta ativa — os Termos do programa proíbem extração automatizada da própria plataforma (ver item 5).

---

## 2. Como começar um projeto novo

Não precisa saber a estrutura interna. Basta responder, quando o sistema perguntar:

1. **Produto** — nome e o que você já sabe sobre ele.
2. **Canal** — mídia social, página de venda, blog/review (pode ser mais de um).
3. **Palavra-chave principal** — só se for peça de blog.
4. **Programa de afiliado e plataforma de destino** — ex.: Hotmart / Instagram; Amazon Associates / blog próprio.
5. **Objetivo** — clique, venda direta, lista de email, ranqueamento.
6. **Voz de marca**, se já tiver uma definida.

Se você não souber alguma resposta, diga "não sei" — o sistema não vai inventar por você.

---

## 3. Como fornecer informação sobre o produto

Três formas, em ordem de preferência:

1. **Nome + link oficial do produto** — se a ferramenta de navegação estiver ativa, o sistema busca especificação e preço sozinho (e sempre confirma com você antes de considerar aprovado).
2. **Sem link, ou navegação indisponível** — cole o texto do anúncio, uma captura de tela, ou um PDF da ficha técnica.
3. **Você mesmo descrevendo o produto** — funciona, mas cada claim (benefício, número, resultado) só entra no texto se você afirmar diretamente.

**Regra que não muda:** o sistema nunca afirma benefício, número ou resultado que você não confirmou. Se você pedir uma peça sem fornecer dado suficiente, ele vai parar e perguntar em vez de inventar.

Cada dado que você fornece fica registrado com a origem (de onde veio) — se disser "usa o mesmo dado de antes", o sistema localiza o que já foi aprovado em vez de pedir de novo.

A cada 5 peças produzidas na conversa, o sistema faz uma pausa curta e resume o que já foi feito — isso é automático, não precisa pedir.

---

## 4. Preço, cupom e ofertas — cuidado com validade

Sempre que informar preço, desconto ou disponibilidade, diga também a data em que você viu essa informação. Depois de cerca de uma semana, o sistema vai avisar que aquele dado pode estar desatualizado e pedir confirmação antes de usá-lo de novo.

---

## 5. Links de afiliado — o que esperar

O sistema **nunca gera um link de afiliado real** — ele não tem como saber o seu ID de rastreamento. Toda peça sai com um marcador como:

```
[SEU LINK DE AFILIADO AQUI]
```

Você substitui pelo link real antes de publicar. Toda vez que uma peça incluir esse marcador, o sistema vai confirmar com você o programa e o formato antes de considerar a peça pronta — mesmo que você já tenha informado isso antes na conversa.

**Instagram, TikTok, Reels (sem link clicável no corpo):** o texto não traz o marcador dentro do post — traz uma instrução separada para você atualizar o link da bio/comentário.

**Mercado Livre especificamente:** o sistema nunca gera nem sugere um Link Especial — você precisa gerar o seu próprio na plataforma do Mercado Livre e colar; o sistema só insere, nunca modifica, encurta ou cria.

---

## 6. Disclosure (identificação de publicidade) — o que o sistema já resolve, e o que não resolve

O sistema **sempre inclui** aviso de conteúdo comercial por padrão (você pode pedir para remover, mas a decisão é sua e fica explícita).

O que o sistema **não inventa**: a regra específica de cada plataforma. Ele aplica a regra geral mais rigorosa (lei + CONAR) até você confirmar a regra exata daquela plataforma — é sua responsabilidade checar os termos do programa antes de publicar em escala.

**Exceção — Mercado Livre:** os termos já foram confirmados com o texto oficial (não é mais suposição). O que isso muda na prática: mídia paga só pode ser feita em redes sociais com conta própria (nunca Google/Bing/YouTube Ads), é proibido comprar termo de busca com a marca "Mercado Livre", e categorias inteiras não podem ser divulgadas pelo programa (medicamentos, veículos, imóveis, produtos usados). Se seu produto cair numa dessas categorias, o sistema vai recusar a peça.

---

## 7. Pedindo uma peça — exemplos de comando

- "Faz um post pra Instagram sobre [produto], modo automático."
- "Preciso de uma página de venda pra [produto], quero ver as escolhas explicadas" → ativa modo assistido.
- "Escreve um review de blog sobre [produto], palavra-chave principal é [X]."
- "Revisa esse texto, só corta o que não tem função" → aciona correção cirúrgica, preserva o que já funciona.

---

## 8. Modos de funcionamento

| Modo | O que muda |
|---|---|
| **Automático** (padrão) | Produz a peça direto, só para nos pontos obrigatórios (item 9). |
| **Assistido** | Explica cada escolha de persuasão, estrutura e SEO feita. |
| **Manual** | Você escolhe cada etapa (gancho, prova, CTA etc.) uma por uma. |

Troque de modo a qualquer momento só pedindo.

---

## 9. Quando o sistema vai parar e te perguntar algo (isso é esperado, não é erro)

- Falta dado sobre o produto ou sobre a palavra-chave.
- A peça vai incluir link de afiliado (sempre, mesmo repetido).
- Duas fontes que você forneceu têm informação conflitante sobre o mesmo dado.
- A peça cai em categoria sensível (saúde, financeiro) ou a regra de disclosure da plataforma não foi confirmada.

Isso não é o sistema "travando" — é o guardrail funcionando. Responda a pergunta e ele continua.

---

## 10. Continuando em uma nova conversa

O sistema não guarda memória entre conversas diferentes. No fim de cada sessão, peça: **"me dá o bloco de estado"**. Copie o que ele te devolver e cole no início da próxima conversa para retomar de onde parou.

---

## 11. O que a ferramenta não faz (fora do escopo)

- Não gera código de schema markup, não configura Search Console, não mexe em velocidade de site — isso é trabalho técnico de quem publica o site, não de produção de texto.
- Não confirma sozinha se um claim é juridicamente seguro para categoria regulada (saúde, financeiro) — sinaliza risco alto e pede revisão humana.
- Não participa de comunidades ou publica nada por você — sugere a ação, quem executa é você.

---

## 12. O que trava a entrega da peça, e o que é só aviso

O sistema classifica cada problema por gravidade — não trata tudo igual:

| Gravidade | Exemplo | O que acontece |
|---|---|---|
| **Sempre trava** | Disclosure ausente ou escondido | Peça não é entregue como pronta, mesmo que o resto esteja perfeito |
| **Trava** | Claim sem fonte que passou despercebido, categoria regulada, regra de plataforma não confirmada | Peça não é entregue; sinaliza revisão sua |
| **Só avisa** | Claim com fonte fraca, urgência duvidosa, preço fora da validade | Entrega a peça, mas avisa o ponto de atenção |
| **Nota interna** | Bloco sem função clara, oportunidade de SEO não usada | Não trava nada, é só observação |

Antes de publicar, confira o básico:

- [ ] Todo claim vem de fonte que você confirmou?
- [ ] Marcador de link de afiliado foi substituído pelo link real (ou instrução de bio atualizada)?
- [ ] Aviso de publicidade está visível, não escondido?
- [ ] Preço/oferta ainda está dentro da validade?
- [ ] Regra específica da plataforma de destino foi checada por você (fora do Mercado Livre, já coberto)?
