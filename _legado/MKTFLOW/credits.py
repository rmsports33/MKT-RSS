from db import get_db
from datetime import datetime
from config import CREDIT_SYSTEM_ENABLED, DAILY_CREDIT_LIMIT

def get_credits(client_id):
    if not CREDIT_SYSTEM_ENABLED: return 999
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT count FROM credits WHERE client_id = ? AND date = ?", (client_id, today))
    row = c.fetchone()
    conn.close()
    used = row[0] if row else 0
    return max(0, DAILY_CREDIT_LIMIT - used)

def consume_credit(client_id):
    if not CREDIT_SYSTEM_ENABLED: return True
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT count FROM credits WHERE client_id = ? AND date = ?", (client_id, today))
    row = c.fetchone()
    if row:
        if row[0] >= DAILY_CREDIT_LIMIT:
            conn.close()
            return False
        c.execute("UPDATE credits SET count = ? WHERE client_id = ? AND date = ?", (row[0]+1, client_id, today))
    else:
        c.execute("INSERT INTO credits (client_id, date, count) VALUES (?, ?, ?)", (client_id, today, 1))
    conn.commit()
    conn.close()
    return True

def get_client_id(request):
    api_key = request.headers.get("X-API-Key")
    if api_key: return f"key_{api_key[:8]}"
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded: return f"ip_{forwarded.split(',')[0].strip()}"
    return f"ip_{request.client.host if request.client else 'unknown'}"