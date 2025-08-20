import logging

import discord
from discord import Forbidden, app_commands
from discord.ext import commands
from discord.ext.commands import errors

logger = logging.getLogger(__name__)


class Manager(commands.Cog):
    """
    🛠️ Manager modernizado do bot
    💡 Centraliza todos os eventos e tratamento de erros!
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """
        ✅ Evento chamado quando o bot está pronto
        💡 Informações úteis sobre o bot conectado + sincronização!
        """
        logger.info(
            "🤖 Bot conectado como: %s (ID: %s)", self.bot.user.name, self.bot.user.id
        )
        logger.info("🌐 Conectado a %d servidores", len(self.bot.guilds))

        # 🎮 Atualiza status do bot
        activity = discord.Activity(
            type=discord.ActivityType.watching, name="🤖 IESB Discord Bot | !help"
        )
        await self.bot.change_presence(activity=activity)

        # Sincroniza os comandos de barra com o Discord
        try:
            await self.bot.tree.sync()
            logger.info("✅ Comandos de barra sincronizados com sucesso!")
        except Exception:
            logger.exception("❌ Erro ao sincronizar comandos de barra")

        logger.info("✨ Bot pronto para uso!")

    # Ve todas as mensagens
    @commands.Cog.listener()
    async def on_message(self, message):
        """
        📝 Processa mensagens e deleta comandos de texto
        💡 Mantém o chat limpo removendo comandos!
        """
        if message.author == self.bot.user:
            return

        if message.content.startswith(self.bot.command_prefix):
            await message.delete()

    # Tratamento de Erros provindos de comandos de texto
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """
        ❌ Tratamento global de erros de comandos
        💡 Mensagens amigáveis para usuários + logs técnicos!
        """
        full_command = (
            f"{self.bot.command_prefix}{ctx.command.name}"
            if ctx.command
            else "Comando desconhecido"
        )

        # 🤫 Ignora comandos não encontrados (menos spam)
        if isinstance(error, errors.CommandNotFound):
            return

        if isinstance(error, errors.MissingPermissions):
            logger.warning("Permissão ausente para o comando: %s", full_command)
            await ctx.send(
                f"❌ {ctx.author.mention}, você não tem permissão para usar este comando!",
                delete_after=5,
            )

        elif isinstance(error, errors.CommandOnCooldown):
            logger.info("Comando em cooldown: %s", full_command)
            await ctx.send(
                f"⏰ {ctx.author.mention}, aguarde {error.retry_after:.1f}s antes de usar novamente!",
                delete_after=5,
            )

        elif isinstance(error, errors.MissingRequiredArgument):
            logger.info("Argumento obrigatório ausente no comando: %s", full_command)
            await ctx.send(
                f"❌ {ctx.author.mention}, argumento obrigatório em falta: `{error.param.name}`",
                delete_after=5,
            )

        elif isinstance(error, errors.CheckFailure):
            logger.warning(
                "Falha na verificação de permissões para o comando: %s", full_command
            )
            await ctx.send(
                f"❌ {ctx.author.mention}, você não tem permissão para executar este comando!",
                delete_after=5,
            )

        elif isinstance(error, Forbidden):
            if "Missing Permissions" in str(error):
                logger.exception(
                    "O bot não tem permissões suficientes para executar o comando: %s",
                    full_command,
                )
                await ctx.send(
                    f"❌ {ctx.author.mention}, o bot não tem permissões suficientes para executar este comando!",
                    delete_after=5,
                )
            elif "hierarchy" in str(error):
                logger.exception(
                    "O bot não pode executar o comando devido à hierarquia de cargos: %s",
                    full_command,
                )
                await ctx.send(
                    f"❌ {ctx.author.mention}, não posso executar este comando devido à hierarquia de cargos!",
                    delete_after=5,
                )
            else:
                logger.exception(
                    "Erro Forbidden desconhecido no comando %s", full_command
                )
                await ctx.send(
                    f"❌ {ctx.author.mention}, ocorreu um erro de permissões!",
                    delete_after=5,
                )

        else:
            # 🆘 Erro inesperado
            logger.exception("Erro inesperado no comando %s", full_command)
            await ctx.send(
                f"❌ {ctx.author.mention}, ocorreu um erro inesperado! Tente novamente.",
                delete_after=5,
            )

    # Tratamento de Erros para comandos de barra (slash commands)
    @commands.Cog.listener()
    async def on_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        """
        ❌ Tratamento global de erros para slash commands
        💡 Logs profissionais + mensagens amigáveis!
        """
        command_name = (
            interaction.command.name if interaction.command else "Comando desconhecido"
        )

        if isinstance(error, app_commands.CommandNotFound):
            logger.info("Comando de barra não encontrado: %s", command_name)
            await interaction.response.send_message(
                "Comando não encontrado.", ephemeral=True
            )

        elif isinstance(error, app_commands.MissingPermissions):
            logger.warning(
                "Permissão ausente para o comando de barra: %s", command_name
            )
            await interaction.response.send_message(
                "Você não tem permissão para usar este comando.", ephemeral=True
            )

        elif isinstance(error, app_commands.CheckFailure):
            logger.warning(
                "Falha na verificação de permissões para o comando de barra: %s",
                command_name,
            )
            await interaction.response.send_message(
                "Você não tem permissão para executar este comando.", ephemeral=True
            )

        elif isinstance(error, app_commands.CommandOnCooldown):
            logger.info("Comando de barra em cooldown: %s", command_name)
            await interaction.response.send_message(
                f"Comando em cooldown. Tente novamente em {int(error.retry_after)} segundos.",
                ephemeral=True,
            )

        else:
            logger.exception("Erro inesperado no comando de barra %s", command_name)
            await interaction.response.send_message(
                "Ocorreu um erro inesperado ao executar o comando.", ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(Manager(bot))
