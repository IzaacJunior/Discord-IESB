"""
🎯 Event Registry - Registro Centralizado de Subscribers
💡 Boa Prática: Configuração centralizada facilita gerenciamento!
"""

import logging

import discord

from infrastructure.events.event_bus import EventBus
from infrastructure.events.subscribers import (
    AnalyticsSubscriber,
    NotificationSubscriber,
    UserStatsSubscriber,
)

logger = logging.getLogger(__name__)


def setup_event_subscribers(event_bus: EventBus, bot: discord.Client | None = None) -> dict:
    """
    📡 Configura e registra todos os subscribers do sistema
    
    💡 Boa Prática: Registro centralizado facilita:
    - Descobrir quem ouve o quê
    - Adicionar/remover subscribers facilmente
    - Gerenciar dependências entre subscribers
    - Testar sistema de eventos
    
    Args:
        event_bus: Instância do Event Bus
        bot: Cliente Discord (opcional, para notificações)
    
    Returns:
        Dicionário com instâncias dos subscribers criados
    
    Examples:
        >>> event_bus = EventBus()
        >>> subscribers = setup_event_subscribers(event_bus, bot)
        >>> # Todos os subscribers agora estão registrados!
    """
    logger.info("🎯 Iniciando configuração de subscribers...")
    
    # ============================================
    # 📊 ANALYTICS SUBSCRIBER
    # ============================================
    analytics_subscriber = AnalyticsSubscriber()
    
    # Registra eventos de interesse
    event_bus.subscribe("temp_room_created", analytics_subscriber.on_temp_room_created)
    event_bus.subscribe("temp_room_deleted", analytics_subscriber.on_temp_room_deleted)
    event_bus.subscribe("command_executed", analytics_subscriber.on_command_executed)
    
    logger.info("✅ Analytics Subscriber registrado (3 eventos)")
    
    # ============================================
    # 📈 USER STATS SUBSCRIBER
    # ============================================
    stats_subscriber = UserStatsSubscriber()
    
    # Registra eventos de interesse
    event_bus.subscribe("temp_room_created", stats_subscriber.on_temp_room_created)
    event_bus.subscribe("temp_room_deleted", stats_subscriber.on_temp_room_deleted)
    event_bus.subscribe("command_executed", stats_subscriber.on_command_executed)
    
    logger.info("✅ Stats Subscriber registrado (3 eventos)")
    
    # ============================================
    # 🔔 NOTIFICATION SUBSCRIBER
    # ============================================
    notification_subscriber = NotificationSubscriber(bot)
    
    # Registra eventos de interesse
    event_bus.subscribe("temp_room_created", notification_subscriber.on_temp_room_created)
    event_bus.subscribe("temp_room_deleted", notification_subscriber.on_temp_room_deleted)
    event_bus.subscribe("member_joined_guild", notification_subscriber.on_member_joined_guild)
    
    logger.info("✅ Notification Subscriber registrado (3 eventos)")
    
    # ============================================
    # 📊 RESUMO
    # ============================================
    total_handlers = sum(
        len(handlers) for handlers in event_bus._handlers.values()
    )
    
    logger.info(
        "🎉 Setup concluído: %d subscriber(s), %d handler(s) registrado(s)",
        3,  # Total de subscribers
        total_handlers
    )
    
    # Retorna referências aos subscribers (útil para testes e debugging)
    return {
        "analytics": analytics_subscriber,
        "stats": stats_subscriber,
        "notifications": notification_subscriber,
    }


def setup_additional_subscribers(event_bus: EventBus) -> None:
    """
    🔮 Placeholder para subscribers adicionais futuros
    
    💡 Boa Prática: Facilita adicionar novos subscribers
    sem modificar setup principal!
    
    Exemplos de subscribers futuros:
    - AuditSubscriber: Registra auditoria de segurança
    - CacheSubscriber: Invalida cache quando necessário
    - AchievementSubscriber: Sistema de conquistas
    - EmailSubscriber: Envia emails sobre eventos
    - WebhookSubscriber: Integração com sistemas externos
    
    Args:
        event_bus: Instância do Event Bus
    """
    logger.info("🔮 Setup adicional de subscribers (implementar conforme necessário)")
    
    # Exemplo de como adicionar no futuro:
    """
    # 🔒 Audit Subscriber
    from infrastructure.events.subscribers import AuditSubscriber
    
    audit_subscriber = AuditSubscriber()
    event_bus.subscribe("temp_room_created", audit_subscriber.on_temp_room_created)
    event_bus.subscribe("temp_room_deleted", audit_subscriber.on_temp_room_deleted)
    event_bus.subscribe("member_banned", audit_subscriber.on_member_banned)
    
    logger.info("✅ Audit Subscriber registrado")
    
    # 💾 Cache Subscriber
    from infrastructure.events.subscribers import CacheSubscriber
    
    cache_subscriber = CacheSubscriber(redis_client)
    event_bus.subscribe("temp_room_created", cache_subscriber.on_temp_room_created)
    event_bus.subscribe("channel_deleted", cache_subscriber.on_channel_deleted)
    
    logger.info("✅ Cache Subscriber registrado")
    """
