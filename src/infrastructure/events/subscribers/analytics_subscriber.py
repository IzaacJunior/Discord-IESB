"""
📊 Analytics Subscriber - Rastreia eventos para análise
💡 Boa Prática: Subscriber isolado facilita manutenção e testes!
"""

import logging

from domain.events import DomainEvent

logger = logging.getLogger(__name__)


class AnalyticsSubscriber:
    """
    📊 Subscriber para eventos de analytics

    Responsável por rastrear eventos importantes do sistema
    para análise de uso e comportamento dos usuários.

    💡 Boa Prática: Cada subscriber tem uma responsabilidade única,
    facilitando manutenção e permitindo falhas isoladas!

    Examples:
        >>> analytics = AnalyticsSubscriber()
        >>> event_bus.subscribe("temp_room_created", analytics.on_temp_room_created)
    """

    def __init__(self) -> None:
        """Inicializa subscriber de analytics"""
        self.events_tracked: list[dict] = []
        logger.info("📊 Analytics Subscriber inicializado")

    async def on_temp_room_created(self, event: DomainEvent) -> None:
        """
        📊 Rastreia criação de sala temporária

        💡 Boa Prática: Se falhar, não quebra a criação da sala!

        Args:
            event: Evento com dados da sala criada
        """
        try:
            data = event.data

            # 📊 Registra evento (aqui você integraria com Google Analytics, Mixpanel, etc)
            tracked_event = {
                "event_type": "temp_room_created",
                "channel_id": data.get("channel_id"),
                "owner_id": data.get("owner_id"),
                "guild_id": data.get("guild_id"),
                "channel_name": data.get("channel_name"),
                "timestamp": event.timestamp.isoformat(),
            }

            self.events_tracked.append(tracked_event)

            logger.info(
                "📊 Analytics registrado: sala '%s' criada por usuário %s",
                data.get("channel_name"),
                data.get("owner_id"),
            )

            # 💡 Aqui você integraria com serviços reais:
            # await self.google_analytics.track_event(tracked_event)
            # await self.mixpanel.track(user_id, "Room Created", tracked_event)

        except Exception as e:
            logger.error("❌ Erro ao rastrear analytics: %s", str(e), exc_info=True)
            # 🛡️ Não propaga erro - falha isolada

    async def on_temp_room_deleted(self, event: DomainEvent) -> None:
        """
        📊 Rastreia exclusão de sala temporária

        Args:
            event: Evento com dados da sala deletada
        """
        try:
            data = event.data

            tracked_event = {
                "event_type": "temp_room_deleted",
                "channel_id": data.get("channel_id"),
                "owner_id": data.get("owner_id"),
                "duration_seconds": data.get("duration_seconds"),
                "timestamp": event.timestamp.isoformat(),
            }

            self.events_tracked.append(tracked_event)

            logger.info(
                "📊 Analytics registrado: sala ID %s deletada após %s segundos",
                data.get("channel_id"),
                data.get("duration_seconds"),
            )

        except Exception as e:
            logger.error("❌ Erro ao rastrear analytics de exclusão: %s", str(e))

    async def on_command_executed(self, event: DomainEvent) -> None:
        """
        📊 Rastreia execução de comandos

        Args:
            event: Evento com dados do comando executado
        """
        try:
            data = event.data

            tracked_event = {
                "event_type": "command_executed",
                "command_name": data.get("command_name"),
                "user_id": data.get("user_id"),
                "guild_id": data.get("guild_id"),
                "success": data.get("success", True),
                "timestamp": event.timestamp.isoformat(),
            }

            self.events_tracked.append(tracked_event)

            logger.info(
                "📊 Analytics registrado: comando '%s' executado por usuário %s",
                data.get("command_name"),
                data.get("user_id"),
            )

        except Exception as e:
            logger.error("❌ Erro ao rastrear comando: %s", str(e))
