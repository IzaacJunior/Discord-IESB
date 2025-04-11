from pathlib import Path
import json


class GetSet:
    def __init__(self, ruta: str) -> None:
        self.filer: Path = Path("json") / f"{ruta}.json" 
        if not self.filer.exists():
            self.filer.touch()  # Cria o arquivo se ele não existir

    def get(self) -> dict | dict[int, list[int]]:
        """Lê o conteúdo do arquivo JSON e retorna como dicionário."""
        try:
            dados: str = self.filer.read_text(encoding="utf-8").strip()
            if not dados:
                return {}
            # Converte o texto JSON em um dicionário
            data: dict = json.loads(dados)
            return {int(k): v for k, v in data.items() }

        except json.JSONDecodeError as e:
            print(f"Erro ao decodificar o JSON: {e}")
            return {}
        except Exception as e:
            print(f"Erro ao ler o arquivo: {e}")
            return {}

    def set(self, dados: dict) -> None:
        """Escreve um dicionário no arquivo JSON."""
        try:
            # Converte o dicionário em uma string JSON e escreve no arquivo
            self.filer.write_text(
                json.dumps(
                    dados, 
                    indent=4, 
                    ensure_ascii=False
                ), 
                encoding="utf-8"
            )
        except Exception as e:
            print(f"Erro ao escrever no arquivo: {e}")

