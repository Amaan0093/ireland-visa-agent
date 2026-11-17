from ireland_visa_agent.ingest import chunk_text, clean_html

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