# voidfx studio handbook

This is everything a voidfx studio needs to make an edit the owner will approve on the first or second pass. It covers the standards (§0: v105 DRACULA, v104 THE PASSENGER, v103 FOREVER), every preference learned over ten edits and more than twenty revision rounds, what works and what doesn't, and how to work twice as fast.

Read this first. Then read `SCENE_PACKS.md` (the sources), `/docs/TOOLKIT.md` (the engine) and `/CLAUDE.md` (the binding rules).

---

## 0. The standards: v105 DRACULA, v104 THE PASSENGER and v103 FOREVER (watch all three first)

### v105 DRACULA (the newest standard; the scaffold starts from it)

The owner, after rev 3: *"I like this edit and would like for you to make it a standard. The only gripe I have is the quality of some of the clips."*

| Layer | DRACULA (v105 rev 3) |
|---|---|
| Concept | SUNDOWN. By day he wears the mask (sunny Miami, the boat, the smile). The last chorus is "run from the sun like Dracula", so the sun sets across the song's one-bar drop-out and night slams in on the drop (the biggest change in the song). Night is the hunt. At the end the sun takes him, and the loop opens in that same sun. |
| Look | Two looks split on the drop. **Day:** a bleached warm "Sunshine State postcard" with teal shadows; the sun with rays and lens ghosts sits **behind him** (his MODNet matte, a light wrap on his near edge), with sunlit dust in the air. **Night:** cold moonlit silver and deep blacks, only crimson kept and pushed, with a crimson bloom. |
| Opening | The clean boat shot with the sun still blazing from the loop, calming over the first quarter second. |
| Set pieces | **SUNDOWN:** the sun sets down the edge of the frame, then an **eclipse** (the moon's disc with a streaming corona and a diamond ring) takes the light, and bats gather behind him. **THE BAT BURST** (the drop): a 3D cloud of bats pours at the lens against a crimson flash, and a per-letter "DRACULA" breaks into bats. **THE BLOOD MOON:** a procedural blood moon rises behind his cut-out. **THE COFFIN:** a height-map-lit lid slams over him. **ASHES TO SUN** (the loop): he burns like paper, 3,000 embers spiral into the sun (frame 0's sun), it flares, and the light collapses into it on the opening shot. |
| Transitions | 27 designed cuts in 23 s, each with its own sound: sun flare, whip, film burn, slam, card flip, quarter-turn, palm sweep, light sweep, eclipse, bat burst, strobe, impact, torch blind-out, cape, moon iris, lamp on, logo, roll into the upside-down shot, coffin, mist, bat swarm, eye dive, face-match, shutter, zipper, great bat, sun flare. |
| Animation | A camera float on every hold; beat punches (strong on the bars) from the drop on; speed ramps with ghost trails; gathering bats; drifting fog; a pulsing crimson backlight. |
| Text | Only the words verified on the Demucs vocal stem (Whisper in tight windows, no hint), on their sung times, in the v9 style: SAW THIS MOMENT / COMING FROM **AFAR**, RUN FROM THE **SUN** / LIKE, the per-letter hero **DRACULA**, and **DRACULA** twice more. |
| Music | Tame Impala "Dracula", h592–h680, one pass, built circularly; the sound design is in the song's key (B-flat minor): a church-bell toll, a dawn chord. |

**The owner's gripe, now a rule: clip quality.**
- *"The only gripe I have is the quality of some of the clips."*
- **Why:** every library pack is 720p (even `pack7_4k`), and several are heavily compressed:
  - p8 (S1) at 0.43 Mb/s;
  - p9, p6 and p10 at about 0.7 Mb/s.
  A 9:16 crop uses about 405×720 source pixels, enlarged about 2.8× (more with zoom). The upscale pass (Lanczos plus noise-gated detail) can't invent detail.
- **v105's softest shots** (`tools/sharpness.py 105` on the shipped MP4):
  - the daybreak walk (p9, zoom 1.3, so 3.5×);
  - the palms (p10);
  - the lollipop (p8);
  - then the ice cream (p1), hood (p3) and pink-wall (p5) shots.
