"""
Entidades de Domínio
Boa Prática: Representam os conceitos centrais do negócio!
"""

from .channel import Channel, ChannelType, TextChannel, VoiceChannel
from .guild import Guild
from .member import Member

__all__ = [
    "Channel",
    "ChannelType",
    "Guild",
    "Member",
    "TextChannel",
    "VoiceChannel",
]
