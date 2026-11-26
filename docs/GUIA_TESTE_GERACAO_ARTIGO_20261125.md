# GUIA DE TESTE — GERAÇÃO DE ARTIGO (SOMENTE RAASCUNHO)

**Data:** 25/11/2026  
**Objetivo:** Testar se o código atualizado gera um artigo melhor, sem publicar nada.  
**Quem faz:** Você (ou alguém que você designar)  
**O que NÃO vai acontecer:** Nenhum artigo será publicado no site. Nenhum gasto será feito sem sua permissão.

---

## O que você precisa antes de começar

| Item | Onde conseguir |
|------|----------------|
| Chave da Groq | https://console.groq.com (gratuito para teste) |
| Acesso ao WordPress do site | Seu usuário e senha de aplicação em conexotech.com.br/wp-admin |
| Código no servidor | Já instalado em `wp-content/mkt-rss/` |

---

## Passo a passo

### 1. Configure a chave da Groq

No seu computador, abra o arquivo `.env` na pasta do MKT-RSS e adicione:

```
GROQ_API_KEY=sua_chave_aqui
GROQ_MODEL=llama-3.3-70b-versatile
```

> **Nunca coloque a senha no chat nem em arquivos enviados ao GitHub.** O arquivo `.env` é ignorado pelo Git.

### 2. Rode o motor de geração

No terminal, dentro da pasta `C:\Users\LIVE2PC\Documents\GitHub\MKT-RSS`:

```bash
python tools/iniciar.py
python pipeline_rss.py --fonte tecnoblog --limite 1 --dry-run
```

Isso vai:
- Buscar uma notícia recente
- Escrever o artigo usando o código atualizado
- Salvar como rascunho privado (não publica)

### 3. Verifique o que foi gerado

O motor vai criar um rascunho no WordPress com status `draft`. Você pode abrir:

```
https://conexotech.com.br/wp-admin/tools.php?page=conexo-gate-revisar-lote
```

Procure o artigo mais recente na fila.

### 4. Revise no Gate V1

Clique no artigo para revisar. Confira:

| O que verificar | O que esperar |
|-----------------|---------------|
| Frases completas | Não devem terminar no meio da palavra |
| Listas bem formadas | Não devem ter itens soltos fora da lista |
| Fontes com links | Cada afirmação deve ter um link para a fonte |
| Tema diverso | Escolha um assunto diferente do #9900 (ex: TV, celular, eletrodoméstico) |

### 5. Decida o destino

No Gate, você tem três opções:

1. **"Aprovar e manter em espera"** — O artigo fica pronto, mas não publicado. É a opção recomendada para teste.
2. **"Agendar automaticamente"** — Não use para teste. Publicaria sem sua revisão final.
3. **"Publicar imediatamente"** — Não use para teste.

---

## O que o código atualizado faz diferente

| Problema antes | O que muda agora |
|----------------|------------------|
| Frases cortadas em vários parágrafos | O HTML é reparado antes de salvar |
| Listas quebradas | Itens de lista ficam juntos |
| Erros de linguagem ignorados | Erros graves bloqueiam a gravação do rascunho |
| Sem prova de qualidade | O código registra se a voz editorial foi aplicada |
| Não havia bloqueio de escrita ruim | Erros críticos impedem o rascunho de ser gravado |

---

## Como saber se o teste funcionou

Se o artigo novo tiver:

- [ ] Frases inteiras (não cortadas)
- [ ] Listas organizadas
- [ ] Links nas fontes
- [ ] Nenhum erro crítico de linguagem

…então o problema da geração foi consertado.

Se ainda estiver ruim, me avise e eu investigo o que falta.

---

## Próximo passo após o teste

Se o artigo estiver bom:

1. Você aprova no Gate (opção "manter em espera")
2. Me avisa
3. Só então, com sua autorização específica, publicamos

Se não estiver bom, descarta o rascunho e não há nenhum prejuízo.

---

**Nada foi publicado. Nenhum gasto foi feito. Você controla tudo.**
