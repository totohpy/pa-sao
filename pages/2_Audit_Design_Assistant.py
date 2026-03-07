# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os, io, re
import docx
from PyPDF2 import PdfReader
from streamlit_agraph import agraph, Node, Edge, Config

import sys, pathlib
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

st.set_page_config(page_title="Audit Design Assistant", page_icon="✨", layout="wide")
apply_theme()

with st.sidebar:
    st.markdown(SIDEBAR_HTML, unsafe_allow_html=True)
    render_ai_sidebar()

# ── Helper Functions ────────────────────────────────────
def init_state():
    ss = st.session_state
    ss.setdefault("plan", {
        "plan_id": "PLN-" + datetime.now().strftime("%y%m%d-%H%M%S"),
        "plan_title":"","program_name":"","who":"","what":"","where":"",
        "when":"","why":"","how":"","how_much":"","whom":"",
        "objectives":"","scope":"","assumptions":"","status":"Draft"
    })
    ss.setdefault("logic_items",  pd.DataFrame(columns=["item_id","plan_id","type","description","metric","unit","target","source"]))
    ss.setdefault("risks",        pd.DataFrame(columns=["risk_id","plan_id","description","category","likelihood","impact","mitigation","hypothesis"]))
    ss.setdefault("audit_issues", pd.DataFrame(columns=["issue_id","plan_id","title","rationale","linked_kpi","proposed_methods","source_finding_id","issue_detail","recommendation"]))
    ss.setdefault("gen_issues",   "")
    ss.setdefault("gen_findings", "")
    ss.setdefault("gen_report",   "")
    ss.setdefault("issue_results", pd.DataFrame())
    ss.setdefault("ref_seed",          "")
    ss.setdefault("issue_query_text",  "")
    ss.setdefault("6w2h_output",       "")

def next_id(prefix, df, col):
    if df.empty: return f"{prefix}-001"
    nums = [int(str(x).split("-")[-1]) for x in df[col] if str(x).split("-")[-1].isdigit()]
    return f"{prefix}-{(max(nums)+1 if nums else 1):03d}"

def df_download_link(df, filename, label):
    buf = BytesIO()
    df.to_csv(buf, index=False, encoding="utf-8-sig")
    st.download_button(label, data=buf.getvalue(), file_name=filename, mime="text/csv")

@st.cache_data(show_spinner=False)
def load_findings(uploaded=None):
    findings_df = pd.DataFrame()
    if os.path.exists("FindingsLibrary.csv"):
        try: findings_df = pd.read_csv("FindingsLibrary.csv")
        except Exception as e: st.error(f"อ่าน FindingsLibrary.csv ผิดพลาด: {e}")
    if uploaded is not None:
        try:
            if uploaded.name.endswith('.csv'):
                uploaded_df = pd.read_csv(uploaded)
            elif uploaded.name.endswith(('.xlsx','.xls')):
                xls = pd.ExcelFile(uploaded)
                sheet_name = "Data" if "Data" in xls.sheet_names else 0
                uploaded_df = pd.read_excel(xls, sheet_name=sheet_name)
            if not uploaded_df.empty:
                findings_df = pd.concat([findings_df, uploaded_df], ignore_index=True)
                st.success(f"อัปโหลด '{uploaded.name}' เรียบร้อยแล้ว")
        except Exception as e: st.error(f"อ่านไฟล์ผิดพลาด: {e}")
    if not findings_df.empty:
        for c in ["issue_title","issue_detail","cause_detail","recommendation","program","unit"]:
            if c in findings_df.columns: findings_df[c] = findings_df[c].fillna("")
        if "year" in findings_df.columns:
            findings_df["year"] = pd.to_numeric(findings_df["year"], errors="coerce").fillna(0).astype(int)
        if "severity" in findings_df.columns:
            findings_df["severity"] = pd.to_numeric(findings_df["severity"], errors="coerce").fillna(3).clip(1,5).astype(int)
    return findings_df

