"""
src/crawler.py
Crawls a book (and ALL of its chapter/section subpages) from Bengali
Wikisource using the official MediaWiki API — not a fragile HTML scraper.

How it works
------------
Bengali Wikisource (like all MediaWiki wikis) organizes multi-page works
as "subpages": e.g. a book titled "X" has chapters at "X/প্রথম খণ্ড/প্রথম
পরিচ্ছেদ", "X/প্রথম খণ্ড/দ্বিতীয় পরিচ্ছেদ", etc. The `list=allpages`
endpoint with `apprefix=X` returns every page whose title starts with
"X", which is exactly every chapter/subpage of the book. This approach
is generic and works for *any* book title, not just one hard-coded book.

Each page's rendered HTML is then fetched via `action=parse` and saved
as raw JSON to data/raw/. preprocess.py cleans this HTML afterwards.
"""
import json
import re
import time
from pathlib import Path

import requests
from tqdm import tqdm

from config import BOOK_TITLE, WIKI_API, RAW_DIR, REQUEST_DELAY_SEC

HEADERS = {"User-Agent": "KB-Chatbot-Assignment/1.0 (educational RAG project)"}

# Used only as a fallback discovery signal (see discover_chapter_links below)
CHAPTER_HINT_WORDS = ["খণ্ড", "পরিচ্ছেদ", "অধ্যায়", "পর্ব", "ভাগ", "কাণ্ড"]


def _api_get(params: dict, max_retries: int = 6):
    """GET against the MediaWiki API with automatic retry/backoff on
    HTTP 429 (rate limiting) — Wikisource will throttle a fast crawl,
    so this is essential for reliably pulling every chapter."""
    backoff = 2.0
    for attempt in range(1, max_retries + 1):
        resp = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=30)
        if resp.status_code == 429:
            wait = float(resp.headers.get("Retry-After", backoff))
            print(f"    [rate limited] waiting {wait:.1f}s "
                  f"(retry {attempt}/{max_retries})...")
            time.sleep(wait)
            backoff = min(backoff * 2, 30)
            continue
        resp.raise_for_status()
        return resp.json()
    raise RuntimeError(
        f"Still rate-limited after {max_retries} retries. Wikisource is asking "
        f"us to slow down further — try raising REQUEST_DELAY_SEC in config.py "
        f"(e.g. to 1.0 or 1.5) and re-run; already-downloaded pages are skipped "
        f"automatically so this just resumes."
    )


def get_all_subpage_titles(book_title: str) -> list:
    """Return the book's main page title plus every chapter/subpage title."""
    titles = []
    apcontinue = None

    while True:
        params = {
            "action": "query",
            "list": "allpages",
            "apprefix": book_title,
            "aplimit": "500",
            "apnamespace": "0",       # main content namespace only
            "format": "json",
        }
        if apcontinue:
            params["apcontinue"] = apcontinue

        data = _api_get(params)

        for page in data.get("query", {}).get("allpages", []):
            title = page["title"]
            # Keep only the book itself or genuine subpages ("Book/...")
            if title == book_title or title.startswith(book_title + "/"):
                titles.append(title)

        cont = data.get("continue", {})
        apcontinue = cont.get("apcontinue")
        if not apcontinue:
            break
        time.sleep(REQUEST_DELAY_SEC)

    return titles


def get_links_from_page(title: str) -> list:
    """All namespace-0 (article) internal links found on a given page."""
    titles = []
    plcontinue = None
    while True:
        params = {
            "action": "query",
            "prop": "links",
            "titles": title,
            "plnamespace": "0",
            "pllimit": "500",
            "format": "json",
        }
        if plcontinue:
            params["plcontinue"] = plcontinue

        data = _api_get(params)

        pages = data.get("query", {}).get("pages", {})
        for p in pages.values():
            for link in p.get("links", []):
                titles.append(link["title"])

        cont = data.get("continue", {})
        plcontinue = cont.get("plcontinue")
        if not plcontinue:
            break
        time.sleep(REQUEST_DELAY_SEC)

    return titles


