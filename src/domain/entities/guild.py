"""
🏛️ Entidade Guild - Representa um servidor Discord
💡 Boa Prática: Agregado principal do domínio!
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Guild:
    """
    🏰 Representa um servidor (guild) no Discord

    💡 Boa Prática: Entidade agregada que representa
    o contexto principal do negócio!
    """

    id: int
    name: str
    member_count: int = 0
    owner_id: int = 0

    def is_small_guild(self) -> bool:
        """
        👥 Verifica se é um servidor pequeno (< 100 membros)

        💡 Boa Prática: Regra de negócio expressa de forma
        clara e testável!
        """
        return self.member_count < 100

    def is_large_guild(self) -> bool:
        """
        🏟️ Verifica se é um servidor grande (>= 500 membros)

        💡 Boa Prática: Constantes de negócio bem definidas!
        """
        return self.member_count >= 500
