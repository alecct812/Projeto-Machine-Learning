#!/bin/bash
# Setup Automático 100% - MovieLens ThingsBoard Dashboard

echo "============================================================"
echo "🚀 Setup Automático - MovieLens ThingsBoard"
echo "============================================================"

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Aguardar ThingsBoard ficar pronto
echo -e "\n${YELLOW}⏳ Aguardando ThingsBoard iniciar...${NC}"
sleep 30

# 2. Sincronizar dados
echo -e "\n${YELLOW}📊 Sincronizando dados do PostgreSQL → ThingsBoard...${NC}"
curl -X POST http://localhost:8000/thingsboard/sync

# 3. Criar dashboard automaticamente
echo -e "\n${YELLOW}🎨 Criando dashboard automaticamente...${NC}"
response=$(curl -X POST http://localhost:8000/thingsboard/create-dashboard)

# Extrair dashboard_id da resposta JSON
dashboard_id=$(echo $response | grep -o '"dashboard_id":"[^"]*"' | cut -d'"' -f4)

# 4. Iniciar sincronização contínua
echo -e "\n${YELLOW}🔄 Iniciando sincronização contínua (5 min)...${NC}"
docker exec -d movielens_fastapi python sync_thingsboard.py --continuous --interval 300

echo ""
echo "============================================================"
echo -e "${GREEN}✅ Setup Concluído - Dashboard Criado Automaticamente!${NC}"
echo "============================================================"
echo ""
echo "🌐 Dashboard URL: http://localhost:9090/dashboards/$dashboard_id"
echo "👤 Login: tenant@thingsboard.org"
echo "🔑 Senha: tenant"
echo ""
echo "📊 Widgets criados:"
echo "  • 4 Cards de estatísticas (Usuários, Filmes, Ratings, Média)"
echo "  • 1 Tabela de Top Filmes"
echo ""
echo "🔄 Sincronização automática: A cada 5 minutos"
echo "============================================================"
