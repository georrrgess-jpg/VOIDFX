# BOP — The Flash × DaBaby "BOP" (voidfx v11, 9:16)

A 20.79 s, 1080×1920, 60 fps TikTok edit. It's built on the v10 LET IT HAPPEN standard engine and loops: the red lightning snatches the last frame back to the first.

**Deliverables:**
- `v11/out/bop_flash_voidfx_9x16.mp4`: H.264 + AAC, fast-start (upload this one).
- `v11/out/bop_flash_voidfx_9x16_master.mov`: CRF 11 + 24-bit PCM master.

## Sources (what was reviewed)

| Pack | What it actually is | Used |
|---|---|---|
| `src/flash_s4.mp4` (attached "FLASH SEASON 4 SCENE PACK 4K 60FPS") | 1280×720 at 60 fps, 186 s, **24p content** (63 % repeated frames), ~1.1 Mbps. 97 shots reviewed on contact sheets. Shots 0–12 are a CGI/fan-render city run plus a non-Flash anime-style face; left out to keep the look live-action and consistent. | 11 shots |
| `src/reverse_flash.mp4` (attached "Reverse Flash … Topazed 4K 60fps") | 1280×720 at 60 fps, 94 s, **true 60 fps**. Every clip is a ~600×600 inset over a blurred, scan-lined copy, with "SCENEPACK LINK IN DESC" under it and "Intro Clip" title cards. 56 shots reviewed; many are dark S1 Wells dialogue. | 3 shots, framed inside the inset (no watermark) |
| Older Flash packs (`flash_b`, `flash_a`) | Reviewed in v10. | Not needed: S4 has stronger action, and the v10 shots stay v10's |

Neither attached pack is actually 4K. Both were restored with `tools/sr_prep.py` (Real-ESRGAN compact, 2×) before rendering.

## Song: the section used and why

`src/bop.mp3` (2:40), 127.0 BPM (half-beat 0.23622 s), checked on the Demucs vocal stem. **Window: half-beats 32 → 120 (7.75 → 28.54 s, 11 bars).**

| Song | What happens | Edit |
|---|---|---|
| 7.75 | The intro talk over the bass-less intro | 0.00 |
| 9.60 | *"I mean, they're like, **Harrison**…"* | 1.85: Harrison Wells is the Reverse-Flash, so the cold open is his |
| 9.64 | The beat drops in (+24.8 dB) | **1.89: the red shudder → his mask** |
| 13.42 | The dip; *"Let's go!"* at 14.34 | 5.67 / 6.59 |
| **15.31** | **The drop:** the verse, *"I needed some shit with some bop in it"* | **7.56: the bolt split** |
| 28.54 | A bar line between two lines (a clean end) | 20.79: tape stop → the loop |

Why this part: the intro's spoken "Harrison" hands the edit a concept, the beat-in at 9.64 gives a first impact within two seconds, and "Let's go!" sets up the real drop exactly where the verse starts. The rest of the verse is explicit, so it carries no captions: as requested, only two designed words appear (LET'S GO, BOP).

## Concept: THE RIVAL

The cold open is Harrison Wells / the Reverse-Flash, in red: Wells' face on "Harrison", his mask's red eyes on the beat, Thawne's smirk, the red lightning. Barry answers on the dip, and on the drop the frame splits along a lightning-bolt seam, red against gold, and the gold breaks through. The verse is Barry's swagger and speed, in gold. At the end the red lightning snatches the frame back to Harrison, so the rivalry loops.

**Look: VOLTAGE / RIVAL** (new): deep clean blacks, the crimson suit, warm gold lightning with bloom, and cool teal in the shadows for Barry. The rival's shots go red (red-shifted highlights, dark red shadows, red halation).

## The edit, shot by shot

