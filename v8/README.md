# WISH YOU WELL — Dexter × Brent Faiyaz "Wish You Well" (voidfx v8, 9:16)

This is a 21.73 s, 1080×1920, 60 fps TikTok edit built on the v7 engine to the standard in `/CLAUDE.md`. It loops.

## Song: the section used and why

The song came as a **36 s phone screen recording** of the YouTube upload (`src/wish_you_well_screenrec.mov`). Its audio was extracted to `src/wish_you_well_rec.wav`. I mapped it with `tools/song_map.py` (138 BPM, half-beat 0.21731 s) and timed the vocal from a Demucs vocal stem with Whisper.

| Song time | What happens | Edit |
|---|---|---|
| 13.96 | quiet section: the hi-hats drop out, *"ooh, ooh, yeah"* | **start** (lead-in) |
| 19.17 | the beat comes back (+16 dB) | the first big hit (headlights) |
| 20.26–25.32 | *"Pick me up, don't know if it's what I need / But it's what I want, God, look out for me"* | lyric typography |
| 27.86 | the drums thin out | the break: the S1 pilot line *"Tonight's the night."* sits in the gap |
| 30.04 | *"Darling,"* (held) | freeze-frame composition |
| 31.34 | near-silent bar | the blood drop falls |
| **33.08** | **the drop** (+46 dB in the high band, the biggest change in the recording) | **hero transition: blood blooms in water** |
| 34.16–35.12 | *"I don't wish you well"* | one cut per syllable |
| 35.69 | the beat after "well" | dead stop, then the loop |

**Window:** half-beats 64 → 164 (13.96 → 35.69 s, 21.73 s). The recording ends at 35.94 s, so the edit is built to *arrive* at the drop rather than play out after it. The quiet lead-in and the near-silent bar make the hook feel earned.

## Concept: "Tonight's the night."

Dexter's night drive to the kill, scored like a toxic love song: the R&B hook becomes his love letter to the man on the table. The look is new: **sodium nocturne**.
- **Colour:** deep indigo shadows, lifted rather than crushed; warm sodium-vapour highlights; skin kept natural.
- **Atmosphere:** rain on the glass, passing streetlight sweeps, warm halation.
- **Type:** elegant serif italic with blood-red accents.

## Timeline

| Time | Picture | Transition in / effect (each has its own sound) |
|---|---|---|
| 0.00 | **Rear-view mirror** in a dark car: rain on the windshield, night-city bokeh, a streetlight comes up on his eyes | **push into the mirror** |
| 1.30 | South Beach at night | **streetlight sweep**: the cut hides in a passing light band (car pass-by) |
| 3.48 | Walking through the night garden. **Speed ramp**: 0.5× flow slow-mo on true-60 fps footage, then 2.4× into the beat | **windshield wiper** clears the rain off the next shot (thunk, squeak) |
| 5.22 | **Beat returns.** Under a streetlight: **PICK / ME / UP** stacked behind him (MODNet cutout, tracked to his head, off-centre framing) | **headlights** rush the lens and flare (pass-by, riser, hit) |
| 7.17 | Gloving up at night. DON'T KNOW IF IT'S / WHAT I *NEED* | **whip pan** |
| 7.82 | Behind the chain-link | **face-match** |
| 8.69 | The kill-room rapture, head back. BUT IT'S WHAT I + a huge serif ***WANT*** behind his head | **sodium light leak** |
| 10.21 | He looks up. *GOD,* / LOOK OUT FOR ME | **vertical whip**, following his gaze |
| 11.73 | Kill room, the lamp | **voidfx logo, original**, fly-through (the only logo appearance) |
| 12.60 | Plastic sheeting | **kill-room plastic wraps the lens** |
| 13.26 | Face shield over blood spatter | **impact frame** (1 frame of negative cut-out, then punch-in) |
| 13.91 | The pilot drive silhouette. ***"Tonight's the night."*** (his line, written on with a pen nib) | **rain-glass focus pull** |
| 15.65 | The orange room; **freeze** on ***"Darling,"***. The world drains to indigo while he stays lit with a warm rim light; the word is written in blood-red script | **a lamp clicks on**: a flickering pool of warm light blooms around his face (switch click, filament hum); shutter click on the freeze |
| 17.38 | **A single drop of blood falls** through the dark in slow motion, **refracting Dexter's face upside-down inside it** | heartbeat, slow fall |
| **19.12** | **The drop hits the water**: crown splash, rings, blood blooming in water that clears onto the kill-room close-up | **blood in water** (sub boom, bloop, splash) |
| 20.20–21.16 | **I / DON'T / WISH / YOU / *WELL***: one cut per syllable (knife, kill-room table, dark walk, red smirk, the stare). The line builds word by word across the cuts | **syllable slams** (a hit per word) |
| 21.30–21.73 | Pull back into the rear-view mirror, the light leaves it | **loop**: the edit reopens on the same mirror |

