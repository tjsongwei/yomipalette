"""Generate small synthetic MOBI / AZW3 fixtures (requires Calibre's
ebook-convert on PATH). The input EPUB is built from scratch so the fixtures
stay under a few KB and are easy to regenerate.
"""

import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).parent
EPUB = ROOT / "_source.epub"
PLAIN_MOBI = ROOT / "plain.mobi"
KF8_AZW3 = ROOT / "kf8.azw3"


CONTAINER = """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""

CONTENT_OPF = """<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="bookid">urn:uuid:fixture-mobi-reader</dc:identifier>
    <dc:title>Fixture</dc:title>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="ch2" href="ch2.xhtml" media-type="application/xhtml+xml"/>
    <item id="ch3" href="ch3.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="ch1"/>
    <itemref idref="ch2"/>
    <itemref idref="ch3"/>
  </spine>
</package>
"""


def _chapter(title: str, body: str) -> str:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
  <head><title>{title}</title></head>
  <body>
    <h1>{title}</h1>
    <p>{body}</p>
  </body>
</html>
"""


CHAPTERS = [
    ("Chapter 1", "First chapter body."),
    ("Chapter 2", "Second chapter body."),
    ("Chapter 3", "Third chapter body."),
]


def _build_epub(target: Path) -> None:
    if target.exists():
        target.unlink()
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        archive.writestr("META-INF/container.xml", CONTAINER)
        archive.writestr("OEBPS/content.opf", CONTENT_OPF)
        for index, (title, body) in enumerate(CHAPTERS, 1):
            archive.writestr(f"OEBPS/ch{index}.xhtml", _chapter(title, body))


def _convert(src: Path, dst: Path) -> None:
    binary = shutil.which("ebook-convert")
    if binary is None:
        sys.exit("ebook-convert (Calibre) is required to regenerate MOBI/AZW3 fixtures.")
    if dst.exists():
        dst.unlink()
    subprocess.run([binary, str(src), str(dst)], check=True, stdout=subprocess.DEVNULL)


def main() -> None:
    with tempfile.TemporaryDirectory() as temp:
        source = Path(temp) / "source.epub"
        _build_epub(source)
        _convert(source, PLAIN_MOBI)
        _convert(source, KF8_AZW3)
    if EPUB.exists():
        EPUB.unlink()


if __name__ == "__main__":
    main()
