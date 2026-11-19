"""Pick a translation engine.

Selection order:
  1. explicit ``name`` argument
  2. ``BILINGUALZ_TRANSLATOR`` environment variable
  3. ``argos`` if installed, else ``azure`` if a key exists, else ``null``
"""

from __future__ import annotations

import importlib.util
import os

from .. import config
from .base import NullTranslator, Translator
from .cache import CachedTranslator


def _argos_available() -> bool:
    return importlib.util.find_spec("argostranslate") is not None


def _azure_available() -> bool:
    return bool(os.environ.get("BILINGUALZ_AZURE_KEY"))


def available_translators() -> dict[str, bool]:
    return {
        "argos": _argos_available(),
        "azure": _azure_available(),
    }


def get_translator(name: str | None = None) -> CachedTranslator:
    choice = (name or os.environ.get("BILINGUALZ_TRANSLATOR") or "").strip().lower()

    if not choice:
        if _argos_available():
            choice = "argos"
        elif _azure_available():
            choice = "azure"
        else:
            choice = "null"

    inner: Translator
    if choice == "argos":
        from .argos import ArgosTranslator

        inner = ArgosTranslator()
    elif choice == "azure":
        from .azure import AzureTranslator

        inner = AzureTranslator()
    elif choice == "null":
        inner = NullTranslator()
    else:
        raise RuntimeError(f"Unknown translator: {choice}")

    return CachedTranslator(inner, config.translate_cache_dir())
