import psycopg
from pgvector.psycopg import register_vector

from ireland_visa_agent.config import settings

SCHEMA = f"""
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunks (
    id          BIGSERIAL PRIMARY KEY,
    url         TEXT NOT NULL,
    title       TEXT,
    chunk_index INT  NOT NULL,
    content     TEXT NOT NULL,
    embedding   VECTOR({settings.embed_dim}) NOT NULL,
    UNIQUE (url, chunk_index)
);

CREATE INDEX IF NOT EXISTS chunks_embedding_idx
    ON chunks USING hnsw (embedding vector_cosine_ops);

ALTER TABLE chunks ADD COLUMN IF NOT EXISTS tsv tsvector
    GENERATED ALWAYS AS (to_tsvector('english', coalesce(title, '') || ' ' || content)) STORED;

CREATE INDEX IF NOT EXISTS chunks_tsv_idx ON chunks USING gin (tsv);
"""

def init_db() -> None:
    with psycopg.connect(settings.database_url, autocommit=True) as conn:
        conn.execute(SCHEMA)

def get_conn() -> psycopg.Connection:
    conn = psycopg.connect(settings.database_url, autocommit=True)
    register_vector(conn)  # lets psycopg send/receive vectors as Python lists
    return conn