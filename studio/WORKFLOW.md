# The fast loop (both studios, from 2026-11-08)

**Targets per edit:** owner rounds to approval ≤ 2 (was 3–4); full renders before the first delivery ≤ 2 (was 4);
one render per revision; studio time to a first delivery ≤ ~1.5 h, a revision ≤ ~30 min.
**Guardrail:** none of this changes a picture. The gates only stop a render that would repeat a note the owner already gave.

## A first delivery
1. **Brief → material.** `tools/song_map.py`, `tools/lyrics.py` (Whisper large-v3 on the vocal stem; beat map checked on
   the drum stem), packs, `tools/new_edit.py N SLUG "TITLE"` (Dexter → `--base v107`, Flash → `--base v12`).
2. **Design before code (15 min).** Read `studio/OWNER_RULES.md`. Write into the EDL:
   - the concept (one sentence from the song's words or the character's history) and the hero object;
   - the shot list (no clip twice; `tools/sharpness.py N --src`, zoom ≤ 1.10);
   - the transitions, chosen from `studio/transitions.json` (liked first; a different idea each; generic ones as filler);
   - `SIGNATURE = [...]` the one custom graphic that becomes a transition (~1 s); `HERO_TINS = [...]` (≤ 4);
   - the loop set piece; a sound budget of ~12 events.
3. `bash tools/build.sh N prep` and `nohup python3 tools/sr_prep.py N &` (restoration runs while you build).
4. `bash tools/build.sh N plan` until it shows **0 FAIL**; read every WARN and decide it (fix, or `PLAN_ACCEPT` with a reason).
5. **Build the custom pieces on warm stills, never on full renders:** `build.sh N sheet:NAME:f,f,...` (render server: 12
   frames in ~4 s once warm; an edited `fxN.py` is spliced in automatically), `strip:A:B` for motion, `clip:A:B` for sound.
   Check each new graphic at phone size and full size: faces, black, does it read, does it look filmed or drawn.
6. `bash tools/build.sh N ship` = audio → plan → video → qc (3 passes in parallel) → signoff → report → deliver.
7. **Review before sending** (10 min): the sign-off pages `vN/frames/signoff_*.jpg` and `faceqc.jpg`, every UNEXPLAINED
   pop, then the **fresh-eyes critique** (`studio/CRITIQUE_PROMPT.md`, one agent run). Fix every HIGH item, `ship` again
   (the second and last render).
8. **Deliver:** the MP4 (SendUserFile), a short message (what it is, what changed, what to watch for), the README's
   Measured section from `vN/work/measured.md`. Ask the owner to watch with sound.

## A revision
1. Record each note (`tools/metrics.py N note CAT "words"`), map it to one fix, and read `OWNER_RULES.md` §5:
   **a slot that failed twice gets a kinetic transition or a clean downbeat cut, not a third graphic concept.**
   Add every rejection to `studio/transitions.json` now (verdict, the owner's words, the fix).
2. Apply **all** notes in one pass → `plan` → stills of the changed moments → `ship` (one render; `video` re-renders only
   the changed shots when the change is local, verified bit-exact outside them).
3. Sign-off pages of what changed + the loop; the critique when a note was about taste, not a defect → deliver.

## At the verdict
Handoff (`sync/HANDOFF_TEMPLATE.md`), the registry verdicts, `data/edits.json` / `preferences.json` / ledger in the kit,
`python3 tools/vrender.py N clean`.

## Speed facts (v107, 4 cores)
| Step | Time |
|---|---|
| plan_check | 1–5 s |
| stills sheet through the render server | 12 frames in 4 s warm, 8 s from cold (v107's scratch stills script: 60–120 s a sheet) |
| full render, 1317 frames | ~4.6 min (partial re-render of one shot ~2–3 min) |
| qc (qc + faceqc + motionqc in parallel) | 72 s (was 103 s in sequence) |
| signoff pages | 6 s (pulling frames by hand: 5–10 min a round) |
| report (Measured block) | 1 s |
| master encode (background) | ~1 min |

## Time sinks seen in v106–v107 (don't)
- A full render to test one transition: use `sheet:` / `strip:`.
- A third graphic concept for a slot the owner rejected twice (v107's 3 s slot took four rounds).
- Re-inventing a rejected or banned piece (v107 rev 3 rebuilt the old `strings` gimmick): check the registry first.
- Hand-pulled frames and hand-typed numbers: `signoff`, `report`.
- Discovering after the render what `plan_check` reports before it (a reused clip, an off-centre landing, a slow spell-out).
