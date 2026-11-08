# voidfx studio: development handoff

This is the starting point for building a fully autonomous and manual editing studio on what exists today. It explains how the current studio works, where every preference and note lives, what each edit taught, the quality gates, the engine's interfaces, the requirements, and the known gaps.

**Snapshot:** branch `claude/gallant-planck-pqpczp` of `georrrgess-jpg/voidfx`, 2026-11-05. Eleven Studio 1 edits (v1–v11) plus notes from Studio 2 (FOREVER, DRACULA).

---

## 1. What's in the package

| Path | What it is | Read it for |
|---|---|---|
| `CLAUDE.md` | **The binding rules**: benchmarks, every owner preference, project conventions | The rule set the studio must follow |
| `studio/preferences.json` | **Machine-readable mirror** of the rules: thresholds, benchmarks, likes, rejections, QC gates | Feeding an autonomous pipeline or a rules UI |
| `studio/VOIDFX_STUDIO.md` | The handbook: benchmarks with quotes, non-negotiables, likes with evidence, the rejected list, craft lessons, pre-build gate, ship checkpoint, style bank, songs used | Why each rule exists |
| `studio/SCENE_PACKS.md` | Every source pack and song: specs, measured quality, proven shots with timecodes, dialogue lines, what to avoid | Shot selection |
| `studio/src_manifest.json` | The 30 media files the library needs (names, sizes, SHA-256, original upload names) | Rebuilding `src/` |
| `sync/` | **The two-studio sync:** workflow (`README.md`), the shared `HANDOFF_TEMPLATE.md`, `RECEIVE_PROMPT.md`, `LEDGER.md`, and every handoff sent and received (`handoffs/`) | Keeping both studios learning at the same pace |
| `studio/START_PROMPT.md` | The one-message brief for a new edit, plus the feedback template | Starting edits; the intake form |
| `studio/NEW_STUDIO_SETUP.md` | How to stand up a second studio session | Parallel studios |
| `docs/TOOLKIT.md` | The engine: pipeline timings, the transition and graphics catalogue (91 transitions registered in the v11 engine), pitfalls, what made each standard | Building and extending the engine |
| `7b769aa4-TIKTOK_EDITING_GUIDE.md` | Your original playbook (beat grid, colour, effect recipes, loop and QC methods). `CLAUDE.md` wins where they differ (e.g. true peak −2.5 dBTP, not −1) | Background |
| `tools/` | The command-line tools (§6) | The pipeline |
| `vN/work/` | Each edit's EDL (`edlN.py`), renderer, audio builder, QC, face tracks, shot lists, transcripts | Worked examples |
| `vN/README.md` | Each edit's notes: concept, song section, shot list, every revision with the owner's words, review fixes, measured checkpoint | The edit history |
| `v11/work/` | **The current engine** (`render11.py`, `audio11.py`, `qc11.py`): every transition from v4 to v11 | The base for new edits |
| `README.md`, `work/` | v1 (THE MASK SLIPS) | The first edit |

**Not in the package (and not in git):**
- the source media (`src/`): copyrighted footage and songs, listed in `studio/src_manifest.json`;
- model weights (downloaded by `tools/setup_studio.sh`);
- the rendered edits (`vN/out/*.mp4`, about 70–85 MB each), which were delivered with each edit. The voidfx logo `src/voidfx_logo.webp` is the one media file included in the kit, because it's yours.

---

## 2. How the studio works today

An edit is a folder `vN/` with one decision file, the **EDL** (`vN/work/edlN.py`). The renderer, audio builder and QC read only the EDL, so every creative decision is in one place.

