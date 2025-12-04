"""
Script para enviar métricas REAIS dos modelos treinados para o ThingsBoard
Baseado nos resultados do notebook parte3_analise_modelagem.ipynb
"""
import os
import requests
from datetime import datetime

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


def create_or_get_device(token, name, device_type, label):
    """Cria device ou retorna se já existir"""
    headers = {
        "Content-Type": "application/json",
        "X-Authorization": f"Bearer {token}"
    }
    
    # Tentar criar
    url = f"{TB_URL}/api/device"
    payload = {"name": name, "type": device_type, "label": label}
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    
    if response.status_code == 200:
        return response.json()
    
    # Se já existe, buscar
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
    print("=" * 80)
    print("📊 SINCRONIZANDO MÉTRICAS REAIS DOS MODELOS")
    print("=" * 80)
    
    # Login
    print("\n🔐 Autenticando...")
    token = login()
    if not token:
        print("❌ Falha na autenticação")
        return
    print("✅ Autenticado!")
    
    # Métricas REAIS do notebook
    models = [
        {
            "name": "Paper_Original_KMeans_KNN",
            "label": "K-Means (K=8) + KNN - Paper Original",
            "algorithm": "K-Means (K=8) + KNN (N=10)",
            "rmse": 1.0807,
            "mae": 0.8455,
            "improvement_vs_baseline": 3.99,
            "k_clusters": 8,
            "n_neighbors": 10
        },
        {
            "name": "Tuned_KMeans_KNN",
            "label": "K-Means Otimizado (Unity) - Melhorado",
            "algorithm": "K-Means (K=5) + KNN (N=15)",
            "rmse": 1.0592,
            "mae": 0.8455,
            "improvement_vs_baseline": 5.91,
            "improvement_vs_paper": 1.98,
            "k_clusters": 5,
            "n_neighbors": 15
        },
        {
            "name": "Random_Forest_Regressor",
            "label": "Random Forest - Regressão Supervisionada",
            "algorithm": "Random Forest (100 trees, depth=15)",
            "rmse": 1.0238,
            "mae": 0.8214,
            "improvement_vs_baseline": 9.05,
            "improvement_vs_paper": 5.27,
            "n_estimators": 100,
            "max_depth": 15,
            "n_features": 23
        },
        {
            "name": "Baseline_Global_Mean",
            "label": "Baseline - Média Global",
            "algorithm": "Predição por média global",
            "rmse": 1.1257,
            "mae": 0.9102,
            "improvement_vs_baseline": 0.0
        }
    ]
    
    print(f"\n📤 Enviando {len(models)} modelos para o ThingsBoard...\n")
    
    success_count = 0
    
    for model in models:
        print(f"🔹 {model['label']}")
        
        # Criar device
        device = create_or_get_device(
            token,
            name=model['name'],
            device_type="ml_model",
            label=model['label']
        )
        
        if not device:
            print(f"   ❌ Erro ao criar/buscar device")
            continue
        
        device_id = device['id']['id']
        
        # Telemetria (métricas que mudam)
        telemetry = {
            "rmse": model['rmse'],
            "mae": model['mae'],
            "improvement_vs_baseline": model.get('improvement_vs_baseline', 0)
        }
        
        if 'improvement_vs_paper' in model:
            telemetry['improvement_vs_paper'] = model['improvement_vs_paper']
        
        # Atributos (metadata estática)
        attributes = {
            "algorithm": model['algorithm'],
            "experiment": "MovieLens_Recommender_System",
            "trained_at": datetime.utcnow().isoformat(),
            "dataset": "MovieLens 100K (90,570 ratings)"
        }
        
        # Adicionar hiperparâmetros específicos
        if 'k_clusters' in model:
            attributes['k_clusters'] = model['k_clusters']
        if 'n_neighbors' in model:
            attributes['n_neighbors'] = model['n_neighbors']
        if 'n_estimators' in model:
            attributes['n_estimators'] = model['n_estimators']
        if 'max_depth' in model:
            attributes['max_depth'] = model['max_depth']
        if 'n_features' in model:
            attributes['n_features'] = model['n_features']
        
        # Enviar dados
        if send_telemetry(token, device_id, telemetry):
            send_attributes(token, device_id, attributes)
            success_count += 1
            print(f"   ✅ Métricas enviadas - RMSE: {model['rmse']:.4f}")
        else:
            print(f"   ❌ Erro ao enviar métricas")
    
    print("\n" + "=" * 80)
    print(f"✅ {success_count}/{len(models)} modelos sincronizados com sucesso!")
    print("=" * 80)
    
    print("\n📊 RESUMO DAS MÉTRICAS:")
    print("\n🏆 Ranking por RMSE (menor é melhor):")
    sorted_models = sorted(models, key=lambda x: x['rmse'])
    for idx, model in enumerate(sorted_models, 1):
        print(f"   {idx}º {model['label']:<45} RMSE: {model['rmse']:.4f}")
    
    print("\n💡 Próximos passos:")
    print("   1. Acesse: http://localhost:9090")
    print("   2. Vá em 'Devices' e veja os 4 modelos")
    print("   3. Crie um dashboard de comparação")
    print("   4. Use gráfico de barras para comparar os RMSEs")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()

