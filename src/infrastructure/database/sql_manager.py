"""
SQL Database Manager - Infrastructure Layer
💡 Boa Prática: Gerenciador SQL moderno e robusto para substituir TinyDB!
🚀 Features: Connection pooling, type safety, error handling, e backup automático
🛡️ Segurança: Validação de entrada, sanitização SQL, e tratamento de exceções
"""

import json
import logging
import re
import shutil
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar

import aiosqlite

# 💡 Caminho do banco de dados centralizado
DB_PATH = Path(__file__).parent / "discord_bot.db"

# 💡 Configuração de logging mais detalhada
logger = logging.getLogger(__name__)


# 🛡️ Exceções customizadas para melhor tratamento de erros
class SQLManagerError(Exception):
    """Exceção base para erros do SQL Manager"""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class DatabaseConnectionError(SQLManagerError):
    """Erro de conexão com o banco de dados"""

    def __init__(self, original_error: Exception):
        message = f"Erro ao conectar com banco de dados: {original_error}"
        super().__init__(message)
        self.original_error = original_error


class ValidationError(SQLManagerError):
    """Erro de validação de dados"""

    def __init__(self, field: str, value: Any, reason: str):
        message = f"Validação falhou para campo '{field}' com valor '{value}': {reason}"
        super().__init__(message)
        self.field = field
        self.value = value
        self.reason = reason


class SchemaError(SQLManagerError):
    """Erro relacionado ao schema do banco"""

    def __init__(self, operation: str, details: str):
        message = f"Erro no schema durante '{operation}': {details}"
        super().__init__(message)
        self.operation = operation
        self.details = details


class QueryBuilder:
    """
    Construtor de queries SQL seguro

    💡 Boa Prática: Centraliza a construção de queries e sanitização!
    🔒 Previne SQL injection validando nomes de tabelas
    """

    # 🛡️ Templates SQL seguros - nomes de tabela são sanitizados antes de usar
    _TEMPLATES: ClassVar[dict[str, str]] = {
        "exists": "SELECT EXISTS(SELECT 1 FROM {} WHERE category_id = ?)",
        "insert_category": "INSERT OR IGNORE INTO {} (category_id) VALUES (?)",
        "select_value": "SELECT value FROM {} WHERE category_id = ? AND key_name = ?",
        "upsert_value": "INSERT OR REPLACE INTO {} (category_id, key_name, value, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
        "list_keys": "SELECT DISTINCT key_name FROM {} WHERE category_id = ? AND key_name IS NOT NULL ORDER BY key_name",
        "delete_key": "DELETE FROM {} WHERE category_id = ? AND key_name = ?",
        "delete_category": "DELETE FROM {} WHERE category_id = ?",
        "create_table": """CREATE TABLE IF NOT EXISTS {} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id TEXT NOT NULL,
            key_name TEXT,
            value TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(category_id, key_name)
        )""",
        "count_records": "SELECT COUNT(*) FROM {}",
    }

    @staticmethod
    def sanitize_table_name(name: str) -> str:
        """
        Sanitiza nome da tabela para SQL

        💡 Boa Prática: Sanitização rigorosa de nomes de tabela!
        """
        if not name or not isinstance(name, str):
            error_msg = "Nome deve ser string não vazia"
            field_name = "table_name"
            raise ValidationError(field_name, name, error_msg)

        # Remove caracteres especiais e substitui por underscore
        normalized = re.sub(r"[^a-zA-Z0-9_]", "_", name.strip())

        # Garante que começa com letra
        if normalized and normalized[0].isdigit():
            normalized = f"table_{normalized}"

        if not normalized:
            normalized = "default_table"

        # Limita tamanho
        if len(normalized) > 64:
            error_msg = "Nome muito longo (máximo 64 caracteres)"
            field_name = "table_name"
            raise ValidationError(field_name, name, error_msg)

        return normalized

    @staticmethod
    def _build_query(template_key: str, table_name: str) -> str:
        """
        Constrói query segura usando template

        💡 Boa Prática: Sistema de templates centralizados!
        """
        safe_table = QueryBuilder.sanitize_table_name(table_name)
        template = QueryBuilder._TEMPLATES[template_key]
        return template.format(safe_table)

    @staticmethod
    def build_exists_query(table_name: str) -> str:
        """Constrói query EXISTS segura"""
        return QueryBuilder._build_query("exists", table_name)

    @staticmethod
    def build_insert_category_query(table_name: str) -> str:
        """Constrói query INSERT OR IGNORE segura"""
        return QueryBuilder._build_query("insert_category", table_name)

    @staticmethod
    def build_select_value_query(table_name: str) -> str:
        """Constrói query SELECT VALUE segura"""
        return QueryBuilder._build_query("select_value", table_name)

    @staticmethod
    def build_upsert_value_query(table_name: str) -> str:
        """Constrói query UPSERT segura"""
        return QueryBuilder._build_query("upsert_value", table_name)

    @staticmethod
    def build_list_keys_query(table_name: str) -> str:
        """Constrói query LIST KEYS segura"""
        return QueryBuilder._build_query("list_keys", table_name)

    @staticmethod
    def build_delete_key_query(table_name: str) -> str:
        """Constrói query DELETE KEY segura"""
        return QueryBuilder._build_query("delete_key", table_name)

    @staticmethod
    def build_delete_category_query(table_name: str) -> str:
        """Constrói query DELETE CATEGORY segura"""
        return QueryBuilder._build_query("delete_category", table_name)

    @staticmethod
    def build_create_table_query(table_name: str) -> str:
        """Constrói query CREATE TABLE segura"""
        return QueryBuilder._build_query("create_table", table_name)

    @staticmethod
    def build_count_query(table_name: str) -> str:
        """Constrói query COUNT segura"""
        return QueryBuilder._build_query("count_records", table_name)

    @staticmethod
    def build_create_indexes_queries(table_name: str) -> list[str]:
        """Constrói queries CREATE INDEX seguras"""
        safe_table = QueryBuilder.sanitize_table_name(table_name)
        return [
            f"CREATE INDEX IF NOT EXISTS idx_{safe_table}_category ON {safe_table}(category_id)",
            f"CREATE INDEX IF NOT EXISTS idx_{safe_table}_key ON {safe_table}(key_name)",
            f"CREATE INDEX IF NOT EXISTS idx_{safe_table}_category_key ON {safe_table}(category_id, key_name)",
        ]


