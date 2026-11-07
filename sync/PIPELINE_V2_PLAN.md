# voidfx pipeline v2: the quality and efficiency upgrade plan

**From:** the Flash studio (Studio 1) · **For:** the Dexter studio (Studio 2), to lead development, with the Flash studio piloting and reviewing · **Date:** 2026-11-07 · **Status:** plan; nothing in it is built yet unless marked **done**.

**How to use this document:** read §0 for the summary, §2 for the guardrails, and §5 for the build order. Each work package in §4 has its evidence, design, deliverables, acceptance tests and effort. Start with Phase 0 (§5). Code and data referenced here live on the Flash studio's branch `claude/gallant-planck-pqpczp` of `georrrgess-jpg/voidfx` (commit `0823636` or later) unless they're named as yours (`v105/…`).

---

## 0. Summary

**Where time and quality are lost today** (measured; §1 has the data):
1. **Owner revision rounds are the biggest cost.**
   - Approved standards took 3–5 rounds: v10 5, v11 4, v105 3.
   - Each round is 0.5–2.5 hours of studio work plus the owner's wait.
   - **11 of the last 19 owner notes asked for the same thing:** more designed transitions, animations, graphics or sound, or called the edit "lacklustre".
   - All three 2026 standards needed a round just to make the loop more creative.
   - These asks are predictable. A first delivery built to a rubric would avoid most of those rounds.
2. **The iteration loop is slow:**
   - a full render takes 13–17 minutes, and edits needed about 1.8 full renders per round (v10: 9 renders, about 2.3 hours; v11: 7, about 1.6 hours);
   - a contact sheet of stills takes 40–70 s (12 s of start-up, then frames rendered one at a time);
   - source restoration takes 25–45 minutes per edit and is redone for every edit.
3. **Review catches defects by eye that a script could catch:** lightning, particles and suns over faces (12+ instances across v10, v11 and v105), white-out flashes, loop seams, cut-off faces, text on chins, the effects-vs-music level.
4. **The engine is hard to work in:**
   - one 9,500-line file (`render11.py`) layers every edit's section on top of the last, and the last definition wins;
   - importing it takes 5 s;
   - the two studios run separate engine copies in places the other can't see;
   - there are two `tools/sharpness.py` files with different scales.

**The plan:** 15 work packages in 5 phases. The biggest wins come first:
- grade-curve lookups (14–27× faster per call, measured);
- cached, contiguous rendering;
- a persistent render server for previews;
- verified partial re-renders;
- a shared source library (restoration, mattes and flow computed once per pack, not per edit);
- a pre-render plan check that enforces the owner's recurring asks;
- QC that detects the usual review catches automatically;
- a fresh-eyes critique pass before each delivery.

**Targets:**

| Metric | Now (measured) | Target |
|---|---|---|
| Owner rounds to approval | 3–5 | ≤ 2 |
| Brief → first delivery (studio time) | about 2–2.5 h (v11) | ≤ 1.5 h |
| Full render, 21–25 s edit, 4 CPU cores | 13–17 min | ≤ 6 min |
| Re-render after a local change | 13–17 min (always full) | ≤ 3 min (partial, verified) |
| Full renders per revision round | ~1.8 | ≤ 1.1 |
| Stills sheet (24 frames at full quality) | 40–70 s | ≤ 12 s |
| Source restoration for an edit reusing known packs | 25–45 min | ≤ 5 min (cache hits) |
| Defects first found by eye (faces, flashes, seams, mix) | most | flagged by QC before anyone looks |

---

## 1. Findings (measured on the Flash branch, 4-core CPU, 15 GB RAM, no GPU: no CUDA, no OpenCL)

### 1.1 What the owner asks for between rounds (19 revision rounds: v5–v11 and v105)

The Flash studio's categorisation of each round's note:

| Category | Rounds | Examples |
|---|---|---|
| More / denser designed transitions, animations, graphics, sound; "lacklustre" | **11 / 19** | v6 r2–3, v9 verdict, v10 r2–5, v11 r2 and r4, v105 r2–3 |
| Replace or cut a specific shot | 5 | v5 r3 (slow-mo run), v7 r2 (jar of blood), v8 r2 (headlights), v9 r2 (Arthur Mitchell), v10 r2 (lit eyes) |
| A specific effect too plain or not detailed enough | 4 | v5 falling letters, v7 steel doors → slide box, v10 r4 glass shatter, v11 r4 the symbol |
| The loop must be more creative | **3** (every 2026 standard) | v10 r3, v11 r3, v105 r3 |
| Picture quality / "professionalism" | 3 | v10 r3 "best quality", v10 r5, v105 verdict "the quality of some of the clips" |
| Text look, timing or words | 3 | v5 wrong lyric, v8 type look, v10 r3 timing |
| A visible defect | 2 | v7 r2 recoloured logo / face gimmick, v105 r2 sun over his head |

