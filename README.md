# MemCastle provider plugin template

Start a MemCastle provider plugin in its own repository.
A plugin can contain any number of Rust/Wasm **sources**, Bun **agent integrations** and Rust/Wasm
**embedding providers**, including none of any type.

This template combines the [source template](https://github.com/memcastle/memcastle-source.tpl)
the [integration template](https://github.com/memcastle/memcastle-integration.tpl)
and the [embedding-provider template](https://github.com/memcastle/memcastle-embedding-provider.tpl)
into one independently versioned plugin.

## Prerequisites

Install [git-tpl](https://noirbizarre.github.io/git-tpl/getting-started/installation/) 0.14.3 or newer and Git.

Building a generated provider also requires a plugin-capable MemCastle Core binary and the toolchains
for its selected modules (Rust 1.100+/`wasm32-wasip3` for sources and embeddings; Bun for integrations).
WASI modules require wasm-tools 1.263.0, Python 3.11+, and migrated development Core from commit `828f0f6`
or a descendant, using its Wasmtime 50.0.3 runtime.
Stable Core 0.5.2 predates the migration even though development currently reports the same version.
The `>=0.5, <0.6` default is transitional and cannot distinguish those binaries;
tighten it when the first compatible stable Core release is available.

## Get started

Choose a stable plugin ID (lowercase letters, digits and hyphens), then create a project:

```sh
git tpl --json questions https://github.com/memcastle/memcastle-plugin.tpl
git tpl init https://github.com/memcastle/memcastle-plugin.tpl my-provider \
  --init --trust --answer plugin_id=my-provider \
  --answer 'sources=["one"]' --answer 'integrations=["assistant"]' \
  --defaults --strict-answers --json
```

The published child templates are used by default.

To develop against sibling checkouts instead, use this repository as the first argument and supply
`--answer "source_template=$PWD/../memcastle-source.tpl"`
and `--answer "integration_template=$PWD/../memcastle-integration.tpl"`.
Use `--answer "embedding_template=$PWD/../memcastle-embedding-provider.tpl"` for a local embedding child.

Those local paths are recorded in the generated project's `.config/git.tpl.toml`;
prefer the published defaults for a repository shared with others.

The new project's [README](template/README.md.jinja) covers building and packaging the plugin.

After rendering, sources are in `sources/<id>/`, integrations in `integrations/<id>/`, embeddings in `embeddings/<id>/`,
and `plugin.toml` describes them.
An ID may appear in multiple lists without the modules sharing files or activation state.
Empty lists are valid.

The generated root README lists selected modules with links to their directories,
where GitHub displays each module's README alongside its files.
Root `mise.toml` exposes `build`, `test`, `lint`, and `format:check` for each module:
use `mise tasks ls` to discover tasks and, for example, `mise run source:one:test` to run native tests.
Namespaces are `source:<id>`, `integration:<id>`, and `embedding:<id>`, so IDs can overlap across types.
Install module dependencies first; Rust build tasks also require `jq` and copy the Wasm component
into its package-ready location.

## Template options

Pass options as repeated `--answer name=value` arguments to `git tpl init`.
List answers use JSON-style arrays (for example, `--answer 'sources=["one","two"]'`).
Omitted answers use the defaults below. `plugin_id` is the only required answer.

| Answer | Default | Purpose |
| --- | --- | --- |
| `plugin_id` | **Required** | Stable plugin ID: lowercase words, numbers and hyphens. |
| `description` | `A MemCastle provider plugin` | Short description in the generated README and descriptor. |
| `provider` | `plugin_id` | Provider family recorded in `plugin.toml`. |
| `memcastle` | `>=0.5, <0.6` | Supported Core version constraint in the descriptor. |
| `github_owner` | `memcastle` | Repository owner used in badges and metadata. |
| `repository_name` | `memcastle-<plugin_id>` | Repository name used in badges and metadata. |
| `registry` | `false` | Show one-command installation when listed in Core's reviewed plugin catalogue. |
| `sources` | `[]` | Source module IDs; each renders in `sources/<id>/`. |
| `integrations` | `[]` | Agent integration IDs; each renders in `integrations/<id>/`. |
| `embeddings` | `[]` | Embedding-provider IDs; each renders in `embeddings/<id>/`. |
| `source_template` | [memcastle-source.tpl] | Source child-template location; `main` is resolved when rendered. |
| `integration_template` | [memcastle-integration.tpl] | Integration child-template location; `main` is resolved when rendered. |
| `embedding_template` | [memcastle-embedding-provider.tpl] | Embedding child-template location; `main` is resolved when rendered. |
| `core_versions` | `["development"]` with WASI modules; otherwise `["development", "0.5"]` | Validate migrated development Core for WASI modules until a compatible stable release exists. |
| `codecov` | `false` | Enable Codecov coverage and test-result uploads. |
| `codecov_project_target` | `80%` | Overall coverage floor when `codecov` is enabled. |
| `codecov_patch_target` | `80%` | Changed-code coverage floor when `codecov` is enabled. |
| `codecov_source_target` | `80%` | Coverage floor for reporting sources when `codecov` is enabled. |
| `codecov_integration_target` | `80%` | Coverage floor for reporting integrations when `codecov` is enabled. |
| `codecov_covered_sources` | `[]` | Source IDs with nonempty LCOV uploads; only these get blocking component checks. |
| `codecov_covered_integrations` | `[]` | Integration IDs with LCOV uploads; only these block coverage. |
| `gh_ship` | `false` | Generate release PR automation instead of manual tag publishing. |
| `ship_token` | `app` | Authentication for gh-ship (`app` or `pat`); used only when `gh_ship` is enabled. |

`registry` refers to the reviewed plugin catalogue at
[`docs/plugins.json`](https://github.com/memcastle/memcastle/blob/main/docs/plugins.json),
not the legacy source registry.
The plugin must also have a published release for installation by ID to work.

Coverage targets are fixed percentages from 0% to 100%; the covered-ID lists
are chosen from the corresponding module IDs.
A plugin with `codecov = false` does not generate Codecov configuration.

The generated README explains repository setup for the selected release and coverage options.

[memcastle-source.tpl]: https://github.com/memcastle/memcastle-source.tpl
[memcastle-integration.tpl]: https://github.com/memcastle/memcastle-integration.tpl
[memcastle-embedding-provider.tpl]: https://github.com/memcastle/memcastle-embedding-provider.tpl

## Keep a project up to date

git-tpl records the exact resolved commits of the parent and child templates in the project.
Updates are explicit for existing plugins: new child `main` commits affect fresh renderings but never silently change
an existing plugin until its owner reviews and merges the updated recorded revisions.
The parent template CI checks each child's current `main` alongside its own rendering cases.
The source 0.5.0 and embedding 0.2.0 child migrations must land before this parent migration;
verify the generated project's recorded child revisions when accepting the update.

In a generated repository:

```sh
git tpl update --defaults --json
git tpl diff --json
git tpl merge --json
```

To add a module, first edit its `sources`, `integrations` or `embeddings` answer in `.config/git.tpl.toml`,
then update, review the diff and merge.

Existing providers using `modules/<id>/` can adopt the typed layout through that ordinary Git merge
while retaining their implementations.

## Development

To work on this template, keep the three child-template repositories checked out alongside it
and put migrated development Core, Rust 1.100 with `wasm32-wasip3`, wasm-tools 1.263.0,
Python 3.11+, Bun, mise and `jq` on your `PATH`.
The Core binary must support the migrated source/embedding contracts as well as plugin packaging and lifecycle tests.

Run the rendering and archive smoke tests with:

```sh
TEMPLATE_ROOT="$PWD" git tpl test --json
```

Check `summary.failed` in the JSON output (success is `0`).
The fixtures cover empty and mixed projects, typed modules, conditional CI, packaging and both release modes.
They validate actual WASI 0.3 imports and current MemCastle exports, run source conformance,
and execute embedding probes against the packaged component in an isolated daemon.
CI records the tested development Core SHA.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the template development workflow
and [AGENTS.md](AGENTS.md) for coding-agent guidance.
