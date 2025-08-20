"""
🏛️ Entidade Member - Representa um membro do Discord
💡 Boa Prática: Entidades puras sem dependências externas!
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Member:
    """
    👤 Representa um membro do servidor Discord

    💡 Boa Prática: Imutável e focada nos dados essenciais
    do negócio, sem lógica complexa!
    """

    id: int
    name: str
    display_name: str | None = None
    is_bot: bool = False
    guild_id: int = 0

    @property
    def effective_name(self) -> str:
        """
        ✨ Nome efetivo do membro (display_name ou name)

        💡 Boa Prática: Encapsula lógica simples de negócio
        dentro da própria entidade!
        """
        return self.display_name or self.name

    def is_human(self) -> bool:
        """
        🤖 Verifica se o membro é humano (não bot)

        💡 Boa Prática: Métodos que expressam regras de negócio
        de forma clara e legível!
        """
        return not self.is_bot
