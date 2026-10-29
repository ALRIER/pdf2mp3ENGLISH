"""Streamlit front-end for a CPU-first audiobook prototype."""
from __future__ import annotations

import hashlib

from audiobook_package import package_audiobook

import streamlit as st

from pipeline import extract_document, split_text
from synthesis import synthesize_wav
from reader import show_reader

st.set_page_config(page_title="PDF to Audiobook", page_icon="🎧")
st.title("PDF to Audiobook — Neural TTS")
st.caption("CPU-first prototype. Uploaded files are processed in memory; do not upload private documents to a public hosted app.")


@st.cache_data(show_spinner=False, max_entries=8)
def cached_extract_document(data: bytes, name: str, skip_tables: bool,
                            skip_margins: bool) -> str:
    """Avoid re-parsing an unchanged upload on every Streamlit rerun."""
    return extract_document(data, name, skip_tables, skip_margins)


file = st.file_uploader("Choose a document", type=["pdf", "docx", "txt"])
skip_tables = st.checkbox("Skip detected PDF tables", value=True)
skip_margins = st.checkbox("Skip PDF header/footer margins", value=True)
voice = st.selectbox("Narration voice", ["af_heart", "af_sky", "am_adam", "am_michael"])
speed = st.slider("Speech speed", 0.75, 1.5, 1.0, 0.05)

if file:
    try:
        data = file.getvalue()
        document_id = hashlib.sha256(data).hexdigest()

        # Never let audio/timings from a previous upload leak into a new document.
        if st.session_state.get("document_id") != document_id:
            st.session_state["document_id"] = document_id
            st.session_state.pop("audiobook_wav", None)
            st.session_state.pop("audiobook_words", None)
            st.session_state.pop("audio_document_id", None)

        with st.spinner("Reading document..."):
            text = cached_extract_document(
                data, file.name, skip_tables, skip_margins
            )

        st.success(f"Extracted {len(text):,} characters")
        edited = st.text_area("Review and edit text before narration", text, height=300, key=f"edited_{document_id}_{skip_tables}_{skip_margins}")
        segments = split_text(edited)
        st.caption(f"{len(segments)} synthesis chunks. Word highlighting is available after audio generation.")

        generation_id = hashlib.sha256(
            repr((document_id, edited, voice, speed)).encode("utf-8")
        ).hexdigest()
        if st.button("Generate WAV audio", type="primary"):
            st.info("Audio generation started. The player and downloads will appear when it finishes.")
            with st.status("Generating narration...", expanded=True) as status:
                st.write("Loading the voice model (this step cannot report percentage).")
                progress = st.progress(0, text="Preparing model...")
                def report_progress(completed: int, total: int) -> None:
                    progress.progress(
                        completed / total,
                        text=f"Narrating section {completed} of {total} ({completed / total:.0%})",
                    )
                wav = synthesize_wav(
                    edited, voice=voice, speed=speed, on_progress=report_progress
                )
                progress.progress(1.0, text="Audio generation complete.")
                st.session_state["audiobook_wav"] = wav
                st.session_state["audio_document_id"] = document_id
                st.session_state["audio_generation_id"] = generation_id
                st.session_state.pop("audiobook_words", None)
                status.update(label="Narration ready", state="complete", expanded=False)
            st.success("Audio is ready. Play it below or download the package.")

        if (
            st.session_state.get("audiobook_wav")
            and st.session_state.get("audio_document_id") == document_id
            and st.session_state.get("audio_generation_id") == generation_id
        ):
            wav = st.session_state["audiobook_wav"]
            st.audio(wav, format="audio/wav")
            st.download_button(
                "Download audiobook WAV",
                wav,
                file_name="audiobook.wav",
                mime="audio/wav",
            )
            st.download_button(
                "Download document + audio (ZIP)",
                package_audiobook(file.name, data, wav),
                file_name=f"{file.name.rsplit('.', 1)[0]}_audiobook.zip",
                mime="application/zip",
            )
        elif st.session_state.get("audiobook_wav"):
            st.info("Document, text, or voice settings changed. Generate audio again to match the current version.")
    except Exception as exc:
        message = str(exc)
        if "Hub" in message or "cache" in message or "Connection" in message or "huggingface" in message.lower():
            st.error("The document was extracted, but the Kokoro model could not be loaded from Hugging Face. Check the server internet connection and model access, then retry. Once downloaded, the model is cached for subsequent uses on the same server.")
            st.caption(f"Technical detail: {type(exc).__name__}: {message[:300]}")
        else:
            st.error(f"Unable to process document: {exc}")

if (
    file
    and st.session_state.get("audiobook_wav")
    and st.session_state.get("audio_document_id") == st.session_state.get("document_id")
):
    st.subheader("Synchronized reader (experimental)")
    st.caption("Word times come from CPU speech recognition, so the highlighted transcript may differ from original text.")
    if st.button("Analyze word timings"):
        try:
            from alignment import recognize_word_timestamps
            with st.spinner("Extracting word timestamps on CPU..."):
                st.session_state["audiobook_words"] = recognize_word_timestamps(
                    st.session_state["audiobook_wav"]
                )
        except Exception as exc:
            st.error(f"Alignment failed: {exc}")
    if st.session_state.get("audiobook_words"):
        show_reader(
            st.session_state["audiobook_wav"],
            st.session_state["audiobook_words"],
        )
