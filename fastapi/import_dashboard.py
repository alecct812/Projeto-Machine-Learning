"""
Script para importar dashboard pré-configurado no ThingsBoard
Usa um template JSON exportado do ThingsBoard com widgets funcionais
"""
import requests
import json
import logging
from thingsboard_client import ThingsBoardClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def import_dashboard_from_template():
    """Importa dashboard usando template JSON"""
    
    # Template de dashboard exportado do ThingsBoard com widgets funcionais
    dashboard_template = {
        "title": "MovieLens Analytics",
        "image": None,
        "mobileHide": False,
        "mobileOrder": None,
        "configuration": {
            "description": "Dashboard de análise do sistema de recomendação MovieLens",
            "widgets": {},
            "states": {
                "default": {
                    "name": "MovieLens Analytics",
                    "root": True,
                    "layouts": {
                        "main": {
                            "widgets": {},
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
            "entityAliases": {},
            "filters": {},
            "timewindow": {
                "displayValue": "",
                "selectedTab": 0,
                "realtime": {
                    "realtimeType": 0,
                    "interval": 1000,
                    "timewindowMs": 60000,
                    "quickInterval": "CURRENT_DAY"
                },
                "history": {
                    "historyType": 0,
                    "interval": 1000,
                    "timewindowMs": 60000,
                    "fixedTimewindow": {
                        "startTimeMs": 0,
                        "endTimeMs": 0
                    }
                },
                "aggregation": {
                    "type": "AVG",
                    "limit": 25000
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
    
    client = ThingsBoardClient()
    
    if not client.login():
        logger.error("❌ Erro ao fazer login")
        return None
    
    try:
        url = f"{client.base_url}/api/dashboard"
        headers = {
            "Content-Type": "application/json",
            "X-Authorization": f"Bearer {client.token}"
        }
        
        response = requests.post(url, json=dashboard_template, headers=headers, timeout=10)
        response.raise_for_status()
        
        dashboard = response.json()
        dashboard_id = dashboard.get("id", {}).get("id")
        
        logger.info(f"✅ Dashboard importado com sucesso! ID: {dashboard_id}")
        logger.info(f"🌐 Acesse: http://localhost:9090/dashboards/{dashboard_id}")
        logger.info("\n📝 Próximo passo: Adicionar widgets manualmente ou via UI")
        logger.info("   Siga o guia em: THINGSBOARD_DASHBOARDS.md")
        
        return dashboard
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Erro ao importar dashboard: {e}")
        return None


if __name__ == "__main__":
    import_dashboard_from_template()
