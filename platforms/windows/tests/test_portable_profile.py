import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "source"))
from bridges.xiaomi.portable_profile import validate_profile
from bridges.xiaomi.xiaomi_config import default_config


class PortableProfileTests(unittest.TestCase):
    def fixture(self):
        return json.loads((Path(__file__).resolve().parents[3] / "profiles/windows/WQS.json").read_text(encoding="utf-8"))

    def test_wqs_is_optional_and_has_no_machine_identity(self):
        before = default_config()
        profile = validate_profile(self.fixture())
        self.assertEqual(profile["name"], "WQS")
        self.assertEqual(profile["button_bindings"]["mic"][0]["keys"], ["ctrl", "shift", "f9"])
        self.assertEqual(profile["button_bindings"]["menu"][0]["keys"], ["leftwin", "tab"])
        self.assertNotIn("address", profile)
        self.assertEqual(default_config(), before)

    def test_import_rejects_commands_and_invalid_voice(self):
        for change in ("command", "mode", "gain", "buttons"):
            value = copy.deepcopy(self.fixture())
            if change == "command":
                value["button_bindings"]["power"] = [{"type": "run", "command": "anything"}]
            elif change == "mode":
                value["voice"]["trigger_mode"] = "invalid"
            elif change == "gain":
                value["voice"]["gain_db"] = float("nan")
            else:
                del value["button_bindings"]["mic"]
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_profile(value)

    def test_machine_fields_are_not_exported(self):
        value = self.fixture()
        value["address"] = "00:11:22:33:44:55"
        self.assertNotIn("address", validate_profile(value))
