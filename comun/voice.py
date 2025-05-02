import discord


from comun.smalldb import SmallDB

class VoiceManager:
    def __init__(self, path) -> None:
        self.path = "voice_channels"
        self.table = SmallDB(path).get(self.path)
        

    async def add_category(self, channel: discord.VoiceChannel) -> bool  :
        db_category = self.table.get_id(channel.category.id)
        if not self.table.exists(channel.category.id):
            # Cria a categoria no banco de dados se não existir
            db_category.create()
            return True
        return False
        

    async def create_voice_temporarias(
        self,
        channel: discord.VoiceChannel
    ) -> discord.VoiceChannel|None:
        """Adiciona um canal temporário."""
        # Verifica se o canal original já existe
        # -------- Verifições -----------
        if not self.table.exists(channel.category.id):

            return 
        db_category = self.table.get_id(channel.category.id)
        if channel.id in self.table.get_id(channel.category.id).get_key(self.path):
            return None
        new_channel: discord.VoiceChannel = await channel.category.create_voice_channel(
            name=f"{channel.category.name} {channel.name}",  
            bitrate=channel.bitrate,                 # Mesmo bitrate
            user_limit=channel.user_limit,           # Mesmo limite de usuários
            overwrites=channel.overwrites            # Mesmas permissões
        )
        # Adiciona o novo canal à categoria no banco de dados
        db_category.add_values(
            self.path, [new_channel.id]
        )
        
        # mover todos os membros para o novo canal
        for member in channel.members:
            await member.move_to(new_channel)
        return new_channel
 

    async def del_category(self, category: discord.CategoryChannel) -> bool:
        """Remove a categoria."""
        # deletar os canais temporarios dentro da categoria
        for channel in category.voice_channels:
            if channel.id in self.table.get_id(category.id).get_key(self.path):
                await channel.delete()
        # Remove a categoria do dicionário
        return self.table.delete_category(category.id)


    async def remove_voice_temporarias(
        self,
        channel: discord.VoiceChannel
    ) -> None:
        """Remove a sala temporária se o membro sair dela."""
        if not self.table.exists(channel.category.id):
            return
        if channel.id not in self.table.get_id(channel.category.id).get_key(self.path):
            return

        # deleta o canal temporário se não houver membros
        if len(channel.members) != 0:
            return
        
        await channel.delete()
        # Remove a categoria do dicionário
        self.table.get_id(channel.category.id).remove_values(self.path, [channel.id])
        
        print(f"Sala temporária deletada: {channel.name}")


        
