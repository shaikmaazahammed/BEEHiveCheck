import streamlit as st
from textblob import TextBlob
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import numpy as np
import cv2
from PIL import Image
import pytesseract

st.set_page_config(page_title="BEEHiveCheck", layout="wide")

# 🎨 UI
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Sreda&display=swap" rel="stylesheet">
<style>
.stApp {background-color:#0e0e0e;color:white;font-family:'Segoe UI';}
img {filter: drop-shadow(0px 0px 10px rgba(250,213,27,0.6));}
.header {font-family:'Sreda';font-size:44px;}
.footer {text-align:center;color:#888;margin-top:40px;border-top:1px solid #333;}
</style>
""", unsafe_allow_html=True)

# 🐝 HEADER
col1, col2 = st.columns([1,6])
with col1:
    st.image("assets/logo.png", width=120)
with col2:
    st.markdown("<div class='header'>BEEHiveCheck</div>", unsafe_allow_html=True)

st.markdown("Content Quality Control System")
st.divider()

# 🔐 GOOGLE SHEETS
scope = ["https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive"]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=scope)

client = gspread.authorize(creds)
sheet = client.open("BEEHiveCheck Data").sheet1

# 📊 LOAD DATA
data = sheet.get_all_records()
df = pd.DataFrame(data)

# 📊 SIDEBAR
st.sidebar.title("📊 Analytics")
if not df.empty:
    st.sidebar.metric("Total Submissions", len(df))

# 👤 INPUT
name = st.text_input("Your Name")
project = st.text_input("Project")

uploaded_file = st.file_uploader("Upload Image", type=["png","jpg","jpeg"])
caption = st.text_area("Caption")

# 🧠 AI ANALYSIS FUNCTION
def analyze_image(image):
    results = []

    img = np.array(image)

    # 🎨 COLOR DETECTION
    avg_color = img.mean(axis=(0,1))
    if avg_color[0] > 100:  # simple check
        results.append("🎨 Brand colors detected ✅")
    else:
        results.append("🎨 Weak brand color presence ⚠️")

    # 🔤 TEXT DETECTION (OCR)
    text = pytesseract.image_to_string(img)
    if len(text.strip()) > 5:
        results.append("🔤 Text detected ✅")
    else:
        results.append("🔤 No text detected ⚠️")

    # 📍 SAFE ZONE (basic)
    h, w, _ = img.shape
    center = img[h//4:3*h//4, w//4:3*w//4]
    if center.mean() > 10:
        results.append("📍 Content inside safe zone ✅")
    else:
        results.append("📍 Possible unsafe placement ⚠️")

    # 🐝 LOGO DETECTION (basic brightness heuristic)
    if np.max(img) > 200:
        results.append("🐝 Possible logo detected ✅")
    else:
        results.append("🐝 Logo not clearly detected ❌")

    return results

# 🖼 IMAGE PREVIEW + AI
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, use_column_width=True)

    st.subheader("🧠 AI Analysis")
    ai_results = analyze_image(image)
    for r in ai_results:
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
logo_check = st.checkbox("Logo placed correctly")

confirm = st.checkbox("Confirm all guidelines")

# 🚀 SUBMIT
if st.button("Submit"):

    if not name or not uploaded_file:
        st.error("Fill all fields")
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
📩 bueb.mentorship@gmail.com <br>
📸 @bee.mentorship.program
</div>
""", unsafe_allow_html=True)
