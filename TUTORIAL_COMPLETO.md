# Tutorial Completo — MKT Flow + Site de Comparativos

Tutorial passo a passo para iniciantes. Siga na ordem. Não pule etapas.

---

## O que você já tem pronto

| Item | Local | Para que serve |
|---|---|---|
| Modelo de planilha | `Desktop\MY PROJECTS FLOW\modelo_planilha_perifericos.csv` | Copiar para o Google Sheets |
| Pipeline de geração | `C:\MKTFLOW\pipeline.py` | Importa planilha → gera com IA → cria site |
| Site gerado | `C:\MKTFLOW\site\` | Pasta pronta para publicar na internet |
| Interface gráfica | `C:\MKTFLOW\app.py` | Gerar conteúdo sem planilha, manualmente |

---

## PARTE 1 — Montar sua planilha no Google Sheets

**Objetivo:** criar a planilha que alimenta o site automaticamente.

1. Abra o arquivo `modelo_planilha_perifericos.csv` com o Bloco de Notas:
   - Clique com o botão direito no arquivo → **Abrir com** → **Bloco de Notas**
   - Pressione `Ctrl+A` (selecionar tudo) e `Ctrl+C` (copiar). Feche.

2. Acesse `https://sheets.google.com` e faça login com sua conta Google.

3. Clique no **+** (Novo) → **Planilha em branco**.

4. Na célula `A1` (a primeira, canto superior esquerdo), clique com o botão direito → **Colar**.

5. Sua planilha agora tem 4 linhas de exemplo (teclado, mouse, webcam, fone) com colunas de especificações.

6. **Preencha com SEUS produtos:**
   - `produto_a_nome` / `produto_b_nome`: nome dos produtos
   - `produto_a_preco` / `produto_b_preco`: preço (use ponto como decimal: `249.90`)
   - `produto_a_url` / `produto_b_url`: seu link de afiliado
   - `spec_nome_X` / `spec_valor_a_X` / `spec_valor_b_X`: especificação + valor de cada produto
   - `titulo`: título do artigo
   - `palavra_chave`: termo que as pessoas buscam (ex: `teclado mecanico vs membrana`)
   - Deixe `slug` em branco — é gerado sozinho.

7. **Regra de ouro:** só coloque especificações verdadeiras do fabricante. A IA não inventa — ela usa exatamente o que está na planilha.

8. **Para adicionar mais comparativos:** copie uma linha inteira (selecione as células, `Ctrl+C`, clique na primeira célula da linha de baixo, `Ctrl+V`) e edite os valores.

9. **Para adicionar mais specs:** use o próximo número. Ex: se você tem até `spec_nome_8`, adicione `spec_nome_9`, `spec_valor_a_9`, `spec_valor_b_9`.

---

## PARTE 2 — Publicar a planilha (transformar em link)

1. No Google Sheets, menu **Arquivo** → **Compartilhar** → **Publicar na web**.

2. Na janela que abrir:
   - Aba **"Conteúdo e configurações"** ou **"Vincular"**
   - Em **Escolha um conteúdo**: selecione a planilha correta (a sua aba)
   - Em **Formato**: selecione **CSV**
   - Clique em **Publicar** (e **OK** para confirmar)

3. Copie o link que aparece (algo como:
   `https://docs.google.com/spreadsheets/d/e/2PACX-.../pub?output=csv`)

4. **Esse link é a "fonte de dados" do seu site.** Guarde-o.

> Dica: se você fizer isso e o link vier com `#gid=...`, não tem problema, o pipeline resolve.

---

## PARTE 3 — Conectar o link ao pipeline

1. Abra o Bloco de Notas.

2. Cole o link que você copiou.

3. Salve o arquivo no caminho exato:
   `C:\MKTFLOW\content\sheets_url.txt`
   - **Importante:** o arquivo precisa se chamar exatamente `sheets_url.txt` e estar na pasta `content` dentro de `C:\MKTFLOW`.
   - Se a pasta `content` não existir, crie: abra `C:\MKTFLOW`, clique com o botão direito → Novo → Pasta → nome `content`.

---

## PARTE 4 — Rodar o pipeline (gerar o site)

1. Abra o **Prompt de Comando** (cmd):
   - Pressione `Windows` + `R`
   - Digite `cmd` e pressione Enter

2. Entre na pasta do projeto:
   ```
   cd C:\MKTFLOW
   ```

3. Rode o pipeline:
   ```
   venv\Scripts\python pipeline.py
   ```

4. O que vai acontecer:
   - Ele lê sua planilha (pelo link salvo)
   - Gera um artigo comparativo para cada linha com a IA
   - Cria os arquivos HTML na pasta `C:\MKTFLOW\site\`

5. Ao final deve aparecer algo como:
   ```
   [OK] Conteudo gerado para 4 comparativos.
   [OK] Site gerado: 4 comparativos em C:\MKTFLOW\site
   ```

6. **Para ver o site no seu computador:** abra o arquivo `C:\MKTFLOW\site\index.html` (duplo clique).

---

## PARTE 5 — Publicar na internet (GitHub + Vercel, 100% grátis)

### 5.1 Criar conta no GitHub

1. Acesse `https://github.com` → **Sign up**
2. Crie com seu e-mail. Confirme o e-mail.

