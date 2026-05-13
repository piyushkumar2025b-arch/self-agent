"""
pages/web_wiki.py
Wikipedia + Web Search + Realtime Data page.
"""
import streamlit as st
from utils.web_search_utils import (
    wikipedia_search, wikipedia_get_full_article,
    ddg_search, ddg_news, ddg_images,
    fetch_news, get_exchange_rates, get_crypto_prices, get_ip_info,
    get_search_usage, init_search_state,
)


def render():
    st.markdown("## 🌐 Web Search & Wikipedia")
    st.markdown(
        "<p style='font-size:13px;margin-bottom:16px'>Wikipedia lookup, web search via DuckDuckGo, "
        "live crypto prices & exchange rates. Free — no API keys required.</p>",
        unsafe_allow_html=True,
    )
    init_search_state()
    usage = get_search_usage()

    # Usage strip
    st.markdown(f"""
    <div style='background:#0b0b1e;border:1px solid #181838;border-radius:10px;
                padding:10px 16px;margin-bottom:16px;font-size:11px'>
      <div style='display:flex;gap:20px;flex-wrap:wrap;color:#505080'>
        <span>📖 Wikipedia: <b style='color:#a0a0cc'>{usage["wikipedia"]["calls"]}</b> calls</span>
        <span>🔍 Web search: <b style='color:#a0a0cc'>{usage["ddg"]["calls"]}</b> calls</span>
        <span>📰 News: <b style='color:#a0a0cc'>{usage["news"]["calls"]}</b> calls</span>
        <span style='color:#26c96e'>● All free · No keys needed</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    tab_wiki, tab_search, tab_news, tab_realtime, tab_images = st.tabs([
        "📖 Wikipedia", "🔍 Web Search", "📰 News", "📊 Realtime Data", "🖼️ Image Search"
    ])

    # ── WIKIPEDIA ────────────────────────────────────────────────────────────
    with tab_wiki:
        col1, col2 = st.columns([4, 1])
        with col1:
            wiki_q = st.text_input("Search Wikipedia", placeholder="e.g. Quantum computing", key="wiki_q")
        with col2:
            wiki_lang = st.selectbox("Language", ["en", "hi", "es", "fr", "de", "ja", "zh", "ar", "pt"],
                                      key="wiki_lang")

        if st.button("🔍 Search Wikipedia", type="primary", key="wiki_btn") and wiki_q:
            with st.spinner("Searching Wikipedia..."):
                result = wikipedia_search(wiki_q, language=wiki_lang)

            if result["error"]:
                st.error(f"❌ {result['error']}")
            else:
                # Header card
                st.markdown(f"""
                <div style='background:#0b0b1e;border:1px solid #181838;border-radius:12px;
                            padding:16px;margin-bottom:12px'>
                  <div style='font-size:16px;font-weight:700;color:#e0e0ff;margin-bottom:4px'>
                    {result['title']}
                  </div>
                  {f'<div style="font-size:11px;color:#505080;margin-bottom:10px">{result.get("description","")}</div>' if result.get("description") else ""}
                  <div style='font-size:13px;color:#9090c0;line-height:1.7'>{result['summary'][:800]}{"..." if len(result["summary"])>800 else ""}</div>
                  <div style='margin-top:10px'>
                    <a href='{result["url"]}' target='_blank' style='color:#4444cc;font-size:11px'>
                      📖 Read full article on Wikipedia →
                    </a>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                if result.get("image"):
                    try:
                        st.image(result["image"], width=200, caption=result["title"])
                    except Exception:
                        pass

                # Related results
                if result.get("all_results") and len(result["all_results"]) > 1:
                    st.markdown("**Related articles:**")
                    for r in result["all_results"][1:5]:
                        import html
                        snippet = html.unescape(r.get("snippet", "")).replace("<span class=\"searchmatch\">", "**").replace("</span>", "**")
                        st.markdown(f"- **{r['title']}** — {snippet[:100]}")

                # Full article toggle
                with st.expander("📄 Load full article"):
                    with st.spinner("Loading full content..."):
                        full = wikipedia_get_full_article(result["title"], wiki_lang)
                    if full["content"]:
                        st.text_area("Full article", full["content"][:20000], height=400)

    # ── WEB SEARCH ───────────────────────────────────────────────────────────
    with tab_search:
        col1, col2 = st.columns([4, 1])
        with col1:
            web_q = st.text_input("Web search (DuckDuckGo)", placeholder="e.g. latest AI news 2025",
                                   key="web_q")
        with col2:
            web_n = st.slider("Results", 3, 15, 8, key="web_n")

        if st.button("🔍 Search Web", type="primary", key="web_btn") and web_q:
            with st.spinner("Searching the web..."):
                result = ddg_search(web_q, max_results=web_n)

            if result["error"]:
                st.error(f"❌ {result['error']}")
            elif not result["results"]:
                st.warning("No results found.")
            else:
                st.success(f"Found {len(result['results'])} results")
                for i, r in enumerate(result["results"], 1):
                    domain = r["url"].split("/")[2] if "/" in r["url"] else r["url"]
                    st.markdown(f"""
                    <div style='background:#0b0b1e;border:1px solid #181838;border-radius:10px;
                                padding:10px 14px;margin-bottom:8px'>
                      <div style='font-size:13px;font-weight:600;color:#e0e0ff;margin-bottom:3px'>
                        {i}. <a href='{r["url"]}' target='_blank' style='color:#d0d0f0;text-decoration:none'>{r["title"]}</a>
                      </div>
                      <div style='font-size:10px;color:#26c96e;margin-bottom:4px'>{domain}</div>
                      <div style='font-size:11px;color:#505080'>{r["snippet"][:200]}</div>
                    </div>
                    """, unsafe_allow_html=True)

                # Send to AI
                if st.button("🧠 Summarize with AI", key="web_ai_sum"):
                    context = "\n\n".join(f"**{r['title']}**\n{r['snippet']}" for r in result["results"])
                    prompt = f"Summarize these web search results for '{web_q}':\n\n{context}"
                    if "chat_histories" not in st.session_state:
                        st.session_state.chat_histories = {}
                    st.session_state.chat_histories.setdefault("web_search", []).append(
                        {"role": "user", "content": prompt}
                    )
                    st.success("✅ Sent to Web Search Agent! Go to Agents → Web Search.")

    # ── NEWS ─────────────────────────────────────────────────────────────────
    with tab_news:
        news_q = st.text_input("News search", placeholder="e.g. artificial intelligence", key="news_q")
        newsapi_key = st.session_state.get("api_keys", {}).get("newsapi", "")
        if newsapi_key:
            st.caption("✅ Using NewsAPI (more results)")
        else:
            st.caption("ℹ️ Using DuckDuckGo news (free, no key needed)")

        if st.button("📰 Get News", type="primary", key="news_btn") and news_q:
            with st.spinner("Fetching news..."):
                result = fetch_news(news_q, api_key=newsapi_key if newsapi_key else None)

            if result.get("error"):
                st.error(f"❌ {result['error']}")
            else:
                articles = result.get("results", [])
                if not articles:
                    st.warning("No news articles found.")
                else:
                    st.success(f"Found {len(articles)} articles")
                    for art in articles:
                        date_str = art.get("date", "")[:10] if art.get("date") else ""
                        source_str = art.get("source", "")
                        st.markdown(f"""
                        <div style='background:#0b0b1e;border:1px solid #181838;border-radius:10px;
                                    padding:10px 14px;margin-bottom:8px;display:flex;gap:10px'>
                          <div style='flex:1'>
                            <div style='font-size:13px;font-weight:600;color:#e0e0ff;margin-bottom:3px'>
                              <a href='{art["url"]}' target='_blank' style='color:#d0d0f0;text-decoration:none'>{art["title"]}</a>
                            </div>
                            <div style='font-size:9px;color:#38aaee;margin-bottom:4px'>
                              {source_str} {f'· {date_str}' if date_str else ''}
                            </div>
                            <div style='font-size:11px;color:#505080'>{art.get("snippet","")[:180]}</div>
                          </div>
                        </div>
                        """, unsafe_allow_html=True)

    # ── REALTIME DATA ────────────────────────────────────────────────────────
    with tab_realtime:
        rt_tab1, rt_tab2, rt_tab3 = st.tabs(["💱 Exchange Rates", "🪙 Crypto", "🌍 IP Lookup"])

        with rt_tab1:
            base_currency = st.selectbox("Base currency", ["USD", "EUR", "GBP", "JPY", "INR", "AUD", "CAD"],
                                          key="fx_base")
            if st.button("💱 Get Rates", key="fx_btn"):
                with st.spinner("Fetching exchange rates..."):
                    result = get_exchange_rates(base_currency)
                if result["error"]:
                    st.error(result["error"])
                else:
                    st.caption(f"Updated: {result.get('time_last_update', 'N/A')}")
                    major = ["USD", "EUR", "GBP", "JPY", "INR", "AUD", "CAD", "CHF", "CNY", "BRL", "MXN", "KRW"]
                    rates = result["rates"]
                    cols = st.columns(4)
                    for i, cur in enumerate([c for c in major if c in rates]):
                        cols[i % 4].metric(cur, f"{rates[cur]:.4f}")
                    with st.expander("All currencies"):
                        st.json(rates)

        with rt_tab2:
            coins_input = st.multiselect(
                "Select coins",
                ["bitcoin", "ethereum", "dogecoin", "solana", "cardano", "ripple", "litecoin",
                 "binancecoin", "polkadot", "shiba-inu", "avalanche-2", "chainlink"],
                default=["bitcoin", "ethereum", "dogecoin"],
                key="crypto_coins",
            )
            if st.button("🪙 Get Prices", key="crypto_btn"):
                with st.spinner("Fetching crypto prices..."):
                    result = get_crypto_prices(coins_input)
                if result["error"]:
                    st.error(result["error"])
                else:
                    prices = result["prices"]
                    for coin, data in prices.items():
                        change = data.get("usd_24h_change", 0)
                        change_color = "#26c96e" if change >= 0 else "#ff4444"
                        st.markdown(f"""
                        <div style='background:#0b0b1e;border:1px solid #181838;border-radius:8px;
                                    padding:10px 14px;margin-bottom:6px;display:flex;justify-content:space-between'>
                          <span style='color:#d0d0f0;font-weight:600;text-transform:capitalize'>{coin}</span>
                          <span style='color:#a0a0cc'>${data.get("usd", 0):,.2f}</span>
                          <span style='color:{change_color}'>{change:+.2f}%</span>
                        </div>
                        """, unsafe_allow_html=True)

        with rt_tab3:
            ip_input = st.text_input("IP address (leave blank for your IP)", key="ip_input",
                                      placeholder="8.8.8.8")
            if st.button("🌍 Lookup", key="ip_btn"):
                with st.spinner("Looking up IP..."):
                    data = get_ip_info(ip_input.strip())
                if data.get("error"):
                    st.error(data["error"])
                else:
                    cols = st.columns(3)
                    cols[0].metric("IP", data.get("ip", "N/A"))
                    cols[1].metric("Country", data.get("country_name", "N/A"))
                    cols[2].metric("City", data.get("city", "N/A"))
                    st.json({k: v for k, v in data.items()
                             if k not in ("error",) and isinstance(v, (str, int, float))})

    # ── IMAGES ────────────────────────────────────────────────────────────────
    with tab_images:
        img_q = st.text_input("Image search (DuckDuckGo)", placeholder="e.g. mountain landscape",
                               key="img_q")
        img_n = st.slider("Number of images", 3, 12, 6, key="img_n")
        if st.button("🖼️ Search Images", type="primary", key="img_btn") and img_q:
            with st.spinner("Searching images..."):
                from utils.web_search_utils import ddg_images
                result = ddg_images(img_q, img_n)
            if result["error"]:
                st.error(result["error"])
            else:
                images = result["results"]
                if not images:
                    st.warning("No images found.")
                else:
                    cols = st.columns(3)
                    for i, img in enumerate(images):
                        with cols[i % 3]:
                            try:
                                st.image(img["thumbnail"] or img["image_url"],
                                         caption=img["title"][:40], use_container_width=True)
                                st.markdown(f"<div style='text-align:center;font-size:9px'>"
                                            f"<a href='{img['source_url']}' target='_blank' style='color:#4444cc'>"
                                            f"Source</a></div>", unsafe_allow_html=True)
                            except Exception:
                                st.markdown(f"<a href='{img['image_url']}' target='_blank' "
                                            f"style='color:#4444cc'>{img['title'][:30]}</a>",
                                            unsafe_allow_html=True)