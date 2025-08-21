"""
🎮 Clean Architecture Manager - Presentation Layer
💡 Boa Prática: Manager centralizado para comandos e tratamento de erros!
"""

import logging

import discord
from discord import app_commands
from discord.ext import commands

from presentation.controllers import ChannelController

logger = logging.getLogger(__name__)


class BotErrorHandler:
    """
    ❌ Gerenciador Central de Erros

    💡 Boa Prática: Centraliza todo tratamento de erros
    da aplicação em um local dedicado!
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._setup_error_handlers()

    def _setup_error_handlers(self) -> None:
        """
        ⚙️ Configura todos os tratadores de erro

        💡 Boa Prática: Separação de responsabilidades!
        """

        @self.bot.event
        async def on_command_error(ctx, error):
            """❌ Tratamento global de erros de comandos"""
            await self._handle_command_error(ctx, error)

        @self.bot.event
        async def on_app_command_error(interaction, error):
            """❌ Tratamento de erros para slash commands"""
            await self._handle_app_command_error(interaction, error)

    async def _handle_command_error(
        self, ctx: commands.Context, error: Exception
    ) -> None:
        """
        🔧 Trata erros de comandos tradicionais

        💡 Boa Prática: Método dedicado para cada tipo de erro!
        """
        from discord import Forbidden
        from discord.ext.commands import errors

        full_command = (
            f"{self.bot.command_prefix}{ctx.command.name}"
            if ctx.command
            else "Comando desconhecido"
        )

        # 🤫 Ignora comandos não encontrados silenciosamente
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
        ⚡ Trata erros de slash commands

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
    🏗️ Manager Principal da Clean Architecture

    💡 Boa Prática: Centraliza toda a configuração
    e coordenação dos componentes!
    """

    def __init__(self, bot: commands.Bot, channel_controller: ChannelController):
        self.bot = bot
        self.channel_controller = channel_controller
        self.error_handler = BotErrorHandler(bot)
        self._setup_events()

    def _setup_events(self) -> None:
        """
        📝 Configura eventos do bot

        💡 Boa Prática: Eventos organizados no manager!
        """

        @self.bot.event
        async def on_ready():
            """✅ Bot conectado e pronto"""
            logger.info(
                "🤖 Bot conectado: %s (ID: %s)", self.bot.user.name, self.bot.user.id
            )
            logger.info("🌐 Conectado a %d servidores", len(self.bot.guilds))

            # 🎮 Atualiza status
            activity = discord.Activity(
                type=discord.ActivityType.watching, name="🏗️ Clean Architecture | !help"
            )
            await self.bot.change_presence(activity=activity)

            # Sincroniza comandos slash
            try:
                await self.bot.tree.sync()
                logger.info("✅ Comandos slash sincronizados!")
            except Exception:
                logger.exception("❌ Erro ao sincronizar comandos slash")

            logger.info("✨ Bot pronto para uso!")

        @self.bot.event
        async def on_voice_state_update(member, before, after):
            """🔊 Delegação para o controller de canais"""
            await self.channel_controller.handle_voice_state_update(
                member, before, after
            )

        @self.bot.event
        async def on_message(message):
            """📝 Processa mensagens"""
            if message.author == self.bot.user:
                return

            # Remove comandos com prefixo para manter chat limpo
            if message.content.startswith(self.bot.command_prefix):
                await message.delete()


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
