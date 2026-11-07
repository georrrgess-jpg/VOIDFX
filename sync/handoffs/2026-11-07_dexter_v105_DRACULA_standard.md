# HANDOFF: v105 DRACULA (Dexter × Tame Impala "Dracula"): STANDARD

**From:** the Dexter studio (Studio 2) · **Date:** 2026-11-07 (verdict given 2026-11-05) · **Revisions:** 3 · **Folder / branch:** `v105/` on `claude/beautiful-volta-wjki7k` (voidfx; the transfer bundle is in Drift-Master `voidfx-v101/`)

## 1. Verdict, in the owner's words
> "I like this edit and would like for you to make it a standard. The only gripe I have is the quality of some of the clips. You do not have to edit this further."

- **Status:** standard. It's the Dexter studio's newest standard, and its scaffold (`tools/new_edit.py`) starts from v105.
- **Gripe:** *"the quality of some of the clips"*, i.e. soft source footage. Now a rule (§7).

## 2. The edit at a glance
| | |
|---|---|
| Song / window | Tame Impala "Dracula", 2:34.6–2:57.5 (half-beats h592–h680, 11 bars), 114.99 BPM. The final chorus run: "Saw this moment coming from afar", then the song's one-bar drop-out at 2:40.8, then the drop at 2:42.9 (+29.8 dB, the biggest change in the song). One pass, no splice; the pre-roll is the song's own lead-in, so the loop plays straight through. |
| Length / format | 22.97 s, 1080×1920, 60 fps (every source plays at its own 24p/30p cadence; no interpolation) |
| Concept | **SUNDOWN.** By day he wears the mask (sunny Miami, the boat, the smile, the ice cream). The lyric is "run from the sun like Dracula", so the sun sets across the drop-out bar and night slams in on the drop. Night is the hunt. At the end the sun takes him, and his ashes become the sun the loop opens in. Found in the **song's own words**, mapped onto **Dexter's double life** (the day mask against the night hunter). |
| Look | Two grades split on the drop. **Day:** a bleached warm "Sunshine State postcard" with teal shadows; the sun (rays and lens ghosts) sits *behind* him via his matte, with a light wrap and sunlit dust. **Night:** cold moonlit silver and deep blacks, with only crimson kept and pushed, plus a crimson bloom. A dusk blend runs through the drop-out bar. |
| Structure | k0–24 the day montage (a cut every 3 half-beats, sun in every shot, the first lyric captioned) → k24–32 SUNDOWN (the sun sets down the frame edge, an eclipse, bats gather behind him) → k32 THE BAT BURST on the drop + "DRACULA" → k48 THE BLOOD MOON (the 2nd "Dracula") → k64 THE COFFIN (the 3rd) → k66–83 the night montage → k83–88 ASHES TO SUN (the loop). |
| Set pieces | **SUNDOWN** (the sun sets → eclipse with corona and diamond ring → gathering bats). **THE BAT BURST** (a 3D bat cloud from the sky, a crimson flash, bats flying past the lens with depth blur; the per-letter DRACULA title breaks into crimson bats). **THE BLOOD MOON** (a moon iris opens; a procedural blood moon rises behind his MODNet cut-out with clouds and bats; a red rim on him; a church-bell toll on B-flat). **THE COFFIN** (a height-map-lit mahogany lid with a brass cross falls and slams; the frame jolts; dust). **ASHES TO SUN** (see §3). |
| Transitions | **27 in 22.97 s**, each with its own sound: sun flare, whip, film burn, slam, **card flip**, quarter-turn, **palm sweep**, light sweep, **eclipse**, **bat burst**, strobe, impact, torch blind-out, **cape**, **moon iris**, lamp on, logo, roll into the upside-down shot, **coffin**, **mist**, **bat swarm**, eye dive, face-match, shutter, zipper, **great bat**, sun flare. Bold = new in v105. |
| Text | Only the words verified on the Demucs vocal stem (Whisper in tight windows, no prompt, so it couldn't echo the expected lyric): SAW THIS MOMENT / COMING FROM **AFAR**; RUN FROM THE **SUN** / LIKE; the per-letter hero **DRACULA**; **DRACULA** twice more. Not captioned (unclear on the vocal): "Now here we are", "this love is spectacular". |
| Sound | Every transition has a layered sound. Tonal sounds are in the song's key (B-flat minor: a bell toll, a dawn chord). The bed is sea air by day and wind plus a sub drone by night. The song is mastered loud (−9 to −11 dBFS RMS), so the effects were pushed +9 dB and the music ducks −3 dB under the three big hits. −13.1 LUFS / −4.1 dBTP after AAC. |

## 3. Creative process
1. **The window.** `song_map` showed the drop at 162.90 s as the biggest change in the song, preceded by a one-bar drop-out. That made the drop-out the natural "sundown" beat and the drop the hero moment. The window was set to start on "Saw this moment" so the lead-in is a lyric.
2. **The lyrics** were verified on the isolated vocal before writing any text. Only clearly sung words were captioned, and the published lyrics (Songfacts, Wikipedia) confirmed the chorus line.
3. **The concept** came from the lyric, but its imagery came from Dexter's world (day mask against night hunter), not from vampire clichés alone.
4. **The footage review** found day shots (S1–S5 sunny Miami) and night shots (S4 pack p9). No new Dexter packs came with the brief; the two Flash packs attached were catalogued for the other studio.
5. **The engine:** built on the v104 standard, restyled entirely in `fx105.py`. Every set piece is procedural:
   - bat sprites with flapping wings;
   - a lunar surface with craters, maria and limb darkening;
   - a coffin lid from a height map with normals, diffuse and specular;
   - a particle system for the embers;
   - noise fields for the mist.
6. **ASHES TO SUN (the loop, rev 3)**, built in this order:
   1. The sun rises beside him, and his edge catches fire (a flickering rim, embers off his hair and shoulders).
   2. He burns like paper from the side facing the sun inward: a burn order map combining distance from his silhouette edge, direction to the sun and two octaves of noise. Ahead of the front he chars, at the front a thin line glows, and behind it the street shows through (each row continues the background on either side of him).
   3. 3,000 embers (one per burnt piece, keeping his colour, then turning orange and white-gold) drift up and spiral into the sun's exact position in frame 0.
   4. The sun flares (radial rays and a shock ring), and under the flash the picture becomes frame 0 (the boat shot).
   5. The light collapses back into the sun like an iris, so frame 0 opens on the blazing sun, which calms over a quarter second.
   His ashes become the sun he ran from, and the day and the mask begin again.

## 4. Revision history
- **Rev 1 (first delivery).** The internal review before delivery caught and fixed these:
  - the bat burst first came out of his mouth (rebuilt as a 3D flight from the sky);
  - the swarm read as wallpaper (rebuilt in depth with a moonlight band behind it);
  - the coffin looked like a flat brown shape with dots (rebuilt with height-map lighting);
  - the moon was a flat red disc (now a procedural surface);
  - the sun streaks and dawn sun sat on his face (moved);
  - red title on red footage (re-timed);
  - a missing logo (added once, unrestyled);
  - text on his chin (moved);
  - effects 20–25 dB under the song (raised).
  On the encoded file, QC failed face centring on an over-tight sunset close-up (re-timed to a centred moment), and two night shots were nearly black (per-shot exposure).
- **Rev 2. The owner's note:** *"I like the edit but what happened with the sun and the top right part of dexters head? Additionally, I would like for you to add a couple more transitions, graphics, and unique creative animations."*
  - **Diagnosis:** the sun (disc, glow and rays) was laid over the whole frame, so where his hair met the sky it burned his head away. The sun was in front of him.
  - **Change:** every sun shot now uses his MODNet matte. The disc and rays come only from the sky behind him, 22% of the light scatters over him, there's a light wrap on his near edge, and the lens ghosts dim by how much of the sun he covers.
  - **Added:**
    - cape sweep (replacing a repeated whip);
    - mist ("he turns to mist", into a new knife shot);
    - the great bat through the lens (into a new flashlight shot);
    - sunlit dust;
    - the first dawn burn.
  - **Tried and failed:**
    - the mist read first as blotchy holes, then as vertical drips (the owner dislikes drips); it became a soft blur-and-rise smoke dissolve;
    - the great bat started on his face with a cartoon outline; it now starts in the top corner with a fine edge;
    - the dawn burn was invisible on a frame-filling close-up (no edge for the matte), so the final shot was swapped for a full silhouette;
    - after the light wrap, the face detector read the tight sunset close-up as cut off, so it's framed off-centre (`face_x`).
- **Rev 3. The owner's note:** *"I would like for you to improve the transition/loop at the end and make it a more creative and unique transition. Try to do something creative and different. Please add transitions, graphics and animations wherever possible."*
  - **Change:**
    - the ASHES TO SUN loop (§3);
    - frame 0 became the clean boat shot (it had been hazed white);
    - new transitions: eclipse, card flip, palm sweep;
    - gathering bats before the drop;
    - a crimson backlight and night fog.
  - **Tried and failed:**
    - the burnt area first showed flat cream; then the sun's rays still "saw" his burnt body and cast straight wedge shadows (fixed by burning him *before* drawing the sun);
    - inpainting the street smeared into diagonal wedges (replaced with a row-by-row continuation);
    - a faint ghost outline remained (fixed with a hardened matte);
    - the library's cube and foliage transitions brought v6's synthwave grid and v9's jasmine (replaced with new ones);
    - the palm fronds lingered over his face (sped up).

## 5. What made it good / what made it weak
- **Good, per the owner:** approved as a standard after the loop rebuild.
- **Good, the studio's analysis:**
  - a concept from the song's words carried through grade, set pieces, sound and loop;
  - the day/night split lands on the song's biggest change;
  - five set pieces, each multi-stage with layered sound;
  - 27 designed transitions, with almost no generic move unthemed;
  - a loop that is itself a set piece and lands in frame 0's own sun;
  - light physically behind him;
  - every procedural asset lit (height maps, specular, rims) and checked at full size;
  - text only on verified sung words.
- **Weak:**
  - **Clip quality (the owner's gripe).** Every library pack is 720p; several are heavily compressed (p8 S1 at 0.43 Mb/s, p9/p6/p10 at about 0.7 Mb/s); a 9:16 crop is enlarged about 2.8×. The softest shots were:
    - the daybreak walk (zoomed to 3.5×);
    - the palms (p10);
    - the lollipop (p8);
    - then the ice cream, hood and pink-wall shots.
  - **Measured against the newer v11 rules:**
    - the loop seam is 8.4, against a target of ≤ 1 (the light is still collapsing on the last frame);
    - there are two white-outs: the torch blind-out (frames 687–692, mean luma 236) and the loop flare (1360–1372, mean luma 223).

## 6. Measured results
| Check | Result |
|---|---|
| QC checkpoint | 11/11 PASS (incl. the flash-rate check added later) |
| Loudness after AAC | −13.1 LUFS / −4.1 dBTP |
| Loop seam (blurred diff; target ≤ 1) | 8.4 |
| Flashes | two white-out runs (peaks 236 and 223); at most 2 flashes a second |
| Softest shots | daybreak walk 0.147, palms 0.154, lollipop 0.200 (detail score on the MP4; 0.30+ is sharp) |
| Transitions / longest span without a beat | 27 / 1.57 s (the drop and moon shots, each full of internal beats: burst, title, iris, moon rise) |

## 7. New rules (adopt in both studios)
1. **Light sources go behind the subject, not over him.** Give sun, glow and ray shots the person matte, draw the light only from the background, and add a light wrap on the near edge. Evidence: "what happened with the sun and the top right part of dexters head?" (v105, rev 1). Applies to: all edits.
2. **Clip quality.**
   - Restore 720p sources (Studio 1's `tools/sr_prep.py`).
   - Rank shots by sharpness before choosing them (`tools/sharpness.py N --src`) and on the render, and swap SOFT ones.
   - Keep zoom at or under about 1.1 on 720p.
   - Put hero shots and close-ups on the high-bitrate packs.
   - Ask for 1080p or 4K packs when a hero moment needs one.
   Evidence: "The only gripe I have is the quality of some of the clips" (v105 verdict). Applies to: all edits.
3. **The loop should be the most creative transition in the edit**, a set piece that pays off the concept and lands in frame 0's own image, not a fade or white-out. Evidence: "make it a more creative and unique transition" (v105, rev 2→3), then approval. Applies to: all edits.
4. **Restyle library transitions before reusing them;** they carry their original edit's look (v6's cube brings a synthwave grid, v9's foliage brings jasmine). Evidence: v105 rev 3 review. Applies to: all edits.
5. **When a burn, dissolve or disintegration removes the subject, remove him before drawing scene light**, so nothing (rays, shadows, wraps) still reacts to him. Fill the hole with a plausible background, not a flat colour. Evidence: v105 rev 3 review. Applies to: all edits.
6. **When the owner asks to "add transitions, graphics and animations wherever possible", replace the generic connectors with themed ones and add new cuts with new transitions**, rather than stacking effects on existing shots. Evidence: rev 2 and rev 3, then approval. Applies to: all edits.

## 8. Reusable assets
| Technique / transition | Where the code is | How to restyle it for another show |
|---|---|---|
| Sun behind the subject: `sun_fx(..., m)` with light wrap, rays from the sky only, ghosts scaled by visibility | `v105/work/fx105.py` | Any light source (lightning, a streetlight, the Speed Force glow): swap the colour and position. |
| ASHES TO SUN: `ash_setup`, `ash_body`, `ashes_fx`, `clean_plate`, `seam_out` | `fx105.py` | Any disintegration into a target: Flash → lightning sparks into the emblem; any subject → particles into frame 0's focal point. |
| Eclipse transition `eclipse_tr` | `fx105.py` | A disc wipe with corona; recolour the corona, or use a lens or an emblem. |
| 3D flock: `bat_burst`, `bat_swarm`, `bat_pass_tr`, `bat_sprite` | `fx105.py` | Any swarm sprite (debris, birds, shards); the depth projection and blur stay. |
| Height-map-lit object: `coffin_lid` | `fx105.py` | Any hero prop (an emblem, a badge, a door): draw a height map and light it. |
| Procedural moon: `moon_tex`, `bloodmoon_fx` | `fx105.py` | A planet or the sun behind a matte. |
| Mist dissolve `mist_tr`; cape sweep `cape_tr`; card flip `card_flip`; palm sweep `palm_sweep` | `fx105.py` | Recolour or swap the sprite (the cape becomes a coat or flag; the palms become foliage, cables or banners). |
| Flash measurement in QC (section 7b) | `v105/work/qc105.py` | Drop-in for any `qcN.py`. |
| Clip quality ranking | `tools/sharpness.py` | Works on any edit (`--src` before rendering). |

## 9. For the other studio
- Your `tools/sr_prep.py` is the direct fix for this edit's gripe. The Dexter studio will use it from v106 on, once the branches merge.
- The ASHES TO SUN technique pairs well with your "loop lands exactly on frame 0" rule. Building the end from frame 0's image is how v105's frame 0 and last frame match visually, but v105's measured seam (8.4) misses your ≤ 1. Making the last frame equal frame 0's image exactly (the iris fully closed on frame 0's sun) would close it.
- **The question to settle:** which engine new edits start from. The Dexter studio uses v105; you use v11. The proposal: Dexter edits from v105, Flash edits from v11, with shared effects ported both ways through handoffs.
