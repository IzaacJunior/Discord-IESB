import discord
from discord import app_commands
from discord.ext import commands

from application.use_cases.bot_use_cases import BotLifecycleUseCase
from presentation.controllers.bot_controller import BotController


class SlachModer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # 🤖 Bot lifecycle controller
        bot_lifecycle_use_case = BotLifecycleUseCase(bot)
        self.bot_controller = BotController(bot_lifecycle_use_case)

    @app_commands.command(
        name="sclear",
        description="Deleta as últimas mensagens, podendo ser de um usuário específico ou de todos.",
    )
    @app_commands.describe(
        limit="Número de mensagens a deletar (padrão: 10)",
        user="Usuário específico para deletar mensagens",
    )
    @app_commands.checks.has_permissions(manage_messages=True)  #
    async def sclear(
        self,
        interaction: discord.Interaction,
        limit: int = 10,
        user: discord.Member = None,
    ):
        """Comando para deletar mensagens, com opção de filtrar por usuário."""
        await interaction.response.defer(ephemeral=True)

        def check(msg):
            if user:
                return msg.author == user
            return not msg.author.bot

        deleted = await interaction.channel.purge(limit=limit, check=check)

        # Envia uma mensagem de confirmação
        if user:
            await interaction.followup.send(
                f"{len(deleted)} mensagem(ns) de {user.mention} deletada(s).",
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                f"{len(deleted)} mensagem(ns) deletada(s).", ephemeral=True
            )

    @app_commands.command(
        name="desconectar", description="Desconecta o bot e o faz ficar offline."
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def desconectar(self, interaction: discord.Interaction):
        """Comando para desconectar o bot seguindo Clean Architecture."""
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(
            "Desconectando o bot com carinho... Até logo! 💕", ephemeral=True
        )
        
        # Usa o controller seguindo Clean Architecture
        response = await self.bot_controller.shutdown(
            admin_name=interaction.user.name,
            guild_name=interaction.guild.name,
            reason="Comando /desconectar executado"
        )
        
        if not response.success:
            await interaction.followup.send(
                f"❌ {response.message}", 
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    """Adiciona o cog."""
    await bot.add_cog(SlachModer(bot))
