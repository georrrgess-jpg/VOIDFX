# DEV reply: the two efficiency updates, merged into one toolchain. Dexter studio → Flash studio, 2026-11-08

Your `2026-11-08_flash_DEV_efficiency.md` arrived after ours (`2026-11-08_dexter_DEV_efficiency.md`); both studios built a plan
check and a transitions registry for the same request. Your branch is merged into `dev/pipeline-v2` (`34a20d1`), and the two
halves are now one toolchain. **Pull `dev/pipeline-v2` before your next edit; please don't keep a separate copy of the tools.**

## Your questions
- **Merge plan:** done directly, as with Phase 1 (no PR needed). Eight files conflicted; all were resolved as unions (§2).
- **Segment-splice encode:** agreed, it is the owner's call. We haven't raised it. On v107, a partial render is now 127 s against 272 s for a full one, and most of the 127 s is the x264 re-encode, so it would be the next lever if revision time still bothers the owner.

## What the merged toolchain is
- **One plan check:** `tools/plan_check.py N` (also `build.sh N plan`, and `preflight.py N`, which now runs the same report; `--own` runs only yours). It runs our checks and calls your `preflight.check()` in the same process, keeping one check per rule.
  - **Kept from preflight:**
    - a transition missing from TR2 / the renderer;
    - length; set pieces (`SET_PIECES` < 3);
    - held 24p/30p frames;
    - the same source shot (`shots_<pack>.json`);
    - the hero in the call graph (`HERO`), and the shared drawing helpers;
    - the Flash emblem;
    - library transitions (INFO);
    - cache determinism;
    - the sound events from `fx_events.json` (count, banned kinds, reverse swells, sounds on beat moments).
  - **Replaced by ours:** plain cuts, loop, repeats, zoom, overlapping clips, registry status, text.
  - **Ours that you didn't have:**
    - the owner's verdicts with tags and families;
    - look-alike clips (thumbnail structure and colour ≥ 0.75; it caught v107 rev 1's "same clip at 17/19 s", which were different frames of the same smiling close-up);
    - spins and dives landing on a tracked face;
    - the loop as a set piece (a `tout` on the last shot or a `tin` on the first);
    - a signature graphic transition;
    - density and generic share;
    - an even spell-out grid;
    - holds with no beat hit;
    - `PLAN_ACCEPT` / `--edl` / `--json`.
  - **Two calibrations against approved edits:**
    - "no plain cuts" passes a cut on a beat hit with the camera's punch (v107's approved 2.75 s cut) and WARNs off the beat;
    - banned sound kinds are a WARN, not a FAIL (the approved v107 has one swirl on its headspin, the approved v106 three).
  - **Results:** the approved v107, v12, v13 and v106 → 0 FAIL. v107 rev 1 → 4 FAIL (the owner's later notes). v13 rev 1 → 1 FAIL (the singularity in 11 transitions).
- **One registry,** `studio/transitions.json`:
  - your generated fields (pre/post, fn, engines, used_in, verdicts per edit, status) plus our curated fields (verdict, tags, evidence, fix, family, studio);
  - `preflight.py registry` now keeps the curated fields across rebuilds and also reads the v106 and v107 engines and the Dexter edits (v101–v107): 208 transitions, 73 owner verdicts, none lost on a rebuild;
  - your `KNOWN` statuses were carried over (`bolt_trace` → tag `leaks`; `emblem_horizon` → rejected);
  - we corrected our own `tv_off` from "rejected" to "caution", because the owner never judged it;
  - **from now on, add a verdict to the JSON** (verdict, tags, evidence, fix), not to `KNOWN`.
- **`build.sh`:**
  - `song:` (yours) and `plan` (the gate: `video` stops on a FAIL; `PLAN_FORCE=1` overrides);
  - `prep` (the plan check as a report, plus your background `sr_prep`);
  - `qc` (yours: four passes in parallel, then the review pack);
  - `signoff` / `report` / `splice` (ours), and auto-splice of an edited `fxN.py` before any rendering step;
  - `rev` = audio → plan → video → qc → signoff → report; `ship` = rev + deliver.

## Tested on the Dexter engine (v107), as you asked
- **Your determinism check found a real one in v107:** `ht_grid()` (the halftone screen) was keyed on `round(pitch, 2)` but filled from the exact pitch. Fixed: the grid is now computed from the key.
  - The re-render differs from the delivered encode only in a fine halftone/screen pattern on the front page and the shots after it: mean 0.6–2.1 grey levels a row, no change in structure.
  - Its order-dependence is gone.
  - We refined the detector: it now flags a cache only when the fill uses an argument the key **rounds** (`ang`, unrounded in the key, is fine).
- **`banner_match`** has no TR2 entry (the stamp's flight lands on the banner shot), so the registry marks it `set_piece` and the transition check skips it.
- **Change-tracked partial render on v107:** one constant edited in `page_turn107` → change tracking named that one function → 26 frames (212–237).
  - Rendered in 19 s, 35 frames verified bit-exact; 127 s in all against 272 s for a full render.
  - **Revert → identical to the full render** (max difference 0 on the review page).
- **`fx_events.json` logging ported to `audio107.py`** (the Dexter scaffold): the mix and stems are md5-identical, and 34 placed effects are logged.

## Proposed next split (unchanged from our handoff)
- **Flash studio:**
  - render speed (the x264 re-encode is now most of a revision render);
  - the Flash verdicts in the registry JSON;
  - motionqc labelling an impact transition's designed negative frame as a flash.
- **Dexter studio:** WP5, a shared source library.
- **Both:**
  - one toolchain on `dev/pipeline-v2`;
  - a verdict goes into `studio/transitions.json` the turn the owner gives it;
  - `studio/OWNER_RULES.md` stays the one-page rule list.
