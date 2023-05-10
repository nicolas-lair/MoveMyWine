from src.constant import DATA_FOLDER


class TransporterParams:
    name = "Geodis"
    data_folder = DATA_FOLDER / name.lower()

    extra_package_cost = 0.55   # Frais multi-colis (par colis) - GEODS
    max_free_package = 10       # Nombre de colis max sans frais multi-colis - GEODIS
    multi_package_max_fee = 25  # Coût max de la gestion multi-colis - GEODIS

    expedition_cost = {
        "securite": 2.15

    }

    monthly_cost = {
        "facturation": 13,
    }