@st.cache_resource(show_spinner=False)
def build_tfidf_index(_df):
    texts = (_df["issue_title"].fillna("") + " " + _df["issue_detail"].fillna("") +
             " " + _df["cause_detail"].fillna("") + " " + _df["recommendation"].fillna(""))
    vec = TfidfVectorizer(max_features=20000, ngram_range=(1,2))
    X = vec.fit_transform(texts)
    return vec, X

def search_candidates(query, findings_df, vec, X, top_k=8):
    qv = vec.transform([query])
    sims = cosine_similarity(qv, X)[0]
    out = findings_df.copy()
    out["sim_score"] = sims
    out["year_norm"] = ((out["year"] - out["year"].min()) / (out["year"].max() - out["year"].min())
                        if "year" in out.columns and out["year"].max() != out["year"].min() else 0.0)
    out["sev_norm"] = out.get("severity", 3) / 5
    out["score"] = out["sim_score"]*0.65 + out["sev_norm"]*0.25 + out["year_norm"]*0.10
    cols = ["finding_id","year","unit","program","issue_title","issue_detail",
            "cause_category","cause_detail","recommendation","outcomes_impact","severity","score","sim_score"]
    return out.sort_values("score", ascending=False).head(top_k)[[c for c in cols if c in out.columns]]

def create_excel_template():
    df = pd.DataFrame(columns=["finding_id","issue_title","unit","program","year",
                                "cause_category","cause_detail","issue_detail",
                                "recommendation","outcomes_impact","severity"])
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as w: df.to_excel(w, index=False, sheet_name='FindingsLibrary')
    return out.getvalue()

def create_interactive_flowchart(df):
    nodes, edges = [], []
    styles = {"Objective":"#E6E6FA","Input":"#a9def9","Activity":"#e4c1f9",
              "Output":"#fcf6bd","Outcome":"#d0f4de","Impact":"#ff99c8"}
    sequence = ["Objective","Input","Activity","Output","Outcome","Impact"]
    nodes_exist = []
    for i, t in enumerate(sequence):
        items = df[df['type']==t]
        if not items.empty:
            lines = [f"• {r.get('description','')} {r.get('target','') or r.get('metric','')} {r.get('unit','')}".strip() for _,r in items.iterrows()]
            nodes.append(Node(id=t, label=f"{t}\n\n"+"\n".join(lines), color=styles.get(t),
                              shape="box", font={'face':'Kanit','align':'left'}, level=i))
            nodes_exist.append(t)
    if len(nodes_exist) > 1:
        for i in range(len(nodes_exist)-1):
            edges.append(Edge(source=nodes_exist[i], target=nodes_exist[i+1], color="#000000"))
    config = Config(width='100%', height=600, directed=True, physics=False,
                    hierarchical={"enabled":True,"direction":"LR","sortMethod":"directed"})
    return nodes, edges, config

def parse_and_update_6w2h(ai_text):
    ss = st.session_state
    all_keys = r"Who:|Whom:|What:|Where:|When:|Why:|How:|How much:"
    patterns = {
        "who":      rf"Who\s*:\s*(.*?)(?={all_keys}|\Z)",
        "whom":     rf"Whom\s*:\s*(.*?)(?={all_keys}|\Z)",
        "what":     rf"What\s*:\s*(.*?)(?={all_keys}|\Z)",
        "where":    rf"Where\s*:\s*(.*?)(?={all_keys}|\Z)",
        "when":     rf"When\s*:\s*(.*?)(?={all_keys}|\Z)",
        "why":      rf"Why\s*:\s*(.*?)(?={all_keys}|\Z)",
        "how":      rf"How\s*:\s*(.*?)(?={all_keys}|\Z)",
        "how_much": rf"How much\s*:\s*(.*?)(?={all_keys}|\Z)",
    }
    extracted = {}
    for key, pat in patterns.items():
        m = re.search(pat, ai_text, re.DOTALL|re.IGNORECASE)
        if m:
            c = m.group(1).strip()
            c = re.sub(r"^\s*[\•\-\s]*","",c,flags=re.MULTILINE).strip()
            c = re.sub(r"^\s*\*\*","",c).strip()
            c = re.sub(r"\*\*\s*$","",c).strip()
            extracted[key] = c
    for key, val in extracted.items():
        if val:
            if key in ss.plan: ss.plan[key] = val
            if f"{key}_input" in ss: ss[f"{key}_input"] = val
    return extracted

