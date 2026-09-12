import os
from dotenv import load_dotenv
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
CONTEXT_TOKEN_BUDGET = int(os.getenv("CONTEXT_TOKEN_BUDGET", "2000"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
CREDIT_SYSTEM_ENABLED = os.getenv("CREDIT_SYSTEM_ENABLED", "true").lower() in ("true", "1", "t")
DAILY_CREDIT_LIMIT = int(os.getenv("DAILY_CREDIT_LIMIT", "10"))