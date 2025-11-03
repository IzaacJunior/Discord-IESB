-- 📊 SCHEMA DO BANCO DE DADOS DE AUDITORIA
-- 💡 Boa Prática: Banco separado para logs evita misturar dados operacionais com auditoria!
-- 🔒 Segurança: Logs de auditoria isolados são mais seguros e difíceis de manipular

-- ============================================================================
-- 📋 TABELA: application_logs
-- Armazena logs detalhados da aplicação para auditoria e análise
-- ============================================================================
CREATE TABLE IF NOT EXISTS application_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    level TEXT NOT NULL CHECK(level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    logger_name TEXT NOT NULL,
    message TEXT NOT NULL,
    module TEXT,
    function TEXT,
    line_number INTEGER,
    extra_data TEXT,  -- JSON com dados extras (guild_id, user_id, etc)
    
    -- 🔑 Índices para performance em consultas comuns
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 📊 Índices para otimizar queries de auditoria
CREATE INDEX IF NOT EXISTS idx_logs_timestamp 
    ON application_logs(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_logs_level 
    ON application_logs(level);

CREATE INDEX IF NOT EXISTS idx_logs_logger_name 
    ON application_logs(logger_name);

CREATE INDEX IF NOT EXISTS idx_logs_level_timestamp 
    ON application_logs(level, timestamp DESC);

-- ============================================================================
-- 📋 VIEWS ÚTEIS PARA AUDITORIA
-- ============================================================================

-- 🔍 View: Logs das últimas 24 horas
CREATE VIEW IF NOT EXISTS v_logs_last_24h AS
SELECT 
    id,
    datetime(timestamp, 'localtime') as timestamp_local,
    level,
    logger_name,
    message,
    module,
    function,
    line_number
FROM 
    application_logs
WHERE 
    timestamp >= datetime('now', '-1 day')
ORDER BY 
    timestamp DESC;

-- 📊 View: Contagem de logs por nível (estatísticas)
CREATE VIEW IF NOT EXISTS v_logs_stats_by_level AS
SELECT 
    level,
    COUNT(*) as total_logs,
    COUNT(CASE WHEN timestamp >= datetime('now', '-1 hour') THEN 1 END) as last_hour,
    COUNT(CASE WHEN timestamp >= datetime('now', '-1 day') THEN 1 END) as last_24h,
    COUNT(CASE WHEN timestamp >= datetime('now', '-7 day') THEN 1 END) as last_7days
FROM 
    application_logs
GROUP BY 
    level
ORDER BY 
    CASE level
        WHEN 'CRITICAL' THEN 1
        WHEN 'ERROR' THEN 2
        WHEN 'WARNING' THEN 3
        WHEN 'INFO' THEN 4
        WHEN 'DEBUG' THEN 5
    END;

-- 🚨 View: Apenas erros e críticos
CREATE VIEW IF NOT EXISTS v_logs_errors AS
SELECT 
    id,
    datetime(timestamp, 'localtime') as timestamp_local,
    level,
    logger_name,
    message,
    module,
    function,
    line_number,
    extra_data
FROM 
    application_logs
WHERE 
    level IN ('ERROR', 'CRITICAL')
ORDER BY 
    timestamp DESC;

-- 📈 View: Logs por módulo (para análise)
CREATE VIEW IF NOT EXISTS v_logs_by_module AS
SELECT 
    module,
    logger_name,
    COUNT(*) as total_logs,
    COUNT(CASE WHEN level = 'ERROR' OR level = 'CRITICAL' THEN 1 END) as errors,
    MAX(timestamp) as last_log
FROM 
    application_logs
WHERE 
    module IS NOT NULL
GROUP BY 
    module, logger_name
ORDER BY 
    total_logs DESC;
