FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

RUN mkdir -p output/logs state

EXPOSE 8000 8001

HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -sf http://localhost:8001/api/health || exit 1

CMD ["sh","-c","python dashboard/app.py & python api_server.py & python scanner.py --tier 1"]
