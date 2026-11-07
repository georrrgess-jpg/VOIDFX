# DEV HANDOFF: pipeline v2, WP2 items 1–3 (grade by lookup, contiguous scheduling, shot-render cache)

**From:** the Dexter studio (development lead) · **To:** the Flash studio · **Date:** 2026-11-07
**PR:** `dev/wp2-speed-1` → `dev/pipeline-v2` on `georrrgess-jpg/voidfx` (PR #1, https://github.com/georrrgess-jpg/VOIDFX/pull/1)
**Machine for every number below:** the Dexter studio's container: 4 CPU cores, a 15 GB memory limit, no GPU. Each timing ran alone on the machine.

## 1. What changed
Every engine now ends with one shared section, `# >>> pipeline v2 · WP2`. It is identical in `render11.py` and `render105.py`.
- **Keep it last.** `splice.py` now inserts a v105-based edit's section above it.
- **In a v11-based engine, add new edit sections above it too.** A `render_shot` defined below it bypasses the cache. That's still correct, only slower.

1. **Grade by lookup: `pre_grade(img, gains, g, ev, key, curve)`.**
   - Gains, gamma, exposure and the look's tone curve (`np.interp`) become one function per channel, tabulated on 65,536 levels from the exact original expression.
   - The grid contains every 8-bit level exactly (65,535 = 255 × 257), so a frame graded from 8-bit pixels (held frames, restored bands) is **bit-identical**.
   - Flow and blended in-betweens use the nearest level plus slope × remainder: within ~2e-5 of `np.interp`, usually within 4e-7.
   - Inputs outside [0, 1] take the exact path.
   - **v11's `grade`** (VOLTAGE/RIVAL) uses it, and runs the rest of the grade (saturation, skin, shadows, highlights) on contiguous colour planes, in place, with the same operations in the same order. It went from 196–289 ms to 65–76 ms per band.
   - **v105's `grade`** (`fx105.py`) uses it for its first stage. v105 has no `np.interp`, so the gain there is small.
2. **Contiguous scheduling: `imap_blocks(pool, frames)`.** It replaces `pool.imap(render, …, chunksize=4)` in `video`, `preview` and `clip`.
   - Each worker gets blocks of 32 consecutive frames, cut where a shot starts. Blocks are split in four over the last 4 × 32 frames, so the workers finish together.
   - **At most workers + 2 blocks are in flight.** Without that bound, `pool.imap` queues every task at once. When the encoder is the slower side, finished frames pile up in memory: the first version of this PR peaked at **12.1 GB** on v11.
   - The `auto` sheets give each worker one side of a cut (3 frames), which share that side's edge frame.
3. **Shot-render caches (per worker).**
   - **`RS_CACHE`** (12 entries) keeps unshaken `render_shot` results (picture + matte) per (shot, frame). v11's afterimages (f−4, f−8, f−12) and v105's ghost trails (f−3, f−6) re-use frames this worker has just rendered. A zero-shake current frame counts as unshaken, which covers most of v105's ghost shots.
   - **`ROI_CACHE`** (8 entries) keeps v11's graded crop per (shot, frame). It doesn't depend on the shake, so the shaken render of f and the unshaken re-render its afterimages ask for 4 frames later share one grade. v11's `render_shot` is split into `graded_roi()` and the warp.
   - Hits return copies. Only the edit's own shot dicts are cached: a copy or modified dict is never cached.
- **Also:**
  - `splice.py` is now idempotent. Each run used to add blank lines, and 59 had piled up in `render105.py`.
  - `docs/PIPELINE_V2.md` describes each package.
  - Settings are environment variables: `VFX_BLOCK`, `VFX_RS_LRU`, `VFX_ROI_LRU`. `0` turns a cache off.

## 2. Golden results (guardrail §2.8: max ≤ 2/255, mean < 0.2/255)
| Check | v11 BOP (with restored bands) | v105 DRACULA |
|---|---|---|
| `golden.py --check` | PASS: worst max 1/255, worst mean 0.0000 (37 frames) | PASS: 0/255 (59 frames) |
| Every frame of the edit (MD5 of each raw frame, base vs PR) | 654 of 1,247 differ: the flow and blended in-betweens, within the golden numbers above. Every frame graded from 8-bit pixels is identical | **0 of 1,378 differ** |
| `--cachetest` (warm, in order, vs cold, a fresh process per frame) | 454–538 (drop, afterimages) and 595–651 (run): 0/255 | 892–939, 1000–1033 (ghosts) and 0–12: 0/255 |

**Note on encoded files.** The v105 MP4s from the base code and from this PR are not byte-identical, although every raw frame is.
- In a 60-frame test, x264 gave byte-identical output for identical input, with or without timing jitter, with one output or two.
- The full-length runs still differ from frame 5 on (PSNR 40.8–∞ dB between the two encodes, mean 49.8).
- Two runs of this PR on the same frames (raw hashes identical) also gave different MP4 bytes, so x264's output varies between full-length runs here (the cause is likely its frame threads over long runs).
- **The golden frames and the raw-frame hashes are the test of picture identity,** not the MP4 bytes.

## 3. Timings (4 cores; before = `dev/pipeline-v2` at `5957c88`)
| Run | Before | After | Change |
|---|---|---|---|
| v11 grade, per restored band | 196–289 ms | 65–76 ms | ~3.5× |
| v11 render only, all 1,247 frames, no encode | 388.6 s (1,469 CPU-s) | 304.1 s (1,095 CPU-s) | −22% wall, −25% CPU |
| v105 render only, all 1,378 frames, no encode | 313.4 s (1,171 CPU-s) | 296.4 s (1,091 CPU-s) | −5% wall, −7% CPU |
| **v11 full render** (`video`: upload MP4 + master MOV) | **698.3 s**, peak 7.6 GB | **622.6 s**, peak 11.1 GB | −11% |
| **v105 full render** | **670.3 s**, peak 7.8 GB | **657.2 s**, peak 9.3 GB | −2% |
| The encode alone (v11: decode + the render's exact two-output encode) | 329.5 s, 1,015 CPU-s | — | — |
| golden check (v11 / v105) | 25.8 / 29.3 s | 21.5 / 29.3 s | |

**Where the full render goes.** A full render's wall time is roughly (render CPU + encode CPU) / 4 cores, since the encoder shares the four cores with the workers.
- **The encoder's share:** x264 `slow` at 1080×1920 for two outputs (CRF 17 upload + CRF 11 master) costs **~1,015 CPU-seconds**, about 4 minutes of the machine on its own.
- **This PR cut v11's render CPU from 1,469 to 1,095 s.** The encoder is now roughly half of the total.
- **The plan's target (v11 full render ≤ 6 min) is not reachable with items 1–3 alone.** Even a free renderer would leave ~4.2 min of encoding. Reaching it needs item 7 (encoder) together with items 4–6.
- **Proposal for item 7, keeping the final preset:** during review rounds, write only the CRF 17 upload with `video`; write the CRF 11 master only at delivery (`video --master`). That removes roughly half of the encode cost in every round. Final quality is unchanged.

**Why v105 gains less.** v105's time is in Lanczos warps of full frames (~31% of the render, in `render_shot`), the sun's rays, and `finish105`. Its grade was only ~5%, and its ghost shots are 9% of the frames. The next v105 wins are items 5 (blur audit) and 6 (band and decode caching), plus a quarter-resolution sun ray pass. That is a picture change, so it needs a golden check.

**Peak memory:** v11 11.1 GB, v105 9.3 GB (before: 7.6 / 7.8 GB). The first, unbounded version peaked at 12.1 GB on v11 (target ≤ 12 GB). The bound on in-flight blocks is what keeps it there. Caches add ~0.5 GB per worker.

## 4. How the Flash studio adopts it
1. **Before merging,** on `dev/pipeline-v2` with your own media: `python3 tools/golden.py 11 --save` (and 10 if you have its mattes and bands).
2. **Check out `dev/wp2-speed-1`** and run `python3 tools/golden.py 11 --check` and `python3 tools/golden.py 11 --cachetest 454:538`. Both must pass. Your restored bands may differ from ours, so your numbers can differ slightly.
3. **v12 from `tools/new_edit.py --base v11`** inherits the section. Keep new edit sections above `# >>> pipeline v2 · WP2`. A `grade` copied from v11 gets the fast path; a new look calls `pre_grade(img, gains, g, ev, "<look>", (lx, ly))` in place of `np.clip(img * gains, 0, 1) ** g` + `np.interp`.
4. **If a render ever looks different,** run it once with `VFX_RS_LRU=0 VFX_ROI_LRU=0` to rule the caches out, and tell us.

## 5. Open questions
- **Item 7:** OK to make the CRF 11 master a delivery-only output (`video --master`), with the upload MP4 alone during review rounds? Final quality is unchanged.
- **v10:** can you add v10's golden check to your review? Its engine isn't touched by this PR.
- **The next PR (WP2 items 4–6: flow cache, blur audit, band decode)** will be benchmarked the same way. Tell us if you'd rather see WP3 (render server and fast previews) first; it would shorten your review loop more.
