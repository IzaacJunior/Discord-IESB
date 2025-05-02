import discord


from comun.smalldb import SmallDB

class TextManager:
    def __init__(self, path: str) -> None:
        self.path = path
        self.db = SmallDB(path).get("text_channels")
    
    async def category_text_channel(self, guild: discord.Guild) -> discord.TextChannel:
        """Cria um canal de voz."""
        # Cria o canal de texto
        category_overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False)
        }
        if self.db.exists_table(self.path):
            # Cria a categoria no banco de dados se não existir
            db = self.db.get_table(self.path)
            category_id = db.list_keys()[0]
            return category
        print("2 Etapa")
        category: discord.CategoryChannel = await guild.create_category(
            name=self.path,
            overwrites=category_overwrites
        )
        
        category = discord.utils.get(guild.categories, id=int(category_id))
        return category
    
    async def create_text_channel(
        self,
        guild: discord.Guild,
        category: discord.CategoryChannel
    ) -> discord.TextChannel:
        """Cria um canal de texto."""
        # Cria o canal de texto
        channel_overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False)
        }
        channel: discord.TextChannel = await category.create_text_channel(
            name=f"{category.name} {guild.name}",  # Nome baseado no criador e no membro
            overwrites=channel_overwrites,         # Mesmas permissões
            topic="Canal de texto temporário"
        )
        return channel
       
        