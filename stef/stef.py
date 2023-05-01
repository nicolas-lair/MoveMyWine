from pathlib import Path

import pandas as pd

from transporter import AbstractTransporter
from constant import UnitType, TarifType, FRENCH_CSV_PARAMS


class SteffFixedCost:
    position = 5.2
    security = 0.7

    # palet_return = 1

    @property
    def total_cost(self):
        return self.position + self.security


class VariableCostCalculator:
    def __init__(self):
        data_folder = Path(r"data/stef")
        self.tarif_structure = pd.read_csv(
            data_folder / "tarif_structure.csv",
            **FRENCH_CSV_PARAMS,
            index_col=["Unité"]
        )
        self.tarif_dep = pd.read_csv(
            data_folder / "tarif_par_departement.csv",
            **FRENCH_CSV_PARAMS,
            index_col=["Département"]
        )

    def _get_tarif_id(self, unit: UnitType, volume: int) -> pd.Series:
        tarif_type = self.tarif_structure.loc[unit]
        return tarif_type[(tarif_type.Min <= volume) & (tarif_type.Max >= volume)]

    def _batch_compute(self, unit: UnitType, volume: int) -> pd.Series:
        tarif = self._get_tarif_id(unit=unit, volume=volume)
        cost = self.tarif_dep[tarif.Tarif.item()].to_frame(volume)
        if tarif.Type.item() == TarifType.VARIABLE:
            cost *= volume
        return cost

    def compute(self, dep_destination: int, n_bottles: int = 0, n_palets: int = 0) -> float:
        bottle_cost = self._batch_compute(unit=UnitType.BOTTLE, volume=n_bottles)
        palet_cost = self._batch_compute(unit=UnitType.PALET, volume=n_palets)
        cost = bottle_cost + palet_cost
        if dep_destination is not None:
            stef_dep = f"FR{dep_destination}"
            cost = cost.loc[stef_dep]
        return cost

    def compute_bottle_cost_nationwide(self, n_bottles: int):
        return self._batch_compute(unit=UnitType.BOTTLE, volume=n_bottles)

    def compute_palet_cost_nationwide(self, n_palets: int):
        return self._batch_compute(unit=UnitType.PALET, volume=n_palets)


class Stef(AbstractTransporter):
    def __init__(self, gas_modulator: float = 1.13):
        self.gas_modulator = gas_modulator
        self.var_cost_calc = VariableCostCalculator()
        self.bottle_cost = pd.concat(
            [self.var_cost_calc.compute_bottle_cost_nationwide(n_bottles=i) for i in range(199)],
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
    def _get_dep_code(department: int) -> str:
        return f"FR{department}"

    def get_total_cost(self, department: int) -> pd.DataFrame:
        df = self.bottle_cost.loc[self._get_dep_code(department)].T
        df *= self.gas_modulator
        df += self.fixed_cost
        return df
