# Tutorial — automação do Google Sheets (conta de serviço)

Objetivo: eu crio e atualizo planilhas no Drive sozinho; você só preenche links.
Tempo: ~10 min, só cliques. Feito 1 vez; vale para todos os projetos.

## Parte 1 — conta de serviço (no Google Cloud)
1. Abra `console.cloud.google.com` (mesma conta Google do YouTube).
2. No topo, selecione o projeto `conexotech` (ou o que usou para a chave do YouTube).
3. Menu ☰ → **IAM e administrador → Contas de serviço** → **+ Criar conta de serviço**.
4. Nome: `conexotech-planilhas` → **Criar e continuar** → pule permissões (Sem função) → **Concluir**.
5. Na lista, clique na conta criada → aba **Chaves** → **Adicionar chave → Criar nova chave → JSON** → baixa um arquivo `.json`.
6. Anote o e-mail da conta (ex.: `conexotech-planilhas@conexotech.iam.gserviceaccount.com`).

## Parte 2 — guardar a chave (no PC)
1. Na pasta `site do projeto`, crie a pasta `secrets` (sem ponto na frente —
   o Windows Explorer recusa nomes começados em ponto).
2. Mova o JSON baixado para lá com o nome exato `google-sheets.json`
   (caminho final: `site do projeto\secrets\google-sheets.json`).
3. Segurança: essa pasta **nunca sobe ao GitHub** (já blindada no `.gitignore`).
   Nunca cole o conteúdo da chave no chat — eu só preciso saber que o arquivo está lá.

## Parte 3 — ativar as APIs
1. No console: **APIs e serviços → Biblioteca** → ative **Google Sheets API**.
2. Na mesma Biblioteca, ative **Google Drive API** (preciso dela para criar a planilha).

## Parte 4 — dar acesso (detalhada)
> Pré-requisito: o e-mail da conta de serviço (Parte 1, passo 6 — algo como
> `conexotech-planilhas@conexotech.iam.gserviceaccount.com`). Deixe-o copiado.
1. ONDE: no navegador, abra `drive.google.com` com a **sua conta Google pessoal**
   (a mesma onde você quer ver as planilhas).
2. No canto superior esquerdo, clique em **+ Novo** → **Nova pasta** → nome
   `ConexoTech` → **Criar**. O QUE esperar: a pasta aparece na lista "Meu Drive".
3. Clique com o **botão direito** em cima da pasta `ConexoTech` → **Compartilhar**
   → **Compartilhar**. O QUE esperar: abre a janela "Compartilhar ConexoTech".
4. No campo **Adicionar pessoas**, cole o e-mail da conta de serviço.
   O QUE esperar: aparece um cartão com o e-mail e, ao lado, a função atual.
5. Clique na função (vem como **Leitor** ou **Visualizador**) e troque para
   **Editor**. ATENÇÃO: como Leitor eu só leio — sem Editor, nada funciona.
6. **Desmarque** "Notificar pessoas" (conta de serviço não lê e-mail).
7. Clique **Enviar** ou **Concluir**. O QUE esperar: o e-mail some do campo e a
   janela fecha sem erro.
8. Conferência: botão direito na pasta → **Compartilhar** → em "Quem tem acesso"
   deve constar o e-mail da conta como **Editor**.
> Alternativa: em vez da pasta, compartilhe planilhas avulsas uma a uma com o
> mesmo e-mail (dá mais trabalho a cada tabela nova).

## Parte 5 — teste comigo
1. Me avise "chave no lugar". Eu escrevo **1 célula de teste** e te mostro o link.
2. Confirmado, apago a célula e a automação está viva.

## Como funciona depois
- Você pede ("planilha dos afiliados de TVs") → eu crio na pasta, com as colunas
  padrão (tipo, modelo, especificação, marketplace, link, status) e te mando o link.
- Você preenche a coluna `link` → me avisa → eu leio a planilha e converto em `/go/`.
- Cotas grátis: Sheets API permite milhões de leituras/escritas por dia — sem custo.

## Se acontecer
| Sintoma | Causa provável | Correção |
|---|---|---|
| Eu digo "sem acesso" | Pasta/planilha não compartilhada com a conta | Refazer Parte 4 com o e-mail exato |
| Erro "API não ativada" | Sheets ou Drive API desligada | Refazer Parte 3 no projeto certo |
| Arquivo `.json` com outro nome | Meu leitor procura `google-sheets.json` | Renomear exatamente |
| Dúvida se a chave vazou | — | Apagar a chave em IAM → Chaves e gerar outra |
