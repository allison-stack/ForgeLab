#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="../arrow-demo"
REPO_URL="https://github.com/arrow-py/arrow"
PRE_FIX_SHA="7225592f8e1d85ecc49ff0ad4b4291386520802f"

if [ -d "$TARGET_DIR" ]; then
  echo "arrow-demo already exists at $TARGET_DIR — skipping clone."
  exit 0
fi

echo "Cloning arrow-py/arrow into $TARGET_DIR..."
git clone "$REPO_URL" "$TARGET_DIR"
cd "$TARGET_DIR"
git checkout "$PRE_FIX_SHA"
echo "Done. Target repo ready at $TARGET_DIR (pre-fix commit $PRE_FIX_SHA)."
