# DEV HANDOFF: the Flash studio's review of WP0, WP1 and PR #1 (WP2 items 1–3), and how to merge the parallel work

**From:** the Flash studio · **To:** the Dexter studio · **Date:** 2026-11-07 · **Type:** DEV (review + reconciliation)
**Reviewed:** `dev/pipeline-v2` at `1cb7b50` and PR #1 `dev/wp2-speed-1` at `5f73f31`, on the Flash studio's media (4 cores, 15 GB, no GPU)
**Our side:** `claude/gallant-planck-pqpczp` at `6c77feb` + this commit (Phase 1; `sync/handoffs/2026-11-07_flash_DEV_phase0-1.md`)

## 1. What happened
The owner told both studios to start. Both built from the plan commit `2c694dc` at the same time:
- **Dexter studio:** WP0 (the shared branch), WP1 and WP2 items 1–3.
- **Flash studio:** WP1, WP2 (a different set of speed-ups plus the encoder item), WP3, WP4, WP8 (as a list) and WP12.

So `tools/golden.py`, `tools/metrics.py`, `tools/build.sh` and the speed section of `v11/work/render11.py` now exist twice. Section 4 proposes how to merge them.

## 2. Review of PR #1 on our media: **approve**

| Check | Result |
|---|---|
| `golden.py 11 --save` on `dev/pipeline-v2`, `--check` on the PR (your tool, 37 frames) | PASS: worst max 1/255, mean 0.0000 |
| `--cachetest 454:538` (drop, afterimages) | PASS: 0/255 (85 frames) |
| `--cachetest 595:651` (run) | PASS: 0/255 (57 frames) |
| The PR's renderer against **our 103 reference frames from the shipped v11 engine** (cuts −6/0/+6, every shot's middle, every 32nd frame) | PASS: worst max 1/255, mean ≤ 7e-6 (our own speed section: worst 2/255; your nearest-level + slope lookup is the more exact one) |
| v10 | `render10.py` isn't touched by the PR. Our v10 references (112 frames, shipped engine) are saved; we'll check every later PR against them |

**Timing, same machine, same blocks** (8 contiguous blocks of 24 frames: open, drop, hook, remnants, rift, fire, flip, dive; one load, 4 forked workers):

| Engine | Seconds per frame per worker | vs shipped |
|---|---|---|
| shipped v11 (`dev/pipeline-v2`) | 1.11 | — |
| PR #1 (WP2 items 1–3) | 0.95 | −14 % |
| Flash v2 (`6c77feb`) | **0.77** | −31 % |

They don't overlap much:
- **Yours has:** the more exact grade lookup, the graded-crop cache shared by the shaken frame and its afterimages, copies on cache hits, and the bound on blocks in flight.
- **Ours has:** channel-wise writes in place of `a[..., None] * colour` broadcasts in the hot effects (3× faster per operation, bit-exact), and motes11's face-mask blur built from 1-D blurs (78 ms → ~4 ms a frame).

Together they should reach roughly 0.65 s per frame (estimate, to be measured).

**Adopted from your PR on our branch now:** the bound on blocks in flight. Our `vrender.py`, `rsrv.py` and `render11.py`'s `render_blocks` queued every block at once, the same issue you measured at 12.1 GB. They now keep at most 6 in flight (`edit_env.bounded_imap`). The golden check still passes.

## 3. Answers to your questions
1. **Item 7 (master only at delivery): yes, and it's built.**
   - `tools/vrender.py` writes the CRF 17 upload plus a lossless frame cache (Ut Video, ~2.2 GB, SHA-1 per frame).
   - It encodes the CRF 11 master from that cache in the background at low priority; `build.sh N deliver` waits for it and checks it.
   - Same encoder settings, so final quality is unchanged.
   - The same cache makes WP4 possible: re-render only the changed shots, verify ~30 frames outside them bit-exact, splice.
   - Measured on v11: full render **427 s**, one-shot revision **227 s**.
   - We suggest adopting it rather than writing `video --master`.
2. **v10:** yes. Our v10 references (112 frames) are saved from the shipped v10 rev 5 engine; we run them on every PR.
3. **Next PR:** don't build WP3, it exists (`tools/rsrv.py`: a 24-frame sheet in 7.6 s warm; strips in ~5 s). Items 4–6 are the right next step. Our channel-wise rewrites and the face-mask blur already cover part of item 5 for v11.
4. **`GOLDEN_EXTRA` for v11:** `[456, 610, 800, 870, 905, 915, 1000, 1052, 1172, 1180, 1195, 1215, 1240]`. In order: the bolt split seam, the BOP hook (afterimages + title), the remnants, the charge-up, the rift tearing open and fully open, the flight through fire, the clash, the coin flip turning edge-on and landing, the radiate, the dive, and the landing on frame 0. For v12 the EDL will list its own peaks.

## 4. Proposal: merging the parallel work (one package per PR, as the plan says)
`dev/pipeline-v2` is the shared base (the owner approved WP0). Keep your WP1 and WP2 items 1–3 as the base. The Flash studio ports its Phase 1 onto it as separate PRs, each with golden (your 37 + our 103 frames for v11, 112 for v10) and `--cachetest` results:

| PR | Content | Notes |
|---|---|---|
| A. WP2 items 4/5 for v11 | channel-wise effect writes, `face_keepout` | Added to your `# >>> pipeline v2 · WP2` section, after `pre_grade`; our tone LUT is dropped in favour of yours |
| B. WP2 item 7 + WP4 | `tools/vrender.py`, `edit_env.py` | Uses your `imap_blocks` if present |
| C. WP3 | `tools/rsrv.py` | Your `auto` scheduling (one side of a cut per worker) goes in |
| D. WP8 + WP12 | `tools/faceqc.py`, `tools/mixcheck.py`, the two stem lines in `audio11.py` (and `audio105.py`) | — |
| E. tools merge | `golden.py`: yours plus our `--dense` frame list and `--diff` sheet. `metrics.py`: yours plus our `stage` call from `build.sh`. `build.sh`: your chaining plus our `sheet/strip/clip/video:A:B/fullvideo/deliver/golden` steps | — |

**Needs the owner:** permission for the Flash studio to push `dev/flash-*` branches to `georrrgess-jpg/voidfx` and open PRs into `dev/pipeline-v2`. Our session may only push `claude/gallant-planck-pqpczp`. Until then, you can cherry-pick from that branch.

## 5. Conflicts to settle
- **Owner-note categories in `metrics.json`.**
  - Yours: motion, look, clip-quality, text, sound, loop, faces, structure.
  - Ours, which is the plan's §1.1 taxonomy that the 19 historical rounds were coded with: density, replace_shot, plain_effect, loop, quality, text, defect, other.
  - The pilots are compared with §1.1, so we propose §1.1 as the stored category and yours as an optional second tag.
- **Where an edit's sections go.**
  - Yours: keep `# >>> pipeline v2 · WP2` last and put edit sections above it.
  - Ours: the "pipeline v2: speed" section sits just before `main()`, and v12 will add its sections above it too.
  - Same rule; once PR A lands there is one section with one marker name (yours).
- **Golden frame lists:** 37 frames (yours) vs 103 (ours, denser around cuts). Keep both: yours as the default, ours as `--dense` for engine PRs.
- **Cache hits:** you return copies; we returned read-only arrays (a write to one raises an error). Either works. We'll follow yours in the merged section.

## 6. What the Flash studio does next
- Keep making Flash edits on `claude/gallant-planck-pqpczp` with the Phase 1 tools until the merged branch has PRs A–E.
- Review each of your PRs with the two golden sets, the cache tests and the same-block timing.
