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

from config import COMMAND_PREFIX
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
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

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
        """Carrega extensões da Clean Architecture"""
        loaded = []
        failed = []

        commands_dir = Path(__file__).parent / "application" / "commands"
        if commands_dir.exists():
            for file in commands_dir.glob("*.py"):
                if file.stem == "__init__":
                    continue
                try:
                    await self.bot.load_extension(f"application.commands.{file.stem}")
                    loaded.append(f"application.commands.{file.stem}")
                except (ImportError, ModuleNotFoundError, AttributeError) as e:
                    failed.append(f"application.commands.{file.stem}")
                    audit.warning(
                        f"{__name__} | ❌ Falha ao carregar comando: {file.stem}",
                        extra={"extension": f"application.commands.{file.stem}", "error": str(e)}
                    )

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
                except (ImportError, ModuleNotFoundError, AttributeError) as e:
                    failed.append(f"application.slash_commands.{file.stem}")
                    audit.warning(
                        f"{__name__} | ❌ Falha ao carregar slash: {file.stem}",
                        extra={"extension": f"application.slash_commands.{file.stem}", "error": str(e)}
                    )

        clean_commands_file = Path(__file__).parent / "clean_commands.py"
        if clean_commands_file.exists():
            try:
                await self.bot.load_extension("clean_commands")
                loaded.append("clean_commands")
            except (ImportError, ModuleNotFoundError, AttributeError) as e:
                failed.append("clean_commands")
                audit.warning(
                    f"{__name__} | ❌ Falha ao carregar clean_commands",
                    extra={"extension": "clean_commands", "error": str(e)}
                )

        total_extensions = len(loaded) + len(failed)
        status = f"✅ {len(loaded)}/{total_extensions} extensões carregadas"
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


async def cleanup_temp_rooms() -> None:
    """
    🧹 Limpa todas as salas temporárias de todos os servidores
    """
    audit.info(
        f"{__name__} | 🧹 Começando limpeza de recursos ao encerrar",
        extra={"action": "cleanup_on_shutdown"},
    )

    try:
        from manager import create_manager

        manager = create_manager(bot)

        for guild in bot.guilds:
            try:
                removed = (
                    await manager.channel_controller.cleanup_all_temp_channels(guild)
                )
                if removed > 0:
                    audit.info(
                        f"{__name__} | 🧹 {removed} salas removidas do servidor {guild.name}",
                        extra={
                            "guild_id": guild.id,
                            "guild_name": guild.name,
                            "rooms_removed": removed,
                            "action": "cleanup_on_shutdown",
                        },
                    )
            except Exception:
                logger.exception(f"❌ Erro ao limpar salas do servidor {guild.name}")
                audit.error(
                    f"{__name__} | ⚠️ Erro ao limpar salas de servidor específico",
                    extra={
                        "guild_id": guild.id,
                        "guild_name": guild.name,
                        "action": "cleanup_on_shutdown",
                    },
                )

    except Exception:
        logger.exception("❌ Erro crítico durante limpeza de salas")
        audit.error(
            f"{__name__} | ⚠️ Erro crítico durante limpeza de salas temporárias",
            extra={"action": "cleanup_on_shutdown"},
        )


async def start() -> None:
    """
    🚀 Função principal de inicialização

    💡 Boa Prática: Gerencia ciclo de vida completo do bot com async context manager!
    ✨ Segurança: Valida token antes de inicializar recursos
    🧹 Limpeza: Garante que recursos sejam liberados corretamente
    """
    setup_logging()

    # 🔐 STEP 1: Valida token ANTES de qualquer inicialização
    try:
        token = config("TOKEN")
    except (KeyError, ValueError, TypeError):
        audit.critical(
            f"{__name__} | 🔐 Token não configurado em .env",
            extra={"error_type": "TokenNotFound"},
        )
        return

    async with bot:
        clean_bot = CleanArchitectureBot(bot)
        status = await clean_bot.load_clean_extensions()
        audit.info(f"{__name__} | {status}")

        try:
            audit.info(
                f"{__name__} | 🚀 Conectando ao Discord",
                extra={"action": "bot_start"},
            )
            await bot.start(token)
        except discord.LoginFailure:
            audit.critical(
                f"{__name__} | 🔐 Token inválido durante start()",
                extra={"error_type": "LoginFailure"},
            )
            raise
        except Exception:
            audit.error(
                f"{__name__} | 🔴 Erro durante bot.start()",
                extra={"error_type": "StartupError"},
            )
            raise
        finally:
            await cleanup_temp_rooms()


def main() -> None:
    """🎯 Ponto de entrada principal"""
    try:
        asyncio.run(start())

    except KeyboardInterrupt:
        audit.info(
            f"{__name__} | 👋 Bot interrompido pelo usuário (Ctrl+C)",
            extra={"action": "shutdown"},
        )

    except discord.LoginFailure:
        audit.critical(
            f"{__name__} | 🔐 Token inválido - verifique .env",
            extra={"error_type": "LoginFailure"},
        )

    except discord.HTTPException:
        audit.error(
            f"{__name__} | 🌐 Erro de conexão HTTP com Discord",
            extra={"error_type": "HTTPException"},
        )

    except FileNotFoundError:
        audit.critical(
            f"{__name__} | 📄 Arquivo .env não encontrado",
            extra={"error_type": "FileNotFoundError"},
        )

    except Exception as e:
        if "pickle" in str(e).lower():
            audit.error(
                f"{__name__} | 🔴 Arquivo corrompido detectado",
                extra={"error_type": "PickleError", "error_detail": str(e)},
            )
        else:
            audit.critical(
                f"{__name__} | 🔴 Erro inesperado na aplicação",
                extra={"error_type": type(e).__name__, "error_detail": str(e)},
            )

    finally:
        audit.info(
            f"{__name__} | ✅ Bot encerrado com sucesso",
            extra={"action": "shutdown"},
        )


if __name__ == "__main__":
    main()
