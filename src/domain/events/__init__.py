"""
🎯 Domain Events - Eventos de Domínio
💡 Boa Prática: Eventos representam fatos que aconteceram no domínio!
"""

from .domain_event import DomainEvent, EventHandler

__all__ = ["DomainEvent", "EventHandler"]
