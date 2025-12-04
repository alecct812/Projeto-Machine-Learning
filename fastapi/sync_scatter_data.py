"""
Script para enviar dados de dispersão (scatter) para o ThingsBoard
Agrupa dados em faixas para visualização em gráfico de linhas/barras
"""
import os
import requests
from datetime import datetime
import sys

# Adicionar path para imports
sys.path.append('/app')

# Configurações
TB_URL = os.getenv("THINGSBOARD_URL", "http://thingsboard:9090")
TB_USER = os.getenv("THINGSBOARD_USERNAME", "tenant@thingsboard.org")
TB_PASSWORD = os.getenv("THINGSBOARD_PASSWORD", "tenant")

# Configuração PostgreSQL
import psycopg2
import pandas as pd

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'postgres'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'database': os.getenv('POSTGRES_DB', 'movielens'),
    'user': os.getenv('POSTGRES_USER', 'ml_user'),
    'password': os.getenv('POSTGRES_PASSWORD', 'ml_password_2025')
}


def get_db_connection():
    """Conecta ao PostgreSQL"""
    return psycopg2.connect(**DB_CONFIG)


def login():
    """Autentica no ThingsBoard"""
    url = f"{TB_URL}/api/auth/login"
    response = requests.post(url, json={"username": TB_USER, "password": TB_PASSWORD}, timeout=10)
    if response.status_code == 200:
        return response.json()["token"]
    return None


def create_or_get_device(token, name, device_type, label):
    """Cria device ou retorna se já existir"""
    headers = {
        "Content-Type": "application/json",
        "X-Authorization": f"Bearer {token}"
    }
    
    url = f"{TB_URL}/api/device"
    payload = {"name": name, "type": device_type, "label": label}
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    
    if response.status_code == 200:
        return response.json()
    
    url = f"{TB_URL}/api/tenant/devices?deviceName={name}"
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 200:
        return response.json()
    
    return None


def send_telemetry(token, device_id, data):
    """Envia telemetria para device"""
    url = f"{TB_URL}/api/plugins/telemetry/DEVICE/{device_id}/timeseries/ANY"
    headers = {
        "Content-Type": "application/json",
        "X-Authorization": f"Bearer {token}"
    }
    response = requests.post(url, json=data, headers=headers, timeout=10)
    return response.status_code == 200


def send_attributes(token, device_id, data):
    """Envia atributos para device"""
    url = f"{TB_URL}/api/plugins/telemetry/DEVICE/{device_id}/attributes/SERVER_SCOPE"
    headers = {
        "Content-Type": "application/json",
        "X-Authorization": f"Bearer {token}"
    }
    response = requests.post(url, json=data, headers=headers, timeout=10)
    return response.status_code == 200


