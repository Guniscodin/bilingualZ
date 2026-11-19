"""The bridge between the web UI and the Python engine.

There is no HTTP server here. pywebview exposes this object as
``window.pywebview.api`` inside the page, so the app ships as a single native
window with no ports, no localhost, and no firewall prompt.
"""

from __future__ import annotations

import json
import traceback

from . import __version__, ingest
from .align import align_identity, align_with_anchors, nudge as nudge_anchors
from .models import Document
from .store import Store, new_id, now
from .translate import available_translators, get_translator

LOW_CONFIDENCE = 0.55
MAX_TITLE = 90


def _title_from(text: str, fallback: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line[:MAX_TITLE]
    return fallback


class Api:
    def __init__(self, store: Store | None = None, translator=None):
        # Every attribute must start with an underscore. pywebview mirrors the
        # public ones onto window.pywebview.api, and a live Window or Store
        # object cannot be serialised - it just floods the console with
        # "Error while processing window.native.*" for every frame.
        self._store = store or Store()
        self._window = None
        self._translator = translator

    # -- plumbing ---------------------------------------------------------
    def set_window(self, window) -> None:
        self._window = window

    def _emit(self, fraction: float, message: str) -> None:
        if self._window is None:
            return
        try:
            payload = json.dumps(message)
            self._window.evaluate_js(
                f"window.BZ && window.BZ.onProgress && "
                f"window.BZ.onProgress({float(fraction):.4f}, {payload})"
            )
        except Exception:
            pass

    def _payload(self, doc: Document) -> dict:
        labels = {"en": "English", "pt": "Português"}
        if doc.mode == "translate":
            target = "pt" if doc.source_lang == "en" else "en"
            labels[target] = labels[target] + " - machine"
        return {"doc": doc.to_dict(), "labels": labels}

    def _translator_for(self):
        if self._translator is None:
            self._translator = get_translator()
        return self._translator

    # -- exposed to JS ----------------------------------------------------
    def ping(self) -> dict:
        return {"ok": True, "version": __version__, "home": str(self._store.root)}

    def translator_info(self) -> dict:
        available = available_translators()
        try:
            name = self._translator_for().name
        except Exception as exc:
            print(traceback.format_exc())
            return {"name": "unavailable", "available": available, "error": str(exc)}
        return {"name": name, "available": available}

    def list_documents(self) -> list[dict]:
        return self._store.list()

    def get_document(self, doc_id: str) -> dict:
        return self._payload(self._store.load(doc_id))

    def delete_document(self, doc_id: str) -> dict:
        return {"deleted": self._store.delete(doc_id)}

    def create_parallel(self, payload: dict) -> dict:
        en_text = payload.get("en", "")
        pt_text = payload.get("pt", "")
        en = ingest.split_paragraphs(en_text)
        pt = ingest.split_paragraphs(pt_text)

        if not en or not pt:
            raise ValueError("Both sides need some text.")
        if len(en) < 2 and len(pt) < 2:
            raise ValueError("Paste at least two paragraphs on the longer side.")

        pairs = align_with_anchors(en, pt)
        doc = Document(
            id=new_id(),
            title=(payload.get("title") or _title_from(en_text, "Untitled")).strip(),
            mode="parallel",
            en=en,
            pt=pt,
            pairs=pairs,
            progress=0,
            created_at=now(),
        )
        self._store.save(doc)
        return self._payload(doc)

    def create_translated(self, payload: dict) -> dict:
        text = payload.get("text", "")
        source = (payload.get("source_lang") or "pt").lower()
        target = "en" if source == "pt" else "pt"

        segments = ingest.split_paragraphs(text)
        if not segments:
            raise ValueError("Nothing to translate.")

        self._emit(0.0, "preparing")
        translator = self._translator_for()
        translated = translator.translate(segments, source, target, on_progress=self._emit)

        if source == "pt":
            en, pt = translated, segments
        else:
            en, pt = segments, translated

        doc = Document(
            id=new_id(),
            title=(payload.get("title") or _title_from(text, "Untitled")).strip(),
            mode="translate",
            en=en,
            pt=pt,
            pairs=align_identity(en, pt),
            progress=0,
            source_lang=source,
            created_at=now(),
        )
        self._store.save(doc)
        self._emit(1.0, "done")
        return self._payload(doc)

    def save_progress(self, doc_id: str, pair_index: int) -> dict:
        doc = self._store.load(doc_id)
        doc.progress = max(0, min(int(pair_index), max(len(doc.pairs) - 1, 0)))
        self._store.save(doc)
        return {"progress": doc.progress}

    def nudge(self, doc_id: str, pair_index: int, delta: int) -> dict:
        doc = self._store.load(doc_id)
        index = max(0, min(int(pair_index), len(doc.pairs) - 1))
        pair = doc.pairs[index]
        doc.forced = nudge_anchors(doc.en, doc.pt, doc.forced, pair, int(delta))
        doc.pairs = align_with_anchors(doc.en, doc.pt, doc.forced)
        doc.progress = min(doc.progress, len(doc.pairs) - 1)
        self._store.save(doc)
        return self._payload(doc)

    def add_anchor(self, doc_id: str, pair_index: int) -> dict:
        doc = self._store.load(doc_id)
        index = max(0, min(int(pair_index), len(doc.pairs) - 1))
        pair = doc.pairs[index]
        if pair.en and pair.pt:
            entry = (pair.en[0], pair.pt[0])
            if entry not in doc.forced:
                doc.forced = sorted(doc.forced + [entry])
                doc.pairs = align_with_anchors(doc.en, doc.pt, doc.forced)
        self._store.save(doc)
        return self._payload(doc)

    def clear_anchors(self, doc_id: str) -> dict:
        doc = self._store.load(doc_id)
        doc.forced = []
        doc.pairs = align_with_anchors(doc.en, doc.pt)
        doc.progress = min(doc.progress, len(doc.pairs) - 1)
        self._store.save(doc)
        return self._payload(doc)


__all__ = ["Api"]
