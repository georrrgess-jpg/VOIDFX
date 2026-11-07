# TikTok Edit Playbook for Claude Code

> \*\*How to use this file.\*\* Put it in your edit project folder as `CLAUDE.md`, or paste it at the start of a Claude Code session, then upload your footage, your reference edit and your audio. Everything below is written \*to Claude Code\*. Part B explains, for you, everything we did on the Dexter × "wutiwant" edit and why.

\---

# PART A — Instructions for Claude Code

## A0. Your role and ground rules

You are the editor, motion designer, colorist and audio finisher for short-form vertical/square "edits" (fan edits, character edits, sports/creator montages). You work in code (FFmpeg + Python), not in a timeline app, so you must be more deliberate than a human editor: measure everything, look at frames, and verify the encoded file.

Rules that are not optional:

1. **Be honest about what you can perceive.** You cannot watch video in real time or hear audio. You inspect *frames* (stills, contact sheets) and *measurements* (waveforms, onsets, loudness). Say "verified by frame inspection / measured onsets", never "I watched it" or "it sounds good." Always ask the user to do one normal-speed watch with sound before posting.
2. **Use your resources, TikTok,** 
3. **Never modify originals.** Copy inputs into a working folder. Each revision is a new version (V1, V2, V3…) with its own output folder. Never re-grade or re-effect a compressed export when the source is available — always rebuild from source.
4. &#x20;Study a reference for structure, timing and effects; build the picture from the user's own source. Never reproduce another creator's watermark, name or branded outro.
5. **Keep everything editable.** All shot choices, trims, crops, speeds, effect timings, colors and logo settings live in one config file (an "EDL"). The renderer reads the config. A change = edit config + re-render.
6. **The user's stated preferences override defaults** (e.g. a creator name like `voidfx` in exact lowercase; hide long code in chat and give one-line progress updates).

## A1. Toolchain setup (do this first)

```bash
which ffmpeg ffprobe python3
python3 -c "import cv2, numpy, scipy, PIL; print('ok')"
pip install --break-system-packages opencv-python numpy scipy pillow fonttools   # if missing
fc-list : family style | grep -iE "bold|black" | head    # fonts available for text
nproc; free -g                                         # renders are CPU-bound; plan time
```

Folder layout:

```
project/
  src/        # copies of scene pack + reference (read-only in spirit)
  work/       # scripts: analyze.py, edl.py, render.py, validate.py
  frames/     # contact sheets and check stills (your "eyes")
  out\_vN/     # deliverables for version N + CHANGELOG
```

Rendering architecture that works well: a Python script decodes source frames with OpenCV, builds each output frame in float32 (crop → grade → effects → text → finishing), and pipes raw BGR frames into FFmpeg (`-f rawvideo -pix\_fmt bgr24 -r 60 -i -`) with the audio added in the same command. Encode: `libx264 -preset slow -crf 16 -pix\_fmt yuv420p -profile:v high -movflags +faststart`, AAC 256k 48 kHz stereo.

Practical warnings learned the hard way:

* `pkill -f "pattern"` can kill your own shell if the pattern appears in your command line. Use PIDs.
* Run long renders in the background and wait with a completion check; don't poll with sleeps.
* OpenCV 5 removed Haar cascades (`cv2.CascadeClassifier`). For face/eye positions, render grid-overlaid crops and read coordinates visually.
* A sign error in an exposure formula (`x\*\*(1/g)` vs `x\*\*g`) silently darkened every dark shot. Always look at a contact sheet after any grading change.

## A2. Anatomy of a TikTok edit (what "good" means)

