# 📺 GUIA VISUAL - Como Abrir e Ver Resultados no ThingsBoard

## ⏳ IMPORTANTE: ThingsBoard leva 3-5 minutos para inicializar na primeira vez!

---

## 📋 **PASSO 1: Aguardar ThingsBoard Inicializar**

### Como saber se está pronto?

**Opção A: Via comando (terminal)**
```bash
curl http://localhost:9090/login
```

Se retornar HTML (código da página de login), está pronto!

**Opção B: Via navegador**

Abra no navegador: **http://localhost:9090**

- ❌ **Se der erro "conexão recusada" ou "não foi possível conectar":**
  - ThingsBoard ainda está inicializando
  - Aguarde mais 1-2 minutos e tente novamente

- ✅ **Se aparecer a tela de LOGIN:**
  - ThingsBoard está pronto! Prossiga para o Passo 2

### Ver logs do ThingsBoard (opcional):
```bash
docker-compose logs -f thingsboard
```

**Procure por essa linha:**
```
Started ThingsBoard Application
```

Quando aparecer, o ThingsBoard está pronto!

Pressione `Ctrl+C` para sair dos logs.

---

## 🔑 **PASSO 2: Fazer Login no ThingsBoard**

### 2.1 - Abrir o navegador

Digite na barra de endereços:
```
http://localhost:9090
```

### 2.2 - Tela de Login

Você verá uma tela de login do ThingsBoard com:
- Logo do ThingsBoard
- Campo "Email"
- Campo "Password"
- Botão "Login"

### 2.3 - Credenciais

Digite:

**Email/Username:**
```
tenant@thingsboard.org
```

**Password:**
```
tenant
```

### 2.4 - Clicar em "Login"

✅ Você será redirecionado para o **Dashboard Home** do ThingsBoard!

---

## 📊 **PASSO 3: Sincronizar os Dados (Primeira Vez)**

Antes de ver os resultados, precisamos enviar os dados para o ThingsBoard.

### 3.1 - Abrir um novo terminal

Mantenha o navegador aberto e abra um terminal.

### 3.2 - Executar sincronização

**Opção A: Via API (recomendado)**
```bash
curl -X POST http://localhost:8000/thingsboard/sync
```

**Opção B: Via script Python**
```bash
docker-compose exec fastapi python thingsboard_client.py
```

### 3.3 - Ver o resultado

Você verá algo como:

```
============================================================
🚀 SINCRONIZAÇÃO COMPLETA - ThingsBoard
============================================================
✅ Autenticado no ThingsBoard com sucesso!

📊 Sincronizando estatísticas do dataset...
✅ Device criado: Dataset_Statistics
✅ Estatísticas do dataset sincronizadas!
   - Total de filmes: 1682
   - Total de usuários: 943
   - Total de avaliações: 90570

🏆 Sincronizando top 20 filmes...
✅ Device criado: Movie_1
✅ Device criado: Movie_2
...
✅ 20/20 filmes sincronizados!

🔬 Sincronizando métricas de modelos ML...
✅ Device criado: Model_KMeans_KNN_K8
...
✅ 3/3 modelos sincronizados!

============================================================
📊 RESUMO DA SINCRONIZAÇÃO
============================================================
✅ Autenticação: OK
✅ Estatísticas do Dataset
✅ Top Filmes (20)
✅ Métricas de Modelos

🎯 Taxa de sucesso: 3/3 (100.0%)
```

✅ **Pronto! Os dados foram enviados!**

---

## 🎯 **PASSO 4: Ver os Devices (Dados) Criados**

Agora voltamos para o navegador (ThingsBoard).

### 4.1 - Clicar em "Devices"

No menu lateral esquerdo, clique em **"Devices"** (ícone de chip/processador).

### 4.2 - Ver lista de devices

Você verá uma lista com **24 devices:**

**Estatísticas:**
- 📊 `Dataset_Statistics`

