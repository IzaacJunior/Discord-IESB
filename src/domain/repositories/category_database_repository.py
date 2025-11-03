"""
💾 Interface para operações de Categoria no Banco de Dados - Domain Layer

🎯 Responsabilidade: Operações de persistência relacionadas a categorias
    - Salas Temporárias (temp_room_categories)
    - Fóruns Únicos (unique_channel_categories)
"""

from abc import ABC, abstractmethod


class CategoryDatabaseRepository(ABC):
    """
    🗄️ Interface abstrata para operações de categoria no banco de dados

    💡 Boa Prática: Abstração permite trocar implementação (SQLite → PostgreSQL)
    sem impactar o resto do sistema!

    ✨ Benefícios:
        - Testabilidade: Pode criar mocks facilmente
        - Flexibilidade: Troca de banco sem quebrar código
        - Clean Architecture: Dependências apontam para o domain
    """

    # ═══════════════════════════════════════════════════════════════
    # 🏠 OPERAÇÕES DE SALAS TEMPORÁRIAS
    # ═══════════════════════════════════════════════════════════════

    @abstractmethod
    async def is_temp_room_category(
        self,
        category_id: int,
        guild_id: int,
    ) -> bool:
        """
        🔍 Verifica se categoria está marcada como geradora de salas temporárias

        Args:
            category_id: ID da categoria Discord
            guild_id: ID do servidor Discord

        Returns:
            bool: True se categoria gera salas temporárias
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

        Args:
            category_id: ID da categoria Discord
            category_name: Nome da categoria
            guild_id: ID do servidor Discord

        Returns:
            bool: True se marcação foi bem-sucedida
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

        Args:
            category_id: ID da categoria Discord
            guild_id: ID do servidor Discord

        Returns:
            bool: True se remoção foi bem-sucedida
        """
        pass

    @abstractmethod
    async def get_temp_channels_by_category(
        self,
        category_id: int,
        guild_id: int,
    ) -> list[int]:
        """
        🔍 Busca todos os canais temporários de uma categoria

        Args:
            category_id: ID da categoria Discord
            guild_id: ID do servidor Discord

        Returns:
            list[int]: Lista com IDs dos canais temporários ativos
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

        Args:
            channel_id: ID do canal Discord
            guild_id: ID do servidor Discord

        Returns:
            bool: True se canal é temporário e ativo
        """
        pass

    # ═══════════════════════════════════════════════════════════════
    # 🎓 OPERAÇÕES DE FÓRUNS ÚNICOS POR MEMBRO
    # ═══════════════════════════════════════════════════════════════

    @abstractmethod
    async def is_unique_channel_category(
        self,
        category_id: int,
        guild_id: int,
    ) -> bool:
        """
        🔍 Verifica se categoria está marcada para criar fóruns únicos

        Args:
            category_id: ID da categoria Discord
            guild_id: ID do servidor Discord

        Returns:
            bool: True se categoria cria fóruns únicos
        """
        pass

    @abstractmethod
    async def get_unique_channel_category(
        self,
        guild_id: int,
    ) -> dict | None:
        """
        🔍 Busca a categoria configurada para fóruns únicos no servidor

        Args:
            guild_id: ID do servidor Discord

        Returns:
            dict | None: Informações da categoria ou None se não configurada
        """
        pass

    @abstractmethod
    async def mark_category_as_unique_generator(
        self,
        category_id: int,
        category_name: str,
        guild_id: int,
    ) -> bool:
        """
        💾 Marca categoria como geradora de fóruns únicos por membro

        Args:
            category_id: ID da categoria Discord
            category_name: Nome da categoria
            guild_id: ID do servidor Discord

        Returns:
            bool: True se marcação foi bem-sucedida
        """
        pass

    @abstractmethod
    async def unmark_category_as_unique_generator(
        self,
        category_id: int,
        guild_id: int,
    ) -> bool:
        """
        🗑️ Remove marcação de categoria como geradora de fóruns únicos

        Args:
            category_id: ID da categoria Discord
            guild_id: ID do servidor Discord

        Returns:
            bool: True se remoção foi bem-sucedida
        """
        pass

    @abstractmethod
    async def member_has_unique_channel_in_category(
        self,
        member_id: int,
        category_id: int,
        guild_id: int,
    ) -> bool:
        """
        🔍 Verifica se membro JÁ possui fórum único nesta categoria

        Args:
            member_id: ID do membro Discord
            category_id: ID da categoria Discord
            guild_id: ID do servidor Discord

        Returns:
            bool: True se membro já tem canal nesta categoria
        """
        pass

    @abstractmethod
    async def register_member_unique_channel(
        self,
        member_id: int,
        channel_id: int,
        channel_name: str,
        guild_id: int,
        category_id: int,
    ) -> bool:
        """
        💾 Registra fórum único criado para um membro

        Args:
            member_id: ID do membro Discord
            channel_id: ID do canal criado
            channel_name: Nome do canal
            guild_id: ID do servidor Discord
            category_id: ID da categoria onde o canal está

        Returns:
            bool: True se registro foi bem-sucedido
        """
        pass

    @abstractmethod
    async def get_member_unique_channels(
        self,
        member_id: int,
        guild_id: int,
    ) -> list[dict]:
        """
        📋 Lista todos os fóruns únicos de um membro no servidor

        Args:
            member_id: ID do membro Discord
            guild_id: ID do servidor Discord

        Returns:
            list[dict]: Lista com informações dos canais
        """
        pass
