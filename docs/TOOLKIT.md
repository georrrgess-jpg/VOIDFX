# voidfx toolkit: how an edit gets made (fast)

<!-- Flash studio (Studio 1) -->
The engine lives in the newest standard, `v11/work/` (BOP rev 4; `v10/`, `v7/`, `v6/` and `v4/` remain benchmarks). It contains every v4–v11 transition and graphic, the restored-source sampler, velocity with optical flow, the beat camera, the v9 text system and the v11 pieces (rival grade, red effects, bolt split, red eye dive, clash, rift, the procedural Reverse-Flash emblem and coin flip, the REVERSE loop, the beat moments). New edits copy it with `tools/new_edit.py`, then write their EDL and **their own frame function** (`render()` at the end of the renderer: grade, text, graphics, finish) and sound design. **Copy the engine, not the look.** Every edit gets its own grade, type and transition mix. Owner preferences and lessons: `studio/VOIDFX_STUDIO.md`; sources: `studio/SCENE_PACKS.md`.

<!-- Dexter studio (Studio 2) -->
The engine is the newest standard, `v104/work/` (THE PASSENGER; see the handbook §0). `render104.py` contains every v4–v9 transition and graphic, and the edit's own section is spliced in from `fx104.py` by `splice.py`. That section carries FOREVER's toolkit and THE PASSENGER's on top of it (the last definitions win, so that section owns the grade, the frame function, the text and the finish). New edits copy all of it, plus THE PASSENGER's EDL as the worked template, with `tools/new_edit.py`. Then they rewrite the EDL, restyle their `fxN.py` (grade, palette, set pieces, frame) and the sound design, and run `python3 vN/work/splice.py` after each `fxN.py` change. **Copy the engine, not the look.** Every edit gets its own grade, type and transition mix. Owner preferences and lessons: `studio/VOIDFX_STUDIO.md`; sources: `studio/SCENE_PACKS.md`.

## 1. Pipeline and timings

Timings were measured on this 4-core box for a 26 s edit.

| Step | Command | Time |
|---|---|---|
| Scaffold | `python3 tools/new_edit.py N SLUG "TITLE"` | 1 s |
| Map the song | `python3 tools/song_map.py src/SONG.mp3 vN/work` | 3 s |
| Shot lists | `python3 vN/work/analyze.py src/PACK.mp4 TAG` (contact sheets, per-shot stats) | ~1 min per pack |
| **Lyric recognition** | `python3 tools/lyrics.py vN src/SONG.mp3 START END "published lyrics \| line 2"`. Demucs vocals (cached), Whisper word times snapped to the real onsets, aligned to the published lyrics, unsung words left out, a ready `TEXT` caption block | ~1 min (+2 min Demucs the first time) |
| Dialogue | `python3 tools/transcribe.py vN NAME MEDIA [--vad] [--start S --dur D]` | 1–3 min |
| Edit-section change | edit `vN/work/fxN.py`, then `python3 vN/work/splice.py` | 1 s |
| Voice under score | `python3 -m demucs -n htdemucs --two-stems=vocals -o vN/audio/sep CLIP.wav` | 15 s per 30 s clip |
| Tracks and mattes | `bash tools/build.sh N prep` | ~35 s |
| **Sharpness check** (Studio 2 rule) | `python3 tools/sharpness.py packs` before picking; `python3 tools/sharpness.py N` on the finished video (flags zoom > 10 % on 720p and shots under 0.80× the edit's median in-focus detail) | packs ~1 min; an edit ~40 s |
| **Source restoration** (v10 rev 3) | `nohup python3 tools/sr_prep.py N &` right after `prep`: Real-ESRGAN compact restores and 2× upscales only the band each frame is cropped from; the renderer uses it automatically | ~3 s per source frame (45 min for 900 frames, in the background while you build) |
| **Every-cut review sheets** | `bash tools/build.sh N auto` → `vN/frames/cuts_*.jpg` (render server) | ~25 s |
| **Stills / strips** (pipeline v2) | `bash tools/build.sh N sheet:NAME:f1,f2,…` · `strip:A:B` (every 2nd frame across a transition) | **7.6 s** for 24 full-quality frames once the server is warm (was 40–70 s) |
| Soundtrack | `bash tools/build.sh N audio` (circular, wrapped master, AAC-checked) **+ the effects-vs-music table** (`tools/mixcheck.py`) | ~12 s |
| **Motion check** | `bash tools/build.sh N clip:A:B` → small MP4 with sound (render server) | ~20 s |
| Whole-edit preview | `bash tools/build.sh N preview` (30 fps, 540×960) | ~half the final render |
| **Final** (pipeline v2) | `bash tools/build.sh N video`: upload MP4 + lossless frame cache; the master encodes in the background | **7.1 min** for v11 (was 13–15) |
| **Revision re-render** (pipeline v2) | `bash tools/build.sh N video` again: re-renders only the EDL's changed shots (verified); `video:A:B` for a code change you can bound | **3.8 min** for one shot (the upload re-encode is ~2.5 min of it) |
| Checkpoint | `bash tools/build.sh N qc` (qcN + the faces-vs-effects list) · `deliver` (waits for and checks the master) | ~2 min · 0–4 min |
| **Engine check** | `bash tools/build.sh N golden` (103 frames vs the reference; required after any engine change) | ~40 s |

**Efficient loop (pipeline v2):**
1. Write the EDL.
2. Run `prep auto`.
3. Fix whatever the sheets show, using `sheet:` / `strip:` / `clip:` on single moments (the render server keeps the engine loaded and restarts itself when the code changes).
4. Run `audio` and read the effects-vs-music table: no kept sound at a transition or set piece more than 12 dB under the music (a silent transition is fine, v106).
5. Run **one** `video qc` per revision. In later revisions `video` re-renders only what changed.
6. Look at every run in the faces-vs-effects list (`vN/frames/faceqc.jpg`) and fix the ones that aren't designed. Then read the motion audit that `qc` prints (`tools/motionqc.py`): fill every dead span with a cut and a designed transition, fix every UNEXPLAINED pop and judder run, and check the wrap step.
7. Visual sign-off on frames pulled from the encoded MP4, then `deliver`.
8. At the verdict: `python3 tools/vrender.py N clean` (the frame cache is ~2.2 GB).

Never final-render to find out whether something works.

**Choosing the song window:** `song_map` prints whole-bar windows of 20–27 s with the biggest section change (the "good part", where the full mix or bass comes back) at 33–47 % of the edit. For Warmpop it independently found the window used in v6 (h416→h496, drop at 10.67 s).

## 1b. Pipeline v2: speed and checks (Phase 0–1, 2026-11-07; plan in `sync/PIPELINE_V2_PLAN.md`)

| Tool | What it does |
|---|---|
| `tools/golden.py N --save / --check [--diff]` | Reference frames: frame 0, the last 3 frames, every cut at −6/0/+6, every shot's middle and every 32nd frame (103 for v11, 112 for v10). Gate: max 2/255 per pixel and mean < 0.2/255. **Run `--check` on v10 and v11 before and after any engine change.** The references are the shipped v10 rev 5 and v11 rev 4 engines (kept out of git). |
| `tools/vrender.py N video [--only A:B] [--full] [--dry]` · `master [--wait]` · `status` · `clean` | Final renders. Workers render contiguous blocks that never cross a cut, so per-worker caches hit. Each full render writes `vN/work/cache/frames.mkv` (Ut Video, lossless) plus a SHA-1 per frame. The master is encoded from that cache in the background at low priority. A partial render needs a cache. It re-renders the declared range plus every shot whose EDL entry changed (±30 frames), then re-renders about 30 frames outside the range and requires a bit-exact match. On any mismatch it falls back to a full render, as it does when the cut points, the tracks, the mattes or the restored bands change. **Since 2026-11-08 it tracks which renderer code drew each frame (§1c): code and EDL-global changes re-render only the frames they reach.** |
| `tools/rsrv.py N stills / full / strip / clip / auto / stop` | A render server with 4 warm workers. It restarts itself when `renderN.py`, the EDL, the tracks, the mattes or the SR index change. |
| `tools/faceqc.py N` | Effects over faces. It compares the final frame with the shot's own picture inside the face box (track, or the matte's head for `face=None`). A gain/offset fit removes grades and fades; a frame is flagged when more than 3 % of the box gains more than 0.10 luma. It writes a list and a sheet; it isn't a gate (designed set pieces and titles show up too). |
| `tools/mixcheck.py N` | Effects vs music at every transition and `E.SET_PIECES` entry, from the stems the audio builder now writes (`stem_music.wav`, `stem_fx.wav`). FLAG: effects more than 12 dB under the music. |
| `tools/metrics.py N …` | `vN/work/metrics.json`. `build.sh` logs every step. Log owner notes (`note CATEGORY "…"`) and by-eye catches (`catch CATEGORY "…"`) so the pilots can be compared. |
| `tools/edit_env.py` | Loads an edit's renderer as a library (set up as its `main()` does); `bounded_imap` keeps at most 6 blocks in flight (an unbounded `pool.imap` reached 12.1 GB on v11 in the Dexter studio's test). |
| `tools/splice_section.py N SECTION.py` · `--check` | Inserts an edit's section above the speed section (idempotent); `--check` lists overrides placed below it. |
| `tools/motionqc.py N [--file F]` | The v106 audits on the encode (~10 s; run by `build.sh N qc`): mean frame difference per half-beat (135×240 grey) and **dead spans** (< 1.5 for ≥ 1 s); **pops** (d > 3·median(±6) + 2) labelled cut / flash / beat / cadence / UNEXPLAINED with the transition they sit in; **hold-cadence judder** per shot (15-frame windows with ≥ 40 % repeat frames; 2:3 pulldown gives 60 %) plus v106's p80/p20 ratio; the loop's wrap step. Writes `vN/work/motionqc.json`. A review list, not a gate. |

**Measured on v11 (4 cores):**

| | Before | After |
|---|---|---|
| Full render | 786–914 s | **427 s** (the master follows in the background, ~4 min at low priority) |
| Render time per frame (contiguous blocks, profiled) | 1.37 s | 1.06 s |
| One-shot revision | a full render | **227 s** |
| 24-frame sheet | 40–70 s | **7.6 s** warm |

Every frame of the v2 render matches the shipped engine within the gate (worst pixel 2/255 at the coin flip, mean 0.001/255). An EDL change rendered partially and then reverted gave a frame cache bit-identical to a full render. A deliberate global change (grain 0.012 → 0.0125) failed verification on 32 of 32 check frames.

**Where the remaining time goes:** the upload encode at x264 preset slow is about 2.3 min of 4-core time and is kept by guardrail 1. Optical flow is ~88 ms a frame (a cross-revision flow cache is part of WP5). INTER_CUBIC warps of float frames are ~42 ms each.

