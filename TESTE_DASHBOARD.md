# 🎯 TESTE DO DASHBOARD - ThingsBoard

## Status Atual

✅ **1-4: COMPLETOS** (Não mexa!)
- ✅ Ingestão de dados (FastAPI + MinIO)
- ✅ Dados estruturados (PostgreSQL)
- ✅ Modelagem (Notebook Jupyter)
- ✅ MLflow configurado

⚙️ **5: EM IMPLEMENTAÇÃO**
- ✅ ThingsBoard configurado no docker-compose
- ✅ Cliente Python criado (thingsboard_client.py)
- ✅ Endpoint da API criado (/thingsboard/sync)
- ⏳ Aguardando ThingsBoard inicializar (2-3 minutos)

---

## 🚀 Como Testar o Dashboard

### Passo 1: Verificar se todos os containers estão rodando

```bash
docker-compose ps
```

**Você deve ver 5 containers:**
- ✅ movielens_minio (portas 9000, 9001)
- ✅ movielens_postgres (porta 5438)
- ✅ movielens_fastapi (porta 8000)
- ✅ movielens_mlflow (porta 5001)
- ✅ movielens_thingsboard (porta 9090) **← NOVO!**

### Passo 2: Aguardar ThingsBoard inicializar

O ThingsBoard pode demorar **2-3 minutos** para inicializar completamente.

**Verificar se está pronto:**
```bash
curl http://localhost:9090/api/noauth/health
```

Se retornar algo (mesmo vazio), está rodando!

**OU** abra o navegador:
```
http://localhost:9090
```

Se aparecer a tela de login do ThingsBoard, está pronto!

### Passo 3: Sincronizar dados para o ThingsBoard

**Opção A: Via API (recomendado)**
```bash
curl -X POST http://localhost:8000/thingsboard/sync
```

**Opção B: Direto no container**
```bash
docker-compose exec fastapi python thingsboard_client.py
```

**O que será sincronizado:**
1. ✅ **Estatísticas do Dataset** - 6 métricas (total filmes, usuários, avaliações, médias)
2. ✅ **Top 20 Filmes** - Filmes mais bem avaliados com detalhes
3. ✅ **Métricas de Modelos ML** - RMSE, Precision@10, Recall@10 de 3 modelos

### Passo 4: Acessar o ThingsBoard

**URL:**
```
http://localhost:9090
```

**Login:**
- **Usuário:** `tenant@thingsboard.org`
- **Senha:** `tenant`

### Passo 5: Verificar Devices criados

Após o login:

1. Clique em **"Devices"** no menu lateral esquerdo
2. Você deverá ver **24 devices criados:**
   - `Dataset_Statistics` (1 device)
   - `Model_KMeans_KNN_K8`, `Model_KMeans_KNN_K5`, `Model_Baseline_Mean` (3 devices)
   - `Movie_1`, `Movie_2`, ..., `Movie_20` (20 devices)

3. **Clique em um device** (ex: `Dataset_Statistics`)
4. Vá na aba **"Latest telemetry"**
5. Você verá os dados enviados:
   - `total_movies`: 1682
   - `total_users`: 943
   - `total_ratings`: 90570
   - `avg_rating`: 3.52
   - etc.

---

## 📊 Dashboards a Serem Importados

### Dashboard 1: Métricas de Modelos ML

**Widgets:**
- 📊 Card: RMSE (1.12)
- 📊 Card: Precision@10 (0.78)
- 📊 Card: Recall@10 (0.65)
- 📈 Gráfico de linhas: Evolução do RMSE
- 📊 Tabela: Ranking de modelos

**Insights:**
- ✅ K-Means (K=8) + KNN é o melhor modelo (menor RMSE)
- ✅ Baseline tem RMSE 20% pior
- ✅ Trade-off entre Precision e Recall

### Dashboard 2: Estatísticas do Dataset

**Widgets:**
- 🎬 Card: Total de Filmes (1,682)
- 👥 Card: Total de Usuários (943)
- ⭐ Card: Total de Avaliações (90,570)
- 📊 Gauge: Avaliação Média (3.52 / 5.0)

**Insights:**
- ✅ Dataset bem balanceado (média ~3.5)
- ✅ Alta atividade: ~96 avaliações por usuário
- ✅ Boa cobertura: ~54 avaliações por filme

### Dashboard 3: Top Filmes

