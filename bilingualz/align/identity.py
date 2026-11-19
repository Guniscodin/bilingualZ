"""Alignment when the correspondence is not guessed but known.

In translate mode we machine-translate one paragraph at a time, so paragraph i
on the left is by construction the translation of paragraph i on the right.
"""

from __future__ import annotations

from ..models import Pair
from . import length_dp


def align_identity(en: list[str], pt: list[str]) -> list[Pair]:
    if len(en) == len(pt):
        return [Pair([i], [i], 1.0) for i in range(len(en))]
    # Should not happen, but never crash a document over it.
    return length_dp.align(en, pt)
