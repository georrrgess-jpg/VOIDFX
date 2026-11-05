# DRACULA — Dexter × Tame Impala "Dracula" (voidfx v105, 9:16)

Studio 2. Built from the v104 THE PASSENGER standard (`tools/new_edit.py`), with the v9 text style (keyline captions, per-letter hero title) and the Flash rules (motion pass, upscale, checked lyrics, set pieces on the drop, hook and loop, a loop that lands on frame 0).

**Song:** `src/dracula.mp3` (Tame Impala "Dracula", 114.99 BPM).

**What came with the brief:**
- Two **Flash** packs, stored for future Flash edits only (not used here):
  - `src/flash_s4.mp4` (key `fs4`: 97 shots, clean, no audio);
  - `src/reverse_flash.mp4` (key `rf`: 56 shots; "SCENEPACK LINK IN DESC" is burned in at the bottom, and there are text cards at about 39, 67 and 85–94 s).
  Both are catalogued in `studio/SCENE_PACKS.md`, with shot lists in `studio/packs/shots_fs4.json` and `shots_rf.json`.
- **No new Dexter packs**, so the edit uses the library packs p1, p3, p4, p5, p6, p7, p8, p9, p10 and doakes.

**Files not available in this session:** `trinity_goodbye.mp4` (listed in the catalog, not in `src/`) and the rendered v4–v9 edits (reviewed through the handbook and their READMEs).

## Pre-render check (handbook §0 and §5a)

**1. A concept rooted in Dexter's world: SUNDOWN.** By day he wears the mask: sunny Miami, the boat, the smile, the ice cream, the badge. The song's last chorus is *"run from the sun like Dracula"*, so the sun sets across the song's one-bar drop-out and night slams in on the drop, the biggest change in the song. Night is the hunt. At the end the sun comes up and burns him white, the way sunlight ends a vampire, and the loop opens in that same light.

**2. Set pieces (multi-stage, themed, each with its own sound), one on every phrase start:**
- **SUNDOWN (k24–32).** The sun sets down the right edge of two shots (off his face), its rays stretching, and the grade slides from day to dusk to night. On the second shot he looks up at the darkening sky. A descending sun glide and a heartbeat play under the song's drop-out bar.
- **THE BAT BURST + "DRACULA" (the drop, k32).** A cloud of bats pours out of the sky above him in 3D, toward the lens. On the downbeat it blacks out the frame against a crimson flash, then flies past the camera (near bats soft, far ones sharp) to reveal him at night. "DRACULA" builds letter by letter, floods red and breaks into crimson bats that scatter away from his face. Sound: a reverse swell, a sub impact, a burst of wings, bat chirps.
- **THE BLOOD MOON (k48, the second "Dracula").** A moon iris opens on him; behind his MODNet cut-out a procedural blood moon rises, with craters, maria, limb darkening, drifting cloud and bats crossing. It lights a red rim on his edge and pulses on the word. Sound: a church-bell toll on B-flat.
- **THE COFFIN (k64, the third "Dracula").** A lacquered mahogany coffin lid with a brass cross, lit from a height map (bevel, raised panel, specular), falls toward the lens. It slams shut over him (the frame jolts, dust kicks up) and lifts away on the next shot. Sound: a hinge creak, a wood thud with its own resonances, dust.
- **DAYBREAK (the loop, k84–88).** Dawn light rises from the bottom, the sun comes up low on the right, and the frame burns to white. Then the white clears into frame 0 itself, so the loop has no seam. Sound: an airy B-flat-minor chord swells, and its tail rings over the loop into the opening.

**3. Designed text and graphics in every section.**
- **Text:** only clearly sung words (see 4): SAW THIS MOMENT / COMING FROM **AFAR**, RUN FROM THE **SUN** / LIKE, the hero **DRACULA**, and **DRACULA** twice more (on the blood moon and on the coffin).
- **Graphics:**
  - the sun with light rays and lens ghosts on every day shot;
  - the setting sun;
  - bats (the burst, the title's bats, the swarm, the moon's bats);
  - the blood moon;
  - the coffin lid;
  - night fog on the drop shot;
  - the daybreak light;
  - the voidfx logo (once, unchanged);
  - a crimson bloom on the strongest reds;
  - warm halation by day and moonlit halation by night.

**4. Lyric recognition (handbook §0).**
- **Checked on the Demucs vocal stem** with faster-whisper (large-v3) in tight windows, with no lyric hint so it couldn't simply echo the expected words:
  - "Saw this moment coming from afar" (155.16–157.6 s);
  - "(So) run from the sun like Dracula" (161.02–163.6 s);
  - "Dracula" again at about 167.2 and 171.4 s.
- **Each caption word starts on its sung onset** (snapped on the vocal envelope).
- **Published-lyric references** confirm the chorus line is about the sun: Songfacts and Wikipedia's page on the song.
- **Not captioned**, because they weren't clear on the vocal: "Now here we are", the other words of the later repeats, and "this love is spectacular".