**Modelos de ML:**
- 🔬 `Model_KMeans_KNN_K8`
- 🔬 `Model_KMeans_KNN_K5`
- 🔬 `Model_Baseline_Mean`

**Top Filmes (20):**
- 🎬 `Movie_1`
- 🎬 `Movie_2`
- 🎬 `Movie_3`
- ... (até `Movie_20`)

### 4.3 - Entender o que são Devices

No ThingsBoard:
- **Device = Entidade que envia dados**
- Cada device tem:
  - **Telemetria:** Dados que mudam ao longo do tempo (ex: RMSE, ratings)
  - **Atributos:** Metadados fixos (ex: título do filme, algoritmo usado)

---

## 📈 **PASSO 5: Ver os Dados de um Device**

Vamos ver os dados do dataset!

### 5.1 - Clicar no device "Dataset_Statistics"

Na lista de devices, clique em **"Dataset_Statistics"**.

### 5.2 - Ver abas disponíveis

Você verá várias abas no topo:
- **Details** - Informações gerais
- **Attributes** - Metadados fixos
- **Latest telemetry** ← **CLIQUE AQUI!**
- **Alarms**
- **Events**
- **Relations**

### 5.3 - Clicar em "Latest telemetry"

Você verá uma tabela com os dados enviados:

| Key | Value | Last Update Time |
|-----|-------|------------------|
| `total_movies` | 1682 | 2025-12-03 04:XX:XX |
| `total_users` | 943 | 2025-12-03 04:XX:XX |
| `total_ratings` | 90570 | 2025-12-03 04:XX:XX |
| `avg_rating` | 3.52 | 2025-12-03 04:XX:XX |
| `std_rating` | 1.12 | 2025-12-03 04:XX:XX |
| `min_rating` | 1.0 | 2025-12-03 04:XX:XX |
| `max_rating` | 5.0 | 2025-12-03 04:XX:XX |

✅ **Esses são os dados do seu dataset MovieLens!**

### 5.4 - Ver dados de um filme

Volte para **Devices** (menu lateral) e clique em **"Movie_1"**.

Vá em **"Latest telemetry"** e você verá:

| Key | Value | Descrição |
|-----|-------|-----------|
| `avg_rating` | 4.45 | Avaliação média do filme |
| `num_ratings` | 583 | Número de avaliações |
| `min_rating` | 1.0 | Nota mínima recebida |
| `max_rating` | 5.0 | Nota máxima recebida |
| `std_rating` | 0.89 | Desvio padrão |

Agora clique em **"Attributes"** para ver:

| Key | Value |
|-----|-------|
| `title` | Star Wars (1977) |
| `rank` | 1 |
| `movie_id` | 50 |
| `category` | Top Movies |

✅ **Essas são as informações do filme #1 mais bem avaliado!**

### 5.5 - Ver dados de um modelo ML

Volte para **Devices** e clique em **"Model_KMeans_KNN_K8"**.

**Latest telemetry:**

| Key | Value | Descrição |
|-----|-------|-----------|
| `rmse` | 1.12 | Root Mean Squared Error |
| `precision_at_10` | 0.78 | Precisão nas top 10 recomendações |
| `recall_at_10` | 0.65 | Recall nas top 10 recomendações |
| `mae` | 0.89 | Mean Absolute Error |

**Attributes:**

| Key | Value |
|-----|-------|
| `algorithm` | K-Means (K=8) + KNN |
| `num_clusters` | 8 |
| `dataset` | MovieLens 100K |
| `experiment` | MovieLens_Experiment_1 |

✅ **Essas são as métricas do seu modelo de ML!**

---

## 🎨 **PASSO 6: Criar um Dashboard Simples**

Agora vamos criar um dashboard para visualizar os dados de forma bonita!

### 6.1 - Ir para Dashboards

No menu lateral esquerdo, clique em **"Dashboards"** (ícone de gráfico).

### 6.2 - Criar novo dashboard

