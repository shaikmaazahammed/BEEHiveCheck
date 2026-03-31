import streamlit as st
from textblob import TextBlob
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import numpy as np
import cv2
from PIL import Image

st.set_page_config(page_title="BEEHiveCheck", layout="wide")

# 🎨 UI + FONT
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Sreda&display=swap" rel="stylesheet">

<style>
.stApp {
    background-color: #0e0e0e;
    color: white;
    font-family: 'Segoe UI', sans-serif;
}

/* LOGO GLOW */
img {
    filter: drop-shadow(0px 0px 10px rgba(250,213,27,0.6));
    transition: 0.3s;
}
img:hover {
    filter: drop-shadow(0px 0px 20px rgba(250,213,27,0.9));
}

/* HEADER */
.header-title {
    font-family: 'Sreda', serif;
    font-size: 44px;
    color: white;
    text-shadow: 0 0 12px rgba(250,213,27,0.4);
}

/* SUBTITLE */
.subtitle {
    text-align: center;
    color: #aaa;
    font-size: 15px;
    margin-top: -8px;
}

/* DIVIDER */
.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, #fad51b, transparent);
    margin-top: 10px;
}

/* BUTTON */
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
    box-shadow: 0px 8px 20px rgba(250, 213, 27, 0.4);
}

/* INPUT */
.stTextInput input, .stTextArea textarea {
    background-color: #1a1a1a;
    color: white;
    border: 1px solid #333;
    border-radius: 8px;
}

/* FOOTER */
.footer {
    text-align:center;
    color:#888;
    font-size:14px;
    margin-top:40px;
    padding-top:20px;
    border-top:1px solid #333;
}
</style>
""", unsafe_allow_html=True)

# 🐝 HEADER (LOGO + TITLE SAME LINE)

col1, col2, col3 = st.columns([2,6,2])

with col2:
    h1, h2 = st.columns([1.5, 6])

    with h1:
        st.image("assets/logo.png", width=120)

    with h2:
        st.markdown('<div class="header-title">BEEHiveCheck</div>', unsafe_allow_html=True)

    st.markdown('<div class="subtitle">Content Quality Control System</div>', unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

st.divider()

# 🔐 GOOGLE SHEETS

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=scope
)

client = gspread.authorize(creds)
sheet = client.open("BEEHiveCheck Data").sheet1

# 📊 LOAD DATA

data = sheet.get_all_records()
df = pd.DataFrame(data)

# 📊 SIDEBAR

st.sidebar.title("📊 Analytics")

if not df.empty:
    st.sidebar.metric("Total Submissions", len(df))

st.divider()

# 👤 INPUTS

name = st.text_input("Your Name")
project = st.text_input("Project you are working on")

uploaded_file = st.file_uploader("Upload Content", type=["png","jpg","jpeg"])
caption = st.text_area("Caption")

# 🧠 AI ANALYSIS (SAFE VERSION)

def analyze_image(image):
    results = []

    img = np.array(image)

    # 🎨 COLOR CHECK
    avg_color = img.mean(axis=(0,1))
    if avg_color[0] > 100:
        results.append("🎨 Brand colors detected ✅")
    else:
        results.append("🎨 Weak brand color presence ⚠️")

    # 🔤 TEXT DETECTION (edge-based)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)

    if edges.mean() > 5:
        results.append("🔤 Likely text detected ✅")
    else:
        results.append("🔤 No clear text detected ⚠️")

    # 📍 SAFE ZONE
    h, w, _ = img.shape
    center = img[h//4:3*h//4, w//4:3*w//4]

    if center.mean() > 20:
        results.append("📍 Content centered (safe zone) ✅")
    else:
        results.append("📍 Content may be off-center ⚠️")

    # 🐝 LOGO HEURISTIC
    if np.max(img) > 220:
        results.append("🐝 Bright element detected (possible logo) ✅")
    else:
        results.append("🐝 Logo not clearly detected ❌")

    return results

# 🖼 IMAGE + AI

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, use_column_width=True)

    st.subheader("🧠 AI Analysis")
    results = analyze_image(image)
    for r in results:
        st.write(r)

# 🧠 GRAMMAR

grammar_ok = True
if caption:
    corrected = TextBlob(caption).correct()
    if caption != str(corrected):
        st.warning("Grammar issues ⚠️")
        grammar_ok = False
    else:
        st.success("Grammar OK ✅")

st.divider()

# ✅ CHECKLIST

color_check = st.checkbox("Brand colors")
font_check = st.checkbox("Correct font")
logo_check = st.checkbox("Logo placement correct")

confirm = st.checkbox("I confirm all guidelines are followed")

# 🚀 SUBMIT

if st.button("Submit for Review"):

    if not name or not uploaded_file:
        st.error("Fill all fields")
    elif not confirm:
        st.error("Confirm guidelines")
    else:

        score = sum([color_check, font_check, logo_check, grammar_ok])
        total = 4

        sheet.append_row([
            name,
            project,
            f"{score}/{total}",
            datetime.now().strftime("%Y-%m-%d %H:%M")
        ])

        st.success(f"Submitted! Score: {score}/{total}")

# 🐝 FOOTER

st.markdown("""
<div class="footer">
📩 Contact email: bueb.mentorship@gmail.com <br>
📸 Instagram: @bee.mentorship.program
</div>
""", unsafe_allow_html=True)