| Stage | Tool | In → out | Time (4-core CPU) | Today |
|---|---|---|---|---|
| 1. Intake | `studio/START_PROMPT.md` | brief + uploads → `src/` | — | Owner |
| 2. Scaffold | `tools/new_edit.py N SLUG "TITLE"` | → `vN/` from the v11 engine + `tools/edl_template.py` | 1 s | Auto |
| 3. Song map | `tools/song_map.py src/SONG vN/work` | song → beat grid, section changes, candidate 20–27 s windows | 3 s | Auto, agent picks |
| 4. Stems + lyrics | Demucs; `tools/transcribe.py` | song → vocal stem, word times (then onset-checked on the stem) | 3–6 min | Auto + agent check |
| 5. Pack review | `vN/work/analyze.py PACK TAG`; `tools/sharpness.py packs` | pack → shot list, contact sheets, quality table | ~1 min/pack | Auto, agent reviews sheets |
| 6. Concept + EDL | hand/agent-written `edlN.py` | shots, transitions, text, knobs | 10–30 min | **Agent (creative)** |
| 7. Prep | `tools/build.sh N prep` | YuNet face tracks, MODNet mattes, source-range audit | 2–7 min | Auto (gate: `check_sources`) |
| 8. Restore | `tools/sr_prep.py N` (background) | 2× restored source bands | ~3 s/frame (25–45 min) | Auto |
| 9. Build the look | the edit's `render()`, new transitions in `TR2` | code | 1–3 h | **Agent (creative)** |
| 10. Review loop | `build.sh N auto`, `render N.py stills/full/clip` | contact sheets, stills, small clips | 20–70 s each | **Agent looks at frames** |
| 11. Sound | `tools/build.sh N audio` | circular mix, wrapped master, AAC-checked | ~10 s | Auto (gate: loudness, seam) |
| 12. Render | `tools/build.sh N video` | upload MP4 + master MOV | 13–17 min | Auto |
| 13. Ship checkpoint | `tools/build.sh N qc`; `tools/sharpness.py N` | QC report, verdict | ~1.5 min | Auto (gates) |
| 14. Visual sign-off | frames from the encoded file | contact sheets | ~1 min | **Agent looks** |
| 15. Deliver + notes | README, commit, push, send | — | — | Agent |
| 16. Owner feedback | one message per revision | → back to 6/9 | — | Owner |

A full edit takes about 1.5–3 hours of wall clock from brief to shipped MP4, mostly unattended; a revision takes 30–90 minutes.

---

## 3. Autonomous and manual modes: where each fits

**What can already run with no one watching** (deterministic, measurable): stages 2, 3, 4, 5, 7, 8, 11, 12, 13, plus the numeric gates in `studio/preferences.json` → `qc_gates`.

