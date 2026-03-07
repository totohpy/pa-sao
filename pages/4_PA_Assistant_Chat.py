import streamlit as st
import pandas as pd
from openai import OpenAI
import os, time
from PyPDF2 import PdfReader

import sys, pathlib
_here = pathlib.Path(__file__).resolve().parent
for _p in [_here.parent, _here, pathlib.Path(os.getcwd())]:
    if (_p / "theme.py").exists():
        if str(_p) not in sys.path: sys.path.insert(0, str(_p))
        break
try:
    from theme import apply_theme, SIDEBAR_HTML, render_ai_sidebar
except ImportError:
    def apply_theme(): pass
    def render_ai_sidebar(): pass
    SIDEBAR_HTML = ""

st.set_page_config(page_title="PA Assistant Chat", page_icon="💬", layout="wide")
apply_theme()

with st.sidebar:
    st.markdown(SIDEBAR_HTML, unsafe_allow_html=True)
    render_ai_sidebar()

st.title("💬 PA Assistant Chat")
st.markdown("ถาม-ตอบผู้ช่วยอัจฉริยะ อ้างอิงคู่มือการปฏิบัติงานและผลการตรวจสอบที่ผ่านมา")

# ══════════════════════════════════════════════════════
# RAG SYSTEM — Typhoon Embeddings
# ══════════════════════════════════════════════════════

CHUNK_SIZE    = 600   # ตัวอักษรต่อ chunk
CHUNK_OVERLAP = 100   # overlap ระหว่าง chunk
TOP_K         = 6     # จำนวน chunk ที่เลือกมาตอบ

def split_chunks(text: str, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP) -> list[str]:
    """แบ่งข้อความเป็น chunks มี overlap"""
    chunks, i = [], 0
    while i < len(text):
        chunks.append(text[i:i+size])
        i += size - overlap
    return [c.strip() for c in chunks if c.strip()]

def tfidf_retrieve(query: str, chunks: list[str], top_k=TOP_K) -> str:
    """
    TF-IDF RAG: ให้คะแนนแต่ละ chunk ตามความเกี่ยวข้องกับคำถาม
    - นับความถี่คำ (TF)
    - ให้คะแนน bigram (คู่คำ) เพื่อเพิ่มความแม่นยำ
    - เรียงตาม index เพื่อรักษาลำดับเนื้อหาเมื่อ top_k > 1
    """
    # แยกคำและสร้าง bigram จากคำถาม
    words  = [w for w in query.split() if len(w) > 1]
    bigrams = [words[i] + words[i+1] for i in range(len(words)-1)]

    scored = []
    for i, chunk in enumerate(chunks):
        score = 0.0
        for w in words:
            score += chunk.count(w) * 1.0
        for bg in bigrams:
            score += chunk.count(bg) * 2.0   # bigram ให้น้ำหนักมากกว่า
        # boost ส่วนต้นเอกสาร (มักเป็นสรุป/หัวข้อ)
        if i < 5:
            score += 0.5
        scored.append((score, i))

    scored.sort(reverse=True)
    top_indices = sorted([idx for _, idx in scored[:top_k]])
    return "\n\n---\n\n".join(chunks[i] for i in top_indices)

# ── Extract text ───────────────────────────────────────
def extract_text_from_files(files, folder_path="Doc"):
    text = ""
    if os.path.isdir(folder_path):
        for fn in os.listdir(folder_path):
            fp = os.path.join(folder_path, fn)
            try:
                if fn.endswith('.pdf'):
                    with open(fp,'rb') as f:
                        for pg in PdfReader(f).pages: text += pg.extract_text() or ""
                elif fn.endswith('.txt'):
                    with open(fp,'r',encoding='utf-8',errors='ignore') as f: text += f.read()
                elif fn.endswith('.csv'):
                    text += pd.read_csv(fp).to_string()
            except Exception as e: print(f"Error {fn}: {e}")
    if files:
        for file in files:
            try:
                if file.name.endswith('.pdf'):
                    for pg in PdfReader(file).pages: text += pg.extract_text() or ""
                elif file.name.endswith('.txt'): text += file.getvalue().decode("utf-8")
                elif file.name.endswith('.csv'): text += pd.read_csv(file).to_string()
            except: pass
    return text

# ── LLM Providers ─────────────────────────────────────
def build_providers(typhoon_key, openrouter_key, ollama_url, ollama_model):
    providers = []
    hdrs = {"HTTP-Referer":"https://streamlit.io/","X-Title":"PA Chat"}
    if ollama_url and ollama_model:
        providers.append(dict(name="🖥️ Local (Ollama)", key="ollama",
            base_url=ollama_url, model=ollama_model,
            extra_hdrs={}, out_tokens=2048))
    if typhoon_key:
        providers.append(dict(name="☁️ Typhoon", key=typhoon_key,
            base_url="https://api.opentyphoon.ai/v1",
            model="typhoon-v2.5-30b-a3b-instruct",
            extra_hdrs={}, out_tokens=2048))
    if openrouter_key:
        for label, model in [
            ("🔵 Qwen3-8b",          "qwen/qwen3-8b:free"),
            ("🔵 Qwen3-14b",         "qwen/qwen3-14b:free"),
            ("🟢 DeepSeek-R1",       "deepseek/deepseek-r1-0528:free"),
            ("🟢 DeepSeek-V3",       "deepseek/deepseek-v3-0324:free"),
            ("🟡 Llama-3.1-8b",      "meta-llama/llama-3.1-8b-instruct:free"),
            ("🟡 Llama-3.3-70b",     "meta-llama/llama-3.3-70b-instruct:free"),
            ("🟠 Gemma-3-4b",        "google/gemma-3-4b-it:free"),
            ("🟠 Gemma-3-27b",       "google/gemma-3-27b-it:free"),
            ("⚪ Phi-4",             "microsoft/phi-4:free"),
            ("⚪ Mistral-7b",        "mistralai/mistral-7b-instruct:free"),
        ]:
            providers.append(dict(name=label, key=openrouter_key,
                base_url="https://openrouter.ai/api/v1",
                model=model, extra_hdrs=hdrs, out_tokens=1024))
    return providers

