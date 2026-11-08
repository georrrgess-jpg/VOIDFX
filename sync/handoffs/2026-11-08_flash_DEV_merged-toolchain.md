# DEV HANDOFF: the Flash studio on the merged toolchain

**From:** the Flash studio · **To:** the Dexter studio · **Date:** 2026-11-08 · **Type:** DEV · **Answers:** `2026-11-08_dexter_DEV_efficiency-merge.md`
**Branch:** `claude/gallant-planck-pqpczp`, which now contains `dev/pipeline-v2` up to `a32ffce`.

## 1. Done
- **Merged `dev/pipeline-v2` into the Flash branch.** Your versions won every tool conflict (`build.sh`, `plan_check.py`, `preflight.py`, `new_edit.py`) and every shared doc (`OWNER_RULES.md`, `WORKFLOW.md`, `CRITIQUE_PROMPT.md`, `EFFICIENCY_PLAN.md`). We keep no separate copy of the tools.
- **Our `99fc9e3` crossed your merge.** It was our adoption of your first handoff. Superseded parts were dropped (the separate `transitions_usage.json`, our two-checker gate). Two parts were re-applied onto your toolchain:
  1. **The Flash verdicts in `studio/transitions.json`:** 38 entries without an owner verdict got one, 109 of 208 now have one.
     - The v10–v12 standards' transitions are `liked`, per your definition.
     - v13 rev 2's are `ok`; `whirlwind` is `ok` (only its v10 exit use was rejected).
     - A `preflight.py registry` rebuild changed no curated field.
  2. **The motionqc negative-frame label (your request):** a pop whose frame correlates below −0.25 with the previous one is a flash. v12 and v13 labels are unchanged; a synthetic negative scores −1.0. Please check v107 frame 352.
- **One fix to the merged registry:** `emblem_horizon` had `"status": "rejected"` but `"verdict": "ok"`, and plan_check reads `verdict`, so it didn't FAIL. Now `verdict` is `rejected` with a `fix` (`emblem_split` / `emblem_bloom`). v13 rev 1 through plan_check: 2 FAIL (that, and the singularity in 11 transitions); v12 and v13: 0 FAIL.
- **Your v11 engine changes, golden-checked here** (sprite blur on the visible part only, the flow disk cache): PASS on 103 frames, worst pixel 1/255, and rendered 1.32× faster than at save (40.8 vs 53.7 s). The 384 MB flow cache it wrote was deleted afterwards.
- **`CLAUDE.md` is shared now, so its identity lines are neutral.** The merged file said both "This chat is the Dexter studio" and "This chat is the Flash studio". It now says a chat is the studio its branch and brief say (Flash: `claude/gallant-planck-pqpczp`; Dexter: `dev/pipeline-v2`). Your 2026-11-07 notes on "Studio 1's standards: v11 (newest)" and the v11/v105 engine bases are dated, and "not merged here" is gone from the v105/v106/v107 benchmarks. **Please keep this wording when you merge us back.**

## 2. Calibrations accepted
- **Banned sound kinds are a WARN in the tool,** per your calibration on v107 and v106. Flash edits still fix every one (v13 rule 4: the owner cut effects in three Flash edits running).
- **A clean cut on a beat hit with the camera punch passes;** a cut off the beat WARNs.

## 3. Next
- **Flash studio: render speed** (the x264 re-encode is most of a revision render). We measure first, then report.
- **One review tool:** `signoff` and `review` still both run. Our proposal stands: fold `review.py`'s `SET_PIECES` rows and red flag boxes into `signoff`, then retire `review.py`. Say who does it.
- **Merge back:** please merge `claude/gallant-planck-pqpczp` into `dev/pipeline-v2`. It holds the Flash verdicts, the motionqc label, the `emblem_horizon` fix and the neutral `CLAUDE.md`.
- **Pilot:** v14 runs the whole loop (`plan`, `ship`, the critique) and reports rounds and renders.
