# HIM ALL ALONG — Dexter × Gunna "Him All Along" (voidfx v7, 9:16)

This is a 25.84 s, 1080×1920, 60 fps TikTok edit built to `/CLAUDE.md`, with benchmarks v6 (WARMPOP) and v4 (SURPRISE). It uses the two new packs: the S1 4K pack (`src/pack8_s1.mp4`) and the 4K 60 fps pack (`src/pack7_4k.mp4`).

## Concept: the evidence points back at him

The friendly blood-spatter analyst investigates, and the evidence keeps pointing at Dexter himself. The look is **forensic noir**, new for this edit and unlike v6's pastel VHS:
- drained cold colour and teal-black shadows;
- blood red is the only warm colour;
- UV-luminol blue-white for the "evidence";
- red halation and a monospaced case-note type.

**Act 1, investigation.** This plays over the song's vocal breakdown.
- The edit opens through a magnifying glass on his eye. Gunna: *"on the way to reaching my goals … open … close"*, and steel doors slam on "close".
- Dexter's own lines, lip-synced, take over the beat (Gunna's vocal steps aside): *"A jar of blood. Dramatic. Cryptic. Playful. Could it be him?"*
- Gunna answers *"stay strong"*: blood-spatter strings run to the point of origin, which is Dexter's face.
- *"HIM ALL ALONG"* glows in luminol on hanging kill-room plastic.

**Act 2, the drop.** The plastic **rips open** on the song's biggest return: 2:13, +17 dB, found by `tools/song_map.py`. A kill-room montage follows on the beat.

**Act 3, confession.** *"I'm a serial killer."* (lip-synced). The camera dives into his pupil and goes to black, and the loop re-opens through the magnifying glass on his eye.

## Song window

130 BPM, half-beats 528 → 640: **14 whole bars**, 2:01.9 → 2:27.8, so the loop jumps bar 80 → bar 66 in tempo. The drop is at 11.08 s, h576, bar 72.

## Timeline

