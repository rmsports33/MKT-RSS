# APÊNDICE CONEXOTECH — camada de adaptação sobre o MCA_AUTO 2.9
Versão 1.0 • Projeto: conexotech.com.br

> Este arquivo NÃO substitui o MCA_AUTO 2.9 — ele o especializa.
> Ordem de leitura da IA: MCA_AUTO 2.9 primeiro, este apêndice depois.
> Em conflito, este apêndice prevalece (é a regra local do projeto).

## 1. Padrões fixos (não perguntar de novo)

- **Site/voz:** ConexoTech — editorial tech direto e opinativo, pt-BR. Veredito em 1 frase com opinião real (inclusive indicar o rival mais barato quando for a compra racional).
- **Canal padrão:** blog/review no WordPress (tema próprio).
- **Objetivo padrão:** ranquear + converter (clique em afiliado).
- **Programas:** Amazon, Shopee, Mercado Livre e outros (contas já criadas pelo dono).
- **Disclosure:** AUTOMÁTICO pelo tema (aviso no review + rodapé + `rel="sponsored nofollow"`). A IA nunca remove; nunca precisa redigir.
- **Schema/velocidade/Search Console:** infraestrutura do tema + Rank Math. Fora do texto.

## 2. Entrada mínima por artigo (FICHA_DE_PAUTA.md)

Nunca começar sem: produto, palavra-chave principal, categoria (slug),
ficha oficial (ou link oficial — a IA pesquisa), números medidos do lab
(se review testado), preços + DATA da captura, contras reais
(obrigatório — se não houver, PERGUNTAR, nunca inventar nem omitir o bloco).

## 3. Regras de fonte (complemento ao MCA §3/§5)

- Link oficial ou nome do produto → a IA pesquisa specs/preço e classifica como confiança B, confirmando com o usuário antes de aprovar.
- **EXCEÇÃO MERCADO LIVRE (regra dura):** nunca buscar/extrair páginas do Mercado Livre por ferramenta automatizada (proibido pelos Termos do programa). ML só entra com texto colado pelo usuário.
- Preço/cupom/estoque = dado volátil: sempre com data; revalidar se a peça for publicada >7 dias depois (rotina do site: conferir preços 2x/semana).
- Níveis de claim no contexto ConexoTech:
  - **A** — spec oficial + medição do lab concordam;
  - **B** — fabricante OU medição própria;
  - **C** — reviews de terceiros (com atribuição);
  - **D** — opinião/estimativa (marcada como tal no texto);
  - **E** — bloqueado.

## 4. Pacote de saída (OUTPUT PACK) — formato obrigatório

Todo artigo de review sai nestes campos exatos (nomes = chaves da API do tema):

| Campo | Formato |
|---|---|
| `titulo` | H1 único, com palavra-chave + gancho de opinião |
| `conteudo` | HTML com H2s (preferir perguntas); resposta direta de ~40–50 palavras logo abaixo de cada H2 principal; listas/tabelas para comparativos |
| `resumo` | 1–2 frases (excerpt + lede) |
| `nota` | `9,2` (0–10, vírgula decimal) |
| `amostra` / `tempo` | ex. `S26U-041` / `12 min` |
| `veredito` | 1 frase opinativa, coerente com a nota |
| `pros` / `contras` | um item por linha; contras sempre reais e fornecidos |
| `specs` | uma por linha: `RÓTULO | Valor` |
| `benchs` | uma por linha: `Rótulo | Detalhe | 0–100` |
| `lojas` | até 3 × (nome + preço + data). URL = `[LINK AFILIADO: nome-da-loja]` — NUNCA URL real/inventada; o dono cola o Link Especial no painel |
| `categoria` | slug de `tipo_produto` (ex. `smartphones`) |
| `seo` | sugestão de meta title (≤60) + meta description (≤160) + palavra-chave foco (dono cola no Rank Math) |
| entidade | nome de marca/modelo/categoria IDÊNTICO em todo o artigo |

## 5. Auditoria reduzida pré-entrega (deriva do MCA §11)

1. Cada número tem fonte na ficha? 2. Contras presentes e reais?
3. Nota coerente com o veredito? 4. Preços dentro da validade?
5. Links são placeholders (nenhuma URL inventada)?
6. H2s com resposta direta + sem keyword stuffing?
7. Drift semântico: nenhum limite virou absoluto, nenhum dado neutro ganhou adjetivo?
Falha em 1–5 = bloqueia. 6–7 = corrige e entrega.

## 6. Operação

- Modo padrão: AUTOMÁTICO. Publicar via API sempre como **rascunho** primeiro; humano confere e publica.
- Interromper e perguntar quando: faltar dado, categoria sensível, divergência entre fontes, qualquer link afiliado (confirmar placeholder), preço fora da validade.
- Ledger de claims por produto em `pautas/<produto>.md` (ver `_MODELO.md`): registra claim + origem + confiança + data. Reutilizar sem reconfirmar.
