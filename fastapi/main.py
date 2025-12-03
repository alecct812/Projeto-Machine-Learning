"""
FastAPI - Sistema de Ingestão de Dados MovieLens
Parte do pipeline de ML para Sistema de Recomendação de Filmes
"""
import os
from typing import List, Optional
from datetime import datetime
import io

from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse
import boto3
from botocore.exceptions import ClientError
import pandas as pd
from pydantic import BaseModel

from minio_client import MinIOClient
from postgres_client import PostgreSQLClient
from etl_minio_postgres import MovieLensETL
from thingsboard_client import ThingsBoardClient

from contextlib import asynccontextmanager

# Inicializar clientes
minio_client = MinIOClient()
pg_client = None  # Será inicializado no startup

def get_pg_client():
    """
    Retorna o cliente PostgreSQL, tentando inicializar se necessário
    """
    global pg_client
    if pg_client is None:
        try:
            pg_client = PostgreSQLClient()
            if not pg_client.check_connection():
                print(f"⚠️ Tentativa de conexão PostgreSQL falhou")
                pg_client = None
            else:
                print(f"✅ Conexão PostgreSQL restabelecida com sucesso!")
        except Exception as e:
            print(f"⚠️ Erro ao reconectar PostgreSQL: {e}")
            pg_client = None
    
    return pg_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa o bucket do MinIO e conexão PostgreSQL na inicialização da aplicação"""
    global pg_client
    
    # MinIO
    minio_client.create_bucket_if_not_exists()
    print(f"✅ Bucket '{minio_client.bucket_name}' verificado/criado com sucesso!")
    
    # PostgreSQL - tentar conectar, mas não falhar se o banco não estiver pronto
    get_pg_client()
    
    yield
    
    # Clean up (se necessário)
    if pg_client:
        pg_client.close()

# Modelos Pydantic
class HealthResponse(BaseModel):
    status: str
    minio_connected: bool
    bucket_exists: bool
    postgres_connected: bool
    timestamp: str


class FileInfo(BaseModel):
    filename: str
    size: int
    last_modified: str
    content_type: str


class UploadResponse(BaseModel):
    message: str
    filename: str
    size: int
    bucket: str
    object_key: str


# Inicializar FastAPI
app = FastAPI(
    title="MovieLens Data Ingestion API",
    description="API para ingestão de dados do dataset MovieLens no MinIO/S3 e PostgreSQL",
    version="2.0.0",
    lifespan=lifespan
)


@app.get("/", tags=["Root"])
async def root():
    """Endpoint raiz da API"""
    return {
        "message": "MovieLens Data Ingestion API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "upload": "/upload",
            "files": "/files",
            "download": "/download/{filename}"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Verifica a saúde da API e conexão com MinIO e PostgreSQL"""
    minio_connected = minio_client.check_connection()
    bucket_exists = minio_client.bucket_exists()
    postgres_connected = pg_client.check_connection() if pg_client else False
    
    return HealthResponse(
        status="healthy" if (minio_connected and bucket_exists and postgres_connected) else "partial",
        minio_connected=minio_connected,
        bucket_exists=bucket_exists,
        postgres_connected=postgres_connected,
        timestamp=datetime.utcnow().isoformat() 
    )


@app.post("/upload", response_model=UploadResponse, tags=["Data Ingestion"])
async def upload_file(
    file: UploadFile = File(...),
    folder: Optional[str] = "raw"
):
    """
    Upload de arquivo para o MinIO
    
    Args:
        file: Arquivo a ser enviado
        folder: Pasta dentro do bucket (default: 'raw')
    
    Returns:
        Informações sobre o arquivo enviado
    """
    try:
        # Ler conteúdo do arquivo
        contents = await file.read()
        file_size = len(contents)
        
        # Definir chave do objeto (caminho no bucket)
        object_key = f"{folder}/{file.filename}"
        
        # Upload para MinIO
        success = minio_client.upload_file(
            file_data=contents,
            object_name=object_key,
            content_type=file.content_type or "application/octet-stream"
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Falha ao fazer upload do arquivo para MinIO"
            )
        
        return UploadResponse(
            message="Arquivo enviado com sucesso!",
            filename=file.filename,
            size=file_size,
            bucket=minio_client.bucket_name,
            object_key=object_key
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar upload: {str(e)}"
        )


