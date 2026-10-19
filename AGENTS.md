# Agent guidance: plugin template

- Read `README.md` for template answers and `CONTRIBUTING.md` for the contribution workflow.
- Treat `template.toml` as the source of truth for questions, defaults and child composition.
  Edit `template/*.jinja` for generated prose and metadata;
  do not edit a rendered provider as a substitute.
- Three pinned child templates provide module implementations.
  `sources`, `integrations` and `embeddings` can each be empty, and IDs can overlap across types.
  Check all relevant conditional paths before adding unconditional claims.
- Keep template-only guidance here and provider guidance in `template/AGENTS.md.jinja`
  and `template/CONTRIBUTING.md.jinja`.
  Update both READMEs and affected `tests/*.toml` expectations when changing user-facing behavior.
- Run `git tpl test --json` and check `summary.failed == 0`.
  Its package fixtures require sibling child checkouts, a plugin-capable `memcastle`,
  Rust/`wasm32-wasip2`, Bun and `jq`; release fixtures also need git-cliff.
  Review empty, mixed, registry, Codecov and both release-mode renders after editing conditional documentation.
