from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json, hashlib, asyncio, logging, uvicorn
from datetime import datetime
from typing import Optional, List

from main import process_request
from credits import get_client_id, get_credits, consume_credit, CREDIT_SYSTEM_ENABLED, DAILY_CREDIT_LIMIT
from middleware import rate_limit_middleware, audit_log_middleware, add_security_headers
from db import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

init_db()
app = FastAPI(title="MKT Flow 3.0 API", version="3.0")
app.middleware("http")(rate_limit_middleware)
app.middleware("http")(audit_log_middleware)
app.middleware("http")(add_security_headers)

class GenerateRequest(BaseModel):
    user_input: str
    product_data: dict
    history: Optional[list] = []
    summary: Optional[str] = ""
    language: Optional[str] = "auto"
    ab_variations: Optional[int] = 1
    target_audience: Optional[str] = None

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/generate")
async def generate(request: Request, gen_req: GenerateRequest):
    client_id = get_client_id(request)
    if CREDIT_SYSTEM_ENABLED and get_credits(client_id) <= 0:
        return JSONResponse(status_code=429, content={"error": "Limite de créditos excedido."})
    
    result = await process_request(
        user_input=gen_req.user_input,
        raw_product_data=gen_req.product_data,
        conversation_history=gen_req.history,
        resumo_anterior=gen_req.summary,
        language=gen_req.language,
        ab_variations=gen_req.ab_variations,
        target_audience=gen_req.target_audience
    )
    if CREDIT_SYSTEM_ENABLED:
        consume_credit(client_id)
    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)