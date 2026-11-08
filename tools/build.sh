#!/usr/bin/env bash
# One-command build steps for edit vN (pipeline v2).  Usage: bash tools/build.sh N STEP [STEP ...]
#   song:FILE[:H0:H1] song prep in one go (tools/song_prep.py): map, stems, drum-stem grid, vocal-stem words, loop wrap, EDL lines
#   prep              source audit + face tracks + mattes + the plan check (report only); starts the source restoration in the background
#   audio             soundtrack (circular, mastered, AAC-checked) + effects-vs-music table
#   auto              sheets around every cut (render server)   sheet:NAME:f,f  tiled stills of chosen frames (render server)
#   strip:A:B         every 2nd frame A..B in one sheet         clip:A:B        frames A..B as a 540x960 MP4 with sound (render server)
#   video             upload MP4 + lossless frame cache; re-renders only the EDL's changed shots when a cache exists; the master
#                     encodes in the background.   video:A:B[,C:D]  re-render only those frames (verified)   fullvideo  force a full render
#   qc                ship checkpoint on the encoded MP4 + faces-vs-effects list + motion audit (dead spans, pops, judder)
#                     + the signoff pages (every transition and cut, set piece, the loop, titles, pops; QC flags boxed red)
#   signoff / review  the review pages alone           deliver   wait for the master and check it
#   golden            engine regression check (tools/golden.py N --check)              preview   whole edit at 30 fps / 540x960 (engine)
#   plan              the plan against the owner's rules (tools/plan_check.py, which also runs preflight's checks); runs before
#                     every video step and a FAIL stops the render (accept a check with PLAN_ACCEPT in the EDL, or PLAN_FORCE=1)
#   report            the Measured block from the tools' outputs -> vN/work/measured.md            splice    re-splice fxN.py
#   rev  = audio plan video qc report                   (a revision round: only the changed frames are re-rendered)
#   ship = rev + deliver                                 all = prep audio plan auto video qc report deliver
#   An edited fxN.py is re-spliced automatically before any step that renders. Every step is logged to vN/work/metrics.json.
set -euo pipefail
N="$1"; shift; ROOT="$(cd "$(dirname "$0")/.." && pwd)"; V="v$N"; W="$ROOT/$V/work"
[ "$#" -gt 0 ] || { sed -n '2,20p' "$0"; exit 1; }
STEPS=("$@")
case "${STEPS[0]}" in
  all)  STEPS=(prep audio plan auto video qc report deliver) ;;
  rev)  STEPS=(audio plan video qc report "${STEPS[@]:1}") ;;                # qc ends with the signoff pages
  ship) STEPS=(audio plan video qc report deliver "${STEPS[@]:1}") ;;
esac
case "${STEPS[0]}" in song:*) SLUG="" ;; *) SLUG=$(cd "$W" && python3 -c "import edl$N as E; print(E.SLUG)") ;; esac
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
    song:*)    IFS=: read -r _ f h0 h1 <<< "$s"; python3 "$T/song_prep.py" "$N" "$f" ${h0:+--h0 $h0} ${h1:+--h1 $h1} ;;
    prep)      python3 "$T/check_sources.py" "$N" | grep -E "BAD|source ranges"
               python3 "$T/splice_section.py" "$N" --check
               python3 "$W/render$N.py" prep > "$W/prep.log" 2>&1; grep -E "track|seg " "$W/prep.log" | tail -40
               python3 "$T/plan_check.py" "$N" 2> "$W/plan_check.err" | head -12 || true
               SRP="$ROOT/$V/sr/prep.pid"
               if [ -f "$SRP" ] && kill -0 "$(cat "$SRP")" 2>/dev/null; then echo "   source restoration already running (pid $(cat "$SRP"))"
               elif python3 "$T/sr_prep.py" "$N" --count 2>/dev/null | grep -q "to process 0,"; then echo "   restored source bands are current"
               else mkdir -p "$ROOT/$V/sr"; nohup nice -n 12 python3 "$T/sr_prep.py" "$N" > "$ROOT/$V/sr/prep.log" 2>&1 & echo $! > "$SRP"
                    echo "   source restoration started in the background (pid $!, log $V/sr/prep.log); the final render uses the bands, so let it finish first (vrender renders in full when they change)"; fi ;;
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
    qc)        MP4="$ROOT/$V/out/${SLUG}_voidfx_9x16.mp4"          # the four passes are independent: run them side by side
               python3 "$W/qc$N.py" "$MP4" > "$W/qc.log" 2>&1 & P1=$!
               python3 "$T/faceqc.py" "$N" > "$W/faceqc.log" 2>&1 & P2=$!
               python3 "$T/motionqc.py" "$N" > "$W/motionqc.log" 2>&1 & P3=$!
               R1=0; R2=0; R3=0; wait $P1 || R1=$?; wait $P2 || R2=$?; wait $P3 || R3=$?
               python3 "$T/signoff.py" "$N" > "$W/signoff.log" 2>&1 || true    # the review pages, after faceqc/motionqc: it boxes their flags
               grep -v WARN "$W/qc.log" | sed -n '/loudness/p;/flagged/p;/text band/p;/near-black/p;/== 8/,$p' | grep -v " 0 flagged" || true
               tail -14 "$W/faceqc.log"; grep -v "activity per" "$W/motionqc.log" || true; tail -1 "$W/signoff.log"
               [ $R1$R2$R3 = 000 ] || echo "   a QC pass exited non-zero (qc $R1, faceqc $R2, motionqc $R3): see $V/work/*.log" ;;
    review)    python3 "$T/signoff.py" "$N" ;;                                # the old name of signoff
    deliver)   python3 "$T/vrender.py" "$N" master --wait ;;
    golden)    python3 "$T/golden.py" "$N" --check ;;
    *)         echo "unknown step $s"; exit 1 ;;
  esac
  dt=$(( $(date +%s) - t0 )); echo "   ($s took $dt s)"
  python3 "$T/metrics.py" "$N" stage "$s" "$dt" || true
done
