# MemCastle provider plugin template

One repository produces one independently versioned plugin, with zero or more source and integration modules.
The plugin template composes the independently maintained `memcastle-source.tpl` and `memcastle-integration.tpl` repositories.
Each child is pinned to a reviewed commit in `template.toml`; `.config/git.tpl.toml` records those exact revisions.
GitTPL 0.14 or newer is required for the `type = "list"` questions and `[[compose]]` declarations.

```sh
git tpl --json questions "$PWD"
git tpl init "$PWD" ../my-provider --init --answer plugin_id=my-provider \
  --answer 'sources=["one","two"]' --answer 'integrations=["assistant"]' \
  --answer "source_template=$PWD/../memcastle-source.tpl" \
  --answer "integration_template=$PWD/../memcastle-integration.tpl" \
  --defaults --strict-answers --json
```

For a shared provider repository, start with `https://github.com/memcastle/memcastle-plugin.tpl` and `--trust`.
The defaults fetch the pinned published child commits; the local-path example above records those machine-specific paths
instead and never silently changes them to the published URLs.

An empty `sources` or `integrations` answer is valid.
To add a module later, edit the recorded `sources` or `integrations` array in `.config/git.tpl.toml`, then run
`git tpl update --defaults` and `git tpl merge`; the rendered ref remains append-only.
To advance a child, test and commit it first, update its full SHA in `template.toml` and the template CI checkouts,
run the parent composition test, then review the GitTPL diff in each provider repository before merging.
Existing projects retain their recorded commits until they explicitly run `git tpl update --defaults --json`,
review `git tpl diff --json`, and run `git tpl merge --json`.
`git tpl test` checks empty and mixed renderings, and `python3 scripts/check_composition.py --build` checks recorded
commits, an added module, generated source builds and the packaged artifact using the released GitTPL 0.14 binary.

`python3 scripts/package.py` builds sources, computes every module artifact hash and produces a deterministic release archive.
It remaps local Rust and Cargo source paths and ignores a local compiler wrapper so the reviewed component hashes match CI.
Commit each generated source module's `Cargo.lock` after packaging; the provider CI requires them for reproducible builds.
The resulting archive is the installation unit; neither source modules nor integration modules are separately fetched from the plugin registry.
The generated `scripts/check_modules.py` formats/lints/tests this provider's source and agent modules independently.
`MEMCASTLE_BIN=/path/to/memcastle python3 scripts/smoke_install.py` validates the built archive in a disposable palace,
including preview, per-source consent, inactive installation, explicit activation and local agent integration installation.
Generated validation workflows call MemCastle Core's shared artifact-testing workflow.
They run once for every pull request and for every push to `main`, including merges; branch pushes to open PRs do not
trigger a second build.
Each provider owns the build, packaging and release jobs in its repository;
the release workflow reuses its provider-specific validation before publishing.
Their Core matrix always includes the permanent `main` prerelease, whose source SHA is recorded in its release body,
and can add exact plugin-capable stable versions via the `core-versions` JSON array.
Every matrix leg runs source fixtures and the archive installation/activation smoke test; Core 0.4.1 predates plugin
installation and is therefore not a compatible matrix entry.
The generated workflows retain provider-specific scripts and metadata; Core owns the host download and integration checks.
Generated workflows follow Core's `main` branch, so improvements to shared validation need no template update.
Core contract CI separately tests a generated project against the current Core checkout.
Tag `PLUGIN_ID/vVERSION` on a reviewed `main` commit to publish just this provider, independently of Core releases.

Set the `codecov` answer to `true` to generate a separate coverage workflow and Codecov configuration.
It measures native Rust source-module tests and Bun integration suites declaring `test:cover`, then uploads
the actual LCOV reports with GitHub OIDC; modules without an instrumented suite are skipped.
The coverage job needs `id-token: write` and Codecov must be enabled for the repository.
