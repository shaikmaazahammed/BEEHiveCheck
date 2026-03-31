import streamlit as st
from textblob import TextBlob

st.set_page_config(page_title="BEEHiveCheck", layout="wide")

# 🖤 Minimal Black UI
st.markdown("""
<style>
.stApp { background-color: #0e0e0e; color: white; }

h1, h2, h3 {
    color: white;
}

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

# 📤 Upload
uploaded_file = st.file_uploader(
    "Upload Content",
    type=["png", "jpg", "jpeg", "mp4"]
)

# ✍️ Caption
caption = st.text_area("Caption")

grammar_ok = True
tone_label = "Unknown"

# 🧠 Language Analysis
if caption:
    st.subheader("🧠 Language Analysis")

    blob = TextBlob(caption)

    # ✍️ Grammar / spelling suggestion
    corrected = blob.correct()

    if caption == str(corrected):
        st.success("✅ Caption looks clean")
        grammar_ok = True
    else:
        st.warning("⚠️ Suggested improvement:")

        st.text_area("Improved Caption", str(corrected), height=100)
        grammar_ok = False

    # 🎭 Tone Detection
    polarity = blob.sentiment.polarity

    if polarity > 0.3:
        tone_label = "Friendly 😊"
    elif polarity < -0.2:
        tone_label = "Formal 😐"
    else:
        tone_label = "Neutral 🤝"

    st.info(f"🎭 Tone: {tone_label}")

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

    st.markdown("**Tone Match")
    tone_check = st.checkbox("Matches brand tone")

st.divider()

# 🚀 Submit Logic
if st.button("Submit for Review"):

    if not uploaded_file or not caption:
        st.error("❌ Please upload content and write a caption.")
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

        st.subheader("📊 Result")

        if score == total:
            st.success(f"✅ Perfect ({score}/{total}) — Ready to post 🚀")
        elif score >= total * 0.7:
            st.warning(f"⚠️ Good ({score}/{total}) — Minor fixes needed")
        else:
            st.error(f"❌ Not approved ({score}/{total}) — Fix before posting")
