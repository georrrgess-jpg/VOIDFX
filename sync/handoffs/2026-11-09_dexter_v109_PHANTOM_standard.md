# HANDOFF: v109 PHANTOM (Dexter × EsDeeKid & Rico Ace "Phantom"): STANDARD

**From:** the Dexter studio · **Date:** 2026-11-09 · **Revisions:** 3 owner rounds after the first delivery (rev 1, rev 2, rev 3) · **Folder / branch:** `v109/` on `dev/pipeline-v2`

## 1. Verdict, in the owner's words
> "I like this edit, make it a standard."

- **Status:** standard. New Dexter edits scaffold from it (`new_edit.py N SLUG "TITLE" --base v109`; the default for Dexter titles). v108 is the previous Dexter standard (`--base v108` still works).
- **The owner's gripes:** none at the verdict. Every round before it carried notes, though, and the removals are now rules (§7):
  - the headspin "doesn't flow";
  - the Doakes shots;
  - the heart monitor;
  - the mist-fade loop and the end flow;
  - a missing focal point.

## 2. The edit at a glance
| | |
|---|---|
| Song / window | EsDeeKid & Rico Ace "Phantom", 0:10.5–0:34.5 (h24–h80), **70.0 BPM on the drum stem** (the auto map read 93.3, 4/3 of it). One bar before the beat drops (13.05 s in the song = 2.57 s in the edit) through "you've never got no motion, as you've never got no action". |
| Length / format | 24.0 s, 1080×1920, 60 fps, loops |
| Concept | **PHANTOM.** *"Rocked out like a phantom"*: the Bay Harbor Butcher as a ghost the city hunts and never sees. He walks out of the dark, a flashlight finds him, he **materialises** out of mist on the drop. His ghost work runs through the middle: after-images, a glass pane, the phone's tantrum, the light failing, the surveillance feed, vanishing where he stands. The end is the hunt, then the fire, then **the gust** that takes him and brings him back. |
| Look | **SPECTRAL**: silver-blue night, inky blacks, cold cyan highlights with a faint ghost bloom. Only blood red survives (`R − 1.85·max(G, B)`, with a per-shot `redthr` to keep sunburnt skin out). Fine grain, a vignette. The one other colour is the red of THE PHANTOM'S TRAIL and the fire's embers. |
| Structure | Frame 0: he walks out of the dark → flashlight → **MATERIALISE** (the drop, red kill room) → **PHANTOM** title over his double, the picture breaking into particles → the ghost section (phone glitch, flicker, **phantom pass**, slices, plastic, evidence photo, surveillance, vanish, page turn) → **THE PHANTOM'S TRAIL** (the focal point, 14.6–15.4 s) → the graphic chain (**FINGERPRINT** 16.7 s, **THE PHOTO'S FIRE** 18.4 s) → red wash, streetlight, a clean downbeat cut to his stare → **THE GUST** into frame 0. |
| Set pieces | **MATERIALISE** (the frame dissolves into mist → on the drop he forms out of it first, then the room). **PHANTOM** (the title condenses letter by letter on a 16th grid and blows away). **THE PHANTOM'S TRAIL**: a red silk ribbon of light spirals in, circles him in depth, then dives at the lens and swells into a window onto the next shot. **THE PHOTO'S FIRE**: an ember catches on the real photo, the photo burns through, then the frame. **THE GUST**: dust from his own matte, body first and face last; the same gust settles head-first into frame 0. |
| Transitions | 22 designed + 1 clean downbeat cut + the loop, in 24 s.<br>**Custom (v109):** flashlight109, materialize109, afterimage109, mirror109, tantrum109, flicker109, phantom_pass109, cctv109, vanish109, trail109, print109, burn109, redwash109, streetlight109, and the loop dust_loop109.<br>**Library:** time_particles, slices, surface, polaroid, page_turn107, whip ×2, smear. |
| Text | One designed title, PHANTOM, on the sung word (the lyrics are explicit: titles, not captions, v11). |
| Sound | **11 placed effects:** the flashlight click; a reverse swell, impact and sub drop into MATERIALISE; the title's breath; the phone buzz; the pass; the vanish; the trail's dive; the photo catching fire; the gust. Effects sit +10 dB against the master, and the music is ducked 3 dB under the drop. −13.1 LUFS. |

