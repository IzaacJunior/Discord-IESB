"""
🎮 Comandos Clean Architecture - Presentation Layer
💡 Boa Prática: Commands/Cogs usando a nova arquitetura!
"""

import logging

import discord
from discord import app_commands
from discord.ext import commands

from presentation.controllers import ChannelController

logger = logging.getLogger(__name__)


class CleanChannelCommands(commands.Cog):
    """
    🎮 Comandos de canal usando Clean Architecture

    💡 Boa Prática: Cog que delega operações para controllers!
    """

    def __init__(self, bot: commands.Bot, channel_controller: ChannelController):
        self.bot = bot
        self.channel_controller = channel_controller

    @app_commands.command(
        name="criar_texto",
        description="🏗️ Cria um novo canal de texto usando Clean Architecture",
    )
    @app_commands.describe(
        nome="Nome do canal de texto", topico="Tópico/descrição do canal (opcional)"
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    async def criar_canal_texto(
        self, interaction: discord.Interaction, nome: str, topico: str | None = None
    ):
        """
        💬 Comando para criar canal de texto

        💡 Boa Prática: Validação na UI, lógica no Controller!
        """
        # Validação básica na UI
        if len(nome) < 2 or len(nome) > 100:
            await interaction.response.send_message(
                "❌ Nome deve ter entre 2 e 100 caracteres!", ephemeral=True
            )
            return

        # Delega para o controller
        await self.channel_controller.handle_create_text_channel(
            interaction, nome, topico
        )

    @app_commands.command(
        name="criar_voz",
        description="🔊 Cria um novo canal de voz usando Clean Architecture",
    )
    @app_commands.describe(
        nome="Nome do canal de voz", limite="Limite de usuários (0 = ilimitado, máx 99)"
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    async def criar_canal_voz(
        self, interaction: discord.Interaction, nome: str, limite: int = 0
    ):
        """
        🔊 Comando para criar canal de voz

        💡 Boa Prática: Separação clara de responsabilidades!
        """
        # Validação básica na UI
        if len(nome) < 2 or len(nome) > 100:
            await interaction.response.send_message(
                "❌ Nome deve ter entre 2 e 100 caracteres!", ephemeral=True
            )
            return

        # Delega para o controller
        await self.channel_controller.handle_create_voice_channel(
            interaction, nome, limite
        )

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        """
        🔄 Evento de mudança de estado de voz

        💡 Boa Prática: Evento delegado para o controller!
        """
        await self.channel_controller.handle_voice_state_update(member, before, after)


async def setup(bot: commands.Bot):
    """
    ⚙️ Setup do Cog com injeção de dependência

    💡 Boa Prática: Como fazer DI com cogs existentes!
    """
    # Aqui você precisaria acessar o container de DI
    # Por enquanto vamos criar um exemplo simples
    from infrastructure.repositories import DiscordChannelRepository

    channel_repository = DiscordChannelRepository(bot)
    channel_controller = ChannelController(channel_repository)

    await bot.add_cog(CleanChannelCommands(bot, channel_controller))
