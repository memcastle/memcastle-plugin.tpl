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
run `git tpl test`, then review the GitTPL diff in each provider repository before merging.
Existing projects retain their recorded commits until they explicitly run `git tpl update --defaults --json`,
review `git tpl diff --json`, and run `git tpl merge --json`.
`git tpl test` checks empty and mixed renders, typed modules, conditional CI and the pinned child composition.
`core_versions` selects a static Core validation matrix. It defaults to `main`; plugin-capable minor/major release
trees can be offered when stable binaries are published, with the Core setup action resolving their latest patch.
Put a Core binary with `plugin package` and `plugin test` on PATH before running it locally;
the empty and mixed cases build and smoke-test actual archives in disposable GitTPL sandboxes.
The template CI downloads the verified Core `main` development binary and installs Rust, `wasm32-wasip2` and Bun.

`ci.yaml` builds source components with reproducible Cargo flags and agent integrations with Bun, then runs
`memcastle plugin package plugin.toml` to write a deterministic release archive containing the generated
`manifest.toml` (descriptor metadata, version and every artifact checksum) and an external
`dist/ID-VERSION.sha256sum` for the archive. `plugin.toml` is never changed or archived.
Commit the regenerated `manifest.toml` and each source module's `Cargo.lock` for reproducible builds.
The resulting archive is the installation unit; neither source modules nor integration modules are separately fetched from the plugin registry.
The generated source and integration jobs format, lint and test each module separately.
The test jobs instrument only Rust library targets, preserve hidden integration assets and allow longer-lived
agent tests; a source-only plugin still runs Core validation when its integration matrix is skipped.
When a source and integration share an ID in an existing provider, the package job excludes the fixture component
from the integration assets and restores it for Core's source conformance check.
`memcastle plugin test dist/ID-VERSION.tar.gz` validates the archive in a disposable palace,
including preview, per-source consent, inactive installation and explicit source activation.
Agent integration registration and legacy adoption remain provider-specific tests.
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
Without gh-ship, tag `PLUGIN_ID/vVERSION` on a reviewed `main` commit to publish independently of Core releases.
Set the `codecov` answer to `true` to enable coverage and test-result uploads in the same `ci.yaml` workflow.
Each source and integration gets its own Cargo/Bun test job and Codecov flag, uploading actual LCOV and JUnit
reports using GitHub OIDC. Manifest-only suites upload JUnit without inventing coverage.
Enable the repository in Codecov for coverage and test-result PR statuses.

Set `gh_ship = true` to generate the automated release PR workflow instead of manual tag publishing.
Choose `ship_token = "app"` (default) for an installation token or `"pat"` for a fine-grained PAT.
git-cliff computes a version and changelog from Conventional Commits; gh-ship opens a reviewed `release/next` PR
and publishes the validated plugin archive after that PR merges. The generated README documents repository setup.
