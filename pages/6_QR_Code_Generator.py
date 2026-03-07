import streamlit as st
import qrcode
from io import BytesIO
from PIL import Image
import os, base64, sys

import sys, os, pathlib
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
    SIDEBAR_HTML = "<p style=\'color:white\'>AIT</p>"

st.set_page_config(page_title="QR Code Generator", page_icon="📱", layout="wide")
apply_theme()

with st.sidebar:
    st.markdown(SIDEBAR_HTML, unsafe_allow_html=True)
    render_ai_sidebar()

def generate_qr_code_with_logo(data, logo_file_name=None, logo_size_factor=3.5):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=2)
    qr.add_data(data); qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert('RGBA')
    if logo_file_name:
        try:
            if os.path.exists(logo_file_name):
                logo = Image.open(logo_file_name)
                if logo_size_factor <= 0: logo_size_factor = 1
                width, height = img.size
                logo_size = int(width / logo_size_factor)
                logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
                logo_bg = Image.new("RGBA", (logo_size, logo_size), "white")
                pos = ((width - logo_size) // 2, (height - logo_size) // 2)
                img.paste(logo_bg, pos)
                if logo.mode == 'RGBA': img.paste(logo, pos, mask=logo)
                else: img.paste(logo, pos)
        except Exception as e: print(f"Logo Error: {e}")
    buf = BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
    return buf

def get_image_base64(image_path):
    try:
        with open(image_path,"rb") as img_file: return base64.b64encode(img_file.read()).decode('utf-8')
    except Exception: return None

# ── UI ────────────────────────────────────────────────
st.title("📱 QR Code Generator")
st.markdown("##### เครื่องมือสร้างคิวอาร์โค้ดพร้อมโลโก้หน่วยงาน")

with st.container(border=True):
    col_left, col_right = st.columns([1.2, 0.8], gap="large")

    with col_left:
        st.subheader("1. ใส่ข้อมูล")
        qr_data = st.text_input("URL หรือข้อความที่ต้องการ:", placeholder="https://www.example.com")

        st.write("")
        st.subheader("2. เลือกโลโก้")
        if 'selected_logo_key' not in st.session_state:
            st.session_state['selected_logo_key'] = 'none'

        l1, l2, l3 = st.columns(3)

        def render_logo_selection(col, key, label, image_path=None, is_no_logo=False):
            with col:
                if is_no_logo:
                    st.markdown("<div style='height:100px;border:1px dashed #ccc;display:flex;align-items:center;justify-content:center;color:#aaa;border-radius:8px;background:white;margin-bottom:10px;font-size:0.8rem;'>No Logo</div>", unsafe_allow_html=True)
                elif image_path and os.path.exists(image_path):
                    b64 = get_image_base64(image_path)
                    if b64:
                        st.markdown(f"<div style='height:100px;display:flex;align-items:center;justify-content:center;border:1px solid #eee;border-radius:8px;background:white;margin-bottom:10px;'><img src='data:image/png;base64,{b64}' style='max-height:80px;max-width:100%;'></div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div style='height:100px;display:flex;align-items:center;justify-content:center;color:red;border:1px solid #eee;border-radius:8px;margin-bottom:10px;'>Missing</div>", unsafe_allow_html=True)
                is_selected = (st.session_state['selected_logo_key'] == key)
                icon = "🔴" if is_selected else "⭕"
                if st.button(f"{icon} {label}", key=f"btn_{key}", type="secondary", use_container_width=True):
                    st.session_state['selected_logo_key'] = key; st.rerun()

        render_logo_selection(l1, 'none', 'ไม่ใส่', is_no_logo=True)
        render_logo_selection(l2, 'bw',   'ขาว-ดำ', image_path="logoSAO-BW-TH_0.png")
        render_logo_selection(l3, 'color','สี',     image_path="logoSAO-TH-02.png")

        logo_map = {"none":None,"bw":"logoSAO-BW-TH_0.png","color":"logoSAO-TH-02.png"}
        selected_logo = logo_map[st.session_state['selected_logo_key']]

        if selected_logo is not None:
            st.write("")
            st.markdown("**ปรับขนาดโลโก้:**")
            logo_scale_input = st.slider("ขนาดโลโก้ (เล็ก - ใหญ่)", min_value=1, max_value=4, value=3, step=1)
            logo_divisor = 5.625 + (logo_scale_input * -0.625)
        else:
            logo_divisor = 3.5

        st.markdown("---")
        if st.button("🚀 สร้าง QR Code", type="primary", use_container_width=True):
            if qr_data:
                with st.spinner("กำลังสร้าง..."):
                    img_buf = generate_qr_code_with_logo(qr_data, selected_logo, logo_divisor)
                    st.session_state['gen_qr_image'] = img_buf
                    st.session_state['gen_qr_data']  = qr_data
            else: st.error("กรุณาใส่ URL หรือข้อความก่อนครับ")

    with col_right:
        st.subheader("3. ผลลัพธ์")
        result_placeholder = st.empty()
        if 'gen_qr_image' in st.session_state:
            with result_placeholder.container():
                st.image(st.session_state['gen_qr_image'], caption="QR Code ของคุณ", width=300)
                st.success("สร้างเรียบร้อย!")
                st.caption(f"Link: {st.session_state.get('gen_qr_data','')[:40]}...")
                st.download_button(label="💾 ดาวน์โหลดไฟล์ PNG", data=st.session_state['gen_qr_image'], file_name="qrcode.png", mime="image/png", use_container_width=True)
        else:
            result_placeholder.markdown("""
            <div style="height:350px;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#94A3B8;text-align:center;border:2px dashed #e3e4c4;border-radius:12px;background:#fafaf0;">
                <div style="font-size:3.5rem;margin-bottom:10px;">📷</div>
                <div style="font-size:1.1rem;font-weight:600;">รอการสร้าง QR Code</div>
                <div style="font-size:0.9rem;margin-top:6px;">กรอกข้อมูลและเลือกโลโก้ทางซ้าย<br>แล้วกดปุ่มสร้างได้เลย</div>
            </div>""", unsafe_allow_html=True)