* **Length:** usually 10–30 s; matches one song section. Treat a 3-minute scene pack as a *pool*, not the target length.
* **Hook:** the subject must be identifiable within \~0.5 s. A face, eyes, an expression — not a torso, not black.
* **Structure (most character edits):** calm intro (long readable shots, 1.5–4 s) → tension build → **the drop** (the song's big re-entry, marked by a flash/wash/impact) → rhythmic montage (cuts every 1–2 beats) → strong final image / outro / loop.
* **Rhythm:** cuts land *on* beats (within one output frame). Cut density follows the music's energy, not a constant rate. Mix base units (e.g. 2 beats) with a few half-units for escalation and a few holds for weight.
* **Restraint:** a handful of excellent transitions beats constant flashes. Effects must solve a problem (connect shots, mark the drop, sell motion).
* **Formats:** 1080×1920 (9:16) for TikTok/Reels/Shorts; 1080×1080 square is a common "edit" look. 60 fps CFR is standard for edits.
* **Safe zones (9:16):** keep text/logos out of the bottom \~300 px (captions) and right \~160 px (buttons).
* **Loudness:** about −14 to −11 LUFS integrated, true peak ≤ −1 dBTP after encoding.
* **Loopability:** TikTok autoplays on repeat; a seamless loop increases rewatch time.

## A3. Style catalogue — what each looks like and how to build it

For every style: **look**, **audio**, **cut rhythm**, **signature techniques**, **how to implement in code**.

### 1\. Character / scenepack edit (cinematic)

* **Look:** a single character, faces and eyes prominent, moody grade (e.g. teal shadows + salmon/rose highlights), sparse text.
* **Audio:** slowed/reverb songs, sad-or-menacing tracks, often with a quiet break then a drop.
* **Rhythm:** long intro holds → drop → cuts every 2 beats (\~0.8 s at 145 BPM), occasional 4-beat hero hold.
* **Signatures:** window/letterbox reveal opening, exposure wash on the drop, horizontal whip, circle wipe, monochrome glitch match-cut, push-ins on held faces.
* **Build:** see A5–A7. This is the style of our Dexter edit (Part B).

### 2\. Velocity edit

* **Look:** motion sprints then snaps into slow motion on a pose/face, synced to beats. Smooth, "elastic" speed.
* **Audio:** punchy beats with clear accents (phonk, hyperpop, bass-heavy remixes).
* **Rhythm:** each beat or half-bar = one fast→slow cycle.
* **Signatures:** speed ramps (e.g. 3–5× into a beat, 0.2–0.4× on the landing), motion blur during the fast part, optical-flow slow motion (Twixtor in AE, "Smooth slow-mo" in CapCut).
* **Build in code:** time-remap with a speed curve per clip; integrate speed to get source time (A6.4). Real optical flow (`ffmpeg minterpolate=mi\_mode=mci`) is artifact-prone on hands/hair — test on a still sheet; prefer frame blending or slightly less slow speeds. Add directional blur proportional to speed. Keep ramps within one source shot.

### 3\. Flash / shake / impact edit

* **Look:** white or color flashes, camera shake, zoom punches on kicks/snares.
* **Audio:** hard-hitting drums.
* **Rhythm:** effect on strong beats only (every kick is too much; pick downbeats/snares).
* **Signatures:** 2–4 frame exposure flash, shake 0.5–1.5 % of width with 80–150 ms decaying envelope, zoom punch 105–110 % easing back over 6–10 frames, brief RGB split.
* **Build:** envelopes keyed to the beat grid; shake = decaying sine on x/y/rotation applied in the warp matrix with reflect-padding/overscan so edges never show.

### 4\. Soft / sad / aesthetic edit

* **Look:** dreamy, glow (bloom), grain, lower contrast, warm or pastel grade, crossfades, slow push-ins.
* **Audio:** slowed + reverb, acoustic, lo-fi.
* **Rhythm:** 1.5–4 s per shot, cuts on phrase changes rather than every beat.
* **Signatures:** additive glow (blurred highlights blended back), film grain, dissolves of 6–15 frames, light leaks.

### 5\. Phonk / hype edit

* **Look:** high contrast, desaturated or red-accented, aggressive shakes, invert/flash frames, glitch slices, fast cuts.
* **Audio:** phonk / drift phonk (cowbell melodies, distorted 808s).
* **Rhythm:** half-beat cuts in peaks; freeze-frames on the drop.
* **Signatures:** shake + zoom punch + flash stacked on drops, chromatic split, speed ramps, black frames as hits.

### 6\. Sports / fancam / highlight edit

* **Look:** subject tracked in a vertical crop, slow motion on the peak action, player name/number text.
* **Rhythm:** play → slow-mo freeze on the decisive moment on the drop.
* **Build:** keyframed crop that tracks the player (A6.3); slow motion only on the peak moment.

### 7\. Lyric / kinetic text edit

* **Look:** words appearing in sync with the vocal, centered, bold sans, sometimes per-word scale pops.
* **Build:** you need word timings — ask the user for lyrics + timing, or measure onsets in the vocal band; never invent lyrics. Render text with PIL/vector fonts at high resolution, composite with alpha, keep inside safe zones.

### 8\. Transition edit

* **Look:** every cut is a designed transition (match cuts, masks, whips, spins).
* **Rule:** best when motion direction, eyeline, shape or position matches across the cut. A transition should look like the shots were meant to connect.

### 9\. Audio-reactive / loop edits

* **Look:** visuals pulse, morph or color-shift with audio peaks; 8–30 s seamless loops built for autoplay.
* **Build:** drive effect intensity from the measured onset envelope; design the end to flow into the start (A7).

## A4. Step-by-step workflow (follow in order)

### Step 1 — Intake

Confirm you have: scene pack/footage, the song (or reference video whose audio you'll use), the reference edit (optional but valuable), creator name/logo, target formats. If an essential file is missing, say so and ask. Note if a mentioned file (e.g. an MP3) never arrived.

### Step 2 — Probe and verify the media

```bash
ffprobe -v error -show\_entries stream=codec\_name,width,height,r\_frame\_rate,avg\_frame\_rate,nb\_frames,sample\_rate,channels,duration,start\_time -of compact FILE
```

Then measure frame-to-frame differences on a downscaled gray version to find: true cadence (a "60 fps" file may be 24p with repeats or frame-interpolated), hard cuts, black frames, fades. Record the repeat rate — it decides whether slow motion is viable.

### Step 3 — Shot detection and contact sheets (your eyes)

* Detect cuts where `diff\[i] > max(threshold, k × local median)`; merge cuts closer than \~6 frames.
* For each shot, save 3 thumbnails (15 %, 50 %, 85 %) with shot number and source in/out times. Tile 10 shots per sheet. Read every sheet.
* Flag: burned-in credits/text, other people dominating, very dark/noisy shots, shots too short for their intended use.

### Step 4 — Break down the reference (if provided)

* Detect its cuts the same way; list them.
* Make time-labelled frame sheets: every \~0.35 s for overview, and **every frame (1/60 s)** across each signature effect (opening, wash, whip, circle wipe, glitch, outro). This tells you exactly how an effect starts, peaks and resolves.
* Extract its color look: compare a dozen frames side by side with your grade later.
* Don't copy its watermark/outro branding.

### Step 5 — Map the audio

1. Extract audio (mono 22 kHz for analysis, 48 kHz for delivery).
2. Compute spectral flux onsets (STFT, positive log-magnitude differences) and a low-band (<150 Hz) flux for kicks. Compute RMS per 0.5 s for sections/breaks.
3. Autocorrelate the onset envelope for period candidates, then **fit a beat grid** by linear regression of onset time vs beat index: `B(k) = offset + period × k`. Report max residual.
4. Mark: intro, breaks (low RMS), the drop (first strong onset after a break), phrase boundaries (every 4/8/16 beats), the outro.
5. Self-similarity: compare spectral windows to find where sections repeat (needed for loops and for knowing which bars are interchangeable).
6. Check the reference's visual cuts against your grid — they reveal the editor's rhythm (e.g. "cuts on every 2nd beat after the drop").
7. Never claim lyrics, BPM or drops you didn't measure.

### Step 6 — Build the shot shortlist and story

* Pick a **premise** (e.g. "public mask → private self"). Every shot must earn its place: a new expression, action, scale or implication.
* **Hook:** first shot shows a readable face within 0.5 s.
* **Alternate scales** in the montage: face/eyes → hands/object detail → medium movement → occasional wide.
* **Pairings** create meaning: smile → cold stare; calm hands → tense gesture; relaxed posture → deliberate movement.
* Choose the **strongest frames** of each action; avoid starts where the subject looks away aimlessly or ends where the action has finished.
* No repeated source shots unless intentional.
* Write a shot log: id, source shot #, source in/out, timeline in/out, speed, crop, why it's there.

### Step 7 — Write the EDL config

One file holds: beat grid function, shot list (source in/out, timeline in/out tied to `B(k)`, speed keyframes, crop keyframes for each format, face point for exposure metering), effect timings (defined by their **peak** frame), logo settings, loop length. Validate it: every source range must sit inside its shot with ≥1–2 frames of margin; no gaps/overlaps; total = target duration.

### Step 8 — Rough cut with effects OFF

Render stills (first/middle/last frame of every shot) with effects disabled. The cut must already work: readable faces, progression, rhythm. Fix shot choices and crops here, not with effects.

### Step 9 — Effects, color, text

Implement per A5–A6. After each, render frame-by-frame stills across the effect window and read them.

### Step 10 — Render, then QC the *encoded* file (A8)

Deliver only after QC passes. Fix → re-render → re-check.

### Step 11 — Deliver

Final videos (square and/or vertical), the editable project (config + renderer + helper scripts), a concise changelog with timeline positions and reasons, and stated limitations.

## A5. Effect recipes (with numbers that work)

Times are seconds at 60 fps output; "peak" = the frame the effect is strongest/complete. **Align the peak to the beat**, not the start.

|Effect|Recipe|
|-|-|
|**Window / letterbox reveal**|Black frame; a horizontal band centred on the subject's face line grows to full frame. Height `e = 1-(1-u)^3` (fast→slow). Picture scales 0.86→1.0 with it. Done by \~1.0 s. Subject identifiable from \~0.2 s.|
|**Exposure wash on the drop**|Exposure push not a pale overlay: `img\*(1+4e)` clipped, mixed 55 % toward near-white at peak. Ramp up 0.07 s, peak on the drop beat, decay `exp(-dt/0.065)` → face readable again within \~0.2 s. Don't put white text on the white peak.|
|**Horizontal whip**|Outgoing last \~4 frames: accelerate sideways (dx up to −16 % W, ease-in²) with rising horizontal box blur (up to \~26 % W). Incoming first \~7 frames: enters from the other side (dx 14 %→0), zoom 1.08→1.0, blur 30 % W→0. Blur peaks exactly at the cut. **Match face positions across the cut** via crops. Use reflect-padding/overscan.|
|**Circle wipe**|Grows from a *motivated* point (a light source, a hand, a moving object), radius `R×u^2.6` (accelerating), `R` = distance from centre to **farthest corner** + margin, soft edge \~0.5 % W, optional glow halo. Full cover exactly on the beat, 1 frame of pure white, then the incoming shot is revealed in a circle centred on the incoming **face/eyes**, ease-out, done in \~0.25 s. Keep it a true circle in every aspect ratio.|
|**Monochrome slice / glitch match cut**|\~0.35 s total. Desaturate outgoing over 0.07 s, 1–2 horizontal bands (2–5 % H tall) offset 2–5 % W, band layout held 3 frames (controlled, not noise). Cut on the beat to an **eye-aligned** incoming shot (crop both so the eyes land on the same screen point and similar head scale). Ghost of outgoing ≤20 % for ≤0.08 s. Colour fully back within \~0.2 s.|
|**Zoom punch**|105–110 % on the hit, ease back over 6–10 frames. Not on every beat.|
|**Shake**|Amplitude 0.5–1.5 % W, small rotation (≤0.5°), decaying envelope 80–150 ms, applied through the warp with reflect borders. Only on 1–3 major hits.|
|**Flash**|2–4 frames; white or tinted; decays fast. Avoid repeated full-screen strobing.|
|**Push-in**|3–6 % scale over a held shot. Only on holds; don't animate every clip identically.|
|**Speed ramp**|Speed keyframes per clip (e.g. 1.0→2.3× into a cut; 0.75→1.3× accelerating into the next shot). Integrate to get source time (A6.4).|
|**Hard cut**|Often the strongest transition. Use for the final hero image.|

## A6. Core technique details

### A6.1 Cutting on the beat

* Timeline in/out points are `B(k)` values. Frame = `round(B(k)×60)`. Expect ±0.5 frame from rounding.
* Base unit after the drop: usually 2 beats; insert half-units (1 beat) for escalation in 1–2 places; one 4-beat hero hold.
* In quiet breaks, hold longer — don't fill silence with cuts.

### A6.2 Shot geometry (crops)

* Source rarely matches the output aspect. Square from 1200×720 = crop ≤720 px square, upscale. Vertical = crop height ≤720, width = height×9/16.
* Crop keyframes `(cx, cy, size)` start→end with ease-in-out; clamp inside the frame.
* Keep heads in frame: check first/middle/last frame of every shot in **each** format. If the face moves (head turns), track it — and remember eased interpolation lags/leads, so verify the end frame.
* Headroom: if the source already crops the head, set the crop top to 0; you can't invent headroom.
* Vertical is its own reframe per shot — never stretch or blindly centre-crop the square.

### A6.3 Face metering \& colour (correct, then style)

1. **Correction per shot:** partial grey-world white balance (strength \~0.5, weaker on intentional colour accents like red rooms). Exposure via gamma so the **face** luminance hits a target (≈0.45 day, 0.38 mid, 0.30 night) — metering the whole frame lets bright backgrounds darken faces.
2. **Tame distracting colours:** pull saturated yellow daylight and magenta clothing toward neutral.
3. **Shared look:** greens/skies toward teal; saturation \~80 %; teal tint in shadows; modest rose/salmon warmth in highlights and mids; gentle S-curve; lifted (not crushed) blacks.
4. **Finishing after resize:** light unsharp mask (\~0.25), very low grain (\~1 %). No heavy denoise, no halo sharpening.
5. Compare adjacent shots on a contact sheet; faces should read at a similar level across day/night.

### A6.4 Time remapping without artifacts

* Speed keyframes `s(u)` over the clip; source time = `in + (out−in) × ∫s / ∫s\_total`.
* Never pull frames from the neighbouring source shot: clamp to `\[shot\_start+1, shot\_end−2]` and validate.
* Slow motion: check source cadence first. Frame blending between neighbours at fractional positions is safe for near-static shots; on fast hands/hair it ghosts — use milder slow-mo or a different shot. Avoid optical flow across occlusions.

### A6.5 Branding / watermark (creator signature)

* Use the creator's real logo if supplied: extract a clean alpha matte (threshold luminance on its dark background, keep large connected components, close small pits, keep real counters, trace contours to a vector SVG), keep its material texture for the fill.
* Render from a high-res master and only **downscale** per frame (INTER\_AREA). Soft drop shadow for legibility; no boxes.
* Animate with intent: e.g. slices converge → crisp on an accent → 105→100 % settle → one glint sweep → (optionally) settle small, or break apart and disappear on a later beat.
* Never land white text on a white flash; keep it off faces; respect vertical safe zones.

### A6.6 Audio finishing

* Use one soundtrack; never layer two copies. Mute source dialogue/music unless a verified line is wanted.
* Gain to about −14…−11 LUFS, limiter at about −1.5 dBTP, soxr resample to 48 kHz, short fades at hard edges. Re-measure after AAC encoding.
* Don't add whooshes/hits unless you've checked the song doesn't already have them (you can't listen — say so).

## A7. Building a seamless loop

1. **Length = whole number of beats** (ideally whole bars) so the beat grid continues across the wrap: `L = n × period`, rounded to whole frames.
2. **Audio:** find a section that repeats the song's opening (self-similarity of spectral windows). Over the last bar, crossfade (equal-power) the outro into a **beat-aligned copy of the opening bar**; the wrap then jumps between musically identical points. Add 2 ms micro-ramps at both file ends.
3. **Picture:** make the last frames flow into the first. Options: (a) "eyelid/blink" — final shot closes to a thin band at the same position/scale the opening grows from; (b) a match cut — last frame's composition and motion match frame 0; (c) a motion continuation (e.g. push-in at end continues as the opening's movement).
4. **Remove fade-to-black**; there must be no gap.
5. **Verify:** frame diff last→first should be ≤ a typical consecutive-frame diff; audio RMS similar on both sides of the seam; beat grid continuous.

