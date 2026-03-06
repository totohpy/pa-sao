import streamlit as st
import pandas as pd
import os, sys, pathlib
from PyPDF2 import PdfReader

_here = pathlib.Path(__file__).resolve().parent
for _p in [_here.parent, _here, pathlib.Path(os.getcwd())]:
    if (_p / "theme.py").exists():
        if str(_p) not in sys.path: sys.path.insert(0, str(_p))
        break
try:
    from theme import apply_theme, SIDEBAR_HTML
except ImportError:
    def apply_theme(): pass
    SIDEBAR_HTML = ""

# load vertex helper
_root = pathlib.Path(__file__).resolve().parent.parent
if str(_root) not in sys.path: sys.path.insert(0, str(_root))
from vertex_ai_helper import chat_stream, is_available

st.set_page_config(page_title="PA Assistant Chat", page_icon="💬", layout="wide")
apply_theme()
with st.sidebar:
    st.markdown(SIDEBAR_HTML, unsafe_allow_html=True)

st.title("💬 PA Assistant Chat")
st.markdown("ถาม-ตอบผู้ช่วยอัจฉริยะ อ้างอิงคู่มือการปฏิบัติงานและผลการตรวจสอบที่ผ่านมา")

# ── RAG helpers ───────────────────────────────────────
CHUNK_SIZE, CHUNK_OVERLAP, TOP_K = 600, 100, 6

def split_chunks(text):
    chunks, i = [], 0
    while i < len(text):
        chunks.append(text[i:i+CHUNK_SIZE])
        i += CHUNK_SIZE - CHUNK_OVERLAP
    return [c.strip() for c in chunks if c.strip()]

def tfidf_retrieve(query, chunks, top_k=TOP_K):
    words   = [w for w in query.split() if len(w) > 1]
    bigrams = [words[i]+words[i+1] for i in range(len(words)-1)]
    scored  = []
    for i, chunk in enumerate(chunks):
        score  = sum(chunk.count(w) for w in words)
        score += sum(chunk.count(bg)*2 for bg in bigrams)
        if i < 5: score += 0.5
        scored.append((score, i))
    scored.sort(reverse=True)
    idx = sorted([i for _, i in scored[:top_k]])
    return "\n\n---\n\n".join(chunks[i] for i in idx)

def extract_text(files, folder="Doc"):
    text = ""
    if os.path.isdir(folder):
        for fn in os.listdir(folder):
            fp = os.path.join(folder, fn)
            try:
                if fn.endswith('.pdf'):
                    with open(fp,'rb') as f:
                        for pg in PdfReader(f).pages: text += pg.extract_text() or ""
                elif fn.endswith('.txt'):
                    with open(fp,'r',encoding='utf-8',errors='ignore') as f: text += f.read()
                elif fn.endswith('.csv'): text += pd.read_csv(fp).to_string()
            except: pass
    if files:
        for file in files:
            try:
                if file.name.endswith('.pdf'):
                    for pg in PdfReader(file).pages: text += pg.extract_text() or ""
                elif file.name.endswith('.txt'): text += file.getvalue().decode("utf-8")
                elif file.name.endswith('.csv'): text += pd.read_csv(file).to_string()
            except: pass
    return text

# ── Session init ──────────────────────────────────────
ss = st.session_state
ss.setdefault('messages',    [{"role":"assistant","content":"สวัสดีครับ PA Assistant พร้อมให้บริการครับ"}])
ss.setdefault('file_context',"")
ss.setdefault('doc_chunks',  [])
ss.setdefault('last_files',  set())

# ── File upload ───────────────────────────────────────
with st.expander("📂 อัปโหลดเอกสาร (PDF, TXT, CSV)"):
    uploaded = st.file_uploader("เลือกไฟล์...", type=['pdf','txt','csv'], accept_multiple_files=True)

cur_files = {f.name for f in uploaded} if uploaded else set()
if cur_files != ss.last_files or (not ss.file_context and (uploaded or os.path.isdir("Doc"))):
    with st.spinner("📖 กำลังอ่านและแบ่ง chunks..."):
        raw = extract_text(uploaded)
    if raw:
        chunks = split_chunks(raw)
        ss.file_context = raw
        ss.doc_chunks   = chunks
        ss.last_files   = cur_files
        st.success(f"✅ พร้อมใช้งาน ({len(raw):,} chars · {len(chunks)} chunks)")
    else:
        st.warning("ยังไม่มีข้อมูลเอกสาร")

# สถานะ
c1, c2 = st.columns(2)
c1.caption(f"{'🟢' if ss.doc_chunks else '⚪'} RAG · {len(ss.doc_chunks)} chunks")
c2.caption(f"{'🟢 Vertex AI พร้อม' if is_available() else '🔴 Vertex AI ไม่พร้อม'}")

# ── Chat UI ───────────────────────────────────────────
chat_container = st.container(height=450, border=True)
with chat_container:
    for msg in ss.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

if prompt := st.chat_input("พิมพ์คำถามของคุณ...", key="chat_input"):
    ss.messages.append({"role":"user","content":prompt})
    with chat_container:
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            placeholder = st.empty()
            try:
                # RAG — ดึง context
                context = (tfidf_retrieve(prompt, ss.doc_chunks)
                           if ss.doc_chunks
                           else "ไม่พบข้อมูลในเอกสาร ตอบตามความรู้ทั่วไป")

                sys_msg = (
                    "คุณคือ PA Assistant ผู้เชี่ยวชาญการตรวจสอบผลสัมฤทธิ์ภาครัฐ\n"
                    "ตอบคำถามโดยอ้างอิงเนื้อหาต่อไปนี้ "
                    "ถ้าไม่พบให้บอกว่า 'ไม่พบข้อมูลในเอกสารที่เกี่ยวข้อง'\n"
                    f"--- เนื้อหาที่เกี่ยวข้อง ---\n{context}\n--------------------------"
                )

                # Streaming จาก Vertex AI
                full = ""
                for chunk in chat_stream(sys_msg, prompt, max_output_tokens=2048):
                    full += chunk
                    placeholder.markdown(full + "▌")
                placeholder.markdown(full)
                ss.messages.append({"role":"assistant","content":full})

            except Exception as e:
                placeholder.error(f"❌ Error: {e}")
