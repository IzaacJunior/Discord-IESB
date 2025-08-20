import logging

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class ADM(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="des", help="Desconecta o bot e o faz ficar offline")
    @commands.has_permissions(administrator=True)
    async def desconectar(self, ctx):
        await ctx.send("Desconectando o bot... Até logo!")
        await self.bot.close()
        logger.info("🤖 Bot desconectado por comando do administrador")

    @commands.command(
        name="cls", help="Limpa o canal de texto atual, de todo ou @ de um usuário"
    )
    @commands.has_permissions(manage_messages=True)
    async def clear_text_channel(
        self, ctx: commands.Context, limit: int = 100, user: discord.Member = None
    ) -> None:
        # Define a função de filtro para o método purge
        def check(msg):
            if user:
                # Filtra mensagens do usuário especificado
                return msg.author == user
            # Filtra mensagens de todos os usuários, exceto bots
            return not msg.author.bot

        # Usa o método purge para deletar mensagens com base no filtro
        deleted = await ctx.channel.purge(limit=limit, check=check)

        # Envia uma mensagem de confirmação e a deleta após 5 segundos
        if user:
            await ctx.send(
                f"{len(deleted)} mensagem(ns) de {user.mention} deletada(s).",
                delete_after=5,
            )
        else:
            await ctx.send(f"{len(deleted)} mensagem(ns) deletada(s).", delete_after=5)

    @commands.command(
        name="+voice", help="Adiciona uma sala temporária de voz ao servidor"
    )
    @commands.has_permissions(administrator=True)
    async def add_category(self, ctx: commands.Context) -> None:
        """Adiciona uma categoria ao servidor."""
        # --------- Verifições -----------
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            await ctx.send("Você não está em um canal de voz.")
            return
        if ctx.author.voice.channel.category is None:
            await ctx.send("O canal de voz não está em uma categoria.")
            return

        channels = ctx.author.voice.channel.category.voice_channels
        if not await self.voice_channel_manager.add_category(ctx.author.voice.channel):
            await ctx.send("A categoria já existe.")
            return

        # Move todos os membros para o novo canal
        for channel in channels:
            if len(channel.members) != 0:
                new_channel = await self.voice_channel_manager.create_voice_temporarias(
                    channel
                )
        # Lógica para criar botões para canais de voz temporários
        # config button:
        # nome do canal
        # limite de usuários do canal
        # peremissões do canal
        # Por roll

    @commands.command(
        name="-voice", help="Remove uma sala temporária de voz do servidor"
    )
    @commands.has_permissions(administrator=True)
    async def remove_category(self, ctx: commands.Context) -> None:
        """Remove uma categoria do servidor."""
        if ctx.author.voice.channel is None:
            await ctx.send("Você não está em um canal de voz.")
            return
        if ctx.author.voice.channel.category is None:
            await ctx.send("Você não está em uma categoria.")
            return
        if await self.voice_channel_manager.del_category(
            ctx.author.voice.channel.category
        ):
            logger.info("✅ Categoria deletada com sucesso")
            return
        logger.warning("⚠️ Categoria não existe ou não pôde ser deletada")


async def setup(bot):
    await bot.add_cog(ADM(bot))
