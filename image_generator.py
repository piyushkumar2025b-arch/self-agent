"""
pages/image_generator.py
Image generation page with Pollinations (free, no key) + HuggingFace.
"""
import streamlit as st
from utils.image_gen import (
    generate_image, get_image_usage_stats, init_image_state,
    PROVIDERS, STYLE_PRESETS,
)
import io


def render():
    st.markdown("## 🖼️ Image Generator")
    st.markdown(
        "<p style='font-size:13px;margin-bottom:16px'>Generate images for free using Pollinations.ai "
        "(no key!) and HuggingFace Stable Diffusion. Live usage tracking included.</p>",
        unsafe_allow_html=True,
    )
    init_image_state()
    usage = get_image_usage_stats()

    # ── Usage panel ───────────────────────────────────────────────────────────
    poll_pct = min(100, int(usage["pollinations"]["today"] / PROVIDERS["pollinations"]["limit_per_day"] * 100))
    hf_pct = min(100, int(usage["huggingface"]["month"] / PROVIDERS["huggingface"]["limit_per_month"] * 100))
    hf_key = st.session_state.get("api_keys", {}).get("huggingface", "")

    st.markdown(f"""
    <div style='background:#0b0b1e;border:1px solid #181838;border-radius:10px;
                padding:12px 16px;margin-bottom:16px'>
      <div style='font-size:10px;color:#303060;margin-bottom:8px;letter-spacing:1px;text-transform:uppercase'>
        API Usage Tracker
      </div>
      <div style='display:flex;gap:24px;flex-wrap:wrap'>
        <div style='flex:1;min-width:200px'>
          <div style='font-size:11px;color:#505080;margin-bottom:4px'>
            🌸 Pollinations.ai · <span style='color:#26c96e'>FREE · No key</span>
          </div>
          <div style='font-size:10px;color:#404060;margin-bottom:3px'>
            Today: {usage["pollinations"]["today"]} / {PROVIDERS["pollinations"]["limit_per_day"]} (fair use)
            · Total: {usage["pollinations"]["total"]}
          </div>
          <div style='height:5px;background:#0e0e20;border-radius:3px;overflow:hidden'>
            <div style='width:{poll_pct}%;height:100%;background:#26c96e;border-radius:3px'></div>
          </div>
        </div>
        <div style='flex:1;min-width:200px'>
          <div style='font-size:11px;color:#505080;margin-bottom:4px'>
            🤗 HuggingFace · {'<span style="color:#26c96e">Key set ✅</span>' if hf_key else '<span style="color:#f0a020">Key needed</span>'}
          </div>
          <div style='font-size:10px;color:#404060;margin-bottom:3px'>
            Month: {usage["huggingface"]["month"]} / {PROVIDERS["huggingface"]["limit_per_month"]}
            · Total: {usage["huggingface"]["total"]}
          </div>
          <div style='height:5px;background:#0e0e20;border-radius:3px;overflow:hidden'>
            <div style='width:{hf_pct}%;height:100%;background:{"#f0a020" if hf_pct > 70 else "#4444cc"};border-radius:3px'></div>
          </div>
        </div>
      </div>
      {f'<div style="margin-top:8px;font-size:10px;color:#303060">Cache: {len(st.session_state.get("image_cache",{}))} images · Errors: {usage["errors"]}</div>' if True else ''}
    </div>
    """, unsafe_allow_html=True)

    tab_generate, tab_gallery, tab_api_info = st.tabs(["🎨 Generate", "🖼️ Gallery", "ℹ️ API Info"])

    with tab_generate:
        # Provider selection
        provider = st.radio(
            "Provider",
            ["pollinations", "huggingface"],
            format_func=lambda x: {
                "pollinations": "🌸 Pollinations.ai (FREE, no key)",
                "huggingface": "🤗 HuggingFace (free with token)",
            }[x],
            horizontal=True,
            key="imggen_provider",
        )

        col1, col2 = st.columns([3, 1])
        with col1:
            prompt = st.text_area(
                "Image prompt",
                placeholder="A majestic mountain at sunset, cinematic lighting, 4K...",
                height=100,
                key="imggen_prompt",
            )

            # Style presets
            st.markdown("<div style='font-size:10px;color:#404060;margin-bottom:4px'>Quick style presets:</div>",
                        unsafe_allow_html=True)
            preset_cols = st.columns(5)
            for i, preset in enumerate(STYLE_PRESETS[:10]):
                if preset_cols[i % 5].button(preset, key=f"preset_{i}", use_container_width=True):
                    st.session_state["imggen_prompt"] = (prompt + f", {preset}" if prompt else preset)
                    st.rerun()

        with col2:
            # Settings
            if provider == "pollinations":
                models = PROVIDERS["pollinations"]["models"]
                model = st.selectbox("Model", models, key="imggen_model_poll")
                width = st.select_slider("Width", [512, 768, 1024, 1280, 1920], value=1024, key="imggen_w")
                height = st.select_slider("Height", [512, 768, 1024, 1280, 1920], value=1024, key="imggen_h")
                use_seed = st.checkbox("Use seed", key="imggen_use_seed")
                seed = st.number_input("Seed", 0, 999999, 42, key="imggen_seed") if use_seed else None
                enhance = st.checkbox("Enhance prompt", value=True, key="imggen_enhance")
                api_key = ""
            else:
                models = PROVIDERS["huggingface"]["models"]
                model = st.selectbox("Model", models, key="imggen_model_hf",
                                      format_func=lambda x: x.split("/")[-1])
                width = st.select_slider("Width", [512, 768, 1024], value=512, key="imggen_w_hf")
                height = st.select_slider("Height", [512, 768, 1024], value=512, key="imggen_h_hf")
                seed = None
                enhance = False
                api_key = st.session_state.get("api_keys", {}).get("huggingface", "")
                if not api_key:
                    st.warning("⚠️ Enter HuggingFace key in API Config")

        negative_prompt = ""
        if provider == "huggingface":
            negative_prompt = st.text_input(
                "Negative prompt (optional)",
                placeholder="blurry, low quality, ugly, deformed...",
                key="imggen_neg",
            )

        if st.button("🎨 Generate Image", type="primary", use_container_width=True, key="imggen_btn"):
            if not prompt.strip():
                st.warning("Please enter a prompt.")
            else:
                with st.spinner(f"Generating with {PROVIDERS[provider]['name']}..."):
                    kwargs = {}
                    if provider == "pollinations":
                        kwargs = {"seed": seed, "enhance": enhance}
                    elif provider == "huggingface" and negative_prompt:
                        kwargs = {"negative_prompt": negative_prompt}

                    result = generate_image(
                        prompt, provider=provider, model=model,
                        api_key=api_key, width=width, height=height, **kwargs
                    )

                if result["error"]:
                    st.error(f"❌ {result['error']}")
                elif result["image_bytes"]:
                    # Show image
                    st.image(result["image_bytes"], caption=prompt[:80], use_container_width=True)

                    # Download + actions
                    col_dl, col_copy = st.columns(2)
                    with col_dl:
                        st.download_button(
                            "⬇ Download PNG",
                            result["image_bytes"],
                            file_name=f"generated_{provider}.png",
                            mime="image/png",
                            key="imggen_dl",
                        )

                    if result.get("cached"):
                        st.info("💾 Loaded from cache (same prompt used before)")

                    # Save to gallery
                    if "imggen_gallery" not in st.session_state:
                        st.session_state.imggen_gallery = []
                    st.session_state.imggen_gallery.insert(0, {
                        "bytes": result["image_bytes"],
                        "prompt": prompt,
                        "provider": provider,
                        "model": model,
                        "size": f"{width}×{height}",
                    })
                    if len(st.session_state.imggen_gallery) > 20:
                        st.session_state.imggen_gallery = st.session_state.imggen_gallery[:20]

    with tab_gallery:
        gallery = st.session_state.get("imggen_gallery", [])
        if not gallery:
            st.markdown("""
            <div style='border:1px dashed #181838;border-radius:12px;padding:40px;
                        text-align:center;color:#181830'>
              <div style='font-size:32px'>🖼️</div>
              <div style='margin-top:8px;font-size:13px'>Generated images will appear here</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"**{len(gallery)} images generated**")
            if st.button("🗑 Clear Gallery", key="gallery_clear"):
                st.session_state.imggen_gallery = []
                st.rerun()

            cols = st.columns(3)
            for i, item in enumerate(gallery):
                with cols[i % 3]:
                    st.image(item["bytes"], caption=item["prompt"][:40], use_container_width=True)
                    st.markdown(f"""
                    <div style='font-size:9px;color:#404060;text-align:center'>
                      {item['provider']} · {item['model'].split('/')[-1][:20]} · {item['size']}
                    </div>
                    """, unsafe_allow_html=True)
                    st.download_button(f"⬇", item["bytes"], f"img_{i}.png",
                                       mime="image/png", key=f"dl_gallery_{i}",
                                       use_container_width=True)

    with tab_api_info:
        st.markdown("""
        <div style='background:#0b0b1e;border:1px solid #181838;border-radius:12px;padding:16px'>
          <div style='font-size:14px;font-weight:700;color:#e0e0ff;margin-bottom:10px'>🌸 Pollinations.ai</div>
          <ul style='color:#606090;font-size:12px;line-height:1.9'>
            <li>Completely free, no API key needed</li>
            <li>Models: flux, flux-realism, flux-anime, flux-3d, turbo</li>
            <li>Supported sizes up to 1920×1920</li>
            <li>No hard rate limit — please use responsibly</li>
            <li>URL: image.pollinations.ai/prompt/{prompt}</li>
          </ul>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style='background:#0b0b1e;border:1px solid #181838;border-radius:12px;padding:16px;margin-top:10px'>
          <div style='font-size:14px;font-weight:700;color:#e0e0ff;margin-bottom:10px'>🤗 HuggingFace Inference</div>
          <ul style='color:#606090;font-size:12px;line-height:1.9'>
            <li>Free tier: ~30,000 calls/month</li>
            <li>Models: SDXL, SD v1.5, SD v2.1, and more</li>
            <li>Get free API key: <a href='https://huggingface.co/settings/tokens' target='_blank' style='color:#4444cc'>huggingface.co/settings/tokens</a></li>
            <li>Cold start possible (~20s wait on first call)</li>
          </ul>
        </div>
        """, unsafe_allow_html=True)