**5. Density (at least 24 designed transitions per ~24 s; no headspace).**
- **25 designed cuts in 22.97 s, no plain cuts, each with its own sound:**
  - sun flare;
  - whip;
  - film burn;
  - slam;
  - tilt;
  - quarter-turn;
  - smear;
  - light sweep;
  - whip up;
  - **bat burst**;
  - strobe;
  - impact frame;
  - torch blind-out;
  - whip;
  - **moon iris**;
  - lamp on;
  - logo;
  - roll into the upside-down shot;
  - **coffin**;
  - **bat swarm** (a river of bats in depth with moonlight behind it);
  - eye dive;
  - face-match;
  - shutter;
  - zipper;
  - sun flare.
- **Bookends:** the opening burn-off and the daybreak.
- **Repeats:** only the whip (twice) and the sun flare (open and close, deliberately).
- **Every hold has motion:** the camera punches on every beat from the drop (strong on the bars), there are light punches through the day, and the camera floats on every hold.
- **The longest shots:**
  - the drop shot, 1.57 s (bat burst, then the title, then its exit);
  - the moon shot, 1.57 s (iris, rising moon, pulse, caption, bats);
  - the looks-up shot, 1.30 s (the sun setting through it, the lyric, the bats arriving);
  - the rest, 0.52–1.04 s.

**6. Flash rules (CLAUDE.md).**
- **The motion pass on every hook shot:**
  - **speed ramps** (`tmap`) on the ice cream, the garage turn, the container grin and the attack, with ghost trails;
  - the **beat-synced camera**;
  - **light rays** from every sun;
  - **no interpolated slow motion:** every source plays at its own 24p/30p cadence (`interp="hold"`), so nothing warps.
- **The upscale pass:** the 720p sources are cropped to about 405×720. The crop is enlarged with Lanczos resampling, then fine luma detail is restored above the noise floor (a noise-gated detail boost, so grain isn't sharpened). **This is not an AI upscaler:** OpenCV 5 here has no super-resolution module, and a Real-ESRGAN-class model on CPU would take about 10 s a frame.
- **Lyrics** were checked against the sung vocal (see 4).
- **Set pieces** sit on the drop (the bat burst), the hook (the blood moon and the coffin) and the loop (daybreak).
- **The loop lands on frame 0:** the last 12 frames come out of the white into frame 0's own image.

**7. Comparison with v103 FOREVER, v104 THE PASSENGER, v7 and v6.**
- **Look:** v6 pastel vapor, v7 forensic noir, v103 undertow, v104 SUMI ink. **v105 SUNDOWN** is two looks in one edit: a bleached, warm "Sunshine State postcard" day with teal shadows and a sun with rays, then a cold, silver moonlit night with deep blacks where only crimson survives. The change happens on the drop.
- **Opening:**
  - v103: surfacing from under water;
  - v104: an ink drop on paper;
  - **v105:** Dexter on his boat in a blown-out sunrise, the white burning off on the first beat.
- **The big moment:** v104's ink shadow was one matte-driven set piece. v105 has four: a 3D bat burst, a matte-composited blood moon, a height-map-lit coffin lid and a 3D bat swarm.
- **Weakest point of the plan, and the answer:** the day half could feel like a slideshow before the drop. **Answer:** it cuts every 3 half-beats (0.78 s) with eight different transitions, a sun with rays in most shots, light beat punches, and the lyric captions word by word.

**8. Frame rate.** 60 fps output, with every source at its own cadence (no optical flow). The graphics and transitions animate at 60.

## Song section

The window is half-beats **h592–h680** (154.55–177.51 s, 11 bars), one pass, no splice. It's the final chorus run: the line "saw this moment coming from afar", the one-bar drop-out, then the biggest change in the song.

| Song time | Edit | What happens |
|---|---|---|
| 154.55 | 0.00 (k0) | Daybreak white burns off Dexter on the boat (the loop seam) |
| 155.16 | 0.61 | "SAW THIS MOMENT / COMING FROM AFAR" |
| 160.81 | 6.26 (k24) | **The drop-out bar: SUNDOWN** |
| 161.02 | 6.47 | "RUN FROM THE SUN / LIKE" |
| 162.90 | 8.35 (k32) | **The drop (+29.8 dB, the biggest change in the song): THE BAT BURST** |
| 163.14 | 8.59 | "DRACULA" (hero) |
| 167.2 | 12.7 (k48 at 12.5) | "DRACULA": THE BLOOD MOON |
| 171.4 | 16.9 (k64 at 16.7) | "DRACULA": THE COFFIN |
| 176.47 | 21.92 (k84) | DAYBREAK |
| 177.51 | 22.97 | Loop: the end runs straight back into 154.55 (the pre-roll is the song's own lead-in) |

**Grid:** k = one half-beat = 0.26090 s, from `tools/song_map.py` (`work/song_map.json`). The drop is the largest loudness change in the song.

**Dialogue:** none. The song's voice carries the text (the brief says dialogue only if it helps).

## Review log (before the first full render)

Each pass asked "what would make this unforgettable?", not just "what's broken?".

1. **The opening was a flat white frame.** That's no hook. Frame 0 now shows Dexter on the boat with the sun through 30% dawn white. The ending comes out of the white into exactly that image (loop seam crossfade), so the seam stays clean.
2. **The bat burst first came out of his mouth** as a black clump. It's rebuilt as a 3D flight: the bats come out of the sky above him (where he's looking), black out the frame against a crimson flash, and fly past the lens with depth blur. Each bat has a crimson-backlit top edge.
3. **The swarm read as wallpaper** (small, uniform bats), and the bats vanished on dark footage. It's rebuilt in depth (parallax, size and blur by distance), with a band of moonlight travelling behind the column so they read as silhouettes.
4. **The coffin lid looked like a flat brown shape with yellow dots.** It's rebuilt from a height map: a bevelled edge, a raised panel, a groove, a brass cross, lacquer specular and a clear-coat sheen. The first wood grain read as zebra stripes and was toned down. It also jolts the frame and kicks up dust on the slam.
5. **The moon was a flat red disc.** It's now a procedural lunar surface (maria, craters with lit and shadowed rims, limb darkening, the brighter edge of the Earth's shadow), coloured as a blood moon.
6. **Overlays on faces:**
   - the sun-flare streak ran across his eyes, so it now runs at the sun's height;
   - the setting sun crossed his face, so it now sets down the right edge;
   - the dawn sun sat on his chin, so it now rises low on the right;
   - the title's bats flew up across his face, so they now scatter sideways.