- Clique no botão **"+"** (canto inferior direito)
- Aparecerá um modal "Add dashboard"

**Preencha:**
- **Title:** `Métricas do Sistema de Recomendação`
- **Description:** `Dashboard com estatísticas, modelos e top filmes`
- Deixe o resto como padrão

Clique em **"Add"**.

### 6.3 - Entrar em modo de edição

Você será redirecionado para o dashboard vazio.

- Clique no ícone de **lápis** (canto superior direito) para entrar em modo de edição
- Ou clique em **"Enter edit mode"**

### 6.4 - Adicionar primeiro widget (Total de Filmes)

1. Clique no botão **"+"** ou **"Add new widget"**

2. Selecione a categoria **"Cards"**

3. Escolha **"Simple card"** ou **"Entity count card"**

4. Clique em **"Add"**

5. **Configurar o widget:**

   **Aba "Data":**
   - **Entity alias:**
     - Clique em **"Create new"**
     - Type: `Single entity`
     - Entity type: `Device`
     - Device: `Dataset_Statistics`
     - Clique em **"Add"**
   
   - **Data key:**
     - Clique em **"+"** para adicionar data key
     - Type: `Timeseries`
     - Key: `total_movies`
     - Clique em **"Add"**

   **Aba "Settings":**
   - **Card title:** `Total de Filmes`
   - **Label:** `Filmes`
   - **Show icon:** ✅ (marque)
   - **Icon:** procure por "movie" ou use 🎬
   - **Icon color:** Escolha uma cor (ex: azul)

   **Aba "Advanced":**
   - Deixe como padrão

6. Clique em **"Add"** (canto inferior direito)

✅ **Primeiro widget criado!** Você verá um card mostrando "1682" (total de filmes).

### 6.5 - Ajustar tamanho e posição

- Clique e arraste o widget para posicioná-lo
- Arraste os cantos para redimensionar
- Posicione no canto superior esquerdo

### 6.6 - Adicionar mais widgets

Repita o processo (Passo 6.4) para criar mais cards:

**Card 2: Total de Usuários**
- Device: `Dataset_Statistics`
- Data key: `total_users`
- Title: `Total de Usuários`
- Icon: 👥 (pessoas)
- Posição: Ao lado do primeiro card

**Card 3: Total de Avaliações**
- Device: `Dataset_Statistics`
- Data key: `total_ratings`
- Title: `Total de Avaliações`
- Icon: ⭐ (estrela)
- Posição: Ao lado do segundo card

**Card 4: Avaliação Média**
- Device: `Dataset_Statistics`
- Data key: `avg_rating`
- Title: `Avaliação Média`
- Label: `/ 5.0 estrelas`
- Icon: 📊
- Posição: Ao lado do terceiro card

### 6.7 - Criar um Gauge (medidor) para Avaliação Média

1. Clique em **"+"** para adicionar novo widget

2. Categoria: **"Gauges"**

3. Escolha: **"Simple gauge"** ou **"Radial gauge"**

4. **Configurar:**
   - Device: `Dataset_Statistics`
   - Data key: `avg_rating`
   - Title: `Avaliação Média do Dataset`
   - Min value: `1`
   - Max value: `5`
   - Units: `estrelas`
   - Threshold (opcional):
     - Verde: 4.0 - 5.0 (Excelente)
     - Amarelo: 3.0 - 4.0 (Bom)
     - Vermelho: 1.0 - 3.0 (Ruim)

5. Clique em **"Add"**

6. Posicione abaixo dos cards

✅ **Gauge criado!** Mostrará um medidor visual com a avaliação média.

### 6.8 - Criar tabela com Top Filmes

1. Clique em **"+"**

2. Categoria: **"Entity tables"** ou **"Tables"**

3. Escolha: **"Entities table"**

4. **Configurar:**
   - **Entity type:** `Device`
   - **Entity name starts with:** `Movie_`
   - Isso vai pegar todos os devices que começam com "Movie_"

