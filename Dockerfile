# image backend ProcureWise untuk Hugging Face Spaces (SDK Docker)
FROM python:3.14-slim

# LightGBM butuh runtime OpenMP di Linux
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Spaces menjalankan container sebagai user dengan uid 1000
RUN useradd --create-home --uid 1000 app
WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# backend mengimpor procurewise_ml dan memuat model dari folder ml
COPY backend/ backend/
COPY ml/procurewise_ml/ ml/procurewise_ml/
COPY ml/models/ ml/models/

ENV ML_DIR=/app/ml \
    ML_MODEL_DIR=/app/ml/models \
    PYTHONUNBUFFERED=1

USER app
WORKDIR /app/backend
EXPOSE 7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
