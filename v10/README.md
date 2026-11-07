# LET IT HAPPEN — The Flash × Tame Impala "Let It Happen" (voidfx v10, 9:16)

> **Approved as a standard (rev 5):** *"I like this edit and would like for you to make it a standard."* It's the newest benchmark and the engine `tools/new_edit.py` builds every new edit on. See `CLAUDE.md` and the handbook §1 for what it's the reference for.

A 24.96 s, 1080×1920, 60 fps TikTok edit. It loops: on "running AROUND" the letters run a ring that opens into the Speed Force, and he flies back through the edit's own moments to its first frame (rev 3).

**Deliverables:**
- `v10/out/let_it_happen_flash_voidfx_9x16.mp4`: H.264 + AAC, fast-start (upload this one).
- `v10/out/let_it_happen_flash_voidfx_9x16_master.mov`: CRF 11 + 24-bit PCM master.

**Sources:** the brief mentioned attached scene packs, but only the song was attached. The edit uses the two Flash packs already in the library:
- `src/flash_b.mp4`: 60 fps container with 24p content, 151 s, 64 shots reviewed. Every shot in the edit comes from this pack.
- `src/flash_a.mp4`: reviewed (48 shots), but it duplicates `flash_b` at 25 fps, so it isn't used.

**Featured character:** one featured Barry Allen (Grant Gustin) with his gold-orange lightning. These were left out to keep the character and colour consistent:
- the Reverse-Flash shot;
- the purple- and blue-lightning speedster shots;
- the black-suit shot;
- frames with a "FAST TRACK LABS" sign;
- the run straight at the camera and the floating shot (both rejected in v5).

## Song: the section used and why

`src/let_it_happen.mp3` is the 4:16 radio edit, mapped at 125.0 BPM (half-beat 0.24003 s). The grid was verified across the window. The vocal was separated with Demucs and word-timed with Whisper, then re-checked in short windows.

**Window:** half-beats 392 → 496 (1:34.32 → 1:59.28, 13 bars).

| Song | What happens | Edit |
|---|---|---|
| 1:34.32 | The bass-less "whirlwind" breakdown: *"it's gonna carry off all that isn't bound…"* | **0.00**: cold open, the build |
| 1:40.26 | *"And when…"* | 5.96 |
| **1:41.94** | **The drop:** the bass returns, +26.5 dB, the biggest change after the intro. *"…it happens, when it happens"* | **7.68: the camera dives through his chest emblem** |
| 1:47.68 | *"So let it happen, let it happen"* | 13.4: the LET IT / HAPPEN hero title |
| **1:52.04** | **The song's own gated stutter:** the music cuts out completely every fourth half-beat | **17.76: TIME STOPS between the beats** |
| **1:55.41** | Second impact (+15 dB): *"All this running around"* | **21.12: time restarts, afterimage run** |
| 1:59.28 | The bar line before *"I can't fight it much longer"* | 24.96: he becomes light, time rewinds to the start |

The section has the song's biggest drop and its title hook. Two of its lines read like Barry's own story (*"a whirlwind that's coming 'round"*, *"all this running around"*), and its built-in stutter is a ready-made time freeze.

**Lyrics on screen:** only the unambiguous lines (AND WHEN IT HAPPENS, LET IT HAPPEN, ALL THIS RUNNING AROUND). Two lines stay off screen because the isolated vocal is ambiguous:
- *"isn't bound / found"*;
- *"won't / will be holding on"*.

## Concept: "Let it happen." Barry stops holding on.

**The build:** in the quiet before the whirlwind he stands calm in the dark lab, smiles, and his eyes catch lightning. The Speed Force crawls over his suit (arcs born on his MODNet silhouette edge, so they follow his body).

**The drop:** his **chest emblem flares**, arcs spread out across the suit, and the camera **dives into the bolt of his own emblem**. The take-off bursts through it as the bass hits.

**The hunt of light** follows:
- the thrown bolt carries across the cut;
- the garage run with afterimages;
- the scream's electric shockwave;
- the grin;
- LET IT / HAPPEN struck letter by letter by lightning.

