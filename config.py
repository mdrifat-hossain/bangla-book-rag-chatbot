"""
config.py — central configuration for the Bangla Knowledge-Base Chatbot.

IMPORTANT: Edit BOOK_TITLE below to the *exact* page title of your
registered book on bn.wikisource.org (spelling/spacing must match the
wiki page title exactly, e.g. as it appears in the page URL after
/wiki/, with underscores replaced by spaces).
"""
from pathlib import Path

# ---------------------------------------------------------------------
# Book selection
# ---------------------------------------------------------------------
BOOK_TITLE = "কপালকুণ্ডলা"          # <-- CHANGE THIS to your registered book
WIKI_API = "https://bn.wikisource.org/w/api.php"

# ---------------------------------------------------------------------
# Crawling
# ---------------------------------------------------------------------
REQUEST_DELAY_SEC = 0.3               # be polite to Wikisource's servers

# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_FILE = BASE_DIR / "data" / "processed" / "book.jsonl"
CHUNKS_FILE = BASE_DIR / "data" / "processed" / "chunks.jsonl"
VECTORSTORE_DIR = BASE_DIR / "vectorstore" / "faiss_index"

# ---------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------
CHUNK_SIZE = 800          # characters
CHUNK_OVERLAP = 150       # characters (~19% overlap)

# ---------------------------------------------------------------------
# Embeddings / LLM — both served locally & free via Ollama
# ---------------------------------------------------------------------
OLLAMA_BASE_URL = "http://localhost:11434"
EMBED_MODEL = "qwen3-embedding:0.6b"       # multilingual, strong on Bengali.
LLM_MODEL = "qwen3:8b"       # already in your `ollama list`
LLM_NUM_CTX = 4096           # generous context window for retrieved chunks

# ---------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------
TOP_K = 6

NO_ANSWER_PHRASE = "দুঃখিত, এই বইয়ে এই প্রশ্নের উত্তর পাওয়া যায়নি।"