# ── Init ────────────────────────────────────────────────
init_state()
plan          = st.session_state["plan"]
logic_df      = st.session_state["logic_items"]
risks_df      = st.session_state["risks"]
audit_issues_df = st.session_state["audit_issues"]

# ── Page Header ─────────────────────────────────────────
st.title("✨ Audit Design Assistant")
st.markdown("เครื่องมือช่วยสรุปข้อมูลและกำหนดประเด็นการตรวจสอบ")

with st.expander("💡 คำแนะนำการใช้งาน"):
    st.info("กรุณาระบุข้อมูล อย่างน้อย **ระบุ แผน & 6W2H** เพื่อค้นหาข้อตรวจพบที่ผ่านมาและให้ PA Assistant แนะนำได้แม่นยำที่สุด")

# ── Tabs ─────────────────────
tab_plan, tab_logic, tab_risk, tab_issue, tab_preview, tab_assist = st.tabs([
    "1. ระบุ แผน & 6W2H",
    "2. ระบุ Logic Model",
    "3. ระบุ Risks",
    "🔍 ค้นหาข้อตรวจพบที่ผ่านมา",
    "📋 สรุปข้อมูล (Preview)",
    "✨ PA Assistant แนะนำประเด็น",
])

# ── Tab 1: Plan & 6W2H ─────────────────────────────────
with tab_plan:
    st.subheader("ข้อมูลแผน")
    with st.container(border=True):
        c1, c2, c3 = st.columns([2,2,1])
        with c1:
            plan["plan_title"]   = st.text_input("ชื่อแผน/เรื่องที่จะตรวจ", plan["plan_title"])
            plan["program_name"] = st.text_input("ชื่อโครงการ/แผนงาน",      plan["program_name"])
            plan["objectives"]   = st.text_area("วัตถุประสงค์การตรวจ",       plan["objectives"])
        with c2:
            plan["scope"]       = st.text_area("ขอบเขตการตรวจ",                 plan["scope"])
            plan["assumptions"] = st.text_area("สมมติฐาน/ข้อจำกัดข้อมูล",     plan["assumptions"])
        with c3:
            st.text_input("Plan ID", plan["plan_id"], disabled=True)
            plan["status"] = st.selectbox("สถานะ", ["Draft","Published"], index=0)

    st.divider()
    st.subheader("สรุปเรื่องที่ตรวจสอบ (6W2H)")

    with st.container(border=True):
        st.markdown("##### 🚀 สร้าง 6W2H อัตโนมัติด้วย AI")
        st.write("คัดลอกข้อความมาวางในช่องด้านล่าง หรืออัปโหลดไฟล์เพื่อดึงข้อความอัตโนมัติ")

    if "uploaded_text" not in st.session_state:
        st.session_state.uploaded_text = ""

    st.write("อัปโหลดไฟล์ .docx หรือ .pdf")
    uploaded_file = st.file_uploader("เลือกไฟล์เอกสาร...", type=['docx','pdf'], label_visibility="collapsed")

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.pdf'):
                reader = PdfReader(uploaded_file)
                text = "".join(p.extract_text() or "" for p in reader.pages)
            elif uploaded_file.name.endswith('.docx'):
                doc = docx.Document(uploaded_file)
                text = "\n".join(p.text for p in doc.paragraphs)
            st.session_state.uploaded_text = text
            st.success("ดึงข้อความจากไฟล์สำเร็จ!")
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")

    st.text_area("ระบุข้อความเพื่อให้ AI ช่วยสรุป 6W2H", key="uploaded_text", height=250)

    if st.button("🚀 สร้าง 6W2H จากข้อความ", type="primary", key="6w2h_button"):
        txt = st.session_state.uploaded_text
        from ai_provider import is_ready, get_ai_response
        if not txt:
            st.error("กรุณาอัปโหลดไฟล์ หรือวางข้อความในช่องก่อน")
        elif not is_ready():
            st.error("ยังไม่ได้ตั้งค่า AI Provider (โปรดตรวจสอบที่แถบด้านข้าง)")
        else:
            with st.spinner("กำลังประมวลผล..."):
                try:
                    prompt = (f"จากข้อความด้านล่างนี้ กรุณาสรุปและแยกแยะข้อมูลให้เป็น 6W2H "
                              f"โดยระบุหัวข้อ (Who, Whom, What, Where, When, Why, How, How much) "
                              f"และใช้เครื่องหมาย : คั่นให้ชัดเจน ดังตัวอย่าง Who: [คำตอบ]\n"
                              f"ข้อความ:\n---\n{txt}\n---\n")
                    ai_out = get_ai_response(
                        messages=[{"role":"user","content":prompt}],
                        temperature=0.7, max_tokens=3072,
                    )
                    st.session_state["6w2h_output"] = ai_out
                    parse_and_update_6w2h(ai_out)
                    st.success("สร้าง 6W2H เรียบร้อยแล้ว!"); st.balloons(); st.rerun()
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาดในการเรียกใช้ AI: {e}")

    if st.session_state.get("6w2h_output"):
        with st.expander("คลิกเพื่อดูผลลัพธ์จาก AI ล่าสุด", expanded=True):
            st.info("ผลลัพธ์จาก AI ถูกเติมลงในช่อง 6W2H แล้ว กรุณาตรวจสอบและแก้ไข")
            with st.container(border=True):
                st.markdown(st.session_state["6w2h_output"])

    st.markdown("##### ⭐ กรุณาระบุข้อมูล (ตรวจสอบ/แก้ไขข้อมูลที่ AI เติมให้)")
    with st.container(border=True):
        cc1, cc2, cc3 = st.columns(3)
        with cc1:
            plan["who"]  = st.text_input("Who (ใคร)",       plan["who"],  key="who_input")
            plan["whom"] = st.text_input("Whom (เพื่อใคร)", plan["whom"], key="whom_input")
            plan["what"] = st.text_input("What (ทำอะไร)",   plan["what"], key="what_input")
        with cc2:
            plan["where"] = st.text_input("Where (ที่ไหน)",    plan["where"], key="where_input")
            plan["when"]  = st.text_input("When (เมื่อใด)",    plan["when"],  key="when_input")
            plan["why"]   = st.text_area("Why (ทำไม)",         plan["why"],   key="why_input")
        with cc3:
            plan["how"]      = st.text_area("How (อย่างไร)",      plan["how"],      key="how_input")
            plan["how_much"] = st.text_input("How much (เท่าไร)", plan["how_much"], key="how_much_input")

