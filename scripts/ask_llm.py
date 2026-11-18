import sys

from ireland_visa_agent.rag import answer_question

result = answer_question(" ".join(sys.argv[1:]))
print(result.answer, "\n")
for s in result.cited:
    print(f"[{s.number}] {s.title}\n    {s.url}")
for sentence in result.uncited:
    print(f"\n⚠ Uncited: {sentence}")