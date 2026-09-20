"""
src/chunker.py
Splits preprocessed pages into overlapping chunks suitable for
embedding, preserving book/part/chapter/source metadata on every chunk.

Chunking choices (see README for full justification):
  - chunk_size    = 800 characters  -> ~2-3 paragraphs, enough context
                     for the LLM to answer without diluting relevance.
  - chunk_overlap = 150 characters  -> preserves continuity across
                     chunk boundaries so a sentence split mid-idea
                     still has its neighbouring context in an
                     adjacent chunk.
  - separators include the Bengali "।" (দাঁড়ি / danda), which is the
    Bengali sentence terminator (the rough equivalent of ".") so the
    splitter prefers breaking on real sentence boundaries instead of
    mid-word.
"""
import json

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from config import PROCESSED_FILE, CHUNK_SIZE, CHUNK_OVERLAP, CHUNKS_FILE

BENGALI_SEPARATORS = ["\n\n", "\n", "।", "?", "!", " ", ""]


def load_processed():
    docs = []
    with open(PROCESSED_FILE, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            docs.append(Document(page_content=rec["text"], metadata=rec["metadata"]))
    return docs


def chunk_documents(docs=None, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
    docs = docs if docs is not None else load_processed()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=BENGALI_SEPARATORS,
        length_function=len,
    )
    chunks = splitter.split_documents(docs)

    for i, c in enumerate(chunks):
        c.metadata["chunk_id"] = i
        c.metadata["chunk_size"] = chunk_size
        c.metadata["chunk_overlap"] = chunk_overlap

    return chunks


def save_chunks(chunks, path=CHUNKS_FILE):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(
                {"text": c.page_content, "metadata": c.metadata}, ensure_ascii=False
            ) + "\n")
    print(f"Saved {len(chunks)} chunk(s) -> {path}")


if __name__ == "__main__":
    _chunks = chunk_documents()
    save_chunks(_chunks)
