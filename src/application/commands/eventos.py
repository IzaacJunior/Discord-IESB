import logging

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class Eventos(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        if member.bot:
            return

        # Verifica se o membro entrou ou saiu de um canal de voz
        if after.channel is not None:
            await self.voice_channel_manager.create_voice_temporarias(after.channel)
            logger.debug("🔊 %s entrou no canal %s", member.name, after.channel.name)

        if before.channel is not None:
            await self.voice_channel_manager.remove_voice_temporarias(before.channel)
            logger.debug("🔇 %s saiu do canal %s", member.name, before.channel.name)

    # Evento é acionado quando um membro entra na guilda
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        logger.info("👋 %s entrou no servidor %s", member.name, member.guild.name)
        if member.bot:
            return None
        logger.debug("📋 Checkpoint 1: Membro validado")
        guild = member.guild
        logger.debug("📋 Checkpoint 2: Guild obtida")
        category: discord.CategoryChannel = (
            await self.text_channel_manager.category_text_channel(guild=guild)
        )

        logger.info("💬 Criando canal de texto para %s", member.name)

        channel_overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                read_message_history=True,
                manage_messages=True,
                manage_webhooks=True,
                attach_files=True,
                embed_links=True,
                add_reactions=True,
                use_application_commands=True,
                use_external_emojis=True,
            ),
        }

        new_channel: discord.TextChannel = await category.create_text_channel(
            name=f"chat-{member.nick or member.name}".lower(),
            overwrites=channel_overwrites,
        )
        return new_channel


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Eventos(bot))
