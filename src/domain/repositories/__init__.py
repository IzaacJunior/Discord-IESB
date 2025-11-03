"""
Interfaces de Repositórios - Domain Layer
Boa Prática: Contratos que definem como acessar dados!
"""

from .category_database_repository import CategoryDatabaseRepository
from .channel_repository import ChannelRepository

__all__ = [
    "CategoryDatabaseRepository",
    "ChannelRepository",
]
