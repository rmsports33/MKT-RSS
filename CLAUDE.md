# CLAUDE.md — Instruções para qualquer agente que abrir este projeto

## 🚨 FAÇA ISSO ANTES DE QUALQUER OUTRA COISA

Toda vez que você iniciar uma sessão neste projeto (OpenCode, Claude Code, DeepSeek, OpenRouter ou qualquer outra plataforma), execute **primeiro** este comando:

```bash
python tools/iniciar.py
```

Ou dê duplo-clique em:
- `iniciar.bat` (Windows)
- `iniciar.sh` (Linux/Mac)

## O que este arquivo faz

1. Verifica se o registro do projeto está completo (`docs/REGISTRO_UNICO_20261118.md`)
2. Corrige automaticamente se algo estiver faltando
3. Diz em palavras simples se você pode começar ou o que ainda falta

## Quando executar novamente

- **Antes de começar** qualquer tarefa
- **Quando terminar** o trabalho (para salvar tudo o que foi feito)
- **Sempre que abrir** uma nova sessão ou mudar de plataforma

## Não pule este passo

Se pular, o projeto pode perder contexto entre sessões e plataformas. O registro único é a fonte da verdade.

## Regras do projeto

- Nunca faça commit direto em `master`/`main`
- Crie sempre uma branch nova para cada tarefa
- Todas as auditorias devem ser registradas no `docs/REGISTRO_UNICO_20261118.md`
