# Relatório de Implementação — SEO, GEO, Ferramentas e Extensões

Data: 08/09/2026 (revisado 22/09/2026) — Status: suíte verde (total atual: `python -m pytest tests/ -q`)

## O que já foi implementado no código (nada a fazer)

### 1. Google Analytics 4 nas landings
- Arquivo: `mkt_flow_p0/landing.py`
- Quando `GA_MEASUREMENT_ID` está no `.env`, cada landing gerada recebe o script gtag no `<head>` e cada clique no botão de afiliado gera o evento `affiliate_click`.
- **Para ativar:** ver Tutorial 1 abaixo (precisa do seu ID de medição).

### 2. Pesquisa de palavras-chave 100% gratuita (substitui o Keywords Everywhere)
- Arquivo: `mkt_flow_p0/keyword_research.py`
- Usa o **Autocomplete público do Google** (suggestqueries.google.com) — sem API key, sem créditos, sem custo.
- Gera frases reais de busca para reviews: "melhor X", "X vale a pena", "X vs Y", "X preço".
- Classifica por intenção: comparação, compra, avaliação, preço.
- **Teste manual (com internet):**
  ```
  python -m mkt_flow_p0.keyword_research "monitor gamer"
  ```

### 3. GEO/AEO — llms.txt (otimização para IAs generativas)
- Arquivo: `mkt_flow_p0/seo.py` → `gerar_llms_txt()`
- Gera o arquivo `llms.txt` (padrão aberto) que ajuda ChatGPT, Perplexity e Claude a citar seu site como fonte.
- O pipeline gera `./llms.txt` automaticamente a cada execução.

### 4. FAQ Schema (rich result do Google + respostas para IAs)
- Arquivo: `mkt_flow_p0/seo.py` → `gerar_faq_schema()` e `gerar_faq_review()`
- Gera perguntas/respostas prontas de review ("X vale a pena?", "Onde comprar X?") em JSON-LD.
- O pipeline salva `./faq_<id>.json` para você colar no post (Rank Math).

### 5. Integração no pipeline
- Arquivo: `pipeline_p0.py`
- A cada execução agora imprime: keywords sugeridas, gera FAQ Schema e `llms.txt`.

---

## O que DEPENDE DE VOCÊ (tutoriais abaixo)

| Tutorial | O que faz | Tempo |
|---|---|---|
| 1 | Ativar Google Analytics 4 (pegar ID e colocar no .env) | 5 min |
| 2 | Instalar plugins no WordPress (Rank Math, Site Kit, AffiliateX) | 15 min |
| 3 | Conectar Google Search Console | 10 min |
| 4 | Instalar extensões do Chrome (Melify, SiteStripe, Block Yourself) | 5 min |
| 5 | Subir llms.txt + FAQ no site | 5 min |

---

## Tutorial 1 — Ativar Google Analytics 4 (5 min)

**Objetivo:** pegar o "ID de medição" (formato `G-XXXXXXX`) e ativar no projeto.

**Passo 1 — Criar conta no Analytics (só a 1ª vez):**
1. Abra `https://analytics.google.com` e entre com `reinaldocr210@gmail.com`
2. Se aparecer "Criar conta", clique em `Administrador` (engrenagem, canto inferior esquerdo) → `Criar` → `Conta`
3. Nome da conta: `ConexoTech` → `Avançar`
4. Preencha: nome da propriedade `conexotech.com.br`, fuso `(GMT-3) Brasil`, moeda `Real Brasileiro (BRL)` → `Avançar`
5. Preencha o que pedir sobre a empresa → `Criar` → aceite os termos

**Passo 2 — Criar fluxo de dados:**
1. No `Administrador`, em `Propriedade`, clique `Fluxos de dados`
2. Clique `Adicionar fluxo de dados` → escolha `Web`
3. URL do site: `https://conexotech.com.br` → Nome: `conexotech.com.br`
4. Clique `Criar fluxo`
5. Copie o **ID de medição** que aparecer (ex: `G-4X7K9M2Q1P`)

**Passo 3 — Colocar no projeto:**
1. Abra o arquivo `.env` (na pasta `C:\Users\LIVE2PC\Desktop\MY PROJECTS FLOW`)
2. Adicione a linha (troque pelo seu ID real):
   ```
   GA_MEASUREMENT_ID=G-XXXXXXXXXX
   ```
