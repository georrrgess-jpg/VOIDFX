# HANDOFF: v11 BOP (The Flash × DaBaby "BOP"): STANDARD

**From:** the Flash studio (Studio 1) · **Date:** 2026-11-07 (verdict given 2026-11-05) · **Revisions:** 4 · **Folder / branch:** `v11/` on `claude/gallant-planck-pqpczp`

## 1. Verdict, in the owner's words
> "I like this edit and would like for you to make it a standard."

- **Status:** standard. The Flash scaffold (`tools/new_edit.py`) starts from v11. The reference for **concept, focal set pieces and the loop**.
- **Gripes:** none at the verdict. Afterwards, the sharpness check (from DRACULA's gripe) flagged the punch and the grin as soft.

## 2. The edit at a glance
| | |
|---|---|
| Song / window | DaBaby "BOP", 0:07.75–0:28.54 (h32–h120, 11 bars), 127 BPM. The intro talk ("…they're like, **Harrison**…" at 9.60), the beat dropping in at 9.64 (+24.8 dB), the dip with "Let's go!" at 14.34, the drop into the verse at 15.31, a clean end between two lines. |
| Length / format | 20.79 s, 1080×1920, 60 fps |
| Concept | **THE RIVAL.** Harrison Wells *is* the Reverse-Flash, so the cold open belongs to the rival in red; Barry answers on "Let's go"; the drop splits the frame red against gold and gold wins; the verse is Barry in gold; at the end the red takes his symbol and the edit loops back to Harrison. Found in **the song's own words** (one spoken name in the intro). |
| Look | Two grades. **VOLTAGE** (Barry): deep clean blacks, crimson suit, warm gold lightning bloom, teal shadows. **RIVAL**: red-shifted highlights, dark red shadows, red halation. |
| Structure | 0–5.7 s rival cold open (Wells → mask on the beat → Thawne → Eobard) → 5.7 the answer (the red eye dive) → 6.6 "Let's go!" → 7.56 BOLT SPLIT drop → verse in gold, speed-ramped → 11.8 time freeze → 13.2 smirk → 14.2 charge-up → 15.1 THE RIFT into the flight through fire → 17.5 CLASH into the punch → 18.4 the final stare → 19.4 REVERSE → loop. |
| Set pieces | **BOLT SPLIT** (a bolt-shaped seam cracks down beside his face, red vs gold halves, the seam sweeps across on the drop tearing LET'S GO apart; shockwave). **THE RIFT** (focal: a tear opens across the frame below his face with electric edges and light spill, the Speed Force churns inside, the camera flies through, the next shot rushes out of the vanishing point). **REVERSE** (loop: a red bolt strikes his chest emblem; the real emblem coin-flips into a detailed Reverse-Flash emblem; red radiates over him; an anticipation pull-back and a dive through the black disc onto frame 0). |
| Transitions | 16 cuts, each a designed transition with its own sound: red phase, red link, red streak, red eye dive, dolly focus pull, bolt split, strobe echo, whip, bolt trace, freeze-in, restart, ignite, rift, heat haze, clash, emblem reveal; plus the REVERSE loop. All new in v11 except freeze-in, restart and ignite. |
| Text | Two designed titles only (the verse is explicit and the owner asked for few or no subtitles): **LET'S GO** (GO lands white-hot, struck by a bolt; torn by the drop's seam) and **BOP** (letters punch in on the word; the O is the Flash emblem). |
| Sound | The song window, tape-stopping into the loop; a red crackle bed under the cold open; a sound per transition (the drop: crackle build, whine, impact, thunder, sub drop; the rift: crack, panned rip, reversed swell, sub drop, roar; the flip: spin whir, sizzle, metal ring); a quiet swish on camera punches; a power-down whine under the tape stop. −13.2 LUFS / −3.4 dBTP after AAC. |

## 3. Creative process
1. Two new packs arrived labelled "4K 60fps"; both were really 720p (the S4 pack 24p content; the Reverse-Flash pack true 60 fps, every clip a 600×600 inset with a watermark, framed inside the inset). The S4 pack's first 13 shots (a CGI fan render) were left out.
2. `song_map` found the beat-in and the drop; the vocal stem showed the intro talk. The word "Harrison" gave the concept, so the structure follows the rivalry, not just the energy.
3. Alternatives rejected: a montage-only edit (no story); an emblem-dive copy of v10 (repeats a standard's look).
4. Each "Barry moving to the beat" shot was given its own beat animation instead of more overlays (rev 3).
5. Hero graphics were built as detailed procedural objects and revealed on the real object in the footage (rev 4).

## 4. Revision history
- **Rev 2, the owner's note:** *"I would like for you to add a lot more animations, graphics, transitions etc. I also want more sound effects, i want this edit to be absolutely amazing with wonderful animations transitions etc."*
  - **Change:** five new transitions (red eye dive, strobe echo, bolt trace, heat haze, clash) and a new punch shot (gold beats red); embers, gold dust, speed particles in depth (masked off faces), edge lightning on bar lines, light sweeps; a full sound pass.
  - **Tried and failed:** the punch first framed on an empty wall; speed particles first crossed faces.
- **Rev 3, the owner's note:** *"I would like for you to improve the loop, just make it overall better, make a more creative loop at the end… a cool graphic or a really cool animation paired with it. I would also like for you to take some of the parts where Barry's just moving to the beat and replace it or implement a new animation or graphic."*
  - **Change:** the REVERSE loop (seam from 3.49 to 0.10, because the dive lands on frame 0's own image); AURA on the grin (silhouette rings pulse out each beat), REMNANTS on the smirk (time copies split off and snap back), CHARGE on the bar shot (lightning gathers into his chest). Each has its own sound.
  - **Tried and failed:** the emblem detector first missed (the bolt split the disc; bridged with a morphological close); the AURA ring needed the matte, so it only works on `seg=True` shots.
- **Rev 4, the owner's note:** *"I like the transition/loop at the end now but I would like for you to polish the symbol more and make it more detailed. I would also like for you to make the transition smoother and flashier. I would also like for you to implement a new creative graphic, animations or transition somewhere throughout the edit. I would like this effect to be one of the focal points of the edit and be well thought and created."*
  - **Change:** a procedural Reverse-Flash emblem (bevelled crimson rim with a groove and neon line, glossy black disc with a reflection, a bevelled glowing bolt with light spill, lit by the real emblem's brightness) revealed by a **coin flip** of the real emblem; a smoother, flashier dive (anticipation, speed-matched blur, radial fringes, rays, sparks, a red flare); **THE RIFT**.
  - **Tried and failed:** the flip's reverse face sat off-centre (the emblem is now found by a circle fit to its visible edge in each source frame); the rim flash first went near-white (mean luma 178; toned to a red flare, 104).

## 5. What made it good / what made it weak
- **Good (the owner):** approved as a standard after the symbol and the focal piece; liked the loop from rev 3.
- **Good (the studio's analysis):**
  - one concept from the song's words, carried through grade, structure, sound and loop;
  - one focal set piece;
  - detailed hero assets revealed physically on the real object;
  - every "just moving" shot animated on the beat;
  - an exact loop;
  - very few, designed words.
- **Weak:**
  - **sharpness:** the S4 pack is soft and compressed; the punch (source motion blur) and the grin (speed-ramp blur) measure soft on the render, and the stare is smoothed by restoration;
  - three Reverse-Flash shots are zoomed 32–40 % to stay inside the inset (they still measure sharpest; that pack was pre-sharpened);
  - light rays are drawn over him rather than only behind (Studio 2's rule 1).

## 6. Measured results
| Check | Result |
|---|---|
| QC checkpoint | all PASS |
| Loudness after AAC | −13.2 LUFS / −3.4 dBTP |
| Loop seam (blurred diff; target ≤ 1) | 0.11 |
| Flashes | rim flare peak mean luma 104 (was 178); no white-out runs |
| Softest shots (render) | punch 0.65×, stare 0.71×, grin 0.73× the edit median (this studio's tool; relative scale) |
| Transitions / longest span without a beat | 16 + the loop / about 1 s (every beat punches or animates) |

## 7. New rules (adopt in both studios)
1. **Find the concept in the material:** a word in the song (even spoken), a line, the character's history; carry it through picture, grade, structure, sound and the loop. Evidence: the "Harrison" concept, then "make it a standard" (v11). Applies to: all edits.
2. **Give every edit one focal set piece** the owner can point to: multi-stage, its own layered sound, on a structural moment (a bar line after a build). Evidence: "I would like this effect to be one of the focal points of the edit" (v11 rev 4). Applies to: all edits.
3. **Build hero graphics as detailed, lit objects and reveal them physically on the real tracked object;** check them at full resolution. Evidence: "polish the symbol more and make it more detailed" (v11 rev 4). Applies to: all edits.
4. **No "just moving to the beat" shots:** give each its own beat animation with its own sound. Evidence: "take some of the parts where Barry's just moving to the beat and replace it or implement a new animation or graphic" (v11 rev 3). Applies to: all edits.
5. **Flash discipline:** measure every flash in the encode; a flare keeps the picture (peak mean luma about 110 or less, no white-out runs). Evidence: v11 rev 4 review (178 → 104). Applies to: all edits.
6. **Explicit lyrics → two designed titles, not captions.** Evidence: "I would like for this edit to not have subtitles or only as few" (v11 brief). Applies to: all edits.
7. **Treat packs labelled 4K as unknown until probed;** frame inside insets and keep watermarks out. Evidence: both v11 packs. Applies to: all edits.

## 8. Reusable assets
| Technique / transition | Where the code is | How to restyle it for another show |
|---|---|---|
| Second grade for an antagonist (`look="rival"` vs `"voltage"`, `finish11`) | `v11/work/render11.py` | Dexter vs Trinity / Doakes: a cold grade for the rival. |
| Red phase (`red_phase`, `red_vibe`) | `render11.py` | Any "shudder" motif (the Dark Passenger surfacing). |
| Red eye dive (`red_eye_dive`) | `render11.py` (rev 2) | Into any glowing point (a lamp, a blood drop) and out of the next subject's eye. |
| BOLT SPLIT (`bolt_split`) | `render11.py` | Any two-sided concept split along a themed seam (a knife edge, a crack). |
| THE RIFT (`rift`, `rift_geom`, `sf_interior`) | `render11.py` (rev 4) | A tear into any world: a wound into a kill room, plastic tearing open. |
| Procedural emblem + coin flip (`rf_emblem`, `coin_flip`, `emblem_src`) | `render11.py` (rev 4) | Any badge or prop flipped to its "other side" (a Miami Metro badge flipping to a blood slide). |
| REVERSE loop (`reverse_loop`) | `render11.py` (rev 3/4) | Strike → transform → radiate → dive into a disc onto frame 0; any round object. |
| Beat moments (`aura_pulse`, `time_remnants`, `charge_up`) | `render11.py` (rev 3) | Recolour: red aura, ghost remnants, blood gathering. |
| Clash, strobe echo, bolt trace, heat haze, whip, dolly focus pull | `render11.py` (rev 1/2) | Swap lightning for blood or light. |
| Depth particles masked off faces (`motes11`) | `render11.py` (rev 2) | Ash, dust, embers for any show. |

## 9. For the other studio
- DRACULA's ASHES TO SUN would reach the ≤ 1 seam if the last frame is frame 0's image exactly (the REVERSE dive does this: the inside of the disc *is* frame 0, scaled to 1.0 on the last frame).
- The coin flip is a ready way to "reveal the other side" of a real prop in the footage.
- Engine base: agreed with your proposal: **Dexter edits from v105, Flash edits from v11**, shared effects ported through handoffs.
