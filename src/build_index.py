"""
src/build_index.py
Embeds every chunk with a local, free, multilingual Ollama embedding
model (bge-m3 by default — supports 100+ languages including Bengali)
and stores the vectors in a FAISS index on disk.
"""
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings

from config import EMBED_MODEL, VECTORSTORE_DIR, OLLAMA_BASE_URL
from src.chunker import chunk_documents, save_chunks


def get_embedder(model: str = EMBED_MODEL) -> OllamaEmbeddings:
    return OllamaEmbeddings(model=model, base_url=OLLAMA_BASE_URL)


def build_index(chunks=None, persist_dir: Path = VECTORSTORE_DIR, embed_model: str = EMBED_MODEL):
    if chunks is None:
        chunks = chunk_documents()
        save_chunks(chunks)

    if not chunks:
        raise RuntimeError("No chunks to embed. Run preprocess.py and chunker.py first.")

    embedder = get_embedder(embed_model)
    print(f"Embedding {len(chunks)} chunk(s) with Ollama model '{embed_model}' "
          f"(this calls your local Ollama server — make sure `ollama serve` is running)...")
    vectorstore = FAISS.from_documents(chunks, embedder)

    persist_dir.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(persist_dir))
    print(f"FAISS index saved -> {persist_dir}")
    return vectorstore


def load_index(persist_dir: Path = VECTORSTORE_DIR, embed_model: str = EMBED_MODEL) -> FAISS:
    if not persist_dir.exists():
        raise RuntimeError(
            f"No FAISS index found at {persist_dir}. Run `python pipeline.py` "
            f"(or `python -m src.build_index`) first."
        )
    embedder = get_embedder(embed_model)
    return FAISS.load_local(str(persist_dir), embedder, allow_dangerous_deserialization=True)


if __name__ == "__main__":
    build_index()
