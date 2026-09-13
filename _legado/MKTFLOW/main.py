import json
import time
import re
import logging
import os
from typing import Optional
from datetime import datetime

from task_router import TaskRouter
from context_compiler import ContextCompiler
from history_manager import HistoryManager
from prompt_loader import load_prompt, ensure_prompts_exist
from output_validator import validate_and_parse
from config import LOG_LEVEL, CONTEXT_TOKEN_BUDGET, GROQ_API_KEY
from credits import get_client_id, consume_credit

# ====== Tentar importar Groq ======
try:
    from groq import Groq
    GROQ_AVAILABLE = True if GROQ_API_KEY else False
except ImportError:
    GROQ_AVAILABLE = False
    print("⚠️ Biblioteca 'groq' não instalada. Instale com: pip install groq")

logging.basicConfig(level=getattr(logging, LOG_LEVEL))
logger = logging.getLogger("mkt_flow")

router = TaskRouter()
compiler = ContextCompiler(token_budget=CONTEXT_TOKEN_BUDGET)
history_mgr = HistoryManager(window_size=4)
ensure_prompts_exist()

# ====== Inicializar cliente Groq ======
groq_client = None
if GROQ_AVAILABLE and GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
        logger.info("✅ Cliente Groq inicializado com sucesso!")
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar Groq: {e}")
        groq_client = None

# ====== Função para chamar o Groq (ou fallback para simulação) ======
async def call_groq(prompt: str, temperature: float = 0.3) -> str:
    """
    Chama a API do Groq para gerar conteúdo. Se não estiver disponível, retorna simulação.
    """
    if groq_client:
        try:
            # Usar modelo Llama 3 (70B) que é gratuito e poderoso
            response = groq_client.chat.completions.create(
                model="mixtral-8x7b-32768", # ou "mixtral-8x7b-32768"
                messages=[
                    {"role": "system", "content": "Você é o Mick, especialista em marketing digital. Seja direto, objetivo e gere conteúdo de alta qualidade. Sempre inclua #ad #linkdeafiliado quando for promocional."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=2048
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"❌ Erro ao chamar Groq: {e}")
            return None
    else:
        logger.warning("⚠️ Groq não disponível. Usando simulação.")
        return None

# ====== Função principal de processamento ======
async def process_request(
    user_input: str,
    raw_product_data: dict,
    conversation_history: list,
    resumo_anterior: str = "",
    language: str = "pt",
    ab_variations: int = 1,
    target_audience: Optional[str] = None
):
    start_time = time.time()
    
    # Validação básica
    if not raw_product_data:
        return {"decision": "ERROR", "content": "Dados do produto não fornecidos."}
    
    # Detectar idioma (se 'auto')
    if language == "auto":
        try:
            from langdetect import detect
            lang = detect(user_input)
            if lang.startswith("pt"): language = "pt"
            elif lang.startswith("es"): language = "es"
            elif lang.startswith("en"): language = "en"
            else: language = "pt"
        except:
            language = "pt"
    
    # Rotear tarefa
    task = router.route(user_input)
    logger.info(f"📌 Tarefa identificada: {task}")
    
    # Compilar contexto (filtrar dados desnecessários)
    contexto_filtrado = compiler.compile(task, raw_product_data)
    
    # Carregar prompt do sistema
    system_prompt = load_prompt(task, lang=language)
    
    # Gerenciar histórico
    messages, novo_resumo = history_mgr.gerenciar_historico(
        system_prompt=system_prompt,
        conversation_history=conversation_history,
        new_user_message=user_input
    )
    
    # Montar mensagem do usuário com contexto
    user_message_content = f"Dados do produto: {json.dumps(contexto_filtrado, ensure_ascii=False)}\n\n"
    if target_audience:
        user_message_content += f"🎯 Público-alvo: {target_audience}\n\n"
    user_message_content += f"Pergunta: {user_input}"
    messages[-1]["content"] = user_message_content
    
    # ====== GERAR CONTEÚDO COM IA (GROQ) OU SIMULAÇÃO ======
    # Montar o prompt completo para enviar ao Groq
    full_prompt = f"{system_prompt}\n\n{user_message_content}"
    
    # Tentar chamar Groq
    ia_response = await call_groq(full_prompt, temperature=0.3)
    
    if ia_response:
        # Se o Groq respondeu, usamos a resposta dele
        try:
            # Tentar parsear como JSON (se o modelo retornar JSON)
            validated = validate_and_parse(ia_response)
        except:
            # Se não for JSON, criar uma estrutura compatível
            validated = validate_and_parse(json.dumps({
                "decision": "ALLOW",
                "content": ia_response,
                "disclosure": "#ad #linkdeafiliado",
                "reason_code": None,
                "metadata": {"task": task, "source": "groq"}
            }))
    else:
        # Fallback: simulação (caso Groq não esteja disponível)
        logger.info("🔄 Usando simulação (fallback)")
        if task == "article":
            content = f"""
# Artigo: {raw_product_data.get('nome', 'Produto')}

Este é um artigo de exemplo gerado pelo MKT Flow 3.0 (modo simulação).

## Introdução
O produto {raw_product_data.get('nome', 'Produto')} é uma excelente opção para quem busca qualidade e preço acessível.

## Especificações
- Nome: {raw_product_data.get('nome', 'Produto')}
- Preço: R$ {raw_product_data.get('preco', 0)}
- Categoria: {raw_product_data.get('categoria', 'Geral')}

## Prós e Contras
**Prós:**
- Qualidade superior
- Preço competitivo
- Garantia estendida

**Contras:**
- Disponibilidade limitada
- Cor única

## Conclusão
Recomendamos a compra do {raw_product_data.get('nome', 'Produto')} para quem busca um produto confiável.

🔗 [Link para comprar]({raw_product_data.get('url', '#')})
"""
        else:
            content = f"Conteúdo gerado para a tarefa '{task}': {raw_product_data.get('nome', 'Produto')}"
        
        validated = validate_and_parse(json.dumps({
            "decision": "ALLOW",
            "content": content,
            "disclosure": "#ad #linkdeafiliado",
            "reason_code": None,
            "metadata": {"task": task, "source": "simulation"}
        }))
    
    # ====== RETORNAR RESPOSTA ======
    latency_ms = (time.time() - start_time) * 1000
    logger.info(f"⏱️ Processamento concluído em {latency_ms:.2f}ms")
    
    return {
        "decision": validated.decision,
        "content": validated.content,
        "disclosure": validated.disclosure,
        "reason_code": validated.reason_code,
        "metadata": validated.metadata,
        "summary": novo_resumo,
        "language": language
    }