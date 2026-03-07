import streamlit as st
import sys, os, pathlib

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

# ── Navigation handler (ต้องอยู่ก่อน render) ──────────────────────────────
NAV_PAGES = {
    "goto_2": "pages/2_Audit_Design_Assistant.py",
    "goto_3": "pages/3_Audit_Plan_Generator.py",
    "goto_4": "pages/4_PA_Assistant_Chat.py",
    "goto_5": "pages/5_Text Converter (OCR).py",
    "goto_6": "pages/6_QR_Code_Generator.py",
    "goto_7": "pages/7_Audit_Dashboard.py",
    "goto_8": "pages/8_Analytics_Sandbox.py",
}
for key, path in NAV_PAGES.items():
    if st.session_state.get(key):
        st.session_state[key] = False
        st.switch_page(path)

# ── CSS ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&family=Noto+Serif+Thai:wght@600;700&display=swap');

/* ── Banner ── */
.banner {
    background: linear-gradient(135deg, #7A2020 0%, #9e2c2c 50%, #5a1515 100%);
    border-radius: 20px;
    padding: 32px 36px 28px;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 12px 40px rgba(122,32,32,0.25);
}
.banner::before {
    content: '';
    position: absolute; top: -60px; right: -40px;
    width: 220px; height: 220px;
    background: rgba(255,255,255,0.05);
    border-radius: 50%;
}
.banner::after {
    content: '';
    position: absolute; bottom: -80px; right: 100px;
    width: 160px; height: 160px;
    background: rgba(255,255,255,0.04);
    border-radius: 40px;
    transform: rotate(20deg);
}
.banner-eyebrow {
    font-size: 11px; font-weight: 700; color: rgba(255,255,255,0.55);
    letter-spacing: 2.5px; text-transform: uppercase;
    margin-bottom: 8px;
}
.banner-title {
    font-size: 28px; font-weight: 700; color: #fff;
    font-family: 'Noto Serif Thai', serif;
    margin-bottom: 8px; position: relative; z-index: 1;
    line-height: 1.3;
}
.banner-desc {
    font-size: 14px; color: rgba(255,255,255,0.72);
    line-height: 1.7; position: relative; z-index: 1;
    max-width: 540px;
}
.banner-badge {
    display: inline-block;
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.25);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 11.5px; color: rgba(255,255,255,0.9);
    margin-top: 14px; position: relative; z-index: 1;
}

/* ── Section label ── */
.sec-lbl {
    font-size: 11px; font-weight: 700; color: #7A2020;
    letter-spacing: 2.5px; text-transform: uppercase;
    margin-bottom: 12px;
    display: flex; align-items: center; gap: 10px;
}
.sec-lbl::after { content: ''; flex: 1; height: 1px; background: #e3e4c4; }

/* ── Card base ── */
.pa-card {
    background: #fff;
    border: 1.5px solid #dddec0;
    border-radius: 16px;
    padding: 22px 20px 18px;
    height: 100%;
    position: relative;
    overflow: hidden;
    transition: all 0.22s cubic-bezier(.34,1.46,.64,1);
    cursor: pointer;
}
.pa-card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #7A2020, #c0392b);
    transform: scaleX(0); transform-origin: left;
    transition: transform 0.2s ease;
}
.pa-card:hover {
    box-shadow: 0 14px 44px rgba(122,32,32,0.13);
    transform: translateY(-5px);
    border-color: #b89898;
}
.pa-card:hover::before { transform: scaleX(1); }

/* ── Card accent dot (top-right) ── */
.pa-card-dot {
    position: absolute; top: 14px; right: 14px;
    width: 10px; height: 10px; border-radius: 50%;
    background: #BCD9A2;
}

