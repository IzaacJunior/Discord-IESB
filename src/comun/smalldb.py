import logging
from pathlib import Path
from typing import Any

from tinydb import TinyDB
from tinydb.operations import delete
from tinydb.operations import set as tinydb_set
from tinydb.table import Document, Table


class CategoryManager:
    """Gerencia uma categoria específica dentro de uma tabela."""

    def __init__(self, table: Table, category_id: int) -> None:
        """Inicializa o gerenciador de categoria."""
        self.table: Table = table
        self.category_id: int | str = category_id
        self.data: dict[str, Any] = self.table.get(doc_id=category_id) or {}

    def exists(self) -> bool:
        """Verifica se a categoria existe no banco de dados."""
        self.data = self.table.get(doc_id=self.category_id) or {}
        return self.data != {}

    def create(self) -> bool:
        """Cria a categoria se ela não existir."""
        if self.exists():
            return False
        self.table.insert(Document({}, doc_id=self.category_id))
        self.data = {}
        return True

    def get_key(self, key: str) -> list[Any]:
        """Obtém os valores de uma chave específica."""
        if not self.exists():
            return []
        self.data = self.table.get(doc_id=self.category_id) or {}
        return self.data.get(key, [])

    def set_key(self, key: str, values: list[Any]) -> bool:
        """Define os valores de uma chave."""

        self.table.update(tinydb_set(key, values), doc_ids=[self.category_id])
        self.data[key] = values
        return True

    def add_values(self, key: str, values: list[Any]) -> bool:
        """Adiciona valores a uma chave existente."""
        current_values: list[Any] = self.get_key(key)
        new_values: list[Any] = current_values + [
            v for v in values if v not in current_values
        ]
        return self.set_key(key, new_values)

    def remove_values(self, key: str, values: list[Any]) -> bool:
        """Remove valores de uma chave."""
        current_values: list[Any] = self.get_key(key)
        new_values: list[Any] = [v for v in current_values if v not in values]
        return self.set_key(key, new_values)

    def list_keys(self) -> list[str]:
        """Lista todas as chaves desta categoria."""
        return list(self.data.keys())

    def delete_key(self, key: str) -> bool:
        """Remove uma chave da categoria."""
        if not self.exists() or key not in self.data:
            return False

        # Usa a operação delete do TinyDB para remover a chave
        self.table.update(delete(key), doc_ids=[self.category_id])

        # Atualiza o cache local de dados
        if key in self.data:
            del self.data[key]

        return True


class TableManager:
    """Gerencia tabelas específicas dentro de um arquivo JSON."""

    def __init__(self, db: Path, db_name: str) -> None:
        """Inicializa o gerenciador de tabelas."""
        self.db: TinyDB = db
        # Cria uma nova tabela se não existir
        self.table = self.db.table(db_name)

    def get_id(self, id_category: int) -> CategoryManager:
        return CategoryManager(self.table, id_category)

    # lista todas as tabelas no banco de dados
    def list_tables(self) -> list[str]:
        """Lista todas as tabelas no banco de dados."""
        return self.db.tables()

    # deleta uma tabela do banco de dados
    def delete_table(self, table_name: str) -> None:
        """Remove uma tabela do banco de dados."""
        if table_name in self.db.tables():
            self.db.drop_table(table_name)

    def exists(self, id_category: int) -> bool:
        """Verifica se um id expecifico existe na tabela."""
        return self.table.contains(doc_id=id_category)

    def delete_category(self, category_id: int) -> bool:
        """Remove uma categoria do banco de dados."""
        if self.table.contains(doc_id=category_id):
            self.table.remove(doc_ids=[category_id])
            return True
        return False


class SmallDB:
    """Classe principal para gerenciar arquivos JSON e inicializar DatabaseManager."""

    def __init__(self, name: str = "json") -> None:
        """Inicializa o gerenciador de arquivos JSON."""
        self.name: str = name
        self.new_file(name)

    # Gera um novo arquivo JSON com o nome especificado
    def new_file(self, name: str) -> None:
        """
        Cria um novo arquivo JSON com tratamento robusto de erros.

        💡 Boa Prática: Tratamento de arquivos corrompidos e inicialização segura
        """
        import json

        new_path: Path = Path("json")
        new_path.mkdir(parents=True, exist_ok=True)
        json_file = new_path / f"{name}.json"

        # Verifica se o arquivo existe e se está válido
        if json_file.exists():
            try:
                # Tenta ler o arquivo para verificar se é um JSON válido
                with open(json_file, encoding="utf-8") as f:
                    content = f.read().strip()
                    if not content:
                        # Arquivo vazio, inicializa com JSON válido
                        with open(json_file, "w", encoding="utf-8") as f:
                            json.dump({}, f, indent=4)
                    else:
                        # Tenta fazer parse para verificar se é válido
                        json.loads(content)
            except (json.JSONDecodeError, UnicodeDecodeError, PermissionError) as e:
                # Arquivo corrompido, recria com conteúdo válido
                print(f"⚠️ Arquivo {json_file} corrompido, recriando: {e}")
                with open(json_file, "w", encoding="utf-8") as f:
                    json.dump({}, f, indent=4)
        else:
            # Arquivo não existe, cria com conteúdo válido
            json_file.touch(exist_ok=True)
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=4)

        try:
            self.db = TinyDB(json_file, indent=4, sort_keys=True)
        except Exception as e:
            # Se ainda assim falhar, tenta recriar o arquivo

            logging.exception(f"❌ Erro ao inicializar TinyDB, recriando arquivo: {e}")
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=4)
            self.db = TinyDB(json_file, indent=4, sort_keys=True)

    # Retorna uma instância de DatabaseManager para gerenciar tabelas
    def get(self, table: str | None) -> "TableManager":
        """Retorna uma instância de DatabaseManager para gerenciar tabelas."""
        return TableManager(self.db, table or self.name)
