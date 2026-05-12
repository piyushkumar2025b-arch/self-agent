import streamlit as st
from utils.agent_registry import AGENTS
from utils.state import get_api_status

def render():
    st.markdown("## 🏠 Dashboard")
    st.markdown("<p>Your central hub for all agents and pipelines.</p>", unsafe_allow_html=True)

    # ── KPI row ──────────────────────────────────────────────────────────────
    api_status = get_api_status()
    connected  = sum(1 for v in api_status.values() if v)
    pipelines  = len(st.session_state.pipelines)

    c1, c2, c3, c4 = st.columns(4)
    kpi_css = ("background:linear-gradient(135deg,#12122a,#1a1a35);"
               "border:1px solid #2a2a4a;border-radius:16px;padding:20px;text-align:center;")
    c1.markdown(f"<div style='{kpi_css}'><div style='font-size:32px;font-weight:700;color:#5b5bde'>{len(AGENTS)}</div>"
                "<div style='font-size:12px;color:#7070a0;margin-top:4px'>TOTAL AGENTS</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div style='{kpi_css}'><div style='font-size:32px;font-weight:700;color:#3ddc84'>{connected}</div>"
                "<div style='font-size:12px;color:#7070a0;margin-top:4px'>APIs CONNECTED</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div style='{kpi_css}'><div style='font-size:32px;font-weight:700;color:#ffc107'>{pipelines}</div>"
                "<div style='font-size:12px;color:#7070a0;margin-top:4px'>PIPELINES</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div style='{kpi_css}'><div style='font-size:32px;font-weight:700;color:#4db6ff'>"
                f"{len(st.session_state.chat_histories)}</div>"
                "<div style='font-size:12px;color:#7070a0;margin-top:4px'>ACTIVE CHATS</div></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Agents grid ──────────────────────────────────────────────────────────
    st.markdown("<div class='section-title'>Available Agents</div>", unsafe_allow_html=True)
    cols = st.columns(3)
    for i, (aid, agent) in enumerate(AGENTS.items()):
        status     = api_status.get(agent["api_key_field"])
        pill_cls   = "pill-green" if status else "pill-yellow"
        pill_label = "Connected" if status else "Setup required"
        with cols[i % 3]:
            st.markdown(f"""
            <div class='agent-card'>
              <div style='font-size:28px;margin-bottom:8px'>{agent['icon']}</div>
              <div style='font-size:16px;font-weight:600;color:#e0e0f8'>{agent['name']}</div>
              <div style='font-size:12px;color:#7070a0;margin:4px 0 12px'>{agent['description']}</div>
              <span class='pill {pill_cls}'>{pill_label}</span>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Open Agent", key=f"open_{aid}", use_container_width=True):
                st.session_state.active_agent = aid
                st.session_state.page = "agents"
                st.rerun()

    # ── Quick pipeline ────────────────────────────────────────────────────────
    st.markdown("<div class='section-title'>Recent Pipelines</div>", unsafe_allow_html=True)
    if not st.session_state.pipelines:
        st.markdown("""
        <div style='background:#12122a;border:1px dashed #2a2a4a;border-radius:16px;
                    padding:40px;text-align:center;color:#444'>
            No pipelines yet — create one in the <strong style='color:#5b5bde'>Pipelines</strong> tab.
        </div>
        """, unsafe_allow_html=True)
    else:
        for p in st.session_state.pipelines[-3:]:
            st.markdown(f"""
            <div class='agent-card'>
              <div style='font-size:14px;font-weight:600;color:#e0e0f8'>🔗 {p['name']}</div>
              <div style='font-size:12px;color:#7070a0;margin-top:4px'>
                  {" → ".join([AGENTS[s]["name"] for s in p["steps"] if s in AGENTS])}
              </div>
            </div>""", unsafe_allow_html=True)
