"""End-to-end tests of the bridge object, without any GUI."""

import pytest

from bilingualz.api import Api
from bilingualz.store import Store
from bilingualz.translate import NullTranslator

EN = """In 1755, an earthquake destroyed most of Lisbon.

The king's minister ordered the city rebuilt from scratch.

His plan produced wide avenues and a grid of streets."""

PT = """Em 1755, um terramoto destruiu grande parte de Lisboa.

O ministro do rei ordenou a reconstrucao da cidade de raiz. O seu plano produziu avenidas largas e uma grelha de ruas."""


@pytest.fixture()
def api(tmp_path):
    return Api(store=Store(tmp_path), translator=NullTranslator())


def test_ping(api):
    assert api.ping()["ok"] is True


def test_create_and_reopen(api):
    response = api.create_parallel({"title": "Lisbon", "en": EN, "pt": PT})
    doc = response["doc"]

    assert doc["title"] == "Lisbon"
    assert doc["mode"] == "parallel"
    assert len(doc["en"]) == 3
    assert len(doc["pt"]) == 2
    assert response["labels"]["en"] == "English"

    reopened = api.get_document(doc["id"])["doc"]
    assert reopened["en"] == doc["en"]
    assert reopened["pairs"] == doc["pairs"]


def test_progress_persists(api):
    doc = api.create_parallel({"en": EN, "pt": PT})["doc"]
    assert len(doc["pairs"]) == 2
    api.save_progress(doc["id"], 1)
    assert api.get_document(doc["id"])["doc"]["progress"] == 1


def test_progress_is_clamped(api):
    doc = api.create_parallel({"en": EN, "pt": PT})["doc"]
    api.save_progress(doc["id"], 999)
    stored = api.get_document(doc["id"])["doc"]
    assert stored["progress"] == len(stored["pairs"]) - 1


def test_nudge_creates_an_anchor_and_realigns(api):
    doc = api.create_parallel({"en": EN, "pt": PT})["doc"]
    index = 0
    nudged = api.nudge(doc["id"], index, 1)["doc"]

    assert len(nudged["forced"]) == 1
    en_seen = [i for pair in nudged["pairs"] for i in pair["en"]]
    pt_seen = [j for pair in nudged["pairs"] for j in pair["pt"]]
    assert en_seen == list(range(3))
    assert sorted(pt_seen) == list(range(2))


def test_clear_anchors_restores_the_engine(api):
    doc = api.create_parallel({"en": EN, "pt": PT})["doc"]
    api.nudge(doc["id"], 0, 1)
    cleared = api.clear_anchors(doc["id"])["doc"]
    assert cleared["forced"] == []
    assert len(cleared["pairs"]) == 2


def test_translate_mode_pairs_one_to_one(api):
    assert api.translator_info()["name"] == "null"
    text = "Primeiro paragrafo.\n\nSegundo paragrafo.\n\nTerceiro paragrafo."
    response = api.create_translated({"text": text, "source_lang": "pt"})
    doc = response["doc"]

    assert doc["mode"] == "translate"
    assert doc["source_lang"] == "pt"
    assert len(doc["pt"]) == 3
    assert len(doc["en"]) == 3
    assert doc["pairs"] == [
        {"en": [0], "pt": [0], "score": 1.0},
        {"en": [1], "pt": [1], "score": 1.0},
        {"en": [2], "pt": [2], "score": 1.0},
    ]
    assert "machine" in response["labels"]["en"]


def test_empty_input_is_rejected(api):
    with pytest.raises(ValueError):
        api.create_parallel({"en": "", "pt": ""})


def test_list_and_delete(api):
    doc = api.create_parallel({"en": EN, "pt": PT})["doc"]
    assert len(api.list_documents()) == 1
    assert api.delete_document(doc["id"])["deleted"] is True
    assert api.list_documents() == []


def test_bridge_exposes_only_callables(api):
    """pywebview mirrors every public attribute into the page.

    A public Window/Store attribute cannot be serialised, so it spams
    "Error while processing window.native.*" on every frame. State must stay
    private; only methods belong on the bridge.
    """
    public = [name for name in dir(api) if not name.startswith("_")]
    leaked = [name for name in public if not callable(getattr(api, name))]
    assert leaked == []
