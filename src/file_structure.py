from abc import ABC
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import ClassVar, Dict, Type

import pandas as pd

from src.constant import CSV_PARAMS


class AbstractCols(StrEnum):
    pass


class CSVFile(ABC):
    name: str
    Cols: Type[AbstractCols]
    csv_format: ClassVar[Dict[str, str]] = CSV_PARAMS

    def load(
        self, data_folder: Path, index_col: str | list[str] = None
    ) -> pd.DataFrame:
        return pd.read_csv(
            data_folder / self.name,
            **self.csv_format,
            index_col=index_col,
        )


class TarifStructureFile(CSVFile):
    name = "tarif_structure.csv"

    class Cols(AbstractCols):
        tarif_id = "Tarif"
        tarif = "Tarif"
        unit = "Unité"
        type_ = "Type"
        min_ = "Min"
        max_ = "Max"


class TarifDeptFile(CSVFile):
    name = "tarif_par_departement.csv"

    class Cols(AbstractCols):
        dpt = "Département"


@dataclass
class ModulationFileConfig(CSVFile):
    path: Path

    class Cols(AbstractCols):
        lower_bound = "Min"
        upper_bound = "Max"
        modulation = "Modulation"


class TarifZoneFile(CSVFile):
    name = "tarif_par_zone.csv"

    class Cols(AbstractCols):
        zone = "Zone"


class CorrespondanceZoneDpt(CSVFile):
    name = "correspondance_zone_dpt.csv"
    csv_format = {**CSVFile.csv_format, "dtype": str}

    class Cols(AbstractCols):
        zone = TarifZoneFile.Cols.zone
        dpt = TarifDeptFile.Cols.dpt


@dataclass(kw_only=True)
class MapZone2PostalCode(CSVFile):
    name: str

    class Cols(AbstractCols):
        zone = TarifZoneFile.Cols.zone
        destination = "Destination"

    csv_format = {**CSVFile.csv_format, "dtype": {Cols.destination: str}}