**The freeze:** a bolt strikes him, and on the song's gated stutter **time stops**. The world drains to steel, gold sparks hang in the air, and only the lightning stays alive. Time jolts forward only on the beats.

**The run:** on *"All this running around"* time restarts in a wave of colour. He runs with his own afterimages trailing him, becomes a line of light, and **outruns time**. The whole edit plays backwards through a streaked time tunnel and lands on the first frame: the loop.

**Look: PRISM SPEED** (new; added to the style bank):
- graphite-slate shadows;
- rich suit crimson;
- white-gold lightning with bloom and anamorphic streaks;
- a prismatic time-slice (colour channels from different moments) on the fastest moments;
- the frozen world in steel.

Skin is protected from the slate push, and blacks keep a floor.

**Type:** the approved v9 system (bold keyline captions, a per-letter hero title), recoloured with **lightning-gold emphasis**. Three Flash-specific variants:
- **HAPPENS slam:** lands white-hot, with arcs and a light ring.
- **Echo:** WHEN IT / HAPPENS arrives with converging gold afterimages.
- **Speed text:** ALL THIS / RUNNING AROUND runs in with his motion and gets pulled into the light streak.

## Signature set pieces (the handbook's §5a gate)

1. **The emblem dive (drop).** His real chest emblem, tracked over time, flares, and arcs spread across the suit. The camera zooms through it, keeps diving through the emblem's texture, and the next shot opens through the bolt with a shockwave. AND WHEN rides the dive.
2. **LET IT / HAPPEN.** Each letter is struck by its own bolt and blooms in white-hot. HAPPEN lands bigger and floods gold. On the second *"let it happen"* the title pulses with lightning, then streaks off.
3. **Time stops (stutter).** The music's gaps freeze the picture: steel world, suspended sparks, lightning kept, a clock tick. On each hit, time lurches forward with a smear. The drain enters as a sweeping gold time-line.
4. **Outrunning time (loop).** Afterimages of his own past positions trail him. The run stretches into a line of light, and the edit **rewinds through every shot** in a streaked, prismatic tunnel, landing on frame 0 while the song rewinds with it.

## Comparison with the benchmarks (written before rendering, per §5a)

- **v5 FASTEST (the earlier Flash edit):**
  - v5 opened on a CG emblem drawn on black and flew through its bolt. Here the dive goes into **his own suit emblem**, tracked in the footage, mid-scene, on the drop.
  - v5's afterimages were shifted copies of the whole frame. Here they're **his own matte cutouts** from earlier frames.
  - v5 lightning was overlaid. Here the arcs are **born on his silhouette** and the transition bolts **start and end at his tracked position**.
  - v5 had no time freeze or rewind.
- **v6 WARMPOP and v7 HIM ALL ALONG:** density and themed physicality match theirs (16 designed transitions, 4 set pieces, 5 text moments). The concept comes from the character (Speed Force, time freeze, time travel), as the v9 feedback demands.

## Timeline

| Edit | Shot (`flash_b` source s) | Transition in |
|---|---|---|
| 0.00 | Calm in the dark lab, emblem glowing (38.6) | **rewind landing** (the loop) |
| 1.92 | The smile (34.4) | **arc link**: an arc leaps from his chest to his chest, bowing round him |
| 3.84 | Lightning in his eyes (116.6) | **ignite**: dark, then bolts strike either side and he comes up brightest-first |
| 5.76 | Lightning crawling over the suit (83.85, blended slow-motion). AND WHEN | **arc link** |
| **7.68** | **Take-off, lightning erupting (4.62).** IT / **HAPPENS** | **EMBLEM DIVE** |
| 9.12 | The lightning throw (124.4) | **speed ramp** |
| 9.60 | Garage, lightning run, afterimages (113.55). WHEN IT / **HAPPENS** (echo) | **bolt link**: his thrown bolt tears across the cut |
| 11.04 | The scream (127.7) | **electric shockwave** |
| 12.00 | The grin (56.3) | **prism cut** (red, green and blue switch shots in turn) |
| 12.96 | Turning to camera (102.9) | **speed ramp** |
| 13.44 | Masked at night (109.8). **LET IT / HAPPEN** | **voidfx logo, original** (fly through the "o") |
| 16.32 | Struck by lightning (10.36) | **lightning strike** (onto his shoulder, clear of his face) |
| **17.76** | **Frozen office (13.0–16.2, advancing only on the beats)** | **time stops**: a gold time-line sweeps the colour out |
| 19.68 | Frozen: he reaches through it (28.1–29.4) | **time jolt** |
| **21.12** | **The run (80.86), afterimages and arcs.** ALL THIS / **RUNNING AROUND** | **time restarts**: a wave of colour and speed |
| 23.04–24.00 | The run stretches into a line of light | |
| 24.00–24.96 | **Rewind through the whole edit** → frame 0 | |

