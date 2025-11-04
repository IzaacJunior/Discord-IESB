import discord
from discord import app_commands
from discord.ext import commands


class SlachNormy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="mudar_nome",
        description="Muda seu nome nesse servidor. Não coloque apelidos!",
    )
    async def mudar_nome(self, interaction: discord.Interaction, nome: str):
        """Comando para mudar o apelido do usuário no servidor."""
        await interaction.response.defer(
            ephemeral=True
        )  # Defer para evitar "O bot não respondeu"
        try:
            await interaction.user.edit(nick=nome)
            await interaction.followup.send(
                f"Seu nome foi alterado para: {nome}", ephemeral=True
            )
        except discord.Forbidden:
            await interaction.followup.send(
                "Não consegui alterar seu nome. Verifique minhas permissões.",
                ephemeral=True,
            )

    @app_commands.command(
        name="clear",
        description="Deleta até 20 mensagens suas das últimas 50 enviadas.",
    )
    async def clear(self, interaction: discord.Interaction, limit: int = 1):
        """Comando para deletar mensagens do usuário."""
        await interaction.response.defer(
            ephemeral=True
        )  # Defer para evitar "O bot não respondeu"
        mensagens_channel = interaction.channel.history(limit=50)
        mensagens_author = [
            msg async for msg in mensagens_channel if msg.author == interaction.user
        ]
        mensagens_a_deletar = mensagens_author[:limit]
        for mensagem in mensagens_a_deletar:
            await mensagem.delete()
        await interaction.followup.send(
            f"{interaction.user.name} deletou {len(mensagens_a_deletar)} mensagem(ns).",
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    """Adiciona o cog."""
    await bot.add_cog(SlachNormy(bot))
