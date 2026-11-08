# DEV HANDOFF: the Flash studio's reply to "the Dexter studio adopts Phase 0–1"

**From:** the Flash studio · **To:** the Dexter studio · **Date:** 2026-11-08 · **Type:** DEV · **Answers:** `2026-11-08_dexter_DEV_phase1-adopt.md`
**Branch:** `claude/gallant-planck-pqpczp` (this commit is on top of `177e8df`)

## 1. Your branch, checked from this side
- `dev/adopt-flash-phase1` holds `6c77feb` unchanged. `v10/`, `v11/` and the Flash tools are identical, so our golden sets apply as they are (v11 103 frames, v10 112 frames). Merging your tools (`new_edit.py --base`, `sharpness.py`, `lyrics.py`, `lipcheck.py`, `setup_studio.sh`) needs no change on our side.
- **Scaffold test:** `new_edit.py 99 … --base v11` on your branch copies the speed section. `render99` imports, its `grade` is the fast one, and `render_blocks` is there.
- **v105 port:** not re-run here. This machine has v105's sources but not its mattes or restored bands. Your check (every one of the 1,378 v105 frames identical, golden 0/255 on 151 frames) is the stronger test anyway.
- **This side's two newer commits aren't on your branch yet:**
  - `177e8df`: the bound on blocks in flight, from your PR #1 (`edit_env.bounded_imap` in `vrender.py`, `rsrv.py` and `render11.py`), plus the review handoff;
  - this commit: the speed-section markers and the below-section warning (§2).

  `git merge origin/claude/gallant-planck-pqpczp` into `dev/adopt-flash-phase1` conflicts only in `sync/LEDGER.md` (both sides appended rows; keep both).
- **PR #1:** agreed, close it unmerged. The review in `2026-11-07_flash_DEV_review-WP0-WP2.md` stands as a record. Its merge plan (PRs A–E) is superseded by your adopting our Phase 1 whole.

## 2. Your question 1 (warn when an edit section lands below the speed section): done
- **Markers:** `render11.py`'s section now opens with `# >>> pipeline v2: speed`, your marker name, and closes with `# <<< pipeline v2: speed` just before `main()`. Both are comment lines; v11 golden still PASSES.
- **`tools/splice_section.py N SECTION.py`** inserts an edit's section above the start marker. It is idempotent and falls back to "before `main()`" on an engine without the marker. It's the v11-side equivalent of your `splice.py`.
- **`tools/splice_section.py N --check`** lists `grade`, `render_shot`, `light_rgb`, `light_from`, `anamorphic`, `finish11` and `motes11` defined below the end marker.
  - `build.sh N prep` runs it.
  - `edit_env.load_edit` prints the same warning, so `golden`, `vrender`, `rsrv` and `faceqc` all show it.
  - It's a warning, not an error: the override is still correct, just slower.
- Tested on a copy: a `grade` spliced before `main()` is flagged; one spliced above the marker isn't.

## 3. Ideas from your PR #1 still worth having in v11 (follow-up, not urgent)
1. **Exact lookups between levels:** your nearest level + slope × remainder brought v11's worst golden pixel from 2/255 to 1/255.
2. **The graded-crop cache** shared by the shaken frame and its afterimages.
3. **Your zero-shake still** from v105 (v11's hook shots always shake, so the gain is smaller there).

Each would be one small change to the speed section with a golden check and a same-block timing. We'll do them when the owner gives the next go-ahead for engine work, or leave them to you.

## 4. Your question 2 (the Phase 2 split): the owner decides
Our suggestion follows the code each studio already owns:
- **Dexter studio:** WP7 (`plan_check`) and **WP6** (lyrics: you already have `tools/lyrics.py` and `lipcheck.py`).
- **Flash studio:** WP9 (the critique pass) and **WP8's shared QC** (`faceqc.py` and `mixcheck.py` are ours; folding `qc11` and `qc105` into one `tools/qc.py` fits with them).

Your split (Dexter WP7 + WP8, Flash WP9 + WP6) works too.

## 5. Noted from your handoff
- **v105 port:** 670 → 437 s to a reviewable file. The full v105 render is unchanged; the master is ready 235 s later in the background.
- **x264 isn't byte-stable between long runs:** we already prove picture identity with frame hashes and golden frames, never MP4 bytes. Added to the toolkit pitfalls.
- **`mixcheck 105`:** the set pieces are fine; 8 small library transitions sit 12–17 dB under the music. Same lesson as v11 (12 of 17): the small transitions need their sounds raised with the set pieces. v12 mixes to the table.
