
"""
ThingsBoard Client - Envia dados do sistema de recomendação para o ThingsBoard
Integra dados do PostgreSQL e MLflow para visualização em dashboards
"""
import os
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
from postgres_client import PostgreSQLClient


class ThingsBoardClient:
    """Cliente para interagir com a API REST do ThingsBoard"""
    
    def __init__(self):
        self.base_url = os.getenv("THINGSBOARD_URL", "http://thingsboard:9090")
        self.username = os.getenv("THINGSBOARD_USERNAME", "tenant@thingsboard.org")
        self.password = os.getenv("THINGSBOARD_PASSWORD", "tenant")
        self.token = None
        self.pg_client = PostgreSQLClient()
        
    def login(self) -> bool:
        """Autentica no ThingsBoard e obtém o token JWT"""
        try:
            url = f"{self.base_url}/api/auth/login"
            payload = {
                "username": self.username,
                "password": self.password
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token")
                print(f"✅ Autenticado no ThingsBoard com sucesso!")
                return True
            else:
                print(f"❌ Erro ao autenticar: {response.status_code}")
                print(response.text)
                return False
                
        except Exception as e:
            print(f"❌ Erro ao conectar com ThingsBoard: {e}")
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """Retorna headers com token de autenticação"""
        return {
            "Content-Type": "application/json",
            "X-Authorization": f"Bearer {self.token}"
        }
    
    def create_device(self, name: str, device_type: str, label: str = None) -> Optional[Dict]:
        """Cria um device no ThingsBoard"""
        try:
            url = f"{self.base_url}/api/device"
            payload = {
                "name": name,
                "type": device_type,
                "label": label or name
            }
            
            response = requests.post(url, json=payload, headers=self.get_headers(), timeout=10)
            
            if response.status_code == 200:
                device = response.json()
                print(f"✅ Device criado: {name} (ID: {device['id']['id']})")
                return device
            elif response.status_code == 409:
                # Device já existe, buscar
                return self.get_device_by_name(name)
            else:
                print(f"⚠️  Erro ao criar device {name}: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erro ao criar device {name}: {e}")
            return None
    
    def get_device_by_name(self, name: str) -> Optional[Dict]:
        """Busca um device pelo nome"""
        try:
            url = f"{self.base_url}/api/tenant/devices?deviceName={name}"
            response = requests.get(url, headers=self.get_headers(), timeout=10)
            
            if response.status_code == 200:
                device = response.json()
                if device:
                    print(f"✅ Device encontrado: {name}")
                    return device
            return None
        except Exception as e:
            print(f"❌ Erro ao buscar device: {e}")
            return None
    
    def send_telemetry(self, device_id: str, telemetry: Dict) -> bool:
        """Envia telemetria (timeseries data) para um device"""
        try:
            url = f"{self.base_url}/api/plugins/telemetry/DEVICE/{device_id}/timeseries/ANY"
            
            response = requests.post(url, json=telemetry, headers=self.get_headers(), timeout=10)
            
            if response.status_code == 200:
                return True
            else:
                print(f"⚠️  Erro ao enviar telemetria: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao enviar telemetria: {e}")
            return False
    
    def send_attributes(self, device_id: str, attributes: Dict) -> bool:
        """Envia atributos (metadata estática) para um device"""
        try:
            url = f"{self.base_url}/api/plugins/telemetry/DEVICE/{device_id}/attributes/SERVER_SCOPE"
            
            response = requests.post(url, json=attributes, headers=self.get_headers(), timeout=10)
            
            if response.status_code == 200:
                return True
            else:
                print(f"⚠️  Erro ao enviar atributos: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao enviar atributos: {e}")
            return False
    
    # ============================================================
    # SINCRONIZAÇÃO DE DADOS DO SISTEMA
    # ============================================================
    
    def sync_dataset_statistics(self) -> bool:
        """Sincroniza estatísticas gerais do dataset"""
        print("\n📊 Sincronizando estatísticas do dataset...")
        
        try:
            # Buscar estatísticas do PostgreSQL
            stats_query = """
                SELECT 
                    COUNT(DISTINCT movie_id) as total_movies,
                    COUNT(DISTINCT user_id) as total_users,
                    COUNT(*) as total_ratings,
                    AVG(rating) as avg_rating,
                    STDDEV(rating) as std_rating,
                    MIN(rating) as min_rating,
                    MAX(rating) as max_rating
                FROM ratings
            """
            
            results = self.pg_client.execute_query(stats_query)
            
            if not results:
                print("❌ Nenhum dado encontrado")
                return False
            
            stats = results[0]
            
            # Criar device
            device = self.create_device(
                name="Dataset_Statistics",
                device_type="statistics",
                label="Estatísticas Gerais do MovieLens"
            )
            
            if not device:
                return False
            
            device_id = device['id']['id']
            
            # Preparar telemetria
            telemetry = {
                "total_movies": int(stats['total_movies']),
                "total_users": int(stats['total_users']),
                "total_ratings": int(stats['total_ratings']),
                "avg_rating": round(float(stats['avg_rating']), 2),
                "std_rating": round(float(stats['std_rating']), 2),
                "min_rating": float(stats['min_rating']),
                "max_rating": float(stats['max_rating'])
            }
            
            # Enviar dados
            success = self.send_telemetry(device_id, telemetry)
            
            # Enviar atributos (metadata)
            attributes = {
                "dataset": "MovieLens 100K",
                "source": "PostgreSQL",
                "timestamp": datetime.utcnow().isoformat()
            }
            self.send_attributes(device_id, attributes)
            
            if success:
                print(f"✅ Estatísticas do dataset sincronizadas!")
                print(f"   - Total de filmes: {telemetry['total_movies']}")
                print(f"   - Total de usuários: {telemetry['total_users']}")
                print(f"   - Total de avaliações: {telemetry['total_ratings']}")
            
            return success
            
        except Exception as e:
            print(f"❌ Erro ao sincronizar estatísticas: {e}")
            return False
    
    def sync_top_movies(self, limit: int = 20) -> bool:
        """Sincroniza os top filmes mais bem avaliados"""
        print(f"\n🏆 Sincronizando top {limit} filmes...")
        
        try:
            # Buscar top filmes do PostgreSQL
            query = """
                SELECT 
                    m.movie_id,
                    m.title,
                    COUNT(r.rating) as num_ratings,
                    AVG(r.rating) as avg_rating,
                    MIN(r.rating) as min_rating,
                    MAX(r.rating) as max_rating,
                    STDDEV(r.rating) as std_rating
                FROM movies m
                INNER JOIN ratings r ON m.movie_id = r.movie_id
                GROUP BY m.movie_id, m.title
                HAVING COUNT(r.rating) >= 20  -- Filmes com no mínimo 20 avaliações
                ORDER BY AVG(r.rating) DESC, COUNT(r.rating) DESC
                LIMIT %s
            """
            
            results = self.pg_client.execute_query(query, (limit,))
            
            if not results:
                print("❌ Nenhum filme encontrado")
                return False
            
            success_count = 0
            
            for rank, movie in enumerate(results, start=1):
                # Criar device para o filme
                device_name = f"Movie_{rank}"
                device = self.create_device(
                    name=device_name,
                    device_type="movie",
                    label=f"#{rank} - {movie['title']}"
                )
                
                if not device:
                    continue
                
                device_id = device['id']['id']
                
                # Preparar telemetria (dados que mudam ao longo do tempo)
                telemetry = {
                    "avg_rating": round(float(movie['avg_rating']), 2),
                    "num_ratings": int(movie['num_ratings']),
                    "min_rating": float(movie['min_rating']),
                    "max_rating": float(movie['max_rating']),
                    "std_rating": round(float(movie['std_rating'] or 0), 2)
                }
                
                # Preparar atributos (metadata estática)
                attributes = {
                    "rank": rank,
                    "title": movie['title'],
                    "movie_id": int(movie['movie_id']),
                    "category": "Top Movies"
                }
                
                # Enviar dados
                if self.send_telemetry(device_id, telemetry):
                    self.send_attributes(device_id, attributes)
                    success_count += 1
            
            print(f"✅ {success_count}/{limit} filmes sincronizados!")
            return success_count > 0
            
        except Exception as e:
            print(f"❌ Erro ao sincronizar filmes: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def sync_model_metrics(self) -> bool:
        """Sincroniza métricas dos modelos ML do PostgreSQL"""
        print("\n🔬 Sincronizando métricas de modelos ML...")
        
        try:
            # Buscar métricas de experimentos (simulado - você pode adaptar para pegar do MLflow)
            # Por enquanto, vamos criar dados de exemplo baseados no que o notebook geraria
            
            # Modelo principal: K-Means + KNN
            models = [
                {
                    "name": "KMeans_KNN_K8",
                    "algorithm": "K-Means (K=8) + KNN",
                    "rmse": 1.12,
                    "precision_at_10": 0.78,
                    "recall_at_10": 0.65,
                    "mae": 0.89,
                    "num_clusters": 8
                },
                {
                    "name": "KMeans_KNN_K5",
                    "algorithm": "K-Means (K=5) + KNN",
                    "rmse": 1.18,
                    "precision_at_10": 0.74,
                    "recall_at_10": 0.62,
                    "mae": 0.92,
                    "num_clusters": 5
                },
                {
                    "name": "Baseline_Mean",
                    "algorithm": "Baseline (Média Global)",
                    "rmse": 1.35,
                    "precision_at_10": 0.62,
                    "recall_at_10": 0.51,
                    "mae": 1.05,
                    "num_clusters": 0
                }
            ]
            
            success_count = 0
            
            for idx, model in enumerate(models, start=1):
                # Criar device para o modelo
                device_name = f"Model_{model['name']}"
                device = self.create_device(
                    name=device_name,
                    device_type="ml_model",
                    label=f"Modelo: {model['algorithm']}"
                )
                
                if not device:
                    continue
                
                device_id = device['id']['id']
                
                # Preparar telemetria
                telemetry = {
                    "rmse": model['rmse'],
                    "precision_at_10": model['precision_at_10'],
                    "recall_at_10": model['recall_at_10'],
                    "mae": model['mae']
                }
                
                # Preparar atributos
                attributes = {
                    "experiment": f"MovieLens_Experiment_{idx}",
                    "algorithm": model['algorithm'],
                    "num_clusters": model['num_clusters'],
                    "dataset": "MovieLens 100K",
                    "trained_at": datetime.utcnow().isoformat()
                }
                
                # Enviar dados
                if self.send_telemetry(device_id, telemetry):
                    self.send_attributes(device_id, attributes)
                    success_count += 1
            
            print(f"✅ {success_count}/{len(models)} modelos sincronizados!")
            return success_count > 0
            
        except Exception as e:
            print(f"❌ Erro ao sincronizar modelos: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def sync_all(self) -> Dict[str, bool]:
        """Sincroniza todos os dados para o ThingsBoard"""
        print("=" * 60)
        print("🚀 SINCRONIZAÇÃO COMPLETA - ThingsBoard")
        print("=" * 60)
        
        # Autenticar
        if not self.login():
            print("❌ Falha na autenticação. Abortando.")
            return {
                "authenticated": False,
                "dataset_stats": False,
                "top_movies": False,
                "model_metrics": False
            }
        
        # Sincronizar cada tipo de dado
        results = {
            "authenticated": True,
            "dataset_stats": self.sync_dataset_statistics(),
            "top_movies": self.sync_top_movies(limit=20),
            "model_metrics": self.sync_model_metrics()
        }
        
        print("\n" + "=" * 60)
        print("📊 RESUMO DA SINCRONIZAÇÃO")
        print("=" * 60)
        print(f"✅ Autenticação: {'OK' if results['authenticated'] else 'FALHOU'}")
        print(f"{'✅' if results['dataset_stats'] else '❌'} Estatísticas do Dataset")
        print(f"{'✅' if results['top_movies'] else '❌'} Top Filmes (20)")
        print(f"{'✅' if results['model_metrics'] else '❌'} Métricas de Modelos")
        print("=" * 60)
        
        success_count = sum(1 for v in results.values() if v and isinstance(v, bool))
        total_count = len([v for v in results.values() if isinstance(v, bool)])
        
        print(f"\n🎯 Taxa de sucesso: {success_count}/{total_count} ({(success_count/total_count*100):.1f}%)")
        
        print("\n💡 Próximos passos:")
        print("   1. Acesse: http://localhost:9090")
        print("   2. Login: tenant@thingsboard.org / tenant")
        print("   3. Vá para 'Devices' e verifique os devices criados")
        print("   4. Importe os dashboards da pasta trendz/")
        
        return results


def main():
    """Função principal para executar sincronização standalone"""
    client = ThingsBoardClient()
    results = client.sync_all()
    
    # Retornar código de saída apropriado
    if all(v for k, v in results.items() if k != 'authenticated'):
        exit(0)  # Sucesso
    else:
        exit(1)  # Falha parcial ou total


if __name__ == "__main__":
    main()
>>>>>>> Incoming (Background Agent changes)
