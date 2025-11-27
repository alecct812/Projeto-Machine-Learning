# Dockerfile para MLFlow Tracking Server
# Registro e versionamento de modelos de Machine Learning

FROM python:3.11-slim

LABEL maintainer="CESAR School - Aprendizado de Máquina 2025.2"
LABEL description="MLFlow Tracking Server para registro de experimentos"

# Definir diretório de trabalho
WORKDIR /mlflow

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar MLFlow e dependências
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    mlflow==2.9.2 \
    psycopg2-binary==2.9.9 \
    boto3==1.34.12 \
    scikit-learn==1.3.2

# Criar diretórios necessários
RUN mkdir -p /mlflow/artifacts /mlflow/backend

# Expor porta do MLFlow
EXPOSE 5000

# Comando para iniciar MLFlow Server
# Backend: PostgreSQL
# Artifact Store: MinIO/S3
CMD mlflow server \
    --host 0.0.0.0 \
    --port 5000 \
    --backend-store-uri postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB} \
    --default-artifact-root s3://${MLFLOW_S3_BUCKET}/ \
    --artifacts-destination s3://${MLFLOW_S3_BUCKET}/
