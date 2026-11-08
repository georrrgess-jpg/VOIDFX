# Edit report: v106 WONDERWALL (The Flash × Oasis "Wonderwall")

> From the **Dexter studio** for the **Flash studio**. This is a Flash edit. The owner asked for it in the Dexter chat as a one-off (*"Creating a flash edit in here was an error on my part and this will not regularly occur"*), so it carries the Dexter studio's number but was built on **your v11 engine** (`tools/new_edit.py 106 … --base v11`) on the shared `dev/pipeline-v2`. The code is all in `v106/` there (`edl106.py`, `fx106.py` spliced above the speed section of `render106.py`, `audio106.py`, `qc106.py`, `README.md`). Apply sections 7 and 8 to your `CLAUDE.md`, handbook and toolkit, then confirm what changed.

## 1. Verdict
**Approved as a standard** after 3 rounds. The owner: *"I like this edit make it a standard"*.

It is a Flash standard next to v11 BOP and v10 LET IT HAPPEN. It is the reference for four things:
- **A story concept taken from a lyric line and the show's own history.**
- **Restraint in sound design.** The owner cut half the effects and approved the result.
- **A loop that lands exactly and keeps moving across the wrap.**
- **A measured hunt for dead spans and pops before delivery.**

The scaffold bases stay as agreed (Flash edits from v11, Dexter edits from v105). Whether the next Flash scaffold should start from v106's engine is the owner's call (see §7, note at the end).

The owner's brief, verbatim: *"I would like for you to create a marvelous flash edit using the attached audio and your best highest quality scene packs. I would like for you to try to utilize the audio attached. I want this to be the highest quality edit you have produced and to include many custom elements such as custom animations, creative custom graphics etc. Please ensure this edit is made with quality and efficiency. Please ensure this edit include cool creative and unique transitions."* Then: *"Just complete it to the best of your ability and if it comes out bad then it's no big deal."*

## 2. The edit
- **Show × song:** The Flash × Oasis "Wonderwall".
  - **Tempo:** 87.02 BPM, fitted on the Demucs drum stem.
  - **The automatic map was wrong:** it locked to 116 BPM, which is 4/3 of the real tempo, on the swung strum.
  - **Grid:** half-beat P = 0.34475 s, offset 0.2889 s.
- **Section used:** half-beats 456–520, which is bars 57–65 (157.50 → 179.56 s, 22.06 s): the second chorus.
  - The lines: "I said maybe / you're gonna be the one that saves me / and after all / you're my wonderwall".
  - Bar 65 starts chorus 3 exactly the way bar 57 starts chorus 2, so the loop is musically exact. There is no tape stop or rewind; the window simply wraps.
- **Concept:** *"Maybe you're gonna be the one that saves me."*
  - In the S3 finale, Barry walks into the Speed Force to pay for Flashpoint while Iris watches him go. In the S4 premiere, she is the one who brings him back.
  - So the edit opens inside the Speed Force. Her tear carries his goodbye, he tears out in gold on "saves", the WONDERWALL rises and bursts, and he walks back into the Speed Force onto frame 0.
- **Look:** WONDER.
  - Colour: golden-hour amber light against Speed Force cobalt, with milky lifted blacks.
  - Halation: red-orange on the highlights, kept off faces with an ellipse mask.
  - Grain: 0.010.
  - Method: a single fast table grade (`tone_lut`), with the colour applied on contiguous planes.
- **Length / format:** 22.06 s (1,324 frames), 1080×1920, 60 fps; loops in picture and sound.
- **Sources:** all four packs are 1280×720 and all were restored with `sr_prep`, 887 source frames in total.

  | Key | Pack | Cadence | Bitrate |
  |---|---|---|---|
  | `fh` | `flash_all_hq.mp4` (all seasons) | 60 fps container, mostly 24p content | 2.20 Mb/s |
  | `f3` | `flash_s3_30.mp4` (S3) | 30 fps | 1.22 Mb/s |
  | `f5` | `flash_s5_24.mp4` (S5) | 23.976 fps | 1.37 Mb/s |
  | `fz` | `flash_blitz.mp4` | 60 fps | 2.06 Mb/s |

  The `f3` Speed Force shot flashes pink-orange at 134.37–134.47 s; see §6.
