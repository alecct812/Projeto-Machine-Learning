"""
Cliente PostgreSQL para o Sistema de Recomendação MovieLens
Gerencia conexão e operações com o banco de dados PostgreSQL
"""

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
import os
import logging

logger = logging.getLogger(__name__)


class PostgreSQLClient:
    """Cliente para interação com PostgreSQL"""
    
    def __init__(self):
        """Inicializa o cliente PostgreSQL"""
        self.host = os.getenv("POSTGRES_HOST", "postgres")
        self.port = int(os.getenv("POSTGRES_PORT", "5432"))
        self.database = os.getenv("POSTGRES_DB", "movielens")
        self.user = os.getenv("POSTGRES_USER", "ml_user")
        self.password = os.getenv("POSTGRES_PASSWORD", "ml_password_2025")
        
        # Pool de conexões
        self.connection_pool = None
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Inicializa o pool de conexões"""
        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            logger.info(f"Pool de conexões PostgreSQL criado - {self.host}:{self.port}/{self.database}")
        except Exception as e:
            logger.error(f"Erro ao criar pool de conexões: {e}")
            raise
    
    def get_connection(self):
        """Obtém uma conexão do pool"""
        try:
            return self.connection_pool.getconn()
        except Exception as e:
            logger.error(f"Erro ao obter conexão: {e}")
            raise
    
    def return_connection(self, conn):
        """Retorna a conexão ao pool"""
        try:
            self.connection_pool.putconn(conn)
        except Exception as e:
            logger.error(f"Erro ao retornar conexão: {e}")
    
    def check_connection(self) -> bool:
        """Verifica se a conexão com PostgreSQL está funcionando"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            cursor.close()
            logger.info(f"PostgreSQL conectado: {version}")
            return True
        except Exception as e:
            logger.error(f"Erro ao conectar PostgreSQL: {e}")
            return False
        finally:
            if conn:
                self.return_connection(conn)
    
    def execute_query(self, query: str, params: tuple = None, fetch: bool = True) -> Optional[List[Dict]]:
        """
        Executa uma query SQL
        
        Args:
            query: Query SQL a executar
            params: Parâmetros da query
            fetch: Se True, retorna os resultados
            
        Returns:
            Lista de dicionários com os resultados (se fetch=True)
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, params)
            
            if fetch:
                results = cursor.fetchall()
                cursor.close()
                conn.commit()
                return [dict(row) for row in results]
            else:
                conn.commit()
                cursor.close()
                return None
                
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Erro ao executar query: {e}")
            raise
        finally:
            if conn:
                self.return_connection(conn)
    
    def execute_many(self, query: str, data: List[tuple]) -> int:
        """
        Executa insert/update em lote
        
        Args:
            query: Query SQL
            data: Lista de tuplas com os dados
            
        Returns:
            Número de linhas afetadas
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.executemany(query, data)
            rowcount = cursor.rowcount
            conn.commit()
            cursor.close()
            logger.info(f"{rowcount} linhas inseridas/atualizadas")
            return rowcount
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Erro ao executar batch: {e}")
            raise
        finally:
            if conn:
                self.return_connection(conn)
    
    def get_table_count(self, table_name: str) -> int:
        """Retorna o número de registros em uma tabela"""
        try:
            result = self.execute_query(f"SELECT COUNT(*) as count FROM {table_name}")
            return result[0]['count'] if result else 0
        except Exception as e:
            logger.error(f"Erro ao contar registros de {table_name}: {e}")
            return 0
    
    def get_tables(self) -> List[str]:
        """Lista todas as tabelas do banco"""
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """
        try:
            results = self.execute_query(query)
            return [row['table_name'] for row in results] if results else []
        except Exception as e:
            logger.error(f"Erro ao listar tabelas: {e}")
            return []
    
    def get_table_info(self) -> Dict[str, int]:
        """Retorna informações sobre todas as tabelas"""
        tables = self.get_tables()
        info = {}
        for table in tables:
            info[table] = self.get_table_count(table)
        return info
    
    def truncate_table(self, table_name: str, cascade: bool = True):
        """
        Limpa uma tabela
        
        Args:
            table_name: Nome da tabela
            cascade: Se True, usa CASCADE para limpar tabelas relacionadas
        """
        try:
            cascade_sql = "CASCADE" if cascade else ""
            self.execute_query(f"TRUNCATE TABLE {table_name} {cascade_sql}", fetch=False)
            logger.info(f"Tabela {table_name} limpa com sucesso")
        except Exception as e:
            logger.error(f"Erro ao limpar tabela {table_name}: {e}")
            raise
    
    def insert_movie(self, movie_data: Dict) -> int:
        """
        Insere um filme no banco
        
        Args:
            movie_data: Dicionário com dados do filme
            
        Returns:
            ID do filme inserido
        """
        query = """
        INSERT INTO movies (
            movie_id, title, release_date, video_release_date, imdb_url,
            unknown, action, adventure, animation, childrens, comedy, crime,
            documentary, drama, fantasy, film_noir, horror, musical, mystery,
            romance, sci_fi, thriller, war, western
        ) VALUES (
            %(movie_id)s, %(title)s, %(release_date)s, %(video_release_date)s, %(imdb_url)s,
            %(unknown)s, %(action)s, %(adventure)s, %(animation)s, %(childrens)s, 
            %(comedy)s, %(crime)s, %(documentary)s, %(drama)s, %(fantasy)s, 
            %(film_noir)s, %(horror)s, %(musical)s, %(mystery)s, %(romance)s, 
            %(sci_fi)s, %(thriller)s, %(war)s, %(western)s
        ) ON CONFLICT (movie_id) DO NOTHING
        RETURNING movie_id
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, movie_data)
            result = cursor.fetchone()
            conn.commit()
            cursor.close()
            return result[0] if result else movie_data['movie_id']
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Erro ao inserir filme: {e}")
            raise
        finally:
            if conn:
                self.return_connection(conn)
    
    def insert_user(self, user_data: Dict) -> int:
        """
        Insere um usuário no banco
        
        Args:
            user_data: Dicionário com dados do usuário
            
        Returns:
            ID do usuário inserido
        """
        query = """
        INSERT INTO users (user_id, age, gender, occupation, zip_code)
        VALUES (%(user_id)s, %(age)s, %(gender)s, %(occupation)s, %(zip_code)s)
        ON CONFLICT (user_id) DO NOTHING
        RETURNING user_id
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, user_data)
            result = cursor.fetchone()
            conn.commit()
            cursor.close()
            return result[0] if result else user_data['user_id']
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Erro ao inserir usuário: {e}")
            raise
        finally:
            if conn:
                self.return_connection(conn)
    
    def insert_rating(self, rating_data: Dict) -> int:
        """
        Insere uma avaliação no banco
        
        Args:
            rating_data: Dicionário com dados da avaliação
            
        Returns:
            ID da avaliação inserida
        """
        query = """
        INSERT INTO ratings (user_id, movie_id, rating, timestamp, rated_at)
        VALUES (%(user_id)s, %(movie_id)s, %(rating)s, %(timestamp)s, %(rated_at)s)
        RETURNING rating_id
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, rating_data)
            result = cursor.fetchone()
            conn.commit()
            cursor.close()
            return result[0]
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Erro ao inserir rating: {e}")
            raise
        finally:
            if conn:
                self.return_connection(conn)
    
    def close(self):
        """Fecha o pool de conexões"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("Pool de conexões PostgreSQL fechado")
