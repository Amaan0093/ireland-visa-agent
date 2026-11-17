import numpy as np

from ireland_visa_agent.db import get_conn
from ireland_visa_agent.embeddings import embed_query

# ---------- SQL ----------

VECTOR_SQL = """
SELECT url, title, content, 1 - (embedding <=> %(vec)s) AS score
FROM chunks
ORDER BY embedding <=> %(vec)s
LIMIT %(k)s
"""

HYBRID_SQL = """
WITH q AS (
    SELECT replace(plainto_tsquery('english', %(text)s)::text, '&', '|')::tsquery AS query
),
semantic AS (
    SELECT id, row_number() OVER (ORDER BY embedding <=> %(vec)s) AS rank
    FROM chunks
    ORDER BY embedding <=> %(vec)s
    LIMIT 20
),
keyword AS (
    SELECT id, row_number() OVER (ORDER BY ts_rank_cd(tsv, q.query) DESC) AS rank
    FROM chunks, q
    WHERE tsv @@ q.query
    ORDER BY ts_rank_cd(tsv, q.query) DESC
    LIMIT 20
)
SELECT c.url, c.title, c.content,
       coalesce(1.0 / (60 + s.rank), 0) + coalesce(1.0 / (60 + k.rank), 0) AS score
FROM semantic s
FULL OUTER JOIN keyword k ON s.id = k.id
JOIN chunks c ON c.id = coalesce(s.id, k.id)
ORDER BY score DESC
LIMIT %(k)s
"""

# ---------- Search functions ----------

def _run(sql: str, query: str, k: int) -> list[dict]:
    vec = np.array(embed_query(query))
    with get_conn() as conn:
        rows = conn.execute(sql, {"text": query, "vec": vec, "k": k}).fetchall()
    return [{"url": u, "title": t, "content": c, "score": float(s)} for u, t, c, s in rows]

def vector_search(query: str, k: int = 5) -> list[dict]:
    return _run(VECTOR_SQL, query, k)

def hybrid_search(query: str, k: int = 5) -> list[dict]:
    return _run(HYBRID_SQL, query, k)