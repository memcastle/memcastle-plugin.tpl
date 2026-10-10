# MemCastle provider plugin template

One repository produces one independently versioned plugin, with zero or more source and integration modules.
The plugin template composes the independently maintained `memcastle-source.tpl` and `memcastle-integration.tpl` repositories at pinned commits; it does not carry their skeletons.

```sh
git tpl --json questions "$PWD"
git tpl init "$PWD" ../my-provider --init --answer plugin_id=my-provider \
  --answer sources=one,two --answer integrations=assistant \
  --answer "source_template=$PWD/../memcastle-source.tpl" \
  --answer "integration_template=$PWD/../memcastle-integration.tpl" \
  --defaults --strict-answers --json
```

After publication, use `https://github.com/memcastle/memcastle-plugin.tpl` and `--trust`
to fetch its pinned child template revisions from their published repositories.

An empty `sources` or `integrations` answer is valid.
To add a module later, change the recorded answer in `.config/git.tpl.toml`, then run `git tpl update --defaults` and `git tpl merge`; the rendered ref remains append-only.
If the parent template's pinned child revision changes, updating the parent incorporates that module skeleton change with a normal Git merge.

`python3 scripts/package.py` builds sources, computes every module artifact hash and produces a deterministic release archive.
Commit each generated source module's `Cargo.lock` after packaging; the provider CI requires them for reproducible builds.
The resulting archive is the installation unit; neither source modules nor integration modules are separately fetched from the plugin registry.
