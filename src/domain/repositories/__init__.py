"""
🏛️ Interfaces de Repositórios - Domain Layer
💡 Boa Prática: Contratos que definem como acessar dados!
"""

from .channel_repository import ChannelRepository
from .guild_repository import GuildRepository
from .member_repository import MemberRepository

__all__ = [
    "ChannelRepository",
    "GuildRepository",
    "MemberRepository",
]
