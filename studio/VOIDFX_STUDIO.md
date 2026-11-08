# voidfx studio handbook

This is everything a voidfx studio needs to make an edit the owner will approve on the first or second pass. It covers the standard, every preference learned over twelve edits here (v1–v12) and the Dexter studio's v105 and v106 and their revision rounds, plus Studio 2's notes, what works and what doesn't, and how to work twice as fast.

Read this first. Then read `SCENE_PACKS.md` (the sources), `/docs/TOOLKIT.md` (the engine) and `/CLAUDE.md` (the binding rules).

---

## 1. The benchmarks: watch these before you start

| Edit | Folder | Why it is a benchmark |
|---|---|---|
| **v105 DRACULA** (Dexter × Tame Impala "Dracula", rev 3; the Dexter studio) | `v105/` on the Dexter studio's branch | Approved as a standard: *"I like this edit and would like for you to make it a standard. The only gripe I have is the quality of some of the clips."* The Dexter scaffold base. Concept SUNDOWN (the lyric "run from the sun like Dracula" × Dexter's day mask / night hunt), two grades split on the drop, five set pieces (SUNDOWN eclipse, BAT BURST, BLOOD MOON, COFFIN, the ASHES TO SUN loop), 27 transitions in 23 s, light physically behind him. Handoff: `sync/handoffs/2026-11-07_dexter_v105_DRACULA_standard.md`. |
| **BLOOM** (The Flash × fakemink "Night Blooming Jasmine", rev 3) | `v12/` | Approved as a standard: *"I like this edit make it a standard."* The newest engine (`tools/new_edit.py` builds on it). The reference for one hero asset carried through the edit (the lightning jasmine), an emblem transition on the real tracked emblem (EMBLEM BLOOM), a transition built on a real phenomenon (FRACTAL BURN), a focal piece lit behind him, a closing-bud dive onto frame 0 (seam 0.19), and restraint: no text, 37 effects. Handoff `sync/handoffs/2026-11-08_flash_v12_BLOOM_standard.md` |
| **v107 ALL CAPS** (Dexter × Madvillain "All Caps", rev 4; the Dexter studio) | `v107/` on `dev/pipeline-v2` (the v12 engine) | Approved as a standard and the Dexter scaffold: *"I like this edit make it a standard."* The reference for a concept from the hook word carried by one object (the name printed, stamped, flown into the sky as the real WE ♥ DEXTER banner, spelled by the crowd's confetti for the loop), physical kinetic transitions (plastic rip, hot molasses, headspin, the front page, page turn), spell-outs on an even rhythm grid, and what not to put in a slot (§4). Handoff `sync/handoffs/2026-11-08_dexter_v107_ALL_CAPS_standard.md` |
| **v106 WONDERWALL** (The Flash × Oasis "Wonderwall", rev 3; made in the Dexter chat as a one-off) | `v106/` on `dev/pipeline-v2` (v11 engine) | Approved as a standard: *"I like this edit make it a standard."* The reference for a **story concept from a lyric line and the show's history** ("the one that saves me" = Iris bringing Barry back from the Speed Force), **sound restraint** (28 → 14 sound moments, silent transitions, the song carries the ending), **a loop that lands exactly and keeps moving** (the Speed Force mist dissolves into frame 0, seam 0.14) and **measured dead-span, pop and judder audits**. Signature pieces: TEAR LENS (his goodbye inside her falling tear), THE WONDERWALL (tiles cut from the edit's own frames rise behind him, then burst toward the camera), the lightning rod, the Speed Force mist. Handoff `sync/handoffs/2026-11-08_dexter_v106_WONDERWALL_standard.md` |
| **BOP** (The Flash × DaBaby, rev 4) | `v11/` | Approved as a standard: *"I like this edit and would like for you to make it a standard."* The previous engine (inside v12). The reference for **concept, focal set pieces and the loop**: the song's spoken "Harrison" turned into the Reverse-Flash rivalry (a red rival grade against Barry's gold); THE RIFT (a tear across the frame into the Speed Force, flown through); a detailed procedural Reverse-Flash emblem revealed by a coin flip of the real tracked chest emblem; the REVERSE loop (strike, flip, red radiating, a dive through the black disc that lands exactly on frame 0); beat animations on every shot that only moved to the beat (aura, time remnants, charge-up); red eye dive, bolt split, clash, strobe echo, bolt trace, heat haze; two designed titles only. See `v11/README.md` for every revision and why. |
| **LET IT HAPPEN** (The Flash × Tame Impala, rev 5) | `v10/` | Approved as a standard: *"I like this edit and would like for you to make it a standard."* The reference for **motion and professional finish**: velocity ramps with optical-flow slow motion on restored 2× source, a beat-synced camera (zoom punches, rotation kicks, hit-frame blur), light rays, multi-stage set pieces (emblem dive + drop wave, time particles, lens shatter, lightning branches, perimeter lap, phase, whirlwind), bullet time in frozen holds, onset-timed lyric type (runner drop-off, charge fill, AROUND ring), and the Speed Force loop back to frame 0. See `v10/README.md` for every revision and why. |
| **HIM ALL ALONG** (Dexter × Gunna, rev 2) | `v7/` | Approved as a standard: *"The transitions were creative and well animated."* Physical, themed, Dexter-specific transitions (blood-slide box, plastic burst, body-bag zipper, blood on the lens, M99 blink, magnifier → pupil loop), and a hero transition on the song's drop. |
| **WARMPOP** (Dexter × George Clanton, rev 3) | `v6/` | Approved as a standard: *"wonderful transitions, animations, graphics, while maintaining the style that I like … I like how the music correlates to the edit. I like the text."* The amount of designed motion per second, the music-led structure, the eased two-line captions and the depth graphics. |
| **SURPRISE** (Doakes × Need It, v4) | `v4/` | The first approved standard. A dialogue-led cold open that plays as **one continuous take**, the barrel → scope fly-through, and the pupil → iris loop. |

