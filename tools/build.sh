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
#   plan              plan_check: the owner's recurring notes on the EDL (runs before every video step; a FAIL stops the render
#                     unless PLAN_FORCE=1)                                          splice    re-splice fxN.py into renderN.py
#   signoff           review sheets from the encode (every transition, the loop, the titles, unexplained pops) -> vN/frames/signoff_*
#   report            the Measured block from the tools' outputs -> vN/work/measured.md
#   ship = audio plan video qc signoff report deliver  (one command per revision)
#   all  = prep audio plan auto video qc signoff report deliver.   Every step is logged to vN/work/metrics.json.
#   An edited fxN.py is re-spliced automatically before any step that renders (sheet, strip, clip, auto, preview, video).
set -euo pipefail
N="$1"; shift; ROOT="$(cd "$(dirname "$0")/.." && pwd)"; V="v$N"; W="$ROOT/$V/work"
[ "$#" -gt 0 ] || { sed -n '2,10p' "$0"; exit 1; }
STEPS=("$@"); [ "${STEPS[0]}" = "all" ] && STEPS=(prep audio plan auto video qc signoff report deliver)
[ "${STEPS[0]}" = "ship" ] && STEPS=(audio plan video qc signoff report deliver "${STEPS[@]:1}")
SLUG=$(cd "$W" && python3 -c "import edl$N as E; print(E.SLUG)")
T="$ROOT/tools"
autosplice() {                                     # an edited fxN.py goes into renderN.py before anything renders
  local fx="$W/fx$N.py" r="$W/render$N.py"
  [ -f "$fx" ] && [ "$fx" -nt "$r" ] || return 0
  if [ -f "$W/splice.py" ]; then python3 "$W/splice.py" | tail -1        # v105-based edits
  else python3 "$T/splice_section.py" "$N" "$fx" --replace; fi
}
plangate() {
  python3 "$T/plan_check.py" "$N" > "$W/plan_check.log" 2> "$W/plan_check.err" && { head -1 "$W/plan_check.log"; return 0; }
  cat "$W/plan_check.log"
  [ "${PLAN_FORCE:-0}" = "1" ] && { echo "   (PLAN_FORCE=1: rendering anyway)"; return 0; }
  echo "   plan_check FAILED: fix the EDL, or accept a check with PLAN_ACCEPT in the EDL, or PLAN_FORCE=1 to render anyway"; exit 1
}
for s in "${STEPS[@]}"; do
  case "$s" in sheet:*|strip:*|clip:*|auto|preview|video|video:*|fullvideo|plan|splice) autosplice ;; esac
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
    plan)      plangate ;;
    splice)    true ;;
    signoff)   python3 "$T/signoff.py" "$N" ;;
    report)    python3 "$T/report.py" "$N" ;;
    video)     [[ " ${STEPS[*]} " == *" plan "* ]] || plangate
               python3 "$T/vrender.py" "$N" video > "$W/render.log" 2>&1 || { tail -5 "$W/render.log"; exit 1; }
               grep -E "render|verification|done|nothing" "$W/render.log" | tail -4 ;;
    video:*)   [[ " ${STEPS[*]} " == *" plan "* ]] || plangate
               python3 "$T/vrender.py" "$N" video --only "${s#video:}" > "$W/render.log" 2>&1 || { tail -5 "$W/render.log"; exit 1; }
               grep -E "render|verification|done" "$W/render.log" | tail -5 ;;
    fullvideo) [[ " ${STEPS[*]} " == *" plan "* ]] || plangate
               python3 "$T/vrender.py" "$N" video --full > "$W/render.log" 2>&1 || { tail -5 "$W/render.log"; exit 1; }
               tail -2 "$W/render.log" ;;
    qc)        python3 "$W/qc$N.py" "$ROOT/$V/out/${SLUG}_voidfx_9x16.mp4" > "$W/qc.log" 2>&1 &   # the three passes in parallel (103 -> 73 s)
               p1=$!; python3 "$T/faceqc.py" "$N" > "$W/faceqc.log" 2>&1 & p2=$!
               python3 "$T/motionqc.py" "$N" > "$W/motionqc.log" 2>&1 & p3=$!
               wait $p1 || true; wait $p2 || true; wait $p3 || true
               grep -v WARN "$W/qc.log" | sed -n '/loudness/p;/flagged/p;/text band/p;/near-black/p;/== 8/,$p' | grep -v " 0 flagged"
               tail -14 "$W/faceqc.log"
               grep -v "activity per" "$W/motionqc.log" ;;
    deliver)   python3 "$T/vrender.py" "$N" master --wait ;;
    golden)    python3 "$T/golden.py" "$N" --check ;;
    *)         echo "unknown step $s"; exit 1 ;;
  esac
  dt=$(( $(date +%s) - t0 )); echo "   ($s took $dt s)"
  python3 "$T/metrics.py" "$N" stage "$s" "$dt" || true
done
