"""src.evergreen — chamada LLM com fallback gratuito (OpenRouter -> Ollama).

Compatível com qualquer servidor OpenAI-compatible (parâmetros via .env).
Sem chave de API paga em nenhum ponto da cadeia.
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / ".env")
except Exception:
    pass


def _cfg():
    return {
        "openrouter_key": os.getenv("OPENROUTER_API_KEY", "").strip(),
        "openrouter_base": os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").strip(),
        "openrouter_model": os.getenv("OPENROUTER_MODEL", "google/gemini-flash-1.5:free").strip(),
        "ollama_base": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1").strip(),
        "ollama_model": os.getenv("OLLAMA_MODEL", "llama3.1:8b").strip(),
    }


def _try_call(api_key: str, base_url: str, model: str, temp: float, system: str, user: str):
    from openai import OpenAI
    if not api_key or not base_url:
        raise RuntimeError("sem credencial")
    c = OpenAI(api_key=api_key, base_url=base_url)
    return c.chat.completions.create(model=model, temperature=temp, max_tokens=4000,
                                     messages=[{"role": "system", "content": system},
                                               {"role": "user", "content": user}])


def gerar_texto(system: str, user: str, temperature: float = 0.7) -> dict:
    """Tenta OpenRouter (Gemini free); cai para Ollama local ilimitado."""
    cfg = _cfg()
    tentativas = []
    if cfg["openrouter_key"]:
        try:
            resp = _try_call(cfg["openrouter_key"], cfg["openrouter_base"],
                             cfg["openrouter_model"], temperature, system, user)
            return {"texto": resp.choices[0].message.content, "provedor": "openrouter",
                    "modelo": cfg["openrouter_model"]}
        except Exception as e:
            tentativas.append(f"openrouter: {str(e)[:100]}")
    try:
        resp = _try_call("ollama", cfg["ollama_base"], cfg["ollama_model"], 0.3, system, user)
        return {"texto": resp.choices[0].message.content, "provedor": "ollama",
                "modelo": cfg["ollama_model"], "avisos": tentativas}
    except Exception as e:
        return {"erro": f"LLM indisponível (openrouter+ollama): {str(e)[:150]}", "tentativas": tentativas}
