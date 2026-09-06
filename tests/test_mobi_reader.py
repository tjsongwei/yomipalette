import unittest
from pathlib import Path

from core.file_reader import load_chapters
from core.mobi_reader import read_mobi_file
from i18n import set_language, t


FIXTURES = Path(__file__).parent / "fixtures" / "mobi"


class MobiReaderTests(unittest.TestCase):
    def setUp(self):
        set_language("en")

    def test_plain_mobi_returns_single_chapter(self):
        chapters = read_mobi_file(str(FIXTURES / "plain.mobi"))

        self.assertEqual(1, len(chapters))
        self.assertEqual("plain", chapters[0].title)
        self.assertTrue(chapters[0].text.strip())

    def test_azw3_with_kf8_splits_by_chapters(self):
        chapters = read_mobi_file(str(FIXTURES / "kf8.azw3"))

        self.assertGreaterEqual(len(chapters), 3)
        joined = "\n".join(ch.text for ch in chapters)
        for needle in ("First chapter body.", "Second chapter body.", "Third chapter body."):
            self.assertIn(needle, joined)

    def test_load_chapters_dispatches_mobi_extensions(self):
        for name in ("plain.mobi", "kf8.azw3"):
            with self.subTest(name=name):
                chapters = load_chapters(str(FIXTURES / name))
                self.assertGreater(len(chapters), 0)

    def test_drm_file_raises_localized_error(self):
        from unittest.mock import patch

        from core import mobi_reader

        with patch.object(mobi_reader, "_detect_drm", return_value=True):
            with self.assertRaises(ValueError) as error:
                load_chapters(str(FIXTURES / "plain.mobi"))
            self.assertEqual(t("error.mobi_drm"), str(error.exception))


if __name__ == "__main__":
    unittest.main()
