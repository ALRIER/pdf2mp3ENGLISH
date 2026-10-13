"""Streamlit front-end for a CPU-first audiobook prototype."""
import streamlit as st

from pipeline import extract_document, split_text
from synthesis import synthesize_wav

st.set_page_config(page_title="PDF to Audiobook", page_icon="🎧")
st.title("PDF to Audiobook — Neural TTS")
st.caption("CPU-first prototype. Uploaded files are processed in memory; do not upload private documents to a public hosted app.")

file = st.file_uploader("Choose a document", type=["pdf", "docx", "txt"])
skip_tables = st.checkbox("Skip detected PDF tables", value=True)
skip_margins = st.checkbox("Skip PDF header/footer margins", value=True)
voice = st.selectbox("Narration voice", ["af_heart", "af_sky", "am_adam", "am_michael"])
speed = st.slider("Speech speed", 0.75, 1.5, 1.0, 0.05)

if file:
    try:
        text = extract_document(file.getvalue(), file.name, skip_tables, skip_margins)
        st.success(f"Extracted {len(text):,} characters")
        edited = st.text_area("Review and edit text before narration", text, height=300)
        segments = split_text(edited)
        st.caption(f"{len(segments)} synthesis chunks. Word highlighting requires a future alignment component.")
        if st.button("Generate WAV audio"):
            with st.spinner("Generating audio on CPU (first run downloads model weights)..."):
                wav = synthesize_wav(edited, voice=voice, speed=speed)
            st.audio(wav, format="audio/wav")
            st.download_button("Download audiobook WAV", wav, file_name="audiobook.wav", mime="audio/wav")
    except Exception as exc:
        st.error(f"Unable to process document: {exc}")
