# Edit report: v107 ALL CAPS (Dexter × Madvillain "All Caps")

> From the **Dexter studio** for the **Flash studio**. Apply sections 7 and 8 to your `CLAUDE.md`, handbook and toolkit, then confirm what changed.
> Code: `v107/` on voidfx `dev/pipeline-v2`, and a copy in Drift-Master `voidfx-studio-kit/repo/v107/`.

## 1. Verdict
**Approved as a standard** after 4 rounds. The owner: *"I like this edit make it a standard"*.

It is now the newest Dexter standard, and **Dexter edits scaffold from it**: `tools/new_edit.py N SLUG "TITLE" --base v107`, which is now the default when the slug or title mentions Dexter. It is the reference for:
- a concept taken from the song's hook word and carried by one object;
- a focal set piece that turns into a real object in the footage (the letterpress strip becomes the real banner);
- a loop built from the edit's own particles (the parade's confetti spells his name);
- what the owner rejects. The 3-second slot took four tries, and the final answer was a clean cut (§5).

## 2. The edit
- **Show × song:** Dexter × Madvillain "All Caps" (2:14).
  - **Tempo:** 87.50 BPM, fitted over 8 bars on the Demucs drum stem.
  - The automatic map read 175.6; the drum autocorrelation read 117.4, which is the dotted pattern.
  - The kick falls on every beat from 22.5166 s.
- **Section used:** half-beats 176 → 240 (8 bars, 60.92 → 82.86 s, 21.94 s): the end of verse 1 and the beat break after it.
  - The bass drops out in the last bar and comes back on bar 1, so the wrap lands like a drop.
- **Concept: ALL CAPS.** *"Just remember ALL CAPS when you spell the man name."* The press only knows him as the BAY HARBOR BUTCHER; the song spells his name.
  - The verse is his work.
  - The newspaper prints him under the BUTCHER headline.
  - On "when you spell the man name", letterpress type stamps D-E-X-T-E-R.
  - The strip flies into the sky and becomes the real banner the plane tows over Miami, WE ♥ DEXTER (the S1 finale fantasy, real footage).
  - The crowd's confetti spells his name again for the loop.
- **Look: TABLOID.**
  - Newsprint-cream highlights, ink blacks and slate blues.
  - One spot red: blood, the heart, the BUTCHER headline.
  - A misregistered red plate, paper grain and a fine screen in the shadows.
  - Red-lit skin is kept out of the spot red per shot (`redthr`).
- **Length / format:** 21.94 s, 1080×1920, 60 fps; loops.
- **Sources:** all 720p in a 60 fps container, restored 2× with `tools/sr_prep.py` (the v12 engine), flow on the restored frames.
  - `dexter_s2_b.mp4` (S2, 2.07 Mb/s)
  - `dexter_s2_a.mp4` (S2, 1.98 Mb/s)
  - `dexter_mix_b.mp4` (S1–S3 mix, 1.72 Mb/s)
- **Text:**
  - Every clearly sung line is captioned in the v9 style: 10 two-line blocks on the sung onsets (Whisper large-v3 on the vocal stem, snapped to the stem). "BUGABOO" is the published word.
  - One designed title: the letterpress DEXTER.

## 3. Creative process
- **How the concept was found:**
  - The hook line names the idea ("ALL CAPS when you spell the man name").
  - S2's Bay Harbor Butcher arc gives the press.
  - The parade pack contains the real WE ♥ DEXTER banner (S1 finale), so the graphic can become footage.
