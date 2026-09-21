# কপালকুণ্ডলা — Bangla Knowledge-Base Chatbot (RAG)

A Retrieval-Augmented Generation (RAG) chatbot that answers questions
about **কপালকুণ্ডলা (Kapalkundala)**, a Bengali novel by Bankim Chandra
Chattopadhyay, using **only** the text of the book itself. Every answer
cites the chapter/section it came from, and the bot explicitly says so
when a question can't be answered from the book. Runs **100% locally
and free** using [Ollama](https://ollama.com).

---

## 1. Book Information

| | |
|---|---|
| **Title** | কপালকুণ্ডলা (বঙ্কিমচন্দ্র চট্টোপাধ্যায়, ১৮৭০) |
| **Author** | বঙ্কিমচন্দ্র চট্টোপাধ্যায় (Bankim Chandra Chattopadhyay) |
| **Bengali Wikisource link** | https://bn.wikisource.org/wiki/কপালকুণ্ডলা |
| **Description** | Published in 1866, considered the first major romantic novel in Bengali literature. It tells the story of Kapalkundala, a girl raised in a remote forest by a Kapalik (tantric ascetic), who saves and later marries Nabakumar, a young gentleman from Saptagram — and the tragedy that follows when her past catches up with her. |

> **Book registration reminder:** Don't forget to register this book in
> your class's shared sheet before submitting, and confirm no classmate
> has already claimed it (the assignment requires each student to pick
> a different book). If you need to switch books, only `BOOK_TITLE` in
> `config.py` needs to change — the entire pipeline is generic and
> works for any prose book on bn.wikisource.org.

---

## 2. Project Structure

```
kb-chatbot-bangla/
├── config.py                  # all settings in one place
├── pipeline.py                 # runs the full ingestion pipeline end-to-end
├── app.py                      # Streamlit chat interface
├── requirements.txt
├── src/
│   ├── crawler.py               # Step A: crawl book + all chapter subpages
│   ├── preprocess.py            # Step B: clean HTML -> plain text + metadata
│   ├── chunker.py                # Step B: split text into overlapping chunks
│   ├── build_index.py            # Step C+D: embeddings -> FAISS vector store
│   └── rag_chain.py               # Step E: retriever + LLM + citation prompt
├── data/
│   ├── raw/                       # raw crawled HTML (JSON), gitignored
│   └── processed/                 # cleaned text + chunks (JSONL), gitignored
├── vectorstore/                  # FAISS index, gitignored
├── tests/
│   ├── test_questions.json        # 10 test Q&A (machine-readable)
│   └── test_questions.md          # 10 test Q&A (readable table)
└── bonus/
    ├── compare_chunking.py         # Bonus: chunking strategy A vs B, hit-rate
    └── compare_embeddings.py       # Bonus (alt): embedding model A vs B
```

---

## 3. Setup & Running Instructions

### Required Python version
Python **3.10+**

### 3.1 Install Ollama and pull the models
This project uses your local Ollama installation for both the embedding
model and the LLM — no API keys, no cost.

```bash
# if you don't already have Ollama: https://ollama.com/download

# Embedding model (multilingual, supports Bengali) — you'll need to pull this:
ollama pull bge-m3

# LLM — you already have this per `ollama list`:
#   qwen3:8b

# make sure the Ollama server is running:
ollama serve
```

### 3.2 Install Python dependencies
```bash
cd kb-chatbot-bangla
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

### 3.3 Build the knowledge base (crawl → clean → chunk → embed → index)
```bash
python pipeline.py
```
This will:
1. Crawl **every** chapter/section subpage of কপালকুণ্ডলা from
   bn.wikisource.org (not just the main page) via the MediaWiki API.
2. Clean the HTML into plain Bengali text.
3. Split it into overlapping chunks.
4. Embed every chunk with `bge-m3` via Ollama.
5. Save a FAISS vector index to `vectorstore/faiss_index/`.

### 3.4 Run the chatbot
```bash
streamlit run app.py
```
Open the URL Streamlit prints (usually http://localhost:8501) and start
asking questions in Bengali. Each answer shows an expandable "উৎস দেখুন"
(view source) section with the retrieved chapter(s).

You can also chat from the terminal without Streamlit:
```bash
python -m src.rag_chain
```

---

## 4. Technical Details

### A. Ingestion (crawling)
`src/crawler.py` uses the **MediaWiki API** (`list=allpages` with
`apprefix=<book title>`), not a hard-coded page scraper. This returns
the book's main page **and every subpage** (all খণ্ড/পরিচ্ছেদ chapter
pages), because Wikisource books are structured as MediaWiki subpages
(`Title/Part/Chapter`). This means the crawler works for *any* book
title dropped into `config.py`, and reliably captures the complete
book rather than only the front page.

### B. Chunking & Preprocessing
- **HTML cleaning** (`src/preprocess.py`): strips Wikisource
  boilerplate (edit-section links, reference/footnote blocks, infoboxes,
  navigation tables, TOC) with BeautifulSoup, keeping only `<p>`, `<li>`,
  headings, and `<blockquote>` text content. Footnote markers like
  `[1]` are also stripped.
- **Metadata preserved per page:** `book`, `part` (খণ্ড), `chapter`
  (পরিচ্ছেদ), `title` (full wiki page title), `source_url`.
- **Chunking** (`src/chunker.py`): `RecursiveCharacterTextSplitter`
  from LangChain with:
  - **chunk_size = 800 characters** — large enough to contain a full
    idea/paragraph (important for a narrative prose text where meaning
    spans several sentences), small enough to keep retrieved context
    focused and not dilute the LLM's attention.
  - **chunk_overlap = 150 characters (~19%)** — prevents a sentence or
    idea that spans a chunk boundary from losing context; the
    surrounding chunk always carries a bit of its neighbour's text.
  - **Bengali-aware separators**: `["\n\n", "\n", "।", "?", "!", " ", ""]`
    — includes the Bengali sentence-ending **দাঁড়ি (।)**, so the
    splitter prefers to break on real sentence boundaries instead of
    mid-sentence, unlike a naive English-only splitter that only looks
    for `.`.
  - Every chunk keeps its parent page's metadata (`book`, `part`,
    `chapter`, `source_url`) plus a `chunk_id`.

### C. Embeddings
- **Model used:** `bge-m3` served locally via Ollama
  (`OllamaEmbeddings` from `langchain-ollama`).
- **Why this model:** `bge-m3` is explicitly multilingual (trained on
  100+ languages, including Bengali) and is one of the models the
  assignment itself lists as an example. It is optimized for retrieval
  (dense embeddings tuned for semantic search), runs fully offline via
  Ollama (free, no API key), and produces strong results on
  low-resource languages like Bengali compared to English-only models
  such as `all-MiniLM` or OpenAI's `text-embedding-ada` when applied to
  Devanagari/Bengali script.
- **How it supports Bengali:** it was trained with a multilingual
  corpus and a unified embedding space across languages, so semantically
  similar Bengali sentences/questions map close together in vector
  space even with different surface wording — which is what makes
  semantic retrieval work for a Bengali-language question against
  Bengali-language book chunks.

### D. Vector Database
- **FAISS** (`faiss-cpu`, via `langchain_community.vectorstores.FAISS`).
- Chosen over Chroma for this project because it's a pure local file
  index (no separate server/process), trivial to `save_local` /
  `load_local`, and is more than fast enough for a single-book corpus
  of a few hundred chunks.
- The vector store is queried through a LangChain **retriever**
  (`vectorstore.as_retriever(search_kwargs={"k": TOP_K})`, `TOP_K=6` by
  default in `config.py`) using **plain cosine-similarity search**
  (not MMR/diversity re-ranking) — for a single-book corpus, the
  highest-similarity chunks are consistently the most relevant ones,
  and diversity re-ranking was tested and found to occasionally
  discard the single most relevant chunk in favor of a less relevant
  but more "different" one, which hurt answer quality on narrative
  questions. `debug_retrieval.py` lets you compare both modes for any
  question if you want to re-evaluate this trade-off on your own book.

### E. RAG Pipeline & LLM
- **LLM used:** `qwen3:8b`, served locally via Ollama
  (`ChatOllama` from `langchain-ollama`), `temperature=0` for
  deterministic, fact-grounded answers, `num_ctx=4096` to comfortably
  fit the retrieved context plus the question.
- **Pipeline** (`src/rag_chain.py`):
  1. User's Bengali question →
  2. embedded with the same `bge-m3` model →
  3. FAISS similarity search retrieves top-`k` chunks →
  4. chunks formatted into a Context block (tagged with their
     part/chapter) →
  5. a strict Bengali system prompt instructs the LLM to answer **only**
     from the Context, always append a `উৎস: <part/chapter>` citation,
     and — if the Context doesn't actually contain the answer — reply
     with the exact configured "not found in book" sentence instead of
     guessing →
  6. Qwen3's `<think>...</think>` reasoning traces (if any) are
     stripped before the answer is shown to the user.
- **No-answer handling:** enforced entirely through the system prompt
  rule + a fixed refusal sentence (`NO_ANSWER_PHRASE` in `config.py`),
  and demonstrated by test question #9 (see below), which asks about
  something anachronistic (mobile phones) that cannot appear in an 1866
  novel.

---

## 5. Chat Interface
`app.py` is a Streamlit chat UI (`streamlit run app.py`):
- Text box to type a question in Bengali.
- Streamed chat-style conversation history.
- Every assistant answer has an expandable **"উৎস দেখুন"** panel showing
  the chapter(s)/part(s) and the original Wikisource URL the answer was
  grounded in.

---

## 6. 10 Test Questions
See [`tests/test_questions.md`](tests/test_questions.md) (readable
table) and [`tests/test_questions.json`](tests/test_questions.json)
(used programmatically by the bonus hit-rate script).

⚠️ Please read the note at the top of `test_questions.md` — the exact
chapter citations should be verified/corrected against your own
pipeline run before final submission.

Question 9 is the required "answer not present in the book" test case.

---

## 7. Demo Video Checklist
When recording your 3–5 minute demo:
1. **Pipeline (≈30–60s):** show `python pipeline.py` running (or its
   completed output/logs) — crawling, chunking, embedding, index build.
2. **Questions (≥5):** ask at least 5 of the questions from
   `tests/test_questions.md` in the Streamlit app, showing each answer
   *and* its source citation panel.
3. **No-answer case:** ask question #9 (or a similar out-of-book
   question) and show the chatbot correctly refusing to hallucinate.

---

## 8. Bonus — Chunking Strategy Comparison (+10 marks)
```bash
python -m bonus.compare_chunking
```
This builds two temporary FAISS indexes — **Strategy A** (chunk_size
500 / overlap 50) vs **Strategy B** (chunk_size 1000 / overlap 150) —
and measures **retrieval hit-rate**: for each of the 9 scored test
questions (excluding the deliberate no-answer question), it checks
whether the expected chapter/part appears among the top-`k` retrieved
chunks' metadata. It prints a per-question hit/miss log and a final
summary table, e.g.:

| Approach | Hit Rate |
|---|---|
| A: chunk_size=500 / overlap=50 | 77.8% |
| B: chunk_size=1000 / overlap=150 | 88.9% |

*(Your actual numbers will depend on your crawled book text — run the
script and paste your real results here for submission.)*

**Method:** both strategies re-chunk the same cleaned/preprocessed
pages, embed with the same `bge-m3` model, and query with the same 9
test questions and `TOP_K`, so chunk size/overlap is the only variable
being isolated.

An alternative bonus script, `bonus/compare_embeddings.py`, is also
included in case you'd rather compare two embedding models instead
(requires pulling a second multilingual Ollama embedding model).

---

## RAG Workflow Summary
```
Wikisource (MediaWiki API crawl of all chapters)
        │
        ▼
   HTML Cleaning (BeautifulSoup)  +  metadata (book/part/chapter/url)
        │
        ▼
  Chunking (RecursiveCharacterTextSplitter, Bengali-aware separators)
        │
        ▼
  Embeddings (bge-m3 via Ollama)
        │
        ▼
   FAISS Vector Store  ──►  LangChain Retriever (top-k)
        │
        ▼
  Context + Question → System Prompt → ChatOllama (qwen3:8b)
        │
        ▼
   Final Answer + Chapter Citation  (or explicit "not found in book")
```
