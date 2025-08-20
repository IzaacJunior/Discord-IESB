"""
🗄️ Interface Channel Repository - Domain Layer
💡 Boa Prática: Define contratos sem implementação!
"""

from abc import ABC, abstractmethod

from ..entities import Channel, TextChannel, VoiceChannel


class ChannelRepository(ABC):
    """
    🗄️ Interface para operações com canais
    
    💡 Boa Prática: Domain define o "O QUE" fazer,
    Infrastructure define "COMO" fazer!
    """
    
    @abstractmethod
    async def create_text_channel(
        self,
        name: str,
        guild_id: int,
        category_id: int | None = None,
        topic: str | None = None,
    ) -> TextChannel:
        """
        💬 Cria um novo canal de texto
        
        💡 Boa Prática: Assinatura clara e tipada!
        """
        pass
    
    @abstractmethod
    async def create_voice_channel(
        self,
        name: str,
        guild_id: int,
        category_id: int | None = None,
        user_limit: int = 0,
        bitrate: int = 64000,
    ) -> VoiceChannel:
        """
        🔊 Cria um novo canal de voz
        
        💡 Boa Prática: Parâmetros com valores padrão sensatos!
        """
        pass
    
    @abstractmethod
    async def get_channel_by_id(self, channel_id: int) -> Channel | None:
        """
        🔍 Busca canal por ID
        
        💡 Boa Prática: Retorna None quando não encontra!
        """
        pass
    
    @abstractmethod
    async def delete_channel(self, channel_id: int) -> bool:
        """
        🗑️ Remove um canal
        
        💡 Boa Prática: Retorna sucesso/falha da operação!
        """
        pass
    
    @abstractmethod
    async def list_channels_by_guild(self, guild_id: int) -> list[Channel]:
        """
        📋 Lista todos os canais de um servidor
        
        💡 Boa Prática: Operação de consulta bem definida!
        """
        pass
