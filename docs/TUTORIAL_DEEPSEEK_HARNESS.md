# 🎯 Tutorial para Começar com o DeepSeek Harness
## Projeto MKT-RSS — para usuários leigos

Não é preciso saber programar. Siga apenas estes passos.

---

## O que é o DeepSeek Harness?

Pense nele como um **assistente que trabalha sozinho** para você neste projeto. Ele lê as regras, segue as instruções e ajuda a fazer tarefas, mas **nunca publica nada no site sem você aprovar**.

---

## Passo 1: Abra o projeto

Entre na pasta do projeto no seu computador:

```
C:\Users\LIVE2PC\Documents\GitHub\MKT-RSS
```

---

## Passo 2: Rode o iniciador (obrigatório)

Antes de qualquer coisa, rode este comando:

```bash
python tools/iniciar.py
```

Ou dê duplo-clique em:
- `iniciar.bat` (Windows)
- `iniciar.sh` (Linux/Mac)

Ele vai verificar se tudo está certo e dizer se pode começar.

---

## Passo 3: Conecte o DeepSeek Harness

No terminal (prompt de comando), rode:

```bash
deepseek-harness --project mkt-rss --start
```

Se ele pedir uma chave de API, use a que já está no arquivo privado do servidor (nunca coloque senhas aqui no chat).

---

## Passo 4: O que o Harness vai fazer

Quando você conectar, ele vai:

1. **Ler o `CLAUDE.md`** — as regras do projeto
2. **Ler o `docs/REGISTRO_UNICO_20261118.md`** — o que já foi feito
3. **Rodar o `tools/iniciar.py`** — verificar se está tudo certo
4. **Fazer apenas o que você pedir** — nada sozinho

---

## Passo 5: Quando terminar

Sempre que terminar de trabalhar com o Harness, rode novamente:

```bash
python tools/iniciar.py
```

Isso salva tudo o que foi feito no registro do projeto.

---

## 📋 Regras de ouro (nunca quebre isso)

| ✅ Faça sempre | ❌ Nunca faça |
|---------------|---------------|
| Rode `tools/iniciar.py` antes de começar | Publique algo sem você aprovar |
| Rode `tools/iniciar.py` quando terminar | Mexa no `master`/`main` diretamente |
| Crie branches novas para cada tarefa | Apague arquivos sem salvar cópia |
| Registre tudo no `REGISTRO_UNICO.md` | Escreva papéis soltos que ninguém lê |

---

## 🆘 Se algo der errado

O próprio `tools/iniciar.py` vai dizer em palavras simples o que está faltando. Não adivinhe: siga o que ele informar.

---

## Resumo em uma frase

**Sempre comece e termine rodando `tools/iniciar.py`, e o DeepSeek Harness trabalhará com segurança neste projeto.**
