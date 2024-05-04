from abc import ABC
from dataclasses import dataclass
from typing import Dict
from pathlib import Path
from enum import Enum

from src.constant import CSV_PARAMS


class AbstractCols(str, Enum):
    pass


class CSVFile(ABC):
    name: str
    Cols: AbstractCols
    csv_format: Dict[str, str] = CSV_PARAMS


class TarifStructureFile(CSVFile):
    name = "tarif_structure.csv"

    class Cols(str, Enum):
        tarif_id = "Tarif"
        tarif = "Tarif"
        unit = "Unité"
        type_ = "Type"
        min_ = "Min"
        max_ = "Max"


class TarifDeptFile(CSVFile):
    name = "tarif_par_departement.csv"

    class Cols(str, Enum):
        dpt = "Département"


@dataclass
class ModulationFileConfig(CSVFile):
    path: Path

    class Cols(str, Enum):
        lower_bound = "Min"
        upper_bound = "Max"
        modulation = "Modulation"


class TarifZoneFile(CSVFile):
    name = "tarif_par_zone.csv"

    class Cols(str, Enum):
        zone = "Zone"


class CorrespondanceZoneDpt(CSVFile):
    name = "correspondance_zone_dpt.csv"
    csv_format = {**CSVFile.csv_format, "dtype": str}

    class Cols(str, Enum):
        zone = TarifZoneFile.Cols.zone.value
        dpt = TarifDeptFile.Cols.dpt.value
