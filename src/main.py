"""
🚀 Clean Architecture Bot - Main Entry Point
💡 Boa Prática: Composition Root da aplicação!
"""

import asyncio
import logging
from pathlib import Path

import discord
from decouple import config
from discord.ext import commands

from infrastructure.repositories import DiscordChannelRepository
from presentation.controllers import ChannelController

# 🎯 Configuração do bot
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

logger = logging.getLogger(__name__)


# 🏗️ Dependency Injection Container
class DIContainer:
    """
    🏗️ Container de Injeção de Dependência

    💡 Boa Prática: Composition Root que configura
    todas as dependências da aplicação!
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._setup_dependencies()

    def _setup_dependencies(self) -> None:
        """
        ⚙️ Configura todas as dependências

        💡 Boa Prática: Dependency Injection Manual!
        """
        # Infrastructure Layer
        self.channel_repository = DiscordChannelRepository(self.bot)

        # Presentation Layer
        self.channel_controller = ChannelController(self.channel_repository)


class CleanArchitectureBot:
    """
    🤖 Bot principal com Arquitetura Limpa

    💡 Boa Prática: Classe principal que coordena
    toda a aplicação seguindo Clean Architecture!
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.container = DIContainer(bot)
        self._setup_events()
        self._setup_error_handlers()

    def _setup_events(self) -> None:
        """
        📝 Configura eventos do bot

        💡 Boa Prática: Eventos delegados para controllers!
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
            await self.container.channel_controller.handle_voice_state_update(
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

    def _setup_error_handlers(self) -> None:
        """
        ❌ Configura tratamento global de erros

        💡 Boa Prática: Tratamento robusto de erros integrado!
        """

        @self.bot.event
        async def on_command_error(ctx, error):
            """❌ Tratamento global de erros de comandos"""
            from discord.ext.commands import errors
            from discord import Forbidden

            full_command = (
                f"{self.bot.command_prefix}{ctx.command.name}"
                if ctx.command
                else "Comando desconhecido"
            )

            # 🤫 Ignora comandos não encontrados
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

        @self.bot.event
        async def on_app_command_error(interaction, error):
            """❌ Tratamento de erros para slash commands"""
            from discord import app_commands

            command_name = (
                interaction.command.name if interaction.command else "Comando desconhecido"
            )

            if isinstance(error, app_commands.MissingPermissions):
                logger.warning("Permissão ausente para slash command: %s", command_name)
                await interaction.response.send_message(
                    "Você não tem permissão para usar este comando.", ephemeral=True
                )

            elif isinstance(error, app_commands.CommandOnCooldown):
                logger.info("Slash command em cooldown: %s", command_name)
                await interaction.response.send_message(
                    f"Comando em cooldown. Tente novamente em {int(error.retry_after)} segundos.",
                    ephemeral=True,
                )

            else:
                logger.exception("Erro inesperado no slash command %s", command_name)
                await interaction.response.send_message(
                    "Ocorreu um erro inesperado ao executar o comando.", ephemeral=True
                )

    async def load_clean_extensions(self) -> str:
        """
        � Carrega extensões da Clean Architecture

        💡 Boa Prática: Carregamento modular e robusto!
        """
        logger.info("� Carregando extensões da Clean Architecture...")

        loaded = []
        failed = []

        # Carrega comandos da Application Layer
        commands_dir = Path(__file__).parent / "application" / "commands"
        if commands_dir.exists():
            for file in commands_dir.glob("*.py"):
                if file.stem == "__init__":
                    continue
                try:
                    await self.bot.load_extension(f"application.commands.{file.stem}")
                    loaded.append(f"application.commands.{file.stem}")
                    logger.info("✅ Comando: application.commands.%s", file.stem)
                except (ImportError, ModuleNotFoundError, AttributeError) as e:
                    failed.append(f"application.commands.{file.stem}")
                    logger.warning(
                        "❌ Falha comando: application.commands.%s - %s", file.stem, e
                    )

        # Carrega slash commands da Application Layer
        slash_dir = Path(__file__).parent / "application" / "slash_commands"
        if slash_dir.exists():
            for file in slash_dir.glob("*.py"):
                if file.stem == "__init__":
                    continue
                try:
                    await self.bot.load_extension(
                        f"application.slash_commands.{file.stem}"
                    )
                    loaded.append(f"application.slash_commands.{file.stem}")
                    logger.info("✅ Slash: application.slash_commands.%s", file.stem)
                except (ImportError, ModuleNotFoundError, AttributeError) as e:
                    failed.append(f"application.slash_commands.{file.stem}")
                    logger.warning(
                        "❌ Falha slash: application.slash_commands.%s - %s",
                        file.stem,
                        e,
                    )

        # Carrega comando clean exemplar
        clean_commands_file = Path(__file__).parent / "clean_commands.py"
        if clean_commands_file.exists():
            try:
                await self.bot.load_extension("clean_commands")
                loaded.append("clean_commands")
                logger.info("✅ Clean commands carregado")
            except (ImportError, ModuleNotFoundError, AttributeError) as e:
                failed.append("clean_commands")
                logger.warning("❌ Falha clean commands: %s", e)

        status = f"� Clean Architecture: {len(loaded)} extensões carregadas"
        if failed:
            status += f", {len(failed)} falharam"

        return status


def setup_logging() -> None:
    """
    📝 Configura logging da aplicação

    💡 Boa Prática: Logging estruturado e configurável!
    """
    level_name = config("LOG_LEVEL", default="INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    format_string = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
    logging.basicConfig(level=level, format=format_string, datefmt="%H:%M:%S")

    # Silencia logs verbosos do discord.py
    discord_logger = logging.getLogger("discord")
    discord_logger.setLevel(logging.WARNING)

    logger.info("📝 Logging configurado: %s", level_name)


async def start() -> None:
    """
    🚀 Função principal de inicialização

    💡 Boa Prática: Composition Root da aplicação!
    """
    setup_logging()

    async with bot:
        # 🔑 Carrega token
        try:
            token = config("TOKEN")
        except (KeyError, ValueError, TypeError):
            logger.exception("❌ Token não encontrado! Verifique .env")
            return

        # 🏗️ Inicializa arquitetura limpa
        clean_bot = CleanArchitectureBot(bot)

        # � Carrega extensões da Clean Architecture
        status = await clean_bot.load_clean_extensions()
        logger.info(status)

        # 🚀 Inicia bot
        logger.info("🚀 Iniciando bot com Clean Architecture...")
        await bot.start(token)


def main() -> None:
    """
    🎯 Ponto de entrada principal

    💡 Boa Prática: Tratamento robusto de erros!
    """
    try:
        asyncio.run(start())

    except KeyboardInterrupt:
        logger.warning("🔴 Interrompido pelo usuário (Ctrl+C)")

    except discord.LoginFailure:
        logger.exception("❌ Token inválido! Verifique .env")
        logger.info("💡 Dica: TOKEN=seu_token_aqui")

    except discord.HTTPException:
        logger.exception("❌ Erro de conexão com Discord")
        logger.info("💡 Verifique sua conexão com internet")

    except FileNotFoundError:
        logger.exception("❌ Arquivo .env não encontrado!")
        logger.info("💡 Crie .env com: TOKEN=seu_token_aqui")

    except Exception as e:
        if "pickle" in str(e).lower():
            logger.exception("❌ Arquivo corrompido detectado!")
            logger.info("🔧 Remova a pasta 'json' e execute novamente")
        else:
            logger.exception("❌ Erro inesperado")

    finally:
        logger.info("✅ Bot encerrado.")


if __name__ == "__main__":
    main()
