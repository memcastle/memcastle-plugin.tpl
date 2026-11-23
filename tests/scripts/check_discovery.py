"""Check generated module links and mise discovery in a rendered project."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tomllib


root = Path.cwd().resolve()
config_path = root / "mise.toml"
config = tomllib.loads(config_path.read_text())
plugin = tomllib.loads((root / "plugin.toml").read_text())
readme = (root / "README.md").read_text()
modules = plugin.get("modules", [])
operations = ("format:check", "lint", "test", "build")
namespaces = {"source": "source", "integration": "integration", "embedding_provider": "embedding"}
expected = {}
for module in modules:
    directory = Path(module["manifest"]).parent
    assert f'[{module["id"]}]({directory.as_posix()}/)' in readme, directory
    assert (root / directory).is_dir(), directory
    assert (root / directory / "README.md").is_file(), directory
    prefix = f'{namespaces[module["type"]]}:{module["id"]}'
    for operation in operations:
        expected[f"{prefix}:{operation}"] = root / directory

assert set(config.get("tasks", {})) == set(expected)
if not modules:
    assert "## Modules" not in readme
    assert "### Root module tasks" not in readme

# Trust only this disposable render, without changing the user's trust settings.
env = dict(os.environ, MISE_TRUSTED_CONFIG_PATHS=str(root), MISE_YES="1",
           MISE_CEILING_PATHS=str(root.parent))


def run(*command, cwd=root, extra_env=None):
    subprocess.run(command, cwd=cwd, env={**env, **(extra_env or {})}, check=True)


for cwd in (root, root / Path(modules[0]["manifest"]).parent if modules else root / ".github"):
    result = subprocess.check_output(["mise", "tasks", "ls", "--json"], cwd=cwd, env=env, text=True)
    tasks = {task["name"]: task for task in json.loads(result)
             if Path(task["source"]).resolve() == config_path}
    assert set(tasks) == set(expected), tasks.keys()
    for name, directory in expected.items():
        assert Path(tasks[name]["dir"]).resolve() == directory, (name, tasks[name]["dir"])

if "--run" in sys.argv:
    checked_types = set()
    for module in modules:
        if module["type"] in checked_types:
            continue
        checked_types.add(module["type"])
        directory = root / Path(module["manifest"]).parent
        if module["type"] == "integration":
            run("bun", "install", cwd=directory)
        else:
            run("cargo", "generate-lockfile", cwd=directory)
        prefix = f'{namespaces[module["type"]]}:{module["id"]}'
        for operation in operations:
            # Invoke from inside the module to exercise root discovery there too.
            # Also verify Cargo's target-directory override, including spaces.
            overrides = {"CARGO_TARGET_DIR": str(root / "custom target")} if operation == "build" else {}
            run("mise", "run", f"{prefix}:{operation}", cwd=directory, extra_env=overrides)
        assert (root / module["entry"]).is_file(), module["entry"]
