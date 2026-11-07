# Edit report: v11 BOP (The Flash × DaBaby "BOP")

> From the **Flash studio** for the other voidfx studio. Apply sections 7 and 8 to your `CLAUDE.md`, handbook and toolkit, then confirm what changed.

## 1. Verdict
**Approved as a standard** after 4 rounds. The owner: *"I like this edit and would like for you to make it a standard."* It's the standard for **concept, focal set pieces and the loop**, and its engine is now the base new edits are scaffolded from (Studio 1).

## 2. The edit
- **Show × song:** The Flash × DaBaby "BOP" (127 BPM).
- **Section used:** 7.75 → 28.54 s (11 bars, 20.79 s). The intro talk includes *"they're like, **Harrison**…"*; the beat drops in at 9.64; "Let's go!" at 14.34 in the dip; the drop at 15.31 is the start of the verse. It ends between two lines, then tape-stops.
- **Concept: THE RIVAL.** The spoken "Harrison" (Harrison Wells *is* the Reverse-Flash) became the whole edit. The cold open is the rival in red; Barry answers on "Let's go"; on the drop the frame splits red against gold and gold wins; the verse is Barry in gold; at the end the red takes his symbol and the edit loops back to Harrison.
- **Look: VOLTAGE / RIVAL.** For Barry: deep clean blacks, crimson suit, warm gold lightning bloom, teal shadows. For the rival: a second grade with red-shifted highlights, dark red shadows and red halation.
- **Length / format:** 20.79 s, 1080×1920, 60 fps, loops.
- **Sources:** a Flash S4 pack and a Reverse-Flash pack (both labelled 4K, both really 720p; the Reverse-Flash clips are a 600×600 inset with a watermark below, framed inside the inset).
- **Text:** the verse is explicit, and the owner asked for few or no subtitles, so there are two designed titles: LET'S GO and BOP (the O is the Flash emblem).

## 3. Creative process
- **The concept came from the material:** a word in the song's own intro. It drove the grade (two colours), the drop (red vs gold), a late punch (gold beats red) and the loop (red takes the symbol).
- **Structure:**
  1. rival cold open (Wells → mask on the beat → Thawne → Eobard);
  2. the answer (a dive from Eobard's red eye out of Barry's eye);
  3. "Let's go!";
  4. the bolt-split drop;
  5. the gold verse with speed ramps on every shot;
  6. a time freeze;
  7. the charge-up into **THE RIFT** (the focal piece) and the flight through fire;
  8. the clash and the punch;
  9. the final stare;
  10. the REVERSE loop.
- **Sound:** the song window plus a red crackle bed under the cold open, a sound for every transition, a quiet swish on each camera punch, and a tape-stop with a power-down whine into the loop. Built circularly.

## 4. Revision history
| Rev | Owner's note | What changed | Why |
|---|---|---|---|
| 1 | (first delivery) | — | — |
| 2 | *"a lot more animations, graphics, transitions… more sound effects… absolutely amazing"* | 5 new transitions (red eye dive, strobe echo, bolt trace, heat haze, clash) and a new punch shot; embers, gold dust, speed particles, edge lightning, light sweeps; a full sound pass | The owner always wants more designed moments and sounds |
| 3 | *"improve the loop… more creative… a cool graphic or animation… replace the parts where Barry's just moving to the beat"* | The REVERSE loop (red strikes his emblem, it inverts, red radiates, a dive through it lands on frame 0); three beat animations: AURA (silhouette rings), REMNANTS (time copies splitting off), CHARGE (lightning gathering into his chest) | Shots that only "move to the beat" read as filler |
| 4 | *"polish the symbol more and make it more detailed… the transition smoother and flashier… a new creative graphic… one of the focal points"* | A detailed procedural Reverse-Flash emblem revealed by a **coin flip** of the real emblem; a smoother, flashier dive (anticipation, speed-matched blur, rays, fringes, a red flare); **THE RIFT** focal piece | Hero graphics have to look like real objects, and the edit needed one centrepiece |

