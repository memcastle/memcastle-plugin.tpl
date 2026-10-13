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
    result = subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(f"{' '.join(args)} failed ({result.returncode}):\n{result.stdout}\n{result.stderr}")
    return result.stdout.strip()


def main() -> None:
    for child in (SOURCE, INTEGRATION):
        if not (child / "template.toml").is_file():
            raise RuntimeError(f"clone {child.name} beside {PARENT.name} before testing composition")
    version = run(GIT_TPL, "--version", cwd=PARENT, env=os.environ.copy()).split()[-1]
    if tuple(map(int, version.split(".")[:2])) < (0, 14):
        raise RuntimeError(f"GitTPL 0.14 or newer is required, found {version}")
    pins = {item["from"]: item["ref"] for item in tomllib.loads((PARENT / "template.toml").read_text())["compose"]}
    for name, repo in (("sources", SOURCE), ("integrations", INTEGRATION)):
        if pins[name] != run("git", "rev-parse", "HEAD", cwd=repo, env=os.environ.copy()):
            raise RuntimeError(f"{name} checkout must match the pinned child revision {pins[name]}")
    with tempfile.TemporaryDirectory(prefix="memcastle-compose-") as temporary:
        root = Path(temporary)
        project = root / "provider"
        env = dict(os.environ, XDG_CONFIG_HOME=str(root / "config"), GIT_AUTHOR_NAME="Template Test",
                   GIT_AUTHOR_EMAIL="test@example.invalid", GIT_COMMITTER_NAME="Template Test",
                   GIT_COMMITTER_EMAIL="test@example.invalid")
        identity = root / "config/git/config"
        identity.parent.mkdir(parents=True)
        # Libgit2 reads this file, not the Git author environment variables, when creating the rendered ref.
        identity.write_text("[user]\n\tname = Template Test\n\temail = test@example.invalid\n")
        result = json.loads(run(GIT_TPL, "--json", "init", str(PARENT), str(project), "--init", "--defaults", "--strict-answers",
            "--answer", "plugin_id=example", "--answer", 'sources=["jira"]',
            "--answer", 'integrations=["assistant"]', "--answer", f"source_template={SOURCE}",
            "--answer", f"integration_template={INTEGRATION}", cwd=PARENT, env=env))
        assert result["ok"]
        config_file = project / ".config/git.tpl.toml"
        config = tomllib.loads(config_file.read_text())
        composed = {child["from"]: child for child in config["composed"]}
        for name, repo in (("sources", SOURCE), ("integrations", INTEGRATION)):
            assert composed[name]["ref"] == pins[name]
            assert composed[name]["commit"] == pins[name]
        assert (project / "modules/jira/memcastle-source.toml").is_file()
        assert (project / "modules/assistant/memcastle-integration.toml").is_file()
        for workflow in ("plugin.yml", "release.yml"):
            content = (project / ".github/workflows" / workflow).read_text()
            if workflow == "plugin.yml":
                assert "memcastle/memcastle/.github/workflows/plugin-validation.yaml@main" in content
                assert "archive-path: ${{ needs.package.outputs.archive }}" in content
                assert "core-versions: '[]'" in content
            else:
                assert "uses: ./.github/workflows/plugin.yml" in content
                assert "gh release create" in content
            assert "latest_core_release" not in content
        duplicate = subprocess.run(
            [GIT_TPL, "--json", "render", str(PARENT), "-o", str(root / "duplicate"), "--defaults",
             "--answer", "plugin_id=example", "--answer", 'sources=["assistant"]',
             "--answer", 'integrations=["assistant"]', "--answer", f"source_template={SOURCE}",
             "--answer", f"integration_template={INTEGRATION}"],
            cwd=PARENT, env=env, text=True, capture_output=True,
        )
        assert duplicate.returncode != 0 and json.loads(duplicate.stdout)["error"]["code"] == "tpl::compose::invalid"
        assert not (root / "duplicate").exists()
        config_file.write_text(config_file.read_text().replace('sources = ["jira"]', 'sources = ["jira", "confluence"]'))
        run("git", "add", ".config/git.tpl.toml", cwd=project, env=env)
        run("git", "commit", "-m", "Add a source module", cwd=project, env=env)
        assert json.loads(run(GIT_TPL, "--json", "update", "--defaults", cwd=project, env=env))["ok"]
        assert json.loads(run(GIT_TPL, "--json", "merge", cwd=project, env=env))["ok"]
        assert (project / "modules/confluence/memcastle-source.toml").is_file()
        assert {child["from"]: child["commit"] for child in tomllib.loads(config_file.read_text())["composed"]} == pins
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
                run(sys.executable, "scripts/smoke_install.py", cwd=project, env=dict(env, MEMCASTLE_BIN=core))
        print("GitTPL 0.14 composed init, recorded commits, and module update/merge passed")


if __name__ == "__main__":
    main()
