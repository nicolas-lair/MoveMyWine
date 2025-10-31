from abc import ABC
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Dict

from src.constant import CSV_PARAMS


class AbstractCols(StrEnum):
    pass


class CSVFile(ABC):
    name: str
    Cols: AbstractCols
    csv_format: Dict[str, str] = CSV_PARAMS


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
