"""
🚀 Clean Architecture Bot - Main Entry Point
💡 Boa Prática: Composition Root da aplicação!
"""

import asyncio
import logging
from pathlib import Path

import colorlog
import discord
from decouple import config
from discord.ext import commands

# 📊 Inicializa sistema de auditoria (DEVE vir antes de pegar o logger!)
from infrastructure.database.audit_logger import audit_logger  # noqa: F401
from infrastructure.repositories import (
    DiscordChannelRepository,
    SQLiteCategoryRepository,
)
from manager import CleanArchitectureManager
from presentation.controllers import ChannelController

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

logger = logging.getLogger(__name__)
audit = logging.getLogger("audit")


# 🏗️ Dependency Injection Container
class DIContainer:
    """
    🏗️ Container de Injeção de Dependência
    💡 Boa Prática: Composition Root centralizado!
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._setup_dependencies()

    def _setup_dependencies(self) -> None:
        """
        ⚙️ Configura todas as dependências

        💡 Boa Prática: Dependency Injection com Clean Architecture!
        """
        # 🔧 STEP 1: Cria repository de banco de dados
        self.category_db_repository = SQLiteCategoryRepository()

        # 🔧 STEP 2: Injeta no repository Discord
        self.channel_repository = DiscordChannelRepository(
            self.bot, self.category_db_repository
        )

        # 🔧 STEP 3: Cria controller com repository Discord
        self.channel_controller = ChannelController(self.channel_repository)


class CleanArchitectureBot:
    """
    🤖 Bot principal com Arquitetura Limpa
    💡 Boa Prática: Coordena toda aplicação!
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.container = DIContainer(bot)
        self.manager = CleanArchitectureManager(bot, self.container.channel_controller)

    async def load_clean_extensions(self) -> str:
        """💡 Carrega extensões da Clean Architecture"""
        logger.info("💡 Carregando extensões")

        loaded = []
        failed = []

        # Comandos tradicionais
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

        # Slash commands
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

        # Clean commands (futuro)
        clean_commands_file = Path(__file__).parent / "clean_commands.py"
        if clean_commands_file.exists():
            try:
                await self.bot.load_extension("clean_commands")
                loaded.append("clean_commands")
                logger.info("✅ Clean commands carregado")
            except (ImportError, ModuleNotFoundError, AttributeError) as e:
                failed.append("clean_commands")
                logger.warning("❌ Falha clean commands: %s", e)

        status = f"✅ {len(loaded)} extensões carregadas"
        if failed:
            status += f", ❌{len(failed)} falharam"

        return status


def setup_logging() -> None:
    """📝 Configura logging da aplicação com cores lindas 🌈"""
    level_name = config("LOG_LEVEL", default="INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    # 🎨 Configura handler com cores
    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
            datefmt="%H:%M:%S",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        )
    )

    # 💡 Configura logger raiz
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)

    # Silencia logs verbosos do discord.py
    discord_logger = logging.getLogger("discord")
    discord_logger.setLevel(logging.WARNING)


async def start() -> None:
    """🚀 Função principal de inicialização"""
    setup_logging()

    async with bot:
        try:
            token = config("TOKEN")
        except (KeyError, ValueError, TypeError):
            logger.exception("❌ Token não encontrado! Verifique .env")
            return

        clean_bot = CleanArchitectureBot(bot)
        status = await clean_bot.load_clean_extensions()
        audit.info(f"{__name__} | {status}")

        try:
            await bot.start(token)
        finally:
            logger.info("🧹 Limpando salas temporárias antes de encerrar...")
            audit.info(f"{__name__} | Bot encerrando - limpando recursos")

            try:
                from manager import create_manager

                manager = create_manager(bot)

                for guild in bot.guilds:
                    removed = (
                        await manager.channel_controller.cleanup_all_temp_channels(
                            guild
                        )
                    )
                    if removed > 0:
                        logger.info(
                            f"🧹 {removed} salas removidas do servidor {guild.name}"
                        )
                        audit.info(
                            f"{__name__} | Salas temporárias limpas ao encerrar",
                            extra={
                                "guild_id": guild.id,
                                "guild_name": guild.name,
                                "rooms_removed": removed,
                                "action": "cleanup_on_shutdown",
                            },
                        )
            except Exception:
                # 💡 Boa Prática: logger.exception() já captura o erro automaticamente
                logger.exception("❌ Erro ao limpar salas")
                audit.error(
                    f"{__name__} | Erro ao limpar salas temporárias",
                    extra={
                        "action": "cleanup_on_shutdown",
                    },
                )


def main() -> None:
    """🎯 Ponto de entrada principal"""
    try:
        asyncio.run(start())

    except KeyboardInterrupt:
        logger.info("Bot interrompido pelo usuário (Ctrl+C)")

    except discord.LoginFailure:
        logger.exception("❌ Token inválido! Verifique .env")
        logger.info("💡 Dica: TOKEN=seu_token_aqui")
        audit.critical(
            f"{__name__} | Falha de autenticação - Token inválido",
            extra={"error_type": "LoginFailure"},
        )

    except discord.HTTPException:
        logger.exception("❌ Erro de conexão com Discord")
        logger.info("💡 Verifique sua conexão com internet")
        audit.error(
            f"{__name__} | Erro de conexão HTTP com Discord",
            extra={"error_type": "HTTPException"},
        )

    except FileNotFoundError:
        logger.exception("❌ Arquivo .env não encontrado!")
        logger.info("💡 Crie .env com: TOKEN=seu_token_aqui")
        audit.critical(
            f"{__name__} | Arquivo .env não encontrado",
            extra={"error_type": "FileNotFoundError"},
        )

    except Exception as e:
        if "pickle" in str(e).lower():
            logger.exception("❌ Arquivo corrompido detectado!")
            logger.info("🔧 Remova a pasta 'json' e execute novamente")
            audit.error(
                f"{__name__} | Arquivo corrompido detectado",
                extra={"error_type": "PickleError", "error_detail": str(e)},
            )
        else:
            logger.exception("❌ Erro inesperado")
            audit.critical(
                f"{__name__} | Erro inesperado na aplicação: {e}",
                extra={"error_type": type(e).__name__, "error_detail": str(e)},
            )

    finally:
        audit.info(
            f"{__name__} | ✅ Bot encerrado.",
        )


if __name__ == "__main__":
    main()
