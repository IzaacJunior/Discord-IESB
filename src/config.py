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

# � Banco de Dados de Auditoria (separado!)
# 💡 Boa Prática: Banco separado para logs de auditoria
AUDIT_DB_PATH = SRC_ROOT / "infrastructure" / "database" / "auditoria.db"

# �📄 Scripts SQL
# 💡 Para adicionar novos scripts, basta adicionar aqui!
SQL_SCRIPTS_PATH = SRC_ROOT / "infrastructure" / "database"
UNIQUE_CHANNELS_SQL = SQL_SCRIPTS_PATH / "create_unique_channels_tables.sql"

# 🎯 Outras configurações
# 💡 Adicione aqui qualquer path ou configuração que precise centralizar!

# 🎮 Configurações do Bot
# 💡 Prefix do bot e status personalizado
COMMAND_PREFIX = "!"  # Prefixo para comandos tradicionais
BOT_STATUS_TEXT = "Sistema NÃO oficial do IESB"  # Status que aparece no perfil do bot

# 🎮 Configurações de Salas Temporárias
# 💡 Valores padrão para salas temporárias (antes buscados do banco)
DEFAULT_TEMP_ROOM_LIMIT = 10  # Limite padrão de membros em salas temporárias
TEMP_ROOM_PREFIX = "🎮"  # Prefixo visual para salas temporárias
MAX_VOICE_CHANNEL_USERS = 99  # Limite máximo de usuários em canal de voz
TEMP_ROOM_EMPTY_TIMEOUT = 3  # Segundos para aguardar antes de deletar sala vazia

# 📝 Configurações de Canais Únicos (Fóruns)
# 💡 Valores padrão para fóruns privados de membros
UNIQUE_CHANNEL_PREFIX = "📝"  # Prefixo para fóruns privados de membros
MAX_CHANNEL_NAME_LENGTH = 100  # Comprimento máximo para nome de canal

# 📊 Configurações de Logs
# 💡 Nível de log padrão para o bot
DEFAULT_LOG_LEVEL = "INFO"  # Nível de log padrão (DEBUG/INFO/WARNING/ERROR)

# 🧹 Configurações de Limpeza de Mensagens
# 💡 Limites para comando de limpeza
DEFAULT_CLEAR_LIMIT = 100  # Limite padrão de mensagens a limpar
MAX_CLEAR_LIMIT = 100  # Limite máximo de mensagens permitidas
CLEAR_HISTORY_LIMIT = 50  # Histórico de mensagens a verificar

# 👥 Configurações de Tamanho de Servidor
# 💡 Limiares para adaptar comportamento baseado no tamanho
SMALL_GUILD_SIZE = 50  # Servidores pequenos
MEDIUM_GUILD_SIZE = 200  # Servidores médios
LARGE_GUILD_SIZE = 500  # Servidores grandes

# 📈 Configurações de Estatísticas
# 💡 Milestones para badges/achievements
STAT_MILESTONES = [10, 50, 100, 500, 1000]  # Marcos para estatísticas
FIRST_ROOM_MILESTONE = 1  # Primeiro canal criado
TEN_ROOMS_MILESTONE = 10  # 10 canais criados
HUNDRED_ROOMS_MILESTONE = 100  # 100 canais criados

# ⏱️ Configurações de Timing
# 💡 Delays e timeouts para operações
BOT_SHUTDOWN_DELAY = 1  # Segundos para aguardar antes de desligar
DATABASE_CACHE_SIZE = 10000  # Tamanho do cache SQLite PRAGMA

# 🎯 Configurações de Pattern Matching
# 💡 Valores para decision making com pattern matching
SMALL_GUILD_THRESHOLD = 100  # Limite para servidores pequenos (< 100 membros)
LARGE_GUILD_THRESHOLD = 500  # Limite para servidores grandes (>= 500 membros)


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
