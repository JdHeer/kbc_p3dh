"""
Ingest KBC P3DH data into a SQLite database.

Reads the CSV data files and Excel mapping files, then writes:
  - `mapping` table  (datapoint metadata from EBA Annotated Table Layouts)
  - `raw_data` table (datapoint, factValue, file  from all k_*.csv files)
  - `mapped_data` table (pre-joined: raw + mapping, ready for dashboard)

Usage:
    uv run python ingest.py          # writes kbc_p3dh.db in project root
    uv run python ingest.py --db mydata.db   # custom output path
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import pandas as pd

from kbc_p3dh.loader import load_raw_data, DATA_DIR, TEMPLATE_GROUPS, get_template_group
from kbc_p3dh.mapping import build_mapping

DB_DEFAULT = Path(__file__).resolve().parent / "kbc_p3dh.db"


def ingest(db_path: Path = DB_DEFAULT) -> None:
    """Run the full ingestion pipeline."""
    print(f"📦 Ingesting data into {db_path} …")

    # ── 1. Build mapping from Excel ──────────────────────────────────────────
    print("  → Parsing EBA mapping files …")
    mapping = build_mapping()
    print(f"    {len(mapping):,} datapoint definitions")

    # ── 2. Load raw CSV data ─────────────────────────────────────────────────
    print("  → Loading CSV data files …")
    raw = load_raw_data(DATA_DIR)
    print(f"    {len(raw):,} raw data rows from {raw['file'].nunique()} files")

    # ── 3. Merge → mapped_data ───────────────────────────────────────────────
    print("  → Merging raw data with mapping …")
    merged = raw.merge(mapping, on="datapoint", how="left")
    merged["factNumeric"] = pd.to_numeric(merged["factValue"], errors="coerce")
    merged["group"] = merged["file"].apply(get_template_group)
    unmatched = merged["template"].isna().sum()
    print(f"    {len(merged):,} merged rows ({unmatched} unmatched)")

    # ── 4. Write to SQLite ───────────────────────────────────────────────────
    print("  → Writing SQLite database …")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    con = sqlite3.connect(str(db_path))

    mapping.to_sql("mapping", con, index=False, if_exists="replace")
    raw.to_sql("raw_data", con, index=False, if_exists="replace")
    merged.to_sql("mapped_data", con, index=False, if_exists="replace")

    # Create indexes for fast dashboard queries
    con.execute("CREATE INDEX IF NOT EXISTS idx_mapped_file ON mapped_data(file)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_mapped_dp ON mapped_data(datapoint)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_mapped_group ON mapped_data('group')")
    con.execute("CREATE INDEX IF NOT EXISTS idx_mapping_dp ON mapping(datapoint)")

    con.close()

    size_mb = db_path.stat().st_size / (1024 * 1024)
    print(f"  ✅ Done — {db_path.name} ({size_mb:.1f} MB)")
    print(f"     Tables: mapping ({len(mapping):,}), raw_data ({len(raw):,}), mapped_data ({len(merged):,})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest P3DH data into SQLite")
    parser.add_argument("--db", type=Path, default=DB_DEFAULT, help="Output database path")
    args = parser.parse_args()
    ingest(args.db)
