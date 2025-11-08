"""
🤖 Bot Lifecycle Use Cases
"""

import asyncio
import logging

from discord.ext import commands

from application.dtos.bot_dtos import ShutdownRequest, ShutdownResponse

audit = logging.getLogger("audit")


class BotLifecycleUseCase:
    """
    🔌 Use Case para gerenciar ciclo de vida do bot
    """

    def __init__(self, bot: commands.Bot):
        self._bot = bot

    async def shutdown(self, request: ShutdownRequest) -> ShutdownResponse:
        """
        🛑 Desliga o bot de forma graciosa
        """
        try:
            audit.warning(
                "🛑 Bot sendo desligado pelo admin %s no servidor %s. Motivo: %s",
                request.admin_name,
                request.guild_name,
                request.reason
            )
            
            await asyncio.sleep(1)
            await self._bot.close()
            
            return ShutdownResponse(
                success=True,
                message="Bot desconectado com sucesso! 💕"
            )
            
        except Exception as e:
            audit.error("💔 Erro ao desligar bot: %s", str(e))
            
            return ShutdownResponse(
                success=False,
                message="Erro ao desconectar o bot! 😢",
                error=str(e)
            )
