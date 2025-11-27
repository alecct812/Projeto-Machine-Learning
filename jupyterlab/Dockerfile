# Dockerfile para JupyterLab
# Ambiente de análise e modelagem de Machine Learning

FROM python:3.11-slim

LABEL maintainer="CESAR School - Aprendizado de Máquina 2025.2"
LABEL description="JupyterLab para análise e modelagem do MovieLens"

# Definir diretório de trabalho
WORKDIR /workspace

# Atualizar sistema e instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar pacotes Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Criar diretório para notebooks
RUN mkdir -p /workspace/notebooks /workspace/data /workspace/models

# Expor porta do JupyterLab
EXPOSE 8888

# Comando para iniciar JupyterLab
CMD ["jupyter", "lab", \
     "--ip=0.0.0.0", \
     "--port=8888", \
     "--no-browser", \
     "--allow-root", \
     "--NotebookApp.token=''", \
     "--NotebookApp.password=''", \
     "--ServerApp.root_dir=/workspace"]
