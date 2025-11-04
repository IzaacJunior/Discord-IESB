"""
📊 Database Audit Logger - Sistema de Auditoria com Banco Separado
💡 Boa Prática: Logs de auditoria em banco separado para melhor segurança e organização!
🚀 Python 3.13: Type hints modernos e async/await otimizado
"""

import contextlib
import json
import logging
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from queue import Empty, Queue
from typing import Any

import colorlog

from config import AUDIT_DB_PATH

# 💡 Caminho do banco de auditoria importado do config.py centralizado!


class DatabaseLogHandler(logging.Handler):
    """
    🗄️ Handler customizado que salva logs em banco de dados SQLite separado.

    💡 Boa Prática: Usa thread separada para não bloquear a aplicação
    🔒 Segurança: Logs ficam isolados do banco de dados principal
    ✨ Features:
        - Thread-safe com Queue
        - Batch inserts para performance
        - Tratamento robusto de erros
        - Suporte a dados extras (extra_data JSON)

    Exemplo de uso:
        >>> audit_logger = logging.getLogger('audit')
        >>> audit_logger.addHandler(DatabaseLogHandler())
        >>> audit_logger.info('Usuário fez login', extra={'user_id': 123})
    """

    def __init__(
        self,
        level: int = logging.INFO,
        batch_size: int = 10,
        flush_interval: float = 5.0,
    ) -> None:
        """
        Inicializa o handler de logs para banco de dados.

        💡 Type hints completos para melhor documentação!

        Args:
            level: Nível mínimo de log a ser salvo (padrão: INFO)
            batch_size: Quantidade de logs para salvar em batch (padrão: 10)
            flush_interval: Intervalo em segundos para forçar flush (padrão: 5.0)
        """
        super().__init__(level)
        self.batch_size = batch_size
        self.flush_interval = flush_interval

        # 📦 Queue thread-safe para armazenar logs antes de salvar
        self.log_queue: Queue[dict[str, Any]] = Queue()

        # 🎯 Thread dedicada para salvar logs sem bloquear a aplicação
        self.worker_thread = threading.Thread(
            target=self._worker, daemon=True, name="AuditLogWorker"
        )
        self.worker_thread.start()

        # 🏗️ Garante que o banco e tabelas existem
        self._initialize_database()

    def _initialize_database(self) -> None:
        """
        �️ Inicializa o banco de dados de auditoria.

        💡 Boa Prática: Usa contextlib.suppress para ignorar erros de forma explícita
        🛡️ Segurança: Falhas não devem quebrar a aplicação principal
        """
        # � ALTERNATIVA 1: Usar contextlib.suppress para suprimir erros esperados
        with contextlib.suppress(sqlite3.Error, OSError, IOError):
            # Cria diretório se não existir
            AUDIT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

            # Lê o schema SQL
            schema_path = Path(__file__).parent / "auditoria_schema.sql"

            if schema_path.exists():
                with sqlite3.connect(AUDIT_DB_PATH) as conn:
                    with schema_path.open(encoding="utf-8") as f:
                        conn.executescript(f.read())
                    conn.commit()
            else:
                # 💡 Fallback: cria schema básico se arquivo não existir
                with sqlite3.connect(AUDIT_DB_PATH) as conn:
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS application_logs (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                            level TEXT NOT NULL,
                            logger_name TEXT NOT NULL,
                            message TEXT NOT NULL,
                            module TEXT,
                            function TEXT,
                            line_number INTEGER,
                            extra_data TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    conn.commit()

    def emit(self, record: logging.LogRecord) -> None:
        """
        📝 Adiciona log na fila para ser salvo no banco.

        💡 Boa Prática: Método não-bloqueante - apenas adiciona na queue!
        🔒 Thread-safe com Queue

        Args:
            record: Registro de log do Python logging
        """
        # 💡 Padronização: Usa contextlib.suppress para tratar erros
        # Se qualquer erro ocorrer, handleError() será chamado automaticamente
        with contextlib.suppress(Exception):
            # 📊 Extrai dados extras se existirem
            extra_data = {}
            for key, value in record.__dict__.items():
                # Ignora atributos padrão do LogRecord
                if key not in {
                    "name",
                    "msg",
                    "args",
                    "created",
                    "filename",
                    "funcName",
                    "levelname",
                    "levelno",
                    "lineno",
                    "module",
                    "msecs",
                    "message",
                    "pathname",
                    "process",
                    "processName",
                    "relativeCreated",
                    "thread",
                    "threadName",
                    "exc_info",
                    "exc_text",
                    "stack_info",
                    "taskName",
                }:
                    extra_data[key] = value

            # 🎁 Prepara dados para inserção
            log_data = {
                "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                "level": record.levelname,
                "logger_name": record.name,
                "message": self.format(record),
                "module": record.module,
                "function": record.funcName,
                "line_number": record.lineno,
                "extra_data": json.dumps(extra_data) if extra_data else None,
            }

            # 📦 Adiciona na fila (não bloqueia!)
            self.log_queue.put(log_data)
            return  # Sucesso - retorna normalmente

        # Se chegou aqui, houve erro - usa handleError() do logging
        self.handleError(record)

    def _worker(self) -> None:
        """
        👷 Thread worker que salva logs do queue no banco.

        💡 Boa Prática: Usa batch insert para melhor performance!
        🔁 Roda em loop infinito (daemon thread)
        """
        batch: list[dict[str, Any]] = []

        while True:
            # 💡 Padronização: Captura Empty com try-except específico
            # contextlib.suppress não funciona bem aqui pois precisamos do fluxo
            try:
                # 📦 Pega log da fila (bloqueia até ter um disponível)
                log_data = self.log_queue.get(timeout=self.flush_interval)
                batch.append(log_data)

                # 💾 Salva batch quando atingir o tamanho
                if len(batch) >= self.batch_size:
                    self._save_batch(batch)
                    batch = []

            except Empty:
                # ✅ Timeout esperado - força flush do batch atual
                if batch:
                    self._save_batch(batch)
                    batch = []

    def _save_batch(self, batch: list[dict[str, Any]]) -> None:
        """
        💾 Salva um lote de logs no banco de dados.

        💡 Boa Prática: Batch insert é muito mais eficiente!
        🔒 Usa transação para garantir consistência

        Args:
            batch: Lista de dicts com dados dos logs
        """
        if not batch:
            return

        # 💡 Padronização: Usa contextlib.suppress para suprimir erros de DB
        # Se falhar ao salvar, descarta o batch para não travar a thread
        with (
            contextlib.suppress(sqlite3.Error, OSError),
            sqlite3.connect(AUDIT_DB_PATH) as conn,
        ):
            cursor = conn.cursor()

            # 📝 Batch insert
            cursor.executemany(
                """
                INSERT INTO application_logs
                (timestamp, level, logger_name, message, module, function, line_number, extra_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        log["timestamp"],
                        log["level"],
                        log["logger_name"],
                        log["message"],
                        log["module"],
                        log["function"],
                        log["line_number"],
                        log["extra_data"],
                    )
                    for log in batch
                ],
            )

            conn.commit()

    def flush(self) -> None:
        """
        🚿 Força salvamento de todos os logs pendentes.

        💡 Útil ao encerrar a aplicação!
        """
        # Processa todos os logs restantes na fila
        remaining_logs = []
        while not self.log_queue.empty():
            # 💡 Padronização: Captura Empty com try-except específico
            # (contextlib.suppress não é ideal aqui pelo fluxo de controle)
            try:
                remaining_logs.append(self.log_queue.get_nowait())
            except Empty:
                # ✅ Queue está vazia - comportamento esperado
                break

        if remaining_logs:
            self._save_batch(remaining_logs)

        super().flush()

    def close(self) -> None:
        """
        🔒 Fecha o handler salvando logs pendentes.

        💡 Boa Prática: Sempre chamar ao encerrar a aplicação!
        """
        self.flush()
        super().close()


def get_audit_logger(name: str = "audit", level: int = logging.INFO) -> logging.Logger:
    """
    🎯 Factory function para criar logger de auditoria configurado.

    💡 Boa Prática: Usa factory pattern para simplificar criação!
    🔒 Logger isolado - não afeta outros loggers da aplicação

    Args:
        name: Nome do logger (padrão: 'audit')
        level: Nível mínimo de log (padrão: INFO)

    Returns:
        Logger configurado com DatabaseLogHandler

    Exemplo de uso:
        >>> audit_logger = get_audit_logger('meu_modulo')
        >>> audit_logger.info('Ação importante', extra={'user_id': 123})
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 🔍 Evita duplicação de handlers
    if not any(isinstance(h, DatabaseLogHandler) for h in logger.handlers):
        db_handler = DatabaseLogHandler(level=level)

        # 📝 Formato personalizado para logs de auditoria
        formatter = logging.Formatter(
            "%(levelname)s | %(name)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        db_handler.setFormatter(formatter)

        logger.addHandler(db_handler)

    # 🎨 Handler de console com cores específicas para o AUDIT
    # 💡 Garantimos um StreamHandler próprio para o logger de auditoria
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        console_handler = colorlog.StreamHandler()
        console_handler.setFormatter(
            colorlog.ColoredFormatter(
                "%(log_color)s%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
                datefmt="%H:%M:%S",
                log_colors={
                    "DEBUG": "cyan",
                    # 🔷 INFO do AUDIT em AZUL
                    "INFO": "blue",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "red,bg_white",
                },
            )
        )
        logger.addHandler(console_handler)

    # � Desliga propagação para evitar que o root aplique a mesma cor do logger padrão
    # ✅ Mantemos dual logging via handlers próprios (DB + Console colorido distinto)
    logger.propagate = False

    return logger


# 🎯 Logger de auditoria global pronto para uso
audit_logger = get_audit_logger("audit")
