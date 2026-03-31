import streamlit as st
from textblob import TextBlob
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

st.set_page_config(page_title="BEEHiveCheck", layout="wide")

# 🎨 CLEAN PREMIUM UI
st.markdown("""
<style>
.stApp {
    background-color: #0e0e0e;
    color: white;
    font-family: 'Segoe UI', sans-serif;
}

/* HEADER */
.header-box {
    text-align: center;
    padding: 30px 0 10px 0;
}

/* TITLE */
.header-box h1 {
    font-size: 42px;
    margin-bottom: 5px;
    text-shadow: 0 0 12px rgba(250, 213, 27, 0.3);
}

/* SUBTITLE */
.header-box p {
    color: #aaa;
    font-size: 16px;
}

/* BUTTON */
div.stButton > button {
    background: linear-gradient(135deg, #fad51b, #f5c400);
    color: black;
    border-radius: 10px;
    font-weight: 600;
    padding: 10px 20px;
    border: none;
    transition: all 0.3s ease;
}
div.stButton > button:hover {
    transform: translateY(-3px);
    box-shadow: 0px 8px 20px rgba(250, 213, 27, 0.4);
}

/* INPUTS */
.stTextInput input, .stTextArea textarea {
    background-color: #1a1a1a;
    color: white;
    border-radius: 8px;
    border: 1px solid #333;
}

/* UPLOAD */
section[data-testid="stFileUploader"] {
    background-color: #1a1a1a;
    border-radius: 12px;
    padding: 12px;
    border: 1px dashed #333;
}
</style>
""", unsafe_allow_html=True)

# 🐝 HEADER (STABLE VERSION)
st.markdown('<div class="header-box">', unsafe_allow_html=True)

st.image("assets/logo.png", width=180)

st.markdown(
    "<h1>BEEHiveCheck</h1>",
    unsafe_allow_html=True
)

st.markdown(
    "<p>Content Quality Control System</p>",
    unsafe_allow_html=True
)

st.markdown('</div>', unsafe_allow_html=True)

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

if not df.empty and "Score" in df.columns:
    st.sidebar.metric("Total Submissions", len(df))

    scores = pd.to_numeric(
        df["Score"].astype(str).str.split("/").str[0],
        errors="coerce"
    ).fillna(0)

    st.sidebar.bar_chart(scores)

    if "Name" in df.columns:
        top_user = df["Name"].value_counts().idxmax()
        st.sidebar.write(f"🏆 Top Contributor: {top_user}")
else:
    st.sidebar.info("No data yet")

st.divider()

# 👤 INPUT
name = st.text_input("Your Name")
project = st.text_input("Project you are working on")

uploaded_file = st.file_uploader(
    "Upload Content",
    type=["png","jpg","jpeg","mp4"]
)

if uploaded_file:
    st.image(uploaded_file, caption="Preview", use_column_width=True)

caption = st.text_area("Caption")

# 🧠 GRAMMAR
grammar_ok = True

if caption:
    blob = TextBlob(caption)
    corrected = blob.correct()

    if caption == str(corrected):
        st.success("✅ No grammar issues")
    else:
        st.warning("⚠️ Grammar issues detected")
        grammar_ok = False

st.divider()

# ✅ CHECKLIST
st.subheader("Checklist")

col1, col2 = st.columns(2)

with col1:
    color_check = st.checkbox("Brand colors used")
    contrast_check = st.checkbox("Good contrast")
    title_font = st.checkbox("Futura used")
    body_font = st.checkbox("Avenir used")
    logo_place = st.checkbox("Logo correct")

with col2:
    safe_zone = st.checkbox("Safe zone followed")
    graphics = st.checkbox("Approved graphics")
    tone_check = st.checkbox("Tone correct")

confirm = st.checkbox("I confirm all guidelines are followed")

st.divider()

# 🚀 SUBMIT
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

        sheet.append_row([
            name,
            project,
            f"{score}/{total}",
            result,
            "Yes",
            datetime.now().strftime("%Y-%m-%d %H:%M")
        ])

        st.success("Saved to dashboard 📊")
