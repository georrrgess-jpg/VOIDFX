# DEV HANDOFF: the efficiency update (Flash studio)

**From:** the Flash studio · **To:** the Dexter studio · **Date:** 2026-11-08 · **Type:** DEV · **Branch:** `claude/gallant-planck-pqpczp`

## 1. The request (sent to both studios)
> "I would like for you to plan and complete an update on which you improve the efficiency at which edits are produced. I do not want the quality of the edits to be diminished or effected at all and if anything the quality should be improved. Currently the editing process is functional and after 3 or so revisions I'm able to wield a relatively good product. But this process takes too long whether that be the revisions or the initial creation process."

**Our reading:** an owner round costs far more than any render, and most notes repeat a rule we already had. v13 rev 1 drew *"the singularity is the primary object in every transition"* and *"remove some of the tedious sound effects"*. The update therefore does three things:
1. checks the plan against the rules before the first render;
2. makes each revision round cheaper;
3. shortens the set-up.

No picture or encoder setting changed. The upload is still x264 preset slow CRF 17, and the master is still CRF 11.

## 2. What we built (all in `tools/`, documented in `docs/TOOLKIT.md` §1c)

| Piece | What it does |
|---|---|
| `preflight.py N` · `build.sh N plan` | Checks the plan against the owner's rules in seconds. It reads the EDL, the renderer's TR2 with a static call graph, and the sound events.<br>**FAIL:** the hero asset (`HERO = [...]` in the EDL) in more than 4 transitions; a Flash edit with no `emblem_at` transition; a plain cut; overlapping clip ranges; banned sound kinds; a sound on a beat-camera hit; a transition the registry marks rejected.<br>**WARN:** two shots from one source shot (`shots_<pack>.json`); more than 12 effects; more than 3 reverse swells; zoom over 1.10; held 24p/30p frames; a repeated transition; fewer than 3 set pieces; an edit-local drawing helper reached by more than 4 transitions; order-dependent caches. |
| `studio/transitions.json` · `preflight.py registry` | Every TR2 transition (v12 and v13 engines): pre/post frames, which edits used it, their verdicts, and the owner's reception from handoffs (`KNOWN` in preflight). |
| `codetrack.py`, used by `vrender.py` | A full render records which renderer functions drew each frame (`sys.monitoring`; no measurable cost; identical pixels). A function is keyed by its qualified name plus a hash of its own source. A later `video` re-renders only the frames that:<ul><li>ran an edited, removed or shadowed function;</li><li>read a changed module value or EDL global;</li><li>ran a function that caches across frames and calls an edited one.</li></ul>Those frames are still verified bit-exact outside. A global the renderer never reads (`SET_PIECES`, audio knobs) renders nothing. `vrender.py N video --dry` shows the decision. |
| `review.py N` (end of `build.sh N qc`) | The review pack from the encode: 8 stills per transition window, set piece and the wrap, with faceqc/motionqc flags boxed. Output: `vN/frames/review_*.jpg`. |
| `song_prep.py N SONG [--h0 --h1]` · `build.sh N song:FILE[:H0:H1]` | One command for the song:<ul><li>the map;</li><li>Demucs stems of the window;</li><li>a grid fit on the drum stem (or the music stem when the drums are silent), tested against the 2/3–3/2 tempo relatives;</li><li>Whisper large-v3 on the vocal stem, with words flagged where the stem's onset disagrees;</li><li>loop-wrap scores;</li><li>the EDL lines to paste.</li></ul> |
| `build.sh` | `qc` runs `qcN`, `faceqc` and `motionqc` in parallel, then the review pack. `prep` runs preflight and starts `sr_prep` in the background. `rev` = `audio video qc`. |
| `v12/work/audio12.py` (scaffold) | `place()` logs every effect from `main()` to `vN/audio/fx_events.json`. The audio is unchanged (identical md5 on v12). |

## 3. Measured (4 cores)

| | Before | After |
|---|---|---|
| v13 rev 1 through preflight, from git, with no v13 entries in the registry | the owner's round | **4 FAIL** (3 swirls, 1 whine) and **6 WARN**, including the black-hole code in 7 transitions, 24 effects, 11 reverse swells and the bookend reuse. That covers 2 of the owner's 5 notes before any render. The approved rev 2 gives 0 FAIL and 2 WARN. |
| Audio-only EDL change | full render (~5 min) | 4 s, nothing rendered |
| One transition edited, no range given (v12 `ecg_bolt`) | full render, 312 s | 157 s: 17 frames found, rendered and checked (33 verified) in 15 s; the rest is the preset-slow re-encode |
| Edit, then revert | — | all 1,401 frames identical to the full render |
| Edit to `grain` (cached by `finish12`) | — | every frame dirty, so a full render (correct) |
| QC | ~100 s in sequence; 138 s logged in v13 rev 2 | 80 s including the review pack (same results: 12/12 PASS on v13) |
| Review sheets | 19 hand-picked `sheet:` calls (v13 rev 1) | 9 s for every transition, set piece and the wrap |
| Song prep | about 6 manual steps | 6.8 min first run, 27 s with stems. On v13 it reproduces the grid within 8 ms and flags "darling" for a check (Whisper was 1.6 half-beats late). |

**Two findings for both engines:**
- **`render(f)` must be a pure function of `f`.** v13's `doppler_row` caches on rounded keys but fills the cache from the first caller's exact values. That made verification fail at frame 782, so every partial render there fell back to a full one. The fix is to compute the cached value from the rounded key. Preflight warns about the pattern.
- **About 140 s of every partial render is the whole-video x264 slow re-encode.** We kept it because it sets the upload's quality. Segment-level splicing (closed GOPs, stream copy) would remove most of it, but it changes the encode settings, so it needs the owner's OK.

## 4. Adopting it in the Dexter studio (v107 scaffold, our v12 engine)
1. Copy the following and add the `build.sh` steps (`song:`, `plan`, `review`, `rev`, the parallel `qc`, sr_prep in `prep`):
   - `tools/codetrack.py`, `preflight.py`, `review.py`, `song_prep.py`;
   - the `vrender.py` change (`_block` returns traces, `ct` in `meta.json`, the new `partial_render` logic, `--no-master`).
2. Add the `place()` logging in your `audio107.py`, which mirrors our `audio12.py` change.
3. **Fill `KNOWN` in `preflight.py` with your verdicts:** v107's redaction boxes and black bars (rejected), the POINT OF ORIGIN graphic (rejected, if it is a TR2 entry), v105's notes. The emblem rule switches itself off for non-Flash sources (`flash` in the `SRC` paths); add a Dexter equivalent if a symbol must carry a transition.
4. Run `preflight.py registry`, then `preflight.py 107`, and send us anything it gets wrong on an approved edit.

**Overlap with your WP7 (`plan_check`):** if you built a plan checker for this request too, let's merge them on `dev/pipeline-v2`:
- the rules live as data (a shared `studio/rules.json`);
- our TR2 call graph, sound-event and source-shot checks become checks in one tool.

Tell us which side's structure to keep.

## 5. Questions
- **Merge plan:** these tools sit on `claude/gallant-planck-pqpczp`. Should we open a PR into `dev/pipeline-v2`, or will you take them into your adopt branch as with Phase 1?
- **The segment-splice encode (§3):** it changes encoder settings, so it is the owner's call. Raise it only if revision render time still bothers them.
