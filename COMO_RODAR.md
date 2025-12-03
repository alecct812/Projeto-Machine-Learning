# 🚀 GUIA RÁPIDO - Como Rodar o Projeto

## ✅ Pré-requisitos
- Docker Desktop instalado e rodando
- Os dados do MovieLens já estão na pasta `archive/ml-100k/` ✅

---

## 📋 Passo a Passo para Rodar

### 1️⃣ Subir todos os containers

```bash
cd /Users/Pedro/.cursor/worktrees/Projeto-Machine-Learning/ocw
docker-compose up -d
```

**Aguarde** 30-60 segundos para os serviços iniciarem.

### 2️⃣ Verificar se os containers estão rodando

```bash
docker-compose ps
```

Você deve ver 5 containers rodando:
- ✅ `movielens_minio` (porta 9000, 9001)
- ✅ `movielens_postgres` (porta 5438)
- ✅ `movielens_fastapi` (porta 8000)
- ✅ `movielens_mlflow` (porta 5001)
- ✅ `movielens_thingsboard` (porta 9090)

### 3️⃣ Carregar os dados no MinIO

```bash
docker-compose exec fastapi python load_data.py
```

### 4️⃣ Transferir dados para o PostgreSQL

```bash
docker-compose exec fastapi python etl_minio_postgres.py
```

### 5️⃣ Criar o bucket do MLflow no MinIO

```bash
docker-compose exec fastapi python create_mlflow_bucket.py
```

### 6️⃣ Sincronizar dados com ThingsBoard

```bash
# Aguardar ThingsBoard inicializar (3-5 minutos)
./verificar_thingsboard.sh

# OU manualmente:
docker-compose exec fastapi python sync_telemetry_only.py
```

---

## 🌐 Acessar os Serviços

| Serviço | URL | Credenciais |
|---------|-----|-------------|
| **FastAPI (Swagger)** | http://localhost:8000/docs | - |
| **MinIO Console** | http://localhost:9001 | User: `projeto_ml_admin`<br>Password: `cavalo-nimbus-xbox` |
| **PostgreSQL** | `localhost:5438` | User: `ml_user`<br>Password: `ml_password_2025`<br>Database: `movielens` |
| **MLflow** | http://localhost:5001 | - |
| **ThingsBoard** | http://localhost:9090 | User: `tenant@thingsboard.org`<br>Password: `tenant` |

---

## 🛑 Para Parar os Containers

```bash
docker-compose down
```

**Para parar E remover todos os dados:**

```bash
docker-compose down -v
```

---

## ✅ Checklist de Verificação

- [ ] Todos os 5 containers estão rodando
- [ ] FastAPI responde: http://localhost:8000/health
- [ ] MinIO Console abre: http://localhost:9001
- [ ] MLflow abre: http://localhost:5001
- [ ] ThingsBoard abre: http://localhost:9090
- [ ] Dados carregados no MinIO
- [ ] Dados carregados no PostgreSQL
- [ ] Dados sincronizados no ThingsBoard

---

**Autor:** Sistema de Recomendação MovieLens  
**Disciplina:** Aprendizado de Máquina - 2025.2  
**Instituição:** CESAR School

