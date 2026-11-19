"""On-disk translation cache.

Keyed by (engine, source, target, text). Re-opening a document, re-aligning, or
nudging an anchor costs zero API calls. With a 2M characters/month free tier
that is the difference between "one book" and "several books".
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from .base import Progress, Translator


class CachedTranslator:
    def __init__(self, inner: Translator, cache_dir: Path | str):
        self.inner = inner
        self.name = getattr(inner, "name", "unknown")
        self.dir = Path(cache_dir) / self.name
        self.dir.mkdir(parents=True, exist_ok=True)

    def _path(self, text: str, source: str, target: str) -> Path:
        digest = hashlib.sha256(
            f"{self.name}\x00{source}\x00{target}\x00{text}".encode("utf-8")
        ).hexdigest()
        return self.dir / f"{digest}.txt"

    def translate(
        self,
        texts: list[str],
        source: str,
        target: str,
        on_progress: Progress | None = None,
    ) -> list[str]:
        resolved: dict[str, str] = {}
        missing: list[str] = []

        for text in texts:
            if text in resolved or text in missing:
                continue
            cached = self._path(text, source, target)
            if cached.exists():
                resolved[text] = cached.read_text(encoding="utf-8")
            else:
                missing.append(text)

        if on_progress and resolved:
            on_progress(len(resolved) / max(len(texts), 1), "cache")

        if missing:
            fresh = self.inner.translate(missing, source, target, on_progress)
            for text, translated in zip(missing, fresh):
                resolved[text] = translated
                self._path(text, source, target).write_text(translated, encoding="utf-8")

        return [resolved.get(text, "") for text in texts]
