"""
🗄️ Implementação SQLite do CategoryDatabaseRepository - Infrastructure Layer

💡 Boa Prática: Toda lógica SQL concentrada em um único lugar,
seguindo o Princípio da Responsabilidade Única (SOLID)!

🎯 Responsabilidade: Operações de banco de dados para categorias
"""

import logging

import aiosqlite

from config import DB_PATH
from domain.repositories import CategoryDatabaseRepository

logger = logging.getLogger(__name__)


class SQLiteCategoryRepository(CategoryDatabaseRepository):
    """
    💾 Implementação SQLite das operações de categoria

    💡 Boa Prática: Implementa APENAS operações de banco de dados,
    sem nenhuma lógica do Discord!

    ✨ Vantagens:
        - Código SQL centralizado e organizado
        - Fácil de testar (pode mockar a interface)
        - Fácil de trocar (SQLite → PostgreSQL)
        - Reutilizável em múltiplos contextos
    """

    def __init__(self, db_path: str = DB_PATH):
        """
        Inicializa o repository com o caminho do banco

        Args:
            db_path: Caminho para o arquivo SQLite (padrão: config.DB_PATH)
        """
        self.db_path = db_path

    # ═══════════════════════════════════════════════════════════════
    # 🏠 OPERAÇÕES DE SALAS TEMPORÁRIAS
    # ═══════════════════════════════════════════════════════════════

    async def is_temp_room_category(
        self,
        category_id: int,
        guild_id: int,
    ) -> bool:
        """
        🔍 Verifica se categoria está marcada como geradora de salas temporárias

        💡 Boa Prática: Query simples e direta, fácil de entender e manter!
        """
        try:
            logger.debug("🔍 Verificando se categoria %s é temp generator", category_id)

            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """
                    SELECT is_active FROM temp_room_categories
                    WHERE category_id = ? AND guild_id = ?
                    """,
                    (category_id, guild_id),
                )
                row = await cursor.fetchone()

                is_active = row and row[0] == 1
                logger.debug(
                    "%s Categoria %s %s temp generator",
                    "✅" if is_active else "❌",
                    category_id,
                    "é" if is_active else "não é",
                )
                return is_active

        except Exception:
            logger.exception("❌ Erro ao verificar categoria temp generator")
            return False

    async def mark_category_as_temp_generator(
        self,
        category_id: int,
        category_name: str,
        guild_id: int,
    ) -> bool:
        """
        💾 Marca categoria como geradora de salas temporárias

        💡 Boa Prática: Usa UPSERT para evitar duplicatas!
        """
        try:
            logger.info("💾 Marcando categoria '%s' como temp generator", category_name)

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    INSERT INTO temp_room_categories
                        (category_id, category_name, guild_id, is_active)
                    VALUES (?, ?, ?, 1)
                    ON CONFLICT(category_id, guild_id)
                    DO UPDATE SET is_active = 1, updated_at = CURRENT_TIMESTAMP
                    """,
                    (category_id, category_name, guild_id),
                )
                await db.commit()

            logger.info(
                "✅ Categoria '%s' (ID: %s) marcada como temp generator",
                category_name,
                category_id,
            )

        except Exception:
            logger.exception("❌ Erro ao marcar categoria como temp generator")
            return False
        else:
            return True

    async def unmark_category_as_temp_generator(
        self,
        category_id: int,
        guild_id: int,
    ) -> bool:
        """
        🗑️ Remove marcação de categoria como geradora de salas temporárias

        💡 Boa Prática: Soft delete (marca como inativa) mantém histórico!
        """
        try:
            logger.info("🗑️ Removendo marcação da categoria ID %s", category_id)

            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """
                    UPDATE temp_room_categories
                    SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                    WHERE category_id = ? AND guild_id = ?
                    """,
                    (category_id, guild_id),
                )
                await db.commit()

                if cursor.rowcount > 0:
                    logger.info(
                        "✅ Categoria ID %s desmarcada com sucesso",
                        category_id,
                    )
                    return True

                logger.warning("⚠️ Categoria ID %s não estava marcada", category_id)
                return False

        except Exception:
            logger.exception("❌ Erro ao desmarcar categoria temp generator")
            return False

    async def get_temp_channels_by_category(
        self,
        category_id: int,
        guild_id: int,
    ) -> list[int]:
        """
        🔍 Busca todos os canais temporários de uma categoria

        💡 Boa Prática: Retorna apenas IDs para processamento eficiente!
        """
        try:
            logger.info(
                "🔍 Buscando canais temporários da categoria ID %s",
                category_id,
            )

            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """
                    SELECT channel_id
                    FROM temporary_channels
                    WHERE category_id = ? AND guild_id = ? AND is_active = 1
                    ORDER BY created_at
                    """,
                    (category_id, guild_id),
                )
                rows = await cursor.fetchall()

                channel_ids = [row[0] for row in rows]

                logger.info(
                    "✅ Encontrados %d canais temporários na categoria %s",
                    len(channel_ids),
                    category_id,
                )
                return channel_ids

        except Exception:
            logger.exception("❌ Erro ao buscar canais temporários")
            return []

    async def is_temporary_channel(
        self,
        channel_id: int,
        guild_id: int,
    ) -> bool:
        """
        🔍 Verifica se canal é uma sala temporária ativa

        💡 Boa Prática: Query rápida com índice no channel_id!
        """
        try:
            logger.debug("🔍 Verificando se canal %s é temporário", channel_id)

            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """
                    SELECT is_active FROM temporary_channels
                    WHERE channel_id = ? AND guild_id = ?
                    """,
                    (channel_id, guild_id),
                )
                row = await cursor.fetchone()

                is_temp = row and row[0] == 1
                logger.debug(
                    "%s Canal %s %s temporário",
                    "✅" if is_temp else "❌",
                    channel_id,
                    "é" if is_temp else "não é",
                )
                return is_temp

        except Exception:
            logger.exception("❌ Erro ao verificar canal temporário")
            return False

    # ═══════════════════════════════════════════════════════════════
    # 🎓 OPERAÇÕES DE FÓRUNS ÚNICOS POR MEMBRO
    # ═══════════════════════════════════════════════════════════════

    async def is_unique_channel_category(
        self,
        category_id: int,
        guild_id: int,
    ) -> bool:
        """
        🔍 Verifica se categoria está marcada para criar fóruns únicos

        💡 Boa Prática: Verifica existência com query simples!
        """
        try:
            logger.debug(
                "🔍 Verificando se categoria %s gera fóruns únicos",
                category_id,
            )

            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """
                    SELECT category_name FROM unique_channel_categories
                    WHERE category_id = ? AND guild_id = ?
                    """,
                    (category_id, guild_id),
                )
                row = await cursor.fetchone()

                if row:
                    logger.debug("✅ Categoria '%s' gera fóruns únicos", row[0])
                    return True

                logger.debug("❌ Categoria %s não gera fóruns únicos", category_id)
                return False

        except Exception:
            logger.exception("❌ Erro ao verificar categoria única")
            return False

    async def get_unique_channel_category(
        self,
        guild_id: int,
    ) -> dict | None:
        """
        🔍 Busca a categoria configurada para fóruns únicos no servidor

        💡 Boa Prática: Apenas UMA categoria por guild (LIMIT 1)!
        """
        try:
            logger.debug("🔍 Buscando categoria configurada para guild %s", guild_id)

            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """
                    SELECT category_id, category_name, created_at
                    FROM unique_channel_categories
                    WHERE guild_id = ?
                    LIMIT 1
                    """,
                    (guild_id,),
                )
                row = await cursor.fetchone()

                if row:
                    category_data = {
                        "category_id": row[0],
                        "category_name": row[1],
                        "created_at": row[2],
                    }
                    logger.debug(
                        "✅ Categoria configurada encontrada: '%s' (ID: %s)",
                        category_data["category_name"],
                        category_data["category_id"],
                    )
                    return category_data

                logger.debug("❌ Nenhuma categoria configurada para guild %s", guild_id)
                return None

        except Exception:
            logger.exception("❌ Erro ao buscar categoria configurada")
            return None

    async def mark_category_as_unique_generator(
        self,
        category_id: int,
        category_name: str,
        guild_id: int,
    ) -> bool:
        """
        💾 Marca categoria como geradora de fóruns únicos por membro

        💡 Boa Prática: Remove antiga e insere nova (apenas UMA por guild)!
        """
        try:
            logger.info(
                "💾 Marcando categoria '%s' como geradora de fóruns únicos",
                category_name,
            )

            async with aiosqlite.connect(self.db_path) as db:
                # 🔍 STEP 1: Verifica se já existe categoria configurada
                cursor = await db.execute(
                    """
                    SELECT category_id, category_name
                    FROM unique_channel_categories
                    WHERE guild_id = ?
                    """,
                    (guild_id,),
                )
                existing = await cursor.fetchone()

                # 🗑️ STEP 2: Se já existe, remove a antiga
                if existing:
                    old_category_id, old_category_name = existing

                    logger.info(
                        "🔄 Substituindo categoria antiga '%s' (ID: %s) por '%s' (ID: %s)",
                        old_category_name,
                        old_category_id,
                        category_name,
                        category_id,
                    )

                    await db.execute(
                        """
                        DELETE FROM unique_channel_categories
                        WHERE guild_id = ?
                        """,
                        (guild_id,),
                    )

                # ✅ STEP 3: Insere nova categoria
                await db.execute(
                    """
                    INSERT INTO unique_channel_categories
                    (category_id, category_name, guild_id)
                    VALUES (?, ?, ?)
                    """,
                    (category_id, category_name, guild_id),
                )
                await db.commit()

                logger.info(
                    "✅ Categoria '%s' marcada com sucesso (única para esta guild)",
                    category_name,
                )
                return True

        except Exception:
            logger.exception("❌ Erro ao marcar categoria como única")
            return False

    async def unmark_category_as_unique_generator(
        self,
        category_id: int,
        guild_id: int,
    ) -> bool:
        """
        🗑️ Remove marcação de categoria como geradora de fóruns únicos

        💡 Boa Prática: Hard delete (remove completamente) pois só há uma!
        """
        try:
            logger.info("🗑️ Removendo marcação da categoria ID %s", category_id)

            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """
                    DELETE FROM unique_channel_categories
                    WHERE category_id = ? AND guild_id = ?
                    """,
                    (category_id, guild_id),
                )
                await db.commit()

                if cursor.rowcount > 0:
                    logger.info(
                        "✅ Categoria ID %s desmarcada com sucesso",
                        category_id,
                    )
                    return True

                logger.warning("⚠️ Categoria ID %s não estava marcada", category_id)
                return False

        except Exception:
            logger.exception("❌ Erro ao desmarcar categoria única")
            return False

    async def member_has_unique_channel_in_category(
        self,
        member_id: int,
        category_id: int,
        guild_id: int,
    ) -> bool:
        """
        🔍 Verifica se membro JÁ possui fórum único nesta categoria

        💡 Boa Prática: Evita duplicatas com query rápida!
        """
        try:
            logger.debug(
                "🔍 Verificando se membro %s tem canal na categoria %s",
                member_id,
                category_id,
            )

            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """
                    SELECT channel_id, channel_name
                    FROM member_unique_channels
                    WHERE member_id = ?
                    AND category_id = ?
                    AND guild_id = ?
                    AND is_active = 1
                    """,
                    (member_id, category_id, guild_id),
                )
                row = await cursor.fetchone()

                if row:
                    logger.debug(
                        "✅ Membro %s já tem canal '%s' (ID: %s)",
                        member_id,
                        row[1],
                        row[0],
                    )
                    return True

                logger.debug(
                    "❌ Membro %s não tem canal na categoria %s",
                    member_id,
                    category_id,
                )
                return False

        except Exception:
            logger.exception("❌ Erro ao verificar canal do membro")
            return False

    async def register_member_unique_channel(
        self,
        member_id: int,
        channel_id: int,
        channel_name: str,
        guild_id: int,
        category_id: int,
    ) -> bool:
        """
        💾 Registra fórum único criado para um membro

        💡 Boa Prática: UNIQUE constraint no banco previne duplicatas!
        """
        try:
            logger.info(
                "💾 Registrando canal único '%s' para membro %s",
                channel_name,
                member_id,
            )

            async with aiosqlite.connect(self.db_path) as db:
                try:
                    await db.execute(
                        """
                        INSERT INTO member_unique_channels
                        (member_id, channel_id, channel_name, guild_id, category_id, is_active)
                        VALUES (?, ?, ?, ?, ?, 1)
                        """,
                        (member_id, channel_id, channel_name, guild_id, category_id),
                    )
                    await db.commit()

                    logger.info(
                        "✅ Canal '%s' registrado para membro %s",
                        channel_name,
                        member_id,
                    )

                except aiosqlite.IntegrityError:
                    # 🔒 UNIQUE constraint violado: membro já tem canal
                    logger.warning(
                        "⚠️ Membro %s já tem canal na categoria %s",
                        member_id,
                        category_id,
                    )
                    return False

        except Exception:
            logger.exception("❌ Erro ao registrar canal único")
            return False
        else:
            return True

    async def get_member_unique_channels(
        self,
        member_id: int,
        guild_id: int,
    ) -> list[dict]:
        """
        📋 Lista todos os fóruns únicos de um membro no servidor

        💡 Boa Prática: Retorna dados estruturados para uso flexível!
        """
        try:
            logger.debug("📋 Buscando canais únicos do membro %s", member_id)

            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """
                    SELECT
                        channel_id,
                        channel_name,
                        category_id,
                        created_at,
                        is_active
                    FROM member_unique_channels
                    WHERE member_id = ? AND guild_id = ?
                    ORDER BY created_at DESC
                    """,
                    (member_id, guild_id),
                )
                rows = await cursor.fetchall()

                channels = [
                    {
                        "channel_id": row[0],
                        "channel_name": row[1],
                        "category_id": row[2],
                        "created_at": row[3],
                        "is_active": bool(row[4]),
                    }
                    for row in rows
                ]

                logger.debug(
                    "✅ Encontrados %d canais para membro %s",
                    len(channels),
                    member_id,
                )
                return channels

        except Exception:
            logger.exception("❌ Erro ao buscar canais do membro")
            return []
