import csv
import json
import sys
from pathlib import Path

results_path = Path(sys.argv[1])
refs_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/eval_answers.csv")
out_dir = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("data/labels")

with open(refs_path, newline="", encoding="utf-8") as f:
    references = {row["question"]: row["reference"] for row in csv.DictReader(f)}

records = [json.loads(line) for line in results_path.read_text(encoding="utf-8").splitlines() if line.strip()]
records = [r for r in records if r["case"]["type"] == "answerable"]

out_dir = Path("data/labels")
out_dir.mkdir(exist_ok=True)

with open(out_dir / "label_sheet.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["id", "question", "reference", "answer", "correct", "faithful", "notes"])
    for i, r in enumerate(records, start=1):
        q = r["case"]["question"]
        writer.writerow([i, q, references[q], r["result"]["answer"], "", "", ""])

lines = []
for i, r in enumerate(records, start=1):
    res = r["result"]
    lines += [f"## {i}. {res['question']}", "",
              f"**Reference:** {references[res['question']]}", "",
              f"**Answer:** {res['answer']}", "",
              "**Sources the model saw:**", ""]
    for s in res["retrieved"]:
        lines += [f"**[{s['number']}] {s['title']}**", "", s["content"], ""]
    lines.append("---\n")
(out_dir / "label_context.md").write_text("\n".join(lines), encoding="utf-8")

print(f"Wrote {len(records)} items to {out_dir}")