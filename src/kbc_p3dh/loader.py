"""
Load KBC P3DH CSV data files and merge with the EBA datapoint mapping.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from kbc_p3dh.mapping import DATA_DIR, build_mapping


def load_raw_data(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """Read all k_*.csv files → single DataFrame with columns [datapoint, factValue, file]."""
    frames: list[pd.DataFrame] = []
    for csv_path in sorted(data_dir.glob("k_*.csv")):
        df = pd.read_csv(csv_path)
        df["file"] = csv_path.stem  # e.g. "k_60.00.a"
        frames.append(df)
    if not frames:
        raise FileNotFoundError(f"No k_*.csv files found in {data_dir}")
    return pd.concat(frames, ignore_index=True)


def load_mapped_data() -> pd.DataFrame:
    """Load CSV data and enrich with mapping metadata.

    Returns DataFrame with columns:
        datapoint, factValue, file, template, template_title,
        row_label, row_code, col_label, col_code, unit
    """
    raw = load_raw_data()
    mapping = build_mapping()

    # Filter mapping to only templates that have data files
    file_templates = set(raw["file"].str.upper().str.replace("K_", "K_"))
    # Merge on datapoint; keep all raw rows (left join)
    merged = raw.merge(mapping, on="datapoint", how="left")

    # Coerce factValue to numeric where possible (keep text as-is for qualitative)
    merged["factNumeric"] = pd.to_numeric(merged["factValue"], errors="coerce")

    return merged


# ── Convenience aggregations ──────────────────────────────────────────────────

# Friendly names for the EBA templates based on the file codes
TEMPLATE_GROUPS = {
    "Key Metrics (EU KM1)": ["K_61.00"],
    "RWA Overview (EU OV1)": ["K_60.00.a", "K_60.00.b"],
    "Capital Composition (EU CC1/CC2)": [
        "K_63.01.a", "K_63.01.b", "K_63.01.c", "K_63.01.d", "K_63.01.e",
    ],
    "Leverage & MREL (EU LR/TLAC)": [
        "K_63.02.a", "K_63.02.b", "K_63.02.c",
    ],
    "Credit Risk RWEA Flows (EU CR8)": ["K_28.00"],
    "Credit Risk (EU CR1)": ["K_07.00"],
    "Market Risk RWEA Flows (EU MR2-B)": ["K_12.00"],
    "IRRBB (EU IRRBB1)": ["K_68.00"],
    "Liquidity – LCR (EU LIQ1)": ["K_73.00.a", "K_73.00.b"],
    "Liquidity – NSFR (EU LIQ2)": ["K_73.00.c", "K_73.00.d", "K_73.00.e"],
    "Qualitative Disclosures": ["K_00.02"],
}


def get_template_group(file_stem: str) -> str:
    """Map a CSV file stem (e.g. 'k_61.00') to its friendly group name."""
    upper = file_stem.upper().replace("K_", "K_")
    for group, templates in TEMPLATE_GROUPS.items():
        if upper in [t.upper() for t in templates]:
            return group
    return file_stem
