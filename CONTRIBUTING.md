# Contributing to the plugin template

Thanks for helping improve MemCastle provider plugins!

This repository generates projects; changes here should make sense both for a new provider
and for an existing provider applying an update.

## Find the right place to edit

- `template.toml` defines questions, defaults and the source/integration child compositions.
- `template/` contains the rendered project's files.
  Jinja templates (`*.jinja`) can conditionally include documentation, workflows and metadata;
  the child templates supply the individual modules.
- `tests/*.toml` describes fixture answers and rendered-file expectations;
  `tests/scripts/` exercises packaged output.
- The root `README.md` documents this template and its answers;
  `template/README.md.jinja` becomes each provider's README.
  Keep both accurate when changing a question or a user-facing workflow.

When changing generated output, consider the empty, source-only, integration-only and mixed renders,
registry-listed and unlisted plugins, optional Codecov, and both gh-ship and manual release paths.

Source and integration IDs can be identical.
Keep provider-specific code in its child template rather than assuming it lives here.

## Run the checks

Place checkouts of `memcastle-source.tpl` and `memcastle-integration.tpl` beside this repository.
Install git-tpl 0.14.3 or newer, a MemCastle Core build supporting `plugin package` and `plugin test`,
Rust and its `wasm32-wasip2` target, Bun, and `jq`.

The template CI also uses git-cliff for release fixtures.

```sh
git tpl test --json
```

Read `summary.failed` in the result: it must be `0`.
The fixture suite renders different answer sets and exercises real package and smoke-test commands
in disposable projects.

Review a representative rendered README and guides when changing Jinja prose or conditions,
not just the template source.
Update fixture expectations when a documented feature or rendered path changes.

## Review downstream updates

git-tpl records the resolved child-template commits in each generated project's `.config/git.tpl.toml`.
To apply a change in a provider repository, review the generated diff before merging:

```sh
git tpl update --defaults --json
git tpl diff --json
git tpl merge --json
```

The update advances a rendered ref; only the merge applies it to the project.

An existing provider can keep custom code while resolving ordinary Git conflicts.
See [the README](README.md#keep-a-project-up-to-date) for adding modules and the complete option reference.