## Built-in review

The first review used every-cut sheets and targeted stills on rendered frames:
1. **Opening car interior:** read as confetti. The bokeh is now fewer, larger and softer, with A-pillars, and the mirror is larger.
2. **Night-garden shot:** played like daylight. Exposure brought down (ev −0.55).
3. **Rear-view-mirror push-in:** didn't finish before the next transition. Shortened.
4. **Headlights:** a white bar flare. Toned down, and the white wash cut to one frame at 60%.
5. **Light leak:** washed out the frame. Gentler.
6. **Lyric words:** ran together ("DON'TKNOWIF"). Spacing and size fixed.
7. **Hook line:** ran off the right edge. Re-laid as I DON'T WISH YOU / big serif *WELL*.
8. **Blood drop:** rendered as a long "pipe" (a shape bug). It is now a real teardrop, larger, with Dexter refracted inside it.
9. **Blood-in-water cloud:** looked like orange smoke. It is now dark, translucent ink.
10. **"Darling" shot:** too dark to read his face. Replaced with the warm orange-room shot.
11. **Daylight jungle "shh" shot:** clashed with the night look. Replaced with the red smirk.
12. **Behind-the-subject PICK ME UP:** in a close-up, his head covered every word. Moved to a streetlight shot framed off-centre, with the words stacked on the open side and tucked behind his head.
13. **Loop seam:** the bokeh and running rain jumped between the last and first frame. Their motion now wraps exactly once per loop.
14. **Audio click at the loop seam:** found and removed (a 15 ms song fade-in at the wrap).

### Checkpoint run 1: **NOT READY** (not shipped)

Automated results: 9 of 10 criteria passed.
- −13.4 LUFS / −3.2 dBTP after AAC.
- 0 clicks at cuts and at the loop seam.
- No frozen runs, and every shot centred.

The text-over-face criterion failed (22 frames), and frame review found real problems behind part of it:
- **BUT IT'S WHAT I overlapped GOD,** for a few frames. That line now exits quickly.
- **The blood-slide close-up was so tight** that *I DON'T* sat on his chin. It was swapped for the kill-room table.
- **Wiper transition:** it revealed the next shot on the wrong side of the blade. Fixed.
- **Shadow pass into "Darling":** left posterized outlines on his face. Replaced with a **lamp clicking on**.
- **"Tonight's the night.":** hard to read over the bright window. It now has a soft dark band behind it, at a larger size.
- **Remaining text flags were false detections** low in the frame (on his shirt). These were checked on frames. QC now lists such low-placed detections separately rather than counting them silently.

The edit was re-rendered and the checkpoint run again.

## Sound

- **Song:** played straight on its beat grid, with a **dead stop** on the beat after "well". The stop's reverb tail wraps into the opening under the rain.
- **Dialogue:** *"Tonight's the night."* comes from a Demucs vocal stem of the S1 pilot, levelled, with the music dipped 4 dB under it.
- **Beds:** rain and car-interior ambience in the car sections, and low room tone under everything, across the wrap.
- **Effects:** every transition has its own sound, plus the pen scratch on the write-ons, the shutter click on the freeze, the slow fall and heartbeat for the drop, and one hit per hook syllable. All of it sits under the song.

## Frame rate

The export is 60 fps for the camera moves, type and graphics. **24p source footage plays at its native cadence (frame hold), with no synthesized frames.** Optical-flow slow motion is used only on genuinely 60 fps footage: the night-garden ramp, the rapture and the face shield.

## Files

- `out/wish_you_well_dexter_voidfx_9x16.mp4`: upload version.
- `out/wish_you_well_dexter_voidfx_9x16_master.mov`: master.
- `work/edl8.py`: every decision (shots, ramps, text timings, the song window).
- `work/render8.py`: the v7 engine plus the v8 toolkit:
  - nocturne grade;
  - rain glass, streetlight sweeps;
  - car interior and mirror;
  - transitions: headlights, wiper, whips, light leak, wrap, impact, rain focus, slam;
  - blood drop and blood bloom;
  - freeze composition;
  - type: behind-subject, lyric, script, hook.
- `work/audio8.py`: sound.
- `work/qc8.py`: the review and ship checkpoint.

### Re-render

```bash
bash tools/build.sh 8 prep audio auto
bash tools/build.sh 8 video qc
```

The stems need to exist first:

```bash
python3 -m demucs -n htdemucs --two-stems=vocals -o v8/audio/sep src/wish_you_well_rec.wav
python3 -m demucs -n htdemucs --two-stems=vocals -o v8/audio/sep v8/audio/p8_open.wav
```

`p8_open.wav` is pack8 from 0 to 6 s at 44.1 kHz.
