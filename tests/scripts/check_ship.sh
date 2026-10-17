#!/usr/bin/env bash
set -euo pipefail

plugin="$1"
git add plugin.toml cliff.toml
git commit -qm 'feat: initial plugin'
test "$(git cliff --bumped-version)" = "$plugin/v0.1.0"
git cliff --bump -o CHANGELOG.md
test -s CHANGELOG.md
git add CHANGELOG.md
git commit -qm 'chore(release): 0.1.0'
git tag "$plugin/v0.1.0"

printf 'corrected\n' > change.txt
git add change.txt
git commit -qm 'fix: correct indexing'
test "$(git cliff --bumped-version)" = "$plugin/v0.1.1"
git cliff --bump -o CHANGELOG.md
test -s CHANGELOG.md
git add CHANGELOG.md
git commit -qm 'chore(release): 0.1.1'
git tag "$plugin/v0.1.1"

test "$(git cliff --bumped-version)" = "$plugin/v0.1.1"