**Engine rules for speed (no change to the picture):**
- Build grades on `tone_lut(key, gains, g, ev, lx, ly)` + `apply_lut3(img, tab)`. One 65,536-entry lookup per channel replaces gain → gamma → exposure → `np.interp` (~280 ms → ~25 ms a band).
- In hot per-frame code, don't write `a[..., None] * colour` on full frames. It is ~3× slower than filling each channel (`mul3(a, col, k)`, or the per-channel loops in `light_rgb` / `finish11`).
- Avoid full-resolution blurs with σ > 4 on masks you can build from 1-D profiles (`face_keepout`).
- Cached unshaken shot renders (`render_shot(..., with_shake=False)`) are **read-only**. Copy before drawing on one.
- **Where an edit's code goes:** above `# >>> pipeline v2: speed` (`python3 tools/splice_section.py N SECTION.py`). Below it, a new `grade` / `render_shot` replaces the fast path: still right, only slower. `build.sh N prep` and every tool that loads the edit warn about it.
- **Prove picture identity with frame hashes or golden frames, never MP4 bytes.** x264's output differs between full-length runs even from identical frames (the Dexter studio, 2026-11-08).
- Don't make an effect depend on the order frames are rendered in. Partial renders and blocks assume `render(f)` is a pure function of `f`.

**First findings on the shipped v11 (for the next Flash edit):**
- `mixcheck`: 12 of 17 transitions have effects 9–31 dB under the music (music −10.2 dBFS RMS, a loud master). The Dexter studio's rule 7 applies to Flash edits too: push effects about +9 dB and duck the music about 3 dB under the biggest hits.
- `faceqc`: light over his face in 9 runs:
  - diagonal light sweeps across the face (answer 378, smirk 830);
  - lightning crossing the face edge (smile 552–574, fireclose 1020);
  - LET'S GO on his chin (420);
  - the designed red radiate in the REVERSE loop (1198–1216).

## 1c. The efficiency update (both studios, merged into one toolchain on 2026-11-08): fewer rounds, faster rounds

**Since the merge:** `build.sh N plan` (and `preflight.py N`) runs `tools/plan_check.py`, one report with both studios' checks; `studio/transitions.json` holds the owner's curated verdicts and `studio/transitions_usage.json` the generated fields (`preflight.py registry`); `build.sh N rev` = audio → plan → video (only the changed frames) → qc (three passes in parallel, then the sign-off pages) → report, `ship` = rev + deliver. The Flash studio's half is the first table, the Dexter studio's the second.

The owner: *"this process takes too long whether that be the revisions or the initial creation process"*, and quality must not drop. Most of an edit's time goes into owner rounds, and most owner notes repeat a rule we already had (v13 rev 1: the hero asset in every transition, too many sounds, swirls and whines). So the update checks the plan before the first render, then makes each round cheaper.

