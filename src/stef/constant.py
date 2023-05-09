from src.constant import DATA_FOLDER


class TransporterParams:
    name = "Stef"
    max_palet_weight = 600

    expedition_cost = dict(
        position=5.2,
        security=0.7
    )

    data_folder = DATA_FOLDER / name.lower()
