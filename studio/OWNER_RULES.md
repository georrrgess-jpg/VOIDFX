# The owner's rules, on one page (both studios)

Read this **before designing** an edit and again **before delivering** one. It distils every owner note and verdict
(v4–v15, v101–v111) into the rules that are still in force; where two records conflict, the newer verdict wins and is the
one written here. Evidence and history: `CLAUDE.md`, `studio/VOIDFX_STUDIO.md`, the handoffs in `sync/handoffs/`.
Markers: **[plan]** checked on the EDL by `tools/plan_check.py` (both studios' checks, one report) before any render · **[qc]** measured on the encode by
`build.sh N qc` · **[eye]** judged on the sign-off sheets (`build.sh N signoff`) and by the fresh-eyes critique
(`studio/CRITIQUE_PROMPT.md`).

## 1. Never
- **Black occluders as transitions**: letterbox bars, redaction boxes, a screen floating in a dark room ("the black bars", "the black box transition", v107). **[plan]** registry tags
- **A symbol drawn in the wrong shape, or a cut-off subject mirrored** (`BORDER_REFLECT` on a push mirrored the S1 emblem into a chevron, v14 rev 1): trace the real shape on the source first. **[eye]**
- **Faces or memories upside down inside a graphic**, even when the optics would invert them (v14 round 3: *"face upright so that Barry's face is facing upwards"*). **[eye]**
- **Graphics on or pointing at a face**: lines or strings converging on it, crosshairs, target rings, even when the face arrives a beat later (v107 rev 3 rebuilt the old `strings` gimmick and lost a round). Nothing crosses a face: lightning, particles, seams, wipe edges, suns go round the face box or behind the matte. **[plan] [qc] [eye]**
- **A transition the owner rejected**, unless the registry's `fix` is applied: see `studio/transitions.json` (press flash, broadcast TV, redact, rorschach, strings, glass shatter, knife pass, emblem horizon …). **[plan]**
- **The same clip twice**, or two shots that look the same (the same close-up from the same scene) (v107 rev 2). **[plan]**
- **Overlays parked on the frame**: glass webs, hanging shards, slides drifting as a constant layer. Transform the picture itself (v10, v103).
- **Drawn-looking props** next to footage: blood, slides, knives, tape only when motivated by the shot or lyric, brief, physically lit, off the face (v103). **[eye]**
- **A face taken apart**: a particle dissolve of a face, fire holes in a face, a scorch line or particles across it (v15 round 3: *"where [Barry] kind of like breaks down into many pieces ... change that"*; `time_particles` is now `caution`). A burn or cover passes a face as one soft edge. **[eye]**
  - *Conflict kept (both 2026-11-09):* v109 PHANTOM was approved as a standard with its loop dissolving him into dust, face last (the gust is the concept: the phantom leaves) and `time_particles` on the PHANTOM title. Read together: no face break-up as a mid-edit transition; a face may dissolve only as the concept's own set piece (the loop), smoothly and last. When in doubt, follow v15.
- **Droplets on the lens or a wavy heat-haze warp as a transition** (v108 rev 2: *"remove the water droplet filter"*, *"the squiggle, swirl, weird animation"*). **[plan]** registry
- Outro / title cards, watermarks, labels, name tags, counters, timecodes, CJK lines; a recoloured logo. **[plan]** `logo_uv` banned
- **Interface / HUD overlays drawn over the footage**: a heart-monitor trace, readouts, timers (v6's VHS counter; v109 rev 2: *"change the heart monitor … You don't have to replace this with anything"*). A frame treatment (v109's surveillance feed) is fine; a widget parked on the picture is not. **[plan]** registry (`ekg109` rejected)
- **Spins in a smooth, dark edit**: v109 rev 1 removed the headspin for flow (*"I don't really like how that flows with this edit"*), and the roll and flip at its end went with it. Spins belong to kinetic edits, once. **[eye]**
- **A graphic where the cut needs none** (v110 rev 2: the window-light panes over the opening, *"isn't really necessary"*). **[eye]**
- **Forensic or lab graphics as a transition** (luminol glow, UV, spatter analysis overlays) (v111 rev 1: *"I dislike the graphic/animation … around the 23 second mark the forensics one"*; `luminol108` now rejected). Use the scene's own material (the blood soaking out). **[plan]** registry
- **Stripe or line transitions and after-images in a dark, smooth edit** (v110 rev 1: *"the doorway transition at 16 seconds … the lines transition at 17 seconds"*: an after-image and a rime frost). **[plan]** registry cautions
- **A mirrored pack shot**: read any text in the frame (v109: p7's tape read SSORƆ TON OD); flip it back with `hflip=True` (v109 base). **[eye]**
- A line shown as spoken when the lips don't match (v101); captions on words the song isn't singing (v103).
- Chimes, bells, shimmers, drones, swirls, whines, a swell on every move (v12, v106, v13). **[plan]** sound kinds (a WARN: v107 shipped one swirl)

## 2. Every first delivery already has (these were asked for again and again)
1. **One signature custom graphic that becomes a transition**: on screen as a graphic for about a second, then it carries the cut (v106 tear lens, v13 light ribbon, v107 front page → stamp → banner). Asked for in **4 of the last 4** edits. **[plan]** `signature`
2. **A loop that is the edit's most creative set piece** and lands exactly on frame 0's own picture, still moving across the wrap (v105, v106, v107 rev 2). **[plan] [qc]** seam ≤ 1
3. **Lean sound**: about 10–12 sound events in 20–23 s, layered only at the set pieces, small transitions silent, nothing on beat punches or letters; v107's 28 placed effects is the ceiling (cut in v12, v106, v13). **[plan]** > 16 warns, > 30 fails
4. **No headspace**: no span over ~1 s without a cut, a transition or a designed beat (v104, v106). **[plan]** estimate **[qc]** motionqc
5. **A concept from the song's own words or the character's history**, carried by one hero object through picture, text and loop; the hero is a **motif** (2–4 appearances), not every transition (v11, v13). **[plan]** families
6. **Physical, kinetic transitions** from the character's world (rip, pour, spin, zipper, page, eye dive, shutter, emblem/prop), each a different idea; generic moves (whip, slam, impact, dolly, smear) are filler between them. **About 24–26 designed transitions in ~22 s (≥ 1.1/s), nearly all custom** (v108 had 21 + the loop, 0.97/s, and the verdict still said *"could have contained slightly more transitions/animations"*). **[plan]** density, generic share, repeats v108 rev 1 asked again for *"a lot more transition and unique graphics with custom animated transitions … smooth transitions and creative ones so the edit flows"*: replace generic connectors with custom, smooth ones. *Read with 11: the density is for an energetic song; a calm song (v14) gets fewer, slower set pieces on its structure.*
7. **Faces centred and whole**; spins and dives land on a centred, tracked face (v107). **[plan] [qc]**
8. **The motion pass**: speed ramps with clean flow on hook shots, the beat camera (punch, kick, blur), smooth sub-pixel motion, no judder (v10, v106). **[qc]** judder
   - *v108 exception (not a new rule):* the owner turned the beat camera off for DOOMSDAY (*"I generally like when on the beat the clip … jumps up and down with the beat, but in this edit I would like for you to remove that just for this edit"*): a slow, menacing edit may flow better without the punch. Keep it the default.
9. **Restored, sharp sources**: `sr_prep`, zoom ≤ 1.10 on 720p, no SOFT shot on a hero moment (v105). **[plan]** zoom **[qc]** sharpness
10. **A smooth ending**: the beat camera rests through the break, fewer and longer cuts (v107).
11. **The style matched to the song** (v14 standard, *"a different style ... but is still really good"*): on a calm, nostalgic song, a calm edit (slower set pieces on the song's structure, a breathing camera, ~5 quiet effects, a low overlay) is right; v10–v12's density and beat camera are for energetic songs.
12. **A liked transition used once, fast; an emblem transition ~2 s with stages; the owner's named moment opens the edit** (v14 rev 2: the print *"too slow and repeats multiple times"*; the emblem *"too fast"*; *"barry waking up ... the focal point of and in the beginning"*). An asset the owner supplies as a reference is built faithfully in our own drawing, with a designed pop (the achievement toast).
13. **The owner's concept boards are built from the shot's own props**: lift, tilt or move the real object (v108: the real slide pivots up in his fingers) rather than a CG copy beside it (*"merge that slide graphic … with one of the actual slides from that scene"*). Board choices (text, timing) apply to that edit only; ask when the rest is left open.
14. **A freeze lands on the hit and is emphasized in depth** (v15 round 2: *"see if there's any other freeze frame shots that could be better selected ... emphasize it more and make the scene a little bit cooler"*): the instant of most action, a real source frame (not an interpolated one), the previous shot running into the same framing; then plate / subject / light layers with a camera stepping on the beat (bullet time), the scene's own light as rays and rim, a few physical particles.
15. **"Blank space" = new cuts with motivated custom transitions plus a visible, motivated in-shot animation in every plain hold**, big enough to read at phone size (v15 round 2).
16. **A seamless loop shows its destination early**: frame 0 visible at the end of the move the whole way, growing to fill on a smooth landing, the surround turning into frame 0's own light; never a giant card fading in from behind the camera (v15 round 2: *"the loop isn't particularly seamless"*; the corridor REWIND, seam 0.13, approved).
17. **A transition the owner wants to "focus" has one small, bright, motivated focal point that grows into the move, with every part a smooth function of time** (fixed noise, eased fronts, analytic particle paths; v15 round 3 IGNITION: *"a focal point graphic ... really, really smooth animation"*).
18. **A focal point mid-edit, besides the drop**: one centrepiece graphic that plays for ~1 s with its own motion and depth (behind him through his matte, in front of him, never across the face) and then *becomes* the transition (v109 rev 3: *"it's just missing one more focal point … one more really, really cool, custom, unique graphic into a transition … the finishing touch"* → THE PHANTOM'S TRAIL, then the verdict; the same ask as v13's light ribbon and v15's IGNITION, rule 17). **[plan]** `SET_PIECES`
19. **A flow of graphics that become transitions**: in the back half, chain two or three graphic → transition moments, each graphic on its shot for ~0.5–1 s first (v109 rev 1: *"a cool flow where there's unique graphics appearing and then transitions from those graphics"* → the fingerprint dive, the photo's fire; approved).
20. **A prop's effect starts on the prop, tracked**: the fire comes out of the real burning photo (its flame's foot tracked through the shot), burns the photo first, then the frame (v109 rev 2: *"make it stem from the actual picture that's burning and try to make it tied into that transition"*). Extends 13 to every prop-motivated transition.
21. **Keep the edit on Dexter; supporting characters only when the concept needs them, and swap soft or busy shots for sharp "texture" clips** (fire, foliage, rust; the high-bitrate S1/S4 packs) (v109 rev 1: *"remove the clips with dokes and replace them with other high-quality texture clips"*).
22. **A violent scene carried by light, not by drawn spatter**: a motivated light (the bare bulb's pool) carries the blood room in, soft-edged, one continuous push; the cast-off spatter sweep was rejected twice (v110: *"smoother and more seamless"*, *"smoother or more cinematic"*, then the SWINGING LIGHT and the verdict).
23. **A calmer drop**: no impact shake on the drop; the beat camera rests through the drop's first bar and runs at about half its punch and kick (v110 rev 2: *"the scenes shake a little bit too much … reduce the shaking/beat jump"*). The beat camera stays the default, lighter. **[eye]**
24. **Text: start without; if a title rides a drop, phase it** (the setup words already written before the drop, the payoff word on it), **and expect to remove it** (v110: *"I'm losing, and then power would be when it drops"*, then *"remove the I'm losing power"* at the verdict; as v12 removed both titles). **[plan]** titles
25. **A prop dive is one continuous, seamless move** (the push into the real muzzle, light first, the next face only once the opening is big, the motion carried through the cut; v110 rev 2 *"more seamless and smoother"*).
26. **A creative loop in which the end causes the start**, never a flash, burst or fade into frame 0 (v111 rev 1: *"implement a new more creative loop"* after a muzzle-flash burst; THE TRACER: he fires, we whip after the tracer, and it lands as the light that blows on "shoot"). **[plan]** loop
27. **A living graphic or animation in every section, on the shots, not only at the cuts** (particles, rays, light washes, a rising moon, dust in a beam), motivated by a light or material in the shot and kept off faces (v111 rev 1: *"I want more custom graphics and animations"*; the verdict: *"adequate"*). **[eye]**
28. **"Adequate" is not "liked":** on a "best edit" brief, plan one designed animation per section and a signature that reads at phone size from the first delivery (v111 verdict). **[eye]**

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
- **"Improve the loop / the ending"** (v109 rev 1): a fade or a fog is not enough; the loop needs animated physics (v109's gust: dust from his own matte, the same gust re-forms frame 0 head first, no dark gap), and the ending's connectors must be smooth and motivated, not a run of library spins.
- "Lacklustre" means motion and polish, not more overlays (v10). "Add transitions/graphics" means new cuts with themed transitions, not effects stacked on shots (v105).
