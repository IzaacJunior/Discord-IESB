import asyncio
import logging
from pathlib import Path

import discord
from decouple import config
from discord.ext import commands

# 🎯 Configuração do bot
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

logger = logging.getLogger(__name__)


class BotLoader:
    """
    🔧 Carregador moderno de extensões
    💡 Responsabilidade única: gerenciar carregamento de extensões!
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.loaded_extensions: list[str] = []
        self.failed_extensions: list[str] = []

    async def load_legacy_extensions(self) -> str:
        """
        ✨ Carrega extensões existentes (comandos e slach)
        💡 Mantém compatibilidade com estrutura atual!
        """
        logger.info("🚀 Carregando extensões existentes...")

        # 📁 Diretórios de extensões
        filer_comandos = Path(__file__).parent / "comandos"
        filer_slash = Path(__file__).parent / "slach"

        success_count = 0

        # 🛠️ Carrega comandos tradicionais
        if filer_comandos.exists():
            arquivos_comandos = list(filer_comandos.glob("*.py"))
            for file in arquivos_comandos:
                if file.stem == "__init__":
                    continue
                try:
                    await self.bot.load_extension(f"comandos.{file.stem}")
                    self.loaded_extensions.append(f"comandos.{file.stem}")
                    logger.info("✅ Comando carregado: comandos.%s", file.stem)
                    success_count += 1
                except (ImportError, AttributeError, commands.ExtensionError) as e:
                    self.failed_extensions.append(f"comandos.{file.stem}")
                    logger.warning("🟡 Falha ao carregar comandos.%s: %s", file.stem, e)

        # ⚡ Carrega comandos slash
        if filer_slash.exists():
            arquivos_slash = list(filer_slash.glob("*.py"))
            for file in arquivos_slash:
                if file.stem == "__init__":
                    continue
                try:
                    await self.bot.load_extension(f"slach.{file.stem}")
                    self.loaded_extensions.append(f"slach.{file.stem}")
                    logger.info("✅ Slash carregado: slach.%s", file.stem)
                    success_count += 1
                except (ImportError, AttributeError, commands.ExtensionError) as e:
                    self.failed_extensions.append(f"slach.{file.stem}")
                    logger.warning("🟡 Falha ao carregar slach.%s: %s", file.stem, e)

        return self._create_status_message(success_count)

    async def load_manager(self) -> bool:
        """
        🛠️ Carrega manager se existir
        💡 Componente essencial do sistema!
        """
        base_dir = Path(__file__).parent
        manager_py = base_dir / "manager.py"

        if not manager_py.exists():
            logger.warning("📝 Arquivo manager.py não encontrado")
            return False

        try:
            await self.bot.load_extension("manager")
        except (ImportError, AttributeError, commands.ExtensionError):
            self.failed_extensions.append("manager")
            logger.exception("❌ Falha ao carregar manager")
            return False
        else:
            self.loaded_extensions.append("manager")
            logger.info("✅ Manager carregado com sucesso")
            return True

    def _create_status_message(self, success_count: int) -> str:
        """
        📊 Cria mensagem de status da inicialização
        💡 Informações úteis para debug!
        """
        if success_count > 0:
            status = f"🟢 Inicialização concluída: {success_count} extensões carregadas"

            if self.loaded_extensions:
                status += f"\n✅ Carregadas: {', '.join(self.loaded_extensions)}"

            if self.failed_extensions:
                status += f"\n❌ Falharam: {', '.join(self.failed_extensions)}"

            return status
        return "🔴 Nenhuma extensão foi carregada com sucesso!"


def setup_logging() -> None:
    """
    📝 Configura logging com nível controlado por LOG_LEVEL no .env
    💡 Logs mais informativos para debug!
    """
    level_name = config("LOG_LEVEL", default="INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    # 🎨 Formato mais bonito e informativo
    format_string = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"

    logging.basicConfig(level=level, format=format_string, datefmt="%H:%M:%S")

    # 🔇 Silencia logs muito verbosos do discord.py
    discord_logger = logging.getLogger("discord")
    discord_logger.setLevel(logging.WARNING)

    logger.info("📝 Logging configurado com nível: %s", level_name)


async def start() -> None:
    """
    🚀 Função principal do bot
    💡 Organiza inicialização de forma limpa!
    """
    setup_logging()

    async with bot:
        # 🔑 Carrega token
        try:
            token = config("TOKEN")
        except (KeyError, ValueError, TypeError):
            logger.exception("❌ Token não encontrado! Verifique seu arquivo .env")
            return

        # 🔧 Carrega extensões
        loader = BotLoader(bot)

        # 🛠️ Carrega manager (essencial)
        await loader.load_manager()

        # 🎮 Carrega extensões existentes
        status = await loader.load_legacy_extensions()
        logger.info(status)

        # 🚀 Inicia bot
        logger.info("🟢 Iniciando bot...")
        await bot.start(token)


def main() -> None:
    """
    🎯 Ponto de entrada principal
    💡 Tratamento elegante de erros!
    """
    try:
        asyncio.run(start())

    except KeyboardInterrupt:
        logger.warning("🔴 Programa interrompido pelo usuário (Ctrl+C)")

    except discord.LoginFailure:
        logger.exception("❌ Token inválido! Verifique seu arquivo .env")
        logger.info("💡 Dica: TOKEN=seu_token_aqui")

    except discord.HTTPException:
        logger.exception("❌ Erro de conexão com Discord")
        logger.info("💡 Verifique sua conexão com a internet")

    except FileNotFoundError:
        logger.exception("❌ Arquivo .env não encontrado!")
        logger.info("💡 Crie um arquivo .env com: TOKEN=seu_token_aqui")

    except (RuntimeError, OSError, ConnectionError):
        logger.exception("❌ Erro fatal")

    except Exception as e:
        # Captura erros de pickle e outros erros não previstos
        if "pickle" in str(e).lower() or "invalid load key" in str(e).lower():
            logger.exception(
                "❌ Erro de arquivo corrompido detectado! Tentando corrigir..."
            )
            # Remove arquivos JSON problemáticos
            import shutil
            from pathlib import Path

            json_dir = Path("json")
            if json_dir.exists():
                try:
                    shutil.rmtree(json_dir)
                    logger.info("🔧 Pasta json removida, será recriada automaticamente")
                except (OSError, PermissionError):
                    logger.exception("❌ Erro ao limpar arquivos")
            logger.info("🔄 Tente executar novamente - arquivos serão recriados")
        else:
            logger.exception("❌ Erro inesperado")

    finally:
        logger.info("✅ Bot encerrado.")


if __name__ == "__main__":
    main()