- **Engine:** v12 (v11 BOP + v12), not the Dexter base v105, because v105 has no restored-source sampler. That sampler is the fix for the owner's v105 gripe, *"the quality of some of the clips."* It was flagged to the owner as a choice they could overrule, and they approved the edit built on it.
- **Structure, in timeline order:**
  1. **0–1.37 s, the stare.** Frame 0 is where the loop lands.
  2. **1.37 s, plastic rip** → the kill table.
  3. **2.75 s, a clean cut on the downbeat** → "shh", with the beat camera punching the cut (see §4 for the four tries at this slot).
  4. **3.6–3.9 s, PAGE TURN** → the blood lab.
  5. **4.8 s, HOT MOLASSES** (a viscous blood pour) → the hazmat suit soaked in blood.
  6. **5.8 s, impact** → the robot step motion (`robo()` tmap) on "do it like the robot".
  7. **6.85 s, HEADSPIN** → his face from directly overhead on the pillow, centred.
  8. **7.55 s, whip** → the grin.
  9. **8.2–9.6 s, THE FRONT PAGE** (it spins in, lands, and we dive into his photo) → the con.
  10. **10.3–14.4 s, the Doakes run:** whip → Doakes, slam → the cage, whip → "look at you", zipper → shame, impact → "just remember".
  11. **14.4 s, slam → the parade.** On "ALL CAPS" the strip slaps on, and D-E-X-T-E-R is stamped (focal).
  12. **16.45 s, the strip flies into the sky** and morphs onto the banner's own DEXTER (`banner_match`).
  13. **17.5 s, the confetti pops** → he laughs.
  14. **18.5 s, dolly** → the crowd.
  15. **19.2 s, smear** → he walks through it.
  16. **20.0–21.9 s, THE MASSES SPELL HIS NAME** (the loop).
- **Set pieces:**
  - HOT MOLASSES;
  - HEADSPIN;
  - THE FRONT PAGE;
  - ALL CAPS, focal: the stamp, then the banner;
  - the confetti pop behind him;
  - THE MASSES SPELL HIS NAME (the loop).
- **Sound:**
  - About 28 placed effects in 21.9 s.
  - Layered only at the set pieces: the pour, the spin, the page, six letterpress hits, the banner.
  - None on beat moments, and nothing in the loop bar except one paper flutter as the name gathers and one whoosh on the burst.
  - The music plays the window straight.
  - A 96-sample sin² fade at both ends of the mix removes the click from the AAC encoder's tail padding.
- **The loop:**
  1. The confetti swirls in from both sides at chest height, never across his face.
  2. It forms a 1000 px DEXTER from about 1,050 lit, fluttering paper pieces while the parade dims and softens.
  3. The name holds through the bass drop-out bar.
  4. On the bar line it bursts toward the lens and down as frame 0 dissolves in underneath.
  5. The last frame is frame 0's picture. Seam 0.10.

## 4. Revision history
| Rev | Owner's note | What changed | Why |
|---|---|---|---|
| 1 | (first delivery) | — | — |
| 2 | *"the transition that occurs at 3 seconds in, I don't really like that. I like to replace it with a custom graphic into a really cool transition. And then the head spin transition, I don't really like it because the final shot doesn't have a centered shot of Dexter … I also don't like that you reuse the same clip around the 17-second mark … and the 19-second mark … smooth out the ending part. And I don't really like how low effort the loop is."* | The press flash became SPECIAL REPORT, a CRT TV in a dark room with a chyron and a channel flip. The headspin lands on a centred overhead face and turns about it. One wide walk replaced the reused close-up. The beat camera rests through the break, with fewer cuts at the end. The loop became THE MASSES SPELL HIS NAME. | Every note applied in one pass. |
| 3 | *"I don't like the transition at 3 seconds with the black bars. I also don't like how slow it writes dexters name in black near the end of the edit. Can you make it line up so it's not too fast and not too slow. Additionally, I want you to implement one new really unique graphic/animation that you have not tried to create before."* | The TV became SPATTER ANALYSIS, a POINT OF ORIGIN graphic that grew into a RORSCHACH transition. DEXTER moved onto an even 16th-note grid, with each letter landing on its hit. | The TV's dark room read as black bars. The stamp had followed uneven word onsets (gaps of 0.19–0.33 s). |
| 4 | *"Can you get rid of the point of origin graphic/transition the remove and replace the black box transition from the 3 and a half second mark."* | Both POINT OF ORIGIN pieces were removed, leaving a clean cut on the downbeat. The redaction boxes at 3.77 s became a newspaper PAGE TURN, rolled over a cylinder. Review also fixed a 2–3 px cyan/magenta edge fringe on every beat hit. | The POINT OF ORIGIN broke a recorded dislike: **converging strings and a target ring where his face appears** (in `preferences.json` "banned"). The redaction boxes were black occluders. |
| — | *"I like this edit make it a standard"* | — | — |

