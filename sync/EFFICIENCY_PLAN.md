# Efficiency and quality update (both studios), 2026-11-08

**From:** the Dexter studio (it leads `dev/pipeline-v2`, per `sync/PIPELINE_V2_PLAN.md` §6) · **For:** the owner and the
Flash studio (the owner sent the same request to both studios).

> *"I would like for you to plan and complete an update on which you improve the efficiency at which edits are produced.
> I do not want the quality of the edits to be diminished or effected at all and if anything the quality should be
> improved. Currently the editing process is functional and after 3 or so revisions I'm able to wield a relatively good
> product. But this process takes too long whether that be the revisions or the initial creation process."*

## 1. Where the time goes (measured, v12 · v13 · v106 · v107)

| Edit | Rounds | Full renders | Round 1 (logged build span) | Owner notes |
|---|---|---|---|---|
| v12 BLOOM | 3 | 6 | 77 min | 5 |
| v13 EVENT HORIZON | 2 | 6 | 77 min | 6 |
| v106 WONDERWALL | 3 | 6 | 101 min | 5 |
| v107 ALL CAPS | 4 | 9 | 107 min | 10 |

The logged span counts only the build commands. The design, the code, and pulling and reading stills come on top.

**Finding 1: the owner rounds are the cost, and most of their notes were predictable.**
- **Repeated across edits:**
  - "remove the tedious sound effects" (3 of 4 edits);
  - "one more really cool custom graphic into a transition" (4 of 4);
  - the loop (2);
  - smoothness (3);
  - dead space (1);
  - a transition the owner didn't like (7 notes).
- **Already in the rules:** several v107 notes broke a rule that was on file before the round. Rev 3 rebuilt the old `strings` gimmick ("lines converging on his face with a target ring", banned years ago), and it cost a round.
- **Why that happened:** the rules were spread over a ~500-line CLAUDE.md with repeats and outdated lines ("every transition gets its own sound", "≥ 24 transitions per 24 s"), and nothing checked an edit against them before a render.

**Finding 2: round 1 needed four full renders, because problems surfaced only after rendering.**
Examples: a reused clip, an off-centre spin landing, the AAC seam click, text over faces, judder.

**Finding 3: the review between renders was manual.**
- Stills came from a scratch script that reloaded the engine (60–120 s a sheet).
- Frames were pulled from the encode by hand, and the Measured numbers were typed by hand.
- QC ran its three passes one after another.

## 2. What changed (done, on `dev/pipeline-v2`)

| Piece | What it does | Effect |
|---|---|---|
| `studio/OWNER_RULES.md` | Every rule still in force on one page, conflicts resolved to the newest verdict, each marked by what enforces it (plan / qc / eye) | Read before designing and before delivering; replaces digging through 500 lines |
| `studio/transitions.json` | The owner's verdict on 73 transitions (liked / ok / rejected / banned), with his words, the fix, tags (black occluder, face gimmick, generic, signature, lands on a face) and hero families | Proven pieces get picked first, and rejected ones can't come back unnoticed |
| `tools/plan_check.py` (WP7) | Runs on the EDL before any render and checks the owner's recurring notes:<br>· rejected or banned transitions and black occluders;<br>· the same clip twice, **or two shots that look the same** (a thumbnail comparison);<br>· spins landing without a centred face;<br>· the loop is a set piece;<br>· a signature graphic transition;<br>· the hero used as a motif (≤ 4);<br>· density, generic share and repeats;<br>· zoom;<br>· an even spell-out grid;<br>· titles;<br>· holds with no beat;<br>· the sound budget (counted on the effects stem) | `build.sh video` stops on a FAIL. Calibrated so the approved v107, v12, v13 and v106 pass (0 FAIL) |
| `tools/signoff.py` | Review pages from the **encoded** file in one decode: every transition as one row (before → cut → end), the loop wrap, every text block, every unexplained pop | 6 s, instead of 5–10 minutes of pulling frames each round |
| `tools/report.py` | The Measured block (QC, loudness, seam, flashes, faces, motion audit, sharpness, plan_check, effort) → `vN/work/measured.md` | 1 s; the README and handoff numbers are measured, not retyped |
| `studio/CRITIQUE_PROMPT.md` (WP9) | A fresh agent with none of the studio's reasoning predicts the owner's next notes from the rules and the sign-off pages | One agent run before each delivery; see §3 for the test |
| `build.sh` | `ship` = audio → plan → video → qc → signoff → report → deliver. Also: `plan`, `signoff`, `report`, `splice`; an edited `fxN.py` is re-spliced automatically before anything renders; the three QC passes run in parallel | One command per revision; QC 103 → 72 s; no stale-code stills |
| `studio/WORKFLOW.md` | The fast loop for a first delivery and a revision, with time budgets and the time sinks seen in v106–v107 | |
| `qc107.py` | The container-duration fix from v13 | |

**Guardrail kept:** nothing in this update changes how a frame is rendered; the engines are untouched, so the golden frames are unaffected. The gates only stop a render that would repeat a note the owner already gave, and a WARN never stops anything.

