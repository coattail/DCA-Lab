#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
DATA_DIR="$ROOT_DIR/web/data"

mkdir -p "$DATA_DIR"

validate_csv() {
  local path="$1"
  [[ -f "$path" ]] || return 1
  head -n 1 "$path" | grep -q '^Date,Open,High,Low,Close,Volume$' || return 1
  [[ "$(wc -l < "$path")" -ge 100 ]] || return 1
}

download_csv() {
  local label="$1"
  local url="$2"
  local target="$3"
  local tmp="${target}.tmp"
  local attempt
  local rc=1

  rm -f "$tmp"

  for attempt in 1 2 3 4 5; do
    echo "Downloading ${label} (attempt ${attempt}/5)..."
    if curl --noproxy '*' --silent --show-error --location --retry 2 --retry-delay 2 --retry-all-errors "$url" -o "$tmp"; then
      rc=0
    else
      rc=$?
    fi

    if validate_csv "$tmp"; then
      mv "$tmp" "$target"
      return 0
    fi

    echo "Download for ${label} did not produce a valid CSV yet (curl exit ${rc}). Retrying..." >&2
    sleep $((attempt * 2))
  done

  rm -f "$tmp"
  return "$rc"
}

download_csv "S&P 500 (^SPX) daily close data" 'https://stooq.com/q/d/l/?s=%5Espx&i=d' "$DATA_DIR/sp500.csv"
download_csv "Nasdaq 100 (^NDX) daily close data" 'https://stooq.com/q/d/l/?s=%5Endx&i=d' "$DATA_DIR/nasdaq100.csv"

echo "Done. Files saved to: $DATA_DIR"
