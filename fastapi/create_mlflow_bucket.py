"""
Script para criar bucket MLflow no MinIO
Execute dentro do container FastAPI que já tem boto3 instalado
"""

import boto3
from botocore.client import Config
import sys

# Configurações MinIO
MINIO_ENDPOINT = "http://minio:9000"
MINIO_ACCESS_KEY = "projeto_ml_admin"
MINIO_SECRET_KEY = "cavalo-nimbus-xbox"
BUCKET_NAME = "mlflow-artifacts"

def create_bucket():
    try:
        # Criar cliente S3 (MinIO)
        s3_client = boto3.client(
            's3',
            endpoint_url=MINIO_ENDPOINT,
            aws_access_key_id=MINIO_ACCESS_KEY,
            aws_secret_access_key=MINIO_SECRET_KEY,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1'
        )
        
        # Verificar se bucket já existe
        buckets = s3_client.list_buckets()
        bucket_names = [bucket['Name'] for bucket in buckets['Buckets']]
        
        if BUCKET_NAME in bucket_names:
            print(f"✅ Bucket '{BUCKET_NAME}' já existe")
        else:
            # Criar bucket
            s3_client.create_bucket(Bucket=BUCKET_NAME)
            print(f"✅ Bucket '{BUCKET_NAME}' criado com sucesso!")
        
        # Verificar acesso
        s3_client.head_bucket(Bucket=BUCKET_NAME)
        print(f"✅ Bucket '{BUCKET_NAME}' está acessível")
        
        # Configurar política pública (opcional, para testes)
        # Isso permite que o MLflow acesse os artifacts
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{BUCKET_NAME}/*"]
                }
            ]
        }
        
        import json
        try:
            s3_client.put_bucket_policy(
                Bucket=BUCKET_NAME,
                Policy=json.dumps(policy)
            )
            print(f"✅ Política de acesso configurada")
        except Exception as e:
            print(f"ℹ️ Política não configurada (não é crítico): {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar bucket: {e}")
        return False

if __name__ == "__main__":
    success = create_bucket()
    sys.exit(0 if success else 1)
