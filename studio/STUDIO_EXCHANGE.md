# The two-studio exchange

Two voidfx chats work in coalition and learn at the same pace. Each studio makes its own edits; when the owner gives a verdict on an edit, that studio writes an **edit report** and the owner pastes it into the other chat. The receiving studio folds the lessons into its own rules.

## Roles

| Studio | Chat | Makes | Version range | Branch |
|---|---|---|---|---|
| **Studio 1: the Flash studio** | this chat | The Flash edits (songs and packs supplied by the owner) | `v12`, `v13` … (v5, v10, v11 were Flash) | `claude/gallant-planck-pqpczp` |
| **Studio 2** | the other chat | its own edits (Dexter so far: FOREVER, DRACULA) | `v101+` | its own branch |

## When a report is written

A report is written **only on a verdict**:
- **Approved** ("this edit is good", "make it a standard"): the report says what made it good, and the studio marks the edit as a standard in its own `CLAUDE.md` and handbook.
- **Rejected** ("this is bad because…"): the report says what made it bad, the owner's reasons, and the rule that stops it happening again.

Revisions in between stay inside the studio; the report covers the whole journey (every revision's note and what changed), so nothing is lost.

## The report (`studio/reports/vN_TITLE.md`)

Use `studio/reports/TEMPLATE.md`. It must stand alone, because the other chat may not have this branch:
1. **Verdict** with the owner's words.
2. **The edit:** show, song and section, concept, look, length.
3. **Creative process:** how the concept was found, the plan, the set pieces, the type, the sound, the loop.
4. **Revision history:** each owner note quoted, what changed, and why.
5. **What made it good** (or bad): specific, with evidence.
6. **What fell short / was fixed by review:** the defects caught and how.
7. **Rules to adopt:** numbered lines, written so the other studio can paste them into its `CLAUDE.md` and handbook as is. Mark each one *new*, *changed* or *confirmed*.
8. **Techniques to reuse:** each with enough detail to rebuild it without this branch's code (inputs, stages, timings, sound), plus the function name if the other studio can merge the code.
9. **Measured numbers:** loudness, true peak, loop seam, cut count, sharpness flags.

Each report is committed under `studio/reports/` and sent to the owner as a file.

## Receiving a report from the other studio

When the owner pastes a report from the other chat here:
1. Add its rules to `CLAUDE.md` and the handbook (`studio/VOIDFX_STUDIO.md`): likes and rejections into §3/§4, gate items into §5a, benchmark rows into §1 if it was approved as a standard.
2. Add its techniques to `docs/TOOLKIT.md` (catalogue rows, pitfalls).
3. If a rule conflicts with an existing one, the newer owner verdict wins; record what it replaces.
4. Commit and push, and confirm to the owner in one short list what changed.

Where the two studios disagree on shared things (the scaffold base, a tool with the same name), the owner decides; record the decision in both chats.

## The owner's side

1. Brief this studio with a song (and packs if any) using `studio/START_PROMPT.md`.
2. Review, give notes, repeat.
3. Say "good / make it a standard" or "bad, because…".
4. Forward the report file this studio sends to the other chat, with a line like *"Report from the Flash studio: apply it."*
