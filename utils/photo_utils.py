"""
photo_utils.py
==============
Free image/photo analysis using:
  1. Hugging Face Vision models — image captioning, classification, OCR (free tier)
  2. Google Cloud Vision — free tier (1000 units/month)
  3. OpenCV-based local analysis (no API needed)
  4. Pillow-based metadata extraction (no API needed)
  5. EXIF data extraction

Limit tracking included.
"""
from __future__ import annotations
import requests
import streamlit as st
import base64
import io
from datetime import datetime
from typing import Optional, Union

# ─── Limits ──────────────────────────────────────────────────────────────────
LIMITS = {
    "huggingface": {
        "calls_per_month": 30000,
        "description": "HuggingFace Inference API free tier",
        "key_required": True,
    },
    "google_vision": {
        "units_per_month": 1000,
        "description": "Google Cloud Vision free tier",
        "key_required": True,
    },
}

HF_VISION_MODELS = {
    "Image Captioning": {
        "model": "Salesforce/blip-image-captioning-large",
        "task": "image-to-text",
        "icon": "📝",
    },
    "Object Detection": {
        "model": "facebook/detr-resnet-50",
        "task": "object-detection",
        "icon": "🔍",
    },
    "Image Classification": {
        "model": "google/vit-base-patch16-224",
        "task": "image-classification",
        "icon": "🏷️",
    },
    "Visual Q&A": {
        "model": "dandelin/vilt-b32-finetuned-vqa",
        "task": "visual-question-answering",
        "icon": "❓",
    },
    "OCR / Document": {
        "model": "microsoft/trocr-base-printed",
        "task": "image-to-text",
        "icon": "📄",
    },
    "Face Detection": {
        "model": "deepface-emotions",
        "task": "image-classification",
        "icon": "😊",
    },
}


# ─── State ───────────────────────────────────────────────────────────────────
def init_photo_state():
    if "photo_usage" not in st.session_state:
        st.session_state.photo_usage = {
            "hf_calls": 0,
            "gvision_calls": 0,
            "local_calls": 0,
            "errors": 0,
            "month": datetime.now().strftime("%Y-%m"),
        }


