# AI-API Host Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uvicorn fastapi pydantic requests 'ray[rllib]' numpy tree

COPY ai_api.py .
COPY capabilities/ ./capabilities/

EXPOSE 8088

CMD ["uvicorn", "ai_api:app", "--host", "0.0.0.0", "--port", "8088"]
