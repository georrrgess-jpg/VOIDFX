# Pipeline v2: what changed, and how to use it

The plan is `sync/PIPELINE_V2_PLAN.md`. This file records what has actually been built, one section per work package, in the order the packages merge into `dev/pipeline-v2`.

## WP1. Golden frames and metrics
- **Before and after every engine change:** `python3 tools/golden.py N --save` on the base commit, then `--check` on the change.
  - The pass rule is §2.8: every frame within max 2/255, and a mean under 0.2/255.
  - `--cachetest A:B` checks that a per-worker cache doesn't change the picture: it compares a warm, in-order render with a cold render (a fresh process per frame).
- **`vN/work/metrics.json`:** `tools/build.sh` appends every step to it. The studio adds owner notes, catches and rounds through `tools/metrics.py`, and `python3 tools/metrics.py N show` summarises them.

## WP2. Render speed, items 1–3
Every engine ends with one shared section, `# >>> pipeline v2 · WP2`. **Keep it last.** `splice.py` inserts a v105-based edit's section above it. In a v11-based engine, add new edit sections above it too: a `render_shot` defined below it bypasses the cache. That's still correct, only slower.

1. **The grade by lookup (`pre_grade`).**
   - Gains, gamma, exposure and the look's tone curve are one function per channel, held in a 65,536-level table built from the exact original expression.
   - The table contains every 8-bit level exactly (65,535 = 255 × 257), so frames graded from 8-bit sources, restored bands included, come out **bit-identical**.
   - Blended and flow in-between inputs use the nearest level plus slope × remainder, which lands within about 2e-5 of `np.interp`, usually within 4e-7. That is a 1/255 step on about 1 pixel in 100,000.
   - Inputs outside [0, 1] take the exact path.
   - v11's grade also runs its saturation, shadow and highlight steps on contiguous colour planes in place: the same operations in the same order.
   - Speed: v11's grade goes from 196–289 ms to 65–76 ms per band (measured on this machine).
2. **Contiguous scheduling (`imap_blocks`).**
   - Full renders, previews and clips send each worker blocks of consecutive frames: `VFX_BLOCK` = 32, cut where a shot starts. At most workers + 2 blocks are in flight, so finished frames never pile up in memory when the encoder is the slower side.
   - Blocks are split in four over the last `4 × 32` frames, so the workers finish together.
   - Auto sheets give each worker one side of a cut, 3 frames, which share that side's edge frame.
3. **Shot-render caches.**
   - **`RS_CACHE`** (`VFX_RS_LRU` = 12 per worker) keeps unshaken `render_shot` results, picture and matte, per (shot, frame). Afterimages (v11) and ghost trails (v105) re-use frames the worker has just rendered. A zero-shake current frame counts as unshaken, which is most of v105's ghost shots.
   - **`ROI_CACHE`** (`VFX_ROI_LRU` = 8) keeps v11's graded crop per (shot, frame). That crop doesn't depend on the shake, so the shaken render of a frame and the unshaken re-render its afterimages ask for later share one grade.
   - A hit returns a copy, and a copied or modified shot dict is never cached.

The settings (`VFX_BLOCK`, `VFX_RS_LRU`, `VFX_ROI_LRU`) are environment variables. `0` turns a cache off.

### WP2 items 1–3: measured (4 cores, 15 GB, each run alone)
| Run | Before | After |
|---|---|---|
| v11 grade per restored band | 196–289 ms | 65–76 ms |
| v11 render only (1,247 frames, no encode) | 388.6 s, 1,469 CPU-s | 304.1 s, 1,095 CPU-s |
| v105 render only (1,378 frames, no encode) | 313.4 s, 1,171 CPU-s | 296.4 s, 1,091 CPU-s |
| v11 full render (upload MP4 + master MOV) | 698.3 s, peak 7.6 GB | 622.6 s, peak 11.1 GB |
| v105 full render | 670.3 s, peak 7.8 GB | 657.2 s, peak 9.3 GB |
| The encode alone (v11, both outputs) | 329.5 s, 1,015 CPU-s | — |

A full render costs about (render CPU + encode CPU) / 4 cores of wall time. The two x264 `slow` encodes cost about 1,000 CPU-seconds on their own, so the WP2 target of ≤ 6 minutes also needs item 7 (encoder) as well as items 4–6. Golden frames: v11 worst max 1/255, worst mean 0.0000; v105 0/255, and all 1,378 raw frames are identical.

x264's output varies between full-length runs even when every input frame is identical (two runs of this code gave different MP4 bytes), so encoded files can't prove that a change left the picture alone. Use `golden.py --check` and per-frame hashes of the raw renders instead.