Every new edit must **match or exceed** these. It must **not copy their look**: each edit gets its own grade, type and transition mix.

---

## 2. Non-negotiables

1. **Format:**
   - 9:16, 1080×1920, 60 fps.
   - H.264 + AAC with fast-start (TikTok upload), plus a high-quality master (CRF 11 + PCM).
   - **20–26 s**; don't run long.
2. **Framing:**
   - Faces centred (face at about 37% of frame height) and never cut off. YuNet tracks every shot.
   - **Leave out shots whose face is wider than the 9:16 window**, or so tight the face fills the frame. Text has nowhere to go on those.
3. **Loop:** seamless in picture and sound. Use a black → black wrap, or the same motif both ends: pupil dive → iris or glass opening, tape rewind → tape load, static → static.
   - The audio is built **circularly**, room tone and drone run across the wrap, and mastering runs on a wrapped copy.
   - Audio and video are **exactly** the same length.
   - **Never use an outro card.**
4. **Logo:**
   - The voidfx logo appears **once**, as a transition: slam in, then fly through the "o".
   - **Never recolour, retheme or restyle it.** Use `src/voidfx_logo.webp` exactly as supplied (`tin="logo_orig"`).
   - No constant watermark.
5. **Text:**
   - Every word **eases in**: fade + rise + blur-to-sharp. Nothing pops on.
   - Readable size and contrast, inside the 1240–1640 px band, clear of faces and TikTok's UI.
   - Each text moment gets its own designed animation.
6. **No labels:** no name tags, speaker chips, "who is who", counters or timecodes. No stamps sitting on top of captions.
7. **Transitions:**
   - Pronounced, designed and **going through something**.
   - **Every transition has its own sound** *(the original rule)*. **Updated by v12 and v106:** at most one sound per transition, small ones may be silent, layered sound only at the set pieces (§5, sound design).
   - No plain hard cuts in quiet or dialogue sections.
8. **Sound:**
   - Smooth and clean; the song is edited on its beat grid.
   - Dialogue is cleaned (Demucs stem), levelled, with equal-power fades.
   - **−13 LUFS, true peak ≤ −2.5 dBTP, measured after AAC.** Keep margin; aim for −3.0 or lower.
9. **Review before delivery:** run the ship checkpoint (section 7), then a visual sign-off on frames pulled from the **encoded** file. If anything fails, fix it and re-render. Never ship on the automated pass alone.
10. **Honesty:** you can't watch or listen. Say what was verified by frames and measurement, and ask the owner to watch once with sound.

---

## 3. What the owner likes (with evidence)

- **Transitions as the star.**
  - *"crazy transitions that are visually appealing"* and *"the kind where the viewer wonders 'how did they do that'"*.
  - Approved: the barrel → scope (v4); the fly-through-the-"o" logo (v4, with the original colours); the pupil dive; the CRT fly-through (v6); the cube, the sun stripes and the film strip (v6); and in v7 the blood-slide box, the plastic burst, the zipper, blood on the lens, the M99 blink and the magnifier.
- **Themed, physical transitions.** Things from the character's world that the camera passes through, not abstract overlays.
  - For Dexter that means blood slides, kill-room plastic, the knife, body bags, luminol, M99 and Harry's code.
  - For The Flash it meant lightning, the speed force and the emblem.
- **Lots of designed motion.** He repeatedly asks for **"more transitions, animations and graphics"** and **"more sound effects"**. Density is welcome when every move is clean.
  - **Sound is the exception since v12 and v106:** in both he asked to cut about half the sound effects (*"get rid of like half the sound effects"*, *"remove like half of the sound effects mostly the tedious annoying ones like the emblem shine and the few near the end"*), then approved. Picture density stays; sound goes to the set pieces and structural hits.
- **Graphics that add depth:**
  - v6: the vapor-world tune-in behind the person matte, palm shadows, bokeh motes, neon light spill and the VHS pause;
  - v7: evidence markers and the CASE CLOSED stamp.
- **Music that drives the structure.** The cold open sits on the song's build; the **biggest transition lands on the song's biggest moment** (the full mix returning); cuts sit on the half-beat grid. *"I like how the music correlates to the edit."*
- **Meaningful text:**
  - the character's own words as two-line eased captions (v6);
  - the song's hook as a designed title (HIM ALL ALONG in luminol);
  - lyric keywords whose animation acts out the meaning (v5: FALLING drops, FADING dissolves, DROWNING ripples).
