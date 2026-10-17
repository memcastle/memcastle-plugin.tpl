#!/usr/bin/env bash
set -euo pipefail

: "${MEMCASTLE_BIN:?set MEMCASTLE_BIN to a plugin-capable Core binary}"
plugin="$1"
version="$2"
"$MEMCASTLE_BIN" plugin inspect plugin.toml --json > .plugin-test-inventory.json

for id in $(jq -r '.modules[] | select(.type == "source") | .id' .plugin-test-inventory.json); do
  module="$PWD/sources/$id"
  cargo generate-lockfile --manifest-path "$module/Cargo.toml"
  cargo_home="$(realpath "${CARGO_HOME:-$HOME/.cargo}")"
  sysroot="$(rustc --print sysroot)"
  commit="$(rustc --version --verbose | awk '/^commit-hash: / {print $2}')"
  export CARGO_BUILD_RUSTC_WRAPPER=
  unset RUSTFLAGS
  export CARGO_ENCODED_RUSTFLAGS="--remap-path-prefix=$cargo_home=/cargo"$'\x1f'"--remap-path-prefix=$sysroot/lib/rustlib/src/rust=/rustc/$commit"$'\x1f'"--remap-path-prefix=$module=/module"
  cargo build --manifest-path "$module/Cargo.toml" --locked --release --target wasm32-wasip2
  crate="$(cargo metadata --no-deps --format-version 1 --manifest-path "$module/Cargo.toml" | jq -er '.packages[0].targets[] | select(.kind | index("cdylib")) | .name')"
  cp "$module/target/wasm32-wasip2/release/$crate.wasm" "$module/source.wasm"
  mkdir -p "$module/dist"
  cp "$module/source.wasm" "$module/dist/source.wasm"
done

for id in $(jq -r '.modules[] | select(.type == "integration") | .id' .plugin-test-inventory.json); do
  if [[ -f "integrations/$id/package.json" ]]; then
    (cd "integrations/$id" && bun install && bun run format:check && bun test && bun run build)
  fi
done

before="$(sha256sum plugin.toml)"
"$MEMCASTLE_BIN" plugin package plugin.toml --json > .plugin-test-package.json
test "$before" = "$(sha256sum plugin.toml)"
archive="$(jq -r .archive .plugin-test-package.json)"
checksum="$(jq -r .checksum .plugin-test-package.json)"
test "$archive" = "dist/$plugin-$version.tar.gz"
test "$checksum" = "dist/$plugin-$version.sha256sum"
tar -tf "$archive" | grep '^manifest.toml$' >/dev/null
if tar -tf "$archive" | grep '^plugin.toml$' >/dev/null; then exit 1; fi
(cd dist && sha256sum --check "$plugin-$version.sha256sum")
"$MEMCASTLE_BIN" plugin test "$archive"
first="$(sha256sum "$archive")"
"$MEMCASTLE_BIN" plugin package plugin.toml --json > .plugin-test-package-again.json
test "$first" = "$(sha256sum "$archive")"
