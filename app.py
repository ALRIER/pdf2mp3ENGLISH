"""Streamlit front-end for a CPU-first audiobook prototype."""
import streamlit as st

from pipeline import extract_document, split_text
from synthesis import synthesize_wav
from reader import show_reader

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
            st.session_state['audiobook_wav'] = wav
            st.session_state.pop('audiobook_words', None)
            st.audio(wav, format="audio/wav")
            st.download_button("Download audiobook WAV", wav, file_name="audiobook.wav", mime="audio/wav")
    except Exception as exc:
        st.error(f"Unable to process document: {exc}")

if 'audiobook_wav' in st.session_state:
    st.subheader('Synchronized reader (experimental)')
    st.caption('Word times come from CPU speech recognition, so the highlighted transcript may differ from original text.')
    if st.button('Analyze word timings'):
        try:
            from alignment import recognize_word_timestamps
            with st.spinner('Extracting word timestamps on CPU...'):
                st.session_state['audiobook_words'] = recognize_word_timestamps(st.session_state['audiobook_wav'])
        except Exception as exc:
            st.error(f'Alignment failed: {exc}')
    if st.session_state.get('audiobook_words'):
        show_reader(st.session_state['audiobook_wav'], st.session_state['audiobook_words'])