## Sound

- **Song:** the window plays straight, with no dialogue (the packs have none usable).
- **Rewind:** from 24.0 s the song **rewinds at speed** from 1:58.3 back to 1:34.3, decelerating as it lands, matching the picture, and loops into the breakdown. The click check at the rewind join and at the loop seam is clean.
- **Effects, saved for the moments that matter:**
  - the drop (charge whine, crack, sub boom, rush through the bolt);
  - the thrown bolt tearing across the stereo field;
  - the strike (thunder);
  - time stopping (a reverse swell into a dead tick, and a clock tick in every gap of the stutter);
  - time restarting (sub boom, whoosh, crackle);
  - the rising whine into the line of light.
- **Quieter layers:** small crackles on the arc links, bolt zaps under each title letter, and a low electrical bed where the arcs crawl over him.
- **Mastering:** built circularly, mastered on a wrapped copy, loudness measured after AAC.

## Frame rate and motion

- **Footage cadence:** the footage is 24p inside 60 fps, and shots play at their own cadence (`hold`) with no synthesised frames.
- **Blended shots:** two shots are slowed with frame blending rather than optical flow. Flow warps lightning.
  - the lightning-charge shot (0.62×);
  - the run (0.75× → 0.25×).
  On both, the blend sits under deliberate afterimages and arcs.
- **The stutter:** frozen frames, then fast-forward jumps (1.7–3×) with shutter blur.

## Built-in review

**Pass 1** (stills): the emblem dive was a flat yellow card. It became a continuous dive into his real chest emblem: its position is tracked over time (it moves from y 462 to 632 in source pixels), and the zoom continues through its texture.

**Pass 2** (every-cut sheets):
- **Lightning over his face:** the arc links, the ignite strikes, the thrown bolt and the lightning strike crossed his face, which is against the "no gimmick on the face" rule. Every bolt now bows round him below the jaw or lands at the side; a face-box guard keeps bolt paths off faces.
- **A target ring:** the time-freeze wipe started as a small ring around a face. It's now a sweeping gold time-line.
- **Wrong subject:** both freeze shots framed the wrong person (the frozen man, then Joe). Both are now framed on Barry.
- **Blocky title exit:** the LET IT / HAPPEN exit stretched letters into blocks. It's now a motion-blurred streak.

**Pass 3** (frames pulled from the first encoded MP4):
- **Loop tint:** the rewind's last frame kept a faint gold tunnel tint that frame 0 doesn't have (picture seam diff 6.2). The tunnel now fades out before the landing; the seam diff is 0.39.
- **Bolts over the chin:** the bolts striking the first letters of LET IT passed over his chin. They're now short strikes from under his jaw.
- **Unreadable hook:** RUNNING AROUND was swallowed by the light streak before AROUND could be read. The streak now starts half a bar later (e98), so the line reads in full before it smears into light.

**Checkpoint on the final encoded MP4: SHIP.**
- **Format:** 1080×1920, 60 fps, 1498 frames, clean decode.
- **Loudness:** −12.7 LUFS, true peak −3.5 dBTP after AAC.
- **Face centring:** 0 flagged frames on every tracked shot. The freeze, run and rewind shots are framed manually on Barry.
- **Text vs. faces:** 0 frames where a face reaches into a text band. The 4 low-placed detections were checked on frames and are title letters and lightning, not faces.
- **Cuts:** 0 clicks at 15 cuts; no frozen runs.
- **Near-black frames:** one, frame 229, the deliberate blackout inside the ignite.
- **Loop seam:** picture matched (luma 38.8 → 38.9, diff 0.39). Audio is continuous: the rewind lands at −18 dB and the opening plays at −18 dB.
- **A/V length:** within one frame.