# ── Tab 2: Logic Model ──────────────────────────────────
with tab_logic:
    st.subheader("ระบุ Logic Model")
    with st.expander("➕ เพิ่มรายการใหม่", expanded=True):
        with st.container(border=True):
            colA, colB, colC = st.columns(3)
            with colA:
                typ  = st.selectbox("ประเภท", ["Objective","Input","Activity","Output","Outcome","Impact"], key="logic_type")
                desc = st.text_input("คำอธิบาย/รายละเอียด", key="logic_desc")
            with colB:
                metric = st.text_input("ตัวชี้วัด (จำนวน)", key="logic_metric")
                unit   = st.text_input("หน่วย", value="", key="logic_unit")
            with colC:
                target = st.text_input("เป้าหมาย", value="", key="logic_target")
                source = st.text_input("แหล่งข้อมูล", value="", key="logic_source")
            if st.button("เพิ่ม Logic Item", type="primary", key="add_logic_btn"):
                if desc:
                    new_row = pd.DataFrame([{"item_id":next_id("LG",logic_df,"item_id"),"plan_id":plan["plan_id"],
                                             "type":typ,"description":desc,"metric":metric,"unit":unit,"target":target,"source":source}])
                    st.session_state.logic_items = pd.concat([logic_df, new_row], ignore_index=True)
                    st.success("เพิ่มข้อมูลเรียบร้อยแล้ว"); st.rerun()
                else: st.warning("กรุณากรอก 'คำอธิบาย/รายละเอียด'")

    st.markdown("---")
    st.markdown("##### 📝 ตาราง Logic Model")
    logic_df = st.session_state.logic_items
    st.session_state.logic_items = st.data_editor(logic_df,
        column_config={
            "type":        st.column_config.SelectboxColumn("ประเภท", options=["Objective","Input","Activity","Output","Outcome","Impact"], required=True),
            "description": st.column_config.TextColumn("คำอธิบาย", required=True),
            "item_id":     st.column_config.TextColumn("ID", disabled=True),
            "plan_id":     st.column_config.TextColumn("Plan ID", disabled=True),
        },
        use_container_width=True, hide_index=True, key="logic_editor_main")

    cols = st.columns([0.85,0.15])
    with cols[1]:
        if st.button("🧹 ล้างทั้งหมด", use_container_width=True):
            st.session_state.logic_items = pd.DataFrame(columns=logic_df.columns); st.rerun()

    st.markdown("---")
    st.subheader("📊 Flowchart Logic Model")
    with st.container(border=True):
        if not st.session_state.logic_items.empty:
            try:
                nodes, edges, config = create_interactive_flowchart(st.session_state.logic_items)
                agraph(nodes=nodes, edges=edges, config=config)
            except Exception as e: st.error(f"ไม่สามารถสร้าง Flowchart ได้: {e}")
        else: st.info("กรุณาเพิ่มข้อมูลเพื่อสร้าง Flowchart")

