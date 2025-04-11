import discord
import comun.getset as gt
from discord.ext import commands


class Unicas(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.ruta_temp = gt.GetSet("temp_channel_config")          # Caminho do arquivo JSON
        self.member_channels = self.ruta_temp.get()      # Carrega os dados ao iniciar o bot


    async def salas_unicas(self, member) -> None:
        """Cria uma sala única automaticamente quando um membro entra na guilda."""
        print(f"Novo membro: {member.name} entrou na guilda.")
        guild = member.guild

        # Verifica se a categoria "Salas Únicas" já existe
        category_name = "▬▬SALAS ÚNICAS▬▬"
        category = discord.utils.get(guild.categories, name=category_name)

        if not category:
            # Cria a categoria se ela não existir
            category = await guild.create_category(category_name)

        # Sanitiza o nome do canal para evitar caracteres inválidos
        sanitized_name = f"sala-{member.name}".replace(" ", "-").replace("#", "").lower()

        # Verifica se o membro já possui um canal exclusivo
        if str(member.id) in self.member_channels:
            channel_id = self.member_channels[str(member.id)]
            existing_channel = discord.utils.get(guild.text_channels, id=channel_id)
            if existing_channel:
                # Restaura as permissões do membro no canal existente
                overwrites = existing_channel.overwrites
                overwrites[member] = discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    manage_channels=True,
                    read_message_history=True,  # Permissão para ver o histórico
                )
                await existing_channel.edit(overwrites=overwrites)
                await existing_channel.send(
                    f"Bem-vindo(a) de volta, {member.mention}! Sua sala exclusiva foi restaurada."
                )
                return

        # Cria um canal de texto exclusivo com permissões completas para o membro
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),  # Bloqueia todos
            member: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                manage_channels=True,  # Permite ao membro gerenciar o canal
                read_message_history=True,  # Permissão para ver o histórico
            ),
        }

        # Cria o canal apenas se ele ainda não existir, dentro da categoria
        channel = await guild.create_text_channel(sanitized_name, overwrites=overwrites, category=category)
        self.member_channels[str(member.id)] = channel.id  # Armazena o ID do canal para o membro
        self.ruta_temp.set(self.member_channels)  # Salva os dados no arquivo JSON
        await channel.send(
            f"Bem-vindo(a),\
            {member.mention}! Esta é sua sala exclusiva. Você tem controle total sobre ela."
        )

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await self.salas_unicas(member)



    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Remove as permissões do membro ao sair da guilda."""
        if str(member.id) in self.member_channels:
            channel_id = self.member_channels[str(member.id)]
            guild = member.guild
            channel = discord.utils.get(guild.text_channels, id=channel_id)
            if channel:
                overwrites = channel.overwrites
                if member in overwrites:
                    del overwrites[member]
                    await channel.edit(overwrites=overwrites)
                await channel.send(f"{member.name} saiu da guilda. Permissões removidas.")
            self.ruta_temp.set(self.member_channels)  # Atualiza o arquivo JSON


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Unicas(bot))