**Visual sign-off:** frames pulled from the encoded file around every transition, every text moment, the emblem dive, the freeze, the run, the rewind and the loop seam.

**Not verifiable here:** I can't watch or listen. Everything above was checked on frames and by measurement, but the edit has not been seen in motion or heard. Please watch it once with sound.

## Files

- `work/edl10.py`: every decision.
- `work/render10.py`: the engine plus the v10 section at the end:
  - grade and finish;
  - tracked edge arcs, afterimages, time-slice and the frozen world;
  - 11 new transitions;
  - the light streak and the rewind;
  - four type styles.
- `work/audio10.py`: the soundtrack.
- `work/qc10.py`: the checkpoint.
- `work/tracks10.json`: face tracks.
- `work/shots_fa.json`, `shots_fb.json`: shot lists.
- `work/song_map.json`, `tr_song.json`: song analysis.
- Media stays out of git.

Re-render: `bash tools/build.sh 10 prep audio video qc`


## Revision 2 (owner feedback)

> "Implement more animations, graphics and transitions… relatively no breathing room or deadspace… remove the scene with Barry's eyes being lit up and replace it with another high quality scene."

**The eyes shot is gone.** It's replaced by `flash_b` 52.85–54.30: the masked Flash in the dark as **his own gold lightning ignites along his suit** and builds into arcs across his shoulders. The lightning is real (from the footage), it builds toward the drop, and it comes in through the **ignite** transition (blackout, side strikes, brightest-first reveal).

**The cold open no longer breathes.** It used to be 4 calm 1.9 s shots; it's now 6 shots cut on the beat:

| Edit | Shot | Transition in |
|---|---|---|
| 0.00 | Calm in the dark lab | rewind landing |
| 0.96 | **New:** unmasked, a hard look (37.16) | **new: speed slices** (the frame rips into horizontal bands at different speeds; gold leading edges) |
| 1.92 | The smile | arc link |
| 2.88 | **New:** masked close-up in the garage (136.50) | **new: lightning tear** (a bolt cracks straight across, below the caption and clear of his face; the halves fly apart) |
| 3.84 | **New:** his lightning ignites (52.85) | ignite |
| 5.76 | Lightning over the suit (the emblem) | arc link → emblem dive |

**New graphics and animation everywhere:**
- **IT'S GONNA / CARRY OFF**: a new lyric in the opening (verified words only). It builds in the approved caption style; then a whirlwind lifts the letters off one by one and spirals them away, trailing gold.
- **Speed Force sparks in depth:** far sparks drift behind him through the matte, near ones streak past soft in front. Used in the cold open, take-off, garage and hook.
- **Edge lightning on the bar lines** of the cold open (from bar 2, so the loop seam stays clean), the hook and the run: bolts flicker down both frame edges, never the centre.
- **Gold light sweeps** across the frame on the cold open's bar lines (from bar 2).
- **Time-line ripples:** a gold time-line sweeps across on each beat that jolts frozen time forward.
- **Beat pulses:** soft zoom pulses on every beat of the cold open; stronger ones after the drop and in the run.

**Transitions:** 18 designed cut transitions plus the light streak and the rewind, all with their own sound. New sounds:
- band whooshes for the slices;
- a crack and rip for the tear;
- a gust for the whirlwind;
- quiet crackles for the edge bolts and the freeze ripples;
- a shimmer for the sweeps.

**Review:**
- The garage close-up replaced a red-lit profile that graded magenta and showed green suit lenses (off-palette).
- The tear was moved off the caption.
- Every-cut sheets were checked.

**Loop seam:** the first rev 2 render showed a picture seam diff of 2.79, because the new edge bolts and sweep fired on frame 0, the rewind's landing. They now start at bar 2, which brings the diff back to 0.39.

**Ship checkpoint (rev 2, measured on the encoded MP4):**

