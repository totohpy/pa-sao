import streamlit as st
import pandas as pd
import os
from PyPDF2 import PdfReader
import sys, pathlib

# ── การตั้งค่า Theme และ Path ──────────────────────────────
_here = pathlib.Path(__file__).resolve().parent
for _p in [_here.parent, _here, pathlib.Path(os.getcwd()), pathlib.Path(os.getcwd()).parent]:
    if (_p / "theme.py").exists():
        if str(_p) not in sys.path: sys.path.insert(0, str(_p))
        break
try:
    # สมมติว่า render_ai_sidebar ถูกนำมาจาก ai_provider หรือ theme แล้ว
    from theme import apply_theme, SIDEBAR_HTML, render_ai_sidebar
except ImportError:
    def apply_theme(): pass
    def render_ai_sidebar(): pass
    SIDEBAR_HTML = ""

st.set_page_config(page_title="PA Assistant Chat", page_icon="💬", layout="wide")
apply_theme()

with st.sidebar:
    st.markdown(SIDEBAR_HTML, unsafe_allow_html=True)
    # แสดงเมนูเลือก AI จาก ai_provider (รวมศูนย์ที่เดียว)
    render_ai_sidebar()

st.title("💬 PA Assistant Chat")
st.markdown("ถาม-ตอบผู้ช่วยอัจฉริยะ อ้างอิงคู่มือการปฏิบัติงานและผลการตรวจสอบที่ผ่านมา")

# ══════════════════════════════════════════════════════
# RAG SYSTEM — Text Extraction & Retrieval
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
    """ดึงข้อมูลโดยให้คะแนน TF-IDF + Bigram อย่างง่าย"""
    words  = [w for w in query.split() if len(w) > 1]
    bigrams = [words[i] + words[i+1] for i in range(len(words)-1)]

    scored = []
    for i, chunk in enumerate(chunks):
        score = 0.0
        for w in words: score += chunk.count(w) * 1.0
        for bg in bigrams: score += chunk.count(bg) * 2.0
        if i < 5: score += 0.5 # boost บทนำ
        scored.append((score, i))

    scored.sort(reverse=True)
    top_indices = sorted([idx for _, idx in scored[:top_k]])
    return "\n\n---\n\n".join(chunks[i] for i in top_indices)

def extract_text_from_files(files, folder_path="Doc"):
    text = ""
    # 1. อ่านไฟล์จากโฟลเดอร์หลักในระบบ
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
            
    # 2. อ่านไฟล์ที่ผู้ใช้อัปโหลดมาใหม่
    if files:
        for file in files:
            try:
                if file.name.endswith('.pdf'):
                    for pg in PdfReader(file).pages: text += pg.extract_text() or ""
                elif file.name.endswith('.txt'): text += file.getvalue().decode("utf-8")
                elif file.name.endswith('.csv'): text += pd.read_csv(file).to_string()
            except: pass
    return text

# ── Session Init ──────────────────────────────────────
def init_state():
    ss = st.session_state
    ss.setdefault('chatbot_messages', [{"role":"assistant","content":"สวัสดีครับ PA Assistant พร้อมให้บริการครับ"}])
    ss.setdefault('file_context',        "")
    ss.setdefault('doc_chunks',          [])
    ss.setdefault('last_processed_files', set())
init_state()

# ── File Upload + RAG Index ────────────────────────────
with st.expander("📂 อัปโหลดเอกสารอ้างอิงเพิ่มเติม (PDF, TXT, CSV)"):
    uploaded_files = st.file_uploader("เลือกไฟล์...", type=['pdf','txt','csv'], accept_multiple_files=True)

current_files_set = {f.name for f in uploaded_files} if uploaded_files else set()
files_changed = current_files_set != st.session_state.last_processed_files
first_load    = not st.session_state.file_context and (uploaded_files or os.path.isdir("Doc"))

if files_changed or first_load:
    with st.spinner("📖 กำลังอ่านและจัดเตรียมเอกสาร..."):
        raw_text = extract_text_from_files(uploaded_files)

    if raw_text:
        chunks = split_chunks(raw_text)
        st.session_state.file_context = raw_text
        st.session_state.doc_chunks   = chunks
        st.session_state.last_processed_files = current_files_set
        st.success(f"✅ เตรียมข้อมูลพร้อมใช้งาน ({len(chunks)} chunks)")
    else:
        st.warning("ยังไม่มีข้อมูลเอกสารในระบบ")

# แสดงสถานะระบบ RAG
if st.session_state.doc_chunks:
    st.caption(f"🟢 RAG ทำงาน · {len(st.session_state.doc_chunks)} chunks")
else:
    st.caption("⚪ ไม่มีเอกสารอ้างอิง")

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
                # ── ดึง Context ที่เกี่ยวข้อง ──────────────
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

                # ── ดึง AI Response จาก Provider กลาง ─────────
                from ai_provider import get_ai_response
                
                stream_gen = get_ai_response(
                    messages=[{"role":"user","content":prompt}],
                    system_prompt=sys_msg,
                    temperature=0.7, 
                    max_tokens=2048,
                    stream=True,
                )

                full_response = ""
                for delta in stream_gen:
                    full_response += delta
                    placeholder.markdown(full_response + "▌")

                placeholder.markdown(full_response)
                
                # เก็บข้อความลงประวัติ
                st.session_state.chatbot_messages.append(
                    {"role":"assistant","content":full_response})

            except Exception as e:
                placeholder.error(f"Error: {e}")
