#!/usr/bin/env bash
set -euo pipefail

plugin="$1"
descriptor="$(sha256sum plugin.toml)"
git add plugin.toml cliff.toml
git commit -qm 'feat: initial plugin'
test "$(git cliff --bumped-version)" = "0.1.0"
git cliff --bump -o CHANGELOG.md
test -s CHANGELOG.md
git add CHANGELOG.md
git commit -qm 'chore(release): 0.1.0'
git tag "0.1.0"

printf 'corrected\n' > change.txt
git add change.txt
git commit -qm 'fix: correct indexing'
test "$(git cliff --bumped-version)" = "0.1.1"
git cliff --bump -o CHANGELOG.md
test -s CHANGELOG.md
test "$descriptor" = "$(sha256sum plugin.toml)"
git add CHANGELOG.md
git commit -qm 'chore(release): 0.1.1'
git tag "0.1.1"

test "$(git cliff --bumped-version)" = "0.1.1"
# Core tests tag inference separately; this fixture checks the release tag and archive format.
archive="$(memcastle plugin package --version 0.1.1 --json | jq -r .archive)"
test "$archive" = "dist/$plugin-0.1.1.tar.gz"
test ! -e manifest.toml
tar -xOzf "$archive" manifest.toml | grep -q '^version = "0.1.1"$'