| Check | Result |
|---|---|
| Format | 1080×1920, 60 fps, 1498 frames, decodes clean |
| Loudness | −12.7 LUFS, −3.5 dBTP after AAC |
| Faces | every shot centred, no failures |
| Text vs faces | clear; frame 182 flags the tear's glow, not a caption (checked) |
| Cuts | 17 cuts, 0 audio clicks |
| Black frames | frame 229 only (the ignite blackout, by design) |
| Loop seam | picture luma 39.4 → 39.5, diff 0.39; audio −18 dB on both sides of the wrap |
| A/V length | within one frame |
| Verdict | SHIP |

**Visual sign-off** (frames from the encoded file):
- the loop seam (1494 → 3);
- the slices, arc link and tear;
- CARRY OFF and its whirlwind;
- the ignite blackout into the ignition shot;
- the emblem dive and every hook caption;
- the logo pass, LET IT HAPPEN, the freeze, the run and the rewind.

## Revision 3 (owner feedback)

> "Implement cooler transitions… more animations and graphics… unique and visually appealing… ensure the text timing and animations are visually appealing and smooth… change the loop transition/animation to be more unique, creative and visually appealing with better quality… drastically improve the edit to be the best flash edit you have created and with the best quality."

### Picture quality
The 720p pack used to be blown up 2.7× (cubic + unsharp mask), so faces were soft and showed compression blocks. Now `tools/sr_prep.py` runs Real-ESRGAN compact (general-x4v3 blended 50/50 with its denoising twin) on exactly the band each frame is cropped from, at 2×, and the renderer samples the restored band: cleaner edges, real hair and stubble detail, no blocking. The unsharp mask drops from 0.40 to 0.16 on restored frames.

