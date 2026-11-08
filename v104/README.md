# THE PASSENGER — Dexter × GLM-RST "still love you (super slowed + reverb)" (voidfx v104, 9:16)

Studio 2. Built from the v103 FOREVER standard (`tools/new_edit.py`), with the v9 text style (keyline captions, per-letter hero titles).

**Song source:** the owner's screen recording of the TikTok sound page (`src/still_love_you_screenrec.mp4`, 23.06 s). The audio track is extracted to `src/still_love_you_rec.wav`. An earlier brief came with Michael Jackson "Smooth Criminal". It was replaced by this sound in the owner's next message; its song analysis is kept in `work/smooth_criminal_analysis/`.

**Files not available in this session:**
- **No new scene packs came with the brief.** Every uploaded pack is already in the library, so the edit uses library packs p1, p4, p5, p7, p8, p9 and p10.
- `trinity_goodbye.mp4` is listed in the catalog but isn't in `src/`.
- The rendered v4–v9 edits aren't in this session; they were reviewed through the handbook and their READMEs. FOREVER (v103) and the v101/v102 renders were available.

## Pre-render check (handbook §0 and §5a)

**1. A concept rooted in Dexter's world.** *"I like to pretend I'm alone. Completely alone."* He isn't: his Dark Passenger is the ink that seeps through every frame. It ends with his own ink shadow rising behind him as he says *"I have a dark side, too."*

**2. Set pieces (multi-stage, themed, each with its own sound), one on every phrase start:**
- **THE INK DROP (open and loop).**
  - During the synth pickup, a drop of ink forms at the top of a sheet of paper, swelling on each synth note. It lets go and falls.
  - It lands exactly on the bass entry, on the word "ALONE". A crown of ink flies out and the bloom spreads into him: the picture lives inside the ink.
  - At the end, the picture drains back into one blob, which pulls into a drop and lifts off the paper. That is the loop.
- **THE SPATTER (P3).** He pulls his face shield down. On the downbeat there's a two-frame red impact, then red ink spatter hits the lens over his already blood-spattered suit, off his face. It hangs, then the heavy drops run.
- **THE PASSENGER (P4).** "I have a **dark** side, too": the world behind him washes to paper and his ink shadow rises behind him, taller than him and swaying. Then it lunges and swallows the frame, and the next shot surfaces through thinning ink.
- **THE SILHOUETTE (P5).** He walks out of the dark (lamp-on). The world around him goes to paper and his body becomes a window into the red kill room; only his face stays.

**3. Designed text and graphics in every section.**
- **Text:** the VO caption I LIKE TO PRETEND / I'M **ALONE,** ("ALONE" lands on the bass entry), and the hero titles COMPLETELY / **ALONE.** and I HAVE A / **DARK SIDE, TOO.** (per letter, flooding red, exiting as red ink droplets).
- **Graphics:**
  - the paper and its fibres;
  - ink drifting through the shadows of every shot;
  - an ink-bled vignette;
  - ivory anamorphic flares on the gloves and the flashlight;
  - the brush strokes;
  - the camera punching on the sub-bass hits.

**4. Lyric recognition (handbook §0).**
- **What was tried:** the sound's vocal is a slowed, reverb-washed sample. Whisper on the Demucs vocal stem heard nothing. On the full mix it produced invented lines with an identical confidence on every segment (a hallucination). A web search found no published lyrics for the track or for GLM-RST.
- **So:** following the rule *text only on clearly sung or spoken words*, there are no lyric captions. The text comes from Dexter's own two lines, word-timed on the isolated voice. The picture "recognises" the music instead: every cut and set piece lands on a sub-bass hit or a phrase start.

**5. Density (handbook §0: at least 24 designed transitions per ~24 s).** The edit has 24 designed cuts in 22.97 s, plus the ink open and the ink close.
- **New ink transitions:** ink bloom, ivory brush, red brush, spatter, ink bleed, passenger reveal.
- **Approved standard pieces:** eye dive, torch blind-out, zipper, logo, shutter, lamp on, plastic wrap.
- **Motion connectors:** whip, impact, slam, light sweep, roll, tilt, whip up, strobe, face-match, film burn, smear.
- **No transition repeats** except the two brushes (ivory, then red), which are deliberately a pair.
- **Animation:** the camera punches on every sub-bass hit from P2 on, with a chromatic kick on the half-bars.

