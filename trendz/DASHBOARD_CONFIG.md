# Configuracao de Dashboards - ThingsBoard & Trendz

## Guia de Configuracao

### Passo 1: Primeiro Acesso ao ThingsBoard

1. **Acesse:** http://localhost:8080
2. **Login padrao:**
   - **Email:** `tenant@thingsboard.org`
   - **Password:** `tenant`

3. **Trocar senha (recomendado):**
   - Clicar no icone do usuario (canto superior direito)
   - Profile -> Change Password

---

### Passo 2: Importar Dados de Predicoes

#### 2.1. Criar Device

1. **Devices -> Add Device (+)**
2. **Nome:** `MovieLens-ML-Model`
3. **Device Profile:** `default`
4. **Label:** `machine-learning`
5. **Salvar**

#### 2.2. Importar Telemetria (CSV)

Os arquivos CSV gerados pelo script de exportacao contem:
- `prediction_history_export.csv` - Historico de predicoes
- `recommendations_summary.csv` - Resumo de recomendacoes
- `cluster_analysis.csv` - Analise de clusters

**Opcao A: Via UI (Manual)**

1. **Devices -> MovieLens-ML-Model -> Attributes**
2. **Add Attribute -> Server attributes**
3. Upload cada CSV manualmente

**Opcao B: Via REST API (Automatizado)**

Usar o script `export_to_thingsboard.py` que ja inclui integracao via API.

---

### Passo 3: Criar Dashboard de Metricas

#### 3.1. Criar Dashboard

1. **Dashboards -> Add Dashboard (+)**
2. **Nome:** `MovieLens - Model Performance`
3. **Descricao:** `Metricas de performance dos modelos de recomendacao`

#### 3.2. Adicionar Widgets

##### Widget 1: RMSE por Modelo (Line Chart)

- **Type:** Charts -> Time Series Line Chart
- **Datasource:** 
  - Device: `MovieLens-ML-Model`
  - Key: `rmse`
- **Timewindow:** Last 30 days
- **Settings:**
  - Title: `RMSE por Modelo (Temporal)`
  - Show legend: true
  - Line width: 2
  - Y-axis: `RMSE`

##### Widget 2: Comparacao de Algoritmos (Bar Chart)

- **Type:** Charts -> Bar Chart
- **Datasource:**
  - Device: `MovieLens-ML-Model`
  - Keys: `rmse`, `mae`, `r2_score`
- **Settings:**
  - Title: `Comparacao de Metricas por Algoritmo`
  - Group by: `algorithm`
  - Colors: Custom palette

##### Widget 3: Distribuicao de Clusters (Pie Chart)

- **Type:** Charts -> Pie Chart
- **Datasource:**
  - CSV: `cluster_analysis.csv`
  - Key: `cluster_number`, Value: `total_users`
- **Settings:**
  - Title: `Distribuicao de Usuarios por Cluster`
  - Show labels: true
  - Show legend: true

##### Widget 4: Top Recomendacoes (Table)

- **Type:** Tables -> Entities Table
- **Datasource:**
  - CSV: `recommendations_summary.csv`
- **Settings:**
  - Title: `Top Recomendacoes por Algoritmo`
  - Columns: `algorithm`, `total_recommendations`, `avg_score`
  - Sort by: `avg_score` (descending)

##### Widget 5: Erro de Predicao (Histogram)

- **Type:** Charts -> Histogram
- **Datasource:**
  - CSV: `prediction_history_export.csv`
  - Key: `prediction_error`
- **Settings:**
  - Title: `Distribuicao de Erros de Predicao`
  - Bins: 20
  - X-axis: `Erro Absoluto`
  - Y-axis: `Frequencia`

---

### Passo 4: Configurar Trendz Analytics

#### 4.1. Conectar ao ThingsBoard

1. **Acesse:** http://localhost:8889 (Trendz)
2. **Conectar ThingsBoard:**
   - URL: `http://thingsboard:9090`
   - Token: (obtido do ThingsBoard)

#### 4.2. Criar Views Avancados

##### View 1: Evolucao de Metricas

- **Type:** Line Chart
- **X-axis:** Timestamp (date)
- **Y-axis:** RMSE, MAE (multiplas series)
- **Grouping:** By `model_version`
- **Aggregation:** Average

##### View 2: Analise de Clusters

- **Type:** Scatter Plot
- **X-axis:** `cluster_avg_age`
- **Y-axis:** `cluster_avg_rating`
- **Size:** `total_users`
- **Color:** `cluster_number`

##### View 3: Heatmap de Performance

- **Type:** Heatmap
- **X-axis:** `n_clusters` (K)
- **Y-axis:** `n_neighbors` (N)
- **Color:** `rmse` (gradient: green -> red)

---

### Passo 5: Configurar Alarmes (Opcional)

#### Alarme: RMSE Alto