**Widgets:**
- 🏆 Card grande: #1 Filme mais bem avaliado
- 📊 Gráfico de barras: Top 10 filmes
- 📈 Scatter plot: Avaliação vs Popularidade
- 📋 Tabela completa: Top 20 com detalhes

**Insights:**
- ✅ Filmes mais populares nem sempre são os melhores
- ✅ Existe correlação positiva entre qualidade e popularidade
- ✅ Alguns "hidden gems" (bons mas pouco conhecidos)

---

## 🎨 Como Criar os Dashboards Manualmente

### 1. Criar Dashboard Vazio

1. No ThingsBoard, clique em **"Dashboards"** (menu lateral)
2. Clique no **"+"** (canto inferior direito)
3. Nome: "Métricas de Modelos ML"
4. Clique em **"Add"**

### 2. Adicionar Widget

1. Entre no dashboard criado
2. Clique em **"Enter edit mode"** (ícone de lápis)
3. Clique no **"+"** para adicionar widget
4. Escolha o tipo de widget (ex: "Cards" → "Numeric Card")
5. Configure:
   - **Entity Alias:** Devices → Type: `ml_model` → Device: `Model_KMeans_KNN_K8`
   - **Data Key:** `rmse`
   - **Label:** "RMSE - K-Means + KNN"
   - **Unidades:** deixe vazio
   - **Cor:** verde
6. Clique em **"Add"**
7. Ajuste o tamanho e posição do widget
8. Clique em **"Save"** (disquete no canto superior)

### 3. Adicionar Mais Widgets

Repita o processo para:
- Precision@10 (Gauge)
- Recall@10 (Card)
- Gráfico de linhas (Time Series - Line Chart)
- Tabela (Entities Table)

---

## 🔄 Atualizar Dados

**Sempre que quiser atualizar os dados:**
```bash
curl -X POST http://localhost:8000/thingsboard/sync
```

**OU**
```bash
docker-compose exec fastapi python thingsboard_client.py
```

---

## 🐛 Troubleshooting

### ThingsBoard não inicia

```bash
# Ver logs
docker-compose logs thingsboard --tail=100

# Reiniciar
docker-compose restart thingsboard

# Aguardar 2-3 minutos
```

### Erro "Connection refused"

ThingsBoard ainda está inicializando. Aguarde mais tempo e tente novamente.

### Devices não aparecem

1. Verifique se a sincronização rodou:
```bash
curl -X POST http://localhost:8000/thingsboard/sync
```

2. Verifique a resposta (deve ser sucesso)

3. Recarregue a página do ThingsBoard

### Dashboard vazio (sem dados)

1. Verifique se devices foram criados: **Devices** no menu
2. Abra um device → **Latest telemetry** (deve ter dados)
3. Ajuste o **Time Window** do dashboard (ex: "Last 24 hours")
4. Re-envie os dados: `curl -X POST http://localhost:8000/thingsboard/sync`

---

## ✅ Checklist Final

Antes de considerar completo:

- [ ] ThingsBoard está acessível em http://localhost:9090
- [ ] Login funciona (tenant@thingsboard.org / tenant)
- [ ] 24 devices foram criados
- [ ] Devices têm telemetria (Latest telemetry não está vazio)
- [ ] Dashboard de Métricas de Modelos foi criado
- [ ] Dashboard de Estatísticas do Dataset foi criado
- [ ] Dashboard de Top Filmes foi criado
- [ ] Todos os dashboards mostram dados reais
- [ ] Gráficos estão claros e bem formatados
- [ ] Insights estão documentados
- [ ] README foi atualizado

---

## 📝 Próximos Passos

1. **Aguardar ThingsBoard inicializar** (2-3 minutos)
2. **Sincronizar dados:** `curl -X POST http://localhost:8000/thingsboard/sync`
3. **Acessar:** http://localhost:9090
4. **Criar dashboards** seguindo o guia acima
5. **Exportar dashboards** criados para `trendz/`
6. **Tirar screenshots** para o relatório final

---

**Dúvidas?** Consulte:
- `trendz/README_THINGSBOARD.md` - Guia completo
- `trendz/DASHBOARD_GUIDE.md` - Como configurar cada widget
- Logs: `docker-compose logs thingsboard`

**Autor:** Sistema de Recomendação MovieLens  
**Disciplina:** Aprendizado de Máquina - 2025.2  
**Instituição:** CESAR School

