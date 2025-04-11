from discord.ext import commands
import discord


class Moder(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    
    @commands.command(
        name="sclear", 
        help="Deleta as últimas mensagens, podendo ser de um usuário específico ou de todos"
    )
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, limit: int = 10, user: discord.Member = None):
        # Define a função de filtro para o método purge
        def check(msg):
            if user:
                return msg.author == user  # Filtra mensagens do usuário especificado
            return not msg.author.bot  # Filtra mensagens de todos os usuários, exceto bots

        # Usa o método purge para deletar mensagens com base no filtro
        deleted = await ctx.channel.purge(limit=limit, check=check)

        # Envia uma mensagem de confirmação e a deleta após 5 segundos
        if user:
            await ctx.send(f"{len(deleted)} mensagem(ns) de {user.mention} deletada(s).", delete_after=5)
        else:
            await ctx.send(f"{len(deleted)} mensagem(ns) deletada(s).", delete_after=5)
    
    @commands.command(name="des", help="Desconecta o bot e o faz ficar offline")
    @commands.has_permissions(administrator=True)
    async def desconectar(self, ctx):
        await ctx.send("Desconectando o bot... Até logo!")
        await self.bot.close()
        print("Bot Desconectado! ")
    
    


async def setup(bot):  
    await bot.add_cog(Moder(bot))