**Implication:** the first delivery systematically under-delivers on density, loop creativity, hero-asset detail and picture quality. All four are checkable before delivery (§4 WP7, WP9).

### 1.2 What the studios' own reviews catch (from the READMEs and handoffs)

| Defect | Times caught | Could a script catch it? |
|---|---|---|
| Effects over faces (lightning, rays, particles, suns, streaks, seams) | 12+ | Yes: compare the frame before and after effects inside the tracked face box (WP8) |
| White-outs / blown exposure | 5 (2 still shipped in v105) | Yes: **done** in `qc11.py` §7b (from your qc105) |
| Loop seam > 1 | 3 (v105 shipped at 8.4) | Yes: **done**, `qc11.py` now gates ≤ 1 |
| A face cut off at the frame edge / wrong person framed | 4 | Mostly: QC face check exists; add a pre-render check from the tracks (WP7) |
| Text on a chin / over a face | 4 | Yes: QC text-band check exists; move it before the render (WP7) |
| Effects far below a loud master | 1 (v105, 20–25 dB under) | Yes: per-set-piece level table (WP12) |
| Library transition bringing its old look | 1 (v105) | Yes: restyle metadata lint (WP10/WP7) |
| A procedural asset that looks drawn (coffin, moon, emblem, lightning blob) | 5 | Partly: full-res asset sheets + the critique pass (WP9) |

### 1.3 Stage timings per edit

| Stage | Time now | Notes |
|---|---|---|
| Song map | 3 s | fine |
| Demucs stems | ~4–5 min | redone per edit; cacheable per song |
| Whisper + manual onset checks | 5–60 min | v10 rev 3 needed a manual pitch/onset pass; Whisper was up to 1 s off |
| Pack analysis | ~1 min per pack, plus reading sheets | redone for every new pack, but cached JSON is reused for known packs |
| Prep (YuNet tracks, MODNet mattes, source audit) | 3–7.5 min | rerun on every shot change (v11: 4 times) |
| Source restoration (`sr_prep.py`) | 25–45 min per edit | 3–4 s per source frame; v10 345 MB, v11 274 MB of bands; no reuse between edits |
| Stills / contact sheets | 40–70 s per call | 12 s start-up (import 5.1 s, load 5.8 s, mattes 0.9 s), then frames one at a time, single process |
| Full render | 13–17 min | 0.6–3.1 s per frame per worker; 4 workers |
| QC | 35–50 s | fine |

### 1.4 Where render time goes (cProfile, 25 hook frames of v11)

| Item | Share | Cause |
|---|---|---|
| `grade()` with `np.interp` on full float bands | **37 %** (21.8 s of 58.7 s) | `np.interp` costs 329 ms per 1440×880×3 band; a lookup index costs 23 ms, a uint16 LUT 12 ms (benchmarked) |
| `afterimages()` (cumulative, overlaps with grade) | 35 % | It re-renders 3 past frames per frame, including their grade. With `imap(chunksize=4)` the past frames belong to other workers, so nothing is cached |
| Optical flow (`DISOpticalFlow.calc`) | 7 % | 130 ms per full-frame pair; recomputed every render and revision (23 ms at 640×720) |
| Restored band decode (`imread`) | 6 % | Each band is decoded again by each worker; a raw `.npy` read is 0.7 ms vs 8 ms JPEG |
| Particles / glows / full-res blurs | ~15 % | A σ16 blur costs 71 ms at full res vs 7 ms at quarter res |
| Per-frame cost by moment | — | Plain shot 0.63 s; set pieces 1.2–2.0 s; hook shots with afterimages + flow + title 3.1 s |

### 1.5 Structure and repository

