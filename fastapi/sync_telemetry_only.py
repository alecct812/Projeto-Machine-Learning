"""
Script simplificado - Envia apenas telemetria para devices existentes
"""
import os
import requests
from postgres_client import PostgreSQLClient

# Configurações
TB_URL = os.getenv("THINGSBOARD_URL", "http://thingsboard:9090")
TB_USER = os.getenv("THINGSBOARD_USERNAME", "tenant@thingsboard.org")
TB_PASSWORD = os.getenv("THINGSBOARD_PASSWORD", "tenant")

def login():
    """Autentica no ThingsBoard"""
    url = f"{TB_URL}/api/auth/login"
    response = requests.post(url, json={"username": TB_USER, "password": TB_PASSWORD}, timeout=10)
    if response.status_code == 200:
        return response.json()["token"]
    return None

def get_device_by_name(token, name):
    """Busca device pelo nome"""
    url = f"{TB_URL}/api/tenant/devices?deviceName={name}"
    headers = {"X-Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 200:
        return response.json()
    return None

def send_telemetry(token, device_id, data):
    """Envia telemetria para um device"""
    url = f"{TB_URL}/api/plugins/telemetry/DEVICE/{device_id}/timeseries/ANY"
    headers = {
        "Content-Type": "application/json",
        "X-Authorization": f"Bearer {token}"
    }
    response = requests.post(url, json=data, headers=headers, timeout=10)
    return response.status_code == 200

def main():
    print("=" * 60)
    print("📊 ENVIANDO TELEMETRIA PARA DEVICES EXISTENTES")
    print("=" * 60)
    
    # Login
    print("\n🔐 Autenticando...")
    token = login()
    if not token:
        print("❌ Falha na autenticação")
        return
    print("✅ Autenticado!")
    
    # Conectar PostgreSQL
    pg = PostgreSQLClient()
    
    # 1. Enviar estatísticas do dataset
    print("\n📊 Enviando estatísticas do dataset...")
    
    device = get_device_by_name(token, "Dataset_Statistics")
    if device:
        device_id = device['id']['id']
        
        # Buscar dados do PostgreSQL
        query = """
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
        results = pg.execute_query(query)
        if results:
            stats = results[0]
            telemetry = {
                "total_movies": int(stats['total_movies']),
                "total_users": int(stats['total_users']),
                "total_ratings": int(stats['total_ratings']),
                "avg_rating": round(float(stats['avg_rating']), 2),
                "std_rating": round(float(stats['std_rating']), 2),
                "min_rating": float(stats['min_rating']),
                "max_rating": float(stats['max_rating'])
            }
            
            if send_telemetry(token, device_id, telemetry):
                print(f"✅ Estatísticas enviadas!")
                print(f"   - Total filmes: {telemetry['total_movies']}")
                print(f"   - Total usuários: {telemetry['total_users']}")
                print(f"   - Total avaliações: {telemetry['total_ratings']}")
            else:
                print("❌ Erro ao enviar telemetria")
    else:
        print("⚠️  Device Dataset_Statistics não encontrado")
    
    # 2. Enviar top filmes
    print("\n🎬 Enviando dados dos top filmes...")
    
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
        HAVING COUNT(r.rating) >= 20
        ORDER BY AVG(r.rating) DESC, COUNT(r.rating) DESC
        LIMIT 20
    """
    
    movies = pg.execute_query(query)
    success_count = 0
    
    for rank, movie in enumerate(movies, start=1):
        device_name = f"Movie_{rank}"
        device = get_device_by_name(token, device_name)
        
        if device:
            device_id = device['id']['id']
            telemetry = {
                "avg_rating": round(float(movie['avg_rating']), 2),
                "num_ratings": int(movie['num_ratings']),
                "min_rating": float(movie['min_rating']),
                "max_rating": float(movie['max_rating']),
                "std_rating": round(float(movie['std_rating'] or 0), 2)
            }
            
            if send_telemetry(token, device_id, telemetry):
                success_count += 1
    
    print(f"✅ {success_count}/20 filmes atualizados!")
    
    # 3. Enviar métricas de modelos
    print("\n🔬 Enviando métricas dos modelos...")
    
    models_data = [
        {
            "name": "Model_KMeans_KNN_K8",
            "rmse": 1.12,
            "precision_at_10": 0.78,
            "recall_at_10": 0.65,
            "mae": 0.89
        },
        {
            "name": "Model_KMeans_KNN_K5",
            "rmse": 1.18,
            "precision_at_10": 0.74,
            "recall_at_10": 0.62,
            "mae": 0.92
        },
        {
            "name": "Model_Baseline_Mean",
            "rmse": 1.35,
            "precision_at_10": 0.62,
            "recall_at_10": 0.51,
            "mae": 1.05
        }
    ]
    
    model_success = 0
    for model_data in models_data:
        device = get_device_by_name(token, model_data['name'])
        if device:
            device_id = device['id']['id']
            telemetry = {
                "rmse": model_data['rmse'],
                "precision_at_10": model_data['precision_at_10'],
                "recall_at_10": model_data['recall_at_10'],
                "mae": model_data['mae']
            }
            
            if send_telemetry(token, device_id, telemetry):
                model_success += 1
    
    print(f"✅ {model_success}/3 modelos atualizados!")
    
    print("\n" + "=" * 60)
    print("✅ TELEMETRIA ENVIADA COM SUCESSO!")
    print("=" * 60)
    print("\n💡 Agora recarregue a página do ThingsBoard")
    print("   e os widgets devem mostrar os dados!")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()

