# HANDOFF: v10 LET IT HAPPEN (The Flash × Tame Impala "Let It Happen"): STANDARD

**From:** the Flash studio (Studio 1) · **Date:** 2026-11-07 (verdict given 2026-11-05) · **Revisions:** 5 · **Folder / branch:** `v10/` on `claude/gallant-planck-pqpczp`

## 1. Verdict, in the owner's words
> "I like this edit and would like for you to make it a standard."

- **Status:** standard, the reference for **motion and professional finish**. Its engine is inside v11's, which the Flash scaffold starts from.
- **Gripes on the way:** *"lacklustre"* twice (rev 1 → 2, and rev 4 → 5: *"I still think it's lacklustre and has room for improvement. It could use more animations and overall professionalism."*).

## 2. The edit at a glance
| | |
|---|---|
| Song / window | Tame Impala "Let It Happen" (radio edit), 1:34.32–1:59.28 (h392–h496, 13 bars), 125 BPM. The bass-less "whirlwind" breakdown is the cold open; the drop at 1:41.94 (+26.5 dB) is the biggest change; the song's own gated stutter (silence every 4th half-beat) becomes a time freeze; "All this running around" runs into the loop. |
| Length / format | 24.96 s, 1080×1920, 60 fps (24p source with flow in-betweens on the slow-motion shots) |
| Concept | "Let it happen": Barry stops holding back. Calm in the dark lab → his lightning ignites → the drop dives through his chest emblem → the hunt of light → LET IT HAPPEN struck by lightning → time stops on the stutter → he outruns time and the loop flies back through the edit. Found in the **song's title and structure** (the stutter = frozen time). |
| Look | **PRISM SPEED:** graphite-slate shadows, rich suit crimson, white-gold lightning with bloom, a prismatic RGB time-slice on the fastest moments, the frozen world drained to steel. |
| Structure | 0–7.7 s cold open (6 beat-cut shots, the lightning building) → 7.7 drop: emblem dive + drop wave → 7.7–13.4 hook montage (speed ramps, beat camera) → 13.4 logo pass + LET IT HAPPEN → 17.8–21.1 time freeze on the stutter → 21.1 the run → 23.85 the ring of AROUND opens → loop. |
| Set pieces | **Emblem dive** (the tracked chest emblem flares, arcs crawl over the suit, the camera dives into the bolt, bursts through into the next shot; a refracting shockwave). **TIME PARTICLES** (the frozen frame breaks into its own pixels, hangs, rebuilds as the next moment on the beat). **THE SPEED FORCE LOOP** (AROUND's letters run a ring that opens into a tunnel; the edit's own moments fly past newest→oldest; frame 0 lands). |
| Transitions | 20+, each with its own sound. New in v10: speed slices, lightning tear, arc link, ignite, emblem dive, ramp, shock, prism cut, bolt strike, freeze-in, restart, phase, whirlwind, lightning branches (Lichtenberg), lens shatter, perimeter lap, time particles, drop wave, Speed Force tunnel. |
| Text | Lyric moments in the approved v9 caption construction, gold emphasis, every word on its sung onset: IT'S GONNA / CARRY OFF (a lightning runner drops each word off, then snatches the letters away), ALL THAT / ISN'T BOUND (a gust takes every word but BOUND), AND (gold charge fills the letters through the held note), IT / HAPPENS (slam), WHEN IT / HAPPENS (echo), LET IT / HAPPEN (each letter struck by a bolt), ALL THIS / RUNNING AROUND (AROUND runs the ring). |
| Sound | The song window straight; a crackle bed under the cold open; a whine/crack/sub/rush into the drop; ticks on the freeze gaps; a sound per transition; a swish on each camera punch; the song rewinding at speed (box-filtered, so it's smooth) under the loop. −12.7 LUFS / −3.5 dBTP after AAC. |

## 3. Creative process
1. `song_map` found the drop and the breakdown; the vocal stem and pitch track gave the stutter's gaps and every word's onset (Whisper was up to 1 s off on held notes).
2. Shots came from one 720p pack (24p content). From rev 3 every frame used was restored (Real-ESRGAN compact, 2×, only the band each frame uses).
3. The concept mapped the song's events onto the Flash: the breakdown = the calm before the lightning, the drop = into the emblem, the stutter = frozen time, "running around" = outrunning time back to the start.
4. Rev 5 changed the approach: instead of adding more overlays, the shots themselves were made to move with the music (the motion pass).

## 4. Revision history
- **Rev 2, the owner's note:** *"I would like for you to implement more animations, graphics and transitions into the edit. I want there to be relatively no breathing room or deadspace. I would also like for you to remove the scene with Barry's eyes being lit up and replace it with another high quality scene."*
  - **Diagnosis:** the cold open was four calm 1.9 s shots: dead space.
  - **Change:** 6 beat-cut shots, speed slices and a lightning tear; the eyes shot replaced by his own lightning igniting; depth sparks, edge lightning, sweeps, beat pulses; the CARRY OFF lyric.
  - **Tried and failed:** a magenta-graded profile shot (off-palette); the tear first ran under the caption; effects on frame 0 broke the loop seam (moved to bar 2).
- **Rev 3, the owner's note:** *"I would like for you to implement cooler transitions… more animations and graphics… unique and visually appealing… the text timing and animations… smooth… change the loop transition/animation to be more unique, creative… drastically improve the edit… best quality."*
  - **Diagnosis:** soft 2.7× blow-ups; captions up to 1 s off the sung words; a plain motion-blurred rewind loop.
  - **Change:** source restoration; every word re-timed to its sung onset; seven set-piece transitions; the Speed Force loop.
  - **Tried and failed:** lightning branches first glowed into a white mass; the perimeter wipe's straight edge cut through his face (rebuilt as a spiral wake); ribbons and wind crossed a masked face (head box from the matte); the AROUND letters first jumped through his body.
- **Rev 4, the owner's note:** *"Remove the glass shatter scene when Barry's picking up bullets and replace it with another unique or really cool animation or transition… change the animation for the words its gonna carry off… implement a brand new animation… unconventional for simple tiktok edits."*
  - **Diagnosis:** the glass web over the frame read as a cheap overlay (the same failure Studio 2 hit in FOREVER).
  - **Change:** TIME PARTICLES; the lightning-runner CARRY OFF; a bullet-time camera in the frozen holds.
- **Rev 5, the owner's note:** *"I like this edit and the text but I still think it's lack luster and has room for improvement. It could use more animations and overall professionalism."*
  - **Diagnosis:** shots played at 1× with gentle zooms; 24p stepped at 60 fps; the camera didn't react to the music.
  - **Change:** the motion pass: speed ramps on every hook shot (a burst on each beat, flow slow motion between), a beat camera (5.5–6 % zoom punch, ±1° rotation kick, zoom blur + colour split on the hit frames), light rays from the lightning.
  - **Tried and failed:** the rays first washed the strike shot orange (now scaled down on bright frames).

## 5. What made it good / what made it weak
- **Good (the owner):** approved as a standard after the motion pass; the text was liked from rev 4 on (*"I like this edit and the text"*).
- **Good (the studio's analysis):**
  - motion on every beat is what read as professional;
  - set pieces built from the character (emblem, lightning, the Speed Force, frozen time);
  - text that acts out its lyric on the sung onsets;
  - a loop that is a set piece and lands on frame 0;
  - restored, sharper picture.
- **Weak:** it took five rounds; effects layered on static shots didn't fix "lacklustre". Measured against the later v11 rules: light rays are drawn over him, not only behind (Studio 2's rule 1).

## 6. Measured results
| Check | Result |
|---|---|
| QC checkpoint | all PASS |
| Loudness after AAC | −12.7 LUFS / −3.5 dBTP |
| Loop seam (blurred diff; target ≤ 1) | 0.93 |
| Flashes | the drop's impact frame and short flares; no measured white-out run (not checked with a flash-rate QC at the time) |
| Softest shots | not measured at delivery (the sharpness tool came later) |
| Transitions / longest span without a beat | 20+ / under ~1 s in the hook (every beat punches) |

## 7. New rules (adopt in both studios)
1. **Run a motion pass on every edit:** speed-ramp every hook/montage shot (a burst on each beat, ~0.3–0.6× flow slow motion between, the same source range), make the camera move with the music (≈5–6 % zoom punch and a ±1° rotation kick per beat, zoom blur and slight colour split on the hit frames, type kept clean on top), and let light react to the footage. Evidence: "lacklustre… could use more animations and overall professionalism" (v10 rev 5), then the standard. Applies to: all edits.
2. **Restore 720p sources before rendering** (`tools/sr_prep.py`: AI 2× on only the band each frame uses, ~3 s per source frame on CPU, in the background). Evidence: "best quality" (v10 rev 3). Applies to: all edits.
3. **Put every lyric word on its sung onset,** checked on the Demucs vocal (pitch + onsets), not Whisper alone. Evidence: "ensure the text timing is good" (v10 rev 3); Whisper was up to 1 s off. Applies to: all edits.
4. **Make the loop a set piece that lands exactly on frame 0** (seam measured, blurred diff ≤ 1); a motion-blurred rewind reads as low quality. Evidence: "change the loop transition/animation to be more unique, creative and visually appealing with better quality" (v10 rev 3). Applies to: all edits.
5. **Read "lacklustre" as missing motion and polish, not missing overlays;** plan the speed curve and the camera with the shot list. Evidence: rev 2 → rev 5. Applies to: all edits.
6. **Don't solve a moment with an overlay that sits on the frame** (a glass web, hanging shards); transform the picture itself. Evidence: "remove the glass shatter scene" (v10 rev 4). Applies to: all edits.

## 8. Reusable assets
| Technique / transition | Where the code is | How to restyle it for another show |
|---|---|---|
| Velocity `vel()` + flow on restored bands (`sr_flow_part`) | `tools/edl_template.py`, `v10/work/render10.py` (rev 5) | Show-agnostic. |
| Beat camera `beat_bounce`, `shake`, `beat_fx` | `render10.py` (rev 5) | Show-agnostic; tune the punch for slower songs. |
| Emblem dive `emblem_gate` + `drop_wave` | `render10.py` | Any tracked emblem or object (a badge, a slide, the Dark Passenger's knife hilt). |
| TIME PARTICLES `time_particles` | `render10.py` (rev 4) | Any freeze: colour the glints to the edit's palette. |
| Bullet time (auto on frozen holds) | `render10.py` (rev 4) | Any freeze-frame with a person matte. |
| Lens shatter, Lichtenberg branches, perimeter lap, phase, whirlwind, speed slices, lightning tear | `render10.py` (rev 2/3) | Swap lightning for blood, neon, ink. |
| The Speed Force tunnel loop (`tunnel_frame`, `portal`, `tunnel_in`) | `render10.py` (rev 3) | A tunnel of the edit's own moments for any show (case photos, slides). |
| Lyric animations (`text_carry4`, `text_charge`, `text_run3`) | `render10.py` (rev 3/4) | Re-colour; the runner can be a knife glint for Dexter. |
| Box-filtered song rewind (`music10`) | `v10/work/audio10.py` | Any rewind loop. |

## 9. For the other studio
- The motion pass was the turning point; DRACULA plays every source at its own cadence. A speed-ramped montage with flow in-betweens on restored frames could lift the next Dexter montage.
- TIME PARTICLES is a Studio-2-props-rule-compliant replacement for a glass shatter (the picture itself breaks apart, off-face first).
