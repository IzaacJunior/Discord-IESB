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
    
    def _setup_events(self) -> None:
        """
        📝 Configura eventos do bot
        
        💡 Boa Prática: Eventos delegados para controllers!
        """
        
        @self.bot.event
        async def on_ready():
            """✅ Bot conectado e pronto"""
            logger.info(
                "🤖 Bot conectado: %s (ID: %s)", 
                self.bot.user.name, 
                self.bot.user.id
            )
            logger.info("🌐 Conectado a %d servidores", len(self.bot.guilds))
            
            # 🎮 Atualiza status
            activity = discord.Activity(
                type=discord.ActivityType.watching, 
                name="🏗️ Clean Architecture | !help"
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
    
    async def load_legacy_extensions(self) -> str:
        """
        🔄 Carrega extensões existentes para transição gradual
        
        💡 Boa Prática: Migração gradual sem quebrar funcionalidades!
        """
        logger.info("🔄 Carregando extensões existentes para compatibilidade...")
        
        loaded = []
        failed = []
        
        # Carrega comandos existentes  
        comandos_dir = Path(__file__).parent / "comandos"
        if comandos_dir.exists():
            for file in comandos_dir.glob("*.py"):
                if file.stem == "__init__":
                    continue
                try:
                    await self.bot.load_extension(f"comandos.{file.stem}")
                    loaded.append(f"comandos.{file.stem}")
                    logger.info("✅ Comando legado: comandos.%s", file.stem)
                except Exception as e:
                    failed.append(f"comandos.{file.stem}")
                    logger.warning("❌ Falha comando legado: comandos.%s - %s", file.stem, e)
        
        # Carrega slash commands existentes
        slash_dir = Path(__file__).parent / "slach"
        if slash_dir.exists():
            for file in slash_dir.glob("*.py"):
                if file.stem == "__init__":
                    continue
                try:
                    await self.bot.load_extension(f"slach.{file.stem}")
                    loaded.append(f"slach.{file.stem}")
                    logger.info("✅ Slash legado: slach.%s", file.stem)
                except Exception as e:
                    failed.append(f"slach.{file.stem}")
                    logger.warning("❌ Falha slash legado: slach.%s - %s", file.stem, e)
        
        # Carrega manager se existir
        manager_file = Path(__file__).parent / "manager.py"
        if manager_file.exists():
            try:
                await self.bot.load_extension("manager")
                loaded.append("manager")
                logger.info("✅ Manager legado carregado")
            except Exception as e:
                failed.append("manager")
                logger.warning("❌ Falha manager legado: %s", e)
        
        status = f"🔄 Compatibilidade: {len(loaded)} carregadas"
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
        
        # 🔄 Carrega extensões legadas para transição
        status = await clean_bot.load_legacy_extensions()
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
