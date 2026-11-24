import csv
import json
from pathlib import Path

from ireland_visa_agent.config import settings
from ireland_visa_agent.judge import JUDGE_VERSION, judge_correctness, judge_faithfulness

GOLD = Path("data/labels/gold")

records = [json.loads(line) for line in (GOLD / "answers.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
answers = {r["case"]["question"]: r for r in records if r["case"]["type"] == "answerable"}

with open(GOLD / "labels.csv", newline="", encoding="utf-8-sig") as f:
    labels = list(csv.DictReader(f))

def kappa(human: list[bool], judge: list[bool]) -> float:
    n = len(human)
    p_observed = sum(h == j for h, j in zip(human, judge)) / n
    p_h, p_j = sum(human) / n, sum(judge) / n
    p_chance = p_h * p_j + (1 - p_h) * (1 - p_j)
    return 1.0 if p_chance == 1 else (p_observed - p_chance) / (1 - p_chance)

scores = {"correct": ([], []), "faithful": ([], [])}
out_path = GOLD / f"judge_{settings.judge_model.replace(':', '-')}_{JUDGE_VERSION}.jsonl"

with open(out_path, "w", encoding="utf-8") as out:
    for row in labels:
        result = answers[row["question"]]["result"]
        c = judge_correctness(row["question"], row["reference"], result["answer"])
        f_ = judge_faithfulness(row["question"], result["answer"], result["retrieved"])

        human = {"correct": row["correct"] == "1", "faithful": row["faithful"] == "1"}
        judged = {"correct": c.correct, "faithful": f_.faithful}
        for k in scores:
            scores[k][0].append(human[k])
            scores[k][1].append(judged[k])

        disagree = [k for k in human if human[k] != judged[k]]
        status = "agree" if not disagree else "DISAGREE: " + ", ".join(disagree)
        print(f"{row['id']:>2}  {status:28} {row['question']}")
        out.write(json.dumps({"id": row["id"], "question": row["question"], "human": human, "judge": judged,
                              "correct_reasoning": c.reasoning, "faithful_reasoning": f_.reasoning}) + "\n")

print(f"\nJudge: {settings.judge_model}  version {JUDGE_VERSION}")
for k, (h, j) in scores.items():
    agree = sum(a == b for a, b in zip(h, j))
    missed = sum((not a) and b for a, b in zip(h, j))
    false_alarm = sum(a and (not b) for a, b in zip(h, j))
    print(f"{k:9} agreement {agree}/{len(h)}   kappa {kappa(h, j):.2f}   "
          f"missed errors {missed}   false alarms {false_alarm}")