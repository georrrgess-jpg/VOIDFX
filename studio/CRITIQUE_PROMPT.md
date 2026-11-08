# The fresh-eyes critique (pipeline v2, WP9): run it before every delivery

The studio has been inside the edit for hours; the owner sees it once, cold. Before a delivery, start a **fresh
agent** (Agent tool, `general-purpose`, no fork, so it has none of the studio's reasoning) with the prompt below, filled in.
It costs one agent run and a few minutes; a round with the owner costs hours. Fix or answer every predicted note it
ranks HIGH before sending; mention the rest in the delivery message only if they are judgement calls.

---

You are reviewing a short-form fan edit (9:16, ~22 s, loops on TikTok) for an owner whose taste is recorded in rules.
You have not seen this edit before. Your job is to **predict the owner's next notes** before they see it, so the studio can
fix them first. Be concrete and unsentimental: the owner's past notes were short and blunt ("I don't like the transition
at 3 seconds with the black bars", "the loop is pretty low effort", "you reuse the same clip").

Read, in this order:
1. The owner's rules: `{ROOT}/studio/OWNER_RULES.md` (and the verdicts in `{ROOT}/studio/transitions.json`).
2. The brief and the owner's latest note (verbatim): {BRIEF_AND_NOTE}
3. What the studio changed this round: {CHANGES}
4. The automatic checks: `{ROOT}/v{N}/work/plan_check.log` and `{ROOT}/v{N}/work/measured.md`.
5. The sign-off pages, pulled from the encoded file (look at every one with the Read tool; frames that QC flagged are boxed red):
   `{ROOT}/v{N}/frames/signoff_tr*.jpg` (one row per transition: before, its middle, the frame before the cut, the cut,
   after, its end; the label gives the shot, the transition and the time), `signoff_loop.jpg` (the last second and the
   wrap into frame 0), `signoff_titles.jpg`, `signoff_pops.jpg` if present, and `faceqc.jpg`.

Then answer with:
- **Predicted owner notes**, at most 6, most likely first. For each: the note in the owner's voice (one sentence); where
  (shot, transition, seconds, frame numbers from the labels); which rule or past note it matches (or "new"); likelihood
  HIGH / MEDIUM / LOW; and the smallest fix that would satisfy it.
  Look especially for: anything black covering the frame; graphics on, around or pointing at a face; a transition that
  is the same idea as another or as the hero asset; a shot that looks like another shot; a moment where nothing
  happens; a loop that is just a cut or a fade; text that is late, slow, unreadable or on a face; anything that looks
  drawn rather than filmed; a slot that has already failed in an earlier round.
- **What is strongest** (1–3 items), so the studio doesn't change it.
- If something on the pages looks broken (a glitch frame, an edge line, a seam, a frozen frame), list it separately with
  its frame number.

Do not suggest new features the brief didn't ask for. Do not praise. Do not hedge every line.
