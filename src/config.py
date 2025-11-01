"""
⚙️ Configuração Central do Projeto - IESB Discord Bot
💡 Boa Prática: Centralizar paths em um único lugar facilita manutenção!
🎯 Baixo Atrito: Mudanças só precisam ser feitas aqui!
"""

from pathlib import Path

#  Caminhos base do projeto
# 💡 PROJECT_ROOT é onde está o pyproject.toml
PROJECT_ROOT = Path(__file__).parent.parent
SRC_ROOT = Path(__file__).parent

# 🗄️ Banco de Dados
# 💡 Para mudar o local do banco, edite apenas esta linha!
DB_PATH = SRC_ROOT / "infrastructure" / "database" / "discord_bot.db"

# 📄 Scripts SQL
# 💡 Para adicionar novos scripts, basta adicionar aqui!
SQL_SCRIPTS_PATH = SRC_ROOT / "infrastructure" / "database"
UNIQUE_CHANNELS_SQL = SQL_SCRIPTS_PATH / "create_unique_channels_tables.sql"

# 🎯 Outras configurações
# 💡 Adicione aqui qualquer path ou configuração que precise centralizar!
# LOGS_PATH = PROJECT_ROOT / "logs"
# BACKUPS_PATH = PROJECT_ROOT / "backups"


def get_db_path() -> Path:
    """
    🎯 Retorna o caminho do banco de dados.
    
    💡 Boa Prática: Função getter permite validação e lógica adicional
    
    Returns:
        Path: Caminho absoluto do banco de dados
    """
    # 🔧 Cria diretório se não existir
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return DB_PATH.resolve()


def get_sql_script_path(script_name: str) -> Path:
    """
    📄 Retorna o caminho de um script SQL.
    
    Args:
        script_name: Nome do arquivo SQL
        
    Returns:
        Path: Caminho absoluto do script SQL
        
    Example:
        >>> get_sql_script_path("create_unique_channels_tables.sql")
    """
    return (SQL_SCRIPTS_PATH / script_name).resolve()