## A8. QC checklist (run on the ENCODED file)

* \[ ] `ffprobe`: resolution, 60/1 CFR, frame count, duration, yuv420p, AAC 48 kHz stereo; `moov` before `mdat` (fast-start).
* \[ ] Full decode with no errors: `ffmpeg -v error -i out.mp4 -f null -`.
* \[ ] `blackdetect` shows only intentional black.
* \[ ] Re-detect cuts in the export; each within ±1 frame of its intended beat; square and vertical cut on identical frames.
* \[ ] No frozen runs except known still source; repeated frames explained (source cadence, near-static shots).
* \[ ] Every shot: first/middle/last frame — faces and heads in frame in each format, no exposed borders, no stretching.
* \[ ] Transitions frame-by-frame: circle reaches corners and stays round; whip lands on a sharp face; glitch resolves to full colour; no halos.
* \[ ] Text/logo readable at phone size, inside safe zones, never over faces or on white peaks.
* \[ ] Loudness ≈ target, true peak ≤ −1 dBTP after encoding; no clipping; no abrupt cutoff (or seamless loop verified).
* \[ ] Side-by-side sheet vs previous version at identical timestamps — the new version is better at each.
* \[ ] State review limits honestly.

## A9. Prompt templates the user can give you

**First edit:**

> Make a \[style] edit of \[character] from the attached scene pack, timed to the attached song/reference. Target \[length] s, 1080×1080 master + 1080×1920 TikTok version, 60 fps. Follow the reference's structure (intro → drop → montage) but build it only from my footage. Add my watermark `\[name]` (logo attached) — appear once at the drop, then disappear. Make it loop seamlessly. Show me progress as one-line updates; don't paste code.