## 5. What made it good (and what didn't)
**Good:**
- **One concept and one object.** The name is printed, stamped, flown into the sky as the real banner, and spelled by the crowd for the loop. Picture, text and loop all say ALL CAPS.
- **Physical, kinetic transitions survived every round:** plastic rip, hot molasses, headspin (once the landing was centred), the front page, the stamp, the banner match, the confetti and the page turn. The owner never asked to change one of these.
- **Spelling the name on a rhythm grid.** Ten frames a letter, each landing on its hit with the sound on the same frame: *"not too fast and not too slow"*.
- **A loop built from the edit's own material:** the parade's confetti forms the name, holds through the drop-out, and bursts into frame 0 (seam 0.10).
- **Clip quality:** restored sources and flow (the v12 engine), with zoom ≤ 1.07 everywhere. No clip-quality note this time (the v105 gripe).

**Weak, from the four tries at the 3 s slot:**
- **Rev 1, press flash:** a halftone newspaper-photo flash. The owner disliked it.
- **Rev 2, SPECIAL REPORT TV:** a 860×645 screen in a dark room reads as **black bars** above and below the picture.
- **Rev 3, SPATTER ANALYSIS → RORSCHACH:** strings converging on a ringed crosshair where his face then appears. That is the banned *"gimmick on the face (target rings, converging strings)"*. **The studio should have caught it at the design stage;** it was already in the banned list.
- **The redaction boxes** (an engine transition): read as a **black box transition**.
- **The answer that was approved:** a clean cut on the downbeat with the beat camera's punch. The owner prefers no transition to a graphic overlay that tries too hard.
- **Name spelled on the sung words:** uneven gaps (0.19–0.33 s) made it feel slow, even though each letter landed on its word.

## 6. Caught by review
- **Loop click:** the AAC tail pads about 2 ms of silence, and frame 0 starts on a loud kick, so the seam stepped 0.43–0.61. Fixed with a 96-sample sin² fade at both ends of the mix; seam step now 0.0005.
- **Tight close-ups** put the face in the caption band or past the frame edge. They were swapped for wider moments; the grin's zoom is held at 1.0, and "JUST REMEMBER" was lowered.
- **24p judder** where flow was refused (the engine held frames). `src_weights` now blends the two frames when the frame difference is over 14 or the colour change is over 6.
- **Confetti covered his face.** It now goes behind his matte and starts in the sky.
- **The banner sky** reflected the banner above and below. It is now extended from the source's own top and bottom colours.
- **Red light on skin read as blood.** Fixed with a per-shot red threshold (`redthr`).
- **Molasses looked flat, like rain.** Rebuilt with undulations, gloss, absorption by thickness and a draining meniscus.
- **The TV exit** switched the screen vignette off in one frame (top-of-frame luma 50 → 80). It now fades with the letterbox. *(The TV was later removed.)*
- **The grin's centring flag:** an extreme close-up wider than the frame is boxed past the edge by the detector, but only inside the whip and the front-page fly-in. QC's centring check now lists flags inside designed transition windows without counting them, using the windows faceqc already leaves out.
- **SPATTER ANALYSIS and RORSCHACH on stills:**
  - drops, strings and tag were too small at phone size (scaled 1.4–1.7×);
  - the blot's wings ran off the frame (reshaped into a card);
  - the unfolding card went edge-on as a dark line through his nose (it now fades out before 90°).
- **Edge fringe on every beat hit:** the beat camera's colour split used `np.roll`, so the shifted channels wrapped and left a 2–3 px cyan line on the left edge and a magenta line on the right, for a frame or two. It had been there since rev 1, and the Flash engine has the same `rgb_split`. v107's `rgb_split` repeats the edge pixels instead.

