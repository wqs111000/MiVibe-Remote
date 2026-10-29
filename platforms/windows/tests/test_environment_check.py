from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "source"
sys.path.insert(0, str(SOURCE))

from standalone.environment_check import evaluate_environment, voice_bridge_is_ready, voice_session_feedback, BridgeLogReader


class EnvironmentCheckTests(unittest.TestCase):
    def test_long_session_keeps_current_readiness_and_resets_on_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bridge.log"
            status = {"bridge_alive": True, "audio_alive": True, "bridge_log_marker": "new-generation"}
            path.write_text("old-generation\nREADY remote=old\nnew-generation\nREADY remote=new\n" + "noise\n" * 60000, encoding="utf-8")
            reader = BridgeLogReader()
            self.assertTrue(voice_bridge_is_ready(reader.read(path, status), status))
            with path.open("a", encoding="utf-8") as stream:
                stream.write("BRIDGE ERROR disconnected\n")
            self.assertFalse(voice_bridge_is_ready(reader.read(path, status), status))
            status["bridge_log_marker"] = "next-generation"
            self.assertFalse(voice_bridge_is_ready(reader.read(path, status), status))

    def test_new_worker_does_not_inherit_old_ready_state(self):
        status = {"bridge_alive": True, "audio_alive": True, "bridge_log_marker": "generation-new"}
        self.assertFalse(voice_bridge_is_ready("READY remote=old\ngeneration-new\n", status))
        self.assertTrue(voice_bridge_is_ready("READY remote=old\ngeneration-new\nREADY remote=new", status))
        self.assertFalse(voice_bridge_is_ready("READY remote=old", status))

    def test_audio_feedback_does_not_claim_transcription(self):
        status = {"bridge_alive": True, "audio_alive": True}
        title, _ = voice_session_feedback("READY remote=new", status)
        self.assertIn("等待按键测试", title)
        title, _ = voice_session_feedback("MIC ON session=1", status)
        self.assertIn("正在接收", title)
        title, detail = voice_session_feedback("MIC ON session=1\nMIC OFF session=1 result=signal", status)
        self.assertEqual(title, "已收到遥控器声音")
        self.assertIn("没有文字", detail)

    def _fixture(self):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        (root / "support").mkdir()
        (root / "support" / "configure-xiaomi-audio.ps1").write_text(
            "# fixture", encoding="utf-8"
        )
        config = root / "xiaomi.json"
        config.write_text(json.dumps({"voice_hotkey": ["ctrl", "win"]}), encoding="utf-8")
        logs = root / "logs"
        logs.mkdir()
        (logs / "bridge.log").write_text(
            "XIAOMI HID TAP READY pid=1234\nREADY remote=MI RC audio_router=127.0.0.1", encoding="utf-8"
        )
        return temporary, root, config, logs

    def test_ready_environment_passes_all_core_checks(self) -> None:
        temporary, root, config, logs = self._fixture()
        self.addCleanup(temporary.cleanup)
        results = evaluate_environment(
            app_dir=root,
            config_path=config,
            log_dir=logs,
            worker_status={"bridge_alive": True, "audio_alive": True},
            audio_devices=[
                {"name": "CABLE Input (VB-Audio Virtual Cable)", "max_output_channels": 2},
                {"name": "CABLE Output (VB-Audio Virtual Cable)", "max_input_channels": 2},
            ],
            platform_name="Windows",
            platform_release="11",
        )

        by_key = {item.key: item for item in results}
        self.assertEqual(by_key["vb_cable"].status, "pass")
        self.assertEqual(by_key["workers"].status, "pass")
        self.assertEqual(by_key["remote"].status, "pass")
        self.assertEqual(by_key["voice_bridge"].status, "pass")
        self.assertFalse([item for item in results if item.status == "fail"])

    def test_missing_capture_endpoint_produces_actionable_failure(self) -> None:
        temporary, root, config, logs = self._fixture()
        self.addCleanup(temporary.cleanup)
        results = evaluate_environment(
            app_dir=root,
            config_path=config,
            log_dir=logs,
            worker_status={"bridge_alive": True, "audio_alive": True},
            audio_devices=[
                {"name": "CABLE Input (VB-Audio Virtual Cable)", "max_output_channels": 2},
            ],
            platform_name="Windows",
            platform_release="10",
        )

        cable = next(item for item in results if item.key == "vb_cable")
        self.assertEqual(cable.status, "fail")
        self.assertIn("CABLE Output", cable.detail)
        self.assertIn("安装/修复语音驱动", cable.action)

    def test_connection_does_not_imply_voice_ready_after_router_failure(self) -> None:
        temporary, root, config, logs = self._fixture()
        self.addCleanup(temporary.cleanup)
        (logs / "bridge.log").write_text(
            "READY remote=old\nCONNECTED remote=new\nATVV DISCOVERED\n"
            "BRIDGE ERROR TimeoutError: central audio router did not become ready\n",
            encoding="utf-8",
        )
        results = evaluate_environment(
            app_dir=root, config_path=config, log_dir=logs,
            worker_status={"bridge_alive": True, "audio_alive": False},
            audio_devices=[], platform_name="Windows", platform_release="11",
        )
        by_key = {item.key: item for item in results}
        self.assertEqual(by_key["remote"].status, "pass")
        self.assertEqual(by_key["voice_bridge"].status, "warn")
        self.assertEqual(by_key["vb_cable"].status, "fail")

    def test_stopped_bridge_cannot_use_old_success_log(self) -> None:
        temporary, root, config, logs = self._fixture()
        self.addCleanup(temporary.cleanup)
        results = evaluate_environment(
            app_dir=root, config_path=config, log_dir=logs,
            worker_status={"bridge_alive": False, "audio_alive": True},
            audio_devices=[], platform_name="Windows", platform_release="11",
        )
        by_key = {item.key: item for item in results}
        self.assertEqual(by_key["remote"].status, "warn")
        self.assertEqual(by_key["voice_bridge"].status, "warn")


if __name__ == "__main__":
    unittest.main()
