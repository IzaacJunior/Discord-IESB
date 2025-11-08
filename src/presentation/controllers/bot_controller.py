"""
🤖 Bot Controller
"""

import logging

from application.dtos.bot_dtos import ShutdownRequest, ShutdownResponse
from application.use_cases.bot_use_cases import BotLifecycleUseCase

audit = logging.getLogger("audit")


class BotController:
    """
    🎮 Controller para operações do bot
    """

    def __init__(self, bot_lifecycle_use_case: BotLifecycleUseCase):
        self._bot_lifecycle_use_case = bot_lifecycle_use_case

    async def shutdown(
        self,
        admin_name: str,
        guild_name: str,
        reason: str = "Comando administrativo"
    ) -> ShutdownResponse:
        """
        🛑 Solicita desligamento do bot
        """
        request = ShutdownRequest(
            admin_name=admin_name,
            guild_name=guild_name,
            reason=reason
        )
        
        return await self._bot_lifecycle_use_case.shutdown(request)