## 7. Rules to adopt
1. **No black occluders as transitions** *(new)*. Letterbox bars, redaction boxes, and a screen floating in a dark room all read as "black bars" or a "black box". A cover must be content: paper, liquid, light, or the picture itself. Evidence: rev 3 *"the transition at 3 seconds with the black bars"*; rev 4 *"the black box transition"*.
2. **No gimmick on the face, including graphics that point at where a face will appear** *(confirmed, sharpened)*. Converging lines, crosshairs and target rings are banned even when the face arrives a beat later. **Read the banned list before designing any graphic.** Evidence: rev 4 *"get rid of the point of origin graphic/transition"*.
3. **When a slot has failed twice, stop adding graphic concepts** *(new)*. Use a kinetic, physical transition (rip, pour, spin, page, whip), or a clean cut on the downbeat with the beat camera's punch. Evidence: the 3 s slot was rejected as press flash, then TV, then POINT OF ORIGIN; the approved version is a clean downbeat cut.
4. **Spell-outs and letter-by-letter titles run on an even rhythm grid, landing on the hit** *(new)*. At about 90 BPM that's a 16th note, about 10 frames a letter. The letter comes down in the frames before the hit and lands on it, with its sound on the same frame. Uneven sung-word onsets read as slow. Evidence: rev 3 *"how slow it writes dexters name … not too fast and not too slow"*, then approval.
5. **A spin transition lands on a centred face and decelerates about it** *(new)*. The second half rotates about the incoming face's centre (`face_scr`), so it reads as the camera turning above his head. Evidence: rev 2 *"the final shot doesn't have a centered shot of Dexter"*.
6. **Never reuse a clip in one edit** *(confirmed)*. Evidence: rev 2 *"you reuse the same clip around the 17-second mark … and the 19-second mark"*.
7. **Smooth endings** *(new)*. Through a beat break and the ending, the beat camera rests and the cuts get fewer and longer (a dolly, a soft smear). Evidence: rev 2 *"smooth out the ending part"*.
8. **The loop is a creative set piece, not "the last shot, then the first shot"** *(confirmed, v105 rule 3)*. Evidence: rev 2 *"the loop is pretty low effort … it kind of just does one shot and then does the shot from the beginning"*.
9. **Dexter edits scaffold from v107** *(new, engine)*: `new_edit.py --base v107`, the v12 engine plus the v107 toolkit. Re-splice an edited toolkit with `tools/splice_section.py N vN/work/fxN.py --replace`. Evidence: the owner approved v107 on the v12 engine, and the v105 clip-quality gripe didn't return.
10. **QC: the beat-hit colour split clamps at the frame edge** *(new, both engines)*. `np.roll` wraps it into a cyan/magenta edge line. Port v107's `rgb_split` (or `_shift_edge`) into v11/v12.
11. **QC: face-centring flags inside designed transition windows are listed, not counted** *(new)*. This is the same window set faceqc already leaves out. Extreme close-ups wider than the frame are boxed past the edge by the detector.

## 8. Techniques to reuse
All functions are in `v107/work/fx107.py`, spliced above the speed section of `render107.py`, and every one is in a `--base v107` scaffold.

- **TABLOID grade and finish** (`look="tabloid"`, `grade`, `finish107`):
  - grade: a `tone_lut` curve; a red mask above a per-shot `redthr` keeps spot red; saturation 0.30 + 0.2·skin + 0.85·red; a paper tint in the highlights;
  - finish: a red-plate ghost offset by (3, 2) px, a fine shadow screen, paper grain and a vignette.
- **HOT MOLASSES** (`tin="molasses"`, 36 / 24 frames). A viscous sheet pours down the lens:
  - a fingered leading edge with a rounded bead, and broad undulations sliding down;
  - it refracts the shot under it, absorbs light by thickness, and has a glossy highlight from its blurred-height gradient;
  - it drains from the top with a meniscus, revealing the next shot.
  - Sound: a gloopy pour, a glug on the cut, a drip.
- **HEADSPIN** (`tin="headspin"`, 20 / 24):
  - two full turns on a smoothstep curve, zoom 1 + 0.28·sin(πq);
  - motion blur from several rotated samples spread by the angular speed, plus a radial blur;
  - the outgoing half turns about the frame centre, and the incoming half turns about **the incoming face's centre**, landing at 0°.
  - Sound: a circling swirl, a whoom, a sub.
- **THE FRONT PAGE** (`tin="frontpage"`, 82 / 28; `page_layers`, `page_with_photo`):
  - the MIAMI GAZETTE built from text masks: masthead, BAY HARBOR in ink, BUTCHER in spot red, a deck line, body columns;
  - his photo printed into the photo box as a halftone, with a caption;
  - the page spins in, lands with a slap and settles; we dive into the photo, and its dots shrink into the next shot.
