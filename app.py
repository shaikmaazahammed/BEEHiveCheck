import streamlit as st
from textblob import TextBlob
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import numpy as np
from PIL import Image
import io
import base64

def get_logo_b64(path: str = "assets/logo.png") -> str:
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return ""

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
.bee-header {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 10px 0 4px;
}
.bee-header-row {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 16px;
}
.bee-header-row img {
    width: 90px;
    filter: drop-shadow(0px 0px 10px rgba(250,213,27,0.6));
}
.header-title {
    font-family: 'Sreda', serif;
    font-size: 44px;
    color: white;
    text-shadow: 0 0 12px rgba(250,213,27,0.4);
    line-height: 1;
}
.subtitle {
    text-align: center;
    color: #aaa;
    font-size: 15px;
    margin-top: 6px;
}
.divider {
    width: 100%;
    height: 1px;
    background: linear-gradient(90deg, transparent, #fad51b, transparent);
    margin-top: 10px;
}
div.stButton > button {
    background: linear-gradient(135deg, #fad51b, #f5c400);
    color: black;
    border-radius: 10px;
    font-weight: 600;
    padding: 10px 20px;
    border: none;
}
div.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0px 8px 20px rgba(250,213,27,0.4);
}
.stTextInput input, .stTextArea textarea {
    background-color: #1a1a1a;
    color: white;
    border: 1px solid #333;
    border-radius: 8px;
}
.footer {
    text-align: center;
    color: #888;
    font-size: 14px;
    margin-top: 40px;
    padding-top: 20px;
    border-top: 1px solid #333;
}
.result-box  { border-radius: 10px; padding: 12px 16px; font-size: 14px; margin: 4px 0; }
.result-ok   { background: rgba(74,222,128,0.12); border: 1px solid rgba(74,222,128,0.3); color: #4ade80; }
.result-warn { background: rgba(250,213,27,0.12);  border: 1px solid rgba(250,213,27,0.3); color: #fad51b; }
.swatch-row  { display: flex; gap: 6px; margin-top: 6px; flex-wrap: wrap; }
.swatch      { display: inline-block; width: 18px; height: 18px; border-radius: 4px; border: 1px solid #555; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 🐝 HEADER — logo embedded as base64 (no path issues)
# ─────────────────────────────────────────────
logo_b64 = get_logo_b64()
logo_img_tag = f'<img src="data:image/png;base64,{logo_b64}" />' if logo_b64 else ""

_, center_col, _ = st.columns([1, 4, 1])
with center_col:
    st.markdown(f"""
    <div class="bee-header">
        <div class="bee-header-row">
            {logo_img_tag}
            <span class="header-title">BEEHiveCheck</span>
        </div>
        <div class="subtitle">Content Quality Control System</div>
        <div class="divider"></div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ─────────────────────────────────────────────
# 🎨 BRAND COLOR PALETTE
# ─────────────────────────────────────────────
BRAND_COLORS = [
    {"name": "Primary Yellow",         "rgb": (250, 213, 27),  "hex": "#fad51b"},
    {"name": "Primary Purple",         "rgb": (58,  42,  109), "hex": "#3a2a6d"},
    {"name": "Secondary Lilac",        "rgb": (228, 205, 220), "hex": "#e4cddc"},
    {"name": "Secondary Purple Light", "rgb": (158, 140, 189), "hex": "#9e8cbd"},
    {"name": "Secondary Off-white",    "rgb": (248, 245, 247), "hex": "#f8f5f7"},
    {"name": "Secondary Dark",         "rgb": (50,  50,  50),  "hex": "#323232"},
]


def color_distance(px, brand_rgb):
    return float(np.sqrt(sum((int(a) - int(b)) ** 2 for a, b in zip(px, brand_rgb))))


# ─────────────────────────────────────────────
# 🔍 FEATURE 1 — Color Palette Detection
# ─────────────────────────────────────────────
def detect_brand_colors(img: Image.Image, threshold: int = 80) -> dict:
    img_rgb = img.convert("RGB").resize((200, 200))
    pixels  = np.array(img_rgb).reshape(-1, 3)

    brand_hits   = 0
    found_colors = set()

    for px in pixels[::4]:
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
    img_rgb  = img.convert("RGB")
    w, h     = img_rgb.size
    corner_s = max(40, min(w, h) // 5)

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
    return {
        "verdict": "warn",
        "label":   "⚠️ Logo not detected — check logo placement in a corner",
    }


# ─────────────────────────────────────────────
# 🔐 GOOGLE SHEETS
# ─────────────────────────────────────────────
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
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
# 🔬 AUTO ANALYSIS
# ─────────────────────────────────────────────
color_ok = False
logo_ok  = False

if uploaded_file:
    img_bytes = uploaded_file.read()
    img       = Image.open(io.BytesIO(img_bytes))
    st.image(img, caption="Preview", use_column_width=True)

    st.subheader("🔬 Automated Analysis")
    col_a, col_b = st.columns(2)

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

    with col_b:
        with st.spinner("Scanning for logo…"):
            logo_result = detect_logo(img)
        css_cls = "result-ok" if logo_result["verdict"] == "ok" else "result-warn"
        st.markdown(f'<div class="result-box {css_cls}">{logo_result["label"]}</div>', unsafe_allow_html=True)
        logo_ok = logo_result["verdict"] == "ok"

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
    color_check    = st.checkbox("Brand colors used",  value=color_ok)
    contrast_check = st.checkbox("Good contrast")
    title_font     = st.checkbox("Futura used")
    body_font      = st.checkbox("Avenir used")
    logo_place     = st.checkbox("Logo correct",       value=logo_ok)

with col2:
    safe_zone  = st.checkbox("Safe zone followed")
    graphics   = st.checkbox("Approved graphics")
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
