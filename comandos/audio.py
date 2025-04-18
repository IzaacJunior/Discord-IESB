import discord
from comun.loggis import Loggin as logs
from discord.ext import commands
from comun.getset import GetSet as gt


class Auto(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # Dicionário para rastrear IDs:
        # chave é a categoria criadora, valor é uma lista de IDs de salas temporárias
        self.ruta_temp = gt("temp_channel_config")
        self.category_to_temp_channel_ids: dict[int, list[int]] = self.ruta_temp.get()
        logs.log("Carregado IDs de canais temporários...")

    
    async def add_voice_temporarias(
        self,
        member: discord.Member,
        creator_channel: discord.VoiceChannel
    ) -> None:
        """Cria uma sala temporária clonando as configurações da sala criadora."""
        if creator_channel.category.id not in self.category_to_temp_channel_ids.keys():
            logs.log(f"Categoria {creator_channel.category.name} não está configurada para criar salas temporárias.")
            return
        if creator_channel.id in self.category_to_temp_channel_ids[creator_channel.category.id]:
            return

        # Cria o canal temporário
        temp_channel: discord.VoiceChannel = await creator_channel.category.create_voice_channel(
            name=f"{creator_channel.name} - {member.nick}",  # Nome baseado no criador e no membro
            bitrate=creator_channel.bitrate,  # Mesmo bitrate
            user_limit=creator_channel.user_limit,  # Mesmo limite de usuários
            overwrites=creator_channel.overwrites  # Mesmas permissões
        )

        # Adiciona o ID do canal temporário ao dicionário
        self.category_to_temp_channel_ids[creator_channel.category.id].append(temp_channel.id)
        self.ruta_temp.set(self.category_to_temp_channel_ids)

        # Move o membro para o canal temporário
        await member.move_to(temp_channel)
        logs.log(f"Sala temporária criada: {temp_channel.name} para {member.name}")

    async def remove_voice_temporarias(
        self,
        temp_channel: discord.VoiceChannel
    ) -> None:
        """Remove a sala temporária se o membro sair dela."""
        if temp_channel.category.id not in self.category_to_temp_channel_ids:
            return 
        if temp_channel.id not in self.category_to_temp_channel_ids[temp_channel.category.id]:
            return
        
        if len(temp_channel.members) == 0:
            await temp_channel.delete()
            logs.log(f"Sala temporária deletada: {temp_channel.name}")
            self.category_to_temp_channel_ids[temp_channel.category.id].remove(temp_channel.id)
            self.ruta_temp.set(self.category_to_temp_channel_ids)

    async def gerenciador_voice_temporarias(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
    ) -> None:
        """Gerencia a criação e exclusão de salas temporárias."""
        
        if after.channel and after.channel.category.id in self.category_to_temp_channel_ids.keys():
            # Se o membro já estiver em uma sala temporária, não cria outra
            logs.log(f"{member.name} entrou na sala de áudio: {after.channel.name}")
            await self.add_voice_temporarias(member, after.channel)

        if before.channel and before.channel.category.id in self.category_to_temp_channel_ids.keys():
            logs.log(f"{member.name} saiu da sala de áudio: {before.channel.name}")
            await self.remove_voice_temporarias(before.channel)

    @commands.command(name="+voice", help="Adiciona uma categoria que cria salas temporárias")
    @commands.has_permissions(administrator=True)
    async def add_temporary_category(self, ctx: commands.Context) -> None:
        """Adiciona uma categoria que cria salas temporárias."""
        if ctx.author.voice is None:
            await ctx.send("Você precisa estar em uma sala de áudio para usar este comando.")
            return

        # Obtém a categoria da sala de áudio
        category: discord.CategoryChannel = ctx.author.voice.channel.category
        if category is None:
            await ctx.send("Você precisa estar em uma sala de áudio dentro de uma categoria.")
            return

        # Verifica se a categoria já está configurada
        
        if category.id in self.category_to_temp_channel_ids.keys():
            await ctx.send(
                f"A categoria {category.name} já está configurada para criar salas temporárias."
            )
            return

        # Adiciona a categoria ao dicionário com uma lista vazia de canais temporários
        self.category_to_temp_channel_ids[category.id] = []
        self.ruta_temp.set(self.category_to_temp_channel_ids)
        await ctx.send(f"Categoria {category.name} adicionada como categoria criadora de salas temporárias.")
        # Move o usuário para a nova sala temporária
        await self.add_voice_temporarias(ctx.author,ctx.author.voice.channel)


    @commands.command(name="-voice", help="Remove uma categoria que cria salas temporárias")
    @commands.has_permissions(administrator=True)
    async def remove_temporary_category(self, ctx: commands.Context) -> None:
        """Remove uma categoria que cria salas temporárias."""
        if ctx.author.voice is None:
            await ctx.send("Você precisa estar em uma sala de áudio para usar este comando.")
            return

        # Obtém a categoria da sala de áudio
        
        category: discord.CategoryChannel = ctx.author.voice.channel.category
        if category is None:
            await ctx.send("Você precisa estar em uma sala de áudio dentro de uma categoria.")
            return

        # Verifica se a categoria está configurada
        if category.id not in self.category_to_temp_channel_ids.keys():
            await ctx.send(f"A categoria {category.name} não está configurada para criar salas temporárias.")
            return

        # Remove a categoria do dicionário
        del self.category_to_temp_channel_ids[category.id]
        self.ruta_temp.set(self.category_to_temp_channel_ids)
        await ctx.send(f"A categoria {category.name} foi removida das categorias criadoras de salas temporárias.")


    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
    ) -> None:
        """Gerencia eventos de mudança de estado de voz."""
        await self.gerenciador_voice_temporarias(member, before, after)

        if before.self_mute != after.self_mute:
            estado = "mutou" if after.self_mute else "desmutou"
            logs.log(f"{member.name} {estado} o microfone.")

        if before.self_deaf != after.self_deaf:
            estado = "ensurdeceu" if after.self_deaf else "desensurdeceu"
            logs.log(f"{member.name} {estado} o fone de ouvido.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Auto(bot))