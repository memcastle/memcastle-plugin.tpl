# MemCastle provider plugin template

One repository produces one independently versioned plugin, with zero or more source and integration modules.
The plugin template composes the independently maintained `memcastle-source.tpl` and `memcastle-integration.tpl` repositories at pinned commits; it does not carry their skeletons.

```sh
git tpl --json questions https://github.com/memcastle/memcastle-plugin.tpl
git tpl init https://github.com/memcastle/memcastle-plugin.tpl my-provider --init --answer plugin_id=my-provider --answer sources=one,two --answer integrations=assistant --defaults --strict-answers --trust --json
```

An empty `sources` or `integrations` answer is valid.
To add a module later, change the recorded answer in `.config/git.tpl.toml`, then run `git tpl update --defaults` and `git tpl merge`; the rendered ref remains append-only.
If the parent template's pinned child revision changes, updating the parent incorporates that module skeleton change with a normal Git merge.

`python3 scripts/package.py` builds sources, computes every module artifact hash and produces a deterministic release archive.
The resulting archive is the installation unit; neither source modules nor integration modules are separately fetched from the plugin registry.
