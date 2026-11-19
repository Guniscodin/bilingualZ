"""Machine translation adapters.

Used only in translate mode, where we generate the second language ourselves so
that alignment is exact rather than guessed. Nothing here is used by parallel
mode, which stays fully offline and dependency free.
"""

from .base import Translator, NullTranslator
from .cache import CachedTranslator
from .factory import get_translator, available_translators

__all__ = [
    "Translator",
    "NullTranslator",
    "CachedTranslator",
    "get_translator",
    "available_translators",
]
