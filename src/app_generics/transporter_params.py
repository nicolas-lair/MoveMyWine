from pathlib import Path
from src.constant import DATA_FOLDER


class AbstractTransporterParams:
    name: str

    expedition_cost = dict()
    monthly_cost = dict()

    @property
    def data_folder(self) -> Path:
        return DATA_FOLDER / self.name.lower()
