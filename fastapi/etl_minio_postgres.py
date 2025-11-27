"""
ETL Script: MinIO -> PostgreSQL
Extrai dados do MinIO e carrega no PostgreSQL de forma estruturada
"""

import io
import logging
from datetime import datetime
from typing import Dict, List
import pandas as pd

from minio_client import MinIOClient
from postgres_client import PostgreSQLClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MovieLensETL:
    """Pipeline ETL para transferir dados do MinIO para PostgreSQL"""
    
    def __init__(self):
        self.minio_client = MinIOClient()
        self.pg_client = PostgreSQLClient()
        self.stats = {
            "movies_inserted": 0,
            "users_inserted": 0,
            "ratings_inserted": 0,
            "errors": 0
        }
    
    def extract_from_minio(self, object_name: str) -> bytes:
        """
        Extrai dados de um arquivo no MinIO
        
        Args:
            object_name: Caminho do objeto no MinIO (ex: 'movielens/items/u.item')
            
        Returns:
            Bytes com os dados do arquivo
        """
        try:
            logger.info(f"Extraindo dados de {object_name}")
            
            # Download do objeto usando boto3 (s3_client)
            response = self.minio_client.s3_client.get_object(
                Bucket=self.minio_client.bucket_name,
                Key=object_name
            )
            
            # Ler conteúdo
            data = response['Body'].read()
            
            return data
            
        except Exception as e:
            logger.error(f"Erro ao extrair dados de {object_name}: {e}")
            raise
    
    def load_movies(self) -> int:
        """
        Carrega filmes do MinIO para PostgreSQL
        
        Returns:
            Número de filmes inseridos
        """
        try:
            logger.info("Iniciando carga de filmes...")
            
            # Extrair dados
            data = self.extract_from_minio("movielens/items/u.item")
            
            # Parsear arquivo u.item (separado por |)
            # Formato: movie id | movie title | release date | video release date | IMDb URL | 19 gêneros
            lines = data.decode('latin-1').strip().split('\n')
            
            movies_data = []
            genre_columns = [
                'unknown', 'action', 'adventure', 'animation', 'childrens',
                'comedy', 'crime', 'documentary', 'drama', 'fantasy',
                'film_noir', 'horror', 'musical', 'mystery', 'romance',
                'sci_fi', 'thriller', 'war', 'western'
            ]
            
            for line in lines:
                parts = line.split('|')
                if len(parts) >= 24:  # 5 campos + 19 gêneros
                    movie_id = int(parts[0])
                    title = parts[1]
                    release_date_str = parts[2]
                    video_release_str = parts[3]
                    imdb_url = parts[4]
                    
                    # Converter datas
                    release_date = None
                    if release_date_str:
                        try:
                            release_date = datetime.strptime(release_date_str, '%d-%b-%Y').date()
                        except:
                            pass
                    
                    video_release_date = None
                    if video_release_str:
                        try:
                            video_release_date = datetime.strptime(video_release_str, '%d-%b-%Y').date()
                        except:
                            pass
                    
                    # Gêneros (últimos 19 campos)
                    genres = {genre: bool(int(parts[5 + i])) for i, genre in enumerate(genre_columns)}
                    
                    movie_data = {
                        'movie_id': movie_id,
                        'title': title,
                        'release_date': release_date,
                        'video_release_date': video_release_date,
                        'imdb_url': imdb_url if imdb_url else None,
                        **genres
                    }
                    
                    movies_data.append(movie_data)
            
            # Inserir no PostgreSQL em batch
            logger.info(f"Inserindo {len(movies_data)} filmes no PostgreSQL...")
            inserted = 0
            for movie in movies_data:
                try:
                    self.pg_client.insert_movie(movie)
                    inserted += 1
                except Exception as e:
                    logger.error(f"Erro ao inserir filme {movie['movie_id']}: {e}")
                    self.stats["errors"] += 1
            
            self.stats["movies_inserted"] = inserted
            logger.info(f"✓ {inserted} filmes inseridos com sucesso")
            return inserted
            
        except Exception as e:
            logger.error(f"Erro ao carregar filmes: {e}")
            raise
    
    def load_users(self) -> int:
        """
        Carrega usuários do MinIO para PostgreSQL
        
        Returns:
            Número de usuários inseridos
        """
        try:
            logger.info("Iniciando carga de usuários...")
            
            # Extrair dados
            data = self.extract_from_minio("movielens/users/u.user")
            
            # Parsear arquivo u.user (separado por |)
            # Formato: user id | age | gender | occupation | zip code
            lines = data.decode('latin-1').strip().split('\n')
            
            users_data = []
            for line in lines:
                parts = line.split('|')
                if len(parts) >= 5:
                    user_id = int(parts[0])
                    age = int(parts[1])
                    gender = parts[2]
                    occupation = parts[3]
                    zip_code = parts[4]
                    
                    user_data = {
                        'user_id': user_id,
                        'age': age,
                        'gender': gender,
                        'occupation': occupation,
                        'zip_code': zip_code
                    }
                    
                    users_data.append(user_data)
            
            # Inserir no PostgreSQL
            logger.info(f"Inserindo {len(users_data)} usuários no PostgreSQL...")
            inserted = 0
            for user in users_data:
                try:
                    self.pg_client.insert_user(user)
                    inserted += 1
                except Exception as e:
                    logger.error(f"Erro ao inserir usuário {user['user_id']}: {e}")
                    self.stats["errors"] += 1
            
            self.stats["users_inserted"] = inserted
            logger.info(f"✓ {inserted} usuários inseridos com sucesso")
            return inserted
            
        except Exception as e:
            logger.error(f"Erro ao carregar usuários: {e}")
            raise
    
    def load_ratings(self, batch_size: int = 1000) -> int:
        """
        Carrega avaliações do MinIO para PostgreSQL
        
        Args:
            batch_size: Tamanho do batch para inserção
            
        Returns:
            Número de avaliações inseridas
        """
        try:
            logger.info("Iniciando carga de avaliações...")
            
            # Extrair dados
            data = self.extract_from_minio("movielens/ratings/u.data")
            
            # Parsear arquivo u.data (separado por tab)
            # Formato: user id | item id | rating | timestamp
            lines = data.decode('latin-1').strip().split('\n')
            
            ratings_data = []
            for line in lines:
                parts = line.split('\t')
                if len(parts) >= 4:
                    user_id = int(parts[0])
                    movie_id = int(parts[1])
                    rating = int(parts[2])
                    timestamp = int(parts[3])
                    
                    # Converter timestamp Unix para datetime
                    rated_at = datetime.fromtimestamp(timestamp)
                    
                    rating_data = {
                        'user_id': user_id,
                        'movie_id': movie_id,
                        'rating': rating,
                        'timestamp': timestamp,
                        'rated_at': rated_at
                    }
                    
                    ratings_data.append(rating_data)
            
            # Inserir em batches (usando o novo método batch)
            total_ratings = len(ratings_data)
            logger.info(f"Inserindo {total_ratings} avaliações no PostgreSQL em batches...")
            
            inserted = 0
            for i in range(0, total_ratings, batch_size):
                batch = ratings_data[i:i + batch_size]
                try:
                    batch_inserted = self.pg_client.insert_ratings_batch(batch)
                    inserted += batch_inserted
                except Exception as e:
                    logger.error(f"Erro ao inserir batch: {e}")
                    self.stats["errors"] += 1
                
                # Log de progresso
                if (i + batch_size) % (batch_size * 10) == 0 or (i + batch_size) >= total_ratings:
                    logger.info(f"Progresso: {min(i + batch_size, total_ratings)}/{total_ratings} ratings processados")
            
            self.stats["ratings_inserted"] = inserted
            logger.info(f"✓ {inserted} avaliações inseridas com sucesso")
            return inserted
            
        except Exception as e:
            logger.error(f"Erro ao carregar ratings: {e}")
            raise
    
    def run_full_etl(self) -> Dict:
        """
        Executa o pipeline ETL completo
        
        Returns:
            Dicionário com estatísticas da execução
        """
        start_time = datetime.now()
        logger.info("="*60)
        logger.info("Iniciando ETL: MinIO -> PostgreSQL")
        logger.info("="*60)
        
        try:
            # Verificar conexões
            if not self.minio_client.check_connection():
                raise Exception("MinIO não está conectado")
            
            if not self.pg_client.check_connection():
                raise Exception("PostgreSQL não está conectado")
            
            # 1. Carregar filmes
            self.load_movies()
            
            # 2. Carregar usuários
            self.load_users()
            
            # 3. Carregar avaliações
            self.load_ratings()
            
            # Calcular tempo de execução
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Estatísticas finais
            self.stats["duration_seconds"] = duration
            self.stats["status"] = "success"
            
            logger.info("="*60)
            logger.info("ETL CONCLUÍDO COM SUCESSO!")
            logger.info(f"Filmes inseridos: {self.stats['movies_inserted']}")
            logger.info(f"Usuários inseridos: {self.stats['users_inserted']}")
            logger.info(f"Avaliações inseridas: {self.stats['ratings_inserted']}")
            logger.info(f"Erros: {self.stats['errors']}")
            logger.info(f"Tempo de execução: {duration:.2f}s")
            logger.info("="*60)
            
            return self.stats
            
        except Exception as e:
            logger.error(f"ERRO NO ETL: {e}")
            self.stats["status"] = "failed"
            self.stats["error_message"] = str(e)
            raise
    
    def get_summary(self) -> Dict:
        """Retorna sumário dos dados no PostgreSQL"""
        try:
            table_info = self.pg_client.get_table_info()
            return {
                "tables": table_info,
                "total_movies": table_info.get("movies", 0),
                "total_users": table_info.get("users", 0),
                "total_ratings": table_info.get("ratings", 0),
                "total_clusters": table_info.get("user_clusters", 0)
            }
        except Exception as e:
            logger.error(f"Erro ao obter sumário: {e}")
            return {}


def main():
    """Função principal para execução do ETL via CLI"""
    etl = MovieLensETL()
    
    try:
        # Executar ETL completo
        stats = etl.run_full_etl()
        
        # Exibir sumário
        print("\n📊 SUMÁRIO DO BANCO DE DADOS:")
        summary = etl.get_summary()
        for key, value in summary.items():
            print(f"  {key}: {value}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Falha na execução do ETL: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