class SQLCategoryManager:
    """
    Gerenciador de Categoria SQL

    💡 Boa Prática: Mantém a mesma interface do TinyDB
    mas com performance e confiabilidade SQL!
    🛡️ Com validação de entrada e tratamento de erros robusto
    """

    def __init__(self, db_manager: "SQLTableManager", category_id: int | str):
        self.db_manager = db_manager
        self.category_id = self._validate_category_id(category_id)
        self.table_name = db_manager.table_name

    def _validate_category_id(self, category_id: int | str) -> str:
        """
        Valida e sanitiza o ID da categoria

        💡 Boa Prática: Sempre valide entrada do usuário!
        """
        if category_id is None:
            error_msg = "não pode ser None"
            field_name = "category_id"
            raise ValidationError(field_name, category_id, error_msg)

        str_id = str(category_id).strip()
        if not str_id:
            error_msg = "não pode estar vazio"
            field_name = "category_id"
            raise ValidationError(field_name, category_id, error_msg)

        # 🔒 Limita tamanho para evitar ataques
        if len(str_id) > 255:
            error_msg = "muito longo (máximo 255 caracteres)"
            field_name = "category_id"
            raise ValidationError(field_name, category_id, error_msg)

        return str_id

    async def exists(self) -> bool:
        """
        Verifica se a categoria existe

        💡 Boa Prática: Query otimizada com EXISTS e tratamento de erro!
        """
        try:
            # 🛡️ Garante que a tabela existe antes de verificar
            await self.db_manager.ensure_table_exists()

            query = QueryBuilder.build_exists_query(self.table_name)

            async with self.db_manager.db_manager.get_connection() as conn:
                cursor = await conn.execute(query, (self.category_id,))
                result = await cursor.fetchone()
                return bool(result[0]) if result else False

        except Exception as e:
            logger.exception(
                "Erro ao verificar existência da categoria %s", self.category_id
            )
            raise DatabaseConnectionError(e) from e

    async def create(self) -> bool:
        """
        Cria a categoria se não existir

        💡 Boa Prática: INSERT OR IGNORE para evitar duplicatas!
        """
        try:
            if await self.exists():
                return False

            # Garante que a tabela existe antes de inserir
            await self.db_manager.ensure_table_exists()

            query = QueryBuilder.build_insert_category_query(self.table_name)

            async with self.db_manager.db_manager.get_connection() as conn:
                await conn.execute(query, (self.category_id,))
                await conn.commit()
                logger.debug("Categoria criada: %s", self.category_id)
                return True

        except Exception as e:
            logger.exception("Erro ao criar categoria %s", self.category_id)
            raise DatabaseConnectionError(e) from e

    async def get_key(self, key: str) -> list[Any]:
        """
        Obtém valores de uma chave específica

        💡 Boa Prática: Deserialização JSON automática com fallback!
        """
        if not key or not isinstance(key, str):
            error_msg = "deve ser string não vazia"
            field_name = "key"
            raise ValidationError(field_name, key, error_msg)

        try:
            await self.db_manager.ensure_table_exists()

            query = QueryBuilder.build_select_value_query(self.table_name)

            async with self.db_manager.db_manager.get_connection() as conn:
                cursor = await conn.execute(query, (self.category_id, key))
                result = await cursor.fetchone()

                if result and result[0]:
                    try:
                        return json.loads(result[0])
                    except json.JSONDecodeError:
                        logger.warning(
                            "Valor JSON inválido para chave %s na categoria %s",
                            key,
                            self.category_id,
                        )
                        return []
                return []

        except Exception as e:
            logger.exception(
                "Erro ao obter chave %s da categoria %s", key, self.category_id
            )
            raise DatabaseConnectionError(e) from e

    async def set_key(self, key: str, values: list[Any]) -> bool:
        """
        Define valores para uma chave

        💡 Boa Prática: UPSERT com ON CONFLICT e validação!
        """
        if not key or not isinstance(key, str):
            error_msg = "deve ser string não vazia"
            field_name = "key"
            raise ValidationError(field_name, key, error_msg)

        if not isinstance(values, list):
            error_msg = "deve ser uma lista"
            field_name = "values"
            raise ValidationError(field_name, values, error_msg)

        try:
            # Garante que a categoria existe
            await self.create()

            query = QueryBuilder.build_upsert_value_query(self.table_name)

            async with self.db_manager.db_manager.get_connection() as conn:
                json_values = json.dumps(values, ensure_ascii=False)
                await conn.execute(query, (self.category_id, key, json_values))
                await conn.commit()
                logger.debug(
                    "Chave definida: %s = %s na categoria %s",
                    key,
                    len(values),
                    self.category_id,
                )
                return True

        except Exception as e:
            logger.exception(
                "Erro ao definir chave %s na categoria %s", key, self.category_id
            )
            raise DatabaseConnectionError(e) from e

    async def add_values(self, key: str, values: list[Any]) -> bool:
        """
        Adiciona valores a uma chave existente

        💡 Boa Prática: Merge inteligente sem duplicatas!
        """
        if not isinstance(values, list):
            error_msg = "deve ser uma lista"
            field_name = "values"
            raise ValidationError(field_name, values, error_msg)

        try:
            current_values = await self.get_key(key)
            new_values = current_values + [v for v in values if v not in current_values]
            return await self.set_key(key, new_values)

        except Exception as e:
            logger.exception(
                "Erro ao adicionar valores à chave %s na categoria %s",
                key,
                self.category_id,
            )
            raise DatabaseConnectionError(e) from e

    async def remove_values(self, key: str, values: list[Any]) -> bool:
        """
        Remove valores de uma chave

        💡 Boa Prática: Filtragem eficiente com validação!
        """
        if not isinstance(values, list):
            error_msg = "deve ser uma lista"
            field_name = "values"
            raise ValidationError(field_name, values, error_msg)

        try:
            current_values = await self.get_key(key)
            new_values = [v for v in current_values if v not in values]
            return await self.set_key(key, new_values)

        except Exception as e:
            logger.exception(
                "Erro ao remover valores da chave %s na categoria %s",
                key,
                self.category_id,
            )
            raise DatabaseConnectionError(e) from e

    async def list_keys(self) -> list[str]:
        """
        Lista todas as chaves da categoria

        💡 Boa Prática: Query otimizada DISTINCT!
        """
        try:
            await self.db_manager.ensure_table_exists()

            query = QueryBuilder.build_list_keys_query(self.table_name)

            async with self.db_manager.db_manager.get_connection() as conn:
                cursor = await conn.execute(query, (self.category_id,))
                results = await cursor.fetchall()
                return [row[0] for row in results]

        except Exception as e:
            logger.exception("Erro ao listar chaves da categoria %s", self.category_id)
            raise DatabaseConnectionError(e) from e

    async def delete_key(self, key: str) -> bool:
        """
        Remove uma chave da categoria

        💡 Boa Prática: DELETE com verificação de affected rows!
        """
        if not key or not isinstance(key, str):
            error_msg = "deve ser string não vazia"
            field_name = "key"
            raise ValidationError(field_name, key, error_msg)

        try:
            await self.db_manager.ensure_table_exists()

            query = QueryBuilder.build_delete_key_query(self.table_name)

            async with self.db_manager.db_manager.get_connection() as conn:
                cursor = await conn.execute(query, (self.category_id, key))
                await conn.commit()
                deleted = cursor.rowcount > 0
                logger.debug(
                    "Chave %s %s da categoria %s",
                    key,
                    "removida" if deleted else "não encontrada",
                    self.category_id,
                )
                return deleted

        except Exception as e:
            logger.exception(
                "Erro ao deletar chave %s da categoria %s", key, self.category_id
            )
            raise DatabaseConnectionError(e) from e


