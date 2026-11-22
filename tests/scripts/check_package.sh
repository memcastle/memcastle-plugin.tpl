#!/usr/bin/env bash
set -euo pipefail

core="$(command -v "${MEMCASTLE_BIN:-memcastle}")"
plugin="$1"
# The rendered command sandbox has no Git history; a project does after GitTPL init.
git init -q
git add .
git -c user.name='GitTPL test' -c user.email='git-tpl@example.invalid' commit -qm 'test: record rendered plugin'
"$core" plugin inspect --json > .plugin-test-inventory.json

for id in $(jq -r '.modules[] | select(.type == "source") | .id' .plugin-test-inventory.json); do
  module="$PWD/sources/$id"
  cargo generate-lockfile --manifest-path "$module/Cargo.toml"
  cargo_home="$(realpath "${CARGO_HOME:-$HOME/.cargo}")"
  sysroot="$(rustc --print sysroot)"
  commit="$(rustc --version --verbose | awk '/^commit-hash: / {print $2}')"
  export CARGO_BUILD_RUSTC_WRAPPER=
  unset RUSTFLAGS
  export CARGO_ENCODED_RUSTFLAGS="--remap-path-prefix=$cargo_home=/cargo"$'\x1f'"--remap-path-prefix=$sysroot/lib/rustlib/src/rust=/rustc/$commit"$'\x1f'"--remap-path-prefix=$module=/module"
  cargo build --manifest-path "$module/Cargo.toml" --locked --release --target wasm32-wasip3
  crate="$(cargo metadata --no-deps --format-version 1 --manifest-path "$module/Cargo.toml" | jq -er '.packages[0].targets[] | select(.kind | index("cdylib")) | .name')"
  cp "${CARGO_TARGET_DIR:-$module/target}/wasm32-wasip3/release/$crate.wasm" "$module/source.wasm"
  python3 scripts/validate_component.py source "$module/source.wasm"
  mkdir -p "$module/dist"
  cp "$module/source.wasm" "$module/dist/source.wasm"
  "$core" source test "$module" --no-build
done

for id in $(jq -r '.modules[] | select(.type == "integration") | .id' .plugin-test-inventory.json); do
  if [[ -f "integrations/$id/package.json" ]]; then
    (cd "integrations/$id" && bun install && bun run format:check && bun test && bun run build)
  fi
done

for id in $(jq -r '.modules[] | select(.type == "embedding_provider") | .id' .plugin-test-inventory.json); do
  module="$PWD/embeddings/$id"
  cargo generate-lockfile --manifest-path "$module/Cargo.toml"
  cargo test --manifest-path "$module/Cargo.toml" --locked --lib
  cargo build --manifest-path "$module/Cargo.toml" --locked --release --target wasm32-wasip3
  crate="$(cargo metadata --no-deps --format-version 1 --manifest-path "$module/Cargo.toml" | jq -er '.packages[0].targets[] | select(.kind | index("cdylib")) | .name')"
  cp "${CARGO_TARGET_DIR:-$module/target}/wasm32-wasip3/release/$crate.wasm" "$module/embedding.wasm"
  python3 scripts/validate_component.py embedding "$module/embedding.wasm"
done

before="$(sha256sum plugin.toml)"
"$core" plugin package --json > .plugin-test-package.json
test "$before" = "$(sha256sum plugin.toml)"
archive="$(jq -r .archive .plugin-test-package.json)"
checksum="$(jq -r .checksum .plugin-test-package.json)"
[[ "$archive" == "dist/$plugin-"*.tar.gz ]]
test "$checksum" = "${archive%.tar.gz}.sha256sum"
test ! -e manifest.toml
tar -tf "$archive" | grep '^manifest.toml$' >/dev/null
if tar -tf "$archive" | grep '^plugin.toml$' >/dev/null; then exit 1; fi
(cd dist && sha256sum --check "$(basename "$checksum")")
"$core" plugin test "$archive"
for id in $(jq -r '.modules[] | select(.type == "embedding_provider") | .id' .plugin-test-inventory.json); do
  python3 "embeddings/$id/tests/conformance.py" --archive "$archive" --plugin-id "$plugin" --module-id "$id"
done
first="$(sha256sum "$archive")"
"$core" plugin package --json > .plugin-test-package-again.json
test "$first" = "$(sha256sum "$archive")"