5. **Columns (colunas):**
   - Adicione as colunas que quer mostrar:
     - `rank` (Atributo) → Ranking
     - `title` (Atributo) → Título
     - `avg_rating` (Telemetry) → Avaliação
     - `num_ratings` (Telemetry) → Nº Avaliações

6. **Sorting:**
   - Ordenar por: `rank`
   - Ordem: Crescente (ASC)

7. Clique em **"Add"**

8. Posicione abaixo do gauge, ocupando toda a largura

✅ **Tabela criada!** Mostrará os Top 20 filmes em uma tabela organizada.

### 6.9 - Salvar o dashboard

- Clique no ícone de **disquete** (💾) no canto superior direito
- Ou clique em **"Save"**
- Clique em **"Apply changes"**

✅ **Dashboard salvo!**

### 6.10 - Sair do modo de edição

- Clique no **"X"** ou **"Exit edit mode"**

Agora você pode ver seu dashboard completo e interativo!

---

## 🎯 **PASSO 7: Ver Insights e Análises**

### 7.1 - Insights do Dataset

Olhando para seu dashboard, você pode concluir:

✅ **Dataset bem balanceado:**
- 1,682 filmes
- 943 usuários  
- 90,570 avaliações
- **Média de 96 avaliações por usuário** (90570 / 943)
- **Média de 54 avaliações por filme** (90570 / 1682)

✅ **Avaliações tendem a ser positivas:**
- Avaliação média: 3.52 / 5.0
- Isso indica que usuários tendem a avaliar filmes que gostam
- Não há viés extremo (nem muito positivo nem muito negativo)

### 7.2 - Insights dos Modelos

Vá em **Devices** → **"Model_KMeans_KNN_K8"** → **Latest telemetry**:

✅ **Modelo K-Means + KNN tem bom desempenho:**
- RMSE: 1.12 (quanto menor, melhor)
- Precision@10: 0.78 (78% das recomendações são relevantes)
- Recall@10: 0.65 (consegue recuperar 65% dos filmes relevantes)

**Comparado com Baseline:**
- Baseline RMSE: 1.35
- **Melhoria de 17%** usando clustering!

### 7.3 - Insights dos Top Filmes

Olhando a tabela de Top Filmes:

✅ **Filmes clássicos dominam:**
- Star Wars, Titanic, Casablanca, etc.
- Alta avaliação média (>4.0)
- Alto número de avaliações (popularidade)

✅ **Consenso vs Polarização:**
- Filmes com baixo `std_rating` = consenso (todos concordam)
- Filmes com alto `std_rating` = polarizam opiniões

---

## 📊 **PASSO 8: Criar Mais Dashboards (Avançado)**

### Dashboard 2: Métricas de Modelos ML

Crie um dashboard específico para comparar modelos:

**Widgets:**
1. **3 Cards lado a lado:**
   - RMSE (Model_KMeans_KNN_K8)
   - Precision@10 (Model_KMeans_KNN_K8)
   - Recall@10 (Model_KMeans_KNN_K8)

2. **Gráfico de barras comparando os 3 modelos:**
   - Widget type: **"Bar chart"** ou **"Charts"**
   - Adicionar 3 data sources:
     - Model_KMeans_KNN_K8 → rmse
     - Model_KMeans_KNN_K5 → rmse
     - Model_Baseline_Mean → rmse
   - Título: "Comparação de RMSE entre Modelos"

3. **Tabela com todos os modelos:**
   - Entity type: Device
   - Type: ml_model
   - Colunas: algorithm, rmse, precision_at_10, recall_at_10

### Dashboard 3: Análise de Filmes

**Widgets:**
1. **Card grande com o filme #1:**
   - Device: Movie_1
   - Mostrar: title (atributo), avg_rating, num_ratings
   - Estilo: Destaque visual

2. **Gráfico de barras horizontal - Top 10:**
   - 10 data sources (Movie_1 a Movie_10)
   - Data key: avg_rating
   - Labels: Usar attribute "title"

