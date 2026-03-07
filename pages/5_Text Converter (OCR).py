import streamlit as st
import io
import os
import sys, pathlib
from PIL import Image

# ── การตั้งค่า Theme และ Path ──────────────────────────────
_here = pathlib.Path(__file__).resolve().parent
for _p in [_here.parent, _here, pathlib.Path(os.getcwd()), pathlib.Path(os.getcwd()).parent]:
    if (_p / "theme.py").exists():
        if str(_p) not in sys.path: sys.path.insert(0, str(_p))
        break
try:
    from theme import apply_theme, SIDEBAR_HTML, render_ai_sidebar
except ImportError:
    def apply_theme(): pass
    def render_ai_sidebar(): pass
    SIDEBAR_HTML = ""

st.set_page_config(page_title="แปลงภาพเป็นข้อความ (OCR)", page_icon="📄", layout="wide")
apply_theme()

with st.sidebar:
    st.markdown(SIDEBAR_HTML, unsafe_allow_html=True)
    render_ai_sidebar()

st.title("📄 แปลงภาพเป็นข้อความ (OCR)")
st.markdown("อัปโหลดไฟล์ภาพ (เช่น JPG, PNG) เพื่อให้ AI ช่วยดึงข้อความออกมา")

# ── ฟังก์ชันดึงข้อความด้วย Vertex AI ────────────────────────
def extract_text_from_image(image_bytes):
    try:
        from ai_provider import is_ready, get_ai_response, PROJECT_ID, LOCATION, VERTEX_MODEL
        
        if not is_ready():
            return "Error: กรุณาตั้งค่า AI Provider ที่แถบด้านข้างก่อน"
        
        provider = st.session_state.get("ai_provider", "vertex")
        
        if provider == "vertex":
            import vertexai
            from vertexai.generative_models import GenerativeModel, Part, GenerationConfig
            
            vertexai.init(project=PROJECT_ID, location=LOCATION)
            model = GenerativeModel(VERTEX_MODEL)
            
            image_part = Part.from_data(data=image_bytes, mime_type="image/jpeg")
            prompt = "ดึงข้อความทั้งหมดจากรูปภาพนี้ออกมาให้ถูกต้องตรงตามต้นฉบับที่สุด ไม่ต้องแต่งเติมคำ"
            
            cfg = GenerationConfig(temperature=0.0) # ใช้ 0.0 เพื่อให้แม่นยำตามรูปที่สุด
            response = model.generate_content([image_part, prompt], generation_config=cfg)
            return response.text
            
        else:
            return "Error: ฟีเจอร์ OCR (วิเคราะห์รูปภาพ) ในตอนนี้รองรับเฉพาะ Cloud AI (Vertex AI) เท่านั้น กรุณาเปลี่ยน Provider ที่แถบด้านข้าง"
            
    except Exception as e:
        return f"เกิดข้อผิดพลาดในการประมวลผล: {str(e)}"

# ── ส่วน UI หลัก ─────────────────────────────────────────
uploaded_file = st.file_uploader("อัปโหลดไฟล์ภาพ...", type=['jpg', 'jpeg', 'png','pdf'])

if uploaded_file is not None:
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("ภาพที่อัปโหลด")
        image = Image.open(uploaded_file)
        st.image(image, use_container_width=True)
        
    with c2:
        st.subheader("ข้อความที่ได้ (OCR)")
        
        if st.button("🚀 เริ่มแปลงเป็นข้อความ", type="primary"):
            with st.spinner("กำลังวิเคราะห์รูปภาพ..."):
                # แปลงภาพเป็น bytes สำหรับส่งให้ API
                img_byte_arr = io.BytesIO()
                # เปลี่ยนโหมดเป็น RGB ป้องกัน error หากเป็น PNG แบบมี Alpha
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                image.save(img_byte_arr, format='JPEG')
                image_bytes = img_byte_arr.getvalue()
                
                extracted_text = extract_text_from_image(image_bytes)
                
                st.session_state["ocr_result"] = extracted_text
        
        # แสดงผลลัพธ์
        result_text = st.session_state.get("ocr_result", "")
        if result_text:
            st.text_area("ผลลัพธ์", value=result_text, height=400, key="ocr_textarea")
            
            st.download_button(
                label="⬇️ ดาวน์โหลดข้อความ (.txt)",
                data=result_text,
                file_name="ocr_result.txt",
                mime="text/plain"
            )
