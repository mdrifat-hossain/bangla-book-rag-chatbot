"""
src/rag_chain.py
The complete RAG pipeline:
    User Question -> Query Embedding -> FAISS Search -> Context ->
    LLM (local Ollama qwen3:8b) -> Final Answer + Citation

The system prompt forces the model to:
  1. answer using ONLY the retrieved context,
  2. always cite the part/chapter it drew the answer from,
  3. explicitly say the answer isn't in the book when the retrieved
     context doesn't actually contain it (no hallucination).
"""
import re

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from config import LLM_MODEL, TOP_K, OLLAMA_BASE_URL, LLM_NUM_CTX, NO_ANSWER_PHRASE
from src.build_index import load_index

SYSTEM_PROMPT = """তুমি একজন সহায়ক বাংলা প্রশ্নোত্তর সহকারী, যে শুধুমাত্র নিচে দেওয়া বইয়ের অংশ (Context) থেকে উত্তর দাও।

নিয়ম (কঠোরভাবে মেনে চলো, কোনো ব্যতিক্রম নেই):
1. শুধুমাত্র Context-এ থাকা তথ্য ব্যবহার করে উত্তর দাও। নিজের প্রশিক্ষণের জ্ঞান, অনুমান, বা বাইরের তথ্য থেকে একটি শব্দও যোগ করবে না।
2. Context-এ উল্লেখ নেই এমন কোনো বই, লেখক, চরিত্র বা গল্পের নাম কখনোই উল্লেখ করবে না — এমনকি "যদি এটি অমুক বই হয়" জাতীয় অনুমানও করবে না। এটি একটি গুরুতর নিয়ম ভঙ্গ।
3. উত্তর সঠিক ও নিশ্চিত হলে, উত্তরের শেষে অবশ্যই উৎস উল্লেখ করবে এই ফরম্যাটে: "উৎস: <খণ্ড/পরিচ্ছেদ>"।
4. যদি Context-এ প্রশ্নের সুনির্দিষ্ট উত্তর না থাকে, Context অপ্রাসঙ্গিক হয়, অথবা তুমি নিশ্চিত না হও, তাহলে অন্য কিছু না লিখে ঠিক এই বাক্যটি লিখো, একটি শব্দও বেশি না:
   "{no_answer}"
5. উত্তর সংক্ষিপ্ত, স্পষ্ট ও বাংলায় দাও। ইংরেজিতে উত্তর দেবে না। কোনো ভূমিকা বা দ্বিধা প্রকাশ করে বাক্য শুরু করবে না।

Context:
{context}
"""

USER_PROMPT = "প্রশ্ন: {question}"

THINK_TAG_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def strip_thinking(text: str) -> str:
    """Qwen3 may emit <think>...</think> reasoning traces before the real
    answer; strip them so only the final answer reaches the user."""
    return THINK_TAG_RE.sub("", text).strip()


def format_docs(docs) -> str:
    blocks = []
    for d in docs:
        meta = d.metadata
        loc = " / ".join([x for x in [meta.get("part"), meta.get("chapter")] if x])
        blocks.append(f"[{loc or meta.get('title')}]\n{d.page_content}")
    return "\n\n---\n\n".join(blocks)


class RagChatbot:
    def __init__(self, k: int = TOP_K, llm_model: str = LLM_MODEL):
        self.vectorstore = load_index()
        self.retriever = self.vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": k, "fetch_k": max(k * 5, 20), "lambda_mult": 0.5},
        )
        self.llm = ChatOllama(
            model=llm_model,
            base_url=OLLAMA_BASE_URL,
            temperature=0,
            num_ctx=LLM_NUM_CTX,
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", USER_PROMPT),
        ])

    def ask(self, question: str) -> dict:
        docs = self.retriever.invoke(question)
        context = format_docs(docs)
        messages = self.prompt.format_messages(
            context=context, question=question, no_answer=NO_ANSWER_PHRASE
        )
        response = self.llm.invoke(messages)
        answer = strip_thinking(response.content)

        sources = []
        for d in docs:
            m = d.metadata
            loc = " / ".join([x for x in [m.get("part"), m.get("chapter")] if x])
            sources.append({"chapter": loc or m.get("title"), "url": m.get("source_url")})

        return {"answer": answer, "sources": sources, "retrieved_docs": docs}


if __name__ == "__main__":
    bot = RagChatbot()
    print("চ্যাটবট প্রস্তুত। প্রশ্ন লিখুন (বের হতে 'exit' লিখুন)।\n")
    while True:
        q = input("প্রশ্ন: ")
        if q.strip().lower() in {"exit", "quit"}:
            break
        result = bot.ask(q)
        print("\nউত্তর:", result["answer"])
        print("উৎসসমূহ:")
        for s in result["sources"]:
            print(" -", s["chapter"], "|", s["url"])
        print()
