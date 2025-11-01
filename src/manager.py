"""
🎮 Clean Architecture Manager - Presentation Layer
💡 Boa Prática: Manager centralizado apenas para coordenação e eventos!
"""

import logging

import discord
from discord.ext import commands

from presentation.controllers import ChannelController

logger = logging.getLogger(__name__)


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
            logger.warning("Permissão ausente para comando: %s", full_command)
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
            logger.warning("Bot sem permissões para comando: %s", full_command)
            await ctx.send(
                f"❌ {ctx.author.mention}, o bot não tem permissões suficientes!",
                delete_after=5,
            )

        else:
            logger.exception("Erro inesperado no comando %s", full_command)
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
            logger.warning("Permissão ausente para slash command: %s", command_name)
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
            logger.exception("Erro inesperado no slash command %s", command_name)
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
            logger.info(
                "🤖 Bot conectado: %s (ID: %s)", self.bot.user.name, self.bot.user.id
            )
            logger.info("🌐 Conectado a %d servidores", len(self.bot.guilds))

            # 🎮 Define status personalizado
            activity = discord.Activity(
                type=discord.ActivityType.watching, name="Sistema NÃO oficial do IESB"
            )
            await self.bot.change_presence(activity=activity)

            # 🔄 Sincroniza comandos slash (gerenciados pelos Cogs)
            try:
                await self.bot.tree.sync()
                logger.info("✅ Comandos slash sincronizados com sucesso!")
            except Exception:
                logger.exception("❌ Falha ao sincronizar comandos slash")

            logger.info("✨ Bot pronto para uso!")

        @self.bot.event
        async def on_voice_state_update(
            member: discord.Member,
            before: discord.VoiceState,
            after: discord.VoiceState,
        ) -> None:
            """
            🔊 Monitora mudanças de estado de voz

            💡 Boa Prática: Manager apenas delega para o controller
            """
            await self.channel_controller.handle_voice_state_update(
                member, before, after
            )

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
                    logger.warning("Sem permissão para deletar mensagem de comando")
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
    from infrastructure.repositories import DiscordChannelRepository

    # 🔧 Criação das dependências
    channel_repository = DiscordChannelRepository(bot)
    channel_controller = ChannelController(channel_repository)

    # 🎯 Manager puro (sem comandos)
    return CleanArchitectureManager(bot, channel_controller)
