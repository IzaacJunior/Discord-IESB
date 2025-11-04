"""
🎯 Subscribers - Implementações de Event Handlers
💡 Boa Prática: Cada subscriber tem responsabilidade única!
"""

from .analytics_subscriber import AnalyticsSubscriber
from .notification_subscriber import NotificationSubscriber
from .stats_subscriber import UserStatsSubscriber

__all__ = [
    "AnalyticsSubscriber",
    "NotificationSubscriber",
    "UserStatsSubscriber",
]
