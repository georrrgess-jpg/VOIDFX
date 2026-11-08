# DEV handoff: the efficiency update (WP7, WP9, part of WP8). Dexter studio → Flash studio, 2026-11-08

The owner sent both studios the same request: make producing an edit faster, in the first delivery and in revisions, with
no loss of quality. This is the Dexter studio's part, merged on `dev/pipeline-v2`. The full plan, the measurements and the
proposed split are in `sync/EFFICIENCY_PLAN.md`.

## What changed
- **`studio/OWNER_RULES.md`:** every owner rule still in force, on one page; conflicts resolved to the newest verdict. Read it before designing and before delivering.
- **`studio/transitions.json`:** the owner's verdict on 73 transitions, with:
  - his words, and a `fix` for each rejected one;
  - tags: `black_occluder`, `face_gimmick`, `generic`, `signature`, `physical`, `lands_on_face`;
  - hero families: `singularity` (v13) and `jasmine` (v12).
- **`tools/plan_check.py N`** (WP7) checks the EDL before any render:
  - rejected and banned transitions;
  - a reused or look-alike clip (thumbnail structure and colour ≥ 0.75);
  - spins and dives that land without a tracked face;
  - the loop is a set piece;
  - a signature graphic transition;
  - the hero family as a motif (warn above 4, fail above 8);
  - density, generic share and repeats;
  - zoom, the spell-out grid, titles, holds with no beat;
  - the sound budget (grouped onsets on the effects stem: warn above 16, fail above 30).
  - **Calibration:** your v12 and v13 pass with 0 FAIL. Their WARNs: v12's jasmine family carries 7 transitions; holds of 1.5–1.75 s at the sky, cortex, full and last shots; v13's eye and watch pick up an earlier take.
  - **On first deliveries:** run on v13 rev 1, it FAILs the singularity at 11 transitions.
- **`tools/signoff.py N`:** review pages from the encode in 6 s (every transition, the loop, the titles, unexplained pops).
- **`tools/report.py N`:** the Measured block.
- **`studio/CRITIQUE_PROMPT.md`** (WP9): one fresh agent predicts the owner's notes before delivery.
- **`build.sh`:**
  - new steps: `plan`, `signoff`, `report`, `splice`, and `ship` (audio → plan → video → qc → signoff → report → deliver);
  - `video` runs `plan` first and stops on a FAIL (`PLAN_FORCE=1` overrides);
  - an edited `fxN.py` is re-spliced automatically before any rendering step;
  - `qc` runs its three passes in parallel (103 → 72 s on v107).
- **`studio/WORKFLOW.md`:** the fast loop for a first delivery and a revision, with time budgets.
- **No engine file changed;** the golden frames are unaffected.

## How to adopt
1. Pull `dev/pipeline-v2`.
2. On your next edit, design from `OWNER_RULES.md` and the registry, put `SIGNATURE = [...]` and `HERO_TINS = [...]` in the EDL, and use `build.sh N ship`.
3. Add your Flash verdicts to `studio/transitions.json` (the v10–v11 pieces, bolt transitions, any family). Unrated transitions are listed by `plan_check`, not judged.
4. If a check misfires on a Flash edit, calibrate it in `plan_check.py`, keeping v12, v13, v106 and v107 at 0 FAIL, and note it in your next DEV handoff.

## Proposed split (so we don't build the same thing twice)
- **Flash studio:**
  - render speed (the WP2 remainder: a ≤ 3 min full render with golden frames unchanged);
  - the Flash verdicts in the registry;
  - motionqc: label an impact transition's designed negative frame as a flash (it reads UNEXPLAINED, e.g. v107 frame 352).
- **Dexter studio:** WP5, a shared source library (restoration and mattes reused across edits).
- **Both:**
  - log every owner rejection in the registry the same turn;
  - keep `OWNER_RULES.md` current at each verdict;
  - pilot the loop on the next edit and report rounds and renders in the edit handoff (metrics.json has them).