## 3. Creative process
- **The tempo:** the auto map locked to 93.3 BPM. The drum-stem fit found 70.0, so the window was re-chosen at h24–h80.
- **The concept** came from the title word and Dexter's double life: a man no one sees. One hero, the mist, carries the drop (materialise), the vanish and the pass, three appearances (v13 rule). The loop uses dust, not mist, so it reads as its own idea.
- **Before the first delivery,** the fresh-eyes critique made these changes:
  - seven v108 transitions were replaced by new ones;
  - the drawn caution tape and a second mist transition were removed;
  - five look-alike or faceless shots were swapped;
  - the mist lost its outlines.
- **The owner's three rounds** pushed in one direction: fewer library moves, more graphics that come out of the footage and become the cut, and a centrepiece.

## 4. Revision history
- **First delivery** (QC SHIP; 3 full renders, one over the target of 2).
- **Rev 1, the owner:** *"I relatively like this edit … the head spin transition. I don't really like how that flows with this edit … replace it with a brand new, unique, and creative transition … remove the clips with dokes and replace them with other high-quality texture clips … make a cool flow where there's unique graphics appearing and then transitions from those graphics … the end flow of the edit and into the loop. I don't really like that part … make it more unique and creative with better animations."*
  - **Diagnosis:**
    - A hard spin broke a slow, dark edit's flow.
    - Two shots featured Doakes, not Dexter, and one was soft.
    - The ending was five library connectors in a row (dolly, whip, flip, roll, dolly).
    - The loop was a grey mist fill-and-clear with blotchy erosion on his face.
  - **Change:**
    - **PHANTOM PASS** replaces the headspin. He walks at us, his body turns see-through (the next shot inside his silhouette, a cold rim), and the camera passes through him.
    - **The mangroves** and **the burning photo** (S1 `dexter_s1_hq`, 2.0 Mb/s) replace the cage and the Doakes close-up.
    - The graphic chain: **FINGERPRINT** (dusted on, a forensic light passes, a dive into the whorl), **THE PHOTO'S FIRE**, and a **heart monitor** that flatlined and opened like an eye.
    - The ending without spins: **red wash** and **streetlight** replace the roll and the flip.
    - The kitchen lunge (soft, off-centre) and the garden (it looked like the night walk) became **the container** and **the police-lot stare**.
    - The p7 tape shot came mirrored ("DO NOT CROSS" read backwards) and is now flipped.
    - **THE GUST** replaces the loop.
  - **Tried and failed on the way:**
    - The pass's rim stacked on a backlit ear (a white speck), so it now uses a screen blend; its matte dropped a shoulder for a frame, so it is steadied over neighbouring frames.
    - The print first sat on his neck and dived onto the incoming face, which read as a target; it now dives into his chest.
    - The first burn edge was a thin white outline; it now has real embers.
    - The gust first eroded in blobby cells, went dark for 0.5 s and re-formed in dark chips. It is now finer and overlapped, his face goes last, and a faint frame 0 shows under the dust.
    - The new day shots' skin went blood-red, fixed with `redthr` 0.30.
  - **The fresh-eyes critique predicted:** the spins, the target-like whorl, the mirrored tape, the look-alike garden and the straight slit of the flatline.
- **Rev 2, the owner:** *"I like this edit a lot … change the heart monitor on the 21-second mark. You don't have to replace this with anything … make the fire transition graphic … stem from the actual picture that's burning and try to make it tied into that transition."*
  - **Diagnosis:**
    - The monitor was an interface overlay drawn on the footage.
    - The fire started at the flame's brightest point near his mouth, not on the photo.
  - **Change:**
    - The monitor is gone: a clean cut on the downbeat with the beat camera's punch.
    - **THE PHOTO BURNS:** the flame's foot is tracked on the real photo (4 keyframes). A burn-time field is fast inside a ragged photo mask, so the photo burns through first with the next shot inside it, then spills off the photo's edges onto the frame.
  - **Tried and failed:** the first photo hole was a clean quad that read as a rectangle. The mask edge is now noise-warped and the fire leaves the photo sooner.
