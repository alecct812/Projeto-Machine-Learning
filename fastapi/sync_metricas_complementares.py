#!/usr/bin/env python3
"""
Script para sincronizar métricas complementares de avaliação com ThingsBoard
"""

import os
import sys
import requests
from datetime import datetime

# Configurações do ThingsBoard
THINGSBOARD_URL = os.getenv("THINGSBOARD_URL", "http://thingsboard:9090")
THINGSBOARD_USERNAME = os.getenv("THINGSBOARD_USERNAME", "tenant@thingsboard.org")
THINGSBOARD_PASSWORD = os.getenv("THINGSBOARD_PASSWORD", "tenant")

class ThingsBoardClient:
    def __init__(self):
        self.url = THINGSBOARD_URL
        self.token = None
        self.authenticate()
    
    def authenticate(self):
        """Autentica e obtém token JWT"""
        auth_url = f"{self.url}/api/auth/login"
        credentials = {
            "username": THINGSBOARD_USERNAME,
            "password": THINGSBOARD_PASSWORD
        }
        
        try:
            response = requests.post(auth_url, json=credentials, timeout=10)
            response.raise_for_status()
            self.token = response.json()["token"]
            print("✅ Autenticado no ThingsBoard com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao autenticar: {e}")
            sys.exit(1)
    
    def get_headers(self):
        """Retorna headers com token de autenticação"""
        return {
            "Content-Type": "application/json",
            "X-Authorization": f"Bearer {self.token}"
        }
    
    def create_or_get_device(self, device_name, device_type="default"):
        """Cria ou obtém device existente"""
        # Buscar device
        search_url = f"{self.url}/api/tenant/devices?deviceName={device_name}"
        response = requests.get(search_url, headers=self.get_headers())
        
        if response.status_code == 200 and response.json():
            device_id = response.json()["id"]["id"]
            print(f"✅ Device '{device_name}' já existe: {device_id}")
            return device_id
        
        # Criar device
        create_url = f"{self.url}/api/device"
        device_data = {
            "name": device_name,
            "type": device_type,
            "label": device_name
        }
        
        response = requests.post(create_url, headers=self.get_headers(), json=device_data)
        if response.status_code in [200, 201]:
            device_id = response.json()["id"]["id"]
            print(f"✅ Device '{device_name}' criado: {device_id}")
            return device_id
        else:
            print(f"❌ Erro ao criar device: {response.text}")
            return None
    
    def send_telemetry(self, device_id, data):
        """Envia telemetria para um device"""
        url = f"{self.url}/api/plugins/telemetry/DEVICE/{device_id}/timeseries/ANY"
        response = requests.post(url, headers=self.get_headers(), json=data)
        
        if response.status_code in [200, 201]:
            print(f"✅ Telemetria enviada com sucesso!")
            return True
        else:
            print(f"❌ Erro ao enviar telemetria: {response.text}")
            return False
    
    def send_attributes(self, device_id, attributes):
        """Envia atributos para um device"""
        url = f"{self.url}/api/plugins/telemetry/DEVICE/{device_id}/attributes/SERVER_SCOPE"
        response = requests.post(url, headers=self.get_headers(), json=attributes)
        
        if response.status_code in [200, 201]:
            print(f"✅ Atributos enviados com sucesso!")
            return True
        else:
            print(f"❌ Erro ao enviar atributos: {response.text}")
            return False


def sync_metricas_complementares():
    """Sincroniza métricas complementares de avaliação"""
    
    print("\n" + "="*70)
    print("📊 SINCRONIZANDO MÉTRICAS COMPLEMENTARES DE AVALIAÇÃO")
    print("="*70 + "\n")
    
    client = ThingsBoardClient()
    
    # Métricas extraídas do notebook
    metricas = [
        {
            "name": "Metricas_Precisao_Recall_K5",
            "label": "Métricas de Ranking K=5",
            "data": {
                "precision": 0.8000,
                "recall": 0.0004,
                "k": 5,
                "precision_percent": 80.00,
                "recall_percent": 0.04
            }
        },
        {
            "name": "Metricas_Precisao_Recall_K10",
            "label": "Métricas de Ranking K=10",
            "data": {
                "precision": 0.7000,
                "recall": 0.0006,
                "k": 10,
                "precision_percent": 70.00,
                "recall_percent": 0.06
            }
        },
        {
            "name": "Metricas_Precisao_Recall_K20",
            "label": "Métricas de Ranking K=20",
            "data": {
                "precision": 0.7000,
                "recall": 0.0013,
                "k": 20,
                "precision_percent": 70.00,
                "recall_percent": 0.13
            }
        }
    ]
    
    timestamp = int(datetime.now().timestamp() * 1000)
    
    for metrica in metricas:
        print(f"\n📍 Processando: {metrica['label']}")
        
        # Criar ou obter device
        device_id = client.create_or_get_device(
            device_name=metrica["name"],
            device_type="metrics"
        )
        
        if not device_id:
            continue
        
        # Enviar telemetria
        telemetry = {
            "ts": timestamp,
            "values": metrica["data"]
        }
        client.send_telemetry(device_id, telemetry)
        
        # Enviar atributos
        attributes = {
            "label": metrica["label"],
            "metric_type": "ranking",
            "k_value": metrica["data"]["k"]
        }
        client.send_attributes(device_id, attributes)
    
    # Criar device para métricas de erro (do Paper Original)
    print(f"\n📍 Processando: Métricas de Erro do Paper Original")
    
    device_id = client.create_or_get_device(
        device_name="Metricas_Erro_Paper_Original",
        device_type="metrics"
    )
    
    if device_id:
        telemetry = {
            "ts": timestamp,
            "values": {
                "rmse": 1.0807,
                "mae": 0.8455,
                "mae_menor_que_rmse_percent": 27.8
            }
        }
        client.send_telemetry(device_id, telemetry)
        
        attributes = {
            "label": "Métricas de Erro - Paper Original",
            "metric_type": "error",
            "interpretacao": "Em média, erramos 0.85 estrelas nas predições"
        }
        client.send_attributes(device_id, attributes)
    
    # Criar device para métricas de cobertura
    print(f"\n📍 Processando: Métricas de Cobertura")
    
    device_id = client.create_or_get_device(
        device_name="Metricas_Cobertura",
        device_type="metrics"
    )
    
    if device_id:
        telemetry = {
            "ts": timestamp,
            "values": {
                "total_filmes": 1682,
                "erro_maior_2_estrelas_percent": 6.8
            }
        }
        client.send_telemetry(device_id, telemetry)
        
        attributes = {
            "label": "Métricas de Cobertura do Catálogo",
            "metric_type": "coverage"
        }
        client.send_attributes(device_id, attributes)
    
    print("\n" + "="*70)
    print("✅ SINCRONIZAÇÃO DE MÉTRICAS COMPLEMENTARES CONCLUÍDA!")
    print("="*70 + "\n")


if __name__ == "__main__":
    sync_metricas_complementares()

