"""
🎮 Channel Controller - Presentation Layer
💡 Boa Prática: Coordena comandos Discord com casos de uso!
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import discord

    from infrastructure.repositories import DiscordChannelRepository

from application.dtos import CreateChannelDTO
from application.use_cases import CreateChannelUseCase, ManageTemporaryChannelsUseCase
from domain.entities import ChannelType

logger = logging.getLogger(__name__)


class ChannelController:
    """
    🎮 Controller para comandos relacionados a canais

    💡 Boa Prática: Presentation Layer que traduz comandos
    Discord para casos de uso da aplicação!
    """

    def __init__(
        self,
        channel_repository: DiscordChannelRepository, 
    ) -> None:
        """
        Inicializa o controller com repositório de canais.

        💡 Boa Prática: Injeção de dependência para facilitar testes!

        Args:
            channel_repository: Repositório para operações com canais Discord
        """
        # 💾 Guarda referência do repositório para uso nos métodos
        self.channel_repository = channel_repository
        
        # 🏗️ Cria use cases com o repositório
        self.create_channel_use_case = CreateChannelUseCase(channel_repository)
        self.manage_temp_channels_use_case = ManageTemporaryChannelsUseCase(
            channel_repository
        )
        
        # ⏱️ Cooldown para criação de salas (member_id: timestamp)
        # 💡 Boa Prática: Previne spam e race conditions
        self._creation_cooldown: dict[int, float] = {}
        self._cooldown_seconds: float = 2.0  # 2 segundos de cooldown

    async def handle_create_text_channel(
        self,
        interaction: discord.Interaction,
        name: str,
        topic: str | None = None,  # 💡 Union syntax moderna do Python 3.10+
    ) -> None:
        """
        💬 Manipula comando de criação de canal de texto

        💡 Boa Prática: Traduz dados do Discord para DTOs!

        Args:
            interaction: Interação Discord para resposta
            name: Nome do canal a ser criado
            topic: Tópico opcional do canal

        Raises:
            ValueError: Se os parâmetros forem inválidos
        """
        logger.info("💬 Processando criação de canal de texto: %s", name)

        # 💡 Validação de entrada robusta - Python 3.13
        if not name or not name.strip():
            await interaction.response.send_message(
                "❌ Nome do canal não pode estar vazio!",
                ephemeral=True,
            )
            return

        try:
            # Cria DTO de entrada
            request = CreateChannelDTO(
                name=name,
                guild_id=interaction.guild_id or 0,
                channel_type=ChannelType.TEXT,
                topic=topic,
            )

            # Executa caso de uso
            result = await self.create_channel_use_case.execute(request)

            # 💡 Pattern matching moderno - Python 3.10+
            match result.created:
                case True:
                    await interaction.response.send_message(
                        f"✅ Canal de texto **{result.name}** criado com sucesso!",
                        ephemeral=True,
                    )
                case False:
                    # 🔍 Verifica se é duplicata ou erro
                    if result.id > 0:
                        await interaction.response.send_message(
                            f"⚠️ Canal **{result.name}** já existe! Não criado duplicata.",
                            ephemeral=True,
                        )
                    else:
                        await interaction.response.send_message(
                            f"❌ Falha ao criar canal **{name}**. Tente novamente.",
                            ephemeral=True,
                        )

        except Exception as e:
            logger.exception("❌ Erro inesperado ao criar canal: %s", name)
            await interaction.response.send_message(
                "❌ Erro interno do servidor. Tente novamente em alguns minutos.",
                ephemeral=True,
            )

    async def handle_create_voice_channel(
        self,
        interaction: discord.Interaction,
        name: str,
        user_limit: int = 0,
    ) -> None:
        """
        🔊 Manipula comando de criação de canal de voz

        💡 Boa Prática: Validação de entrada e tratamento de erros!

        Args:
            interaction: Interação Discord para resposta
            name: Nome do canal de voz a ser criado
            user_limit: Limite de usuários no canal (0-99)

        Raises:
            ValueError: Se os parâmetros forem inválidos
        """
        logger.info("🔊 Processando criação de canal de voz: %s", name)

        if not name or not name.strip():
            await interaction.response.send_message(
                "❌ Nome do canal não pode estar vazio!",
                ephemeral=True,
            )
            return

        # 💡 Validação de range com pattern matching
        match user_limit:
            case x if x < 0:
                await interaction.response.send_message(
                    "❌ Limite de usuários não pode ser negativo!",
                    ephemeral=True,
                )
                return
            case x if x > 99:
                await interaction.response.send_message(
                    "❌ Limite máximo é 99 usuários!",
                    ephemeral=True,
                )
                return

        try:
            # Cria DTO de entrada
            request = CreateChannelDTO(
                name=name,
                guild_id=interaction.guild_id or 0,
                channel_type=ChannelType.VOICE,
                user_limit=user_limit,
            )

            # Executa caso de uso
            result = await self.create_channel_use_case.execute(request)

            # 💡 Pattern matching moderno - Python 3.10+
            match result.created:
                case True:
                    await interaction.response.send_message(
                        f"✅ Canal de voz **{result.name}** criado com sucesso!",
                        ephemeral=True,
                    )
                case False:
                    # 🔍 Verifica se é duplicata ou erro  
                    if result.id > 0:
                        await interaction.response.send_message(
                            f"⚠️ Canal **{result.name}** já existe! Não criado duplicata.",
                            ephemeral=True,
                        )
                    else:
                        await interaction.response.send_message(
                            f"❌ Falha ao criar canal **{name}**. Tente novamente.",
                            ephemeral=True,
                        )

        except Exception as e:
            logger.exception("❌ Erro inesperado ao criar canal de voz: %s", name)
            await interaction.response.send_message(
                "❌ Erro interno do servidor. Tente novamente em alguns minutos.",
                ephemeral=True,
            )

    async def handle_remove_voice_channel(
        self,
        channel: discord.VoiceChannel,
    ) -> None:
        """
        ❌ Manipula remoção de canal de voz

        💡 Boa Prática: Encapsula lógica de remoção!
        """
        logger.info("❌ Removendo canal de voz: %s", channel.name)

        try:
            await channel.delete(reason="Canal temporário vazio removido")
            logger.info("✅ Canal de voz %s removido com sucesso", channel.name)
        except Exception as e:
            logger.exception("❌ Falha ao remover canal de voz %s: %s", channel.name)

    async def handle_voice_state_update(
        self, 
        member: "discord.Member", 
        before: "discord.VoiceState", 
        after: "discord.VoiceState"
    ) -> bool:
        """
        Gerencia mudanças de estado de voz dos membros
        
        🔄 FLUXO AUTOMÁTICO:
        - Member entra em canal de categoria geradora → Cria canal temporário
        - Member sai de sala temporária vazia → Remove canal
        
        Args:
            member: Membro que mudou estado de voz
            before: Estado anterior de voz 
            after: Estado atual de voz
            
        Returns:
            True se ação foi executada com sucesso
        """
        try:
            # 🎯 FLUXO 1: CRIAÇÃO - Verifica se entrou em categoria geradora
            if after.channel and after.channel.category:
                # 🔍 Verifica se canal já é uma sala temporária
                is_temp_channel = await self.channel_repository.is_temporary_channel(
                    channel_id=after.channel.id,
                    guild_id=member.guild.id
                )
                
                # 🔍 Verifica se categoria está marcada como geradora
                is_generator_category = await self.channel_repository.is_temp_room_category(
                    category_id=after.channel.category.id,
                    guild_id=member.guild.id,
                    category_name=after.channel.category.name  # 💖 Passa nome para log
                )
                
                # 🎯 Se entrou em categoria geradora E canal NÃO é sala temporária
                print(is_generator_category, is_temp_channel)
                if is_generator_category and not is_temp_channel:
                    # ⏱️ Verifica cooldown para evitar criações duplicadas
                    current_time = time.time()
                    last_creation = self._creation_cooldown.get(member.id, 0)
                    time_since_last = current_time - last_creation
                    
                    if time_since_last < self._cooldown_seconds:
                        remaining = self._cooldown_seconds - time_since_last
                        logger.debug(
                            "⏱️ %s em cooldown. Aguarde %.1f segundos", 
                            member.display_name, 
                            remaining
                        )
                        return True  # 💡 Ignora silenciosamente para não spammar
                    
                    # 💾 Atualiza timestamp do último uso
                    self._creation_cooldown[member.id] = current_time
                    
                    logger.info(
                        "✨ %s entrou em categoria geradora. Criando sala temporária...", 
                        member.display_name
                    )
                    
                    # 📝 Cria DTO para canal de voz temporário
                    create_dto = CreateChannelDTO(
                        name=f"🔊 {member.display_name}",
                        channel_type=ChannelType.VOICE,
                        guild_id=member.guild.id,
                        category_id=after.channel.category.id,
                        member_id=member.id,
                        is_temporary=True
                    )
                    
                    # 🚀 Delega para Use Case
                    result = await self.create_channel_use_case.execute(create_dto)
                    
                    if result.created and result.id > 0:
                        # ✅ Move membro para o novo canal
                        new_channel = member.guild.get_channel(result.id)
                        if new_channel:
                            await member.move_to(new_channel)
                            logger.info(
                                "✅ %s movido para sala temporária: %s", 
                                member.display_name, 
                                new_channel.name
                            )
                            
                            # 🧹 Limpeza periódica do cooldown (remove entradas antigas)
                            self._cleanup_old_cooldowns()
                            
                            return True
                    else:
                        logger.error("❌ Falha ao criar sala temporária para %s", member.display_name)
                        return False
            
            # 🗑️ FLUXO 2: REMOÇÃO - Remove sala temporária quando fica vazia
            if before.channel:
                # 🔍 Verifica se canal que saiu é temporário
                is_temp_channel = await self.channel_repository.is_temporary_channel(
                    channel_id=before.channel.id,
                    guild_id=member.guild.id
                )
                
                # 🔍 Verifica se sala ficou vazia
                channel_is_empty = len(before.channel.members) == 0
                
                # 🗑️ Se é temporário E está vazio → Remove após timeout
                if is_temp_channel and channel_is_empty:
                    logger.info(
                        "🗑️ Sala temporária vazia detectada: %s - aguardando timeout...", 
                        before.channel.name
                    )
                    
                    # ⏱️ Aguarda 3 segundos antes de deletar (timeout para evitar race conditions)
                    await asyncio.sleep(3)
                    
                    # 🔍 Verifica novamente se ainda está vazia após timeout
                    try:
                        # 💡 Busca o canal novamente para verificar estado atual
                        channel_check = member.guild.get_channel(before.channel.id)
                        
                        if channel_check is None:
                            # Canal já foi deletado por outro processo
                            logger.debug("⚠️ Canal já foi removido: %s", before.channel.name)
                            return True
                        
                        # 🔍 Verifica se ainda está vazio após timeout
                        if len(channel_check.members) == 0:
                            logger.info(
                                "🗑️ Confirmado vazio após timeout. Removendo: %s", 
                                channel_check.name
                            )
                            
                            # 💾 Marca como inativo no banco primeiro
                            await self._remove_temp_channel_from_database(channel_check.id)
                            
                            # 🗑️ Remove do Discord
                            await channel_check.delete(
                                reason=f"Sala temporária vazia - último usuário: {member.display_name}"
                            )
                            
                            logger.info("✅ Sala temporária removida: %s", channel_check.name)
                            return True
                        else:
                            logger.debug(
                                "ℹ️ Canal não está mais vazio, mantendo: %s (%d membros)", 
                                channel_check.name, 
                                len(channel_check.members)
                            )
                            return True
                            
                    except Exception as delete_error:
                        logger.error(
                            "❌ Erro ao deletar canal %s: %s", 
                            before.channel.name, 
                            str(delete_error)
                        )
                        return False
                
            return True
            
        except Exception as e:
            logger.error("❌ Erro ao gerenciar estado de voz: %s", str(e))
            return False

    async def _remove_temp_channel_from_database(self, channel_id: int) -> bool:
        """
        💾 Marca canal temporário como inativo no banco de dados
        
        Args:
            channel_id: ID do canal para marcar como inativo
            
        Returns:
            True se marcação foi bem-sucedida
        """
        import aiosqlite
        from pathlib import Path
        
        try:
            db_path = Path("database/discord_bot.db")
            async with aiosqlite.connect(db_path) as db:
                await db.execute(
                    """
                    UPDATE temporary_channels 
                    SET is_active = 0, deleted_at = CURRENT_TIMESTAMP
                    WHERE channel_id = ?
                    """,
                    (channel_id,)
                )
                await db.commit()
            
            logger.info("💾 Canal %s marcado como inativo no banco", channel_id)
            return True
            
        except Exception as e:
            logger.error("❌ Erro ao remover canal do banco: %s", str(e))
            return False

    def _cleanup_old_cooldowns(self) -> None:
        """
        🧹 Remove entradas antigas do dicionário de cooldown
        
        💡 Boa Prática: Previne memory leak mantendo apenas
        cooldowns recentes (últimos 10 minutos)
        """
        current_time = time.time()
        cutoff_time = current_time - 600  # 10 minutos
        
        # 🗑️ Remove entradas antigas
        old_keys = [
            member_id 
            for member_id, timestamp in self._creation_cooldown.items() 
            if timestamp < cutoff_time
        ]
        
        for key in old_keys:
            del self._creation_cooldown[key]
        
        if old_keys:
            logger.debug("🧹 Limpou %d cooldowns antigos", len(old_keys))

    async def handle_create_member_text_channel(
        self, 
        member: "discord.Member", 
        category_id: int | None = None
    ) -> bool:
        """
        📝 Cria canal de texto automático para novo membro
        
        Args:
            member: Membro que entrou no servidor
            category_id: ID da categoria (opcional)
            
        Returns:
            True se canal foi criado com sucesso
        """
        try:
            logger.info("📝 Criando canal de texto para %s", member.display_name)
            
            # 📝 STEP 2: Cria DTO para canal de texto
            create_dto = CreateChannelDTO(
                name=f"chat-{member.display_name.lower()}",
                channel_type=ChannelType.TEXT,
                guild_id=member.guild.id,
                category_id=category_id,
                member_id=member.id,
                is_temporary=False
            )
            
            # 🚀 STEP 3: Delega para Use Case (Application Layer)
            result = await self.create_channel_use_case.execute(create_dto)
            
            if result.success:
                logger.info("✅ Canal de texto criado para %s", member.display_name)
            else:
                logger.error("❌ Falha ao criar canal: %s", result.error_message)
                
            return result.success
            
        except Exception as e:
            logger.error("❌ Erro ao criar canal para membro: %s", str(e))
            return False

    async def handle_mark_category_as_temp_generator(
        self, 
        category: "discord.CategoryChannel",
        guild_id: int
    ) -> bool:
        """
        🎙️ Marca categoria como geradora de salas temporárias
        
        💡 Funcionamento:
        - Salva categoria no banco como "temp room generator"
        - Quando alguém entrar em canal dessa categoria, cria sala temporária
        
        Args:
            category: Categoria Discord para marcar
            guild_id: ID da guild/servidor
            
        Returns:
            True se categoria foi marcada com sucesso
        """
        try:
            logger.info("Marcando categoria %s como temp generator", category.name)
            
            # 🔍 Verifica se já está marcada
            is_already_marked = await self.channel_repository.is_temp_room_category(
                category_id=category.id,
                guild_id=guild_id
            )
            
            if is_already_marked:
                logger.warning("⚠️ Categoria %s já está marcada", category.name)
                return False
            
            # 💾 Salva categoria como temp room generator
            success = await self.channel_repository.mark_category_as_temp_generator(
                category_id=category.id,
                category_name=category.name,
                guild_id=guild_id
            )
            
            if success:
                logger.info("✅ Categoria %s marcada como temp generator", category.name)
            else:
                logger.error("❌ Falha ao marcar categoria %s", category.name)
                
            return success
            
        except Exception as e:
            logger.error("❌ Erro ao marcar categoria: %s", str(e))
            return False

    async def handle_unmark_category_as_temp_generator(
        self, 
        category_id: int,
        guild_id: int
    ) -> bool:
        """
        🗑️ Remove marcação de categoria como geradora de salas temporárias
        
        Args:
            category_id: ID da categoria
            guild_id: ID da guild/servidor
            
        Returns:
            True se categoria foi desmarcada com sucesso
        """
        try:
            logger.info("🗑️ Removendo marcação de categoria ID %s", category_id)
            
            # 🗑️ Remove categoria do banco
            success = await self.channel_repository.unmark_category_as_temp_generator(
                category_id=category_id,
                guild_id=guild_id
            )
            
            if success:
                logger.info("✅ Categoria ID %s desmarcada", category_id)
            else:
                logger.warning("⚠️ Categoria ID %s não estava marcada", category_id)
                
            return success
            
        except Exception as e:
            logger.error("❌ Erro ao desmarcar categoria: %s", str(e))
            return False

