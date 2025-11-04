"""
💼 DTOs para operações com canais
💡 Boa Prática: Separa dados de entrada e saída!
"""

from __future__ import annotations  # 🆕 Python 3.13 - Forward references

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from domain.entities import ChannelType


@dataclass(slots=True, frozen=True)
class CreateChannelDTO:
    """
    📝 DTO para criação de canais

    💡 Boa Prática: Usa slots=True para economia de memória
    e frozen=True para imutabilidade e thread-safety
    """

    name: str
    channel_type: ChannelType
    guild_id: int
    category_id: int | None = None
    member_id: int | None = None
    is_temporary: bool = False  # 🆕 Para salas temporárias

    # 🔊 Campos específicos para canais de voz
    user_limit: int = 0  # 💖 Limite de usuários (0 = ilimitado)
    bitrate: int = 64000  # 💖 Taxa de bits padrão
    overwrites: dict[Any, Any] | None = (
        None  # 🔒 Permissões customizadas (roles/membros)
    )

    # 💬 Campos específicos para canais de texto
    topic: str | None = None  # 💖 Tópico do canal

    def __post_init__(self) -> None:
        """
        ✅ Validação automática dos dados

        💡 Boa Prática: Validação no DTO previne erros
        em camadas mais profundas da aplicação
        """
        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("Nome do canal não pode estar vazio")

        if len(self.name) > 100:
            raise ValueError("Nome do canal muito longo (máximo 100 caracteres)")

        if self.guild_id <= 0:
            raise ValueError("Guild ID deve ser positivo")


@dataclass(frozen=True, slots=True)  # 🆕 Performance otimizada
class ChannelResponseDTO:
    """
    📤 Dados de resposta de um canal

    💡 Boa Prática: DTO de saída com dados essenciais!

    Attributes:
        id: ID único do canal criado
        name: Nome do canal
        channel_type: Tipo do canal (texto, voz, etc.)
        guild_id: ID do servidor Discord
        category_id: ID da categoria pai (opcional)
        created: Status de criação (True = sucesso, False = falha)
    """

    id: int
    name: str
    channel_type: ChannelType
    guild_id: int
    category_id: int | None = None  # 💡 Union syntax moderna
    created: bool = False

    def __str__(self) -> str:
        """
        💡 Representação amigável do DTO para logs e debug.

        Returns:
            String formatada com informações do canal
        """
        status = "✅ Criado" if self.created else "❌ Falhou"
        return f"Canal {self.name} (ID: {self.id}) - {status}"

    @property
    def is_text_channel(self) -> bool:
        """💬 Verifica se é canal de texto."""
        # Import dinâmico para evitar circular import
        from domain.entities import ChannelType

        return self.channel_type == ChannelType.TEXT

    @property
    def is_voice_channel(self) -> bool:
        """🔊 Verifica se é canal de voz."""
        # Import dinâmico para evitar circular import
        from domain.entities import ChannelType

        return self.channel_type == ChannelType.VOICE
