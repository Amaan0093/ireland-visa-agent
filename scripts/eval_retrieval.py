import csv

from ireland_visa_agent.search import hybrid_search, vector_search

METHODS = {"vector": vector_search, "hybrid": hybrid_search}
K = 5

with open("data/eval_retrieval.csv", newline="", encoding="utf-8") as f:
    cases = list(csv.DictReader(f))

totals = {name: {"hits": 0, "rr": 0.0} for name in METHODS}

for case in cases:
    cells = []
    for name, search in METHODS.items():
        urls = [r["url"] for r in search(case["question"], k=K)]
        expected = case["expected"].split("|")
        rank = next((i + 1 for i, u in enumerate(urls) if any(e in u for e in expected)), None)
        if rank:
            totals[name]["hits"] += 1
            totals[name]["rr"] += 1 / rank
        cells.append(f"{name}={rank or '-'}")
    print(f"{'  '.join(cells):22} {case['question']}")

n = len(cases)
print()
for name, t in totals.items():
    print(f"{name:7} hit@{K} = {t['hits']}/{n}   MRR = {t['rr'] / n:.2f}")