- **Text:**
  - Every clearly sung word is captioned on its onset in the v9 construction, with gold emphasis words (MAYBE, ONE, SAVES, ALL).
  - The word times came from Whisper large-v3 on the vocal stem and were each checked against the stem's envelope. The small model had put "I said maybe" 3.4 s early.
  - There is one designed title, WONDERWALL, on the held word.

## 3. Creative process
- **How the concept was found.** The chorus line "you're gonna be the one that saves me" already describes the S3→S4 arc: Iris is the one who saves him from the Speed Force. "Wonderwall" became a literal object, a wall of glowing tiles cut from the edit's own frames, which he breaks through on the word.
- **Structure** (rev 3 times):
  1. **0.00 "I said maybe".** Inside the Speed Force (`f3` 133.00): Barry in the cobalt mist, looking back over his shoulder. The mist drifts behind his matte, and a cold flicker sits in the mist on the half bar.
  2. **2.07 `mist_swirl` → his eyes, gold lightning in them.** Then **3.45 `strobe_echo` → the first velocity run.**
  3. **4.48 "you're gonna be": `lightning_rod`.** A bolt strikes beside Iris's face and the shot burns open onto her in tears. The beat camera rests from here to 6.89.
  4. **4.87–5.86 TEAR LENS** (rev 2/3, §8). Her tear holds Barry's goodbye and falls through onto him on "BE". His goodbye (the S3 farewell, the reverse shot) carries "the one that".
  5. **6.89 "SAVES": `clash106`.** He tears out in gold.
  6. **7.58–11.03, the instrumental run:** `lightstreak`, `phase`, `speedforce_in`, `bolt_trace`. Velocity ramps run on every beat (burst, then 0.3× flow), plus the beat camera.
  7. **11.03 "and after all": `whirlwind` → he looks up**, and THE WONDERWALL rises behind his matte, tile by tile. Then `emblem_flash`, `dolly` and `lichtenberg`.
  8. **14.48 "you're my".** `whip` → arms open, `strobe` → the eyes, then `perimeter` → the charge-up. The wall's mortar cracks with lightning.
  9. **16.55 "WONDERWALL": the focal burst.** The WONDERWALL title is struck letter by letter over the 1.52 s sung word.
  10. **18.62 `light_leak` → the smile.**
  11. **20.00 `mist_swirl` → he turns and walks back into the Speed Force.** `loop_mist` then dissolves into frame 0.
- **Set pieces:**
  - **The lightning rod:** a leader flicker, the strike beside the face, a burn-open outward from the bolt with an ember rim.
  - **The tear** (§8).
  - **The wall:** it rises, breathes on the beat, then cracks.
  - **THE WONDERWALL burst** (the focal piece): the frame becomes the wall, trembles, then bursts toward the camera, and he walks out through gold light.
  - **The loop mist** (§8).
- **Type:** the v9 captions, plus one title that is forged from light letter by letter and phases out as vibrating ghosts.
- **Sound** (after rev 2): only the structural hits.
  - **Kept:** the lightning strike (crackle, zap, thunder, impact); the clash; the light streaks; phase; the Speed Force rush; the whirlwind; the dolly; the Lichtenberg; the whip; the perimeter; the wall's stone grind; the charge hum; the burst (rumble, crack, impact, sub, thunder, stone-and-glass shatter, whoosh); and the tear.
  - **Mix:** effects lifted +10 dB against the loud master; the music ducks 3 dB under the three biggest hits.
  - **After the burst:** only the music.
- **Loop:** the mist rolls over the lens while he walks into the Speed Force, and clears on frame 0's own picture. Sound: the music wraps from bar 65 into bar 57.

## 4. Revision history
| Rev | Owner's note | What changed | Why |
|---|---|---|---|
| 1 | (first delivery) | — | — |
| 2 | *"I would like for you to remove like half of the sound effects mostly the tedious annoying ones like the emblem shine and the few near the end . I would also like for you to do one more polish smooth over the animations make sure the loop is seemless and I would like for you to identify one space where these isn't anything happening and add a custom unique graphic into a cool transition."* | **Sound:** 14 of 28 sound moments cut (details below). **Smoothing:** five 24p held shots now use flow; mist transitions are exactly clear at their ends; tile tremble is a smooth shiver; mist drifts sub-pixel and never wraps; mist lightning kept to the frame edges. **Loop:** the picture under the mist now dissolves into frame 0's, with the mist behind him rendered at the wrap's virtual frames; the last shot starts after the source's colour flicker. **Dead span:** the Iris hold (4.8–6.5 s, the stillest span by measurement) became Iris → TEAR LENS → Barry's goodbye. | Every one of these was found by measurement (§6): a frame-difference pop list, a per-shot cadence check and a per-beat activity table. |
| 3 | *"can you slow down the tear drop transition so it's more visible?"* | The tear now runs 1.0 s instead of 0.6 s: 0.4 s gathering with Barry visible inside, 0.15 s hanging and swelling, 0.45 s falling. The settle after the cut went from 0.30 to 0.43 s. To make room, the cut onto Barry moved one half-beat later onto the sung "BE", and the clash moved one half-beat later onto the sung "SAVES" (it had been 0.43 s early). | A designed graphic needs time to read at phone size, and moving cuts to the next sung word kept them on lyrics. |

