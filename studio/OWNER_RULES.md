# The owner's rules, on one page (both studios)

Read this **before designing** an edit and again **before delivering** one. It distils every owner note and verdict
(v4–v13, v101–v107) into the rules that are still in force; where two records conflict, the newer verdict wins and is the
one written here. Evidence and history: `CLAUDE.md`, `studio/VOIDFX_STUDIO.md`, the handoffs in `sync/handoffs/`.
Markers: **[plan]** checked on the EDL by `tools/plan_check.py` (both studios' checks, one report) before any render · **[qc]** measured on the encode by
`build.sh N qc` · **[eye]** judged on the sign-off sheets (`build.sh N signoff`) and by the fresh-eyes critique
(`studio/CRITIQUE_PROMPT.md`).

## 1. Never
- **Black occluders as transitions**: letterbox bars, redaction boxes, a screen floating in a dark room ("the black bars", "the black box transition", v107). **[plan]** registry tags
- **Graphics on or pointing at a face**: lines or strings converging on it, crosshairs, target rings, even when the face arrives a beat later (v107 rev 3 rebuilt the old `strings` gimmick and lost a round). Nothing crosses a face: lightning, particles, seams, wipe edges, suns go round the face box or behind the matte. **[plan] [qc] [eye]**
- **A transition the owner rejected**, unless the registry's `fix` is applied: see `studio/transitions.json` (press flash, broadcast TV, redact, rorschach, strings, glass shatter, knife pass, emblem horizon …). **[plan]**
- **The same clip twice**, or two shots that look the same (the same close-up from the same scene) (v107 rev 2). **[plan]**
- **Overlays parked on the frame**: glass webs, hanging shards, slides drifting as a constant layer. Transform the picture itself (v10, v103).
- **Drawn-looking props** next to footage: blood, slides, knives, tape only when motivated by the shot or lyric, brief, physically lit, off the face (v103). **[eye]**
- **Droplets on the lens or a wavy heat-haze warp as a transition** (v108 rev 2: *"remove the water droplet filter"*, *"the squiggle, swirl, weird animation"*). **[plan]** registry
- Outro / title cards, watermarks, labels, name tags, counters, timecodes, CJK lines; a recoloured logo. **[plan]** `logo_uv` banned
- A line shown as spoken when the lips don't match (v101); captions on words the song isn't singing (v103).
- Chimes, bells, shimmers, drones, swirls, whines, a swell on every move (v12, v106, v13). **[plan]** sound kinds (a WARN: v107 shipped one swirl)

## 2. Every first delivery already has (these were asked for again and again)
1. **One signature custom graphic that becomes a transition**: on screen as a graphic for about a second, then it carries the cut (v106 tear lens, v13 light ribbon, v107 front page → stamp → banner). Asked for in **4 of the last 4** edits. **[plan]** `signature`
2. **A loop that is the edit's most creative set piece** and lands exactly on frame 0's own picture, still moving across the wrap (v105, v106, v107 rev 2). **[plan] [qc]** seam ≤ 1
3. **Lean sound**: about 10–12 sound events in 20–23 s, layered only at the set pieces, small transitions silent, nothing on beat punches or letters; v107's 28 placed effects is the ceiling (cut in v12, v106, v13). **[plan]** > 16 warns, > 30 fails
4. **No headspace**: no span over ~1 s without a cut, a transition or a designed beat (v104, v106). **[plan]** estimate **[qc]** motionqc
5. **A concept from the song's own words or the character's history**, carried by one hero object through picture, text and loop; the hero is a **motif** (2–4 appearances), not every transition (v11, v13). **[plan]** families
6. **Physical, kinetic transitions** from the character's world (rip, pour, spin, zipper, page, eye dive, shutter, emblem/prop), each a different idea; generic moves (whip, slam, impact, dolly, smear) are filler between them. **About 24–26 designed transitions in ~22 s (≥ 1.1/s), nearly all custom** (v108 had 21 + the loop, 0.97/s, and the verdict still said *"could have contained slightly more transitions/animations"*). **[plan]** density, generic share, repeats v108 rev 1 asked again for *"a lot more transition and unique graphics with custom animated transitions … smooth transitions and creative ones so the edit flows"*: replace generic connectors with custom, smooth ones.
7. **Faces centred and whole**; spins and dives land on a centred, tracked face (v107). **[plan] [qc]**
8. **The motion pass**: speed ramps with clean flow on hook shots, the beat camera (punch, kick, blur), smooth sub-pixel motion, no judder (v10, v106). **[qc]** judder
   - *v108 exception (not a new rule):* the owner turned the beat camera off for DOOMSDAY (*"I generally like when on the beat the clip … jumps up and down with the beat, but in this edit I would like for you to remove that just for this edit"*): a slow, menacing edit may flow better without the punch. Keep it the default.
9. **Restored, sharp sources**: `sr_prep`, zoom ≤ 1.10 on 720p, no SOFT shot on a hero moment (v105). **[plan]** zoom **[qc]** sharpness
10. **A smooth ending**: the beat camera rests through the break, fewer and longer cuts (v107).

11. **The owner's concept boards are built from the shot's own props**: lift, tilt or move the real object (v108: the real slide pivots up in his fingers) rather than a CG copy beside it (*"merge that slide graphic … with one of the actual slides from that scene"*). Board choices (text, timing) apply to that edit only; ask when the rest is left open.

## 3. Text
- Dexter: every clearly sung line captioned word by word on its sung onset, in the v9 style (heavy caps, keyline, red emphasis, eased in). Flash: text is optional and titles must earn their place (v12 removed both).
- At most two designed titles. A spell-out runs on an even rhythm grid (~10 frames a letter at ~90 BPM), each letter landing on its hit with its sound (v107). **[plan]**
- Text in the 1240–1640 band, never on a face. **[qc]**

## 4. Sound and finish
- −13 LUFS, true peak ≤ −2.5 dBTP after AAC; no clicks at cuts or the wrap; audio = video length on the container. **[qc]**
- Effects measured against the music: +9–10 dB on a loud master, the music ducked ~3 dB under the biggest hits (v105). `mixcheck`
- Flashes: peak mean luma ≤ ~110, no white-outs, ≤ 3 a second. **[qc]**

## 5. Revisions
- Apply **every** note in one pass, then `plan_check`, stills, one render, `ship`.
- **A slot that has failed twice gets no new graphic concept**: a kinetic physical transition or a clean cut on the downbeat with the beat camera's punch (v107: press flash → TV → point of origin, then the clean cut was approved).
- When the owner removes or dislikes something, add the verdict to `studio/transitions.json` in the same turn, so neither studio repeats it.
- "Lacklustre" means motion and polish, not more overlays (v10). "Add transitions/graphics" means new cuts with themed transitions, not effects stacked on shots (v105).