# ═══════════════════════════════════════════════════════════════════════
# HUGGING FACE VISION
# ═══════════════════════════════════════════════════════════════════════
def analyze_image_hf(
    image_bytes: bytes,
    api_key: str,
    task: str = "image-to-text",
    model: str = "Salesforce/blip-image-captioning-large",
    question: str = None,
) -> dict:
    """
    Analyze image using HuggingFace Inference API.
    Returns: { "result": any, "raw": dict, "error": None }
    """
    init_photo_state()
    url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        if task == "visual-question-answering" and question:
            # VQA requires JSON with both image and question
            img_b64 = base64.b64encode(image_bytes).decode("utf-8")
            payload = {"inputs": {"image": img_b64, "question": question}}
            r = requests.post(url, headers=headers, json=payload, timeout=60)
        else:
            r = requests.post(url, headers=headers, data=image_bytes, timeout=60)

        if r.status_code == 503:
            return {"result": None, "raw": {}, "error": "Model loading. Wait ~20s and retry."}
        r.raise_for_status()
        raw = r.json()
        st.session_state.photo_usage["hf_calls"] += 1

        # Normalize response
        if isinstance(raw, list) and raw:
            if task == "image-to-text":
                result = raw[0].get("generated_text", str(raw[0]))
            elif task == "object-detection":
                result = [{"label": item.get("label"), "score": round(item.get("score", 0), 3),
                           "box": item.get("box", {})} for item in raw]
            elif task == "image-classification":
                result = sorted(raw, key=lambda x: x.get("score", 0), reverse=True)[:5]
                result = [{"label": item.get("label"), "confidence": f"{item.get('score', 0)*100:.1f}%"}
                          for item in result]
            else:
                result = raw
        else:
            result = raw

        return {"result": result, "raw": raw, "error": None}

    except Exception as e:
        st.session_state.photo_usage["errors"] += 1
        return {"result": None, "raw": {}, "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════
# LOCAL IMAGE ANALYSIS (Pillow — no API needed)
# ═══════════════════════════════════════════════════════════════════════
def analyze_image_local(image_bytes: bytes) -> dict:
    """
    Extract basic image metadata and stats using Pillow.
    No API key or network needed.
    """
    init_photo_state()
    try:
        from PIL import Image, ExifTags
        import io as _io

        img = Image.open(_io.BytesIO(image_bytes))

        # Basic info
        info = {
            "format": img.format or "Unknown",
            "mode": img.mode,
            "width": img.width,
            "height": img.height,
            "megapixels": round(img.width * img.height / 1_000_000, 2),
            "file_size_kb": round(len(image_bytes) / 1024, 1),
            "aspect_ratio": f"{img.width}:{img.height}",
        }

        # Color analysis
        if img.mode in ("RGB", "RGBA"):
            small = img.resize((50, 50)).convert("RGB")
            pixels = list(small.getdata())
            avg_r = sum(p[0] for p in pixels) // len(pixels)
            avg_g = sum(p[1] for p in pixels) // len(pixels)
            avg_b = sum(p[2] for p in pixels) // len(pixels)
            info["avg_color"] = {"r": avg_r, "g": avg_g, "b": avg_b}
            info["brightness"] = round((avg_r * 0.299 + avg_g * 0.587 + avg_b * 0.114), 1)

        # EXIF data
        exif_data = {}
        try:
            raw_exif = img._getexif()
            if raw_exif:
                for tag_id, value in raw_exif.items():
                    tag = ExifTags.TAGS.get(tag_id, tag_id)
                    if isinstance(value, (str, int, float)):
                        exif_data[str(tag)] = str(value)
        except Exception:
            pass
        info["exif"] = exif_data

        st.session_state.photo_usage["local_calls"] += 1
        return {"info": info, "error": None}

    except ImportError:
        return {"info": {}, "error": "Pillow not installed. Run: pip install Pillow"}
    except Exception as e:
        return {"info": {}, "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════
# GOOGLE CLOUD VISION (1000 units/month free)
# ═══════════════════════════════════════════════════════════════════════
def analyze_image_google(
    image_bytes: bytes,
    api_key: str,
    features: list = None,
) -> dict:
    """
    Google Cloud Vision API — 1000 units/month free.
    Features: LABEL_DETECTION, TEXT_DETECTION, SAFE_SEARCH_DETECTION,
              FACE_DETECTION, LANDMARK_DETECTION, WEB_DETECTION
    """
    init_photo_state()
    if features is None:
        features = ["LABEL_DETECTION", "TEXT_DETECTION", "WEB_DETECTION"]

    img_b64 = base64.b64encode(image_bytes).decode("utf-8")
    url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
    payload = {
        "requests": [{
            "image": {"content": img_b64},
            "features": [{"type": f, "maxResults": 10} for f in features],
        }]
    }

    try:
        r = requests.post(url, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        response = data.get("responses", [{}])[0]
        st.session_state.photo_usage["gvision_calls"] += 1

        result = {}
        if "labelAnnotations" in response:
            result["labels"] = [{"label": l["description"], "confidence": f"{l['score']*100:.1f}%"}
                                  for l in response["labelAnnotations"]]
        if "textAnnotations" in response:
            result["text"] = response["textAnnotations"][0].get("description", "") if response["textAnnotations"] else ""
        if "webDetection" in response:
            web = response["webDetection"]
            result["web"] = {
                "best_guess": [e.get("label") for e in web.get("bestGuessLabels", [])],
                "entities": [e.get("description") for e in web.get("webEntities", [])[:5]],
            }
        if "safeSearchAnnotation" in response:
            result["safe_search"] = response["safeSearchAnnotation"]

        return {"result": result, "error": None}
    except Exception as e:
        st.session_state.photo_usage["errors"] += 1
        return {"result": {}, "error": str(e)}


def image_to_base64_url(image_bytes: bytes, mime: str = "image/jpeg") -> str:
    """Convert image bytes to a data URL for display."""
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def get_photo_usage_stats() -> dict:
    init_photo_state()
    return st.session_state.photo_usage.copy()