**6. Comparison with WARMPOP (v6), HIM ALL ALONG (v7), WISH YOU WELL (v8) and FOREVER (v103).**
- **Look:** v6 pastel vapor, v7 forensic noir, v8 sodium nocturne, v103 undertow. **v104 SUMI** is an ink-wash monochrome: ivory paper highlights, ink-blue blacks and only the strongest reds kept as red ink. It also unifies footage from five seasons into one look.
- **Opening:**
  - v7: an eye in a magnifier;
  - v8: a push into a rear-view mirror;
  - v103: surfacing from under water;
  - **v104:** a drop of ink on blank paper with his voice, which lands on the bass and blooms into him.
- **The big moments:**
  - v7: a plastic burst;
  - v103: a plastic rip and evidence photos;
  - **v104:** his ink shadow detaching from him, a Dark Passenger graphic that interacts with a MODNet matte of the footage, and a subject cut-out that turns his body into the kill room.
- **Loop:**
  - v7: a pupil dive;
  - v103: sinking and surfacing in the same water;
  - **v104:** the picture drains back into the same drop that opened it.
- **Weakest point of the plan and the answer:** the sound has no drums and no section change after the bass entry; it's a hypnotic loop. **Answer:** the progression is built into the edit:
  - **P1 alone:** slow, VO;
  - **P2 the ritual:** gloves, the slide, the mirror, the shield;
  - **P3 the violence:** the spatter and attacks;
  - **P4 the passenger;**
  - **P5 the fastest run.**
  Cuts tighten from 2 bars to 4–5 sixteenths, and every bass hit drives a cut, a punch or a set-piece beat.

**7. Frame rate.** 60 fps output, with every source played at its own 24p/30p cadence (`interp="hold"`). There's no optical-flow interpolation, so no warping artefacts; the graphics and transitions animate at 60.

## Song section

The whole clip is the window: it's the section TikTok's sound already selected, and its five phrases end exactly on a loop boundary.

- **Grid:** fitted to the sub-bass hits on the Demucs bass stem with a 2.7 ms mean error: **112.19 BPM**, k = one sixteenth = 0.13370 s, k0 = song 0.042 s.
- **Bass pattern:** 4-4-3-3-3-3-3-3-3-3 sixteenths per two bars.

| Song time | Edit | What happens |
|---|---|---|
| 0.04 | 0.00 (k0) | Synth pickup (dotted notes at k0, 3, 6, 9): the ink drop forms and falls; "I like to pretend I'm…" |
| 1.65 | 1.60 (k12) | **The sub-bass enters**: the drop lands, the bloom, "ALONE," |
| 5.92 | 5.88 (k44) | P2: the ritual |
| 10.20 | 10.16 (k76) | P3: THE SPATTER |
| 14.48 | 14.44 (k108) | P4: THE PASSENGER ("DARK" on the k112 hit) |
| 18.76 | 18.72 (k140) | P5: THE SILHOUETTE, the fastest run, the ink-out |
| 23.04 | 22.97 | Loop (end of the clip, on the phrase boundary) |

**Dialogue** (S1, pack p8; Demucs stems; voice-over, not shown as spoken):
- "I like to pretend I'm alone. Completely alone." (225.8–229.9; the pause between the halves is tightened so the second "ALONE" lands on the k29 hit);
- "I have a dark side, too." (296.4–299.6).

In the speech band the voice sits 8–13 dB above the music.

## Review log (before the first full render)

Each pass asked "what would make this unforgettable?", not just "what's broken?".

