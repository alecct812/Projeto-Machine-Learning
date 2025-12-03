#!/bin/bash

# Script para verificar se ThingsBoard está pronto e sincronizar dados

echo "============================================================"
echo "🔍 VERIFICANDO THINGSBOARD"
echo "============================================================"

# Função para testar ThingsBoard
testar_thingsboard() {
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9090/login 2>/dev/null)
    if [ "$STATUS" = "200" ] || [ "$STATUS" = "302" ]; then
        return 0  # Sucesso
    else
        return 1  # Falhou
    fi
}

# Aguardar ThingsBoard
echo ""
echo "⏳ Aguardando ThingsBoard inicializar..."
echo "   (Isso pode levar 3-5 minutos na primeira vez)"
echo ""

TENTATIVAS=0
MAX_TENTATIVAS=30  # 30 tentativas = 5 minutos

while [ $TENTATIVAS -lt $MAX_TENTATIVAS ]; do
    TENTATIVAS=$((TENTATIVAS + 1))
    SEGUNDOS=$((TENTATIVAS * 10))
    
    echo "   ⏱️  Tentativa $TENTATIVAS/$MAX_TENTATIVAS ($SEGUNDOS segundos)..."
    
    if testar_thingsboard; then
        echo ""
        echo "✅ ThingsBoard está PRONTO!"
        echo ""
        echo "============================================================"
        echo "📊 SINCRONIZANDO DADOS"
        echo "============================================================"
        echo ""
        
        # Sincronizar dados
        echo "🔄 Enviando dados para o ThingsBoard..."
        curl -X POST http://localhost:8000/thingsboard/sync
        
        echo ""
        echo ""
        echo "============================================================"
        echo "✅ TUDO PRONTO!"
        echo "============================================================"
        echo ""
        echo "📺 Acesse o ThingsBoard no navegador:"
        echo ""
        echo "   URL: http://localhost:9090"
        echo ""
        echo "🔑 Credenciais de login:"
        echo ""
        echo "   Email:    tenant@thingsboard.org"
        echo "   Password: tenant"
        echo ""
        echo "📖 Siga o guia completo em:"
        echo "   GUIA_VISUAL_THINGSBOARD.md"
        echo ""
        echo "============================================================"
        
        exit 0
    fi
    
    sleep 10
done

echo ""
echo "❌ ThingsBoard não iniciou após 5 minutos"
echo ""
echo "🔍 Ver logs:"
echo "   docker-compose logs thingsboard --tail=50"
echo ""
echo "🔄 Reiniciar ThingsBoard:"
echo "   docker-compose restart thingsboard"
echo ""

exit 1

