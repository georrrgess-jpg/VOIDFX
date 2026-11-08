# LET GO — The Flash × Ark Patrol "Let Go" (ft. Veronika Redd) (voidfx v102, 9:16)

> **Owner review: liked and complete, but lacklustre compared with the other builds and the Dexter edits.** The owner wants every edit to go above and beyond. That bar is now `studio/VOIDFX_STUDIO.md` §5a.

A 23.42 s, 1080×1920, 60 fps TikTok edit that loops. It is built on the v7 engine plus the v5 Flash toolkit, with a new look, new transitions and new graphics.

- Upload file: `v102/out/let_go_flash_voidfx_9x16.mp4` (H.264 + AAC, fast-start)
- Master: `v102/out/let_go_flash_voidfx_9x16_master.mov` (CRF 11 + 24-bit PCM)
- Every decision is in `v102/work/edl102.py`. The look, effects, transitions, text and frame function are in `v102/work/fx102.py` (spliced into `render102.py` by `python3 v102/work/splice.py`). The sound design is in `v102/work/audio102.py`.

## Sources

- **Footage:** `src/flash_b.mp4` (fb) only, the red-suit Barry Allen (Grant Gustin) footage. No new Flash packs came with the brief.
  - `src/flash_a.mp4` was reviewed, but its strong shots duplicate fb's at a lower frame rate (25.4 fps), so it isn't used.
  - Other speedsters and suits in the packs were left out on purpose so the character stays consistent: the yellow suit, purple and green lightning, and the black suit with the blue chest.
- **Song:** `src/let_go.mp3` (the uploaded Ark Patrol track).
- **Not reviewed:** v5 FASTEST's rendered video. It isn't in the repo, so the comparison is against its write-up and code.

## Concept: he's been holding it back, then he lets go

1. **Cold open, the song's second breakdown** (bass and chopped vocals, no drums).
   - Time is frozen around an unmasked Barry, with gold sparks hanging in the air; tiny arcs flicker off his eyes on the vocal chops.
   - A bolt jumps out of his eye and splits the frame, and the lightning starts crawling over him. His own lightning overloads the frame and the suit burns in.
2. **The riser.** Over the riser he says, on camera, **"How's this for power?"** (lip-synced, checked with `tools/lipcheck.py` → `v102/frames/lip_power.jpg`).
3. **The drop.** On "power?" time stops: the colour drains, the music drops out, and lightning crawls over his silhouette. A bolt then strikes down through him, two impact frames hit, and **the drop** explodes as he throws lightning. **LET GO** slams in on two beats.
4. **The speed montage on the drop.** The emblem draws itself in lightning and the camera flies through the bolt. Then:
   - lightning climbing his body;
   - a speed-ramped run straight into the lens;
   - the wall run turned vertical;
   - lightning crawling on his face;
   - the grin, then the glowing eyes;
   - the final sprint with afterimages.
5. **Ending: he runs so fast he goes back in time.** The whole edit rewinds in 1.1 s, picture and sound together (35× at its peak), and lands exactly on the first frame. That is the loop.

**Look, "storm":** crimson suit, gold lightning with white-hot cores, steel-blue shadows, natural skin, gold halation, anamorphic flares on the lightning, edge chromatic aberration on the fast shots, fine grain.

## Song section

The song runs at 163.96 BPM; one half-beat is 0.18297 s and one bar is 1.464 s. It was mapped with `tools/song_map.py`, Demucs stems (drums, bass, other, vocals) and per-half-beat stem energy.

| Song time | Half-beat | What happens |
|---|---|---|
| 2:11.78 | h720 | The second half of breakdown 2 (bass and vocal chops, no kick): the edit starts |
| 2:17.63 | h752 | Riser: the hats build, the bass falls away, the chops speed up |
| **2:20.56** | **h768** | **Drop 2: kick and bass slam back. This is the biggest change in the song (+31 dB), larger than drop 1** |
| 2:20.6–2:34.1 | h768–h842 | 10 bars of the drop |
| 2:34.1–2:35.2 | h842–h848 | The rewind runs back to 2:11.78, so the loop wraps onto the first sample |

**Lyrics:**
- The verse hook "but now you won't let go" was verified at 0:32.4–0:33.5. The title word LET GO comes from the song's own hook.
- The riser's chopped vocal could not be verified. Whisper hears "back, back…" with varying endings ("in time" / "in town" / "down"), so no lyric is shown on screen.

## Timeline (edit seconds; each transition goes through something and has its own sound)

