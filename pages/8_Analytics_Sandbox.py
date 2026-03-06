import streamlit as st
import pandas as pd
import sweetviz as sv
from ydata_profiling import ProfileReport
import streamlit.components.v1 as components
import pygwalker as pyg
from pygwalker.api.streamlit import StreamlitRenderer
import os, sys
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns

import sys, os, pathlib
_here = pathlib.Path(__file__).resolve().parent
for _p in [_here.parent, _here, pathlib.Path(os.getcwd())]:
    if (_p / "theme.py").exists():
        if str(_p) not in sys.path: sys.path.insert(0, str(_p))
        break
try:
    from theme import apply_theme, SIDEBAR_HTML
except ImportError:
    def apply_theme(): pass
    SIDEBAR_HTML = "<p style=\'color:white\'>AIT</p>"

st.set_page_config(page_title="Super Analytics Sandbox", page_icon="🕵️", layout="wide")
apply_theme()

with st.sidebar:
    st.markdown(SIDEBAR_HTML, unsafe_allow_html=True)

# ── Thai Font Setup ───────────────────────────────────
def setup_thai_font():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir  = os.path.dirname(current_dir)
    font_paths  = [
        os.path.join(parent_dir, "Sarabun-Regular.ttf"),
        os.path.join(parent_dir, "Sarabun-Bold.ttf"),
        "Sarabun-Regular.ttf"
    ]
    found_path = next((p for p in font_paths if os.path.exists(p)), None)
    if found_path:
        fm.fontManager.addfont(found_path)
        prop = fm.FontProperties(fname=found_path)
        font_name = prop.get_name()
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = [font_name] + plt.rcParams['font.sans-serif']
        plt.rcParams['axes.unicode_minus'] = False
        sns.set_theme(font=font_name)
        return font_name, True
    return None, False

thai_font_name, font_found = setup_thai_font()
if font_found:
    st.toast(f"✅ ฟอนต์: {thai_font_name}", icon="🇹🇭")
else:
    st.warning("⚠️ ไม่พบไฟล์ฟอนต์ Sarabun-Regular.ttf")

# ── UI ────────────────────────────────────────────────
st.title("🕵️ Super Analytics Sandbox")
st.markdown("เครื่องมือวิเคราะห์ข้อมูลครบวงจร")

with st.container(border=True):
    uploaded_file = st.file_uploader("📂 อัปโหลดไฟล์ Excel หรือ CSV", type=['xlsx','csv'])

@st.cache_data
def load_data(file):
    try:
        if file.name.endswith('.csv'): return pd.read_csv(file)
        else: return pd.read_excel(file)
    except: return None

@st.cache_resource
def get_pyg_renderer(dataframe):
    return StreamlitRenderer(dataframe, spec="./gw_config.json", spec_io_mode="RW")

if uploaded_file:
    df = load_data(uploaded_file)
    if df is not None:
        st.success(f"✅ โหลดข้อมูลสำเร็จ: {df.shape[0]:,} รายการ, {df.shape[1]} คอลัมน์")

        tab_bi, tab_ydata, tab_sweetviz, tab_audit = st.tabs([
            "🎨 Power BI Mode",
            "🔬 Deep Scan (YData)",
            "📑 Quick Report",
            "🛠️ Audit Tools"
        ])

        with tab_bi:
            renderer = get_pyg_renderer(df)
            renderer.explorer()

        with tab_ydata:
            st.subheader("🔬 Deep Data Profiling (YData)")
            if st.button("🚀 เริ่มวิเคราะห์เจาะลึก", type="primary"):
                with st.spinner("กำลังประมวลผล..."):
                    try:
                        if font_found:
                            plt.rcParams['font.family'] = 'sans-serif'
                            plt.rcParams['font.sans-serif'] = [thai_font_name] + plt.rcParams['font.sans-serif']
                            sns.set_theme(font=thai_font_name)
                        pr = ProfileReport(df, explorative=True, title="Audit Data Profiling",
                            plot={'dpi':200,'image_format':'png','font':{'family':'sans-serif','sans-serif':[thai_font_name]}})
                        report_path = "ydata_report.html"
                        pr.to_file(report_path)
                        with open(report_path,'r',encoding='utf-8') as f: html_content = f.read()
                        st.success("วิเคราะห์เสร็จสิ้น!")
                        components.html(html_content, height=1000, scrolling=True)
                        with open(report_path,"rb") as f:
                            st.download_button("💾 ดาวน์โหลดรายงาน", f, "Deep_Audit_Report.html", "text/html")
                    except Exception as e:
                        st.error(f"เกิดข้อผิดพลาด: {e}")

        with tab_sweetviz:
            st.subheader("📑 Quick Scan Report")
            if st.button("🚀 สร้างรายงานด่วน", type="primary"):
                with st.spinner("กำลังสร้างรายงาน..."):
                    report = sv.analyze(df)
                    report.show_html("sweetviz_report.html", open_browser=False, layout='vertical', scale=1.0)
                    with open("sweetviz_report.html",'r',encoding='utf-8') as f:
                        components.html(f.read(), height=1000, scrolling=True)

        with tab_audit:
            st.subheader("🛠️ Audit Tools")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**สุ่มตัวอย่าง**")
                sample_size = st.number_input("จำนวนสุ่ม", 1, len(df), min(5, len(df)))
                if st.button("สุ่มข้อมูล", type="primary"):
                    st.dataframe(df.sample(sample_size), use_container_width=True, hide_index=True)
            with c2:
                num_cols = df.select_dtypes(include=['number']).columns.tolist()
                if num_cols:
                    st.markdown("**Top 5 ตามคอลัมน์**")
                    col = st.selectbox("เรียงตาม", num_cols)
                    if st.button("แสดง Top 5", type="secondary"):
                        st.dataframe(df.nlargest(5, col), use_container_width=True, hide_index=True)
                else:
                    st.info("ไม่พบคอลัมน์ตัวเลขในข้อมูล")
    else:
        st.error("ไม่สามารถอ่านไฟล์ได้ กรุณาตรวจสอบรูปแบบไฟล์")
else:
    st.info("👆 กรุณาอัปโหลดไฟล์ Excel หรือ CSV เพื่อเริ่มต้น")
