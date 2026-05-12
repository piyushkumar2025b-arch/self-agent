import streamlit as st

st.set_page_config(
    page_title="AgentOS — Multi-Agent Platform",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Shared CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

*, body, .stApp { font-family: 'Inter', sans-serif !important; }

/* sidebar */
section[data-testid="stSidebar"] {
    background: #0f0f1a !important;
    border-right: 1px solid #1e1e3a;
}
section[data-testid="stSidebar"] * { color: #c9c9e3 !important; }
section[data-testid="stSidebar"] .stRadio label { font-size: 14px; }

/* main bg */
.stApp { background: #080812; }
.block-container { padding-top: 1.5rem !important; }

/* cards */
.agent-card {
    background: linear-gradient(135deg, #12122a 0%, #1a1a35 100%);
    border: 1px solid #2a2a4a;
    border-radius: 16px;
    padding: 22px 24px;
    margin-bottom: 16px;
    transition: border-color 0.2s, box-shadow 0.2s;
    cursor: pointer;
}
.agent-card:hover {
    border-color: #5b5bde;
    box-shadow: 0 0 20px rgba(91,91,222,0.15);
}
.agent-card.active { border-color: #5b5bde; box-shadow: 0 0 20px rgba(91,91,222,0.2); }

/* status pill */
.pill {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 99px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: .5px;
}
.pill-green  { background: #0d2b1a; color: #3ddc84; border: 1px solid #1e5c38; }
.pill-yellow { background: #2b250d; color: #ffc107; border: 1px solid #5c4e1e; }
.pill-red    { background: #2b0d0d; color: #ff5252; border: 1px solid #5c1e1e; }
.pill-blue   { background: #0d1a2b; color: #4db6ff; border: 1px solid #1e3a5c; }

/* chat bubbles */
.bubble-user {
    background: linear-gradient(135deg,#5b5bde,#7c5bd4);
    color: #fff;
    border-radius: 18px 18px 4px 18px;
    padding: 12px 18px;
    margin: 8px 0 8px 60px;
    font-size: 14px;
    line-height: 1.6;
}
.bubble-ai {
    background: #1a1a35;
    border: 1px solid #2a2a4a;
    color: #d0d0f0;
    border-radius: 18px 18px 18px 4px;
    padding: 12px 18px;
    margin: 8px 60px 8px 0;
    font-size: 14px;
    line-height: 1.6;
}
.bubble-tool {
    background: #0f2a1a;
    border: 1px solid #1e5c38;
    color: #3ddc84;
    border-radius: 10px;
    padding: 8px 14px;
    margin: 4px 60px 4px 0;
    font-size: 12px;
    font-family: monospace;
}

/* inputs */
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb] {
    background: #12122a !important;
    border: 1px solid #2a2a4a !important;
    color: #e0e0f8 !important;
    border-radius: 10px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #5b5bde !important;
    box-shadow: 0 0 0 2px rgba(91,91,222,.2) !important;
}

/* buttons */
.stButton > button {
    background: linear-gradient(135deg,#5b5bde,#7c5bd4) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    padding: 8px 20px !important;
    transition: opacity .2s !important;
}
.stButton > button:hover { opacity: .85 !important; }
.stButton > button[kind="secondary"] {
    background: #1a1a35 !important;
    border: 1px solid #2a2a4a !important;
}

/* headings */
h1,h2,h3,h4 { color: #e0e0f8 !important; }
p, label, .stMarkdown { color: #9090b8 !important; }

/* section headers */
.section-title {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #5b5bde !important;
    margin: 24px 0 10px;
}

/* pipeline node */
.pipe-node {
    background: #12122a;
    border: 1px solid #2a2a4a;
    border-radius: 12px;
    padding: 14px 18px;
    text-align: center;
    color: #d0d0f0;
    font-size: 13px;
    font-weight: 500;
    position: relative;
}
.pipe-arrow {
    text-align: center;
    color: #5b5bde;
    font-size: 22px;
    margin: 2px 0;
}

/* expander */
details summary { color: #c0c0e0 !important; }

/* divider */
hr { border-color: #1e1e3a !important; }
</style>
""", unsafe_allow_html=True)

# ── Session defaults ──────────────────────────────────────────────────────────
defaults = {
    "page": "dashboard",
    "api_keys": {},
    "agent_configs": {},
    "pipelines": [],
    "chat_histories": {},
    "active_agent": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Sidebar nav ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:16px 0 24px'>
      <div style='font-size:28px'>🤖</div>
      <div style='font-size:18px;font-weight:700;color:#e0e0f8;margin-top:4px'>AgentOS</div>
      <div style='font-size:11px;color:#5b5bde;letter-spacing:1px'>MULTI-AGENT PLATFORM</div>
    </div>
    """, unsafe_allow_html=True)

    pages = {
        "dashboard":   ("🏠", "Dashboard"),
        "agents":      ("🤖", "Agents"),
        "pipelines":   ("🔗", "Pipelines"),
        "api_config":  ("🔑", "API Config"),
        "logs":        ("📋", "Logs"),
        "settings":    ("⚙️", "Settings"),
    }

    for pid, (icon, label) in pages.items():
        active = st.session_state.page == pid
        btn_style = "primary" if active else "secondary"
        if st.button(f"{icon}  {label}", key=f"nav_{pid}", use_container_width=True, type=btn_style):
            st.session_state.page = pid
            st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:11px;color:#444;text-align:center'>v1.0.0 · AgentOS</div>", unsafe_allow_html=True)

# ── Page router ───────────────────────────────────────────────────────────────
page = st.session_state.page

if page == "dashboard":
    from pages import dashboard; dashboard.render()
elif page == "agents":
    from pages import agents; agents.render()
elif page == "pipelines":
    from pages import pipelines; pipelines.render()
elif page == "api_config":
    from pages import api_config; api_config.render()
elif page == "logs":
    from pages import logs; logs.render()
elif page == "settings":
    from pages import settings; settings.render()
