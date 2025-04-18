import pickle
from pathlib import Path


class GetSet:
    def __init__(self, ruta: str) -> None:
        self.doc = {}
        self.filer: Path = Path("data") / f"{ruta}.pkl"
        self.filer.parent.mkdir(parents=True, exist_ok=True)
        if not self.filer.exists():
            self.filer.touch()  # Cria o arquivo se ele não existir

    def __get(self) -> dict[int, dict]:
        """Lê o conteúdo do arquivo e retorna como dicionário com chaves inteiras."""
        try:
            if self.filer.stat().st_size == 0:  # Verifica se o arquivo está vazio
                return {}
            with self.filer.open("rb") as filer:
                return pickle.load(filer)
        except Exception as e:
            print(f"Erro ao ler o arquivo: {e}")

    def set(self) -> None:
        """Escreve um dicionário no arquivo."""
        try:
            doc = self.__get().update(self.doc)
            with self.filer.open("wb") as filer:
                pickle.dump(doc, filer)
        except Exception as e:
            print(f"Erro ao escrever no arquivo: {e}")
            raise

    def is_exists(self, var) -> bool:
        """Verifica se a variável existe no dicionário."""
        return var in self.__get()
    
    def id(self) -> int:
        return max(self.__get.keys(), default=0) + 1

