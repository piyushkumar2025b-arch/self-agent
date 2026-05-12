import streamlit as st
from datetime import datetime

def render():
    st.markdown("## 📋 Activity Logs")

    logs = st.session_state.get("logs", [])

    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("🗑 Clear Logs", use_container_width=True):
            st.session_state.logs = []
            st.rerun()

    if not logs:
        st.markdown("""
        <div style='background:#12122a;border:1px dashed #2a2a4a;border-radius:16px;
                    padding:60px;text-align:center;color:#444'>
            <div style='font-size:40px;margin-bottom:12px'>📋</div>
            No activity yet — start chatting with agents or running pipelines.
        </div>""", unsafe_allow_html=True)
        return

    st.markdown(f"<p>{len(logs)} events recorded this session</p>", unsafe_allow_html=True)

    action_colors = {
        "user_message": "#5b5bde",
        "tool_use":     "#ffc107",
        "pipeline_run": "#3ddc84",
        "error":        "#ff5252",
    }

    for i, log in enumerate(reversed(logs)):
        color = action_colors.get(log.get("action", ""), "#7070a0")
        st.markdown(f"""
        <div style='background:#12122a;border-left:3px solid {color};border-radius:0 10px 10px 0;
                    padding:12px 16px;margin-bottom:8px;border:1px solid #1e1e3a;
                    border-left:3px solid {color}'>
          <div style='display:flex;justify-content:space-between;margin-bottom:4px'>
            <span style='color:#e0e0f8;font-weight:600;font-size:13px'>
              {log.get('agent','System')}
            </span>
            <span style='color:#555;font-size:11px'>#{len(logs)-i}</span>
          </div>
          <div style='display:flex;gap:12px;align-items:center'>
            <span style='background:{color}22;color:{color};padding:2px 8px;border-radius:99px;
                         font-size:10px;font-weight:700;letter-spacing:.5px'>
              {log.get('action','').upper()}
            </span>
            <span style='color:#9090b8;font-size:13px'>{str(log.get('content',''))[:120]}</span>
          </div>
        </div>""", unsafe_allow_html=True)
