"""Configuration and output helpers."""

from __future__ import annotations

from pathlib import Path
import random
import numpy as np


def set_seed(seed: int) -> None:
    """Set deterministic seeds for reproducible synthetic experiments."""
    random.seed(seed)
    np.random.seed(seed)


def ensure_output_dirs(base_dir: str | Path = "outputs") -> dict[str, Path]:
    """Create local output folders and return their paths."""
    base = Path(base_dir)
    folders = {
        "base": base,
        "results": base / "results",
        "figures": base / "figures",
        "reports": base / "reports",
        "audit": base / "audit",
    }
    for folder in folders.values():
        folder.mkdir(parents=True, exist_ok=True)
    return folders
