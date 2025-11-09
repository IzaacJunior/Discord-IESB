-- ============================================================================
-- 🔧 Migração: Adicionar ON DELETE CASCADE
-- ⚡ CRÍTICO: Integridade referencial automática
--
-- Data: 8 de novembro de 2025
-- Objetivo: Garantir que salas temporárias sejam deletadas quando categoria é removida
-- ============================================================================

-- ============================================================================
-- MIGRAÇÃO: Adicionar ON DELETE CASCADE à member_unique_channels
-- ============================================================================

-- 💡 Importante: SQLite não permite ALTER CONSTRAINT
-- Solução: Recriar a tabela com a constraint correta

BEGIN TRANSACTION;

-- 1️⃣ Criar tabela temporária com a nova estrutura
CREATE TABLE member_unique_channels_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    channel_name TEXT NOT NULL,
    guild_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    UNIQUE(member_id, category_id, guild_id),
    FOREIGN KEY (category_id) 
        REFERENCES unique_channel_categories(category_id)
        ON DELETE CASCADE     -- ⭐ NOVO: Deleta automaticamente!
        ON UPDATE CASCADE
);

-- 2️⃣ Copiar todos os dados da tabela antiga
INSERT INTO member_unique_channels_new (
    id, member_id, channel_id, channel_name, 
    guild_id, category_id, created_at, is_active
)
SELECT 
    id, member_id, channel_id, channel_name,
    guild_id, category_id, created_at, is_active
FROM member_unique_channels;

-- 3️⃣ Deletar trigger antigo (se existir)
DROP TRIGGER IF EXISTS update_member_channel_timestamp;

-- 4️⃣ Dropar tabela antiga
DROP TABLE member_unique_channels;

-- 5️⃣ Renomear nova tabela para nome original
ALTER TABLE member_unique_channels_new 
RENAME TO member_unique_channels;

-- 6️⃣ Recriar índices para performance
CREATE INDEX IF NOT EXISTS idx_member_channels_member 
ON member_unique_channels(member_id, guild_id);

CREATE INDEX IF NOT EXISTS idx_member_channels_category 
ON member_unique_channels(category_id, guild_id);

CREATE INDEX IF NOT EXISTS idx_member_channels_channel 
ON member_unique_channels(channel_id);

CREATE INDEX IF NOT EXISTS idx_member_channels_unique_check 
ON member_unique_channels(member_id, category_id, guild_id, is_active);

-- 7️⃣ Recriar trigger para atualizar timestamp ao reativar
CREATE TRIGGER IF NOT EXISTS update_member_channel_timestamp
AFTER UPDATE ON member_unique_channels
FOR EACH ROW
WHEN NEW.is_active = 1 AND OLD.is_active = 0
BEGIN
    UPDATE member_unique_channels 
    SET created_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- ✅ Confirmar transação
COMMIT;

-- 🎉 SUCESSO!
-- ✅ Tabela member_unique_channels agora tem ON DELETE CASCADE
-- ✅ Integridade referencial garantida
-- ✅ Salas deletadas automaticamente quando categoria é removida
