# admin/Dockerfile — Bot Telegram always-on (Fly.io/Render/Railway)
FROM python:3.11-slim
WORKDIR /app
COPY requirements/rss.txt requirements/rss.txt
COPY requirements/base.txt requirements/base.txt
RUN pip install --no-cache-dir -r requirements/rss.txt && pip install --no-cache-dir "python-telegram-bot==20.*"
COPY mkt_flow_p0 mkt_flow_p0
COPY admin admin
COPY pipeline_rss.py .
COPY .env.example .env.example
# .env real vem via secrets do host (não copiar .env)
CMD ["python", "admin/bot.py"]