.pa-icon {
    font-size: 26px;
    width: 48px; height: 48px;
    background: rgba(122,32,32,0.07);
    border: 1px solid rgba(122,32,32,0.12);
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    margin-bottom: 13px;
}
.pa-title {
    font-size: 15px; font-weight: 700; color: #1a1a1a;
    font-family: 'Noto Serif Thai', serif;
    margin-bottom: 6px; line-height: 1.4;
}
.pa-desc { font-size: 12.5px; color: #777; line-height: 1.65; }

/* ── Util card (smaller) ── */
.pa-card-sm {
    background: #fff;
    border: 1px solid #dddec0;
    border-radius: 14px;
    padding: 16px 16px 14px;
    position: relative; overflow: hidden;
    transition: all 0.2s cubic-bezier(.34,1.46,.64,1);
    cursor: pointer;
}
.pa-card-sm::after {
    content: '';
    position: absolute; bottom: 0; left: 0; right: 0; height: 3px;
    background: #7A2020;
    transform: scaleX(0); transform-origin: left;
    transition: transform 0.18s ease;
}
.pa-card-sm:hover {
    box-shadow: 0 8px 28px rgba(122,32,32,0.11);
    transform: translateY(-4px);
}
.pa-card-sm:hover::after { transform: scaleX(1); }
.pa-sm-icon {
    font-size: 20px;
    width: 38px; height: 38px;
    background: rgba(122,32,32,0.06);
    border: 1px solid rgba(122,32,32,0.10);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    margin-bottom: 10px;
}
.pa-sm-title { font-size: 13.5px; font-weight: 700; color: #1a1a1a; margin-bottom: 4px; font-family:'Noto Serif Thai',serif; }
.pa-sm-desc  { font-size: 12px; color: #888; line-height: 1.6; }

/* ── Hide default Streamlit button style — make it invisible overlay ── */
div[data-testid="stButton"] > button {
    position: absolute !important;
    inset: 0 !important;
    width: 100% !important;
    height: 100% !important;
    opacity: 0 !important;
    cursor: pointer !important;
    border: none !important;
    background: transparent !important;
    padding: 0 !important;
    margin: 0 !important;
    z-index: 20 !important;
}
/* wrapper column ต้องเป็น relative */
div[data-testid="stColumn"] {
    position: relative !important;
}

/* ── Infobox ── */
.infobox {
    background: #FEFFD3;
    border: 1px solid #e0e098;
    border-left: 4px solid #7A2020;
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 13px; color: #404040;
    line-height: 1.6; margin-top: 20px;
}
</style>
""", unsafe_allow_html=True)

# ── Banner ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="banner">
  <div class="banner-eyebrow">สำนักงานการตรวจเงินแผ่นดิน</div>
  <div class="banner-title">Performance Audit Planning Studio</div>
  <div class="banner-desc">เครื่องมืออัจฉริยะสำหรับการตรวจสอบผลสัมฤทธิ์และประสิทธิภาพดำเนินงาน</div>
  <div class="banner-badge">🤖 AI-Powered · Vertex AI Gemini</div>
</div>
""", unsafe_allow_html=True)


# ── Helper: card + invisible button overlay ────────────────────────────────
def main_card(key, icon, title, desc):
    st.markdown(f"""
    <div class="pa-card">
      <div class="pa-card-dot"></div>
      <div class="pa-icon">{icon}</div>
      <div class="pa-title">{title}</div>
      <div class="pa-desc">{desc}</div>
    </div>""", unsafe_allow_html=True)
    st.button(" ", key=key)   # invisible overlay button


def util_card(key, icon, title, desc):
    st.markdown(f"""
    <div class="pa-card-sm">
      <div class="pa-sm-icon">{icon}</div>
      <div class="pa-sm-title">{title}</div>
      <div class="pa-sm-desc">{desc}</div>
    </div>""", unsafe_allow_html=True)
    st.button(" ", key=key)


# ── Main Tools ──────────────────────────────────────────────────────────────
st.markdown('<div class="sec-lbl">เครื่องมือหลัก</div>', unsafe_allow_html=True)
m1, m2, m3 = st.columns(3, gap="medium")

with m1:
    main_card("goto_2", "🏳️", "Audit Design Assistant",
              "วิเคราะห์แผน 6W2H · Logic Model · Flowchart ค้นหาข้อตรวจพบเดิม และแนะนำประเด็นด้วย AI")
with m2:
    main_card("goto_3", "🔮", "Audit Plan Generator",
              "ร่างแผนและแนวการตรวจสอบอัตโนมัติ AI สร้างเนื้อหา ส่งออก Word / HTML ได้ทันที")
with m3:
    main_card("goto_4", "🤖", "PA Assistant Chat",
              "ถาม-ตอบผู้ช่วยอัจฉริยะ อ้างอิงคู่มือและผลการตรวจสอบ รองรับ PDF · CSV · TXT")

# ── Utility Tools ───────────────────────────────────────────────────────────
st.markdown('<div class="sec-lbl" style="margin-top:28px;">ยูทิลิตี้</div>', unsafe_allow_html=True)
u1, u2, u3, u4 = st.columns(4, gap="medium")

with u1:
    util_card("goto_5", "📄", "OCR แปลงภาพเป็นข้อความ",
              "ดึงข้อความจากเอกสารภาษาไทย–อังกฤษด้วย Typhoon OCR")
with u2:
    util_card("goto_6", "📱", "QR Code Generator",
              "สร้าง QR Code พร้อมโลโก้หน่วยงาน ดาวน์โหลด PNG ได้ทันที")
with u3:
    util_card("goto_7", "📊", "Audit Dashboard",
              "Dashboard สรุปสภาพปัญหาด้านสิ่งแวดล้อมและการวางแผนตรวจสอบ")
with u4:
    util_card("goto_8", "🕵️", "Analytics Sandbox",
              "Power BI Mode · YData · Sweetviz · PyGWalker วิเคราะห์ข้อมูลเชิงลึก")

st.markdown('<div class="infobox">⚠️ การใช้ฟีเจอร์ AI อาจผิดพลาดได้ โปรดตรวจสอบคำตอบอีกครั้ง ระบบไม่มีการจัดเก็บข้อมูลไว้</div>',
            unsafe_allow_html=True)
