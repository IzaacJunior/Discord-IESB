import discord


class Temporario:
    def __init__(self, ctx):
        self.ctx = ctx

    async def create_text_channel(self, channel_name: str, overwrites=None, category=None) -> discord.TextChannel:
        """Cria ou edita um canal de texto temporário."""
        sanitized_name = channel_name.replace("#", "").lower()
        channel = discord.utils.get(self.ctx.guild.text_channels, name=sanitized_name)
        if channel:
            await channel.edit(
                overwrites=overwrites,
                category=category
            )
            return channel
        # Cria um novo canal se não existir
        channel = await self.ctx.guild.create_text_channel(
            sanitized_name,
            overwrites=overwrites,
            category=category
        )
        return channel

    async def create_voice_channel(self, channel_name: str, category=None, overwrites=None) -> discord.VoiceChannel:
        """Cria ou edita um canal de voz temporário."""
        voice_channel = discord.utils.get(self.ctx.guild.voice_channels, name=channel_name)
        if voice_channel:
            await voice_channel.edit(
                overwrites=overwrites,
                category=category
            )
            return voice_channel
        
        voice_channel = await self.ctx.guild.create_voice_channel(
            channel_name,
            overwrites=overwrites,
            category=category
        )
        return voice_channel

    async def create_category(self, category_name: str, overwrites=None) -> discord.CategoryChannel:
        """Cria uma categoria temporária."""
        category = discord.utils.get(self.ctx.guild.categories, name=category_name)
        if category:
            await category.edit(
                overwrites=overwrites
            )
            return category  # Retorna a categoria existente
        return await self.ctx.guild.create_category(
            name=category_name,
            overwrites=overwrites
        )

    async def delete_channel(self, channel: discord.abc.GuildChannel) -> None:
        """Exclui um canal."""
        if channel is None:
            print("Canal não encontrado.")
            return
        try:
            await channel.delete()
        except Exception as e:
            print(f"Erro ao excluir o canal {channel.name}: {e}")