## 3. Acceptance tests

**plan_check on the first deliveries, with today's rules.** Every catch below cost the owner a round when it happened.

| First delivery | What plan_check reports | What the owner later said |
|---|---|---|
| v107 rev 1 | FAIL `press_flash`, FAIL `redact` (both rejected since); FAIL `laugh` and `hero` look like the same clip (structure 0.86, colour 0.91); FAIL `headspin` lands on a shot with no tracked face; WARN the DEXTER spell-out is uneven (14.9 frames a letter, 19 % spread) | rev 2: the 3 s transition, the reused clip at 17/19 s, the spin's landing not centred; rev 3: the name written too slowly; rev 4: the black box |
| v107 rev 2 / rev 3 | FAIL `broadcast` / FAIL `rorschach` | rev 3: "the black bars"; rev 4: "get rid of the point of origin" |
| v13 rev 1 | FAIL the singularity carries 11 transitions | rev 2: "the singularity is the primary object in every transition" |
| v107, v12, v13, v106 as approved | 0 FAIL (WARNs point at long holds and sound counts) | approved |

**The critique on v107 rev 3,** given only the rules on file before that round (the banned list already named "target rings, converging strings") and that round's encoded frames:
- **Its #1 prediction (HIGH):** *"Get rid of the target and the red lines pointing at his face"*, citing the banned rule. The owner's actual next note was *"Can you get rid of the point of origin graphic/transition"*. That round would have been saved.
- **Also flagged (MEDIUM):** black left at the 3 s transition, the same family as the owner's *"black box transition"* note that round.
- **Other predictions:** it also predicted the mirrored face reading as uncanny and the blood reading as drawn; the owner didn't comment on either.
- **Not every flag was right:** two of its "broken frame" items were not defects (the stamp's designed descending letter, and a dark object that is in the source shot). So the workflow keeps the rule: **verify every critique claim on frames before acting on it.**

## 4. Split with the Flash studio (the same request went to both)

Adopt the above: the tools are shared and work on Flash EDLs (tested on v12, v13 and v106). To avoid building the same thing twice, the Dexter studio proposes:

- **Flash studio:**
  - **render speed** (WP2 remainder: profile the hot paths of the v12 engine; target ≤ 3 min a full render with golden frames unchanged; they wrote the speed section);
  - **Flash verdicts in `studio/transitions.json`** (bolt pieces, v10–v11 transitions, the families of the v10/v11 hero assets);
  - **motionqc labels** (an impact transition's designed negative frame still reads as UNEXPLAINED, e.g. v107 frame 352);
  - **pilot the loop** on v14.
- **Dexter studio:**
  - `plan_check`, `signoff`, `report`, the critique, the registry format, `OWNER_RULES.md`;
  - next: a shared source library (WP5: restoration and mattes reused across edits);
  - pilot the loop on the next Dexter edit.
- **Both:**
  - add every owner rejection to `transitions.json` in the turn it happens;
  - keep `OWNER_RULES.md` current at every verdict (it is the short form; the handbooks keep the history).

## 5. Results to watch (metrics.json records them for every edit)

- **Owner rounds to approval:** target ≤ 2 (was 3–4).
- **Full renders before the first delivery:** target ≤ 2 (was 4).
- **Renders per revision:** target 1.
- **plan_check FAILs at the first `ship`:** target 0.
- **Critique predictions that match the owner's actual notes:** recorded in each edit's handoff (the v107 rev 3 test: 1 of 1 HIGH predictions matched).

## 6. Merged with the Flash studio's update (2026-11-08)

The Flash studio answered the same request in parallel (`sync/handoffs/2026-11-08_flash_DEV_efficiency.md`). Their branch is merged into `dev/pipeline-v2` (`34a20d1`), and the two halves are one toolchain (`sync/handoffs/2026-11-08_dexter_DEV_efficiency-merge.md`).

**Added from their side:**
- **Change-tracked partial renders** (`tools/codetrack.py` in `vrender.py`): only the frames that ran edited code are re-rendered, verified bit-exact outside.
- **`song_prep.py`** (`build.sh N song:`): song prep in one command.
- **The review pack** (`review.py`, at the end of `qc`).
- **`fx_events.json` sound-event logging.**
- **Preflight's checks** inside the one plan report: the TR2 call graph, the emblem, source shots, cache determinism and sound kinds.

**Measured on v107 (the Dexter engine):**

| Step | Before | After |
|---|---|---|
| One transition edited, then re-rendered | full render, 272 s | **127 s** (26 frames found and drawn in 19 s; the rest is the full-video re-encode); edit + revert identical to the full render |
| An audio-only change | full render | nothing re-rendered |
| Plan check (both studios' checks) | — | 6–20 s |

**Found on the way:**
- **v107 `ht_grid()`:** it filled its cache from the exact pitch under a rounded key, so the pixels depended on render order. Fixed; the re-render differs only in a fine screen pattern, with no change in structure.
- **`tv_off`:** our registry had it as "rejected", but the owner never judged it. It is now "caution".
