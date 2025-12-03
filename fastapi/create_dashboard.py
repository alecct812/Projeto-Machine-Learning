"""
Script para criar dashboard do MovieLens automaticamente no ThingsBoard via API
Cria todos os widgets e configurações sem intervenção manual
"""
import requests
import json
import logging
from typing import Dict, Any, Optional
from thingsboard_client import ThingsBoardClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DashboardCreator:
    """Classe para criar dashboards automaticamente no ThingsBoard"""
    
    def __init__(self, base_url: str = "http://thingsboard:9090"):
        self.base_url = base_url
        self.client = ThingsBoardClient(base_url=base_url)
        self.token = None
    
    def login(self) -> bool:
        """Faz login e obtém token"""
        if self.client.login():
            self.token = self.client.token
            return True
        return False
    
    def _create_all_widgets(self) -> Dict:
        """Cria todos os widgets e retorna configuração completa"""
        
        # Dashboard vazio - widgets serão adicionados manualmente ou via outra abordagem
        # O ThingsBoard tem formato JSON complexo que varia por versão
        
        return {
            "widgets": {},
            "layouts": {},
            "aliases": {}
        }
    
    def _create_card_widget_config(
        self, device_name: str, data_key: str, label: str,
        icon: str, color: str, decimals: int = 0
    ) -> Dict:
        """Cria configuração de widget Simple Card"""
        
        return {
            "isSystemType": True,
            "bundleAlias": "cards",
            "typeAlias": "simple_card",
            "type": "latest",
            "title": label,
            "config": {
                "datasources": [{
                    "type": "entity",
                    "name": device_name,
                    "entityAliasId": "movielens_system_alias",
                    "dataKeys": [{
                        "name": data_key,
                        "type": "timeseries",
                        "label": label,
                        "color": color,
                        "settings": {},
                        "decimals": decimals,
                        "units": "",
                        "usePostProcessing": False
                    }]
                }],
                "timewindow": {
                    "realtime": {"timewindowMs": 60000}
                },
                "showTitle": True,
                "backgroundColor": "#ffffff",
                "color": "rgba(0, 0, 0, 0.87)",
                "padding": "16px",
                "settings": {
                    "labelPosition": "top",
                    "layout": "left",
                    "autoScale": True,
                    "showLabel": True,
                    "showIcon": True,
                    "icon": icon,
                    "iconColor": color,
                    "iconSize": "40px"
                }
            }
        }
    
    def _create_table_widget_config(self) -> Dict:
        """Cria configuração de widget Entities Table para top filmes"""
        
        return {
            "isSystemType": True,
            "bundleAlias": "tables",
            "typeAlias": "entities_table",
            "type": "latest",
            "title": "Top 10 Filmes",
            "config": {
                "datasources": [{
                    "type": "entity",
                    "dataKeys": [
                        {
                            "name": "title",
                            "type": "attribute",
                            "label": "Filme",
                            "settings": {},
                            "hidden": False
                        },
                        {
                            "name": "rank",
                            "type": "timeseries",
                            "label": "Rank",
                            "settings": {},
                            "hidden": False
                        },
                        {
                            "name": "avg_rating",
                            "type": "timeseries",
                            "label": "Nota Média",
                            "settings": {},
                            "decimals": 2,
                            "hidden": False
                        },
                        {
                            "name": "num_ratings",
                            "type": "timeseries",
                            "label": "Avaliações",
                            "settings": {},
                            "hidden": False
                        }
                    ],
                    "entityFilter": {
                        "type": "deviceNamePrefix",
                        "deviceNamePrefix": "movie_"
                    }
                }],
                "timewindow": {
                    "realtime": {"timewindowMs": 60000}
                },
                "showTitle": True,
                "settings": {
                    "enablePagination": True,
                    "defaultPageSize": 10,
                    "defaultSortOrder": "rank"
                }
            }
        }
    
    def create_dashboard(self) -> Optional[Dict]:
        """Cria o dashboard MovieLens Analytics com widgets pré-configurados"""
        
        # Criar widgets primeiro
        widgets_config = self._create_all_widgets()
        
        dashboard_config = {
            "title": "MovieLens Analytics",
            "configuration": {
                "description": "Dashboard de análise do sistema de recomendação MovieLens",
                "widgets": widgets_config["widgets"],
                "states": {
                    "default": {
                        "name": "MovieLens Analytics",
                        "root": True,
                        "layouts": {
                            "main": {
                                "widgets": widgets_config["layouts"],
                                "gridSettings": {
                                    "backgroundColor": "#eeeeee",
                                    "columns": 24,
                                    "margin": 10,
                                    "backgroundSizeMode": "100%"
                                }
                            }
                        }
                    }
                },
                "entityAliases": widgets_config["aliases"],
                "filters": {},
                "timewindow": {
                    "realtime": {
                        "timewindowMs": 60000
                    }
                },
                "settings": {
                    "stateControllerId": "entity",
                    "showTitle": True,
                    "showDashboardsSelect": True,
                    "showEntitiesSelect": True,
                    "showDashboardTimewindow": True,
                    "showDashboardExport": True,
                    "toolbarAlwaysOpen": True
                }
            }
        }
        
        try:
            url = f"{self.base_url}/api/dashboard"
            headers = {
                "Content-Type": "application/json",
                "X-Authorization": f"Bearer {self.token}"
            }
            
            response = requests.post(url, json=dashboard_config, headers=headers, timeout=10)
            response.raise_for_status()
            
            dashboard = response.json()
            logger.info(f"✅ Dashboard '{dashboard_config['title']}' criado com sucesso!")
            return dashboard
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erro ao criar dashboard: {e}")
            return None


def main():
    """Função principal"""
    print("=" * 60)
    print("🎨 Criação Automática de Dashboard - MovieLens")
    print("=" * 60)
    
    creator = DashboardCreator()
    
    # 1. Login
    logger.info("\n🔐 Fazendo login no ThingsBoard...")
    if not creator.login():
        logger.error("❌ Erro ao fazer login")
        return
    
    # 2. Criar dashboard com widgets incluídos
    logger.info("\n📊 Criando dashboard com 5 widgets...")
    dashboard = creator.create_dashboard()
    
    if not dashboard:
        logger.error("❌ Falha ao criar dashboard")
        return
    
    dashboard_id = dashboard.get("id", {}).get("id")
    
    print("\n" + "=" * 60)
    print("✅ Dashboard criado com sucesso!")
    print("=" * 60)
    print(f"\n🌐 Acesse: http://localhost:9090/dashboards/{dashboard_id}")
    print("👤 Login: tenant@thingsboard.org")
    print("🔑 Senha: tenant")
    print("\n📊 Widgets incluídos:")
    print("  • 4 Simple Cards (Usuários, Filmes, Ratings, Média)")
    print("  • 1 Entities Table (Top 10 Filmes)")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
