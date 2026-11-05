#!/usr/bin/env bash
# Stand up (or check) a voidfx studio: Python deps, fonts, models, source library, smoke test.
#   bash tools/setup_studio.sh            install what's missing, then verify
#   bash tools/setup_studio.sh --check    verify only (no installs / downloads)
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"; CHECK=0; [ "${1:-}" = "--check" ] && CHECK=1
ok() { printf "  [ok]   %s\n" "$1"; }; bad() { printf "  [MISS] %s\n" "$1"; MISSING=1; }; MISSING=0

echo "== tools"
for t in ffmpeg ffprobe python3; do command -v $t >/dev/null && ok "$t" || bad "$t (install it: apt-get install -y ffmpeg python3)"; done

echo "== python packages"
for m in numpy scipy cv2 PIL onnxruntime faster_whisper demucs; do
  if python3 -c "import $m" 2>/dev/null; then ok "$m"
  elif [ $CHECK = 0 ]; then
    pkg=$m; [ $m = cv2 ] && pkg=opencv-python-headless; [ $m = PIL ] && pkg=pillow; [ $m = faster_whisper ] && pkg=faster-whisper
    pip install -q "$pkg" && ok "$m (installed)" || bad "$m"
  else bad "$m"; fi
done

echo "== fonts"
for f in /usr/share/fonts/opentype/inter/InterDisplay-Black.otf /usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf; do
  if [ -f "$f" ]; then ok "$(basename $f)"
  elif [ $CHECK = 0 ]; then apt-get install -y -q fonts-inter fonts-jetbrains-mono >/dev/null 2>&1 && [ -f "$f" ] && ok "$(basename $f) (installed)" || bad "$f"
  else bad "$f"; fi
done

echo "== models"
YN=v3/models/face_detection_yunet_2023mar.onnx; MN=v3/models/modnet/onnx/model.onnx
mkdir -p v3/models/modnet/onnx
[ -s $YN ] || { [ $CHECK = 0 ] && curl -sSL -o $YN https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx; }
[ -s $MN ] || { [ $CHECK = 0 ] && curl -sSL -o $MN https://huggingface.co/Xenova/modnet/resolve/main/onnx/model.onnx; }
[ -s $YN ] && ok "YuNet" || bad "YuNet ($YN)"; [ -s $MN ] && ok "MODNet" || bad "MODNet ($MN)"
echo "  (faster-whisper large-v3 and Demucs htdemucs download themselves on first use)"

echo "== source library (src/ vs studio/src_manifest.json)"
python3 - <<'EOF'
import json, os, hashlib
m = json.load(open("studio/src_manifest.json"))["files"]; miss = 0
for e in m:
    p = f"src/{e['file']}"
    if not os.path.exists(p): print(f"  [MISS] src/{e['file']:24s} upload: {e['uploaded_as']}"); miss += 1; continue
    if os.path.getsize(p) != e["bytes"]: print(f"  [DIFF] src/{e['file']} size differs from the library copy (different encode?)"); continue
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    print(f"  [{'ok' if h == e['sha256'] else 'DIFF'}]   src/{e['file']}")
print(f"  {len(m) - miss}/{len(m)} present")
EOF

echo "== smoke test"
python3 v7/work/edl7.py >/dev/null 2>&1 && ok "benchmark EDL (v7) loads" || bad "v7 EDL"
python3 v10/work/edl10.py >/dev/null 2>&1 && ok "standard EDL (v10) loads" || bad "v10 EDL"
(cd v10/work && python3 -c "import sys; sys.argv=['x']; import render10" >/dev/null 2>&1) && ok "standard engine (v10) imports" || bad "v10 engine"
python3 v11/work/edl11.py >/dev/null 2>&1 && ok "standard EDL (v11) loads" || bad "v11 EDL"
(cd v11/work && python3 -c "import sys; sys.argv=['x']; import render11" >/dev/null 2>&1) && ok "newest engine (v11) imports" || bad "v11 engine"
[ -f src/pack8_s1.mp4 ] && { python3 tools/check_sources.py 7 | tail -1; } || echo "  (skip source audit: packs not uploaded yet)"
[ $MISSING = 0 ] && echo "studio ready" || echo "some items missing (see [MISS] above)"
