import streamlit as st
import language_tool_python
from textblob import TextBlob

st.set_page_config(page_title="Bee Content Review", layout="wide")

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
</style>
""", unsafe_allow_html=True)

st.title("🐝 Bee Content Review")
st.markdown("Smart content validation system")

st.divider()

# Upload
uploaded_file = st.file_uploader("Upload Content", type=["png","jpg","jpeg","mp4"])
caption = st.text_area("Caption")

tool = language_tool_python.LanguageTool('en-US')

grammar_ok = True
tone_label = "Unknown"

if caption:
    st.subheader("🧠 Language Analysis")

    matches = tool.check(caption)

    if len(matches) == 0:
        st.success("✅ No grammar issues")
        grammar_ok = True
    else:
        grammar_ok = False
        st.warning(f"⚠️ {len(matches)} issue(s) found")

        for match in matches[:3]:
            st.write(f"• {match.message}")

    corrected = tool.correct(caption)

    if st.button("✨ Auto Fix Caption"):
        st.text_area("Improved Caption", corrected)

    blob = TextBlob(caption)
    polarity = blob.sentiment.polarity

    if polarity > 0.3:
        tone_label = "Friendly 😊"
    elif polarity < -0.2:
        tone_label = "Formal 😐"
    else:
        tone_label = "Neutral 🤝"

    st.info(f"🎭 Tone: {tone_label}")

st.divider()

# Checklist
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

if st.button("Submit"):
    if not uploaded_file or not caption:
        st.error("Upload content and add caption")
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

        st.subheader("Result")

        if score == total:
            st.success(f"Perfect ({score}/{total}) 🚀")
        elif score >= total * 0.7:
            st.warning(f"Needs improvement ({score}/{total})")
        else:
            st.error(f"Not approved ({score}/{total})")
