import asyncio
import logging

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class Normy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="name", help="Muda seu nome nesse servidor\n Não coloque apelidos!"
    )
    async def mudar_nome(self, ctx, *nome):
        """
        Muda o nome do usuário no servidor.

        💡 Boa Prática: Validação robusta + tratamento de erros!
        """
        # ✅ Validação de entrada
        if not nome:
            await ctx.send("❌ Por favor, forneça um nome! Exemplo: `!name João Silva`")
            return

        # 🔧 Converte tupla para string
        nome_completo = " ".join(nome)
        logger.info("📝 Alteração solicitada: %s -> '%s'", nome, nome_completo)

        # ✅ Validação de tamanho
        if len(nome_completo) > 32:
            await ctx.send("❌ Nome muito longo! Máximo 32 caracteres.")
            return

        if len(nome_completo) < 2:
            await ctx.send("❌ Nome muito curto! Mínimo 2 caracteres.")
            return

        # ✅ Verifica se usuário já tem apelido
        if ctx.author.nick:
            await ctx.send(f"❌ Você já tem um apelido: **{ctx.author.nick}**")
            return

        # 🎯 Execução com tratamento de erros
        try:
            await ctx.author.edit(nick=nome_completo)
            await ctx.send(
                f"✅ Seu nome foi alterado para: **{nome_completo}**", delete_after=5
            )
            logger.info("✅ %s mudou o nome para '%s'", ctx.author.name, nome_completo)

        except discord.Forbidden:
            await ctx.send(
                "❌ Não tenho permissão para alterar seu nome!", delete_after=5
            )

        except discord.HTTPException as e:
            await ctx.send(f"❌ Erro ao alterar nome: {e}", delete_after=5)

        except discord.NotFound:
            await ctx.send("❌ Usuário não encontrado!", delete_after=5)

        except Exception:
            await ctx.send("❌ Erro inesperado ao alterar nome!", delete_after=5)
            logger.exception("❌ Erro no comando name")

    @commands.command(
        name="clear",
        help="Analizo as ultimas 50 mensagens e posso deletar até 20 mensagens suas",
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
            delete_after=5,
        )


async def setup(bot):
    await bot.add_cog(Normy(bot))