def main():
    print("=" * 70)
    print("📊 SINCRONIZANDO DADOS DE DISPERSÃO (SCATTER)")
    print("=" * 70)
    
    # Login ThingsBoard
    print("\n🔐 Autenticando no ThingsBoard...")
    token = login()
    if not token:
        print("❌ Falha na autenticação")
        return
    print("✅ Autenticado!")
    
    # Conectar PostgreSQL
    print("\n📦 Conectando ao PostgreSQL...")
    try:
        conn = get_db_connection()
        print("✅ Conectado ao PostgreSQL!")
    except Exception as e:
        print(f"❌ Erro: {e}")
        return
    
    # ============================================================
    # 1. DISPERSÃO: Usuários - Atividade vs Rating
    # ============================================================
    print("\n📊 Calculando dispersão de USUÁRIOS...")
    
    query_users = """
        SELECT 
            user_id,
            COUNT(*) as num_ratings,
            AVG(rating) as avg_rating
        FROM ratings
        GROUP BY user_id
    """
    
    user_stats = pd.read_sql(query_users, conn)
    
    # Criar faixas de atividade (buckets)
    bins_users = [0, 50, 100, 150, 200, 300, 500, 800]
    labels_users = ['0-50', '51-100', '101-150', '151-200', '201-300', '301-500', '501+']
    user_stats['activity_range'] = pd.cut(user_stats['num_ratings'], bins=bins_users, labels=labels_users)
    
    # Agregar por faixa
    user_scatter = user_stats.groupby('activity_range', observed=True).agg(
        avg_rating_mean=('avg_rating', 'mean'),
        avg_rating_std=('avg_rating', 'std'),
        user_count=('user_id', 'count')
    ).reset_index()
    
    print(f"   Faixas calculadas: {len(user_scatter)}")
    
    # ============================================================
    # 2. DISPERSÃO: Filmes - Popularidade vs Rating
    # ============================================================
    print("\n📊 Calculando dispersão de FILMES...")
    
    query_movies = """
        SELECT 
            movie_id,
            COUNT(*) as num_ratings,
            AVG(rating) as avg_rating
        FROM ratings
        GROUP BY movie_id
    """
    
    movie_stats = pd.read_sql(query_movies, conn)
    
    # Criar faixas de popularidade (buckets)
    bins_movies = [0, 20, 50, 100, 200, 300, 500, 700]
    labels_movies = ['0-20', '21-50', '51-100', '101-200', '201-300', '301-500', '501+']
    movie_stats['popularity_range'] = pd.cut(movie_stats['num_ratings'], bins=bins_movies, labels=labels_movies)
    
    # Agregar por faixa
    movie_scatter = movie_stats.groupby('popularity_range', observed=True).agg(
        avg_rating_mean=('avg_rating', 'mean'),
        avg_rating_std=('avg_rating', 'std'),
        movie_count=('movie_id', 'count')
    ).reset_index()
    
    print(f"   Faixas calculadas: {len(movie_scatter)}")
    
    conn.close()
    
    # ============================================================
    # 3. ENVIAR PARA THINGSBOARD
    # ============================================================
    print("\n📤 Enviando dados para o ThingsBoard...")
    
    # Device: Dispersão de Usuários
    print("\n🔹 Criando device: Scatter_Users_Activity")
    device = create_or_get_device(
        token,
        name="Scatter_Users_Activity",
        device_type="eda_scatter",
        label="Dispersão: Atividade Usuário vs Rating"
    )
    
    if device:
        device_id = device['id']['id']
        
        # Criar telemetria com cada faixa
        telemetry = {}
        for _, row in user_scatter.iterrows():
            range_name = str(row['activity_range']).replace('-', '_').replace('+', 'plus')
            telemetry[f"rating_{range_name}"] = round(row['avg_rating_mean'], 3)
            telemetry[f"count_{range_name}"] = int(row['user_count'])
        
        # Adicionar resumo
        telemetry['total_users'] = int(user_stats['user_id'].nunique())
        telemetry['avg_ratings_per_user'] = round(user_stats['num_ratings'].mean(), 1)
        telemetry['correlation'] = -0.1378
        
        if send_telemetry(token, device_id, telemetry):
            print(f"   ✅ Telemetria enviada!")
            
        attributes = {
            "chart_type": "Scatter/Line",
            "x_axis": "Número de Avaliações (Atividade)",
            "y_axis": "Rating Médio",
            "dataset": "MovieLens 100K"
        }
        send_attributes(token, device_id, attributes)
    
    # Device: Dispersão de Filmes
    print("\n🔹 Criando device: Scatter_Movies_Popularity")
    device = create_or_get_device(
        token,
        name="Scatter_Movies_Popularity",
        device_type="eda_scatter",
        label="Dispersão: Popularidade Filme vs Rating"
    )
    
    if device:
        device_id = device['id']['id']
        
        telemetry = {}
        for _, row in movie_scatter.iterrows():
            range_name = str(row['popularity_range']).replace('-', '_').replace('+', 'plus')
            telemetry[f"rating_{range_name}"] = round(row['avg_rating_mean'], 3)
            telemetry[f"count_{range_name}"] = int(row['movie_count'])
        
        telemetry['total_movies'] = int(movie_stats['movie_id'].nunique())
        telemetry['avg_ratings_per_movie'] = round(movie_stats['num_ratings'].mean(), 1)
        telemetry['correlation'] = 0.4297
        
        if send_telemetry(token, device_id, telemetry):
            print(f"   ✅ Telemetria enviada!")
            
        attributes = {
            "chart_type": "Scatter/Line",
            "x_axis": "Número de Avaliações (Popularidade)",
            "y_axis": "Rating Médio",
            "dataset": "MovieLens 100K"
        }
        send_attributes(token, device_id, attributes)
    
    # ============================================================
    # RESUMO
    # ============================================================
    print("\n" + "=" * 70)
    print("✅ SINCRONIZAÇÃO COMPLETA!")
    print("=" * 70)
    
    print("\n📊 DEVICES CRIADOS:")
    print("   - Scatter_Users_Activity")
    print("   - Scatter_Movies_Popularity")
    
    print("\n📈 KEYS DISPONÍVEIS (Usuários):")
    for _, row in user_scatter.iterrows():
        range_name = str(row['activity_range']).replace('-', '_').replace('+', 'plus')
        print(f"   rating_{range_name}: {row['avg_rating_mean']:.3f} ({int(row['user_count'])} usuários)")
    
    print("\n📈 KEYS DISPONÍVEIS (Filmes):")
    for _, row in movie_scatter.iterrows():
        range_name = str(row['popularity_range']).replace('-', '_').replace('+', 'plus')
        print(f"   rating_{range_name}: {row['avg_rating_mean']:.3f} ({int(row['movie_count'])} filmes)")
    
    print("\n💡 No ThingsBoard, use 'Line Chart' ou 'Bar Chart' com essas keys!")


if __name__ == "__main__":
    main()

