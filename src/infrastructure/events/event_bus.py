"""
🎯 Event Bus - Mediador Central de Eventos
💡 Boa Prática: Implementa padrão Observer/Pub-Sub para desacoplamento!
"""

import asyncio
import logging
from collections import defaultdict
from typing import Any

from domain.events import DomainEvent, EventHandler

logger = logging.getLogger(__name__)


class EventBus:
    """
    🎯 Event Bus - Sistema centralizado de eventos

    Implementa o padrão Observer/Pub-Sub permitindo que diferentes
    partes do sistema se comuniquem sem conhecer umas às outras.

    💡 Boa Prática: Desacopla publishers de subscribers, facilitando
    manutenção, testes e adição de novas funcionalidades!

    Features:
        ✅ Subscribers múltiplos por evento
        ✅ Execução paralela de handlers
        ✅ Error handling isolado (falha de um não afeta outros)
        ✅ Logging detalhado para debugging
        ✅ Type-safe com type hints

    Examples:
        >>> event_bus = EventBus()
        >>>
        >>> # Registra subscriber
        >>> async def on_room_created(event: DomainEvent):
        ...     print(f"Sala criada: {event.data['channel_id']}")
        >>>
        >>> event_bus.subscribe("temp_room_created", on_room_created)
        >>>
        >>> # Publica evento
        >>> await event_bus.publish(DomainEvent(
        ...     event_type="temp_room_created",
        ...     data={"channel_id": 123}
        ... ))
    """

    def __init__(self) -> None:
        """
        💡 Inicializa Event Bus vazio

        Usa defaultdict para facilitar adição de handlers
        sem verificar se chave existe!
        """
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._stats: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"published": 0, "handlers_executed": 0, "handlers_failed": 0}
        )
        logger.info("🎯 Event Bus inicializado")

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """
        📡 Registra um handler para um tipo de evento

        💡 Boa Prática: Permite múltiplos handlers para mesmo evento,
        facilitando composição de funcionalidades!

        Args:
            event_type: Tipo do evento a escutar (ex: "temp_room_created")
            handler: Função async que processa o evento

        Examples:
            >>> async def send_notification(event: DomainEvent):
            ...     await notification_service.send(event.data)
            >>>
            >>> event_bus.subscribe("temp_room_created", send_notification)
        """
        if not asyncio.iscoroutinefunction(handler):
            raise TypeError(
                f"Handler deve ser uma coroutine (async function). "
                f"Recebido: {type(handler).__name__}"
            )

        self._handlers[event_type].append(handler)
        handler_name = handler.__name__

        logger.info(
            "📡 Handler registrado: %s -> %s (total: %d handlers)",
            event_type,
            handler_name,
            len(self._handlers[event_type]),
        )

    def unsubscribe(self, event_type: str, handler: EventHandler) -> bool:
        """
        🔕 Remove um handler de um evento

        Args:
            event_type: Tipo do evento
            handler: Handler a remover

        Returns:
            True se removeu, False se handler não estava registrado
        """
        if event_type not in self._handlers:
            return False

        try:
            self._handlers[event_type].remove(handler)
            logger.info("🔕 Handler removido: %s -> %s", event_type, handler.__name__)
            return True
        except ValueError:
            return False

    async def publish(self, event: DomainEvent) -> None:
        """
        📢 Publica um evento para todos os handlers registrados

        💡 Boa Prática: Executa handlers em paralelo para melhor
        performance e isola falhas para que erro de um não afete outros!

        Args:
            event: Evento a ser publicado

        Examples:
            >>> await event_bus.publish(DomainEvent(
            ...     event_type="temp_room_created",
            ...     data={
            ...         "channel_id": 123,
            ...         "owner_id": 456,
            ...         "channel_name": "Sala VIP"
            ...     }
            ... ))
        """
        handlers = self._handlers.get(event.event_type, [])

        if not handlers:
            logger.debug(
                "📭 Nenhum handler registrado para evento: %s", event.event_type
            )
            return

        logger.info(
            "📢 Publicando evento: %s (ID: %s) para %d handler(s)",
            event.event_type,
            event.event_id,
            len(handlers),
        )

        # 📊 Atualiza estatísticas
        self._stats[event.event_type]["published"] += 1

        # 🚀 Executa todos os handlers em paralelo
        # return_exceptions=True garante que erro de um não quebra outros
        results = await asyncio.gather(
            *[self._safe_handle(handler, event) for handler in handlers],
            return_exceptions=True,
        )

        # 📊 Conta sucessos e falhas
        successes = sum(1 for r in results if r is True)
        failures = sum(1 for r in results if isinstance(r, Exception))

        logger.info(
            "✅ Evento %s processado: %d sucesso(s), %d falha(s)",
            event.event_type,
            successes,
            failures,
        )

    async def _safe_handle(self, handler: EventHandler, event: DomainEvent) -> bool:
        """
        🛡️ Executa handler com tratamento de erros isolado

        💡 Boa Prática: Isola falhas para que erro em um handler
        não impeça execução dos outros!

        Args:
            handler: Handler a executar
            event: Evento a processar

        Returns:
            True se executou com sucesso, False se falhou
        """
        handler_name = handler.__name__

        try:
            logger.debug("⚙️ Executando handler: %s", handler_name)
            await handler(event)

            # 📊 Atualiza estatísticas
            self._stats[event.event_type]["handlers_executed"] += 1

            logger.debug("✅ Handler executado com sucesso: %s", handler_name)
            return True

        except Exception as e:
            # 📊 Atualiza estatísticas de falha
            self._stats[event.event_type]["handlers_failed"] += 1

            logger.error(
                "❌ Erro no handler %s para evento %s: %s",
                handler_name,
                event.event_type,
                str(e),
                exc_info=True,  # 🔍 Inclui stack trace completo
            )

            # 💡 Aqui você pode integrar com Sentry ou outro monitoring
            # await self._report_to_monitoring(e, handler_name, event)

            return False

    def get_handlers(self, event_type: str) -> list[EventHandler]:
        """
        📋 Retorna lista de handlers para um evento

        Útil para debugging e testes!
        """
        return self._handlers.get(event_type, []).copy()

    def get_stats(self, event_type: str | None = None) -> dict[str, Any]:
        """
        📊 Retorna estatísticas do Event Bus

        Args:
            event_type: Se especificado, retorna stats de um evento específico
                       Se None, retorna stats de todos os eventos

        Returns:
            Dicionário com estatísticas
        """
        if event_type:
            return self._stats.get(event_type, {}).copy()

        return dict(self._stats)

    def clear_handlers(self, event_type: str | None = None) -> None:
        """
        🧹 Remove handlers

        Args:
            event_type: Se especificado, remove apenas handlers deste evento
                       Se None, remove todos os handlers
        """
        if event_type:
            if event_type in self._handlers:
                del self._handlers[event_type]
                logger.info("🧹 Handlers removidos para: %s", event_type)
        else:
            self._handlers.clear()
            logger.info("🧹 Todos os handlers removidos")

    def __repr__(self) -> str:
        """Representação amigável do Event Bus"""
        total_handlers = sum(len(handlers) for handlers in self._handlers.values())
        return (
            f"EventBus("
            f"event_types={len(self._handlers)}, "
            f"total_handlers={total_handlers}"
            f")"
        )
