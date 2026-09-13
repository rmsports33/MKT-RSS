import json, re
from pydantic import BaseModel
from typing import Optional, List, Literal

class MKTFlowOutput(BaseModel):
    decision: Literal["ALLOW", "BLOCK", "NEEDS_EVIDENCE"]
    content: Optional[str] = None
    variations: Optional[List[str]] = None
    disclosure: Optional[str] = "#ad #linkdeafiliado"
    reason_code: Optional[str] = None
    metadata: Optional[dict] = None

def _repair_json(raw):
    raw = re.sub(r"```json\\s*", "", raw)
    raw = re.sub(r"```\\s*", "", raw)
    raw = re.sub(r"(?<=\\{)\\s*'([^']+)'\\s*:", r'"\\1":', raw)
    raw = re.sub(r":\\s*'([^']+)'", r': "\\1"', raw)
    raw = re.sub(r",\\s*\\}", "}", raw)
    raw = re.sub(r",\\s*\\]", "]", raw)
    return raw.strip()

def validate_and_parse(llm_response):
    try:
        return MKTFlowOutput(**json.loads(_repair_json(llm_response)))
    except:
        fallback = re.search(r"\\{.*\\}", llm_response, re.DOTALL)
        if fallback:
            return MKTFlowOutput(**json.loads(_repair_json(fallback.group())))
        raise ValueError("Resposta inválida")