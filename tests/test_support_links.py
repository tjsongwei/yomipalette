import unittest
from unittest.mock import Mock, patch

from core.app_info import SUPPORT_LINKS
from gui.app import TTSApp


class SupportLinkTests(unittest.TestCase):
    def test_services_and_urls_are_declared_in_display_order(self):
        self.assertEqual(
            SUPPORT_LINKS,
            (
                ("GitHub Sponsors", "https://github.com/sponsors/tjsongwei"),
                ("Buy Me a Coffee", "https://buymeacoffee.com/tjsongweic"),
            ),
        )

    def test_each_support_url_is_sent_to_the_browser(self):
        app = object.__new__(TTSApp)
        app._show_support_open_failed = Mock()

        with patch("gui.app.webbrowser.open", return_value=True) as browser:
            for _label, url in SUPPORT_LINKS:
                app._open_support_url(url)

        self.assertEqual(
            [call.args[0] for call in browser.call_args_list],
            [url for _label, url in SUPPORT_LINKS],
        )
        app._show_support_open_failed.assert_not_called()

    def test_failed_browser_open_shows_the_selected_url(self):
        app = object.__new__(TTSApp)
        app._show_support_open_failed = Mock()
        selected_url = SUPPORT_LINKS[1][1]

        with patch("gui.app.webbrowser.open", return_value=False):
            app._open_support_url(selected_url)

        app._show_support_open_failed.assert_called_once_with(selected_url)
