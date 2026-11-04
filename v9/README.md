# NIGHT BLOOM — Dexter × fakemink "Night, Blooming Jasmine" (voidfx v9, 9:16)

A 21.60 s, 1080×1920, 60 fps TikTok edit built on the v8 engine to the standard in `/CLAUDE.md`. It loops in picture and sound.

**Deliverables:**
- `v9/out/night_bloom_dexter_voidfx_9x16.mp4`: H.264 CRF 17 + AAC 256k, fast-start (upload this one).
- `v9/out/night_bloom_dexter_voidfx_9x16_master.mov`: CRF 11 + 24-bit PCM master.

## Song: the section used and why

`src/night_blooming_jasmine.mp3` (fakemink, 3:54). `tools/song_map.py` mapped it at 102.8 BPM (half-beat 0.29185 s). The vocal was split out with Demucs and word-timed with Whisper. The hook was re-transcribed in short windows with the title as a prompt, then checked against the published lyric structure.

What the map showed:
- The song's single biggest moment is late in the track. A 26 s **filtered breakdown** (1:52–2:19, the beat low-passed to a murmur, no vocals) climbs into a short build. Then the track drops to **1.45 s of digital silence** (2:19.38–2:20.83). Then the full beat and the vocal slam back in (+26 dB).
- The silence is not a whole number of beats, so the second half sits on its own grid. Half-beat 482 is the drop onset, at 140.839 s.
- The title hook (*"night bloom jasmine, second name Yasmin"*) doesn't arrive until 46 s after that drop.

So the edit uses two pieces of the song, spliced on the beat grid:

| Song time | What happens | Edit time |
|---|---|---|
| 2:10.92 | Filtered breakdown (lead-in; the dialogue sits on it) | **0.00** |
| 2:17.78 | Build | 6.86 |
| **2:19.38** | **The beat cuts to dead silence** | **8.46: a shutter snaps; Arthur Mitchell, frozen: "Hello, Arthur Mitchell."** |
| **2:20.84** | **The drop** (full beat + vocal, +26 dB) | **9.92: hero transition** |
| 2:20.84–2:27.84 | Verse over the 808s | montage, cut on beats and claps |
| 2:27.84 → **3:05.20** | **Splice.** The instrumental repeats on a 4-bar cycle, and the bar at 2:27.84 matches the bar at 3:05.20 (spectral correlation 0.98). The last word before the splice ends on a breath at 2:27.42; from there to the splice is the instrumental stem, so no word is cut off. | 16.93 (masked by the M99 blink and a short low-pass dip) |
| 3:05.36 | *"I swear I'm on a mission"* | 17.09 |
| 3:07.12 | ***"Night, bloom jasmine"*** | 18.85: hero title |
| 3:08.56 | *"second name Yasmin"* | 20.29: into the drop of blood |
| 3:09.87 | Downbeat: the mix sinks under a low-pass, and its reverb tail wraps into the breakdown | **21.60 → loops** |

The splice is click-free: the sample step at the join is 0.0021 against a local median of 0.0018.

## Concept: "Some things only bloom at night."

This edit uses the new S4 packs (the Trinity season), plus one S4 POV shot from p10.

The cold open:
- A blood moon over Miami. Dexter looks up at it: *"I had to evolve. It was the only way to survive."*
- He walks through a night garden of white jasmine and stops, staring into the lens.

The silence:
- The song cuts to dead silence. A camera shutter snaps shut on Dexter's stare and opens on **Arthur Mitchell himself**, frozen in a doorway. Jasmine petals hang in the air, and the world drains to violet while he stays lit.
- Alone in the silence: *"Hello, Arthur Mitchell."*

The drop:
- On the drop, the frozen frame **bursts into jasmine petals** from its heart outward. Each petal carries a piece of the picture, tumbles toward the lens and shows its white back.
- The kill is behind them.

The hunt and the hook:
- The hunt runs on the 808s.
- Then *"I swear I'm on a mission"* and the hook title **NIGHT BLOOM / JASMINE**.

The ending:
- He holds Trinity's blood slide up to the lens. The camera pushes through the drop of blood until the frame is red.
- The edit loops: the camera pulls back out of the **blood moon**, where it started.

