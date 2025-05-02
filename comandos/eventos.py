import discord
from discord.ext import commands
from discord import Permissions, PermissionOverwrite

from comun.voice import VoiceManager
from comun.text import TextManager


class Eventos(commands.Cog):    

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.voice_channel_manager = VoiceManager("channels")
        self.text_channel_manager = TextManager("channels")

    @commands.Cog.listener()
    async def on_voice_state_update(
        self, member: discord.Member, 
        before: discord.VoiceState, 
        after: discord.VoiceState
    ):
        if member.bot:
            return

        # Verifica se o membro entrou ou saiu de um canal de voz
        if after.channel is not None:
            print(f"antes de criar {after.channel.name}")
            await self.voice_channel_manager.create_voice_temporarias(
                after.channel
            )
            print(f"{member.name} entrou no canal {after.channel.name}")

        if before.channel is not None:
            await self.voice_channel_manager.remove_voice_temporarias(
                before.channel
            )
            print(f"{member.name} saiu do canal {before.channel.name}")

    # Evento é acionado quando um membro entra na guilda
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return
        guild = member.guild

        print("1 Etapa")
        category = await self.text_channel_manager.category_text_channel(
            guild=guild
        )
        if category is None:
            ...


        
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
            )
        }

            
        print("3 Etapa")
        new_channel: discord.TextChannel = await category.create_text_channel(
            name=f"chat-{member.nick or member.name}".lower(),
            overwrites=channel_overwrites           
        )
        return new_channel
        


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Eventos(bot))