import streamlit as st
from textblob import TextBlob
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

st.set_page_config(page_title="BEEHiveCheck", layout="wide")

# 🖤 Minimal UI
st.markdown("""
<style>
.stApp { background-color: #0e0e0e; color: white; }

h1, h2, h3 { color: white; }

div.stButton > button {
    background-color: #fad51b;
    color: black;
    border-radius: 8px;
    font-weight: bold;
}

.stTextArea textarea {
    background-color: #1a1a1a;
    color: white;
}

section[data-testid="stFileUploader"] {
    background-color: #1a1a1a;
    border-radius: 10px;
    padding: 10px;
}
</style>
""", unsafe_allow_html=True)

# 🐝 Title
st.title("🐝 BEEHiveCheck")
st.markdown("Content Quality Control for Your Hive")

st.divider()

# 🔐 CONNECT GOOGLE SHEETS
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

# 📊 SIDEBAR ANALYTICS
st.sidebar.title("📊 Analytics")

if not df.empty:
    st.sidebar.metric("Total Submissions", len(df))

    approved = df[df["Result"] == "Perfect ✅"]
    st.sidebar.metric("Approved", len(approved))

    scores = df["Score"].str.split("/").str[0].astype(int)
    st.sidebar.bar_chart(scores)
else:
    st.sidebar.info("No data yet")

# 👤 INPUT
name = st.text_input("Your Name")

# 📤 Upload
uploaded_file = st.file_uploader(
    "Upload Content",
    type=["png", "jpg", "jpeg", "mp4"]
)

# ✍️ Caption
caption = st.text_area("Caption")

# 🧠 Grammar Check (NO suggestions)
grammar_ok = True

if caption:
    st.subheader("🧠 Grammar Check")

    blob = TextBlob(caption)
    corrected = blob.correct()

    if caption == str(corrected):
        st.success("✅ No major grammar issues")
        grammar_ok = True
    else:
        st.warning("⚠️ Possible grammar issues detected")
        grammar_ok = False

st.divider()

# ✅ Checklist
st.subheader("Checklist")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Design**")
    color_check = st.checkbox("Brand colors used")
    contrast_check = st.checkbox("Good contrast")

    st.markdown("**Typography**")
    title_font = st.checkbox("Futura (title)")
    body_font = st.checkbox("Avenir (body)")

    st.markdown("**Logo**")
    logo_place = st.checkbox("Correct placement")
    logo_space = st.checkbox("Clear spacing")
    logo_distort = st.checkbox("Not distorted")

with col2:
    st.markdown("**Reel Safety**")
    safe_zone = st.checkbox("Inside safe zone")

    st.markdown("**Graphics**")
    graphics = st.checkbox("Approved graphics")

    st.markdown("**Tone Match**")
    tone_check = st.checkbox("Matches brand tone")

st.divider()

# 🚀 SUBMIT
if st.button("Submit for Review"):

    if not name or not uploaded_file or not caption:
        st.error("❌ Please fill all fields")
    else:
        checks = [
            color_check, contrast_check,
            title_font, body_font,
            logo_place, logo_space, logo_distort,
            safe_zone,
            graphics,
            tone_check,
            grammar_ok
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

        # 📝 SAVE TO GOOGLE SHEETS
        sheet.append_row([
            name,
            f"{score}/{total}",
            result,
            "Yes",
            datetime.now().strftime("%Y-%m-%d %H:%M")
        ])

        st.success("Saved to dashboard 📊")
