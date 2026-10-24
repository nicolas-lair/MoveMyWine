# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run all tests
uv run pytest

# Run a single test file
uv run pytest test/my_transporters/geodis/test_cost.py

# Run a single test
uv run pytest test/test_app.py::test_app

# Lint (ruff version is pinned once, in pyproject.toml; pre-commit and CI both use it)
ruff check src/ test/
ruff check --fix src/ test/

# Format
ruff format src/ test/

# Run the Streamlit app locally
streamlit run src/streamlit_app.py

# Pre-commit hooks (runs uv-export, uv-lock, ruff)
pre-commit run --all-files
```

## Deployment

The app runs on Streamlit Cloud from the public GitHub repo:
- `main` → [movemywine.streamlit.app](https://movemywine.streamlit.app)
- `develop` → [movemywine-dev.streamlit.app](https://movemywine-dev.streamlit.app)

Streamlit Cloud reads `requirements.txt` directly, which is why it is auto-exported via the `uv-export` pre-commit hook on every commit. **Never skip pre-commit hooks.**

Branch strategy: `feat/*` → `develop` → `main`.

## Architecture

This is a Streamlit web app that computes wine transport prices. Users select a transporter, enter destination and bottle quantities, and get a cost breakdown.

### Design Philosophy

The library is built around **modularity and composition over inheritance**. The goal is to make adding a new transporter as easy as possible by reusing existing building blocks:
- Unit cost calculators are small, focused, and reusable across transporters
- Protocols are preferred over base classes (inheritance is avoided unless clearly warranted)
- Each transporter assembles its own combination of cost components and modulators

### Transporter Pattern

Each transporter lives under `src/my_transporters/{name}/` and has four files:
- **`constant.py`** — `TransporterParams` dataclass with pricing config (modulators, fixed costs, zone surcharges)
- **`cost.py`** — Cost calculator classes implementing `BaseCostCalculator` protocol
- **`app_calculator.py`** — `TransporterApp` implementation that wires Streamlit session state to cost computation
- **`indicator_scrapper.py`** — Scrapes live fuel/cold surcharge indicators from transporter websites

Current transporters: `stef`, `chronopost`, `geodis`, `kuehne_nagel`.

`geodis` exposes two offers shown as separate transporters in the app: **Geodis Messagerie** (priced per bottle) and **Geodis Palette** (Résopal, priced per palet, 1–2 palets max). They share one package: `GeodisParams` holds common params, `MessagerieParams` / `PaletteParams` the offer-specific ones, and `build_total_cost()` assembles both calculators. Tarif data lives in `data/geodis/{messagerie,palette}/`; files common to both offers stay in `data/geodis/`.

**To add a new transporter**, create the four files above, then manually register it in `src/streamlit_app.py` in the transporter list.

### Cost Calculation Flow

```
TotalCostCalculator
├── BaseCostList         → aggregates per-unit costs (bottle, package, destination, expedition)
└── ModCostCollection   → applies percentage surcharges (GNR fuel, cold storage)
                           using CSV lookup tables (ModulatorFromIndicator)
```

Each cost calculator returns a `DetailedCost: dict[CostType, float]`. `CostType` enum is in `src/cost_calculator/constant.py`.

### Data Files

Per-transporter CSV files in `data/{transporter}/`:
- `tarif_structure.csv` — base pricing tiers
- `tarif_par_zone.csv` / `tarif_par_departement.csv` — zone/department rates
- `correspondance_zone_dpt.csv` — zone → department mapping
- `modulation_{indicator}.csv` — lookup tables for surcharge modulation

`src/file_structure.py` defines the expected CSV column names.

These files are updated manually when carriers send updated Excel or PDF tariff documents. An LLM can help convert those documents into the expected CSV format.

### Key Abstractions

- `SingleRefExpedition` / `MultiRefExpedition` (`src/cost_calculator/expedition.py`) — represent a shipment
- `BaseCostCalculator` protocol — any cost component implements `name: CostType` and `compute_cost()`
- `TransporterApp` protocol (`src/app_generics/transporter_app.py`) — interface all transporter apps implement
- Streamlit session state is managed in `src/streamlit_utils.py`; cache is cleared on month boundaries to refresh scraped indicators

### Baqio import

`src/baqio/` lets the user fill the expedition form from Baqio (wine ERP) orders — the 50 most recent uninvoiced orders are fetched once per session ("Recharger Baqio" refetches), the product catalogue is fetched in a background thread right after, and orders are picked in a multiselect; typing a text not in the list and pressing Enter searches Baqio for it: `client.py` (HTTP client), `order.py` (parsing 75 cl / magnum lines), `destination.py` (postal code → destination entry), `app.py` (Streamlit widget "Importer depuis Baqio", rendered right after `#### Expédition`, before the inputs it fills; loading happens in the `on_change` callbacks of the order multiselect and main-recipient radio, because widget keys cannot be written after their widget is declared).

The widget is hidden unless `.streamlit/secrets.toml` has a `[baqio]` section:

```toml
[baqio]
user = "..."
password = "..."
base_url = "https://app.baqio.com/api/v1"  # optional
```

### Testing

`test/test_app.py` is a **non-regression test** for the Streamlit layer — it is the main safety net for the fragile UI code. It uses Streamlit's `AppTest`, mocking indicator scrapers and the postal code API. Always keep it green and extend it when adding a new transporter.

Transporter-specific unit tests live in `test/my_transporters/{name}/`.

**Reliability by transporter**: `stef` and `geodis` are the actively used and best-tested ones. `chronopost` and `kuehne_nagel` are not currently in use and may contain bugs.
