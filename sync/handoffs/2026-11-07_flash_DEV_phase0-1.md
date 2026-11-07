# DEV HANDOFF: pipeline v2, Phase 0–1 (speed, previews, partial renders, face and mix checks)

**From:** the Flash studio (Studio 1) · **Date:** 2026-11-07 · **Type:** DEV (development, not an edit verdict) · **Branch:** `claude/gallant-planck-pqpczp` of `georrrgess-jpg/voidfx` · **Plan:** `sync/PIPELINE_V2_PLAN.md` (status table at the top)

The owner asked the Flash studio to begin the update ("You may begin the update"), so Phase 1 was built here instead of in the Dexter studio. **Nothing changes the look of an edit.** Every speed-up was checked against reference frames from the shipped engines.

## 1. What changed

| Package | Files | What it does |
|---|---|---|
| WP1 reference frames | `tools/golden.py`, `tools/edit_env.py` | Saves and compares 103–112 frames per edit (frame 0, last 3, every cut −6/0/+6, every shot's middle, every 32nd frame). Gate: max 2/255 per pixel, mean < 0.2/255. Prints render time, so it is also the benchmark. |
| WP1 metrics | `tools/metrics.py`, `tools/build.sh` | `vN/work/metrics.json`: every build step and its time (automatic), plus owner notes and by-eye catches by category (the studio logs them). |
| WP2 render speed | `v11/work/render11.py` (section "pipeline v2: speed", spliced before `main()`) | 1. One lookup table per channel for the grade's gain → gamma → exposure → tone curve (280 ms → 25 ms a band). 2. Cached read-only unshaken shot renders (afterimages, time slices). 3. Contiguous blocks per worker that never cross a cut. 4. Channel-wise writes instead of `a[..., None] * colour` broadcasts (3× faster, bit-exact) in `light_rgb`, `light_from`, `anamorphic`, `finish11`, `motes11` and the grade. 5. motes11's face mask blur (σ 25, 78 ms every frame) built from 1-D blurs (exact to 7e-7). |
| WP2/WP4 final renders | `tools/vrender.py` | Upload MP4 + a lossless frame cache (Ut Video, ~2.2 GB, SHA-1 per frame). The master is encoded from the cache in the background at low priority; `deliver` waits for it and checks it. **Partial re-renders:** the declared range (`--only A:B`) plus every shot whose EDL entry changed (±30 frames). ~30 frames outside the range (both edges, one per shot, 12 random) must re-render bit-exact, or it falls back to a full render. Changed EDL globals, cut points, tracks, mattes or restored bands also force a full render. `--dry` runs only the verification. |
| WP3 render server | `tools/rsrv.py` | Keeps the edit loaded with 4 warm workers: `stills`, `full` (PNG), `strip A B`, `clip A B`, `auto`. It restarts itself when the renderer, EDL, tracks, mattes or SR index change. |
| WP8 effects over faces | `tools/faceqc.py` | Final frame vs the shot's own picture inside the face box, after a gain/offset fit. It lists runs where > 3 % of the box gains > 0.10 luma, with a sheet. It skips transition windows, replaced faces and the last 12 frames (the loop landing). It is a review list, not a gate. |
| WP12 effects vs music | `tools/mixcheck.py`, `v11/work/audio11.py` (writes `stem_music.wav` / `stem_fx.wav`; the mix is byte-identical) | The loudest 50 ms of effects vs the music RMS at every transition and every `E.SET_PIECES` entry; flags more than 12 dB under. |
| build steps | `tools/build.sh` | `sheet:NAME:f,f` · `strip:A:B` · `clip:A:B` (server) · `video` (auto-partial) · `video:A:B` · `fullvideo` · `qc` (+ faceqc) · `deliver` · `golden`; `all` = prep audio auto video qc deliver. |

## 2. Measured results (v11 BOP, 4 cores)

| | Before | After | Plan target |
|---|---|---|---|
| Full render | 786–914 s | **427 s** (master follows in the background, ~4 min at low priority) | ≤ 6 min (missed: see §4) |
| Render work per frame (contiguous blocks, profiled) | 1.37 s | 1.06 s | — |
| One-shot revision (118 frames) | a full render | **227 s** | ≤ 3 min (close) |
| 24-frame full-quality sheet | 40–70 s | **7.6 s** warm, 28 s cold | ≤ 12 s ✓ |
| Reference frames, v2 engine vs shipped v11 | — | worst pixel 2/255 (coin flip 1176), mean ≤ 0.0013/255 | within gate ✓ |
| EDL change + partial render, then revert + partial render | — | frame cache bit-identical to the original full render (0 of 1,247 frames differ) | ✓ |
| Injected global change (grain 0.012 → 0.0125) with `--only 600:660` | — | verification failed on 32 of 32 frames → full render | ✓ |
| Frame cache | — | Ut Video, lossless (all 1,247 hashes verified on decode), 4.5× faster to encode than FFV1 | — |

## 3. Findings on the shipped v11 (they apply to the next edits)
- **Effects under the music:** 12 of 17 transitions have their effects 9–31 dB under the music. The music is −10.2 dBFS RMS, a loud master, the same situation as your v105 rev 1. Your rule 7 holds for Flash edits too. The next Flash edit will mix to the table.
- **Light over faces (faceqc):**
  - diagonal light sweeps across his face (frames 378, 830);
  - lightning crossing the face edge (552–574, 1020);
  - LET'S GO on his chin (420);
  - the designed red radiate in the REVERSE loop (1198–1216).
  This matches v11's known weakness ("light drawn over him, not behind") and your rule 1.

## 4. Open, and why
- **WP0:** your branch isn't visible from here, so `dev/pipeline-v2` doesn't exist yet. It needs the owner's approval. The Phase 1 code sits on the Flash branch.
- **6-minute render target:** the upload encode at x264 preset slow is about 2.3 min of 4-core time and the plan's guardrail 1 keeps it. What's left in rendering: INTER_CUBIC warps of float frames (~42 ms each), optical flow (~88 ms a frame; a cross-revision flow cache belongs to WP5), and many small full-frame NumPy ops. Next candidates if wanted: a flow cache in the library, the remaining `a[..., None] * c` sites in set pieces.
- **3-minute partial target:** the full upload re-encode is ~2.5 min of every partial. Splicing x264 segments at GOP boundaries would cut it to ~1 min, but changes rate-control behaviour at the joins, so it wasn't done without a quality A/B.
- **faceqc** is a list for the visual review. Titles and designed set pieces show up in it, so it shouldn't become a gate without per-edit allow-lists.

## 5. How the Dexter studio adopts it
1. Pull `tools/{golden,edit_env,vrender,rsrv,faceqc,mixcheck,metrics}.py` and `tools/build.sh` from `claude/gallant-planck-pqpczp`. They work with any `renderN.py` that has `load()`, `init_hits()`, `RAW_TRK`, `SEG`, `render(f)` and `shot_at(f)` (v105 has them). Ut Video must be in ffmpeg (`ffmpeg -h encoder=utvideo`).
2. `python3 tools/golden.py 105 --save` on your **shipped** v105 engine first.
3. Port the speed section ("pipeline v2: speed" before `main()` in `render11.py`):
   - `tone_lut` + `apply_lut3` for your grade;
   - the still cache, `frame_blocks` / `render_blocks`;
   - the channel-wise rewrites of whichever of your hot functions are profiled hot.
   Profile with cProfile on contiguous blocks first; the numbers differ per edit.
4. `python3 tools/golden.py 105 --check`: max ≤ 2, mean < 0.2, or revert that item.
5. In `audio105.py`, write the two stems just before music and effects are summed (two lines, see `audio11.py`). Then `mixcheck.py 105`.
6. Reply with a DEV handoff (`sync/handoffs/YYYY-MM-DD_dexter_DEV_<WP>.md`): golden result, timings before/after, anything that didn't port.

## 6. What the Flash studio does next
- v12 runs on this pipeline: the render server for sheets, `video` partials in revisions, mixcheck and faceqc before delivery, and `metrics.json` filled in, so v12 can be compared with v10/v11.
- Phase 2 (WP7 plan check, WP9 critique pass, WP6 lyrics, WP5 library), when the owner says go and the studios agree who builds which.
