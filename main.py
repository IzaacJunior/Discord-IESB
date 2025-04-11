import discord
from pathlib import Path
import asyncio
from discord.ext import commands
from decouple import config
from comandos.audio import Auto


intents = discord.Intents.default()
intents.members = True  
intents.message_content = True
bot = commands.Bot(
    command_prefix='!', 
    intents=intents, 
    application_id=config("APPLICATION_ID") 
)


async def load_cogs(bot):  
    await bot.load_extension("manager")
    for file in Path("comandos").glob("*.py"): 
        if file.stem == "__init__":
            continue
        if file.suffix == ".py":
            await bot.load_extension(f"comandos.{file.stem}")


async def main():  
    try:
        async with bot:
            TOKEN = config("TOKEN")
            await load_cogs(bot)
            await bot.start(TOKEN)
    except KeyboardInterrupt:
        print("Bot desconectado pelo usuário.")
        # Limpa os comandos de barra antes de desconectar
        try:
            await bot.tree.clear_commands(guild=None)  # Remove todos os comandos globais
            await bot.tree.sync()  # Sincroniza a remoção dos comandos
            print("Comandos de barra limpos com sucesso!")
        except Exception as e:
            print(f"Erro ao limpar os comandos de barra: {e}")
        await bot.close()


asyncio.run(main())  # Executa a função principal
