"""
�️ Interface ChannelRepository - Domain Layer
💡 Boa Prática: Define contratos para persistência sem dependências externas!
"""

from __future__ import annotations 

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.entities import Channel, TextChannel, VoiceChannel

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

        Args:
            guild_id: ID do servidor Discord

        Returns:
            list[Channel]: Lista de canais do servidor
        """
        pass

    @abstractmethod
    async def channel_exists_by_name(
        self,
        name: str,
        guild_id: int,
    ) -> bool:
        """
        � Verifica se canal com nome específico já existe no servidor

        �💡 Boa Prática: Previne duplicatas antes da criação!

        Args:
            name: Nome do canal a verificar
            guild_id: ID do servidor Discord

        Returns:
            bool: True se canal já existe, False caso contrário
        """
        pass

    @abstractmethod
    async def get_channel_by_name_and_guild(
        self,
        name: str,
        guild_id: int,
    ) -> Channel | None:
        """
        🔍 Busca canal específico por nome e servidor

        💡 Boa Prática: Evita duplicatas com mesmo nome!

        Args:
            name: Nome do canal
            guild_id: ID do servidor Discord

        Returns:
            Channel | None: Canal encontrado ou None se não existir
        """
        pass

    @abstractmethod
    async def is_temp_room_category(
        self,
        category_id: int,
        guild_id: int,
        category_name: str | None = None,  # 💖 Nome opcional para logs mais bonitos
    ) -> bool:
        """
        🔍 Verifica se categoria está marcada como geradora de salas temporárias

        💡 Boa Prática: Consulta específica para evitar lógica duplicada!

        Args:
            category_id: ID da categoria Discord
            guild_id: ID do servidor Discord
            category_name: Nome da categoria (opcional, para logs)

        Returns:
            bool: True se categoria gera salas temporárias, False caso contrário
        """
        pass

    @abstractmethod
    async def mark_category_as_temp_generator(
        self,
        category_id: int,
        category_name: str,
        guild_id: int,
    ) -> bool:
        """
        💾 Marca categoria como geradora de salas temporárias

        💡 Boa Prática: Persiste configuração para uso posterior!

        Args:
            category_id: ID da categoria Discord
            category_name: Nome da categoria
            guild_id: ID do servidor Discord

        Returns:
            bool: True se marcação foi bem-sucedida, False caso contrário
        """
        pass

    @abstractmethod
    async def unmark_category_as_temp_generator(
        self,
        category_id: int,
        guild_id: int,
    ) -> bool:
        """
        🗑️ Remove marcação de categoria como geradora de salas temporárias

        💡 Boa Prática: Permite desativar funcionalidade!

        Args:
            category_id: ID da categoria Discord
            guild_id: ID do servidor Discord

        Returns:
            bool: True se remoção foi bem-sucedida, False caso contrário
        """
        pass

    @abstractmethod
    async def is_temporary_channel(
        self,
        channel_id: int,
        guild_id: int,
    ) -> bool:
        """
        🔍 Verifica se canal é uma sala temporária ativa

        💡 Boa Prática: Consulta banco para verificar status!

        Args:
            channel_id: ID do canal Discord
            guild_id: ID do servidor Discord

        Returns:
            bool: True se canal é temporário e ativo, False caso contrário
        """
        pass
