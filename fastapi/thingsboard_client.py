"""
ThingsBoard Client - Integração com ThingsBoard IoT Platform
Envia dados e métricas do sistema de recomendação para visualização
"""
import os
import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ThingsBoardClient:
    """Cliente para comunicação com ThingsBoard via API REST"""
    
    def __init__(
        self,
        base_url: str = None,
        username: str = "tenant@thingsboard.org",
        password: str = "tenant"
    ):
        """
        Inicializa o cliente ThingsBoard
        
        Args:
            base_url: URL base do ThingsBoard (ex: http://localhost:9090)
            username: Username para login (default: tenant@thingsboard.org)
            password: Password para login (default: tenant)
        """
        self.base_url = base_url or os.getenv("THINGSBOARD_URL", "http://thingsboard:9090")
        self.username = username
        self.password = password
        self.token = None
        self.device_tokens = {}
        
    def login(self) -> bool:
        """
        Faz login no ThingsBoard e obtém token JWT
        
        Returns:
            bool: True se login bem-sucedido
        """
        try:
            url = f"{self.base_url}/api/auth/login"
            payload = {
                "username": self.username,
                "password": self.password
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            self.token = data.get("token")
            
            if self.token:
                logger.info(f"✅ Login no ThingsBoard realizado com sucesso!")
                return True
            else:
                logger.error(f"❌ Token não encontrado na resposta")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erro ao fazer login no ThingsBoard: {e}")
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """Retorna headers com token de autenticação"""
        return {
            "Content-Type": "application/json",
            "X-Authorization": f"Bearer {self.token}"
        }
    
    def get_device_by_name(self, device_name: str) -> Optional[Dict]:
        """
        Busca um dispositivo existente pelo nome
        
        Args:
            device_name: Nome do dispositivo
            
        Returns:
            Dict com informações do dispositivo ou None
        """
        if not self.token:
            if not self.login():
                return None
        
        try:
            url = f"{self.base_url}/api/tenant/devices?deviceName={device_name}"
            
            response = requests.get(
                url,
                headers=self.get_headers(),
                timeout=10
            )
            response.raise_for_status()
            
            device = response.json()
            if device:
                logger.info(f"📱 Dispositivo '{device_name}' encontrado!")
                return device
            return None
            
        except requests.exceptions.RequestException as e:
            logger.debug(f"Dispositivo '{device_name}' não encontrado: {e}")
            return None
    
    def create_device(self, device_name: str, device_type: str = "default") -> Optional[Dict]:
        """
        Cria um dispositivo no ThingsBoard ou retorna existente
        
        Args:
            device_name: Nome do dispositivo
            device_type: Tipo do dispositivo
            
        Returns:
            Dict com informações do dispositivo criado
        """
        if not self.token:
            logger.warning("Token não disponível. Fazendo login...")
            if not self.login():
                return None
        
        # Tentar buscar dispositivo existente primeiro
        existing_device = self.get_device_by_name(device_name)
        if existing_device:
            device = existing_device
            logger.info(f"♻️ Usando dispositivo existente '{device_name}'")
        else:
            # Criar novo dispositivo
            try:
                url = f"{self.base_url}/api/device"
                payload = {
                    "name": device_name,
                    "type": device_type
                }
                
                response = requests.post(
                    url,
                    json=payload,
                    headers=self.get_headers(),
                    timeout=10
                )
                response.raise_for_status()
                
                device = response.json()
                logger.info(f"✅ Dispositivo '{device_name}' criado com sucesso!")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Erro ao criar dispositivo: {e}")
                return None
        
        # Obter access token do dispositivo
        device_id = device.get("id", {}).get("id")
        if device_id:
            token = self.get_device_token(device_id)
            if token:
                self.device_tokens[device_name] = token
                device["access_token"] = token
        
        return device
    
    def get_device_token(self, device_id: str) -> Optional[str]:
        """
        Obtém o access token de um dispositivo
        
        Args:
            device_id: ID do dispositivo
            
        Returns:
            Access token do dispositivo
        """
        try:
            url = f"{self.base_url}/api/device/{device_id}/credentials"
            
            response = requests.get(
                url,
                headers=self.get_headers(),
                timeout=10
            )
            response.raise_for_status()
            
            credentials = response.json()
            token = credentials.get("credentialsId")
            
            return token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erro ao obter token do dispositivo: {e}")
            return None
    
    def send_attributes(
        self,
        device_id: str,
        attributes: Dict[str, Any]
    ) -> bool:
        """
        Envia atributos (server-side) para um dispositivo
        
        Args:
            device_id: ID do dispositivo
            attributes: Dict com atributos a serem definidos
            
        Returns:
            bool: True se enviado com sucesso
        """
        try:
            url = f"{self.base_url}/api/plugins/telemetry/DEVICE/{device_id}/attributes/SERVER_SCOPE"
            
            response = requests.post(
                url,
                json=attributes,
                headers=self.get_headers(),
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f"✅ Atributos enviados com sucesso!")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erro ao enviar atributos: {e}")
            return False
    
    def send_telemetry(
        self,
        device_token: str,
        telemetry_data: Dict[str, Any]
    ) -> bool:
        """
        Envia dados de telemetria para um dispositivo
        
        Args:
            device_token: Access token do dispositivo
            telemetry_data: Dados a serem enviados (dict com key-value pairs)
            
        Returns:
            bool: True se enviado com sucesso
        """
        try:
            url = f"{self.base_url}/api/v1/{device_token}/telemetry"
            
            response = requests.post(
                url,
                json=telemetry_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f"✅ Telemetria enviada com sucesso!")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erro ao enviar telemetria: {e}")
            return False
    
    def send_ml_metrics(
        self,
        device_name: str,
        metrics: Dict[str, float]
    ) -> bool:
        """
        Envia métricas de ML para ThingsBoard
        
        Args:
            device_name: Nome do dispositivo (ex: "ml_model_v1")
            metrics: Dict com métricas (ex: {"rmse": 0.95, "precision_10": 0.82})
            
        Returns:
            bool: True se enviado com sucesso
        """
        # Verificar se já temos o token do dispositivo
        if device_name not in self.device_tokens:
            # Tentar criar o dispositivo
            device = self.create_device(device_name, "ML_Model")
            if not device:
                return False
        
        device_token = self.device_tokens[device_name]
        
        # Adicionar timestamp
        metrics["timestamp"] = int(datetime.now().timestamp() * 1000)
        
        return self.send_telemetry(device_token, metrics)
    
    def send_recommendation_stats(
        self,
        stats: Dict[str, Any]
    ) -> bool:
        """
        Envia estatísticas do sistema de recomendação
        
        Args:
            stats: Dict com estatísticas (total_users, total_movies, etc.)
            
        Returns:
            bool: True se enviado com sucesso
        """
        device_name = "recommendation_system"
        return self.send_ml_metrics(device_name, stats)
    
    def send_user_activity(
        self,
        user_id: int,
        activity_data: Dict[str, Any]
    ) -> bool:
        """
        Envia dados de atividade de usuários
        
        Args:
            user_id: ID do usuário
            activity_data: Dict com dados de atividade
            
        Returns:
            bool: True se enviado com sucesso
        """
        device_name = f"user_{user_id}"
        return self.send_ml_metrics(device_name, activity_data)
    
    def get_or_create_device(self, device_name: str, device_type: str = "default") -> Optional[str]:
        """
        Obtém o token de um dispositivo existente ou cria um novo
        
        Args:
            device_name: Nome do dispositivo
            device_type: Tipo do dispositivo
            
        Returns:
            Access token do dispositivo
        """
        if device_name in self.device_tokens:
            return self.device_tokens[device_name]
        
        device = self.create_device(device_name, device_type)
        if device and "access_token" in device:
            return device["access_token"]
        
        return None


# Exemplo de uso
if __name__ == "__main__":
    # Inicializar cliente
    tb_client = ThingsBoardClient()
    
    # Fazer login
    if tb_client.login():
        print("Login realizado com sucesso!")
        
        # Criar dispositivo para métricas de ML
        device = tb_client.create_device("ml_model_kmeans_knn", "ML_Model")
        
        if device:
            print(f"Dispositivo criado: {device.get('name')}")
            print(f"Device ID: {device.get('id', {}).get('id')}")
            print(f"Access Token: {device.get('access_token')}")
            
            # Enviar métricas de exemplo
            metrics = {
                "rmse": 0.9234,
                "precision_at_10": 0.8543,
                "recall_at_10": 0.7821,
                "coverage": 0.6543,
                "num_clusters": 10,
                "training_time_seconds": 45.23
            }
            
            success = tb_client.send_ml_metrics("ml_model_kmeans_knn", metrics)
            print(f"Métricas enviadas: {success}")
    else:
        print("Erro no login!")
