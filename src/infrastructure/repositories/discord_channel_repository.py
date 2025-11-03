import logging

import discord

from domain.entities import Channel, TextChannel, VoiceChannel
from domain.repositories import CategoryDatabaseRepository, ChannelRepository

logger = logging.getLogger(__name__)


class DiscordChannelRepository(ChannelRepository):
    """
    🔗 Implementação concreta do ChannelRepository usando Discord.py

    💡 Boa Prática: Implementa a interface do domain usando
    a biblioteca específica (Discord.py)!
    
    ✨ NOVO: Agora usa injeção de dependência para operações de banco de dados!
    """

    def __init__(
        self, bot: discord.Client, category_db: CategoryDatabaseRepository
    ):
        """
        Inicializa o repository com bot Discord e repository de banco de dados
        
        💡 Boa Prática: Injeção de Dependência (SOLID) - facilita testes e manutenção!
        
        Args:
            bot: Cliente Discord.py
            category_db: Repository para operações de categoria no banco de dados
        """
        self.bot = bot
        self.category_db = category_db  # 🔗 Composição ao invés de herança!

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
        overwrites: dict[discord.Role | discord.Member, discord.PermissionOverwrite]
        | None = None,
    ) -> VoiceChannel:
        """
        🔊 Cria um canal de voz no Discord

        💡 Boa Prática: Parâmetros com valores padrão sensatos!
        🔒 Novo: Suporta cópia de permissões (overwrites) do canal original

        Args:
            name: Nome do canal
            guild_id: ID do servidor
            category_id: ID da categoria (opcional)
            user_limit: Limite de usuários (0 = sem limite)
            bitrate: Taxa de bits para áudio
            overwrites: Permissões específicas para roles/membros (opcional)
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

        # 🎨 Cria o canal no Discord com permissões customizadas
        discord_channel = await guild.create_voice_channel(
            name=name,
            category=category,
            user_limit=user_limit,
            bitrate=bitrate,
            overwrites=overwrites,  # 🔒 Aplica permissões personalizadas
        )

        # 💡 Log das permissões aplicadas
        if overwrites:
            logger.debug(
                "🔒 Canal criado com %d permissões customizadas", len(overwrites)
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
                manage_channels=True,  # ✏️ Pode editar nome e configurações
                create_public_threads=False,  # ❌ NÃO pode criar threads públicas
                create_private_threads=True,  # 🔒 Pode criar threads privadas
                manage_threads=True,  # 🎛️ Pode gerenciar threads
                embed_links=True,
                attach_files=True,
                add_reactions=True,
                use_external_emojis=True,
                read_message_history=True,
            ),
        }

        # 🏗️ Cria o canal de fórum no Discord
        # ⏰ Sem limite de auto-arquivo: threads nunca expiram!
        forum_channel = await guild.create_forum(
            name=name,
            category=category,
            overwrites=overwrites,
            topic=f"🏠 Fórum privado de {member.display_name}",
            default_auto_archive_duration=None,  # ♾️ Sem limite de tempo!
            default_sort_order=discord.ForumOrderType.latest_activity,
            default_layout=discord.ForumLayoutType.list_view,
            default_reaction_emoji="📗",  # 📗 Reação padrão: Livro verde fechado!
        )

        logger.info(
            "✅ Fórum privado criado | nome=%s | member=%s | id=%s",
            name,
            member.display_name,
            forum_channel.id,
        )

        return forum_channel

    async def create_forum_channel(
        self,
        name: str,
        guild_id: int,
        category_id: int | None = None,
        creator_id: int | None = None,
    ) -> discord.ForumChannel:
        """
        📚 Cria um canal de fórum público em uma categoria

        💡 Boa Prática: Canal de fórum com permissões padrão da categoria!
        ✨ Usado para criar fóruns de turmas e discussões públicas
        👥 NOVO: Cria role automático com mesmo nome do fórum
        🔒 NOVO: Configura permissões do fórum baseado no role

        Args:
            name: Nome do canal de fórum
            guild_id: ID do servidor do Discord
            category_id: ID da categoria onde o fórum será criado (opcional)
            creator_id: ID do criador (para criar role associado)

        Returns:
            discord.ForumChannel: Objeto do canal de fórum criado

        Raises:
            ValueError: Se o servidor não for encontrado
        """
        # 🔍 Busca o servidor
        guild = self.bot.get_guild(guild_id)
        if not guild:
            error_msg = f"❌ Servidor com ID {guild_id} não encontrado"
            raise ValueError(error_msg)

        # 📂 Busca a categoria (se fornecida)
        category = None
        if category_id:
            category = guild.get_channel(category_id)
            if not category or not isinstance(category, discord.CategoryChannel):
                error_msg = f"❌ Categoria com ID {category_id} não encontrada"
                raise ValueError(error_msg)

        # 👥 NOVO: Cria role automático com nome do fórum
        role_name = name.lower().replace(" ", "-")  # "Matemática" → "matemática"

        # Verifica se role já existe
        existing_role = discord.utils.get(guild.roles, name=role_name)
        if existing_role:
            logger.warning(
                "⚠️ Role '%s' já existe no servidor (ID: %s)", role_name, guild_id
            )
            role = existing_role
        else:
            # Cria novo role
            role = await guild.create_role(
                name=role_name,
                reason=f"📚 Role automático para fórum '{name}'",
                color=discord.Color.blue(),  # Cor azul para fóruns
            )
            logger.info(
                "✅ Role criado para fórum | role=%s | id=%s", role_name, role.id
            )

        # 🏗️ Cria o canal de fórum no Discord com PERMISSÕES especiais
        # ⏰ Sem limite de auto-arquivo: threads nunca expiram!
        forum_channel = await guild.create_forum(
            name=name,
            category=category,
            topic=f"📚 Fórum {name}\n🔒 Acesso: Somente @{role_name}",
            default_auto_archive_duration=None,  # ♾️ Sem limite de tempo!
            default_sort_order=discord.ForumOrderType.latest_activity,
            default_layout=discord.ForumLayoutType.list_view,
            default_reaction_emoji="📗",  # 📗 Reação padrão: Livro verde fechado!
            # 🔒 Configurações de permissão baseadas no role
            overwrites={
                guild.default_role: discord.PermissionOverwrite(
                    view_channel=False,  # ❌ @everyone NÃO vê
                    read_messages=False,
                ),
                role: discord.PermissionOverwrite(
                    view_channel=True,  # ✅ Role VÊ
                    read_messages=True,  # ✅ Lê mensagens
                    send_messages=True,  # ✅ Envia mensagens
                    create_public_threads=True,  # ✅ CRIA POSTS/THREADS (tags) no fórum! 📝
                    create_private_threads=True,  # ✅ Cria tags privadas
                    manage_threads=True,  # ✅ Gerencia suas próprias tags
                    read_message_history=True,  # ✅ Lê histórico
                    embed_links=True,  # ✅ Incorpora links
                    attach_files=True,  # ✅ Anexa arquivos
                    add_reactions=True,  # ✅ Reações
                    use_external_emojis=True,  # ✅ Emojis externos
                ),
            },
        )

        logger.info(
            "✅ Fórum público criado | nome=%s | id=%s | categoria=%s | role=%s",
            name,
            forum_channel.id,
            category.name if category else "Nenhuma",
            role_name,
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
        logger.debug(
            "🔍 Verificando se canal '%s' existe no servidor %s", name, guild_id
        )

        guild = self.bot.get_guild(guild_id)
        if not guild:
            logger.warning("❌ Guild não encontrada: %s", guild_id)
            return False

        # 🔍 Busca canal por nome (case insensitive)
        for channel in guild.channels:
            if (
                isinstance(channel, (discord.TextChannel, discord.VoiceChannel))
                and channel.name.lower() == name.lower()
            ):
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
            if (
                isinstance(discord_channel, (discord.TextChannel, discord.VoiceChannel))
                and discord_channel.name.lower() == name.lower()
            ):
                logger.debug(
                    "✅ Canal '%s' encontrado: ID %s", name, discord_channel.id
                )

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

        💡 Boa Prática: Delega para o CategoryDatabaseRepository!
        ✨ Responsabilidade Única: Discord repo não faz SQL!

        Args:
            category_id: ID da categoria Discord
            guild_id: ID do servidor Discord
            category_name: Nome da categoria (opcional, para logs)

        Returns:
            bool: True se categoria gera salas temporárias
        """
        # � Delega para o repository de banco de dados
        return await self.category_db.is_temp_room_category(category_id, guild_id)

    async def mark_category_as_temp_generator(
        self,
        category_id: int,
        category_name: str,
        guild_id: int,
    ) -> bool:
        """
        💾 Marca categoria como geradora de salas temporárias

        💡 Boa Prática: Delega para o CategoryDatabaseRepository!

        Args:
            category_id: ID da categoria Discord
            category_name: Nome da categoria
            guild_id: ID do servidor Discord

        Returns:
            bool: True se marcação foi bem-sucedida
        """
        # 🔗 Delega para o repository de banco de dados
        return await self.category_db.mark_category_as_temp_generator(
            category_id, category_name, guild_id
        )

    async def unmark_category_as_temp_generator(
        self,
        category_id: int,
        guild_id: int,
    ) -> bool:
        """
        🗑️ Remove marcação de categoria como geradora de salas temporárias

        💡 Boa Prática: Delega para o CategoryDatabaseRepository!

        Args:
            category_id: ID da categoria Discord
            guild_id: ID do servidor Discord

        Returns:
            bool: True se remoção foi bem-sucedida
        """
        # � Delega para o repository de banco de dados
        return await self.category_db.unmark_category_as_temp_generator(
            category_id, guild_id
        )

    async def get_temp_channels_by_category(
        self,
        category_id: int,
        guild_id: int,
    ) -> list[int]:
        """
        🔍 Busca todos os canais temporários de uma categoria

        💡 Boa Prática: Delega para o CategoryDatabaseRepository!

        Args:
            category_id: ID da categoria Discord
            guild_id: ID do servidor Discord

        Returns:
            list[int]: Lista com IDs dos canais temporários ativos
        """
        # 🔗 Delega para o repository de banco de dados
        return await self.category_db.get_temp_channels_by_category(
            category_id, guild_id
        )

    async def is_temporary_channel(
        self,
        channel_id: int,
        guild_id: int,
    ) -> bool:
        """
        🔍 Verifica se canal é uma sala temporária ativa

        💡 Boa Prática: Delega para o CategoryDatabaseRepository!

        Args:
            channel_id: ID do canal Discord
            guild_id: ID do servidor Discord

        Returns:
            bool: True se canal é temporário e ativo
        """
        # 🔗 Delega para o repository de banco de dados
        return await self.category_db.is_temporary_channel(channel_id, guild_id)

    # ═══════════════════════════════════════════════════════════════
    # 🏠 GERENCIAMENTO DE FÓRUNS ÚNICOS POR MEMBRO
    # ═══════════════════════════════════════════════════════════════

    async def is_unique_channel_category(
        self,
        category_id: int,
        guild_id: int,
    ) -> bool:
        """
        🔍 Verifica se categoria está marcada para criar fóruns únicos

        💡 Boa Prática: Delega para o CategoryDatabaseRepository!

        Args:
            category_id: ID da categoria Discord
            guild_id: ID do servidor Discord

        Returns:
            bool: True se categoria cria fóruns únicos
        """
        # 🔗 Delega para o repository de banco de dados
        return await self.category_db.is_unique_channel_category(category_id, guild_id)

    async def get_unique_channel_category(
        self,
        guild_id: int,
    ) -> tuple[int, str] | None:
        """
        🔍 Busca a categoria configurada para fóruns únicos no servidor

        💡 Boa Prática: Delega para o CategoryDatabaseRepository!

        Args:
            guild_id: ID do servidor Discord

        Returns:
            tuple[int, str] | None: (category_id, category_name) ou None
        """
        # 🔗 Delega para o repository de banco de dados
        return await self.category_db.get_unique_channel_category(guild_id)

    async def mark_category_as_unique_generator(
        self,
        category_id: int,
        category_name: str,
        guild_id: int,
    ) -> bool:
        """
        💾 Marca categoria como geradora de fóruns únicos por membro

        💡 Boa Prática: Delega para o CategoryDatabaseRepository!

        Args:
            category_id: ID da categoria Discord
            category_name: Nome da categoria
            guild_id: ID do servidor Discord

        Returns:
            bool: True se marcação foi bem-sucedida
        """
        # 🔗 Delega para o repository de banco de dados
        return await self.category_db.mark_category_as_unique_generator(
            category_id, category_name, guild_id
        )

    async def unmark_category_as_unique_generator(
        self,
        guild_id: int,
    ) -> bool:
        """
        🗑️ Remove marcação de categoria como geradora de fóruns únicos

        💡 Boa Prática: Delega para o CategoryDatabaseRepository!

        Args:
            guild_id: ID do servidor Discord

        Returns:
            bool: True se remoção foi bem-sucedida
        """
        # � Delega para o repository de banco de dados
        return await self.category_db.unmark_category_as_unique_generator(guild_id)

    async def member_has_unique_channel_in_category(
        self,
        member_id: int,
        category_id: int,
        guild_id: int,
    ) -> bool:
        """
        🔍 Verifica se membro JÁ possui fórum único nesta categoria

        💡 Boa Prática: Delega para o CategoryDatabaseRepository!

        Args:
            member_id: ID do membro Discord
            category_id: ID da categoria Discord
            guild_id: ID do servidor Discord

        Returns:
            bool: True se membro já tem canal nesta categoria
        """
        # 🔗 Delega para o repository de banco de dados
        return await self.category_db.member_has_unique_channel_in_category(
            member_id, category_id, guild_id
        )

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

        💡 Boa Prática: Delega para o CategoryDatabaseRepository!

        Args:
            member_id: ID do membro Discord
            channel_id: ID do canal criado
            channel_name: Nome do canal
            guild_id: ID do servidor Discord
            category_id: ID da categoria onde o canal está

        Returns:
            bool: True se registro foi bem-sucedido
        """
        # � Delega para o repository de banco de dados
        return await self.category_db.register_member_unique_channel(
            member_id, channel_id, channel_name, guild_id, category_id
        )

    async def get_member_unique_channels(
        self,
        member_id: int,
        guild_id: int,
    ) -> list[dict]:
        """
        📋 Lista todos os fóruns únicos de um membro no servidor

        💡 Boa Prática: Delega para o CategoryDatabaseRepository!

        Args:
            member_id: ID do membro Discord
            guild_id: ID do servidor Discord

        Returns:
            list[dict]: Lista com informações dos canais
        """
        # 🔗 Delega para o repository de banco de dados
        return await self.category_db.get_member_unique_channels(member_id, guild_id)
