from io import BytesIO
from zipfile import ZipFile

from audiobook_package import package_audiobook


def test_package_contains_document_and_audio():
    data = package_audiobook("report.pdf", b"%PDF-example", b"RIFF-example")
    with ZipFile(BytesIO(data)) as z:
        assert set(z.namelist()) == {"report.pdf", "report.wav"}
        assert z.read("report.pdf") == b"%PDF-example"
        assert z.read("report.wav") == b"RIFF-example"


def test_package_strips_parent_paths():
    data = package_audiobook("../../private/report.docx", b"doc", b"audio")
    with ZipFile(BytesIO(data)) as z:
        assert set(z.namelist()) == {"report.docx", "report.wav"}
