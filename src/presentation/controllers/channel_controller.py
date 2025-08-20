"""
🎮 Channel Controller - Presentation Layer
💡 Boa Prática: Coordena comandos Discord com casos de uso!
"""

import logging
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from application.dtos import ChannelResponseDTO, CreateChannelDTO
from application.use_cases import CreateChannelUseCase, ManageTemporaryChannelsUseCase
from domain.entities import ChannelType

if TYPE_CHECKING:
    from infrastructure.repositories import DiscordChannelRepository

logger = logging.getLogger(__name__)


class ChannelController:
    """
    🎮 Controller para comandos relacionados a canais
    
    💡 Boa Prática: Presentation Layer que traduz comandos
    Discord para casos de uso da aplicação!
    """
    
    def __init__(
        self,
        channel_repository: "DiscordChannelRepository",
    ):
        self.create_channel_use_case = CreateChannelUseCase(channel_repository)
        self.manage_temp_channels_use_case = ManageTemporaryChannelsUseCase(channel_repository)
    
    async def handle_create_text_channel(
        self,
        interaction: discord.Interaction,
        name: str,
        topic: str | None = None,
    ) -> None:
        """
        💬 Manipula comando de criação de canal de texto
        
        💡 Boa Prática: Traduz dados do Discord para DTOs!
        """
        logger.info("💬 Processando criação de canal de texto: %s", name)
        
        # Cria DTO de entrada
        request = CreateChannelDTO(
            name=name,
            guild_id=interaction.guild_id or 0,
            channel_type=ChannelType.TEXT,
            topic=topic,
        )
        
        # Executa caso de uso
        result = await self.create_channel_use_case.execute(request)
        
        # Responde baseado no resultado
        if result.created:
            await interaction.response.send_message(
                f"✅ Canal de texto **{result.name}** criado com sucesso!",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"❌ Falha ao criar canal **{name}**. Tente novamente.",
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
        """
        logger.info("🔊 Processando criação de canal de voz: %s", name)
        
        # Validação simples
        if user_limit < 0 or user_limit > 99:
            await interaction.response.send_message(
                "❌ Limite de usuários deve estar entre 0 e 99!",
                ephemeral=True,
            )
            return
        
        # Cria DTO de entrada
        request = CreateChannelDTO(
            name=name,
            guild_id=interaction.guild_id or 0,
            channel_type=ChannelType.VOICE,
            user_limit=user_limit,
        )
        
        # Executa caso de uso
        result = await self.create_channel_use_case.execute(request)
        
        # Responde baseado no resultado
        if result.created:
            await interaction.response.send_message(
                f"✅ Canal de voz **{result.name}** criado com sucesso!",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"❌ Falha ao criar canal **{name}**. Tente novamente.",
                ephemeral=True,
            )
    
    async def handle_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        """
        🔄 Manipula mudanças de estado de voz (criação/remoção temporária)
        
        💡 Boa Prática: Lógica de eventos complexa delegada
        para casos de uso!
        """
        if member.bot:
            return
        
        # Membro entrou em um canal
        if after.channel and not before.channel:
            logger.info("👤 %s entrou no canal %s", member.name, after.channel.name)
            
            result = await self.manage_temp_channels_use_case.create_temporary_channel(
                base_channel_id=after.channel.id,
                guild_id=member.guild.id,
            )
            
            if result and result.created:
                logger.info("✅ Canal temporário criado: %s", result.name)
        
        # Membro saiu de um canal
        if before.channel and not after.channel:
            logger.info("👤 %s saiu do canal %s", member.name, before.channel.name)
            
            # Tenta limpar canal vazio
            success = await self.manage_temp_channels_use_case.cleanup_empty_channel(
                channel_id=before.channel.id
            )
            
            if success:
                logger.info("🧹 Canal vazio removido: %s", before.channel.name)
