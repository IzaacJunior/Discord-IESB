from discord.ext import commands
import asyncio


class Normy(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    
    @commands.command(name="name", help="Muda seu nome nesse servidor\n Não coloque apelidos!")
    async def mudar_nome(self, ctx, Nome: str):        
        await ctx.author.edit(nick=Nome)
        await ctx.send(f"Seu nome foi alterado para: {Nome}")
        print(f"{ctx.author.name} mudou o nome para {Nome}")
        

    @commands.command(
            name="clear", 
            help="Analizo as ultimas 50 mensagens e posso deletar até 20 mensagens suas"
        )
    async def clear(self, ctx, limit: int = 1):
        await asyncio.sleep(1)
        mensagens_channel = ctx.channel.history(limit=50)

        # Filtra as mensagens do autor que executou o comando
        mensagens_author = [
            msg async for msg in mensagens_channel if msg.author == ctx.author
        ]

        mensagens_a_deletar = mensagens_author[:limit]

        for mensagem in mensagens_a_deletar:
            await mensagem.delete()
        await ctx.send(
            f"{ctx.author.name} deletou {len(mensagens_a_deletar)} mensagem(ns).", 
            delete_after=5
        )


async def setup(bot):  
    await bot.add_cog(Normy(bot))