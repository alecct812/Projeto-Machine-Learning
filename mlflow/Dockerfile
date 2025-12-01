# Dockerfile customizado para MLflow com suporte a PostgreSQL e MinIO

FROM python:3.10-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar MLflow e dependências
RUN pip install --no-cache-dir \
    mlflow==2.9.2 \
    psycopg2-binary==2.9.9 \
    boto3==1.29.7 \
    botocore==1.32.7 \
    sqlalchemy==2.0.23 \
    protobuf==4.25.1

# Criar diretório de trabalho
WORKDIR /mlflow

# Expor porta do servidor MLflow
EXPOSE 5000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Comando padrão será sobrescrito pelo docker-compose
CMD ["mlflow", "server", "--host", "0.0.0.0", "--port", "5000"]