@app.get("/files", response_model=List[FileInfo], tags=["Data Management"])
async def list_files(prefix: Optional[str] = ""):
    """
    Lista arquivos no bucket do MinIO
    
    Args:
        prefix: Filtro de prefixo (pasta) para listar arquivos
    
    Returns:
        Lista de arquivos no bucket
    """
    try:
        objects = minio_client.list_objects(prefix=prefix)
        
        files = []
        for obj in objects:
            files.append(FileInfo(
                filename=obj['Key'],
                size=obj['Size'],
                last_modified=obj['LastModified'].isoformat(),
                content_type=obj.get('ContentType', 'unknown')
            ))
        
        return files
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar arquivos: {str(e)}"
        )


@app.get("/download/{file_path:path}", tags=["Data Management"])
async def download_file(file_path: str):
    """
    Download de arquivo do MinIO
    
    Args:
        file_path: Caminho do arquivo no bucket
    
    Returns:
        Arquivo solicitado
    """
    try:
        file_data = minio_client.download_file(file_path)
        
        if file_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Arquivo '{file_path}' não encontrado"
            )
        
        return JSONResponse(
            content={
                "filename": file_path,
                "size": len(file_data),
                "message": "Arquivo baixado com sucesso"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao baixar arquivo: {str(e)}"
        )


@app.delete("/files/{file_path:path}", tags=["Data Management"])
async def delete_file(file_path: str):
    """
    Remove arquivo do MinIO
    
    Args:
        file_path: Caminho do arquivo no bucket
    
    Returns:
        Confirmação de remoção
    """
    try:
        success = minio_client.delete_file(file_path)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Arquivo '{file_path}' não encontrado"
            )
        
        return {
            "message": f"Arquivo '{file_path}' removido com sucesso",
            "deleted": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao remover arquivo: {str(e)}"
        )


@app.post("/ingest/movielens", tags=["Data Ingestion"])
async def ingest_movielens_dataset():
    """
    Ingere o dataset MovieLens completo do diretório /data/archive para o MinIO
    
    Este endpoint lê todos os arquivos do dataset e os envia para o MinIO
    organizados por tipo (ratings, users, items, etc.)
    """
    try:
        archive_path = "/data/archive/ml-100k"
        
        if not os.path.exists(archive_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Diretório do dataset não encontrado: {archive_path}"
            )
        
        uploaded_files = []
        errors = []
        
        # Arquivos principais do MovieLens
        # Nota: usando ua.base (80% dos dados) em vez de u.data
        files_to_upload = {
            "ua.base": "ratings/u.data",  # Renomeando para u.data para compatibilidade
            "u.user": "users/u.user",
            "u.item": "items/u.item",
            "u.genre": "metadata/u.genre",
            "u.occupation": "metadata/u.occupation",
            "u.info": "metadata/u.info"
        }
        
        for filename, object_key in files_to_upload.items():
            file_path = os.path.join(archive_path, filename)
            
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'rb') as f:
                        file_data = f.read()
                    
                    success = minio_client.upload_file(
                        file_data=file_data,
                        object_name=f"movielens/{object_key}",
                        content_type="text/plain"
                    )
                    
                    if success:
                        uploaded_files.append({
                            "filename": filename,
                            "object_key": f"movielens/{object_key}",
                            "size": len(file_data)
                        })
                    else:
                        errors.append(f"Falha ao enviar {filename}")
                        
                except Exception as e:
                    errors.append(f"Erro ao processar {filename}: {str(e)}")
            else:
                errors.append(f"Arquivo não encontrado: {filename}")
        
        return {
            "message": "Ingestão do dataset MovieLens concluída",
            "uploaded_count": len(uploaded_files),
            "error_count": len(errors),
            "uploaded_files": uploaded_files,
            "errors": errors if errors else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro durante ingestão: {str(e)}"
        )


# ====================================================================
# ENDPOINTS POSTGRESQL (PARTE 2)
# ====================================================================

@app.get("/postgres/health", tags=["PostgreSQL"])
async def postgres_health():
    """Verifica conexão com PostgreSQL"""
    client = get_pg_client()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cliente PostgreSQL não inicializado"
        )
    
    connected = client.check_connection()
    
    return {
        "postgres_connected": connected,
        "status": "healthy" if connected else "unhealthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/postgres/tables", tags=["PostgreSQL"])
async def get_postgres_tables():
    """Lista todas as tabelas do banco de dados"""
    client = get_pg_client()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cliente PostgreSQL não inicializado"
        )
    
    try:
        tables = client.get_tables()
        table_info = client.get_table_info()
        
        return {
            "total_tables": len(tables),
            "tables": tables,
            "table_counts": table_info
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar tabelas: {str(e)}"
        )