# ── Session Init ──────────────────────────────────────
def init_state():
    ss = st.session_state
    ss.setdefault('chatbot_messages', [{"role":"assistant","content":"สวัสดีครับ PA Assistant พร้อมให้บริการครับ"}])
    ss.setdefault('file_context',        "")
    ss.setdefault('doc_chunks',          [])
    ss.setdefault('last_processed_files', set())
    ss.setdefault('last_provider',       "")
    ss.setdefault('use_ollama',          False)
    ss.setdefault('ollama_url',          "http://localhost:11434/v1")
    ss.setdefault('ollama_model',        "typhoon2-8b")

init_state()

# ── Sidebar ────────────────────────────────────────────
with st.sidebar:
    st.markdown("---")
    st.markdown("**⚙️ Local AI (Ollama)**")
    use_ollama = st.toggle("ใช้ Ollama", value=st.session_state.use_ollama, key="toggle_ollama")
    st.session_state.use_ollama = use_ollama
    if use_ollama:
        st.session_state.ollama_url   = st.text_input("URL",        value=st.session_state.ollama_url,   key="inp_url")
        st.session_state.ollama_model = st.text_input("Model name", value=st.session_state.ollama_model, key="inp_model")
        st.caption("https://ollama.com\n`ollama pull typhoon2-8b`")

# ── File Upload + RAG Index ────────────────────────────
with st.expander("📂 อัปโหลดเอกสาร (PDF, TXT, CSV)"):
    uploaded_files = st.file_uploader("เลือกไฟล์...", type=['pdf','txt','csv'], accept_multiple_files=True)

try:    typhoon_key    = st.secrets["api_key"]
except: typhoon_key    = ""
try:    openrouter_key = st.secrets["openrouter_api_key"]
except: openrouter_key = ""

current_files_set = {f.name for f in uploaded_files} if uploaded_files else set()
files_changed = current_files_set != st.session_state.last_processed_files
first_load    = not st.session_state.file_context and (uploaded_files or os.path.isdir("Doc"))

if files_changed or first_load:
    with st.spinner("📖 กำลังอ่านและแบ่ง chunks..."):
        raw_text = extract_text_from_files(uploaded_files)

    if raw_text:
        chunks = split_chunks(raw_text)
        st.session_state.file_context = raw_text
        st.session_state.doc_chunks   = chunks
        st.session_state.last_processed_files = current_files_set
        st.success(f"✅ พร้อมใช้งาน! ({len(raw_text):,} chars · {len(chunks)} chunks)")
    else:
        st.warning("ยังไม่มีข้อมูลเอกสาร")

# แสดงสถานะ
col_s1, col_s2 = st.columns(2)
with col_s1:
    if st.session_state.doc_chunks:
        st.caption(f"🟢 RAG พร้อม · {len(st.session_state.doc_chunks)} chunks")
    else:
        st.caption("⚪ ยังไม่มีเอกสาร")
with col_s2:
    if st.session_state.last_provider:
        st.caption(f"Provider: {st.session_state.last_provider}")

# ── Chat UI ───────────────────────────────────────────
chat_container = st.container(height=450, border=True)
with chat_container:
    for msg in st.session_state.chatbot_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

if prompt := st.chat_input("พิมพ์คำถามของคุณ...", key="chat_input_main"):
    st.session_state.chatbot_messages.append({"role":"user","content":prompt})
    with chat_container:
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            placeholder = st.empty()
            try:
                # ── RAG: ดึง context ที่เกี่ยวข้อง ──────────────
                chunks = st.session_state.doc_chunks
                if chunks:
                    context = tfidf_retrieve(prompt, chunks, top_k=TOP_K)
                else:
                    context = "ไม่พบข้อมูลในเอกสาร ตอบตามความรู้ทั่วไป"

                sys_msg = (
                    "คุณคือ PA Assistant ผู้เชี่ยวชาญการตรวจสอบผลสัมฤทธิ์ภาครัฐ\n"
                    "ตอบคำถามโดยอ้างอิงเนื้อหาต่อไปนี้ "
                    "ถ้าไม่พบให้บอกว่า 'ไม่พบข้อมูลในเอกสารที่เกี่ยวข้อง'\n"
                    f"--- เนื้อหาที่เกี่ยวข้อง ---\n{context}\n--------------------------"
                )

                from ai_provider import get_ai_response, provider_badge
                provider = st.session_state.get("ai_provider", "vertex")
                stream_gen = get_ai_response(
                    messages=[{"role":"user","content":prompt}],
                    system_prompt=sys_msg,
                    temperature=0.7, max_tokens=2048,
                    stream=True,
                )

                full_response = ""
                for delta in stream_gen:
                    full_response += delta
                    placeholder.markdown(full_response + "▌")

                placeholder.markdown(full_response)
                st.session_state.last_provider = provider
                st.session_state.chatbot_messages.append(
                    {"role":"assistant","content":full_response})

            except Exception as e:
                placeholder.error(f"Error: {e}")
