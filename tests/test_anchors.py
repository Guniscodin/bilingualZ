from bilingualz.align import anchors
from bilingualz.models import Pair

EN = [
    "The first paragraph mentions 1900 and the city of Porto.",
    "The second paragraph mentions 1911 and the city of Lisbon.",
    "The third paragraph mentions 1922 and the city of Coimbra.",
    "The fourth paragraph mentions 1933 and the city of Braga.",
]

PT = [
    "O primeiro paragrafo menciona 1900 e a cidade do Porto.",
    "O segundo paragrafo menciona 1911 e a cidade de Lisboa.",
    "O terceiro paragrafo menciona 1922 e a cidade de Coimbra.",
    "O quarto paragrafo menciona 1933 e a cidade de Braga.",
]


def test_anchor_is_honoured_exactly():
    pairs = anchors.align_with_anchors(EN, PT, [(2, 2)])
    forced = [pair for pair in pairs if pair.en == [2] and pair.pt == [2]]
    assert forced and forced[0].score == 1.0


def test_anchors_keep_full_coverage():
    pairs = anchors.align_with_anchors(EN, PT, [(1, 1), (3, 3)])
    en_seen = [index for pair in pairs for index in pair.en]
    pt_seen = [index for pair in pairs for index in pair.pt]
    assert en_seen == list(range(4))
    assert pt_seen == list(range(4))


def test_non_monotone_anchors_are_dropped():
    pairs = anchors.align_with_anchors(EN, PT, [(2, 2), (1, 1)])
    assert pairs
    en_seen = [index for pair in pairs for index in pair.en]
    assert en_seen == list(range(4))


def test_nudge_shifts_the_portuguese_side():
    pairs = anchors.align_with_anchors(EN, PT)
    target = pairs[1]
    updated = anchors.nudge(EN, PT, [], target, 1)
    assert updated == [(target.en[0], target.pt[0] + 1)]


def test_nudge_is_clamped_to_the_document():
    pairs = anchors.align_with_anchors(EN, PT)
    target = pairs[0]
    updated = anchors.nudge(EN, PT, [], target, -5)
    assert updated == [(target.en[0], 0)]


def test_realigned_document_still_covers_everything():
    pairs = anchors.align_with_anchors(EN, PT)
    forced = anchors.nudge(EN, PT, [], pairs[2], 1)
    realigned = anchors.align_with_anchors(EN, PT, forced)
    en_seen = [index for pair in realigned for index in pair.en]
    pt_seen = [index for pair in realigned for index in pair.pt]
    assert en_seen == list(range(len(EN)))
    assert pt_seen == list(range(len(PT)))
    assert isinstance(realigned[0], Pair)
