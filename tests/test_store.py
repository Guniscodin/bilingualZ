from bilingualz.models import Document, Pair
from bilingualz.store import Store


def make_document() -> Document:
    return Document(
        id="abc123",
        title="Test",
        mode="parallel",
        en=["One.", "Two."],
        pt=["Um.", "Dois."],
        pairs=[Pair([0], [0], 0.9), Pair([1], [1], 0.8)],
        forced=[(0, 0)],
        progress=1,
        created_at="2026-01-01T00:00:00+00:00",
    )


def test_round_trip(tmp_path):
    store = Store(tmp_path)
    original = make_document()
    store.save(original)

    loaded = store.load("abc123")
    assert loaded.title == "Test"
    assert loaded.en == ["One.", "Two."]
    assert loaded.forced == [(0, 0)]
    assert loaded.progress == 1
    assert [p.score for p in loaded.pairs] == [0.9, 0.8]


def test_list_summaries(tmp_path):
    store = Store(tmp_path)
    store.save(make_document())
    summaries = store.list()
    assert len(summaries) == 1
    assert summaries[0]["id"] == "abc123"
    assert summaries[0]["total"] == 2


def test_delete(tmp_path):
    store = Store(tmp_path)
    store.save(make_document())
    assert store.delete("abc123") is True
    assert store.delete("abc123") is False
    assert store.list() == []


def test_unicode_survives(tmp_path):
    store = Store(tmp_path)
    doc = make_document()
    doc.pt = ["A nação e a revolução.", "Coração."]
    store.save(doc)
    assert store.load("abc123").pt[0] == "A nação e a revolução."
