"""
ETL PostgreSQL → ThingsBoard
Envia dados do sistema de recomendação MovieLens para o ThingsBoard
"""
import os
import sys
import time
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor

# Importar cliente ThingsBoard
from thingsboard_client import ThingsBoardClient

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PostgreSQLToThingsBoard:
    """ETL de dados do PostgreSQL para ThingsBoard"""
    
    def __init__(self):
        """Inicializa conexões com PostgreSQL e ThingsBoard"""
        # Configuração PostgreSQL
        self.pg_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', 5438)),
            'database': os.getenv('POSTGRES_DB', 'movielens'),
            'user': os.getenv('POSTGRES_USER', 'ml_user'),
            'password': os.getenv('POSTGRES_PASSWORD', 'ml_password_2025')
        }
        
        # Cliente ThingsBoard
        self.tb_client = ThingsBoardClient(
            base_url=os.getenv('THINGSBOARD_URL', 'http://thingsboard:9090')
        )
        
        self.conn = None
    
    def connect_postgres(self) -> bool:
        """Conecta ao PostgreSQL"""
        try:
            self.conn = psycopg2.connect(**self.pg_config)
            logger.info("✅ Conectado ao PostgreSQL")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao conectar PostgreSQL: {e}")
            return False
    
    def close_postgres(self):
        """Fecha conexão com PostgreSQL"""
        if self.conn:
            self.conn.close()
            logger.info("Conexão PostgreSQL fechada")
    
    def get_system_stats(self) -> Optional[Dict[str, Any]]:
        """Obtém estatísticas gerais do sistema"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Total de usuários
                cur.execute("SELECT COUNT(*) as total FROM users")
                total_users = cur.fetchone()['total']
                
                # Total de filmes
                cur.execute("SELECT COUNT(*) as total FROM movies")
                total_movies = cur.fetchone()['total']
                
                # Total de ratings
                cur.execute("SELECT COUNT(*) as total FROM ratings")
                total_ratings = cur.fetchone()['total']
                
                # Média geral de ratings
                cur.execute("SELECT AVG(rating) as avg_rating FROM ratings")
                avg_rating = float(cur.fetchone()['avg_rating'] or 0)
                
                # Rating mais recente
                cur.execute("""
                    SELECT MAX(timestamp) as last_rating 
                    FROM ratings
                """)
                last_rating = cur.fetchone()['last_rating']
                
                stats = {
                    "total_users": total_users,
                    "total_movies": total_movies,
                    "total_ratings": total_ratings,
                    "avg_rating": round(avg_rating, 2),
                    "last_rating_timestamp": last_rating or 0
                }
                
                logger.info(f"📊 Estatísticas do sistema obtidas: {stats}")
                return stats
                
        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas: {e}")
            return None
    
    def get_ml_metrics(self) -> Optional[Dict[str, Any]]:
        """Obtém métricas dos modelos de ML"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Total de clusters
                cur.execute("""
                    SELECT COUNT(DISTINCT cluster_number) as num_clusters 
                    FROM user_clusters
                """)
                result = cur.fetchone()
                num_clusters = result['num_clusters'] if result else 0
                
                # Total de recomendações geradas
                cur.execute("SELECT COUNT(*) as total FROM recommendations")
                result = cur.fetchone()
                total_recommendations = result['total'] if result else 0
                
                # Média de similaridade
                cur.execute("""
                    SELECT AVG(similarity_score) as avg_similarity 
                    FROM movie_similarities
                    WHERE similarity_score > 0
                """)
                result = cur.fetchone()
                avg_similarity = float(result['avg_similarity'] or 0) if result else 0
                
                metrics = {
                    "num_clusters": num_clusters,
                    "total_recommendations": total_recommendations,
                    "avg_similarity_score": round(avg_similarity, 4)
                }
                
                logger.info(f"🔬 Métricas ML obtidas: {metrics}")
                return metrics
                
        except Exception as e:
            logger.error(f"❌ Erro ao obter métricas ML: {e}")
            return None
    
    def get_top_movies(self, limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """Obtém os top N filmes mais bem avaliados"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        m.movie_id,
                        m.title,
                        COUNT(r.rating_id) as num_ratings,
                        AVG(r.rating) as avg_rating,
                        MAX(r.rating) as max_rating,
                        MIN(r.rating) as min_rating
                    FROM movies m
                    JOIN ratings r ON m.movie_id = r.movie_id
                    GROUP BY m.movie_id, m.title
                    HAVING COUNT(r.rating_id) >= 10
                    ORDER BY avg_rating DESC, num_ratings DESC
                    LIMIT %s
                """, (limit,))
                
                movies = cur.fetchall()
                
                # Converter para lista de dicts
                result = []
                for movie in movies:
                    result.append({
                        "movie_id": movie['movie_id'],
                        "title": movie['title'],
                        "num_ratings": movie['num_ratings'],
                        "avg_rating": float(movie['avg_rating']),
                        "max_rating": movie['max_rating'],
                        "min_rating": movie['min_rating']
                    })
                
                logger.info(f"🎬 Top {limit} filmes obtidos")
                return result
                
        except Exception as e:
            logger.error(f"❌ Erro ao obter top movies: {e}")
            return None
    
    def get_cluster_distribution(self) -> Optional[Dict[int, int]]:
        """Obtém distribuição de usuários por cluster"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        cluster_number,
                        COUNT(*) as num_users
                    FROM user_clusters
                    GROUP BY cluster_number
                    ORDER BY cluster_number
                """)
                
                clusters = cur.fetchall()
                
                distribution = {
                    row['cluster_number']: row['num_users']
                    for row in clusters
                }
                
                logger.info(f"📊 Distribuição de clusters obtida: {distribution}")
                return distribution
                
        except Exception as e:
            logger.error(f"❌ Erro ao obter distribuição de clusters: {e}")
            return None
    
    def send_all_data_to_thingsboard(self):
        """Envia todos os dados para ThingsBoard"""
        logger.info("=" * 60)
        logger.info("🚀 Iniciando ETL PostgreSQL → ThingsBoard")
        logger.info("=" * 60)
        
        # Conectar ao PostgreSQL
        if not self.connect_postgres():
            logger.error("Falha ao conectar ao PostgreSQL")
            return False
        
        # Login no ThingsBoard
        if not self.tb_client.login():
            logger.error("Falha ao fazer login no ThingsBoard")
            self.close_postgres()
            return False
        
        try:
            # 1. Enviar estatísticas do sistema
            logger.info("\n📊 Enviando estatísticas do sistema...")
            stats = self.get_system_stats()
            if stats:
                self.tb_client.send_ml_metrics("movielens_system", stats)
            
            # 2. Enviar métricas de ML
            logger.info("\n🔬 Enviando métricas de ML...")
            ml_metrics = self.get_ml_metrics()
            if ml_metrics:
                self.tb_client.send_ml_metrics("ml_model_metrics", ml_metrics)
            
            # 3. Enviar distribuição de clusters
            logger.info("\n📊 Enviando distribuição de clusters...")
            cluster_dist = self.get_cluster_distribution()
            if cluster_dist:
                for cluster_num, num_users in cluster_dist.items():
                    data = {
                        "cluster_number": cluster_num,
                        "num_users": num_users
                    }
                    self.tb_client.send_ml_metrics(f"cluster_{cluster_num}", data)
            
            # 4. Enviar top movies
            logger.info("\n🎬 Enviando top 20 filmes...")
            top_movies = self.get_top_movies(20)
            if top_movies:
                for idx, movie in enumerate(top_movies, 1):
                    device_name = f"movie_{movie['movie_id']}"
                    
                    # Criar/obter dispositivo
                    device = self.tb_client.create_device(device_name, "ML_Model")
                    if device:
                        device_id = device.get("id", {}).get("id")
                        
                        # Enviar atributos (nome do filme)
                        attributes = {
                            "title": movie['title'],
                            "movie_id": movie['movie_id']
                        }
                        self.tb_client.send_attributes(device_id, attributes)
                        
                        # Enviar telemetria (métricas)
                        movie_data = {
                            "rank": idx,
                            "num_ratings": movie['num_ratings'],
                            "avg_rating": movie['avg_rating']
                        }
                        self.tb_client.send_ml_metrics(device_name, movie_data)
            
            logger.info("\n" + "=" * 60)
            logger.info("✅ ETL concluído com sucesso!")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro durante ETL: {e}")
            return False
            
        finally:
            self.close_postgres()
    
    def run_continuous(self, interval_seconds: int = 60):
        """
        Executa ETL continuamente em intervalos regulares
        
        Args:
            interval_seconds: Intervalo entre execuções (default: 60s)
        """
        logger.info(f"🔄 Modo contínuo ativado (intervalo: {interval_seconds}s)")
        
        while True:
            try:
                self.send_all_data_to_thingsboard()
                logger.info(f"\n⏰ Próxima execução em {interval_seconds} segundos...")
                time.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                logger.info("\n⚠️ Interrompido pelo usuário")
                break
            except Exception as e:
                logger.error(f"❌ Erro no loop contínuo: {e}")
                time.sleep(interval_seconds)


def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ETL PostgreSQL → ThingsBoard')
    parser.add_argument(
        '--continuous',
        action='store_true',
        help='Executar continuamente (padrão: execução única)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Intervalo em segundos entre execuções no modo contínuo (padrão: 60)'
    )
    
    args = parser.parse_args()
    
    # Criar instância do ETL
    etl = PostgreSQLToThingsBoard()
    
    if args.continuous:
        etl.run_continuous(args.interval)
    else:
        etl.send_all_data_to_thingsboard()


if __name__ == "__main__":
    main()
