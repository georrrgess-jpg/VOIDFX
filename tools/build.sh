#!/usr/bin/env bash
# One-command build steps for edit vN (pipeline v2).  Usage: bash tools/build.sh N STEP [STEP ...]
#   prep              source audit + face tracks + mattes      audio           soundtrack (circular, mastered, AAC-checked) + effects-vs-music table
#   auto              sheets around every cut (render server)   sheet:NAME:f,f  tiled stills of chosen frames (render server)
#   strip:A:B         every 2nd frame A..B in one sheet         clip:A:B        frames A..B as a 540x960 MP4 with sound (render server)
#   video             upload MP4 + lossless frame cache; re-renders only the EDL's changed shots when a cache exists; the master
#                     encodes in the background.   video:A:B[,C:D]  re-render only those frames (verified)   fullvideo  force a full render
#   qc                ship checkpoint on the encoded MP4 + faces-vs-effects list + motion audit (dead spans, pops, judder)
#                     deliver   wait for the master and check it
#   golden            engine regression check (tools/golden.py N --check)              preview   whole edit at 30 fps / 540x960 (engine)
#   all = prep audio auto video qc deliver.   Every step is logged to vN/work/metrics.json.
set -euo pipefail
N="$1"; shift; ROOT="$(cd "$(dirname "$0")/.." && pwd)"; V="v$N"; W="$ROOT/$V/work"
[ "$#" -gt 0 ] || { sed -n '2,10p' "$0"; exit 1; }
STEPS=("$@"); [ "${STEPS[0]}" = "all" ] && STEPS=(prep audio auto video qc deliver)
SLUG=$(cd "$W" && python3 -c "import edl$N as E; print(E.SLUG)")
T="$ROOT/tools"
for s in "${STEPS[@]}"; do
  t0=$(date +%s); echo "== $V: $s"
  case "$s" in
    prep)      python3 "$T/check_sources.py" "$N" | grep -E "BAD|source ranges"
               python3 "$T/splice_section.py" "$N" --check
               python3 "$W/render$N.py" prep > "$W/prep.log" 2>&1; grep -E "track|seg " "$W/prep.log" | tail -40 ;;
    audio)     python3 "$W/audio$N.py" | tail -4
               [ -f "$ROOT/$V/audio/stem_fx.wav" ] && python3 "$T/mixcheck.py" "$N" | tail -12 || true ;;
    auto)      python3 "$T/rsrv.py" "$N" auto cuts ;;
    sheet:*)   IFS=: read -r _ name fl <<< "$s"; python3 "$T/rsrv.py" "$N" stills "$name" ${fl//,/ } ;;
    strip:*)   IFS=: read -r _ a b <<< "$s"; python3 "$T/rsrv.py" "$N" strip "$a" "$b" ;;
    clip:*)    IFS=: read -r _ a b <<< "$s"; python3 "$T/rsrv.py" "$N" clip "$a" "$b" ;;
    preview)   python3 "$W/render$N.py" preview ;;
    video)     python3 "$T/vrender.py" "$N" video > "$W/render.log" 2>&1 || { tail -5 "$W/render.log"; exit 1; }
               grep -E "render|verification|done|nothing" "$W/render.log" | tail -4 ;;
    video:*)   python3 "$T/vrender.py" "$N" video --only "${s#video:}" > "$W/render.log" 2>&1 || { tail -5 "$W/render.log"; exit 1; }
               grep -E "render|verification|done" "$W/render.log" | tail -5 ;;
    fullvideo) python3 "$T/vrender.py" "$N" video --full > "$W/render.log" 2>&1 || { tail -5 "$W/render.log"; exit 1; }
               tail -2 "$W/render.log" ;;
    qc)        python3 "$W/qc$N.py" "$ROOT/$V/out/${SLUG}_voidfx_9x16.mp4" > "$W/qc.log" 2>&1
               grep -v WARN "$W/qc.log" | sed -n '/loudness/p;/flagged/p;/text band/p;/near-black/p;/== 8/,$p' | grep -v " 0 flagged"
               python3 "$T/faceqc.py" "$N" | tail -14
               python3 "$T/motionqc.py" "$N" | grep -v "activity per" ;;
    deliver)   python3 "$T/vrender.py" "$N" master --wait ;;
    golden)    python3 "$T/golden.py" "$N" --check ;;
    *)         echo "unknown step $s"; exit 1 ;;
  esac
  dt=$(( $(date +%s) - t0 )); echo "   ($s took $dt s)"
  python3 "$T/metrics.py" "$N" stage "$s" "$dt" || true
done
