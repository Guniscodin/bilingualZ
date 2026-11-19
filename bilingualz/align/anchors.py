"""User anchors.

An anchor is a pair of indices the user asserts are the same chunk. The engine
treats every anchor as hard truth: it aligns the gap before an anchor, emits
the anchor verbatim with score 1.0, then continues after it. That means a single
nudge repairs only one stretch of the document, never the whole thing.
"""

from __future__ import annotations

from .. import config
from ..models import Pair
from . import length_dp


def _normalise(forced: list[tuple[int, int]], n: int, m: int) -> list[tuple[int, int]]:
    cleaned: list[tuple[int, int]] = []
    for a, b in sorted((int(a), int(b)) for a, b in forced):
        a = min(max(a, 0), max(n - 1, 0))
        b = min(max(b, 0), max(m - 1, 0))
        if cleaned:
            pa, pb = cleaned[-1]
            if a <= pa or b <= pb:      # must advance on both sides to stay monotone
                continue
        cleaned.append((a, b))
    return cleaned


def align_with_anchors(
    en: list[str],
    pt: list[str],
    forced: list[tuple[int, int]] | None = None,
    *,
    band: int | None = None,
) -> list[Pair]:
    """Align two documents, honouring the user's hard anchors."""
    n, m = len(en), len(pt)
    if n == 0 or m == 0:
        return []

    width = config.DP_BAND if band is None else band
    anchors = _normalise(list(forced or []), n, m)

    pairs: list[Pair] = []
    ei = pi = 0

    for a, b in anchors:
        gap_en = list(range(ei, a))
        gap_pt = list(range(pi, b))

        if gap_en and gap_pt:
            pairs.extend(length_dp.align(en[ei:a], pt[pi:b], band=width, offset=(ei, pi)))
            pairs.append(Pair([a], [b], 1.0))
        elif gap_en:
            pairs.append(Pair(gap_en + [a], [b], 0.40))
        elif gap_pt:
            pairs.append(Pair([a], gap_pt + [b], 0.40))
        else:
            pairs.append(Pair([a], [b], 1.0))
        ei, pi = a + 1, b + 1

    # Whatever is left after the final anchor. When only one side has segments
    # left, fold them into the previous pair instead of inventing a partner
    # index that is already taken.
    if ei < n and pi < m:
        pairs.extend(length_dp.align(en[ei:], pt[pi:], band=width, offset=(ei, pi)))
    elif ei < n and pairs:
        pairs[-1].en.extend(range(ei, n))
    elif pi < m and pairs:
        pairs[-1].pt.extend(range(pi, m))

    return pairs


def anchor_for_pair(pair: Pair) -> tuple[int, int] | None:
    """Turn "this pair is correct" into an anchor at its first index."""
    if not pair.en or not pair.pt:
        return None
    return pair.en[0], pair.pt[0]


def nudge(
    en: list[str],
    pt: list[str],
    forced: list[tuple[int, int]],
    pair: Pair,
    delta: int,
) -> list[tuple[int, int]]:
    """Return an updated anchor list that shifts this pair's PT side by delta."""
    anchor = anchor_for_pair(pair)
    if anchor is None or delta == 0:
        return list(forced)

    a, b = anchor
    b = min(max(b + int(delta), 0), len(pt) - 1)

    updated = [(x, y) for x, y in forced if x != a]
    updated.append((a, b))
    updated.sort()
    return _normalise(updated, len(en), len(pt))
