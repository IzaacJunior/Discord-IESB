"""
💼 DTOs para operações com canais
💡 Boa Prática: Separa dados de entrada e saída!
"""

from dataclasses import dataclass

from domain.entities import ChannelType


@dataclass(frozen=True)
class CreateChannelDTO:
    """
    📝 Dados para criar um novo canal
    
    💡 Boa Prática: DTO de entrada com validação implícita!
    """
    
    name: str
    guild_id: int
    channel_type: ChannelType
    category_id: int | None = None
    topic: str | None = None
    user_limit: int = 0
    bitrate: int = 64000


@dataclass(frozen=True)
class ChannelResponseDTO:
    """
    📤 Dados de resposta de um canal
    
    💡 Boa Prática: DTO de saída com dados essenciais!
    """
    
    id: int
    name: str
    channel_type: ChannelType
    guild_id: int
    category_id: int | None = None
    created: bool = False
