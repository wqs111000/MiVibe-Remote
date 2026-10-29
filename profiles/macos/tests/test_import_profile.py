import copy
import importlib.util
import json
import plistlib
import subprocess
import sys
import unittest
import uuid
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('import_profile', ROOT / 'import-profile.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
PROFILE = json.loads((ROOT / 'WQS.json').read_text(encoding='utf-8'))


class ImportProfileTests(unittest.TestCase):
    def existing(self):
        preset = {key: copy.deepcopy(PROFILE[key]) for key in module.FIELDS}
        preset.update(id=str(uuid.uuid4()).upper(), name='已有预设')
        preset.pop('customVoiceShortcut')  # Swift omits nil optional fields.
        return preset

    def test_add_preserves_existing_and_creates_new_id(self):
        original = [self.existing()]
        saved = copy.deepcopy(original)
        result = module.prepare(PROFILE, original)
        self.assertEqual(result[0], saved[0])
        self.assertEqual(original, saved)
        self.assertNotEqual(result[1]['id'], result[0]['id'])
        self.assertEqual(result[1]['buttonBindings']['menu'], 'appSwitcher')

    def test_rejects_duplicates_and_invalid_bindings_without_writing(self):
        existing = self.existing()
        existing['name'] = 'wqs'
        with self.assertRaises(ValueError):
            module.prepare(PROFILE, [existing])
        bad = copy.deepcopy(PROFILE)
        bad['buttonBindings']['menu'] = 'notAnAction'
        with self.assertRaises(ValueError):
            module.prepare(bad, [])
        bad = copy.deepcopy(PROFILE)
        bad['buttonShortcuts']['tv']['keyCode'] = '45'
        with self.assertRaises(ValueError):
            module.prepare(bad, [])

    def test_existing_preset_requires_valid_id_and_decodable_fields(self):
        existing = self.existing()
        existing['id'] = 'bad-id'
        with self.assertRaises(ValueError):
            module.prepare(PROFILE, [existing])
        existing = self.existing()
        existing['buttonBindings']['menu'] = 'unknownAction'
        with self.assertRaises(ValueError):
            module.prepare(PROFILE, [existing])

    def test_import_writes_only_local_presets(self):
        existing = self.existing()
        prefs = plistlib.dumps({'localPresets': json.dumps([existing]).encode(),
                                'peripheralIdentifier': 'keep-private', 'gainDB': 12})
        writes = []
        def run(args, **kwargs):
            if args[0] == '/usr/bin/pgrep':
                return subprocess.CompletedProcess(args, 1)
            if args[1] == 'export':
                return subprocess.CompletedProcess(args, 0, stdout=prefs)
            writes.append(args)
            return subprocess.CompletedProcess(args, 0)
        with mock.patch.object(module.sys, 'platform', 'darwin'), \
             mock.patch.object(module.sys, 'argv', ['import-profile.py']), \
             mock.patch.object(module.subprocess, 'run', side_effect=run):
            module.main()
        self.assertEqual(len(writes), 1)
        self.assertEqual(writes[0][1:4], ['write', module.DOMAIN, 'localPresets'])
        decoded = json.loads(bytes.fromhex(writes[0][-1]))
        self.assertEqual(decoded[0], existing)
        self.assertEqual(decoded[1]['name'], 'WQS')
        self.assertNotIn('keep-private', repr(decoded))

    def test_running_app_blocks_before_read_or_write(self):
        with mock.patch.object(module.sys, 'platform', 'darwin'), \
             mock.patch.object(module.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)) as run:
            with self.assertRaises(ValueError):
                module.main()
        self.assertEqual(run.call_count, 1)


if __name__ == '__main__':
    unittest.main()
