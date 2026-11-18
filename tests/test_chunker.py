from ireland_visa_agent.ingest import chunk_text, clean_html, build_chunks, split_sections

def test_sections_track_heading_hierarchy():
    text = "§1 Page\nintro\n§2 Documents\n§4 Stamp 0\nzero docs\n§4 Stamp 1A\naccountant docs\n§2 Fees\nfee text"
    assert split_sections(text) == [
        ("", "intro"),
        ("Documents > Stamp 0", "zero docs"),
        ("Documents > Stamp 1A", "accountant docs"),
        ("Fees", "fee text"),
    ]

def test_chunks_start_with_their_section():
    chunks = build_chunks("§2 Documents\n§4 Stamp 1A\naccountant docs")
    assert chunks == ["Section: Documents > Stamp 1A\naccountant docs"]

def test_short_text_is_one_chunk():
    assert chunk_text("a\nb\nc") == ["a\nb\nc"]

def test_long_text_splits_with_overlap():
    paras = [f"paragraph {i} " + "x" * 300 for i in range(6)]
    chunks = chunk_text("\n".join(paras), max_chars=1000)
    assert len(chunks) > 1
    assert all(len(c) <= 1000 for c in chunks)
    assert chunks[0].split("\n")[-1] == chunks[1].split("\n")[0]  # overlap

def test_page_wrapped_in_form_is_kept():
    body = "<p>" + "Real content about permits. " * 40 + "</p>"
    html = f"""<html><head><title>T</title></head><body>
      <section id="globalCookieBar"><p>We use cookies</p></section>
      <form id="aspnetForm"><article>{body}</article></form>
    </body></html>"""
    title, text = clean_html(html)
    assert "Real content about permits" in text
    assert "cookies" not in text