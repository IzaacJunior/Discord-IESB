"""
🧹 Log Cleanup Manager - Limpeza Automática de Logs Antigos
⚡ CRÍTICO: Previne crescimento infinito do banco de auditoria
💡 Boa Prática: Thread separada para não bloquear a aplicação

Data: 8 de novembro de 2025
"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path

import aiosqlite

logger = logging.getLogger(__name__)
audit = logging.getLogger("audit")


class LogCleanupManager:
    """
    🧹 Gerenciador de limpeza automática de logs antigos.

    💡 Boa Prática: Task async que roda em background
    🔒 Thread-safe com asyncio
    ✨ Features:
        - Limpeza automática baseada em política
        - Preservação de logs críticos
        - Relatório detalhado de limpeza
        - Recuperação automática de erros
    """

    def __init__(
        self,
        db_path: Path,
        cleanup_interval_hours: int = 24,
        batch_size: int = 1000,
    ) -> None:
        """
        Inicializa o gerenciador de limpeza.

        Args:
            db_path: Caminho do banco de auditoria
            cleanup_interval_hours: Intervalo entre limpezas (padrão: 24h)
            batch_size: Quantidade de registros a deletar por vez
        """
        self.db_path = db_path
        self.cleanup_interval = timedelta(hours=cleanup_interval_hours)
        self.batch_size = batch_size
        self.last_cleanup: datetime | None = None
        self.is_running = False

    async def start_cleanup_loop(self) -> None:
        """
        ♻️ Inicia loop de limpeza automática.

        Roda indefinidamente verificando se é hora de fazer limpeza.
        """
        self.is_running = True
        logger.info("🧹 Iniciando serviço de limpeza de logs...")

        while self.is_running:
            try:
                # Verifica se é hora de fazer limpeza
                now = datetime.now()
                if (
                    self.last_cleanup is None
                    or (now - self.last_cleanup) >= self.cleanup_interval
                ):
                    await self.cleanup_expired_logs()
                    self.last_cleanup = now

                # Aguarda antes de próxima verificação (1 hora)
                await asyncio.sleep(3600)

            except asyncio.CancelledError:
                logger.info("🧹 Limpeza de logs cancelada")
                self.is_running = False
                break
            except Exception:
                logger.exception("❌ Erro na limpeza automática de logs")
                # Aguarda antes de tentar novamente
                await asyncio.sleep(3600)

    async def cleanup_expired_logs(self) -> None:
        """
        🗑️ Remove logs expirados baseado na política de retenção.

        Deleta logs em lotes para não sobrecarregar o banco.
        """
        if not self.db_path.exists():
            logger.warning(f"Banco de auditoria não encontrado: {self.db_path}")
            return

        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Busca política de retenção
                cursor = await db.execute("""
                    SELECT level, days_to_keep
                    FROM audit_retention_policy
                    ORDER BY days_to_keep DESC
                """)
                policies = await cursor.fetchall()

                if not policies:
                    logger.warning("⚠️ Nenhuma política de retenção configurada")
                    return

                total_deleted = 0
                cleanup_details = {}

                # Processa cada nível de log
                for level, days_to_keep in policies:
                    try:
                        deleted_count = await self._delete_logs_by_level(
                            db, level, days_to_keep
                        )
                        total_deleted += deleted_count
                        cleanup_details[level] = deleted_count

                        if deleted_count > 0:
                            logger.debug(f"🗑️ {deleted_count} logs {level} deletados")

                    except Exception:
                        logger.exception(f"❌ Erro ao limpar logs {level}")

                # Log de auditoria com detalhes
                if total_deleted > 0:
                    audit.info(
                        f"infrastructure.database.cleanup_manager | 🧹 {total_deleted} logs expirados deletados",
                        extra={
                            "total_deleted": total_deleted,
                            "details": cleanup_details,
                            "action": "cleanup_completed",
                        },
                    )

                    logger.info(f"✅ Limpeza concluída: {total_deleted} logs removidos")
                else:
                    logger.debug("i Info: nenhum log expirado para deletar")

                # Atualiza timestamp da última limpeza
                now = datetime.now().isoformat()
                await db.execute(
                    """
                    UPDATE audit_retention_policy
                    SET last_cleanup = ?
                    WHERE last_cleanup IS NULL OR last_cleanup < datetime('now', '-1 day')
                """,
                    (now,),
                )
                await db.commit()

        except Exception:
            logger.exception("❌ Erro ao fazer cleanup de logs")

    async def _delete_logs_by_level(
        self, db: aiosqlite.Connection, level: str, days_to_keep: int
    ) -> int:
        """
        🗑️ Deleta logs expirados de um nível específico em lotes.

        Args:
            db: Conexão com banco de dados
            level: Nível de log (DEBUG, INFO, etc)
            days_to_keep: Quantos dias manter

        Returns:
            Quantidade total de logs deletados
        """
        total_deleted = 0
        deleted_in_batch = self.batch_size

        # Delete em lotes para não sobrecarregar
        while deleted_in_batch >= self.batch_size:
            # Deleta um lote de logs antigos
            cursor = await db.execute(
                """
                DELETE FROM application_logs
                WHERE id IN (
                    SELECT id FROM application_logs
                    WHERE level = ?
                    AND timestamp < datetime('now', '-' || ? || ' days')
                    LIMIT ?
                )
            """,
                (level, days_to_keep, self.batch_size),
            )

            deleted_in_batch = cursor.rowcount
            total_deleted += deleted_in_batch

            await db.commit()

            if deleted_in_batch > 0:
                logger.debug(
                    f"🗑️ Lote de {deleted_in_batch} logs {level} deletados "
                    f"(total: {total_deleted})"
                )

        return total_deleted

    async def get_cleanup_stats(self) -> dict:
        """
        📊 Retorna estatísticas da limpeza.

        Returns:
            Dicionário com stats por nível de log
        """
        if not self.db_path.exists():
            return {}

        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT
                        level,
                        days_to_keep,
                        datetime(last_cleanup, 'localtime') as last_cleanup_local,
                        COUNT(*) as total_logs
                    FROM audit_retention_policy
                    LEFT JOIN application_logs ON audit_retention_policy.level = application_logs.level
                    GROUP BY audit_retention_policy.level
                    ORDER BY
                        CASE audit_retention_policy.level
                            WHEN 'CRITICAL' THEN 1
                            WHEN 'ERROR' THEN 2
                            WHEN 'WARNING' THEN 3
                            WHEN 'INFO' THEN 4
                            WHEN 'DEBUG' THEN 5
                        END
                """)

                stats = {}
                for level, days, last_cleanup, count in await cursor.fetchall():
                    stats[level] = {
                        "days_to_keep": days,
                        "last_cleanup": last_cleanup or "Nunca",
                        "current_logs": count or 0,
                    }

                return stats
        except Exception:
            logger.exception("❌ Erro ao obter stats de limpeza")
            return {}

    async def stop(self) -> None:
        """⏹️ Para o loop de limpeza."""
        self.is_running = False
        logger.info("🧹 Serviço de limpeza de logs parado")


# 🎯 Factory function para criar manager
def create_cleanup_manager(
    db_path: Path | None = None, cleanup_interval_hours: int = 24
) -> LogCleanupManager:
    """
    🏭 Factory function para criar LogCleanupManager.

    Args:
        db_path: Caminho do banco (se None, tenta importar de config)
        cleanup_interval_hours: Intervalo entre limpezas

    Returns:
        LogCleanupManager configurado e pronto para usar
    """
    if db_path is None:
        from config import AUDIT_DB_PATH

        db_path = AUDIT_DB_PATH

    return LogCleanupManager(db_path, cleanup_interval_hours)
