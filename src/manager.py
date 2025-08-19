from discord.ext.commands import errors
from discord.ext import commands
from discord import Forbidden, app_commands
import discord

class Manager(commands.Cog):
    """Manage the bot"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.bot.user.name} estou online!")  
        
        # Sincroniza os comandos de barra com o Discord
        try:
            await self.bot.tree.sync()
            print("Comandos de barra sincronizados com sucesso!")
        except Exception as e:
            print(f"Erro ao sincronizar comandos de barra: {e}")

    # Ve todas as mensagens
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if message.content.startswith(self.bot.command_prefix):
            await message.delete()

    # Tratamento de Erros provindos de comandos de texto
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        full_command = f"{self.bot.command_prefix}{ctx.command.name}" if ctx.command else "Comando desconhecido"
        match error:
            case errors.CommandNotFound():
                print(f"Comando não encontrado: {full_command}")
                await ctx.send("Comando não encontrado.", delete_after=5)

            case errors.MissingRequiredArgument():
                print(f"Argumento obrigatório ausente no comando: {full_command}")
                await ctx.send("Argumento obrigatório ausente.", delete_after=5)

            case errors.CommandOnCooldown():
                print(f"Comando em cooldown: {full_command}")
                await ctx.send(f"Comando em cooldown. Tente novamente em {int(error.retry_after)} segundos.", delete_after=5)
            
            case errors.MissingPermissions():
                print(f"Permissão ausente para o comando: {full_command}")
                await ctx.send("Você não tem permissão para usar este comando.", delete_after=5)
            
            case errors.CheckFailure():
                print(f"Falha na verificação de permissões para o comando: {full_command}")
                await ctx.send(f"Você não tem permissão para executar o comando {full_command}.", delete_after=5)
            
            case Forbidden() as forbidden_error:
                if "Missing Permissions" in str(forbidden_error):
                    print(f"O bot não tem permissões suficientes para executar o comando: {full_command}")
                    await ctx.send("O bot não tem permissões suficientes para executar este comando.", delete_after=5)
                elif "hierarchy" in str(forbidden_error):
                    print(f"O bot não pode executar o comando devido à hierarquia de cargos: {full_command}")
                    await ctx.send("O bot não pode executar este comando devido à hierarquia de cargos.", delete_after=5)
                else:
                    print(f"Erro Forbidden desconhecido no comando {full_command}: {forbidden_error}")
                    await ctx.send("Ocorreu um erro desconhecido relacionado a permissões.", delete_after=5)
            
            case _:
                print(f"Erro inesperado no comando {full_command}: {error}")
                await ctx.send("Ocorreu um erro inesperado ao executar o comando.", delete_after=5)

    # Tratamento de Erros para comandos de barra (slash commands)
    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        command_name = interaction.command.name if interaction.command else "Comando desconhecido"
        match error:
            case app_commands.CommandNotFound():
                print(f"Comando de barra não encontrado: {command_name}")
                await interaction.response.send_message("Comando não encontrado.", ephemeral=True)

            case app_commands.MissingPermissions():
                print(f"Permissão ausente para o comando de barra: {command_name}")
                await interaction.response.send_message("Você não tem permissão para usar este comando.", ephemeral=True)

            case app_commands.CheckFailure():
                print(f"Falha na verificação de permissões para o comando de barra: {command_name}")
                await interaction.response.send_message("Você não tem permissão para executar este comando.", ephemeral=True)

            case app_commands.CommandOnCooldown() as cooldown_error:
                print(f"Comando de barra em cooldown: {command_name}")
                await interaction.response.send_message(
                    f"Comando em cooldown. Tente novamente em {int(cooldown_error.retry_after)} segundos.",
                    ephemeral=True
                )

            case _:
                print(f"Erro inesperado no comando de barra {command_name}: {error}")
                await interaction.response.send_message("Ocorreu um erro inesperado ao executar o comando.", ephemeral=True)


async def setup(bot):  
    await bot.add_cog(Manager(bot))