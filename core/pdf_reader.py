"""Extract embedded PDF text in physical page order; no OCR or outline parsing."""

from pypdf import PdfReader

from core.file_reader import Chapter, _clean_text
from i18n import t


class _PasswordRequired(Exception):
    pass


def read_pdf_file(path: str) -> list[Chapter]:
    chapters = []
    with open(path, "rb") as source:
        try:
            reader = PdfReader(source)
            if reader.is_encrypted and not reader.decrypt(""):
                raise _PasswordRequired
            for page_number, page in enumerate(reader.pages, 1):
                text = _clean_text(page.extract_text() or "")
                if text:
                    chapters.append(Chapter(
                        index=len(chapters) + 1,
                        title=f"Page {page_number:03d}",
                        text=text,
                    ))
        except _PasswordRequired as error:
            raise ValueError(t("error.pdf_password")) from error
        except Exception as error:
            raise ValueError(t("error.pdf_invalid")) from error
    if not chapters:
        raise ValueError(t("error.pdf_no_text"))
    return chapters
