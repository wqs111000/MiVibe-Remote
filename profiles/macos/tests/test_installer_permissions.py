import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
POSTINSTALL = ROOT / 'platforms/macos/packaging/doubao-driver/install/postinstall'


class InstallerPermissionsTests(unittest.TestCase):
    def test_normalization_preserves_executable_helpers_and_nonexecutable_resources(self):
        lines = POSTINSTALL.read_text().splitlines()
        commands = [line for line in lines if line.startswith('/usr/bin/find "$APP_DESTINATION" -type f')]
        self.assertEqual(len(commands), 1)
        with tempfile.TemporaryDirectory() as temp:
            app = Path(temp) / 'MiVibe Remote.app'
            helper = app / 'Contents/Frameworks/Sparkle.framework/Versions/B/Autoupdate'
            resource = app / 'Contents/Resources/README.md'
            helper.parent.mkdir(parents=True)
            resource.parent.mkdir(parents=True)
            helper.write_text('executable')
            resource.write_text('resource')
            helper.chmod(0o755)
            resource.chmod(0o644)
            env = dict(os.environ, APP_DESTINATION=str(app))
            subprocess.run(['/bin/zsh', '-c', commands[0]], env=env, check=True)
            self.assertEqual(stat.S_IMODE(helper.stat().st_mode), 0o755)
            self.assertEqual(stat.S_IMODE(resource.stat().st_mode), 0o644)


if __name__ == '__main__':
    unittest.main()
