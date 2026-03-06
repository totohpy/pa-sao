# theme.py — PA Planning Studio v5.7
# Sidebar color = config.toml (secondaryBackgroundColor = #7A2020)
# Streamlit auto-sets nav text to white when bg is dark — no CSS needed

GOV_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sarabun:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=Noto+Serif+Thai:wght@400;600;700&display=swap');
:root {
    --red:#7A2020; --red-dark:#621a1a; --red-pale:rgba(122,32,32,0.08);
    --cream:#FEFFD3; --green:#6D9E51; --green-lt:#BCD9A2; --green-pale:#e8f5e0;
    --blue:#3c5a8c; --bg:#f8f9ee; --bg-card:#ffffff; --border:#e3e4c4;
    --border-card:#d8d9b4; --text-h:#1a1a1a; --text-b:#404040; --text-mute:#7a7a7a;
}
html,body,[class*="css"],.stApp { font-family:'Sarabun',sans-serif !important; }
[data-testid="stAppViewContainer"]>.main { background-color:var(--bg) !important; }
.block-container { padding-top:1.6rem !important; padding-bottom:3rem !important; }

/* Nav link shape only — NO color override (config.toml handles text color) */
[data-testid="stSidebarNav"] a {
    border-radius:8px !important;
    padding:8px 14px !important;
    margin-bottom:2px !important;
    font-size:14px !important;
    display:block !important;
    transition:background 0.15s !important;
}
[data-testid="stSidebarNav"] a:hover {
    background:rgba(255,255,255,0.15) !important;
}
[data-testid="stSidebarNav"] a[aria-current="page"] {
    background:rgba(255,255,255,0.22) !important;
    font-weight:700 !important;
    border:1px solid rgba(255,255,255,0.28) !important;
}

/* ═══ Typography ═══ */
h1 { font-size:24px !important; font-weight:700 !important; color:var(--text-h) !important; font-family:'Noto Serif Thai',serif !important; }
h2 { font-size:19px !important; font-weight:700 !important; color:var(--text-h) !important; font-family:'Noto Serif Thai',serif !important; }
h3 { font-size:16px !important; font-weight:600 !important; color:var(--text-h) !important; }
h4 { font-size:12px !important; font-weight:700 !important; color:var(--red) !important; text-transform:uppercase; letter-spacing:1px; border-bottom:none !important; }

/* ═══ Inputs ═══ */
.stTextInput>div>div>input,.stTextArea>div>div>textarea,.stNumberInput>div>div>input {
    background:#fafaf0 !important; border:1px solid var(--border-card) !important;
    border-radius:9px !important; color:var(--text-h) !important;
    font-family:'Sarabun',sans-serif !important; font-size:15px !important;
}
.stTextInput>div>div>input:focus,.stTextArea>div>div>textarea:focus {
    border-color:var(--red) !important; box-shadow:0 0 0 3px rgba(122,32,32,0.07) !important;
}
.stTextInput label,.stTextArea label,.stSelectbox label,.stNumberInput label,
.stSlider label,.stFileUploader label,.stMultiSelect label,.stDateInput label {
    color:var(--text-mute) !important; font-size:12px !important;
    font-weight:700 !important; text-transform:uppercase; letter-spacing:0.5px;
}

