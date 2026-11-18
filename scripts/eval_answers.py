import csv
import json

from ireland_visa_agent.rag import NOT_FOUND, answer_question

def contains_fact(text: str, must_include: str) -> bool:
    if not must_include:
        return True
    text = text.lower()
    return any(option.strip().lower() in text for option in must_include.split("|"))

with open("data/eval_answers.csv", newline="", encoding="utf-8") as f:
    cases = list(csv.DictReader(f))

s = {"pass": 0, "answerable": 0, "unanswerable": 0, "false_abstain": 0,
     "answered_unanswerable": 0, "fully_cited": 0, "right_page": 0}

with open("data/eval_answers_results.jsonl", "w", encoding="utf-8") as out:
    for case in cases:
        result = answer_question(case["question"])
        abstained = result.abstained

        if case["type"] == "unanswerable":
            s["unanswerable"] += 1
            passed = abstained
            s["answered_unanswerable"] += not abstained
        else:
            s["answerable"] += 1
            passed = not abstained and contains_fact(result.answer, case["must_include"])
            s["false_abstain"] += abstained
            s["fully_cited"] += (not abstained and not result.uncited)
            expected = case["expected"].split("|")
            s["right_page"] += any(e in src.url for src in result.cited for e in expected)

        s["pass"] += passed
        print(f"{'PASS' if passed else 'FAIL'}  {case['type'][:6]:6}  {case['question']}")
        out.write(json.dumps({"case": case, "passed": passed, "result": result.model_dump()}) + "\n")

a, u = s["answerable"], s["unanswerable"]
print(f"""
Overall pass:              {s['pass']}/{len(cases)}
Wrongly said "don't know": {s['false_abstain']}/{a}
Answered the unanswerable: {s['answered_unanswerable']}/{u}   <- the most dangerous number
Answers fully cited:       {s['fully_cited']}/{a}
Cited the right page:      {s['right_page']}/{a}""")