The 14 sound moments cut in rev 2 were:
- the emblem shine, and every other shimmer or chime;
- everything after the burst: the light-leak chime, the mist into the last shot, ten letter zaps on the title, the loop swells, and both Speed Force air beds;
- the strobe-echo stutter, the bolt-trace crackle and the eyes-close-up strobe zaps;
- a swish on every camera punch;
- the wall's eleven row ticks, its two-second crack bed, the aura hit and the remnant whooshes;
- the whine in the Speed Force rush.

Verdict after rev 3: *"I like this edit make it a standard"*.

## 5. What made it good (or bad)
- **The concept is a story, not a motif.** The lyric line maps onto a real arc in the show (S3 finale → S4 premiere), so every set piece is a beat of that story: into the Speed Force, her tear, he is saved, the wall, back into the Speed Force. The tear works because it carries the reverse shot. Barry's goodbye sits inside Iris's tear, and the next shot is him.
- **The focal piece is made of the edit itself.** The WONDERWALL tiles are frames from the edit's own sources, and the burst turns the current frame into the wall. It reads as the payoff of the wall that rose on "and after all", not as a library effect.
- **Fewer sounds was better.** The owner approved after half the effects went. What remains is a strike, a clash, a run, the wall and the burst. The ending is just Liam's held "wonderwall" with the loop wrapping on the music. Rev 1 had followed rule 7 (push effects until none are buried) and put a sound on every camera punch, letter and minor transition; that read as "tedious".
- **Measuring rather than guessing found everything rev 2 fixed.** A per-beat activity table found the dead span, and a pop list found six real defects, three of them invisible on stills (§6).
- **What was weaker:**
  - Source sharpness: nine shots are flagged SOFT by the tool. They are 720p packs, restored, with zoom ≤ 1.08; the flags are within 0.01 of the threshold.
  - Three single-frame flashes peak over 110 mean luma (§9).

## 6. Caught by review
**Rev 1 (before the first delivery):**
- **Tempo:** the automatic beat map locked to 116 BPM on the strum. The drum stem gave 87.02, the real tempo.
- **Lyrics:** Whisper's small model put "I said maybe" 3.4 s early. Fixed with large-v3 plus the vocal envelope.
- **Source leaks:** three ranges crossed into neighbouring source shots (pov, city, through); found by `check_sources.py`.
- **The mist:** it looked flat and opaque. Rebuilt with refraction, soft fractal edges, luminous colour and at most 88% cover.
- **The clash:** sparks crossed his face. `clash106` puts the collision below the face and masks the sparks.
- **The frame-as-wall:** it read as graph paper. Fixed with a running bond and bevels.
- **The burst:** slow and muddy. Made faster, with brighter tile rims.
- **Time particles:** left speckle. Replaced with the light streaks.
- **Effects mix:** buried 20–25 dB under the master. Fixed with +10 dB and a 3 dB duck.
- **Text over faces:** fixed by splitting a caption over the close-up, letting QC honour a caption's `from`, and lowering the title off his chin.
- **Halation and the wall's light wrap:** both reached his face; kept off the face box.
- **Loop seam:** it measured 2.51 after the face mask. The last frames now use frame 0's own finish (0.11).

