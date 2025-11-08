"""
Controllers - Presentation Layer
Boa Prática: Camada que coordena UI com aplicação!
"""

from .bot_controller import BotController
from .channel_controller import ChannelController

__all__ = [
    "BotController",
    "ChannelController",
]
