"""
🎯 Domain Event - Representa eventos que acontecem no domínio
💡 Boa Prática: Eventos são imutáveis e descrevem fatos passados!
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class DomainEvent:
    """
    🎯 Evento de domínio imutável
    
    Representa algo que aconteceu no sistema e que outras
    partes podem querer reagir.
    
    💡 Boa Prática: Eventos são sempre no passado (ex: "created", não "create")
    e contêm todos os dados necessários para reagir a eles!
    
    Attributes:
        event_type: Tipo do evento (ex: "temp_room_created")
        data: Dados relevantes do evento
        timestamp: Quando o evento ocorreu (UTC)
        event_id: ID único do evento (gerado automaticamente)
    
    Examples:
        >>> event = DomainEvent(
        ...     event_type="temp_room_created",
        ...     data={"channel_id": 123, "owner_id": 456}
        ... )
        >>> print(event.event_type)
        temp_room_created
    """
    
    event_type: str
    data: dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    event_id: str = field(default_factory=lambda: f"evt_{datetime.now(UTC).timestamp()}")
    
    def __post_init__(self) -> None:
        """
        🛡️ Validação pós-inicialização
        
        💡 Boa Prática: Valida dados na criação para garantir
        que eventos sejam sempre válidos!
        """
        if not self.event_type:
            raise ValueError("event_type não pode estar vazio")
        
        if not isinstance(self.data, dict):
            raise TypeError("data deve ser um dicionário")


# 💡 Type alias para handlers de eventos
EventHandler = Callable[[DomainEvent], Awaitable[None]]