- **Rev 3, the owner:** *"I really like this edit still, but I think it's just missing one more focal point … one more really, really cool, custom, unique graphic into a transition … the finishing touch."*
  - **Change:** **THE PHANTOM'S TRAIL** on the dock shot, into the night hunt. It replaced the hot-molasses pour reused from v108, so the cut count stays the same.
  - **Tried and failed:** the first build was a thin red line with a red-flash dive. It is now bold two-strand silk with a white-hot core, and a dive where the ribbon's head leads and the band swells into a window with glowing edges.
- **Verdict:** *"I like this edit, make it a standard."*

## 5. What made it good / what made it weak
- **Good:**
  - the owner liked it from the first delivery ("relatively like", "like a lot", "really like … still");
  - one look carried throughout (SPECTRAL, with red as the only colour);
  - graphics that come out of the footage and *become* the cut (fingerprint, fire on the real photo, trail);
  - a centrepiece with real depth (behind him through his matte, in front of him);
  - a loop with real animation;
  - lean sound (11);
  - no text beyond one title.
- **Weak:**
  - **It took 3 owner rounds** (the target is 2): each one asked for more custom graphics or a better flow, which a first delivery should already have.
  - **Two spins** (the headspin, then the roll and flip) survived to the first delivery.
  - **The heart monitor** was an overlay in a chain of graphics that otherwise came from the footage.
  - **Soft shots:** `sharpness.py` flags 8 shots soft (open, flash, hood, double, anthem, hazmat, gloves, dock); the owner did not raise clip quality this time.
  - **The container shot** (S1 371.7) also appeared in v108.

## 6. Measured results
| Check | Result |
|---|---|
| QC checkpoint | 11/11 on the encode |
| Loudness after AAC | −13.1 LUFS / −3.1 dBTP |
| Loop seam (blurred diff; target ≤ 1) | 0.12; wrap step 0.8 vs a local median of 0.9; audio seam step 0.001 |
| Flashes | 0 over the limit, no white-outs |
| Motion audit | No dead spans and no judder. 2 unexplained pops: f571, real motion in the hazmat source (since the first delivery); f1254, a small source change in the dark drive shot. |
| Faces vs effects | 3 runs, all designed: the phone glitch (412), the real tape crossing his face (734), his face dissolving in the gust (1378–1384) |
| Softest shots (`tools/sharpness.py`) | open, flash, hood, double, anthem, hazmat, gloves, dock |
| Transitions / density | 22 designed + 1 clean cut + the loop in 24 s (0.96/s); generic connectors 4 (whip ×2, smear, slices) |
| Effort | 7 full renders across 4 deliveries (1.8 per round); `metrics.py 109 summary` |

