"""
bonus/compare_chunking.py

BONUS TASK (+10 marks): Compare two different chunking strategies using
a simple hit-rate score, as requested in the assignment.

For each of the 10 test questions (excluding the deliberate no-answer
question), we:
  1. Build a temporary FAISS index using strategy A's chunk size/overlap.
  2. Retrieve the top-K chunks for the question.
  3. Count it as a HIT if the expected chapter/part string appears among
     the metadata of the retrieved chunks.
  4. Repeat for strategy B.
  5. Report hit-rate (%) for each strategy.

Run (from the project root):
    python -m bonus.compare_chunking

Requires the pipeline to have already been run once (data/processed/book.jsonl
must exist) and Ollama running locally with the embedding model pulled.
"""
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from langchain_community.vectorstores import FAISS

from config import TOP_K, EMBED_MODEL
from src.chunker import load_processed, chunk_documents
from src.build_index import get_embedder

TESTS_FILE = Path(__file__).resolve().parents[1] / "tests" / "test_questions.json"

# The two strategies being compared. Feel free to edit these, or switch
# to comparing two embedding models instead (see the note at the bottom).
STRATEGIES = {
    "A: chunk_size=500 / overlap=50":   {"chunk_size": 500,  "chunk_overlap": 50},
    "B: chunk_size=1000 / overlap=150": {"chunk_size": 1000, "chunk_overlap": 150},
}


def hit_rate_for_strategy(name: str, params: dict, questions: list, embedder) -> float:
    print(f"\n=== {name} ===")
    docs = load_processed()
    chunks = chunk_documents(
        docs, chunk_size=params["chunk_size"], chunk_overlap=params["chunk_overlap"]
    )
    print(f"  {len(chunks)} chunks created")

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

    # Exclude the deliberate "no answer in book" question from hit-rate
    # scoring — it has no expected_source to match against.
    questions = [q for q in all_questions if not q.get("no_answer_expected")]

    print(f"Evaluating on {len(questions)} question(s) "
          f"(excluded {len(all_questions) - len(questions)} no-answer question).")
    print(f"NOTE: make sure `expected_source` values in tests/test_questions.json "
          f"have been verified against your actual crawled book before trusting "
          f"these numbers (see tests/test_questions.md).")

    embedder = get_embedder(EMBED_MODEL)

    results = {}
    for name, params in STRATEGIES.items():
        results[name] = hit_rate_for_strategy(name, params, questions, embedder)

    print("\n\n=== Summary ===")
    print("| Approach | Hit Rate |")
    print("|---|---|")
    for name, rate in results.items():
        print(f"| {name} | {rate:.1f}% |")

    best = max(results, key=results.get)
    print(f"\nBest performing strategy: {best} ({results[best]:.1f}%)")


if __name__ == "__main__":
    main()
