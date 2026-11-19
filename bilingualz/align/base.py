"""The pluggable alignment interface.

``Aligner`` is the seam. Today there are two implementations:

* :mod:`bilingualz.align.length_dp` - scoring + monotone DP (parallel mode)
* :mod:`bilingualz.align.identity`  - index pairing (translate mode)

A future embedding-based aligner slots in here without touching the UI.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..models import Pair


@runtime_checkable
class Aligner(Protocol):
    """Two paragraph lists in, an ordered list of pairs out."""

    name: str

    def __call__(
        self,
        en: list[str],
        pt: list[str],
        forced: list[tuple[int, int]] | None = None,
    ) -> list[Pair]: ...
