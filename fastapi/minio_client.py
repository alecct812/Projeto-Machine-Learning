"""
Cliente MinIO para gerenciamento de armazenamento de objetos
Compatível com API S3
"""
import os
from typing import Optional, List
import io

import boto3
from botocore.exceptions import ClientError
from botocore.client import Config


class MinIOClient:
    """Cliente para interação com MinIO (compatível com S3)"""
    
    def __init__(self):
        """Inicializa o cliente MinIO com variáveis de ambiente"""
        self.endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
        self.bucket_name = os.getenv("MINIO_BUCKET", "movielens-data")
        
        # Configurar cliente S3 para usar MinIO
        self.s3_client = boto3.client(
            's3',
            endpoint_url=f'http://{self.endpoint}',
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1'
        )
    
    def check_connection(self) -> bool:
        """
        Verifica se a conexão com MinIO está funcionando
        
        Returns:
            True se conectado, False caso contrário
        """
        try:
            self.s3_client.list_buckets()
            return True
        except Exception as e:
            print(f"❌ Erro ao conectar com MinIO: {e}")
            return False
    
    def bucket_exists(self) -> bool:
        """
        Verifica se o bucket existe
        
        Returns:
            True se o bucket existe, False caso contrário
        """
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True
        except ClientError:
            return False
    
    def create_bucket_if_not_exists(self) -> bool:
        """
        Cria o bucket se ele não existir
        
        Returns:
            True se bucket foi criado ou já existe, False em caso de erro
        """
        try:
            if not self.bucket_exists():
                self.s3_client.create_bucket(Bucket=self.bucket_name)
                print(f"✅ Bucket '{self.bucket_name}' criado com sucesso!")
            else:
                print(f"ℹ️  Bucket '{self.bucket_name}' já existe")
            return True
        except ClientError as e:
            print(f"❌ Erro ao criar bucket: {e}")
            return False
    
    def upload_file(
        self,
        file_data: bytes,
        object_name: str,
        content_type: str = "application/octet-stream"
    ) -> bool:
        """
        Faz upload de um arquivo para o MinIO
        
        Args:
            file_data: Dados do arquivo em bytes
            object_name: Nome/caminho do objeto no bucket
            content_type: Tipo de conteúdo do arquivo
        
        Returns:
            True se upload bem-sucedido, False caso contrário
        """
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_name,
                Body=file_data,
                ContentType=content_type
            )
            print(f"✅ Upload realizado: {object_name}")
            return True
        except ClientError as e:
            print(f"❌ Erro ao fazer upload de {object_name}: {e}")
            return False
    
    def download_file(self, object_name: str) -> Optional[bytes]:
        """
        Baixa um arquivo do MinIO
        
        Args:
            object_name: Nome/caminho do objeto no bucket
        
        Returns:
            Dados do arquivo em bytes ou None se não encontrado
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=object_name
            )
            return response['Body'].read()
        except ClientError as e:
            print(f"❌ Erro ao baixar {object_name}: {e}")
            return None
    
    def list_objects(self, prefix: str = "") -> List:
        """
        Lista objetos no bucket
        
        Args:
            prefix: Prefixo para filtrar objetos (pasta)
        
        Returns:
            Lista de objetos
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' in response:
                return response['Contents']
            return []
        except ClientError as e:
            print(f"❌ Erro ao listar objetos: {e}")
            return []
    
    def delete_file(self, object_name: str) -> bool:
        """
        Remove um arquivo do MinIO
        
        Args:
            object_name: Nome/caminho do objeto no bucket
        
        Returns:
            True se removido com sucesso, False caso contrário
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_name
            )
            print(f"✅ Arquivo removido: {object_name}")
            return True
        except ClientError as e:
            print(f"❌ Erro ao remover {object_name}: {e}")
            return False
    
    def get_object_metadata(self, object_name: str) -> Optional[dict]:
        """
        Obtém metadados de um objeto
        
        Args:
            object_name: Nome/caminho do objeto no bucket
        
        Returns:
            Dicionário com metadados ou None se não encontrado
        """
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=object_name
            )
            return {
                'size': response['ContentLength'],
                'last_modified': response['LastModified'],
                'content_type': response.get('ContentType', 'unknown'),
                'etag': response['ETag']
            }
        except ClientError as e:
            print(f"❌ Erro ao obter metadados de {object_name}: {e}")
            return None
