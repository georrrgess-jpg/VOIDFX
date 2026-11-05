# voidfx toolkit: how an edit gets made (fast)

The engine is the newest standard, `v104/work/` (THE PASSENGER; see the handbook §0). `render104.py` contains every v4–v9 transition and graphic, and the edit's own section is spliced in from `fx104.py` by `splice.py`. That section carries FOREVER's toolkit and THE PASSENGER's on top of it (the last definitions win, so that section owns the grade, the frame function, the text and the finish). New edits copy all of it, plus THE PASSENGER's EDL as the worked template, with `tools/new_edit.py`. Then they rewrite the EDL, restyle their `fxN.py` (grade, palette, set pieces, frame) and the sound design, and run `python3 vN/work/splice.py` after each `fxN.py` change. **Copy the engine, not the look.** Every edit gets its own grade, type and transition mix. Owner preferences and lessons: `studio/VOIDFX_STUDIO.md`; sources: `studio/SCENE_PACKS.md`.

## 1. Pipeline and timings

Timings were measured on this 4-core box for a 26 s edit.

| Step | Command | Time |
|---|---|---|
| Scaffold | `python3 tools/new_edit.py N SLUG "TITLE"` | 1 s |
| Map the song | `python3 tools/song_map.py src/SONG.mp3 vN/work` | 3 s |
| Shot lists | `python3 vN/work/analyze.py src/PACK.mp4 TAG` (contact sheets, per-shot stats) | ~1 min per pack |
| **Lyric recognition** | `python3 tools/lyrics.py vN src/SONG.mp3 START END "published lyrics \| line 2"`. Demucs vocals (cached), Whisper word times snapped to the real onsets, aligned to the published lyrics, unsung words left out, a ready `TEXT` caption block | ~1 min (+2 min Demucs the first time) |
| Dialogue | `python3 tools/transcribe.py vN NAME MEDIA [--vad] [--start S --dur D]` | 1–3 min |
| Edit-section change | edit `vN/work/fxN.py`, then `python3 vN/work/splice.py` | 1 s |
| Voice under score | `python3 -m demucs -n htdemucs --two-stems=vocals -o vN/audio/sep CLIP.wav` | 15 s per 30 s clip |
| Tracks and mattes | `bash tools/build.sh N prep` | ~35 s |
| **Every-cut review sheets** | `bash tools/build.sh N auto` → `vN/frames/cuts_*.jpg` | ~35 s |
| Soundtrack | `bash tools/build.sh N audio` (circular, wrapped master, AAC-checked) | ~7 s |
| **Motion check** | `bash tools/build.sh N clip:A:B` → small MP4 with sound | ~20 s |
| Whole-edit preview | `bash tools/build.sh N preview` (30 fps, 540×960) | ~half the final render |
| Final + checkpoint | `bash tools/build.sh N video qc` | ~15 min + 1 min |

**Efficient loop:**
1. Write the EDL.
2. Run `prep auto`.
3. Fix whatever the sheets show, using `stills` / `clip` on single moments.
4. Run `audio`.
5. Run **one** `video qc` per revision.
6. Visual sign-off on frames pulled from the encoded MP4.

Never final-render to find out whether something works.

**Choosing the song window:** `song_map` prints whole-bar windows of 20–27 s with the biggest section change (the "good part", where the full mix or bass comes back) at 33–47 % of the edit. For Warmpop it independently found the window used in v6 (h416→h496, drop at 10.67 s).

## 2. Transitions (`tin=` on the incoming shot)

Each transition goes through something and has its own sound in `audioN.py` (`if tin == ...`).

