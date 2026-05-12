import streamlit as st
import anthropic
import json

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AgentOS",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS  — injected once, uses Streamlit CSS vars so theme stays consistent
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Global ── */
[data-testid="stAppViewContainer"] { background: #08081a; }
[data-testid="stSidebar"]          { background: #0c0c1e !important; border-right: 1px solid #1e1e3a; }
[data-testid="stSidebar"] *        { color: #c0c0e0; }
.block-container                   { padding: 1.5rem 2rem 2rem !important; max-width: 1200px; }

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }

/* ── Nav radio buttons → styled as nav items ── */
[data-testid="stSidebar"] .stRadio > label { display: none; }
[data-testid="stSidebar"] .stRadio > div   { gap: 4px !important; display: flex; flex-direction: column; }
[data-testid="stSidebar"] .stRadio div[role="radio"] {
    background: transparent !important;
    border: 1px solid transparent !important;
    border-radius: 10px !important;
    padding: 10px 14px !important;
    cursor: pointer;
    transition: all .15s ease;
    color: #9090c0 !important;
    font-size: 14px !important;
    font-weight: 500 !important;
}
[data-testid="stSidebar"] .stRadio div[role="radio"]:hover {
    background: #1a1a35 !important;
    border-color: #2a2a4a !important;
    color: #e0e0f8 !important;
}
[data-testid="stSidebar"] .stRadio div[aria-checked="true"] {
    background: linear-gradient(135deg,#1e1e45,#2a1a4a) !important;
    border-color: #5b5bde !important;
    color: #e0e0f8 !important;
    box-shadow: 0 0 12px rgba(91,91,222,.2);
}
/* hide the actual radio dot */
[data-testid="stSidebar"] .stRadio div[role="radio"] p { margin: 0; font-size: 14px; }
[data-testid="stSidebar"] .stRadio span[data-baseweb] { display: none !important; }

/* ── Cards ── */
.card {
    background: linear-gradient(135deg,#10102a,#181830);
    border: 1px solid #222240;
    border-radius: 14px;
    padding: 20px 22px;
    margin-bottom: 14px;
}
.card:hover { border-color: #5b5bde; }

/* ── Pills ── */
.pill { display:inline-block; padding:3px 11px; border-radius:99px; font-size:11px; font-weight:700; letter-spacing:.4px; }
.pill-green  { background:#0a2118; color:#3ddc84; border:1px solid #1a5c38; }
.pill-yellow { background:#25200a; color:#ffc107; border:1px solid #5c4a18; }
.pill-blue   { background:#0a1828; color:#4db6ff; border:1px solid #185060; }

/* ── Chat bubbles ── */
.bubble-u {
    background: linear-gradient(135deg,#4a4ace,#6a4ace);
    color:#fff; border-radius:16px 16px 4px 16px;
    padding:11px 17px; margin:8px 0 8px 80px; font-size:14px; line-height:1.65;
}
.bubble-a {
    background:#14142e; border:1px solid #222244; color:#d0d0f0;
    border-radius:16px 16px 16px 4px;
    padding:11px 17px; margin:8px 80px 8px 0; font-size:14px; line-height:1.65;
}
.bubble-t {
    background:#0a2018; border:1px solid #1a5030; color:#3ddc84;
    border-radius:8px; padding:7px 13px; margin:4px 80px 4px 0;
    font-size:12px; font-family:monospace;
}

/* ── KPI boxes ── */
.kpi { background:linear-gradient(135deg,#10102a,#181830); border:1px solid #222240;
       border-radius:14px; padding:18px; text-align:center; }
.kpi-num { font-size:36px; font-weight:800; }
.kpi-lbl { font-size:11px; color:#606080; margin-top:4px; letter-spacing:.5px; text-transform:uppercase; }

/* ── Section title ── */
.stitle { font-size:10px; font-weight:700; letter-spacing:1.5px; text-transform:uppercase;
          color:#5b5bde; margin:22px 0 8px; }

/* ── Inputs ── */
input, textarea, [data-baseweb="select"] > div {
    background: #10102a !important;
    border-color: #222244 !important;
    color: #e0e0f0 !important;
    border-radius: 9px !important;
}
input:focus, textarea:focus { border-color: #5b5bde !important; box-shadow: 0 0 0 2px rgba(91,91,222,.18) !important; }

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg,#4a4ace,#6a4ace) !important;
    color:#fff !important; border:none !important;
    border-radius:9px !important; font-weight:600 !important;
    padding:8px 18px !important;
}
.stButton > button:hover { opacity:.85 !important; }
button[kind="secondary"] { background:#14142e !important; border:1px solid #222244 !important; }

/* ── Pipeline flow ── */
.pnode { background:#10102a; border:1px solid #222240; border-radius:11px;
         padding:12px 16px; text-align:center; min-width:110px; display:inline-block; }
.parrow { color:#5b5bde; font-size:22px; display:inline-block; margin:0 6px; vertical-align:middle; }

/* ── Tabs ── */
[data-testid="stTab"] { background: transparent !important; color:#9090c0 !important; }
[data-testid="stTab"][aria-selected="true"] { color:#e0e0f8 !important; border-bottom-color:#5b5bde !important; }

/* ── Headings ── */
h1,h2,h3,h4 { color:#e8e8ff !important; }
p { color:#9090b8; }
hr { border-color:#1a1a38 !important; }

/* ── Expander ── */
summary { color:#c0c0e0 !important; }

/* ── Sidebar logo area ── */
.logo-wrap { text-align:center; padding:20px 0 28px; border-bottom:1px solid #1a1a38; margin-bottom:16px; }
.logo-wrap .logo-icon { font-size:32px; }
.logo-wrap .logo-name { font-size:17px; font-weight:700; color:#e8e8ff; margin-top:6px; }
.logo-wrap .logo-sub  { font-size:10px; color:#5b5bde; letter-spacing:1.5px; margin-top:2px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# AGENT REGISTRY
# ─────────────────────────────────────────────────────────────────────────────
AGENTS = {
    "github": {
        "name": "GitHub Agent", "icon": "🐙",
        "description": "Repos, issues, PRs, branches, code search.",
        "api_key_field": "github",
        "capabilities": [
            "List and search repositories",
            "Create / update / close issues",
            "Review and merge pull requests",
            "Browse files and commit history",
            "Create branches and releases",
        ],
        "system_prompt": (
            "You are a GitHub Agent. Help users manage GitHub repos, issues, PRs, and code. "
            "When the user asks to perform a GitHub action, explain what API calls would be made, "
            "simulate a realistic result, and format outputs clearly using markdown tables and code blocks."
        ),
    },
    "gmail": {
        "name": "Gmail Agent", "icon": "📧",
        "description": "Read, compose, send, organize Gmail.",
        "api_key_field": "gmail_oauth",
        "capabilities": [
            "Search and read emails",
            "Compose and send messages",
            "Summarize email threads",
            "Extract action items",
            "Manage labels",
        ],
        "system_prompt": (
            "You are a Gmail Agent. Help the user manage their Gmail inbox. "
            "Draft professional emails when asked, summarize threads concisely, "
            "and extract key action items. Always confirm before 'sending'."
        ),
    },
    "google_keep": {
        "name": "Keep Agent", "icon": "📝",
        "description": "Create, search, manage Google Keep notes.",
        "api_key_field": "google_keep",
        "capabilities": [
            "Create text notes and checklists",
            "Search notes by content or label",
            "Pin, archive, and label notes",
            "Complete checklist items",
        ],
        "system_prompt": (
            "You are a Google Keep Agent. Help the user manage notes and checklists. "
            "When creating notes, confirm the title, body, and labels. "
            "Format checklists with clear checkboxes. Be concise and organised."
        ),
    },
    "google_calendar": {
        "name": "Calendar Agent", "icon": "📅",
        "description": "Schedule, view, manage Google Calendar.",
        "api_key_field": "google_calendar",
        "capabilities": [
            "View upcoming schedule",
            "Create single and recurring events",
            "Schedule meetings with attendees",
            "Check availability",
            "Set reminders",
        ],
        "system_prompt": (
            "You are a Google Calendar Agent. Help the user manage their schedule. "
            "When creating events ask for: date, time, duration, attendees, location. "
            "Present schedules in a clean readable format and flag conflicts."
        ),
    },
    "api_connector": {
        "name": "API Connector", "icon": "🔌",
        "description": "Connect to any REST API, build integrations.",
        "api_key_field": "anthropic",
        "capabilities": [
            "Inspect any REST endpoint",
            "Generate Python / JS / curl code",
            "Parse and explain API responses",
            "Debug HTTP errors",
            "Build webhook handlers",
        ],
        "system_prompt": (
            "You are an API Connector expert. Help the user call any REST API. "
            "Generate complete, runnable code in Python (requests), JavaScript (fetch), or curl. "
            "Explain auth, headers, and body clearly. Debug errors with specific fixes."
        ),
    },
}

API_FIELDS = {
    "anthropic":       {"label": "Anthropic API Key",            "hint": "sk-ant-…",    "docs": "https://console.anthropic.com/"},
    "github":          {"label": "GitHub Personal Access Token", "hint": "ghp_…",        "docs": "https://github.com/settings/tokens"},
    "gmail_oauth":     {"label": "Gmail OAuth JSON",             "hint": "Paste JSON…", "docs": "https://console.cloud.google.com/"},
    "google_calendar": {"label": "Google Calendar API Key",      "hint": "AIza…",        "docs": "https://console.cloud.google.com/"},
    "google_keep":     {"label": "Google Keep Token",            "hint": "master token…","docs": "https://pypi.org/project/gkeepapi/"},
}

MODELS = [
    "claude-sonnet-4-20250514",
    "claude-opus-4-20250514",
    "claude-haiku-4-5-20251001",
]

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────────────────────────────────────
_defaults = {
    "api_keys":       {},
    "pipelines":      [],
    "chat_histories": {},
    "active_agent":   "github",
    "logs":           [],
    "model":          MODELS[0],
    "max_tokens":     2048,
    "pipeline_steps": [],
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def api_connected(field: str) -> bool:
    v = st.session_state.api_keys.get(field, "")
    return bool(v and len(v) > 6)

def add_log(agent: str, action: str, content: str):
    st.session_state.logs.append({"agent": agent, "action": action, "content": content})


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
NAV_OPTIONS = ["🏠  Dashboard", "🤖  Agents", "🔗  Pipelines", "🔑  API Config", "📋  Logs", "⚙️  Settings"]

with st.sidebar:
    st.markdown("""
    <div class='logo-wrap'>
      <div class='logo-icon'>🤖</div>
      <div class='logo-name'>AgentOS</div>
      <div class='logo-sub'>MULTI-AGENT PLATFORM</div>
    </div>
    """, unsafe_allow_html=True)

    # st.radio is ONE widget — no rerun on click, Streamlit re-renders only content
    nav = st.radio("nav", NAV_OPTIONS, label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)
    connected_count = sum(1 for a in AGENTS.values() if api_connected(a["api_key_field"]))
    st.markdown(f"""
    <div style='padding:10px 14px;background:#10102a;border:1px solid #1e1e3a;border-radius:10px;font-size:12px;'>
      <div style='color:#606080'>API Status</div>
      <div style='color:#3ddc84;font-weight:700;margin-top:4px'>{connected_count}/{len(AGENTS)} connected</div>
    </div>
    <div style='font-size:10px;color:#333;text-align:center;margin-top:20px'>AgentOS v2.0</div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
def page_dashboard():
    st.markdown("## 🏠 Dashboard")
    st.markdown("<p style='margin-top:-8px;margin-bottom:24px'>Your central hub for all agents and pipelines.</p>",
                unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    for col, num, lbl, color in [
        (c1, len(AGENTS),                            "AGENTS",    "#5b5bde"),
        (c2, connected_count,                        "CONNECTED", "#3ddc84"),
        (c3, len(st.session_state.pipelines),        "PIPELINES", "#ffc107"),
        (c4, len(st.session_state.chat_histories),   "CHATS",     "#4db6ff"),
    ]:
        col.markdown(f"""
        <div class='kpi'>
          <div class='kpi-num' style='color:{color}'>{num}</div>
          <div class='kpi-lbl'>{lbl}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div class='stitle'>Available Agents</div>", unsafe_allow_html=True)
    cols = st.columns(3)
    for i, (aid, agent) in enumerate(AGENTS.items()):
        ok = api_connected(agent["api_key_field"])
        pill = f"<span class='pill pill-green'>● Connected</span>" if ok else \
               f"<span class='pill pill-yellow'>⚠ Setup needed</span>"
        with cols[i % 3]:
            st.markdown(f"""
            <div class='card'>
              <div style='font-size:28px'>{agent['icon']}</div>
              <div style='font-size:15px;font-weight:600;color:#e8e8ff;margin:6px 0 4px'>{agent['name']}</div>
              <div style='font-size:12px;color:#606080;margin-bottom:10px'>{agent['description']}</div>
              {pill}
            </div>""", unsafe_allow_html=True)

    st.markdown("<div class='stitle'>Recent Pipelines</div>", unsafe_allow_html=True)
    pipes = st.session_state.pipelines
    if not pipes:
        st.markdown("""
        <div style='border:1px dashed #222240;border-radius:14px;padding:36px;text-align:center;color:#303058'>
            No pipelines yet — build one in the Pipelines tab.
        </div>""", unsafe_allow_html=True)
    else:
        for p in pipes[-3:]:
            names = " → ".join(AGENTS[s]["name"] for s in p["steps"] if s in AGENTS)
            st.markdown(f"""
            <div class='card'>
              <div style='font-size:14px;font-weight:600;color:#e8e8ff'>🔗 {p['name']}</div>
              <div style='font-size:12px;color:#606080;margin-top:4px'>{names}</div>
            </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: AGENTS
# ─────────────────────────────────────────────────────────────────────────────
def page_agents():
    st.markdown("## 🤖 Agents")

    left, right = st.columns([1, 3], gap="medium")

    with left:
        st.markdown("<div class='stitle'>Select Agent</div>", unsafe_allow_html=True)
        for aid, agent in AGENTS.items():
            ok  = api_connected(agent["api_key_field"])
            dot = "🟢" if ok else "🟡"
            is_active = st.session_state.active_agent == aid
            if st.button(
                f"{agent['icon']} {agent['name']} {dot}",
                key=f"agbtn_{aid}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state.active_agent = aid

    with right:
        aid   = st.session_state.active_agent
        agent = AGENTS[aid]
        ok    = api_connected(agent["api_key_field"])

        # Header card
        pill_html = f"<span class='pill pill-green'>● Connected</span>" if ok else \
                    f"<span class='pill pill-yellow'>⚠ Setup needed</span>"
        st.markdown(f"""
        <div class='card' style='display:flex;align-items:center;gap:16px'>
          <div style='font-size:36px'>{agent['icon']}</div>
          <div style='flex:1'>
            <div style='font-size:17px;font-weight:700;color:#e8e8ff'>{agent['name']}</div>
            <div style='font-size:12px;color:#606080;margin-top:2px'>{agent['description']}</div>
          </div>
          <div>{pill_html}</div>
        </div>""", unsafe_allow_html=True)

        if not ok and aid != "api_connector":
            st.info(f"Add the required API key in **API Config** to enable live {agent['name']} actions.")

        with st.expander("📋 Capabilities"):
            for cap in agent["capabilities"]:
                st.markdown(f"• {cap}")

        # Chat history for this agent
        if aid not in st.session_state.chat_histories:
            st.session_state.chat_histories[aid] = []
        history = st.session_state.chat_histories[aid]

        # Render chat
        st.markdown("<div class='stitle'>Conversation</div>", unsafe_allow_html=True)

        if not history:
            st.markdown(f"""
            <div style='text-align:center;padding:36px 0;color:#303058'>
              <div style='font-size:40px'>{agent['icon']}</div>
              <div style='margin-top:10px'>Ask {agent['name']} anything…</div>
            </div>""", unsafe_allow_html=True)
        else:
            for msg in history:
                if msg["role"] == "user":
                    st.markdown(f"<div class='bubble-u'>{msg['content']}</div>", unsafe_allow_html=True)
                elif msg["role"] == "assistant":
                    st.markdown(f"<div class='bubble-a'>{msg['content']}</div>", unsafe_allow_html=True)
                elif msg["role"] == "tool":
                    st.markdown(f"<div class='bubble-t'>🔧 {msg['content']}</div>", unsafe_allow_html=True)

        # Clear
        _, clr_col = st.columns([6, 1])
        with clr_col:
            if st.button("🗑 Clear", key=f"clr_{aid}"):
                st.session_state.chat_histories[aid] = []
                st.rerun()

        # Chat input
        user_input = st.chat_input(f"Message {agent['name']}…", key=f"ci_{aid}")
        if user_input:
            _send_agent_message(aid, agent, user_input)


def _send_agent_message(aid, agent, user_input):
    history = st.session_state.chat_histories.setdefault(aid, [])
    history.append({"role": "user", "content": user_input})
    add_log(agent["name"], "user_message", user_input)

    ant_key = st.session_state.api_keys.get("anthropic", "")
    if not ant_key:
        history.append({"role": "assistant",
                        "content": "⚠️ No Anthropic API key set. Add it in **API Config**."})
        st.rerun()
        return

    try:
        client = anthropic.Anthropic(api_key=ant_key)
        msgs   = [{"role": m["role"], "content": m["content"]}
                  for m in history if m["role"] in ("user", "assistant")]

        with st.spinner(f"{agent['icon']} Thinking…"):
            resp = client.messages.create(
                model=st.session_state.model,
                max_tokens=st.session_state.max_tokens,
                system=agent["system_prompt"],
                messages=msgs,
            )

        text = "".join(b.text for b in resp.content if b.type == "text")
        history.append({"role": "assistant", "content": text or "✅ Done."})
        add_log(agent["name"], "assistant_reply", (text or "")[:100])

    except Exception as e:
        history.append({"role": "assistant", "content": f"❌ Error: {e}"})
        add_log(agent["name"], "error", str(e))

    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: PIPELINES
# ─────────────────────────────────────────────────────────────────────────────
def page_pipelines():
    st.markdown("## 🔗 Pipeline Maker")
    st.markdown("<p style='margin-bottom:20px'>Chain agents together — each step's output feeds the next.</p>",
                unsafe_allow_html=True)

    tab_build, tab_run = st.tabs(["🏗  Build", "▶  Run"])

    # ── BUILD ─────────────────────────────────────────────────────────────────
    with tab_build:
        c1, c2 = st.columns([2, 1])
        with c1:
            pipe_name = st.text_input("Pipeline name", placeholder="e.g. GitHub → Email → Calendar")
        with c2:
            pipe_desc = st.text_input("Description", placeholder="What does it do?")

        st.markdown("<div class='stitle'>Add Steps</div>", unsafe_allow_html=True)
        a_col, b_col, c_col = st.columns([2, 3, 1])
        with a_col:
            agent_choices = {aid: f"{a['icon']} {a['name']}" for aid, a in AGENTS.items()}
            new_agent = st.selectbox("Agent", list(agent_choices.keys()),
                                     format_func=lambda x: agent_choices[x], label_visibility="collapsed")
        with b_col:
            new_instr = st.text_input("Instruction for this step (optional)",
                                       placeholder="e.g. Summarise the issues…",
                                       label_visibility="collapsed")
        with c_col:
            if st.button("➕ Add", use_container_width=True):
                st.session_state.pipeline_steps.append({"agent": new_agent, "instruction": new_instr})
                st.rerun()

        steps = st.session_state.pipeline_steps
        if not steps:
            st.markdown("""
            <div style='border:1px dashed #222240;border-radius:14px;padding:36px;
                        text-align:center;color:#303058;margin:12px 0'>
                Add agents above to build your pipeline ↑
            </div>""", unsafe_allow_html=True)
        else:
            # Flow visualisation
            flow = ""
            for i, step in enumerate(steps):
                a = AGENTS.get(step["agent"], {})
                instr_txt = f"<div style='font-size:10px;color:#5b5bde;margin-top:3px'>{step['instruction'][:28]}…</div>" \
                            if step["instruction"] else ""
                flow += f"<div class='pnode'><div style='font-size:22px'>{a.get('icon','?')}</div>" \
                        f"<div style='font-size:11px;color:#d0d0f0;margin-top:3px'>{a.get('name','?')}</div>" \
                        f"{instr_txt}</div>"
                if i < len(steps) - 1:
                    flow += "<span class='parrow'>→</span>"
            st.markdown(f"<div style='margin:16px 0;display:flex;align-items:center;flex-wrap:wrap;gap:4px'>{flow}</div>",
                        unsafe_allow_html=True)

            st.markdown("<div class='stitle'>Manage Steps</div>", unsafe_allow_html=True)
            for i, step in enumerate(steps):
                a = AGENTS.get(step["agent"], {})
                sc1, sc2, sc3, sc4 = st.columns([2, 4, 1, 1])
                with sc1:
                    st.markdown(f"**{i+1}. {a.get('icon','')} {a.get('name','?')}**")
                with sc2:
                    steps[i]["instruction"] = st.text_input(
                        "instr", value=step["instruction"],
                        key=f"si_{i}", label_visibility="collapsed", placeholder="Instruction…")
                with sc3:
                    if i > 0 and st.button("⬆", key=f"up_{i}"):
                        steps[i], steps[i-1] = steps[i-1], steps[i]
                        st.rerun()
                with sc4:
                    if st.button("🗑", key=f"rm_{i}"):
                        steps.pop(i)
                        st.rerun()
            st.session_state.pipeline_steps = steps

        _, sv_col = st.columns([4, 1])
        with sv_col:
            if st.button("💾 Save Pipeline", type="primary", use_container_width=True):
                if not pipe_name:
                    st.error("Give it a name.")
                elif not steps:
                    st.error("Add at least one step.")
                else:
                    st.session_state.pipelines.append({
                        "name": pipe_name, "description": pipe_desc,
                        "steps": [s["agent"] for s in steps],
                        "instructions": [s["instruction"] for s in steps],
                    })
                    st.session_state.pipeline_steps = []
                    st.success(f"✅ Pipeline **{pipe_name}** saved!")
                    st.rerun()

    # ── RUN ──────────────────────────────────────────────────────────────────
    with tab_run:
        pipes = st.session_state.pipelines
        if not pipes:
            st.info("No pipelines saved yet. Build one in the Build tab.")
            return

        selected_name = st.selectbox("Select pipeline", [p["name"] for p in pipes])
        pipeline = next(p for p in pipes if p["name"] == selected_name)

        # Show flow
        flow2 = ""
        for i, aid in enumerate(pipeline["steps"]):
            a = AGENTS.get(aid, {})
            flow2 += f"<div class='pnode'><div style='font-size:20px'>{a.get('icon','?')}</div>" \
                     f"<div style='font-size:11px;color:#d0d0f0;margin-top:2px'>{a.get('name','?')}</div></div>"
            if i < len(pipeline["steps"]) - 1:
                flow2 += "<span class='parrow'>→</span>"
        st.markdown(f"<div style='margin:12px 0 20px;display:flex;align-items:center;flex-wrap:wrap;gap:4px'>{flow2}</div>",
                    unsafe_allow_html=True)

        initial = st.text_area("Initial input / prompt", height=110,
                                placeholder="What should the first agent work on?")

        if st.button("▶  Run Pipeline", type="primary"):
            if not initial:
                st.error("Provide an input.")
                return
            ant_key = st.session_state.api_keys.get("anthropic", "")
            if not ant_key:
                st.error("Add your Anthropic API key in API Config first.")
                return

            client  = anthropic.Anthropic(api_key=ant_key)
            context = initial
            results = []
            prog    = st.progress(0)

            for idx, aid in enumerate(pipeline["steps"]):
                agent  = AGENTS.get(aid, {})
                instr  = pipeline["instructions"][idx] if idx < len(pipeline["instructions"]) else ""
                prompt = f"{instr}\n\n{context}" if instr else context

                with st.spinner(f"Step {idx+1}/{len(pipeline['steps'])}: {agent.get('name')}…"):
                    try:
                        r = client.messages.create(
                            model=st.session_state.model,
                            max_tokens=st.session_state.max_tokens,
                            system=agent.get("system_prompt", "You are a helpful assistant."),
                            messages=[{"role": "user", "content": prompt}],
                        )
                        out = "".join(b.text for b in r.content if b.type == "text")
                        context = out
                        results.append({"step": idx+1, "agent": agent.get("name"), "output": out, "ok": True})
                    except Exception as e:
                        results.append({"step": idx+1, "agent": agent.get("name"), "output": str(e), "ok": False})
                        context = f"[Error: {e}]"

                prog.progress((idx+1) / len(pipeline["steps"]))

            add_log(f"Pipeline:{selected_name}", "pipeline_run", f"{len(results)} steps")

            st.markdown("---")
            st.markdown("<div class='stitle'>Results</div>", unsafe_allow_html=True)
            for r in results:
                icon = "✅" if r["ok"] else "❌"
                with st.expander(f"{icon} Step {r['step']}: {r['agent']}", expanded=(r is results[-1])):
                    st.markdown(f"<div class='bubble-a'>{r['output']}</div>", unsafe_allow_html=True)
            st.success("Pipeline complete!")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: API CONFIG
# ─────────────────────────────────────────────────────────────────────────────
def page_api_config():
    st.markdown("## 🔑 API Configuration")
    st.markdown("<p style='margin-bottom:16px'>Keys live in session memory only — never written to disk.</p>",
                unsafe_allow_html=True)
    st.info("🔒 Keys are cleared when you close the browser tab.")

    st.markdown("<div class='stitle'>Enter Keys</div>", unsafe_allow_html=True)

    # Use individual text_inputs (NOT a form) so values save immediately without a submit button lag
    changed = False
    for field, meta in API_FIELDS.items():
        col_i, col_d = st.columns([5, 1])
        with col_i:
            new_val = st.text_input(
                meta["label"],
                value=st.session_state.api_keys.get(field, ""),
                type="password",
                placeholder=meta["hint"],
                key=f"apik_{field}",
            )
            if new_val != st.session_state.api_keys.get(field, ""):
                st.session_state.api_keys[field] = new_val
                changed = True
        with col_d:
            st.markdown(f"<div style='padding-top:28px'><a href='{meta['docs']}' target='_blank' "
                        "style='color:#5b5bde;font-size:12px'>📖 Docs</a></div>", unsafe_allow_html=True)

    if changed:
        st.success("✅ Key updated.")

    st.markdown("<div class='stitle'>Connection Status</div>", unsafe_allow_html=True)
    rows = ""
    for field, meta in API_FIELDS.items():
        val = st.session_state.api_keys.get(field, "")
        ok  = bool(val and len(val) > 6)
        status_pill = "<span class='pill pill-green'>● OK</span>" if ok else \
                      "<span class='pill pill-yellow'>⚠ Missing</span>"
        masked = ("•" * min(len(val), 24)) if val else "—"
        rows += f"""<tr style='border-bottom:1px solid #1a1a38'>
          <td style='padding:10px 12px;color:#e0e0f0;font-size:13px'>{meta['label']}</td>
          <td style='padding:10px 12px;color:#404060;font-size:12px;font-family:monospace'>{masked}</td>
          <td style='padding:10px 12px'>{status_pill}</td>
        </tr>"""

    st.markdown(f"""
    <table style='width:100%;border-collapse:collapse;background:#10102a;border:1px solid #1e1e3a;border-radius:12px;overflow:hidden'>
      <thead>
        <tr style='background:#14143a'>
          <th style='padding:10px 12px;color:#505080;font-size:10px;text-align:left;letter-spacing:.5px'>SERVICE</th>
          <th style='padding:10px 12px;color:#505080;font-size:10px;text-align:left;letter-spacing:.5px'>KEY</th>
          <th style='padding:10px 12px;color:#505080;font-size:10px;text-align:left;letter-spacing:.5px'>STATUS</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>""", unsafe_allow_html=True)

    st.markdown("<div class='stitle'>Agent Requirements</div>", unsafe_allow_html=True)
    for aid, agent in AGENTS.items():
        field = agent["api_key_field"]
        ok    = api_connected(field)
        lbl   = API_FIELDS.get(field, {}).get("label", field)
        badge = "<span class='pill pill-green'>Ready</span>" if ok else \
                "<span class='pill pill-yellow'>Needs key</span>"
        st.markdown(f"""
        <div style='display:flex;align-items:center;justify-content:space-between;
                    background:#10102a;border:1px solid #1e1e3a;border-radius:10px;
                    padding:12px 16px;margin-bottom:8px'>
          <div>
            <span style='font-size:18px'>{agent['icon']}</span>
            <strong style='color:#e0e0f0;margin-left:10px;font-size:13px'>{agent['name']}</strong>
            <span style='color:#404060;font-size:12px;margin-left:8px'>→ {lbl}</span>
          </div>
          {badge}
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: LOGS
# ─────────────────────────────────────────────────────────────────────────────
def page_logs():
    st.markdown("## 📋 Activity Logs")
    logs = st.session_state.logs

    hc, bc = st.columns([5, 1])
    with hc:
        st.markdown(f"<p>{len(logs)} events this session</p>", unsafe_allow_html=True)
    with bc:
        if st.button("🗑 Clear", use_container_width=True):
            st.session_state.logs = []
            st.rerun()

    if not logs:
        st.markdown("""
        <div style='border:1px dashed #222240;border-radius:14px;padding:48px;text-align:center;color:#303058'>
            No activity yet.
        </div>""", unsafe_allow_html=True)
        return

    ACTION_COLORS = {
        "user_message":   "#5b5bde",
        "assistant_reply":"#3ddc84",
        "tool_use":       "#ffc107",
        "pipeline_run":   "#4db6ff",
        "error":          "#ff5252",
    }
    for i, log in enumerate(reversed(logs)):
        color = ACTION_COLORS.get(log.get("action", ""), "#606080")
        num   = len(logs) - i
        st.markdown(f"""
        <div style='background:#10102a;border-left:3px solid {color};border:1px solid #1a1a38;
                    border-left-width:3px;border-left-color:{color};border-radius:0 10px 10px 0;
                    padding:11px 16px;margin-bottom:7px'>
          <div style='display:flex;justify-content:space-between'>
            <span style='color:#e0e0f0;font-weight:600;font-size:13px'>{log.get('agent','System')}</span>
            <span style='color:#303050;font-size:11px'>#{num}</span>
          </div>
          <div style='margin-top:5px;display:flex;align-items:center;gap:10px'>
            <span style='background:{color}22;color:{color};padding:2px 9px;border-radius:99px;
                         font-size:10px;font-weight:700;letter-spacing:.5px'>
              {log.get('action','').upper()}
            </span>
            <span style='color:#7070a0;font-size:12px'>{str(log.get('content',''))[:120]}</span>
          </div>
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: SETTINGS
# ─────────────────────────────────────────────────────────────────────────────
def page_settings():
    st.markdown("## ⚙️ Settings")

    st.markdown("<div class='stitle'>Model</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        # Find current index safely
        current_model = st.session_state.get("model", MODELS[0])
        idx = MODELS.index(current_model) if current_model in MODELS else 0
        chosen = st.selectbox("Model", MODELS, index=idx, key="model_select")
        st.session_state.model = chosen
    with c2:
        st.session_state.max_tokens = st.slider(
            "Max tokens per response", 256, 4096,
            st.session_state.max_tokens, 256)

    st.markdown("<div class='stitle'>Danger Zone</div>", unsafe_allow_html=True)
    dc1, dc2, dc3 = st.columns(3)
    with dc1:
        if st.button("🗑 Clear All Chats", use_container_width=True):
            st.session_state.chat_histories = {}
            st.success("Chats cleared.")
    with dc2:
        if st.button("🗑 Clear Pipelines", use_container_width=True):
            st.session_state.pipelines = []
            st.success("Pipelines cleared.")
    with dc3:
        if st.button("🗑 Clear Logs", use_container_width=True):
            st.session_state.logs = []
            st.success("Logs cleared.")

    st.markdown("<div class='stitle'>About</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='card'>
      <div style='font-size:15px;font-weight:600;color:#e8e8ff;margin-bottom:6px'>AgentOS v2.0</div>
      <div style='font-size:13px;color:#606080'>Multi-agent platform powered by Claude.</div>
      <div style='font-size:13px;color:#606080;margin-top:4px'>Agents: GitHub · Gmail · Keep · Calendar · API Connector</div>
    </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# ROUTER  — pure if/elif on the radio value, no rerun needed
# ─────────────────────────────────────────────────────────────────────────────
if   "Dashboard" in nav: page_dashboard()
elif "Agents"    in nav: page_agents()
elif "Pipelines" in nav: page_pipelines()
elif "API Config" in nav: page_api_config()
elif "Logs"      in nav: page_logs()
elif "Settings"  in nav: page_settings()
