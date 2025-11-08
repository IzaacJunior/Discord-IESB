"""
🎮 Clean Architecture Manager - Presentation Layer
💡 Boa Prática: Manager centralizado apenas para coordenação e eventos!
"""

import logging

import discord
from discord.ext import commands

from config import BOT_STATUS_TEXT
from presentation.controllers import ChannelController

logger = logging.getLogger(__name__)
audit = logging.getLogger("audit")


class BotErrorHandler:
    """
    ❌ Centraliza todo tratamento de erros da aplicação
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._setup_error_handlers()

    def _setup_error_handlers(self) -> None:
        """
        ⚙️ Configura todos os tratadores de erro do bot
        """

        @self.bot.event
        async def on_command_error(ctx: commands.Context, error: Exception) -> None:
            """❌ Tratamento global de erros de comandos com prefixo"""
            await self._handle_command_error(ctx, error)

        @self.bot.event
        async def on_app_command_error(
            interaction: discord.Interaction, error: Exception
        ) -> None:
            """❌ Tratamento de erros para slash commands"""
            await self._handle_app_command_error(interaction, error)

    async def _handle_command_error(
        self, ctx: commands.Context, error: Exception
    ) -> None:
        """
        🔧 Trata erros de comandos tradicionais com mensagens amigáveis
        """
        from discord import Forbidden
        from discord.ext.commands import errors

        full_command = (
            f"{self.bot.command_prefix}{ctx.command.name}"
            if ctx.command
            else "Comando desconhecido"
        )

        if isinstance(error, errors.CommandNotFound):
            return

        if isinstance(error, errors.MissingPermissions):
            audit.warning(
                f"{__name__} | 🔐 Tentativa de uso de comando sem permissão",
                extra={
                    "command": full_command,
                    "user_id": ctx.author.id,
                    "module": "manager.BotErrorHandler",
                },
            )
            await ctx.send(
                f"❌ {ctx.author.mention}, você não tem permissão para usar este comando! 🔒",
                delete_after=5,
            )

        elif isinstance(error, errors.CommandOnCooldown):
            await ctx.send(
                f"⏰ {ctx.author.mention}, aguarde {error.retry_after:.1f}s antes de usar novamente! 💤",
                delete_after=5,
            )

        elif isinstance(error, errors.MissingRequiredArgument):
            await ctx.send(
                f"❌ {ctx.author.mention}, argumento obrigatório em falta: `{error.param.name}`",
                delete_after=5,
            )

        elif isinstance(error, Forbidden):
            audit.warning(
                f"{__name__} | 🔐 Bot sem permissões suficientes",
                extra={"command": full_command, "module": "manager.BotErrorHandler"},
            )
            await ctx.send(
                f"❌ {ctx.author.mention}, o bot não tem permissões suficientes!",
                delete_after=5,
            )

        else:
            audit.error(
                f"{__name__} | ⚠️ Erro inesperado no comando: {full_command}",
                extra={"command": full_command, "error_type": type(error).__name__},
            )
            await ctx.send(
                f"❌ {ctx.author.mention}, ocorreu um erro inesperado! Tente novamente.",
                delete_after=5,
            )

    async def _handle_app_command_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        """
        ⚡ Trata erros de slash commands com respostas ephemeral
        """
        from discord import app_commands

        command_name = (
            interaction.command.name if interaction.command else "Comando desconhecido"
        )

        if isinstance(error, app_commands.MissingPermissions):
            audit.warning(
                f"{__name__} | 🔐 Slash command sem permissão",
                extra={"command": command_name, "module": "manager.BotErrorHandler"},
            )
            await interaction.response.send_message(
                "❌ Você não tem permissão para usar este comando.", ephemeral=True
            )

        elif isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"⏰ Comando em cooldown. Tente novamente em {int(error.retry_after)} segundos.",
                ephemeral=True,
            )

        else:
            audit.error(
                f"{__name__} | ⚠️ Erro inesperado no slash command: {command_name}",
                extra={"command": command_name, "error_type": type(error).__name__},
            )
            await interaction.response.send_message(
                "❌ Ocorreu um erro inesperado ao executar o comando.", ephemeral=True
            )


class CleanArchitectureManager:
    """
    🏗️ Manager Principal - Apenas Coordenação e Eventos
    """

    def __init__(
        self, bot: commands.Bot, channel_controller: ChannelController
    ) -> None:
        self.bot = bot
        self.channel_controller = channel_controller
        self.error_handler = BotErrorHandler(bot)
        self._setup_events()

    def _setup_events(self) -> None:
        """
        📝 Configura eventos essenciais do bot
        """

        @self.bot.event
        async def on_ready() -> None:
            """✅ Bot conectado e configurado"""

            activity = discord.Activity(
                type=discord.ActivityType.watching, name=BOT_STATUS_TEXT
            )
            await self.bot.change_presence(activity=activity)

            try:
                await self.bot.tree.sync()
            except (discord.HTTPException, discord.Forbidden):
                logger.exception("❌ Erro ao sincronizar comandos slash")
            
            audit.info(
                f"{__name__} | 🤖 Bot conectado: %s (ID: %s) | Servidores: %d",
                self.bot.user.name,
                self.bot.user.id,
                len(self.bot.guilds),
            )

        @self.bot.event
        async def on_message(message: discord.Message) -> None:
            """
            📝 Processa mensagens do chat
            """
            if message.author == self.bot.user:
                return

            await self.bot.process_commands(message)

            if message.content.startswith(self.bot.command_prefix):
                try:
                    # Verifica se o bot ainda tá conectado antes de deletar
                    if not self.bot.is_closed():
                        await message.delete()
                except discord.Forbidden:
                    audit.warning(
                        "🔐 Sem permissão para deletar mensagem de comando no servidor %s",
                        message.guild.name if message.guild else "DM"
                    )
                except discord.NotFound:
                    pass
                except RuntimeError as e:
                    # Session fechada durante shutdown - ignora graciosamente
                    if "Session is closed" in str(e):
                        logger.debug("⏹️ Bot desligando, ignorando deleção de mensagem")
                    else:
                        raise


def create_manager(bot: commands.Bot) -> CleanArchitectureManager:
    """
    🏭 Factory function para criar o manager
    """
    from infrastructure.repositories import (
        DiscordChannelRepository,
        SQLiteCategoryRepository,
    )

    category_db_repository = SQLiteCategoryRepository()
    channel_repository = DiscordChannelRepository(bot, category_db_repository)
    channel_controller = ChannelController(channel_repository)

    return CleanArchitectureManager(bot, channel_controller)
