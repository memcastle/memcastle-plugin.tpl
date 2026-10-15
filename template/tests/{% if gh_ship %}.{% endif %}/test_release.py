"""Exercise the release artifact generator without publishing a tag or pushing a branch."""

from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/prepare_release.py"


class ReleasePreparationTests(unittest.TestCase):
    def test_a_fix_bumps_the_plugin_tag_and_release_only_commits_are_ignored(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "scripts").mkdir()
            script = root / "scripts/prepare_release.py"
            shutil.copyfile(SCRIPT, script)
            def git(*args):
                return subprocess.check_output(("git", *args), cwd=root, text=True).strip()

            git("init", "-q")
            git("config", "user.name", "Release Test")
            git("config", "user.email", "release@example.invalid")
            (root / "plugin.toml").write_text('[plugin]\nid = "example"\nversion = "0.1.0"\n')
            git("add", "plugin.toml")
            git("commit", "-qm", "feat: initial plugin")
            subprocess.run((sys.executable, str(script)), cwd=root, check=True, capture_output=True)
            self.assertEqual(json.loads((root / "ship.release.json").read_text())["tag"], "example/v0.1.0")
            self.assertIn("## example/v0.1.0", (root / "CHANGELOG.md").read_text())
            git("add", "CHANGELOG.md")
            git("commit", "-qm", "chore(release): 0.1.0")
            git("tag", "example/v0.1.0")
            (root / "change.txt").write_text("corrected\n")
            git("add", "change.txt")
            git("commit", "-qm", "fix: correct indexing")

            subprocess.run((sys.executable, str(script)), cwd=root, check=True, capture_output=True)
            artifact = json.loads((root / "ship.release.json").read_text())
            self.assertEqual(artifact["tag"], "example/v0.1.1")
            self.assertIn("fix: correct indexing", artifact["release"]["notes"])
            self.assertIn("## example/v0.1.1", (root / "CHANGELOG.md").read_text())
            self.assertIn('version = "0.1.1"', (root / "plugin.toml").read_text())

            git("add", "plugin.toml", "CHANGELOG.md")
            git("commit", "-qm", "chore(release): 0.1.1")
            git("tag", "example/v0.1.1")
            subprocess.run((sys.executable, str(script)), cwd=root, check=True, capture_output=True)
            self.assertEqual(json.loads((root / "ship.release.json").read_text()),
                             {"schemaVersion": 1, "changed": False})


if __name__ == "__main__":
    unittest.main()
