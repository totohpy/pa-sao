import streamlit as st
import pandas as pd
import json, os, sys, pathlib

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

st.set_page_config(page_title="Audit Dashboard", page_icon="📊", layout="wide")
apply_theme()

with st.sidebar:
    st.markdown(SIDEBAR_HTML, unsafe_allow_html=True)
    render_ai_sidebar()

# ── Init ──────────────────────────────────────────────
if 'api_key_global' not in st.session_state:
    try: st.session_state['api_key_global'] = st.secrets["api_key"]
    except: st.session_state['api_key_global'] = ""

# ── Page Header ───────────────────────────────────────
st.title("📊 Audit Dashboard Builder")
st.markdown("อัปโหลดข้อมูล แล้วเลือก Template หรือสั่ง AI สร้าง Dashboard ให้อัตโนมัติ")

# ─────────────────────────────────────────────────────
# STEP 1: Upload Data
# ─────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown("#### 📂 Step 1 — อัปโหลดข้อมูล")
    uploaded = st.file_uploader(
        "เลือกไฟล์ Excel หรือ CSV",
        type=["xlsx","xls","csv"],
        label_visibility="collapsed"
    )

@st.cache_data
def load_df(file):
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    return pd.read_excel(file)

df = None
if uploaded:
    try:
        df = load_df(uploaded)
        st.success(f"✅ โหลดข้อมูลสำเร็จ — {df.shape[0]:,} แถว × {df.shape[1]} คอลัมน์")
    except Exception as e:
        st.error(f"อ่านไฟล์ไม่ได้: {e}")

