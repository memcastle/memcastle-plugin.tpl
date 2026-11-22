# Agent guidance: plugin template

- Read `README.md` for template answers and `CONTRIBUTING.md` for the contribution workflow.
- Treat `template.toml` as the source of truth for questions, defaults and child composition.
  Edit `template/*.jinja` for generated prose and metadata;
  do not edit a rendered provider as a substitute.
- Three independently maintained child templates provide module implementations.
  `sources`, `integrations` and `embeddings` can each be empty, and IDs can overlap across types.
  Check all relevant conditional paths before adding unconditional claims.
- Keep template-only guidance here and provider guidance in `template/AGENTS.md.jinja`
  and `template/CONTRIBUTING.md.jinja`.
  Update both READMEs and affected `tests/*.toml` expectations when changing user-facing behavior.
- Run `git tpl test --json` and check `summary.failed == 0`.
  Set `TEMPLATE_ROOT="$PWD"` when invoking the suite.
  Its package fixtures require all three sibling child checkouts and migrated development Core (`828f0f6` or later),
  Rust 1.100/`wasm32-wasip3`, wasm-tools 1.263.0, Python 3.11+, Bun and `jq`; release fixtures also need git-cliff.
  Source 0.5.0 and embedding 0.2.0 child changes must land before the parent; preserve exact resolved rendering locks.
  Review empty, mixed, registry, Codecov and both release-mode renders after editing conditional documentation.
