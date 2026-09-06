"""TXT/EPUB/PDF/MOBI ファイルの読み込みとチャプター抽出"""

import re
from dataclasses import dataclass

import chardet
from i18n import t


@dataclass
class Chapter:
    index: int
    title: str
    text: str


def sanitize_filename(name: str, max_len: int = 60) -> str:
    name = re.sub(r'[\\/:*?"<>|\r\n\t]', "_", name).strip(" ._")
    if not name:
        name = "untitled"
    return name[:max_len]


def _clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" ?\n ?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def read_text_file(path: str) -> list[Chapter]:
    with open(path, "rb") as f:
        raw = f.read()
    detected = chardet.detect(raw)
    encoding = detected.get("encoding") or "utf-8"
    if encoding.lower() in ("shift_jis", "windows-1252"):
        for enc in ("utf-8", "cp932", encoding):
            try:
                text = raw.decode(enc)
                break
            except (UnicodeDecodeError, LookupError):
                continue
        else:
            text = raw.decode(encoding, errors="replace")
    else:
        try:
            text = raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            text = raw.decode("utf-8", errors="replace")

    title = path.replace("\\", "/").rsplit("/", 1)[-1]
    title = title.rsplit(".", 1)[0]
    return [Chapter(index=1, title=title, text=_clean_text(text))]


def _html_to_text(html_content: bytes | str) -> str:
    from bs4 import BeautifulSoup

    if isinstance(html_content, bytes):
        html_content = html_content.decode("utf-8", errors="replace")
    soup = BeautifulSoup(html_content, "lxml")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return _clean_text(soup.get_text("\n"))


def read_epub_file(path: str) -> list[Chapter]:
    from core.epub_reader import read_epub_sections

    return [Chapter(index=i, title=title, text=text)
            for i, (title, text) in enumerate(read_epub_sections(path), 1)]


def load_chapters(path: str) -> list[Chapter]:
    lower = path.lower()
    if lower.endswith(".epub"):
        chapters = read_epub_file(path)
    elif lower.endswith(".txt"):
        chapters = read_text_file(path)
    elif lower.endswith(".pdf"):
        from core.pdf_reader import read_pdf_file

        chapters = read_pdf_file(path)
    elif lower.endswith((".mobi", ".azw", ".azw3")):
        from core.mobi_reader import read_mobi_file

        chapters = read_mobi_file(path)
    else:
        raise ValueError(t("error.unsupported_file", path=path))
    if not chapters:
        raise ValueError(t("error.no_text", path=path))
    return chapters


def split_chapters_by_chars(chapters: list[Chapter], max_chars: int) -> list[Chapter]:
    """チャプター本文を文書順に連結し、指定文字数以内の部分に分割する。"""
    if not isinstance(max_chars, int) or isinstance(max_chars, bool) or max_chars <= 0:
        raise ValueError(t("error.invalid_chars"))

    full_text = "\n".join(chapter.text for chapter in chapters if chapter.text)
    if not full_text.strip():
        return []

    parts: list[Chapter] = []
    offset = 0
    while offset < len(full_text):
        remaining = len(full_text) - offset
        if remaining <= max_chars:
            end = len(full_text)
        else:
            window = full_text[offset : offset + max_chars]
            boundaries = list(re.finditer(r"[。．.!?！？\n]", window))
            end = offset + (boundaries[-1].end() if boundaries else max_chars)

        text = full_text[offset:end]
        if text.strip():
            index = len(parts) + 1
            parts.append(Chapter(index=index, title=f"Part {index:03d}", text=text))
        offset = end

    return parts
