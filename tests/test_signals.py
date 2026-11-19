from bilingualz.align.signals import features


def test_digits_are_verbatim_evidence():
    fingerprint = features("In 1755, an earthquake destroyed Lisbon.", "en")
    assert fingerprint.digits == frozenset({"1755"})


def test_proper_noun_stems_match_across_languages():
    en = features("In 1755, an earthquake destroyed Lisbon.", "en")
    pt = features("Em 1755, um terramoto destruiu Lisboa.", "pt")
    assert "lisb" in en.names
    assert "lisb" in pt.names
    assert en.names & pt.names


def test_cognate_stems_overlap():
    en = features("The revolution transformed the national economy.", "en")
    pt = features("A revolucao transformou a economia nacional.", "pt")
    assert {"revo", "tran", "econ"} <= (en.stems & pt.stems)


def test_accents_are_folded():
    accented = features("A política económica da nação.", "pt")
    plain = features("A politica economica da nacao.", "pt")
    assert accented.stems == plain.stems


def test_stopwords_are_not_signal():
    fingerprint = features("The man and the woman were here.", "en")
    assert "the" not in fingerprint.stems
    assert "and" not in fingerprint.stems


def test_sentence_initial_capital_is_not_a_name():
    fingerprint = features("Meanwhile the ship arrived.", "en")
    assert "mean" not in fingerprint.names
