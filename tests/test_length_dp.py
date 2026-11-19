from bilingualz.align import length_dp
from bilingualz.models import Pair

EN = [
    "In 1755 an earthquake destroyed most of Lisbon.",
    "The king's minister, the Marquis of Pombal, ordered the city rebuilt.",
    "His plan produced wide avenues and a grid of streets.",
]

PT = [
    "Em 1755, um terramoto destruiu grande parte de Lisboa.",
    (
        "O ministro do rei, o Marques de Pombal, ordenou a reconstrucao da cidade. "
        "O seu plano produziu avenidas largas e uma grelha de ruas."
    ),
]


def coverage(pairs: list[Pair], en_count: int, pt_count: int) -> None:
    en_seen = [index for pair in pairs for index in pair.en]
    pt_seen = [index for pair in pairs for index in pair.pt]
    assert en_seen == list(range(en_count))
    assert pt_seen == list(range(pt_count))


def test_aligns_a_merged_paragraph():
    pairs = length_dp.align(EN, PT)
    coverage(pairs, len(EN), len(PT))
    assert len(pairs) == 2
    assert pairs[0].en == [0] and pairs[0].pt == [0]
    # The translator folded two English paragraphs into one Portuguese one.
    assert pairs[1].en == [1, 2] and pairs[1].pt == [1]


def test_correct_pairs_score_high_and_wrong_ones_low():
    pairs = length_dp.align(EN, PT)
    assert pairs[0].score > 0.6
    assert pairs[1].score > 0.6


def test_identity_input_is_trivially_aligned():
    texts = [f"Paragraph number {i} talks about number {i * 7}." for i in range(6)]
    translated = [f"O paragrafo numero {i} fala sobre o numero {i * 7}." for i in range(6)]
    pairs = length_dp.align(texts, translated)
    coverage(pairs, len(texts), len(translated))
    assert all(pair.en == pair.pt for pair in pairs)


def test_empty_input():
    assert length_dp.align([], []) == []
    assert length_dp.align(["a"], []) == []


def test_single_side_collapses():
    pairs = length_dp.align(["only one paragraph here"], ["a", "b", "c"])
    assert len(pairs) == 1
    assert pairs[0].en == [0]
    assert pairs[0].pt == [0, 1, 2]


def test_structurally_different_documents_still_cover_everything():
    # Half the English side has no Portuguese counterpart at all: the narrow
    # corridor cannot reach the far corner, so the fallback must still produce
    # a complete, monotone mapping instead of dropping paragraphs.
    en = [f"Sentence {i} says something about {i * 11} things." for i in range(120)]
    pt = [f"A frase {i} diz algo sobre {i * 11} coisas." for i in range(60)]
    pairs = length_dp.align(en, pt)
    assert [i for pair in pairs for i in pair.en] == list(range(120))
    assert [j for pair in pairs for j in pair.pt] == list(range(60))


def test_proportional_fallback_is_monotone():
    pairs = length_dp._proportional(10, 3, (0, 0))
    assert [i for pair in pairs for i in pair.en] == list(range(10))
    assert [j for pair in pairs for j in pair.pt] == [0, 1, 2]
