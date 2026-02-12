"""Entry point for `uv run dashboard`."""

import sys
from pathlib import Path


def main() -> None:
    # Ensure the repo root is on sys.path so Streamlit can find dashboard.py
    root = str(Path(__file__).resolve().parents[2])
    from streamlit.web.cli import main as st_main

    sys.argv = ["streamlit", "run", str(Path(root) / "dashboard.py"), "--server.headless", "true"]
    st_main()
