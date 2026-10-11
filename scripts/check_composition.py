#!/usr/bin/env python3
"""Exercise the released GitTPL compose/update contract with these three real template repositories."""

import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import hashlib
import json


PARENT = Path(__file__).resolve().parents[1]
SOURCE = PARENT.parent / "memcastle-source.tpl"
INTEGRATION = PARENT.parent / "memcastle-integration.tpl"
GIT_TPL = os.environ.get("GIT_TPL_BIN", "git-tpl")


def run(*args: str, cwd: Path, env: dict[str, str]) -> str:
    return subprocess.run(args, cwd=cwd, env=env, check=True, text=True, capture_output=True).stdout.strip()


def main() -> None:
    for child in (SOURCE, INTEGRATION):
        if not (child / "template.toml").is_file():
            raise RuntimeError(f"clone {child.name} beside {PARENT.name} before testing composition")
    version = run(GIT_TPL, "--version", cwd=PARENT, env=os.environ.copy()).split()[-1]
    if tuple(map(int, version.split(".")[:2])) < (0, 14):
        raise RuntimeError(f"GitTPL 0.14 or newer is required, found {version}")
    with tempfile.TemporaryDirectory(prefix="memcastle-compose-") as temporary:
        root = Path(temporary)
        project = root / "provider"
        env = dict(os.environ, XDG_CONFIG_HOME=str(root / "config"), GIT_AUTHOR_NAME="Template Test",
                   GIT_AUTHOR_EMAIL="test@example.invalid", GIT_COMMITTER_NAME="Template Test",
                   GIT_COMMITTER_EMAIL="test@example.invalid")
        run(GIT_TPL, "init", str(PARENT), str(project), "--init", "--defaults", "--strict-answers",
            "--answer", "plugin_id=example", "--answer", 'sources=["jira"]',
            "--answer", 'integrations=["assistant"]', "--answer", f"source_template={SOURCE}",
            "--answer", f"integration_template={INTEGRATION}", cwd=PARENT, env=env)
        config_file = project / ".config/git.tpl.toml"
        config = tomllib.loads(config_file.read_text())
        composed = {child["from"]: child for child in config["composed"]}
        for name, repo in (("sources", SOURCE), ("integrations", INTEGRATION)):
            assert composed[name]["ref"] == "main"
            assert composed[name]["commit"] == run("git", "rev-parse", "HEAD", cwd=repo, env=env)
        assert (project / "modules/jira/memcastle-source.toml").is_file()
        assert (project / "modules/assistant/memcastle-integration.toml").is_file()
        duplicate = subprocess.run(
            [GIT_TPL, "--json", "render", str(PARENT), "-o", str(root / "duplicate"), "--defaults",
             "--answer", "plugin_id=example", "--answer", 'sources=["assistant"]',
             "--answer", 'integrations=["assistant"]', "--answer", f"source_template={SOURCE}",
             "--answer", f"integration_template={INTEGRATION}"],
            cwd=PARENT, env=env, text=True, capture_output=True,
        )
        assert duplicate.returncode != 0 and "tpl::compose::invalid" in duplicate.stdout + duplicate.stderr
        assert not (root / "duplicate").exists()
        config_file.write_text(config_file.read_text().replace('sources = ["jira"]', 'sources = ["jira", "confluence"]'))
        run("git", "add", ".config/git.tpl.toml", cwd=project, env=env)
        run("git", "commit", "-m", "Add a source module", cwd=project, env=env)
        run(GIT_TPL, "update", "--defaults", cwd=project, env=env)
        run(GIT_TPL, "merge", cwd=project, env=env)
        assert (project / "modules/confluence/memcastle-source.toml").is_file()
        if "--build" in sys.argv[1:]:
            run(sys.executable, "scripts/package.py", cwd=project, env=env)
            run(sys.executable, "-m", "unittest", "discover", "-s", "tests", cwd=project, env=env)
            with tarfile.open(project / "dist/example-0.1.0.tar.gz", "r:gz") as archive:
                manifest = tomllib.loads(archive.extractfile("plugin.toml").read().decode())
                assert len(manifest["modules"]) == 3
                for module in manifest["modules"]:
                    for path, key in ((module["manifest"], "manifest_sha256"), (module["entry"], "sha256")):
                        assert hashlib.sha256(archive.extractfile(path).read()).hexdigest() == module[key]
            if core := os.environ.get("MEMCASTLE_BIN"):
                # Local Core from this PR validates the generated archive without starting a daemon or using a registry.
                key = root / "test-only-signing.key"
                run(core, "source", "keygen", str(key), cwd=project, env=env)
                signed = json.loads(run(core, "--json", "plugin", "sign", "--key", str(key),
                                        str(project / "dist/example-0.1.0.tar.gz"), cwd=project, env=env))
                assert signed["sha256"] == hashlib.sha256((project / "dist/example-0.1.0.tar.gz").read_bytes()).hexdigest()
        print("GitTPL 0.14 composed init, recorded commits, and module update/merge passed")


if __name__ == "__main__":
    main()