- **From now on:**
  1. Run `tools/sharpness.py N --src` while choosing shots, and swap anything flagged SOFT for a sharper moment or pack.
  2. Keep zoom at or under about 1.1 on 720p sources.
  3. Prefer the high-bitrate packs (p5, p7, p3, p4, scenepack2: 1.7–2.2 Mb/s) for close-ups and hero shots. Use the 0.4–0.8 Mb/s packs for fast or dark moments, where softness hides.
  4. Hide what's left of the softness with grade and grain, not with sharpening.
  5. Run `tools/sharpness.py N` on the render, and list the SOFT shots in the README's checkpoint.
  5a. Restore the sources with Studio 1's `tools/sr_prep.py` (Real-ESRGAN compact, 2×, on the CPU) once the branches are merged. It's the direct fix for soft 720p packs.
  6. Ask the owner for 1080p or 4K packs when a hero moment depends on a soft source. Otherwise restore the sources with Studio 1's `tools/sr_prep.py` (Real-ESRGAN compact, 2×, practical on the CPU; the large model tried in v105 took about 10 s a frame).

### v104 THE PASSENGER (a standard)

The owner, after rev 3: *"I really like this edit and would like for it to be a standard. Only gripe I have is that one span of the edit had some headspace that definitely could have had an edit or a cool transition."*