| tin | What it does | Extra EDL fields | Sound |
|---|---|---|---|
| `tape_in` | Static → VCR roll-in while the song winds up to speed (the loop start) | — | Clunk, motor, static |
| `eye_dive` | Dives into the outgoing face's eye; the pupil swallows the frame; a hexagonal aperture opens | Face track | Heartbeat, shutter blades |
| `assemble` | The next shot builds itself from flying pixel blocks | — | Reversed crumble |
| `polaroid` | Flash; the frame freezes into a print that is tossed away | — | Flash, shutter, print eject |
| `facematch` | Face slides and scales onto the next shot's face | Face tracks | Whoosh, soft hit |
| `tear` | VHS tape tear: sliding bands with chroma fringes | — | Glitch burst |
| `crt` (+ `tout="crt"` on the previous shot) | Frame shrinks into a CRT in the vapor world; the camera dives through the screen with hyperspace streaks | — | Hum, riser, drop impact, degauss |
| `cube` | 3D cube turn over the vapor world | — | Whoosh, landing thud |
| `sun` | A striped retro sun rises; the camera flies through the stripes | — | Riser, chord swell, blind rattle |
| `filmstrip` | The frame becomes a film strip on a light table, whips to the next frame | — | Projector rattle |
| `peel` | Glossy sticker peel from the corner | — | Sticky crackle, flap |
| `ink` | A blood drop falls and splats; the stain blooms open into the shot | — | Drip, splash |
| `slash` | A blade streak cuts the frame; the halves fly apart with blood flecks | — | Swish, steel ring |
| `logo` | voidfx logo as a neon sign, flying through the "o" (**once per edit**) | — | Neon buzz, whoosh |
| `burn` | Film burn holes | — | Fire crackle |
| `lens` | The next shot reflects in the sunglasses; the camera dives into a lens | `lens=(dy, kx, ky)` on the outgoing shot | Glass chime |
| `shadow` | Darkness swallows the frame; the next shot emerges brightest-first | — | Reverse swell |
| `tv_off` | Finger-gun muzzle flash → CRT power-off → power-on | `muzzle=(x, y)` on the outgoing shot | Gunshot, power-off whine, power-on sweep |
| `slidebox_close` (v7) | Dexter's rosewood blood-slide box: the lid slams on a sung word (`CLOSE_T`), with the word engraved on a brass plate; it reopens and the camera dives into a blood drop on a slide | `CLOSE_T` | Creak, wood slam, slides rattling, latch, glass, bloop |
| `burst` (v7) | Kill-room plastic stretches toward the camera (centre-weighted bulge), then bursts into flaps with a blood spray and shock ring; the hero drop transition | Previous shot `plastic=True` | Plastic stretch, riser, rip, sub impact, splash |
| `blood_lens` (v7) | A blood drop falls and splats on the lens; the next shot is seen through it, then drips clear | — | Drip, splat, squelch |
| `zipper` (v7) | A body bag zips shut over the frame, then unzips onto the next shot | — | Zip rasp ×2 |
| `m99` (v7) | Sedative: double vision, blur, the eyelids close; they blink open on the next shot (the music is muffled underneath) | — | Heartbeats, thump, breath |
| `mag_sweep` (v7) | A magnifying glass sweeps in; inside it is the next shot, and the glass becomes the frame (`lensframe=True` on the next shot) | — | Whoosh, glass chime |
| `logo_orig` | The voidfx logo exactly as supplied, slammed in and flown through the "o" | — | Impact, shimmer, whoosh |
| `tout="rewind_end"` | The last shot rewinds at 8× → static → loops into `tape_in` | — | Tape scrub, the song scrubs backwards |
| `mirror_in` / `tout="mirror_out"` (v8) | Push into a rear-view mirror in a dark rainy car / pull back into it (the loop) | `rain=True` | Streetlight hum, whoosh, chime |
| `light_sweep`, `wiper`, `whip`, `whip_up`, `light_leak`, `wrap`, `impact`, `rainfocus`, `lamp_on`, `slam`, `knife_pass` (v8) | The "basic" set the owner liked (streetlight band, windshield wiper, whip pans, plastic wrap, one-frame negative, rain focus pull, lamp switching on), plus the knife roll and pass | — | each has its own sound in `audio8.py` |
| `loop_in` / `tout="drop_moon"` (v9) | The last shot pushes through the drop of blood on a slide until the frame is red; frame 0 pulls back out of the blood moon | `spot=(x, y)` source px of the blood | Plunge, bloop, heartbeat, low-pass "night closes" |
| `tilt` (v9) | One eased vertical camera move: the moon slides up, the shot rises in from below | — | Low air move |
| `foliage` (v9) | The lens passes behind a moonlit bush with white blossoms (a feathered 3.4×W strip) | — | Leaf rustle |
| `petals` (v9) | A gust of jasmine petals blows across the lens, densest on the cut | — | Wind gust, petal flutter, chimes |
| `bloom` (v9 hero) | The (frozen) frame bursts into image-carrying petal cells from its heart outward; they tumble toward the lens, showing their white backs; the next shot is behind | `BLOOM_C` | Breath-in swell, sub boom, a burst of petal flutter |
| `strobe` (v9) | Two soft strobe hits across the cut (never full black or white) | — | Zaps, sub |
| `beam` (v9) | The brightest point (a torch) swings into the lens and whites out; the next shot comes up brightest-first | — | Click, light swell, shimmer |
| `blinds` (v9) | Backlit venetian slats rotate shut, then open on the next shot (staggered top to bottom) | — | Slat rattle ×2 |
| `roll` (v9) | The world rolls 90° with rotational blur (lands on an upside-down shot) | — | Doppler whoosh, floor thud |
| `smear` (v9) | Step-printed long-exposure echoes drag the frame, then settle | — | Tape-warble whoosh |
| `projector_on`, `latex`, `frameslip`, `filmmelt`, `whip`, `hooddark`, `lavalamp`, `slidewipe`, `newsspin`, `papertear`, `oilwheel`, `tout="reel_end"` (v101, in `v101/work/fx101.py`) | 16 mm psych reel: projector strike-up and run-out (loop), a glove-stretch tear, a frame slip in the gate, a film burn-through (hero), a hood over the lens, lava-lamp blood blobs, a blood-slide glass wipe, a newspaper spin and tear, an oil-wheel light show. **v101's look was rejected; reuse transitions only if reworked** | — | Each has its own in `audio101.py` |
| `rewind_in` + `tout="rewind_end"` (v102, in `v102/work/fx102.py`) | The loop as time travel: the last bar plays the whole edit backwards (35× at its peak, picture and sound together via `rew_pos`) and lands on frame 0, whose flash and smear settle into the first shot | — | The song runs backwards (band-limited), tape scrub, crackle |
| `bolt_link`, `overcharge`, `strike`, `emblem`, `passby`, `smear` (light streaks), `impact`, `remnant` (soft) (v102) | A bolt out of the outgoing face's eye splits the frame; his own lightning floods the frame and the next shot burns in through gold; HERO strike (a frozen frame, a leader bolt, two impact frames, a shockwave); the emblem drawn in lightning, fly through the bolt; he passes the lens as a motion wipe; horizontal light streaks; a two-frame impact frame; converging time-remnants | Face track (`bolt_link`, `strike`); previous shot `freeze=True` (`strike`) | Zap / swell / thunder + time-stop / hum + whoosh / doppler / whoosh / hit / shimmer |

