"""
app.py — Streamlit chat interface for the Bangla Knowledge-Base Chatbot.

Run with:  streamlit run app.py
(Run `python pipeline.py` once first to build the index.)
"""
import streamlit as st

from config import BOOK_TITLE
from src.rag_chain import RagChatbot

st.set_page_config(page_title=f"{BOOK_TITLE} — KB Chatbot", page_icon="📚")
st.title(f"📚 {BOOK_TITLE} — জ্ঞানভিত্তিক চ্যাটবট")
st.caption(
    "RAG (Retrieval-Augmented Generation) দিয়ে তৈরি — উত্তর শুধুমাত্র নির্বাচিত "
    "বই থেকে আসে, প্রতিটি উত্তরের সাথে খণ্ড/পরিচ্ছেদের উৎস দেখানো হয়।"
)


@st.cache_resource(show_spinner="মডেল ও ভেক্টর ডেটাবেস লোড হচ্ছে...")
def get_bot():
    return RagChatbot()


try:
    bot = get_bot()
except Exception as e:
    st.error(
        "চ্যাটবট লোড করা যায়নি। নিশ্চিত করুন যে:\n\n"
        "1. Ollama চলছে (টার্মিনালে `ollama serve`)\n"
        "2. মডেল ডাউনলোড করা আছে: `ollama pull bge-m3` এবং `ollama pull qwen3:8b`\n"
        "3. ভেক্টর ইনডেক্স তৈরি করা আছে: `python pipeline.py`\n\n"
        f"বিস্তারিত ত্রুটি: {e}"
    )
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("উৎস দেখুন"):
                for s in msg["sources"]:
                    st.markdown(f"- **{s['chapter']}** — [{s['url']}]({s['url']})")

question = st.chat_input("বই সম্পর্কে একটি প্রশ্ন লিখুন...")
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("খোঁজা হচ্ছে..."):
            result = bot.ask(question)
        st.markdown(result["answer"])
        with st.expander("উৎস দেখুন"):
            for s in result["sources"]:
                st.markdown(f"- **{s['chapter']}** — [{s['url']}]({s['url']})")

    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"],
        "sources": result["sources"],
    })
