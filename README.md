# MemCastle provider plugin template

One repository produces one independently versioned plugin, with zero or more source and integration modules.
The plugin template composes the independently maintained `memcastle-source.tpl` and `memcastle-integration.tpl` repositories.
Each child follows `main`; `.config/git.tpl.toml` and the rendered commit record its actual commit, not a copy of its skeleton.
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
The defaults then fetch the published child branches; the local-path example above records those machine-specific paths
instead and never silently changes them to the published URLs.

An empty `sources` or `integrations` answer is valid.
To add a module later, edit the recorded `sources` or `integrations` array in `.config/git.tpl.toml`, then run
`git tpl update --defaults` and `git tpl merge`; the rendered ref remains append-only.
When a child branch moves, `update` records its new commit and merges any module skeleton changes normally.
`git tpl test` checks empty and mixed renderings, and `python3 scripts/check_composition.py --build` checks recorded
commits, an added module, generated source builds and the packaged artifact using the released GitTPL 0.14 binary.

`python3 scripts/package.py` builds sources, computes every module artifact hash and produces a deterministic release archive.
It remaps local Rust and Cargo source paths and ignores a local compiler wrapper so the reviewed component hashes match CI.
Commit each generated source module's `Cargo.lock` after packaging; the provider CI requires them for reproducible builds.
The resulting archive is the installation unit; neither source modules nor integration modules are separately fetched from the plugin registry.