**Rev 2 (from the measured pop list on the rev 1 encode).** The test: a frame-to-frame mean difference more than 3× the local median plus 2 that isn't a cut or a designed flash.
- **The loop switched the picture under the mist in one frame** (a jump of 25.8 at 21.4 s) and froze the mist behind him. Fixed with a dissolve under the thickest mist, plus virtual frames.
- **Both mist transitions popped at their ends** (29.1 at 20.27 s): the coverage formula left the corners covered at u = 0. The offset is now `1.22 − 1.55u`, which is exactly 0 at 0 and full at 1.
- **24p judder.** Held `fh` shots alternated 0.7 / 5–11 grey levels every 2–3 frames (eyes, emblem, saves, through, smile). Fixed with `interp="flow"`; I checked the frames and saw no warping.
- **The mist stepped and wrapped.** It drifted in whole quarter-res steps (a jump every ~3 frames), and at negative time the `%` wrap jumped to a different part of the noise. That broke the loop's virtual frames (pops at 1316 and 1320). Fixed with sub-pixel bilinear crops on a canvas big enough not to wrap between −1.5 and 23 s.
- **The source flickers.** The S3 Speed Force shot flashes pink-orange at 134.37–134.47 s, which became two pops (20.27, 20.35 s) under the mist and the flow. The last shot now starts at 134.50.
- **Lightning crossed his face.** The loop mist's lightning crossed his face (frame 1306); it now stays in the outer 20% of the frame.
- **A framing jump at the tear's cut.** The tear's progress never reached 1 at j = −1 (it used `/(pre+1)`); now it uses `/pre`.

## 7. Rules to adopt
1. **Sound restraint** *(new; changes "every transition gets its own sound")*.
   - Sound the set pieces and structural hits only.
   - Don't put a sound on every camera punch, letter, small transition or beat animation.
   - No shimmer, chime or "shine" sounds.
   - Let the song carry the ending and the loop.
   - A transition may be silent. The mixcheck "buried" list is a review list, not a target. Dexter rule 7 (+9–10 dB against a loud master, a 3 dB duck) still applies to the sounds you keep.
   - Evidence: rev 2, *"remove like half of the sound effects mostly the tedious annoying ones like the emblem shine and the few near the end"*, then approval.
