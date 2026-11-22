# Contributing to the plugin template

Thanks for helping improve MemCastle provider plugins!

This repository generates projects; changes here should make sense both for a new provider
and for an existing provider applying an update.

## Find the right place to edit

- `template.toml` defines questions, defaults and the source/integration/embedding child compositions.
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

Place checkouts of `memcastle-source.tpl`, `memcastle-integration.tpl`, and `memcastle-embedding-provider.tpl`
beside this repository.
Install git-tpl 0.14.3 or newer, migrated development Core from `828f0f6` or a descendant,
Rust 1.100 and its `wasm32-wasip3` target, wasm-tools 1.263.0, Python 3.11+, Bun, mise, and `jq`.
Stable Core 0.5.2 is incompatible with the new components despite matching the transitional SemVer range.
Use the updated source 0.5.0 and embedding 0.2.0 child revisions before validating the parent.

The template CI also uses git-cliff for release fixtures.

```sh
TEMPLATE_ROOT="$PWD" git tpl test --json
```

Read `summary.failed` in the result: it must be `0`.
The fixture suite renders different answer sets and exercises real package and smoke-test commands
in disposable projects.
Component checks include WASI 0.3 validation, source execution, and embedding execution against an isolated Core daemon.
Embedding native tests additionally check exact sample vectors and batch ordering.

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