- `v11/work/render11.py` is 9,501 lines: v4–v11 sections layered, with later definitions overriding earlier ones. Finding the live version of a function is error-prone, and an override inserted in the wrong place silently does nothing (toolkit pitfall 1).
- Each edit copies the whole engine; fixes don't flow back; QC is copied per edit (`qcN.py`).
- **The Dexter studio's branch isn't visible in `georrrgess-jpg/voidfx` from the Flash studio.** `git ls-remote` shows only `claude/gallant-planck-pqpczp`, and your handoff says the transfer bundle is in Drift-Master `voidfx-v101/`. Neither studio can pull the other's code today.
- Duplicated tools: two `tools/sharpness.py` (yours: absolute detail scale, ≈0.30+ sharp, ZOOM > 3.1×, LOWBIT < 800 kb/s; ours: relative to the edit's median, zoom > 2.95× (z 1.10), LOWBIT adopted, plus `--src`).

### 1.6 Sources
- Every pack in the library is 720p (several are labelled 4K); bitrates run 0.43–2.2 Mb/s. The measured table is in `studio/SCENE_PACKS.md` ("Pack quality").
- Restoration is CPU-only, at about 3 s per source band.
- Disk has about 7 GB free in the Flash container, which bounds any caching design.

---

## 2. Guardrails: what must not be cut

Every change must keep these. A work package that would break one is redesigned, not shipped.
1. **The final render is full resolution, full quality:** CRF 17 upload plus a CRF 11 master; no lower encoder preset for finals.
2. **Restored sources for every frame used,** and optical-flow slow motion on restored frames.
3. **Visual sign-off on frames pulled from the encoded file** before every delivery. Automation reduces what reaches it; it doesn't replace it.
4. **A designed sound for every transition;** loudness measured after AAC; the loop built circularly.
5. **The loop is a set piece that lands on frame 0** (seam ≤ 1).
6. **Captions only on verified sung words,** on their onsets.
7. **Nothing on faces; light behind the subject.**
8. **Any speed-up must produce identical pictures.** Golden frames must match within ±2/255 per pixel and a mean difference under 0.2/255 (WP1), or the change is reverted.
9. **A partial re-render is used for a delivery only if its verification passes** (WP4); otherwise do a full render.

---

## 3. The upgraded process, stage by stage

| # | Stage | Change | Tool (new = *) | Time now → target |
|---|---|---|---|---|
| 1 | Intake | Unchanged brief, plus the owner can optionally name one "must-have" moment | `START_PROMPT.md` | — |
| 2 | Pack ingest | **Once per pack, not per edit:** probe true resolution/cadence/bitrate, detect insets and watermarks, find shots, faces, sharpness and bitrate class, write a catalogue draft. Mattes, restored bands and flow go into a shared library on demand | `tools/ingest.py`*, `library/`* | 1 min/pack + per-edit recompute → once per pack |
| 3 | Song + lyrics | Stems cached per song; key, master loudness and vocal activity measured; every lyric word verified against its sung onset automatically | `tools/song_map.py` (+key, +loudness), `tools/lyrics.py`* | 10–60 min → ~8 min |
| 4 | Plan | A structured **plan sheet** in the EDL: concept, set pieces (≥3, one focal, the loop), per-shot purpose, beat moment, transition (themed or generic, restyled?), sound, light, text | `PLAN` dict in the EDL; `tools/plan_check.py`* | — |
| 5 | Plan check | **Lint before any render:** density, sounds, zoom, sharpness, faces vs text bands, loop design, restyle metadata, logo once, duration, drop position | `tools/plan_check.py`* | catches round-1 notes before rendering |
| 6 | Prep | Library lookups; only new frames are computed | `build.sh N prep` | 3–7.5 min → < 1 min on known packs |
| 7 | Build | The edit's look and set pieces, on the engine package with the transition registry | `engine/`* | — |
| 8 | Preview | A **render server** keeps the engine loaded; stills, transition strips and proxy clips run on 4 workers | `tools/rsrv.py`* | 40–70 s → ≤ 12 s per sheet |
| 9 | Render | Contiguous worker chunks, caches, LUT grade, cached flow | `build.sh N video` | 13–17 min → ≤ 6 min |
| 10 | Revise | **Partial re-render** of the changed range, verified against the cached frames | `build.sh N video --only A:B`* | 13–17 min → ≤ 3 min |
| 11 | QC v2 | Adds: effects over faces, flashes (**done**), seam ≤ 1 (**done**), sharpness on the render, dead spans, effects-vs-music table, logo count; one report | shared `tools/qc.py`* | 40 s → ~60 s, far fewer by-eye catches |
| 12 | Critique | **Fresh-eyes review** against the owner rubric (Appendix B) before delivery; optional A/B clips for the loop or focal piece | Agent tool + `tools/sheets.py`* | +10–15 min, saves a round |
| 13 | Deliver + handoff | Handoff drafted from the README, QC and metrics | `tools/handoff.py`* | 20 min → 5 min |

---

## 4. Work packages

Effort is in **sessions** (a session is about 2–4 hours of agent work). Every package ships as one PR with: the diff, golden-frame results (WP1), timing before/after, and a short README section.

### WP0. One shared code base (prerequisite)
- **Why:** neither studio can see the other's branch (§1.5); ports happen by copy; tools and rules diverge.
- **Design:**
  1. Push the Dexter branch (`claude/beautiful-volta-wjki7k`, `v101–v105`) to `georrrgess-jpg/voidfx`.
  2. Create `dev/pipeline-v2` from the merge of both branches (the owner approves the merge).
  3. Resolve the known conflicts:
     - **`tools/sharpness.py`:** one tool with both scales: absolute detail (yours) and relative-to-median (ours); flags SOFT, ZOOM (> 2.95×, the z ≤ 1.10 rule), LOWBIT; modes `packs`, `N --src`, `N`.
     - **`CLAUDE.md` and handbooks:** merge both rule sets; the newer verdict wins.
     - **`studio/preferences.json`:** one schema (WP14).
     - **Scaffold bases:** Flash from v11, Dexter from v105, until WP10 makes both run on one engine.
- **Deliverables:** one branch both studios pull; a merge note.
- **Acceptance:** both studios can render v11 and v105 from the same checkout.
- **Effort:** 1. **Risk:** large docs merge. Resolve section by section and keep both studios' evidence.

### WP1. Regression harness and metrics
- **Golden frames:** `tools/golden.py N --save|--check`.
  - Renders a fixed list: one frame per shot, every set-piece peak, the drop, the last 3 frames and frame 0.
  - Stores them in `vN/work/golden/` (PNG, kept out of git).
  - Checks max/mean absolute difference.
  - Run on v11 and v105 before and after every engine change.
- **Metrics:** `vN/work/metrics.json`, appended automatically by `build.sh` (timings per stage, full renders, QC failures) and by the studio (owner-note categories from §1.1, review catches by category from §1.2, rounds).
- **Acceptance:** `golden.py --check` passes on an unchanged tree; metrics appear after one build.
- **Effort:** 0.5.

### WP2. Render speed (profile-driven)
1. **Grade by lookup:** replace `np.interp` with a precomputed uint16 or index LUT (benchmarked 329 → 12–23 ms per band). Cache the graded band per (shot, source frame) when the grade doesn't depend on the output frame.
2. **Contiguous scheduling:** give each worker a contiguous range (a whole shot, or 30–60 frames) instead of `chunksize=4`, so per-worker caches hit (restored bands are shared by ~2.5 output frames at 24p; afterimages need the previous 12 frames).
3. **Afterimage cache:** an LRU of unshaken shot renders and mattes per (shot, frame), about 24 entries per worker.
4. **Flow cache:** compute DIS flow once per source pair (on the restored band, or at source resolution and scaled), store it float16 in the library, and reuse it across revisions and edits.
5. **Blur audit:** move remaining full-resolution blurs with σ > 4 to quarter resolution (71 → 7 ms each).
6. **Band decode:** keep decoded bands in a per-worker LRU sized to RAM (about 1–1.5 GB per worker). Store raw `.npy` only if disk allows (3 MB vs 0.33 MB per band).
7. **Encoder:** measure its share. Never lower the final preset; previews may use `veryfast`.
- **Acceptance:** v11 full render ≤ 6 min; golden frames within the §2.8 tolerance; peak RAM ≤ 12 GB.
- **Effort:** 1–1.5.

### WP3. Render server and fast previews
- `tools/rsrv.py N` loads the edit once (engine, sources, tracks, mattes, caches) with a persistent pool of 4 workers, and takes commands over a local socket or a file queue:
  - `stills f…`, `full f…`;
  - `strip A B` (every 2nd frame across a transition, in one sheet);
  - `clip A B` (proxy MP4 with sound);
  - `sheet cuts` (the existing `auto` mode).
- It reloads the edit's own modules on change (needs WP10 for a clean reload; until then, restart in ~12 s).
- **Acceptance:** a 24-frame full-res sheet in ≤ 12 s; a 2 s proxy clip in ≤ 20 s.
- **Effort:** 1.

### WP4. Partial re-render, verified
- Every full render also writes a lossless frame cache (FFV1 `.mkv`, about 1.5–2.5 GB for 1,250 frames; one per edit, deleted at the verdict).
- `build.sh N video --only A:B` re-renders the dirty range, splices it into the cache, and encodes the upload and master from the cache.
- **Dirty range:** by default derived from the EDL diff (changed shots ± their transition windows), or declared by the studio.
- **Verification:**
  - re-render 12 random frames outside the range and require a bit-exact match with the cache;
  - any mismatch means the change had global effects, so do a full render automatically;
  - any change to the shared engine (not the edit's own modules) forces a full render.
- **Acceptance:** a one-shot EDL change re-renders in ≤ 3 min, and verification catches a deliberately introduced global change in a test.
- **Effort:** 1. **Risk:** stale frames. Guardrail §2.9 plus the forced full render on engine changes.

### WP5. Pack ingest and a shared source library
`tools/ingest.py PACK KEY` writes `library/<key>/`:
- `meta.json`: true resolution, fps and cadence (repeat ratio), bitrate, bits per pixel, an inset/watermark mask (static high-contrast regions from temporal variance), and intro cards;
- `shots.json` and sheets;
- per-shot face tracks and the widest face width (to check it fits 9:16);
- the detail score and a sharpness rank (WP0's merged tool);
- a draft row for `SCENE_PACKS.md`.

Computed on demand and cached across edits: MODNet (or WP13 matting) mattes, restored bands (`sr_prep` grows each band as needed), flow pairs, and transcripts.

`tools/lib.py find` queries shots by face width, sharpness, bitrate, cadence and keywords from the catalogue.

- **Disk policy:** a cap (default 4 GB of library) with least-recently-used pruning of bands and flow.
- **Acceptance:** an edit reusing flash_b or the S4 pack needs < 5 min of restoration; ingesting a new pack is one command.
- **Effort:** 2.

### WP6. Lyrics and timing tool
`tools/lyrics.py SONG [--window a b] [--known "lyric text"]`:
1. Demucs, cached per song hash.
2. Whisper large-v3 in tight windows, both unprompted and prompted with the known lyric.
3. Snap each word to a sung onset (spectral flux on the vocal stem + pitch track) within ±150 ms.
4. Output `words.json` with a confidence per word and an "unclear" flag, plus a waveform sheet.

Unclear words are never captioned.

- **Acceptance:** reproduces v10's and v105's verified word times within ±1 frame; flags "Now here we are" (v105) as unclear.
- **Effort:** 1.

### WP7. The plan sheet and `plan_check`
- **The plan sheet.** The EDL gains a `PLAN` dict:
  - `concept` (one sentence + where it came from);
  - `set_pieces` (≥ 3, each with stages and a sound; one `focal: True`; the loop);
  - per shot: `purpose`, `beat_moment`, `light` (behind / none);
  - per transition: `themed` / `generic`, `restyled_from`, `sound`.
  - `tools/plan_check.py` also generates the benchmark comparison table skeleton (handbook §5a item 6).
- **`tools/plan_check.py N`** runs before any render, using the rubric in Appendix B. **FAIL** checks:
  - duration 20–26 s; drop at 30–47 %;
  - ≥ 18 designed transitions, generic ≤ 30 %, no repeats except a declared motif;
  - every transition has a sound recipe;
  - every hook or montage shot has the motion pass;
  - every shot longer than 2 beats has a transition or a beat moment;
  - the longest span after the drop without a designed event is ≤ 1.0 s;
  - zoom ≤ 1.10 on 720p unless justified in the plan;
  - no SOFT or LOWBIT source on a hero or close-up shot;
  - captions only from WP6's verified words, inside the text band, and the band clear of the tracked faces;
  - the loop is declared as landing on frame 0;
  - the logo appears once, `logo_orig`;
  - library transitions carry this edit's restyle parameters (WP10).

  **WARN** checks: concept not traced to the song or character; fewer than 2 beat moments; no focal piece on a bar line.
- **Acceptance:** run against v11 rev 1's EDL, it flags the density and loop gaps the owner raised in rev 2–3; run against the approved v11, it passes.
- **Effort:** 1.5.

### WP8. QC v2 (one shared `tools/qc.py`)
- **Effects over faces (the #1 review catch):**
  - in `render()`, keep the base picture (after grade and graphics, before transitions and effects);
  - after effects and before the finish, measure the added light and change inside the screen-space face box (from the tracks);
  - workers return per-frame values; QC lists runs over a threshold with frame numbers;
  - shots with `face=None` use the matte's head box.
- **Flashes and seam:** **done** in `qc11.py` §7b; move them into the shared QC.
- **Sharpness on the render:** run the merged tool's render mode and attach its table.
- **Dead spans:** designed events from the EDL (transitions with pre/post windows, text in/out, beat moments, set-piece stages) against the beat grid. Report the longest span after the drop and every shot with no event.
- **Effects vs music:** the audio builder writes, per transition and set piece, the effects RMS against the local music RMS. QC flags effects more than 12 dB under the music at a set piece, and any music duck deeper than 4 dB (rule 7).
- **Logo:** template-match the supplied logo; exactly one appearance window.
- **Output:** one `vN/work/qc_report.md` with sheets, plus `qc.json` feeding the metrics.
- **Acceptance:** on v11 rev 1 frames it flags the bolt seam through the nose and the face-crossing particles that review caught; on v105 it flags the two white-outs and the 8.4 seam.
- **Effort:** 1.5.

### WP9. The fresh-eyes critique pass, and A/B options
- **The critique:** before each delivery, a fresh-context reviewer agent (Agent tool, without the studio's reasoning) gets:
  - the brief and the owner's latest note;
  - Appendix B (the rubric);
  - the QC report;
  - full-resolution crops of every set piece, transition strip and title, the loop, and frame 0.

  It returns the five biggest weaknesses ranked, each with frame numbers, and a predicted owner note ("would ask for more transitions in 9–12 s", "the loop reads as a fade"). The studio fixes or answers each in the delivery message.
- **A/B options (optional, ask the owner once):** for the riskiest creative choice (usually the loop or the focal piece), render two versions as 3–5 s proxy clips next to the first delivery. The owner picks one in the same reply as his other notes. Cost: about 10 min. Target: the loop-rework round (§1.1: 3 of 3).
- **Acceptance:** run on v11 rev 1's sheets, the critique predicts at least two of the owner's rev 2–4 asks.
- **Effort:** 0.5 (prompt, sheet generator, wiring). **Cost:** one agent run per delivery (tokens).

### WP10. The engine as a package, with a transition registry
- **Layout:** `engine/`
  - `core/`: sources, sampler, restored-band reader, geometry, flow, matte, face tracks;
  - `look/`: grades and finishes, registered by name;
  - `fx/`: one module per family (lightning, light, speed, particles, glass, shapes, swarms, props, loops);
  - `text/`: the v9 construction plus each lyric style;
  - `audio/`: mix and an SFX recipe registry;
  - `qc/`;
  - `shows/flash/`, `shows/dexter/`: show-specific assets.
- **A registry with metadata:**

  ```python
  @transition("rift", pre=18, post=26, tags=["speed force", "tear"], sound="rift",
              restyle={"edge": GOLD, "interior": "speedforce"}, face_safe=True, origin="v11")
  ```

  `plan_check` reads `restyle`, `sound` and `face_safe`; the audio builder reads `sound`.
- **Mechanical de-layering:**
  - import `render11` (and your `render105`/`fx105`);
  - list the live functions (module globals whose `__module__` is the renderer);
  - write their current source (`inspect.getsource`) into modules;
  - resolve wrappers that call an earlier version (`_base10_r3 = base10` chains) by keeping the whole chain in order.
- **Per edit:** `vN/edl.py`, `vN/look.py` (grade, finish, `render()` overrides), and `vN/fx_local.py`. Local transitions are promoted into `engine/fx` after an approval.
- **Acceptance:** v11 and v105 golden frames identical from the package; import < 1 s; a new edit scaffolds as an EDL plus a look file.
- **Effort:** 3. **Risk:** subtle behaviour changes. Golden frames after every module moved; Phase A is mechanical only, no clean-ups.

### WP11. Shared assets, ported both ways on the registry

| From | Asset | To / restyle |
|---|---|---|
| Dexter v105 | `sun_fx(..., m)` light behind the subject | Flash: lightning and Speed Force glows behind Barry (fixes v10/v11 rays drawn over him) |
| Dexter v105 | ASHES TO SUN (`ash_setup`, `ash_body`, `ashes_fx`, `clean_plate`, `seam_out`) | Flash: Barry disintegrates into sparks that fly into the emblem; generic "subject → particles → frame-0 focal point" loop |
| Dexter v105 | `eclipse_tr`, `bat_burst`/`bat_swarm`/`bat_pass_tr`, `coffin_lid` (height-map prop), `moon_tex`, `mist_tr`, `cape_tr`, `card_flip`, `palm_sweep`, qc105 §7b | A generic swarm (debris, shards), `heightmap_prop`, a planet behind the matte |
| Flash v10 | `vel()` + flow, beat camera, `sr_prep`, emblem dive + drop wave, TIME PARTICLES, bullet time, Speed Force tunnel loop, lyric animations, box-filtered rewind | Dexter: a speed-ramped montage; a frozen-moment break-up; a tunnel of case photos or slides |
| Flash v11 | rival grade, red phase, red eye dive, BOLT SPLIT, THE RIFT, coin flip + procedural emblem, REVERSE loop, beat moments (aura, remnants, charge), clash, strobe echo, bolt trace, heat haze, depth particles masked off faces | Dexter: a badge or slide flip; a wound or plastic tear (rift); a red-vs-cold split on a drop |

- **Acceptance:** each port renders a test shot in the other show's palette and passes its golden check.
- **Effort:** 2.

### WP12. Audio v2
- **The SFX recipe registry** (one recipe per transition, next to it in `engine/fx`), so a missing sound is a lint error, not a review catch.
- **Song analysis adds:** master loudness (RMS dBFS), key (chroma → key) for tonal sounds in key (v105's B-flat bell), and vocal activity.
- **Auto gain staging per set piece** against the local music level (rule 7), printed as a table. Keep the circular build, the wrapped master, and loudness measured after AAC.
- **Acceptance:** v105's corrected mix is reproduced automatically from its uncorrected rev 1 levels.
- **Effort:** 1.

### WP13. Quality experiments (adopt only if they win an A/B)
Each experiment runs on golden shots, with a metric and a full-resolution side-by-side; a studio adopts it only if it's visibly better and within budget.
1. **Matting:** Robust Video Matting (temporally stable, higher resolution) against MODNet at 384×672. Edges matter for light behind the subject, beat moments and burns. Measure CPU cost per frame.
2. **Restoration flicker:** measure frame-to-frame flicker on static shots, restored vs. plain; if it flickers, add a flow-guided temporal blend.
3. **A stronger upscaler (x4plus or a video model):** only with a GPU (CPU is too slow). **Ask the owner whether a GPU environment is available**; it would also cut restoration, flow and render times.
4. **Face restoration (CodeFormer/GFPGAN) on soft close-ups:** identity drift is a real risk. Low fidelity weight, never on a hero face without an A/B, and only with the owner's approval.
5. **Platform re-encode test:** simulate a low-bitrate platform re-encode of the upload and compare detail and banding; tune grain and sharpening so the edit survives TikTok's transcode.

- **Effort:** 2+ (per experiment ~0.5).

### WP14. Knowledge sync automation
- `tools/handoff.py N --verdict standard|rejected` drafts a handoff (shared template) from the README, `qc.json`, `metrics.json` and the git log:
  - sections 2, 4 and 6 are pre-filled;
  - 3, 5 and 7 are left for the studio to write.
- **One `studio/preferences.json` schema in both studios:**
  - `rules_from_handoffs` with evidence and `applies_to`;
  - `qc_gates`;
  - `benchmarks`;
  - `engine_bases`.
- The ledger line is appended automatically.
- **Effort:** 0.5.

---

## 5. Phases and order

| Phase | Packages | Why first | Effort |
|---|---|---|---|
| **0. Foundation** | WP0, WP1 | Nothing else can be shared or verified without them | 1.5 |
| **1. Fast wins** | WP2, WP3, WP4; WP8's face-overlay check; WP12's level table | Cut the iteration loop from ~15 min to minutes without touching the creative side | 4 |
| **2. First-pass quality** | WP7, WP9, WP6, WP5 | Attack the owner rounds (§1.1), the biggest cost | 5.5 |
| **3. Engine** | WP10, WP11, WP14 | Makes ports and maintenance cheap; both studios on one engine | 5.5 |
| **4. Experiments** | WP13 | Quality ceiling, once the base is fast and safe | 2+ |

**Pilots:** after Phases 1–2, the Flash studio runs v12 and the Dexter studio runs v106 on the new pipeline. Compare `metrics.json` with v10, v11 and v105 (rounds, time to first delivery, render minutes, by-eye catches) and report through the sync.

**First steps for the Dexter studio:**
1. Ask the owner to approve WP0 (pushing your branch to `georrrgess-jpg/voidfx` and creating `dev/pipeline-v2` from both branches).
2. Build WP1 (golden frames for v11 and v105) before changing any engine code.
3. Do WP2 items 1–3 (LUT grade, contiguous chunks, afterimage cache) as the first PR, with before/after timings and golden results.

---

## 6. Roles and coordination
- **Dexter studio:** leads development (as the owner asked): owns `dev/pipeline-v2`, the PRs and the merges, after owner approval.
- **Flash studio:**
  - reviews each PR against its edits (golden v10/v11);
  - ports Flash-specific pieces (WP11);
  - pilots each phase on v12;
  - keeps making Flash edits on the current pipeline until a phase is merged.
- **Development handoffs:** use the sync folder with a `DEV` type (`sync/handoffs/YYYY-MM-DD_<studio>_DEV_<WP>.md`): what changed, golden results, timings, and how the other studio adopts it. Edit handoffs stay as they are.
- **One package per PR,** each with golden results and timings. No engine changes outside `dev/pipeline-v2`.

---

## 7. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Refactor or speed-ups change the picture | Golden frames for v10, v11 and v105 on every PR; Phase A of WP10 is mechanical only |
| Partial renders leave stale frames | Bit-exact verification outside the range; engine changes force a full render; guardrail §2.9 |
| Disk (about 7 GB free in the Flash container) | Library cap with LRU pruning; the frame cache is deleted at the verdict; restored bands stay JPEG unless space allows |
| The plan check becomes box-ticking | It fails on measurable gaps only; the critique pass and the owner judge taste |
| Critique-agent cost and noise | One run per delivery; the studio answers each point; drop it if the pilots show no fewer rounds |
| Owner fatigue with A/B | Optional; ask once; at most one A/B per delivery |
| Two studios changing the engine at once | One dev branch, one lead, one package per PR |
| No GPU | Everything above is designed for 4 CPU cores; GPU-only items are experiments |

---

## Appendix A. Raw measurements

- **Profile** (v11, frames 560–656 every 4th, single worker, cumulative 58.7 s):
  - `np.interp` 13.3 s tottime (754 calls);
  - `grade` 21.8 s cumulative (68 calls for 25 frames);
  - `afterimages` 20.7 s cumulative;
  - `DISOpticalFlow.calc` 4.2 s (32 calls);
  - `imread` 3.6 s (30);
  - `warpAffine` 3.4 s (176);
  - `motes11` 5.2 s cumulative;
  - `GaussianBlur` 2.9 s (354);
  - `light_from` 2.4 s;
  - `finish11` 3.5 s cumulative;
  - `sr_flow_part` 9.2 s cumulative.
- **Per-frame render times:**

  | Frame | Moment | Time |
  |---|---|---|
  | 100 | rival open | 0.63 s |
  | 452 | bolt split | 1.26 s |
  | 610 | BOP hook | 3.14 s |
  | 800 | remnants | 2.05 s |
  | 906 | rift | 1.52 s |
  | 1000 | fire | 1.16 s |
  | 1176 | flip | 1.24 s |
  | 1232 | dive | 1.85 s |

- **Start-up:** import 5.1 s, source load 5.8 s, mattes 0.9 s.
- **Benchmarks:**
  - grade curve: `np.interp` 329 ms, index LUT 23 ms, uint16 LUT 12 ms;
  - band 1440×704: JPEG 8 ms, raw `.npy` 0.7 ms (0.33 MB vs 3.04 MB);
  - DIS flow at 640×720: 23 ms;
  - σ16 blur: 71 ms at full resolution, 7 ms at quarter resolution.
- **Full renders:** v9 3 (606–629 s each); v10 9 (752–1044 s); v11 7 (786–914 s). QC 28–51 s. Audio 7–10 s.
- **Commit timeline:**
  - v11 first delivery about 2–2.5 h after the brief;
  - rev 2 about 30 min;
  - rev 3 about 1 h;
  - rev 4 about 1.5 h;
  - v10 rev 3 about 3 h (including restoration).

## Appendix B. The first-pass rubric (use it now, before the tools exist)

Answer every line before delivering a first cut:
1. **Concept:** one sentence, found in the song's words or the character's history, visible in the grade, set pieces, sound and loop.
2. **Song:** the best part; the drop at 30–47 %; the biggest transition on the biggest change.
3. **Density:**
   - ≥ 18 designed, themed transitions, each with its own sound;
   - no span over ~1 s after the drop without a designed event;
   - no shot that only "moves to the beat" (give each a beat moment).
4. **Set pieces:** ≥ 3 multi-stage pieces; one focal piece on a structural moment; **the loop is the most creative transition** and lands on frame 0 (seam ≤ 1).
5. **Motion:** speed ramps with flow slow motion on the hook and montage; the beat camera.
6. **Detail:** hero graphics built as lit, bevelled objects and revealed on real tracked objects; checked at full resolution; nothing looks drawn; library transitions restyled.
7. **Faces and light:** nothing over faces; light sources behind the subject with a light wrap; when a subject burns or dissolves away, remove him before drawing light.
8. **Text:** only verified sung words, on their onsets, in the approved construction, one designed animation per moment; two titles at most for explicit songs.
9. **Picture:** restored sources; sharpness-ranked, no SOFT or LOWBIT on hero shots; zoom ≤ 1.10; per-shot exposure; no white-outs, flares ≤ ~110 mean luma.
10. **Sound:** layered sound per transition; effects mixed against the master's loudness; a circular loop; −13 LUFS, ≤ −2.5 dBTP after AAC.
11. **Branding:** the logo once, unrestyled; no labels, watermarks, counters or outro.
12. **Predict the owner's notes:**
    - Would he ask for more transitions, animations, graphics or sound? Where?
    - Is the loop the best moment?
    - Is any effect plain?
    - Is any clip soft?
    - Is any shot weak?

    Fix every "yes" before delivering.

## Appendix C. Where things are today (Flash branch)

| Thing | Path |
|---|---|
| Engine (Flash base) | `v11/work/render11.py`, `audio11.py`, `qc11.py` (flash check §7b, seam ≤ 1) |
| Tools | `tools/` (`new_edit.py`, `song_map.py`, `transcribe.py`, `check_sources.py`, `build.sh`, `sr_prep.py`, `srnet.py`, `sharpness.py`, `setup_studio.sh`, `edl_template.py`) |
| Rules and data | `CLAUDE.md`, `studio/VOIDFX_STUDIO.md`, `studio/preferences.json`, `studio/SCENE_PACKS.md`, `docs/TOOLKIT.md`, `studio/STUDIO_HANDOFF.md` |
| Sync | `sync/` (README, template, ledger, handoffs) |
| Edit history | `vN/README.md`; handoffs in `sync/handoffs/` |
