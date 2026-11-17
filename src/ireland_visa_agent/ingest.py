import time

import httpx
import numpy as np
from bs4 import BeautifulSoup

from ireland_visa_agent.db import get_conn
from ireland_visa_agent.embeddings import embed_documents

HEADERS = {"User-Agent": "ireland-visa-agent/0.1 (student portfolio project)"}

def fetch_html(url: str) -> str:
    resp = httpx.get(url, headers=HEADERS, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    return resp.text

CANDIDATES = ["article", "main", "[role=main]", ".entry-content", "#content"]
JUNK_TAGS = ["nav", "header", "footer", "script", "style", "aside", "noscript",
             "button", "input", "select", "textarea"]
JUNK_HINTS = ("cookie", "consent", "breadcrumb", "feedback", "back-to-top")
MIN_CHARS = 500

def remove_section_menus(soup: BeautifulSoup) -> None:
    """irishimmigration.ie pages start with an 'In This Section' heading followed by a list of links."""
    for text in soup.find_all(string=lambda s: s and s.strip() == "In This Section"):
        title = text.find_parent(class_="fusion-title")
        if title is None:
            continue
        menu = title.find_next_sibling()
        if menu is not None:
            menu.decompose()
        title.decompose()

def clean_html(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else ""

    for tag in soup.find_all(JUNK_TAGS):
        tag.decompose()
    for tag in soup.find_all(True):
        if tag.decomposed or tag.name in ("html", "body"):
            continue
        hints = " ".join([tag.get("id") or "", *tag.get("class", [])]).lower()
        if any(h in hints for h in JUNK_HINTS):
            tag.decompose()
    remove_section_menus(soup)

    main = next(
        (el for sel in CANDIDATES for el in soup.select(sel)
         if len(el.get_text(strip=True)) >= MIN_CHARS),
        soup.body,
    )
    lines = [line.strip() for line in main.get_text("\n").splitlines()]
    text = "\n".join(line for line in lines if line)

    if len(text) < MIN_CHARS:
        raise ValueError(f"Only {len(text)} characters extracted - check this page's HTML")
    return title, text

def chunk_text(text: str, max_chars: int = 1000) -> list[str]:
    paragraphs = [p for p in text.split("\n") if p.strip()]
    chunks: list[str] = []
    current = ""
    for p in paragraphs:
        if current and len(current) + len(p) + 1 > max_chars:
            chunks.append(current)
            current = current.rsplit("\n", 1)[-1]  # overlap: carry the last paragraph forward
        current = f"{current}\n{p}" if current else p
    if current:
        chunks.append(current)
    return chunks

def ingest_html(url: str, html: str) -> int:
    title, text = clean_html(html)
    chunks = chunk_text(text)
    vectors = embed_documents([f"{title}\n{c}" for c in chunks])

    with get_conn() as conn, conn.transaction():
        conn.execute("DELETE FROM chunks WHERE url = %s", (url,))
        conn.cursor().executemany(
            "INSERT INTO chunks (url, title, chunk_index, content, embedding) "
            "VALUES (%s, %s, %s, %s, %s)",
            [(url, title, i, c, np.array(v)) for i, (c, v) in enumerate(zip(chunks, vectors))],
        )
    return len(chunks)

def ingest_url(url: str) -> int:
    return ingest_html(url, fetch_html(url))

def ingest_all(urls: list[str]) -> None:
    for url in urls:
        try:
            print(f"{ingest_url(url):3d} chunks  {url}")
        except httpx.HTTPError as e:
            print(f"  FAILED  {url}  ({e})")
        time.sleep(1)  # be polite to a government server