The older v4/v5 transitions are still in the file and work as `tin` values: `kaleido`, `rewind`, `flash`, `tiles`, `neon_trace`, `ripple`, `pixel_sort`, `vhs_roll`. Add new transitions to `TR2` as `fn(A, B, j, f, sa, sb)` with `(fn, frames_before, frames_after)`:
- `j < 0`: A is the live outgoing shot and B is the incoming shot's first frame.
- `j >= 0`: A is the outgoing shot's last visible frame and B is the live incoming shot.

### The v103 FOREVER transitions (the standard; in `fx103.py`, copied into every new edit's `fxN.py`)

| tin | What it does | Extra EDL fields | Sound in `audio103.py` |
|---|---|---|---|
| `plastic_rip` | **THE RIP.** The kill-room plastic tears open down the middle on the drop and the flaps fly apart. Pair it with `plastic=(t0, t1)` on the outgoing shot (the sheet is pulled over the lens first). | `plastic=` on the previous shot | crinkle under the build, riser, tear, impact, whoosh |
| `photo` / `photo_l` | The flash fires; the frame freezes into a crime-scene photo that is tossed right or left onto the next shot. Land it on a sung word. | none | flash whine and pop, shutter click, toss whoosh |
| `shutter` | Six gunmetal camera blades snap shut over the shot and open on the next. | none | shutter ticks and a click |
| `pupil_dive` | The camera dives into his eye (via YuNet's eye position); the pupil swallows the frame and a round iris opens on the next shot. | the outgoing shot needs a face track | reverse swell, rush, low boom, whoosh out |
| `torch_blind` | A light in the outgoing shot (flashlight, lamp, headlights) flares into the lens and whites out the frame; the next shot burns in out of the glare, brightest parts first. | a hot light in the outgoing shot | flashlight click, swell, shimmer, bright hit |
| `ripple` | A clear water drop falls, hits, and the rings refract open onto the next shot. | none | drip, bloop, bubbles |
| `wave` | A rolling, refracting wall of sea spray washes across the lens. | none | wash and splash |
| `bubbles_up` | A surge of rising bubbles sweeps up the frame. | none | bubble burst and whoosh |
| `surface` (first shot) / `sink=True` (last shot) | The loop: it opens underwater rising to the surface (meniscus, droplets on the lens) and ends with the bag sinking into the same water. | `T_SURFACE`, `T_SPLASH` | surface break, splash, underwater low-pass across the wrap |
| `strobe`, `roll`, `whip`, `whip_up`, `impact`, `lamp_on`, `light_sweep`, `wrap`, `zipper`, `rainfocus`, `logo_orig` | Engine moves used in FOREVER as connectors between the set pieces. | see the tables above | yes, each |

### The v103 animation layers (EDL knobs and shot flags)

| Knob / flag | What it does |
|---|---|
| `BEAT_PUNCH = [(k, strength), ...]` | `beat_fx`: the camera punches on the beat, a zoom kick with a stronger chromatic hit at strength ≥ 0.9. **Cover every section with drums** (the §0 target). |
| `PULSE_K = [k, ...]` | `pulse_fx` and a heartbeat thump: the frame edges pulse red and the picture thumps on each beat of a quiet build (with a heartbeat sound). |
| `flare=amt` | `anam_flare`: hot lights throw a long horizontal teal anamorphic streak. Keep it off faces (it was turned off on the night-drive shot because it crossed his eye). |
| `swing=True` | `lamp_swing`: a kill-room lamp's pool of light sways across the shot. |
| `plastic=(t0, t1)` | `plastic_sheet`: milky kill-room sheeting with swaying, light-catching folds is pulled over the lens between t0 and t1. |
| `caustics=amt`, `snow=True`, `rain=True`, `moonglow=True` | water light, marine snow, rain on the glass, a glow on the moon. |
| `TEXT` dicts | `style="cap"` (v9 keyline captions; `band=` for QC, optional `ys=`), `style="hero"` (per-letter title; `exit="bubbles"` or `"blood"`). Word times come from `tools/lyrics.py` (lyrics) or `transcribe.py` (dialogue), each on its sung or spoken time. |

### From Studio 1's Flash benchmark (chat 1): the motion pass and the 720p upscale

These live on Studio 1's branch (`claude/gallant-planck-pqpczp`); this copy only records them. Fetch the code from there before relying on it.
- **The motion pass:** speed ramps with smooth slow motion, a beat-synced camera, and light rays, applied to every hook shot. In Studio 2's engine, the closest pieces are:
  - `tmap` ramps (above 1.7x the engine adds shutter blur);
  - `interp="flow"` (for clean slow motion only; check the frames);
  - `beat_fx`, `cam_float` and `anam_flare`;
  - the engine's ray and beam graphics.
- **The upscale:** the 720p packs are cropped to about 405×720 and enlarged to 1080×1920. Studio 2 uses a cubic resample plus a mild unsharp mask in `finish`; Studio 1's upscaler replaces that.

### The v104 THE PASSENGER toolkit (the newest standard; in `fx104.py`, copied into every new edit's `fxN.py`)

| tin / flag | What it does | Sound in `audio104.py` |
|---|---|---|
| `graphic="ink_open"` (first shot) | The pickup: bare paper (frame 0 matches the loop's last frame). An ink sketch of the next shot draws itself, one stroke group per beat (`sketch_fx`), ink creeps in from the corners (`edge_seep`), and a drop forms, swells and falls (`drop_at`). | pen and brush scratches, a plink, a reverse swell |
| `ink_bloom` | The drop lands on the downbeat: a crown of droplets, and the bloom spreads with fingered edges and an ink rim; the picture lives inside the ink. | splat, wet bloom, impact |
| `ink_out=dict(k0)` (last shot) | The loop: the picture drains back into one blob on the same ghosted paper, which pulls into a drop and lifts away. | reverse swell, reversed plink |
| `brush` + `brush=dict(ang, seed, red/white)` | A sumi brush band sweeps across: wet ragged front, dry bristly tail, the next shot behind it. Ivory reads on dark footage, red on light; black disappears on dark. | dry bristle swish |
| `page_turn` | The frame turns over like a sketchbook page: paper on its back, a bright fold, cast shadows. | paper flip + whoosh |
| `ink_bleed` | Ink blooms in from several points and retracts onto the next shot (it leaves gaps: no dead black frame). | reverse swell, wet bloom |
| `spatter` + `spat=dict(k, x, y)` | A two-frame red impact; red ink spatter lands on the lens (organic body, elongated drops pointing away, gloss), hangs, then the heavy drops run. Place it off the face. | splat, impact, drips |
| `passenger` set piece: `passenger=dict(k_rise, k_lunge, cut_y)` on a `seg=True` shot, then `tin="passenger"` on the next | A light comes on behind him and the wall goes to lit paper; his matte shadow (body only, above `cut_y`) is thrown beside him, with a crisp ink edge, a red rim, sway, breathing on the bass and rising smoke; two ember eyes open (masked behind him); push-in with a dutch tilt; the lunge pans to centre and both eyes rush the lens; the next shot surfaces through thinning ink. | lamp click, ember ignite, sub drop, rising drone, reverse swell, impact |
| `window=dict(src, a, k_in, k_out)` on a `seg=True` shot | The silhouette: the world goes to paper, his body becomes a window into another shot, his face stays. | a breath of air |
| `roll` / `quarter_roll` / `spin=(a0, a1)` | The rotation motif (the owner's favourite): a spin into an upside-down shot that keeps turning through its hold; a 90° roll into a rotational blur and out upright. | deep spin whoosh + swell |
| `ghost=a` | Ink ghost trails: darker echoes of the last frames of motion (pair with a speed ramp in `tmap`). | (the cut's own) |
| `motes=a`, `swash=dict(k0, k1, y)`, `flare=a` | Ink motes drifting in depth; an ivory brush swash painted behind a hero word; ivory anamorphic flares. | bristle swish for the swash |
| always on | `cam_float` (a breathing camera on every hold), `beat_fx` (punches with radial motion blur on strong hits), the breathing vignette on `PHR`, `ink_drift` in the shadows. | — |

### The v105 DRACULA toolkit (in `fx105.py`)

| tin / flag | What it does | Sound in `audio105.py` |
|---|---|---|
| `look="day"/"dusk"/"night"` | Per-shot grade: `day_grade` (bleached warm, teal shadows), `night_grade` (cold silver, crimson kept above `redthr`); `dusk_u` slides day → night across `SUN_K` (and back for `daybreak`). | sea air by day, wind and a B-flat drone by night |
| `sun=(x, y)` on a day shot | A sun with light rays (the bright parts streaked away from it, quarter-res), a glow and lens ghosts (`sun_fx`). Dusk shots set it down the right edge, off the face. | — |
| `sun_flare` | A flare crosses the frame at the sun's height and whites it out for a moment. | bright whoosh + glint |
| `bat_burst` | The drop: a 3D cloud of bats pours out of the sky toward the lens, blacks out the frame against a crimson flash, and flies past (depth blur on the near ones). | reverse swell, sub impact, a burst of wings, chirps |
| `bat_swarm` | A river of bats crosses in depth (parallax, size and blur by distance); a band of moonlight travels behind the column so they read; the cut rides its middle. | wings panned left to right |
| `bloodmoon=dict(k0, k1)` on a `seg=True` shot | A procedural blood moon (maria, craters, limb darkening, the Earth's-shadow edge) rises behind his matte, with cloud, bats, a pulse and a red rim on him. | church-bell toll on B-flat |
| `moon_iris` | A circular iris opens from the dark with a crimson rim. | reverse swell, toll, sub |
| `coffin` | A height-map-lit lacquered coffin lid with a brass cross falls to the lens, slams (jolt, dust) and lifts away on the next shot. | hinge creak, wood thud, dust |
| `daybreak=True` on the last shot + `seam_out` | Dawn light rises, the sun comes up low right, the frame burns white, then crossfades into frame 0 (which opens at `SEAM_W` white). | B-flat-minor chord swell, tail wrapped into frame 0 |
| hero `exit="bats"` | The per-letter hero title (red flood) breaks into crimson bats that scatter sideways, away from the face. | a small flutter |
| `fog=a` | Night fog drifting through the shot. | — |
| `cape` | A Dracula cape sweeps across the lens: black satin in broad moving folds, a crimson lining turned out along the billowing edge, a lit hem, motion blur, a shadow thrown ahead; the next shot is behind it. | heavy cloth whoosh |
| `mist` | He turns to mist: the shot softens and rises into billowing silver fog; the next condenses out of it, soft to sharp. | airy breath + hollow whoom |
| `bat_pass` | One great bat flies out of the dark through the lens (soft when near, wing bones in the membrane, fine crimson edge); the cut is in its shadow; it dives out under the camera. | three heavy wingbeats, whoosh, chirps |
| `motes=a` on a day shot | Sunlit dust: drifting motes, brighter near the sun, sharp far and soft near, kept behind him with the matte. | — |
| `seg=True` on a sun shot | The sun sits behind him: disc and rays only from the sky, a light wrap on his near edge, ghosts dimmed by how much he covers. (rev 2 fix: the sun used to be laid over his hair.) | — |
| `eclipse` | The sun goes out: the moon's black disc slides across with a streaming corona, the next shot inside it, a diamond-ring flash on its rim, then the disc swells to fill the frame. | reverse swell, deep impact, shimmer, low bell |
| `card_flip` | A 3D card flip around the vertical axis against the bright blurred sky of both shots (a sun glint edge-on). | whoosh + flick |
| `palm_sweep` | Procedural palm fronds sweep past the lens (depth blur, dappled light); the next shot comes in their shadow. | leaf rustle + whoosh |
| `gather=True` (+ `seg`) | Bats gather in the sky behind him through the shot, more and more toward its end. | — |
| `rim=a` (+ `seg`) | A pulsing crimson backlight on his edge. | — |
| ASHES TO SUN (`daybreak` on the last shot; `ASH`, `SUN_T`, `seam_out`) | The loop: he burns like paper (char, glowing line, the street behind him, row-continued); 3,000 embers spiral into the sun at frame 0's sun position; the sun flares over the frame and the light collapses back into it, revealing frame 0. | crackle, hiss, riser, flare impact + shimmer, reverse swell, bloom on the loop |
| `daybreak=True` + `seg=True` | He burns in the sunlight: a flickering hot rim on his edge, embers lifting off his hair and shoulders, then the white. Needs a shot with a clear silhouette (not a frame-filling close-up). | sizzle + crackle |
| always on | `render_shot` upscale: Lanczos + a noise-gated luma detail boost (not AI super-resolution). `finish105`: warm or moonlit halation and a crimson bloom (skipped on logo frames). | — |

## 3. Graphics and text

- **v9 graphics and type** (`render9.py`, end of file):
  - `freeze_e=E` on a shot: a dead freeze on the song's silence with 2.5-D parallax (matte vs. background), violet drain and a moonlight rim;
  - `petals=density`: a jasmine-petal depth field (behind the person matte, soft bokeh in front that keeps off the face; it freezes with the picture);
  - `graphic="moon"`: a still blood moon on a generated night sky with moonlit wisps;
  - TEXT style `cap` (**the approved standard text, "it was perfect"**): bold two-line captions with a dark keyline and soft shadow, auto-fit to 940 px, red emphasis (`emph`), optional `from` and `big`;
  - TEXT style `hero`: per-letter bloom-in on a shared baseline; line 2 floods crimson from the bottom; the exit blows the letters away as petals;
  - `accents9`: soft strobe lifts on every clap after the drop.


- **Captions** (`CAPS`): two-line retro lockups. Each word eases in on its spoken time (fade, rise, blur-to-sharp) with pink and cyan echoes; emphasis words are chrome. The `vanish` style dissolves into pixels.
- **Drop title** (`DROP_TITLE`): a chrome word sweeps in from the left, with a light sweep.
- **End words** (`END_CAP`): neon tubes that ease in and flicker on, word by word, and spill coloured light onto the face.
- **v7 graphics:**
  - evidence markers (`markers=True`) drop in on the beat;
  - the CASE CLOSED rubber stamp (TEXT style `casestamp`);
  - the kill-room plastic layer with the luminol title (`plastic=True`);
  - the magnifying-glass lens frame (`lensframe=True`);
  - blood spatter hits on montage beats;
  - the forensic viewfinder.
- **Shot flags:**
  - `vapor_bg`: the person stands in the vapor world, then reality tunes in scanline by scanline (person matte);
  - `palms`: palm-frond shadows;
  - `motes`: bokeh specks;
  - `echo`: VHS colour trails;
  - `pause=FRAME`: VHS ‖ PAUSE freeze with jitter;
  - `vanish`: pixel-dust dissolve, timed by `VANISH_T0`.
- **Montage** (`MONTAGE` half-beat range): beat bounce, glints, light leaks and hits on the downbeats.
- **Finish:** bloom, anamorphic streak, VHS chroma bleed and scanlines, vignette, grain. The OSD is limited to PLAY ▶ at the start, ◀◀ REW at the end and ‖ PAUSE. **No SP counter or timecode.**

- **v101 / v102 graphics (Studio 2).** These are built on the v7 engine, not v9: port a piece into the v9 engine before reusing it.
  - v101 (look rejected): a liquid-light projection behind the person matte; prism silhouette echoes on bass accents; a 16 mm film finish.
  - v102 (The Flash):
    - `sarcs` lightning that hugs the silhouette (person-matte contour);
    - `echoes` matte afterimages;
    - `motes` frozen-time sparks in depth;
    - `eyespark` arcs off the YuNet eye landmarks;
    - `freeze` (a colour drain on a held frame);
    - `rot` (a sideways source rotated to fill 9:16);
    - an electrified slammed title.
- **Is he really saying it?** Run `python3 tools/lipcheck.py SRC t0 t1 OUT.jpg --vocals STEM.wav [--stem-t0 S]`. It draws face and lip crops every 0.1 s with the speech level under them. The lips must move with the bars before a line is used as lip-synced. (An automatic mouth-motion score disagreed with known cases, so judge it by eye.)

## 4. Pitfalls that cost time in v6 (check these first)

1. **Override layering.** `renderN.py` contains several `render()` functions, and the **last one wins**. When inserting routing with a string replace, target the active `render()` (after the "v6 frame" marker) or the change silently does nothing.
2. **Optical flow fails on lighting jumps** (police lights, flashes) and leaves dark blocky blotches. The sampler already falls back to a blend when consecutive frames differ by more than 6 levels; keep that fallback.
3. **Angle morphs can't be seamless.** Morphing an unfolded frame into a kaleidoscope fold always leaves a wedge seam. Dissolve into the full fold instead.
4. **`cv2.putText` only draws on 8-bit images.** The frames are float, so draw shapes or use the PIL `text_mask` helpers.
5. **Motion blur must match the real per-frame speed**, not a guess. The film strip smeared because its blur was about 30× too long.
6. **Face landmarks under caps and sunglasses** sit on the top edge of the lenses. Give lens transitions the real lens shape per shot (`lens=`).
7. **Faces wider than the 9:16 window** (big profiles, two-shots): check the YuNet width before picking a shot (`analyze.py` sheets print `w`) and reject anything over about 400 px of a 720p source.
8. **Titles must end before the next transition starts.** MIAMI over the cube looked broken.
9. **Quiet-section transitions and VO:** keep caption lines inside 1280–1640 px and keep them two-line, never one long line.
10. **Never wait on a full render to test a transition**: use `auto`, `stills` and `clip`.
12. **Packs hide cuts the shot detector misses** (a jump to a closer angle, the next scene starting a few frames early). Interpolating across them makes a ghost frame, and running a source range past the shot's end puts another actor on screen. The sampler now holds frames across hard cuts; `tools/check_sources.py N` (run automatically by `build.sh N prep`) now fails any shot whose source range leaks past a source cut (found twice on v7).
13. **Text vs very tight close-ups:** a face box that fills the 9:16 frame leaves no text-safe band. Swap the shot (v7: the "Could it be him?" close-up → kill-room floor) rather than shrinking the type.
11. **CJK subtitles and VHS counters read as clutter** to the user. Don't add them.

## 5. What made v6 the benchmark (carry the principles, not the look)

- **A concept that ties picture, sound and text together:** VO about disappearing, then he dissolves; the drop goes *through* a CRT; the ending confession lights up word by word; the loop is a tape rewinding into static, then the tape loading.
- **The music drives the structure:** the cold open sits on the song's filtered build, and the full-mix return lands exactly as the camera passes through the screen. Every cut sits on the half-beat grid.
- **Every transition is designed, "goes through something" and has its own sound.** No plain cuts.
- **Text is meaningful (the character's own words), eased in, two lines, and designed per moment.**
- **Built-in review passes** caught real problems before delivery, every time.