| Time | Shot (fb source s) | Transition in | Sound |
|---|---|---|---|
| 0.00 | Unmasked Barry, frozen-time sparks, eye arcs (37.15–38.52, 0.62×) | **Rewind lands**: speed smear and flash settle (the loop entry) | Zap |
| 2.20 | Lightning crawling over him (83.83–85.06) | **Bolt from his eye** splits the frame open | Zap, crack, whoosh |
| 4.39 | Pulls the cowl on (69.25–71.45) | **Overcharge**: his lightning floods the frame; the suit burns in brightest-first | Electric swell, zap |
| 6.59 | **"How's this for power?"** (110.18–112.06, 1:1 lip-sync) → freeze | **Whip pan** with a bolt riding it | Whoosh, zap |
| 8.78 | **Drop**: the lightning throw (124.20–124.78) + LET | **Strike**: a leader bolt, then two impact frames (gold negative, hard silhouette), a shockwave and residual bolt | Time-stop suck-in, thunder, sub, the drop |
| 9.51 | The scream (127.70–128.43) + GO | Cut on the beat | Zap on GO |
| 10.25 | Lightning climbing his body (113.10–114.56) | **Emblem**: draws itself in lightning, fly through the bolt | Hum, zap, whoosh |
| 11.71 | Run into the lens (65.05–68.60, ramped 1.9×→0.5×) | **Time remnants** converge | Shimmer, whoosh |
| 13.91 | Wall run, rotated to run up the frame (80.85–82.25) | **Pass-by**: his body smears off the lens | Doppler whoosh |
| 15.37 | Lightning crawling on his face (89.75–91.05) | **Lightning split** | Zap, crack |
| 16.83 | Dark, lit by his lightning (53.40–54.13) | **Speed smear** | Whoosh |
| 17.57 | The grin (56.10–57.56) | **voidfx logo** as supplied, through the "o" (once) | Impact, shimmer, whoosh |
| 19.03 | The glowing eyes (116.62–118.08) | **Impact frame** | Hit, zap |
| 20.49 | Final sprint with afterimages (4.30–6.13) | **Shockwave** from his face | Whoosh, boom |
| 22.32 → 23.42 | **He runs back in time**: the whole edit rewinds onto frame 0 | — | The song runs backwards, tape scrub, crackle |

## Graphics

All of these are tied to the footage:
- **Lightning that hugs the silhouette.** Arcs crawl along the MODNet person matte's edge, with the odd leap off the body, pulsing on the vocal chops before the drop and the beats after it. They match his gold lightning and extend the lightning already in the shots.
- **Eye arcs** anchored to the YuNet eye landmarks, on the breakdown's vocal chops.
- **Frozen-time sparks** in three depth layers: the far ones go behind him (matte), the near ones are out-of-focus bokeh in front.
- **Speed afterimages:** gold, ember and crimson silhouette echoes from earlier frames trail behind him, while his own silhouette stays clean.
- **The freeze:** the colour drains to cold steel and he stays brighter than the world.
- **Type:**
  - Bold, high-contrast two-line captions in the WARMPOP manner (Inter Display Black Italic, white with crimson and gold offset echoes; POWER? in electric gold). Each word eases in on its spoken time, and the words go cold on the freeze.
  - LET GO: white-hot to gold letters with a crimson depth shadow. Lightning crawls along the letter outlines; each word slams in on a beat, bounces on the kicks and streaks off at speed.

## Built-in review (before the final render)

The stills and every-cut sheets (`build.sh 102 auto`) caught these:
1. The sparks on the opener were invisible; they are brighter now.
2. LET GO sat behind Barry, but he fills the frame, so it was invisible. It is in front now.
3. The 9:16 crop of the scream cut out the lightning blast. The drop now opens on the wide lightning throw; it turned out to be one take that the shot detector had split on the flash, which was checked on frames and merged.
4. The rewind looked like VHS scanlines over a blur. It is now two crisp frames per step with gold speed streaks.
5. The bolt split left two half-faces on screen; the halves now fade as they fly apart.
6. The overcharge peaked on a flat white frame; it now burns in through gold.
7. The time-remnant arrival blew out to white; it is re-weighted.
8. LET GO's exit overlapped the emblem slam; it now exits earlier.
9. The face tracker lost the tiny far runner at the start of the run into the lens, so that shot's framing is now locked to its measured position.
10. The same sprint was used twice; the post-drop slot now uses the garage shot.
11. The street run and the lightning throw were split by the shot detector on lightning flashes; both were merged in `shots_fb.json` after checking on frames.

### Checkpoint run 1: automated FAIL on the loop seam (not shipped)

- Nine of ten criteria passed: −13.4 LUFS / −4.1 dBTP after AAC, 0 clicks at the 13 cuts, faces centred, no text over faces, no frozen or black frames.
- **Loop seam picture: FAIL** (last frame luma 205 vs first 122). The rewind added its own flash on top of frames that already contain the opener's flash, so the brightness doubled at the wrap.
- The visual sign-off on frames pulled from the encoded MP4 found two more problems:
  - the overcharge still had two flat gold frames;
  - the row-sliced speed smear read as blocky compression artifacts. It was replaced with a clean light-streak transition.

### Checkpoint run 2: automated FAIL on the loop seam (not shipped)

- The seam gap was down to a blurred difference of 27 (limit 12).
- The rewind lands on source frame ~1, but the opener's flash was already fading by frame 1. The flash is now flat for the first two frames; the stills measured 0.25.
- The upload encode is now capped at 16 Mb/s in `render102.py`, keeping it under TikTok's upload limit.

### Checkpoint run 3: automated PASS, visual sign-off PASS (shipped)

| Check | Result |
|---|---|
| Format | 1080×1920, 60 fps, 1405 frames, H.264 + AAC, fast-start, 49.3 MB (16.8 Mb/s) |
| Loudness after AAC | −13.4 LUFS, true peak −4.1 dBTP |
| Clicks | 0 at the 13 cuts; loop seam clean |
| Loop seam picture | matched: luma 134.6 / 134.5, blurred difference 0.48 |
| Faces | centred in every shot (1 frame flagged inside the rewind blur, within tolerance) |
| Text over faces | 0 frames |
| Frozen / black | none |
| Length | audio and video within 7 ms |

**Visual sign-off** was done on frames pulled from the encoded MP4: every cut, the captions, LET GO, the strike and impact frames, the emblem fly-through, the rewind, and the seam (frames 1403 → 1404 → 0 → 1).

**Not verified:** watching and listening in real time. The sound was checked by measurement: loudness, true peak, clicks at every cut, the seam, and section levels (breakdown −17.5, freeze −25.1, drop −14.0, rewind −18.2 dB RMS).
