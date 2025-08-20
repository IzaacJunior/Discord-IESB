"""
💼 DTOs - Data Transfer Objects
💡 Boa Prática: Objetos para transferir dados entre camadas!
"""

from .channel_dto import ChannelResponseDTO, CreateChannelDTO
from .member_dto import MemberDTO

__all__ = [
    "ChannelResponseDTO",
    "CreateChannelDTO",
    "MemberDTO",
]