| Edit | Music | Shot | Transition in (each with its own sound) |
|---|---|---|---|
| 0.00 | Intro talk | Harrison Wells, side-lit (rf 13.05) | **Red loop landing:** the Reverse-Flash shudder settles (continues the last frame) |
| 1.89 | **Beat in** | The Reverse-Flash mask (rf 15.02) | **Red phase:** the frame vibrates into red ghost copies (his signature face blur) and resolves into the mask. Red arcs crawl on his silhouette |
| 3.31 | | Thawne smirks, cowl down (s4 95.50) | **Red link:** a red arc leaps out of the mask, off both faces |
| 4.72 | | Eobard, red eyes (rf 34.00) | **Red slices:** the frame rips into bands with red edges |
| 5.67 | The dip | Barry's answer, intense close-up (s4 93.90) | **Red streak:** the rival runs past below his chin, and Barry is behind him |
| 6.61 | *"Let's go!"* | Barry, close (s4 100.12) | **Dolly / focus pull**, a quiet breath. **LET'S GO** (GO lands white-hot, struck by a bolt) |
| **7.56** | **THE DROP** | Yellow lenses, gold lightning off him (s4 28.70) | **BOLT SPLIT:** a lightning-bolt seam cracks down beside his face as LET'S GO lands. The left side goes red, the right gold; on the drop the gold breaks through, the seam sweeps across like the emblem's bolt (tearing LET'S GO apart), and a refracting shockwave rings out |
| 8.98 | | Grinning in the suit (s4 31.40) | Gold arc link |
| 9.92 | *"…some **bop** in it"* | Running in the dark with lightning (s4 122.95) | **Whip pan** with a gold streak. **BOP** punches in letter by letter, the O is the Flash emblem |
| 10.87 | | Low-angle lightning run (s4 137.20) | Speed slices |
| 11.81 | | **Time freeze:** the same run, from below (s4 140.95–141.85) | **Freeze:** time stops on the beat, the colour half drains, gold sparks hang in the air and the camera glides through the moment in 3-D (bullet time) |
| 13.23 | | Masked smirk (s4 62.90) | **Restart:** time snaps back on a ring |
| 14.17 | | Masked close-up in the bar (s4 155.80) | **Ignite:** blackout, side strikes, brightest-first |
| 15.12 | | **The flight through fire**, wide (s4 171.76) | **Into the Speed Force:** a radial tunnel pull, with light streaks rushing from the vanishing point through the shot |
| 16.54 | | The flight, close (s4 173.40) | Speed ramp |
| 18.43 | | The final stare, frontal (s4 146.40) | **Emblem reveal:** the Flash emblem draws itself in light (ring, then bolt) exactly where his chest emblem will be; the next shot opens through it, emblem on emblem. Lightning ribbons spiral round him |
| 19.84 → 20.79 | Tape stop | The red lightning takes the frame back | **The loop:** a red streak runs along the bottom, the frame shudders in red and becomes Harrison, frame 0 |

**Motion pass (the v10 standard):**
- Every verse shot is speed-ramped: a burst on each beat, then optical-flow slow motion on the restored source.
- On every beat from the drop to the loop, the camera punches in 5.5 % with an alternating ±1° kick, plus zoom blur and a colour split on the hit frames.
- The cold open's beats get a softer 2.5 % punch.
- Light rays and light warps sit on the lightning shots.

**Sound:**
- The song window plays straight, then tape-stops into the loop.
- Every transition has its own sound: the red shudder (buzz, whoom, crackle), the bolt-split crackle building into the drop's impact, thunder and sub drop, swirl passes, the Speed Force rush, and a tick and shimmer for the freeze.
- A quiet swish on each camera punch that isn't a cut.
- Room tone runs continuously across the wrap.
- Built circularly, mastered on a wrapped copy, measured after AAC.

## Review passes (before the final render)

- **Cut sheets of every transition**, plus stills of every set piece at full size.
- **Shots swapped:**
  - A tux-wedding shot blew out in orange and was replaced by the low-angle lightning run.
  - The first time-freeze plate showed only the back of Barry's head. The freeze moved to the dutch-angle lightning run, with a partial colour drain, because MODNet couldn't hold a matte on that angle.
  - The bar shot was re-picked so his face isn't hidden.
- **Moved off faces:**
  - The bolt seam moved beside his face (it ran through his nose).
  - The red streak moved below the chin.
  - The emblem reveal moved onto his chest emblem.
  - The loop streak moved to the bottom of the frame.
- **Exposure:** brought down on the fire shots, the dark lightning run and the drop (white skies and fire clipped). The speed ramp no longer brightens. The drop's impact frame was halved, so there's no full-screen white flash.

## Ship checkpoint (measured on the encoded MP4)

| Check | Result |
|---|---|
| Format | 1080×1920, 60 fps, 1247 frames, decodes clean |
| Loudness | −13.2 LUFS, −3.3 dBTP after AAC |
| Faces | every shot centred. The first final render failed here: a background guard's face was cut at the frame edge in the BOP run. That shot is now framed on Barry |
| Text vs faces | clear. Frames 394/396 flag the dolly frames *before* LET'S appears (checked: no text yet). LET'S GO was moved 80 px lower, clear of his chin |
| Cuts | 15 cuts, 0 audio clicks |
| Black frames | frame 849 only: the ignite blackout, by design |
| Loop seam | blurred diff 3.47, inside the red shudder's own frame-to-frame motion (4.0–7.9 across 1243 → 2): frames 1244 → 2 show the same image. Audio continuous through the tape stop |
| A/V length | within one frame |
| Verdict | SHIP |

**Visual sign-off:** frames pulled from the encoded file around every transition, both titles, the freeze, the Speed Force flight, the emblem reveal and the loop seam.

## Revision 2 (owner feedback)

> "Add a lot more animations, graphics, transitions etc. I also want more sound effects… absolutely amazing with wonderful animations, transitions etc."

**New transitions (each with its own layered sound):**

| Edit | Into | Transition | Sound |
|---|---|---|---|
| 4.72 | Eobard (red eyes) | **Red streak** (moved here): the rival runs past and Eobard is behind him | Swirl pass + crackle |
| 5.67 | Barry's answer | **RED EYE DIVE:** the camera dives into Eobard's glowing red eye until the frame is red light, then pulls out of Barry's eye (a macro of his eye, widening to his face) | Power-up whine, red rush, sub drop |
| 8.98 | The grin | **STROBE ECHO:** the frame snaps left leaving a trail of gold stroboscopic afterimages; the grin lands from the right with its own echoes collapsing | A stuttered run of five passes, a zap |
| 10.87 | Low-angle run | **BOLT TRACE:** a bolt zig-zags across the frame below his face and the next shot burns in along it, edges glowing like embers | Crackle panned left to right, fire whoosh |
| 16.54 | The flight, close | **HEAT HAZE:** the fire's heat rises up the frame, refracting the picture, and carries the next shot in behind a glowing wall | Fire roar swelling up |
| 17.48 | **New shot: the punch** (Barry slams Thawne into the pillar, his red glove at Thawne's collar) | **CLASH:** a red bolt and a gold bolt race in from opposite sides and collide; red and gold sparks burst out behind a refracting shockwave | Two zaps racing in, impact, thunder crack, crackle |

The new punch shot (s4 90.45–91.30) is the gold beating the red just before the final stare. The fire flight was shortened to make room.

**New graphics:**
- **Embers in depth:** red for the rival (cold open), orange rising off the fire. They pass behind the subject through the matte.
- **Gold dust:** drifts through the calm and close-up shots.
- **Speed particles:** streaks rushing past in depth on the drop, the runs and the slam. They're masked off every face.
- **Edge lightning on bar lines:** red on the beat-in (1.89) and 3.78; gold at 9.45, 11.34 and 17.0.
- **Light sweeps:** white-gold diagonal sweeps at 6.14, 10.39 and 13.70.

**New sound design:**
- a red crackle bed under the whole cold open;
- a sub swell into the beat-in;
- a reverse swell (the breath) before the drop;
- crackles on every edge-lightning bar;
- shimmers on the sweeps;
- clock ticks in the frozen moment;
- speed passes on the runs and the flight;
- a power-down whine under the loop's tape stop.

REV2_RESULTS_V11

