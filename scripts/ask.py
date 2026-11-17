import sys

from ireland_visa_agent.search import hybrid_search, vector_search

query = " ".join(sys.argv[1:])
for name, fn in [("VECTOR", vector_search), ("HYBRID", hybrid_search)]:
    print(f"\n===== {name} =====")
    for r in fn(query):
        print(f"[{r['score']:.4f}] {r['url'].rstrip('/').rsplit('/', 1)[-1]}")
        print(f"    {r['content'][:150]!r}")