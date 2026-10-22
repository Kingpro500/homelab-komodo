#!/usr/bin/env bash
# Publish the network map from Git, never from an arbitrary working copy.
# Run on CT120, from the homelab-komodo checkout that backs `nettkart`.
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
map_rel='docs/network-map/nettverkskart.html'
live_map="$repo_root/$map_rel"
backup_dir='/var/lib/nettkart/backups'

version_of() {
  sed -n 's/.*versjon <b>\([0-9][0-9.]*\)<\/b>.*/\1/p' "$1" | head -n 1
}

version_key() {
  awk -F. '{ printf "%08d%08d\n", $1, $2 }' <<<"$1"
}

require_complete_layout() {
  local file="$1"
  grep -q 'Serviceoversikt' "$file" &&
    grep -q 'data-vmid=' "$file" &&
    grep -q 'NODE-SAMMENDRAGET' "$file" &&
    grep -q '9118/nodes' "$file"
}

git fetch --quiet origin main
stage="$(mktemp "$(dirname "$live_map")/.nettverkskart.XXXXXX")"
trap 'rm -f "$stage"' EXIT
git show "origin/main:$map_rel" >"$stage"

candidate_version="$(version_of "$stage")"
if [[ -z "$candidate_version" ]] || ! require_complete_layout "$stage"; then
  echo 'Refusing publish: Git candidate lacks a valid version or required map layout.' >&2
  exit 1
fi

if [[ -f "$live_map" ]]; then
  live_version="$(version_of "$live_map")"
  if [[ -n "$live_version" ]] && [[ "$(version_key "$candidate_version")" < "$(version_key "$live_version")" ]]; then
    echo "Refusing downgrade: live is v$live_version, Git candidate is v$candidate_version." >&2
    exit 1
  fi
fi

install -d -m 0750 "$backup_dir"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
if [[ -f "$live_map" ]]; then
  cp -p "$live_map" "$backup_dir/nettverkskart-${live_version:-unknown}-${timestamp}.html"
fi

chmod 0644 "$stage"
mv -f "$stage" "$live_map"
trap - EXIT
printf 'Published network map v%s from origin/main; previous live copy retained in %s.\n' \
  "$candidate_version" "$backup_dir"
