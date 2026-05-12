import streamlit as st

def render():
    st.markdown("## ⚙️ Settings")

    st.markdown("<div class='section-title'>Model Settings</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        model = st.selectbox("Default Model",
            ["claude-sonnet-4-20250514", "claude-opus-4-20250514", "claude-haiku-4-5-20251001"],
            index=0)
        st.session_state["default_model"] = model
    with col2:
        max_tokens = st.slider("Max Tokens per Response", 256, 4096, 2048, 256)
        st.session_state["max_tokens"] = max_tokens

    st.markdown("<div class='section-title'>Pipeline Settings</div>", unsafe_allow_html=True)
    col3, col4 = st.columns(2)
    with col3:
        st.selectbox("Default context passing", ["Full response", "Summary only", "Key points"])
    with col4:
        st.selectbox("Default failure handling", ["Stop pipeline", "Skip to next", "Retry once"])

    st.markdown("<div class='section-title'>Appearance</div>", unsafe_allow_html=True)
    st.toggle("Show tool calls in chat", value=True, key="show_tool_calls")
    st.toggle("Auto-scroll to latest message", value=True, key="auto_scroll")

    st.markdown("<div class='section-title'>Danger Zone</div>", unsafe_allow_html=True)
    col5, col6 = st.columns(2)
    with col5:
        if st.button("🗑 Clear All Chat Histories", type="secondary", use_container_width=True):
            st.session_state.chat_histories = {}
            st.success("Chat histories cleared.")
    with col6:
        if st.button("🗑 Clear All Pipelines", type="secondary", use_container_width=True):
            st.session_state.pipelines = []
            st.success("Pipelines cleared.")
