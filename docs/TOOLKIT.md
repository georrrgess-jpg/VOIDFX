# voidfx toolkit: how an edit gets made (fast)

The engine lives in the benchmark edit `v6/work/` (WARMPOP). New edits copy it with `tools/new_edit.py` and change only their EDL. **Copy the engine, not the look.** Every edit gets its own grade, type and transition mix.

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

The older v4/v5 transitions are still in the file and work as `tin` values: `kaleido`, `rewind`, `flash`, `tiles`, `neon_trace`, `ripple`, `pixel_sort`, `vhs_roll`. Add new transitions to `TR2` as `fn(A, B, j, f, sa, sb)` with `(fn, frames_before, frames_after)`:
- `j < 0`: A is the live outgoing shot and B is the incoming shot's first frame.
- `j >= 0`: A is the outgoing shot's last visible frame and B is the live incoming shot.

## 3. Graphics and text

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

## 5. What made v6 the benchmark (carry the principles, not the look)

- **A concept that ties picture, sound and text together:** VO about disappearing, then he dissolves; the drop goes *through* a CRT; the ending confession lights up word by word; the loop is a tape rewinding into static, then the tape loading.
- **The music drives the structure:** the cold open sits on the song's filtered build, and the full-mix return lands exactly as the camera passes through the screen. Every cut sits on the half-beat grid.
- **Every transition is designed, "goes through something" and has its own sound.** No plain cuts.
- **Text is meaningful (the character's own words), eased in, two lines, and designed per moment.**
- **Built-in review passes** caught real problems before delivery, every time.
