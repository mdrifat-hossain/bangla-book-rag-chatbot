"""
src/preprocess.py
Cleans the raw HTML pages crawled from Wikisource into plain Bengali
text, attaching book / part (খণ্ড) / chapter (পরিচ্ছেদ) metadata, and
writes one JSONL file: data/processed/book.jsonl
    -> one line per SECTION: {"text": ..., "metadata": {...}}

IMPORTANT DESIGN NOTE
----------------------
Some Wikisource books put the ENTIRE work on one wiki page (rather than
one page per chapter). To still get chapter-level citations in that
case, this module splits each crawled page into sections at every
heading (h1/h2/h3/h4) it finds, in document order, and uses the
heading text itself as the chapter/section label. A page crawled as a
genuine subpage (title already encodes part/chapter) still works the
same way — it just usually has 0-1 headings, so it becomes 1 section
whose label falls back to the page-title-derived chapter.

Text is extracted from the ENTIRE cleaned content container (not just
<p> tags), because Wikisource pages transcluded from proofread scans
often lay out prose as plain text nodes separated by <br> rather than
wrapped in <p> elements. <br> tags are converted to newlines first so
line breaks are preserved instead of words gluing together.
"""
import json
import re

from bs4 import BeautifulSoup

from config import RAW_DIR, PROCESSED_FILE, BOOK_TITLE

# Wikisource boilerplate we never want in the knowledge base
DROP_CLASSES = [
    "mw-editsection", "reference", "references", "reflist", "noprint",
    "mw-cite-backlink", "thumb", "thumbinner", "infobox", "navbox",
    "metadata", "mw-headline-anchor", "printfooter", "catlinks",
    "ws-noexport", "toc", "vector-toc", "sistersitebox",
]
DROP_TAGS = ["table", "sup", "style", "script"]

MIN_SECTION_LEN = 20   # drop near-empty sections


def _clean_soup(html: str) -> BeautifulSoup:
    soup = BeautifulSoup(html, "html.parser")
    for tag in DROP_TAGS:
        for el in soup.find_all(tag):
            el.decompose()
    for cls in DROP_CLASSES:
        for el in soup.find_all(class_=cls):
            el.decompose()
    for br in soup.find_all("br"):
        br.replace_with("\n")
    return soup


def _clean_text(text: str) -> str:
    text = re.sub(r"\[\d+\]", "", text)          # stray footnote markers
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"^[ \t]+|[ \t]+$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_title(title: str):
    """
    'কপালকুণ্ডলা/প্রথম খণ্ড/প্রথম পরিচ্ছেদ'
        -> book='কপালকুণ্ডলা', part='প্রথম খণ্ড', chapter='প্রথম পরিচ্ছেদ'
    'কপালকুণ্ডলা' -> book='কপালকুণ্ডলা', part=None, chapter='প্রধান পাতা'
    """
    segments = title.split("/")
    book = segments[0]
    if len(segments) == 1:
        return book, None, "প্রধান পাতা"
    if len(segments) == 2:
        return book, None, segments[1]
    return book, segments[1], segments[-1]


def extract_sections(html: str, page_title: str) -> list:
    """
    Returns a list of (heading_label, section_text) tuples, splitting
    the cleaned page content at every h1/h2/h3/h4 encountered, in
    document order. Falls back to a single section (using the
    page-title-derived chapter as its label) if no headings exist at
    all — this is normal for a page that's already a single-chapter
    subpage.
    """
    soup = _clean_soup(html)
    container = soup.find("div", class_="mw-parser-output") or soup

    _, _, default_chapter = split_title(page_title)

    blocks = container.find_all(["h1", "h2", "h3", "h4", "p", "li", "blockquote", "dd", "dt"])

    sections = []
    current_label = default_chapter
    current_parts = []

    def flush():
        text = _clean_text("\n".join(current_parts))
        if len(text) >= MIN_SECTION_LEN:
            sections.append((current_label, text))

    for el in blocks:
        if el.name in ("h1", "h2", "h3", "h4"):
            flush()
            current_label = el.get_text(strip=True) or current_label
            current_parts = []
        else:
            t = el.get_text(separator=" ", strip=True)
            if t:
                current_parts.append(t)

    flush()

    # Absolute fallback: no headings AND no p/li/blockquote text was found
    # (e.g. prose sitting as bare text nodes under a wrapper div with no
    # <p> at all) -> grab everything via get_text() as one big section.
    if not sections:
        raw_text = _clean_text(container.get_text(separator="\n"))
        if len(raw_text) >= MIN_SECTION_LEN:
            sections.append((default_chapter, raw_text))

    return sections


def preprocess_all(book_title: str = BOOK_TITLE):
    PROCESSED_FILE.parent.mkdir(parents=True, exist_ok=True)
    raw_files = sorted(RAW_DIR.glob("*.json"))
    if not raw_files:
        raise RuntimeError(f"No raw files found in {RAW_DIR}. Run crawler.py first.")

    records = []
    for path in raw_files:
        page = json.loads(path.read_text(encoding="utf-8"))
        book, part, _ = split_title(page["title"])

        sections = extract_sections(page["html"], page["title"])
        for heading, text in sections:
            records.append({
                "text": text,
                "metadata": {
                    "book": book,
                    "part": part or "",
                    "chapter": heading,
                    "title": page["title"],
                    "source_url": page["url"],
                },
            })

    with open(PROCESSED_FILE, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    total_chars = sum(len(r["text"]) for r in records)
    print(f"Preprocessed {len(raw_files)} raw page(s) -> {len(records)} section(s) "
          f"-> {PROCESSED_FILE}")
    print(f"Total extracted text: {total_chars:,} characters "
          f"(sanity check: a full novel should be tens of thousands of characters+)")
    if total_chars < 5000:
        print("⚠️  WARNING: extracted text looks too short for a full novel. "
              "The crawler likely only captured a landing/index page — "
              "see the troubleshooting note in README.md.")
    return records


if __name__ == "__main__":
    preprocess_all()
