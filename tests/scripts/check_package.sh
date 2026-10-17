#!/usr/bin/env bash
set -euo pipefail

command -v memcastle >/dev/null || { echo 'put a plugin-capable Core binary on PATH'; exit 1; }
plugin="$1"
# The rendered command sandbox has no Git history; a project does after GitTPL init.
git init -q
git add .
git -c user.name='GitTPL test' -c user.email='git-tpl@example.invalid' commit -qm 'test: record rendered plugin'
memcastle plugin inspect --json > .plugin-test-inventory.json

for id in $(jq -r '.modules[] | select(.type == "source") | .id' .plugin-test-inventory.json); do
  module="$PWD/modules/$id"
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
done

for id in $(jq -r '.modules[] | select(.type == "integration") | .id' .plugin-test-inventory.json); do
  if [[ -f "modules/$id/package.json" ]]; then
    (cd "modules/$id" && bun install && bun run format:check && bun test && bun run build)
  fi
done

before="$(sha256sum plugin.toml)"
memcastle plugin package --json > .plugin-test-package.json
test "$before" = "$(sha256sum plugin.toml)"
archive="$(jq -r .archive .plugin-test-package.json)"
checksum="$(jq -r .checksum .plugin-test-package.json)"
[[ "$archive" == "dist/$plugin-"*.tar.gz ]]
test "$checksum" = "${archive%.tar.gz}.sha256sum"
test ! -e manifest.toml
tar -tf "$archive" | grep '^manifest.toml$' >/dev/null
if tar -tf "$archive" | grep '^plugin.toml$' >/dev/null; then exit 1; fi
(cd dist && sha256sum --check "$(basename "$checksum")")
memcastle plugin test "$archive"
first="$(sha256sum "$archive")"
memcastle plugin package --json > .plugin-test-package-again.json
test "$first" = "$(sha256sum "$archive")"