3. Salve. Pronto — as próximas landings geradas já terão o Analytics.

> **Importante:** se você ainda não instalou o Google Analytics no WordPress, o **Google Site Kit** (Tutorial 2) faz isso sozinho pelo seu site. Aqui no `.env` é para as landings estáticas do pipeline.

---

## Tutorial 2 — Instalar plugins no WordPress (15 min)

**Objetivo:** instalar Rank Math (SEO), Google Site Kit (Analytics/Search Console) e AffiliateX (tabelas comparativas).

**Passo 1 — Entrar no painel:**
1. Abra `https://conexotech.com.br/wp-admin` → login
2. No menu preto à esquerda, `Plugins` → `Adicionar novo`

**Passo 2 — Instalar Rank Math:**
1. Na busca, digite `Rank Math` → pressione Enter
2. Encontre `Rank Math SEO` (por Rank Math) → clique `Instalar agora`
3. Depois `Ativar`
4. Siga o assistente (pode pular/avançar; nas perguntas finais deixe o padrão)

**Passo 3 — Instalar Google Site Kit:**
1. Volte em `Plugins → Adicionar novo`
2. Busque `Site Kit by Google`
3. `Instalar agora` → `Ativar`
4. Clique `Começar` e conecte com `reinaldocr210@gmail.com`
5. Aceite as permissões do Google
6. No assistente, ative o **Google Analytics** e o **Search Console** quando pedir

**Passo 3 — Instalar AffiliateX:**
1. `Plugins → Adicionar novo`
2. Busque `AffiliateX` (por WPCenter)
3. `Instalar agora` → `Ativar`
4. (Opcional) Ativar o módulo gratuito de analytics de cliques e verificador de links quebrados

---

## Tutorial 3 — Conectar Google Search Console (10 min)

**Objetivo:** o Google mostrar quais palavras-chave seu site rankeia (dados reais — o mais valioso).

**Caminho mais fácil (via Site Kit):** se você ativou o Search Console no Site Kit (Tutorial 2), pule este tutorial — já está conectado.

**Caminho manual (se o Site Kit não conectou):**
1. Abra `https://search.google.com/search-console` com `reinaldocr210@gmail.com`
2. Clique `Adicionar propriedade`
3. Escolha a aba `Prefixo de URL`
4. Digite `https://conexotech.com.br` → `Continuar`
5. Verificação: escolha `Tag HTML` → copie o código `<meta name="google-site-verification" ...>`
6. No WordPress: `Aparência → Personalizar → Cabeçalho` (ou plugin Insert Headers and Footers) → cole a tag → Salvar
7. Volte ao Search Console → `Verificar`

---

## Tutorial 4 — Instalar extensões do Chrome (5 min)

**Objetivo:** agilizar captura de produtos e não sujar o Analytics.

1. Abra o Chrome → `chrome.google.com/webstore`
2. Pesquise e instale:
   - **Melify para afiliados do Mercado Livre** (mostra comissão real nos produtos do ML)
   - **SiteStripe** (a Amazon mostra a barra oficial sozinha quando você entra no site — basta estar logado no Associates)
3. Pesquise e instale **Block Yourself from Analytics** → clique no ícone → `Opções` → adicione `*conexotech.com.br` → `Salvar`

---

## Tutorial 5 — Subir llms.txt e FAQ no site (5 min)

**Objetivo:** colocar os arquivos gerados pelo pipeline no ar.

**llms.txt:**
1. Rode o pipeline (ou use o `llms.txt` já gerado na pasta do projeto)
2. No Hostinger: painel → `Gerenciador de Arquivos` → `public_html`
3. Clique `Upload` → selecione `llms.txt`
4. Confira: `https://conexotech.com.br/llms.txt`

**FAQ Schema (a cada post de review):**
1. Rode o pipeline → ele gera `faq_<id>.json`
2. No WordPress, edite o post → role até o final
3. Se usar Rank Math: aba `Schema` (ícone) → `Adicionar novo Schema` → `FAQ` → cole as perguntas/respostas
4. Ou cole o JSON-LD no bloco `HTML Personalizado` dentro do post

---