- **ALL CAPS stamp** (`style="stamp"` in `TEXT`; `strip_tex`, `strip_canvas`, `text_stamp`):
  - a torn newsprint strip slaps on with "CAPS";
  - each letter comes down over 3 frames (scale 1.6 → 1 with blur) and lands on its grid hit (16ths, e44 → e46.5), with ink spread at the hit and an emboss on the paper;
  - the strip shakes on every hit; at the cut it flies to `banner_target()` and morphs onto the real banner's DEXTER.
  - Sound: a paper slap, six letterpress hits (scrape, knock, a low body, a small rattle).
- **Banner shot** (`banner_frame`): a crop tracking the banner at only 1.2×, with the sky extended from the source's own top and bottom colours, so WE ♥ DEXTER fits whole in 9:16.
- **Confetti** (`conf_set`, `draw_confetti`, `confetti_pop`, `pop_behind`): lit paper pieces in the press palette with flutter and depth of field. They burst in the sky, then carry on behind his matte.
- **THE MASSES SPELL HIS NAME** (`tout="name_loop"`; `name_targets`, `draw_pieces`, `name_loop`). The loop:
  1. 1,050 targets are sampled inside a DEXTER mask (Inter Black, squeezed to 1000 px, centred at y 1110), mostly cream and red pieces sized 18–32 px.
  2. They enter from both sides at chest height (start x = W/2 ± 0.62–1.05 W), staggered, with a curl.
  3. While the name holds, the plate behind dims and softens.
  4. The burst flies toward the lens and down as `frame0_plate()` dissolves in; the last frame is frame 0.
  - Sound: one flutter as it gathers, one whoosh on the burst.
- **PAGE TURN** (`tin="page_turn107"`, 14 / 12). A true roll; v104's was a flat fold. Set-up:
  - the turn travels along d (from the bottom-right corner to the top-left); s is distance along d, c is the roll line, R the radius (60 → 130 px);
  - each screen pixel samples the page at material coordinate σ, with source point = pixel + (σ − s)·d.

  The layers at each pixel:
  - **flat page** (s > c): the front;
  - **rising quarter** (c − R ≤ s ≤ c): the front at σ = c − R·asin((c − s)/R), shaded by cos θ;
  - **top of the roll:** the back at θ₂ = π − θ₁, drawn on top;
  - **turned part lying flat** (s > c): the back at σ = 2c − πR − s;
  - **uncovered** (s < c − R): the next shot, with the roll's shadow exp(−distance / 46) · 0.55.

  The back is newsprint: three columns of body type, crossheads and rules, with the picture faintly showing through, mirrored. Sound: one paper flip.
- **Edge-clamped colour split** (`_shift_edge`, `rgb_split`): shift each channel with the edge column repeated instead of `np.roll`.
- **Tools:**
  - `new_edit.py --base v107`;
  - `splice_section.py N SECTION.py --replace`;
  - `qc107.py` centring with transition windows (`_tr_window`).
- **Built and working but rejected in this edit** (still in `fx107.py`). Reuse them only with the lessons in §5 and §7.
  - `press_flash`;
  - `broadcast` (the TV): avoid the black room around it;
  - `spatter_fx`: never converge on a face;
  - `rorschach`: the mirrored-face bloom and the unfolding card.

## 9. Measured (final, rev 4)
- **QC:** 11/11 on the encode.
- **Loudness:** −13.0 LUFS, true peak −3.5 dBTP after AAC.
- **Loop seam:** blurred difference 0.10 (the gate is ≤ 1); the audio seam step is 0.0005.
- **Cuts:** 18 cuts, 0 suspicious; no audio clicks at any cut.
- **Transitions:** 17 designed transitions plus the loop set piece, and 1 clean downbeat cut.
- **Flashes:** 0 events over a mean luma of 110; no white-outs.
- **Faces:**
  - text over faces: 2 single frames, both inside transitions (the headspin at frame 422, the whip at frame 620);
  - faces vs effects: 13 flags in 3 runs. Doakes's extreme close-up, frames 626–644, ≤ 4.4 % of the face box; a cage beat hit at 700; the loop burst at 1290–1292, as frame 0 dissolves in.
- **Glitch audit:** every frame-to-frame jump is a cut, a beat hit or a designed transition.
- **Dead spans:** none of 0.5 s or more.
- **Sharpness:** four shots flagged SOFT (hazmat, robot, cage, crowd). All are 720p, restored, with zoom ≤ 1.07.
- **Effort:** 4 rounds, 9 full renders at about 280 s each (42 min of render, 21 min of QC).