1. **Brushes:** the first brush read as horizontal scanlines. It's rebuilt as a visible band of ink with a wet front and a dry, bristly tail, at a diagonal. The black stroke disappeared on dark footage, so the first is ivory ink and the second red.
2. **Spatter:** it first looked like a cartoon splat over his face. It's now an organic splash on his already spattered white suit, flung left, off the face.
3. **Passenger:** the shadow was invisible (black ink on a dark wall). Now the wall behind him goes to paper as it rises. The matte included the table, which made a black wall instead of a figure, so the shadow is cut from his body only and lifted so its head and shoulders rise up-left of his.
4. **Silhouette window:** the first cut-out hid his face and then barely read. Now his face stays and his body becomes the kill room, brightened.
5. **Red skin:** warm skin leaked red on four shots; a per-shot red threshold fixes it.
6. **Text-over-face rules:** the enso ring landed around his face (too close to the rejected v7 "target ring"), so it was replaced by a lamp-on: he walks out of the dark. The v7 blood-on-the-lens drop landed on his face, so it was replaced by a film burn into the red kill room.
7. **Ink bleed:** it held about 7 fully black frames on the P4 downbeat; the blooms now leave gaps.
8. **Other replacements:** the blinds transition moiréd in mono, so it was replaced by the camera shutter. The red-lit smirk wasn't detected at 344.5 (the crop showed an arm), so it now starts on the face at 346.9.
9. **Full render 1: 9/10, not shipped.** The loop seam failed (blurred difference 18.9): frame 0 has the faint ghost of the first shot washed into the paper, but the ink drained to clean paper. Now the ink drains back onto exactly the same ghosted paper. The final shot was also lifted in exposure (target 0.46) so the ending reads.

## Checkpoint: render 2, 10/10 PASS, visual sign-off PASS (shipped)

| Check | Result |
|---|---|
| Format | 1080×1920, 60 fps, 1378 frames (22.97 s), H.264 + AAC, fast-start, 16 Mb/s cap |
| Loudness after AAC | −13.3 LUFS, true peak −4.0 dBTP |
| Clicks | 0 at the 24 cuts; loop seam clean by the QC rule |
| Loop seam picture | paper at both ends: blurred difference 0.12 |
| Faces | centred in every shot; 0 text-over-face frames. Frame 300 was checked: the detection is his knee, and the caption sits below his face. The low detections at 774–856 fall where there's no text |
| Black frames | none |
| Length | audio and video within 9.3 ms |
| Voice vs music | the voice is 8–13 dB above the music in the speech band (300 Hz–4 kHz) |

**Visual sign-off** was done on frames pulled from the encoded MP4: the whole edit every 22 frames, every cut (6 frames around each), all five set pieces frame by frame, the flagged frames and the seam.

**Not verified:** watching and listening in real time. The sound was checked by measurement only.

## Revision 2 (owner notes)

The owner: *"I really like what you did with Dexter being upside down and that transition. I would like for you to do one more pass where you add more graphics, animations and polish the overall feel of the edit"*, plus any other improvements.

1. **More of the upside-down moment.** The roll into the upside-down shot stays. The shot is a little longer (k66–72, now landing on a bass hit), and it keeps slowly turning through the hold. Rotation becomes a motif: a new **quarter-turn** transition (the red smirk rolls 90° into a rotational blur and the head-turn rolls out of it upright) replaces the smear at k126.
2. **Animation polish:**
   - a slow, breathing **camera float** on every hold (drift, a little rotation), so no frame sits dead;
   - the **beat punches** get a short radial motion blur on the strong hits;
   - **speed ramps** on the attack, the container grin, the head-turn and the police grin: fast with shutter blur into the hit, then slow;
   - the **ink-bled vignette breathes in** on every phrase start.
3. **More graphics:**
   - **ink creeps in from the paper's corners** during the opening as the drop forms (none at frame 0, so the loop still matches);
   - **ink ghost-trails** behind the motion on the attack, the container grin and the head-turn;
   - a thin **red-ink edge** on the passenger's shadow so the figure reads;
   - the **silhouette window** now shows the bright plastic kill room and its lamp (S4 p10) inside his body.
4. **Sound:**
   - soft paper foley under the opening;
   - sub hits under the phrase starts (P2, P4, P5);
   - risers into the spatter (P3) and into the finale (P5);
   - a deep spin whoosh for both rotations.

### Revision 2 checkpoint: 10/10 PASS on the first run, visual sign-off PASS

