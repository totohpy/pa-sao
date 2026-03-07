import streamlit as st
import requests, json
from PIL import Image
from io import BytesIO
from docx import Document
import os, sys

import sys, os, pathlib
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
    SIDEBAR_HTML = "<p style=\'color:white\'>AIT</p>"

st.set_page_config(page_title="Typhoon OCR", page_icon="📄", layout="wide")
apply_theme()

with st.sidebar:
    st.markdown(SIDEBAR_HTML, unsafe_allow_html=True)
    render_ai_sidebar()

if 'api_key' not in st.session_state:
    try: st.session_state['api_key'] = st.secrets.get("api_key","")
    except Exception: st.session_state['api_key'] = ""

MODEL     = "typhoon-ocr"
TASK_TYPE = "v1.5"

def extract_text_from_image(uploaded_file, api_key, model, task_type, max_tokens, temperature, top_p, repetition_penalty, pages=None):
    url   = "https://api.opentyphoon.ai/v1/ocr"
    files = {'file': (uploaded_file.name, uploaded_file, uploaded_file.type)}
    data  = {'model':model,'task_type':task_type,'max_tokens':str(max_tokens),'temperature':str(temperature),'top_p':str(top_p),'repetition_penalty':str(repetition_penalty)}
    if pages and pages.strip(): data['pages'] = pages.strip()
    headers = {'Authorization': f'Bearer {api_key}'}
    try:
        response = requests.post(url, files=files, data=data, headers=headers)
        if response.status_code == 200:
            result = response.json(); extracted_texts = []
            for page_result in result.get('results',[]):
                if page_result.get('success') and page_result.get('message'):
                    content = page_result['message']['choices'][0]['message']['content']
                    try:
                        parsed = json.loads(content); text = parsed.get('natural_text', content)
                        if isinstance(text,(dict,list)): text = json.dumps(text, ensure_ascii=False)
                    except json.JSONDecodeError: text = content
                    extracted_texts.append(text)
                elif not page_result.get('success'):
                    extracted_texts.append(f"[Error: {page_result.get('error','Unknown error')}]")
            return '\n\n---\n\n'.join(extracted_texts)
        else: return f"API Error: {response.status_code}\n{response.text}"
    except Exception as e: return f"Connection Error: {str(e)}"

def create_docx(text):
    doc = Document()
    for paragraph in text.split('\n'): doc.add_paragraph(paragraph)
    buffer = BytesIO(); doc.save(buffer); buffer.seek(0)
    return buffer

# ── UI ────────────────────────────────────────────────
st.title("📄 ระบบแปลงภาพเป็นข้อความ (OCR)")
st.markdown("##### เครื่องมือช่วยดึงข้อความจากเอกสารภาษาไทยและอังกฤษด้วย AI")

input_method = st.radio("เลือกวิธีการนำเข้าข้อมูล:", options=["📁 อัปโหลดไฟล์","📸 ถ่ายภาพ (Camera)"], horizontal=True, label_visibility="collapsed")
uploaded_file = None

if input_method == "📁 อัปโหลดไฟล์":
    file_upload = st.file_uploader("เลือกไฟล์ภาพ (JPG, PNG) หรือเอกสาร (PDF)", type=['png','jpg','jpeg','webp','pdf'], key="file_uploader")
    if file_upload: uploaded_file = file_upload
elif input_method == "📸 ถ่ายภาพ (Camera)":
    camera_image = st.camera_input("ถ่ายภาพเอกสาร")
    if camera_image:
        uploaded_file = camera_image
        if not hasattr(uploaded_file,'name'): uploaded_file.name = "camera_capture.jpg"
        if not hasattr(uploaded_file,'type'): uploaded_file.type = "image/jpeg"

if uploaded_file:
    col1, col2 = st.columns([1,1], gap="large")
    with col1:
        st.info("🖼️ **ไฟล์ต้นฉบับ**")
        if uploaded_file.type == "application/pdf":
            st.warning("⚠️ ไฟล์ PDF จะไม่แสดงตัวอย่าง แต่สามารถประมวลผลได้ปกติ")
        else:
            st.image(uploaded_file, use_column_width=True)
        pages_input = st.text_input("ระบุหน้า (สำหรับ PDF)", placeholder="เช่น 1, 2 หรือ 1-5 (เว้นว่างเพื่อทำทั้งหมด)")
        st.markdown("---")
        with st.expander("⚙️ การตั้งค่า (Advanced)"):
            max_tokens        = st.slider("Max Tokens", 1000, 16000, st.session_state.get("max_tokens",16000), 100, key="max_tokens_slider")
            temperature       = st.slider("Temperature", 0.0, 1.0, st.session_state.get("temperature",0.1), 0.1, key="temperature_slider")
            top_p             = st.slider("Top P", 0.0, 1.0, st.session_state.get("top_p",0.6), 0.1, key="top_p_slider")
            repetition_penalty= st.slider("Repetition Penalty", 1.0, 2.0, st.session_state.get("repetition_penalty",1.1), 0.1, key="repetition_penalty_slider")
        st.markdown("---")
        current_api_key = st.session_state.get("api_key","")
        if st.button("🚀 เริ่มประมวลผล (Start OCR)", type="primary", use_container_width=True):
            if not current_api_key:
                st.error("❌ กรุณาตั้งค่า API Key ใน Streamlit Secrets")
            else:
                st.session_state["max_tokens"]         = max_tokens
                st.session_state["temperature"]        = temperature
                st.session_state["top_p"]              = top_p
                st.session_state["repetition_penalty"] = repetition_penalty
                with st.spinner("🌀 AI กำลังอ่านเอกสาร..."):
                    result_text = extract_text_from_image(uploaded_file, current_api_key, MODEL, TASK_TYPE, max_tokens, temperature, top_p, repetition_penalty, pages_input)
                    st.session_state["ocr_result"] = result_text
                    st.success("✅ เสร็จสิ้น!")

    with col2:
        st.info("📝 **ผลลัพธ์ข้อความ**")
        result_text = st.session_state.get("ocr_result","")
        st.text_area(label="Text Output", value=result_text, height=600, placeholder="ผลลัพธ์จากการ OCR จะปรากฏที่นี่...", label_visibility="collapsed")
        if result_text:
            docx_file = create_docx(result_text)
            st.download_button(label="💾 ดาวน์โหลดไฟล์ .docx", data=docx_file, file_name="ocr_result.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