- **Detailed, themed text treatments:**
  - footage-in-letters knockout type;
  - blood-fill and drip, then shattering with the glass;
  - light-sweep reveals;
  - fly-in from the camera;
  - chrome titles;
  - neon tubes that flicker on per word;
  - engraved brass (CLOSE on the slide box).
- **A strong opening**, either dialogue-led as one continuous take (v4) or a striking visual hook (the magnifier on his eye, the VHS tape load).
- **Polish:** halation and bloom, grain, anamorphic streaks, colour grades with a clear identity, and smooth sound.
- **Built-in review passes.** He wants the studio to catch problems itself rather than rely on rounds of feedback, and to judge whether the edit is ready to ship before it is sent.

- **v8 WISH YOU WELL** (owner: *"I like this edit, I think it did most things well"*):
  - **The "Darling," sequence (liked):** a freeze-frame where the room drains to indigo, the word written on in red script with a swash, the comma swelling into a drop of blood that falls in slow motion with Dexter refracted inside it, then blooms in water on the drop.
  - **The rear-view-mirror open and loop (liked):** a mirror in a dark rainy car, push into it, and pull back into it at the end.
  - **The "basic" transitions were good:**
    - streetlight sweep;
    - windshield wiper;
    - whip pans, horizontal and vertical;
    - plastic sheet wrapping the lens;
    - one-frame impact negative;
    - rain-on-glass focus pull;
    - lamp switching on;
    - one cut per syllable on the hook.

