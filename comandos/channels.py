import discord
from discord.ext import commands

from comun.getset import GetSet as gt
from comun.loggis import Loggin as logs
from comun.temporarios import Temporario as temp


class Unicas(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.ruta_temp = gt("temp_channel_config")
        self.member_channels = self.ruta_temp.get()


    async def salas_unicas(self, member) -> None:
        """Cria uma sala única automaticamente quando um membro entra na guilda."""
        logs.log(f"Novo membro: {member.name} entrou na guilda.")
        temps = temp(member)
        # Verifica se a categoria "Salas Únicas" já existe
        category_name: str = "▬▬SALAS ÚNICAS▬▬"
        if temps.verify_category(category_name):
            category = await temps.create_category(category_name)

        permissionOverwrite = discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    manage_channels=True,
                    read_message_history=True
                )
        # Verifica se o membro já possui um canal exclusivo
        if member.id in self.member_channels:
            channel_id = self.member_channels[member.id]
            existing_channel = discord.utils.get(member.guild.text_channels, id=channel_id)
            if existing_channel:
                # Restaura as permissões do membro no canal existente
                overwrites = existing_channel.overwrites
                overwrites[member] = permissionOverwrite
                await existing_channel.edit(overwrites=overwrites)
                await existing_channel.send(
                    f"Bem-vindo(a) de volta, {member.mention}! Sua sala exclusiva foi restaurada."
                )
                logs.log(f"Canal recuperado: {existing_channel.name}")
                return
        
        # Cria um canal de texto exclusivo com permissões completas para o membro
        overwrites = {
            member.guild.default_role: discord.PermissionOverwrite(
                read_messages=False
            ),  # Bloqueia todos
            member: permissionOverwrite
        }
        channel = await temps.create_text_channels(
            f"🔒{member.name}🔒",
            permissionOverwrite,
            category
        )
        # Cria o canal apenas se ele ainda não existir, dentro da categoria
        self.member_channels[member.id] = channel.id  # Armazena o ID do canal para o membro
        self.ruta_temp.set(self.member_channels)  # Salva os dados no arquivo JSON
        await channel.send(
            f"Bem-vindo(a),\
            {member.mention}! Esta é sua sala exclusiva. Você tem controle total sobre ela."
        )
        logs.log(f"Canal exclusivo criado: {channel.name}")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await self.salas_unicas(member)



async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Unicas(bot))