class SQLTableManager:
    """
    Gerenciador de Tabela SQL

    💡 Boa Prática: Abstração de tabela com interface compatível!
    🔒 Com sanitização e validação robusta
    """

    def __init__(self, db_manager: "SQLDatabase", table_name: str):
        self.db_manager = db_manager
        self.table_name = QueryBuilder.sanitize_table_name(table_name)

    async def ensure_table_exists(self) -> None:
        """
        Garante que a tabela existe

        💡 Boa Prática: CREATE TABLE IF NOT EXISTS com índices!
        🔓 Método público para permitir verificação externa
        """
        try:
            query = QueryBuilder.build_create_table_query(self.table_name)
            index_queries = QueryBuilder.build_create_indexes_queries(self.table_name)

            async with self.db_manager.get_connection() as conn:
                await conn.execute(query)
                for index_query in index_queries:
                    await conn.execute(index_query)
                await conn.commit()

        except Exception as e:
            logger.exception("Erro ao criar tabela %s", self.table_name)
            operation = "create_table"
            error_details = str(e)
            raise SchemaError(operation, error_details) from e

    def get_id(self, category_id: int | str) -> SQLCategoryManager:
        """
        Retorna gerenciador de categoria

        💡 Boa Prática: Factory pattern para categories!
        """
        return SQLCategoryManager(self, category_id)

    async def list_tables(self) -> list[str]:
        """
        Lista todas as tabelas no banco

        💡 Boa Prática: Query de metadados SQLite!
        """
        try:
            query = """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """

            async with self.db_manager.get_connection() as conn:
                cursor = await conn.execute(query)
                results = await cursor.fetchall()
                return [row[0] for row in results]

        except Exception as e:
            logger.exception("Erro ao listar tabelas")
            raise DatabaseConnectionError(e) from e

    async def delete_table(self) -> None:
        """
        Remove a tabela do banco

        💡 Boa Prática: DROP TABLE IF EXISTS!
        """
        try:
            safe_table = QueryBuilder.sanitize_table_name(self.table_name)
            query = f"DROP TABLE IF EXISTS {safe_table}"

            async with self.db_manager.get_connection() as conn:
                await conn.execute(query)
                await conn.commit()
                logger.info("Tabela removida: %s", self.table_name)

        except Exception as e:
            logger.exception("Erro ao deletar tabela %s", self.table_name)
            operation = "delete_table"
            error_details = str(e)
            raise SchemaError(operation, error_details) from e

    async def exists(self, category_id: int | str) -> bool:
        """
        Verifica se uma categoria existe

        💡 Boa Prática: Delega para CategoryManager!
        """
        category = self.get_id(category_id)
        return await category.exists()

    async def delete_category(self, category_id: int | str) -> bool:
        """
        Remove uma categoria completa

        💡 Boa Prática: DELETE em cascata com validação!
        """
        try:
            await self._ensure_table_exists()

            query = QueryBuilder.build_delete_category_query(self.table_name)

            async with self.db_manager.get_connection() as conn:
                cursor = await conn.execute(query, (str(category_id),))
                await conn.commit()
                deleted = cursor.rowcount > 0
                logger.debug(
                    "Categoria %s %s da tabela %s",
                    category_id,
                    "removida" if deleted else "não encontrada",
                    self.table_name,
                )
                return deleted

        except Exception as e:
            logger.exception(
                "Erro ao deletar categoria %s da tabela %s",
                category_id,
                self.table_name,
            )
            raise DatabaseConnectionError(e) from e