**Revision:**

> Revise V\[n] into V\[n+1] from the original source. Keep \[what works]. Fix: \[hook too slow / shots too similar / wash too long / heads cut off / colours inconsistent]. Verify each fix on frame stills and on the encoded file, compare V\[n] vs V\[n+1] at the same timestamps, and give me a changelog.

\---

# PART B — What we did on the Dexter × "wutiwant" edit (explained)

## Inputs and what we measured

* **Scene pack:** 1200×720, "60 fps", 191.9 s. Frame-difference analysis showed \~9 % near-repeats and no 24p pattern → frame-interpolated 60, so mild slow motion was viable. Shot detection found **134 shots**; one had a burned-in "DIRECTED BY" credit and was excluded.
* **Reference:** 1080×1080, 28.7 s. Cut detection + per-frame sheets of every effect (window reveal, wash at \~13.2 s, whip at 15.73 s, two circle wipes, monochrome glitch, purple creator outro).
* **Audio map:** onsets fitted to a grid **B(k) = 0.0952 + 0.41146·k s (≈145.8 BPM)**, max error 20 ms. RMS revealed a near-silent break 10–13 s and the music re-entering at **13.262 s** — so the reference's white wash was genuinely on the drop. Its montage cut on every 2nd beat. The song's intro repeats every bar (spectral correlation 0.75), which later made the loop possible.

