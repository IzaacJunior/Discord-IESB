"""
🎮 Channel Controller - Presentation Layer
Coordena eventos Discord com casos de uso da aplicação.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import discord
    from infrastructure.repositories import DiscordChannelRepository

from application.dtos import CreateChannelDTO
from application.use_cases import CreateChannelUseCase
from domain.entities import ChannelType

logger = logging.getLogger(__name__)


class ChannelController:
    """
    Controller para gerenciamento de canais Discord.
    
    Responsabilidades:
    - Criar canais de texto e voz
    - Gerenciar salas temporárias automáticas
    - Coordenar eventos de voz (entrada/saída)
    """

    def __init__(
        self,
        channel_repository: DiscordChannelRepository,
    ) -> None:
        """Inicializa controller."""
        self.channel_repository = channel_repository
        self.create_channel_use_case = CreateChannelUseCase(channel_repository)

    async def handle_create_text_channel(
        self,
        interaction: discord.Interaction,
        name: str,
        topic: str | None = None,
    ) -> None:
        """Cria canal de texto via comando slash."""
        logger.info("💬 Processando criação de canal de texto: %s", name)

        if not name or not name.strip():
            await interaction.response.send_message(
                "❌ Nome do canal não pode estar vazio!",
                ephemeral=True,
            )
            return

        try:
            request = CreateChannelDTO(
                name=name,
                guild_id=interaction.guild_id or 0,
                channel_type=ChannelType.TEXT,
                topic=topic,
            )

            result = await self.create_channel_use_case.execute(request)

            # Responde baseado no resultado
            match result.created:
                case True:
                    await interaction.response.send_message(
                        f"✅ Canal de texto **{result.name}** criado com sucesso!",
                        ephemeral=True,
                    )
                case False:
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
        """Cria canal de voz via comando slash."""
        logger.info("🔊 Processando criação de canal de voz: %s", name)

        if not name or not name.strip():
            await interaction.response.send_message(
                "❌ Nome do canal não pode estar vazio!",
                ephemeral=True,
            )
            return

        # Validação do limite de usuários
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
            request = CreateChannelDTO(
                name=name,
                guild_id=interaction.guild_id or 0,
                channel_type=ChannelType.VOICE,
                user_limit=user_limit,
            )

            result = await self.create_channel_use_case.execute(request)

            match result.created:
                case True:
                    await interaction.response.send_message(
                        f"✅ Canal de voz **{result.name}** criado com sucesso!",
                        ephemeral=True,
                    )
                case False:
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

    async def handle_create_member_text_channel(
        self, 
        member: discord.Member, 
        category_id: int | None = None
    ) -> bool:
        """Cria canal de texto automático para novo membro."""
        try:
            logger.info("📝 Criando canal de texto para %s", member.display_name)

            create_dto = CreateChannelDTO(
                name=f"chat-{member.display_name.lower()}",
                channel_type=ChannelType.TEXT,
                guild_id=member.guild.id,
                category_id=category_id,
                member_id=member.id,
                is_temporary=False
            )

            result = await self.create_channel_use_case.execute(create_dto)
            
            if result.success:
                logger.info("✅ Canal de texto criado para %s", member.display_name)
            else:
                logger.error("❌ Falha ao criar canal: %s", result.error_message)
                
            return result.success
            
        except Exception as e:
            logger.error("❌ Erro ao criar canal para membro: %s", str(e))
            return False

    # ═══════════════════════════════════════════════════════════════
    # 🎧 GERENCIAMENTO DE SALAS TEMPORÁRIAS
    # ═══════════════════════════════════════════════════════════════

    async def handle_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
    ) -> bool:
        """
        Ponto de entrada principal para eventos de voz.
        
        Fluxo:
        - Entrada em canal → Cria sala temporária se categoria for geradora
        - Saída de canal → Remove sala se ficou vazia
        """
        try:
            # Entrada em novo canal
            if after.channel and after.channel.category and before.channel != after.channel:
                logger.debug(
                    "📥 ENTRADA: %s → '%s'",
                    member.display_name,
                    after.channel.name
                )
                await self._handle_channel_entry(member, after)

            # Saída de canal
            if before.channel and before.channel != after.channel:
                logger.debug(
                    "� SAÍDA: %s ← '%s'",
                    member.display_name,
                    before.channel.name
                )
                await self._handle_channel_exit(member, before)

            return True

        except Exception as e:
            logger.error("❌ Erro em handle_voice_state_update: %s", str(e))
            return False

    async def _handle_channel_entry(
        self,
        member: discord.Member,
        after: discord.VoiceState
    ) -> bool:
        """
        Processa entrada em canal de voz.
        
        Verifica:
        1. Se já está em sala temporária → Ignora
        2. Se categoria é geradora → Cria sala temporária
        """
        if not after.channel:
            return False

        logger.info(
            "� SOLICITAÇÃO: %s entrou no canal '%s' (ID: %s)",
            member.display_name,
            after.channel.name,
            after.channel.id
        )

        # CHECK 1: Já está em sala temporária?
        is_temp_channel = await self.channel_repository.is_temporary_channel(
            channel_id=after.channel.id,
            guild_id=member.guild.id
        )

        if is_temp_channel:
            logger.info(
                "⏭️ IGNORADO: %s entrou em sala temporária existente",
                member.display_name
            )
            return True

        # CHECK 2: Categoria é geradora?
        if not after.channel.category:
            logger.debug("⏭️ IGNORADO: Canal sem categoria")
            return False

        is_generator_category = await self.channel_repository.is_temp_room_category(
            category_id=after.channel.category.id,
            guild_id=member.guild.id,
            category_name=after.channel.category.name
        )

        if not is_generator_category:
            logger.info(
                "⏭️ IGNORADO: Categoria '%s' não é geradora",
                after.channel.category.name
            )
            return False

        # Categoria é geradora → Cria sala temporária
        logger.info(
            "🎯 ACEITO: Criando sala temporária para %s",
            member.display_name
        )
        return await self._create_temporary_room(member, after)

    async def _create_temporary_room(
        self,
        member: discord.Member,
        after: discord.VoiceState
    ) -> bool:
        """Cria sala temporária para o membro."""
        try:
            parent_channel = after.channel
            
            # Cria DTO de criação
            create_dto = CreateChannelDTO(
                name=f"{parent_channel.name} - {member.display_name}",
                channel_type=ChannelType.VOICE,
                guild_id=member.guild.id,
                category_id=after.channel.category.id,
                member_id=member.id,
                is_temporary=True,
                user_limit=parent_channel.user_limit,
                bitrate=parent_channel.bitrate
            )

            logger.info(
                "✨ Criando sala temporária '%s' para %s",
                create_dto.name,
                member.display_name
            )

            # Executa criação
            result = await self.create_channel_use_case.execute(create_dto)

            if result.id > 0:
                # Move usuário para nova sala
                new_channel = member.guild.get_channel(result.id)
                if new_channel:
                    await member.move_to(new_channel)
                    logger.info(
                        "✅ %s movido para sala '%s' (ID: %s)",
                        member.display_name,
                        new_channel.name,
                        new_channel.id
                    )
                    return True
                else:
                    logger.error("❌ Canal ID %s não encontrado", result.id)
                    return False
            else:
                logger.error("❌ Falha ao criar sala para %s", member.display_name)
                return False

        except Exception as e:
            logger.error("❌ Erro ao criar sala temporária: %s", str(e))
            return False

    async def _handle_channel_exit(
        self,
        member: discord.Member,
        before: discord.VoiceState
    ) -> bool:
        """
        Processa saída de canal de voz.
        Remove sala temporária se ficou vazia após 3 segundos.
        """
        if not before.channel:
            return False

        logger.debug(
            "🚪 %s saiu do canal '%s' (ID: %s)",
            member.display_name,
            before.channel.name,
            before.channel.id
        )

        # Verifica se é sala temporária
        is_temp_channel = await self.channel_repository.is_temporary_channel(
            channel_id=before.channel.id,
            guild_id=member.guild.id
        )

        if not is_temp_channel:
            logger.debug(
                "ℹ️ Canal '%s' não é temporário, ignorando",
                before.channel.name
            )
            return False

        # Verifica se está vazio
        channel_is_empty = len(before.channel.members) == 0

        if not channel_is_empty:
            logger.debug(
                "ℹ️ Sala temporária '%s' ainda tem %d membros",
                before.channel.name,
                len(before.channel.members)
            )
            return False

        # Sala está vazia → Aguarda 3s antes de deletar
        logger.info(
            "🗑️ Sala temporária '%s' ficou vazia. Aguardando 3s antes de deletar...",
            before.channel.name
        )

        await asyncio.sleep(3)

        # Verifica novamente após aguardar
        try:
            channel_check = member.guild.get_channel(before.channel.id)

            if channel_check is None:
                logger.debug(
                    "ℹ️ Canal '%s' já foi removido",
                    before.channel.name
                )
                return True

            if len(channel_check.members) > 0:
                logger.debug(
                    "ℹ️ Canal '%s' não está mais vazio (%d membros), mantendo",
                    channel_check.name,
                    len(channel_check.members)
                )
                return True

            # Confirma vazio → Deleta
            logger.info(
                "🗑️ Confirmado vazio após 3s. Deletando: '%s'",
                channel_check.name
            )

            # Marca no banco como inativo
            await self._remove_temp_channel_from_database(
                channel_id=channel_check.id,
                channel_name=channel_check.name,
                category_name=channel_check.category.name if channel_check.category else ""
            )

            # Remove do Discord
            await channel_check.delete(
                reason=f"Sala temporária vazia - último usuário: {member.display_name}"
            )

            logger.info(
                "✅ Sala temporária '%s' removida com sucesso",
                channel_check.name
            )
            return True

        except Exception as delete_error:
            logger.error(
                "❌ Erro ao deletar canal '%s': %s",
                before.channel.name,
                str(delete_error)
            )
            return False

    # ═══════════════════════════════════════════════════════════════
    # 🏷️ GERENCIAMENTO DE CATEGORIAS GERADORAS
    # ═══════════════════════════════════════════════════════════════

    async def handle_mark_category_as_temp_generator(
        self,
        category: discord.CategoryChannel,
        guild_id: int
    ) -> bool:
        """
        Marca categoria como geradora de salas temporárias.
        Quando alguém entrar em canal dessa categoria, cria sala temporária.
        """
        try:
            logger.info("🎙️ Marcando categoria '%s' como geradora", category.name)

            # Verifica se já está marcada
            is_already_marked = await self.channel_repository.is_temp_room_category(
                category_id=category.id,
                guild_id=guild_id
            )

            if is_already_marked:
                logger.warning("⚠️ Categoria '%s' já está marcada", category.name)
                return False

            # Marca categoria
            success = await self.channel_repository.mark_category_as_temp_generator(
                category_id=category.id,
                category_name=category.name,
                guild_id=guild_id
            )

            if success:
                logger.info("✅ Categoria '%s' marcada como geradora", category.name)
            else:
                logger.error("❌ Falha ao marcar categoria '%s'", category.name)

            return success

        except Exception as e:
            logger.error("❌ Erro ao marcar categoria: %s", str(e))
            return False

    async def handle_unmark_category_as_temp_generator(
        self,
        category_id: int,
        guild_id: int
    ) -> bool:
        """Remove marcação de categoria como geradora de salas temporárias."""
        try:
            logger.info("🗑️ Removendo marcação de categoria ID %s", category_id)

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

    # ═══════════════════════════════════════════════════════════════
    # 🧹 LIMPEZA E MANUTENÇÃO
    # ═══════════════════════════════════════════════════════════════

    async def _remove_temp_channel_from_database(self, channel_id: int, channel_name: str = "", category_name: str = "") -> bool:
        """Marca canal temporário como inativo no banco de dados."""
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

            logger.info(
                "💾 Canal temporário marcado como inativo | Nome: '%s' | Categoria: '%s' | ID: %s",
                channel_name or "Desconhecido",
                category_name or "Desconhecida",
                channel_id
            )
            return True

        except Exception as e:
            logger.error("❌ Erro ao remover canal do banco: %s", str(e))
            return False

    async def cleanup_all_temp_channels(self, guild: discord.Guild) -> int:
        """
        Remove todas as salas temporárias do servidor.
        Chamado quando bot desconecta.
        """
        import aiosqlite
        from pathlib import Path

        removed_count = 0

        try:
            logger.info("🧹 Iniciando limpeza de todas as salas temporárias...")

            db_path = Path("database/discord_bot.db")
            async with aiosqlite.connect(db_path) as db:
                cursor = await db.execute(
                    """
                    SELECT channel_id, channel_name
                    FROM temporary_channels
                    WHERE guild_id = ? AND is_active = 1
                    """,
                    (guild.id,)
                )
                temp_channels = await cursor.fetchall()

                logger.info(f"📋 Encontradas {len(temp_channels)} salas temporárias ativas")

                # Remove cada sala
                for channel_id, channel_name in temp_channels:
                    try:
                        channel = guild.get_channel(channel_id)
                        if channel:
                            category_name = channel.category.name if channel.category else "Sem categoria"
                            await channel.delete(reason="Limpeza automática - Bot desconectando")
                            logger.info(f"✅ Sala removida: '{channel_name}' (Categoria: '{category_name}')")
                            removed_count += 1
                            
                            await self._remove_temp_channel_from_database(
                                channel_id=channel_id,
                                channel_name=channel_name,
                                category_name=category_name
                            )
                        else:
                            await self._remove_temp_channel_from_database(
                                channel_id=channel_id,
                                channel_name=channel_name
                            )

                    except Exception as e:
                        logger.error(f"❌ Erro ao remover sala {channel_name}: {str(e)}")
                        continue

            logger.info(f"✅ Limpeza concluída! {removed_count} salas removidas")
            return removed_count

        except Exception as e:
            logger.error(f"❌ Erro na limpeza geral: {str(e)}")
            return removed_count
