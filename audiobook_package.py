"""Create an in-memory download with the document and generated narration."""
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def package_audiobook(filename: str, document: bytes, audio: bytes) -> bytes:
    name = Path(filename.replace("\\", "/")).name
    if not name or name in {".", ".."}:
        name = "document.pdf"
    stem = Path(name).stem or "document"
    buffer = BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr(name, document)
        archive.writestr(f"{stem}.wav", audio)
    return buffer.getvalue()
