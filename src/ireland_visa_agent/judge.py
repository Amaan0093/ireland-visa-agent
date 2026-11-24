import hashlib
import re

import ollama
from pydantic import BaseModel
from rapidfuzz import fuzz

from ireland_visa_agent.config import settings

CITATION = r"\[\d+(?:\s*,\s*\d+)*\]"


# ---------- Output models ----------

class CorrectnessVerdict(BaseModel):
    reasoning: str
    correct: bool

class SentenceCheck(BaseModel):
    sentence_id: int
    source_number: int
    quote: str
    same_situation: bool

class SentenceChecks(BaseModel):
    checks: list[SentenceCheck]

class FaithfulnessVerdict(BaseModel):
    reasoning: str
    faithful: bool


# ---------- Prompts ----------

CORRECTNESS_PROMPT = """You grade answers from an assistant about Irish immigration rules.
Decide whether the ANSWER is correct, using the REFERENCE ANSWER as the ground truth.

correct = true when the answer's main point matches the reference and nothing it states is wrong.
Leaving out a minor detail is acceptable.

correct = false when ANY of these apply:
- it states something that contradicts the reference
- it answers for a different situation or category of person than the question asks about
- the reference says the answer depends on the person's situation, and the answer does not say so
- it is misleading in a way that could make someone act wrongly, especially about timing or deadlines

Important:
- Extra details that are not in the reference are fine, as long as they do not contradict it.
- Ignore differences in wording, spelling, style or length.
- Missing minor details is fine. Only the main point the question asks about matters.
- The reference is the ground truth. Do not use your own knowledge.

Write your reasoning first, then give the verdict."""

SENTENCES_PROMPT = """You check an answer from an assistant about Irish immigration rules
against the SOURCES the assistant was given.

The answer has been split into numbered SENTENCES. Check EVERY sentence, one by one.
Ignore citation markers like [1].

For each sentence return:
- sentence_id: the sentence's number
- source_number: the number of the ONE source that supports the sentence, or 0 if no source does
- quote: the supporting sentence copied EXACTLY, word for word, from that ONE source.
  Copy one continuous passage. Do not combine text from different places. Use "" if source_number is 0.
- same_situation: true only if the quoted passage is about the same situation, the same group of
  people and the same timing as the sentence. false if the source describes a different case, for
  example a rule for one category of person presented as applying to everyone, a rule about one
  process presented as applying to another, or "before" presented as "after".

Guesses ("it seems", "probably"), conclusions the sources do not state, and comments about what
the sources do or do not say are not supported by any source: give them source_number 0."""

JUDGE_VERSION = hashlib.sha256((CORRECTNESS_PROMPT + SENTENCES_PROMPT).encode()).hexdigest()[:8]


# ---------- Model call ----------

_client = ollama.Client(host=settings.ollama_host)

def _ask(system: str, user: str, schema: type[BaseModel], model: str) -> BaseModel:
    response = _client.chat(
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        format=schema.model_json_schema(),
        options={"temperature": 0, "num_ctx": 8192},
    )
    return schema.model_validate_json(response.message.content)


# ---------- Correctness ----------

def judge_correctness(question: str, reference: str, answer: str) -> CorrectnessVerdict:
    user = f"QUESTION:\n{question}\n\nREFERENCE ANSWER:\n{reference}\n\nANSWER TO GRADE:\n{answer}"
    return _ask(CORRECTNESS_PROMPT, user, CorrectnessVerdict, settings.correctness_judge_model)

# ---------- Faithfulness ----------

def split_sentences(text: str) -> list[str]:
    """Split an answer into checkable units. Bullet points keep their lead-in line for context."""
    units = []
    for para in re.split(r"\n\s*\n", text.strip()):
        lines = [l.strip() for l in para.split("\n") if l.strip()]
        if len(lines) > 1 and any(l.startswith("-") for l in lines[1:]):
            lead = lines[0]
            units += [f"{lead} {l[1:].strip()}" for l in lines[1:] if l.startswith("-")]
            continue
        joined = re.sub(rf"([.!?])\s*((?:{CITATION}\s*)+)",
                        lambda m: " " + m.group(2).strip() + m.group(1) + " ", " ".join(lines))
        units += [s for s in re.split(r"(?<=[.!?])\s+", joined.strip()) if s]
    return units

def _quote_found(quote: str, sources: list[dict], number: int) -> bool:
    source = next((s for s in sources if s["number"] == number), None)
    if source is None or len(quote) < 15:
        return False
    return fuzz.partial_ratio(quote.lower(), source["content"].lower()) >= 90

def judge_faithfulness(question: str, answer: str, sources: list[dict]) -> FaithfulnessVerdict:
    sentences = split_sentences(answer)
    blocks = "\n\n".join(f"[{s['number']}] {s['title']}\n{s['content']}" for s in sources)
    numbered = "\n".join(f"{i}. {s}" for i, s in enumerate(sentences, start=1))
    user = f"QUESTION:\n{question}\n\nSOURCES:\n{blocks}\n\nSENTENCES TO CHECK:\n{numbered}"
    result = _ask(SENTENCES_PROMPT, user, SentenceChecks, settings.faithfulness_judge_model)
    
    by_id = {c.sentence_id: c for c in result.checks}
    problems, lines = [], []
    for i, sentence in enumerate(sentences, start=1):
        c = by_id.get(i)
        if c is None:
            problems.append(f"NOT CHECKED: {sentence}")
            continue
        lines.append(f'{i}. {sentence} -> [{c.source_number}] "{c.quote}" same_situation={c.same_situation}')
        if c.source_number == 0:
            problems.append(f"UNSUPPORTED: {sentence}")
        elif not _quote_found(c.quote, sources, c.source_number):
            problems.append(f"QUOTE NOT FOUND in [{c.source_number}]: {sentence}")
        elif not c.same_situation:
            problems.append(f"DIFFERENT SITUATION [{c.source_number}]: {sentence}")

    reasoning = "\n".join(lines + (["PROBLEMS:"] + problems if problems else []))
    return FaithfulnessVerdict(reasoning=reasoning, faithful=not problems)