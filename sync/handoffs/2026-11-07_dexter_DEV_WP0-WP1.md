# DEV HANDOFF: pipeline v2, WP0 (one code base) + WP1 (golden frames and metrics)

**From:** the Dexter studio (development lead) · **To:** the Flash studio · **Date:** 2026-11-07
**Branch:** `dev/pipeline-v2` on `georrrgess-jpg/voidfx` (WP0 merge `a09772a`, WP1 `5957c88`)
**Owner approvals:** the code base lives in the voidfx repo; merge both branches as planned, keeping both sides (asked and answered before anything was pushed).

## 1. What changed

### WP0. One shared code base
- **Dexter branch pushed.** `claude/beautiful-volta-wjki7k` (v101–v105) is now on `georrrgess-jpg/voidfx` beside yours.
- **`dev/pipeline-v2`** is the merge of `claude/gallant-planck-pqpczp` (at `2c694dc`, your plan commit) and `claude/beautiful-volta-wjki7k`. All 11 conflicts were docs and tools, none was engine code:
  - **Docs** (`CLAUDE.md`, handbook, toolkit, start prompt, scene packs):
    - both studios' records are kept, each labelled `<!-- Flash studio (Studio 1) -->` / `<!-- Dexter studio (Studio 2) -->`;
    - tables keep each studio's own rows once;
    - a preface in `CLAUDE.md` records the agreed engine bases.
  - **`tools/new_edit.py`** takes `--base v11` (Flash, template `tools/edl_template.py`) or `--base v105` (Dexter, template `tools/edl_template_v105.py`). The default is v105 when "dexter" is in the slug or title, otherwise v11.
    - The v105 path also ports `fxN.py`, `splice.py` and `big.py`.
    - Both paths add `vN/sr/` to `.gitignore`.
  - **`tools/sharpness.py`** is one tool:
    - your tile/percentile `detail` and the `packs`, `N` and `N --src` modes;
    - plus our absolute scale (`abs` = mean|L − blur 1.2| / mean|L − blur 8|; ≈0.30+ reads sharp, < 0.20 soft) and LOWBIT (< 800 kb/s) in every mode;
    - SOFT = below 0.80× the edit's median, or below 0.20 absolute;
    - ZOOM above 2.95×;
    - dark shots no longer give a `nan` median (`np.nanmedian`).
  - **`tools/setup_studio.sh`** checks both engines: v11 and v105 import, their EDLs load.
  - **`.gitignore`** and `studio/src_manifest.json`: the union of both.
- **Acceptance met:** v11 and v105 both render from one checkout, and both scaffold bases import and build.

### WP1. Regression harness and metrics
- **`tools/golden.py`** (all modes return exit code 0 on pass, 1 on fail):
  - `python3 tools/golden.py N --save` renders the reference frames with the edit's own renderer, exactly as `renderN.py stills` sets it up: tracks and mattes loaded, full resolution, a fork pool of 4 workers. It stores them as PNG in `vN/work/golden/`, which git ignores.
  - `--check` renders them again and compares: every frame must be within max |diff| ≤ 2/255 and mean < 0.2/255 (guardrail §2.8). It writes `vN/work/golden/report.json`.
  - **The frame list** comes from the EDL: frame 0, the last 3 frames, every cut, the middle of every shot, the drop, and any set-piece peaks listed in an optional `GOLDEN_EXTRA = [frames]` in the EDL.
  - **Options:**
    - `--frames a,b,c` renders only those frames;
    - `--tag NAME` stores or compares a named set;
    - `--workers K`;
    - `--cachetest A:B` renders the range warm (one worker, in order, as a contiguous scheduler would) and cold (each frame in a fresh process), and the two must match. This is the test for any per-worker cache (WP2).
- **`tools/metrics.py`:** `vN/work/metrics.json`, an append-only event list. Each event records the time, the git commit, and whether the tree had uncommitted changes.
  - **`build.sh` writes it after every step:** seconds, exit status, QC `[FAIL]` lines, and the frame count of a full render.
  - **The studio writes it during review:**
    - `metrics.py N note CATEGORY "owner's words"`;
    - `metrics.py N catch CATEGORY "what was caught by eye"`;
    - `metrics.py N round K`;
    - `metrics.py N verdict standard|rejected`.
  - **`metrics.py N show`** summarises: time per step, full renders, the last QC result, notes and catches by category, rounds, and the verdict.
- **`tools/build.sh`:** every step is timed and logged to metrics. Steps with several commands are chained, so a failure still stops the build. Previously `set -e` did that; it now records the failure first.
- **Fixed on the way:** in `golden.py`, `--frames` was read after the renderer import had replaced `sys.argv`, so it was ignored.

## 2. Golden results (unchanged tree)
| Edit | Frames | `--save` | `--check` |
|---|---|---|---|
| v105 DRACULA | 59 | 19.8 s (4 workers) | PASS, worst max 0/255, worst mean 0 |
| v11 BOP, with the restored bands (`v11/sr`, 710 bands) | 37 | 15.8 s (4 workers) | PASS, 0/255 |

Rendering is bit-deterministic across workers and runs on both engines.

## 3. Timings
WP1 adds no render cost. Baselines for WP2 (the full renders of v11 and v105, and the peak RAM) are in `2026-11-07_dexter_DEV_WP2-1.md`.

## 4. How the Flash studio adopts it
1. **Check out the branch:** `git fetch origin dev/pipeline-v2 && git checkout dev/pipeline-v2`. A separate worktree works too.
2. **Media stays out of git:** `src/`, `v*/out`, `v*/audio`, `v*/frames`, `v*/sr` and `v3/models`. Both EDLs hardcode `ROOT = "/home/user/VOIDFX"`. Either point `/home/user/VOIDFX` at the checkout (`ln -sfn <checkout> /home/user/VOIDFX`), or symlink your media folders into it.
3. **Save golden sets once, from the base commit, on your own machine:** `python3 tools/golden.py 11 --save` (and 10, if v10's mattes and bands are present).
   - Golden PNGs depend on local media (restored bands, mattes), so each studio keeps its own set and they are not compared across studios.
   - Then run `--check` on every PR branch.
4. **Log review metrics** while you work on v12: `python3 tools/metrics.py 12 note motion "…"`. Use the §1.1 note categories: motion, look, clip-quality, text, sound, loop, faces, structure.

## 5. Notes and open questions
- **v11's restored bands** were regenerated here with `tools/sr_prep.py 11` (710 frames, about 23 min on 4 threads). If your `v11/sr/index.json` has a different frame count, your v11 golden frames will differ from ours. That's expected, and it's why golden sets are per studio.
- **v11's song isn't in this checkout.** Timing renders of v11 here use silent stand-ins for `v11/audio/mix*.wav`. The picture and the video encode are unaffected.
- **v10 isn't in the golden runs yet.** Its mattes and bands aren't in this checkout. WP2's first PR doesn't touch `render10.py`, so v10 can't change. Please run `golden.py 10 --save` on your side from `dev/pipeline-v2` if you want it covered on later PRs.
- **Question:** which v11/v12 set-piece peaks should go into `GOLDEN_EXTRA`? For example the emblem flip, the dive and the rift. Shot midpoints cover most of them today.
