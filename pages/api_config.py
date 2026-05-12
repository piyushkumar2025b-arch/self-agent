import streamlit as st
from utils.agent_registry import AGENTS

API_FIELDS = {
    "anthropic":       {"label": "Anthropic API Key",       "hint": "sk-ant-…",          "docs": "https://console.anthropic.com/"},
    "github":          {"label": "GitHub Personal Access Token", "hint": "ghp_…",         "docs": "https://github.com/settings/tokens"},
    "gmail_oauth":     {"label": "Gmail OAuth Credentials (JSON)", "hint": "Paste JSON…", "docs": "https://console.cloud.google.com/"},
    "google_calendar": {"label": "Google Calendar API Key", "hint": "AIza…",              "docs": "https://console.cloud.google.com/"},
    "google_keep":     {"label": "Google Keep Auth Token",  "hint": "master token…",      "docs": "https://pypi.org/project/gkeepapi/"},
}

def render():
    st.markdown("## 🔑 API Configuration")
    st.markdown("<p>Securely store your API keys for each integration. Keys are held in session memory only.</p>",
                unsafe_allow_html=True)

    st.warning("🔒 Keys are stored in Streamlit session state only and are not persisted to disk or any server.")

    # ── Main config form ──────────────────────────────────────────────────────
    st.markdown("<div class='section-title'>Service Keys</div>", unsafe_allow_html=True)

    with st.form("api_form"):
        for field, meta in API_FIELDS.items():
            current = st.session_state.api_keys.get(field, "")
            col1, col2 = st.columns([4, 1])
            with col1:
                val = st.text_input(
                    meta["label"],
                    value=current,
                    type="password",
                    placeholder=meta["hint"],
                    key=f"inp_{field}",
                )
            with col2:
                st.markdown(f"<br><a href='{meta['docs']}' target='_blank' "
                            "style='font-size:12px;color:#5b5bde'>📖 Docs</a>",
                            unsafe_allow_html=True)
            st.session_state.api_keys[field] = val

        submitted = st.form_submit_button("💾 Save All Keys", use_container_width=False)
        if submitted:
            st.success("✅ Keys saved to session state.")

    # ── Status table ──────────────────────────────────────────────────────────
    st.markdown("<div class='section-title'>Connection Status</div>", unsafe_allow_html=True)

    rows_html = ""
    for field, meta in API_FIELDS.items():
        val   = st.session_state.api_keys.get(field, "")
        ok    = bool(val and len(val) > 6)
        pill  = "<span class='pill pill-green'>● Connected</span>" if ok else \
                "<span class='pill pill-yellow'>⚠ Missing</span>"
        rows_html += f"""
        <tr style='border-bottom:1px solid #1e1e3a'>
          <td style='padding:10px 12px;color:#e0e0f8;font-weight:500'>{meta['label']}</td>
          <td style='padding:10px 12px;color:#555'>{"•" * min(len(val), 20) if val else "—"}</td>
          <td style='padding:10px 12px'>{pill}</td>
        </tr>"""

    st.markdown(f"""
    <table style='width:100%;border-collapse:collapse;background:#12122a;
                  border:1px solid #2a2a4a;border-radius:12px;overflow:hidden'>
      <thead>
        <tr style='background:#1a1a35'>
          <th style='padding:10px 12px;color:#7070a0;font-size:11px;text-align:left'>SERVICE</th>
          <th style='padding:10px 12px;color:#7070a0;font-size:11px;text-align:left'>KEY</th>
          <th style='padding:10px 12px;color:#7070a0;font-size:11px;text-align:left'>STATUS</th>
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>""", unsafe_allow_html=True)

    # ── Agent → key mapping ───────────────────────────────────────────────────
    st.markdown("<div class='section-title'>Agent API Requirements</div>", unsafe_allow_html=True)
    for aid, agent in AGENTS.items():
        field  = agent.get("api_key_field")
        val    = st.session_state.api_keys.get(field, "")
        ok     = bool(val and len(val) > 6)
        status = "<span class='pill pill-green'>Ready</span>" if ok else \
                 "<span class='pill pill-yellow'>Needs setup</span>"
        req    = API_FIELDS.get(field, {}).get("label", field)
        st.markdown(f"""
        <div style='display:flex;align-items:center;justify-content:space-between;
                    background:#12122a;border:1px solid #2a2a4a;border-radius:10px;
                    padding:12px 18px;margin-bottom:8px'>
          <div>
            <span style='font-size:18px'>{agent['icon']}</span>
            <strong style='color:#e0e0f8;margin-left:10px'>{agent['name']}</strong>
            <span style='color:#555;font-size:12px;margin-left:8px'>requires: {req}</span>
          </div>
          {status}
        </div>""", unsafe_allow_html=True)
