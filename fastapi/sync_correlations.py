"""
Script para enviar dados de correlação da EDA para o ThingsBoard
Baseado nos gráficos de dispersão do notebook
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
    print("📊 SINCRONIZANDO DADOS DE CORRELAÇÃO (EDA)")
    print("=" * 70)
    
    # Login
    print("\n🔐 Autenticando...")
    token = login()
    if not token:
        print("❌ Falha na autenticação")
        return
    print("✅ Autenticado!")
    
    # Dados de correlação do notebook
    correlations = [
        {
            "name": "Correlation_Users_Activity",
            "label": "Correlação: Atividade Usuário vs Rating",
            "metric_name": "Usuários - Nº Avaliações vs Rating",
            "correlation": -0.1378,
            "interpretation": "Fraca negativa",
            "insight": "Usuários mais ativos tendem a ser ligeiramente mais críticos"
        },
        {
            "name": "Correlation_Movies_Popularity",
            "label": "Correlação: Popularidade Filme vs Rating",
            "metric_name": "Filmes - Nº Avaliações vs Rating",
            "correlation": 0.4297,
            "interpretation": "Moderada positiva",
            "insight": "Filmes populares tendem a ter melhores avaliações"
        },
        {
            "name": "Correlation_Users_Age",
            "label": "Correlação: Idade Usuário vs Rating",
            "metric_name": "Usuários - Idade vs Rating",
            "correlation": 0.0928,
            "interpretation": "Muito fraca",
            "insight": "Idade tem pouco impacto nas avaliações"
        }
    ]
    
    print(f"\n📤 Enviando {len(correlations)} métricas de correlação...\n")
    
    success_count = 0
    
    for corr in correlations:
        print(f"🔹 {corr['metric_name']}")
        
        device = create_or_get_device(
            token,
            name=corr['name'],
            device_type="eda_correlation",
            label=corr['label']
        )
        
        if not device:
            print(f"   ❌ Erro ao criar device")
            continue
        
        device_id = device['id']['id']
        
        # Telemetria
        telemetry = {
            "correlation": corr['correlation'],
            "correlation_abs": abs(corr['correlation']),
            "correlation_percent": round(corr['correlation'] * 100, 2)
        }
        
        # Atributos
        attributes = {
            "metric_name": corr['metric_name'],
            "interpretation": corr['interpretation'],
            "insight": corr['insight'],
            "analysis_type": "Pearson Correlation",
            "dataset": "MovieLens 100K"
        }
        
        if send_telemetry(token, device_id, telemetry):
            send_attributes(token, device_id, attributes)
            success_count += 1
            print(f"   ✅ Correlação: {corr['correlation']:.4f} ({corr['interpretation']})")
        else:
            print(f"   ❌ Erro ao enviar")
    
    # Criar device com todas as correlações juntas (para gráfico de barras)
    print(f"\n🔹 Criando device consolidado para gráfico de barras...")
    
    device = create_or_get_device(
        token,
        name="EDA_All_Correlations",
        device_type="eda_summary",
        label="Resumo de Correlações - EDA"
    )
    
    if device:
        device_id = device['id']['id']
        
        telemetry = {
            "corr_users_activity": -0.1378,
            "corr_movies_popularity": 0.4297,
            "corr_users_age": 0.0928
        }
        
        attributes = {
            "analysis": "Análise de Correlação - EDA",
            "dataset": "MovieLens 100K",
            "method": "Pearson Correlation"
        }
        
        if send_telemetry(token, device_id, telemetry):
            send_attributes(token, device_id, attributes)
            print(f"   ✅ Device consolidado criado!")
            success_count += 1
    
    print("\n" + "=" * 70)
    print(f"✅ {success_count} devices sincronizados!")
    print("=" * 70)
    
    print("\n📊 RESUMO DAS CORRELAÇÕES:")
    print("-" * 50)
    for corr in sorted(correlations, key=lambda x: abs(x['correlation']), reverse=True):
        bar = "█" * int(abs(corr['correlation']) * 20)
        sign = "+" if corr['correlation'] > 0 else ""
        print(f"   {corr['metric_name']:<35} {sign}{corr['correlation']:.4f} {bar}")
    
    print("\n💡 Devices criados:")
    print("   - Correlation_Users_Activity")
    print("   - Correlation_Movies_Popularity")
    print("   - Correlation_Users_Age")
    print("   - EDA_All_Correlations (consolidado)")


if __name__ == "__main__":
    main()

