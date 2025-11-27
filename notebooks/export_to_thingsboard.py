"""
Script de exportação de métricas e predições para ThingsBoard/Trendz
Integração entre modelos ML e plataforma de visualização
"""
import os
import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
import requests
from datetime import datetime
import json
from typing import Dict, List, Optional

class ThingsBoardExporter:
    """
    Classe para exportar dados de ML para ThingsBoard
    """
    
    def __init__(self):
        self.pg_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': os.getenv('POSTGRES_PORT', '5432'),
            'database': os.getenv('POSTGRES_DB', 'movielens'),
            'user': os.getenv('POSTGRES_USER', 'ml_user'),
            'password': os.getenv('POSTGRES_PASSWORD', 'ml_password_2025')
        }
        
        self.tb_url = os.getenv('THINGSBOARD_URL', 'http://thingsboard:9090')
        self.tb_token = None  # Será configurado após login
        
    def connect_db(self):
        """Conectar ao PostgreSQL"""
        return psycopg2.connect(**self.pg_config)
    
    def login_thingsboard(self, username: str = "tenant@thingsboard.org", 
                         password: str = "tenant"):
        """
        Fazer login no ThingsBoard e obter token JWT
        
        Args:
            username: Email do usuário (padrão: tenant)
            password: Senha do usuário
        """
        login_url = f"{self.tb_url}/api/auth/login"
        
        payload = {
            "username": username,
            "password": password
        }
        
        try:
            response = requests.post(login_url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            self.tb_token = data.get('token')
            print(f"✅ Login ThingsBoard realizado com sucesso!")
            return self.tb_token
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro ao fazer login no ThingsBoard: {e}")
            return None
    
    def export_model_metrics(self, model_version: str):
        """
        Exportar métricas do modelo para ThingsBoard
        
        Args:
            model_version: Versão do modelo a exportar
        """
        conn = self.connect_db()
        
        query = """
        SELECT 
            model_name,
            model_version,
            metric_name,
            metric_value,
            dataset_type,
            created_at,
            experiment_id,
            run_id
        FROM model_metrics
        WHERE model_version = %s
        ORDER BY created_at DESC
        """
        
        df = pd.read_sql(query, conn, params=(model_version,))
        conn.close()
        
        print(f"📊 Exportando {len(df)} métricas do modelo {model_version}")
        
        # Preparar telemetria para ThingsBoard
        telemetry_data = []
        
        for _, row in df.iterrows():
            telemetry_data.append({
                'ts': int(row['created_at'].timestamp() * 1000),
                'values': {
                    row['metric_name']: row['metric_value'],
                    'model_name': row['model_name'],
                    'model_version': row['model_version'],
                    'dataset_type': row['dataset_type']
                }
            })
        
        return telemetry_data
    
    def export_prediction_history(self, limit: int = 1000):
        """
        Exportar histórico de predições para análise
        
        Args:
            limit: Número máximo de registros a exportar
        """
        conn = self.connect_db()
        
        query = """
        SELECT 
            ph.prediction_id,
            ph.user_id,
            ph.movie_id,
            m.title as movie_title,
            ph.predicted_rating,
            ph.actual_rating,
            ph.prediction_error,
            ph.model_version,
            ph.predicted_at,
            u.age as user_age,
            u.gender as user_gender,
            u.occupation as user_occupation
        FROM prediction_history ph
        LEFT JOIN movies m ON ph.movie_id = m.movie_id
        LEFT JOIN users u ON ph.user_id = u.user_id
        WHERE ph.actual_rating IS NOT NULL
        ORDER BY ph.predicted_at DESC
        LIMIT %s
        """
        
        df = pd.read_sql(query, conn, params=(limit,))
        conn.close()
        
        print(f"📈 Exportando {len(df)} predições do histórico")
        
        return df
    
    def export_recommendations_summary(self):
        """
        Exportar resumo de recomendações por algoritmo
        """
        conn = self.connect_db()
        
        query = """
        SELECT 
            algorithm,
            model_version,
            COUNT(*) as total_recommendations,
            AVG(recommendation_score) as avg_score,
            AVG(predicted_rating) as avg_predicted_rating,
            MIN(recommendation_date) as first_recommendation,
            MAX(recommendation_date) as last_recommendation
        FROM recommendations
        GROUP BY algorithm, model_version
        ORDER BY algorithm, model_version
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        print(f"🎯 Resumo de recomendações por algoritmo:")
        print(df.to_string())
        
        return df
    
    def export_cluster_analysis(self):
        """
        Exportar análise de clusters para visualização
        """
        conn = self.connect_db()
        
        query = """
        SELECT 
            uc.cluster_number,
            COUNT(DISTINCT uc.user_id) as total_users,
            AVG(uc.distance_to_centroid) as avg_distance,
            AVG(us.avg_rating) as cluster_avg_rating,
            AVG(us.age) as cluster_avg_age,
            uc.model_version
        FROM user_clusters uc
        LEFT JOIN user_stats us ON uc.user_id = us.user_id
        GROUP BY uc.cluster_number, uc.model_version
        ORDER BY uc.cluster_number
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        print(f"🔵 Análise de {len(df)} clusters:")
        print(df.to_string())
        
        return df
    
    def save_to_csv(self, df: pd.DataFrame, filename: str):
        """
        Salvar DataFrame em CSV para importação manual
        
        Args:
            df: DataFrame a salvar
            filename: Nome do arquivo CSV
        """
        output_dir = "/workspace/reports"
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = os.path.join(output_dir, filename)
        df.to_csv(filepath, index=False)
        
        print(f"💾 Arquivo salvo: {filepath}")
        return filepath


def main():
    """
    Função principal para exportação de dados
    """
    print("🚀 Iniciando exportação de dados para ThingsBoard/Trendz...")
    
    exporter = ThingsBoardExporter()
    
    # Exportar dados
    try:
        # 1. Histórico de predições
        predictions_df = exporter.export_prediction_history(limit=10000)
        exporter.save_to_csv(predictions_df, 'prediction_history_export.csv')
        
        # 2. Resumo de recomendações
        recommendations_df = exporter.export_recommendations_summary()
        exporter.save_to_csv(recommendations_df, 'recommendations_summary.csv')
        
        # 3. Análise de clusters
        clusters_df = exporter.export_cluster_analysis()
        exporter.save_to_csv(clusters_df, 'cluster_analysis.csv')
        
        print("\n✅ Exportação concluída com sucesso!")
        print("📂 Arquivos salvos em: /workspace/reports/")
        print("\n📋 Próximos passos:")
        print("1. Importar os CSVs no ThingsBoard")
        print("2. Criar dispositivos e ativos no ThingsBoard")
        print("3. Configurar dashboards no Trendz Analytics")
        
    except Exception as e:
        print(f"❌ Erro durante exportação: {e}")
        raise


if __name__ == "__main__":
    main()
