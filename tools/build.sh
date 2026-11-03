#!/usr/bin/env bash
# One-command build steps for edit vN.  Usage: bash tools/build.sh N STEP [STEP ...]
#   prep            source-range audit + face tracks + MODNet mattes            audio        soundtrack (circular, mastered, AAC-checked)
#   auto            review sheets around every cut         clip:A:B     frames A..B as a small MP4 with sound
#   preview         whole edit at 30 fps / 540x960         video        final upload MP4 + master MOV
#   qc              ship checkpoint on the encoded MP4     all          prep audio auto video qc
set -euo pipefail
N="$1"; shift; ROOT="$(cd "$(dirname "$0")/.." && pwd)"; V="v$N"; W="$ROOT/$V/work"
[ "$#" -gt 0 ] || { sed -n '2,6p' "$0"; exit 1; }
STEPS=("$@"); [ "${STEPS[0]}" = "all" ] && STEPS=(prep audio auto video qc)
SLUG=$(cd "$W" && python3 -c "import edl$N as E; print(E.SLUG)")
for s in "${STEPS[@]}"; do
  t0=$(date +%s); echo "== $V: $s"
  case "$s" in
    prep)    python3 "$ROOT/tools/check_sources.py" "$N" | grep -E "BAD|source ranges"
             python3 "$W/render$N.py" prep > "$W/prep.log" 2>&1; grep -E "track|seg " "$W/prep.log" | tail -40 ;;
    audio)   python3 "$W/audio$N.py" | tail -4 ;;
    auto)    python3 "$W/render$N.py" auto cuts ;;
    clip:*)  IFS=: read -r _ a b <<< "$s"; python3 "$W/render$N.py" clip "$a" "$b" ;;
    preview) python3 "$W/render$N.py" preview ;;
    video)   python3 "$W/render$N.py" video "$V/out" > "$W/render.log" 2>&1; tail -1 "$W/render.log" ;;
    qc)      python3 "$W/qc$N.py" "$ROOT/$V/out/${SLUG}_voidfx_9x16.mp4" > "$W/qc.log" 2>&1
             grep -v WARN "$W/qc.log" | sed -n '/loudness/p;/flagged/p;/text band/p;/near-black/p;/== 8/,$p' | grep -v " 0 flagged" ;;
    *)       echo "unknown step $s"; exit 1 ;;
  esac
  echo "   ($s took $(( $(date +%s) - t0 )) s)"
done
