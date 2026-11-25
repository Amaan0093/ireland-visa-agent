# Labelling guidelines: answer quality (gold set v1)

These guidelines define how answers from the Ireland Visa Agent are labelled by hand.
The human labels in `labels.csv` were produced with these rules, and the LLM judge
prompts in `src/ireland_visa_agent/judge.py` are derived from them.

- **Labeller:** Amaan
- **Gold set:** 23 answerable questions from `eval_answers.csv`
- **Answers graded:** `answers.jsonl` (prompt `v2.2-d59aad79`), frozen and never regenerated
- **Date:** November 2026

---

## What each item contains

| Field | Used for |
|---|---|
| Question | What the user asked |
| Reference answer | Ground truth, written from the official pages (used for **correct**) |
| Answer | The assistant's output being graded |
| Sources [1]-[5] | The exact chunks the assistant was given (used for **faithful**) |

Unanswerable questions are **not** labelled here. Refusals are checked by code (`is_abstention`).

---

## Criterion 1: `correct` (1 or 0)

Is the main answer right? Compare the answer with the **reference answer**.

**correct = 1** when the answer's main point matches the reference and nothing it states is wrong.
Leaving out a minor detail is acceptable.

**correct = 0** when any of these apply:

1. It states something that contradicts the reference.
2. It answers for a different situation or category of person than the question asks about
   (for example, the wrong stamp).
3. The reference says the answer depends on the person's situation, and the answer neither
   says so nor asks which situation applies.
4. It is misleading in a way that could make someone act wrongly, especially about
   timing or deadlines (for example, saying to act *after* a permission expires
   when the source says while it is *due to* expire).

---

## Criterion 2: `faithful` (1 or 0)

Is everything the answer says supported by the sources it was given?
Compare the answer with the **sources only**, not with the reference and not with your own knowledge.

**faithful = 1** when every statement in the answer can be found in the sources.

**faithful = 0** when any of these apply:

1. **Unsupported facts:** it states a fact, number, condition or consequence that no source states.
2. **Speculation:** it infers or guesses beyond the sources ("it seems", "this suggests", "probably").
3. **Meta-commentary:** it adds notes or comments about what the sources do or do not say.
4. **Situation mismatch:** it takes a statement a source makes about one situation or group of people
   and presents it as applying to a different or wider situation.

Citation formatting is **not** part of this criterion. A supported sentence with a missing citation
is still faithful; missing citations are measured separately by code (`uncited_sentences`).

---

## The two criteria are independent

| correct | faithful | Example pattern |
|---|---|---|
| 1 | 0 | Right main point, plus an unsupported note or speculation |
| 0 | 1 | Accurately quotes sources, but answers the wrong situation or misses that it depends |
| 0 | 0 | Wrong claim that is also not in the sources |

Label each criterion on its own. Do not let one decide the other.

---

## Rules added while labelling

These rules were not in the original rubric. They came from specific gold items:

| Rule | Criterion | Came from |
|---|---|---|
| Notes about what the sources don't say → 0 | faithful | Q3 |
| Speculation such as "it seems" → 0 | faithful | Q6 |
| Source applied to a different situation → 0 | faithful | Q9, Q8 |
| Consequences no source states → 0 | faithful | Q12 |
| Timing that could leave someone without valid permission → 0 | correct | Q17 |
| Document lists given for some stamps, without saying it depends on the stamp → 0 | correct | Q8 |

Because these rules were derived from this gold set, an LLM judge's agreement on this set
will be somewhat optimistic. Report judge agreement on freshly labelled answers as well.

---

## Borderline cases

When a case is genuinely borderline:

1. Make a decision. Do not leave the label blank.
2. Write a note starting with **"Borderline"** explaining both sides and why you chose.
3. Apply the same decision to similar cases.

Example: **Q2** says the graduate programme lasts "12 months" without mentioning that a master's
graduate can get a further 12 months. Labelled **correct = 1**: nothing stated is wrong, and the
omission was treated as a minor detail rather than misleading.

---

## Process

- Label without looking at any LLM judge output, to avoid being anchored by it.
- Write a note for **every 0**, quoting the answer and the relevant source.
- Check each source against the answer yourself; do not rely on memory of the rules.
- If a new kind of error appears, add a rule to this file and re-check earlier labels for consistency.
