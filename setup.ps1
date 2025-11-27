# Script de inicialização automática do projeto MovieLens
# Executa todo o pipeline de forma automatizada

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  MovieLens ML Pipeline - Auto Setup   " -ForegroundColor Cyan
Write-Host "  CESAR School - AM 2025.2             " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se Docker está rodando
Write-Host "1️⃣  Verificando Docker..." -ForegroundColor Yellow
try {
    docker --version | Out-Null
    Write-Host "   ✅ Docker instalado" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Docker não encontrado! Instale o Docker Desktop." -ForegroundColor Red
    exit 1
}

docker ps | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ❌ Docker não está rodando! Inicie o Docker Desktop." -ForegroundColor Red
    exit 1
}
Write-Host "   ✅ Docker está rodando" -ForegroundColor Green
Write-Host ""

# Iniciar containers
Write-Host "2️⃣  Iniciando containers (pode levar 5-10 min)..." -ForegroundColor Yellow
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "   ❌ Erro ao iniciar containers!" -ForegroundColor Red
    exit 1
}
Write-Host "   ✅ Containers iniciados" -ForegroundColor Green
Write-Host ""

# Aguardar inicialização
Write-Host "3️⃣  Aguardando inicialização dos serviços (180s)..." -ForegroundColor Yellow
Write-Host "   ⏳ Pode tomar um café... ☕" -ForegroundColor Cyan

for ($i = 180; $i -gt 0; $i--) {
    Write-Progress -Activity "Aguardando inicialização" -Status "$i segundos restantes" -PercentComplete ((180 - $i) / 180 * 100)
    Start-Sleep -Seconds 1
}

Write-Host "   ✅ Aguarde concluído" -ForegroundColor Green
Write-Host ""

# Verificar status dos containers
Write-Host "4️⃣  Verificando status dos containers..." -ForegroundColor Yellow
$containers = docker-compose ps --format json | ConvertFrom-Json

$allRunning = $true
foreach ($container in $containers) {
    $status = $container.State
    if ($status -eq "running") {
        Write-Host "   ✅ $($container.Service) - Running" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $($container.Service) - $status" -ForegroundColor Red
        $allRunning = $false
    }
}

if (-not $allRunning) {
    Write-Host ""
    Write-Host "⚠️  Alguns containers não estão rodando!" -ForegroundColor Yellow
    Write-Host "Execute: docker-compose logs [nome-container]" -ForegroundColor Cyan
    Write-Host ""
    
    $continue = Read-Host "Deseja continuar mesmo assim? (s/N)"
    if ($continue -ne "s" -and $continue -ne "S") {
        Write-Host "Abortando..." -ForegroundColor Red
        exit 1
    }
}
Write-Host ""

# Ingerir dados
Write-Host "5️⃣  Ingerindo dados no MinIO..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/ingest/movielens" -Method POST -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✅ Dados ingeridos com sucesso" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Status: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Erro ao ingerir dados: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   Tentando método alternativo..." -ForegroundColor Yellow
    
    docker-compose exec -T fastapi python load_data.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Dados ingeridos via container" -ForegroundColor Green
    }
}
Write-Host ""

# Executar ETL
Write-Host "6️⃣  Executando ETL (MinIO → PostgreSQL)..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/etl/run" -Method POST -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✅ ETL executado com sucesso" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Status: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Erro ao executar ETL: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   Tentando método alternativo..." -ForegroundColor Yellow
    
    docker-compose exec -T fastapi python etl_minio_postgres.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ ETL executado via container" -ForegroundColor Green
    }
}
Write-Host ""

# Verificar dados no PostgreSQL
Write-Host "7️⃣  Verificando dados no PostgreSQL..." -ForegroundColor Yellow
try {
    $count = docker-compose exec -T postgres psql -U ml_user -d movielens -t -c "SELECT COUNT(*) FROM ratings;"
    $count = $count.Trim()
    
    if ($count -eq "100000") {
        Write-Host "   ✅ 100.000 ratings carregados corretamente" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  $count ratings encontrados (esperado: 100000)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Erro ao verificar dados: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Resumo final
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  🎉 Setup Concluído!                  " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📊 Serviços Disponíveis:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  JupyterLab:     http://localhost:8888" -ForegroundColor Cyan
Write-Host "  MLFlow:         http://localhost:5000" -ForegroundColor Cyan
Write-Host "  FastAPI:        http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  MinIO Console:  http://localhost:9001" -ForegroundColor Cyan
Write-Host "  ThingsBoard:    http://localhost:8080" -ForegroundColor Cyan
Write-Host ""

Write-Host "🔑 Credenciais:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  MinIO:         projeto_ml_admin / cavalo-nimbus-xbox" -ForegroundColor White
Write-Host "  PostgreSQL:    ml_user / ml_password_2025" -ForegroundColor White
Write-Host "  ThingsBoard:   tenant@thingsboard.org / tenant" -ForegroundColor White
Write-Host ""

Write-Host "📝 Próximos Passos:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  1. Abra JupyterLab: http://localhost:8888" -ForegroundColor White
Write-Host "  2. Execute o notebook: notebooks/parte3_analise_modelagem.ipynb" -ForegroundColor White
Write-Host "  3. Visualize experimentos em: http://localhost:5000" -ForegroundColor White
Write-Host "  4. Configure dashboards em: http://localhost:8080" -ForegroundColor White
Write-Host ""

Write-Host "🛠️  Comandos Úteis:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Ver logs:       docker-compose logs -f [serviço]" -ForegroundColor White
Write-Host "  Parar:          docker-compose down" -ForegroundColor White
Write-Host "  Reiniciar:      docker-compose restart [serviço]" -ForegroundColor White
Write-Host ""

# Oferecer abrir JupyterLab
Write-Host ""
$openJupyter = Read-Host "Deseja abrir o JupyterLab agora? (S/n)"
if ($openJupyter -ne "n" -and $openJupyter -ne "N") {
    Start-Process "http://localhost:8888"
    Write-Host "✅ JupyterLab aberto no navegador" -ForegroundColor Green
}

# Oferecer abrir MLFlow
$openMLFlow = Read-Host "Deseja abrir o MLFlow UI agora? (S/n)"
if ($openMLFlow -ne "n" -and $openMLFlow -ne "N") {
    Start-Process "http://localhost:5000"
    Write-Host "✅ MLFlow UI aberto no navegador" -ForegroundColor Green
}

Write-Host ""
Write-Host "🎓 CESAR School - Aprendizado de Máquina 2025.2" -ForegroundColor Cyan
Write-Host "📚 Leia o QUICKSTART.md para mais informações" -ForegroundColor Cyan
Write-Host ""
Write-Host "Pressione qualquer tecla para sair..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
