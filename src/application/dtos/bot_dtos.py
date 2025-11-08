"""
🤖 Bot DTOs

Data Transfer Objects para operações do bot.
"""

from dataclasses import dataclass


@dataclass
class ShutdownRequest:
    """Requisição para desligar o bot"""
    admin_name: str
    guild_name: str
    reason: str = "Comando administrativo"


@dataclass
class ShutdownResponse:
    """Resposta do desligamento"""
    success: bool
    message: str
    error: str | None = None
