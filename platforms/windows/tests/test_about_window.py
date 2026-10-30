from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock


WINDOWS = Path(__file__).resolve().parents[1]
SOURCE = WINDOWS / "source"
if str(SOURCE) not in sys.path:
    sys.path.insert(0, str(SOURCE))

from standalone.about_window import (
    AboutWindow,
    about_window_size,
)


class AboutWindowTests(unittest.TestCase):
    def test_repeated_show_activates_existing_toplevel(self) -> None:
        existing = mock.Mock()
        existing.winfo_exists.return_value = 1
        about = AboutWindow(
            mock.Mock(),
            "MiVibe Remote",
            "0.1.18",
            mock.Mock(),
            mock.Mock(),
        )
        about.window = existing
        with mock.patch.object(about, "_build") as build:
            about.show()
        build.assert_not_called()
        existing.deiconify.assert_called_once_with()
        existing.lift.assert_called_once_with()
        existing.focus_force.assert_called_once_with()

    def test_preferred_size_is_constrained_to_the_screen(self) -> None:
        self.assertEqual(about_window_size(1920, 1080), (680, 700))
        self.assertEqual(about_window_size(640, 480), (592, 384))
        self.assertEqual(about_window_size(300, 300), (300, 300))
        with self.assertRaises(ValueError):
            about_window_size(0, 1080)

    def test_windows_host_and_spec_expose_about_entry_and_assets(self) -> None:
        host = (SOURCE / "standalone" / "xiaomi_main.py").read_text(
            encoding="utf-8"
        )
        about = (SOURCE / "standalone" / "about_window.py").read_text(
            encoding="utf-8"
        )
        spec = (SOURCE / "XiaomiRemoteBridge.spec").read_text(encoding="utf-8")
        self.assertIn('text="关于"', host)
        self.assertIn('"关于 MiVibe Remote"', host)
        self.assertNotIn("AUTHOR_LINE", host)
        self.assertNotIn("self.about.show()", host)
        self.assertIn('text="检查更新"', about)
        self.assertIn('text="关闭"', about)
        self.assertNotIn("AuthorDouyin.jpg", spec)
        self.assertNotIn("AuthorXiaohongshu.jpg", spec)


if __name__ == "__main__":
    unittest.main()
