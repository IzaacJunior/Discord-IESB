"""
🎮 Clean Architecture Manager - Presentation Layer
💡 Boa Prática: Manager centralizado apenas para coordenação e eventos!
"""

import logging

import discord
from discord.ext import commands

from presentation.controllers import ChannelController

logger = logging.getLogger(__name__)
audit = logging.getLogger("audit")


class BotErrorHandler:
    """
    ❌ Centraliza todo tratamento de erros da aplicação em um local dedicado!

    💡 Boa Prática: Separação de responsabilidades para tratamento de erros
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._setup_error_handlers()

    def _setup_error_handlers(self) -> None:
        """
        ⚙️ Configura todos os tratadores de erro do bot
        """

        # Tratador de erros de comandos tradicionais
        @self.bot.event
        async def on_command_error(ctx: commands.Context, error: Exception) -> None:
            """❌ Tratamento global de erros de comandos com prefixo"""
            await self._handle_command_error(ctx, error)

        # Tratador de erros de slash commands
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

        💡 Boa Prática: Logs específicos + feedback claro para usuários
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
                f"{__name__} | Permissão ausente para comando",
                extra={
                    "command": full_command,
                    "user_id": ctx.author.id,
                    "module": "manager.BotErrorHandler",
                },
            )
            await ctx.send(
                f"❌ {ctx.author.mention}, você não tem permissão para usar este comando!",
                delete_after=5,
            )

        elif isinstance(error, errors.CommandOnCooldown):
            logger.info("Comando em cooldown: %s", full_command)
            await ctx.send(
                f"⏰ {ctx.author.mention}, aguarde {error.retry_after:.1f}s antes de usar novamente!",
                delete_after=5,
            )

        elif isinstance(error, errors.MissingRequiredArgument):
            logger.info("Argumento obrigatório ausente: %s", full_command)
            await ctx.send(
                f"❌ {ctx.author.mention}, argumento obrigatório em falta: `{error.param.name}`",
                delete_after=5,
            )

        elif isinstance(error, Forbidden):
            audit.warning(
                f"{__name__} | Bot sem permissões para comando",
                extra={"command": full_command, "module": "manager.BotErrorHandler"},
            )
            await ctx.send(
                f"❌ {ctx.author.mention}, o bot não tem permissões suficientes!",
                delete_after=5,
            )

        else:
            audit.error(
                f"{__name__} | Erro inesperado no comando: {full_command}",
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

        💡 Boa Prática: Tratamento específico para app commands!
        """
        from discord import app_commands

        command_name = (
            interaction.command.name if interaction.command else "Comando desconhecido"
        )

        if isinstance(error, app_commands.MissingPermissions):
            audit.warning(
                f"{__name__} | Permissão ausente para slash command",
                extra={"command": command_name, "module": "manager.BotErrorHandler"},
            )
            await interaction.response.send_message(
                "❌ Você não tem permissão para usar este comando.", ephemeral=True
            )

        elif isinstance(error, app_commands.CommandOnCooldown):
            logger.info("Slash command em cooldown: %s", command_name)
            await interaction.response.send_message(
                f"⏰ Comando em cooldown. Tente novamente em {int(error.retry_after)} segundos.",
                ephemeral=True,
            )

        else:
            audit.error(
                f"{__name__} | Erro inesperado no slash command: {command_name}",
                extra={"command": command_name, "error_type": type(error).__name__},
            )
            await interaction.response.send_message(
                "❌ Ocorreu um erro inesperado ao executar o comando.", ephemeral=True
            )


class CleanArchitectureManager:
    """
    🏗️ Manager Principal - Apenas Coordenação e Eventos

    💡 Boa Prática: Manager focado apenas em:
    - ✅ Coordenação de eventos
    - ✅ Configuração do bot
    - ✅ Delegação para controllers
    - ❌ SEM comandos (isso fica nos Cogs separados)
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
        📝 Configura apenas eventos essenciais do bot

        💡 Boa Prática: Manager cuida só de eventos, não de comandos!
        """

        @self.bot.event
        async def on_ready() -> None:
            """✅ Bot conectado e configurado"""

            # 🎮 Define status personalizado
            activity = discord.Activity(
                type=discord.ActivityType.watching, name="Sistema NÃO oficial do IESB"
            )
            await self.bot.change_presence(activity=activity)

            # 🔄 Sincroniza comandos slash
            try:
                await self.bot.tree.sync()
                logger.info("✅ Comandos slash sincronizados com sucesso!")
            except Exception as e:
                audit.error(
                    f"{__name__} | Falha ao sincronizar comandos slash",
                    extra={
                        "error_type": type(e).__name__,
                        "module": "manager.on_ready",
                    },
                )
            audit.info(
                f"{__name__} | 🤖 Bot conectado: %s (ID: %s) | Servidores: %d",
                self.bot.user.name,
                self.bot.user.id,
                len(self.bot.guilds),
            )
            logger.info("✅ Bot pronto e operando!")

        @self.bot.event
        async def on_message(message: discord.Message) -> None:
            """
            📝 Processa mensagens do chat

            💡 Boa Prática: Processa comandos ANTES de deletar a mensagem!
            """
            if message.author == self.bot.user:
                return

            await self.bot.process_commands(message)

            if message.content.startswith(self.bot.command_prefix):
                try:
                    await message.delete()
                except discord.Forbidden:
                    audit.warning(
                        f"{__name__} | Sem permissão para deletar mensagem de comando"
                    )
                except discord.NotFound:
                    pass


def create_manager(bot: commands.Bot) -> CleanArchitectureManager:
    """
    🏭 Factory function para criar o manager

    💡 Boa Prática: Factory pattern + injeção de dependência


    Args:
        bot: Instância do bot Discord configurada

    Returns:
        Manager configurado apenas para coordenação
    """
    from infrastructure.repositories import (
        DiscordChannelRepository,
        SQLiteCategoryRepository,
    )

    # 🔧 Criação das dependências (Clean Architecture com injeção de dependência!)
    # 💡 Boa Prática: Repository de banco de dados separado do repository Discord
    category_db_repository = SQLiteCategoryRepository()
    channel_repository = DiscordChannelRepository(bot, category_db_repository)
    channel_controller = ChannelController(channel_repository)

    # 🎯 Manager puro (sem comandos)
    return CleanArchitectureManager(bot, channel_controller)
