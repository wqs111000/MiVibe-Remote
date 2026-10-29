from pathlib import Path
import sys
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "source"))
from standalone.log_view import display_log, LogPanel


class LogViewTests(unittest.TestCase):
    def test_filter_reads_only_selected_category_without_changing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            content = "READY remote=test\nBRIDGE ERROR timeout\nMIC ON session=1\n"
            (root / "bridge.log").write_text(content, encoding="utf-8")
            self.assertEqual(display_log(root, "按键与语音"), content)
            self.assertEqual(display_log(root, "按键与语音", True), "BRIDGE ERROR timeout")
            self.assertIn("暂无日志", display_log(root, "音频"))
            self.assertEqual((root / "bridge.log").read_text(encoding="utf-8"), content)

    def test_panel_refresh_copy_and_timer_lifecycle(self):
        root = tk.Tk()
        try:
            with patch("standalone.log_view.display_log", return_value="BRIDGE ERROR test"):
                panel = LogPanel(root, Path("unused"))
                panel.pack(fill="both", expand=True)
                panel.start()
                root.update()
                self.assertEqual(panel.text.get("1.0", "end-1c"), "BRIDGE ERROR test")
                self.assertEqual(str(panel.text["state"]), "disabled")
                panel.copy()
                self.assertEqual(root.clipboard_get(), "BRIDGE ERROR test")
                panel.stop()
                self.assertIsNone(panel._timer)
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
