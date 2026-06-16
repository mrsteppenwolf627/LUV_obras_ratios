-- LUV Obras Ratios — initial schema for Supabase PostgreSQL
-- Run this once in the Supabase SQL Editor: https://supabase.com/dashboard/project/hjoodpjhnvlfvzkmqitx/sql

CREATE TABLE IF NOT EXISTS budgets (
    id          SERIAL PRIMARY KEY,
    filename    VARCHAR(255) NOT NULL,
    file_hash   VARCHAR(64)  UNIQUE NOT NULL,
    import_date TIMESTAMP    NOT NULL DEFAULT NOW(),
    surface_m2  FLOAT,
    building_type VARCHAR(100),
    source_format VARCHAR(20) NOT NULL,
    total_cost  FLOAT,
    raw_data_json TEXT
);

CREATE TABLE IF NOT EXISTS line_items (
    id                SERIAL PRIMARY KEY,
    budget_id         INTEGER NOT NULL REFERENCES budgets(id) ON DELETE CASCADE,
    chapter_code      VARCHAR(100),
    chapter_name      VARCHAR(500),
    description       TEXT,
    quantity          FLOAT,
    unit              VARCHAR(30),
    unit_cost         FLOAT,
    total_cost        FLOAT,
    validation_status VARCHAR(20) NOT NULL DEFAULT 'VALID'
);

CREATE TABLE IF NOT EXISTS ratios (
    id            SERIAL PRIMARY KEY,
    chapter_code  VARCHAR(100) NOT NULL,
    chapter_name  VARCHAR(500),
    building_type VARCHAR(100),
    cost_per_m2   FLOAT,
    median        FLOAT,
    min_value     FLOAT,
    max_value     FLOAT,
    percentil_25  FLOAT,
    percentil_75  FLOAT,
    std_dev       FLOAT,
    sample_count  INTEGER DEFAULT 0,
    last_updated  TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_ratio_chapter_type UNIQUE (chapter_code, building_type)
);

CREATE TABLE IF NOT EXISTS space_ratios (
    id                 SERIAL PRIMARY KEY,
    budget_id          INTEGER NOT NULL REFERENCES budgets(id) ON DELETE CASCADE,
    nombre             VARCHAR(200) NOT NULL,
    zona               VARCHAR(100),
    coste              FLOAT,
    m2                 FLOAT DEFAULT 0.0,
    ratio_eur_m2       FLOAT,
    coste_prorrateado  FLOAT,
    import_date        TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS item_master (
    id                   SERIAL PRIMARY KEY,
    item_key             VARCHAR(500) UNIQUE NOT NULL,
    categoria            VARCHAR(100),
    subcategoria         VARCHAR(100),
    unidad               VARCHAR(50),
    mediana_unitario     FLOAT,
    media_unitario       FLOAT,
    min_unitario         FLOAT,
    max_unitario         FLOAT,
    desv_std             FLOAT,
    muestras_count       INTEGER DEFAULT 0,
    primera_fecha        TIMESTAMP,
    ultima_fecha         TIMESTAMP,
    ultima_actualizacion TIMESTAMP DEFAULT NOW(),
    categoria_asignada   VARCHAR(20) NOT NULL DEFAULT 'MEDIUM',
    gama_asignada        VARCHAR(20) NOT NULL DEFAULT 'SIN_CLASIFICAR'
);

CREATE TABLE IF NOT EXISTS item_master_ratios (
    id                   SERIAL PRIMARY KEY,
    item_master_id       INTEGER NOT NULL REFERENCES item_master(id) ON DELETE CASCADE,
    categoria            VARCHAR(20) NOT NULL,
    ratio_actual         FLOAT,
    mediana              FLOAT,
    min_valor            FLOAT,
    max_valor            FLOAT,
    desv_std             FLOAT,
    percentil_25         FLOAT,
    percentil_75         FLOAT,
    muestras_count       INTEGER DEFAULT 0,
    confianza            VARCHAR(20) DEFAULT 'MUY_DÉBIL',
    ultima_actualizacion TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_item_cat_ratio UNIQUE (item_master_id, categoria)
);

CREATE TABLE IF NOT EXISTS item_instance (
    id                      SERIAL PRIMARY KEY,
    budget_id               INTEGER NOT NULL REFERENCES budgets(id) ON DELETE CASCADE,
    item_master_id          INTEGER NOT NULL REFERENCES item_master(id) ON DELETE CASCADE,
    codigo                  VARCHAR(200),
    descripcion             TEXT,
    categoria_original      VARCHAR(200),
    unidad                  VARCHAR(50),
    cantidad                FLOAT,
    precio_unitario         FLOAT,
    precio_total            FLOAT,
    categoria_detectada     VARCHAR(100),
    confianza_clasificacion FLOAT,
    desviacion_vs_historico FLOAT,
    clasificacion_precio    VARCHAR(50),
    categoria_asignada      VARCHAR(20) NOT NULL DEFAULT 'MEDIUM',
    ratio_comparativa       FLOAT,
    validation_status       VARCHAR(20) NOT NULL DEFAULT 'VALID',
    created_at              TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS budget_imports (
    id            SERIAL PRIMARY KEY,
    filename      VARCHAR(255) NOT NULL,
    file_hash     VARCHAR(64)  UNIQUE NOT NULL,
    building_type VARCHAR(100),
    import_date   TIMESTAMP    NOT NULL DEFAULT NOW(),
    status        VARCHAR(50)  NOT NULL DEFAULT 'success',
    items_count   INTEGER,
    error_message VARCHAR(1000)
);

CREATE TABLE IF NOT EXISTS validation_logs (
    id           SERIAL PRIMARY KEY,
    line_item_id INTEGER REFERENCES line_items(id) ON DELETE CASCADE,
    budget_id    INTEGER REFERENCES budgets(id)    ON DELETE CASCADE,
    rule_name    VARCHAR(100) NOT NULL,
    status       VARCHAR(20)  NOT NULL,
    message      TEXT,
    created_at   TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS gama_ranges (
    id               SERIAL PRIMARY KEY,
    material_type    VARCHAR(100) NOT NULL,
    categoria        VARCHAR(100) NOT NULL,
    medium_min       FLOAT,
    medium_max       FLOAT,
    premium_min      FLOAT,
    premium_max      FLOAT,
    luxury_min       FLOAT,
    luxury_max       FLOAT,
    luxury_plus_min  FLOAT,
    luxury_plus_max  FLOAT,
    fuente           VARCHAR(255),
    notas            TEXT,
    created_at       TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_gama_material_categoria UNIQUE (material_type, categoria)
);