2. **Find dead spans by measurement** *(new; makes v104's "no headspace" rule measurable)*.
   - Compute the mean frame-to-frame difference of the encode per half-beat (frames scaled to 135×240, grey).
   - Any span of about 1 s or more near the static floor (about 1–1.5 grey levels, against 5–18 in an active edit) gets a new cut and a designed transition.
   - Evidence: rev 2, *"identify one space where these isn't anything happening"*. The Iris hold measured 1.2–1.4 and was the answer.
3. **A pop audit on every encode** *(new)*.
   - List frames whose difference exceeds 3× the local median (±6 frames) plus 2.
   - Each one is either a cut, a designed flash or a beat hit, or it is a defect to fix.
   - Evidence: rev 1 shipped with six such defects that no still showed.
4. **Give a signature transition time to read** *(new)*.
   - A custom graphic transition needs about 1 s on screen, and the graphic should be at least about 8% of the frame width while it is being read.
   - Move the cut to the next sung word to make room rather than squeezing the transition.
   - Evidence: rev 3, *"slow down the tear drop transition so it's more visible"*, 0.6 s → 1.0 s, then approval.
5. **Smoothness** *(new)*.
   - 24p hold-cadence shots between 60p flow shots read as judder. Use flow on held shots wherever the frames stay clean.
   - Procedural motion must be sub-pixel (no integer-step drift).
   - Tremble uses smooth per-element sines (9–15 Hz), not a new random offset every frame.
   - No noise texture may wrap inside the edit's time range, including the loop's virtual frames.
   - Evidence: rev 2, *"one more polish smooth over the animations"*.
6. **Cover transitions start and end at exactly zero** *(new)*.
   - Check `cover.max()` at u = 0 and `cover.min()` at u = 1.
   - Keep the cover continuous across the cut.
   - Dissolve the two plates under the cover instead of switching them.
   - Evidence: the rev 1 pops at both mist transitions.
7. **The loop lands exactly and keeps moving** *(changed: extends v10/v11 rule 9)*.
   - Dissolve into frame 0's picture under the cover (never switch).
   - Fade frame 0's own finish in.
   - Render frame 0's background animation at the wrap's virtual negative frames so it carries on into frame 0.
   - Keep periodic events (flickers, flashes) off frame 0 itself.
   - Pass: seam ≤ 1, and no frame-difference spike across the wrap.
   - Evidence: rev 2, *"make sure the loop is seemless"*. Seam 0.14, with the wrap steps 0.5/0.5 then 1.5 (the footage starts).
8. **Probe the chosen range for VFX flickers** *(new)*: colour flashes in the source become pops under flow and transitions. Evidence: S3 Speed Force at 134.37–134.47 s.
9. *(confirmed)* Find the concept in the song's own words and the character's history (v11), have one focal set piece (v11), keep nothing on faces (v10/v11), and check lyric onsets on the vocal stem (v10).
   - On faces: the tear sits on Iris's jaw because it is the subject, and its ripple is masked off Barry's face.
   - On lyric onsets: also check Whisper's model size, and the beat map against the drum stem.

*Note for the owner and the Flash studio:* the scaffold base for Flash edits is a shared decision. v106's engine is v11 plus the pipeline-v2 speed section plus this edit's section. Everything v106 adds lives in `v106/`; v11's own files are untouched. Moving the Flash scaffold to v106 would bring in these new pieces as starting points: the mist, the wall, the tear, the lightning rod, `clash106`, the loop mist and the WONDER grade. That is the owner's call; until then, port the pieces from `v106/work/fx106.py`.

## 8. Techniques to reuse
- **TEAR LENS** (`tear_lens`, `drop_over`; 60 frames before the cut, 26 after).
  - **Gather** (first 40% of the pre-roll): a water drop forms at Iris's jawline, `(face_x + 0.30·w, face_y + 0.29·w)` with w the face width. Its radius grows 4 → 34 px and it stretches 10% vertically.
  - **Hang** (next 15%): it swells to 44 px with a small wobble and sags 12 px.
  - **Fall** (last 45%): it moves toward (0.5 W, 0.62 H) while its radius grows exponentially (`44·exp(ln(1500/44)·v^2.3)`) to cover the frame.
  - **Inside the drop:** the next shot is seen through a magnifying lens. Sampling is `q = P + d·m(ρ)` with `m = (1 − L·(1 − ρ²))·mag`.
    - P starts at the incoming face and moves to the drop centre as it falls.
    - mag goes 6 → 1 as the drop grows (a tiny drop shows his whole head, minified).
    - L (the bulge) goes 0.42 → 0.25.
  - **Lighting:**
    - a dark Fresnel edge (the inner 30% of the radius, at most 70 px, falling to 45% brightness);
    - a thin rim that is warm gold below and cobalt above;
    - a white-gold streetlight highlight at (−0.34 r, −0.40 r);
    - a gold caustic opposite it;
    - a soft shadow on the skin below while the drop is small.
  - **After the cut:** the lens relaxes, L = 0.25 → 0, and a ripple ring (24 px displacement, 55 px wide) runs out to 1,580 px. The ripple is masked off his face ellipse and catches a little light.
  - **Sound:** a plip as it lets go (a sine 1,780 → 380 Hz plus a little band noise), a reversed swell into the cut, then a low muffled bloom (noise low-passed at 900 Hz, 0.12 s decay) with a 62 → 30 Hz sub.
- **THE WONDERWALL** (`wall_tex`, `wall_frame`, `wall_layer`).
  - **Texture:** a running-bond wall of 6 × 11 tiles at half resolution. Each tile is a frame from the edit's own sources, desaturated 20% and warm-tinted (BGR × 0.82/0.93/1.06), darkened to 74%. Each has a bevel (lit top-left, shaded bottom-right) and a 4 px mortar gap.
  - **Placement:** perspective-warped from below, so the wall recedes upward, with a slow sway. It is drawn behind his matte at 90%.
  - **Light:** the mortar glows gold-white and pulses on every beat (`0.65 + 0.35·exp(−phase/0.18 s)`). The light wraps his near edge, but never his face.
  - **Rise:** the tiles flip in bottom row first, with random jitter, over 3.4 half-beats on "and after all".
  - **Crack:** lightning crawls along the horizontal mortar lines over the five half-beats before the burst.
  - **Tremble:** a smooth per-tile sine in the last two half-beats.
  - **Sound:** a low stone grind (60–420 Hz band noise) under the rise.
- **THE WONDERWALL burst** (`wonderwall`, `tile_split`, `tiles_of`; 12 frames before, 30 after).
  - **Before the cut:** the current frame becomes the wall: a running-bond grid with lit bevels and glowing mortar, its tiles shivering 1 → 10 px.
  - **After the cut:** the frame's tiles fly toward the camera from the centre outward (zoom to 1 + 4.5·w^1.25, outward travel to 1,500 px plus a little gravity, rotation up to ±60°, motion blur growing). They fade out between 25% and 70% of their flight. Tiles over his face go first and fastest.
  - **Behind them:** the next shot, lit with gold that decays over about nine frames, and a shockwave ring.
  - **Sound:** a rumble build, a reversed swell, a rising crackle, a zap, an impact at −9 dB, a sub drop, thunder, a stone-and-glass shatter (70 decaying resonant clicks at 1.8–7 kHz over a noise crunch), and a whoosh.
- **Speed Force mist** (`fbm`, `mist_field`, `crop_frac`, `mist_layer`, `mist_over`).
  - **Noise:** two fractal noise layers at quarter resolution, cropped at sub-pixel offsets that drift (layer one at +18/+11 px/s, layer two at −13/−7 px/s), from a canvas big enough never to wrap. The wisps are the ridges of the second layer.
  - **Colour:** deep cobalt body, pale blue-white wisps, a hint of violet.
  - **Behind him** (`mist=`): masked by his matte, with a cold lightning flicker on the half bar.
  - **As a transition** (`mist_over`): the coverage is a fractal radial edge closing from the frame edges. Under the cover, the picture refracts along the density gradient (60 px) and softens; the cover never goes above 88%.
- **Loop mist** (`loop_mist`, `loop_w`, `sf_virtual`).
  - Over the last 1.38 s, the cover rises to its peak at 55% of the way through and is fully clear by the last frame.
  - Between 40% and 62%, the picture under it dissolves into frame 0's footage, with frame 0's mist rendered at virtual frame f − DUR (negative) so the drift is continuous across the wrap.
  - Frame 0's finish (the face mask for halation) fades in with the same weight.
- **Lightning rod** (`lightning_rod`; 6 frames before, 20 after).
  - A gold leader flickers down beside the next face, 330 px to the side, never on it.
  - The strike hits the ground with a glow.
  - The next shot burns open outward from the bolt (a distance field from the bolt, radius 30 → 1,130 px) with an ember rim.
- **`clash106`:** v11's clash with the collision 110 px below the face box, and every spark and ring masked off a face ellipse.
- **WONDERWALL title** (`text_wonder`, `wonder_letter`).
  - Bevelled letters with a white-gold to gold face, an embossed vertical gradient and a cobalt glow.
  - Each letter is struck on its share of the sung word: it eases in, scales 1.35 → 1, blurs to sharp, and gets a gold flare.
  - Exit: vibrating ghosts at ±14 px as the letters fade, staggered by 15 ms.
- **The audits** (scripts in this session's scratchpad; easy to rebuild):
  1. Decode the encode at 135×240 grey and take `np.abs(np.diff(frames)).mean()` per frame.
  2. Average it per half-beat to find dead spans.
  3. Flag `d > 3·median(±6) + 2` as pops.
  4. Per shot, compare the 80th and 20th percentiles of the differences; a ratio over about 2.5 on a held shot means cadence judder.

## 9. Measured (final, rev 3)
- **Loudness:** −13.0 LUFS, true peak −2.9 dBTP after AAC (256 kb/s). The audio loop seam step is 0.022 against a local median of 0.010 (OK).
- **Picture loop seam:** blurred difference 0.14. Last and first frame mean luma 116.7 / 116.7.
- **Cuts and timing:** 20 shots; 19 transitions plus the loop set piece; 19 cuts checked, 0 suspicious, no clicks; no frozen runs; no black frames.
- **Faces:**
  - Text over faces: 0 frames.
  - faceqc: 50 flags in 7 runs. This is a review list; they are halation or rays on background pixels inside wide face boxes, plus the loop mist.
- **Flashes:** 8 events, at most 3 a second, no white-out runs. Three single-frame peaks are over 110 mean luma, all inside designed flashes:
  - frame 558 at 155.6 (the cut into the Speed Force POV);
  - frames 929 at 117.4 and 931 at 139.2 (the strobe).
- **Sharpness:** nine shots are flagged SOFT (`run1`, `saves`, `pov`, `runred`, `lookup`, `arms`, `charge`, `through`, `smile`).
  - Their absolute detail is within ±0.01 of rev 1.
  - All sources are 720p, restored; zoom ≤ 1.08.
- **Activity:** no pops left that aren't cuts, designed flashes or beat hits. The Iris span went from 1.2–1.4 to 3.2–3.3 grey levels a frame.
- **Effort:**
  - 3 owner rounds; 6 full renders (2 per round).
  - A full render: about 305 s to the upload file, then the master in the background.
  - QC: about 136 s.