- **v9 NIGHT BLOOM: the text was "perfect"** (owner, after calling the edit good but lacklustre overall). **This is the standard text style for every edit.** The code is in `v9/work/render9.py` and new edits inherit it:
  - **Captions** (`text_cap` + `cap_word`, TEXT style `cap`):
    - Inter Display Black, all caps, two lines (line 1 about 88 px, line 2 about 114 px, a little larger), centred in the 1240–1640 band.
    - White face; a dark keyline about 7 % of the size; a soft drop shadow; a light dark scrim behind the band.
    - **Emphasis words in bright red** (BGR 0.20, 0.17, 1.00) with a soft red glow, so they hold on any background, even a red sky.
    - Each word eases in on its spoken time (fade, 30 px rise, blur to sharp, 0.17 s). The exit is a fade, a slight blur and a 14 px drift up.
    - Lines auto-fit to 940 px. A second lockup can wait (`from`) so the first stays readable.
  - **Hero title** (`text_hero`, TEXT style `hero`):
    - Per-letter build on a shared baseline. Each letter blooms open from a point (scale 0.3 → 1 with a small overshoot, a ±24° twist, blur to sharp, a soft white flare behind it), staggered about 35 ms and timed to the sung words.
    - Line 2 lands bigger, white-hot, then floods crimson from the bottom like blood.
    - On the exit, the letters loosen and blow away as particles (petals in v9; use the edit's own motif: blood droplets, ash, glass).
  - Keep the construction and motion; change only the palette, the emphasis colour and the exit particles to fit each edit.

## 4. What the owner rejected: never do these

| Rejected | Edit | Lesson |
|---|---|---|
| A sloppy, choppy opening; dialogue clips "stuck together with Elmer's glue" | v3 | Dialogue must play as **one continuous take** (J-cuts, dissolves, a matched-angle morph, equal-power audio fades). |
| Name labels ("who is Doakes / who is Dexter"), a stamp under the captions | v3 | No labels. Text never sits under or over other text. |
| Text that just appears; the TARGET ACQUIRED / I NEED IT moment "off" and not pronounced | v3 | Every word eases in. Big moments get big, designed, continuous moves. |
| A constant watermark; an outro card that broke the loop | v3 | Logo once, as a transition. No outro. |
| The BLEED IT animation was invisible or weak; a sloppy cut before "What can I say" | v4 rev | Check every text moment on stills. Never cut mid-dialogue without a designed join. |
| An explosion or starburst transition | v5 | Avoid generic bursts. Bursts only when they are physical and themed (the v7 plastic burst was liked). |
| A title card ("THE FLASH: FASTEST MAN ALIVE") | v5 | No title cards. Open on a striking move instead. |
| Slow-motion run-at-camera and floating shots | v5 | Cut weak or odd footage even if it is "on theme". |
| Generic lyric words; wrong lyric ("think a thing" for "feel a thing") | v5 | Use meaningful phrases. Verify lyrics on the isolated vocal and the official lyrics. |
| Falling letters that weren't cool enough | v5 rev | Detailed, multi-stage text animation: plunge → slam → tumble. |
| Japanese subtitle lines | v6 | No foreign-language subtitle lines. |
| The VHS "SP 0:00:10" timer | v6 | No counters or timecodes. |
| Rapid dialogue run "Dramatic. Cryptic. Playful." with quick cuts | v7 | Dialogue: one or two short lines at most. No single-word stamp runs. |
| A talking "jar of blood" shot: *"pointless, especially with him talking"* | v7 | Every shot must earn its place. Don't hold on dialogue that doesn't set up the song. |
| The ending where Dexter "just says he's a serial killer" | v7 | Let the visuals carry the ending (stamp, glass, pupil dive). Don't end on exposition. |
| STAY STRONG plus red strings converging on his face with a target ring | v7 | No gimmick overlays on the face. |
| The voidfx logo turned blue (UV recolour) | v7 | **Never restyle the logo.** |
| Plain steel doors for CLOSE | v7 | Make the big text moments **character-themed and detailed** (the rosewood blood-slide box with an engraved brass plate was the fix). |
| The **text appearance in v8**: thin, wide-tracked sans lyric lines with sodium serif-italic emphasis words, letter-by-letter fades, underlines; big extruded words behind his head; elegant serif-italic script | v8 | That "elegant / editorial" type look didn't land. Go back toward what was praised in v6: bold, high-contrast, two-line captions with a clear designed treatment per moment. Keep script handwriting for at most one hero word. |
| v9 NIGHT BLOOM overall: *"good… complete"*, but **lacklustre** next to the other builds and Dexter edits in general | v9 | **Go above and beyond.** The petal/moon concept came from the song title, not from Dexter's world, and read soft instead of dark and intense. The montage leaned on quick generic moves (strobe, beam, blinds, roll, smear) with one real set piece (the bloom). Root every concept in Dexter, build at least three signature set pieces, and add more graphics (the v9 text itself was "perfect"; keep it). See §5a. |

| v105 rev 1: the sun laid over the whole frame burned away the top of Dexter's head (*"what happened with the sun and the top right part of dexters head?"*) | v105 (Dexter studio) | Light sources go behind the subject via his matte, with a light wrap (§5a item 13). |
| v105 verdict gripe: *"the quality of some of the clips"* (soft 720p, heavily compressed packs, a 3.5× zoom) | v105 (Dexter studio) | Rank sources before choosing (`sharpness.py N --src`), zoom ≤ 1.1, hero shots on high-bitrate packs, ask for better packs (§5a item 12). |
| v10 rev 3: the glass shatter in the frozen bullet scene (a crack web and hanging shards over the frame) | v10 | Replaced in rev 4 by TIME PARTICLES: the frozen moment comes apart into fragments of its own pixels and rebuilds as the next moment, from his hand outward. Glass has to land (see the props rule below). |
| v10 rev 3: the CARRY OFF whirlwind exit | v10 | Replaced in rev 4 by a lightning runner that drops each word off on its sung onset and later snatches the letters away. |
| v12 rev 2–3: the NIGHT and BLOOM titles; half the sound effects; the bell on the flower; a whoosh on an early transition | v12 | Text is optional; fewer, bigger sounds; no chimes or bells on graphics. |
| v106 rev 2: *"the tedious annoying"* sounds (the emblem shine, a sound on every camera punch and title letter, the sounds after the burst); a span *"where there isn't anything happening"*; animations not smooth enough | v106 (Dexter chat, Flash edit) | Sound the set pieces and structural hits only; transitions may be silent. Find dead spans, pops and judder by measurement (`tools/motionqc.py`). Flow on held 24p shots; sub-pixel procedural motion; covers exactly clear at their ends. |
| v106 rev 3: the tear-drop transition too quick to see (0.6 s) | v106 | A signature graphic transition gets ~1 s and ≥ 8 % of the frame width; move the cut to the next sung word to make room. |
| v107 rev 2–4 (Dexter studio): the 3 s slot rejected four times: a halftone press flash, a SPECIAL REPORT TV in a dark room (*"the black bars"*), SPATTER ANALYSIS → RORSCHACH (strings converging on a crosshair where his face appears), redaction boxes (*"the black box transition"*) | v107 | No black occluders; no graphics that point at a face, even one arriving later; after two failures in one slot, use a physical move or a clean downbeat cut. |
| v107 rev 2–3: a headspin landing off-centre; the same clip at 17 s and 19 s; a rough ending; a "low effort" loop; the name spelled too slowly on uneven sung onsets | v107 | Spins land on a centred face; never reuse a clip; rest the camera and lengthen the cuts at the end; the loop is a set piece; spell-outs on an even 16th-note grid. |
| v13 rev 1: *"I don't like that the singularity is the primary object in every transition and animation"*; the emblem transition (a black hole born in the emblem) didn't count as one; *"the tedious sound effects"* | v13 | The hero asset gets 2–4 appearances, and every other transition is a different idea. An emblem transition comes from the emblem itself (its bolt, its shape). Start sound lean (~10–12 events). |
| v13 verdict: *"I like this edit but I do not want you to make it a standard. It does somethings good and somethings bad."* | v13 | Approved, not a standard. The studio's reading of the weak parts: an abstract concept (a black hole as the voice of a love song); nearly all footage from the soft S1 pack under a grey grade; a drumless section with few beat moments and no big moment in the first 10 s; newer bright-red suits mixed with S1 maroon. |

### Props and effects from the character's world: when they work (Studio 2, after FOREVER)

The owner no longer bans the blood slides or the knife across the screen. In FOREVER they failed for four reasons:
- **They lingered.** The blood slides drifted around the opening as a constant overlay.
- **They were random.** The drips, the spatter and the knife pass came in on beats with no reason in the shot.
- **They looked drawn, not real.** The slide smear and the corridor of slides were flat red circles on grey glass, cheap next to the real footage.
- **They didn't land.** The glass shatter put a web of shards over his face, and the duct-tape strips fell flat.

Use blood, slides, knives, glass or tape (or any prop-style effect) only when it is:
- motivated by the shot, the lyric or the story;
- brief, not left on screen;
- lit like a real object, or taken from real footage (e.g. the S1 shot of him holding up a slide);
- in that edit's own look;
- off his face.

Check each one on still frames next to the footage, and rebuild or cut anything that looks drawn. Examples that worked: the v7 blood-slide box and the v7 blood on the lens.

## 5a. Raising the bar (after v9): the pre-build gate

The owner's standard after v9: *"go above and beyond with these edits."* "Technically clean and on time" is not enough; every edit has to **visibly exceed** v6, v7 and v8. Clear this gate **before** the first render:

1. **Concept from Dexter's world.** One sentence, rooted in the character (kill room, plastic, blood slides, tools, the Code, Harry, the Dark Passenger, the victims, the season's villain). The song shapes the rhythm and mood; it doesn't supply the imagery.
2. **Three or more signature set pieces**, each multi-stage (anticipation, action, payoff), physical, character-themed and with its own layered sound:
   - one on the drop;
   - one on the hook;
   - one on the loop.
   They're on the level of v7's slide box, plastic burst and zipper, and v8's "Darling," freeze into the falling drop. Quick moves (whips, strobes, flashes) only connect the set pieces; they don't count toward the three.
