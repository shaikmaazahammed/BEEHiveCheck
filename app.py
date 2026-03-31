import streamlit as st
from textblob import TextBlob
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

st.set_page_config(page_title="BEEHiveCheck", layout="wide")

# 🖤 UI
st.markdown("""
<style>
.stApp { background-color: #0e0e0e; color: white; }

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
</style>
""", unsafe_allow_html=True)

st.title("🐝 BEEHiveCheck")
st.markdown("Content Quality Control System")

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

data = sheet.get_all_records()
df = pd.DataFrame(data)

# 📊 SIDEBAR ANALYTICS
st.sidebar.title("📊 Analytics")

if not df.empty:
    st.sidebar.metric("Total Submissions", len(df))

    approved = df[df["Result"] == "Approved ✅"]
    st.sidebar.metric("Approved", len(approved))

    st.sidebar.metric("Approval Rate", f"{(len(approved)/len(df))*100:.1f}%")

    top_user = df["Name"].value_counts().idxmax()
    st.sidebar.write(f"🏆 Top Contributor: {top_user}")

    scores = df["Score"].str.split("/").str[0].astype(int)
    st.sidebar.bar_chart(scores)
else:
    st.sidebar.info("No data yet")

st.divider()

# 👤 USER INPUT
name = st.text_input("Your Name")
project = st.text_input("Project you are working on")

uploaded_file = st.file_uploader("Upload Content", type=["png","jpg","jpeg","mp4"])

# 🖼️ PREVIEW
if uploaded_file:
    st.image(uploaded_file, caption="Preview", use_column_width=True)

caption = st.text_area("Caption")

# 🧠 Grammar Check
grammar_ok = True

if caption:
    blob = TextBlob(caption)
    corrected = blob.correct()

    if caption == str(corrected):
        st.success("✅ No grammar issues")
    else:
        st.warning("⚠️ Grammar issues detected")
        grammar_ok = False

# ✅ Checklist
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

# 📌 USER CONFIRMATION
confirm = st.checkbox("I confirm all brand guidelines are followed")

st.divider()

# 🚀 SUBMIT
if st.button("Submit for Review"):

    if not name or not project or not uploaded_file or not caption:
        st.error("Fill all fields")
    elif not confirm:
        st.error("Please confirm guidelines compliance")
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

        # Default status
        status = "Pending ⏳"

        if score == total:
            st.success(f"Perfect ({score}/{total})")
        elif score >= total * 0.7:
            st.warning(f"Needs Fix ({score}/{total})")
        else:
            st.error(f"Not Approved ({score}/{total})")

        # SAVE
        sheet.append_row([
            name,
            project,
            f"{score}/{total}",
            status,
            "Yes",
            datetime.now().strftime("%Y-%m-%d %H:%M")
        ])

        st.success("Submitted for approval 🐝")

# 👨‍💼 ADMIN PANEL
st.divider()
st.subheader("👨‍💼 Admin Approval Panel")

if not df.empty:

    selected_index = st.selectbox("Select Submission", df.index)

    selected_row = df.iloc[selected_index]

    st.write(selected_row)

    if st.button("Approve ✅"):
        sheet.update_cell(selected_index+2, 4, "Approved ✅")
        st.success("Approved")

    if st.button("Reject ❌"):
        sheet.update_cell(selected_index+2, 4, "Rejected ❌")
        st.error("Rejected")