# ── Tab 3: Risks ────────────────────────────────────────
with tab_risk:
    st.subheader("ระบุความเสี่ยง (Risks)")
    st.dataframe(risks_df, use_container_width=True, hide_index=True)
    with st.expander("➕ เพิ่ม Risk"):
        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
            rdesc       = c1.text_area("คำอธิบายความเสี่ยง")
            category    = c1.selectbox("หมวด", ["policy","org","data","process","people"])
            likelihood  = c2.select_slider("โอกาสเกิด (1-5)", options=[1,2,3,4,5], value=3)
            impact      = c2.select_slider("ผลกระทบ (1-5)",   options=[1,2,3,4,5], value=3)
            mitigation  = c3.text_area("มาตรการลดความเสี่ยง")
            hypothesis  = c3.text_input("สมมติฐานที่ต้องทดสอบ")
            if st.button("เพิ่ม Risk", type="primary", key="add_risk_btn"):
                new_row = pd.DataFrame([{"risk_id":next_id("RSK",risks_df,"risk_id"),"plan_id":plan["plan_id"],
                                         "description":rdesc,"category":category,"likelihood":likelihood,
                                         "impact":impact,"mitigation":mitigation,"hypothesis":hypothesis}])
                st.session_state["risks"] = pd.concat([risks_df, new_row], ignore_index=True); st.rerun()