### Text: re-timed and redesigned
Every word was re-timed to its sung onset on the vocal stem (pitch track + onsets, checked against Whisper and the verse's parallel phrasing). The old times were off by up to a second:

| Line | Was | Now |
|---|---|---|
| ALL THIS RUNNING AROUND | 20.96 s (the vocal is silent until 22.08) | **22.08 / 22.64 / 23.08 / 23.65** |
| IT HAPPENS | HAPPENS 0.2 s late | IT 8.21, HAPPENS 8.33 |
| WHEN IT HAPPENS | HAPPENS 0.2 s early | WHEN 9.05, IT 10.10, HAPPENS 10.22 |
| AND (WHEN) | 0.2 s late | 5.78 / 7.25 |
| ALL THAT ISN'T BOUND | not shown | 3.36 / 3.87 / 4.59 / 5.34 |

Text moments, in the approved caption construction (keyline, soft shadow, gold emphasis, every word easing in):
- **IT'S GONNA / CARRY OFF**: the whirlwind lifts the letters off in reading order and spirals them away, each with a short gold trail.
- **ALL THAT / ISN'T BOUND** (new, completes the sentence): a gust takes every word except BOUND, which locks in place with a flash. Then BOUND is struck and bursts, clearing the way for AND.
- **AND**: gold charge rises inside the letters through the long held note, crackling at the top; WHEN lands white-hot. Both ride the emblem dive.
- **ALL THIS / RUNNING AROUND**: the words run in on their sung onsets. Then the letters of AROUND leap onto a ring and run round it, and the ring becomes the loop.

### New transitions (each with its own sound)

| Edit | Into | Transition |
|---|---|---|
| 0.96 | look | **Phase**: he vibrates his molecules and passes through the frame (chromatic copies, row shimmer, every edge lit gold) |
| 2.88 | garage close-up | **Whirlwind** on "carry OFF": the frame twists into a spiral storm and the next shot unwinds out of it |
| 5.76 | lightning over the suit | **Lichtenberg**: a branching lightning figure grows from his chest (stopping short of his face); the next shot opens inside the branches |
| 7.68 | the drop | the emblem dive, now followed by a **particle-accelerator wave** (a refracting dark-matter ring) |
| 9.60 | garage | **Lens shatter**: the lightning he throws hits the camera lens; electric cracks, then the glass bursts toward us |
| 12.00 | grin | **Perimeter**: he runs laps round the frame edge as a streak; the next shot fills in as a spiral wake closing on the centre |
| 19.68 | frozen moment 2 | **Frozen shatter**: frozen time cracks like glass; the shards hang apart, and the beat that restarts time blows them away |
| 23.85 → 0.00 | **the loop** | **The Speed Force**: AROUND's letters run a ring of lightning that opens in the middle of the run. Inside, the edit's own moments fly past as glowing panels, newest to oldest, through a turning tunnel of light; the first shot comes up ahead and lands as frame 0. The song rewinds underneath (now anti-aliased: smooth, not gritty) and starts after "around" finishes |

Kept from rev 2: speed slices, ignite, the emblem dive, the speed ramps, the shock ring, the logo pass, the lightning strike, the time-stop wave, and the restart.

### New graphics
- **The whirlwind** (cold open): gold debris and pale wind streaks orbit him in depth. The far side passes behind him through the matte, the near side in front, never across his face. It builds through the breakdown and swells on the bar lines.
- **Lightning ribbons in 3-D** (ignition, LET IT HAPPEN): two ribbons spiral round him, behind his head and shoulders and across his chest, with a bright pulse running along them.

### Review passes
- **Lightning branches** first glowed into a white mass: now a sharp core with a modest glow, seeded at the emblem.
- **Perimeter** first split the frame with a straight clock-wipe edge through his face. It's now a spiral wake that closes on his chest, with a feathered edge.
- **Lightning ribbons** were mostly off-frame on the close-up. They now wrap behind his head and across the shoulders. They never cross a face: masked faces with no face track use a head box from the matte. The same rule applies to the wind.
- **AROUND** letters first jumped to the top of the ring through his body. They now step onto the bottom of the ring and run counter-clockwise, facing inward.
- **Loop seam:** the first render had a picture seam diff of 3.80, because the tunnel's rings and bolts were still over the landing panel. They now clear before the landing, the panel lands at exactly full frame, and the diff is 0.91.
- **ALL THAT / ISN'T BOUND** touched his chin early in the ignition shot (QC flagged 8 frames). The caption now sits 50 px lower.
- **The rewind** was gritty (about 30× playback with no filtering). It's now box-filtered over each output sample's span, and it starts after "around" finishes, with an equal-power crossfade.

### Ship checkpoint (rev 3, measured on the encoded MP4)

| Check | Result |
|---|---|
| Format | 1080×1920, 60 fps, 1498 frames, decodes clean |
| Loudness | −12.7 LUFS, −3.4 dBTP after AAC |
| Faces | every shot centred; one flag is the slices transition frame (checked) |
| Text vs faces | clear; frame 1464 flags a face inside a tunnel panel (checked) |
| Cuts | 17 cuts, 0 audio clicks; loop seam audio continuous |
| Black frames | none |
| Loop seam | picture luma 41.3 → 42.3, blurred diff 0.91 |
| A/V length | within one frame |
| Verdict | SHIP |

**Visual sign-off** (frames from the encoded file):
- the loop seam (1494 → 3);
- every new transition;
- each caption at its sung word;
- the ring and the tunnel;
- the frozen shatter.

## Revision 4 (owner feedback)

> "Remove the glass shatter scene when Barry's picking up bullets and replace it with another unique or really cool animation or transition… change the animation for the words IT'S GONNA CARRY OFF… implement a brand new animation or graphic somewhere throughout the edit… really well thought, cool, and executed in a manner that's usually unconventional for simple TikTok edits."

The props rule from Studio 2 (after FOREVER) also applies: glass, blood, slides, knives and tape must be motivated, brief, real-looking, in the edit's look, and off his face. The frozen-scene glass shatter broke that rule: a crack web and hanging shards over the frame.

- **TIME PARTICLES** (replaces the glass, 19.68 → 20.16 s, the frozen bullet scene):
  - The frozen moment comes apart into fragments of its own pixels: the edges first, the people last.
  - The fragments burst outward, then the frozen air slows them to a hang, like the bullets hanging around him. They turn slowly round a dark eye that opens in the middle of the frame.
  - Then they swirl back together as the next frozen moment. The rebuild starts at his reaching hand and the bullet, spreads outward, and lands exactly on the beat that restarts time.
  - Nothing is drawn: every fragment is a pixel of the real footage. Sound: disintegration grains, a shimmer while they hang, the grains reversed into an impact on the hit.
- **CARRY OFF**: a lightning runner streaks along the caption line and drops each word off in its wake on its sung onset (stretched and blurred, then sharp). On "carry off" the runner comes back along both lines and snatches the letters away: they stretch into gold speed smears and leave the frame with him. Sound: a zip per word, then the snatch.
- **BULLET TIME** (new animation): in every frozen hold (17.76, 18.72 and 20.64 s) the camera now glides through the frozen moment in 3-D. The people move against the room with real parallax (depth from the MODNet matte plus the floor), with a slow dolly push. The swing continues across the holds and resets inside the transitions. Sound: a soft panned air move.
- **Also fixed:** the speed slices left black gaps between bands for a frame or two. The gaps now show the incoming shot, smeared.

### Ship checkpoint (rev 4, measured on the encoded MP4)

| Check | Result |
|---|---|
| Format | 1080×1920, 60 fps, 1498 frames, decodes clean |
| Loudness | −12.7 LUFS, −3.5 dBTP after AAC |
| Faces | every shot centred |
| Text vs faces | clear. Frame 182 flags the masked close-up's neck under CARRY OFF (checked: the caption sits below his mouth). Frame 1464 is a face inside a tunnel panel. |
| Cuts | 17 cuts, 0 audio clicks |
| Loop seam | blurred diff 0.91; audio continuous |
| A/V length | within one frame |
| Verdict | SHIP |

**Visual sign-off** (frames from the encoded file): the runner dropping off each word and snatching them; the particle break-up, hang and rebuild (frames 1176–1208); the bullet-time glides (1068 → 1094, 1240 → 1266); the speed-slice gaps.

## Revision 5 (owner feedback)

> "I like this edit and the text but I still think it's lacklustre and has room for improvement. It could use more animations and overall professionalism."

Diagnosis against professional Flash edits: the shots played at plain 1× speed with gentle zooms. The 24p footage stepped (each frame held 2–3 times at 60 fps), and the camera didn't move with the music. This revision is a motion pass:
- **Velocity (speed ramps):** every hook shot (takeoff, throw, garage, scream, grin, turn, the LET IT HAPPEN close-up, the strike) is time-remapped to the beat. Each beat gets a speed burst (up to ~4.5×, with real shutter blur from the source frames), with smooth slow motion between beats (~0.3–0.6×). The slow motion uses optical-flow in-between frames built on the restored 2× source, so the footage plays at a true 60 fps instead of stepping. Each shot still uses exactly its old source range.
- **Camera animation:** the camera now moves with the music. On every beat of the hook and the run there's a 6 % zoom punch and an alternating rotation kick (±1.1°), plus zoom motion blur and a colour split on the hit frames. The type stays clean on top. The cold open keeps its soft 1 % breath.
- **Light rays:** volumetric god rays now pour out of the lightning (ignition, the charge, takeoff, throw, garage, scream, strike). They're softer where the frame is already bright.
- **Sound:** a quiet swish on each camera punch that isn't already a cut.

### Ship checkpoint (rev 5, measured on the encoded MP4)

| Check | Result |
|---|---|
| Format | 1080×1920, 60 fps, 1498 frames, decodes clean |
| Loudness | −12.7 LUFS, −3.5 dBTP after AAC |
| Faces | every shot centred, 0 flagged |
| Text vs faces | clear (frame 1464 is a face inside a tunnel panel) |
| Cuts | 17 cuts, 0 audio clicks |
| Loop seam | blurred diff 0.93; audio continuous |
| A/V length | within one frame |
| Verdict | SHIP |

**Visual sign-off** (frames from the encoded file):
- the beat punches with zoom blur and colour split (490/491);
- the rotation kicks (720, 780, 1300);
- a velocity burst (548) followed by crisp flow slow motion (557);
- the light rays on the strike, now moderate (1000/1010);
- the loop seam (1497 → 0).

Consecutive slow-motion frames in the garage and the grin were checked at full resolution for flow artifacts: they are clean.

