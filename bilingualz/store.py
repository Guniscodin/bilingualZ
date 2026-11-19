"""Persistence: one JSON file per document.

Deliberately dumb. A reading session survives a crash, a reboot, and being
opened on another machine if you copy the folder.
"""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from . import config
from .models import Document


def new_id() -> str:
    return uuid.uuid4().hex[:12]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Store:
    def __init__(self, root: Path | str | None = None):
        self.root = Path(root) if root else config.app_home()
        self.docs_dir = self.root / "docs"
        self.docs_dir.mkdir(parents=True, exist_ok=True)

    # -- paths ------------------------------------------------------------
    def path_for(self, doc_id: str) -> Path:
        return self.docs_dir / f"{doc_id}.json"

    # -- writes -----------------------------------------------------------
    def save(self, doc: Document) -> None:
        payload = json.dumps(doc.to_dict(), ensure_ascii=False, indent=1)
        target = self.path_for(doc.id)
        fd, tmp = tempfile.mkstemp(dir=str(self.docs_dir), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
            os.replace(tmp, target)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise

    def delete(self, doc_id: str) -> bool:
        target = self.path_for(doc_id)
        if target.exists():
            target.unlink()
            return True
        return False

    # -- reads ------------------------------------------------------------
    def load(self, doc_id: str) -> Document:
        target = self.path_for(doc_id)
        if not target.exists():
            raise FileNotFoundError(f"No such document: {doc_id}")
        with target.open("r", encoding="utf-8") as handle:
            return Document.from_dict(json.load(handle))

    def list(self) -> list[dict]:
        summaries: list[dict] = []
        for path in sorted(self.docs_dir.glob("*.json")):
            try:
                with path.open("r", encoding="utf-8") as handle:
                    data = json.load(handle)
            except (OSError, json.JSONDecodeError):
                continue
            summaries.append(
                {
                    "id": data.get("id", path.stem),
                    "title": data.get("title", "Untitled"),
                    "mode": data.get("mode", "parallel"),
                    "total": len(data.get("pairs", [])),
                    "progress": int(data.get("progress", 0)),
                    "created_at": data.get("created_at", ""),
                }
            )
        summaries.sort(key=lambda item: item.get("created_at", ""), reverse=True)
        return summaries