# ── Tab 4: ค้นหาข้อตรวจพบ ──────────────────────────────
with tab_issue:
    st.subheader("🔎 แนะนำประเด็นตรวจสอบจากรายงานเก่า")
    with st.expander("อัปโหลดและจัดการฐานข้อมูลข้อตรวจพบ"):
        st.write("อัปโหลดไฟล์ .csv หรือ .xlsx ที่มีข้อมูลข้อตรวจพบ ถ้าไม่มีจะค้นหาภายในคลังข้อมูล")
        st.download_button(
            label="⬇️ ดาวน์โหลดไฟล์แม่แบบ FindingsLibrary.xlsx",
            data=create_excel_template(),
            file_name="FindingsLibrary.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        uploaded = st.file_uploader("อัปโหลด FindingsLibrary.csv หรือ .xlsx", type=["csv","xlsx","xls"], label_visibility="collapsed")

    findings_df = load_findings(uploaded=uploaded)

    if findings_df.empty:
        st.info("ไม่พบข้อมูล Findings โปรดอัปโหลดไฟล์")
    else:
        st.success(f"พบข้อมูล Findings ทั้งหมด {len(findings_df)} รายการ")
        vec, X = build_tfidf_index(findings_df)
        seed = (f"Who:{plan.get('who','')} What:{plan.get('what','')} Where:{plan.get('where','')} "
                f"When:{plan.get('when','')} Why:{plan.get('why','')} Whom:{plan.get('whom','')} "
                f"How:{plan.get('how','')} "
                f"Outputs:{' | '.join(logic_df[logic_df['type']=='Output']['description'].tolist())} "
                f"Outcomes:{' | '.join(logic_df[logic_df['type']=='Outcome']['description'].tolist())} "
                f"Objective:{' | '.join(logic_df[logic_df['type']=='Objective']['description'].tolist())}")

        def refresh_query_text(new_seed):
            st.session_state["issue_query_text"] = new_seed
            st.session_state["ref_seed"] = new_seed

        if not st.session_state.get("issue_query_text"):
            st.session_state["issue_query_text"] = seed
            st.session_state["ref_seed"] = seed
        elif st.session_state.get("ref_seed") != seed and st.session_state.get("issue_query_text") == st.session_state.get("ref_seed"):
            st.session_state["issue_query_text"] = seed
            st.session_state["ref_seed"] = seed

        c_q, c_r = st.columns([6,1])
        with c_q:
            query_text = st.text_area("**ข้อมูล (Context) ที่ใช้ค้นหา (แก้ไขได้):**",
                                      st.session_state["issue_query_text"], height=140,
                                      key="issue_query_text")
        with c_r:
            st.markdown("<br>", unsafe_allow_html=True)
            st.button("🔄", on_click=refresh_query_text, args=(seed,),
                      help="อัปเดตช่องค้นหาด้วยข้อมูลล่าสุด", type="secondary")

        top_k = st.slider("ปรับจำนวนผลลัพธ์:", min_value=1, max_value=20, value=8)

        if st.button("ค้นหาประเด็นที่ใกล้เคียง", type="primary", key="search_btn"):
            st.session_state["issue_results"] = search_candidates(
                st.session_state.get("issue_query_text", seed), findings_df, vec, X, top_k=top_k)
            st.success(f"พบประเด็นที่เกี่ยวข้อง {len(st.session_state['issue_results'])} รายการ")

        results = st.session_state.get("issue_results", pd.DataFrame())
        if not results.empty:
            st.divider(); st.subheader("ผลลัพธ์การค้นหา 🗃️")
            for i, row in results.reset_index(drop=True).iterrows():
                with st.container(border=True):
                    title_txt = row.get("issue_title","(ไม่มีชื่อประเด็น)")
                    year_txt  = int(row["year"]) if "year" in row and str(row["year"]).isdigit() else row.get("year","-")
                    st.markdown(f"**{title_txt}** \nหน่วย: {row.get('unit','-')} · โครงการ: {row.get('program','-')} · ปี: {year_txt}")
                    st.caption(f"สาเหตุ: *{row.get('cause_category','-')}* — {row.get('cause_detail','-')}")
                    with st.expander("รายละเอียด/ข้อเสนอแนะเดิม"):
                        st.write(row.get("issue_detail","-"))
                        st.caption("ข้อเสนอแนะเดิม: " + (row.get("recommendation","") or "-"))
                        st.markdown(
                            f"**ผลกระทบ:** {row.get('outcomes_impact','-')}  ·  "
                            f"<span style='color:red;'>**ความเกี่ยวข้อง**</span>: {row.get('score',0):.3f} "
                            f"(<span style='color:blue;'>Similarity</span>={row.get('sim_score',0):.3f})",
                            unsafe_allow_html=True
                        )
                    c1, c2 = st.columns([3,1])
                    with c1:
                        st.text_area("เหตุผลที่ควรตรวจ", key=f"rat_{i}", value=f"อ้างอิงกรณีเดิม ปี {year_txt} | ")
                        st.text_input("KPI ที่เกี่ยว (ถ้ามี)",         key=f"kpi_{i}")
                        st.text_input("วิธีเก็บข้อมูลที่เสนอ",          key=f"mth_{i}", value="สัมภาษณ์/สังเกต/ตรวจเอกสาร")
                    with c2:
                        if st.button("➕ เพิ่มเป็นประเด็น", key=f"add_{i}", type="secondary"):
                            audit_issues_df = st.session_state["audit_issues"]
                            new_row = pd.DataFrame([{
                                "issue_id":        next_id("ISS", audit_issues_df, "issue_id"),
                                "plan_id":         plan.get("plan_id",""),
                                "title":           title_txt,
                                "rationale":       st.session_state.get(f"rat_{i}",""),
                                "linked_kpi":      st.session_state.get(f"kpi_{i}",""),
                                "proposed_methods":st.session_state.get(f"mth_{i}",""),
                                "source_finding_id":row.get("finding_id",""),
                                "issue_detail":    row.get("issue_detail",""),
                                "recommendation":  row.get("recommendation",""),
                            }])
                            st.session_state["audit_issues"] = pd.concat([audit_issues_df, new_row], ignore_index=True)
                            st.success("เพิ่มประเด็นเข้าแผนแล้ว ✅"); st.rerun()

        st.markdown("### ประเด็นที่เพิ่มเข้าแผน 🛒")
        st.dataframe(st.session_state["audit_issues"], use_container_width=True, hide_index=True)

# ── Tab 5: Preview ──────────────────────────────────────
with tab_preview:
    st.subheader("สรุปแผน (Preview)")
    with st.container(border=True):
        st.markdown(f"**Plan ID:** {plan['plan_id']}  \n**ชื่อแผน:** {plan['plan_title']}  \n**โครงการ:** {plan['program_name']}  \n**หน่วยรับตรวจ:** {plan['who']}")
    st.markdown("### สรุปเรื่องที่ตรวจสอบ (6W2H)")
    with st.container(border=True):
        st.markdown(f"- **Who**: {plan['who']}\n- **Whom**: {plan['whom']}\n- **What**: {plan['what']}\n"
                    f"- **Where**: {plan['where']}\n- **When**: {plan['when']}\n- **Why**: {plan['why']}\n"
                    f"- **How**: {plan.get('how','')}\n- **How much**: {plan.get('how_much','')}")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Logic Model")
        st.dataframe(st.session_state["logic_items"], use_container_width=True, hide_index=True)
        df_download_link(st.session_state["logic_items"], "logic_items.csv", "⬇️ ดาวน์โหลด Logic Items")
    with c2:
        st.markdown("### Risks")
        st.dataframe(st.session_state["risks"], use_container_width=True, hide_index=True)
        df_download_link(st.session_state["risks"], "risks.csv", "⬇️ ดาวน์โหลด Risks")

    st.markdown("### ประเด็นการตรวจสอบที่เพิ่มเข้ามา")
    if not st.session_state["audit_issues"].empty:
        st.dataframe(st.session_state["audit_issues"], use_container_width=True, hide_index=True)
        df_download_link(st.session_state["audit_issues"], "audit_issues.csv", "⬇️ ดาวน์โหลด Audit Issues")
    else:
        st.info("ยังไม่มีประเด็นการตรวจสอบที่เพิ่มเข้ามาในแผน")

    st.divider()
    df_download_link(pd.DataFrame([plan]), "plan.csv", "⬇️ ดาวน์โหลด Plan")
    st.success("พร้อมเชื่อมต่อ 🤖 PA Assistant เพื่อแนะนำประเด็นที่ควรตรวจสอบ ✨")

# ── Tab 6: PA Assistant ─────────────────────────────────
with tab_assist:
    st.subheader("💡 PA Assistant (AI/LLM)")
    st.write("🤖 สร้างคำแนะนำประเด็นที่ควรตรวจสอบจาก AI")

    if st.button("🚀 สร้างคำแนะนำจาก AI", type="primary", key="llm_assist_btn"):
        from ai_provider import is_ready, get_ai_response
        if not is_ready():
            st.error("กรุณาตั้งค่า AI Provider ที่แถบด้านข้างก่อนทำการสร้างคำแนะนำ")
        else:
            with st.spinner("กำลังสร้างคำแนะนำ..."):
                try:
                    issues_for_llm = st.session_state["audit_issues"][["title","rationale"]]
                    plan_summary = (
                        f"ชื่อแผน: {plan['plan_title']}\nโครงการ: {plan['program_name']}\n"
                        f"วัตถุประสงค์: {plan['objectives']}\nขอบเขต: {plan['scope']}\n---\n"
                        f"6W2H:\nWho: {plan['who']}\nWhom: {plan['whom']}\nWhat: {plan['what']}\n"
                        f"Where: {plan['where']}\nWhen: {plan['when']}\nWhy: {plan['why']}\n"
                        f"How: {plan['how']}\nHow much: {plan['how_much']}\n---\n"
                        f"Logic Model:\n{st.session_state['logic_items'].to_string()}\n---\n"
                        f"ประเด็นจากรายงานเก่า:\n{issues_for_llm.to_string()}"
                    )
                    user_prompt = (
                        f"จากข้อมูลแผนการตรวจสอบด้านล่างนี้ กรุณาช่วยสร้างคำแนะนำ 3 อย่าง:\n"
                        f"1. ประเด็นที่ควรตรวจสอบ พร้อมเหตุผล\n"
                        f"2. ข้อตรวจพบที่คาดว่าจะพบ (โอกาส: สูง/กลาง/ต่ำ) พร้อมเหตุผล\n"
                        f"3. ร่างรายงานตรวจสอบ วิเคราะห์ผลกระทบและสาเหตุ\n---\n{plan_summary}\n---\n"
                        f"กรุณาตอบตามรูปแบบ:\n"
                        f"<ประเด็นที่ควรตรวจสอบ>\n[ข้อความ]\n</ประเด็นที่ควรตรวจสอบ>\n\n"
                        f"<ข้อตรวจพบที่คาดว่าจะพบ>\n[ข้อความ]\n</ข้อตรวจพบที่คาดว่าจะพบ>\n\n"
                        f"<ร่างรายงานตรวจสอบ>\n[ข้อความ]\n</ร่างรายงานตรวจสอบ>"
                    )
                    full = get_ai_response(
                        messages=[{"role":"user","content":user_prompt}],
                        system_prompt="คุณคือผู้เชี่ยวชาญด้านการตรวจสอบผลสัมฤทธิ์และประสิทธิภาพการดำเนินงาน (Performance Auditing)",
                        temperature=0.7, max_tokens=3072,
                    )
                    def extract(text, tag):
                        s = text.find(f"<{tag}>") + len(f"<{tag}>")
                        e = text.find(f"</{tag}>")
                        return text[s:e].strip() if s > -1 and e > -1 else ""
                    st.session_state["gen_issues"]   = extract(full, "ประเด็นที่ควรตรวจสอบ")
                    st.session_state["gen_findings"] = extract(full, "ข้อตรวจพบที่คาดว่าจะพบ")
                    st.session_state["gen_report"]   = extract(full, "ร่างรายงานตรวจสอบ")
                    st.success("สร้างคำแนะนำจาก AI เรียบร้อยแล้ว ✅")
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาด: {e}")

    with st.expander("1. ประเด็นที่ควรตรวจสอบ", expanded=True):
        st.write(st.session_state.get("gen_issues",   "ยังไม่มีข้อมูล กด 'สร้างคำแนะนำจาก AI' เพื่อเริ่มต้น"))
    with st.expander("2. ข้อตรวจพบที่คาดว่าจะพบ"):
        st.write(st.session_state.get("gen_findings", "ยังไม่มีข้อมูล"))
    with st.expander("3. ร่างรายงานตรวจสอบ (Preview)"):
        st.write(st.session_state.get("gen_report",   "ยังไม่มีข้อมูล"))
