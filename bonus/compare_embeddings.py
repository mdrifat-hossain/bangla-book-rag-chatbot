"""
bonus/compare_embeddings.py

OPTIONAL alternative bonus comparison: instead of two chunking
strategies (see compare_chunking.py), this compares two different
multilingual embedding models using the same hit-rate methodology.
Only run this if you additionally `ollama pull` a second embedding
model, e.g.:

    ollama pull bge-m3
    ollama pull paraphrase-multilingual   # or any other multilingual embed model you have

Run:  python -m bonus.compare_embeddings
"""
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from langchain_community.vectorstores import FAISS

from config import TOP_K, CHUNK_SIZE, CHUNK_OVERLAP
from src.chunker import chunk_documents
from src.build_index import get_embedder

TESTS_FILE = Path(__file__).resolve().parents[1] / "tests" / "test_questions.json"

# Edit these to any two embedding models you have pulled in Ollama.
EMBED_MODELS = ["bge-m3", "paraphrase-multilingual"]


def hit_rate_for_model(model_name: str, chunks, questions) -> float:
    print(f"\n=== Embedding model: {model_name} ===")
    embedder = get_embedder(model_name)
    vs = FAISS.from_documents(chunks, embedder)

    hits = 0
    for q in questions:
        expected = q["expected_source"] or ""
        results = vs.similarity_search(q["question"], k=TOP_K)
        found = any(
            expected.strip() and expected.strip() in
            (r.metadata.get("chapter", "") + " " + r.metadata.get("part", ""))
            for r in results
        )
        hits += int(found)
        print(f"  [{'HIT ' if found else 'MISS'}] {q['question'][:60]}")

    rate = hits / len(questions) * 100 if questions else 0.0
    print(f"  -> Hit rate: {rate:.1f}% ({hits}/{len(questions)})")
    return rate


def main():
    with open(TESTS_FILE, encoding="utf-8") as f:
        all_questions = json.load(f)
    questions = [q for q in all_questions if not q.get("no_answer_expected")]

    chunks = chunk_documents(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

    results = {}
    for model in EMBED_MODELS:
        try:
            results[model] = hit_rate_for_model(model, chunks, questions)
        except Exception as e:
            print(f"  [SKIPPED] '{model}' failed (is it pulled in Ollama?): {e}")

    print("\n\n=== Summary ===")
    print("| Embedding Model | Hit Rate |")
    print("|---|---|")
    for name, rate in results.items():
        print(f"| {name} | {rate:.1f}% |")


if __name__ == "__main__":
    main()