| Tool | What it does |
|---|---|
| `tools/preflight.py N` · `build.sh N plan` (also at the end of `prep`) | The plan against the owner's standing rules, in seconds, before rendering. It reads the EDL, the renderer (imported without set-up: TR2 and a static call graph of every transition) and the sound events (`vN/audio/fx_events.json`, or a sandbox run of the audio builder).<br>**FAIL:**<ul><li>the hero asset (`HERO = [...]` in the EDL, or `--hero`) in more than 4 transitions;</li><li>no transition using `emblem_at` in a Flash edit;</li><li>a plain cut;</li><li>overlapping source ranges;</li><li>drone/swirl/whine/chime/bell/shine sounds;</li><li>a sound on a beat-camera hit away from a cut or set piece;</li><li>a transition the registry marks rejected.</li></ul>**WARN:**<ul><li>two shots from one source shot (`shots_<pack>.json`);</li><li>more than 12 effects;</li><li>more than 3 reverse swells;</li><li>z > 1.10;</li><li>held 24p/30p frames;</li><li>a repeated transition;</li><li>fewer than 3 set pieces;</li><li>an edit-local drawing helper reached by more than 4 transitions (the undeclared hero asset);</li><li>caches keyed on rounded arguments but filled from exact ones.</li></ul>**INFO:** the emblem transition, the library transitions to pull frames of, the text. Exit 1 on any FAIL. |
| `studio/transitions.json` (curated) · `studio/transitions_usage.json` (generated: `preflight.py registry`) | The owner's verdict on each transition (`verdict` liked / ok / rejected / banned, his words in `evidence`, a `fix`, `tags`, hero `family`, `studio`, a `caution` for technical traps), and, generated, where each is defined and used (pre/post frames, engines, edits, their verdicts). Add each verdict to `transitions.json` the turn the owner gives it. |
| `tools/plan_check.py N` (one report for both studios since the merge; it also runs preflight's checks) | Checks the EDL against the registry's verdicts, look-alike clips (thumbnail structure and colour ≥ 0.75), spins and dives landing without a tracked face, the loop and `SIGNATURE`, the hero family (`HERO_TINS`: WARN above 4, FAIL above 8), density, generic share and repeats, zoom, the spell-out grid, titles, holds with no beat, and the sound budget (grouped onsets on the effects stem: WARN above 16, FAIL above 30). `PLAN_ACCEPT` in the EDL accepts an item on purpose. Takes 1–5 s. |
| `tools/signoff.py N` · `tools/report.py N` (the Dexter studio's) | Sign-off pages from the encode in 6 s: a row per transition (before, middle, the frame before the cut, the cut, after, end), the loop, the titles, the unexplained pops. The Measured block from the tools' outputs goes to `vN/work/measured.md`. |
| `studio/OWNER_RULES.md` · `studio/WORKFLOW.md` · `studio/CRITIQUE_PROMPT.md` (the Dexter studio's) | The rules on one page; the fast loop with targets (at most 2 owner rounds, at most 2 full renders before a first delivery); the fresh-eyes critique, one agent that predicts the owner's notes before a delivery. |
| `tools/codetrack.py` (inside `vrender.py`) | Change tracking for partial renders. A full render records the renderer functions that drew each frame (`sys.monitoring`, one event per function per frame; no measurable cost, identical pixels). Each function is keyed by its qualified name plus a hash of its own source, so moving code changes nothing. At the next `video`, a frame is dirty when it ran a function that was edited, removed or shadowed by a later layer, read a changed module value or EDL global, or ran a function that caches across frames (`global`, a module dict/list) and calls an edited one. Only those frames re-render, still verified bit-exact outside. A global no traced code reads (`SET_PIECES`, `VO`, audio knobs) renders nothing. Changed SRC/FPS/W/H/DUR_F, cut points, tracks, mattes, bands or helper modules still render in full, and so do changes reaching more than 70 % of the frames. `vrender.py N video --dry` shows what would re-render and why. |
| `tools/signoff.py N` · `build.sh N signoff` (also at the end of `qc`; `review` is its old name) | The one review tool (the Flash studio's `review.py` folded in, 2026-11-08): from the encode, one row per transition and cut, per `SET_PIECES` entry, the loop wrap, the titles and every UNEXPLAINED pop; frames that faceqc or motionqc flagged are boxed red → `vN/frames/signoff_*.jpg` (~10 s) |
| `tools/song_prep.py N SONG [--h0 --h1]` · `build.sh N song:FILE[:H0:H1]` | In one command:<ul><li>the song map;</li><li>Demucs stems of the window ±8 s;</li><li>the grid fitted on the drum stem, against the map's period and its 2/3, 3/4, 4/3 and 3/2 relatives (v106's map locked to 4/3);</li><li>Whisper large-v3 words on the vocal stem (v13's full mix heard "girl" for "God"), in song seconds and edit half-beats;</li><li>loop-wrap scores (bar before H0 vs bar before H1) for the chosen and candidate windows.</li></ul>It writes `vN/work/song.json` and prints the EDL lines. |
| `build.sh` | `plan` runs `plan_check` (with preflight's checks inside); a FAIL stops `video`, `video:A:B` and `fullvideo` (`PLAN_FORCE=1` overrides). `qc` runs `qcN`, `faceqc` and `motionqc` in parallel, then the sign-off pages (`signoff.py`). `prep` prints the plan check and starts `sr_prep` in the background (niced; skipped when the bands are current or it is already running). `rev` = audio plan video qc report; `ship` = `rev` + deliver. An edited `fxN.py` is re-spliced before any rendering step. The scaffold's `audio12.py` logs every `place()` from `main()` to `vN/audio/fx_events.json` (the audio itself is unchanged: identical md5 on v12). |

**Measured (4 cores):**

| | Before | After |
|---|---|---|
| Plan check | none: the owner's round found it | **6 s** (15 s when the audio builder must run in a sandbox) |
| v13 rev 1 run through preflight (retroactively, from git) | the owner's notes after a full build | **with no v13 hindsight in the registry:** 4 FAIL (3 swirls and a whine) and 6 WARN: the black-hole code reached by 7 transitions (the undeclared hero), 24 effects in 21 moments, 11 reverse swells, the bookend reuse (`pull`/`last` in one source shot), a repeated `lens_drop`, the order-dependent cache. That covers two of the owner's five rev 1 notes (the singularity everywhere, the tedious sounds) before any render. On the approved rev 2: 0 FAIL, 2 WARN (the bookend, the cache) |
| An audio-only EDL change (`SET_PIECES`) | a full render (~5 min) | **4 s**, nothing rendered |
| One transition's code edited, no range given (v12 `ecg_bolt`) | a full render, **312 s** | **157 s**: 17 frames found and re-rendered in 15 s, 33 frames outside verified bit-exact; ~140 s is re-encoding the upload at preset slow (kept: it is the upload's quality) |
| Edit, then revert, both partial | — | all 1,401 frames identical to the full render |
| A helper whose result is cached across frames (`grain`, cached by `finish12`) | — | all frames dirty → full render (correct) |
| v13 (`doppler_row` cache keyed on rounded values) | — | the edit found (12 frames); verification caught frame 782 in the horizon shot → full render (safe) |
| QC | ~100 s in sequence (qc 30, faceqc 64, motionqc 5); v13 rev 2 logged 138 s | **72–80 s** with the sign-off pages |
| Review sheets | v13 rev 1: 19 hand-picked `sheet:` calls | **9 s**, every transition, set piece and the wrap |
| Song prep | about six manual steps (map, Demucs, grid fit, Whisper, wrap check, EDL lines) | **one command: 6.8 min the first time (Demucs and Whisper large-v3 on the CPU), 27 s when the stems exist**; on v13 it reproduces the grid within 8 ms and flags "darling" (Whisper e51.2, stem onset e50.4, checked e49.6) for a check on the stem |

**Rules that come with it:**
- **Declare `HERO`, `HERO_TINS`, `SIGNATURE` and `SET_PIECES` in the EDL** and run `plan` before `prep`. Fix every FAIL before the first render; each WARN is a decision, and the handoff says why one was kept.
- **`render(f)` must be a pure function of `f`.** Compute cached values from the rounded key, never from the first caller's exact arguments (the v13 `doppler_row` pattern). Otherwise every partial render falls back to a full one.
- **When the owner removes or dislikes a transition**, add the verdict to `studio/transitions.json` in the same turn (verdict, his words, the fix), then run `preflight.py registry`. Both studios' next plans then carry it.

### 1c, the Dexter studio's half (`sync/EFFICIENCY_PLAN.md`, `studio/WORKFLOW.md`, `studio/OWNER_RULES.md`)

| Command | What it does | Time |
|---|---|---|
| `build.sh N plan` / `tools/plan_check.py N [--edl PATH] [--json]` | The owner's recurring notes, checked on the EDL before any render, against `studio/transitions.json`. Runs automatically before `video`; a FAIL stops the render (`PLAN_ACCEPT = {"check": "why"}` in the EDL, or `PLAN_FORCE=1`). Optional EDL fields: `SIGNATURE`, `HERO_TINS` | 1–5 s |
| `build.sh N rev` / `ship` | audio → plan → video → qc → signoff → report (→ deliver) | one render (partial when the change is local) |
| `build.sh N signoff` / `tools/signoff.py N` | Review pages from the encode: every transition as a row (before, its middle, the frame before the cut, the cut, after, its end), the loop wrap, every text block, every UNEXPLAINED pop → `vN/frames/signoff_*.jpg` | 6 s |
| `build.sh N report` / `tools/report.py N` | The Measured block → `vN/work/measured.md` | 1 s |
| `build.sh N splice` | Re-splice `fxN.py` (automatic before any rendering step when `fxN.py` is newer) | 0 s |
| `studio/CRITIQUE_PROMPT.md` | The fresh-eyes critique: one agent run that predicts the owner's notes from the rules and the sign-off pages | a few minutes |

**The registry** (`studio/transitions.json`): every transition the owner has a verdict on (liked / ok / rejected / banned), with his words, the `fix` for a rejected one, tags (`black_occluder`, `face_gimmick`, `generic`, `signature`, `physical`, `lands_on_face`) and hero `family`. Add a verdict in the same turn the owner gives it.

## 2. Transitions (`tin=` on the incoming shot)

Each transition goes through something. Its sound lives in `audioN.py` (`if tin == ...`): at most one sound, none for a small move, layered sound only at the set pieces (v12, v106).

| tin | What it does | Extra EDL fields | Sound |
|---|---|---|---|
| `tape_in` | Static → VCR roll-in while the song winds up to speed (the loop start) | — | Clunk, motor, static |
| `eye_dive` | Dives into the outgoing face's eye; the pupil swallows the frame; a hexagonal aperture opens | Face track | Heartbeat, shutter blades |
| `assemble` | The next shot builds itself from flying pixel blocks | — | Reversed crumble |
| `polaroid` | Flash; the frame freezes into a print that is tossed away | — | Flash, shutter, print eject |
| `facematch` | Face slides and scales onto the next shot's face | Face tracks | Whoosh, soft hit |
| `tear` | VHS tape tear: sliding bands with chroma fringes | — | Glitch burst |
| `crt` (+ `tout="crt"` on the previous shot) | Frame shrinks into a CRT in the vapor world; the camera dives through the screen with hyperspace streaks | — | Hum, riser, drop impact, degauss |
| `cube` | 3D cube turn over the vapor world | — | Whoosh, landing thud |
| `sun` | A striped retro sun rises; the camera flies through the stripes | — | Riser, chord swell, blind rattle |
| `filmstrip` | The frame becomes a film strip on a light table, whips to the next frame | — | Projector rattle |
| `peel` | Glossy sticker peel from the corner | — | Sticky crackle, flap |
| `ink` | A blood drop falls and splats; the stain blooms open into the shot | — | Drip, splash |
| `slash` | A blade streak cuts the frame; the halves fly apart with blood flecks | — | Swish, steel ring |
| `logo` | voidfx logo as a neon sign, flying through the "o" (**once per edit**) | — | Neon buzz, whoosh |
| `burn` | Film burn holes | — | Fire crackle |
| `lens` | The next shot reflects in the sunglasses; the camera dives into a lens | `lens=(dy, kx, ky)` on the outgoing shot | Glass chime |
| `shadow` | Darkness swallows the frame; the next shot emerges brightest-first | — | Reverse swell |
| `tv_off` | Finger-gun muzzle flash → CRT power-off → power-on | `muzzle=(x, y)` on the outgoing shot | Gunshot, power-off whine, power-on sweep |
| `slidebox_close` (v7) | Dexter's rosewood blood-slide box: the lid slams on a sung word (`CLOSE_T`), with the word engraved on a brass plate; it reopens and the camera dives into a blood drop on a slide | `CLOSE_T` | Creak, wood slam, slides rattling, latch, glass, bloop |
| `burst` (v7) | Kill-room plastic stretches toward the camera (centre-weighted bulge), then bursts into flaps with a blood spray and shock ring; the hero drop transition | Previous shot `plastic=True` | Plastic stretch, riser, rip, sub impact, splash |
| `blood_lens` (v7) | A blood drop falls and splats on the lens; the next shot is seen through it, then drips clear | — | Drip, splat, squelch |
| `zipper` (v7) | A body bag zips shut over the frame, then unzips onto the next shot | — | Zip rasp ×2 |
| `m99` (v7) | Sedative: double vision, blur, the eyelids close; they blink open on the next shot (the music is muffled underneath) | — | Heartbeats, thump, breath |
| `mag_sweep` (v7) | A magnifying glass sweeps in; inside it is the next shot, and the glass becomes the frame (`lensframe=True` on the next shot) | — | Whoosh, glass chime |
| `logo_orig` | The voidfx logo exactly as supplied, slammed in and flown through the "o" | — | Impact, shimmer, whoosh |
| `tout="rewind_end"` | The last shot rewinds at 8× → static → loops into `tape_in` | — | Tape scrub, the song scrubs backwards |
| `mirror_in` / `tout="mirror_out"` (v8) | Push into a rear-view mirror in a dark rainy car / pull back into it (the loop) | `rain=True` | Streetlight hum, whoosh, chime |
| `light_sweep`, `wiper`, `whip`, `whip_up`, `light_leak`, `wrap`, `impact`, `rainfocus`, `lamp_on`, `slam`, `knife_pass` (v8) | The "basic" set the owner liked (streetlight band, windshield wiper, whip pans, plastic wrap, one-frame negative, rain focus pull, lamp switching on), plus the knife roll and pass | — | each has its own sound in `audio8.py` |
| `loop_in` / `tout="drop_moon"` (v9) | The last shot pushes through the drop of blood on a slide until the frame is red; frame 0 pulls back out of the blood moon | `spot=(x, y)` source px of the blood | Plunge, bloop, heartbeat, low-pass "night closes" |
| `tilt` (v9) | One eased vertical camera move: the moon slides up, the shot rises in from below | — | Low air move |
| `foliage` (v9) | The lens passes behind a moonlit bush with white blossoms (a feathered 3.4×W strip) | — | Leaf rustle |
| `petals` (v9) | A gust of jasmine petals blows across the lens, densest on the cut | — | Wind gust, petal flutter, chimes |
| `bloom` (v9 hero) | The (frozen) frame bursts into image-carrying petal cells from its heart outward; they tumble toward the lens, showing their white backs; the next shot is behind | `BLOOM_C` | Breath-in swell, sub boom, a burst of petal flutter |
| `strobe` (v9) | Two soft strobe hits across the cut (never full black or white) | — | Zaps, sub |
| `beam` (v9) | The brightest point (a torch) swings into the lens and whites out; the next shot comes up brightest-first | — | Click, light swell, shimmer |
| `blinds` (v9) | Backlit venetian slats rotate shut, then open on the next shot (staggered top to bottom) | — | Slat rattle ×2 |
| `roll` (v9) | The world rolls 90° with rotational blur (lands on an upside-down shot) | — | Doppler whoosh, floor thud |
| `smear` (v9) | Step-printed long-exposure echoes drag the frame, then settle | — | Tape-warble whoosh |
| `projector_on`, `latex`, `frameslip`, `filmmelt`, `whip`, `hooddark`, `lavalamp`, `slidewipe`, `newsspin`, `papertear`, `oilwheel`, `tout="reel_end"` (v101, in `v101/work/fx101.py`) | 16 mm psych reel: projector strike-up and run-out (loop), a glove-stretch tear, a frame slip in the gate, a film burn-through (hero), a hood over the lens, lava-lamp blood blobs, a blood-slide glass wipe, a newspaper spin and tear, an oil-wheel light show. **v101's look was rejected; reuse transitions only if reworked** | — | Each has its own in `audio101.py` |
| `rewind_in` + `tout="rewind_end"` (v102, in `v102/work/fx102.py`) | The loop as time travel: the last bar plays the whole edit backwards (35× at its peak, picture and sound together via `rew_pos`) and lands on frame 0, whose flash and smear settle into the first shot | — | The song runs backwards (band-limited), tape scrub, crackle |
| `bolt_link`, `overcharge`, `strike`, `emblem`, `passby`, `smear` (light streaks), `impact`, `remnant` (soft) (v102) | A bolt out of the outgoing face's eye splits the frame; his own lightning floods the frame and the next shot burns in through gold; HERO strike (a frozen frame, a leader bolt, two impact frames, a shockwave); the emblem drawn in lightning, fly through the bolt; he passes the lens as a motion wipe; horizontal light streaks; a two-frame impact frame; converging time-remnants | Face track (`bolt_link`, `strike`); previous shot `freeze=True` (`strike`) | Zap / swell / thunder + time-stop / hum + whoosh / doppler / whoosh / hit / shimmer |
| `phase` (v10 r3) | He vibrates through the frame: jittered chromatic copies, row shimmer, every edge lit gold; the next shot shows through for a few frames, then settles | — | Rising saw buzz, whoom |
| `whirlwind` (v10 r3) | The frame twists into a spiral round the eye of a storm (angular blur, wind and debris torn round); the next shot unwinds out of it | — | Wind swirl circling the stereo field |
| `lichtenberg` (v10 r3) | A branching lightning figure grows from his chest (stopping short of his face); the next shot opens inside the branches | — | Growing crackle, snap |
| `lens_shatter` (v10 r3) | A bolt flies at the camera and hits the lens; electric cracks, then the glass bursts toward us in Voronoi shards | — | Whine, glass break, impact |
| `perimeter` (v10 r3) | A lightning streak runs laps round the frame edge; the next shot fills in as a spiral wake closing on the centre | — | Swirl pass, crackle |
| `frozen_shatter` (v10 r3) | In frozen time the frame cracks and the shards hang apart; the beat that restarts time blows them away | `frozen=True` shots | Dull crack, then a glass burst on the hit |
| `time_particles` (v10 r4, replaces `frozen_shatter`) | The frozen moment comes apart into fragments of its own pixels (edges first, people last), they burst and hang in the stopped air, then swirl back together as the next moment from `pfocus` outward, landing on the hit | `pfocus=(x, y)` output px on the incoming shot | Disintegration grains, shimmer, reversed grains into an impact |
| bullet time (v10 r4, automatic on `frozen=True` holds) | In each frozen hold the camera glides through the moment in 3-D: depth from the MODNet matte + a floor gradient drives a parallax remap, plus a dolly push | — | Soft panned air |
| `carry` text (v10 r4) | A lightning runner streaks along the line and drops each word off on its onset; at the end it snatches the letters away (stretch + blur + gold trail) | — | Zips + crackle |
| `rift` (v11 r4, focal point) | A rift tears across the frame (a diagonal path below the face): a crack grows from the centre, splits into a jagged lens with electric edges and light spill; the Speed Force (`speedforce_bg` + lightning) churns inside; the camera flies through; the next shot rushes out of the vanishing point | `rift_geom()` path | Crack, panned rip, reversed swell into a sub drop, roar and whine, arrival impact |
| Reverse-Flash emblem + coin flip (v11 r4) | `rf_emblem(R)`: a procedural, bevelled, lit emblem sprite; `coin_flip()`: the real emblem flips on its axis (edge thickness, inpainted suit behind) to reveal it; flare at edge-on, shockwave and sparks on landing | emblem tracked by a circle fit in the source | Spin whir, sizzle, metal ring |
| REVERSE loop (v11 r3) | `reverse_loop`: a red bolt strikes the tracked chest emblem (found in the source each frame: the cream disc, bolt bridged by a morphological close); the real emblem inverts in place (disc to glossy black, gold to red, shading kept); red radiates over the suit; the camera dives through the black disc, a portal onto frame 0, and lands exactly on it (seam diff 0.10) | `E_STRIKE/E_RADIATE/E_DIVE`, the first shot's `tin="loop_in"` | Thunder, reversed shimmer and boom, crackle and buzz, rush, landing impact |
| `aura=`, `remnants=`, `charge=` (v11 r3) | Beat moments for shots where he only moves to the beat: silhouette rings pulsing out on each beat; time-remnant copies splitting sideways and snapping back; lightning and dust gathering into the chest emblem | per shot (`seg=True`) | Sub pulse and shimmer; doubled panned whoosh; rising hum and crackle |
| `red_eye_dive` (v11 r2) | Dive into the rival's glowing red eye (auto-found: brightest red point) until the frame is red light, then pull out of Barry's eye (face-track landmarks) | — | Power-up whine, rush, sub drop |
| `strobe_echo` (v11 r2) | The frame snaps sideways leaving gold stroboscopic afterimages; the next shot lands with its echoes collapsing | — | Stuttered passes, zap |
| `bolt_trace` (v11 r2) | A zig-zag bolt crosses below the face; the next shot burns in along it (distance transform, ragged ember rim) | — | Panned crackle, fire whoosh |
| `heat_haze` (v11 r2) | Heat rises up the frame (refraction), carrying the next shot in behind a glowing wall | — | Fire roar |
| `clash` (v11 r2) | Red and gold bolts race in from opposite sides and collide; two-colour spark burst + refracting shockwave | — | Two zaps, impact, thunder |
| `bolt_split` (v11) | A lightning-bolt seam cracks down beside the face; red vs gold halves; the seam sweeps across on the drop (tears the title) | — | Crackle build, impact, thunder, sub drop |
| `red_phase`, `red_link`, `red_streak`, `dolly`, `whip`, `speedforce_in`, `emblem_flash` (v11) | The rival's red vibration / arc / streak; a focus-pull dolly; a whip pan; a radial Speed Force pull; the emblem drawn in light where the next shot's chest emblem is | — | each in `audio11.py` |
| `ember=`, `fire=`, `dust=`, `speed=` (v11 r2) | Depth particles (`motes11`): behind the subject through the matte, front ones masked off the face | per shot | — |
| velocity (v10 r5) | `tmap=vel(e0, e1, a, b, lo, hi, tau), lin=True, interp="flow"`: a speed burst on every beat, slow motion between; flow in-betweens run on the restored 2× bands (`sr_flow_part`) | EDL helper `vel()` | The music; optional swish per punch |
| beat camera (v10 r5) | `beat_bounce` 6 % zoom punch + `shake` rotation kick per beat in the hook; `beat_fx` zoom blur + colour split on the hit frames | — | Quiet swish |
| `rays=` (v10 r5) | Screen-space god rays from the brightest warm light (quarter res, 20 samples); scaled down when the frame is already bright | per shot | — |
| `wave=True` (v10 r3) | After the drop: a refracting dark-matter ring rings out of the frame centre | on the drop shot | Sub drop |
| `tunnel_in` + `graphic="tunnel"` (v10 r3 loop) | The letters of a lyric run a ring that opens into the Speed Force; panels of the edit's own moments fly past newest to oldest and frame 0 lands | `T_OPEN`, `TUN_PANELS` | Ring crackle, swirl, panel whooshes, the song rewinding (box-filtered) |

The older v4/v5 transitions are still in the file and work as `tin` values: `kaleido`, `rewind`, `flash`, `tiles`, `neon_trace`, `ripple`, `pixel_sort`, `vhs_roll`. Add new transitions to `TR2` as `fn(A, B, j, f, sa, sb)` with `(fn, frames_before, frames_after)`:
- `j < 0`: A is the live outgoing shot and B is the incoming shot's first frame.
- `j >= 0`: A is the outgoing shot's last visible frame and B is the live incoming shot.

### The v103 FOREVER transitions (the standard; in `fx103.py`, copied into every new edit's `fxN.py`)

| tin | What it does | Extra EDL fields | Sound in `audio103.py` |
|---|---|---|---|
| `plastic_rip` | **THE RIP.** The kill-room plastic tears open down the middle on the drop and the flaps fly apart. Pair it with `plastic=(t0, t1)` on the outgoing shot (the sheet is pulled over the lens first). | `plastic=` on the previous shot | crinkle under the build, riser, tear, impact, whoosh |
| `photo` / `photo_l` | The flash fires; the frame freezes into a crime-scene photo that is tossed right or left onto the next shot. Land it on a sung word. | none | flash whine and pop, shutter click, toss whoosh |
| `shutter` | Six gunmetal camera blades snap shut over the shot and open on the next. | none | shutter ticks and a click |
| `pupil_dive` | The camera dives into his eye (via YuNet's eye position); the pupil swallows the frame and a round iris opens on the next shot. | the outgoing shot needs a face track | reverse swell, rush, low boom, whoosh out |
| `torch_blind` | A light in the outgoing shot (flashlight, lamp, headlights) flares into the lens and whites out the frame; the next shot burns in out of the glare, brightest parts first. | a hot light in the outgoing shot | flashlight click, swell, shimmer, bright hit |
| `ripple` | A clear water drop falls, hits, and the rings refract open onto the next shot. | none | drip, bloop, bubbles |
| `wave` | A rolling, refracting wall of sea spray washes across the lens. | none | wash and splash |
| `bubbles_up` | A surge of rising bubbles sweeps up the frame. | none | bubble burst and whoosh |
| `surface` (first shot) / `sink=True` (last shot) | The loop: it opens underwater rising to the surface (meniscus, droplets on the lens) and ends with the bag sinking into the same water. | `T_SURFACE`, `T_SPLASH` | surface break, splash, underwater low-pass across the wrap |
| `strobe`, `roll`, `whip`, `whip_up`, `impact`, `lamp_on`, `light_sweep`, `wrap`, `zipper`, `rainfocus`, `logo_orig` | Engine moves used in FOREVER as connectors between the set pieces. | see the tables above | yes, each |

### The v103 animation layers (EDL knobs and shot flags)

| Knob / flag | What it does |
|---|---|
| `BEAT_PUNCH = [(k, strength), ...]` | `beat_fx`: the camera punches on the beat, a zoom kick with a stronger chromatic hit at strength ≥ 0.9. **Cover every section with drums** (the §0 target). |
| `PULSE_K = [k, ...]` | `pulse_fx` and a heartbeat thump: the frame edges pulse red and the picture thumps on each beat of a quiet build (with a heartbeat sound). |
| `flare=amt` | `anam_flare`: hot lights throw a long horizontal teal anamorphic streak. Keep it off faces (it was turned off on the night-drive shot because it crossed his eye). |
| `swing=True` | `lamp_swing`: a kill-room lamp's pool of light sways across the shot. |
| `plastic=(t0, t1)` | `plastic_sheet`: milky kill-room sheeting with swaying, light-catching folds is pulled over the lens between t0 and t1. |
| `caustics=amt`, `snow=True`, `rain=True`, `moonglow=True` | water light, marine snow, rain on the glass, a glow on the moon. |
| `TEXT` dicts | `style="cap"` (v9 keyline captions; `band=` for QC, optional `ys=`), `style="hero"` (per-letter title; `exit="bubbles"` or `"blood"`). Word times come from `tools/lyrics.py` (lyrics) or `transcribe.py` (dialogue), each on its sung or spoken time. |

### From Studio 1's standards (v10 LET IT HAPPEN, v11 BOP): the motion pass, source restoration, the v11 engine

These live on Studio 1's branch (`claude/gallant-planck-pqpczp`, read at `122013b`); this copy only records them. Fetch the code from there before relying on it.
- **The motion pass (v10):** `tmap=vel(...)`, `lin=True` and `interp="flow"` on every hook or montage shot (a burst on the beat, smooth slow motion between), plus the beat camera (zoom punch, rotation kick, hit-frame blur and colour split) and light rays. In Studio 2's engine, the closest pieces are:
  - `tmap` ramps (above 1.7x the engine adds shutter blur);
  - `interp="flow"` (clean slow motion only; check the frames);
  - `beat_fx`, `cam_float` and `anam_flare`;
  - `sun_fx` rays.
- **Source restoration (v10):** `tools/sr_prep.py N` with `tools/srnet.py`. It runs Real-ESRGAN compact through ONNX Runtime on the CPU, 2×, only over the horizontal band each frame is cropped from, in the background after prep. It writes `vN/sr/`, and the renderer uses a band when it covers the crop. This replaces the cubic or Lanczos blow-up and is the fix for the owner's v105 clip-quality note.
- **The v11 engine:** v4–v11 with 91 transitions plus the audio builder. Its EDL template adds `E_BEAT` (where the beat drops in), `E_DIP` (the dip before the drop) and `E_LOOP` (where the loop set piece starts; the beat camera rests from there). New v11 pieces:
  - THE RIFT (a focal set piece);
  - the emblem coin flip (a lit, bevelled procedural emblem revealed on the tracked real one);
  - beat moments: aura rings, time remnants, charge-up;
  - heat haze, clash and `speedforce_in`;
  - the REVERSE loop (`reverse_loop` + `loop_in`);
  - `look="voltage"|"rival"`.
- **Flash discipline (v11):** measure every flash in the encode; a flare keeps the picture (v11's rim flash went from mean luma 178 to 104). Studio 2's `qc105.py` (copied into every new edit) reports it in section 7b: white-out runs at mean luma ≥ 200, and flashes per second, failing above 3.

### The Flash studio's techniques (from the v10 and v11 reports; code on Studio 1's branch)

Each is described well enough to rebuild in Studio 2's engine.

| Technique | Function (Studio 1) | How it works | Sound |
|---|---|---|---|
| Velocity ramps | `vel()` in the EDL template | speed = slow + burst·exp(−t/70 ms) on each beat, integrated to source time; flow in-betweens on restored frames | — |
| Beat camera | `beat_bounce`, `shake`, `beat_fx` | about a 5–6% zoom punch and ±1° rotation kick per beat; zoom blur and colour split on the hit frames; type on top | a quiet swish per punch |
| Emblem dive | `emblem_gate`, `drop_wave` | track the chest emblem with keyframes, flare it, zoom into the bolt, burst through into the next shot, then a refracting shockwave | whine, crack, sub, rush |
| TIME PARTICLES | `time_particles` | the frozen frame breaks into fragments of its own pixels (edges first, people last), they hang in the stopped air, then rebuild as the next shot from a focus point on the beat | grains, shimmer, reversed grains into an impact |
| Bullet time | (automatic on frozen holds) | parallax from the person matte plus a floor gradient, with a slow dolly push | — |
| Speed Force loop | (v10 loop) | the lyric's letters run a ring that opens into a tunnel; panels of the edit's own moments fly past, newest to oldest, and frame 0 lands | the song rewinding (anti-aliased) |
| Rival grade | `look="rival"` vs `"voltage"` | a second grade for the antagonist (red-shifted highlights, dark red shadows, red halation) | — |
| Red phase | `red_phase` | jittered red ghost copies (face vibration) resolving into the next shot | crackle |
| Red eye dive | `red_eye_dive` | find the brightest red point (an eye), dive in until the frame is red light, pull out of the next character's eye (face landmarks) | — |
| BOLT SPLIT drop | `bolt_split` | a lightning-bolt seam cracks down beside the face; left half graded red, right gold; on the drop the seam sweeps across, tears the title apart, shockwave | crackle build, impact, thunder, sub drop |
| THE RIFT (focal piece) | `rift` | a tear grows along a jagged diagonal below the face, opens with white-gold electric edges and light spill, the Speed Force churns inside, the camera flies through, and the next shot rushes out of the vanishing point | crack, a rip panned across, reversed swell into a sub drop, roar and whine, arrival impact |
| Coin-flip emblem | `rf_emblem`, `coin_flip` | a procedural emblem (bevelled rim, groove, glossy disc with a reflection, emissive bolt with light spill) lit by the real emblem's brightness; the real emblem flips on its axis (found by a circle fit to its visible edge each frame), edge visible, suit filled in behind; flare at edge-on, shockwave and sparks on landing | spin whir, sizzle, metal ring |
| REVERSE loop | `reverse_loop` | strike → flip → red radiates → an anticipation pull-back and accelerating dive into the black disc (speed-matched blur, radial colour fringes, rays, sparks, a red flare as the rim passes) → lands on frame 0 | power-down whine, tape-stop |
| Beat moments | `aura`, `remnants`, `charge` | silhouette rings pulsing out on each beat; time-remnant copies splitting sideways and snapping back; lightning and dust gathering into the chest | one each |
| Ideas for Dexter (from the Flash studio's reports) | — | rival grade → a cold grade for Trinity or Doakes; red phase → the Dark Passenger surfacing; red eye dive → into a lamp or a blood drop and out of the next subject's eye; BOLT SPLIT → a knife-edge or crack seam; THE RIFT → plastic sheeting or a wound tearing open into the kill room; coin flip → a Miami Metro badge flipping to a blood slide; beat moments → a red aura, ghost remnants, blood gathering; the Speed Force tunnel → a tunnel of case photos or slides; the CARRY OFF runner → a knife glint; depth particles masked off faces (`motes11`) → ash, dust, embers | — |
| Also in Studio 1's catalogue | — | clash, strobe echo, bolt trace, heat haze, whip, dolly focus pull, emblem draw-on reveal, lens shatter, Lichtenberg lightning branches, perimeter lap, phase, whirlwind, speed slices, lightning tear | — |

### The v104 THE PASSENGER toolkit (a standard; in `fx104.py`, carried in every new edit's `fxN.py`)

| tin / flag | What it does | Sound in `audio104.py` |
|---|---|---|
| `graphic="ink_open"` (first shot) | The pickup: bare paper (frame 0 matches the loop's last frame). An ink sketch of the next shot draws itself, one stroke group per beat (`sketch_fx`), ink creeps in from the corners (`edge_seep`), and a drop forms, swells and falls (`drop_at`). | pen and brush scratches, a plink, a reverse swell |
| `ink_bloom` | The drop lands on the downbeat: a crown of droplets, and the bloom spreads with fingered edges and an ink rim; the picture lives inside the ink. | splat, wet bloom, impact |
| `ink_out=dict(k0)` (last shot) | The loop: the picture drains back into one blob on the same ghosted paper, which pulls into a drop and lifts away. | reverse swell, reversed plink |
| `brush` + `brush=dict(ang, seed, red/white)` | A sumi brush band sweeps across: wet ragged front, dry bristly tail, the next shot behind it. Ivory reads on dark footage, red on light; black disappears on dark. | dry bristle swish |
| `page_turn` | The frame turns over like a sketchbook page: paper on its back, a bright fold, cast shadows. | paper flip + whoosh |
| `ink_bleed` | Ink blooms in from several points and retracts onto the next shot (it leaves gaps: no dead black frame). | reverse swell, wet bloom |
| `spatter` + `spat=dict(k, x, y)` | A two-frame red impact; red ink spatter lands on the lens (organic body, elongated drops pointing away, gloss), hangs, then the heavy drops run. Place it off the face. | splat, impact, drips |
| `passenger` set piece: `passenger=dict(k_rise, k_lunge, cut_y)` on a `seg=True` shot, then `tin="passenger"` on the next | A light comes on behind him and the wall goes to lit paper; his matte shadow (body only, above `cut_y`) is thrown beside him, with a crisp ink edge, a red rim, sway, breathing on the bass and rising smoke; two ember eyes open (masked behind him); push-in with a dutch tilt; the lunge pans to centre and both eyes rush the lens; the next shot surfaces through thinning ink. | lamp click, ember ignite, sub drop, rising drone, reverse swell, impact |
| `window=dict(src, a, k_in, k_out)` on a `seg=True` shot | The silhouette: the world goes to paper, his body becomes a window into another shot, his face stays. | a breath of air |
| `roll` / `quarter_roll` / `spin=(a0, a1)` | The rotation motif (the owner's favourite): a spin into an upside-down shot that keeps turning through its hold; a 90° roll into a rotational blur and out upright. | deep spin whoosh + swell |
| `ghost=a` | Ink ghost trails: darker echoes of the last frames of motion (pair with a speed ramp in `tmap`). | (the cut's own) |
| `motes=a`, `swash=dict(k0, k1, y)`, `flare=a` | Ink motes drifting in depth; an ivory brush swash painted behind a hero word; ivory anamorphic flares. | bristle swish for the swash |
| always on | `cam_float` (a breathing camera on every hold), `beat_fx` (punches with radial motion blur on strong hits), the breathing vignette on `PHR`, `ink_drift` in the shadows. | — |

### The v105 DRACULA toolkit (the newest standard; in `fx105.py`, copied into every new edit's `fxN.py`)

Clip quality (the owner's v105 gripe): `tools/sharpness.py N --src` ranks the source crop of every shot (detail, upscale factor, pack bitrate; flags SOFT, ZOOM, LOWBIT) before the render; `tools/sharpness.py N` does the same on the encoded MP4.

| tin / flag | What it does | Sound in `audio105.py` |
|---|---|---|
| `look="day"/"dusk"/"night"` | Per-shot grade: `day_grade` (bleached warm, teal shadows), `night_grade` (cold silver, crimson kept above `redthr`); `dusk_u` slides day → night across `SUN_K` (and back for `daybreak`). | sea air by day, wind and a B-flat drone by night |
| `sun=(x, y)` on a day shot | A sun with light rays (the bright parts streaked away from it, quarter-res), a glow and lens ghosts (`sun_fx`). Dusk shots set it down the right edge, off the face. | — |
| `sun_flare` | A flare crosses the frame at the sun's height and whites it out for a moment. | bright whoosh + glint |
| `bat_burst` | The drop: a 3D cloud of bats pours out of the sky toward the lens, blacks out the frame against a crimson flash, and flies past (depth blur on the near ones). | reverse swell, sub impact, a burst of wings, chirps |
| `bat_swarm` | A river of bats crosses in depth (parallax, size and blur by distance); a band of moonlight travels behind the column so they read; the cut rides its middle. | wings panned left to right |
| `bloodmoon=dict(k0, k1)` on a `seg=True` shot | A procedural blood moon (maria, craters, limb darkening, the Earth's-shadow edge) rises behind his matte, with cloud, bats, a pulse and a red rim on him. | church-bell toll on B-flat |
| `moon_iris` | A circular iris opens from the dark with a crimson rim. | reverse swell, toll, sub |
| `coffin` | A height-map-lit lacquered coffin lid with a brass cross falls to the lens, slams (jolt, dust) and lifts away on the next shot. | hinge creak, wood thud, dust |
| `daybreak=True` on the last shot + `seam_out` | Dawn light rises, the sun comes up low right, the frame burns white, then crossfades into frame 0 (which opens at `SEAM_W` white). | B-flat-minor chord swell, tail wrapped into frame 0 |
| hero `exit="bats"` | The per-letter hero title (red flood) breaks into crimson bats that scatter sideways, away from the face. | a small flutter |
| `fog=a` | Night fog drifting through the shot. | — |
| `cape` | A Dracula cape sweeps across the lens: black satin in broad moving folds, a crimson lining turned out along the billowing edge, a lit hem, motion blur, a shadow thrown ahead; the next shot is behind it. | heavy cloth whoosh |
| `mist` | He turns to mist: the shot softens and rises into billowing silver fog; the next condenses out of it, soft to sharp. | airy breath + hollow whoom |
| `bat_pass` | One great bat flies out of the dark through the lens (soft when near, wing bones in the membrane, fine crimson edge); the cut is in its shadow; it dives out under the camera. | three heavy wingbeats, whoosh, chirps |
| `motes=a` on a day shot | Sunlit dust: drifting motes, brighter near the sun, sharp far and soft near, kept behind him with the matte. | — |
| `seg=True` on a sun shot | The sun sits behind him: disc and rays only from the sky, a light wrap on his near edge, ghosts dimmed by how much he covers. (rev 2 fix: the sun used to be laid over his hair.) | — |
| `eclipse` | The sun goes out: the moon's black disc slides across with a streaming corona, the next shot inside it, a diamond-ring flash on its rim, then the disc swells to fill the frame. | reverse swell, deep impact, shimmer, low bell |
| `card_flip` | A 3D card flip around the vertical axis against the bright blurred sky of both shots (a sun glint edge-on). | whoosh + flick |
| `palm_sweep` | Procedural palm fronds sweep past the lens (depth blur, dappled light); the next shot comes in their shadow. | leaf rustle + whoosh |
| `gather=True` (+ `seg`) | Bats gather in the sky behind him through the shot, more and more toward its end. | — |
| `rim=a` (+ `seg`) | A pulsing crimson backlight on his edge. | — |
| ASHES TO SUN (`daybreak` on the last shot; `ASH`, `SUN_T`, `seam_out`) | The loop: he burns like paper (char, glowing line, the street behind him, row-continued); 3,000 embers spiral into the sun at frame 0's sun position; the sun flares over the frame and the light collapses back into it, revealing frame 0. | crackle, hiss, riser, flare impact + shimmer, reverse swell, bloom on the loop |
| `daybreak=True` + `seg=True` | He burns in the sunlight: a flickering hot rim on his edge, embers lifting off his hair and shoulders, then the white. Needs a shot with a clear silhouette (not a frame-filling close-up). | sizzle + crackle |
| always on | `render_shot` upscale: Lanczos + a noise-gated luma detail boost (not AI super-resolution). `finish105`: warm or moonlit halation and a crimson bloom (skipped on logo frames). | — |

### The v106 WONDERWALL toolkit (a standard; The Flash, on the v11 engine; in `v106/work/fx106.py`, spliced above the speed section of `render106.py`)
Port by copying the functions into the edit's own section (`tools/splice_section.py`). Full recipes in `sync/handoffs/2026-11-08_dexter_v106_WONDERWALL_standard.md` §8.

| Piece | Call | What it does |
|---|---|---|
| TEAR LENS | `tin="tear_lens"` (60 / 26 frames), `drop_over` | A lit water drop gathers on the outgoing face's jaw holding the next shot (minified, then the whole frame), hangs, falls toward the lens and fills the frame; the lens relaxes and a ripple runs out, masked off the incoming face. Give it ~1 s. |
| Lightning rod | `tin="lightning_rod"` (6 / 20) | A leader flickers down beside the next face (330 px aside, never on it); the strike; the next shot burns open outward from the bolt with an ember rim. |
| Clash below the face | `tin="clash106"` (10 / 14) | v11's clash with the collision 110 px under the face box and every spark masked off a face ellipse. |
| Speed Force mist | `mist=1.0` (shot flag), `mist_swirl` (10 / 16), `mist_over`, `mist_field` | Drifting cobalt fractal mist behind the matte (sub-pixel drift, never wraps), a cold flicker on the half bar; as a transition, a refracting cover ≤ 88 % that closes from the edges and clears exactly, with the plates dissolving under it. |
| THE WONDERWALL | `wall=1..3` (shot flag), `wall_tex`, `wall_frame`, `wall_state` | A running-bond wall of bevelled tiles cut from the edit's own source frames (warm sepia), gold mortar light breathing on the beat, in perspective behind the matte; rises tile by tile, cracks with lightning along the mortar, shivers before the burst. |
| THE WONDERWALL burst | `tin="wonderwall"` (12 / 30), `tile_split`, `tiles_of` | The frame becomes the wall, then its tiles fly toward the camera from the centre (the ones over the face first), gold light and a shockwave behind them. |
| Loop mist | `tout="loop_mist"` on the last shot, `loop_w`, `sf_virtual` | The mist rolls over the lens; the picture under it dissolves into frame 0's, whose background animation is rendered at the wrap's virtual negative frames; frame 0's finish fades in. Seam 0.14. |
| Title forged from light | `style="wonder"` in `TEXT`, `text_wonder` | Bevelled white-gold letters with a cobalt glow, struck one by one over the sung word, phasing out as vibrating ghosts. |
| Smooth shiver | `shiver(shape, f, seed)` | Per-element sines at 9–15 Hz for tremble (no per-frame random). |
| WONDER grade + finish | `look="wonder"`, `grade`, `finish106` | Amber highs, cobalt shadows, milky blacks by `tone_lut`; halation kept off the face box (its weight can be faded, for the loop). |


### The v107 ALL CAPS toolkit (the newest Dexter standard; on the v12 engine; in `v107/work/fx107.py`, spliced above the speed section of `render107.py`; every `--base v107` scaffold carries it)
Restyle it in the new edit's `fxN.py` and re-splice with `tools/splice_section.py N vN/work/fxN.py --replace`. Full recipes in `sync/handoffs/2026-11-08_dexter_v107_ALL_CAPS_standard.md` §8.

| Piece | Call | What it does |
|---|---|---|
| TABLOID grade + finish | `look="tabloid"`, `grade`, `finish107`, `redthr` (per shot) | Tone LUT; spot red kept above a per-shot red threshold (red-lit skin stays out); paper tint in the highlights; a misregistered red-plate ghost, a fine shadow screen, paper grain. |
| HOT MOLASSES | `tin="molasses"` (36 / 24) | A viscous blood sheet pours down the lens: fingered leading edge with a bead, sliding undulations, refraction, absorption by thickness, gloss; drains from the top with a meniscus. |
| HEADSPIN | `tin="headspin"` (20 / 24), `spin_about` | Two turns, multi-sample motion blur and radial blur; the incoming half turns about the incoming face's centre and lands at 0° on a centred face. |
| THE FRONT PAGE | `tin="frontpage"` (82 / 28), `page_layers`, `page_with_photo`, `halftone` | The MIAMI GAZETTE (masthead, BAY HARBOR / BUTCHER in spot red, columns) spins in with his halftone photo and caption, lands, settles; we dive into the photo and its dots resolve. |
| ALL CAPS stamp | `style="stamp"` in `TEXT`, `strip_canvas`, `text_stamp`, `banner_target` | A torn newsprint strip slaps on; letterpress letters on an even 16th grid, each landing on its hit (3-frame descent, ink spread, deboss, strip shake); at the cut it flies onto the real banner's DEXTER. |
| Banner shot | `banner=True`, `banner_frame` | A 1.2× crop tracking the banner, the sky extended from the source's own top and bottom colours, so a wide sign fits whole in 9:16. |
| Confetti | `pop=True` + `tin="confetti_pop"`, `conf_set`, `draw_confetti`, `pop_behind` | Lit, fluttering paper pieces with depth of field in the edit's palette; bursts in the sky, carries on behind the person matte. |
| THE MASSES SPELL HIS NAME (loop) | `tout="name_loop"`, `name_targets`, `draw_pieces`, `name_loop` | ~1,050 confetti pieces swirl in from both sides at chest height and form a word (a text mask), hold through the drop-out bar, burst toward the lens and down while `frame0_plate()` dissolves in; the last frame is frame 0. |
| PAGE TURN | `tin="page_turn107"` (14 / 12), `pt_back` | A true cylinder roll from the bottom-right corner: flat front, the rising quarter (front, foreshortened), the top of the roll and the turned part (newsprint back with the picture faintly showing through), the roll's shadow on the next shot. |
| Edge-clamped colour split | `rgb_split`, `_shift_edge` | The beat-hit colour split repeats the edge column instead of wrapping (`np.roll` left a cyan/magenta edge line). |
| Rejected in v107 (kept, working) | `press_flash`, `broadcast` (TV), `spatter_fx`, `rorschach` | Reuse only with the lessons: no black room around a screen; never converge on a face. |

## 3. Graphics and text

- **v9 graphics and type** (`render9.py`, end of file):
  - `freeze_e=E` on a shot: a dead freeze on the song's silence with 2.5-D parallax (matte vs. background), violet drain and a moonlight rim;
  - `petals=density`: a jasmine-petal depth field (behind the person matte, soft bokeh in front that keeps off the face; it freezes with the picture);
  - `graphic="moon"`: a still blood moon on a generated night sky with moonlit wisps;
  - TEXT style `cap` (**the approved standard text, "it was perfect"**): bold two-line captions with a dark keyline and soft shadow, auto-fit to 940 px, red emphasis (`emph`), optional `from` and `big`;
  - TEXT style `hero`: per-letter bloom-in on a shared baseline; line 2 floods crimson from the bottom; the exit blows the letters away as petals;
  - `accents9`: soft strobe lifts on every clap after the drop.


- **Captions** (`CAPS`): two-line retro lockups. Each word eases in on its spoken time (fade, rise, blur-to-sharp) with pink and cyan echoes; emphasis words are chrome. The `vanish` style dissolves into pixels.
- **Drop title** (`DROP_TITLE`): a chrome word sweeps in from the left, with a light sweep.
- **End words** (`END_CAP`): neon tubes that ease in and flicker on, word by word, and spill coloured light onto the face.
- **v7 graphics:**
  - evidence markers (`markers=True`) drop in on the beat;
  - the CASE CLOSED rubber stamp (TEXT style `casestamp`);
  - the kill-room plastic layer with the luminol title (`plastic=True`);
  - the magnifying-glass lens frame (`lensframe=True`);
  - blood spatter hits on montage beats;
  - the forensic viewfinder.
- **Shot flags:**
  - `vapor_bg`: the person stands in the vapor world, then reality tunes in scanline by scanline (person matte);
  - `palms`: palm-frond shadows;
  - `motes`: bokeh specks;
  - `echo`: VHS colour trails;
  - `pause=FRAME`: VHS ‖ PAUSE freeze with jitter;
  - `vanish`: pixel-dust dissolve, timed by `VANISH_T0`.
- **Montage** (`MONTAGE` half-beat range): beat bounce, glints, light leaks and hits on the downbeats.
- **Finish:** bloom, anamorphic streak, VHS chroma bleed and scanlines, vignette, grain. The OSD is limited to PLAY ▶ at the start, ◀◀ REW at the end and ‖ PAUSE. **No SP counter or timecode.**

- **v101 / v102 graphics (Studio 2).** These are built on the v7 engine, not v9: port a piece into the v9 engine before reusing it.
  - v101 (look rejected): a liquid-light projection behind the person matte; prism silhouette echoes on bass accents; a 16 mm film finish.
  - v102 (The Flash):
    - `sarcs` lightning that hugs the silhouette (person-matte contour);
    - `echoes` matte afterimages;
    - `motes` frozen-time sparks in depth;
    - `eyespark` arcs off the YuNet eye landmarks;
    - `freeze` (a colour drain on a held frame);
    - `rot` (a sideways source rotated to fill 9:16);
    - an electrified slammed title.
- **Is he really saying it?** Run `python3 tools/lipcheck.py SRC t0 t1 OUT.jpg --vocals STEM.wav [--stem-t0 S]`. It draws face and lip crops every 0.1 s with the speech level under them. The lips must move with the bars before a line is used as lip-synced. (An automatic mouth-motion score disagreed with known cases, so judge it by eye.)

## 4. Pitfalls that cost time in v6 (check these first)

1. **Override layering.** `renderN.py` contains several `render()` functions, and the **last one wins**. When inserting routing with a string replace, target the active `render()` (after the "v6 frame" marker) or the change silently does nothing.
2. **Optical flow fails on lighting jumps** (police lights, flashes) and leaves dark blocky blotches. The sampler already falls back to a blend when consecutive frames differ by more than 6 levels; keep that fallback.
3. **Angle morphs can't be seamless.** Morphing an unfolded frame into a kaleidoscope fold always leaves a wedge seam. Dissolve into the full fold instead.
4. **`cv2.putText` only draws on 8-bit images.** The frames are float, so draw shapes or use the PIL `text_mask` helpers.
5. **Motion blur must match the real per-frame speed**, not a guess. The film strip smeared because its blur was about 30× too long.
6. **Face landmarks under caps and sunglasses** sit on the top edge of the lenses. Give lens transitions the real lens shape per shot (`lens=`).
7. **Faces wider than the 9:16 window** (big profiles, two-shots): check the YuNet width before picking a shot (`analyze.py` sheets print `w`) and reject anything over about 400 px of a 720p source.
8. **Titles must end before the next transition starts.** MIAMI over the cube looked broken.
9. **Quiet-section transitions and VO:** keep caption lines inside 1280–1640 px and keep them two-line, never one long line.
10. **Never wait on a full render to test a transition**: use `auto`, `sheet:`, `strip:` and `clip:` (render server).
12. **Packs hide cuts the shot detector misses** (a jump to a closer angle, the next scene starting a few frames early). Interpolating across them makes a ghost frame, and running a source range past the shot's end puts another actor on screen. The sampler now holds frames across hard cuts; `tools/check_sources.py N` (run automatically by `build.sh N prep`) now fails any shot whose source range leaks past a source cut (found twice on v7).
13. **Text vs very tight close-ups:** a face box that fills the 9:16 frame leaves no text-safe band. Swap the shot (v7: the "Could it be him?" close-up → kill-room floor) rather than shrinking the type.
11. **CJK subtitles and VHS counters read as clutter** to the user. Don't add them.
14. **Whisper word times drift on sung, held notes** (v10: up to 1.1 s early on "All this running around", ~0.2 s late on others). Before captions go in, check every word against the Demucs vocal stem: a 30 ms RMS + pitch track shows where each syllable starts, and the line's parallel phrase (verse 1 vs verse 2) confirms it.
15. **A 720p pack cropped to 9:16 is a 2.7× blow-up.** Run `tools/sr_prep.py` (restoration + 2× from the network) instead of cubic + unsharp mask; the renderer drops the unsharp mask to 0.16 on restored frames.
16. **Soft shots (Studio 2, DRACULA):** check every shot with `tools/sharpness.py` while picking and on the finished video; zoom ≤ 10 % on 720p; close-ups on the least-compressed packs. The detail score is per-tile (80th percentile), so a shallow depth-of-field background doesn't read as soft, but motion blur and restoration-smoothed skin do.
17. **The automatic beat map can lock to the wrong tempo** on a swung strum (v106: 116 BPM, 4/3 of the real 87.02). Fit the grid on the Demucs drum stem and check that the downbeats sit on its kick onsets.
18. **Whisper's small model drifts by seconds on sung lines** (v106: "I said maybe" 3.4 s early). Use large-v3 on the vocal stem and check each word against the stem's envelope.
19. **Procedural textures:** drift in whole low-res pixels steps visibly (a jump every ~3 frames); crop at sub-pixel offsets (`crop_frac`, bilinear). A `%` wrap on the noise canvas jumps at negative time and breaks the loop's virtual frames; make the canvas big enough for −1.5 s … DUR + 1 s.
20. **Cover formulas that don't reach exactly 0 and 1** leave the corners covered at u = 0 and pop at the transition's ends (v106 mist: fixed with an offset of `1.22 − 1.55u`). Assert `cover.max() == 0` at u = 0 and `cover.min() == 1` at u = 1. Likewise a pre-roll progress of `j/(pre+1)` never reaches 1 before the cut and makes a framing jump; use `j/pre`.
21. **Source VFX flickers** (S3 Speed Force pink-orange flash at `flash_s3.mp4` 134.37–134.47 s) become pops under flow and transitions. Start the range after them.
22. **Held 24p shots in a 60p edit judder** next to flow shots (2:3 cadence: big, small, big, small, small differences). `interp="hold"` on 24p content in `flash_b_hq` (60 fps container) did this in v106 and in v12's strike shot; use `interp="flow"`. v12's crouch (`flash_s5`, flow set) still measured a cadence run at 777–834: check where flow falls back.
23. **Hidden jump cuts survive `check_sources.py`** when the angle change is small (same suit, same light): `flash_s5.mp4` 73.50 s cuts to a closer angle inside v12's street shot and left a ghost frame at 736. `motionqc` lists it as an UNEXPLAINED pop; probe each range with a frame-difference scan of the source.
24. **Library transitions can sample past their shot.** v11 `bolt_trace` showed the next pack shot in v13. Pull frames of any library transition before using it.
25. **The engine holds frames when flow is refused** (mean frame difference over 14 levels at 1/8 res), which is 30p judder on fast shots. Use `flowmax` per shot (v13), and `flowfall="blend"` where a lightning jump would warp.

## 5c. Port candidates from the Dexter studio (v105 DRACULA)

These live in `v105/work/fx105.py` / `qc105.py` on the Dexter studio's branch; port them when the branches merge.

| Asset | What it does | Flash restyle |
|---|---|---|
| `sun_fx(..., m)` | A light source behind the subject: rays from the sky only, light wrap on the near edge, lens ghosts dimmed by how much of the source he covers | The lightning glow / Speed Force light behind Barry (fixes rule 13 for our `light_rays`) |
| ASHES TO SUN: `ash_setup`, `ash_body`, `ashes_fx`, `clean_plate`, `seam_out` | The subject burns away like paper (burn-order map: edge distance + direction to the light + noise), 3,000 embers spiral into frame 0's focal point; the hole filled row by row | Barry disintegrates into lightning sparks that fly into the emblem |
| `eclipse_tr` | A disc wipe with corona and diamond ring | The emblem as the eclipsing disc |
| `bat_burst`, `bat_swarm`, `bat_pass_tr`, `bat_sprite` | A 3D flock with depth projection and depth blur | Debris, sparks or shards in depth |
| `coffin_lid` | A height-map-lit prop (normals, diffuse, specular) | Emblems, the cowl, a S.T.A.R. Labs door |
| `moon_tex`, `bloodmoon_fx` | A procedural moon behind a matte | A planet or a singularity behind Barry |
| `mist_tr`, `cape_tr`, `card_flip`, `palm_sweep` | Smoke dissolve, cape sweep, card flip, foliage sweep | Speed-wind sweep, a card-flip of a photo |
| QC §7b flash measurement | Flags white-out runs and flash rate on the encoded file | **Ported** into `v11/work/qc11.py` §7b (so every new Flash edit has it) |
| Their `tools/sharpness.py` metric | detail = mean \|L − blur 1.2\| / mean \|L − blur 8\| over the middle of each shot; flags SOFT, ZOOM (> 3.1×), LOWBIT (< 800 kb/s); absolute scale, ≈0.30+ sharp | Ours scores relative to the edit's median and flags zoom at > 2.95× (z 1.10); LOWBIT adopted. Pick one tool at the merge |

## 5e. Port candidates from the Dexter chat's Flash edit (v106 WONDERWALL)

All in `v106/work/fx106.py` on `origin/dev/pipeline-v2` (557 lines, spliced above the speed section of `render106.py`; built on the v11 engine, so the names match ours). Read it with `git show origin/dev/pipeline-v2:v106/work/fx106.py`. Port a piece by copying its functions into the new edit's section and registering it in `TR2`; restyle the colours (`COBALT`, `WGOLD`, `WCORE`, `MIST_*`) to the new edit's look.

| Asset | Functions (pre/post frames) | What it does | Use in a Flash edit |
|---|---|---|---|
| **TEAR LENS** | `tear_lens`, `drop_over` (60/26) | A water drop gathers on the outgoing face's jawline (radius 4 → 34 px), hangs and swells (44 px), then falls and grows to fill the frame (`44·exp(ln(1500/44)·v^2.3)`). Inside it, the next shot through a magnifying lens (`q = P + d·m(ρ)`, `m = (1 − L(1 − ρ²))·mag`, mag 6 → 1, L 0.42 → 0.25); dark Fresnel edge, gold/cobalt rim, highlight and caustic, a skin shadow; after the cut the lens relaxes and a ripple ring (masked off his face) runs out. Sound: a plip, a reversed swell, a low muffled bloom with a sub. | Any reverse-shot reveal (a goodbye, a memory); a drop of rain or sweat, or a lens of light in the Speed Force. Give it ~1 s. |
| **THE WONDERWALL** | `wall_tex`, `wall_quad`, `wall_frame`, `wall_state`, `wall_layer` | A running-bond wall of 6 × 11 tiles cut from the edit's own frames (bevelled, warm-tinted, gold mortar), perspective-warped, behind his matte at 90 %. It rises tile by tile, its mortar pulses on the beat, lightning crawls along the mortar before the burst, and it trembles in smooth sines. | A wall of moments behind him (his past, the Speed Force's memories). |
| **WONDERWALL burst** | `wonderwall`, `tile_split`, `tiles_of` (12/30) | The frame becomes the wall, its tiles shiver, then fly at the camera from the centre out (zoom 1 + 4.5·w^1.25, rotation ±60°, motion blur), tiles over his face first; the next shot behind in decaying gold, a shockwave ring. | A focal burst made of the edit itself. |
| **Speed Force mist** | `fbm`, `crop_frac`, `mist_field`, `mist_rgb`, `mist_layer`, `mist_cover`, `mist_over`, `mist_swirl` (10/16) | Two fractal noise layers drifting sub-pixel from a canvas that never wraps; cobalt body, pale wisps; behind his matte with a cold lightning flicker, or as a closing radial cover that refracts the picture (≤ 88 %, exactly clear at both ends). | Inside the Speed Force; a cover transition that hides a dissolve. |
| **Loop mist** | `loop_mist`, `loop_w`, `sf_virtual` | The cover peaks at 55 % of the last 1.38 s; between 40 % and 62 % the picture under it dissolves into frame 0, with frame 0's mist rendered at virtual frame f − DUR, and frame 0's finish fades in. | The pattern for any loop that should keep moving across the wrap. |
| **Lightning rod** | `lightning_rod` (6/20) | A gold leader flickers down 330 px beside the next face, strikes, and the next shot burns open outward from the bolt (distance field, radius 30 → 1,130 px) with an ember rim. | A strike link that never touches a face. |
| **`clash106`** | `clash106`, `clash_at` (10/14) | v11's clash with the collision 110 px below the face box; every spark and ring masked off a face ellipse. | Replace v11's `clash` with it. |
| **WONDERWALL title** | `text_wonder`, `wonder_letter` | Bevelled white-gold letters with a cobalt glow, each struck on its share of the sung word (ease in, scale 1.35 → 1, blur to sharp, a gold flare), exiting as vibrating ghosts. | A held sung word, if the edit has a title. |
| **WONDER grade** | `lutw`, `grade`, `finish106` | One `tone_lut` table grade; halation kept off faces with an ellipse mask. | Don't reuse the look; reuse the construction. |
| **The audits** | (scratchpad scripts in the Dexter chat) | Dead spans, pops, judder. | **Built here as `tools/motionqc.py`.** |

**What made v106 a standard (carry the principles, not the look):**
- **A story, not a motif.** The lyric line maps onto a real arc in the show (S3 finale → S4 premiere), so every set piece is a beat of that story: into the Speed Force, her tear, he is saved, the wall, back into the Speed Force.
- **The focal piece is made of the edit itself** (the wall's tiles are the edit's own frames; the burst turns the current frame into the wall).
- **Fewer sounds was better:** a strike, a clash, a run, the wall and the burst; after the burst, only the music.
- **Measured, not guessed:** a per-beat activity table found the dead span, a pop list found six defects (three invisible on stills), a cadence check found the 24p judder.

## 5g. Port candidates from the Dexter studio (v107 ALL CAPS, standard)

All in `v107/work/fx107.py` on `origin/dev/pipeline-v2`, written for the v12 engine, so they splice into a Flash edit as is. Read it with `git show origin/dev/pipeline-v2:v107/work/fx107.py`.

| Asset | Functions (pre/post frames) | Flash use |
|---|---|---|
| HOT MOLASSES | `tin="molasses"` (36/24): a viscous sheet pours down the lens with a fingered edge and bead, refracts the shot, absorbs by thickness, glossy highlight, drains with a meniscus | Molten light or liquid lightning pouring over the lens |
| HEADSPIN | `tin="headspin"` (20/24): two turns on a smoothstep, angular motion blur; **the second half turns about the incoming face's centre** | A spin into a centred face (rule 5) |
| THE FRONT PAGE | `tin="frontpage"` (82/28), `page_layers`, `page_with_photo`: a newspaper built from text masks spins in, lands, and we dive into its halftone photo | A Central City Picture News front page (Iris's byline, "FLASH MISSING") |
| ALL CAPS stamp | `style="stamp"`, `strip_tex`, `strip_canvas`, `text_stamp`: letterpress letters on an even grid, ink spread, emboss, then the strip flies to a target (`banner_target`) | Any spell-out on the beat grid (rule 4) |
| Banner shot | `banner_frame`: a crop tracking a wide object at 1.2×, the sky extended from the source's own colours | Fitting a wide prop or sign into 9:16 |
| Confetti | `conf_set`, `draw_confetti`, `confetti_pop`, `pop_behind`: lit paper pieces with flutter and depth of field, behind the matte | Sparks or embers in depth |
| THE MASSES SPELL HIS NAME (loop) | `name_targets`, `draw_pieces`, `name_loop`, `frame0_plate`: 1,050 pieces gather into a word, hold, burst into frame 0 | A loop built from the edit's own particles |
| PAGE TURN | `tin="page_turn107"` (14/12): a true roll over a cylinder, newsprint back, the roll's shadow | A page of the Picture News |
| TABLOID grade | `look="tabloid"`, `grade`, `finish107`, per-shot `redthr` | Don't reuse the look; reuse the spot-colour construction |
| Edge-clamped colour split | `_shift_edge`, `rgb_split` | **Ported** into `v12/work/render12.py` |
| QC transition windows | `qc107.py` `_tr_window` | **Ported** into `v12/work/qc12.py` |
| Rejected in v107 (reuse with care) | `press_flash`, `broadcast` (avoid the black room), `spatter_fx` (never converge on a face), `rorschach` | — |

## 5f. Reusable from v13 EVENT HORIZON (approved, not a standard)

All in `v13/work/sec13.py`.

| Asset | Functions | Notes |
|---|---|---|
| LIGHT RIBBON (graphic, then transition, then loop) | `ribbon_pts`, `ribbon_canvas`, `ribbon_light`, `ribbon_draw`, `ribbon_orbit`, `ribbon_spiral`, `ribbon_loop` | Two twisting light bands on a tilted orbit in depth (behind the matte, in front of the chest), a current and sparks; spirals out with the next shot inside its loop. Keep the orbit at the shoulders and fade it before it lingers on a face |
| EMBLEM SPLIT | `emblem_split`, `zig_pts` | The real emblem's bolt ignites, leaps off and splits the frame along its zigzag. Shift the masks with a constant border |
| EDGE CURRENT, FOCUS RACK, EYE IRIS, TIME SLICE, PANEL RUN, AFTERIMAGE, LIGHT LEAK, SPEED WHIP, WHIP UP | `edge_current`, `focus_rack`, `eye_iris`, `time_slice`, `panel_run`, `afterimage`, `light_leak13`, `speed_whip`, `whip_up13` | General designed moves; afterimages only on the speedster |
| Black-hole kit (use once) | `bh_warp` (point-mass lensing), `bh_disk`, `bh_draw` (`inner=` throat), `clean_plate`, `doppler_row`; `horizon_fx`, `event_horizon_tr`, `grav_wave`; EDL `dilate()` | Lensing behind a matte needs `clean_plate`, or a ghost of him follows his edge |
| Smoothness | `src_weights` with `flowmax` / `flowfall` | The engine refuses flow above a 14-level frame difference (30p judder on fast shots) |

## 5d. What made v12 the standard (carry the principles, not the look)
- **One hero asset, many stages.** The lightning jasmine (`jas_draw`, `jas_light`, `jas_geom`, `jas_veins`) appears as:
  - a bud in his pupil;
  - a frame-filling bloom on the drop;
  - a flower behind him (`behind`: light only from the background, plus a wrap);
  - the petals of the cracked emblem;
  - the closing bud the camera dives into.
- **Transitions:** strike link, ECG bolt, bud iris, `bloom`, `full_bloom` (in), petal pass, pollen burst, petal whip, `fractal_burn`, `emblem_bloom`. Library moves are restyled by repointing `GOLD*`, `RED*` and `EMBER2`.
- **Tools:**
  - `emblem_at(s, f)` finds the real chest emblem (Hough on the source frame through `to_screen`);
  - `face_guard` keeps beat moments off faces;
  - `flash_governor` caps flare frames;
  - `tame` turns coloured light to cream without touching the suit.
- **Restraint the owner asked for:** no text (both titles removed) and 37 effects instead of 87.

## 5b. What made v11 the standard (carry the principles, not the look)

- **A concept found in the material:** the song's spoken "Harrison" became the whole edit (the Reverse-Flash rivalry): a second grade for the rival, red against gold at the drop (the bolt split), the gold winning on the punch (the clash), the red taking the symbol at the end (REVERSE).
- **One focal set piece:** THE RIFT, on the bar line after the charge-up: a tear grows, opens with electric edges, the Speed Force inside, the camera flies through, the next shot rushes out of the vanishing point.
- **Detailed hero assets on real objects:** the procedural Reverse-Flash emblem (bevel, brushed rim, groove, glossy disc, emissive bolt, light spill, matched to the shot) revealed by a coin flip of the tracked real emblem (circle-fit each frame, the suit inpainted behind it).
- **Beat moments for "moving to the beat" shots:** aura rings, time remnants, a charge-up, each with a sound.
- **A loop that lands:** the dive ends on frame 0's own image (seam 0.11), and the beat camera rests during it.
- **Measured finish:** flash brightness measured in the encode, particles masked off faces, every new effect checked at full resolution.

## 5a. What made v10 the standard (carry the principles, not the look)

- **Motion first.** Velocity on every hook shot (`vel()`: a burst on each beat, ~0.3–0.6× flow slow motion between, the same source range), the beat camera (6 % punch, ±1.1° kick, zoom blur + colour split on the hit frames), bullet time in frozen holds. Without this, effects on static shots read as lacklustre.
- **Quality.** `tools/sr_prep.py` restoration on every 720p pack; flow in-betweens run on the restored bands (`sr_flow_part`), so slow motion stays sharp.
- **Set pieces from the character's world** on the drop (emblem dive + drop wave), the hook (lens shatter, perimeter lap), the freeze (time particles) and the loop (the AROUND ring → the Speed Force → frame 0), with signature moves between them (phase, whirlwind, lightning branches), each with its own layered sound.
- **Type on the sung onsets**, every word verified on the vocal stem; each lyric moment acts out its meaning (runner drop-off and carry-off, the charge fill, the ring).
- **Graphics with depth that react to the footage:** the matte-aware whirlwind and ribbons, light rays from the real lightning, edge arcs on the silhouette.
- **Reviews:** stills of every transition at full size, the loop seam measured (blurred diff ≤ 1), QC flags checked visually and written into the README.

## 5. What made v6 the benchmark (carry the principles, not the look)

- **A concept that ties picture, sound and text together:** VO about disappearing, then he dissolves; the drop goes *through* a CRT; the ending confession lights up word by word; the loop is a tape rewinding into static, then the tape loading.
- **The music drives the structure:** the cold open sits on the song's filtered build, and the full-mix return lands exactly as the camera passes through the screen. Every cut sits on the half-beat grid.
- **Every transition is designed, "goes through something" and has its own sound.** No plain cuts.
- **Text is meaningful (the character's own words), eased in, two lines, and designed per moment.**
- **Built-in review passes** caught real problems before delivery, every time.
