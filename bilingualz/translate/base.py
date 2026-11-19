"""The translator interface, plus a no-dependency fallback."""

from __future__ import annotations

from typing import Callable, Protocol, runtime_checkable

Progress = Callable[[float, str], None]


@runtime_checkable
class Translator(Protocol):
    name: str

    def translate(
        self,
        texts: list[str],
        source: str,
        target: str,
        on_progress: Progress | None = None,
    ) -> list[str]: ...


class NullTranslator:
    """Marks text instead of translating it.

    Keeps translate mode walkable during development and in tests, and gives a
    readable error-free experience when no engine is installed.
    """

    name = "null"

    def translate(
        self,
        texts: list[str],
        source: str,
        target: str,
        on_progress: Progress | None = None,
    ) -> list[str]:
        out = [f"[{target}] {text}" for text in texts]
        if on_progress:
            on_progress(1.0, "done")
        return out