def discover_chapter_links(main_title: str, book_title: str) -> list:
    """
    Fallback discovery for books whose chapter pages are NOT literal
    'BookTitle/...' subpages (some Wikisource books link out to
    separately-titled chapter pages from a table-of-contents on the
    main page instead). Scans every internal link on the main page and
    keeps ones that look like a part/chapter page based on common
    Bengali structural words (খণ্ড, পরিচ্ছেদ, অধ্যায়, etc.), even if
    they don't share the exact literal book_title prefix.
    """
    links = get_links_from_page(main_title)
    hits = []
    for t in links:
        if t == book_title or t.startswith(book_title + "/"):
            continue  # already covered by the subpage search
        if any(word in t for word in CHAPTER_HINT_WORDS):
            hits.append(t)
    # de-duplicate while preserving order
    seen = set()
    unique_hits = []
    for t in hits:
        if t not in seen:
            seen.add(t)
            unique_hits.append(t)
    return unique_hits


def fetch_rendered_html(title: str) -> dict:
    """Fetch the rendered HTML body of a single wiki page."""
    params = {
        "action": "parse",
        "page": title,
        "prop": "text|displaytitle",
        "format": "json",
        "redirects": 1,
    }
    data = _api_get(params)
    if "error" in data:
        raise RuntimeError(f"API error for '{title}': {data['error']}")

    html = data["parse"]["text"]["*"]
    return {
        "title": title,
        "url": f"https://bn.wikisource.org/wiki/{title.replace(' ', '_')}",
        "html": html,
    }


def slugify(title: str) -> str:
    slug = re.sub(r"[^\w\-]+", "_", title, flags=re.UNICODE)
    return slug.strip("_")[:150]


def crawl_book(book_title: str = BOOK_TITLE) -> list:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    titles = get_all_subpage_titles(book_title)
    if not titles:
        raise RuntimeError(
            f"No pages found for '{book_title}'. Open the book on "
            f"bn.wikisource.org and copy the EXACT title from the URL "
            f"(after /wiki/, with underscores turned back into spaces) "
            f"into config.py's BOOK_TITLE."
        )

    print(f"Found {len(titles)} page(s) via subpage search for '{book_title}':")
    for t in titles:
        print("  -", t)

    # Fallback: some books link to separately-titled chapter pages from
    # the main page's table of contents instead of using literal
    # 'Book/Chapter' subpage titles. If the subpage search barely found
    # anything, check the main page's own links for chapter-like pages.
    if len(titles) <= 1:
        print(
            "\nOnly the main page was found via subpage search. Checking its "
            "internal links for additional chapter pages "
            "(fallback for books that don't use '/' subpage titles)..."
        )
        extra = discover_chapter_links(book_title, book_title)
        if extra:
            print(f"Found {len(extra)} additional linked chapter page(s):")
            for t in extra:
                print("  -", t)
            titles.extend(extra)
        else:
            print(
                "No additional chapter-like links found either. The book may "
                "genuinely be a single page, OR its chapter links use naming "
                "this heuristic doesn't recognize — open the page in your "
                "browser to check manually if the crawl still looks "
                "incomplete after this run."
            )

    saved_paths = []
    for title in tqdm(titles, desc="Crawling pages"):
        out_path = RAW_DIR / f"{slugify(title)}.json"
        if out_path.exists():
            saved_paths.append(out_path)
            continue
        try:
            page = fetch_rendered_html(title)
        except Exception as e:
            print(f"  [WARN] failed to fetch '{title}': {e}")
            continue
        out_path.write_text(
            json.dumps(page, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        saved_paths.append(out_path)
        time.sleep(REQUEST_DELAY_SEC)

    print(f"\nSaved {len(saved_paths)} raw page(s) to {RAW_DIR}")
    return saved_paths


if __name__ == "__main__":
    crawl_book()
