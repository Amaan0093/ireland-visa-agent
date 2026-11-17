from pathlib import Path
from urllib.parse import urldefrag

from ireland_visa_agent.db import init_db
from ireland_visa_agent.ingest import ingest_all

raw = [u.strip() for u in Path("data/sources.txt").read_text().splitlines() if u.strip()]
urls = list(dict.fromkeys(urldefrag(u).url for u in raw))  # strip #fragments, de-duplicate, keep order
print(f"{len(raw)} lines -> {len(urls)} unique pages")

init_db()
ingest_all(urls)