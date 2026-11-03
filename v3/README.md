# SURPRISE — Doakes × Need It (voidfx v3, 9:16)

A 26.4-second, 1080×1920, 60 fps TikTok edit built in code from all five scene packs plus the
"Doakes catches Dexter" scene, cut to Migos "Need It" (ft. YoungBoy Never Broke Again).
The style is deliberately different from v2 (no comic ink): full-colour cinematic grade with bloom,
face-tracked motion graphics, and designed transitions.

## Story

| Time | Section | What happens |
|---|---|---|
| 0.00–6.50 | **Cold open** (scene audio) | DOAKES: *"Jesus fucking Christ, you're the Bay Harbor Butcher."* DEXTER: *"I really hate that name."* … *"What can I say? You were right about me."* Word-by-word captions with speaker chips, face-tracked name tags, a red BAY HARBOR BUTCHER stamp. |
| 6.50–11.06 | **Build** (*"I said I need it, this Draco undefeated… then I bleed it"*) | Doakes's gun at the lens, then a face-tracked targeting reticle locks onto Dexter. A SHIPPING YARD MASSACRE clipping, then the picture drains of colour while lock-on beeps accelerate and heartbeats play in the song's bass gap. |
| **11.06** | **Drop** (bass returns on *"Go long, these bullets"*) | Doakes's real muzzle-flash frame, then cracked glass spreading from the impact, then about 110 Voronoi shards exploding toward camera to reveal the montage. |
| 11.06–22.31 | **Montage** (one cut per beat, 74 BPM) | Night walk → split-slam → eye portal → cube rotate → impact cuts → datamosh → whip → light-leak → polaroid flick → **face-lock burst** → zoom-through with motion echo → push-up slide → finger-gun |
| 22.31 | **Stop** on *"…can't get caught up"* | Freeze and desaturate, tape-stop with reverb tail |
| 22.62–24.75 | **Outro** | DOAKES: *"I always knew there was something with you."* |
| 24.75–26.40 | **Logo** | voidfx logo revealed by a scanline sweep, glow and a sheen; no drips |

The dialogue was transcribed with a local Whisper large-v3 model. Word timings drive the captions.

## Transitions and effects

- **Gunshot shatter:** the scene's own muzzle-flash frame, then procedural crack lines (Voronoi edges plus radial fractures), then Voronoi shards. Each shard has its own velocity, spin, depth scale, gravity and edge highlight.
- **Eye portal:** YuNet face landmarks find Dexter's eye. The camera zooms into it with radial blur while the next shot opens inside the pupil, then expands out.
- **Face-lock burst:** four shots from different packs where the tracker scales and positions each face to the same screen spot and size, one per half-beat.
- **Datamosh:** the outgoing frame's pixels are dragged by the incoming shot's optical flow (DIS), then the new shot bleeds through, brightest areas first.
- **Cube rotate:** a 3D perspective cube turn with shading.
- **Split slam:** three horizontal strips slam in from alternating sides with motion blur.
- **Whip pan:** directional blur.
- **Light leak:** a warm screen-blended burn across the cut.
- **Polaroid flick:** the outgoing frame shrinks into a polaroid labelled "SUSPECT #1 — D. MORGAN" and flicks off-screen.
- **Zoom-through:** radial blur into the cut.
- **Push-up slide:** the outgoing shot is pushed up out of frame by the incoming one.
- **Small cut accents:** glitch blocks with RGB split, white impact flashes, beat-synced zoom pulses and impact shakes.
- **Motion echo trails** on the tackle shot.

## Graphics

- **Captions:** word-by-word TikTok-style captions with the current word in red and a speaker chip (DOAKES / DEXTER).
- **Name tags:** face-tracked tags (leader line plus a typed chip) for SGT. JAMES DOAKES and DEXTER MORGAN.
- **Stamp:** a worn red-ink rubber stamp reading BAY HARBOR BUTCHER.
- **Reticle:** a face-tracked targeting reticle (ACQUIRING → TARGET LOCKED) that tightens as the tension builds.
- **Lyric typography:** each lyric moment has its own animation:
  - I NEED IT: letters drop in one by one.
  - UNDEFEATED: an outline that fills left to right.
  - BLEED IT: slices snap together.
  - BULLETS: an impact punch.
  - I CAN'T SEE IT: defocus to sharp, over Dexter in a hood and sunglasses.
  - CAN'T GET CAUGHT: stacked slams with CAUGHT in red.
