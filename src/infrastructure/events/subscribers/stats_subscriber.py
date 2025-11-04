"""
📈 Stats Subscriber - Atualiza estatísticas de usuários
💡 Boa Prática: Subscriber dedicado para métricas de usuário!
"""

import logging
from collections import defaultdict

from domain.events import DomainEvent

logger = logging.getLogger(__name__)


class UserStatsSubscriber:
    """
    📈 Subscriber para estatísticas de usuários

    Mantém contadores e métricas sobre ações dos usuários
    no sistema (salas criadas, comandos executados, etc).

    💡 Boa Prática: Estatísticas isoladas em subscriber próprio
    facilitam adição de novas métricas sem afetar core!

    Examples:
        >>> stats = UserStatsSubscriber()
        >>> event_bus.subscribe("temp_room_created", stats.on_temp_room_created)
    """

    def __init__(self) -> None:
        """Inicializa subscriber de estatísticas"""
        # 💡 Usa defaultdict para facilitar contadores
        self.user_stats: dict[int, dict[str, int]] = defaultdict(
            lambda: {
                "rooms_created": 0,
                "rooms_deleted": 0,
                "commands_executed": 0,
                "total_room_time_seconds": 0,
            }
        )
        logger.info("📈 Stats Subscriber inicializado")

    async def on_temp_room_created(self, event: DomainEvent) -> None:
        """
        📈 Atualiza contador de salas criadas

        Args:
            event: Evento com dados da sala criada
        """
        try:
            owner_id = event.data.get("owner_id")

            if not owner_id:
                logger.warning("⚠️ Evento sem owner_id, ignorando stats")
                return

            # + Incrementa contador
            self.user_stats[owner_id]["rooms_created"] += 1

            total_rooms = self.user_stats[owner_id]["rooms_created"]

            logger.info(
                "📈 Stats atualizadas: usuário %s criou %d sala(s) no total",
                owner_id,
                total_rooms,
            )

            # 💡 Futuro: Persistir stats no banco de dados para análise histórica

            # 🏆 Verifica conquistas baseadas em stats
            if total_rooms == 1:
                logger.info("🏆 Primeira sala do usuário %s!", owner_id)
            elif total_rooms == 10:
                logger.info("🏆 Usuário %s criou 10 salas!", owner_id)
            elif total_rooms == 100:
                logger.info("🏆 Usuário %s criou 100 salas! 🎉", owner_id)

        except Exception:
            logger.exception("❌ Erro ao atualizar stats de criação")

    async def on_temp_room_deleted(self, event: DomainEvent) -> None:
        """
        📈 Atualiza contador de salas deletadas e tempo total

        Args:
            event: Evento com dados da sala deletada
        """
        try:
            owner_id = event.data.get("owner_id")
            duration = event.data.get("duration_seconds", 0)

            if not owner_id:
                return

            # + Incrementa contadores
            self.user_stats[owner_id]["rooms_deleted"] += 1
            self.user_stats[owner_id]["total_room_time_seconds"] += duration

            stats = self.user_stats[owner_id]

            logger.info(
                "📈 Stats atualizadas: usuário %s - %d deletadas, %d segundos totais",
                owner_id,
                stats["rooms_deleted"],
                stats["total_room_time_seconds"],
            )

        except Exception:
            logger.exception("❌ Erro ao atualizar stats de exclusão")

    async def on_command_executed(self, event: DomainEvent) -> None:
        """
        📈 Atualiza contador de comandos executados

        Args:
            event: Evento com dados do comando
        """
        try:
            user_id = event.data.get("user_id")

            if not user_id:
                return

            # + Incrementa contador
            self.user_stats[user_id]["commands_executed"] += 1

            total_commands = self.user_stats[user_id]["commands_executed"]

            logger.info(
                "📈 Stats atualizadas: usuário %s executou %d comando(s)",
                user_id,
                total_commands,
            )

            # 🏆 Marcos de comandos
            if total_commands in [10, 50, 100, 500, 1000]:
                logger.info(
                    "🏆 Usuário %s atingiu %d comandos executados!",
                    user_id,
                    total_commands,
                )

        except Exception:
            logger.exception("❌ Erro ao atualizar stats de comando")

    def get_user_stats(self, user_id: int) -> dict[str, int]:
        """
        📊 Retorna estatísticas de um usuário

        Args:
            user_id: ID do usuário

        Returns:
            Dicionário com estatísticas do usuário
        """
        return self.user_stats[user_id].copy()

    def get_top_users(
        self, metric: str = "rooms_created", limit: int = 10
    ) -> list[tuple[int, int]]:
        """
        🏆 Retorna top usuários por métrica

        Args:
            metric: Métrica para ranking (ex: "rooms_created")
            limit: Número de usuários a retornar

        Returns:
            Lista de tuplas (user_id, value) ordenadas
        """
        rankings = [
            (user_id, stats[metric]) for user_id, stats in self.user_stats.items()
        ]

        # 🔽 Ordena do maior para menor
        rankings.sort(key=lambda x: x[1], reverse=True)

        return rankings[:limit]
