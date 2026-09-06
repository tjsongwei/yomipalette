import tempfile
import unittest
from pathlib import Path

from core.file_reader import load_chapters, split_chapters_by_chars
from i18n import set_language, t

FIXTURES = Path(__file__).parent / 'fixtures' / 'pdf'


class PdfReaderTests(unittest.TestCase):
    def setUp(self):
        set_language('en')

    def test_page_order_unicode_and_empty_pages(self):
        chapters = load_chapters(str(FIXTURES / 'text-pages.pdf'))
        self.assertEqual([1, 2, 3], [c.index for c in chapters])
        self.assertEqual(['Page 001', 'Page 003', 'Page 005'], [c.title for c in chapters])
        self.assertEqual(['First page text.', '日本語の本文です。', 'Last page text.'],
                         [c.text for c in chapters])
        parts = split_chapters_by_chars(chapters, 10)
        self.assertEqual('\n'.join(c.text for c in chapters), ''.join(c.text for c in parts))
        self.assertTrue(all(len(c.text) <= 10 for c in parts))

    def test_uppercase_extension(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'book.PDF'
            target.write_bytes((FIXTURES / 'text-pages.pdf').read_bytes())
            self.assertEqual(3, len(load_chapters(str(target))))

    def test_image_only_explains_ocr(self):
        with self.assertRaisesRegex(ValueError, 'OCR'):
            load_chapters(str(FIXTURES / 'image-only.pdf'))

    def test_password_required(self):
        with self.assertRaises(ValueError) as error:
            load_chapters(str(FIXTURES / 'password.pdf'))
        self.assertEqual(t('error.pdf_password'), str(error.exception))

    def test_empty_password_can_be_opened(self):
        self.assertEqual(3, len(load_chapters(str(FIXTURES / 'empty-password.pdf'))))

    def test_invalid_pdf_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'broken.pdf'
            target.write_bytes(b'%PDF-1.7\nnot a valid PDF')
            with self.assertRaises(ValueError) as error:
                load_chapters(str(target))
            self.assertEqual(t('error.pdf_invalid'), str(error.exception))