1. **Device -> Alarm Rules -> Add Alarm Rule**
2. **Name:** `High RMSE Alert`
3. **Condition:**
   ```javascript
   return ctx.rmse > 1.2;
   ```
4. **Severity:** Warning
5. **Clear condition:**
   ```javascript
   return ctx.rmse <= 1.0;
   ```

---

## Estrutura de Dados para Import

### CSV: prediction_history_export.csv

```csv
prediction_id,user_id,movie_id,movie_title,predicted_rating,actual_rating,prediction_error,model_version,predicted_at,user_age,user_gender,user_occupation
1,1,242,"Kolya (1996)",4.23,5,0.77,v1.0,2025-11-27 10:30:00,24,M,technician
2,1,302,"L.A. Confidential (1997)",3.89,4,0.11,v1.0,2025-11-27 10:30:01,24,M,technician
...
```

### CSV: recommendations_summary.csv

```csv
algorithm,model_version,total_recommendations,avg_score,avg_predicted_rating,first_recommendation,last_recommendation
kmeans,v1.0,15000,0.87,3.92,2025-11-27 10:00:00,2025-11-27 11:30:00
knn,v1.0,15000,0.89,4.01,2025-11-27 10:00:00,2025-11-27 11:30:00
hybrid,v1.0,15000,0.91,4.05,2025-11-27 10:00:00,2025-11-27 11:30:00
```

### CSV: cluster_analysis.csv

```csv
cluster_number,total_users,avg_distance,cluster_avg_rating,cluster_avg_age,model_version
0,189,0.34,3.52,28.5,v1.0
1,156,0.29,4.12,35.2,v1.0
2,201,0.41,3.89,22.8,v1.0
...
```

---

## Temas e Customizacao

### Tema Escuro

1. **Profile -> Settings**
2. **Theme:** Dark
3. **Apply**

### Cores Personalizadas

```javascript
// Paleta de cores sugerida
const colors = {
  primary: '#1976d2',    // Azul
  success: '#4caf50',    // Verde
  warning: '#ff9800',    // Laranja
  error: '#f44336',      // Vermelho
  info: '#00bcd4'        // Ciano
};
```

---

## KPIs Sugeridos

### Dashboard Principal

1. **RMSE Medio:** Card widget - Valor numerico grande
2. **MAE Medio:** Card widget - Valor numerico grande
3. **Total de Recomendacoes:** Card widget - Contador
4. **Numero de Clusters:** Card widget - Valor fixo
5. **Melhoria vs Original:** Card widget - Porcentagem

### Dashboard Tecnico

1. **Training Time:** Line chart (temporal)
2. **Model Size:** Card widget (MB)
3. **Prediction Latency:** Line chart (ms)
4. **Coverage:** Gauge widget (%)

---

## Exemplos de Queries

### Query 1: Media de RMSE por Modelo

```sql
SELECT 
    model_version,
    AVG(rmse) as avg_rmse,
    MIN(rmse) as min_rmse,
    MAX(rmse) as max_rmse
FROM model_metrics
GROUP BY model_version
ORDER BY avg_rmse ASC;
```

### Query 2: Top 10 Filmes Mais Recomendados

```sql
SELECT 
    m.title,
    COUNT(r.recommendation_id) as total_recommendations,
    AVG(r.recommendation_score) as avg_score
FROM recommendations r
JOIN movies m ON r.movie_id = m.movie_id
GROUP BY m.title
ORDER BY total_recommendations DESC
LIMIT 10;
```

### Query 3: Erros de Predicao por Faixa Etaria

```sql
SELECT 
    CASE 
        WHEN u.age < 25 THEN '18-24'
        WHEN u.age < 35 THEN '25-34'
        WHEN u.age < 45 THEN '35-44'
        ELSE '45+'
    END as age_group,
    AVG(ph.prediction_error) as avg_error,
    COUNT(*) as total_predictions
FROM prediction_history ph
JOIN users u ON ph.user_id = u.user_id
WHERE ph.actual_rating IS NOT NULL
GROUP BY age_group
ORDER BY age_group;
```

---

## Metricas de Sucesso

### Modelo Baseline (Paper Original)
- RMSE < 1.0
- MAE < 0.8
- Precision@10 > 0.6
- Recall@10 > 0.4

### Modelo Otimizado (Grid Search)
- RMSE < 0.9
- MAE < 0.75
- Precision@10 > 0.7
- Recall@10 > 0.5

---

## Proximos Passos

1. **Automatizar exportacao:** Agendar script Python para rodar periodicamente
2. **Real-time updates:** Configurar streaming de metricas
3. **A/B Testing:** Comparar multiplas versoes de modelos
4. **Alertas:** Configurar notificacoes para degradacao de performance
5. **Relatorios:** Agendar geracao de relatorios semanais/mensais

---

**Documentacao Completa:**
- ThingsBoard: https://thingsboard.io/docs/
- Trendz: https://thingsboard.io/docs/trendz/

**CESAR School - Aprendizado de Maquina 2025.2**
j