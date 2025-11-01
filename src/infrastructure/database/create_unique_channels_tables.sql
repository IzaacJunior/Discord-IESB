-- 🏠 TABELA: CATEGORIAS DE FÓRUNS ÚNICOS
-- 💡 Armazena categorias configuradas para criar fóruns únicos por membro

CREATE TABLE IF NOT EXISTS unique_channel_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL,
    category_name TEXT NOT NULL,
    guild_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category_id, guild_id)
);

-- 🔍 Índice para buscas rápidas por guild
CREATE INDEX IF NOT EXISTS idx_unique_categories_guild 
ON unique_channel_categories(guild_id);

-- 🔍 Índice para verificação de categoria específica
CREATE INDEX IF NOT EXISTS idx_unique_categories_lookup 
ON unique_channel_categories(category_id, guild_id);


-- 👤 TABELA: CANAIS ÚNICOS POR MEMBRO
-- 💡 Relaciona membros com seus fóruns privados únicos

CREATE TABLE IF NOT EXISTS member_unique_channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    channel_name TEXT NOT NULL,
    guild_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    UNIQUE(member_id, category_id, guild_id),
    FOREIGN KEY (category_id) REFERENCES unique_channel_categories(category_id)
);

-- 🔍 Índice para busca rápida por membro
CREATE INDEX IF NOT EXISTS idx_member_channels_member 
ON member_unique_channels(member_id, guild_id);

-- 🔍 Índice para busca por categoria
CREATE INDEX IF NOT EXISTS idx_member_channels_category 
ON member_unique_channels(category_id, guild_id);

-- 🔍 Índice para busca por canal
CREATE INDEX IF NOT EXISTS idx_member_channels_channel 
ON member_unique_channels(channel_id);

-- 🔍 Índice para verificação de membro + categoria (evita duplicatas)
CREATE INDEX IF NOT EXISTS idx_member_channels_unique_check 
ON member_unique_channels(member_id, category_id, guild_id, is_active);


-- 💡 TRIGGER: Atualiza timestamp quando canal é reativado
CREATE TRIGGER IF NOT EXISTS update_member_channel_timestamp
AFTER UPDATE ON member_unique_channels
FOR EACH ROW
WHEN NEW.is_active = 1 AND OLD.is_active = 0
BEGIN
    UPDATE member_unique_channels 
    SET created_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;


-- 📊 VIEW: Estatísticas de fóruns únicos por servidor
CREATE VIEW IF NOT EXISTS v_unique_channels_stats AS
SELECT 
    guild_id,
    category_id,
    category_name,
    COUNT(DISTINCT member_id) as total_members,
    COUNT(DISTINCT channel_id) as total_channels,
    SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_channels
FROM member_unique_channels
JOIN unique_channel_categories USING (category_id, guild_id)
GROUP BY guild_id, category_id, category_name;


-- 📊 VIEW: Membros com múltiplos canais únicos
CREATE VIEW IF NOT EXISTS v_member_multiple_channels AS
SELECT 
    member_id,
    guild_id,
    COUNT(*) as channel_count,
    GROUP_CONCAT(channel_name, ', ') as channels
FROM member_unique_channels
WHERE is_active = 1
GROUP BY member_id, guild_id
HAVING COUNT(*) > 1;


-- 🎉 SUCESSO!
-- ✅ Tabelas criadas com índices otimizados
-- ✅ Foreign keys para integridade referencial
-- ✅ Triggers para automação
-- ✅ Views para análises rápidas
-- 💡 Sistema pronto para armazenar fóruns únicos por membro!
