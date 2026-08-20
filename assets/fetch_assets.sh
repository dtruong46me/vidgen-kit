#!/usr/bin/env bash
# Downloads a handful of small, freely-licensed sample media files into
# assets/{video,audio,image}/ so the demos have real files to work with.
#
# assets/ is gitignored (see .gitignore) — nothing here is meant to be
# committed. Re-run any time to refresh/redownload.
#
# Usage: bash assets/fetch_assets.sh

set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

mkdir -p video audio image

fetch() {
  local url="$1" out="$2"
  if [ -s "$out" ]; then
    echo "skip (already have): $out"
    return
  fi
  echo "downloading: $out"
  curl -sL --max-time 30 -o "$out" "$url"
}

# CC0, MDN's sample media (https://github.com/mdn/learning-area)
fetch "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4" \
      "video/flower.mp4"

# Big Buck Bunny (CC-BY, Blender Foundation), re-encoded 10s/1MB clip hosted
# for testing by test-videos.co.uk
fetch "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/Big_Buck_Bunny_360_10s_1MB.mp4" \
      "video/big_buck_bunny.mp4"

# samplelib.com — generated tone, explicitly published for use as test/sample audio
fetch "https://download.samplelib.com/mp3/sample-15s.mp3" \
      "audio/sample.mp3"

# picsum.photos — free-to-use placeholder photo service (Unsplash-backed)
fetch "https://picsum.photos/1280/720" \
      "image/sample.jpg"

echo "done."