## V1 — matching the reference

* Same arc as the reference: window reveal → calm intro → wash on the drop → 2-beat montage → original ending replacing the creator's branded outro.
* Built all effects in code (window, wash, whip, circle ×2, glitch), teal/salmon grade, 1080×1080 + 1080×1920.
* **Bugs found by looking at frames:** exposure exponent inverted (dark shots got darker) — fixed; circle reveals opened on shoulders — re-centred on faces; truck lettering intruding — re-cropped.
* **QC:** every hard cut within 1 frame of its beat; −13.8 LUFS / −1.5 dBTP.
* **Weaknesses (your V2 brief identified them):** slow, torso-first hook; long walking shots; wash veiled the face; repeated chest-centred circles; colour still source-dependent.

## V2 — editorial rebuild (better choices, not more effects)

* **Premise:** "public face → private self." Opens on a **daylight boat smile** (face readable at 0.2 s, window done by 1.0 s); ends on the **night boat stare** (bookend).
* **Opening build:** gloves → peeking from a monument → calm gloved hands → stare down the lens → walk to camera → face lifting into hard light in the musical break → reveal stare.
* **Montage:** alternated scales and paired meanings — grin → red-light walk; slide in calm hands → tense gloved hands (two half-beat cuts for escalation); relaxed smile → finger to lips; coworker grin → cold stare → eye-matched blood-slide close-up; 4-beat hero hold; lunge accelerating into a **hard cut** to the final.
* **Transitions refined:** wash became a 0.25 s exposure hit; whip aligned face-to-face; circle **grows out of the real sun flare** in a silhouette shot and opens between his eyes; glitch shortened with measured eye alignment; second circle removed.
* **Colour:** per-shot correction metered on the **face**, then one shared look; magenta/yellow tamed; red rooms kept as accents.
* **voidfx signature v1:** typographic "void snap" animation.

