"""Read MOBI / AZW / AZW3 files and return chapter text.

DRM-protected files raise ValueError with a localized message.
AZW3 with embedded KF8 (EPUB) reuses the EPUB reader to preserve its
chapter structure. Older MOBI / AZW files are returned as a single chapter
because the format does not expose a reliable table of contents.
"""

import os
import shutil
import struct

from i18n import t

from core.file_reader import Chapter, _html_to_text


def _detect_drm(path: str) -> bool:
    """Return True if the file is a MOBI variant carrying a DRM payload."""
    from mobi.kindleunpack import Sectionizer
    from mobi.mobi_header import MobiHeader, unpackException

    try:
        sect = Sectionizer(path)
    except Exception:
        return False
    if sect.ident not in (b"BOOKMOBI", b"TEXtREAd"):
        return False
    try:
        header = MobiHeader(sect, 0)
    except (unpackException, struct.error):
        return False
    return bool(header.isEncrypted())


def _is_kf8_epub(path: str) -> bool:
    """Return True if the extracted output is a KF8 EPUB inside AZW3."""
    return path.lower().endswith(".epub")


def _read_html_chapter(html_path: str, base_title: str) -> list[Chapter]:
    with open(html_path, "r", encoding="utf-8", errors="replace") as source:
        html_content = source.read()
    text = _html_to_text(html_content)
    if not text:
        return []
    return [Chapter(index=1, title=base_title, text=text)]


def _read_kf8_epub(epub_path: str, base_title: str) -> list[Chapter]:
    """Extract chapters from a KF8 EPUB embedded in an AZW3 file."""
    from core.epub_reader import read_epub_sections

    sections = read_epub_sections(epub_path)
    if not sections:
        return []
    chapters = []
    for index, (title, text) in enumerate(sections, 1):
        chapter_title = title or f"Chapter {index:03d}"
        chapters.append(Chapter(index=index, title=chapter_title, text=text))
    if not chapters:
        return [Chapter(index=1, title=base_title, text="")]
    return chapters


def read_mobi_file(path: str) -> list[Chapter]:
    if _detect_drm(path):
        raise ValueError(t("error.mobi_drm"))

    base_title = os.path.splitext(os.path.basename(path))[0]

    # mobi.extract returns (tempdir, output_path) where output_path is an
    # EPUB for KF8/AZW3, a single HTML for older MOBI/AZW, or a PDF for
    # print-replica files. The library creates the tempdir itself.
    from mobi import extract

    tempdir, output_path = extract(path)
    try:
        if _is_kf8_epub(output_path):
            chapters = _read_kf8_epub(output_path, base_title)
        elif output_path.lower().endswith((".html", ".xhtml", ".htm")):
            chapters = _read_html_chapter(output_path, base_title)
        else:
            # PDF print replica: best-effort single-chapter fallback.
            try:
                with open(output_path, "rb") as source:
                    raw = source.read()
                text = _html_to_text(raw)
                chapters = [Chapter(index=1, title=base_title, text=text)] if text else []
            except OSError:
                chapters = []
    finally:
        shutil.rmtree(tempdir, ignore_errors=True)

    if not chapters:
        raise ValueError(t("error.no_text", path=path))
    return chapters
