# HANDOFF: v12 BLOOM (The Flash × fakemink "Night Blooming Jasmine"): STANDARD

**From:** the Flash studio (Studio 1) · **Date:** 2026-11-08 · **Revisions:** 3 · **Folder / branch:** `v12/` on `claude/gallant-planck-pqpczp`

## 1. Verdict, in the owner's words
> "I like this edit make it a standard"

- **Status:** standard. The Flash scaffold (`tools/new_edit.py`) now starts from v12.
- **Gripes:** none at the verdict. On the way: remove both titles, cut about half the sound effects, remove a chime and an early whoosh, add one more great transition and an emblem transition.

## 2. The edit at a glance
| | |
|---|---|
| Song / window | fakemink "Night Blooming Jasmine", song 18.71–42.05 s (bars 8–18, h64–h144), 102.79 BPM. The owner asked for a start around 18–23 s. Bars 8–11 are the instrumental groove; bar 12 (28.05 s) the vocal enters and the hats fall away (the drop, 40 % in); bar 16 (37.39 s) the claps enter. The last ~2 s: the vocal stem fades on a half-beat echo so the instrumental wraps into bar 8 on the bar grid. |
| Length / format | 23.35 s, 1080×1920, 60 fps |
| Concept | **LIGHTNING BLOOM.** "Night blooming" = the night Barry was struck by lightning. Lightning leaves Lichtenberg figures ("lightning flowers"), so the hero asset is a procedural five-petal **lightning jasmine** that runs bud → bloom → full bloom → closing. Found in the **song's title** meeting **the character's origin**. |
| Look | **NOCTURNE**: indigo nights (daylight shots pushed to night), the suit kept crimson, orange/red light turned to cream, lightning in jasmine white over a cream glow, a deep vignette, fine grain. Every library transition was restyled by repointing the palette constants (gold, red, ember) to v12's colours. |
| Structure | 0–9.3 s the night (storm sky → strike → wake → sparks → cortex → the eye) · 9.34 THE BLOOM · the speed montage · 18.68 FULL BLOOM · 20.4 petal pass · 21.6 pollen burst · 22.4 the bud closes and the camera dives into it → frame 0 |
| Set pieces | **THE BLOOM** (a bud forms in his pupil, bursts into a frame-filling jasmine with the next shot inside the petals, afterimage petals and a ring). **FULL BLOOM**, the focal piece (a bolt strikes from the sky into the heart of a jasmine that unfolds *behind* him with a light wrap; its petals glow as surfaces and breathe on the claps; then they let go and sweep past the camera). **The loop** (a bud closes on his emblem; anticipation pull-back, then an accelerating dive into it; its opening holds frame 0, which reaches scale 1.0 on the last frame). |
| Transitions | 16 cuts + the loop. **New in v12:** strike link, ECG bolt, bud iris, THE BLOOM, full-bloom-in, petal pass, pollen burst, petal whip, **FRACTAL BURN** and **EMBLEM BLOOM** (rev 3). Restyled library moves: bolt trace, dolly, strobe echo, slices, haze, whip. |
| Text | **None.** Both designed titles (NIGHT, BLOOM) were built and then removed at the owner's request. Mumbled rap that Whisper can't time reliably, so no captions either. |
| Sound | The song window plus 37 placed effects (down from 87 in rev 2): layered hits only at the strike, THE BLOOM, FULL BLOOM, the emblem and the loop; one sound per other transition; no sounds on beat moments; no chimes or bells. −13.0 LUFS / −3.5 dBTP after AAC. |

## 3. Creative process
1. **Packs:**
   - analysed five new high-bitrate packs from the owner's Drive list (all 720p despite the labels);
   - used a compact grid per pack (one frame per shot with YuNet face width) instead of full contact sheets;
   - chose night shots across S1–S5 suits.
2. **Concept:** v9 used this song for Dexter with soft jasmine petals, which the owner called lacklustre. For Flash the flower had to be *lightning*: Lichtenberg figures made it physical and tied it to his origin.
3. **Hero asset:** one asset carries the edit, in the iris, behind him, on the emblem, in the loop.
4. **Rejected:**
   - captions on unverified lyrics;
   - reusing the v10 Lichtenberg reveal as-is (it became FRACTAL BURN in rev 3);
   - reusing v11's coin flip for the emblem (EMBLEM BLOOM cracks the emblem into petals instead).

