"""
🏛️ Entidades Channel - Representa canais do Discord
💡 Boa Prática: Hierarquia clara e bem definida!
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class ChannelType(Enum):
    """
    📝 Tipos de canal disponíveis
    
    💡 Boa Prática: Enum torna o código mais legível
    e evita magic numbers!
    """
    TEXT = "text"
    VOICE = "voice"
    CATEGORY = "category"


@dataclass(frozen=True)
class Channel(ABC):
    """
    🌐 Classe base abstrata para todos os canais
    
    💡 Boa Prática: Define o contrato comum que todos
    os tipos de canal devem seguir!
    """
    
    id: int
    name: str
    guild_id: int
    category_id: int | None = None
    
    @abstractmethod
    def channel_type(self) -> ChannelType:
        """
        🏷️ Tipo específico do canal
        
        💡 Boa Prática: Método abstrato força implementação
        nas classes filhas!
        """
        pass


@dataclass(frozen=True)
class TextChannel(Channel):
    """
    💬 Canal de texto do Discord
    
    💡 Boa Prática: Especialização focada em texto!
    """
    
    topic: str | None = None
    
    def channel_type(self) -> ChannelType:
        """💬 Identifica como canal de texto"""
        return ChannelType.TEXT
    
    def has_topic(self) -> bool:
        """
        📝 Verifica se o canal tem tópico definido
        
        💡 Boa Prática: Encapsula verificação de negócio!
        """
        return bool(self.topic and self.topic.strip())


@dataclass(frozen=True)  
class VoiceChannel(Channel):
    """
    🔊 Canal de voz do Discord
    
    💡 Boa Prática: Especialização focada em voz!
    """
    
    user_limit: int = 0
    bitrate: int = 64000
    
    def channel_type(self) -> ChannelType:
        """🔊 Identifica como canal de voz"""
        return ChannelType.VOICE
    
    def is_unlimited(self) -> bool:
        """
        ♾️ Verifica se o canal tem limite ilimitado de usuários
        
        💡 Boa Prática: Expressão clara da regra de negócio!
        """
        return self.user_limit == 0
    
    def has_high_quality(self) -> bool:
        """
        🎵 Verifica se o canal tem qualidade alta (>= 128kbps)
        
        💡 Boa Prática: Constantes de negócio encapsuladas!
        """
        return self.bitrate >= 128000
