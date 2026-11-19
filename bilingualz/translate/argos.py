"""Offline translation via Argos Translate (CTranslate2 + OpenNMT).

Default engine: no API key, no signup, no network after the first model
download. Quality is fair rather than beautiful; Azure is the upgrade path.

Model packages are ~100-300 MB per direction and are fetched on first use.
"""

from __future__ import annotations

import os

from .base import Progress

# Windows/Linux both accept "pt"; allow an explicit Brazilian preference.
_PT_ALIASES = {"pt": ["pt", "pt_BR"], "pt_BR": ["pt_BR", "pt"]}


class ArgosTranslator:
    name = "argos"

    def __init__(self) -> None:
        self._installed: set[tuple[str, str]] = set()
        self._warned = False

    # -- model management -------------------------------------------------
    def _codes(self, code: str) -> list[str]:
        return _PT_ALIASES.get(code, [code])

    def _ensure_installed(self, source: str, target: str) -> tuple[str, str]:
        if not self._warned:
            self._warned = True

        from argostranslate import package  # imported lazily: optional dependency

        for src in self._codes(source):
            for tgt in self._codes(target):
                if (src, tgt) in self._installed:
                    return src, tgt
                try:
                    installed = package.get_installed_packages()
                except Exception:
                    installed = []

                if any(p.from_code == src and p.to_code == tgt for p in installed):
                    self._installed.add((src, tgt))
                    return src, tgt

                try:
                    package.update_package_index()
                    available = package.get_available_packages()
                except Exception:  # offline: fall through to whatever is local
                    available = []

                match = next(
                    (p for p in available if p.from_code == src and p.to_code == tgt),
                    None,
                )
                if match is not None:
                    package.install_from_path(match.download())
                    self._installed.add((src, tgt))
                    return src, tgt

        raise RuntimeError(
            f"Argos has no {source}->{target} model installed and could not "
            "download one. Run once with a network connection, or switch to "
            "BILINGUALZ_TRANSLATOR=azure."
        )

    # -- translation ------------------------------------------------------
    def translate(
        self,
        texts: list[str],
        source: str,
        target: str,
        on_progress: Progress | None = None,
    ) -> list[str]:
        from argostranslate import translate as argos_translate

        src, tgt = self._ensure_installed(source, target)
        out: list[str] = []
        total = max(len(texts), 1)

        for index, text in enumerate(texts):
            if not text.strip():
                out.append("")
            else:
                out.append(argos_translate.translate(text, src, tgt))
            if on_progress and (index % 5 == 0 or index == total - 1):
                on_progress((index + 1) / total, "translating")

        return out


def variant_hint() -> str:
    return os.environ.get("BILINGUALZ_PT_VARIANT", "pt")