3. **Scatter plot (se disponível):**
   - Eixo X: num_ratings (popularidade)
   - Eixo Y: avg_rating (qualidade)
   - Insight: Correlação entre popularidade e qualidade

---

## 📤 **PASSO 9: Exportar Dashboard (Para o Relatório)**

### 9.1 - Exportar como JSON

1. Abra o dashboard que criou
2. Clique no ícone de **menu** (3 pontinhos) no canto superior direito
3. Clique em **"Export dashboard"**
4. Salve o arquivo JSON em: `trendz/dashboard_metricas.json`

### 9.2 - Tirar Screenshots

Para o relatório, tire prints de:

1. **Dashboard completo** (visão geral)
2. **Cards de estatísticas** (zoom nos números)
3. **Gauge de avaliação média**
4. **Tabela de Top Filmes**
5. **Device individual** (Latest telemetry + Attributes)

Salve em: `reports/dashboard_screenshots/`

---

## 🔄 **PASSO 10: Atualizar Dados**

### Quando re-treinar modelos ou adicionar dados:

```bash
# Re-sincronizar todos os dados
curl -X POST http://localhost:8000/thingsboard/sync
```

Depois:
1. Volte para o ThingsBoard
2. Recarregue a página (F5)
3. Os dashboards mostrarão os novos dados automaticamente

---

## ✅ **Checklist Final**

- [ ] ThingsBoard está acessível em http://localhost:9090
- [ ] Consegui fazer login (tenant@thingsboard.org / tenant)
- [ ] Vejo 24 devices na lista de Devices
- [ ] Devices têm telemetria (Latest telemetry não está vazio)
- [ ] Criei pelo menos 1 dashboard
- [ ] Dashboard mostra dados reais (não vazio)
- [ ] Entendo os insights dos dados
- [ ] Tirei screenshots para o relatório
- [ ] Exportei dashboards para `trendz/`

---

## 🐛 **Problemas Comuns**

### "Não consigo acessar http://localhost:9090"

**Causa:** ThingsBoard ainda está inicializando

**Solução:**
```bash
# Ver logs
docker-compose logs thingsboard --tail=100

# Aguardar aparecer "Started ThingsBoard Application"
docker-compose logs -f thingsboard | grep "Started"

# Pressione Ctrl+C quando aparecer
```

Aguarde 3-5 minutos e tente novamente.

### "Devices não aparecem na lista"

**Causa:** Dados não foram sincronizados

**Solução:**
```bash
# Sincronizar dados
curl -X POST http://localhost:8000/thingsboard/sync

# Recarregar página do ThingsBoard (F5)
```

### "Latest telemetry está vazio"

**Causa:** Telemetria não foi enviada ou expirou

**Solução:**
```bash
# Re-enviar dados
curl -X POST http://localhost:8000/thingsboard/sync

# No ThingsBoard, ajuste o "Time window" do widget
# Troque de "Last hour" para "Last 24 hours" ou "Last 7 days"
```

### "Dashboard não mostra dados"

**Causa:** Time window incorreto ou device errado

**Solução:**
1. Entre em edit mode (lápis)
2. Clique no widget com problema
3. Verifique se o device e data key estão corretos
4. Ajuste Time window: **"Latest telemetry"** (mostra último valor sempre)

---

## 📚 **Próximos Passos**

1. ✅ Crie os 3 dashboards recomendados
2. ✅ Tire screenshots para o relatório
3. ✅ Exporte dashboards (JSON) para `trendz/`
4. ✅ Documente os insights encontrados
5. ✅ Escreva a seção "Dashboard e Insights" do relatório

---

**🎉 Parabéns! Você completou a implementação do Ponto 5!**

**Autor:** Sistema de Recomendação MovieLens  
**Disciplina:** Aprendizado de Máquina - 2025.2  
**Instituição:** CESAR School

