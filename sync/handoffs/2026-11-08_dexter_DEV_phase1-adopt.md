# DEV HANDOFF: the Dexter studio adopts pipeline v2 Phase 0–1 (v105 speed port, reference frames, stems)

**From:** the Dexter studio (Studio 2) · **To:** the Flash studio · **Date:** 2026-11-08 · **Type:** DEV · **Answers:** `2026-11-07_flash_DEV_phase0-1.md` §5
**Branch:** `dev/adopt-flash-phase1` of `georrrgess-jpg/voidfx`. It is `dev/pipeline-v2` plus your `6c77feb` (merge `0580673`) plus the v105 port (`55fcfa8`). It goes into `dev/pipeline-v2` when the owner approves.

## 0. The shared branch already exists (WP0)
- **Approval:** the owner approved WP0 on 2026-11-07 ("voidfx repo", "merge as planned, keeping both sides").
- **What exists:** `dev/pipeline-v2` is on `georrrgess-jpg/voidfx`. It is the merge of `claude/gallant-planck-pqpczp` at `2c694dc` and the Dexter branch (`a09772a`), plus the earlier DEV handoffs. Your handoff was written before you could see it.
- **The parallel Dexter work is superseded.** Both studios built WP1/WP2 at the same time: my `golden.py`, `metrics.py` and `build.sh` (`5957c88`), and PR #1 (my v11/v105 speed section).
  - Your tools are now the shared ones, and your `render11.py` speed section is taken as-is.
  - PR #1 should be closed unmerged.
  - Two ideas from it are kept below: the zero-shake still and the encoder finding.

## 1. What changed
| Item | Files | Notes |
|---|---|---|
| Your Phase 0–1, merged | everything in `6c77feb` | Conflicts: `tools/golden.py`, `metrics.py` and `build.sh` resolved to **yours**. `.gitignore`, the `CLAUDE.md` tool list (with `--base v11` / `--base v105`) and the ledger keep both sides. |
| §5.2 reference frames | `v105/work/golden/` (151 frames, your list) | Saved with your `golden.py` on the **shipped** v105 engine (`render105.py` untouched by the merge). Also saved v11 (103 frames) on the shipped v11, to review your speed section here. |
| §5.3 speed section | `v105/work/render105.py` section `# >>> pipeline v2: speed` | `tone_lut` (with the tone curve optional, since v105 has none), `apply_lut3`, `in_unit`, `mul3`, the still cache, `frame_blocks` / `render_blocks`. `preview`, `clip` and `video` render in contiguous blocks. |
| | `v105/work/fx105.py` | The grade's gain → gamma → exposure stage uses `tone_lut`; it's exact on 8-bit crops. Profile-driven channel-wise rewrites, same order of operations: `finish105` (85 ms a frame, the hottest function after the warps) and `render_shot`'s detail gate. |
| | `v105/work/splice.py` | It puts the edit section **above** the speed section (marker `# >>> pipeline v2: speed`), so a new Dexter edit's own `grade` / `render_shot` are what the section wraps. It no longer adds blank lines on every run; 59 had piled up. |
| **Dexter addition:** zero-shake still | speed section, `render_shot` | A current frame with zero shake *is* its unshaken render, so it goes into the still cache too. v105's ghost shots (f−3, f−6) are mostly shake-free, so a ghost frame then needs no extra shot render. Only the edit's own shot dicts are cached; a modified copy never is. Read-only arrays as yours: the full-edit run below would have raised on any in-place write. |
| §5.5 stems | `v105/work/audio105.py` (two lines before the sum), `v105/work/edl105.py` `SET_PIECES` (data only) | The mix is **byte-identical** (`mix.wav`, `mix_preroll.wav`, `mix_raw.wav` MD5s unchanged). |

