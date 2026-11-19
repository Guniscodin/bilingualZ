"""The v1 alignment engine: a banded monotone dynamic program.

Cost model
----------
Every candidate pair of chunks gets a cost. Lower is better.

* **Length ratio** - Portuguese runs slightly longer than English. A 1:1 pair
  whose lengths differ wildly from the expected ratio is expensive.
* **Numbers** - ``1755`` is ``1755`` in every language. Matching digit groups
  are strong evidence; mismatching ones are strong evidence against.
* **Proper nouns** - ``Lisbon``/``Lisboa`` share the stem ``lisb``.
* **Word stems** - shared 4-character prefixes (``destroyed``/``destruiu`` ->
  ``dest``). This is what makes EN<->PT alignment work without any dictionary.

The path through the ((n+1) x (m+1)) grid is monotone: only forward steps are
allowed (1-1, 1-2, 2-1, and up to 1-3 / 3-1 for heavier merges), so a paragraph
can never jump ahead. That constraint is what makes the output stable, and it
is why merges and splits come out as ``Pair([4, 5], [4])`` instead of silently
drifting.
"""

from __future__ import annotations

import math

from .. import config
from ..models import Pair
from .signals import Features, features, merge_features

_INF = float("inf")


def _moves(max_group: int | None = None) -> tuple[tuple[int, int], ...]:
    """Allowed DP steps: straight pairs plus bounded merges on either side."""
    limit = max(config.MAX_GROUP, max_group or config.MAX_GROUP)
    steps: list[tuple[int, int]] = []
    for size in range(1, limit + 1):
        for right in range(1, limit + 1):
            if size == 1 and right == 1:
                steps.append((1, 1))
            elif size == 1 or right == 1:
                steps.append((size, right))
    return tuple(steps)


_MOVES = _moves()


def _score(cost: float) -> float:
    """Map a raw cost onto 0..1 confidence."""
    centre = 0.35
    scale = 1.0
    try:
        return 1.0 / (1.0 + math.exp(-((centre - cost) / scale)))
    except OverflowError:  # pragma: no cover - absurd inputs only
        return 0.0 if cost > centre else 1.0


def pair_cost(en: list[Features], pt: list[Features]) -> float:
    """Cost of claiming these two chunks are the same chunk."""
    penalty = 0.55 * (len(en) + len(pt) - 2)
    # Fast path: the overwhelming majority of DP cells are 1:1 and do not need
    # a merged fingerprint allocated for them.
    if len(en) == 1 and len(pt) == 1:
        return _fingerprint_cost(en[0], pt[0], penalty)
    return _fingerprint_cost(
        merge_features(en, "en"), merge_features(pt, "pt"), penalty
    )


def _fingerprint_cost(en_feat: Features, pt_feat: Features, penalty: float) -> float:
    if en_feat.char_len <= 0 or pt_feat.char_len <= 0:
        return 4.0 + penalty

    # --- length ratio -----------------------------------------------------
    ratio = math.log(pt_feat.char_len / en_feat.char_len)
    cost = abs(ratio - config.LENGTH_MU) / config.LENGTH_SIGMA

    # --- numbers ----------------------------------------------------------
    if en_feat.digits and pt_feat.digits:
        shared = en_feat.digits & pt_feat.digits
        cost += 0.6 * len(en_feat.digits ^ pt_feat.digits)
        cost -= 0.8 * min(len(shared), 3)
    elif en_feat.digits or pt_feat.digits:
        cost += 1.2

    # --- proper nouns -----------------------------------------------------
    if en_feat.names and pt_feat.names:
        cost -= 0.45 * min(len(en_feat.names & pt_feat.names), 4)

    # --- shared word stems ------------------------------------------------
    if en_feat.stems and pt_feat.stems:
        shared = len(en_feat.stems & pt_feat.stems)
        union = len(en_feat.stems | pt_feat.stems)
        if union:
            cost -= 3.0 * (shared / union)

    # --- discourage merges slightly --------------------------------------
    return cost + penalty


