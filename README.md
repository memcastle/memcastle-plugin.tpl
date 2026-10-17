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

`ci.yaml` builds source components with reproducible Cargo flags and agent integrations with Bun, then runs
`memcastle plugin package plugin.toml` to update hashes and write a deterministic release archive.
Commit each generated source module's `Cargo.lock` and reviewed manifest hashes; CI requires both for reproducible builds.
The resulting archive is the installation unit; neither source modules nor integration modules are separately fetched from the plugin registry.
The generated source and integration jobs format, lint and test each module separately.
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
Tag `PLUGIN_ID/vVERSION` on a reviewed `main` commit to publish just this provider, independently of Core releases.

Set the `codecov` answer to `true` to enable coverage and test-result uploads in the same `ci.yaml` workflow.
Each source and integration gets its own Cargo/Bun test job and Codecov flag, uploading actual LCOV and JUnit
reports using GitHub OIDC. Manifest-only suites upload JUnit without inventing coverage.
Enable the repository in Codecov for coverage and test-result PR statuses.