@app.get("/postgres/summary", tags=["PostgreSQL"])
async def get_database_summary():
    """Retorna sumário completo do banco de dados"""
    client = get_pg_client()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cliente PostgreSQL não inicializado"
        )
    
    try:
        table_info = client.get_table_info()
        
        return {
            "database": "movielens",
            "tables": table_info,
            "summary": {
                "total_movies": table_info.get("movies", 0),
                "total_users": table_info.get("users", 0),
                "total_ratings": table_info.get("ratings", 0),
                "total_user_clusters": table_info.get("user_clusters", 0),
                "total_movie_similarities": table_info.get("movie_similarities", 0),
                "total_recommendations": table_info.get("recommendations", 0)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter sumário: {str(e)}"
        )


@app.post("/etl/run", tags=["ETL"])
async def run_etl_pipeline():
    """
    Executa o pipeline ETL completo: MinIO -> PostgreSQL
    
    Este endpoint:
    1. Extrai dados do MinIO (u.data, u.user, u.item)
    2. Transforma os dados para o formato do banco
    3. Carrega no PostgreSQL (movies, users, ratings)
    """
    client = get_pg_client()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cliente PostgreSQL não inicializado"
        )
    
    try:
        # Executar ETL
        etl = MovieLensETL()
        stats = etl.run_full_etl()
        
        return {
            "message": "ETL executado com sucesso!",
            "status": stats.get("status", "unknown"),
            "statistics": {
                "movies_inserted": stats.get("movies_inserted", 0),
                "users_inserted": stats.get("users_inserted", 0),
                "ratings_inserted": stats.get("ratings_inserted", 0),
                "errors": stats.get("errors", 0),
                "duration_seconds": stats.get("duration_seconds", 0)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao executar ETL: {str(e)}"
        )


@app.get("/postgres/stats/movies", tags=["Statistics"])
async def get_movie_statistics():
    """Retorna estatísticas sobre filmes"""
    client = get_pg_client()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cliente PostgreSQL não inicializado"
        )
    
    try:
        query = "SELECT * FROM movie_stats LIMIT 20"
        results = client.execute_query(query)
        
        return {
            "total_results": len(results),
            "movies": results
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter estatísticas: {str(e)}"
        )


@app.get("/postgres/stats/users", tags=["Statistics"])
async def get_user_statistics():
    """Retorna estatísticas sobre usuários"""
    client = get_pg_client()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cliente PostgreSQL não inicializado"
        )
    
    try:
        query = "SELECT * FROM user_stats LIMIT 20"
        results = client.execute_query(query)
        
        return {
            "total_results": len(results),
            "users": results
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter estatísticas: {str(e)}"
        )


@app.get("/postgres/top-movies", tags=["Statistics"])
async def get_top_movies(limit: int = 10):
    """Retorna os filmes mais bem avaliados"""
    client = get_pg_client()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cliente PostgreSQL não inicializado"
        )
    
    try:
        query = f"SELECT * FROM top_movies LIMIT {limit}"
        results = client.execute_query(query)
        
        return {
            "total_results": len(results),
            "top_movies": results
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter top filmes: {str(e)}"
        )


# ====================================================================
# ENDPOINTS THINGSBOARD (PARTE 5)
# ====================================================================

@app.post("/thingsboard/sync", tags=["ThingsBoard"])
async def sync_thingsboard():
    """
    Sincroniza todos os dados com o ThingsBoard
    
    Este endpoint:
    1. Envia métricas dos modelos ML
    2. Envia estatísticas do dataset
    3. Envia top filmes mais bem avaliados
    
    O ThingsBoard deve estar rodando em: http://thingsboard:9090
    """
    try:
        client = ThingsBoardClient()
        results = client.sync_all()
        
        if not results.get("authenticated"):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Não foi possível autenticar no ThingsBoard"
            )
        
        success_count = sum(1 for k, v in results.items() if k != "authenticated" and v)
        total_count = len(results) - 1
        
        return {
            "message": "Sincronização com ThingsBoard concluída",
            "status": "success" if success_count == total_count else "partial",
            "results": results,
            "success_rate": f"{success_count}/{total_count}",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao sincronizar com ThingsBoard: {str(e)}"
        )


@app.get("/thingsboard/health", tags=["ThingsBoard"])
async def thingsboard_health():
    """Verifica conexão com ThingsBoard"""
    try:
        import requests
        
        tb_url = "http://thingsboard:9090/api/noauth/health"
        response = requests.get(tb_url, timeout=5)
        
        return {
            "thingsboard_available": response.status_code == 200,
            "status": "healthy" if response.status_code == 200 else "unhealthy",
            "url": tb_url,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "thingsboard_available": False,
            "status": "unreachable",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
