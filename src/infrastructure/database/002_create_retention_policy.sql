-- ============================================================================
-- 📋 TABELA: audit_retention_policy
-- 💡 Boa Prática: Define política de retenção de logs por nível
-- ⚡ CRÍTICO: Previne crescimento infinito do banco de auditoria
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_retention_policy (
    id INTEGER PRIMARY KEY,
    level TEXT UNIQUE NOT NULL,
    days_to_keep INTEGER NOT NULL,
    last_cleanup TIMESTAMP,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK(level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    CHECK(days_to_keep > 0)
);

-- ============================================================================
-- 📊 Inserir Política Padrão de Retenção
-- ============================================================================

INSERT OR IGNORE INTO audit_retention_policy (
    level, days_to_keep, description
) VALUES
    ('DEBUG', 7, '🔧 Debug: manter 7 dias (muito verboso)'),
    ('INFO', 30, '📝 Info: manter 30 dias'),
    ('WARNING', 90, '⚠️ Warning: manter 90 dias'),
    ('ERROR', 180, '❌ Error: manter 180 dias (6 meses)'),
    ('CRITICAL', 365, '🔴 Critical: manter 1 ano (máximo)');

-- ============================================================================
-- 📊 ÍNDICES para Performance
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_retention_policy_level 
ON audit_retention_policy(level);

CREATE INDEX IF NOT EXISTS idx_retention_policy_cleanup 
ON audit_retention_policy(last_cleanup);

-- ============================================================================
-- 📈 VIEW: Estatísticas de Retenção
-- ============================================================================

CREATE VIEW IF NOT EXISTS v_retention_stats AS
SELECT 
    p.level,
    p.days_to_keep,
    datetime(p.last_cleanup, 'localtime') as last_cleanup_local,
    COUNT(l.id) as current_logs,
    COUNT(CASE 
        WHEN l.timestamp < datetime('now', '-' || p.days_to_keep || ' days')
        THEN 1 
    END) as logs_to_delete,
    ROUND(
        COUNT(CASE 
            WHEN l.timestamp < datetime('now', '-' || p.days_to_keep || ' days')
            THEN 1 
        END) * 100.0 / NULLIF(COUNT(l.id), 0),
        2
    ) as percent_to_delete,
    MAX(l.timestamp) as last_log_date
FROM audit_retention_policy p
LEFT JOIN application_logs l ON p.level = l.level
GROUP BY p.level, p.days_to_keep, p.last_cleanup
ORDER BY 
    CASE p.level
        WHEN 'CRITICAL' THEN 1
        WHEN 'ERROR' THEN 2
        WHEN 'WARNING' THEN 3
        WHEN 'INFO' THEN 4
        WHEN 'DEBUG' THEN 5
    END;

-- ============================================================================
-- 📊 VIEW: Próximas Limpezas Necessárias
-- ============================================================================

CREATE VIEW IF NOT EXISTS v_cleanup_needed AS
SELECT 
    p.level,
    p.days_to_keep,
    COUNT(l.id) as total_logs,
    COUNT(CASE 
        WHEN l.timestamp < datetime('now', '-' || p.days_to_keep || ' days')
        THEN 1 
    END) as logs_to_delete,
    CASE 
        WHEN COUNT(CASE 
            WHEN l.timestamp < datetime('now', '-' || p.days_to_keep || ' days')
            THEN 1 
        END) > 0 THEN '✅ LIMPEZA NECESSÁRIA'
        ELSE '⏭️ SEM LIMPEZA'
    END as cleanup_status,
    datetime('now', '+24 hours') as recommended_next_cleanup
FROM audit_retention_policy p
LEFT JOIN application_logs l ON p.level = l.level
GROUP BY p.level;

-- ============================================================================
-- 🎉 SUCESSO!
-- ✅ Tabela audit_retention_policy criada
-- ✅ Política padrão inserida
-- ✅ Views para monitoramento criadas
-- ✅ Pronto para LogCleanupManager!
-- ============================================================================
