import time, json, logging
from fastapi.responses import JSONResponse
from config import LOG_LEVEL
from credits import get_client_id, get_credits, consume_credit, CREDIT_SYSTEM_ENABLED

logger = logging.getLogger("mkt_flow_middleware")
logger.setLevel(getattr(logging, LOG_LEVEL))

async def rate_limit_middleware(request, call_next):
    client_id = get_client_id(request)
    if CREDIT_SYSTEM_ENABLED and get_credits(client_id) <= 0:
        return JSONResponse(status_code=429, content={"error": "Limite de créditos excedido."})
    response = await call_next(request)
    if response.status_code == 200:
        consume_credit(client_id)
    return response

async def audit_log_middleware(request, call_next):
    start = time.time()
    response = await call_next(request)
    logger.info(json.dumps({
        "timestamp": time.time(),
        "method": request.method,
        "path": request.url.path,
        "client_ip": request.client.host if request.client else "unknown",
        "status": response.status_code,
        "latency_ms": round((time.time() - start) * 1000, 2)
    }))
    return response

async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response