- **Clipping layout:** the SHIPPING YARD MASSACRE newspaper insert is shown as a framed clipping over a blurred cover of itself.
- **Watermark:** a small voidfx watermark, top-centre, at 45% opacity.

## 9:16 framing

Every shot is reframed from 16:9 using YuNet face tracking:
- **Detection:** faces are detected on the source frames, then median-filtered and smoothed.
- **Placement:** the face sits at 37% of the frame height.
- **Excluded shots:** shots whose face is wider than the 9:16 window were left out (four of the "Aesthetic" pack's extreme close-ups).
- **Check:** the automated QC pass (`work/qc3.py`) runs face detection on the finished video and flags any face cut by the frame edge or pushed off-centre.

## Sound

- **Dialogue:** cleaned (high-pass, presence lift) and levelled.
- **Cold-open bed:** a dark drone with a riser into the song.
- **Song entry:** an impact as the song enters.
- **Synthesized effects:**
  - stamp thud
  - reticle lock-on beeps that accelerate
  - heartbeats in the bass gap
  - a gunshot (crack, body, thump, room) on the drop, with a glass shatter on top
  - a whoosh or impact for every transition
  - camera shutter for the polaroid
  - thuds on BULLETS and CAUGHT
  - tape-stop on the freeze
  - logo whoosh and shimmer
- **Mix:** music ducks under the drop. Mastered to about −13 LUFS with true peak ≤ −2.5 dBTP, measured after AAC encoding.

## Files

- `out/surprise_doakes_voidfx_9x16.mp4`: upload version (H.264 High, AAC 256k, fast-start).
- `out/surprise_doakes_voidfx_9x16_master.mov`: master (H.264 CRF 11 + 24-bit PCM).
- `work/edl3.py`: every decision.
- `work/render3.py`: picture.
- `work/audio3.py`: sound.
- `work/facetrack.py`: YuNet face tracking.
- `work/qc3.py`: automated review passes.

### Re-render

```bash
python3 v3/work/render3.py prep
python3 v3/work/audio3.py
python3 v3/work/render3.py video v3/out
python3 v3/work/qc3.py v3/out/surprise_doakes_voidfx_9x16.mp4
```

## Review passes (run on the encoded upload file)

| Pass | Result |
|---|---|
| Format | 1080×1920, 60 fps CFR, 1,584 frames, 26.400 s, yuv420p, AAC 48 kHz; full decode with no errors |
| Loudness | −13.2 LUFS, true peak −2.9 dBTP |
| Face centering | all 25 shots pass: no face cut by the frame edge, no face outside the middle 64% (YuNet on every 2nd output frame) |
| Text over faces | the only flags are false detections on Doakes's hands and gun in the first shot; captions sit below every face |
| Cuts | 25 of 27 re-detected on their exact frames; the cube and datamosh cuts are hidden inside their transitions on purpose |
| Frozen / black | no frozen runs; black frames only at the logo's fade-in and fade-out |
| Audio | no clicks at any edit point; audio sample-aligned to the mix at 1, 7, 11, 20 and 23.5 s |

Fixes made between passes:
- **Ice-cream shot:** re-timed (it showed a crowd instead of Dexter).
- **Face-lock shot:** replaced (it showed the back of his head).
- **Tight "peek" close-up:** replaced, because its face was cut in 9:16.
- **Light leak:** re-routed and softened (it burned out his face).
- **"BLEED IT":** made to end exactly on the drop.
- **Newspaper insert:** changed to the framed-clipping layout.
- **Text and tags:** name tags moved above the heads, reticle labels enlarged, BULLETS resized.
- **Dialogue:** raised 2.5 dB.

## Limitations

- **I can't watch or listen.** Everything was checked frame by frame and by measurement. Watch once at normal speed with sound before posting.
- **Sources are 720p.** The "4K" and "120FPS" packs are 1280×720 at 60 fps or less, so 9:16 crops are upscaled about 2.7×.
- **Explicit lyrics and profanity.** The song lyrics are explicit and the dialogue includes profanity, as in the sources.
