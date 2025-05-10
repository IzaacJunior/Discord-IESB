from discord.ext import commands
import asyncio


class Normy(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    
    @commands.command(
        name="name", 
        help="Muda seu nome nesse servidor\n Não coloque apelidos!"
    )
    async def mudar_nome(self, ctx, *nome): 
        """Muda o nome do usuário no servidor."""
        print(nome)
        nome = " ".join(nome)
        print(nome)
        if ctx.author.nick:
            # Se o usuário já tem um apelido, não pode mudar o nome
            await ctx.send("Você já tem um apelido!")
            return 
        
        await ctx.author.edit(nick=nome)
        
        await ctx.send(f"Seu nome foi alterado para: {nome}")
        print(f"{ctx.author.name} mudou o nome para {nome}")
        

    @commands.command(
            name="clear", 
            help="Analizo as ultimas 50 mensagens e posso deletar até 20 mensagens suas"
        )
    async def clear(self, ctx, limit: int = 10):
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