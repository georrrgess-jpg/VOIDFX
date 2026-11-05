# voidfx toolkit: how an edit gets made (fast)

The engine lives in the newest standard, `v11/work/` (BOP rev 4; `v10/`, `v7/`, `v6/` and `v4/` remain benchmarks). It contains every v4–v11 transition and graphic, the restored-source sampler, velocity with optical flow, the beat camera, the v9 text system and the v11 pieces (rival grade, red effects, bolt split, red eye dive, clash, rift, the procedural Reverse-Flash emblem and coin flip, the REVERSE loop, the beat moments). New edits copy it with `tools/new_edit.py`, then write their EDL and **their own frame function** (`render()` at the end of the renderer: grade, text, graphics, finish) and sound design. **Copy the engine, not the look.** Every edit gets its own grade, type and transition mix. Owner preferences and lessons: `studio/VOIDFX_STUDIO.md`; sources: `studio/SCENE_PACKS.md`.

## 1. Pipeline and timings

Timings were measured on this 4-core box for a 26 s edit.

| Step | Command | Time |
|---|---|---|
| Scaffold | `python3 tools/new_edit.py N SLUG "TITLE"` | 1 s |
| Map the song | `python3 tools/song_map.py src/SONG.mp3 vN/work` | 3 s |
| Shot lists | `python3 vN/work/analyze.py src/PACK.mp4 TAG` (contact sheets, per-shot stats) | ~1 min per pack |
| Dialogue / lyrics | `python3 tools/transcribe.py vN NAME MEDIA [--vad] [--start S --dur D]` | 1–3 min |
| Voice under score | `python3 -m demucs -n htdemucs --two-stems=vocals -o vN/audio/sep CLIP.wav` | 15 s per 30 s clip |
| Tracks and mattes | `bash tools/build.sh N prep` | ~35 s |
| **Source restoration** (v10 rev 3) | `nohup python3 tools/sr_prep.py N &` right after `prep`: Real-ESRGAN compact restores and 2× upscales only the band each frame is cropped from; the renderer uses it automatically | ~3 s per source frame (45 min for 900 frames, in the background while you build) |
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
| `phase` (v10 r3) | He vibrates through the frame: jittered chromatic copies, row shimmer, every edge lit gold; the next shot shows through for a few frames, then settles | — | Rising saw buzz, whoom |
| `whirlwind` (v10 r3) | The frame twists into a spiral round the eye of a storm (angular blur, wind and debris torn round); the next shot unwinds out of it | — | Wind swirl circling the stereo field |
| `lichtenberg` (v10 r3) | A branching lightning figure grows from his chest (stopping short of his face); the next shot opens inside the branches | — | Growing crackle, snap |
| `lens_shatter` (v10 r3) | A bolt flies at the camera and hits the lens; electric cracks, then the glass bursts toward us in Voronoi shards | — | Whine, glass break, impact |
| `perimeter` (v10 r3) | A lightning streak runs laps round the frame edge; the next shot fills in as a spiral wake closing on the centre | — | Swirl pass, crackle |
| `frozen_shatter` (v10 r3) | In frozen time the frame cracks and the shards hang apart; the beat that restarts time blows them away | `frozen=True` shots | Dull crack, then a glass burst on the hit |
| `time_particles` (v10 r4, replaces `frozen_shatter`) | The frozen moment comes apart into fragments of its own pixels (edges first, people last), they burst and hang in the stopped air, then swirl back together as the next moment from `pfocus` outward, landing on the hit | `pfocus=(x, y)` output px on the incoming shot | Disintegration grains, shimmer, reversed grains into an impact |
| bullet time (v10 r4, automatic on `frozen=True` holds) | In each frozen hold the camera glides through the moment in 3-D: depth from the MODNet matte + a floor gradient drives a parallax remap, plus a dolly push | — | Soft panned air |
| `carry` text (v10 r4) | A lightning runner streaks along the line and drops each word off on its onset; at the end it snatches the letters away (stretch + blur + gold trail) | — | Zips + crackle |
| `rift` (v11 r4, focal point) | A rift tears across the frame (a diagonal path below the face): a crack grows from the centre, splits into a jagged lens with electric edges and light spill; the Speed Force (`speedforce_bg` + lightning) churns inside; the camera flies through; the next shot rushes out of the vanishing point | `rift_geom()` path | Crack, panned rip, reversed swell into a sub drop, roar and whine, arrival impact |
| Reverse-Flash emblem + coin flip (v11 r4) | `rf_emblem(R)`: a procedural, bevelled, lit emblem sprite; `coin_flip()`: the real emblem flips on its axis (edge thickness, inpainted suit behind) to reveal it; flare at edge-on, shockwave and sparks on landing | emblem tracked by a circle fit in the source | Spin whir, sizzle, metal ring |
| REVERSE loop (v11 r3) | `reverse_loop`: a red bolt strikes the tracked chest emblem (found in the source each frame: the cream disc, bolt bridged by a morphological close); the real emblem inverts in place (disc to glossy black, gold to red, shading kept); red radiates over the suit; the camera dives through the black disc, a portal onto frame 0, and lands exactly on it (seam diff 0.10) | `E_STRIKE/E_RADIATE/E_DIVE`, the first shot's `tin="loop_in"` | Thunder, reversed shimmer and boom, crackle and buzz, rush, landing impact |
| `aura=`, `remnants=`, `charge=` (v11 r3) | Beat moments for shots where he only moves to the beat: silhouette rings pulsing out on each beat; time-remnant copies splitting sideways and snapping back; lightning and dust gathering into the chest emblem | per shot (`seg=True`) | Sub pulse and shimmer; doubled panned whoosh; rising hum and crackle |
| `red_eye_dive` (v11 r2) | Dive into the rival's glowing red eye (auto-found: brightest red point) until the frame is red light, then pull out of Barry's eye (face-track landmarks) | — | Power-up whine, rush, sub drop |
| `strobe_echo` (v11 r2) | The frame snaps sideways leaving gold stroboscopic afterimages; the next shot lands with its echoes collapsing | — | Stuttered passes, zap |
| `bolt_trace` (v11 r2) | A zig-zag bolt crosses below the face; the next shot burns in along it (distance transform, ragged ember rim) | — | Panned crackle, fire whoosh |
| `heat_haze` (v11 r2) | Heat rises up the frame (refraction), carrying the next shot in behind a glowing wall | — | Fire roar |
| `clash` (v11 r2) | Red and gold bolts race in from opposite sides and collide; two-colour spark burst + refracting shockwave | — | Two zaps, impact, thunder |
| `bolt_split` (v11) | A lightning-bolt seam cracks down beside the face; red vs gold halves; the seam sweeps across on the drop (tears the title) | — | Crackle build, impact, thunder, sub drop |
| `red_phase`, `red_link`, `red_streak`, `dolly`, `whip`, `speedforce_in`, `emblem_flash` (v11) | The rival's red vibration / arc / streak; a focus-pull dolly; a whip pan; a radial Speed Force pull; the emblem drawn in light where the next shot's chest emblem is | — | each in `audio11.py` |
| `ember=`, `fire=`, `dust=`, `speed=` (v11 r2) | Depth particles (`motes11`): behind the subject through the matte, front ones masked off the face | per shot | — |
| velocity (v10 r5) | `tmap=vel(e0, e1, a, b, lo, hi, tau), lin=True, interp="flow"`: a speed burst on every beat, slow motion between; flow in-betweens run on the restored 2× bands (`sr_flow_part`) | EDL helper `vel()` | The music; optional swish per punch |
| beat camera (v10 r5) | `beat_bounce` 6 % zoom punch + `shake` rotation kick per beat in the hook; `beat_fx` zoom blur + colour split on the hit frames | — | Quiet swish |
| `rays=` (v10 r5) | Screen-space god rays from the brightest warm light (quarter res, 20 samples); scaled down when the frame is already bright | per shot | — |
| `wave=True` (v10 r3) | After the drop: a refracting dark-matter ring rings out of the frame centre | on the drop shot | Sub drop |
| `tunnel_in` + `graphic="tunnel"` (v10 r3 loop) | The letters of a lyric run a ring that opens into the Speed Force; panels of the edit's own moments fly past newest to oldest and frame 0 lands | `T_OPEN`, `TUN_PANELS` | Ring crackle, swirl, panel whooshes, the song rewinding (box-filtered) |

