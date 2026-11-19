"""Application paths and alignment tunables.

Everything that a user might reasonably want to tune lives here so the engine
modules stay pure and testable.
"""

from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "Bilingualz"

# ---------------------------------------------------------------------------
# Alignment tunables (see align/length_dp.py for how they are used)
# ---------------------------------------------------------------------------
# Portuguese prose typically runs ~10% longer than the English original.
LENGTH_MU = 0.0953          # ln(1.10)
LENGTH_SIGMA = 0.28

# Half-width of the diagonal search corridor, in paragraphs.
DP_BAND = 40

# Pairs scoring below this are drawn with a dashed "check me" underline.
LOW_CONFIDENCE = 0.55

# Longest run of paragraphs a single aligned pair may cover (1-2 / 2-1 merges).
MAX_GROUP = 3


def app_home() -> Path:
    """Root of all user data. Override with BILINGUALZ_HOME for tests."""
    override = os.environ.get("BILINGUALZ_HOME")
    if override:
        root = Path(override).expanduser()
    else:
        try:
            from platformdirs import user_data_dir

            root = Path(user_data_dir(APP_NAME, APP_NAME))
        except Exception:  # platformdirs missing -> still usable
            root = Path.home() / ".bilingualz"
    root.mkdir(parents=True, exist_ok=True)
    return root


def docs_dir() -> Path:
    path = app_home() / "docs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def cache_dir() -> Path:
    path = app_home() / "cache"
    path.mkdir(parents=True, exist_ok=True)
    return path


def translate_cache_dir() -> Path:
    path = cache_dir() / "translate"
    path.mkdir(parents=True, exist_ok=True)
    return path