| Layer | THE PASSENGER (v104 rev 3) |
|---|---|
| Concept | His own lines: "I like to pretend I'm alone. Completely alone." Then "I have a dark side, too." The ink is his Dark Passenger. |
| Look | SUMI ink wash: ivory paper with fibres, ink-blue lifted blacks, only strong reds kept as red ink. One grade unifies footage from five seasons. |
| Opening | Frame 0 is bare paper. An ink sketch of him draws itself, one stroke group per synth note, while ink creeps in from the corners. A drop forms, falls, and blooms into him on the bass entry and on "ALONE". |
| Set pieces (one per phrase start) | **THE SPATTER:** red ink on his already spattered suit. **THE PASSENGER:** a light comes on, the wall goes to paper, his shadow is thrown beside him with smoke rising off it, ember eyes open on "DARK", and it lunges so both eyes rush the lens. **THE SILHOUETTE:** his body becomes a window into the kill room. **THE INK-OUT:** the picture drains back into the drop, which is the loop. |
| Transitions | 26 designed cuts in 23 s, almost none repeated, each with its own sound: ink bloom, page turn, ivory brush, whip, smear, impact, slam, light sweep, red brush, **roll into the upside-down shot** (the owner's favourite), tilt, spatter, whip up, strobe, face-match, film burn, ink bleed, passenger reveal, **quarter-turn**, logo, shutter, lamp on, plastic wrap, flashlight blind-out, eye dive, zipper. |
| Animation | A camera float on every hold; beat punches on every sub-bass hit with motion blur; speed ramps with ink ghost trails; the upside-down hold keeps turning; a breathing ink vignette on the phrase starts. |
| Graphics | Paper and its fibres, ink drift in the shadows, ink motes in depth, an ivory swash behind "ALONE.", ivory anamorphic flares, the self-drawing sketch. |
| Text | Dexter's two lines, word-timed on the isolated voice, in the v9 style. "COMPLETELY / ALONE." and "I HAVE A / DARK SIDE, TOO." are per-letter hero titles. The sound has no intelligible lyric (checked with Whisper and a published-lyrics search), so per the rule there are no lyric captions. |
| Music | A screen-recorded TikTok sound with no drums. The grid is fitted to its sub-bass hits; every cut lands on a hit or a phrase start. |

**The owner's gripe, now a rule: no headspace.**
- No span longer than about a second without a cut, a transition or a designed beat (a speed ramp, a reveal, a graphic hit or a text beat). That includes the inside of set pieces and dialogue holds.
- The owner didn't say which span. v104's longest are the candidates:
  - the pickup, 1.60 s;
  - the dark-side shot, 1.60 s;
  - the final shot, 1.31 s;
  - the floor shot, 1.20 s;
  - the dock, spatter and silhouette shots, 1.07 s each.
- In a new edit, plan a cut or a beat inside anything that long, and list each span over a second in the pre-build gate (§5a, item 8).

### v103 FOREVER

The owner, after rev 5: *"I like this edit. I would like for you to make it a standard. I just have one note. I would like for there to be more animations and transitions moving forward and that lyric kind of recognition to happen."*

**Every new edit starts from FOREVER.** `python3 tools/new_edit.py N SLUG "TITLE"` copies its engine, its toolkit (`fxN.py`) and its EDL. Then **exceed it on the owner's two counts.**

**What FOREVER does (the floor):**

| Layer | FOREVER (v103 rev 5) |
|---|---|
| Concept | From Dexter's world: *"How is it I can kill people and feel no regret?"* He keeps every kill forever (he photographs it); the Gulf Stream keeps the rest. |
| Set pieces (multi-stage, themed, own sound) | **THE RIP** (drop): kill-room plastic is pulled over the lens as the build peaks and tears open on the drop. **THE EVIDENCE PHOTOS** (hook): he raises the forensic camera, the ring flash fires on "IF" and the frame is tossed away as a photo, then a camera shutter, his wall of photos, and a last flash onto the boat. **THE GULF STREAM** (loop): the bag sinks; the edit opens in the same water, surfacing under his boat. |
| Transitions | 20 designed transitions in 24.3 s, no plain cuts, each with its own sound: surfacing, sea spray, water-drop ripple, lamp on, light sweep, plastic wrap, strobe, plastic rip, impact frame, **eye dive**, whip, **flashlight blind-out**, logo, zipper, rain focus, whip up, bubbles, roll, flash-photo toss ×2, camera shutter. |
| Animation | The camera **punches on every beat** (a zoom kick; the half-bars get a stronger kick with a chromatic split) through the riff, the verse and the hook. The frame **thumps with a heartbeat** in the build. Every shot has a slow push. |
| Graphics | Caustics, marine snow and bubbles in the water; the red heartbeat pulse at the frame edges; a swinging kill-room lamp; an anamorphic flare on the flashlight; the plastic sheet; the photo cards; the hero title exits as bubbles. |
| Text | The v9 standard (§3): his narrated line as a word-timed caption over voice-over; **every clearly sung lyric in the window captioned word by word on its sung time** (AND I **WONDER**; IF EVERYTHING COULD EVER / FEEL THIS **REAL**); the per-letter hero title **FOREVER** on the sung word. |
| Sound | Narration as VO (his lips don't move, so it isn't shown as spoken). The song is spliced on a downbeat; a sound for every transition; −13.2 LUFS / −4.1 dBTP after AAC; a circular build so the loop is seamless. |

**The owner's note, as targets for every new edit:**
1. **More animations and transitions than FOREVER:**
   - at least **24 designed transitions per ~24 s** (FOREVER had 20), each with its own sound, and no transition repeated except as a deliberate motif;
   - **beat-synced camera animation** (`BEAT_PUNCH` in the EDL, `beat_fx` in the toolkit) through **every** section with drums, and a pulse or thump layer in quiet builds;
   - **no dead holds:** any shot held longer than about a second gets a designed animation inside it (a light move, flare, speed ramp, push, text beat or themed graphic);
   - graphics in every section.
2. **Lyric recognition:**
   - Choose the song window so its **lyrics** are on screen; an instrumental-only window isn't enough.
   - Run `python3 tools/lyrics.py vN src/SONG.mp3 START END "published lyrics | line 2 | ..."`. It separates the vocals, times every sung word, corrects Whisper's mishears from the published lyrics, and leaves out anything not clearly sung.
   - **Caption every clearly sung line, word by word, on its sung time**, in the v9 caption style, with the hook or title word as a per-letter hero title.
   - The **picture recognises the lyric too:** at least three moments where a transition, animation or title lands on a sung word and acts it out. FOREVER's: the flash fires on "IF"; FEEL THIS **REAL** turns red as its photo is tossed; **FOREVER** builds as the bag goes over and sinks.
   - Never caption a part the song isn't singing (the rev 2 note), and never show narration as spoken unless his lips match.

**FOREVER's revision lessons: what was replaced, and why.** The ideas themselves aren't banned. The owner: *"I didn't necessarily hate the blood slide or the knife across the screen, I just don't like how it looked in this specific edit."* (v7's blood-slide box and blood on the lens were liked.) The execution was the problem:
- **Lingering:** blood slides drifted around the cold open as a constant overlay.
- **Random:** drips from the top edge and spatter hits fell on beats with no reason in the shot; a big knife swept across the lens mid-montage, unmotivated.
- **Looked drawn, not real:** the scalpel-cut / blood-bead / slide-smear drop and the corridor of slides were flat red discs on grey glass, cheap next to the footage and outside the edit's water look.
- **Didn't land:** the glass shatter (a shard web over his face) and the duct-tape strips.
- **So:** use blood, slides, knives, glass and tape when they are **motivated** (by the shot, the lyric or the story), **brief**, **photographic or physically lit** (or real footage), **in the edit's own look**, and off his face. Judge each on stills next to the footage; if it reads as a drawn graphic, rebuild it or cut it.
- **What stayed:** transitions **motivated by the shot or the lyric** (the flashlight in his hand blinds the lens; his camera's flash takes the photo; the dive goes into his own eye; the plastic of the kill room he's standing in tears).

---

## 1. The benchmarks: watch these before you start

| Edit | Folder | Why it is a benchmark |
|---|---|---|
| **BOP** (The Flash × DaBaby "BOP", rev 4, Studio 1) | `v11/` (Studio 1's branch) | **Studio 1's newest benchmark and base engine.** *"I like this edit and would like for you to make it a standard."* The reference for a concept found in the song itself ("Harrison" → the Reverse-Flash rivalry), a single focal set piece (THE RIFT), detailed graphics revealed on real objects (the emblem coin flip), a beat animation for every shot that only moved to the beat, and a loop that lands exactly on frame 0 (seam 0.11). Its rules are in CLAUDE.md. |
| **LET IT HAPPEN** (The Flash × Tame Impala "Let It Happen", rev 5, Studio 1) | `v10/` (Studio 1's branch) | **Studio 1's standard for motion and finish** (the Flash edit approved in chat 1): speed ramps with smooth slow motion on restored source, the beat camera, light rays, multi-stage set pieces, the AROUND ring loop. Two rounds of "lacklustre" were fixed by **the motion pass, not by more effects**. |
| **DRACULA** (Dexter × Tame Impala "Dracula", rev 3, Studio 2) | `v105/` | **The newest standard (§0); the scaffold starts from it.** *"I like this edit and would like for you to make it a standard."* The day/night split on the drop, the sun behind him, the bat burst, the blood moon, the eclipse and the ASHES TO SUN loop. The gripe: clip quality (§0, §2 item 11). |
| **THE PASSENGER** (Dexter × GLM-RST "still love you (super slowed + reverb)", rev 3, Studio 2) | `v104/` | **A standard (§0).** *"I really like this edit and would like for it to be a standard."* The ink-wash look, the self-drawing opening, the lit dark-side set piece, the rotation motif. |
| **FOREVER** (Dexter × Foo Fighters "Everlong", rev 5, Studio 2) | `v103/` | **The standard (§0).** *"I like this edit. I would like for you to make it a standard."* New edits start from it and must add more animations and transitions and caption the sung lyrics. |
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
   - **Every transition has its own sound.**
   - No plain hard cuts in quiet or dialogue sections.
8. **Sound:**
   - Smooth and clean; the song is edited on its beat grid.
   - Dialogue is cleaned (Demucs stem), levelled, with equal-power fades.
   - **−13 LUFS, true peak ≤ −2.5 dBTP, measured after AAC.** Keep margin; aim for −3.0 or lower.
9. **Review before delivery:** run the ship checkpoint (section 7), then a visual sign-off on frames pulled from the **encoded** file. If anything fails, fix it and re-render. Never ship on the automated pass alone.
10. **Honesty:** you can't watch or listen. Say what was verified by frames and measurement, and ask the owner to watch once with sound.
11. **Clip quality (v105):** restore the sources with Studio 1's `tools/sr_prep.py` (after the merge), run `tools/sharpness.py N --src` when choosing shots and `tools/sharpness.py N` on the render. Swap SOFT shots, keep zoom at or under about 1.1 on 720p packs, put the hero shots on the high-bitrate packs, and ask for 1080p or 4K packs when a hero moment needs one (§0).

---

## 3. What the owner likes (with evidence)

- **Transitions as the star.**
  - *"crazy transitions that are visually appealing"* and *"the kind where the viewer wonders 'how did they do that'"*.
  - Approved: the barrel → scope (v4); the fly-through-the-"o" logo (v4, with the original colours); the pupil dive; the CRT fly-through (v6); the cube, the sun stripes and the film strip (v6); and in v7 the blood-slide box, the plastic burst, the zipper, blood on the lens, the M99 blink and the magnifier.
- **Themed, physical transitions.** Things from the character's world that the camera passes through, not abstract overlays.
  - For Dexter that means blood slides, kill-room plastic, the knife, body bags, luminol, M99 and Harry's code.
  - For The Flash it meant lightning, the speed force and the emblem.
- **Lots of designed motion.** He repeatedly asks for **"more transitions, animations and graphics"** and **"more sound effects"**. Density is welcome when every move is clean.
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
| v101 THE LESS YOU KNOW (Studio 2) overall: *"I do not like this edit … I largely disliked the style"*; some transitions were good | v101 | The 16 mm psychedelic look (oxblood / amber / plum liquid light, 70s soft-serif type) didn't land. Don't reuse it. |
| v101: Dexter's narrated line shown as if he were saying it (*"the scene with Dexter speaking where he wasn't actually speaking"*) | v101 | **Only present a line as spoken when his lips match it.** Many of his lines are inner-monologue narration. Check with `tools/lipcheck.py` and on frames, or play the line as voice-over over a shot where he isn't talking. |
| v102 LET GO (Studio 2, The Flash) overall: *"I like this edit and I honestly think it's good. It's complete"*, but **lacklustre** next to the other builds and the Dexter edits | v102 | **Go above and beyond** (the §5a gate). The remaining gaps were the **concept** (built around the lyric "let go" rather than a moment from his world), the **number of standout set pieces** (the strike on the drop was the only one; the rest were quick reworked v5 moves), and the **graphics** (subtle sparks and arcs that don't read at phone size). |

| v10 rev 2 (Flash studio): *"relatively no breathing room or deadspace… remove the scene with Barry's eyes being lit up"* | v10 | Dead space was the problem, not missing effects. Glowing-eyes shots read as a gimmick; replace them with something from the character (his own lightning igniting). |
| v10 rev 3: *"cooler transitions… text timing… smooth… a more creative loop… best quality"* | v10 | Quality and timing were part of "lacklustre": restore the source and put every lyric on its sung onset. |
| v10 rev 4: *"remove the glass shatter scene… a brand-new animation… unconventional"* | v10 | A glass web over the frame reads as a cheap overlay (as in v103). Build unconventional set pieces from the character's world (TIME PARTICLES). |
| v10 rev 5: *"still… lacklustre… could use more animations and overall professionalism"* | v10 | The motion pass (speed ramps + beat camera + reactive light) fixed it, not more effects. |
| v11 rev 3: *"improve the loop… more creative… replace the parts where Barry's just moving to the beat"* | v11 | Shots that only move to the beat read as filler; give each a beat animation and sound. The loop must be creative (the same note as v105 rev 3). |
| v11 rev 4: *"polish the symbol more and make it more detailed… smoother and flashier… one of the focal points"* | v11 | Hero graphics must look like real objects revealed on the real thing; every edit needs one focal centrepiece. |
| v103 rev 1: the last word of the VO line "gets cut off"; a low-quality early shot; captions where *"the song didn't sing the lyrics at those parts"* | v103 | Narration lines must end on a full stop or question with silence after them. Check every shot at full resolution. **Text only on clearly sung or spoken words**, each on its time (`tools/lyrics.py` marks what isn't clearly sung). |
| v103 rev 2 → 4: blood slides that *"stick around"* in the cold open; *"random blood dripping"*; the knife slicing across the lens; *"the blood and slide animation"* (the scalpel/beads/slide-smear drop and the drawn slide corridor) | v103 | **The ideas are fine; the execution wasn't** (*"I didn't necessarily hate the blood slide or the knife across the screen, I just don't like how it looked in this specific edit"*). They lingered (slides parked on screen), were random (drips, spatter and the knife pass with no reason in the shot), or looked drawn next to the footage (flat red discs on grey glass). Use them motivated, brief, physically lit or as real footage, in the edit's look, and off the face (§0). |
| v103 rev 4: the glass shatter and the duct-tape strips, as built in that edit | v103 | Replaced by the eye dive and the flashlight blind-out (approved in rev 5). Prefer transitions motivated by something in the shot; if you bring glass or tape back, it has to look physically real and stay off the face. |

## 5a. Raising the bar (after v9): the pre-build gate

The owner's standard after v9: *"go above and beyond with these edits."* "Technically clean and on time" is not enough; every edit has to **visibly exceed** v6, v7 and v8. Clear this gate **before** the first render:

1. **Concept from Dexter's world.** One sentence, rooted in the character (kill room, plastic, blood slides, tools, the Code, Harry, the Dark Passenger, the victims, the season's villain). The song shapes the rhythm and mood; it doesn't supply the imagery.
2. **Three or more signature set pieces**, each multi-stage (anticipation, action, payoff), physical, character-themed and with its own layered sound:
   - one on the drop;
   - one on the hook;
   - one on the loop.
   They're on the level of v7's slide box, plastic burst and zipper, and v8's "Darling," freeze into the falling drop. Quick moves (whips, strobes, flashes) only connect the set pieces; they don't count toward the three.
3. **Text in the approved v9 style** (§3: "it was perfect"): keyline captions for dialogue and lyrics, plus at least two designed title moments in the hero-title style that act out their meaning.
4. **Graphics in every section**, not only the cold open: depth layers, themed overlays (evidence, plastic, light, water, blood, slides), each motivated, brief and physically lit, never parked on screen (§0), beat-synced camera animation through every section with drums.
5. **Shot strength.** Every shot earns its place by expression, motion or composition in 9:16. Swap weak, soft or awkward crops early (v9 lost three planned shots to the crop).
6. **Benchmark comparison, written down:** for each section, say what the plan does that v6/v7/v8 didn't. If a section has no answer, redesign it.
7. **Ambition in review.** Review passes must also ask "what would make this moment unforgettable?", not only "is anything broken?".
7a. **Studio 1's rules (v10 LET IT HAPPEN and v11 BOP).** Check each one off in the plan:
   - a **motion pass on every hook shot** (speed ramps, smooth slow motion where it stays clean, beat-synced camera);
   - the **720p source restored** (Studio 1's `tools/sr_prep.py`, Real-ESRGAN compact on the CPU), plus `tools/sharpness.py`;
   - **lyrics checked against the sung vocal**;
   - **designed set pieces on the drop, the hook and the loop**;
   - a **concept found in the song or the character** (v11: "Harrison" → the Reverse-Flash);
   - **one focal set piece** with its own layered sound, on a structural moment;
   - **hero graphics detailed and lit to the shot**, revealed on real objects, checked at full size;
   - **no shot that only moves to the beat**: each gets its own beat animation and sound;
   - a **loop that lands exactly on the first frame**: measure the seam (blurred difference ≤ 1);
   - **flash brightness measured in the final file** (`qcN.py` section 7b): a flare should keep the picture;
   - when the lyrics are explicit, **only a couple of designed titles**.
   - **nothing on faces:** effects routed around a face/head box;
   - **flash peaks at or under about 110 mean luma**, measured in QC section 7b.
   When an edit reads as lacklustre, do the motion pass first; more effects didn't fix it.
8. **More motion than FOREVER, and no headspace (§0):**
   - count the plan's designed transitions (at least 24 per ~24 s; THE PASSENGER has 26);
   - list the beat-punch sections;
   - **list every span longer than about a second** and name the cut, transition or designed beat inside it.
9. **Lyric recognition (§0):** the window has sung lyrics; `tools/lyrics.py` has been run with the published lyrics; every clearly sung line is captioned on its words; at least three picture moments land on sung words.

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
  - its own sound.

**Text:**
- Two-line lockups, word-timed to speech or lyrics with Whisper word times.
- Emphasis words get colour or a material (chrome, blood, brass, neon).
- Exit with a fade or a designed disintegration.

**Graphics:**
- Depth layers that react to the person matte (MODNet), plus beat-synced accents (glints, blood hits, markers).
- The finish pass (halation, grain, vignette) gives every edit its signature.

**Sound design:**
- A drone or room tone bed across the whole loop.
- Every transition has a layered sound: whoosh + impact + a material sound (glass, wood, plastic, zipper, paper).
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
- **Light sources go behind him, not over him** (v105, the owner noticed). A sun, glow or rays laid over the whole frame burns the top of his head away where his hair meets the sky. Give the shot his MODNet matte (`seg=True`), draw the light only from the background, and add a light wrap on his near edge (v105 rev 2 `sun_fx`).
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
- audio and video length.

Then the **visual sign-off**:
- pull frames from the **encoded** file around every transition, title, the drop and the loop;
- look at them;
- fix and re-render anything weak.

Only then deliver.

## 8. Working at twice the speed

**One brief per edit.** Use `START_PROMPT.md`: song, packs, theme ideas and must-haves in one message, so the studio never needs to ask.

**Front-load the rules.** This handbook plus the rejected list in §4 removes most revision rounds. v7 needed one round of notes; aim for zero.

**The fast loop** (wall-clock on the 4-core cloud box):

| Step | Command | Time |
|---|---|---|
| Scaffold | `python3 tools/new_edit.py N SLUG "TITLE"` | 1 s |
| Map the song | `python3 tools/song_map.py src/SONG.mp3 vN/work` | 3 s |
| Shot list and contact sheets (new packs only; cached JSON for known packs) | `python3 vN/work/analyze.py src/PACK.mp4 TAG` | ~1 min/pack |
| Dialogue or lyrics on a vocal stem | `python3 tools/transcribe.py vN NAME MEDIA --start S --dur D` | 1–3 min |
| Write the EDL from `SCENE_PACKS.md` proven shots | | 10–20 min |
| Audit, tracks, sheets of every cut | `bash tools/build.sh N prep auto` | ~1 min |
| Motion check | `bash tools/build.sh N clip:A:B` | ~20 s |
| Sound | `bash tools/build.sh N audio` | ~7 s |
| **One** final render + checkpoint | `bash tools/build.sh N video qc` | ~10 min |

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
| v101 THE LESS YOU KNOW | 16 mm psychedelic reel (oxblood / amber / plum liquid light, film burn, 70s soft-serif type). **Rejected: don't reuse** |
| v102 LET GO (The Flash) | storm (crimson suit, gold lightning with white-hot cores, steel-blue shadows, gold halation, anamorphic flares) |
| v103 FOREVER | undertow (deep teal-black water, bone highlights, blood the only warm colour, caustics, marine snow, cyan halation) |
| v104 THE PASSENGER | SUMI ink wash (ivory paper highlights with fibres, ink-blue lifted blacks, only strong reds kept as red ink; ink drop, ink blooms, brush strokes, ink-bled vignette) |
| v105 DRACULA | SUNDOWN: two looks split on the drop. Day: a bleached warm "Sunshine State postcard" (teal shadows, a sun with rays and lens ghosts). Night: cold moonlit silver, deep blacks, only crimson kept and pushed (a blood moon, bats, a crimson bloom). |

Fresh directions for future edits:
- 16 mm film burn / home movie (Harry flashbacks);
- red-and-black ink wash with Japanese-print restraint (no CJK text);
- surveillance / CCTV night-vision;
- chalk outline / crime-scene diagram;
- blueprint / technical drawing;
- cold winter teal (Trinity season);
- Sunshine State postcard (used for v105's day half; a whole edit in it is still open);
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
| v101 | Tame Impala "The Less I Know The Better" | 117 BPM | half-beats 7–95 (0:01.9–0:24.4, 11 bars); the last half bar is the song's own intro pickup, so the loop wraps onto the first downbeat | 0:10.08, the bassline enters after the 4-bar drum intro → film burn-through |
| v102 | Ark Patrol "Let Go" | 164 BPM | half-beats 720–848 (2:11.8–2:35.2, 16 bars); the last 6 half-beats rewind the whole edit back to the start | 2:20.56, drop 2 (+31 dB) → the strike |
| v103 | Foo Fighters "Everlong" | 158 BPM | h1000–h1080 + h1096–h1152 (3:09.9–3:38.7; two riff bars spliced out) | 3:20.51, the full band returns → THE RIP (rev 4; was THE SAMPLE) |
| v104 | GLM-RST "still love you (super slowed + reverb)" (TikTok sound, screen-recorded) | 112.19 BPM (fitted to the sub-bass hits; k = sixteenth 0.13370 s, k0 = 0.042 s) | the whole 23 s clip: synth pickup + five two-bar phrases, ends on a loop boundary | 1.65 s, the sub-bass enters → THE INK DROP lands |
| v105 | Tame Impala "Dracula" | 114.99 BPM | half-beats 592–680 (2:34.6–2:57.5, 11 bars, one pass); the pre-roll is the song's own lead-in, so the loop plays through | 2:40.8 one-bar drop-out → SUNDOWN; 2:42.9 drop (+29.8 dB) → THE BAT BURST |

## 11. Communication

- Short progress lines while working. No long code in chat.
- **Final message:**
  1. what the edit is (one paragraph);
  2. what changed or what's new;
  3. what the review passes caught and fixed;
  4. the measured checkpoint numbers;
  5. a request to watch once with sound.
- Name every file path in full. Commit and push to the session's branch.