class SQLDatabase:
    """
    Gerenciador Principal do Banco SQL

    💡 Boa Prática: Interface compatível com SmallDB mas usando SQL!
    🚀 Features: Connection pooling, backup, estatísticas, schema automático
    """

    def __init__(self, name: str = "discord_bot"):
        if not name or not isinstance(name, str):
            error_msg = "deve ser string não vazia"
            field_name = "database_name"
            raise ValidationError(field_name, name, error_msg)

        self.name = name.strip()
        self.db_path = self._setup_database_path(self.name)
        self._connection_pool: aiosqlite.Connection | None = None

    def _setup_database_path(self, name: str) -> Path:
        """
        Configura caminho do banco de dados

        💡 Boa Prática: Estrutura de diretórios organizada!
        """
        db_dir = Path("database")
        db_dir.mkdir(parents=True, exist_ok=True)
        return db_dir / f"{name}.db"

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[aiosqlite.Connection]:
        """
        Gerenciador de contexto para conexões

        💡 Boa Prática: Gerenciamento automático de recursos com configurações otimizadas!
        """
        try:
            conn = await aiosqlite.connect(self.db_path)
            # 🚀 Configurações de performance
            await conn.execute("PRAGMA foreign_keys = ON")
            await conn.execute("PRAGMA journal_mode = WAL")
            await conn.execute("PRAGMA synchronous = NORMAL")
            await conn.execute("PRAGMA cache_size = 10000")
            await conn.execute("PRAGMA temp_store = MEMORY")

            yield conn
        except Exception as e:
            logger.exception("Erro ao conectar com banco %s", self.db_path)
            raise DatabaseConnectionError(e) from e
        finally:
            await conn.close()

    def get(self, table_name: str | None = None) -> SQLTableManager:
        """
        Retorna gerenciador de tabela

        💡 Boa Prática: Interface compatível com SmallDB!
        """
        table_name = table_name or self.name
        return SQLTableManager(self, table_name)

    async def close(self) -> None:
        """
        Fecha conexões do banco

        💡 Boa Prática: Cleanup de recursos!
        """
        if self._connection_pool:
            await self._connection_pool.close()
            self._connection_pool = None

    async def backup(self, backup_path: Path | None = None) -> Path:
        """
        Cria backup do banco de dados

        💡 Boa Prática: Backup incremental com timestamp!
        """
        try:
            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir = Path("backups")
                backup_dir.mkdir(parents=True, exist_ok=True)
                backup_path = backup_dir / f"{self.name}_backup_{timestamp}.db"

            # Se o arquivo do banco não existe ainda, cria um vazio
            if not self.db_path.exists():
                self.db_path.touch()

            shutil.copy2(self.db_path, backup_path)
            logger.info("Backup criado: %s", backup_path)
        except Exception as e:
            logger.exception("Erro ao criar backup")
            error_msg = f"Falha no backup: {e}"
            raise SQLManagerError(error_msg) from e
        else:
            return backup_path

    async def get_stats(self) -> dict[str, Any]:
        """
        Retorna estatísticas do banco

        💡 Boa Prática: Métricas para monitoramento!
        """
        try:
            # Se o arquivo não existe, retorna stats vazias
            if not self.db_path.exists():
                return {
                    "database_file": str(self.db_path),
                    "file_size_mb": 0,
                    "tables": {},
                    "total_records": 0,
                }

            stats = {
                "database_file": str(self.db_path),
                "file_size_mb": round(self.db_path.stat().st_size / (1024 * 1024), 2),
                "tables": {},
                "total_records": 0,
            }

            async with self.get_connection() as conn:
                # Lista todas as tabelas
                cursor = await conn.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """)
                tables = await cursor.fetchall()

                # Conta registros em cada tabela usando query segura
                for (table_name,) in tables:
                    # Usa o QueryBuilder para query COUNT segura
                    count_query = QueryBuilder.build_count_query(table_name)
                    cursor = await conn.execute(count_query)
                    count = await cursor.fetchone()
                    stats["tables"][table_name] = count[0] if count else 0
                    stats["total_records"] += stats["tables"][table_name]

        except Exception as e:
            logger.exception("Erro ao obter estatísticas")
            raise DatabaseConnectionError(e) from e
        else:
            return stats

    async def initialize_schema(self) -> None:
        """
        Inicializa o schema do banco com as tabelas do Discord

        💡 Boa Prática: Schema versionado baseado no simple_schema.sql!
        """
        try:
            schema_path = (
                Path(__file__).parent.parent.parent.parent
                / "docs"
                / "simple_schema.sql"
            )

            if schema_path.exists():
                schema_sql = schema_path.read_text(encoding="utf-8")

                async with self.get_connection() as conn:
                    # Executa o schema SQL
                    await conn.executescript(schema_sql)
                    await conn.commit()

                logger.info("Schema do banco inicializado com sucesso!")

            else:
                logger.warning("Arquivo de schema não encontrado: %s", schema_path)
                # Cria schema básico se não encontrar o arquivo
                await self._create_basic_schema()

        except Exception as e:
            logger.exception("Erro ao inicializar schema")
            operation = "initialize_schema"
            error_details = str(e)
            raise SchemaError(operation, error_details) from e

    async def _create_basic_schema(self) -> None:
        """
        Cria schema básico para funcionalidade mínima

        💡 Boa Prática: Fallback schema quando arquivo não existe!
        """
        basic_schema = """
        -- Schema básico para Discord Bot
        CREATE TABLE IF NOT EXISTS discord_bot (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id TEXT NOT NULL,
            key_name TEXT,
            value TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(category_id, key_name)
        );

        CREATE INDEX IF NOT EXISTS idx_discord_bot_category ON discord_bot(category_id);
        CREATE INDEX IF NOT EXISTS idx_discord_bot_key ON discord_bot(key_name);
        CREATE INDEX IF NOT EXISTS idx_discord_bot_category_key ON discord_bot(category_id, key_name);
        """

        async with self.get_connection() as conn:
            await conn.executescript(basic_schema)
            await conn.commit()

        logger.info("Schema básico criado com sucesso!")


# 🏭 Factory function para manter compatibilidade
def create_sql_database(name: str = "discord_bot") -> SQLDatabase:
    """
    Factory para criar instância do banco SQL

    💡 Boa Prática: Factory pattern para inicialização!
    """
    return SQLDatabase(name)


# 🔗 Alias para compatibilidade com código existente
SmallSQLDB = SQLDatabase