# ─────────────────────────────────────────────────────
# STEP 2: Mode Selection
# ─────────────────────────────────────────────────────
if df is not None:
    st.markdown("---")
    with st.container(border=True):
        st.markdown("#### 🎯 Step 2 — เลือกโหมด")
        mode = st.radio(
            "โหมด",
            ["🤖 AI สร้างให้อัตโนมัติ", "📋 เลือก Template สำเร็จรูป", "🔧 กำหนดเอง (Custom)"],
            horizontal=True,
            label_visibility="collapsed"
        )

    # ══════════════════════════════════════
    # MODE A: AI Auto-generate
    # ══════════════════════════════════════
    if mode == "🤖 AI สร้างให้อัตโนมัติ":
        st.markdown("---")
        with st.container(border=True):
            st.markdown("#### 🤖 Step 3 — บอก AI ว่าต้องการ Dashboard แบบไหน")

            col_a, col_b = st.columns([3,1])
            with col_a:
                ai_prompt = st.text_area(
                    "อธิบาย Dashboard ที่ต้องการ",
                    placeholder="เช่น: สร้าง Dashboard สรุปผลการตรวจสอบ แสดง: 1) จำนวนข้อตรวจพบตามหน่วยงาน (แท่ง) 2) แนวโน้มปีละ (เส้น) 3) สัดส่วนความรุนแรง (วงกลม)",
                    height=120, key="ai_prompt_input"
                )
            with col_b:
                st.markdown("<br>", unsafe_allow_html=True)
                run_ai = st.button("🚀 สร้าง Dashboard", type="primary", use_container_width=True)

            # Quick prompt buttons
            st.markdown("**หรือเลือก prompt สำเร็จรูป:**")
            qp1, qp2, qp3, qp4 = st.columns(4)
            if qp1.button("📊 สรุปภาพรวม", use_container_width=True):
                st.session_state['ai_prompt_input'] = "สร้าง Dashboard ภาพรวม แสดงสถิติสำคัญ จำนวนรายการ ค่าเฉลี่ย สูงสุด ต่ำสุด และแผนภูมิแท่งเปรียบเทียบแต่ละหมวด"
                st.rerun()
            if qp2.button("📈 แนวโน้มตามเวลา", use_container_width=True):
                st.session_state['ai_prompt_input'] = "สร้าง Dashboard แนวโน้มตามเวลา แสดงกราฟเส้นการเปลี่ยนแปลง พร้อม highlight จุดสูงสุดและต่ำสุด"
                st.rerun()
            if qp3.button("🔍 วิเคราะห์ข้อตรวจพบ", use_container_width=True):
                st.session_state['ai_prompt_input'] = "สร้าง Dashboard วิเคราะห์ข้อตรวจพบ แสดงจำนวนตามหน่วยงาน ระดับความรุนแรง สาเหตุหลัก และข้อเสนอแนะที่พบบ่อย"
                st.rerun()
            if qp4.button("💰 งบประมาณ", use_container_width=True):
                st.session_state['ai_prompt_input'] = "สร้าง Dashboard งบประมาณ แสดงการเบิกจ่าย เปรียบเทียบแผนกับผล สัดส่วนตามประเภทรายจ่าย"
                st.rerun()

        if run_ai and ai_prompt:
            with st.spinner("🤖 AI กำลังวิเคราะห์ข้อมูลและสร้าง Dashboard..."):
                try:
                    col_info = []
                    for c in df.columns:
                        dtype = str(df[c].dtype)
                        nunique = df[c].nunique()
                        col_info.append(f"- {c} ({dtype}, {nunique} unique values)")

                    sample_data = df.head(5).to_string()

                    system_prompt = """คุณคือ Data Analyst ผู้เชี่ยวชาญ Python + Plotly + Streamlit
ภารกิจ: รับข้อมูล DataFrame และ requirement จากผู้ใช้ แล้ว generate Python code สำหรับสร้าง Dashboard ด้วย Plotly

กฎเหล็ก:
1. ตอบเฉพาะ Python code เท่านั้น ไม่มี markdown, ไม่มี ``` wrapper
2. ใช้ st.plotly_chart() แสดงกราฟ
3. ใช้ st.metric() แสดง KPI cards
4. ใช้ st.columns() จัดวาง layout
5. DataFrame ชื่อ `df` อยู่แล้วในสภาพแวดล้อม ไม่ต้อง import หรือโหลดใหม่
6. import ที่ใช้ได้: import plotly.express as px, import plotly.graph_objects as go, import pandas as pd
7. ใส่ try/except ทุก chart เพื่อป้องกัน error จาก column ที่อาจไม่มี
8. ถ้าไม่แน่ใจ column ให้ใช้ df.columns[0], df.columns[1] เป็น fallback
9. Code ต้องรันได้ทันทีโดยไม่มี input จากผู้ใช้เพิ่มเติม"""

                    user_msg = f"""ข้อมูล DataFrame:
คอลัมน์:
{chr(10).join(col_info)}

ตัวอย่างข้อมูล 5 แถวแรก:
{sample_data}

ความต้องการ: {ai_prompt}

กรุณา generate Python + Streamlit + Plotly code สำหรับสร้าง Dashboard ตามที่ต้องการ"""

                    from ai_provider import get_ai_response
                    generated_code = get_ai_response(
                        messages=[{"role":"user","content":user_msg}],
                        system_prompt=system_prompt,
                        temperature=0.3, max_tokens=4096,
                    )
                    if not isinstance(generated_code, str):
                        generated_code = ""
                    # Strip markdown if AI added it
                    generated_code = generated_code.replace("```python","").replace("```","").strip()
                    st.session_state['dashboard_code'] = generated_code
                    st.success("✅ AI สร้าง Dashboard code เรียบร้อยแล้ว!")

                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาด: {e}")
                    st.info("ลองใช้โหมด Template สำเร็จรูปแทนครับ")

        # ── Show generated dashboard ─────────────────
        if st.session_state.get('dashboard_code'):
            st.markdown("---")
            st.markdown("#### 📊 Dashboard ที่ AI สร้าง")

            with st.expander("📝 ดู/แก้ไข Code ที่ AI สร้าง"):
                edited_code = st.text_area("Code", value=st.session_state['dashboard_code'], height=300, key="code_editor")
                if st.button("🔄 รัน Code ที่แก้ไขแล้ว", type="secondary"):
                    st.session_state['dashboard_code'] = edited_code

            with st.container(border=True):
                try:
                    import plotly.express as px
                    import plotly.graph_objects as go
                    exec(st.session_state['dashboard_code'], {"st": st, "df": df, "px": px, "go": go, "pd": pd})
                except Exception as e:
                    st.error(f"รัน Dashboard ไม่ได้: {e}")
                    st.code(st.session_state['dashboard_code'], language="python")

    # ══════════════════════════════════════
    # MODE B: Templates
    # ══════════════════════════════════════
    elif mode == "📋 เลือก Template สำเร็จรูป":
        import plotly.express as px
        import plotly.graph_objects as go

        st.markdown("---")
        st.markdown("#### 📋 Step 3 — เลือก Template")

        num_cols = df.select_dtypes(include='number').columns.tolist()
        cat_cols = df.select_dtypes(include=['object','category']).columns.tolist()
        all_cols = df.columns.tolist()

        t1, t2, t3, t4 = st.tabs(["📊 สรุปภาพรวม", "📈 แผนภูมิเปรียบเทียบ", "🔗 ความสัมพันธ์", "📋 ตาราง"])

        with t1:
            st.markdown("**KPI Summary**")
            if num_cols:
                kpi_cols = st.columns(min(4, len(num_cols)))
                for i, col in enumerate(num_cols[:4]):
                    with kpi_cols[i]:
                        st.metric(col, f"{df[col].sum():,.0f}", delta=f"เฉลี่ย {df[col].mean():,.1f}")
            if cat_cols and num_cols:
                col_x = st.selectbox("หมวดหมู่ (แกน X)", cat_cols, key="ov_x")
                col_y = st.selectbox("ค่า (แกน Y)", num_cols, key="ov_y")
                agg = st.selectbox("สรุปด้วย", ["sum","mean","count"], key="ov_agg")
                grouped = df.groupby(col_x)[col_y].agg(agg).reset_index().sort_values(col_y, ascending=False)
                fig = px.bar(grouped, x=col_x, y=col_y, title=f"{col_y} ({agg}) แยกตาม {col_x}",
                             color_discrete_sequence=["#7A2020"])
                fig.update_layout(plot_bgcolor="#f8f9ee", paper_bgcolor="#f8f9ee")
                st.plotly_chart(fig, use_container_width=True)

        with t2:
            if cat_cols and num_cols:
                col_x2 = st.selectbox("หมวดหมู่", cat_cols, key="cmp_x")
                col_y2 = st.selectbox("ค่า", num_cols, key="cmp_y")
                chart_type = st.radio("ประเภทกราฟ", ["แท่ง","วงกลม","แนวนอน"], horizontal=True)
                grouped2 = df.groupby(col_x2)[col_y2].sum().reset_index()
                if chart_type == "วงกลม":
                    fig2 = px.pie(grouped2, names=col_x2, values=col_y2, title=f"สัดส่วน {col_y2}",
                                  color_discrete_sequence=px.colors.sequential.Reds_r)
                elif chart_type == "แนวนอน":
                    fig2 = px.bar(grouped2, x=col_y2, y=col_x2, orientation='h', title=f"{col_y2} แยกตาม {col_x2}",
                                  color_discrete_sequence=["#9e2c2c"])
                else:
                    fig2 = px.bar(grouped2, x=col_x2, y=col_y2, title=f"{col_y2} แยกตาม {col_x2}",
                                  color=col_x2, color_discrete_sequence=px.colors.qualitative.Set2)
                fig2.update_layout(plot_bgcolor="#f8f9ee", paper_bgcolor="#f8f9ee")
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("ต้องมีคอลัมน์ข้อความและตัวเลขในข้อมูล")

        with t3:
            if len(num_cols) >= 2:
                cx = st.selectbox("แกน X", num_cols, key="sc_x")
                cy = st.selectbox("แกน Y", num_cols, index=min(1, len(num_cols)-1), key="sc_y")
                color_col = st.selectbox("สีตาม (optional)", ["(ไม่ใช้)"] + cat_cols, key="sc_c")
                color_arg = None if color_col == "(ไม่ใช้)" else color_col
                fig3 = px.scatter(df, x=cx, y=cy, color=color_arg, title=f"ความสัมพันธ์ {cx} vs {cy}",
                                  trendline="ols" if not color_arg else None,
                                  color_discrete_sequence=px.colors.qualitative.Bold)
                fig3.update_layout(plot_bgcolor="#f8f9ee", paper_bgcolor="#f8f9ee")
                st.plotly_chart(fig3, use_container_width=True)

                # Correlation heatmap
                if len(num_cols) >= 3:
                    st.markdown("**Correlation Heatmap**")
                    corr = df[num_cols].corr().round(2)
                    fig_hm = px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r",
                                       title="Correlation Matrix", aspect="auto")
                    st.plotly_chart(fig_hm, use_container_width=True)
            else:
                st.info("ต้องมีคอลัมน์ตัวเลขอย่างน้อย 2 คอลัมน์")

        with t4:
            st.markdown("**ตรวจสอบข้อมูล**")
            m1, m2, m3 = st.columns(3)
            m1.metric("จำนวนแถว", f"{df.shape[0]:,}")
            m2.metric("จำนวนคอลัมน์", f"{df.shape[1]:,}")
            m3.metric("ค่าว่าง", f"{df.isnull().sum().sum():,}")
            filter_col = st.selectbox("กรองตาม", ["(ไม่กรอง)"] + cat_cols, key="tbl_filter")
            if filter_col != "(ไม่กรอง)":
                val = st.selectbox("ค่า", df[filter_col].unique(), key="tbl_val")
                display_df = df[df[filter_col] == val]
            else:
                display_df = df
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            csv_out = display_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button("⬇️ ดาวน์โหลด CSV", csv_out, "filtered_data.csv", "text/csv")

    # ══════════════════════════════════════
    # MODE C: Custom
    # ══════════════════════════════════════
    else:
        import plotly.express as px
        import plotly.graph_objects as go

        st.markdown("---")
        with st.container(border=True):
            st.markdown("#### 🔧 Step 3 — กำหนด Chart เอง")
            st.markdown("เพิ่มกราฟได้ทีละตัว เลือกคอลัมน์และประเภทกราฟตามต้องการ")

        if 'custom_charts' not in st.session_state:
            st.session_state['custom_charts'] = []

        num_cols = df.select_dtypes(include='number').columns.tolist()
        cat_cols = df.select_dtypes(include=['object','category']).columns.tolist()

        with st.expander("➕ เพิ่ม Chart ใหม่", expanded=True):
            with st.container(border=True):
                cc1, cc2, cc3 = st.columns(3)
                chart_type_c = cc1.selectbox("ประเภทกราฟ", ["Bar","Line","Pie","Scatter","Histogram","Box"], key="cust_type")
                x_col = cc2.selectbox("แกน X / หมวดหมู่", df.columns.tolist(), key="cust_x")
                y_col = cc3.selectbox("แกน Y / ค่า", num_cols if num_cols else df.columns.tolist(), key="cust_y")
                chart_title_c = st.text_input("ชื่อกราฟ", value=f"{chart_type_c}: {y_col} by {x_col}", key="cust_title")
                if st.button("➕ เพิ่มกราฟนี้", type="primary"):
                    st.session_state['custom_charts'].append({"type": chart_type_c, "x": x_col, "y": y_col, "title": chart_title_c})
                    st.success(f"เพิ่ม {chart_type_c} chart แล้ว"); st.rerun()

        if st.session_state['custom_charts']:
            st.markdown("---")
            st.markdown(f"**Dashboard ({len(st.session_state['custom_charts'])} charts)**")
            col_right = st.columns([5,1])[1]
            if col_right.button("🗑️ ล้างทั้งหมด", type="secondary"):
                st.session_state['custom_charts'] = []; st.rerun()

            chart_cols = st.columns(2)
            for idx, chart_cfg in enumerate(st.session_state['custom_charts']):
                with chart_cols[idx % 2]:
                    try:
                        ctype = chart_cfg["type"]; cx = chart_cfg["x"]; cy = chart_cfg["y"]
                        title = chart_cfg["title"]
                        if ctype == "Bar":       fig = px.bar(df, x=cx, y=cy, title=title, color_discrete_sequence=["#7A2020"])
                        elif ctype == "Line":    fig = px.line(df, x=cx, y=cy, title=title, color_discrete_sequence=["#7A2020"])
                        elif ctype == "Pie":     fig = px.pie(df, names=cx, values=cy, title=title, color_discrete_sequence=px.colors.sequential.Reds_r)
                        elif ctype == "Scatter": fig = px.scatter(df, x=cx, y=cy, title=title, color_discrete_sequence=["#9e2c2c"])
                        elif ctype == "Histogram": fig = px.histogram(df, x=cx, title=title, color_discrete_sequence=["#7A2020"])
                        elif ctype == "Box":     fig = px.box(df, x=cx, y=cy, title=title, color_discrete_sequence=["#7A2020"])
                        else:                    fig = px.bar(df, x=cx, y=cy, title=title)
                        fig.update_layout(plot_bgcolor="#f8f9ee", paper_bgcolor="#f8f9ee", margin=dict(t=40,b=20,l=10,r=10))
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Chart {idx+1} error: {e}")
        else:
            st.info("ยังไม่มีกราฟ — กดเพิ่มกราฟด้านบน")

else:
    # No file uploaded yet
    st.markdown("---")
    with st.container(border=True):
        st.markdown("""
        <div style="text-align:center;padding:40px 20px;color:#7a7a7a;">
          <div style="font-size:3.5rem;margin-bottom:12px;">📂</div>
          <div style="font-size:16px;font-weight:600;color:#1a1a1a;margin-bottom:8px;">อัปโหลดข้อมูลเพื่อเริ่มต้น</div>
          <div style="font-size:13px;line-height:1.7;">รองรับไฟล์ Excel (.xlsx, .xls) และ CSV<br>
          จากนั้นเลือกโหมด: AI อัตโนมัติ · Template สำเร็จรูป · หรือกำหนดเอง</div>
        </div>
        """, unsafe_allow_html=True)
