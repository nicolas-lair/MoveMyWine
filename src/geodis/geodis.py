from pathlib import Path

import pandas as pd

from src.cost_calculator.transporter import AbstractTransporter
from src.constant import UnitType, TarifType, CSV_PARAMS


class GeodisPackaging:
    def __init__(self, packages: int = 0, palets: int = 0):
        self.packages = packages
        self.palets = palets


class GeodisFixedCost:
    position = 0
    security = 0.7

    # palet_return = 1

    @property
    def total_cost(self):
        return self.position + self.security


class VariableCostCalculator:
    def __init__(self, max_palet_weight: int = 600, package_weight: int = 8):
        data_folder = Path(r"../data/stef")
        self.tarif_structure = pd.read_csv(
            data_folder / "tarif_structure.csv",
            **CSV_PARAMS,
            index_col=["Unité"]
        )
        self.tarif_dep = pd.read_csv(
            data_folder / "tarif_par_departement.csv",
            **CSV_PARAMS,
            index_col=["Département"]
        )
        self.max_palet_weight = max_palet_weight
        self.package_weight = package_weight
        self.bottle_by_package = 6

    @property
    def max_bottles(self) -> int:
        return self.tarif_structure.loc[UnitType.BOTTLE, "Max"].max()

    @property
    def max_bottles_in_palet(self) -> int:
        return (self.max_palet_weight * self.bottle_by_package) // self.package_weight

    def _get_container_type(self, n_bottles: int):
        self.tarif_structure

    def _get_tarif_id(self, unit: UnitType, volume: int) -> pd.Series:
        tarif_type = self.tarif_structure.loc[unit]
        return tarif_type[(tarif_type.Min <= volume) & (tarif_type.Max >= volume)]

    def _batch_compute(self, unit: UnitType, volume: int) -> pd.Series:
        tarif = self._get_tarif_id(unit=unit, volume=volume)
        cost = self.tarif_dep[tarif.Tarif.item()].to_frame(volume)
        if tarif.Type.item() == TarifType.VARIABLE:
            cost *= volume
        return cost

    def compute(self, dep_destination: int, n_bottles: int) -> float:
        bottle_cost = self._batch_compute(unit=UnitType.BOTTLE, volume=n_bottles)
        palet_cost = self._batch_compute(unit=UnitType.PALET, volume=n_palets)
        cost = bottle_cost + palet_cost
        if dep_destination is not None:
            stef_dep = f"FR{dep_destination}"
            cost = cost.loc[stef_dep]
        return cost

    def compute_packaging(self, n_bottles: int):
        if n_bottles < self.max_bottles:
            return StefPackaging(n_bottles=n_bottles)

    def compute_bottle_cost_nationwide(self, n_bottles: int):
        return self._batch_compute(unit=UnitType.BOTTLE, volume=n_bottles)

    def compute_palet_cost_nationwide(self, n_palets: int):
        return self._batch_compute(unit=UnitType.PALET, volume=n_palets)


class GasModulation:
    def __init__(self):
        data_folder = Path(r"../data/stef")
        self.gas_modulation = pd.read_csv(data_folder / "gas_modulation.csv",
                                          **CSV_PARAMS
                                          )
        self.gas_modulation["Modulation"] = (
            self.gas_modulation
            .Modulation
            .str.replace("%", "")
            .astype(int)
            .div(100)
            .add(1)
        )

    def get_modulation_factor(self, gas_price: float):
        min_condition = self.gas_modulation.Min <= gas_price
        max_condition = self.gas_modulation.Max >= gas_price
        return self.gas_modulation.loc[min_condition & max_condition, "Modulation"].item()


class Geodis(AbstractTransporter):
    def __init__(self):
        self.gas_modulator = GasModulation()
        self.var_cost_calc = VariableCostCalculator()
        max_bottles = self.var_cost_calc.max_bottles
        self.bottle_cost = pd.concat(
            [self.var_cost_calc.compute_bottle_cost_nationwide(n_bottles=i) for i in range(max_bottles + 1)],
            axis=1
        )

        self.palet_cost = pd.concat(
            [self.var_cost_calc.compute_palet_cost_nationwide(n_palets=i) for i in range(11)],
            axis=1
        )

    @property
    def fixed_cost(self):
        return SteffFixedCost().total_cost

    @staticmethod
    def _get_dept_code(department: str) -> str:
        return f"FR{department}"

    def get_total_cost(self, department: str, gas_price: float = 1.40) -> pd.DataFrame:
        df = self.bottle_cost.loc[self._get_dept_code(department)].T
        df *= self.gas_modulator.get_modulation_factor(gas_price)
        df += self.fixed_cost
        return df

    def get_cost_by_bottle(self, department: str, gas_price: float) -> pd.DataFrame:
        return super().get_cost_by_bottle(department=department, gas_price=gas_price)
