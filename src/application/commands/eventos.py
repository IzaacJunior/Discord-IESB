"""
🎯 MÓDULO DE EVENTOS DO BOT DISCORD

📌 Responsabilidades:
    - Detectar eventos do Discord (voz, membros entrando)
    - Delegar ações para o Controller (Presentation Layer)
    - Logging de atividades importantes

💡 Arquitetura: Segue Clean Architecture
    Discord Events → Presentation Layer → Use Cases → Domain → Infrastructure
"""

import logging
import discord
from discord.ext import commands

from infrastructure.repositories import DiscordChannelRepository
from presentation.controllers.channel_controller import ChannelController


# 📝 Logger para rastreamento de eventos
logger = logging.getLogger(__name__)


class Eventos(commands.Cog):
    """
    🎧 Gerenciador de Eventos do Discord
    
    💡 Boa Prática: Usa Cog para organizar eventos relacionados
    🏗️ Arquitetura: Camada de entrada que delega para Controllers
    """

    def __init__(self, bot: commands.Bot) -> None:
        """
        Inicializa o módulo de eventos.

        Args:
            bot: Instância do bot Discord.py

        💡 Boa Prática: Injeção de dependências no construtor
        """
        self.bot = bot
        
        # 🏗️ Injeção de dependência correta - Clean Architecture!
        channel_repository = DiscordChannelRepository(bot)
        self.channel_controller = ChannelController(channel_repository)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        """
        🔄 PONTO DE ENTRADA: Detecta mudanças de estado de voz

        💡 Fluxo: Discord Event → Presentation Layer → Use Cases → Domain

        Args:
            member: Membro que teve mudança no estado de voz
            before: Estado de voz anterior
            after: Novo estado de voz

        🎯 Casos de uso:
            - Criar sala temporária ao entrar em canal criador
            - Deletar sala temporária quando ficar vazia
            - Transferir ownership se dono sair
        """
        logger.info("🎧 Voice state update: %s", member.name)

        # 🎯 STEP 1: Delega para o Controller (Presentation Layer)
        await self.channel_controller.handle_voice_state_update(
            member=member,
            before=before,
            after=after,
        )

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """
        👋 Cria fórum privado automático quando membro entra no servidor

        💡 Boa Prática: Cada membro recebe seu espaço privado personalizado
        🏠 Fluxo: Discord Event → Controller → Repository → Discord API

        Funcionalidades do fórum criado:
        - 🔒 Completamente privado (só o membro vê)
        - ✏️ Membro pode editar nome e configurações do canal
        - 🗑️ Membro pode gerenciar todas as mensagens
        - 📝 Membro pode criar threads (posts) no fórum
        - 🎨 Threads herdam as mesmas permissões privadas

        Args:
            member: Membro que acabou de entrar no servidor

        💡 Design Pattern: Event-Driven Architecture
        """
        logger.info("👋 %s entrou no servidor %s", member.name, member.guild.name)

        # 🤖 Ignora bots - eles não precisam de fóruns privados
        if member.bot:
            logger.debug("🤖 Membro é bot, ignorando criação de fórum")
            return

        # 🎯 Delega para Controller criar fórum privado
        success = await self.channel_controller.handle_create_member_text_channel(
            member=member,
            category_id=None,  # Pode ser configurado para categoria específica
        )

        # 💬 Log do resultado com pattern matching (Python 3.13)
        match success:
            case True:
                logger.info(
                    "✅ Fórum privado criado | member=%s | guild=%s",
                    member.display_name,
                    member.guild.name
                )
            case False:
                logger.error(
                    "❌ Falha ao criar fórum | member=%s | guild=%s",
                    member.display_name,
                    member.guild.name
                )


async def setup(bot: commands.Bot) -> None:
    """
    🔧 Função de setup para carregar o Cog

    💡 Boa Prática: Padrão obrigatório do Discord.py para extensões
    """
    await bot.add_cog(Eventos(bot))