3. **Text in the approved v9 style** (§3: "it was perfect"): keyline captions for dialogue and lyrics, plus at least two designed title moments in the hero-title style that act out their meaning.
4. **Graphics in every section**, not only the cold open: depth layers, themed overlays (evidence, slides, plastic, blood), beat-synced accents in the montage.
5. **Shot strength.** Every shot earns its place by expression, motion or composition in 9:16. Swap weak, soft or awkward crops early (v9 lost three planned shots to the crop).
6. **Benchmark comparison, written down:** for each section, say what the plan does that v6/v7/v10/v11 didn't. If a section has no answer, redesign it.
7. **Ambition in review.** Review passes must also ask "what would make this moment unforgettable?", not only "is anything broken?".
8. **(v10 rev 3) Picture quality and timing are part of the bar.** The owner asked for "the best quality": restore the 720p packs (`tools/sr_prep.py`) on every edit, and check every caption word against the vocal stem (pitch + onsets) before the first render. In v10 the first two deliveries showed "ALL THIS RUNNING AROUND" a full second before it was sung.
9. **(v10 rev 3) The loop is a set piece, not a rewind blur.** A plain motion-blurred rewind read as low quality. Build the loop from the character's world and the edit itself (v10: the lyric's letters run a ring that opens into the Speed Force; panels of the edit's own moments fly past back to frame 0), and keep every frame of it sharp.
10. **(v10 rev 5, the standard) Motion is what reads as professional.** After two "lacklustre" notes, more effects on static shots didn't fix it; the motion pass did: every hook shot time-remapped to the beat (burst + flow slow motion), the camera punching and kicking on each beat with blur, light that reacts to the footage. Plan the velocity curve and the camera with the shot list, not as a last pass.
11. **(v11, the standard) Concept, focus, and the finish.** Find the concept in the material (a word in the song, the character's history); give the edit one focal set piece; build hero graphics as detailed, lit, physical assets on the real objects; give every "just moving" shot a beat animation; land the loop exactly on frame 0; measure flashes. Reached through four owner revisions: more transitions and sounds → a creative loop and beat moments → a detailed symbol, a flashier dive and a focal piece.
12. **(Studio 2, DRACULA) Source sharpness is part of the plan.** Every pack is 720p, so every shot is enlarged ~2.7× before any zoom, and several packs are heavily compressed. Run `tools/sharpness.py packs` before picking, keep zoom ≤ 10 % on 720p, put close-ups and big moments on the least-compressed packs, and run `tools/sharpness.py N` on the finished video: swap what it flags. v11 measured afterwards: the punch (source motion blur, dark, the S4 pack's heavy compression) and the grin (speed-ramp blur) read soft; the stare scores low because restoration smooths skin texture.
13. **(Dexter studio, v105) Light, loops and library reuse.** Light sources go behind the subject (matte + light wrap). The loop is the most creative transition in the edit and lands in frame 0's own image. Restyle any library transition before reuse. When the subject is burned/dissolved away, remove him before drawing light and fill the hole with real background. "Add transitions wherever possible" = replace generic connectors with themed ones and add new cuts. Mix effects against the song's mastering level (a loud master: effects +9 dB, music ducked 3 dB under the big hits).
15. **(Dexter studio, v107 ALL CAPS) Design checks before any graphic:** read the banned list; no black occluders (bars, boxes, a screen in a dark room); nothing that points at a face; spell-outs on an even grid; spins land on a centred face; no reused clips; a smooth ending. If a slot is rejected twice, a physical move or a clean downbeat cut beats a third graphic.
14. **(Dexter chat's Flash edit, v106 WONDERWALL) Measure the motion, not only the stills.** Before the first delivery, run `tools/motionqc.py N` on the encode: no span of ~1 s near the static floor (a dead span gets a new cut and a designed transition), every pop is a cut, a designed flash or a beat hit, no hold-cadence judder (flow on held 24p/30p shots), and no spike across the loop's wrap. Give each signature transition ~1 s to read. Cover transitions start and end at exactly zero and dissolve their plates. The loop keeps its background moving across the wrap (frame 0's animation rendered at virtual negative frames). Probe every source range for VFX colour flickers and hidden cuts. Fit the beat grid on the Demucs drum stem (an automatic map locked to 4/3 of the tempo on a swung strum) and time lyrics with Whisper large-v3 on the vocal stem.

## 5. What works: craft lessons

**Concept:**
- One sentence ties picture, sound and text together:
  - v6: *"a VHS Miami daydream: he disappears, the tape rewinds"*;
  - v7: *"the evidence points back at him"*.
- Pick it before choosing shots.

**Song:**
- Use the **good part**: the drop or hook where the full mix or bass returns.
- `tools/song_map.py` finds it in 3 s (biggest section change, whole-bar windows of 20–27 s with the drop at 33–47%).
- A breakdown or filtered build before the drop gives a natural cold open for dialogue or titles.
- **A dead-silence gap before a drop** is the strongest place for one short line and a freeze-frame (v9: *"Hello, Arthur Mitchell."* alone in the 1.45 s silence, then the petal bloom on the drop).
- **When the hook is far from the drop, splice the song on its beat grid** (v9). Find a bar in the later section whose instrumental matches the bar you leave (spectral correlation of whole bars; house and trap loops repeat on 4-bar cycles). End the outgoing vocal on a breath, fill to the splice with the Demucs instrumental stem, crossfade 12 ms on the downbeat, and hide the join under a designed transition with its own sound. Check the sample step at the splice.
- **Check the grid on both sides of a silence.** A gap that is not a whole number of beats shifts the grid; fit the half-beat phase locally (v9: HB_OFF puts the drop exactly on h482).

**Structure:**
- **Cold open (35–45%):** a hook shot, a line or lyric, two or three investigation or build shots, the title or hook text.
- **Hero transition on the drop.**
- **Montage on the beat** (one designed transition every 2–4 half-beats).
- **Ending motif** that loops into the opening.

**Dialogue:**
- One short line that sets up the hook works best: *"Could it be him?"* → **HIM ALL ALONG**.
- Lip-sync it on its own shot, and swap the singer's vocal to the song's instrumental stem underneath so the beat never stops.

**Transitions:**
- Vary them. Never repeat one within an edit except as a deliberate motif.
- Physical metaphors from the character's world rate highest.
- Each needs:
  - a pre-roll (the outgoing shot starts reacting 6–15 frames before the cut);
  - a post-roll (the incoming shot settles over 8–18 frames);
  - at most one sound, or none for a small move (v12, v106). A signature transition gets about 1 s and a graphic at least ~8 % of the frame width (v106 rev 3).

**Text:**
- Two-line lockups, word-timed to speech or lyrics with Whisper word times.
- Emphasis words get colour or a material (chrome, blood, brass, neon).
- Exit with a fade or a designed disintegration.

**Graphics:**
- Depth layers that react to the person matte (MODNet), plus beat-synced accents (glints, blood hits, markers).
- The finish pass (halation, grain, vignette) gives every edit its signature.

**Sound design:**
- **Restraint first (v12, v106):** layered sound only at the set pieces and structural hits; at most one sound per other transition, and small ones may be silent; no sounds on beat moments, camera punches or title letters; no chimes, shimmers or "shine"; let the song carry the ending and the loop. Both times the owner cut about half the effects, so start lean.
- A drone or room tone bed across the whole loop (if it doesn't fight the song).
- Set pieces get a layered sound: whoosh + impact + a material sound (glass, wood, plastic, zipper, paper).
- Text ticks (typewriter for case notes).
- A sub drop and riser into the drop.
- The ending: a tape-stop, rewind or heartbeat into the loop.

## 6. What doesn't work: technical pitfalls

The full list is in `/docs/TOOLKIT.md` §4. The most expensive ones:
- **Packs hide cuts.** Jump cuts the shot detector misses cause ghost frames, and source ranges running past a cut put another actor on screen. `tools/check_sources.py` (run by `build.sh prep`) catches both. The sampler never interpolates across hard cuts.
- **Text over very tight close-ups:** swap the shot; don't shrink the type.
- **Particles over a big close-up:** a person matte that fills the frame hides every "behind" particle, and "front" particles land on the face. Give close-ups a few placed hero particles that frame the face instead (v9 freeze).
- **9:16 kills two-subject shots:** a reflection or two-shot whose subjects are more than about 400 source px apart can't keep both in the crop. Check before building a transition around it.
- **Distortion transitions** (bulges, barrels) must not warp titles. Weight the distortion to the centre.
- **Particles** (blood spray, dust) must move fast and fade, or they read as blobs.
- **The last `render()` in the file wins.** Insert routing in the active one.
- **Optical flow breaks on lighting flashes:** blend those pairs instead.
- **Lyrics:** Whisper mishears rap. Transcribe the **Demucs vocal stem** in short windows, with the song title as the initial prompt, and verify.
- **True peak after AAC** is about 0.3–0.8 dB hotter than the WAV. Limit at −4 dB if the check is within 0.5 dB of −2.5.

---

## 7. The ship checkpoint (run on the encoded MP4)

`bash tools/build.sh N video qc` runs `qcN.py`, which checks:
- format and frame count;
- clean decode;
- loudness and true peak after AAC;
- frozen runs;
- face centering per shot (subject-less `face=None` shots are skipped);
- text over faces (per-shot summary; check every flag on frames);
- clicks at every cut and at the loop seam;
- the loop-seam picture;
- audio and video length;
- then the faces-vs-effects list (`tools/faceqc.py`) and the **motion audit** (`tools/motionqc.py`: dead spans per half-beat, pops, hold-cadence judder, the loop's wrap step).

Then the **visual sign-off**:
- pull frames from the **encoded** file around every transition, title, the drop and the loop;
- look at them;
- fix and re-render anything weak.

Only then deliver.

## 8. Working at twice the speed

**One brief per edit.** Use `START_PROMPT.md`: song, packs, theme ideas and must-haves in one message, so the studio never needs to ask.

**Front-load the rules.** This handbook plus the rejected list in §4 removes most revision rounds. v7 needed one round of notes; aim for zero. **Since 2026-11-08 the rules are also checks:** `build.sh N plan` (`tools/preflight.py`) runs the plan against them in seconds, before the first render. Fix every FAIL; decide every WARN. Run retroactively on v13 rev 1, it flags what the owner's rev 1 notes said: the hero asset in 7 transitions, 24 sound effects, the swirls and whines.

**The fast loop** (wall-clock on the 4-core cloud box):

| Step | Command | Time |
|---|---|---|
| Scaffold | `python3 tools/new_edit.py N SLUG "TITLE"` | 1 s |
| Song prep: map, stems, drum-stem grid, vocal-stem words, loop wrap, EDL lines | `bash tools/build.sh N song:src/SONG.mp3[:H0:H1]` | ~7 min (27 s once the stems exist) |
| Shot list and contact sheets (new packs only; cached JSON for known packs) | `python3 vN/work/analyze.py src/PACK.mp4 TAG` | ~1 min/pack |
| Dialogue on a vocal stem | `python3 tools/transcribe.py vN NAME MEDIA --start S --dur D` | 1–3 min |
| Write the EDL from `SCENE_PACKS.md` proven shots (with `HERO`, `SET_PIECES`); pick transitions from `studio/transitions.json` | | 10–20 min |
| Sound, then the plan against every owner rule | `bash tools/build.sh N audio plan` | ~15 s |
| Audit, tracks, preflight, restoration started in the background, sheets of every cut | `bash tools/build.sh N prep auto` | ~1–2 min |
| Motion check | `bash tools/build.sh N clip:A:B` | ~20 s |
| Sound | `bash tools/build.sh N audio` | ~7 s |
| **One** final render + checkpoint + review pack (QC passes in parallel) | `bash tools/build.sh N video qc` | ~7 min |
| A revision round (only the frames the change reached re-render) | `bash tools/build.sh N plan rev` | ~4–8 min |

**Two studios in parallel:**
- Each studio works on its **own git branch** and its **own version range** (Studio 1: v8, v9, …; Studio 2: v101, v102, …), so folders never collide.
- Shared engine changes go into the newest benchmark's files and the `tools/`. Merge them through a PR.

**Give feedback in one message,** listing every change. The studio applies them all in one revision and runs one checkpoint.

**Don't re-analyse known packs.** `vN/work/shots_*.json` and the transcripts are committed; copy them into the new edit.

## 9. Style bank: looks already used (don't repeat them)

| Edit | Look |
|---|---|
| v1 THE MASK SLIPS | warm cinematic, blood red |
| v2 THE DARK PASSENGER | comic-ink / halftone, 16:9 + 9:16 |
| v3/v4 SURPRISE | night thriller, scope / barrel, glass shatter, chrome-red type |
| v5 FASTEST | amber/gold lightning over deep teal (The Flash) |
| v6 WARMPOP | pastel vapor + VHS (chroma bleed, scanlines, CRT, neon) |
| v7 HIM ALL ALONG | forensic noir (drained cold colour, blood red only, UV luminol, case-file type) |
| v8 WISH YOU WELL | sodium nocturne (indigo shadows, sodium-vapour highlights, rain on glass, streetlight sweeps, warm halation) |
| v9 NIGHT BLOOM | moonbloom (violet-black night, moon-silver highlights, white Pro-Mist bloom, jasmine petals in depth, a blood moon; bold keyline captions) |
| v10 LET IT HAPPEN | prism speed (graphite-slate shadows, suit crimson, white-gold lightning bloom, prismatic RGB time-slice, frozen world in steel) |
| v105 DRACULA (Dexter studio) | SUNDOWN: bleached warm "Sunshine State postcard" day with teal shadows and the sun behind him → cold moonlit silver night with only crimson kept |
| v11 BOP | voltage / rival (deep clean blacks, crimson suit, warm gold lightning bloom, teal shadows; the rival's shots red-shifted with red halation) |
| v12 BLOOM | NOCTURNE: indigo nights, crimson suit, orange light turned cream, lightning in jasmine white over a cream glow, deep vignette |
| v107 ALL CAPS (Dexter studio) | TABLOID: newsprint-cream highlights, ink blacks, slate blues, one spot red; a misregistered red plate, paper grain and a fine shadow screen |
| v13 EVENT HORIZON | REDSHIFT: a desaturated silver-steel world, only the suit's crimson, skin and the light keep colour; the picture redshifts (dimmer, sliding to red) as time slows |
| v106 WONDERWALL (Dexter chat, Flash) | WONDER: golden-hour amber against Speed Force cobalt, milky lifted blacks, red-orange halation kept off faces, grain 0.010 |

Fresh directions for future edits:
- 16 mm film burn / home movie (Harry flashbacks);
- red-and-black ink wash with Japanese-print restraint (no CJK text);
- surveillance / CCTV night-vision;
- chalk outline / crime-scene diagram;
- blueprint / technical drawing;
- cold winter teal (Trinity season);
- Sunshine State postcard;
- a black-and-white newspaper "BAY HARBOR BUTCHER" press look;
- an X-ray or MRI medical look.

## 10. Songs used so far

| Edit | Song | Tempo | Window used | Drop / hero moment |
|---|---|---|---|---|
| v1 | Blood Theme (instrumental) | pulse grid 0.333 s | 22 s | hard stop as the "shh" |
| v2 | Matrix Funk (slowed ×1.126) | 102.8 BPM | 4 bars + drop | drop after the bass-less intro |
| v3/v4 | Migos "Need It" | 74 BPM | 25 s | 11.06 s, the gunshot |
| v5 | bôa "Duvet" | 93 BPM | half-beats 208–288 (10 bars) | "I am falling" |
| v6 | George Clanton "Warmpop" | 90 BPM | half-beats 416–496 (2:18.9–2:45.5) | 2:29.5, full mix returns → CRT dive |
| v7 | Gunna "Him All Along" | 130 BPM | half-beats 528–640 (2:01.9–2:27.8, 14 bars) | 2:13.0, +17 dB return → plastic burst |
| v8 | Brent Faiyaz "Wish You Well" (screen recording) | 138 BPM | half-beats 64–164 (13.96–35.69 s) | 33.08 drop → blood blooms in water |
| v9 | fakemink "Night, Blooming Jasmine" | 102.8 BPM | h448–h506 + h634–h650, spliced on the 4-bar cycle (2:10.9–2:27.8 + 3:05.2–3:09.9) | 2:19.38 dead silence → freeze; 2:20.84 drop → petal bloom |
| v10 | Tame Impala "Let It Happen" (radio edit) | 125 BPM | h392–h496 (1:34.3–1:59.3, 13 bars) | 1:41.94 drop → emblem dive; 1:52.04 gated stutter → time freeze; 1:59.3 → rewind loop |
| v105 (Dexter studio) | Tame Impala "Dracula" | 115 BPM | h592–h680 (2:34.6–2:57.5, 11 bars) | 2:40.8 one-bar drop-out → sundown; 2:42.9 drop (+29.8 dB) → bat burst |
| v11 | DaBaby "BOP" | 127 BPM | h32–h120 (7.75–28.54 s, 11 bars) | 9.64 beat in → red shudder; 14.34 "Let's go!"; 15.31 drop → bolt split; 28.54 → tape stop → loop |
| v12 | fakemink "Night Blooming Jasmine" (again; v9 used 2:19–3:09) | 102.8 BPM | 18.71–42.05 s (bars 8–18) | bar 12 (28.05 s) the vocal enters, the hats fall away; bar 16 the claps |
| v107 (Dexter studio) | Madvillain "All Caps" | 87.50 BPM (drum stem; the automatic map read 175.6, the drum autocorrelation 117.4) | h176–h240 (1:00.92–1:22.86, the end of verse 1 and the beat break) | "when you spell the man name" → the stamp; the bass drops out in the last bar and returns on bar 1, so the wrap lands like a drop |
| v13 | Brent Faiyaz "Wish You Well" (full version; v8 used a 36 s screen recording) | 138 BPM half-beats, 69 BPM feel (drum-stem fit) | h92–h188 (0:20.05–0:40.92, six 16-half-beat phrases, no drums: an 808 hit at e8 mod 16, a rest at e12–14) | "Darling," (30.84) → a 3 s vocal silence → the deepest rest (33.1) → the music returns (33.97); bar 23 mirrors bar 11, so the window wraps exactly |
| v106 (Dexter chat, Flash) | Oasis "Wonderwall" | 87.02 BPM (drum stem; the automatic map said 116) | h456–h520 (2:37.50–2:59.56, bars 57–65, the second chorus) | "WONDERWALL" (16.55 s edit) → the wall bursts; bar 65 starts chorus 3 like bar 57, so the window wraps exactly |

## 11. Communication

- Short progress lines while working. No long code in chat.
- **Final message:**
  1. what the edit is (one paragraph);
  2. what changed or what's new;
  3. what the review passes caught and fixed;
  4. the measured checkpoint numbers;
  5. a request to watch once with sound.
- Name every file path in full. Commit and push to the session's branch.
