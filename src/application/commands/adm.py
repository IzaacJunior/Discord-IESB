import logging

import discord
from discord.ext import commands

from infrastructure.repositories import DiscordChannelRepository
from presentation.controllers.channel_controller import ChannelController

logger = logging.getLogger(__name__)


class ADM(commands.Cog):
    """
    🔧 Comandos administrativos do bot
    
    💡 Boa Prática: Injeta dependências para manter
    baixo acoplamento e facilitar testes!
    """
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        
        # 🏗️ Injeção de dependência - Clean Architecture!
        channel_repository = DiscordChannelRepository(bot)
        self.channel_controller = ChannelController(channel_repository)

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
        name="+voice", help="Marca categoria atual como geradora de salas temporárias"
    )
    @commands.has_permissions(administrator=True)
    async def add_category(self, ctx: commands.Context) -> None:
        """
        🎙️ Marca uma categoria como geradora de salas temporárias
        
        💡 Funcionamento:
        1. Admin usa comando em canal de voz
        2. Categoria do canal é marcada como "temp room generator"
        3. Sistema salva no banco de dados
        4. Quando alguém entrar em canais dessa categoria, cria sala temporária
        """
        # 🔍 Verificações de segurança
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            await ctx.send("❌ Você precisa estar em um canal de voz!", delete_after=5)
            return
            
        if ctx.author.voice.channel.category is None:
            await ctx.send("❌ O canal de voz precisa estar em uma categoria!", delete_after=5)
            return

        category = ctx.author.voice.channel.category
        
        try:
            # 🚀 Delega para o controller marcar categoria como temp room generator
            success = await self.channel_controller.handle_mark_category_as_temp_generator(
                category=category,
                guild_id=ctx.guild.id
            )
            
            if success:
                await ctx.send(
                    f"✅ Categoria **{category.name}** marcada como geradora de salas temporárias!\n"
                    f"💡 Agora, quando alguém entrar em qualquer canal desta categoria, "
                    f"uma sala temporária será criada automaticamente! 🎉",
                    delete_after=10
                )
                logger.info("✅ Categoria %s marcada como temp generator", category.name)
            else:
                await ctx.send(
                    f"⚠️ A categoria **{category.name}** já está configurada como geradora!",
                    delete_after=5
                )
                logger.warning("⚠️ Categoria %s já está configurada", category.name)
                
        except Exception as e:
            logger.error("❌ Erro ao configurar categoria: %s", str(e))
            await ctx.send(
                f"❌ Erro ao configurar categoria: {str(e)}",
                delete_after=5
            )

    @commands.command(
        name="-voice", help="Remove configuração de categoria de salas temporárias"
    )
    @commands.has_permissions(administrator=True)
    async def remove_category(self, ctx: commands.Context) -> None:
        """
        🗑️ Remove marcação de categoria como geradora de salas temporárias
        
        💡 Funcionamento:
        1. Admin usa comando em canal de voz
        2. Categoria do canal deixa de gerar salas temporárias
        3. Sistema remove configuração do banco
        """
        # 🔍 Verificações de segurança
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            await ctx.send("❌ Você precisa estar em um canal de voz!", delete_after=5)
            return
            
        if ctx.author.voice.channel.category is None:
            await ctx.send("❌ O canal de voz precisa estar em uma categoria!", delete_after=5)
            return

        category = ctx.author.voice.channel.category
        
        try:
            # 🗑️ Delega para o controller remover categoria
            success = await self.channel_controller.handle_unmark_category_as_temp_generator(
                category_id=category.id,
                guild_id=ctx.guild.id
            )
            
            if success:
                await ctx.send(
                    f"✅ Categoria **{category.name}** não gera mais salas temporárias!",
                    delete_after=5
                )
                logger.info("✅ Categoria %s desmarcada", category.name)
            else:
                await ctx.send(
                    f"⚠️ A categoria **{category.name}** não estava configurada!",
                    delete_after=5
                )
                logger.warning("⚠️ Categoria %s não estava configurada", category.name)
                
        except Exception as e:
            logger.error("❌ Erro ao remover categoria: %s", str(e))
            await ctx.send(
                f"❌ Erro ao remover categoria: {str(e)}",
                delete_after=5
            )


async def setup(bot):
    await bot.add_cog(ADM(bot))
