# Ollama local opcional — contingência sem dependência de PC na nuvem

**Estado:** integração de código em branch experimental, **não homologada no Windows/Hostinger**; nada foi instalado nem ativado.

## Hardware informado

- Windows 10, RAM **16 GB**, Radeon **RX 580 8 GB**.
- A RX 580 **não é GPU ROCm oficialmente suportada** pelo Ollama atual no Windows; use CPU como referência e teste Vulkan somente se a instalação do Ollama reconhecer a placa. Não dependa de drivers ou builds comunitários.
- Candidatos locais: `qwen3:4b` (~2,5 GB de download de modelo) para início; `qwen2.5:7b` (~4,7 GB) para comparação de qualidade. RAM consumida é superior ao arquivo quantizado e depende de contexto.
- Artigos devem passar pelos mesmos contratos de texto, persona, evidências e revisão. Modelo local **não** aprova fatos nem assina recibos.

## Instalação opt-in no PC

1. Baixar o Ollama do endereço oficial https://ollama.com/download/windows .
2. No PowerShell: `ollama --version`. Se instalado, executar `ollama pull qwen3:4b` (download opcional).
3. Verificar disponibilidade local com `ollama list` e `ollama ps` após primeiro uso.
4. Configuração de uma sessão PowerShell local **apenas para ensaio**:

```powershell
$env:AI_PROVIDER = "ollama"
$env:OLLAMA_MODEL = "qwen3:4b"
$env:AI_FREE_ONLY = "true"
$env:AI_FALLBACK_ENABLED = "false"
python -m pytest tests/test_ai_providers.py tests/test_ollama_optional_provider.py -q
```

Os testes acima **simulam a rede** e não demonstram qualidade nem acessibilidade do servidor Ollama. O ensaio real somente deve ocorrer com entrada editorial de teste, sem WordPress.

## Segurança e operacionalização

- Adaptador usa **somente** `http://127.0.0.1:11434/v1/chat/completions`. Não há opção de URL externa configurável ou encaminhamento para Hostinger.
- Nenhum token de cloud é enviado para Ollama. O serviço não deve ser exposto publicamente via `OLLAMA_HOST=0.0.0.0`, portas ou túneis.
- Não ativar Ollama como fallback automático no executor Hostinger: `127.0.0.1` na Hostinger é **a própria Hostinger**, não o PC Windows.
- Um worker local futuro poderá consumir tarefas não sensíveis da fila Turso **somente quando PC estiver ligado**, com autorização e conta de serviço restrita, entrega idempotente e sem permissão de publicação.
- O plano de continuidade primário continua Groq Free → Gemini/OpenRouter conforme homologação. A fila permanece operacional quando todos falharem.
- A escolha de um modelo local não garante geração editorial adequada: testar português, extensões, JSON válido e rejeição de trechos genéricos.
- O provedor padrão da branch permanece Groq, `AI_FREE_ONLY=true`, `AI_FALLBACK_ENABLED=false`. Esta branch **não altera** a operacional Hostinger nem o Gate.

## Reversão

Trocar `AI_PROVIDER` de volta para `groq` ou simplesmente encerrar a sessão PowerShell de testes. Se ainda não integrou a branch experimental, nenhuma reversão na produção é necessária.
