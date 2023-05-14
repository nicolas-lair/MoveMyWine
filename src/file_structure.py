from abc import ABC
from typing import Dict

from enum import Enum

from constant import CSV_PARAMS


class AbstractCols(str, Enum):
    pass


class CSVFile(ABC):
    name: str
    Cols: AbstractCols
    csv_format: Dict[str, str] = CSV_PARAMS


class TarifStructureFile(CSVFile):
    name = "tarif_structure.csv"

    class Cols(str, Enum):
        tarif = "Tarif"
        unit = "Unité"
        type_ = "Type"
        min_ = "Min"
        max_ = "Max"


class TarifDeptFile(CSVFile):
    name = "tarif_par_departement.csv"

    class Cols(str, Enum):
        dpt = "Département"


class GasModulationFile(CSVFile):
    name = "gas_modulation.csv"

    class Cols(str, Enum):
        min_price = "Min"
        max_price = "Max"
        modulation = "Modulation"


class TarifZoneFile(CSVFile):
    name = "tarif_par_zone.csv"

    class Cols(str, Enum):
        zone = "Zone"


class CorrespondanceZoneDpt(CSVFile):
    name = "correspondance_zone_dpt.csv"

    class Cols(str, Enum):
        zone = TarifZoneFile.Cols.zone.value
        dpt = TarifDeptFile.Cols.dpt.value
