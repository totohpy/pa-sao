import streamlit as st
import sys, os, pathlib

# ── การตั้งค่า Path ──
_here = pathlib.Path(__file__).resolve().parent
for _p in [_here, pathlib.Path(os.getcwd())]:
    if (_p / "theme.py").exists():
        if str(_p) not in sys.path: sys.path.insert(0, str(_p))
        break
try:
    from theme import apply_theme, SIDEBAR_HTML, render_ai_sidebar
except ImportError:
    def apply_theme(): pass
    def render_ai_sidebar(): pass
    SIDEBAR_HTML = ""

st.set_page_config(page_title="PA Planning Studio", page_icon="🔎", layout="wide")
apply_theme()

with st.sidebar:
    st.markdown(SIDEBAR_HTML, unsafe_allow_html=True)
    render_ai_sidebar()

# ── inject CSS สำหรับตกแต่ง Card และทำ Overlay ──────────
st.markdown("""
<style>
/* ── Banner ── */
.banner {
    background:linear-gradient(135deg,#7A2020 0%,#9e2c2c 55%,#5a1515 100%);
    border-radius:18px; padding:28px 32px 24px; margin-bottom:22px;
    position:relative; overflow:hidden;
    box-shadow:0 10px 36px rgba(122,32,32,0.22);
}
.banner-title {
    font-size:26px; font-weight:700; color:#fff;
    font-family:'Noto Serif Thai',serif; margin-bottom:6px;
    position:relative; z-index:1;
}
.banner-desc {
    font-size:13.5px; color:rgba(255,255,255,0.76);
    line-height:1.7; position:relative; z-index:1;
}

/* ── Section label ── */
.sec-lbl {
    font-size:14px; font-weight:700; color:#7A2020;
    letter-spacing:1.8px; text-transform:uppercase;
    margin-bottom:14px; display:flex; align-items:center; gap:10px;
}
.sec-lbl::after { content:''; flex:1; height:1px; background:#e3e4c4; }

/* ── Card Styling ── */
.card-container {
    position: relative;
    height: 180px;
    margin-bottom: 20px;
}

.fcard-main, .fcard-util {
    background:#fff; border:1.5px solid #d8d9b4; border-radius:18px;
    padding:22px 20px; height: 100%; width: 100%;
    box-shadow:0 2px 10px rgba(122,32,32,0.06);
    transition: all 0.3s ease;
    display: flex;
    flex-direction: column;
}

/* Hover Effect */
.card-container:hover .fcard-main, .card-container:hover .fcard-util {
    box-shadow: 0 12px 40px rgba(122,32,32,0.14);
    transform: translateY(-6px);
    border-color: #7A2020;
}

/* ── Overlay Logic (สำคัญมาก) ── */
/* กำหนดให้ Vertical Block ภายในคอลัมน์เป็นจุดอ้างอิงตำแหน่ง */
[data-testid="column"] > div > [data-testid="stVerticalBlock"] {
    position: relative !important;
}

/* ทำให้ st.page_link ครอบคลุมพื้นที่ทั้งหมดของคอลัมน์ */
div[data-testid="stPageLink"] {
    position: absolute !important;
    top: 0 !important; 
    left: 0 !important;
    width: 100% !important; 
    height: 180px !important; /* เท่ากับความสูงของ card-container */
    z-index: 10 !important;
    margin: 0 !important;
}

div[data-testid="stPageLink"] a {
    width: 100% !important; 
    height: 100% !important;
    opacity: 0 !important; /* ซ่อนองค์ประกอบจริงเพื่อให้เห็น Card ด้านล่าง */
    border: none !important;
    padding: 0 !important;
    margin: 0 !important;
}

.fcard-icon { font-size: 28px; margin-bottom: 10px; }
.fcard-title { font-size: 16px; font-weight: 700; color: #1a1a1a; margin-bottom: 5px; font-family:'Noto Serif Thai',serif; }
.fcard-desc { font-size: 13px; color: #666; line-height: 1.5; }

.infobox {
    background:#FEFFD3; border-left:4px solid #7A2020;
    border-radius:10px; padding:15px; font-size:13px; margin-top:20px;
}
</style>
""", unsafe_allow_html=True)

# ── Banner ────────────────────────────────────────────
st.markdown("""
<div class="banner">
  <div class="banner-title">Performance Audit Planning Studio</div>
  <div class="banner-desc">เครื่องมืออัจฉริยะสำหรับการตรวจสอบผลสัมฤทธิ์และประสิทธิภาพดำเนินงาน</div>
</div>
""", unsafe_allow_html=True)

# ── ฟังก์ชันช่วยสร้าง Card ──
def make_card(icon, title, desc, page_path, is_main=True):
    card_class = "fcard-main" if is_main else "fcard-util"
    st.markdown(f"""
    <div class="card-container">
        <div class="{card_class}">
            <div class="fcard-icon">{icon}</div>
            <div class="fcard-title">{title}</div>
            <div class="fcard-desc">{desc}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    # วาง page_link ในลำดับถัดมา ซึ่งจะถูกดึงขึ้นไปซ้อนทับด้วย CSS absolute
    st.page_link(page_path, label=" ")

# ── Main Tools ──────────────────────────────
st.markdown('<div class="sec-lbl">เครื่องมือหลัก</div>', unsafe_allow_html=True)
m1, m2, m3 = st.columns(3)

with m1:
    make_card("🏳️", "Audit Design Assistant", "วิเคราะห์แผน 6W2H · Logic Model ค้นหาข้อตรวจพบเดิม", "pages/2_Audit_Design_Assistant.py")

with m2:
    make_card("🔮", "Audit Plan Generator", "ร่างแผนและแนวการตรวจสอบอัตโนมัติ ส่งออก Word ได้ทันที", "pages/3_Audit_Plan_Generator.py")

with m3:
    make_card("🤖", "PA Assistant Chat", "ถาม-ตอบผู้ช่วยอัจฉริยะ อ้างอิงคู่มือและผลการตรวจสอบ", "pages/4_PA_Assistant_Chat.py")

# ── Utility Tools ───────────────────────────────
st.markdown('<div class="sec-lbl" style="margin-top:24px;">ยูทิลิตี้</div>', unsafe_allow_html=True)
u1, u2, u3, u4 = st.columns(4)

with u1:
    make_card("📄", "OCR แปลงภาพเป็นข้อความ", "ดึงข้อความจากเอกสารภาษาไทย–อังกฤษ", "pages/5_แปลงภาพเป_นข_อความ__OCR_.py", False)

with u2:
    make_card("📱", "QR Code Generator", "สร้าง QR Code พร้อมโลโก้หน่วยงาน", "pages/6_QR_Code_Generator.py", False)

with u3:
    make_card("📊", "Audit Dashboard", "Dashboard สรุปสภาพปัญหาและการวางแผนตรวจสอบ", "pages/7_Audit_Dashboard.py", False)

with u4:
    make_card("🕵️", "Analytics Sandbox", "วิเคราะห์ข้อมูลเชิงลึกด้วย Power BI Mode และ PyGWalker", "pages/8_Analytics_Sandbox.py", False)

st.markdown('<div class="infobox">⚠️ การใช้ฟีเจอร์ AI อาจผิดพลาดได้ โปรดตรวจสอบคำตอบอีกครั้ง ระบบไม่มีการจัดเก็บข้อมูลไว้</div>', unsafe_allow_html=True)