### 5.2 Criar um repositório (a "pasta" online)

1. No GitHub, clique em **New repository** (botão verde) ou **+** → **New repository**
2. Nome: `site-perifericos` (ou qualquer nome)
3. Deixe **Public** selecionado
4. NÃO marque a caixa "Add a README file"
5. Clique em **Create repository**

### 5.3 Subir a pasta `site` para o GitHub

1. Abra o Prompt de Comando:
   ```
   cd C:\MKTFLOW
   ```
2. Inicialize o Git dentro de `site` (um passo só, não se assuste):
   ```
   cd site
   git init
   git add .
   git commit -m "primeira versao do site"
   git branch -M main
   git remote add origin https://github.com/SEU-USUARIO/site-perifericos.git
   git push -u origin main
   ```
   - Troque `SEU-USUARIO` pelo seu nome de usuário do GitHub
   - Na hora do `git push`, o Git pede usuário e senha.
     - Usuário: seu nome do GitHub
     - Senha: **não é sua senha!** É um token de acesso. Veja o passo 5.4.

### 5.4 Criar o token de acesso (senha do push)

1. No GitHub: clique na sua **foto** (canto superior direito) → **Settings**
2. No menu esquerdo, desça até **Developer settings**
3. Clique em **Personal access tokens** → **Tokens (classic)** → **Generate new token (classic)**
4. Dê um nome (ex: "site") e marque a caixa **repo**
5. Clique em **Generate token**
6. **Copie o token imediatamente** (só aparece uma vez). Ele começa com `ghp_...`
7. Use esse token como senha quando o Git pedir.

### 5.5 Publicar no Vercel

1. Acesse `https://vercel.com` → **Sign up**
2. Clique em **Continue with GitHub** (mais rápido)
3. Siga a autorização (Vercel vai pedir acesso ao seu GitHub — clique em **Authorize**)
4. Depois de logado: clique em **Add New** → **Project**
5. Selecione o repositório `site-perifericos`
6. Na tela de configuração:
   - **Framework Preset:** deixe como está (Vercel reconhece sozinho)
   - **Build Command:** deixe em branco
   - **Output Directory:** deixe em branco (o Vercel já detecta `public` ou o diretório raiz — nossa pasta `site` é a raiz do repositório, então funciona)
7. Clique em **Deploy**
8. Aguarde ~30 segundos. Ao terminar, aparecerá seu endereço:
   `https://site-perifericos.vercel.app`

**Seu site está no ar!** Compartilhe esse link onde quiser.

---

## PARTE 6 — Corrigir o domínio no sitemap (opcional, recomendado)

O site usa `seu-dominio.vercel.app` como exemplo no sitemap. Para corrigir:

1. Abra `C:\MKTFLOW\generate_site.py` no Bloco de Notas
2. Encontre: `https://seu-dominio.vercel.app`
3. Troque pelo seu endereço real (ex: `https://site-perifericos.vercel.app`)
4. Salve e rode novamente:
   ```
   cd C:\MKTFLOW
   venv\Scripts\python pipeline.py
   ```
5. Suba a pasta `site` de novo (repita os comandos do passo 5.3)

---

## PARTE 7 — Atualizar o site quando quiser

Sempre que fizer mudanças na planilha (novos produtos, preços, links):

1. Atualize a planilha no Google Sheets
2. No cmd:
   ```
   cd C:\MKTFLOW
   venv\Scripts\python pipeline.py
   cd site
   git add .
   git commit -m "atualizacao"
   git push
   ```

O Vercel atualiza automaticamente sozinho após o `git push`.

---

## BÔNUS — Interface gráfica (gerar conteúdo manualmente)

Se quiser gerar um comparativo sem planilha:

1. No cmd:
   ```
   cd C:\MKTFLOW
   venv\Scripts\python -m uvicorn api:app --port 8000
   ```
2. Abra **outro** Prompt de Comando:
   ```
   cd C:\MKTFLOW
   venv\Scripts\python -m streamlit run app.py
   ```
3. O navegador abre a interface do MKT Flow
4. Na tarefa, escolha **comparativo**
5. Preencha Produto A e Produto B (nome, preço, link, specs no formato `chave: valor`)
6. Clique em **Gerar**

---

## Problemas comuns

**"ERRO: Groq não disponível"** → verifique se o arquivo `C:\MKTFLOW\.env` existe e tem a chave. Não compartilhe esse arquivo com ninguém.

**"429 Too Many Requests"** → é o limite da Groq (grátis). Espere alguns minutos e rode de novo. O pipeline já tenta de novo sozinho.

**O site abre mas está sem o conteúdo novo** → rode o `pipeline.py` de novo e faça o `git push`. O Vercel precisa da versão mais nova.

**Não lembro meu token do GitHub** → gere outro (passo 5.4). Tokens podem ser revogados e recriados.

**A página não carrega imagens** → o modelo atual é só texto (tabelas). Imagens serão um próximo passo.

---

## Fluxo rápido de referência

```
Planilha Sheets → (link CSV) → pipeline.py → IA gera artigos → site/ → git push → Vercel publica
```

Cada vez que você atualizar a planilha e rodar `pipeline.py` + `git push`, o site atualiza.