| Check | Result |
|---|---|
| Format | 1080×1920, 60 fps, 1378 frames (22.97 s), H.264 + AAC, fast-start, 16 Mb/s cap |
| Loudness after AAC | −13.3 LUFS, true peak about −4 dBTP |
| Clicks | 0 at the 24 cuts; loop seam clean by the QC rule |
| Loop seam picture | blurred difference 0.15 |
| Faces | centred in every shot; 0 text-over-face frames. Frame 300 (his knee) and frame 964 (the title sits about 400 px below his chin; YuNet's box runs long) were checked on frames |
| Black or frozen frames | none |
| Length | audio and video within 9.3 ms |

**Visual sign-off** was done on frames pulled from the encoded MP4: the opening seep, the roll and the turning upside-down hold, the speed-ramped trails, the passenger's red edge, the quarter-turn, the silhouette window, the ink-out and the seam.

**Not verified:** watching and listening in real time.

## Revision 3 (owner notes)

*"Further detail and improve the dark side animation to be more professional and visually appealing. Add more animations, transitions and graphics towards the beginning of the edit to get rid of the dead space."*

**THE PASSENGER, rebuilt as a lit set piece:**
1. **The light:** just before "DARK", a hard light comes on behind him (a lamp click). The wall behind him washes to lit paper, brightest where the light hits and falling off into the corners, and the light catches the edge of him.
2. **The shadow:** his silhouette (MODNet, his body only) is thrown onto the wall beside him. It has a crisp, organic ink edge and a thin red-ink rim, leans slightly, sways and breathes on the bass hits.
3. **The smoke:** animated ink smoke rises off the top of the shadow.
4. **The embers:** two red eyes open in the shadow's head on "DARK" (an ember-ignite sound and a sub drop under the word). They're masked behind his body, so they never sit on his face.
5. **The camera:** a slow push-in with a 2.4° dutch tilt while it rises.
6. **The lunge:** the shadow turns to the lens and pans to centre as it zooms. Both eyes rush at the camera with motion blur as the ink swallows the frame, and the red smirk surfaces out of the ink.

**The opening (0–5.9 s): no more dead space.**
1. **The pickup draws itself:** an ink sketch of him (line art from the first shot) is drawn stroke by stroke on the paper, one stroke group per synth note, with pen and brush scratches. Ink creeps in from the corners and the drop forms, falls and blooms on the bass. Frame 0 is still bare, so the loop matches.
2. **Two more cuts and a new transition:**
   - the dock walk is trimmed to one bar with a speed ramp;
   - a **page turn** (the frame turns over like a sketchbook page, with paper on its back and a cast shadow; paper-flip sound) reveals a new S4 night stare;
   - a new **"shh"** insert (S1, a finger to his lips) closes the phrase.
   The opening now cuts at k12, 20, 26, 35, 41 and 44 (was 12, 28, 38, 44).
3. **Graphics:**
   - floating **ink motes** in depth over the opening shots;
   - an **ivory brush swash** painted behind the red "ALONE." as it lands (red letters on white paint);
   - stronger beat punches on the opening's bass hits.

### Revision 3 checkpoint: 10/10 PASS on the first run, visual sign-off PASS

| Check | Result |
|---|---|
| Format | 1080×1920, 60 fps, 1378 frames (22.97 s), H.264 + AAC, fast-start, 16 Mb/s cap |
| Loudness after AAC | −13.3 LUFS, true peak −4.1 dBTP |
| Clicks | 0 at the 26 cuts; loop seam clean by the QC rule |
| Loop seam picture | blurred difference 0.14 (frame 0 is still bare paper) |
| Faces | centred in every shot; 0 text-over-face frames. Frame 964 was checked: the title sits about 400 px below his chin |
| Black or frozen frames | none |
| Length | audio and video within 9.3 ms |

**Visual sign-off** was done on frames pulled from the encoded MP4: the whole opening (the sketch drawing itself, the page turn, the new stare and shh shots, the swash) and THE PASSENGER frame by frame (the light coming on, the shadow, the embers, the lunge, the reveal).

**Not verified:** watching and listening in real time.

## Approved as a standard (after rev 3)

The owner: *"I really like this edit and would like for it to be a standard. Only gripe I have is that one span of the edit had some headspace that definitely could have had an edit or a cool transition. Do not change anything about the edit just keep for future reference."*

- **The edit is unchanged.** It's written into CLAUDE.md, handbook §0/§1 and TOOLKIT.md as the newest standard, and `tools/new_edit.py` now scaffolds from it. A scaffolded test edit rendered pixel-identical to v104.
- **The gripe is recorded as a rule: no headspace.** No span longer than about a second without a cut, a transition or a designed beat. The owner didn't say which span. The longest here, all candidates for next time:
  - the pickup, 1.60 s;
  - the dark-side shot, 1.60 s;
  - the final shot, 1.31 s;
  - the floor shot, 1.20 s;
  - the dock, spatter and silhouette shots, 1.07 s each.
