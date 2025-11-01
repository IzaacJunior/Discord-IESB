import logging

import discord
from discord.ext import commands

from infrastructure.repositories import DiscordChannelRepository
from presentation.controllers.channel_controller import ChannelController

logger = logging.getLogger(__name__)


class Eventos(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
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
        
        💡 Fluxo: Discord Event → Presentation Layer
        """
        logger.info("🎧 Voice state update: %s", member.name)
        
        # 🎯 STEP 1: Delega para o Controller (Presentation Layer)
        await self.channel_controller.handle_voice_state_update(
            member=member,
            before=before,
            after=after,
        )

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """
        👋 EXEMPLO: Cria canal de texto automático quando membro entra
        
        💡 Fluxo: Discord Event → Controller → Use Case → Repository → Discord API
        """
        logger.info("� %s entrou no servidor %s", member.name, member.guild.name)
        
        if member.bot:
            return None
            
        # 🎯 STEP 1: Delega para Controller (Presentation Layer)
        success = await self.channel_controller.handle_create_member_text_channel(
            member=member,
            category_id=None  # Pode ser obtido de configuração
        )
        
        if success:
            logger.info("✅ Canal criado automaticamente para %s", member.name)
        else:
            logger.warning("❌ Falha ao criar canal para %s", member.name)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Eventos(bot))
