"""
💼 DTO para Member
💡 Boa Prática: Transferência de dados entre camadas!
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MemberDTO:
    """
    👤 Dados de um membro para transferência
    
    💡 Boa Prática: Estrutura simples e imutável!
    """
    
    id: int
    name: str
    display_name: str | None = None
    guild_id: int = 0
