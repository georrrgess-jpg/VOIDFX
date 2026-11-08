# voidfx two-studio sync (Flash studio side)

Two voidfx chats work as a coalition, and each learns from the other's edits:
- **the Flash studio** (this chat, Studio 1): every Flash edit, numbered v13 onward (v5, v10, v11, v12 were Flash);
- **the Dexter studio** (the other chat, Studio 2): every Dexter edit, numbered v107 onward (FOREVER and v105 DRACULA so far; v106 WONDERWALL was a one-off Flash edit made there at the owner's request).

After every verdict, the studio that made the edit writes a **handoff**: one self-contained markdown file in the shared format (`HANDOFF_TEMPLATE.md`, the same in both studios). The owner sends it to the other chat, which adopts the lessons.

## The loop (Flash studio)

1. **Brief.** The owner sends the song and, optionally, scene packs (`studio/START_PROMPT.md` or free-form).
2. **Build.** Pre-build gate, render, QC, visual sign-off, delivery.
3. **Review.** Each revision applies every note in one pass with one render and one checkpoint.
4. **Verdict.** "good / make it a standard" (record the standard, move the Flash scaffold to it, turn any gripes into rules) or "bad, because…" (record it as rejected, turn the reasons into rules or bans). A lasting lesson given mid-revision goes into the next handoff's rules.
5. **Handoff, in the same turn as the verdict:**
   - write `sync/handoffs/YYYY-MM-DD_flash_vNN_TITLE_<standard|rejected>.md` from `HANDOFF_TEMPLATE.md`;
   - add the new rules to `CLAUDE.md`, the handbook and `studio/preferences.json`; add the edit to the edit history (`studio/STUDIO_HANDOFF.md` §5);
   - add a line to `LEDGER.md`;
   - commit, push, and send the owner the handoff file.
6. **Send.** The owner gives the file to the Dexter studio with the message in `RECEIVE_PROMPT.md` (B).
7. **Receive.** When the owner attaches a handoff from the Dexter studio here:
   - file it in `sync/handoffs/` and the ledger;
   - adopt its rules (section 7) into `CLAUDE.md`, the handbook and `studio/preferences.json`, with their evidence, noting which apply to Flash edits; if one conflicts, keep both and tell the owner;
   - record the edit in the benchmarks and edit history; list its reusable assets (section 8) as port candidates in `docs/TOOLKIT.md`;
   - commit, push, and reply in a few lines: what was adopted, any conflicts, what the next Flash edit will try.

Handoffs are self-contained: the other chat must be able to act on one without this branch.

## Files

| File | Purpose |
|---|---|
| `README.md` | This workflow. |
| `HANDOFF_TEMPLATE.md` | The shared structure every handoff follows (identical in both studios). |
| `RECEIVE_PROMPT.md` | The messages the owner pastes with a handoff. |
| `LEDGER.md` | Every handoff sent and received, in order. |
| `handoffs/` | The handoff files. |