def align(
    en: list[str],
    pt: list[str],
    *,
    band: int | None = None,
    offset: tuple[int, int] = (0, 0),
) -> list[Pair]:
    """Align two lists of paragraphs. Returns pairs with ``offset`` applied."""
    n, m = len(en), len(pt)
    if n == 0 or m == 0:
        return []

    fe = [features(t, "en") for t in en]
    fp = [features(t, "pt") for t in pt]

    # Degenerate windows (all of one side vs all of the other) have no valid
    # monotone decomposition, so collapse them into a single pair.
    if n == 1 or m == 1:
        return [
            Pair(
                en=[i + offset[0] for i in range(n)],
                pt=[j + offset[1] for j in range(m)],
                score=_score(pair_cost(fe, fp)),
            )
        ]

    width = config.DP_BAND if band is None else band
    for candidate in (width, width * 4, width * 16):
        result = _dp(fe, fp, candidate, offset)
        if result is not None:
            return result

    # The corridor could not reach the far corner. Try one genuinely wide pass
    # when the grid is small enough to fit in memory.
    if n * m <= 400_000:
        result = _dp(fe, fp, max(n, m) + 1, offset)
        if result is not None:
            return result

    # Structures this far apart (missing chapters, unrelated texts) get a
    # proportional mapping: still monotone, still complete, just honest about
    # being a guess.
    return _proportional(n, m, offset)


def _proportional(n: int, m: int, offset: tuple[int, int]) -> list[Pair]:
    """Map by relative position, guaranteeing full coverage of both sides."""
    pairs: list[Pair] = []
    if n >= m:
        group: list[int] = []
        expected = -1
        for i in range(n):
            j = (i * m) // n
            if j != expected:
                if group:
                    pairs.append(Pair([x + offset[0] for x in group], [expected + offset[1]], 0.2))
                group, expected = [i], j
            else:
                group.append(i)
        if group:
            pairs.append(Pair([x + offset[0] for x in group], [expected + offset[1]], 0.2))
    else:
        group = []
        expected = -1
        for j in range(m):
            i = (j * n) // m
            if i != expected:
                if group:
                    pairs.append(Pair([expected + offset[0]], [y + offset[1] for y in group], 0.2))
                group, expected = [j], i
            else:
                group.append(j)
        if group:
            pairs.append(Pair([expected + offset[0]], [y + offset[1] for y in group], 0.2))
    return pairs


def _dp(
    fe: list[Features],
    fp: list[Features],
    band: int,
    offset: tuple[int, int],
) -> list[Pair] | None:
    n, m = len(fe), len(fp)

    def bounds(i: int) -> tuple[int, int]:
        expected = i * m / n
        lo = max(0, int(math.floor(expected - band)))
        hi = min(m, int(math.ceil(expected + band)))
        return lo, hi

    dp: list[dict[int, float]] = [dict() for _ in range(n + 1)]
    back: list[dict[int, tuple[int, int]]] = [dict() for _ in range(n + 1)]
    dp[0][0] = 0.0
    cache: dict[tuple[int, int, int, int], float] = {}

    for i in range(n + 1):
        row = dp[i]
        if not row:
            continue
        row_lo, row_hi = bounds(i)
        for j in list(row):
            if j < row_lo or j > row_hi:
                continue
            base = row[j]
            for di, dj in _MOVES:
                ni, nj = i + di, j + dj
                if ni > n or nj > m:
                    continue
                nlo, nhi = bounds(ni)
                if not (nlo <= nj <= nhi):
                    continue
                key = (i, ni, j, nj)
                cost = cache.get(key)
                if cost is None:
                    cost = pair_cost(fe[i:ni], fp[j:nj])
                    cache[key] = cost
                candidate = base + cost
                if candidate < dp[ni].get(nj, _INF):
                    dp[ni][nj] = candidate
                    back[ni][nj] = (i, j)

    if m not in dp[n]:
        return None

    pairs: list[Pair] = []
    i, j = n, m
    while (i, j) != (0, 0):
        pi, pj = back[i][j]
        pairs.append(
            Pair(
                en=[x + offset[0] for x in range(pi, i)],
                pt=[y + offset[1] for y in range(pj, j)],
                score=_score(pair_cost(fe[pi:i], fp[pj:j])),
            )
        )
        i, j = pi, pj
    pairs.reverse()
    return pairs
