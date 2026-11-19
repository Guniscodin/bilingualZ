"""Core data structures. Plain dataclasses, trivially JSON-serialisable."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Pair:
    """One step of an alignment path.

    ``en`` / ``pt`` hold the paragraph indices covered on each side. A normal
    pair is ``Pair([3], [3])``; a merge is ``Pair([4, 5], [4])``.
    """

    en: list[int]
    pt: list[int]
    score: float = 1.0

    @property
    def size(self) -> int:
        return len(self.en) + len(self.pt)

    def contains(self, side: str, index: int) -> bool:
        return index in (self.en if side == "en" else self.pt)

    def to_dict(self) -> dict:
        return {
            "en": list(self.en),
            "pt": list(self.pt),
            "score": round(float(self.score), 4),
        }

    @staticmethod
    def from_dict(data: dict) -> "Pair":
        return Pair(
            en=[int(i) for i in data.get("en", [])],
            pt=[int(i) for i in data.get("pt", [])],
            score=float(data.get("score", 1.0)),
        )


@dataclass
class Document:
    """A bilingual reading session."""

    id: str
    title: str
    mode: str                       # "parallel" | "translate"
    en: list[str]
    pt: list[str]
    pairs: list[Pair] = field(default_factory=list)
    forced: list[tuple[int, int]] = field(default_factory=list)
    progress: int = 0
    source_lang: str = "en"         # side that was machine translated (translate mode)
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "mode": self.mode,
            "en": list(self.en),
            "pt": list(self.pt),
            "pairs": [p.to_dict() for p in self.pairs],
            "forced": [list(f) for f in self.forced],
            "progress": self.progress,
            "source_lang": self.source_lang,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(data: dict) -> "Document":
        return Document(
            id=data["id"],
            title=data.get("title", "Untitled"),
            mode=data.get("mode", "parallel"),
            en=list(data.get("en", [])),
            pt=list(data.get("pt", [])),
            pairs=[Pair.from_dict(p) for p in data.get("pairs", [])],
            forced=[tuple(int(i) for i in f) for f in data.get("forced", [])],
            progress=int(data.get("progress", 0)),
            source_lang=data.get("source_lang", "en"),
            created_at=data.get("created_at", ""),
        )
