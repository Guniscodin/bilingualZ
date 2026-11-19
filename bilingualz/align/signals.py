"""Cheap, LLM-free evidence that two paragraphs are the same paragraph.

The engine never translates anything. It only notices that two chunks of text
look like they came from the same place: matching numbers, matching proper
nouns, and matching word stems (English and Portuguese share a lot of Latin
vocabulary, so 4-character stems line up surprisingly often).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

WORD_RE = re.compile(r"[^\W\d_]+", re.UNICODE)
DIGIT_RE = re.compile(r"\d+")

# Strip Portuguese diacritics is handled by unicode decomposition in fold().

EN_STOP = frozenset(
    """a about above after again against all am an and any are as at be because
    been before being below between both but by can could did do does doing down
    during each few for from further had has have having he her here hers herself
    him himself his how i if in into is it its itself just me more most my myself
    no nor not now of off on once only or other our ours ourselves out over own
    same she should so some such than that the their theirs them themselves then
    there these they this those through to too under until up very was we were
    what when where which while who whom why will with would you your yours
    yourself yourselves""".split()
)

PT_STOP = frozenset(
    """a à ao aos aquela aquelas aquele aqueles aquilo as até com como da das de
    dela delas dele deles depois do dos e ela elas ele eles em entre era eram
    essa essas esse esses esta estas este estes eu foi foram há isso isto já lhe
    lhes mais mas me mesmo meu meus minha minhas muito na nas não no nos nós o os
    ou para pela pelas pelo pelos por qual quando que quem se sem seu seus sua
    suas são também te tem têm teu teus tu tua tuas um uma umas uns você vocês
    vos""".split()
)

STEM_LEN = 4


@dataclass(frozen=True)
class Features:
    """Pre-computed, comparable fingerprints of one paragraph."""

    char_len: int
    words: tuple[str, ...]
    stems: frozenset[str]       # 4-char prefixes of content words
    digits: frozenset[str]      # every number that appears verbatim
    names: frozenset[str]       # 4-char prefixes of capitalised, mid-sentence words

    def union(self, other: "Features") -> "Features":
        return Features(
            char_len=self.char_len + other.char_len,
            words=self.words + other.words,
            stems=self.stems | other.stems,
            digits=self.digits | other.digits,
            names=self.names | other.names,
        )

    @property
    def content_stems(self) -> frozenset[str]:
        return self.stems


def fold(text: str) -> str:
    """Lowercase and remove diacritics."""
    decomposed = unicodedata.normalize("NFD", text.lower())
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return unicodedata.normalize("NFC", stripped)


def features(text: str, lang: str) -> Features:
    stop = PT_STOP if lang == "pt" else EN_STOP
    raw = WORD_RE.findall(text or "")
    folded = [fold(w) for w in raw]

    stems = {w[:STEM_LEN] for w in folded if len(w) >= STEM_LEN and w not in stop}

    names = set()
    for idx, (original, low) in enumerate(zip(raw, folded)):
        if idx == 0:                      # first word of a paragraph is capitalised anyway
            continue
        if len(low) < 3 or low in stop:
            continue
        if original[:1].isupper() and not original.isupper():
            names.add(low[:STEM_LEN])

    return Features(
        char_len=len(text or ""),
        words=tuple(folded),
        stems=frozenset(stems),
        digits=frozenset(DIGIT_RE.findall(text or "")),
        names=frozenset(names),
    )


def merge_features(items: list[Features], lang: str) -> Features:
    """Fingerprint for a run of 2+ contiguous paragraphs."""
    if not items:
        return Features(0, (), frozenset(), frozenset(), frozenset())
    acc = items[0]
    for item in items[1:]:
        acc = acc.union(item)
    return acc