/* ═══ Buttons ═══ */
.stButton>button { border-radius:9px !important; font-family:'Sarabun',sans-serif !important; font-weight:600 !important; font-size:14px !important; transition:all 0.18s !important; }
button[data-testid="baseButton-primary"] { background:var(--red) !important; color:#fff !important; border:none !important; }
button[data-testid="baseButton-primary"]:hover { background:var(--red-dark) !important; transform:translateY(-1px) !important; box-shadow:0 4px 16px rgba(122,32,32,0.28) !important; }
button[data-testid="baseButton-secondary"] { background:#fff !important; color:var(--text-h) !important; border:1px solid var(--border-card) !important; }
button[data-testid="baseButton-secondary"]:hover { border-color:var(--red) !important; color:var(--red) !important; }

/* ═══ Tabs ═══ */
div[data-baseweb="tab-list"] { background:#fff !important; border:1px solid var(--border-card) !important; border-radius:12px !important; padding:5px !important; gap:3px !important; border-bottom:none !important; flex-wrap:wrap !important; margin-bottom:16px !important; }
button[data-baseweb="tab"] { background:transparent !important; border-radius:8px !important; color:var(--text-mute) !important; font-size:13px !important; font-weight:500 !important; padding:7px 14px !important; border:none !important; box-shadow:none !important; transition:all 0.16s !important; transform:none !important; font-family:'Sarabun',sans-serif !important; }
button[data-baseweb="tab"]:hover { background:var(--cream) !important; color:var(--text-h) !important; }
button[data-baseweb="tab"][aria-selected="true"] { background:var(--red) !important; color:#fff !important; font-weight:600 !important; }

/* ═══ DataFrame ═══ */
.stDataFrame,.stDataEditor { border-radius:12px !important; overflow:hidden !important; border:1px solid var(--border-card) !important; }
.stDataFrame thead th { background:rgba(254,255,211,0.85) !important; color:var(--red) !important; font-size:11.5px !important; font-weight:700 !important; text-transform:uppercase !important; }
.stDataFrame tbody td { color:var(--text-b) !important; font-size:14px !important; }

/* ═══ Alerts ═══ */
div[data-testid="stInfo"]    { background:var(--cream) !important; border:1px solid #e0e098 !important; border-left:4px solid var(--red) !important; border-radius:10px !important; }
div[data-testid="stSuccess"] { background:var(--green-pale) !important; border:1px solid var(--green-lt) !important; border-left:4px solid var(--green) !important; border-radius:10px !important; }
div[data-testid="stWarning"] { background:#fff8e1 !important; border:1px solid #ffe082 !important; border-left:4px solid #f59e0b !important; border-radius:10px !important; }
div[data-testid="stError"]   { background:rgba(122,32,32,0.05) !important; border:1px solid rgba(122,32,32,0.2) !important; border-left:4px solid var(--red) !important; border-radius:10px !important; }

/* ═══ Container ═══ */
div[data-testid="stVerticalBlockBorderWrapper"]>div { background:var(--bg-card) !important; border:1px solid var(--border-card) !important; border-radius:14px !important; padding:18px !important; }

/* ═══ Chat ═══ */
div[data-testid="stChatMessage"] { background:var(--bg-card) !important; border:1px solid var(--border) !important; border-radius:12px !important; margin-bottom:8px !important; }
.stChatInput>div { background:#fafaf0 !important; border:1px solid var(--border-card) !important; border-radius:12px !important; }
.stChatInput>div:focus-within { border-color:var(--red) !important; }

/* ═══ Misc ═══ */
.stSelectbox>div>div,.stMultiSelect>div>div { background:#fafaf0 !important; border:1px solid var(--border-card) !important; border-radius:9px !important; }
.stSlider>div>div>div>div { background:var(--red) !important; }
div[data-testid="stFileUploader"] { background:rgba(254,255,211,0.4) !important; border:1.5px dashed var(--border-card) !important; border-radius:12px !important; }
div[data-testid="stFileUploader"]:hover { border-color:var(--red) !important; }
.stDownloadButton>button { background:var(--green-pale) !important; color:#2d5a1a !important; border:1px solid var(--green-lt) !important; border-radius:9px !important; font-weight:600 !important; }
div[data-testid="stMetric"] { background:var(--bg-card) !important; border:1px solid var(--border-card) !important; border-radius:12px !important; padding:16px !important; }
div[data-testid="stMetricLabel"] { color:var(--text-mute) !important; font-size:12px !important; font-weight:700 !important; text-transform:uppercase; }
div[data-testid="stMetricValue"] { color:var(--text-h) !important; font-size:24px !important; }
hr { border-color:var(--border) !important; margin:20px 0 !important; }
::-webkit-scrollbar { width:5px; height:5px; }
::-webkit-scrollbar-thumb { background:rgba(122,32,32,0.2); border-radius:10px; }

/* ═══ Sidebar footer card ═══ */
.sb-footer { padding:12px; border-top:1px solid rgba(255,255,255,0.18); margin-top:12px; }
.sb-footer-card { background:rgba(255,255,255,0.13); border:1px solid rgba(255,255,255,0.22); border-radius:10px; padding:10px 12px; display:flex; align-items:center; gap:10px; }
.sb-emblem { width:32px; height:32px; background:rgba(255,255,255,0.22); border-radius:8px; display:flex; align-items:center; justify-content:center; flex-shrink:0; font-size:17px; }
.sb-name { font-size:13px; font-weight:700; display:block; }
.sb-org  { font-size:11px; opacity:0.70; margin-top:1px; display:block; }
</style>
"""

SIDEBAR_HTML = """
<div class="sb-footer">
  <div class="sb-footer-card">
    <div class="sb-emblem">🏛️</div>
    <div>
      <span class="sb-name">Audit Intelligence Team</span>
      <span class="sb-org">By PAO1 · สตง.</span>
    </div>
  </div>
</div>
"""

def apply_theme():
    import streamlit as st
    st.markdown(GOV_CSS, unsafe_allow_html=True)