## Resumo do que mudou no código

| Arquivo | Mudança |
|---|---|
| `mkt_flow_p0/landing.py` | Injeção automática do GA4 + evento affiliate_click |
| `mkt_flow_p0/keyword_research.py` | NOVO — Autocomplete do Google gratuito |
| `mkt_flow_p0/seo.py` | llms.txt, FAQ Schema, enriquecer_com_keywords |
| `pipeline_p0.py` | Etapas de keywords, FAQ e llms.txt |
| `tests/` | 11 novos testes (total 239) |
| `MKTFLOW/site/bancada-standalone.html` | v3.12 — sem campo de senha, prompt na hora |

---

## O que DEPENDE DE VOCÊ (tutoriais acima)

| # | O que fazer | Tempo |
|---|---|---|
| **1** | **Ativar GA4**: criar conta em `analytics.google.com` → copiar o ID `G-XXXXXX` → me mandar (eu coloco no `.env`) | 5 min |
| **2** | **Plugins no WordPress**: `Plugins → Adicionar novo` → instalar `Rank Math`, `Site Kit by Google`, `AffiliateX` | 15 min |
| **3** | **Search Console**: conectar via Site Kit (ou manual com a tag de verificação) | 10 min |
| **4** | **Extensões Chrome**: Melify (comissão ML), SiteStripe (Amazon), Block Yourself from Analytics (`*conexotech.com.br`) | 5 min |
| **5** | **Subir `llms.txt`** no Hostinger (`public_html`) | 5 min |

**Sugestão de ordem:** comece pelo **Tutorial 1** — quando tiver o ID do GA4 (`G-...`), me mande que eu ativo no `.env`. Depois faça o 2 e 3 (são os que trazem os dados reais de busca do Search Console).

---

## Tutorial — Corrigir a Bancada (5 min)

O WordPress apagou o JavaScript ao salvar. A solução: **não usar WordPress**, hospedar direto no Hostinger.

**Passo 1 — Enviar o arquivo:**
1. Painel Hostinger → `Gerenciador de Arquivos` → `public_html`
2. Clique `Upload` → selecione o `bancada-standalone.html` do seu PC
4. Renomeie para **`bancada.html`**

**Passo 2 — Testar (botões voltam à vida):**
1. Aba anônima (`Ctrl+Shift+N`) → `https://conexotech.com.br/bancada.html`
2. Cole link de **produto** → `1. Validar link` → responde na hora

**Passo 3 — Apagar página antiga do WordPress:**
1. `wp-admin` → `Páginas` → `Todas as páginas`
2. Passe o mouse em `Bancada` → **`Mover para lixeira`**

**Passo 4 — Robots.txt + Revisão:**
1. `public_html` → editar `robots.txt` → adicionar `Disallow: /bancada/`
2. Search Console → `Problemas de segurança` → `Pedir revisão`

---

## Tutorial — Corrigir a exposição de usuários (5 min)

O endpoint `/wp-json/wp/v2/users` expõe seu login.

1. Hostinger → `Gerenciador de Arquivos` → `public_html` → `wp-content` → `themes` → pasta do tema → `functions.php` → `Editar`
2. Cole no final (antes do `?>` se houver):

```php
// Bloqueia exposição de usuários via REST API (segurança)
add_filter('rest_endpoints', function($endpoints){
    if (isset($endpoints['/wp/v2/users'])) unset($endpoints['/wp/v2/users']);
    if (isset($endpoints['/wp/v2/users/(?P<id>[\d]+)'])) unset($endpoints['/wp/v2/users/(?P<id>[\d]+)']);
    return $endpoints;
});
```
3. `Salvar`

---

## Tutorial — Pedir revisão ao Google (10 min)

**Passo 1:** `https://search.google.com/search-console` → `Problemas de segurança`
**Passo 2:** Clique `Pedir revisão` → marque a caixa → `Enviar`
**Passo 3:** Aguarde 1–3 dias úteis.

---

## Próximo passo sugerido

Me mande o **ID do GA4** (`G-XXXXXX`) que eu ativo no `.env`. Depois faça os Tutoriais 2 e 3. Quando o "Gerador de links" do ML gerar um link com `wid=`, me avise que fecho o ciclo completo: validar → gerar → agendar → publicar.