from bilingualz import ingest


def test_blank_lines_define_paragraphs():
    text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
    assert ingest.split_paragraphs(text) == [
        "First paragraph.",
        "Second paragraph.",
        "Third paragraph.",
    ]


def test_hard_wrapped_paragraph_is_joined():
    text = "A very long paragraph that was\nwrapped by the PDF export\ninto three lines."
    assert ingest.split_paragraphs(text) == [
        "A very long paragraph that was wrapped by the PDF export into three lines."
    ]


def test_single_newlines_become_paragraphs_when_there_are_no_blank_lines():
    text = "Line one is here.\nLine two is here.\nLine three is here."
    assert ingest.split_paragraphs(text) == [
        "Line one is here.",
        "Line two is here.",
        "Line three is here.",
    ]


def test_hyphenated_line_break_is_rejoined():
    text = "This is a trans-\nlation artefact."
    assert ingest.split_paragraphs(text) == ["This is a translation artefact."]


def test_proper_noun_hyphen_break_is_not_rejoined():
    text = "The city of Co-\nOperacao stayed separate."
    assert "Co-" in ingest.split_paragraphs(text)[0]


def test_long_paragraph_is_split_on_sentences():
    sentence = "This sentence exists purely to add length to the paragraph. "
    text = (sentence * 120).strip()
    chunks = ingest.split_paragraphs(text)
    assert len(chunks) > 1
    assert all(len(chunk) <= ingest.CHAR_LIMIT for chunk in chunks)


def test_windows_line_endings_are_normalised():
    text = "One.\r\n\r\nTwo.\r\n\r\nThree."
    assert ingest.split_paragraphs(text) == ["One.", "Two.", "Three."]


def test_empty_input():
    assert ingest.split_paragraphs("") == []
    assert ingest.split_paragraphs("   \n\n  ") == []