**Look: MOONBLOOM** (new; added to the style bank).
- **Colour:** violet-black night; moon-silver highlights with a soft white Pro-Mist bloom; jasmine-white petals; crimson kept only for blood and the hook word. Shadows are lifted, never crushed, and skin is protected from the violet push.
- **Grain:** fine.
- **Sharpening:** a gentle unsharp mask on the 720p footage only.

**Type:** this answers the v8 feedback.
- Bold, high-contrast two-line captions (Inter Display Black) with a dark keyline and soft shadow, so they read on any background. Every word eases in (fade, rise, blur to sharp) on its spoken time. Emphasis words are red.
- One hero title, designed per letter: each letter blooms open from a point (scale, twist, blur to sharp, a white flare). JASMINE lands bigger and white-hot, then floods crimson from the bottom like blood. On the exit, the letters loosen into petals and blow away.

## Timeline

| Edit | Shot (source) | Transition in (each has its own sound) |
|---|---|---|
| 0.00 | Blood moon (p9 230.0, as a still on a generated night sky with moonlit wisps) | **loop-in**: out of the red, the camera pulls back from inside the moon (sub bloop, heartbeat) |
| 0.88 | Looks up at the moon (p9 230.8). VO: I HAD TO / **EVOLVE.**, then IT WAS THE ONLY / WAY TO **SURVIVE.** | **tilt**: one eased vertical camera move from the moon down to him (low air move) |
| 4.09 | Night garden walk (p9 82.3) | **foliage**: the lens passes behind a jasmine bush, with moonlit leaves and white blossoms (leaf rustle) |
| 5.84 | Stares into the lens (p9 117.6), petals framing him in depth | **petal gust** across the lens (wind, petal flutter, chimes) |
| **8.46** | **Arthur Mitchell, frozen** (the owner's "Trinity Finds Out" clip, 103.4), on the silence: 2.5-D parallax (cutout vs. background), violet drain, moonlight rim, suspended petals. HELLO, / ARTHUR MITCHELL. | **shutter**: six gunmetal blades snap shut on the dead stop and open on him (shutter clicks, a faint high ring, nothing else) |
| **9.92** | **The drop**: the kill table, Trinity's victim under plastic (p9 103.3) | **BLOOM** (hero): the frame bursts into image-carrying jasmine petals (breath-in swell, sub boom, a burst of petal flutter) |
| 11.09 | Kill room, face shield, power tool (p9 180.2) | **strobe**: two soft strobe hits on the hi-hats (zaps, sub) |
| 12.26 | Flashlight in the dark (p9 186.6) | **whip** |
| 12.84 | By the blinds (p9 101.2) | **beam**: his torch swings into the lens and whites out, and the next shot comes up brightest-first (click, light swell, shimmer) |
| 14.01 | The latex glove goes up (p10 36.2) | **venetian blinds**: backlit slats rotate shut, then open (slat rattle) |
| 14.59 | Light-table silhouette, overhead (p9 145.8) | **voidfx logo, original**: slam in and fly through the "o" (impact, shimmer, whoosh) |
| 15.76 | Upside down on the floor (p9 126.0) | **roll**: the world spins 90° with rotational blur (Doppler sweep, floor thud) |
| 16.93 | M99 in hand (p10 66.4). I SWEAR / I'M ON A **MISSION** | **M99 blink** (v7, liked), over the splice; the music dips under the lids (heartbeats) |
| 18.68 | Gloved, hammer in hand, under the night sky (p9 222.9). **NIGHT BLOOM / JASMINE** | **impact frame** (v8, liked) |
| 20.43 | Blood slide held up to the lens (p10 164.0) | **smear**: step-printed long-exposure echoes, for a song described as "smeared, strobing" (tape-warble whoosh) |
| 21.13–21.60 | Push through the drop of blood until the frame is red | **into the blood → loops into the blood moon** (plunge, bloop, heartbeat, low-pass "night closes") |

**Count:** 16 designed transitions and no plain cuts. Graphics:
- moon and wisps;
- a jasmine-petal depth field (behind him via the MODNet matte, soft bokeh petals in front that keep off his face);
- the freeze composition;
- the bloom mosaic;
- strobe accents on every clap after the drop;
- a beat bounce on the 808s.

## Sound

- **Song:** the two segments above, spliced on the beat grid and ducked 3.5 dB under the dialogue.
- **Dialogue:** two lines, each from the Demucs vocal stem of the pack audio, levelled, with equal-power fades and a touch of room.
  - *"I had to evolve. It was the only way to survive."* (p9 131.2) over the breakdown.
  - *"Hello, Arthur Mitchell."* (p9 223.3), alone in the song's silence.
- **Beds:** a night-garden bed (two cricket voices plus air) under the cold open, crossing the wrap; a low drone everywhere.
- **Transitions:** every transition has its own layered sound (table above).
- **Hook title:** a soft bloom chime on NIGHT and BLOOM, and a deeper bloom and hit on JASMINE.
- **Ending:** the mix sinks under a low-pass as the camera enters the blood. The last downbeat's reverb tail wraps into the opening, and the breakdown pad pre-rolls across the seam.
- **Mastering:** built circularly and mastered on a wrapped copy; loudness measured after AAC encoding.

## Frame rate

The p9 pack is 24p inside a 60 fps container, and p10 is native 24p. Every shot plays at its own cadence (`interp="hold"`), so there are **no synthesised in-between frames**. The export is 60 fps so the transitions, type and graphics move smoothly over the footage.

Two shots are slowed slightly: the glove at 0.78×, held frames only, and the M99 shot at 0.90×. The moon is a still.

## Built-in review (passes before delivery)

**Pass 1** (stills and every-cut sheets; caught and fixed):
- The moon crop left a hard square edge and blotchy clouds: feathered disc, deeper blood moon, thin wisps.
- Too many rice-like petals drifted over his face: 24 larger petals, mostly behind him via the matte; the near ones keep clear of his face.
- Crimson emphasis vanished on the red sky, and ARTHUR MITCHELL. clipped the frame: a keyline and shadow on every word, a brighter red, and auto-fit to 940 px.
- The bloom's pre-roll made a **starburst flare on his mouth**. That is a "gimmick on the face" and a starburst, both on the rejected list. Rebuilt as a petal mosaic with no flare, starting at chest height.
- The ending drew a glossy red ball over his face (it read as a clown nose). Replaced with a push through the real blood on the slide into a red frame that becomes the moon.
- The S4 reflection shot loses its reflection in a 9:16 crop: replaced with the glove shot. The dim knife shot was weak in the crop: replaced with the light-table overhead.
- A NaN in the new petal sprites made black blocks: clipped.

**Pass 2** (every-cut sheets):
- The petal gust whited out the frame: fewer, smaller petals.
- The closed blinds held as flat white for 5 frames: darker slats with light between them, shorter hold.
- The light table was blown out: −0.7 EV.
- The blinds shot was underexposed: +0.3 EV.
- The hero title's exit overlapped the smear: it ends first.
- The freeze had no visible petals: framing petals hang around (never over) his face.

**Pass 3** (visual sign-off on frames pulled from the first encoded MP4):
- The automated checkpoint passed, but at full size the first frames of the bloom read as skin flaking off his chin in small ellipses (body-horror, not a flower).
- Rebuilt with half as many, larger petals that flip to their white backs almost at once and brighten as they lift, with light pouring through the gaps from the flower's heart. Re-rendered and re-checked.

**Audio:**
- The loop seam stepped (0.024 vs a local 0.001) because the breakdown started from zero. The pad now pre-rolls across the wrap: 0.0014 vs 0.0013.

## Files

- `work/edl9.py`: every decision (song grid, two-segment splice, shots, dialogue, text).
- `work/render9.py`: the engine (v4–v8) plus the v9 section at the end. It holds the moonbloom grade, moon, petals, freeze, the ten new transitions (tilt, foliage, petals, shutter, bloom, strobe, beam, blinds, roll, smear), the loop, type and finish.
- `work/audio9.py`: the soundtrack.
- `work/qc9.py`: the ship checkpoint.
- `work/tracks9.json`: face tracks.
- `work/shots_p9.json`, `shots_p10.json`: shot lists.
- `work/tr_song.json`: lyric word times.
- Media (`src/`, `audio/`, `frames/`, `out/`, `seg9.npz`) stays out of git.

Re-render: `bash tools/build.sh 9 prep audio video qc`

## Checkpoint (encoded MP4)

Run on the encoded upload file (`bash tools/build.sh 9 qc`), after the pass-3 re-render. **VERDICT: SHIP.**

**Automated checks:**
- **Format:** 1080×1920, 60 fps, 1296 frames, H.264 + AAC, clean decode.
- **Loudness:** −13.0 LUFS, true peak −3.4 dBTP, measured after AAC.
- **Face centring:** every face-tracked shot had 0 flagged frames. The moon, the light table and the upside-down floor shot are subject-less by design.
- **Text vs. faces:** one flag, at frame 1222. It's the smear ghost during the title's exit, and no face is under the text.
  - 43 low-placed detections (the apron, gloved hands, his bowed head in the blinds shot) were checked on frames and are false positives.
- **Cuts and picture:** no frozen runs, no black frames, and no clicks at any of the 13 cuts.
- **Song splice:** sample step 0.0021 against a local median of 0.0018.
- **Loop seam:** matched in picture (luma 48.3 → 48.7) and in sound (−31.7 / −31.8 dBFS over 20 ms).
- **A/V length:** 21.600 s vs 21.611 s (under one frame).

**Visual sign-off:** frames pulled from the encoded MP4 around every transition, every caption, the freeze, the drop, the hook title and the loop.

**Not verifiable here:** I can't watch or listen. The structure, timing and loudness are measured, and every moment was checked on stills, but the edit has not been seen in motion or heard. Please watch it once with sound.


## Revision 2 (owner feedback)

> "I like the edit but can you make the clip where he says hello arthur mitchell actually arthur mitchell?"

Before, the caption HELLO, / ARTHUR MITCHELL. sat under Dexter's own frozen face, which read as if Dexter were Arthur Mitchell.

**What changed:**
- **Footage:** Dexter's stare now plays up to the silence. On the song's dead stop, a new **shutter** transition closes over him and opens on **Arthur Mitchell (Trinity)**, frozen. The source is the owner's clip `src/trinity_goodbye.mp4` at 103.4 s: the doorway stare, chin up, the one Trinity close-up that fits 9:16 cleanly.
- **Freeze:** the freeze composition (parallax, violet drain, moonlight rim, petals framing him) and the caption now sit on him.
- **Drop:** the drop's petal bloom bursts his frozen frame open into the kill table.
- **Sound:** the shutter has its own blade clicks. The dialogue, song and every other shot are unchanged.

### Revision 2 checkpoint: **SHIP**

Run on the encoded MP4.

**Automated checks:**
- **Format:** 1080×1920, 60 fps, 1296 frames, clean decode.
- **Loudness:** −13.0 LUFS, true peak −3.3 dBTP after AAC.
- **Face centring:** 0 flagged frames, including the new Arthur shot (43 face frames).
- **Text vs. faces:** the only flag is the same smear-ghost frame (1222) as before.
- **Cuts and picture:** no clicks at any of the 14 cuts, no frozen runs, no black frames.
- **Loop seam:** matched in picture and sound.
- **A/V length:** within one frame.

**Visual sign-off:** frames pulled from the encoded file through the stare, the shutter, the Arthur freeze with its caption, and the bloom into the kill table.


## Owner feedback on revision 2

> "I like this edit and I honestly think it's good. It's complete. However, I want you to note that in comparison to your other builds and dexter edits in general this one was lack luster, I want you to go above and beyond with these edits."

**My assessment of why it fell short:**
- **Concept:** the jasmine-petal and moon idea came from the song title, not from Dexter's world. It looks soft where a Dexter edit should hit dark and hard.
- **Set pieces:** only one real one (the bloom). The montage relied on quick, generic moves (strobe, beam, blinds, roll, smear, whip).
- **Text and graphics:** thinner than in v6/v7.
- **Shots:** three planned shots were lost to the 9:16 crop and replaced with weaker ones.

**What I've recorded:**
- the binding note in `/CLAUDE.md` ("v9 feedback");
- a row in the handbook's rejected table;
- a new **pre-build gate** (`studio/VOIDFX_STUDIO.md` §5a): a concept from Dexter's world, three or more signature set pieces, graphics density, a written comparison with v6/v7/v8 before the first render, and ambition in the review passes;
- the gate in `studio/START_PROMPT.md`.

**Later note from the owner:** *"Another thing I was really fond of from this edit was the text, it was perfect."*

The v9 caption and hero-title system is now the standard text style:
- `CLAUDE.md`;
- `studio/VOIDFX_STUDIO.md` §3, with the full spec;
- the toolkit catalog.

It ships with the engine that new edits copy.