## 4. Revision history
- **Rev 1 (first delivery):** as above, with the NIGHT and BLOOM titles and 87 effects.
  - **Tried and failed on the way:**
    - The jasmine petal tips went NaN: `sin(π)` is slightly negative in float32, and `** 0.7` turns that into NaN, so `fillPoly` crawled. Clamped.
    - FULL BLOOM at radius 980 with every vein read as a web of lightning, not a flower. Moved to radius 660, main veins only, with glowing petal surfaces.
    - The bud missed the pupil twice: I had estimated the eye position from thumbnails. Measured from the render instead.
    - The strike shot's red light was protected as suit-red. Added a per-shot `tame`.
    - The aura ring drew on his face where the matte failed on the dark mask. Added a face guard on beat moments.
    - Two flares reached mean luma 133 / 119. Added a flash governor (cap 0.40 before the finish).
- **Rev 2, the owner's note:** *"can you remove the night text at the beginning and get rid of like half the sound effects. Do this efficiently."*
  - **Change:** NIGHT removed; effects 87 → 37. Removed: every beat-moment sound, the letter chimes, the secondary layers (whines, glass, shimmers, extra crackles and zaps), the cloud flickers and the pre-cut beeps.
  - **Render:** a verified partial re-render (96 frames) in 164 s.
- **Rev 3, the owner's note:** *"get rid of the bloom text, remove the bell sound on the flower and the whoosh on one of the first transitions. I would also like for you to implement one more really cool transition and try to do an emblem transition aswell."*
  - **Change:**
    - BLOOM removed;
    - the bud-iris chime swapped for a short crackle;
    - the whoosh into the sparks shot removed;
    - **FRACTAL BURN** (replaces the restyled Lichtenberg crawl);
    - **EMBLEM BLOOM** (replaces the clash).
  - **Tried and failed:**
    - The emblem shot first chosen ("charge") pushes past the emblem by its end. Moved the transition to hood → charge, where the S4 emblem stays large.
    - The first burn opened too fast and its branch lines lingered over the next shot. The burn-through was slowed and the lines fade faster.
    - The partial render ran out of memory next to the render server's warm workers; `vrender.py` now stops the server first.

