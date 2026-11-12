# HANDOFF: v111 MONSTER (Dexter × Kanye West "Monster"): STANDARD

**From:** the Dexter studio · **Date:** 2026-11-11 · **Revisions:** 1 owner round after the first delivery · **Folder / branch:** `v111/` on `dev/pipeline-v2`

## 1. Verdict, in the owner's words
> "This edit is adequate make it a standard"

- **Status:** standard. New Dexter edits scaffold from it (`new_edit.py N SLUG "TITLE" --base v111`; the default for Dexter titles). v110 is the previous Dexter standard (`--base v110` still works).
- **The verdict is lukewarm ("adequate").** It was not praised outright. Treat v111 as a solid base, not the ceiling: the owner asked for *"the best Dexter edit"* and rated it adequate.
- **The brief:** *"create an edit using the attached song … high quality … the best edit you have created … really cool and unique transitions, graphics and animations … the best dexter edit … completed with efficiency and quality."*

## 2. The edit at a glance
| | |
|---|---|
| Song / window | Kanye West "Monster" (6:19). **93.7 BPM** (the drum stem, the snare and the full mix agree on a 0.640 s beat; the first map's 125 BPM was a 3:4 alias of the dotted-eighth kicks, and its auto window at 4:36 had no words). Window: the whole Bon Iver intro and the drop, padded file `src/monster_pad.wav` (1.0 s of silence in front) h2–h90 = 28.18 s; the drop at e65 (20.8 s, "…I'm a monster"), ending on "rumbles" |
| Length / format | 28.18 s, 1080×1920, 60 fps, loops |
| Concept | **I SHOOT THE LIGHTS OUT.** He is the thing that lives in the dark; a flow of light: the lights shot out → the light comes back from below → daybreak → the day burns white → nightfall → the moon → the kill lamp → the shadows close in → the monster in daylight → the light bar → the woods → the shot |
| Look | **NIGHTSHADE**: teal-navy shadows, warm practicals, the day golden; harder and redder after the drop. No text |
| Structure | LIGHTS OUT (the marina, slowed: a light blows on each beat of "shoot", then a wave of lights dies toward him on "the lights out", sparks and glass falling) → emerge (his face lit from below) → door pan → fence push → DAYBREAK (god rays) → bright out → tear → NIGHTFALL (the garden lamp comes on) → look up → THE MOON (rises behind him, swells, becomes the kill lamp; dust in its light) → the table, the gloves, underlight into the scalpel → light match → THE PASSENGER (the build: the shadows grow, the light in his hands pulses; the drop: the day opens from the frame's edges behind him, he goes last) → the suit → slides → BLEED → the grin (a clean downbeat cut) → the red face → THE SIREN + the light bar → the woods, fronds, bokeh → THE TRACER (the loop) |
| Transitions | 25 + the loop in 28.2 s.<br>**Custom (v111):** emerge, doorslide, fence, daybreak, brightout, nightfall, lookup, moon, underlight, lightmatch, passenger (the signature), slide, bleed, siren, shot/THE TRACER (the loop).<br>**Liked library:** tear110, light_sweep108, plasticroll110, flicker109, fronds108, bokeh110. Connectors: dolly ×3, whip |
| Animations on shots | the lights blowing with sparks and glass; god rays at the sunrise; the moon rising, swelling, behind him; dust in the lamp light; the build's shadows and pulse; the light bar's red and blue over the crime scene; the muzzle flash, smoke and tracer |
| Sound | ~12 lean effects: lamp pops (one per blown light on "shoot" and the wave), the light on him dying, the daybreak swell, crickets, a whoosh up to the sky, the kill lamp's buzz, a breath in to the drop with an impact and sub drop, a siren whoop on "trouble", the gunshot, a bullet whiz under the whip, the hit at frame 0; the echo carries over the loop |

## 3. Creative process
- **The lyric gave the concept and the loop:** "I shoot the lights out" opens it, so the end fires the shot. In the final loop the tracer lands as the light that blows on "shoot", so the end causes the start.
- **The tempo was wrong at first.** The map's 125 BPM was a 3:4 alias; the drum, snare and full-mix grids all agreed on 93.7 BPM. The song was padded with 1 s of silence so the edit can start just before Bon Iver's "I".
- **Shots were found for light:** a skyline of lights for the opening, a real night sky for the moon, a lamp-lit kill room, a light table, a scalpel lit from below, the blood suit in daylight, the crime-scene tape, a pistol raised at the lens in the woods.
- **Before the first delivery (all fixed before the owner saw it):**
  - frame 0 went through three shots (a tight close-up with no lights, a garden walk that leaves the frame, then the marina);
  - the moon shot first had no sky in the 9:16 crop; the face tracker lost him in three night shots (framed by hand);
  - THE PASSENGER went through four designs (a wall shadow the matte couldn't read; a red-edged double that read as a ring round his face; a shadow lunge that went black; dark-first, then the day from the edges with him last);
  - the fresh-eyes critique caught: the loop as "a flash and a fade", a face-match mirroring his face at the borders, the drop blotching his face, double exposures, the opening too quiet at phone size, the tape smeared by interpolation.
- **Process failures:** a render worker was OOM-killed while the source restoration ran (the pool hung for 30 min); the disk filled once (old edits' regenerable caches were cleared).

## 4. Revision history
- **First delivery:** QC 11/11 after four internal render rounds.
- **Rev 1, the owner:** *"I generally like this edit but I would like for you to change a couple things. Firstly, I dislike the graphic/animation that appeared around the 23 second mark the forensics one. I would like for you to also implement a new more creative loop. I want more custom graphics and animations to be implemented."*
  - **Change:**
    - The luminol (the forensic glow into the blood room) became **BLEED**: the blood spot on his slide soaks out through the frame, the blood room inside it.
    - The loop became **THE TRACER**: he fires; we whip after the bullet's tracer up through the night, and it lands in the marina's skyline as the light that blows on "shoot".
    - New animations: sparks and glass from every blowing light, god rays at the sunrise, dust in the lamp light, the light bar washing the crime scene.
  - **Caught:** the tracer's first path crossed his face (routed up the right); the bleed's wet front stained his face (guarded).
- **Verdict:** *"This edit is adequate make it a standard."*

## 5. What made it good / what made it weak
- **Good:**
  - two owner rounds (the target);
  - a concept built from the lyric, with the loop closing it causally (the end fires the shot that starts it);
  - light as the through-line (every transition and graphic motivated by a light in the shot);
  - QC 12/12 and a 0.16 loop seam.
- **Weak:**
  - **"adequate", not liked:** the owner wanted the best Dexter edit and more custom graphics; the first delivery had too few living graphics on the shots;
  - **the forensic luminol graphic** (a liked v108 piece) read as a lab graphic here and was disliked;
  - **the first loop** (a burst from the muzzle into frame 0) was not creative enough;
  - 28.2 s is longer than the owner's usual 20–26 s;
  - a long, slow intro (20.8 s before the drop) that needed many graphics to stay alive.

## 6. Measured results
| Check | Result |
|---|---|
| QC checkpoint | 12/12 on the encode |
| Loudness after AAC | −13.1 LUFS / −2.6 dBTP |
| Loop seam (blurred diff; target ≤ 1) | 0.16; audio seam step 0.0009 |
| Flashes | none over the limit; no white-outs |
| Motion audit | one quiet span flagged at 0.3–2.2 s (the slowed opening, lights popping); the flagged pops are the designed stutter of the last light on "out"; judder on the garden shot (its source) |
| Faces vs effects | 3 light flags: the hit flare beside his head at frame 0, the muzzle flash, the build's pulse |
| Transitions | 25 + the loop in 28.2 s |
| Effort | 2 owner rounds; 6 full renders (4 before the first delivery); `metrics.py 111 summary` |

## 7. New rules (adopt in both studios)
1. **No forensic or lab graphics as a transition** (luminol glow, UV, spatter-analysis overlays). Use the scene's own material instead (the blood on the slide soaking out). Evidence: *"I dislike the graphic/animation … around the 23 second mark the forensics one"*. `luminol108` is now rejected (it was liked in v108; the newer verdict wins). Applies to: all edits.
2. **The loop must be a creative, causal event, not a flash, burst or fade into frame 0.** The best loop makes the end cause the start (the tracer becomes the light that blows on "shoot"). Evidence: *"implement a new more creative loop"*, after a muzzle-flash burst into frame 0. Applies to: all edits.
3. **Every section carries a living graphic or animation on the shot, not only at the cuts** (particles, rays, light washes, a rising moon, dust in a beam), each motivated by a light or material in the shot and kept off faces. Evidence: *"I want more custom graphics and animations"*. Applies to: all edits.
4. **"Adequate" is not "liked".** For "the best edit" briefs, plan at least one designed animation per section and a signature that reads at phone size from the first delivery.
5. **Technical:**
   - check the map's tempo against the drum stem, the snare band and the full mix; a 3:4 alias picks the wrong grid and an instrumental window;
   - pad the song (1 s of silence) to start just before a pickup word;
   - do not render while the source restoration runs (a worker was OOM-killed and the pool hung); clear old edits' frame caches when the disk is low;
   - tracked or drawn light (a tracer, a flare) is routed and masked away from faces; a light front over a face uses a face guard;
   - frame night shots by hand (`face=None, cx=…`) when the tracker loses him in the dark.

   Applies to: all edits.

## 8. Reusable assets
| Technique / transition | Where the code is | How to restyle it for another show |
|---|---|---|
| LIGHTS OUT (`lightsout111`, `_lo_map`, `_sparks111`: practical lights found by luminance, each dying with a stutter and a flare, sparks and glass falling, the room stepping down on sung words) | `v111/work/fx111.py` | Any skyline or room of lights: a city blackout, a power cut, a Speed Force surge killing the lights |
| THE TRACER loop (`shot111`: tracked muzzle flash, a whip after a tracer into the light it hits in frame 0) | `fx111.py` (rev 1 section) | Any loop where the end's action causes the start: a thrown object, a lightning bolt, a bullet, a spark |
| THE MOON (`moon_draw111`, `moon111`: a drawn moon only in the sky mask, swelling into a lamp) | `fx111.py` | Any sky object that becomes a practical light (sun → headlight, moon → lamp) |
| THE PASSENGER (`shadow111`, `passenger111`: shadows grow on the beat; the next shot opens from the frame's edges behind him, the subject last) | `fx111.py` | Any drop that should feel like the world turning around the subject |
| BLEED (`bleed111`: a real spot in the shot soaks out with an organic, noise-warped edge, face-guarded) | `fx111.py` (rev 1) | Ink, paint, wine, lightning burns |
| DAYBREAK, BRIGHT OUT, NIGHTFALL, EMERGE, UNDERLIGHT, LIGHT MATCH, LOOK UP, DOOR, FENCE, SLIDE, SIREN | `fx111.py` | Light-motivated, generic |
| Animations: god rays (`rays111`), dust in light (`motes111`), the light bar (`lightbar111`) | `fx111.py` (rev 1) | Drop-in for any shot with a strong light |
| NIGHTSHADE grade (`grade`, `finish111`) | `fx111.py` | A night look that hardens after the drop |

## 9. For the other studio
- **Rules 1–4 apply to Flash edits as they are.** Rule 1's Flash form: no lab or tech readouts as transitions (no HUDs, already banned); use the scene's own material. Rule 3: a living graphic in every section (lightning motes, speed-force dust, light washes), kept off faces.
- **The loop bar has risen:** the owner now asks for a creative loop in which the end causes the start, not a flash or burst into frame 0.
- **The scaffold:** Dexter edits now start from `--base v111` (v110 + the v111 toolkit); the Flash scaffold (v12) is unchanged. `lightsout111`, `shot111`, `moon_draw111`, `bleed111`, `rays111`, `motes111` port through `fxN.py`; they need `_person`, `_pp_clean`, `face_scr`, `to_screen`, `nz108`, `frame0_plate108`.
- **The operational lesson:** no renders while `sr_prep` runs; watch the disk.
