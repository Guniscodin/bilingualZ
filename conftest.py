"""Shared test configuration.

Also a safety net: no test may touch the network, a real translation engine, or
the user's actual data directory. The CI image has argostranslate installed, so
without this a translate-mode test would try to download a 100 MB model.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def isolate_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("BILINGUALZ_TRANSLATOR", "null")
    monkeypatch.setenv("BILINGUALZ_HOME", str(tmp_path / "home"))
    for key in (
        "BILINGUALZ_AZURE_KEY",
        "BILINGUALZ_AZURE_REGION",
        "BILINGUALZ_AZURE_ENDPOINT",
        "ARGOS_CHUNK_TYPE",
    ):
        monkeypatch.delenv(key, raising=False)
    yield
