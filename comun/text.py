import discord


from comun.smalldb import SmallDB
# Em desenvolvimento, o banco de dados é um arquivo JSON
class TextManager:

    def __init__(self, path: str) -> None:
        self.path = "text_channels"
        self.db = SmallDB(path).get(path)
    
    async def category_text_channel(self, guild: discord.Guild) -> discord.CategoryChannel:
        """Cria um canal de voz."""
        # Cria o canal de texto
        print("c0")
        tabela = self.db.get_id(guild.id)
        tabela.create()
        catagory_ids: list = tabela.get_key(self.path)
        print("primeiro etapa")
        if catagory_ids is None:
            category_overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False)
            }
            print("segundo etapa")

            category: discord.CategoryChannel = await guild.create_category(
                name=f"Seu cantinho",
                overwrites=category_overwrites,         # Mesmas permissões
                reason="Lugar de uso pessoa e privado para o usuário exemplo usar para notas"
            )
            tabela.add_values(
                self.path, [category.id]
            )
            return category
        print("terceiro etapa")
        category = guild.get_channel(catagory_ids[0])
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
       
        