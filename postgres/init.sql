-- ====================================================================
-- SCHEMA DO BANCO DE DADOS - SISTEMA DE RECOMENDAÇÃO MOVIELENS
-- ====================================================================
-- Projeto: Aprendizado de Máquina - CESAR School
-- Database: PostgreSQL 15
-- Dataset: MovieLens 100K
-- ====================================================================

-- Criar extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ====================================================================
-- TABELA: movies
-- ====================================================================
-- Armazena informações sobre filmes
CREATE TABLE IF NOT EXISTS movies (
    movie_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    release_date DATE,
    video_release_date DATE,
    imdb_url VARCHAR(500),
    -- Gêneros (19 gêneros do MovieLens)
    unknown BOOLEAN DEFAULT FALSE,
    action BOOLEAN DEFAULT FALSE,
    adventure BOOLEAN DEFAULT FALSE,
    animation BOOLEAN DEFAULT FALSE,
    childrens BOOLEAN DEFAULT FALSE,
    comedy BOOLEAN DEFAULT FALSE,
    crime BOOLEAN DEFAULT FALSE,
    documentary BOOLEAN DEFAULT FALSE,
    drama BOOLEAN DEFAULT FALSE,
    fantasy BOOLEAN DEFAULT FALSE,
    film_noir BOOLEAN DEFAULT FALSE,
    horror BOOLEAN DEFAULT FALSE,
    musical BOOLEAN DEFAULT FALSE,
    mystery BOOLEAN DEFAULT FALSE,
    romance BOOLEAN DEFAULT FALSE,
    sci_fi BOOLEAN DEFAULT FALSE,
    thriller BOOLEAN DEFAULT FALSE,
    war BOOLEAN DEFAULT FALSE,
    western BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para otimizar consultas
CREATE INDEX idx_movies_title ON movies(title);
CREATE INDEX idx_movies_release_date ON movies(release_date);

-- ====================================================================
-- TABELA: users
-- ====================================================================
-- Armazena informações demográficas dos usuários
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    age INTEGER,
    gender CHAR(1) CHECK (gender IN ('M', 'F')),
    occupation VARCHAR(50),
    zip_code VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices
CREATE INDEX idx_users_age ON users(age);
CREATE INDEX idx_users_gender ON users(gender);
CREATE INDEX idx_users_occupation ON users(occupation);

-- ====================================================================
-- TABELA: ratings
-- ====================================================================
-- Armazena as avaliações (100k ratings)
CREATE TABLE IF NOT EXISTS ratings (
    rating_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    movie_id INTEGER NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    timestamp BIGINT NOT NULL,
    rated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_ratings_user_movie UNIQUE (user_id, movie_id)
);

-- Índices compostos para otimizar queries de recomendação
CREATE INDEX idx_ratings_user_id ON ratings(user_id);
CREATE INDEX idx_ratings_movie_id ON ratings(movie_id);
CREATE INDEX idx_ratings_user_movie ON ratings(user_id, movie_id);
CREATE INDEX idx_ratings_rating ON ratings(rating);
CREATE INDEX idx_ratings_timestamp ON ratings(timestamp);

-- ====================================================================
-- TABELA: user_clusters
-- ====================================================================
-- Armazena clusters de usuários (resultado do K-Means)
CREATE TABLE IF NOT EXISTS user_clusters (
    cluster_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    cluster_number INTEGER NOT NULL,
    distance_to_centroid FLOAT,
    cluster_assignment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    model_version VARCHAR(50),
    UNIQUE(user_id, model_version)
);

-- Índices
CREATE INDEX idx_user_clusters_user_id ON user_clusters(user_id);
CREATE INDEX idx_user_clusters_cluster_number ON user_clusters(cluster_number);
CREATE INDEX idx_user_clusters_model_version ON user_clusters(model_version);

-- ====================================================================
-- TABELA: movie_similarities
-- ====================================================================
-- Armazena similaridades entre filmes (para KNN)
CREATE TABLE IF NOT EXISTS movie_similarities (
    similarity_id SERIAL PRIMARY KEY,
    movie_id_1 INTEGER NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    movie_id_2 INTEGER NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    similarity_score FLOAT NOT NULL,
    calculation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    model_version VARCHAR(50),
    UNIQUE(movie_id_1, movie_id_2, model_version),
    CHECK (movie_id_1 < movie_id_2) -- Evita duplicação (A-B e B-A)
);

-- Índices
CREATE INDEX idx_movie_sim_movie1 ON movie_similarities(movie_id_1);
CREATE INDEX idx_movie_sim_movie2 ON movie_similarities(movie_id_2);
CREATE INDEX idx_movie_sim_score ON movie_similarities(similarity_score DESC);

-- ====================================================================
-- TABELA: recommendations
-- ====================================================================
-- Armazena recomendações geradas
CREATE TABLE IF NOT EXISTS recommendations (
    recommendation_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    movie_id INTEGER NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    predicted_rating FLOAT,
    recommendation_score FLOAT NOT NULL,
    recommendation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    model_version VARCHAR(50),
    algorithm VARCHAR(50), -- 'kmeans', 'knn', 'hybrid'
    UNIQUE(user_id, movie_id, model_version, algorithm)
);

-- Índices
CREATE INDEX idx_recommendations_user_id ON recommendations(user_id);
CREATE INDEX idx_recommendations_movie_id ON recommendations(movie_id);
CREATE INDEX idx_recommendations_score ON recommendations(recommendation_score DESC);
CREATE INDEX idx_recommendations_date ON recommendations(recommendation_date DESC);

-- ====================================================================
-- VIEWS ÚTEIS
-- ====================================================================

-- View: Estatísticas de filmes
CREATE OR REPLACE VIEW movie_stats AS
SELECT 
    m.movie_id,
    m.title,
    COUNT(r.rating_id) as total_ratings,
    AVG(r.rating) as avg_rating,
    MIN(r.rating) as min_rating,
    MAX(r.rating) as max_rating,
    STDDEV(r.rating) as stddev_rating
FROM movies m
LEFT JOIN ratings r ON m.movie_id = r.movie_id
GROUP BY m.movie_id, m.title;

-- View: Estatísticas de usuários
CREATE OR REPLACE VIEW user_stats AS
SELECT 
    u.user_id,
    u.age,
    u.gender,
    u.occupation,
    COUNT(r.rating_id) as total_ratings,
    AVG(r.rating) as avg_rating,
    MIN(r.rating) as min_rating,
    MAX(r.rating) as max_rating
FROM users u
LEFT JOIN ratings r ON u.user_id = r.user_id
GROUP BY u.user_id, u.age, u.gender, u.occupation;

-- View: Top filmes por rating médio (com pelo menos 50 avaliações)
CREATE OR REPLACE VIEW top_movies AS
SELECT 
    m.movie_id,
    m.title,
    COUNT(r.rating_id) as total_ratings,
    AVG(r.rating) as avg_rating,
    ROUND(AVG(r.rating)::numeric, 2) as avg_rating_rounded
FROM movies m
INNER JOIN ratings r ON m.movie_id = r.movie_id
GROUP BY m.movie_id, m.title
HAVING COUNT(r.rating_id) >= 50
ORDER BY AVG(r.rating) DESC, COUNT(r.rating_id) DESC
LIMIT 100;

-- View: Distribuição de clusters
CREATE OR REPLACE VIEW cluster_distribution AS
SELECT 
    cluster_number,
    COUNT(DISTINCT user_id) as total_users,
    AVG(distance_to_centroid) as avg_distance,
    model_version
FROM user_clusters
GROUP BY cluster_number, model_version
ORDER BY cluster_number;

-- ====================================================================
-- FUNÇÕES AUXILIARES
-- ====================================================================

-- Função: Atualizar timestamp de updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para atualizar updated_at
CREATE TRIGGER update_movies_updated_at BEFORE UPDATE ON movies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ====================================================================
-- COMENTÁRIOS NAS TABELAS
-- ====================================================================

COMMENT ON TABLE movies IS 'Informações sobre filmes do dataset MovieLens 100K';
COMMENT ON TABLE users IS 'Dados demográficos dos usuários';
COMMENT ON TABLE ratings IS '100.000 avaliações de filmes (1-5 estrelas)';
COMMENT ON TABLE user_clusters IS 'Clusters de usuários gerados pelo algoritmo K-Means';
COMMENT ON TABLE movie_similarities IS 'Similaridades entre filmes calculadas para KNN';
COMMENT ON TABLE recommendations IS 'Recomendações geradas pelos algoritmos de ML';

-- ====================================================================
-- INSERÇÃO DE DADOS INICIAIS (METADADOS)
-- ====================================================================

-- Inserir log de inicialização
CREATE TABLE IF NOT EXISTS db_metadata (
    id SERIAL PRIMARY KEY,
    event VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO db_metadata (event, description) 
VALUES ('schema_initialized', 'Database schema created successfully for MovieLens recommendation system');

-- ====================================================================
-- FINALIZAÇÃ
-- ====================================================================

-- Mensagem de sucesso (via RAISE NOTICE)
DO $$
BEGIN
    RAISE NOTICE '================================================';
    RAISE NOTICE 'Schema do banco de dados criado com sucesso!';
    RAISE NOTICE 'Database: movielens';
    RAISE NOTICE 'Tabelas: movies, users, ratings, user_clusters, movie_similarities, recommendations';
    RAISE NOTICE 'Views: movie_stats, user_stats, top_movies, cluster_distribution';
    RAISE NOTICE '================================================';
END $$;
