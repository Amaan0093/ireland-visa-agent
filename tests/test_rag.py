from fastapi.testclient import TestClient

from ireland_visa_agent.main import app
from ireland_visa_agent.rag import build_context, extract_citations, NOT_FOUND, uncited_sentences

def test_citations_outside_range_are_dropped():
    assert extract_citations("A [1]. B [2][9]. C [1].", n_sources=5) == [1, 2]

def test_context_numbers_sources_from_one():
    ctx = build_context([
        {"title": "T1", "url": "u1", "content": "c1"},
        {"title": "T2", "url": "u2", "content": "c2"},
    ])
    assert ctx.startswith("[1] T1")
    assert "[2] T2" in ctx

def test_ask_rejects_empty_question():
    response = TestClient(app).post("/ask", json={"question": ""})
    assert response.status_code == 422

def test_flags_uncited_sentence():
    text = "You must apply within six months [2]. Provisional results will not suffice."
    assert uncited_sentences(text) == ["Provisional results will not suffice."]

def test_citation_after_full_stop_counts():
    assert uncited_sentences("Max 20 hours during term. [1]") == []

def test_not_found_is_never_flagged():
    assert uncited_sentences(NOT_FOUND) == []

from ireland_visa_agent.rag import is_abstention

def test_paraphrased_refusal_is_detected():
    assert is_abstention("I couldn't find this information in the official sources I have.", [])

def test_refusal_mentioning_the_topic_is_detected():
    assert is_abstention("I couldn't find any information about needing proof of address in the provided sources.", [])

def test_cited_answer_mentioning_cannot_find_is_not_a_refusal():
    assert not is_abstention("If you cannot find your IRP card, include an explanation why [2].", [2])