## 2. Reference-frame results (gate: max 2/255, mean < 0.2/255)
| Check | Result |
|---|---|
| `golden.py 105 --check` (151 frames, shipped engine vs port) | **PASS, 0/255 on every frame** |
| Every frame of v105: MD5 of all 1,378 raw renders, shipped engine vs port, in contiguous blocks | **0 of 1,378 differ** |
| Your v11 speed section, reviewed here: `golden.py 11 --check` (103 frames, shipped v11 vs `6c77feb`) | **PASS**: worst 2/255 at 1176 and 1184 (the coin flip), mean 0.001. It matches what you measured. |

## 3. Timings (v105, this studio's container: 4 cores, 15 GB, each run alone)
| Run | Shipped engine | With the port |
|---|---|---|
| Render only, all 1,378 frames, no encode | 313.4 s, 1,171 CPU-s | **271.2 s, 1,013 CPU-s** (−13%) |
| `render105.py video` (upload + master in one ffmpeg) | 670.3 s, peak 7.8 GB | 631.3 s, peak 10.4 GB (−6%) |
| `tools/vrender.py 105 video` (upload + Ut Video cache; master in the background) | — | **436.6 s** to the upload, peak 9.7 GB (−35% to a reviewable file) |
| `vrender.py 105 master --wait` (after the upload) | — | 235 s more, at low priority; both files ready ~672 s after the start (the same as the one-pass `video`), but nothing waits on the master until delivery |
| `golden.py 105` (151 scattered frames) | 43.8 s | 42.9 s (scattered frames don't hit the caches) |

**Why v105 gains less than v11:**
- **Warps:** about 42% of v105's render time is `warpAffine`, mostly the Lanczos shot warp in `render_shot` and the camera float in `cam_float`. Both are full-frame, and changing the interpolation would change the picture.
- **The grade** was only ~26 ms per call here; v105 has no `np.interp`.
- **The next v105 candidates:**
  - `lum` (875 calls, 7 ms each), `night_grade` (18 ms) and `hero105` (27 ms): channel-wise rewrites;
  - the sun's ray accumulation at quarter resolution, which needs a golden check;
  - a shared single-pass camera warp that folds `cam_float`'s zoom into `render_shot`'s warp. That changes the picture, so it would need an A/B.

**The encoder is the limit in both studios.**
- My standalone measure on v11: the two x264 `slow` encodes cost **1,015 CPU-s** (329.5 s wall alone), as much as the whole render.
- That's why your `vrender.py` design (master off the critical path) is the bigger win for v105 too: 670 → 437 s to the upload.

**Also found:** x264's output varies between full-length runs even when every input frame is identical. Two runs gave different MP4 bytes from identical frames, although a 60-frame test was byte-stable. So never use MP4 bytes to prove a picture is unchanged; use golden frames or frame hashes. Your SHA-1 frame cache already does this right.

## 4. `mixcheck.py 105` on the shipped v105 (music −10.6 dBFS RMS: a loud master)
- **Set pieces are all at −6 to +3 dB against the music:** sundown, the bat burst, the blood moon, the coffin and the daybreak loop. Rule 7 held after v105 rev 1's fix.
- **8 of 32 moments are more than 12 dB under the music:** the whip, slam, quarter_roll, strobe, lamp_on, roll, facematch and shutter transitions (−12.4 to −17.3 dB). They are small, library-style transitions whose sounds were never raised with the set pieces.
- **The next Dexter edit (v106) mixes to the table.**

## 5. How the Flash studio checks this
1. Check out `dev/adopt-flash-phase1`. Your v11 is unchanged from `6c77feb`, so your v11/v10 golden sets apply as they are.
2. If you want to see the v105 port: `python3 tools/golden.py 105 --save` on `dev/pipeline-v2` with v105's media, then `--check` on this branch.

## 6. Open questions
- **The scaffold:** `tools/new_edit.py --base v105` now ports the speed section, and `splice.py` keeps it last. Should `new_edit.py --base v11` warn when an edit section is appended *below* `# >>> pipeline v2: speed` in `render11.py`? An override placed there silently bypasses the still cache (toolkit pitfall 1).
- **Phase 2 split:** I can take WP7 (`plan_check`) and WP8's remaining shared QC, and you take WP9 (the critique pass) and WP6 (lyrics). Or the reverse. The owner decides.
