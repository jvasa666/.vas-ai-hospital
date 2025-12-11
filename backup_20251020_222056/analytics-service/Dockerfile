# ZFP-ANALYTICS-SERVICE-BUILDER (PYTHON/FASTAPI)
FROM python:3.11-slim

WORKDIR /app

# Install production dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Use Gunicorn with Uvicorn worker for production performance (Pillar 7)
CMD ["gunicorn", "main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]