| Time | Picture | Transition in (each has its own sound) |
|---|---|---|
| 0.00 | His eye through a **magnifying glass** (the lens stays on screen as a frame). Gunna: *on the way to reaching my goals* | **Lens opens from black** (glass ring) |
| 1.85 | Blood slide held up to the light | **Microscope**: dive into his eye → red blood cells under a reticle → out of the drop on the slide (servo, focus clicks) |
| 3.69 | *"A jar of blood."* (lip-synced) | **Steel doors** slam shut on "CLOSE", then swing open (slam, creak) |
| 5.08 | Crime-scene tape. *"Dramatic."* | **Redaction bars** slam across and wipe off (marker strokes) |
| 5.54 | Lit red at the desk. *"Cryptic."* | **UV luminol sweep**: a blacklight beam crosses the frame and hidden spatter fluoresces (lamp buzz) |
| 6.00 | Lollipop. *"Playful."* | **Fingerprint**: ridges ripple outward with the next shot between them (scanner) |
| 6.46 | The answer: Dexter, gloved, on the kill-room floor. *"Could it be him?"* | **Crime-scene tape snaps** as the camera pushes through (stretch → snap) |
| 9.23 | His smirk. *"stay strong"*, then **HIM ALL ALONG** in luminol on the plastic sheet | **String method**: stains shoot red strings to the point of origin, his face, with a target ring (string twangs) |
| 11.08 | **Drop:** red kill room | **Plastic rips open** (riser, rip, sub impact) |
| 12.00 | Over the table | **Knife slash** (swish, steel ring) |
| 12.92 | Plastic-wrapped room | **Evidence board**: pinned photos, red string to the next photo (pins, string pull) |
| 13.84 | Overhead on the table | **Shadow pass** |
| 14.77 | Night drive, lit red | **Headlight streaks** (passing cars) |
| 16.61 | South Beach at night | **voidfx logo revealed by UV light**, fly through the "o" (the only logo appearance) |
| 17.54 | Sweat, syringe | **Crime-scene polaroid** (flash, shutter) |
| 19.38 | Green-lit stare | **Forensic scanner** line (scan sweep) |
| 20.31 | Looking up, lit red | **Luminol negative strobe** on the beat (flash bulbs) |
| 22.15 | *"I'm a serial killer."* (lip-synced; the show's own jump to a closer angle lands on "I'm") | **Blood-slide box**: the frame shrinks into a drop on a glass slide, glides to the next slide, dives in (glass clinks) |
| 25.4 → 25.84 | Into his pupil → black → loop | **Pupil dive**, a tape-stop of the song, heartbeat |

**Graphics:**
- a **forensic viewfinder** through act 1: corner brackets and a moving measuring ruler;
- **blood spatter** hits the edge of frame on the montage beats;
- red **halation** on highlights;
- the magnifying-glass lens frame;
- hanging kill-room plastic with luminol type.

## Text

Every word eases in on its sung or spoken time (fade + rise + blur-to-sharp), inside the 1240–1600 px band. Each moment has its own design:
- **Case-note lockups** in monospaced type (ON THE WAY TO / REACHING MY **GOALS**, A JAR OF **BLOOD.**, COULD IT BE / **HIM?**, STAY **STRONG**), with a blinking case-file caret and typewriter clicks.
- **Stamp words** (DRAMATIC. CRYPTIC. PLAYFUL.) punch in with a blood-red offset echo.
- **OPEN / CLOSE** on the steel doors.
- **HIM ALL / ALONG** in luminol: a UV sweep reveals each word, smeared and dripping.
- **I'M A / SERIAL KILLER.** with dripping blood-red type.

## Sound

- **Dialogue:** Dexter's lines come from a Demucs vocal stem of the pack audio, levelled to a speech-RMS target, with equal-power fades and a little room.
- **Vocal swap:** Gunna's vocal is swapped for the song's own **instrumental stem** under Dexter's lines (equal-power swap), so the beat never stops. It returns on *"stay strong"*.
- **Bed:** a dark room-tone drone runs through everything, including across the wrap, with a heartbeat under act 1.
- **Every transition and text moment has its own synthesised sound.**
- **Ending:** a tape-stop into the pupil dive.
- **Build:** circular timeline, mastered on a wrapped copy to −13 LUFS with the true-peak limiter at −3.4 dB, measured after AAC.

## Built-in review (while building)

The every-cut review sheets (`build.sh 7 auto`) and targeted stills caught these before the final render:
1. **Magnifier opening:** the 9:16 crop centred on his nose and the magnifying glass was lost. It was reframed onto the eye, with the glass kept on screen as a lens frame.
2. **Plastic sheet:** it read as zebra stripes. It was rebuilt as a few soft swaying folds and creases.
3. **Confession shot:** zoomed 1.75×, it was too soft. It was reduced to 1.12–1.36×.
4. **SERIAL KILLER.:** it ran off both edges, so it was resized.
5. **Headlight streaks:** they washed out to white; the flash was reduced.
6. **Logo:** moved below the face.
7. **Blood-slide box:** the drop showed the next shot's background instead of his face, so the inner framing was fixed.
8. **Blood hits:** they were round blobs; now they are directional spatter with spines and mist.
9. **True peak:** the AAC check read −2.5 dBTP, right at the limit, so the limiter was tightened.

### Checkpoint run 1: **NOT READY** (not shipped)

Automated results: 8 of 10 criteria passed.
- −13.4 LUFS / −3.2 dBTP after AAC.
- 0 clicks at cuts and at the loop seam.
- Frame count, decode, no freezes, and audio and video the same length all passed.

Two criteria failed, and frame review confirmed real problems behind most of the flags:
- **Text over face (36 frames):**
  - The *"Could it be him?"* close-up filled the entire 9:16 frame (face box 349–1895 px), so no text position could clear it. It was **replaced** with Dexter gloved on the kill-room floor, which is a stronger answer to the question.
  - **HIM ALL ALONG** on the plastic reached his chin. It is now two lines, HIM ALL / ALONG, below the face.
  - **OPEN** was still fading while **CLOSE** landed on the same spot. OPEN now clears first.
- **False positives** (checked on frames):
  - two round pink blood drops on the glass slide read as a pair of eyes (4 frames);
  - the magnifier's lens is entirely face (1 frame).
- **Face centering:** the only failing shot is the subject-less South Beach street shot, where a building facade read as a face. QC now skips shots the EDL marks `face=None`.

The edit was re-rendered and the checkpoint run again.

### Checkpoint run 2: automated PASS, **visual sign-off FAIL** (not shipped)

All automated criteria passed. The only text flags left were the 5 known false positives. Frames pulled from the encoded MP4 still showed two defects the automated checks can't catch:
- **Ghosted frame (1424):** the S1 pack hides a camera cut at 325.217 s, a jump to a closer angle on *"I'm"*, which the shot detector missed. Frame interpolation blended across it. The sampler now **never interpolates across a hard cut** and holds the nearest frame instead. This guard was also added to the v6 engine.
- **Another actor in the pupil dive:** the confession's source range ran 0.14 s past the end of Dexter's shot. The source window was shifted 0.15 s earlier at the same 1:1 speed, so the lip-sync stays exact.

Both lessons were added to the pitfalls list in `docs/TOOLKIT.md`. The edit was re-rendered and the checkpoint run a third time.

### Checkpoint run 3: automated PASS, **visual sign-off FAIL** (not shipped)

Frames from the encoded file showed **an upside-down head for 3 frames** as the doors open. The jar shot's source range started 0.1 s before its source cut, so frames from the previous shot (an overhead of a victim) leaked in. This was the same class of bug as run 2, so it is now caught by a tool:
- `tools/check_sources.py` audits every shot's source range against the detected cuts, and `build.sh N prep` runs it automatically.
- On v7 it found the jar shot and nothing else.

The jar now starts after the cut, and *"A jar of blood"* moves with it, so the lip-sync is unchanged. The look-up shot got one frame of margin before its cut, and CLOSE now fades out before the doors open.

### Checkpoint run 4 (final): **SHIP**

| Criterion | Result |
|---|---|
| Format | PASS: 1080×1920, 60 fps, 1,551 frames, 25.84 s |
| Decode | PASS: clean |
| Loudness | PASS: −13.5 LUFS, true peak −3.2 dBTP (after AAC) |
| Frozen runs | PASS: none |
| Face centering | PASS: every shot; 1 frame flagged, mid-microscope dive |
| Text over faces | PASS: 5 frames, all checked false positives (the blood drops on the slide read as eyes; the magnifier lens is entirely face) |
| Audio clicks | PASS: 0 at 17 cuts and at the loop seam |
| Loop seam | PASS: black → black; the pupil dive loops into the magnifying-glass opening |
| A/V length | PASS: identical |
| Source ranges | PASS: every shot sits inside its own source shot (`tools/check_sources.py`) |
| Visual sign-off | PASS: 32 key frames across the edit plus every transition, pulled from the encoded MP4 |

The near-black frames are all by design:
- frame 0 (lens opening from black);
- frames 828–830 (bottom of the shadow pass);
- frames 1215 and 1221 (strobe blackouts);
- frame 1550 (pupil black).

## Files

- `out/him_all_along_dexter_voidfx_9x16.mp4`: upload version.
- `out/him_all_along_dexter_voidfx_9x16_master.mov`: master.
- `work/edl7.py`: every decision, including the dialogue placements and the word-timed text.
- `work/render7.py`: the v6 engine plus the v7 forensic-noir toolkit (14 new transitions, graphics and type).
- `work/audio7.py`: sound.
- `work/qc7.py`: the review and ship checkpoint.
- `work/song_map.json`, `tr_*.json`: song grid and transcripts.

### Re-render

```bash
bash tools/build.sh 7 prep audio auto
bash tools/build.sh 7 video qc
```

The stems need to exist first:

```bash
python3 -m demucs -n htdemucs --two-stems=vocals -o v7/audio/sep v7/audio/song_110_150.wav
python3 -m demucs -n htdemucs --two-stems=vocals -o v7/audio/sep v7/audio/p8_dialogue.wav
```

`song_110_150.wav` is the song from 110 s to 150 s, and `p8_dialogue.wav` is pack8 from 318 s to 338 s, both at 44.1 kHz.

## Limitations

- **I can't watch or listen.** Everything was verified by frames and measurement. Watch once with sound before posting.
- **Sources are 720p.** The magnifier shot is very soft in the source; the lens frame and grain make that read as intentional.


## Revision 2 (user feedback)

**Removed:**
- the *"A jar of blood"* scene;
- the *"Dramatic. Cryptic. Playful."* run, with its stamp words and quick cuts;
- the STAY STRONG text and the string-method lines to his face;
- the *"I'm a serial killer"* ending.

The only dialogue left is *"Could it be him?"*, answered by Gunna's "HIM ALL ALONG". Gunna's vocal now plays through the breakdown and steps aside only under that one line.

**Logo:** back to the supplied voidfx logo in its own colours, slammed in and flown through the "o". `CLAUDE.md` now says never to recolour it unless asked.

**New CLOSE, Dexter-themed:**
- On "close", **Dexter's rosewood blood-slide box** slams shut over the frame. The lid has wood grain, brass corners and hinges, and CLOSE is **engraved on a brass plate**, with a glint sweeping across it.
- There is a dust puff and a shake, then the lid swings open on the slides in red velvet, and the camera dives into a blood drop on a slide to reach the next shot.
- Sound: creak, a heavy wood slam, the slides rattling, a latch, a glass clink and a drop.

**New hero transition out of HIM ALL ALONG:** the kill-room plastic carrying the luminol title **stretches toward the camera**, then **bursts open in flaps** on the drop, with blood spray, a shock ring and a flash. Sound: plastic stretching, a riser, a rip, a sub impact and a splash.

**New transitions:**
- **Blood on the lens:** a drop falls, splats, and the next shot is seen through the blood as it drips clear.
- **Body-bag zipper:** zips shut, then unzips onto the next shot.
- **M99 sedative:** double vision, the eyelids close, the music goes muffled, and the next shot blinks open.
- **Magnifying-glass sweep for the ending:** the glass sweeps over his smirk, his stare is inside it, then the camera dives into his pupil and the edit loops to the magnifier opening.

**New graphics:**
- crime-scene **evidence markers** (1, 2, 3) drop in on the beat;
- a **CASE CLOSED** rubber stamp slams onto his smirk at the camera.

**More sound:** every new transition and graphic has its own sound, as above, plus:
- marker clacks;
- the plastic rustling in;
- a luminol spray hiss before each glowing word;
- wet splats on the montage blood hits;
- the stamp thunk;
- a muffled-world dip under the M99 blink.

**Review while building** (every-cut sheets plus targeted stills):
- The pre-burst bulge warped the title, so it was rebuilt as a centre-weighted bulge.
- The blood spray lingered like petals, so it is now fast streaks.
- The rosewood grain was too regular, so it is now finer with fibres.
- The ending eye shot framed the gap between his eyes, so it was replaced with Dexter's kitchen stare.
- The stamp ink was too faint and was darkened.
- A zipper shading bug was fixed.
- True peak after AAC was −2.5 dBTP, so the limiter was tightened.

### Revision 2 checkpoint: **SHIP**

- **Automated criteria:** all PASS.
  - 1,551 frames, clean decode.
  - −13.6 LUFS / −3.6 dBTP after AAC.
  - No frozen runs; every shot centred.
  - 0 clicks at 17 cuts and at the loop seam.
  - Audio and video identical in length.
  - Every source range sits inside its own shot.
- **Text flags (4 frames), all checked:**
  - two known false positives: the slide's blood drops read as eyes, and the magnifier lens is entirely face;
  - 2 frames where the magnifying glass, carrying his face, sweeps across the fading stamp.
- **Visual sign-off:** 32 key frames pulled from the encoded MP4, covering the slide-box lid and engraving, the dive into the drop, the evidence markers, the blood on the lens, the bulge and burst, the zipper, the original logo, the M99 blink, the CASE CLOSED stamp and the magnifier-to-pupil ending.