7. **Red on red:** the title exit spilled onto the red-lit drive shot. The title now ends before the cut.
8. **The logo** wasn't in the first cut. It's now on the garage shot, once, unchanged (no halo or bloom on logo frames).
9. **Text over the face:** the third "DRACULA" sat on his chin in the container shot, so it moved below (band 1570–1785).
10. **Sound levels:** the song is mastered loud (−9 to −11 dBFS RMS), so the first design sat 20–25 dB under it. The design is now 9 dB hotter, and the music ducks 3 dB under the three big hits.

## Full render 1: 9/10, not shipped

| Check | Result |
|---|---|
| Format | 1080×1920, 60 fps, 1378 frames (22.97 s), H.264 + AAC |
| Loudness after AAC | −13.0 LUFS, true peak −4.2 dBTP |
| Clicks | 0 at the 25 cuts; loop seam clean by the QC rule |
| Loop seam picture | blurred difference 3.92 (frame 0 against the last frame) |
| **Faces** | **FAIL:** in the sunset shot (frames 420–432) he leans in and his face, about 900 px wide, no longer fits the 9:16 crop |
| Text over faces | pass |
| Black frames | 844–847 (the designed lamp-on blackout) and 1111–1112 (the eye dive's black pupil), both by design |
| Length | audio and video within 9.3 ms |

**Visual sign-off of render 1** (the encoded MP4, every 22nd frame):
- the blinds and lamp shots were close to black;
- the opening boat shot was milky (a hazy source under the bleached day grade);
- the sunset was the face failure above.

**Fixes for render 2:**
11. **Sunset:** it now ends before he leans in (405.95–406.62, k24–27). The looks-up shot takes the rest of the bar (k27–32, 1:1), so he looks up at the sky as it darkens.
12. **Exposure:** the blinds shot gets +0.6 EV and the lamp shot +0.55 EV (a new per-shot `ev`), so both read at night.
13. **The hook:** the boat shot gets a contrast curve (a new per-shot `con`), so frame 0 has a blue sky, a white sun and a readable face rather than a milky haze.

## Checkpoint: render 2, 10/10 PASS, visual sign-off PASS (shipped)

| Check | Result |
|---|---|
| Format | 1080×1920, 60 fps, 1378 frames (22.97 s), H.264 + AAC, fast-start |
| Loudness after AAC | −13.0 LUFS, true peak −4.3 dBTP |
| Clicks | 0 at the 25 cuts; loop seam clean by the QC rule |
| Loop seam picture | blurred difference 4.16: the last frames come out of the white into frame 0's own image |
| Faces | centred in every shot (one borderline frame each in the sunset and dawn shots, within the tolerance); 0 text-over-face frames. Frames 116 (the ice cream cone) and 970 (the upside-down shot) were checked visually: the detection is low, and there's no text there |
| Black frames | 844–847 (the lamp-on blackout) and 1111–1112 (the eye dive's pupil), both by design |
| Frozen runs | none |
| Length | audio and video within 9.3 ms |

**Visual sign-off** was done on frames pulled from the encoded MP4. It covered:
- the whole edit, every 22nd frame;
- the bat burst frame by frame (494–520);
- the title and its bats (566–596);
- the moon iris and the blood moon;
- the coffin (996–1013);
- the swarm (1058–1070);
- the flagged frames;
- the loop seam (1360–1377 → 0–6).

The renderer's frame 0 and the MP4's frame 0 were also compared: they match (mean colour within 3 levels).

**Not verified:** watching and listening in real time. The sound was checked by measurement only (levels per section, effects against the music at every set piece, clicks, the loop).
