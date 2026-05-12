import streamlit as st
import anthropic
import json
from utils.agent_registry import AGENTS
from utils.state import get_api_status
from utils.tools import get_tools_for_agent

def render():
    st.markdown("## 🤖 Agents")

    api_status = get_api_status()

    # ── Sidebar agent selector ────────────────────────────────────────────────
    left, right = st.columns([1, 3])

    with left:
        st.markdown("<div class='section-title'>Select Agent</div>", unsafe_allow_html=True)
        for aid, agent in AGENTS.items():
            status   = api_status.get(agent["api_key_field"])
            dot      = "🟢" if status else "🟡"
            active   = st.session_state.active_agent == aid
            btn_type = "primary" if active else "secondary"
            if st.button(f"{agent['icon']} {agent['name']} {dot}", key=f"sel_{aid}",
                         use_container_width=True, type=btn_type):
                st.session_state.active_agent = aid
                st.rerun()

    with right:
        aid = st.session_state.active_agent
        if not aid:
            st.markdown("""
            <div style='height:400px;display:flex;align-items:center;justify-content:center;
                        background:#12122a;border:1px dashed #2a2a4a;border-radius:16px'>
                <div style='text-align:center;color:#444'>
                    <div style='font-size:48px'>👈</div>
                    <div style='margin-top:12px'>Select an agent to start chatting</div>
                </div>
            </div>""", unsafe_allow_html=True)
            return

        agent = AGENTS[aid]
        api_ok = api_status.get(agent["api_key_field"])

        # Header
        st.markdown(f"""
        <div style='background:linear-gradient(135deg,#12122a,#1a1a35);border:1px solid #2a2a4a;
                    border-radius:16px;padding:20px 24px;margin-bottom:16px;
                    display:flex;align-items:center;gap:16px'>
          <div style='font-size:36px'>{agent['icon']}</div>
          <div>
            <div style='font-size:18px;font-weight:700;color:#e0e0f8'>{agent['name']}</div>
            <div style='font-size:12px;color:#7070a0;margin-top:2px'>{agent['description']}</div>
          </div>
          <div style='margin-left:auto'>
            <span class='pill {"pill-green" if api_ok else "pill-yellow"}'>
              {"● Connected" if api_ok else "⚠ Setup required"}
            </span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        if not api_ok:
            st.warning(f"⚠️ {agent['name']} needs an API key. Go to **API Config** to add it.")

        # Capabilities
        with st.expander("📋 Agent Capabilities", expanded=False):
            for cap in agent.get("capabilities", []):
                st.markdown(f"• {cap}")

        # Chat history init
        if aid not in st.session_state.chat_histories:
            st.session_state.chat_histories[aid] = []

        history = st.session_state.chat_histories[aid]

        # Chat display
        st.markdown("<div class='section-title'>Conversation</div>", unsafe_allow_html=True)
        chat_container = st.container()
        with chat_container:
            if not history:
                st.markdown(f"""
                <div style='text-align:center;padding:30px;color:#444'>
                    <div style='font-size:32px;margin-bottom:8px'>{agent['icon']}</div>
                    <div>Start a conversation with {agent['name']}</div>
                </div>""", unsafe_allow_html=True)
            for msg in history:
                role = msg["role"]
                content = msg["content"] if isinstance(msg["content"], str) else str(msg["content"])
                if role == "user":
                    st.markdown(f"<div class='bubble-user'>{content}</div>", unsafe_allow_html=True)
                elif role == "assistant":
                    st.markdown(f"<div class='bubble-ai'>{content}</div>", unsafe_allow_html=True)
                elif role == "tool":
                    st.markdown(f"<div class='bubble-tool'>🔧 Tool: {content}</div>", unsafe_allow_html=True)

        # Clear button
        col_a, col_b = st.columns([5, 1])
        with col_b:
            if st.button("🗑 Clear", key=f"clear_{aid}"):
                st.session_state.chat_histories[aid] = []
                st.rerun()

        # Input
        user_input = st.chat_input(f"Ask {agent['name']} anything…", key=f"chat_{aid}")
        if user_input:
            _handle_chat(aid, agent, user_input, api_ok)


def _handle_chat(aid, agent, user_input, api_ok):
    history = st.session_state.chat_histories[aid]
    history.append({"role": "user", "content": user_input})

    # Log
    if "logs" not in st.session_state:
        st.session_state.logs = []
    st.session_state.logs.append({"agent": agent["name"], "action": "user_message", "content": user_input})

    anthropic_key = st.session_state.api_keys.get("anthropic", "")
    if not anthropic_key:
        history.append({"role": "assistant",
                        "content": "⚠️ Anthropic API key not set. Please add it in **API Config**."})
        st.session_state.chat_histories[aid] = history
        st.rerun()
        return

    try:
        client = anthropic.Anthropic(api_key=anthropic_key)
        tools  = get_tools_for_agent(aid)

        messages = [{"role": m["role"], "content": m["content"]}
                    for m in history if m["role"] in ("user", "assistant")]

        with st.spinner(f"{agent['icon']} {agent['name']} is thinking…"):
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                system=agent["system_prompt"],
                messages=messages,
                tools=tools if tools else [],
            )

        # Parse response
        assistant_text = ""
        tool_uses      = []

        for block in response.content:
            if block.type == "text":
                assistant_text += block.text
            elif block.type == "tool_use":
                tool_uses.append(block)

        if tool_uses:
            for tu in tool_uses:
                history.append({"role": "tool",
                                 "content": f"{tu.name}({json.dumps(tu.input, indent=2)})"})
                st.session_state.logs.append({
                    "agent": agent["name"], "action": "tool_use",
                    "content": f"{tu.name}: {json.dumps(tu.input)}"
                })

        if assistant_text:
            history.append({"role": "assistant", "content": assistant_text})
        elif not tool_uses:
            history.append({"role": "assistant", "content": "✅ Done."})

        st.session_state.chat_histories[aid] = history

    except Exception as e:
        history.append({"role": "assistant", "content": f"❌ Error: {str(e)}"})
        st.session_state.chat_histories[aid] = history

    st.rerun()
