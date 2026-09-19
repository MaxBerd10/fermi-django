from apps.content.management.commands.import_legacy_pages import LegacyDocumentFinder


def test_finder_matches_url_encoded_apostrophe_to_legacy_backtick_filename(tmp_path):
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    document = uploads / "Yo`l xaritasi.pdf"
    document.write_bytes(b"%PDF-1.4")

    finder = LegacyDocumentFinder(str(uploads))

    assert finder.find("https://api.fermi.uz/uploads/Yo%E2%80%98l%20xaritasi.pdf") == str(document)


def test_finder_refuses_ambiguous_filename(tmp_path):
    uploads = tmp_path / "uploads"
    (uploads / "one").mkdir(parents=True)
    (uploads / "two").mkdir()
    (uploads / "one" / "nizom.pdf").write_bytes(b"%PDF-1.4")
    (uploads / "two" / "nizom.pdf").write_bytes(b"%PDF-1.4")

    finder = LegacyDocumentFinder(str(uploads))

    assert finder.find("https://api.fermi.uz/uploads/nizom.pdf") is None


def test_finder_ignores_non_pdf_files(tmp_path):
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    (uploads / "qollanma.docx").write_bytes(b"not a PDF")

    finder = LegacyDocumentFinder(str(uploads))

    assert finder.find("https://api.fermi.uz/uploads/qollanma.docx") is None
