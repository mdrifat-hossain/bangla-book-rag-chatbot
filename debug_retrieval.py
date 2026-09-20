"""
debug_retrieval.py
Inspect exactly what text gets retrieved for a question, WITHOUT
involving the LLM at all. Use this to tell apart two different
problems:
  (a) retrieval is missing the right passage (fix: TOP_K, embedding
      model, chunk size, or rephrase the question)
  (b) retrieval found the right passage but the LLM ignored/misused it
      (fix: prompt strength, temperature, or model choice)

Run:
    python debug_retrieval.py "আপনার প্রশ্ন এখানে লিখুন"
"""
import sys

from src.build_index import load_index
from config import TOP_K


def main():
    if len(sys.argv) < 2:
        print('Usage: python debug_retrieval.py "প্রশ্ন"')
        sys.exit(1)

    question = sys.argv[1]
    vectorstore = load_index()

    print(f"\n=== Plain similarity search (k={TOP_K}) ===")
    for i, doc in enumerate(vectorstore.similarity_search(question, k=TOP_K), 1):
        m = doc.metadata
        print(f"\n[{i}] {m.get('part')} / {m.get('chapter')}")
        print(doc.page_content[:400].replace("\n", " "))

    print(f"\n\n=== MMR search (k={TOP_K}, fetch_k={TOP_K * 5}) ===")
    for i, doc in enumerate(
        vectorstore.max_marginal_relevance_search(question, k=TOP_K, fetch_k=TOP_K * 5), 1
    ):
        m = doc.metadata
        print(f"\n[{i}] {m.get('part')} / {m.get('chapter')}")
        print(doc.page_content[:400].replace("\n", " "))


if __name__ == "__main__":
    main()