**What needs judgement** (an agent today, a person in manual mode):
- **Concept and song section** (stage 3/6): which window, what the edit is about. The best concepts came from the material itself (v11: the intro says "Harrison" → the Reverse-Flash rivalry).
- **Shot choice** (stage 6): expression, motion, composition in 9:16, sharpness. Many shots were swapped only after looking at frames (a face hidden by lightning, a guard's face cut at the edge, an overexposed sky).
- **Designing set pieces and graphics** (stage 9): the owner's main ask in every revision. They're written as code per edit.
- **Visual review** (stages 10, 14): most real defects were found by looking at frames, not by QC: lightning over faces, a bolt seam through a nose, an emblem off-centre, a white-out flash, text over a chin.

**Suggestions for the manual side:**
- The EDL is already a human-editable timeline: each `shot(...)` line is one clip with its source range, framing (`z`, `cx`), speed (`tmap`/`vel`), transition in (`tin`) and graphics flags. A manual UI can edit these fields and call `render N.py stills` / `clip A B` for previews (20–70 s).
- Text moments are entries in `TEXT` (words, times, line, emphasis, style).
- Every transition's parameters are in its function; exposing the main ones (timing, colour, intensity) per instance would make them manually tweakable.

**Suggestions for the autonomous side:**
- Use `studio/preferences.json` as the rule set; turn each `qc_gates` entry into a pass/fail step; add the flash and sharpness checks to `qcN.py` (they're run separately today).
- Keep the visual sign-off as a required step (frames from the encoded file around every transition, title, the drop and the loop).
- Keep the revision memory: every owner note becomes a rule in `CLAUDE.md` and the handbook, and every rejection goes into the rejected table.

---

## 4. The owner's preferences (summary)

The full rules with the owner's own words are in `CLAUDE.md` and the handbook; `studio/preferences.json` has the numbers. In short:

**Always:**
- 9:16, 1080×1920, 60 fps, 20–26 s; upload MP4 (H.264 + AAC, fast-start) + a high-quality master.
- −13 LUFS, true peak ≤ −2.5 dBTP, measured after AAC; every transition has its own sound; smooth, clean audio on the beat grid.
- Faces centred (≈37 % height), never cut off; text in the 1240–1640 px band, clear of faces and TikTok's UI.
- Every word eases in. Text uses the v9 NIGHT BLOOM construction ("it was perfect"), recoloured per edit; lyrics on their sung onsets.
- A seamless loop in picture and sound (seam diff ≤ 1), built as a set piece.
- The voidfx logo once, as a transition, exactly as supplied.
- One concept tying picture, sound, text and loop, found in the material; at least three multi-stage set pieces (drop, hook, loop) plus one focal piece; 15+ designed transitions that "go through something".
- The motion pass: speed ramps on the beat with flow slow motion, a camera that punches and kicks on the beat, light that reacts to the footage; a beat animation for every shot that only moves to the beat.
- Restored source (`sr_prep.py`); sharp shots (`sharpness.py`); zoom ≤ 10 % on 720p.
- Built-in review passes before delivery, and honest reporting (can't watch or listen).

**Never:**
- outro cards, watermarks, a recoloured logo, labels, name tags, counters, timecodes, CJK subtitle lines, title cards;
- choppy dialogue openings, rapid single-word dialogue runs, endings carried by exposition;
- gimmick overlays on faces (target rings, converging lines), effects or lightning across faces;
- generic bursts, white-out flashes, prolonged strobing;
- props that linger, appear at random, look drawn, or sit on a face;
- the v8 "editorial" type look; soft, pretty concepts for Dexter.

---

## 5. Edit history and what each one taught

| Edit | Show × song | Look | What the owner said | What it taught |
|---|---|---|---|---|
| v1 THE MASK SLIPS | Dexter × Blood Theme | warm cinematic | (first build) | EDL-driven pipeline; the song's hard stop as a story beat |
| v2 THE DARK PASSENGER | Dexter × Matrix Funk (slowed) | comic ink / halftone | more clips, faster cuts, more transitions (3 rounds) | density; motion-blurred camera moves |
| v3 SURPRISE | Doakes × Need It | night thriller | choppy opening, labels, popping text, watermark, outro card | the "never" list's first half |
| v4 SURPRISE | (rework) | night thriller | **first standard** | one-take dialogue open; barrel → scope; pupil → iris loop; BLEED IT blood fill; footage-in-letters type |
| v5 FASTEST | Flash × Duvet | amber/teal lightning | no title card, no starburst, cut odd footage, right lyric, better falling letters | themed bursts only; verify lyrics; multi-stage text |
| v6 WARMPOP | Dexter × Warmpop | pastel vapor + VHS | **standard**: "wonderful transitions… I like the text" | density with quality; music-led structure; depth graphics; no CJK, no counters |
| v7 HIM ALL ALONG | Dexter × Him All Along | forensic noir | **standard** after cutting dialogue runs, face gimmicks, the blue logo | character-themed physical transitions; dialogue less is more; never restyle the logo |
| v8 WISH YOU WELL | Dexter × Wish You Well | sodium nocturne | "did most things well"; liked the Darling drop, mirror loop and basic moves; disliked the text | bold captions over editorial type |
| v9 NIGHT BLOOM | Dexter × Night Blooming Jasmine | moonbloom | "good, complete" but **lacklustre**; the text "was perfect" | the text standard; concept from the character; 3+ set pieces; the pre-build gate |
| v10 LET IT HAPPEN | Flash × Let It Happen | prism speed | 5 revisions ("lacklustre" twice), then **standard** | the motion pass; restored source; onset-timed lyrics; loop as a set piece; the props rule |
| v11 BOP | Flash × BOP | voltage / rival | 4 revisions, then **standard** | concept from the material; one focal set piece; detailed physical assets; beat moments; exact loop; flash discipline |
| FOREVER (Studio 2) | Dexter | — | props lingered, were random, looked drawn, didn't land | the props rule |
| v105 DRACULA (Dexter studio) | Dexter × Tame Impala "Dracula" | SUNDOWN (day postcard / moonlit night) | 3 revisions, **standard**; gripe: clip quality | light behind the subject; the loop as the most creative transition; restyle library moves; the sharpness rule |
| v12 BLOOM | Flash × fakemink "Night Blooming Jasmine" | NOCTURNE (indigo night, crimson suit, jasmine-white lightning) | 3 revisions (remove both titles, half the sounds, the bell; add a transition and an emblem transition), then **standard** | text is optional; fewer, bigger sounds; an emblem transition on the tracked emblem; a transition on a real phenomenon (FRACTAL BURN); one hero asset carried through |
| v107 ALL CAPS (Dexter studio) | Dexter × Madvillain "All Caps" | TABLOID (newsprint, one spot red) | 4 revisions (the 3 s slot rejected four times; a centred headspin; no reused clip; a smooth ending; a creative loop; the name on an even grid), then **standard** and the Dexter scaffold | a concept carried by one object; no black occluders; nothing pointing at a face; spell-outs on a grid; the loop from the edit's own particles |
| v13 EVENT HORIZON | Flash × Brent Faiyaz "Wish You Well" | REDSHIFT (desaturated steel) | rev 1: *"I really don't like this edit … the singularity is the primary object in every transition"*; rev 2 approved, **not a standard** (*"does somethings good and somethings bad"*) | a hero asset is a motif, not the transition kit; an emblem transition comes from the emblem itself; a hero graphic becomes a transition; start sound lean |
| v106 WONDERWALL (Dexter chat, a Flash edit) | Flash × Oasis "Wonderwall" | WONDER (golden-hour amber vs Speed Force cobalt) | 3 revisions (half the sounds, smoother animation, a seamless loop, fill a dead span; slow the tear), then **standard** | a story concept from a lyric line; sound restraint (silent transitions allowed); measured dead-span, pop and judder audits; signature transitions get ~1 s; a loop that keeps moving across the wrap |

The pattern across eleven edits: the owner keeps asking for **more designed transitions, animations, graphics and sound effects**, for **character-specific physical ideas**, and for **polish** (no soft shots, no white-outs, no effects on faces). Approval came when the edit had a clear concept, a focal piece, and motion on every beat. Since v12 and v106 the sound runs the other way: twice he cut about half the effects, then approved; picture density stays, sound goes to the set pieces.

---

## 6. Engine reference

**Tools** (`tools/`):

| Tool | Does |
|---|---|
| `new_edit.py N SLUG "TITLE"` | Scaffolds `vN/` from the v11 engine and the EDL template |
| `song_map.py SONG OUTDIR` | Beat grid (BPM, half-beat P, offset), per-bar energy, section changes, candidate windows |
| `transcribe.py vN NAME MEDIA [--start --dur --vad]` | faster-whisper large-v3 word times |
| `check_sources.py N` | Fails any shot whose source range leaks past a source cut |
| `build.sh N STEP…` | `prep`, `auto`, `audio`, `clip:A:B`, `preview`, `video`, `qc`, `all` |
| `sr_prep.py N [--count] [--threads]` | Real-ESRGAN compact (ONNX Runtime) on only the bands each frame uses → `vN/sr/` |
| `srnet.py` | The upscaler network, tensors-only weight loading, ONNX export |
| `sharpness.py packs` / `sharpness.py N` | Pack quality table; per-shot enlargement + in-focus detail on the finished video |
| `setup_studio.sh [--check]` | Python packages, fonts, models, source-library check, smoke tests |
| `edl_template.py` | The EDL every new edit starts from |

**The EDL** (`vN/work/edlN.py`) defines:
- `VER`, `SLUG`, `SONG`, `SONG_STEMS`, `SRC` (pack key → path, fps, width, height);
- the beat grid `HB`, `HB_OFF`, the window `H0`, `H1`, the drop `HDROP`, section marks (`E_BEAT`, `E_DIP`, `E_LOOP`, `E_STUT`, `E_RUN`, `E_REW`) and helpers `th(e)`, `fh(e)`, `s2e(t)`;
- `vel(e0, e1, a, b)`: the beat-synced speed ramp;
- `SHOTS`: `shot(name, pack, e0, e1, src_in, src_out, **options)`, in edit half-beats. Options: `tin` (transition in), `tmap`, `lin`, `interp` (`hold`/`blend`/`flow`), `z` (zoom keys), `face` / `cx` (framing), `look` (grade), `seg` (matte), and graphics flags (`arcs`, `wind`, `orbit`, `sparks`, `trails`, `rays`, `wave`, `ember`, `fire`, `dust`, `speed`, `red_arcs`, `aura`, `remnants`, `charge`, `warp`, `frozen`, `drain`, …);
- `TEXT`: text moments `dict(style, words=[(WORD, t, line)], end, emph, rides)`.

**The renderer** (`vN/work/renderN.py`):
- `render(f)` builds one frame: base picture (restored source, grade, graphics) → text that rides the transition → incoming and outgoing transitions → global effects → text → finish (bloom, halation, grain).
- Transitions live in the registry `TR2[name] = (fn, frames_before, frames_after)`, with `fn(A, B, j, f, sa, sb)`: `j < 0` is the pre-roll on the outgoing shot, `j ≥ 0` the post-roll on the incoming one.
- Each edit appends its own section before `main()` and redefines what it changes. **The last definition wins.**
- Modes: `prep`, `auto NAME`, `stills NAME f…`, `full f…`, `clip A B`, `preview`, `video OUTDIR`.

**The audio builder** (`vN/work/audioN.py`) builds the song window circularly with a pre-roll, layers the effects (each transition's sound is keyed to its `tin`), masters a wrapped copy to the loudness target, aligns it back, and checks the AAC encode.

**QC** (`vN/work/qcN.py`) runs on the encoded MP4: format, decode, loudness after AAC, frozen runs, faces, text vs faces, cuts, black frames, clicks, loop seam, A/V length, and a verdict.

**Engine notes for development:**
- `render11.py` is a 9,500-line file built by layering each edit's section on the previous ones. It works, but for a product the transitions, graphics, text styles and grades would be better as separate modules in a registry, with each edit's `render()` and look kept on its own.
- Rendering is CPU-bound: about 0.6 s per frame on 4 cores, ~15 minutes for a 21–25 s edit. A GPU would speed up restoration, optical flow and the per-pixel effects.
- Caches are per worker process (source frames, mattes, restored bands, flow fields). Workers use `multiprocessing.Pool(4)`.

---

## 7. Requirements

- **System:** Linux, `ffmpeg`/`ffprobe`, Python 3 (tested on 3.13), 4+ CPU cores, ~16 GB RAM, ~1–2 GB of free disk per edit for its working files (frames, mattes, restored bands, audio, outputs).
- **Python:** numpy, scipy, opencv-python(-headless), pillow, onnxruntime, onnx, faster-whisper, demucs, torch (once, for the upscaler's ONNX export).
- **Fonts:** Inter Display (Black, ExtraBold, Bold, SemiBold), JetBrains Mono.
- **Models** (downloaded by `tools/setup_studio.sh`): YuNet face detector (OpenCV zoo), MODNet matting (`Xenova/modnet` ONNX), Real-ESRGAN compact general-x4v3 + wdn (xinntao/Real-ESRGAN v0.2.5.0, BSD-3), faster-whisper large-v3 and Demucs htdemucs (fetched on first use).
- **Media:** the 30 files in `studio/src_manifest.json`, placed in `src/` with those names (`setup_studio.sh` verifies sizes and checksums). Every scene pack is 720p; see the quality table in `studio/SCENE_PACKS.md`.

---

## 8. Open items and known gaps

- **Studio 2's branch isn't merged here.** DRACULA and FOREVER, Studio 2's own `tools/sharpness.py` (this branch has an independent version with the same name and job) and any Studio 2 engine changes live there. Merging will need a decision on the scaffold base (this branch: v11; Studio 2: DRACULA) and on which `sharpness.py` to keep.
- **v11 soft shots:** the punch and the grin measure soft; the owner approved the edit as is.
- **Flash brightness** and **sharpness** are measured outside `qcN.py`; folding them into QC would make the gate fully automatic.
- **The final visual sign-off still needs eyes** (an agent looking at frames today).
- **Sources are 720p and some are heavily compressed;** better sources (true 1080p/4K, higher bitrate) would lift every edit more than any processing.
