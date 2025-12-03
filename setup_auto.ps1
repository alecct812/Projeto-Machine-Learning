# Setup Automático 100% - MovieLens ThingsBoard Dashboard
# PowerShell Version

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🚀 Setup Automático - MovieLens ThingsBoard" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Aguardar ThingsBoard ficar pronto
Write-Host "`n⏳ Aguardando ThingsBoard iniciar..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# 2. Sincronizar dados
Write-Host "`n📊 Sincronizando dados do PostgreSQL → ThingsBoard..." -ForegroundColor Yellow
$syncResponse = Invoke-RestMethod -Uri "http://localhost:8000/thingsboard/sync" -Method POST

if ($syncResponse.status -eq "success") {
    Write-Host "✅ Dados sincronizados com sucesso!" -ForegroundColor Green
} else {
    Write-Host "⚠️ Aviso: Sincronização pode ter falhado" -ForegroundColor Yellow
}

# 3. Criar dashboard automaticamente
Write-Host "`n🎨 Criando dashboard automaticamente..." -ForegroundColor Yellow
try {
    $dashboardResponse = Invoke-RestMethod -Uri "http://localhost:8000/thingsboard/create-dashboard" -Method POST
    
    $dashboardId = $dashboardResponse.dashboard_id
    $dashboardUrl = $dashboardResponse.dashboard_url
    
    Write-Host "✅ Dashboard criado com sucesso!" -ForegroundColor Green
} catch {
    Write-Host "❌ Erro ao criar dashboard: $_" -ForegroundColor Red
    Write-Host "Verifique se o ThingsBoard está rodando e acessível" -ForegroundColor Yellow
    exit 1
}

# 4. Iniciar sincronização contínua
Write-Host "`n🔄 Iniciando sincronização contínua (5 min)..." -ForegroundColor Yellow
docker exec -d movielens_fastapi python sync_thingsboard.py --continuous --interval 300
Write-Host "✅ Sincronização contínua iniciada" -ForegroundColor Green

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "✅ Setup Concluído - Dashboard Criado Automaticamente!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 Dashboard URL: " -NoNewline
Write-Host $dashboardUrl -ForegroundColor Blue
Write-Host "👤 Login: " -NoNewline
Write-Host "tenant@thingsboard.org" -ForegroundColor Yellow
Write-Host "🔑 Senha: " -NoNewline
Write-Host "tenant" -ForegroundColor Yellow
Write-Host ""
Write-Host "📊 Widgets criados:" -ForegroundColor White
Write-Host "  • 4 Cards de estatísticas (Usuários, Filmes, Ratings, Média)" -ForegroundColor Gray
Write-Host "  • 1 Tabela de Top Filmes" -ForegroundColor Gray
Write-Host ""
Write-Host "🔄 Sincronização automática: " -NoNewline
Write-Host "A cada 5 minutos" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
