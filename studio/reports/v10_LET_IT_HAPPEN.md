# Edit report: v10 LET IT HAPPEN (The Flash × Tame Impala "Let It Happen")

> From the **Flash studio** for the other voidfx studio. Apply sections 7 and 8 to your `CLAUDE.md`, handbook and toolkit, then confirm what changed.

## 1. Verdict
**Approved as a standard** after 5 rounds. The owner: *"I like this edit and would like for you to make it a standard."* It's the standard for **motion and professional finish**. Before that, the owner called it *"lacklustre"* twice (rev 1 and rev 4).

## 2. The edit
- **Show × song:** The Flash × Tame Impala "Let It Happen" (radio edit, 125 BPM).
- **Section used:** 1:34.32 → 1:59.28 (13 bars, 24.96 s). The bass-less "whirlwind" breakdown is the cold open, the drop at 1:41.94 (+26.5 dB) gets the biggest transition, the song's own gated stutter (silence every 4th half-beat) becomes a time freeze, and "All this running around" is the run into the loop.
- **Concept:** "Let it happen": Barry stops holding back. Calm in the dark lab → his lightning ignites → on the drop the camera dives through his chest emblem → the hunt of light → LET IT HAPPEN struck by lightning → time stops on the stutter → he runs so fast he outruns time, and the loop flies back through the edit to frame 0.
- **Look: PRISM SPEED.** Graphite-slate shadows, rich suit crimson, white-gold lightning bloom, a prismatic RGB time-slice on the fastest moments, and the frozen world drained to steel.
- **Length / format:** 24.96 s, 1080×1920, 60 fps, loops.
- **Sources:** one Flash pack (`flash_b`, 720p, 24p content in a 60 fps file).

## 3. Creative process
- **Song first:** the beat grid and the section changes decided the structure; the drop sits at 31 % of the edit.
- **Set pieces:**
  - the emblem dive on the drop (the camera dives into his tracked chest emblem, through its bolt, into the next shot, and a refracting shockwave rings out);
  - TIME PARTICLES in the freeze (rev 4);
  - LET IT HAPPEN, with each letter struck by its own bolt;
  - the Speed Force loop.
- **Type:** the approved v9 caption construction recoloured gold, with each lyric moment acting out its meaning:
  - CARRY OFF: a lightning runner drops each word off, then snatches the letters away;
  - AND: gold charge fills the letters through the held note;
  - AROUND: the letters run round a ring.
- **Sound:** the song plus a crackle bed in the cold open, a whine/crack/sub/rush into the drop, ticks on the freeze gaps, a sound for every transition, and the song rewinding (anti-aliased) under the loop.

## 4. Revision history
| Rev | Owner's note | What changed | Why |
|---|---|---|---|
| 1 | (first delivery) | — | — |
| 2 | *"more animations, graphics and transitions… relatively no breathing room or deadspace… remove the scene with Barry's eyes being lit up"* | The calm 4-shot cold open became 6 beat-cut shots; new speed-slices and lightning-tear transitions; the eyes shot replaced by his own lightning igniting; depth sparks, edge lightning, sweeps, beat pulses | Dead space was the problem, not missing effects in the hook |
| 3 | *"cooler transitions… more animations and graphics… text timing… smooth… a more creative loop… best quality"* | Restored source (AI 2× upscale); every lyric re-timed to its sung onset (Whisper was up to 1 s off); 7 new set-piece transitions (phase, whirlwind, lightning branches, lens shatter, perimeter lap, frozen shatter, drop wave); the Speed Force loop | Quality and timing were part of "lacklustre" |
| 4 | *"remove the glass shatter scene… change the animation for IT'S GONNA CARRY OFF… a brand-new animation… unconventional"* | TIME PARTICLES replaced the glass; the lightning-runner CARRY OFF; bullet-time camera in the frozen holds | The glass web over the frame read as a cheap overlay |
| 5 | *"still… lacklustre… could use more animations and overall professionalism"* | **The motion pass:** speed ramps on every hook shot (a burst on each beat, smooth flow slow motion between), a camera that punches and kicks on every beat with hit-frame blur, light rays from the lightning | Effects on static, 1×-speed footage still read as amateur |

## 5. What made it good
- **Motion on every beat** (rev 5) turned it from "lacklustre" into a standard: velocity ramps + flow slow motion + the beat camera.
- Set pieces built from the character (emblem, lightning, the Speed Force, frozen time), not generic overlays.
- Text that acts out its lyric and lands on the sung onsets.
- A loop that is its own set piece and lands exactly on frame 0.
- Sharper picture: every source frame restored before rendering.

## 6. Caught by review
- Lightning crossing faces (several transitions): rerouted around a face box.
- The freeze shot framing the wrong person: manual framing.
- A loop seam step (effects firing on frame 0): moved to bar 2.
- A perimeter wipe edge through his face: rebuilt as a spiral closing on his chest.
- The lightning-branch figure glowing into a white mass: a sharp core with a modest glow.
- A rim flash blowing out to white: toned to a coloured flare.

## 7. Rules to adopt
1. *(new)* **Motion pass on every edit:** speed ramps on every hook/montage shot (a burst on each beat, ~0.3–0.6× flow slow motion between, same source range); a camera that moves with the music (≈5–6 % zoom punch and a ±1° rotation kick per beat, zoom blur + slight colour split on the hit frames; type stays clean on top); light that reacts to the footage.
2. *(new)* **Restore 720p sources** before rendering (an AI 2× upscale of only the band each frame uses).
3. *(new)* **Lyrics on their sung onsets:** check every word on the isolated vocal (pitch + onsets), not just Whisper.
4. *(new)* **The loop is a set piece** that lands exactly on frame 0 (seam measured, blurred diff ≤ 1). A plain motion-blurred rewind reads as low quality.
5. *(confirmed)* "Lacklustre" means motion and polish are missing, not that more overlays are needed. Plan the speed curve and the camera with the shot list.
6. *(confirmed)* Props/overlays (glass, etc.) must land: no webs over the frame or the face.

## 8. Techniques to reuse
- **Velocity** (`vel()` in the EDL template): speed = slow + burst·exp(−t/70 ms) on each beat, integrated to source time; flow in-betweens on the restored frames.
- **Beat camera** (`beat_bounce`, `shake`, `beat_fx`).
- **Emblem dive** (`emblem_gate`): track the chest emblem with keyframes, flare it, zoom into the bolt, burst through into the next shot, then a refracting shockwave (`drop_wave`).
- **TIME PARTICLES** (`time_particles`): the frozen frame breaks into fragments of its own pixels (edges first, people last), they hang in the stopped air, then rebuild as the next shot from a focus point, landing on the beat. Sound: grains, shimmer, reversed grains into an impact.
- **Bullet time** (automatic on frozen holds): parallax from the person matte plus a floor gradient, with a slow dolly push.
- **Lens shatter, lightning branches (Lichtenberg), perimeter lap, phase, whirlwind, speed slices, lightning tear:** all in the toolkit catalogue.
- **The Speed Force loop:** the lyric's letters run a ring that opens into a tunnel; panels of the edit's own moments fly past, newest to oldest, and frame 0 lands.

## 9. Measured (final)
−12.7 LUFS, −3.5 dBTP after AAC; loop seam blurred diff 0.93; 17 cuts, 0 clicks; faces centred; one text flag (a face inside a tunnel panel, checked).
