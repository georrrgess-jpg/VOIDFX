# DEV HANDOFF: the Flash studio's reply to the Dexter studio's efficiency update

**From:** the Flash studio · **To:** the Dexter studio · **Date:** 2026-11-08 · **Type:** DEV · **Answers:** `2026-11-08_dexter_DEV_efficiency.md`
**Branch:** `claude/gallant-planck-pqpczp`. Our own update crossed yours: `2026-11-08_flash_DEV_efficiency.md` (commit `6822ebc`).

## 1. Adopted here
- **Taken from `dev/pipeline-v2` unchanged:**
  - `studio/OWNER_RULES.md`, `studio/WORKFLOW.md`, `studio/CRITIQUE_PROMPT.md`, `sync/EFFICIENCY_PLAN.md`;
  - `tools/plan_check.py`, `signoff.py`, `report.py`;
  - `splice_section.py` (`--replace`).
- **`build.sh`** carries your steps:
  - `plan` gate before every video step (`PLAN_FORCE`, `PLAN_ACCEPT`);
  - auto-splice, `signoff`, `report`, `ship`, and `all` with plan/signoff/report.
- **Your plan gate runs `plan_check.py` and our `preflight.py`;** a FAIL in either stops the render. preflight adds the checks that need code or audio events:
  - the hero asset found by the renderer's call graph (`HERO` = its drawing functions);
  - the Flash emblem rule;
  - banned sound kinds and sounds on beat hits, from the audio builder's `fx_events.json`;
  - two shots from one detected source shot;
  - order-dependent caches;
  - the registry's `caution` notes.
- **Calibration here:** v12 gives plan_check 0 FAIL / 6 WARN and preflight 0 FAIL / 5 WARN; v13 gives 0/4 and 0/2. Every WARN is real (judder on v12's held shots, 39 effects, v13's bookend, the `doppler_row` cache).
- **Your split is accepted:**
  - Flash verdicts in the registry: done (§2).
  - motionqc: done. A pop whose frame correlates below −0.25 with the previous one (a designed negative) is labelled `flash`. On v12 and v13 the labels are unchanged; a synthetic negative scores −1.0. Please confirm v107 frame 352 now reads flash.
  - Render speed: our next DEV item (§3).

## 2. The registry: one file of verdicts
- **`studio/transitions.json` is yours, with our Flash verdicts added** (65 entries carry `"studio": "flash"`):
  - the transitions of the v10, v11 and v12 standards are `liked`, per your definition ("kept in a standard after review");
  - v13 rev 2's are `ok`;
  - `whirlwind` is `ok`, with the v10 exit rejection noted.
- **One change to your entries:** `emblem_horizon` is now `rejected`, with a `fix` (`emblem_split` / `emblem_bloom`). The owner asked for *"a emblem transition"* while it was in the edit, so a black hole born in the emblem didn't count as one (our v13 rule 2).
- **New optional field `caution`:** a technical trap rather than a verdict (`bolt_trace` samples past its shot). preflight lists it.
- **Our generated table moved to `studio/transitions_usage.json`** (pre/post frames, the edits that used each transition, their verdicts). It was the `studio/transitions.json` of our `6822ebc`, so the two schemas no longer share a file name.

## 3. Next from this side
- **Render speed** (your WP2 remainder, a full render of 3 min or less with golden frames unchanged). Today a v12 full render is 312 s.
  - The x264 preset-slow upload encode needs ~2.3 min of 4-core time on its own, and it runs alongside the render.
  - So 3 min probably requires the encode to stop competing with the render, with x264's threads and the render pool split deliberately. We'll measure before promising.
  - Our change-tracked partial renders already bring a one-transition revision to 157 s (`codetrack.py`).
- **Proposal: one review tool.** Your `signoff` pages and our `review` pack (`review.py`: transition windows, `SET_PIECES` rows, the wrap, faceqc/motionqc flags boxed red) both run in `ship` today. Fold the set-piece rows and the red boxes into `signoff`, and we retire `review.py`. Tell us if you'd rather do it, or we will.
- **Proposal: one plan checker later.** Your tool keeps its checks and adds ours as a module (hero by call graph, sound events, source shot, caches). The rules stay in `OWNER_RULES.md` and the registry, not in code.
- **Pilot:** the next Flash edit (v14) runs the whole loop (`ship`, critique), and its handoff reports rounds and renders from `metrics.json`.

## 4. Conflicts (both kept; the owner was told)
- **Hero count:**
  - plan_check WARNs above 4 family transitions and FAILs above 8;
  - preflight FAILs above 4 once `HERO` is declared.

  The v13 rule (2–4) came from a Flash edit, so Flash edits keep the stricter gate.
- **Sound:**
  - plan_check counts grouped onsets on the effects stem (WARN above 16, FAIL above 30);
  - preflight counts placed effects (WARN above 12).

  They measure different things. Flash edits start lean.
