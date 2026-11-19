"""Turning pasted text into clean paragraphs.

This is unglamorous and absolutely load-bearing: every alignment failure I have
seen from a naive implementation starts with "the text was pasted with hard
wrapped lines".
"""

from __future__ import annotations

import re

# Only rejoin a broken line when it looks like real hyphenation
# ("trans-\nlation"), not a dash between two words.
_HYPHEN_BREAK = re.compile(r"([^\W\d_])-\n([^\W\d_])")
_WHITESPACE = re.compile(r"[ \t\u00a0\u2007\u202f]+")
_SENTENCE_END = re.compile(r"(?<=[.!?\u2026])\s+")
_BLANK_LINE = re.compile(r"\n\s*\n")

TERMINAL = (".", "!", "?", "\u2026", ":", ";", '"', "'", "\u201d", "\u2019")

CHAR_LIMIT = 3000


def _continues(previous: str, line: str) -> bool:
    """True when ``line`` looks like a hard-wrapped continuation of ``previous``.

    This is the difference between "the PDF exported my paragraph across three
    lines" and "these are three separate one-line paragraphs", and it matters
    enormously: the aligner can only be as good as the paragraph boundaries.
    """
    if not previous:
        return False
    if previous.endswith(TERMINAL):
        return False
    if previous.endswith((",", "\u2014", "-", "(", "[")):
        return True
    return line[:1].islower()


def _merge_wrapped(lines: list[str]) -> list[str]:
    merged: list[str] = []
    for line in lines:
        if merged and _continues(merged[-1], line):
            merged[-1] = f"{merged[-1]} {line}"
        else:
            merged.append(line)
    return merged


def normalize(text: str) -> str:
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")

    def rejoin(match: re.Match[str]) -> str:
        before, after = match.group(1), match.group(2)
        if before.islower() and after.islower():
            return before + after
        return match.group(0)

    text = _HYPHEN_BREAK.sub(rejoin, text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _squash(text: str) -> str:
    return _WHITESPACE.sub(" ", text).strip()


def _split_long(text: str, limit: int) -> list[str]:
    if len(text) <= limit:
        return [text]
    sentences = [s.strip() for s in _SENTENCE_END.split(text) if s.strip()]
    if len(sentences) <= 1:
        return [text[i : i + limit] for i in range(0, len(text), limit)]

    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if current and len(current) + 1 + len(sentence) > limit:
            chunks.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        chunks.append(current)
    return chunks


def split_paragraphs(text: str, *, limit: int = CHAR_LIMIT) -> list[str]:
    """Split pasted text into paragraph chunks, tolerating PDF-style pastes."""
    normalised = normalize(text)
    if not normalised:
        return []

    blocks = [_squash(b) for b in _BLANK_LINE.split(normalised) if b.strip()]

    if len(blocks) <= 1:
        # No blank lines at all: treat one line as one paragraph when there are
        # several lines (the usual "copy from a PDF / plain text file" shape),
        # rejoining the ones that are clearly wrapped mid-sentence.
        lines = [_squash(line) for line in normalised.split("\n") if line.strip()]
        if len(lines) > 1:
            blocks = _merge_wrapped(lines)

    result: list[str] = []
    for block in blocks:
        result.extend(_split_long(block, limit))
    return [p for p in result if p.strip()]


def word_count(text: str) -> int:
    return len(text.split())
