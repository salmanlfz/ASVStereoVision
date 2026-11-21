#!/usr/bin/env bash
set -euo pipefail

worlds="$1/vrx_gz/worlds"
mapfile -t urls < <(grep -ohE 'https://fuel\.gazebosim\.org/[^< ]+' \
  "$worlds"/{ls1,ls2,ls3_lurus,ls3_zigzag}.sdf | sort -u)
if (( ${#urls[@]} == 0 )); then
  echo "Tidak menemukan URL model Fuel di empat arena." >&2
  exit 1
fi

for url in "${urls[@]}"; do
  printf 'Mengunduh model %s\n' "$url"
  timeout 300 gz fuel download -u "$url"
done
