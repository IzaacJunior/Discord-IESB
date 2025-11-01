import logging

import discord

from domain.entities import Channel, TextChannel, VoiceChannel
from domain.repositories import ChannelRepository

logger = logging.getLogger(__name__)


class DiscordChannelRepository(ChannelRepository):
    """
    🔗 Implementação concreta do ChannelRepository usando Discord.py

    💡 Boa Prática: Implementa a interface do domain usando
    a biblioteca específica (Discord.py)!
    """

    def __init__(self, bot: discord.Client):
        self.bot = bot

    async def create_text_channel(
        self,
        name: str,
        guild_id: int,
        category_id: int | None = None,
        topic: str | None = None,
    ) -> TextChannel:
        """
        💬 Cria um canal de texto no Discord

        💡 Boa Prática: Traduz entidades do domain para objetos Discord.py!
        """
        logger.info("💬 Criando canal de texto: %s", name)

        guild = self.bot.get_guild(guild_id)
        if not guild:
            error_msg = f"Guild não encontrada: {guild_id}"
            raise ValueError(error_msg)

        category = None
        if category_id:
            category = guild.get_channel(category_id)
            if not isinstance(category, discord.CategoryChannel):
                category = None

        # Cria o canal no Discord
        discord_channel = await guild.create_text_channel(
            name=name,
            category=category,
            topic=topic,
        )

        # Converte para entidade do domain
        return TextChannel(
            id=discord_channel.id,
            name=discord_channel.name,
            guild_id=discord_channel.guild.id,
            category_id=discord_channel.category.id
            if discord_channel.category
            else None,
            topic=discord_channel.topic,
        )

    async def create_voice_channel(
        self,
        name: str,
        guild_id: int,
        category_id: int | None = None,
        user_limit: int = 0,
        bitrate: int = 64000,
    ) -> VoiceChannel:
        """
        🔊 Cria um canal de voz no Discord

        💡 Boa Prática: Parâmetros com valores padrão sensatos!
        """
        logger.info("🔊 Criando canal de voz: %s", name)

        guild = self.bot.get_guild(guild_id)
        if not guild:
            error_msg = f"Guild não encontrada: {guild_id}"
            raise ValueError(error_msg)

        category = None
        if category_id:
            category = guild.get_channel(category_id)
            if not isinstance(category, discord.CategoryChannel):
                category = None

        # Cria o canal no Discord
        discord_channel = await guild.create_voice_channel(
            name=name,
            category=category,
            user_limit=user_limit,
            bitrate=bitrate,
        )

        # Converte para entidade do domain
        return VoiceChannel(
            id=discord_channel.id,
            name=discord_channel.name,
            guild_id=discord_channel.guild.id,
            category_id=discord_channel.category.id
            if discord_channel.category
            else None,
            user_limit=discord_channel.user_limit,
            bitrate=discord_channel.bitrate,
        )

    async def create_private_forum_channel(
        self,
        name: str,
        guild_id: int,
        member_id: int,
        category_id: int | None = None,
    ) -> discord.ForumChannel:
        """
        🏠 Cria um canal de fórum privado para um membro específico
        
        💡 Boa Prática: Canal totalmente privado com permissões granulares!
        🔒 Segurança: Apenas o membro tem acesso total ao fórum
        
        Args:
            name: Nome do canal de fórum
            guild_id: ID do servidor
            member_id: ID do membro que terá acesso exclusivo
            category_id: ID da categoria (opcional)
            
        Returns:
            discord.ForumChannel: Canal de fórum criado
            
        Raises:
            ValueError: Se guild ou member não forem encontrados
        """
        logger.info("🏠 Criando fórum privado: %s para membro ID %s", name, member_id)

        guild = self.bot.get_guild(guild_id)
        if not guild:
            error_msg = f"Guild não encontrada: {guild_id}"
            raise ValueError(error_msg)

        member = guild.get_member(member_id)
        if not member:
            error_msg = f"Membro não encontrado: {member_id}"
            raise ValueError(error_msg)

        category = None
        if category_id:
            category = guild.get_channel(category_id)
            if not isinstance(category, discord.CategoryChannel):
                category = None

        # 🔒 Configuração de permissões privadas
        overwrites = {
            # ❌ @everyone não pode ver nada
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False,
                read_messages=False,
                send_messages=False,
                create_public_threads=False,
                create_private_threads=False,
            ),
            # ✅ Membro tem controle total do seu fórum
            member: discord.PermissionOverwrite(
                view_channel=True,
                read_messages=True,
                send_messages=True,
                manage_messages=True,  # 🗑️ Pode deletar mensagens
                manage_channels=True,   # ✏️ Pode editar nome e configurações
                create_public_threads=False,   # ❌ NÃO pode criar threads públicas
                create_private_threads=True,  # 🔒 Pode criar threads privadas
                manage_threads=True,    # 🎛️ Pode gerenciar threads
                embed_links=True,
                attach_files=True,
                add_reactions=True,
                use_external_emojis=True,
                read_message_history=True,
            ),
        }

        # 🏗️ Cria o canal de fórum no Discord
        forum_channel = await guild.create_forum(
            name=name,
            category=category,
            overwrites=overwrites,
            topic=f"🏠 Fórum privado de {member.display_name}",
            default_auto_archive_duration=10080,  # 7 dias
            default_sort_order=discord.ForumOrderType.latest_activity,
            default_layout=discord.ForumLayoutType.list_view,
        )

        logger.info(
            "✅ Fórum privado criado | nome=%s | member=%s | id=%s",
            name,
            member.display_name,
            forum_channel.id
        )

        return forum_channel

    async def get_channel_by_id(self, channel_id: int) -> Channel | None:
        """
        🔍 Busca canal por ID

        💡 Boa Prática: Conversão segura para entidades do domain!
        """
        discord_channel = self.bot.get_channel(channel_id)
        if not discord_channel:
            return None

        # Converte para entidade do domain baseado no tipo
        if isinstance(discord_channel, discord.TextChannel):
            return TextChannel(
                id=discord_channel.id,
                name=discord_channel.name,
                guild_id=discord_channel.guild.id,
                category_id=discord_channel.category.id
                if discord_channel.category
                else None,
                topic=discord_channel.topic,
            )
        if isinstance(discord_channel, discord.VoiceChannel):
            return VoiceChannel(
                id=discord_channel.id,
                name=discord_channel.name,
                guild_id=discord_channel.guild.id,
                category_id=discord_channel.category.id
                if discord_channel.category
                else None,
                user_limit=discord_channel.user_limit,
                bitrate=discord_channel.bitrate,
            )

        # Tipo de canal não suportado
        return None

    async def delete_channel(self, channel_id: int) -> bool:
        """
        🗑️ Remove um canal

        💡 Boa Prática: Tratamento de erros e retorno claro!
        """
        try:
            discord_channel = self.bot.get_channel(channel_id)
            if not discord_channel:
                return False

            await discord_channel.delete()
            logger.info("🗑️ Canal removido: %s", discord_channel.name)
        except discord.Forbidden:
            logger.warning("❌ Sem permissão para deletar canal: %s", channel_id)
            return False
        except discord.NotFound:
            logger.warning("❌ Canal não encontrado: %s", channel_id)
            return False
        except Exception:
            logger.exception("❌ Erro ao deletar canal: %s", channel_id)
            return False
        else:
            return True

    async def list_channels_by_guild(self, guild_id: int) -> list[Channel]:
        """
        📋 Lista todos os canais de um servidor

        💡 Boa Prática: Conversão em lote com tratamento de erros!
        """
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return []

        channels: list[Channel] = []

        for discord_channel in guild.channels:
            if isinstance(discord_channel, discord.TextChannel):
                channels.append(
                    TextChannel(
                        id=discord_channel.id,
                        name=discord_channel.name,
                        guild_id=discord_channel.guild.id,
                        category_id=discord_channel.category.id
                        if discord_channel.category
                        else None,
                        topic=discord_channel.topic,
                    )
                )
            elif isinstance(discord_channel, discord.VoiceChannel):
                channels.append(
                    VoiceChannel(
                        id=discord_channel.id,
                        name=discord_channel.name,
                        guild_id=discord_channel.guild.id,
                        category_id=discord_channel.category.id
                        if discord_channel.category
                        else None,
                        user_limit=discord_channel.user_limit,
                        bitrate=discord_channel.bitrate,
                    )
                )

        return channels

    async def channel_exists_by_name(
        self,
        name: str,
        guild_id: int,
    ) -> bool:
        """
        🔍 Verifica se canal com nome específico já existe no servidor

        💡 Boa Prática: Usa Discord.py para verificar duplicatas!
        """
        logger.debug("🔍 Verificando se canal '%s' existe no servidor %s", name, guild_id)

        guild = self.bot.get_guild(guild_id)
        if not guild:
            logger.warning("❌ Guild não encontrada: %s", guild_id)
            return False

        # 🔍 Busca canal por nome (case insensitive)
        for channel in guild.channels:
            if (isinstance(channel, (discord.TextChannel, discord.VoiceChannel)) 
                and channel.name.lower() == name.lower()):
                logger.debug("✅ Canal '%s' encontrado no servidor %s", name, guild_id)
                return True

        logger.debug("❌ Canal '%s' não existe no servidor %s", name, guild_id)
        return False

    async def get_channel_by_name_and_guild(
        self,
        name: str,
        guild_id: int,
    ) -> Channel | None:
        """
        🔍 Busca canal específico por nome e servidor

        💡 Boa Prática: Conversão segura para entidade do domain!
        """
        logger.debug("🔍 Buscando canal '%s' no servidor %s", name, guild_id)

        guild = self.bot.get_guild(guild_id)
        if not guild:
            logger.warning("❌ Guild não encontrada: %s", guild_id)
            return None

        # 🔍 Busca canal por nome (case insensitive)
        for discord_channel in guild.channels:
            if (isinstance(discord_channel, (discord.TextChannel, discord.VoiceChannel))
                and discord_channel.name.lower() == name.lower()):
                
                logger.debug("✅ Canal '%s' encontrado: ID %s", name, discord_channel.id)
                
                # Converte para entidade do domain
                if isinstance(discord_channel, discord.TextChannel):
                    return TextChannel(
                        id=discord_channel.id,
                        name=discord_channel.name,
                        guild_id=discord_channel.guild.id,
                        category_id=discord_channel.category.id
                        if discord_channel.category
                        else None,
                        topic=discord_channel.topic,
                    )
                elif isinstance(discord_channel, discord.VoiceChannel):
                    return VoiceChannel(
                        id=discord_channel.id,
                        name=discord_channel.name,
                        guild_id=discord_channel.guild.id,
                        category_id=discord_channel.category.id
                        if discord_channel.category
                        else None,
                        user_limit=discord_channel.user_limit,
                        bitrate=discord_channel.bitrate,
                    )

        logger.debug("❌ Canal '%s' não encontrado no servidor %s", name, guild_id)
        return None

    async def is_temp_room_category(
        self,
        category_id: int,
        guild_id: int,
        category_name: str | None = None,  # 💖 Nome opcional para logs mais bonitos
    ) -> bool:
        """
        🔍 Verifica se categoria está marcada como geradora de salas temporárias
        
        💡 Boa Prática: Consulta banco de dados para verificar configuração
        
        Args:
            category_id: ID da categoria Discord
            guild_id: ID do servidor Discord
            category_name: Nome da categoria (opcional, para logs)
            
        Returns:
            bool: True se categoria gera salas temporárias
        """
        import aiosqlite
        from pathlib import Path
        
        try:
            # 💖 Log com nome bonito se disponível
            display_name = f"'{category_name}'" if category_name else f"ID {category_id}"
            logger.info("🔍 Verificando se categoria %s é temp generator", display_name)
            
            # 🔍 Conecta ao banco de dados
            db_path = Path("database/discord_bot.db")
            async with aiosqlite.connect(db_path) as db:
                cursor = await db.execute(
                    """
                    SELECT is_active FROM temp_room_categories 
                    WHERE category_id = ? AND guild_id = ?
                    """,
                    (category_id, guild_id)
                )
                row = await cursor.fetchone()
                
                if row and row[0] == 1:  # is_active = 1
                    logger.info("✅ Categoria %s é geradora ativa", display_name)
                    return True
                else:
                    logger.debug("❌ Categoria %s não é geradora", display_name)
                    return False
            
        except Exception as e:
            logger.error("❌ Erro ao verificar categoria: %s", str(e))
            return False

    async def mark_category_as_temp_generator(
        self,
        category_id: int,
        category_name: str,
        guild_id: int,
    ) -> bool:
        """
        💾 Marca categoria como geradora de salas temporárias
        
        💡 Boa Prática: Persiste no banco para uso posterior
        
        Args:
            category_id: ID da categoria Discord
            category_name: Nome da categoria
            guild_id: ID do servidor Discord
            
        Returns:
            bool: True se marcação foi bem-sucedida
        """
        import aiosqlite
        from pathlib import Path
        
        try:
            logger.info("💾 Marcando categoria %s como temp generator", category_name)
            
            # 💾 Salva no banco de dados
            db_path = Path("database/discord_bot.db")
            async with aiosqlite.connect(db_path) as db:
                await db.execute(
                    """
                    INSERT INTO temp_room_categories 
                        (category_id, category_name, guild_id, is_active)
                    VALUES (?, ?, ?, 1)
                    ON CONFLICT(category_id, guild_id) 
                    DO UPDATE SET is_active = 1, updated_at = CURRENT_TIMESTAMP
                    """,
                    (category_id, category_name, guild_id)
                )
                await db.commit()
            
            logger.info(
                "✅ Categoria %s (ID: %s) marcada como temp generator para guild %s",
                category_name,
                category_id,
                guild_id
            )
            
            return True
            
        except Exception as e:
            logger.error("❌ Erro ao marcar categoria: %s", str(e))
            return False

    async def unmark_category_as_temp_generator(
        self,
        category_id: int,
        guild_id: int,
    ) -> bool:
        """
        🗑️ Remove marcação de categoria como geradora de salas temporárias
        
        Args:
            category_id: ID da categoria Discord
            guild_id: ID do servidor Discord
            
        Returns:
            bool: True se remoção foi bem-sucedida
        """
        import aiosqlite
        from pathlib import Path
        
        try:
            logger.info("🗑️ Removendo marcação de categoria ID %s", category_id)
            
            # 🗑️ Remove do banco de dados (marca como inativa)
            db_path = Path("database/discord_bot.db")
            async with aiosqlite.connect(db_path) as db:
                cursor = await db.execute(
                    """
                    UPDATE temp_room_categories 
                    SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                    WHERE category_id = ? AND guild_id = ?
                    """,
                    (category_id, guild_id)
                )
                await db.commit()
                
                # Verifica se alguma linha foi afetada
                if cursor.rowcount > 0:
                    logger.info("✅ Categoria ID %s desmarcada para guild %s", category_id, guild_id)
                    return True
                else:
                    logger.warning("⚠️ Categoria ID %s não estava marcada", category_id)
                    return False
            
        except Exception as e:
            logger.error("❌ Erro ao desmarcar categoria: %s", str(e))
            return False

    async def get_temp_channels_by_category(
        self,
        category_id: int,
        guild_id: int,
    ) -> list[int]:
        """
        🔍 Busca todos os canais temporários de uma categoria
        
        💡 Boa Prática: Retorna lista de IDs para processamento em batch
        
        Args:
            category_id: ID da categoria Discord
            guild_id: ID do servidor Discord
            
        Returns:
            list[int]: Lista com IDs dos canais temporários ativos
        """
        import aiosqlite
        from pathlib import Path
        
        try:
            logger.info(
                "🔍 Buscando canais temporários da categoria ID %s", 
                category_id
            )
            
            # 🔍 Consulta banco de dados
            db_path = Path("database/discord_bot.db")
            async with aiosqlite.connect(db_path) as db:
                cursor = await db.execute(
                    """
                    SELECT channel_id 
                    FROM temporary_channels 
                    WHERE category_id = ? AND guild_id = ? AND is_active = 1
                    ORDER BY created_at
                    """,
                    (category_id, guild_id)
                )
                rows = await cursor.fetchall()
                
                # 📋 Extrai IDs dos canais
                channel_ids = [row[0] for row in rows]
                
                logger.info(
                    "✅ Encontrados %d canais temporários na categoria %s",
                    len(channel_ids),
                    category_id
                )
                
                return channel_ids
            
        except Exception as e:
            logger.error(
                "❌ Erro ao buscar canais temporários: %s", 
                str(e)
            )
            return []

    async def is_temporary_channel(
        self,
        channel_id: int,
        guild_id: int,
    ) -> bool:
        """
        🔍 Verifica se canal é uma sala temporária ativa
        
        Args:
            channel_id: ID do canal Discord
            guild_id: ID do servidor Discord
            
        Returns:
            bool: True se canal é temporário e ativo
        """
        import aiosqlite
        from pathlib import Path
        
        try:
            logger.debug("🔍 Verificando se canal %s é temporário", channel_id)
            
            # 🔍 Consulta banco de dados
            db_path = Path("database/discord_bot.db")
            async with aiosqlite.connect(db_path) as db:
                cursor = await db.execute(
                    """
                    SELECT is_active FROM temporary_channels 
                    WHERE channel_id = ? AND guild_id = ?
                    """,
                    (channel_id, guild_id)
                )
                row = await cursor.fetchone()
                
                if row and row[0] == 1:  # is_active = 1
                    logger.debug("✅ Canal %s é temporário ativo", channel_id)
                    return True
                else:
                    logger.debug("❌ Canal %s não é temporário", channel_id)
                    return False
            
        except Exception as e:
            logger.error("❌ Erro ao verificar canal temporário: %s", str(e))
            return False

    # ═══════════════════════════════════════════════════════════════
    # 🏠 GERENCIAMENTO DE FÓRUNS ÚNICOS POR MEMBRO
    # ═══════════════════════════════════════════════════════════════

    async def is_unique_channel_category(
        self,
        category_id: int,
        guild_id: int,
    ) -> bool:
        """
        🔍 Verifica se categoria está marcada para criar fóruns únicos.
        
        💡 Boa Prática: Consulta banco de dados para verificar configuração
        
        Args:
            category_id: ID da categoria Discord
            guild_id: ID do servidor Discord
            
        Returns:
            bool: True se categoria cria fóruns únicos
        """
        import aiosqlite
        from pathlib import Path
        
        try:
            logger.debug(
                "🔍 Verificando se categoria %s gera fóruns únicos", 
                category_id
            )
            
            db_path = Path("database/discord_bot.db")
            async with aiosqlite.connect(db_path) as db:
                cursor = await db.execute(
                    """
                    SELECT category_name FROM unique_channel_categories
                    WHERE category_id = ? AND guild_id = ?
                    """,
                    (category_id, guild_id)
                )
                row = await cursor.fetchone()
                
                if row:
                    logger.debug(
                        "✅ Categoria '%s' gera fóruns únicos", 
                        row[0]
                    )
                    return True
                else:
                    logger.debug(
                        "❌ Categoria %s não gera fóruns únicos", 
                        category_id
                    )
                    return False
                
        except Exception as e:
            logger.error(
                "❌ Erro ao verificar categoria única: %s", 
                str(e)
            )
            return False

    async def get_unique_channel_category(
        self,
        guild_id: int,
    ) -> dict | None:
        """
        🔍 Busca a categoria configurada para fóruns únicos no servidor.
        
        💡 Boa Prática: Apenas UMA categoria por guilda
        
        Args:
            guild_id: ID do servidor Discord
            
        Returns:
            dict | None: Informações da categoria ou None se não configurada
                {
                    "category_id": int,
                    "category_name": str,
                    "created_at": str
                }
        """
        import aiosqlite
        from pathlib import Path
        
        try:
            logger.debug(
                "🔍 Buscando categoria configurada para guilda %s",
                guild_id
            )
            
            db_path = Path("database/discord_bot.db")
            async with aiosqlite.connect(db_path) as db:
                cursor = await db.execute(
                    """
                    SELECT category_id, category_name, created_at
                    FROM unique_channel_categories
                    WHERE guild_id = ?
                    LIMIT 1
                    """,
                    (guild_id,)
                )
                row = await cursor.fetchone()
                
                if row:
                    category_data = {
                        "category_id": row[0],
                        "category_name": row[1],
                        "created_at": row[2]
                    }
                    logger.debug(
                        "✅ Categoria configurada encontrada: '%s' (ID: %s)",
                        category_data["category_name"],
                        category_data["category_id"]
                    )
                    return category_data
                else:
                    logger.debug(
                        "❌ Nenhuma categoria configurada para guilda %s",
                        guild_id
                    )
                    return None
                
        except Exception as e:
            logger.error(
                "❌ Erro ao buscar categoria configurada: %s",
                str(e)
            )
            return None

    async def mark_category_as_unique_generator(
        self,
        category_id: int,
        category_name: str,
        guild_id: int,
    ) -> bool:
        """
        💾 Marca categoria como geradora de fóruns únicos por membro.
        
        💡 Boa Prática: Apenas UMA categoria por guilda
        🔒 Remove categoria antiga se já existir e adiciona nova
        
        Args:
            category_id: ID da categoria Discord
            category_name: Nome da categoria
            guild_id: ID do servidor Discord
            
        Returns:
            bool: True se marcação foi bem-sucedida
        """
        import aiosqlite
        from pathlib import Path
        
        try:
            logger.info(
                "💾 Marcando categoria '%s' como geradora de fóruns únicos",
                category_name
            )
            
            db_path = Path("database/discord_bot.db")
            async with aiosqlite.connect(db_path) as db:
                # 🔍 STEP 1: Verifica se já existe categoria configurada nesta guilda
                cursor = await db.execute(
                    """
                    SELECT category_id, category_name 
                    FROM unique_channel_categories
                    WHERE guild_id = ?
                    """,
                    (guild_id,)
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
                        category_id
                    )
                    
                    await db.execute(
                        """
                        DELETE FROM unique_channel_categories
                        WHERE guild_id = ?
                        """,
                        (guild_id,)
                    )
                
                # ✅ STEP 3: Insere nova categoria
                await db.execute(
                    """
                    INSERT INTO unique_channel_categories 
                    (category_id, category_name, guild_id)
                    VALUES (?, ?, ?)
                    """,
                    (category_id, category_name, guild_id)
                )
                await db.commit()
                
                logger.info(
                    "✅ Categoria '%s' marcada com sucesso (única para esta guilda)",
                    category_name
                )
                return True
                
        except Exception as e:
            logger.error(
                "❌ Erro ao marcar categoria: %s", 
                str(e)
            )
            return False

    async def unmark_category_as_unique_generator(
        self,
        category_id: int,
        guild_id: int,
    ) -> bool:
        """
        🗑️ Remove marcação de categoria como geradora de fóruns únicos.
        
        💡 Boa Prática: Remove apenas configuração, mantém registros de canais
        
        Args:
            category_id: ID da categoria Discord
            guild_id: ID do servidor Discord
            
        Returns:
            bool: True se remoção foi bem-sucedida
        """
        import aiosqlite
        from pathlib import Path
        
        try:
            logger.info(
                "🗑️ Removendo marcação da categoria ID %s",
                category_id
            )
            
            db_path = Path("database/discord_bot.db")
            async with aiosqlite.connect(db_path) as db:
                cursor = await db.execute(
                    """
                    DELETE FROM unique_channel_categories
                    WHERE category_id = ? AND guild_id = ?
                    """,
                    (category_id, guild_id)
                )
                await db.commit()
                
                if cursor.rowcount > 0:
                    logger.info(
                        "✅ Categoria ID %s desmarcada com sucesso",
                        category_id
                    )
                    return True
                else:
                    logger.warning(
                        "⚠️ Categoria ID %s não estava marcada",
                        category_id
                    )
                    return False
                
        except Exception as e:
            logger.error(
                "❌ Erro ao desmarcar categoria: %s", 
                str(e)
            )
            return False

    async def member_has_unique_channel_in_category(
        self,
        member_id: int,
        category_id: int,
        guild_id: int,
    ) -> bool:
        """
        🔍 Verifica se membro JÁ possui fórum único nesta categoria.
        
        💡 Boa Prática: Evita criar canais duplicados para o mesmo membro
        
        Args:
            member_id: ID do membro Discord
            category_id: ID da categoria Discord
            guild_id: ID do servidor Discord
            
        Returns:
            bool: True se membro já tem canal nesta categoria
        """
        import aiosqlite
        from pathlib import Path
        
        try:
            logger.debug(
                "🔍 Verificando se membro %s tem canal na categoria %s",
                member_id,
                category_id
            )
            
            db_path = Path("database/discord_bot.db")
            async with aiosqlite.connect(db_path) as db:
                cursor = await db.execute(
                    """
                    SELECT channel_id, channel_name 
                    FROM member_unique_channels
                    WHERE member_id = ? 
                    AND category_id = ? 
                    AND guild_id = ?
                    AND is_active = 1
                    """,
                    (member_id, category_id, guild_id)
                )
                row = await cursor.fetchone()
                
                if row:
                    logger.debug(
                        "✅ Membro %s já tem canal '%s' (ID: %s)",
                        member_id,
                        row[1],
                        row[0]
                    )
                    return True
                else:
                    logger.debug(
                        "❌ Membro %s não tem canal na categoria %s",
                        member_id,
                        category_id
                    )
                    return False
                
        except Exception as e:
            logger.error(
                "❌ Erro ao verificar canal do membro: %s", 
                str(e)
            )
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
        💾 Registra fórum único criado para um membro.
        
        💡 Boa Prática: Relaciona membro com canal para controle
        🔒 UNIQUE constraint evita duplicatas
        
        Args:
            member_id: ID do membro Discord
            channel_id: ID do canal criado
            channel_name: Nome do canal
            guild_id: ID do servidor Discord
            category_id: ID da categoria onde o canal está
            
        Returns:
            bool: True se registro foi bem-sucedido
        """
        import aiosqlite
        from pathlib import Path
        
        try:
            logger.info(
                "💾 Registrando canal único '%s' para membro %s",
                channel_name,
                member_id
            )
            
            db_path = Path("database/discord_bot.db")
            async with aiosqlite.connect(db_path) as db:
                try:
                    await db.execute(
                        """
                        INSERT INTO member_unique_channels
                        (member_id, channel_id, channel_name, guild_id, category_id, is_active)
                        VALUES (?, ?, ?, ?, ?, 1)
                        """,
                        (member_id, channel_id, channel_name, guild_id, category_id)
                    )
                    await db.commit()
                    
                    logger.info(
                        "✅ Canal '%s' registrado para membro %s",
                        channel_name,
                        member_id
                    )
                    return True
                    
                except aiosqlite.IntegrityError:
                    # Membro já tem canal nesta categoria
                    logger.warning(
                        "⚠️ Membro %s já tem canal na categoria %s",
                        member_id,
                        category_id
                    )
                    return False
                
        except Exception as e:
            logger.error(
                "❌ Erro ao registrar canal único: %s", 
                str(e)
            )
            return False

    async def get_member_unique_channels(
        self,
        member_id: int,
        guild_id: int,
    ) -> list[dict]:
        """
        📋 Lista todos os fóruns únicos de um membro no servidor.
        
        💡 Útil para debug e listagem de canais do membro
        
        Args:
            member_id: ID do membro Discord
            guild_id: ID do servidor Discord
            
        Returns:
            list[dict]: Lista com informações dos canais
        """
        import aiosqlite
        from pathlib import Path
        
        try:
            logger.debug(
                "📋 Buscando canais únicos do membro %s",
                member_id
            )
            
            db_path = Path("database/discord_bot.db")
            async with aiosqlite.connect(db_path) as db:
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
                    (member_id, guild_id)
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
                    member_id
                )
                
                return channels
                
        except Exception as e:
            logger.error(
                "❌ Erro ao buscar canais do membro: %s", 
                str(e)
            )
            return []
