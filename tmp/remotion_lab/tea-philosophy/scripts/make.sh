#!/usr/bin/env bash
# Làm trọn 1 video từ kịch bản tới file mp4.
#
#   ./scripts/make.sh 2026-08-21
#
# Làm cả loạt:
#   for f in content/*.json; do
#     case "$f" in *.build.json) continue;; esac
#     ./scripts/make.sh "$(basename "$f" .json)"
#   done

set -euo pipefail

slug="${1:?Thiếu slug. Ví dụ: ./scripts/make.sh 2026-08-21}"
cd "$(dirname "$0")/.."

echo "==> [1/2] TTS + tính thời lượng"
python3 scripts/build.py "$slug"

echo "==> [2/2] Render"
npx remotion render Daily "out/$slug.mp4" --props="./content/$slug.build.json"

echo "==> Xong: out/$slug.mp4"