## 5. What made it good / what made it weak
- **Good (the owner):** approved after rev 3; he asked for more designed transitions and an emblem moment, and for less text and less sound.
- **Good (the studio's analysis):**
  - one physical hero asset carried through every stage and the loop;
  - the origin story told in the instrumental intro without words;
  - the drop out of his pupil;
  - a focal set piece lit behind him;
  - an emblem transition on the *real, tracked* emblem;
  - a transition built on a real phenomenon (Lichtenberg burning);
  - fewer, bigger sounds;
  - fast revisions (rev 2 and rev 3 were partial re-renders of 96 and 343 frames).
- **Weak:**
  - every source is 720p (softest on the render: dash 0.80×, charge 0.82×, strike 0.86× the edit's median);
  - two transitions now sit more than 12 dB under the music after the sound cuts (bud iris, dolly);
  - one QC face-centring flag is a verified detector false positive (s3night 1022–1026: YuNet finds only the left half of a 710 px masked face).

## 6. Measured results
| Check | Result |
|---|---|
| QC checkpoint | all pass except the face-centring false positive above (verified on stills and on the neighbouring frames) |
| Loudness after AAC | −13.0 LUFS / −3.5 dBTP |
| Loop seam (blurred diff; target ≤ 1) | 0.19 |
| Flashes | none (no white-out runs, nothing over mean luma 110) |
| Effects vs music (`mixcheck`) | 18 of 20 within 12 dB (the two exceptions follow from the owner's removals) |
| Faces vs effects (`faceqc`) | 2 runs, both checked: FULL BLOOM's light is behind him (the face box is wider than his head); a 6 % bloom on the eye highlights in the last shot |
| Softest shots (render) | dash 0.80×, charge 0.82×, strike 0.86× the edit median; none flagged |
| Render | full render 289 s; revisions by verified partial re-render |

## 7. New rules (adopt in both studios)
1. **Text is optional: start without titles when the lyrics aren't captioned.** A title has to earn its place. Evidence: *"remove the night text"* (rev 2), *"get rid of the bloom text"* (rev 3), then *"I like this edit make it a standard"*. Applies to: all edits (v11's two titles were liked; v12 shows none is fine too).
2. **Fewer, bigger sounds.**
   - One sound per transition.
   - Layered hits only at the set pieces.
   - About 35–40 effects in a 23 s edit.
   - No sounds on beat moments.
   - No chimes or bells on graphics.

   Evidence: *"get rid of like half the sound effects"* (rev 2), *"remove the bell sound on the flower and the whoosh on one of the first transitions"* (rev 3). Applies to: all edits. Updates v11's "beat moments, each with its own sound": keep the animation, drop the sound.
3. **Every Flash edit has an emblem transition built on the real, tracked emblem** (a Hough circle on the source frame mapped through the shot's camera). Evidence: *"try to do an emblem transition aswell"* (rev 3), and the emblem dive (v10) and coin flip (v11) were liked. Applies to: Flash; for Dexter the equivalent is a signature prop (the badge, a blood slide).
4. **Build at least one transition on a real physical phenomenon tied to the concept** (FRACTAL BURN: lightning burning a Lichtenberg figure into wood). Evidence: *"implement one more really cool transition"* (rev 3), then approval. Applies to: all edits.
5. **One hero asset carries the whole edit:** bud → bloom → full bloom → closing → the loop; reuse it in the drop, the focal piece, the emblem and the loop. Evidence: the verdict. Applies to: all edits.

## 8. Reusable assets
| Technique / transition | Where the code is | How to restyle it for another show |
|---|---|---|
| Lightning jasmine: procedural petals with 2.5D opening, Lichtenberg veins, lightning edges, heart/stamens (`jas_geom`, `jas_draw`, `jas_light`, `jas_veins`) | `v12/work/render12.py` (v12 section) | A blood-drop splash, a plastic sheet opening, any five-fold "flower" of light |
| Light behind the subject with a light wrap (`behind`) | `render12.py` | Any glow, sun or flower behind a matted subject (rule 1 from v105) |
| THE BLOOM: bud in the pupil → frame-filling bloom with the next shot inside the petals | `bloom`, `eye_pos` | Dexter: a drop of blood blooming out of an eye or a slide |
| FULL BLOOM: a flower unfolding behind him, petals as glowing surfaces, breathing on claps | `full_bloom_fx` | A blood moon / sun corona behind Dexter |
| EMBLEM BLOOM: tracked emblem cracks into five petals that peel open | `emblem_bloom`, `emblem_at`, `crack_canvas` | Miami Metro badge, a blood slide, a kill-room lamp |
| FRACTAL BURN: Lichtenberg burn with embers and char, burning through to the next shot | `fractal_burn` (uses v10 `lich_tree`) | Dexter: a burn through plastic, a scorch across a photo |
| STRIKE LINK, ECG BOLT, BUD IRIS, PETAL PASS, POLLEN BURST | `render12.py` | ECG: a hospital or crime-scene monitor; pollen: ash or blood mist |
| Closing-bud dive onto frame 0 (`loop_dive`, `frame0_prefinish`) | `render12.py` | Any closing aperture whose inside is frame 0 |
| Face guard for beat moments (`face_guard`), flash governor (`flash_governor`), per-shot `tame` for coloured light | `render12.py` | Generic |
| NOCTURNE grade (indigo shadows, cream conversion of orange light, crimson protect) | `grade` in the v12 section | A night grade for Dexter's hunts |

## 9. For the other studio
- **Engine base:** Flash edits now scaffold from **v12** (was v11). Dexter edits still from v105. The v12 section sits above `# >>> pipeline v2: speed`.
- **Sound:** rule 2 changes how many effects go in. Worth applying to v106 from the start (your v105 `mixcheck` also showed many small transition sounds; fewer, bigger sounds is the owner's direction now).
- **Text:** rule 1. A Dexter edit with captionable lyrics still captions them (the v9 style). The rule is about titles on uncaptioned songs.
- **Pipeline v2:** this edit was the first full production on it.
  - Full render 289 s; revisions 164–211 s via verified partial re-renders.
  - One refused partial correctly fell back to a full render.
  - The render server should be stopped before a render (now automatic).