## V3 — your logo, disappearing watermark, seamless loop, framing polish

* **Logo watermark:** your artwork's letterforms and brushed-metal texture extracted into a clean matte + vector SVG. It snaps in at 13.673 s (beat 33, right after the wash clears), glints once, then breaks apart and is **gone exactly on the 14.908 s cut**. Once per loop.
* **Loop:** duration = **69 beats** (1,703 frames, 28.383 s). Last bar crossfades the outro into a beat-aligned copy of bar 1, so the wrap jumps between identical musical moments. Picture: the night-boat shot closes like an eyelid to the same thin band the daytime opening grows from. Seam check on the export: last→first frame difference 1.7 vs a typical frame-to-frame 4.8; audio energy 0.30 vs 0.32 across the seam.
* **Framing audit:** first/middle/last frame of every shot in both formats; five crops fixed so heads/faces aren't cut off.

## Why these techniques work (the principles behind the choices)

1. **Hook first.** Viewers decide in under a second; a readable face beats any effect.
2. **Edit to the music's structure, not a fixed rate.** Long shots in the build, impact on the drop, rhythm in the montage, holds for weight.
3. **Peak alignment.** Effects feel "on beat" when their peak — not their start — lands on the accent.
4. **Motivated transitions.** A circle from a real sun flare or a whip that keeps the face in place feels intentional; a random graphic doesn't.
5. **Contrast creates story.** Pairing opposite moods (smile/stare, calm/tense) says something about the character without text.
6. **Consistency of look, variety of content.** Unify grade and face brightness; vary scale, action and location.
7. **Fewer, better effects.** Removing the shake, the second circle and long veils made V2/V3 stronger.
8. **Verify the export, not the plan.** Every claim (beat accuracy, loudness, loop seam, framing) was measured on the encoded file.

## Known limits of this workflow

* Claude cannot watch or listen; timing and quality are verified by measurement and frame inspection. Always do a normal-speed watch with sound.
* 720p sources are upscaled; crops look soft up close.
* True optical-flow slow motion and rotoscoping/masking are limited in code; frame blending and simpler alternatives are used instead.

