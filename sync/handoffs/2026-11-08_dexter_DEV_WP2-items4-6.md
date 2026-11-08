# DEV HANDOFF: WP2 items 4–6 (flow cache, blur audit, band decode), and the owner's decisions closing Phase 1

**From:** the Dexter studio · **To:** the Flash studio · **Date:** 2026-11-08 · **Type:** DEV
**Branch:** `dev/wp2-speed-items4-6`, now merged into `dev/pipeline-v2` (see §5).

## 1. The owner's decisions (2026-11-08: "can you just decide for me")
1. **PR #1 is closed unmerged.** Your Phase 0–1 is the shared base; your review stays as the record.
2. **Everything is merged into `dev/pipeline-v2`:** your Phase 0–1 (`6c77feb`, `177e8df`, `bcff29c`), the v105 port, and this package. Both studios edit from `dev/pipeline-v2` from now on.
3. **Phase 2 is paused, and both studios go back to editing.**
   - v106 (Dexter) and v12 (Flash) are the pilots the plan asks for. Log them in `metrics.json` with the §1.1 categories.
   - **The split when Phase 2 resumes** follows the code each studio owns (your suggestion):
     - **Dexter studio:** WP7 (`plan_check`) and WP6 (lyrics);
     - **Flash studio:** WP9 (the critique pass) and WP8's shared QC.

## 2. What changed
| Item | Change | Exact? |
|---|---|---|
| **4. Flow cache** (v11 speed section, block 6) | `flow_cols()`: each source pair's DIS flow, both directions, computed on the whole source frame as before. It is stored once as float32, cropped to the columns the pair's two restored bands share (the only part `sr_flow_part` reads), in `vN/work/cache/flow/<source file>/i0_i1_xa_xb.npy` with an atomic write. Later renders, revisions and partial re-renders load it. `sr_flow_part` is overridden in the speed section to read it. `VFX_FLOW_CACHE=0` turns it off. v11: 345 pairs, ~1.65 GB. `vrender.py clean` leaves it; delete the folder at the verdict. | Yes: the stored numbers are the computed ones |
| **5. Blur audit** | **v11:** no full-resolution blur with σ > 4 is left in the hot path (your Phase 1 moved them). The largest full-res blur is `base10`'s σ 1.5 sharpen, which has to stay full res. **v105:** `draw_sprite` (both engines) now blurs only the part of the warped tile that lands in the frame, plus 4σ + 2 px, as a copy so the borders are the tile's own. It used to blur whole zoomed sprites up to 5,067 × 5,067 × 4, 1.85 s each, mostly off-screen. | Yes: 0.0 difference on 40 random sprites; 0/255 on golden |
| | **Rejected:** moving v105's big full-frame blurs (`coffin_tr` σ 40, `burn_fx` σ 14, `rim_fx` σ 18, `logo_through` σ 20, `hero105` σ 9, `ash_body` σ 6) to quarter or half resolution. Measured on their real inputs, it moves the blurred values by 2.6–7.8% of their peak (up to 20/255), far outside the gate. | — |
| **6. Band decode** | **Not done (measured):** restored-band `imread` is 105 calls and 0.8 s over the 192 benchmark frames, ~4 ms a frame (0.4%). Raw `.npy` bands would cost 2.6 GB of disk for that. | — |

## 3. Reference frames (your `golden.py`, saved on the shipped engines; gate max 2/255, mean < 0.2/255)
| Check | v11 (103 frames) | v105 (151 frames) |
|---|---|---|
| `golden.py --check` | PASS: worst 2/255 at 1176/1184 (the coin flip, from the Phase 1 grade), mean 0.0013. Unchanged by this package | PASS: 0/255 on every frame |
| Every frame, MD5 of the raw renders | **0 of 1,247 differ** between flow cache off, filling and warm | **0 of 1,378 differ** from the shipped v105 |

## 4. Timings (4 cores, 15 GB, each run alone)
| Run | Before this package | After |
|---|---|---|
| v11 same-block benchmark (8 × 24 contiguous frames, s per frame per worker) | 0.973 s (flow cache off) | **0.877 s** (−10%) (warm) |
| v11 render only, all 1,247 frames | 247.6 s, 856 CPU-s (cache off) | **227.8 s, 784 CPU-s** (−8%) (warm); first render, filling the cache: 245.7 s (it costs nothing extra) |
| v11 `vrender.py video` (upload + frame cache; master in the background) | 375.4 s, peak 11.8 GB | **369.1 s**, peak 10.9 GB (6.2 min; the master follows in the background) |
| v105 render only, all 1,378 frames | 271.2 s, 1,013 CPU-s (the Phase 1 port) | **262.7 s, 954 CPU-s** |
| v105 same-block benchmark | — | 0.741 s per frame per worker |

**Reading these numbers.** The flow cache cuts render CPU by 8–10%, but the full render to the upload barely moves (375 → 369 s): with the CRF 17 upload encode sharing the 4 cores, the encoder is now the limit. The plan's ≤ 6 min target is reached within 10 s (6.2 min to a reviewable upload). The next real gain is an encoder decision (guardrail 1 keeps preset slow), not more render work. The flow cache's bigger win is in revisions: every partial re-render (`video:A:B`) and every render after the first skips the flow entirely.

## 5. Merged
`dev/pipeline-v2` now contains:
- `d697a66`: your Phase 0–1, the v105 port and the stems;
- this package.

Scaffolding a new edit (`tools/new_edit.py --base v11` or `--base v105`) carries the speed section, the flow cache and the cropped sprite blur.

## 6. For the Flash studio
- **Pull `dev/pipeline-v2` for v12.** Its first full render fills the flow cache. Every revision after that reads flow from disk.
- **Follow-ups for when engine work resumes** (from PR #1, your §3): the exact lookup between levels (v11's worst golden pixel 2 → 1/255) and the graded-crop cache.
