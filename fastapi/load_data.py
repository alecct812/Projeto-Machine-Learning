"""
Script de Carga Inicial do Dataset MovieLens
Envia todos os arquivos do dataset para o MinIO via API FastAPI
"""
import os
import requests
from pathlib import Path


# Configurações
FASTAPI_URL = "http://localhost:8000"
DATASET_PATH = "../archive/ml-100k"


def check_api_health():
    """Verifica se a API está funcionando"""
    try:
        response = requests.get(f"{FASTAPI_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ API Status:")
            print(f"   - Status: {data['status']}")
            print(f"   - MinIO Conectado: {data['minio_connected']}")
            print(f"   - Bucket Existe: {data['bucket_exists']}")
            return True
        else:
            print(f"❌ API retornou status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao conectar com a API: {e}")
        print("\n💡 Certifique-se de que o Docker Compose está rodando:")
        print("   docker-compose up -d")
        return False


def ingest_movielens_dataset():
    """Usa o endpoint de ingestão automática do MovieLens"""
    try:
        print("\n📤 Iniciando ingestão do dataset MovieLens...")
        response = requests.post(f"{FASTAPI_URL}/ingest/movielens", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ Ingestão concluída com sucesso!")
            print(f"   - Arquivos enviados: {data['uploaded_count']}")
            print(f"   - Erros: {data['error_count']}")
            
            if data['uploaded_files']:
                print("\n📁 Arquivos enviados:")
                for file_info in data['uploaded_files']:
                    size_kb = file_info['size'] / 1024
                    print(f"   - {file_info['filename']} → {file_info['object_key']} ({size_kb:.2f} KB)")
            
            if data.get('errors'):
                print("\n⚠️  Erros encontrados:")
                for error in data['errors']:
                    print(f"   - {error}")
            
            return True
        else:
            print(f"❌ Erro na ingestão: {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro durante ingestão: {e}")
        return False


def list_uploaded_files():
    """Lista arquivos que foram enviados para o MinIO"""
    try:
        print("\n📋 Listando arquivos no MinIO...")
        response = requests.get(f"{FASTAPI_URL}/files?prefix=movielens/", timeout=10)
        
        if response.status_code == 200:
            files = response.json()
            print(f"\n✅ Total de arquivos: {len(files)}")
            
            for file_info in files:
                size_kb = file_info['size'] / 1024
                print(f"   - {file_info['filename']} ({size_kb:.2f} KB) - {file_info['last_modified']}")
            
            return True
        else:
            print(f"❌ Erro ao listar arquivos: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao listar arquivos: {e}")
        return False


def main():
    """Função principal"""
    print("=" * 60)
    print("🎬 CARGA INICIAL - DATASET MOVIELENS")
    print("=" * 60)
    
    # 1. Verificar saúde da API
    if not check_api_health():
        print("\n❌ Não foi possível conectar com a API. Abortando.")
        return
    
    # 2. Fazer ingestão do dataset
    if not ingest_movielens_dataset():
        print("\n❌ Falha na ingestão do dataset.")
        return
    
    # 3. Listar arquivos enviados
    list_uploaded_files()
    
    print("\n" + "=" * 60)
    print("✅ PROCESSO CONCLUÍDO COM SUCESSO!")
    print("=" * 60)
    print("\n💡 Próximos passos:")
    print("   1. Acesse o console do MinIO: http://localhost:9001")
    print("      - User: minioadmin")
    print("      - Password: minioadmin123")
    print("   2. Visualize os arquivos no bucket 'movielens-data'")
    print("   3. Acesse a documentação da API: http://localhost:8000/docs")


if __name__ == "__main__":
    main()
