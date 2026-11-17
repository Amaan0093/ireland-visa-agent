import csv
from pathlib import Path

from ireland_visa_agent.db import get_conn, init_db
from ireland_visa_agent.ingest import ingest_html

with open("data/manual_pages.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

init_db()
for row in rows:
    html = Path("data/html", row["file"]).read_text(encoding="utf-8", errors="ignore")
    print(f"{ingest_html(row['url'], html):3d} chunks  {row['url']}")

urls = [row["url"] for row in rows]
with get_conn() as conn:
    removed = conn.execute("DELETE FROM chunks WHERE url <> ALL(%s)", (urls,)).rowcount
print(f"Removed {removed} chunks from pages no longer in the list")