## 7. New rules (adopt in both studios)
1. **A focal point mid-edit, besides the drop**: one centrepiece graphic, about 1 s with its own motion and depth (behind him through his matte, in front of him, never across the face), that becomes the transition. Evidence: *"it's just missing one more focal point … one more really, really cool, custom, unique graphic into a transition … the finishing touch"* (rev 3), then the verdict. It is the same ask as v13's light ribbon. Applies to: all edits.
2. **A flow of graphics that become transitions**: chain two or three graphic → transition moments in the back half, each graphic on its shot for about 0.5–1 s first. Evidence: *"a cool flow where there's unique graphics appearing and then transitions from those graphics"* (rev 1); the fingerprint and the fire stayed. Applies to: all edits.
3. **A prop's effect starts on the prop, tracked through the shot**: burn, pour or shatter from the real object, the object first, then the frame. Evidence: *"make it stem from the actual picture that's burning and try to make it tied into that transition"* (rev 2). Extends v108 rule 2 to every prop-motivated transition. Applies to: all edits (Flash: the emblem, the suit, the ring).
4. **No HUD or interface overlays** (monitor traces, readouts, timers) drawn over the footage. A frame treatment such as v109's surveillance feed is fine. Evidence: *"change the heart monitor … You don't have to replace this with anything"* (rev 2), and v6's removed VHS counter. `ekg109` is rejected in the registry. Applies to: all edits.
5. **Spins only in kinetic edits, and once.** A headspin, roll or flip breaks a smooth, dark edit. Evidence: *"I don't really like how that flows with this edit"* (rev 1, the headspin; the roll and flip went with it). Applies to: all edits.
6. **Stay on the main character; swap soft or busy shots for sharp "texture" clips** (fire, foliage, rust; the high-bitrate packs). Evidence: *"remove the clips with dokes and replace them with other high-quality texture clips"* (rev 1). Applies to: Dexter (Flash: keep the focus on Barry unless the concept needs the rival).
7. **The loop needs real animated physics** that builds frame 0 from its own picture, with no dark gap; a fade or fog is not enough. Evidence: *"the end flow of the edit and into the loop. I don't really like that part … more unique and creative with better animations"* (rev 1), then THE GUST was approved. Applies to: all edits.
8. **Technical:**
   - read any text in pack shots to catch mirroring (`hflip=True` in the v109 base);
   - keep sunburnt skin out of a blood-red channel with a per-shot `redthr`;
   - before a matte-driven transition, close the matte's holes and take the max over neighbouring frames.
   Applies to: all edits.

## 8. Reusable assets
| Technique / transition | Where the code is | How to restyle it for another show |
|---|---|---|
| **THE PHANTOM'S TRAIL** (`trail109`: a 3-D ribbon of light orbiting a matte, a twisting silk width, a white-hot core, a companion strand, embers, a dive that swells into a window) | `v109/work/fx109.py` (rev 3 section) | Flash: a lightning-gold ribbon around Barry that dives into the next shot (it echoes v13's light ribbon, built here with depth through the matte). The orbit is placed from the matte; keep it on the chest and waist. |
| **The prop-born burn** (`burn109`: a tracked origin, a burn-time field fast inside a ragged prop mask, then spilling out; ember lip, char, scorch, sparks) | `fx109.py` (rev 2 section) | Any burning or melting prop: a letter, a photo, a map. Re-key `BN_KEYS` (the flame's foot per keyframe) and the prop's quad. |
| **FINGERPRINT** (`print109`: a procedural whorl-to-loop print with ridge endings and powder grain, a brush reveal, a forensic light, a dive into the whorl) | `fx109.py` (rev 1 section) | Any forensic moment; dive into the chest, not the face. |
| **PHANTOM PASS** (`phantom_pass109`: a see-through body, then a camera move through the silhouette) | `fx109.py` | Any walk toward the camera; needs a clean, steadied matte (`_pp_clean`). |
| **THE GUST** (`dust_loop109`: release and arrival fields, a flight integrated along a gust and swirl field, near flakes, a ghost of frame 0 under the dust) | `fx109.py` | Any loop where the subject leaves and frame 0 re-forms; colour the motes to the grade. |
| `splat109` (bilinear point splat into a low-res buffer) | `fx109.py` | Any particle work (sparks, embers, dust). |
| SPECTRAL grade + `finish109` | `fx109.py` (v109 section) | A night look where one colour survives. |
| `hflip` for mirrored packs | `fx109.py` (end) | Set `hflip=True` on the shot. |

## 9. For the other studio
- **The focal-point ask is now on record in both studios** (v13 light ribbon, v109 trail): plan one centrepiece graphic → transition mid-edit, besides the drop.
- **No HUD overlays:** check any planned speed readout, timer or scanner widget against rule 4. A frame treatment is fine.
- **Spins:** v13 and v12 are kinetic, so one spin fits. In a slow Flash edit (v14 style), skip them.
- **The scaffold:** Dexter edits now start from `--base v109` (v108 + the v109 toolkit). The Flash scaffold (v12) is unchanged. `trail109`, `burn109` and `dust_loop109` port to the v12 engine through `fxN.py` + `splice_section.py`; they need `_person`, `face_scr`, `nz108`, `_up`, `splat109` and `_pp_clean` from the v108/v109 sections.
