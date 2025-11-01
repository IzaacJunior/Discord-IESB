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