The older v4/v5 transitions are still in the file and work as `tin` values: `kaleido`, `rewind`, `flash`, `tiles`, `neon_trace`, `ripple`, `pixel_sort`, `vhs_roll`. Add new transitions to `TR2` as `fn(A, B, j, f, sa, sb)` with `(fn, frames_before, frames_after)`:
- `j < 0`: A is the live outgoing shot and B is the incoming shot's first frame.
- `j >= 0`: A is the outgoing shot's last visible frame and B is the live incoming shot.

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
14. **Whisper word times drift on sung, held notes** (v10: up to 1.1 s early on "All this running around", ~0.2 s late on others). Before captions go in, check every word against the Demucs vocal stem: a 30 ms RMS + pitch track shows where each syllable starts, and the line's parallel phrase (verse 1 vs verse 2) confirms it.
15. **A 720p pack cropped to 9:16 is a 2.7× blow-up.** Run `tools/sr_prep.py` (restoration + 2× from the network) instead of cubic + unsharp mask; the renderer drops the unsharp mask to 0.16 on restored frames.

## 5b. What made v11 the standard (carry the principles, not the look)

- **A concept found in the material:** the song's spoken "Harrison" became the whole edit (the Reverse-Flash rivalry): a second grade for the rival, red against gold at the drop (the bolt split), the gold winning on the punch (the clash), the red taking the symbol at the end (REVERSE).
- **One focal set piece:** THE RIFT, on the bar line after the charge-up: a tear grows, opens with electric edges, the Speed Force inside, the camera flies through, the next shot rushes out of the vanishing point.
- **Detailed hero assets on real objects:** the procedural Reverse-Flash emblem (bevel, brushed rim, groove, glossy disc, emissive bolt, light spill, matched to the shot) revealed by a coin flip of the tracked real emblem (circle-fit each frame, the suit inpainted behind it).
- **Beat moments for "moving to the beat" shots:** aura rings, time remnants, a charge-up, each with a sound.
- **A loop that lands:** the dive ends on frame 0's own image (seam 0.11), and the beat camera rests during it.
- **Measured finish:** flash brightness measured in the encode, particles masked off faces, every new effect checked at full resolution.

