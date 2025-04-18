from comun.getset import GetSet as gt
import time


class Loggin:
    """Classe principal para registro de logs."""

    def __init__(self, mensagem: dict) -> None:
        self.log_mensagen = mensagem
        print(mensagem)

    def log(self) -> None:
        """Registra uma mensagem de log."""
        self.__set_log(gt("log"))

    def log_error(self) -> None:
        """Registra uma mensagem de erro."""
        self.__set_log(gt("log_error"))

    def __set_log(self, filer: gt) -> None:
        """Registra a mensagem no arquivo de log."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        try:
            
            filer.doc[filer.id()] = {"timestamp": timestamp, "mensagem": self.log_mensagen}
            filer.set()
        except Exception as e:
            print(f"Erro ao registrar log: {e}")

