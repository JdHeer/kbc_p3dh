# P3DH — EBA Pillar 3 Data Hub Fact Database

Universal ingestion tool that converts [EBA Pillar 3 Data Hub](https://www.eba.europa.eu/risk-and-data-analysis/pillar-3-data-hub) downloads into a single, queryable SQLite database — one row per reported value, across any entity and reporting period.

## Quick start

```bash
# Install dependencies (Python ≥ 3.12, managed by uv)
uv sync

# Ingest a P3DH download folder (auto-detects entity, period, module)
uv run python ingest_p3dh.py "P3DH downloads"

# Ingest multiple folders at once
uv run python ingest_p3dh.py "downloads/ABN_2025H1" "downloads/KBC_2025H1"

# Custom database path
uv run python ingest_p3dh.py --db mydata.db "P3DH downloads"
```

## How it works

1. **Auto-detect metadata** — reads `parameters.csv` and `report.json` from the download folder to determine entity (LEI), reporting period, and module (FINDIS, CODI, IRRBB, …).
2. **Parse EBA mapping** — loads the matching Annotated Table Layout Excel from `Mapping/` to get template names, row/column labels, and datapoint codes.
3. **Match CSV values** — reads all `k_*.csv` files and joins each value to its mapping definition via the EBA datapoint code.
4. **Write to SQLite** — inserts matched facts into `p3dh.db`. Re-running the same folder is idempotent (deletes existing entity + period + module first).

## Database schema

The `facts` table contains **21 columns**:

| Column | Description |
|---|---|
| `entity` | Short entity name (e.g. ABN AMRO, KBC Group) |
| `lei` | LEI code |
| `ref_period` | Reporting date (e.g. 2025-06-30) |
| `module` | EBA module (findis, codi, irrbb, …) |
| `currency` | Base currency |
| `template` | Template code (e.g. K 07.00) |
| `template_title` | Template title |
| `row_code` | Row code from mapping |
| `row_label` | Row label |
| `col_code` | Column code from mapping |
| `col_label` | Column label |
| `col_parent` | Parent column label |
| `col_header` | Top-level column header |
| `col_group` | Column group |
| `col_sub` | Column sub-group |
| `file` | Source CSV filename stem |
| `datapoint` | EBA datapoint code |
| `value` | Numeric value (EUR) |
| `value_raw` | Raw string value from CSV |
| `value_eur_m` | Value in EUR millions |
| `unit` | Unit (monetary, percentage, count, date) |

## Supported modules

FINDIS, CODI, IRRBB, ESG, GSII, MREL/TLAC, REM, P3DH.

## Pre-configured entities

ABN AMRO, KBC Group, ING Group, Rabobank, BNP Paribas, HSBC, Deutsche Bank, Goldman Sachs, Barclays, UBS. Additional LEIs are stored verbatim.

## Project structure

```
ingest_p3dh.py     # Ingestion script (single file, ~475 lines)
Mapping/           # EBA Annotated Table Layout Excel files (12 files)
pyproject.toml     # Project config (uv, Python ≥ 3.12, openpyxl)
```

## Requirements

- Python ≥ 3.12
- [uv](https://docs.astral.sh/uv/) package manager
- Only runtime dependency: `openpyxl`
