"""
🎯 Infrastructure Events - Event Bus e Subscribers
💡 Boa Prática: Implementação concreta do padrão Observer!
"""

from .event_bus import EventBus
from .event_registry import setup_event_subscribers

__all__ = ["EventBus", "setup_event_subscribers"]
