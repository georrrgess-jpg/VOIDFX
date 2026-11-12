# HANDOFF: v17 MR. BLUE SKY (The Flash × Electric Light Orchestra "Mr. Blue Sky"): STANDARD

**From:** the Flash studio · **Date:** 2026-11-12 · **Revisions:** 3 owner rounds after the first delivery · **Folder / branch:** `v17/` on `claude/gallant-planck-pqpczp` (v12 engine + `v17/work/sec17.py`)

## 1. Verdict, in the owner's words
> "I like this edit make it a standard"

- **Status:** standard. Flash edits still scaffold from v12 (`--base v12`); v17's pieces port from `v17/work/sec17.py`.
- **The brief:** *"try and follow the beat throughout the song and have a new scene for each … not include the scene with barrys eyes and electricity … many cool animations, graphics and transitions … the best flash edit that you've created … completed in an efficient manner."*
- **It took three rounds.** Most of the notes were about shots and set pieces, not the concept:
  - round 1: the emblem transition, a block slide, two supporting characters, and "more creative";
  - round 2: a shot, a distorted source, a cloud cover, an attention-grabber, and the loop.

## 2. The edit at a glance
| | |
|---|---|
| Song / window | ELO "Mr. Blue Sky", half-beats 177 → 321 (30.51 → 55.21 s), **175 BPM** fitted on the drum stem (kicks on every other half-beat, so the window starts on 177); from "Hey, running down the avenue" to "…hide away for so long"; the next line's "Where" faded off the vocal stem |
| Length / format | 24.69 s, 1080×1920, 60 fps, loops |
| Concept | **AFTER THE STORM.** The Flash was made in a storm; this is the day after. Frame 0 is a storm sky, and the sun breaks through on "Hey!". The hero is **the sun**: the sun break, THE SUN as a halo behind him, the emblem igniting into the sun, and the loop |
| Look | **BLUE SKY**: high-key, skies pushed cerulean, sunny gold highlights, the suit's red rich, skin natural; a warm bloom and a faint sun streak. The storm is cool grey. No text |
| Structure (key moments) | SUN BREAK (frame 0) → SUN BURST into the avenue → **SONIC BOOM** (1.4 s: a vapour cone on his chest, a shock ring that bends the picture, his POV run inside it) → a new scene every two beats → **THE SUN** (4.8–7 s: on the S1 golden-hour shot the sun rises behind his head as a halo, the sky exposed down, its spikes turning on the beat; a lens ghost on his chest opens as **GHOST IRIS**) → rain ripple, cloud shadow, **ZIP** (a whip with his lightning on the seam) → sun open → Flash Day, the ball game, the laugh → **BOLT WINDOW** (a Flash bolt flies at the lens with the charged Flash inside) → the spin onto the S5 suit in the sunlit trees → blue bloom → **EMBLEM IGNITE** (17.8–19.5 s: the real tracked emblem charges, tears free on a tether of current, coin-flips up the open side and ignites into the sun, throwing lightning; the camera rises after it and it hangs as the sun in the leap's sky) → **CUBE TURN** → bokeh rack → glare wash → **PEEL** (a sticker peel, "hide away") → smear → **LIGHTNING STRIKE** → **LIGHTNING ASCENT** (the loop) |
| Transitions | 33 designed + the loop in 24.7 s (1.34/s), 0 % generic. New in v17: sun_burst, sonic_boom, speed_zoom, glint_sweep, sky_whip, flare_cut, ray_rake, ghost_iris, prism, whip_pan, bolt_crack, rain_ripple, tilt_up, cloud_shadow, zip17, sun_open, sun_whip, balloon_rise, light_streak, throw_whip, bolt_window, spin_roll, blue_bloom, punch_cut, emblem_ignite, cube_turn, bokeh_rack, glare_wash, peel17, smear17, lightning_strike, the loop |
| Animations on shots | glints (SHINE), god rays, sunlit dust (MOTES), lightning crawling over the suit (CRACKLE), THE SUN's halo, the loop's charge |
| Sound | 12 effects in 10 moments, none on beats: the sun break's swell, the boom (impact + sub drop), the raindrop, the zip, the spin, the emblem's crackle, rise and drop, the strike's thunder, the ascent's zap and whoosh |

## 3. Creative process
- **The song:** the automatic window was the instrumental outro, so the window was chosen by hand on the lyrics, and the grid was moved so the kicks land on even half-beats.
- **The concept:** from the title and the Flash's origin (the storm that struck him), carried by the sun: SUN BREAK, THE SUN, the emblem as the sun, and the storm returning for the loop.
- **Shots were scored for daylight and blue sky.** Most packs are night.
  - Excluded: pack10, which is Dexter footage, and every lightning-eyes shot (flash_b_hq 116.5–119.5 s and 54.4–56 s, flash_a 87.6–89.9 s).
- **Before the first delivery:**
  - the sun break first washed the storm grey;
  - the focal sun hid behind his cowl;
  - procedural clouds read as stucco, and later as grey plaster, so the storm footage itself was used;
  - the loop seam failed at 1.93 because the beat camera punched frame 0;
  - the fresh-eyes critique caught: look-alike shots, the Blitzkrieg pack's tan suit, five face-over-face dissolves, a clip-art sun, and the hook's 1.4 s shots.
- **Process failures:**
  - the disk filled twice (a stale frame cache);
  - OOM kills when the render server ran during `sr_prep`;
  - a shot's range changed after prep left it with no matte, and the sun jumped in front of his head (caught by motionqc);
  - `cx` read as (x, y) when it is a start-to-end pan;
  - packs share clips, so the same shot came from two files twice.

## 4. Revision history
- **First delivery (rev 4 internally):** QC 11/11, seam 0.10.
- **Round 1, the owner:** *"I largely dislike the transition done with the emblem at 19 seconds. It kind of feels incomplete and as if the emblem isn't really doing anything. I would rather you make it a transition from the emblem into the sun or just a general emblem and lightning transition. Additionally, I don't really like the transition done towards the end that is block transition with the three block lines. I also don't like the scenes with Wally and XS. I'd rather those just be flash scenes. And I would like more creative transitions and unique graphics."*
  - EMBLEM SUN v1 lit the emblem in place and tilted away. It became **EMBLEM IGNITE**: the emblem tears free, flips and ignites, clear of his face, and holds in the next sky.
  - The slice wipe became **LIGHTNING STRIKE**.
  - Wally and XS became the charged Flash and the S5 forest shot, with **BOLT WINDOW**.
  - CRACKLE, MOTES, **PEEL** and **CUBE TURN** were added, and the whips were feathered.
  - Caught by the critique:
    - two reused clips (packs share footage);
    - the emblem's sun read as a flat grey disc with stacked seams;
    - the charged shot's `cx` panned away from him.
- **Round 2, the owner:** *"I dislike the beginning scene where barry seperates into a speed mirage and himself … change the scene at 6 seconds or fix the part where barrys mouth and facial features as well as part of the suit are distorted … have a really cool and unique transition or focal point to try and get the viewers attention … fix the half second of the clouds and lightning in the sky that appear at 11 and a half seconds … change the loop to something that's more creative and cool and visually appealing ensure this loop is perfect and seamless."*
  - The race shot became **SONIC BOOM** into a POV run.
  - The Blitzkrieg close-up (AI-processed at the source, plus a blotchy suit recolour) was replaced: THE SUN moved to the S1 golden-hour shot.
  - The storm-footage cloud cover became **ZIP**.
  - The clouds-over loop became **LIGHTNING ASCENT**: the storm returns, his suit charges, a bolt launches beside him, and the camera rises with it into frame 0's storm (seam 0.09).
- **Verdict:** *"I like this edit make it a standard."*

## 5. What made it good / what made it weak
- **Good:**
  - one hero (the sun) used as a motif, with a causal loop: he answers the storm and the storm is the opening;
  - an attention-grabber 1.4 s in (SONIC BOOM);
  - the emblem as an object that acts (EMBLEM IGNITE);
  - 33 custom transitions with no generic ones;
  - living animations in the holds;
  - lean sound;
  - QC 11/11 with a 0.09 seam every round.
- **Weak:**
  - **three owner rounds**, not two. Round 1's emblem was a glow, not an action. Round 2's notes were source problems (a doubling shot, an AI-distorted pack) that a closer look at the sources would have caught.
  - Several 720p shots are soft (13 flagged by `sharpness.py`).
  - Lightning carries many transitions; the owner didn't object, but it is the Flash's easiest motif.

## 6. Measured results
| Check | Result |
|---|---|
| QC | 11/11 on the encode |
| Loudness after AAC | −13.0 LUFS / −4.5 dBTP |
| Loop seam (blurred diff; target ≤ 1) | 0.09; audio seam step 0.074; picture wrap step 0.62 vs median 0.69 |
| Flashes | no white-outs; one flash event (the strike) within the limit |
| Motion audit | no dead spans, no judder; 16 pops, all cuts, beats or designed flashes |
| Faces vs effects | 5 runs, none on a face itself (the sun's glow behind his head, the arm shot's restored cowl, the ascent's glow beside his helmet) |
| Transitions | 33 + the loop in 24.7 s (1.34/s), 0 % generic; 31 shots, no clip twice |
| Sound | 12 effects in 10 moments |
| Effort | 4 owner rounds incl. the verdict; 9 full renders (`metrics.py 17 summary`) |

## 7. New rules (adopt in both studios)
1. **An emblem (or any symbol) transition must show the object acting:** it lifts off, turns, transforms. Lighting it in place is not enough. Evidence: *"it kind of feels incomplete and as if the emblem isn't really doing anything"*, then EMBLEM IGNITE was approved. This refines v13 rule 2 and v14 rule 5. Applies to: all (the Dexter form: the slide, the badge, the knife acts).
2. **No block or slice wipes** (panels sliding apart). `split_slide` is rejected. Evidence: *"the block transition with the three block lines"*. Applies to: all.
3. **Stay on the main character unless the owner asks otherwise.** Evidence: *"I also don't like the scenes with Wally and XS. I'd rather those just be flash scenes"*. This confirms v109 rule 6. Applies to: all.
4. **Look at every source at full size for AI processing or distortion before using it.** `flash_blitzkrieg` close-ups have waxy, warped faces, and recolouring a suit leaves blotches on a cowl. Evidence: *"barrys mouth and facial features as well as part of the suit are distorted"*. Never ship a shot where a speed effect doubles him (*"barry seperates into a speed mirage and himself"*). Applies to: all.
5. **No full-frame sky or storm footage as a cover.** `cloud_break` is rejected. Evidence: *"the half second of the clouds and lightning in the sky … I don't like this scene"*. Applies to: all.
6. **An attention-grabber in the first ~1.5 s:** a signature transition with its own physics and sound (SONIC BOOM). Evidence: *"a really cool and unique transition or focal point to try and get the viewers attention"*, then the verdict. Applies to: all.
7. **The loop is a causal event that keeps moving into frame 0** (LIGHTNING ASCENT: he answers the storm, and the camera rises with his bolt into frame 0's storm). This confirms v111 rule 2. Applies to: all.
8. **Technical:**
   - `cx=(x0, x1)` is a start-to-end pan, not a point;
   - packs share clips, so check a sheet of every shot's mid-frame for reuse;
   - re-run prep after changing a shot's source range (with no matte, the sun drew in front of him);
   - feather a whip's two shots mid-move, closing to nothing at its ends;
   - `face_soft` pad 1.3 is about twice the face: use pad ~0.6–1.0 for drawn light beside a face, and give shots with `face=None` a `face_hint`;
   - no renders while `sr_prep` runs.

   Applies to: all.

## 8. Reusable assets
| Technique / transition | Where the code is | How to restyle it |
|---|---|---|
| SONIC BOOM (`sonic_boom`: a vapour cone, a refraction shock ring via `cv2.remap`, a shake, the next shot inside) | `v17/work/sec17.py` | Any impact or speed break: a gunshot's shock wave, an explosion, a car at speed |
| EMBLEM IGNITE (`emblem_ignite`, `emb_hole`, `emb_patch`, `coin_back`, `put_sprite`: a tracked real emblem cut out, the hole inpainted, a coin flip with a plain back, igniting into a sun) | `sec17.py` | Any prop that can lift off and transform: a badge, a slide, a coin, a ring |
| THE SUN (`sun_draw` photographic sun, `sun_fx`: behind the matte, the sky exposed down, spikes turning on the beat; `ghost_iris`) | `sec17.py` | Any light source as a focal point: a moon, a lamp, a headlight |
| LIGHTNING ASCENT loop (`loop_fx`: a charge on his body, a bolt from beside him, a feathered rise into frame 0's own picture) | `sec17.py` | Any loop where the end sends something into frame 0: a bullet, a flare, a firework |
| PEEL (`peel17`: a sticker peel with a reflected, curled paper flap and a soft shadow), CUBE TURN (`cube_turn`: a perspective cube) | `sec17.py` | Generic and kinetic |
| BOLT WINDOW, LIGHTNING STRIKE, ZIP, CRACKLE, MOTES, `strip_pan` (feathered) | `sec17.py` | Lightning → any energy (blue for a portal, red for blood); motes → dust in any beam |
| BLUE SKY grade (`grade`, `finish17`) | `sec17.py` | A sunny high-key look |

## 9. For the other studio
- **Rules 1–8 apply to Dexter edits.** Rule 1's Dexter form: the prop itself acts (the slide pivots up, the badge flips). Rule 4: check packs at full size for AI processing; never recolour clothing on a face.
- **Loops:** v111 rule 2 and v17 rule 7 are the same ask. Both approved loops are causal: the end fires or sends what starts the edit.
- **The scaffold is unchanged:** Flash v12 (`v17` = v12 + `sec17.py`); Dexter v111.
- **Operational:** no renders while `sr_prep` runs; clear a frame cache before a full re-render when the disk is under ~3 GB free.
