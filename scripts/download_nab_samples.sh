#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DIR="$ROOT_DIR/backend/data/nab"
LABELS_DIR="$ROOT_DIR/backend/data/nab_labels"
BASE_URL="https://raw.githubusercontent.com/numenta/NAB/master/data/realKnownCause"
LABELS_URL="https://raw.githubusercontent.com/numenta/NAB/master/labels/combined_windows.json"

mkdir -p "$TARGET_DIR"
mkdir -p "$LABELS_DIR"

files=(
  "ambient_temperature_system_failure.csv"
  "cpu_utilization_asg_misconfiguration.csv"
  "machine_temperature_system_failure.csv"
)

for file in "${files[@]}"; do
  curl -fsSL "$BASE_URL/$file" -o "$TARGET_DIR/$file"
  echo "downloaded $file"
done

echo "NAB sample files saved to $TARGET_DIR"
curl -fsSL "$LABELS_URL" -o "$LABELS_DIR/combined_windows.json"
echo "downloaded combined_windows.json"
