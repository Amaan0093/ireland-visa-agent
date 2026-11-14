import math

from ireland_visa_agent.db import init_db
from ireland_visa_agent.embeddings import embed_documents, embed_query

def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))

docs = [
    "Graduates apply for the Third Level Graduate Programme after receiving their final results.",
    "An employment permit requires a job offer from an Irish employer.",
    "Dublin Bus fares can be paid with a Leap card.",
]
query = embed_query("When can I apply for Stamp 1G after my exams?")

for doc, vec in zip(docs, embed_documents(docs)):
    print(f"{cosine(query, vec):.3f}  {doc}")

init_db()
print("Database schema ready")