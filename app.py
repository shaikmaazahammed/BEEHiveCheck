import streamlit as st
from textblob import TextBlob
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import numpy as np
from PIL import Image
import pytesseract
import io

st.set_page_config(page_title="BEEHiveCheck", layout="wide")

# ─────────────────────────────────────────────
# 🎨 UI + FONT
# ─────────────────────────────────────────────
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Sreda&display=swap" rel="stylesheet">
<style>
.stApp { background-color: #0e0e0e; color: white; font-family: 'Segoe UI', sans-serif; }
img { filter: drop-shadow(0px 0px 10px rgba(250,213,27,0.6)); transition: 0.3s; }
img:hover { filter: drop-shadow(0px 0px 20px rgba(250,213,27,0.9)); }
.header-title { font-family: 'Sreda', serif; font-size: 44px; color: white; text-shadow: 0 0 12px rgba(250,213,27,0.4); }
.subtitle { text-align: center; color: #aaa; font-size: 15px; margin-top: -8px; }
.divider { height: 1px; background: linear-gradient(90deg, transparent, #fad51b, transparent); margin-top: 10px; }
div.stButton > button { background: linear-gradient(135deg, #fad51b, #f5c400); color: black; border-radius: 10px; font-weight: 600; padding: 10px 20px; border: none; }
div.stButton > button:hover { transform: translateY(-2px); box-shadow: 0px 8px 20px rgba(250,213,27,0.4); }
.stTextInput input, .stTextArea textarea { background-color: #1a1a1a; color: white; border: 1px solid #333; border-radius: 8px; }
.footer { text-align:center; color:#888; font-size:14px; margin-top:40px; padding-top:20px; border-top:1px solid #333; }
.result-box { border-radius: 10px; padding: 12px 16px; font-size: 14px; margin: 4px 0; }
.result-ok { background: rgba(74,222,128,0.12); border: 1px solid rgba(74,222,128,0.3); color: #4ade80; }
.result-warn { background: rgba(250,213,27,0.12); border: 1px solid rgba(250,213,27,0.3); color: #fad51b; }
.result-err { background: rgba(248,113,113,0.12); border: 1px solid rgba(248,113,113,0.3); color: #f87171; }
.swatch-row { display: flex; gap: 6px; margin-top: 6px; flex-wrap: wrap; }
.swatch { display: inline-block; width: 18px; height: 18px; border-radius: 4px; border: 1px solid #555; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 🐝 HEADER
# ─────────────────────────────────────────────
col1, col2, col3 = st.columns([2, 6, 2])
with col2:
    h1, h2 = st.columns([1.5, 6])
    with h1:
        st.image("assets/logo.png", width=110)
    with h2:
        st.markdown('<div class="header-title">BEEHiveCheck</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Content Quality Control System</div>', unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

st.divider()

# ─────────────────────────────────────────────
# 🎨 BRAND COLOR PALETTE (from brand guidelines)
# ─────────────────────────────────────────────
BRAND_COLORS = [
    {"name": "Primary Yellow",        "rgb": (250, 213, 27),  "hex": "#fad51b"},
    {"name": "Primary Purple",        "rgb": (58,  42,  109), "hex": "#3a2a6d"},
    {"name": "Secondary Lilac",       "rgb": (228, 205, 220), "hex": "#e4cddc"},
    {"name": "Secondary Purple Light","rgb": (158, 140, 189), "hex": "#9e8cbd"},
    {"name": "Secondary Off-white",   "rgb": (248, 245, 247), "hex": "#f8f5f7"},
    {"name": "Secondary Dark",        "rgb": (50,  50,  50),  "hex": "#323232"},
]

# Reel safe zone constants (1080x1920 spec)
REEL_WIDTH  = 1080
REEL_HEIGHT = 1920
NOGO_TOP_PX = 220   # top no-go zone in pixels
NOGO_BOT_PX = 450   # bottom no-go zone in pixels
SIDE_MARGIN = 35    # left/right margin in pixels


def color_distance(px, brand_rgb):
    """Euclidean distance in RGB space."""
    return float(np.sqrt(sum((int(a) - int(b)) ** 2 for a, b in zip(px, brand_rgb))))


# ─────────────────────────────────────────────
# 🔍 FEATURE 1 — Color Palette Detection
# ─────────────────────────────────────────────
def detect_brand_colors(img: Image.Image, threshold: int = 80) -> dict:
    """
    Sample pixels from the image and check how many match brand palette.
    Returns dict with match_pct, found_colors list, and verdict.
    """
    img_rgb = img.convert("RGB").resize((200, 200))  # downsample for speed
    pixels = np.array(img_rgb).reshape(-1, 3)

    brand_hits   = 0
    found_colors = set()

    for px in pixels[::4]:  # sample every 4th pixel
        min_dist  = float("inf")
        min_color = None
        for bc in BRAND_COLORS:
            d = color_distance(tuple(px), bc["rgb"])
            if d < min_dist:
                min_dist  = d
                min_color = bc
        if min_dist < threshold:
            brand_hits += 1
            found_colors.add(min_color["hex"])

    total     = len(pixels[::4])
    match_pct = round((brand_hits / total) * 100) if total else 0

    if match_pct >= 40:
        verdict = "ok"
        label   = f"✅ Brand colors detected ({match_pct}% match)"
    elif match_pct >= 15:
        verdict = "warn"
        label   = f"⚠️ Partial brand colors ({match_pct}% match) — check palette"
    else:
        verdict = "warn"
        label   = f"⚠️ Non-brand colors used ({match_pct}% match)"

    return {
        "verdict":      verdict,
        "label":        label,
        "match_pct":    match_pct,
        "found_colors": list(found_colors),
    }


# ─────────────────────────────────────────────
# 🔍 FEATURE 2 — Basic Logo Detection
# ─────────────────────────────────────────────
def detect_logo(img: Image.Image, threshold: int = 60) -> dict:
    """
    Look for a brand-color cluster in each corner (typical logo placement).
    Returns verdict and details.
    """
    img_rgb  = img.convert("RGB")
    w, h     = img_rgb.size
    corner_s = max(40, min(w, h) // 5)  # 20% of shorter dimension

    corners = {
        "Top-left":     img_rgb.crop((0,          0,          corner_s,   corner_s)),
        "Top-right":    img_rgb.crop((w-corner_s, 0,          w,          corner_s)),
        "Bottom-left":  img_rgb.crop((0,          h-corner_s, corner_s,   h)),
        "Bottom-right": img_rgb.crop((w-corner_s, h-corner_s, w,          h)),
    }

    best_region = None
    best_score  = 0.0

    for region_name, patch in corners.items():
        pixels    = np.array(patch.resize((50, 50))).reshape(-1, 3)
        brand_cnt = sum(
            1 for px in pixels
            if any(color_distance(tuple(px), bc["rgb"]) < threshold for bc in BRAND_COLORS)
        )
        score = brand_cnt / len(pixels) if len(pixels) else 0
        if score > best_score:
            best_score  = score
            best_region = region_name

    if best_score > 0.15:
        return {
            "verdict": "ok",
            "label":   f"✅ Logo likely detected ({best_region} corner, {round(best_score*100)}% brand pixels)",
        }
    else:
        return {
            "verdict": "warn",
            "label":   "⚠️ Logo not detected — check logo placement in a corner",
        }


# ─────────────────────────────────────────────
# 🔍 FEATURE 3 — OCR Text Detection + Safe Zone Check
# ─────────────────────────────────────────────
def detect_text_zones(img: Image.Image) -> dict:
    """
    Run Tesseract OCR with bounding boxes, then classify each word block
    as inside the safe zone or in a no-go zone (scaled to Reel 1080x1920 spec).
    """
    img_rgb = img.convert("RGB")
    orig_w, orig_h = img_rgb.size

    # Scale factors to map image pixels → 1080x1920 reel space
    scale_x = REEL_WIDTH  / orig_w
    scale_y = REEL_HEIGHT / orig_h

    try:
        ocr_data = pytesseract.image_to_data(img_rgb, output_type=pytesseract.Output.DICT)
    except Exception:
        return {
            "verdict": "warn",
            "label":   "⚠️ OCR engine unavailable — install pytesseract & Tesseract",
            "text_found": False,
            "unsafe_words": [],
            "safe_words":   [],
        }

    unsafe_words = []
    safe_words   = []

    for i, word in enumerate(ocr_data["text"]):
        word = word.strip()
        if not word or int(ocr_data["conf"][i]) < 30:
            continue

        # Bounding box in original image pixels
        x  = int(ocr_data["left"][i])
        y  = int(ocr_data["top"][i])
        bh = int(ocr_data["height"][i])

        # Convert to reel-space pixels
        reel_y_top = y        * scale_y
        reel_y_bot = (y + bh) * scale_y

        in_top_nogo = reel_y_top < NOGO_TOP_PX
        in_bot_nogo = reel_y_bot > (REEL_HEIGHT - NOGO_BOT_PX)

        if in_top_nogo or in_bot_nogo:
            zone = "top no-go (220px)" if in_top_nogo else "bottom no-go (450px)"
            unsafe_words.append(f'"{word}" — {zone}')
        else:
            safe_words.append(word)

    text_found = bool(unsafe_words or safe_words)

    if unsafe_words:
        verdict = "warn"
        label   = f"⚠️ Text detected in unsafe zone — {len(unsafe_words)} word(s) at risk of cropping"
    elif safe_words:
        verdict = "ok"
        label   = f"✅ Text detected in safe zone ({len(safe_words)} word(s) — no cropping risk)"
    else:
        verdict = "warn"
        label   = "⚠️ No text detected — ensure captions/text are visible"

    return {
        "verdict":      verdict,
        "label":        label,
        "text_found":   text_found,
        "unsafe_words": unsafe_words,
        "safe_words":   safe_words,
    }


# ─────────────────────────────────────────────
# 🔐 GOOGLE SHEETS
# ─────────────────────────────────────────────
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds  = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)
sheet  = client.open("BEEHiveCheck Data").sheet1

# ─────────────────────────────────────────────
# 📊 DATA + SIDEBAR
# ─────────────────────────────────────────────
data = sheet.get_all_records()
df   = pd.DataFrame(data)

st.sidebar.title("📊 Analytics")
if not df.empty and "Score" in df.columns:
    st.sidebar.metric("Total Submissions", len(df))
    scores = pd.to_numeric(
        df["Score"].astype(str).str.split("/").str[0], errors="coerce"
    ).fillna(0)
    st.sidebar.bar_chart(scores)
    if "Name" in df.columns:
        top_user = df["Name"].value_counts().idxmax()
        st.sidebar.write(f"🏆 Top Contributor: {top_user}")
else:
    st.sidebar.info("No data yet")

st.divider()

# ─────────────────────────────────────────────
# 👤 INPUTS
# ─────────────────────────────────────────────
name    = st.text_input("Your Name")
project = st.text_input("Project you are working on")

uploaded_file = st.file_uploader("Upload Content", type=["png", "jpg", "jpeg"])

# ─────────────────────────────────────────────
# 🔬 AUTO ANALYSIS when image is uploaded
# ─────────────────────────────────────────────
color_result = None
logo_result  = None
text_result  = None
color_ok     = False
logo_ok      = False
text_ok      = False

if uploaded_file:
    img_bytes = uploaded_file.read()
    img       = Image.open(io.BytesIO(img_bytes))
    st.image(img, caption="Preview", use_column_width=True)

    st.subheader("🔬 Automated Analysis")
    col_a, col_b, col_c = st.columns(3)

    # — Color palette —
    with col_a:
        with st.spinner("Detecting brand colors…"):
            color_result = detect_brand_colors(img)
        css_cls = "result-ok" if color_result["verdict"] == "ok" else "result-warn"
        st.markdown(f'<div class="result-box {css_cls}">{color_result["label"]}</div>', unsafe_allow_html=True)

        if color_result["found_colors"]:
            swatches = "".join(
                f'<span class="swatch" style="background:{c};" title="{c}"></span>'
                for c in color_result["found_colors"]
            )
            st.markdown(f'<div class="swatch-row">{swatches}</div>', unsafe_allow_html=True)
        color_ok = color_result["verdict"] == "ok"

    # — Logo detection —
    with col_b:
        with st.spinner("Scanning for logo…"):
            logo_result = detect_logo(img)
        css_cls = "result-ok" if logo_result["verdict"] == "ok" else "result-warn"
        st.markdown(f'<div class="result-box {css_cls}">{logo_result["label"]}</div>', unsafe_allow_html=True)
        logo_ok = logo_result["verdict"] == "ok"

    # — OCR + safe zone —
    with col_c:
        with st.spinner("Running OCR text detection…"):
            text_result = detect_text_zones(img)
        css_cls = "result-ok" if text_result["verdict"] == "ok" else "result-warn"
        st.markdown(f'<div class="result-box {css_cls}">{text_result["label"]}</div>', unsafe_allow_html=True)

        if text_result.get("unsafe_words"):
            with st.expander("⚠️ Unsafe zone words"):
                for w in text_result["unsafe_words"]:
                    st.write(f"• {w}")
        text_ok = text_result["verdict"] == "ok"

    st.divider()

caption = st.text_area("Caption")

# 🧠 Grammar check
grammar_ok = True
if caption:
    blob      = TextBlob(caption)
    corrected = blob.correct()
    if caption == str(corrected):
        st.success("✅ No grammar issues")
    else:
        st.warning("⚠️ Grammar issues detected")
        grammar_ok = False

st.divider()

# ─────────────────────────────────────────────
# ✅ CHECKLIST
# ─────────────────────────────────────────────
st.subheader("Checklist")

col1, col2 = st.columns(2)
with col1:
    color_check    = st.checkbox("Brand colors used",    value=color_ok)
    contrast_check = st.checkbox("Good contrast")
    title_font     = st.checkbox("Futura used")
    body_font      = st.checkbox("Avenir used")
    logo_place     = st.checkbox("Logo correct",         value=logo_ok)

with col2:
    safe_zone = st.checkbox("Safe zone followed",        value=text_ok)
    graphics  = st.checkbox("Approved graphics")
    tone_check = st.checkbox("Tone correct")

confirm = st.checkbox("I confirm all guidelines are followed")

st.divider()

# ─────────────────────────────────────────────
# 🚀 SUBMIT
# ─────────────────────────────────────────────
if st.button("Submit for Review"):
    if not name or not project or not uploaded_file or not caption:
        st.error("❌ Fill all fields")
    elif not confirm:
        st.error("❌ Confirm guidelines")
    else:
        checks = [
            color_check, contrast_check,
            title_font, body_font,
            logo_place,
            safe_zone,
            graphics,
            tone_check,
            grammar_ok,
        ]

        score = sum(checks)
        total = len(checks)

        if score == total:
            result = "Perfect ✅"
            st.success(f"Perfect ({score}/{total}) 🚀")
        elif score >= total * 0.7:
            result = "Needs Fix ⚠️"
            st.warning(f"Needs improvement ({score}/{total})")
        else:
            result = "Not Approved ❌"
            st.error(f"Not approved ({score}/{total})")

        sheet.append_row([
            name,
            project,
            f"{score}/{total}",
            result,
            "Yes",
            datetime.now().strftime("%Y-%m-%d %H:%M"),
        ])
        st.success("Saved to dashboard 📊")

# ─────────────────────────────────────────────
# 🐝 FOOTER
# ─────────────────────────────────────────────
st.markdown("""
<div class="footer">
    📩 Contact email: bueb.mentorship@gmail.com <br>
    📸 Instagram: @bee.mentorship.program
</div>
""", unsafe_allow_html=True)
