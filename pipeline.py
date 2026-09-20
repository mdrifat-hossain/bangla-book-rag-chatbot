"""
pipeline.py — runs the full ingestion pipeline end-to-end:

    Wikisource crawl -> HTML cleaning -> chunking -> embeddings -> FAISS index

Run this once (it can take a few minutes depending on book length and
your machine) before starting the chat app:

    python pipeline.py
"""
from src.crawler import crawl_book
from src.preprocess import preprocess_all
from src.chunker import chunk_documents, save_chunks
from src.build_index import build_index


def main():
    print("STEP 1/4 — Crawling book pages from Bengali Wikisource...")
    crawl_book()

    print("\nSTEP 2/4 — Cleaning & preprocessing pages...")
    preprocess_all()

    print("\nSTEP 3/4 — Chunking text...")
    chunks = chunk_documents()
    save_chunks(chunks)

    print("\nSTEP 4/4 — Generating embeddings & building FAISS index...")
    build_index(chunks)

    print("\n✅ Pipeline complete! Now run the chatbot with:  streamlit run app.py")


if __name__ == "__main__":
    main()