## 5a. What made v10 the standard (carry the principles, not the look)

- **Motion first.** Velocity on every hook shot (`vel()`: a burst on each beat, ~0.3–0.6× flow slow motion between, the same source range), the beat camera (6 % punch, ±1.1° kick, zoom blur + colour split on the hit frames), bullet time in frozen holds. Without this, effects on static shots read as lacklustre.
- **Quality.** `tools/sr_prep.py` restoration on every 720p pack; flow in-betweens run on the restored bands (`sr_flow_part`), so slow motion stays sharp.
- **Set pieces from the character's world** on the drop (emblem dive + drop wave), the hook (lens shatter, perimeter lap), the freeze (time particles) and the loop (the AROUND ring → the Speed Force → frame 0), with signature moves between them (phase, whirlwind, lightning branches), each with its own layered sound.
- **Type on the sung onsets**, every word verified on the vocal stem; each lyric moment acts out its meaning (runner drop-off and carry-off, the charge fill, the ring).
- **Graphics with depth that react to the footage:** the matte-aware whirlwind and ribbons, light rays from the real lightning, edge arcs on the silhouette.
- **Reviews:** stills of every transition at full size, the loop seam measured (blurred diff ≤ 1), QC flags checked visually and written into the README.

## 5. What made v6 the benchmark (carry the principles, not the look)

- **A concept that ties picture, sound and text together:** VO about disappearing, then he dissolves; the drop goes *through* a CRT; the ending confession lights up word by word; the loop is a tape rewinding into static, then the tape loading.
- **The music drives the structure:** the cold open sits on the song's filtered build, and the full-mix return lands exactly as the camera passes through the screen. Every cut sits on the half-beat grid.
- **Every transition is designed, "goes through something" and has its own sound.** No plain cuts.
- **Text is meaningful (the character's own words), eased in, two lines, and designed per moment.**
- **Built-in review passes** caught real problems before delivery, every time.