## 5. What made it good
- **One concept from the material**, carried through grade, structure, sound and the loop.
- **One focal set piece** the owner can point to (THE RIFT).
- **Detailed hero assets revealed physically:** the real chest emblem flips like a coin to show a bevelled, lit Reverse-Flash emblem.
- **Every "just moving" shot got its own beat animation**, each with a sound.
- **The loop lands exactly:** the dive ends on frame 0's own image (seam diff 0.11).
- Very few words, all designed.

## 6. Caught by review
- The bolt-split seam through his nose: moved beside the face.
- Red streak, emblem reveal and loop streak over faces: moved off faces.
- Particles in front of faces: masked off every face.
- Exposure blow-outs (fire, white skies): exposure brought down per shot.
- The drop's impact frame and the dive's rim flash were near-white (mean luma 178): toned to a coloured flare (104).
- The coin-flip reverse face sat off-centre: the emblem is now found by a circle fit to its visible edge in every source frame.
- A background guard's face cut at the frame edge (caught by QC): reframed.
- LET'S GO touching his chin: moved down.

## 7. Rules to adopt
1. *(new)* **Find the concept in the material:** a word in the song, a line, the character's history. Carry it through picture, grade, sound and the loop.
2. *(new)* **One focal set piece** per edit: multi-stage, with its own layered sound, on a structural moment (a bar line after a build).
3. *(new)* **Detailed physical hero assets:** build them lit and bevelled to match the shot, reveal them on the real tracked object, and check them at full resolution.
4. *(new)* **No "just moving to the beat" shots:** give each its own beat animation and sound.
5. *(new)* **Flash discipline:** measure every flash in the encode; a flare must keep the picture (peak mean luma about 110 or less).
6. *(new)* **Explicit lyrics → two designed titles, not captions.**
7. *(confirmed)* The loop lands exactly on frame 0 (seam ≤ 1), built from frame 0's own image.
8. *(confirmed)* Nothing on faces: lightning, seams, particles and streaks are routed around a face/head box.
9. *(new)* **Packs labelled 4K are usually 720p:** check specs, frame inside insets, avoid watermarks.

## 8. Techniques to reuse
- **Rival grade** (`look="rival"` vs `"voltage"`): a second grade for the antagonist; the finish blooms red for the rival's shots.
- **Red phase** (`red_phase`): the Reverse-Flash face-vibration, i.e. jittered red ghost copies resolving into the next shot.
- **Red eye dive** (`red_eye_dive`): find the brightest red point (his eye), dive in until the frame is red light, pull out of the next character's eye (face-track landmarks).
- **BOLT SPLIT drop** (`bolt_split`): a lightning-bolt-shaped seam cracks down beside the face; the left half graded red, the right gold; on the drop the seam sweeps across and tears the title apart; shockwave. Sound: crackle build, impact, thunder, sub drop.
- **THE RIFT** (`rift`): a tear grows along a jagged diagonal below the face, opens with white-gold electric edges and light spill, the Speed Force churns inside, the camera flies through, and the next shot rushes out of the vanishing point. Sound: crack, a rip panned across, reversed swell into a sub drop, roar and whine, arrival impact.
- **Coin-flip emblem** (`rf_emblem`, `coin_flip`): a procedural emblem (bevelled rim, groove, glossy disc with a reflection, an emissive bolt with light spill), lit by the real emblem's brightness; the real emblem flips on its axis with its edge visible and the suit filled in behind; a flare at edge-on, a shockwave and sparks on landing. Sound: spin whir, sizzle, metal ring.
- **REVERSE loop** (`reverse_loop`): strike → flip → red radiates → an anticipation pull-back and accelerating dive into the black disc (speed-matched blur, radial colour fringes, rays, sparks, a red flare as the rim passes) → lands on frame 0.
- **Beat moments** (`aura`, `remnants`, `charge`): silhouette rings pulsing out on each beat; time-remnant copies splitting sideways and snapping back; lightning and dust gathering into the chest.
- **Clash, strobe echo, bolt trace, heat haze, whip, dolly focus pull, emblem draw-on reveal:** in the toolkit catalogue.

## 9. Measured (final)
−13.2 LUFS, −3.4 dBTP after AAC; loop seam blurred diff 0.11; 16 cuts, 0 clicks; faces centred; sharpness check afterwards: the punch (source motion blur) and the grin (speed-ramp blur) measure soft, the stare low because restoration smooths skin.
