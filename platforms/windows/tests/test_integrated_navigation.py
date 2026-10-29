"""Exercise the shared settings model without touching the user's devices or files."""

from pathlib import Path
import sys
import tkinter as tk
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "source"
sys.path.insert(0, str(SOURCE))

from bridges.xiaomi.xiaomi_config import default_config, default_keys_config
from standalone.xiaomi_main import XiaomiApp


class IntegratedNavigationTests(unittest.TestCase):
    def test_navigation_preserves_edits_and_saves_shared_voice_settings(self):
        with patch("bridges.xiaomi.xiaomi_settings.load_config", side_effect=default_config), \
             patch("bridges.xiaomi.xiaomi_settings.load_keys_config", side_effect=default_keys_config), \
             patch("bridges.xiaomi.xiaomi_settings.save_config") as save_config, \
             patch("bridges.xiaomi.xiaomi_settings.save_keys_config"), \
             patch("bridges.xiaomi.xiaomi_settings.send_hub_restart", return_value=123), \
             patch("bridges.xiaomi.xiaomi_settings.messagebox.showinfo"):
            root = tk.Tk()
            root.geometry("1100x700")
            app = XiaomiApp.__new__(XiaomiApp)
            app.root = root
            app._settings_panel = None
            app._current_page = "home"
            app._maintenance_running = False
            app.status_var = tk.StringVar(value="test")
            app.detail_var = tk.StringVar(value="")
            app.config_var = tk.StringVar(value="")
            app._build_ui()
            app._build_maintenance()
            try:
                root.update()
                app._navigate("keys")
                root.update()
                panel = app._settings_panel
                for widget in (panel.canvas, panel.capture_button, panel.voice_mode_combo,
                               panel.compact_gain_entry, panel.add_preset_button):
                    self.assertTrue(widget.winfo_ismapped())
                    self.assertLessEqual(widget.winfo_rooty() + widget.winfo_height(),
                                         root.winfo_rooty() + root.winfo_height())
                    self.assertLessEqual(widget.winfo_rootx() + widget.winfo_width(),
                                         root.winfo_rootx() + root.winfo_width())
                panel.edit_voice_shortcut()
                self.assertEqual(panel.selected_id, "mic")
                panel.gain_db.set("12.5")
                app._navigate("keys")
                root.update()
                app._navigate("home")
                app._navigate("keys")
                root.update()
                self.assertIs(panel, app._settings_panel)
                self.assertEqual(panel.gain_db.get(), "12.5")
                self.assertEqual(len([w for w in root.winfo_children() if isinstance(w, tk.Toplevel)]), 0)
                panel.voice_enabled.set(False)
                panel.voice_trigger_mode.set("开关型")
                panel.apply_wechat_preset()
                panel.apply_codex_preset()
                self.assertFalse(panel.voice_enabled.get())
                self.assertEqual(panel.voice_trigger_mode.get(), "开关型")
                panel.save()
                self.assertEqual(save_config.call_args.args[0]["gain_db"], 12.5)
                with patch("standalone.log_view.display_log", return_value="MIC ON test"):
                    app._navigate("logs")
                    root.update()
                    self.assertEqual(app.logs_page.text.get("1.0", "end-1c"), "MIC ON test")
                    app._navigate("keys")
                    self.assertIsNone(app.logs_page._timer)
                    self.assertIs(panel, app._settings_panel)
                address = panel.config.get("address")
                wqs = Path(__file__).resolve().parents[3] / "profiles/windows/WQS.json"
                with patch("bridges.xiaomi.xiaomi_settings.filedialog.askopenfilename", return_value=str(wqs)):
                    panel.import_profile()
                self.assertEqual(panel.config.get("address"), address)
                self.assertEqual(panel.working_custom_presets[panel.working_preset]["name"], "WQS")
                self.assertEqual(panel._current_voice_hotkey(), "ctrl+shift+f9")
                self.assertEqual(panel.voice_trigger_mode.get(), "按住型")
                self.assertEqual(panel.working_bindings["menu"][0]["keys"], ["leftwin", "tab"])
                panel.save()
                self.assertEqual(save_config.call_args.args[0]["active_preset"], panel.working_preset)
            finally:
                root.destroy()


if __name__ == "__main__":
    unittest.main()
