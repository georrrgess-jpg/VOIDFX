# HANDOFF: v14 KEEPSAKES (The Flash × C418 "Mice on Venus"): STANDARD

**From:** the Flash studio · **Date:** 2026-11-09 · **Revisions:** 3 (rev 1, rev 2, and a one-note round 3) · **Folder / branch:** `v14/` on `claude/gallant-planck-pqpczp`

## 1. Verdict, in the owner's words
> "I like this edit make it a standard. However, I want it to be noted that this edit is a different style from the
> flash edits we normally create but is still really good."

- **Status:** standard, a **different style** from the Flash standards. It is the reference for a calm, nostalgic edit
  on a slow song. v10–v12 stay the reference for energetic Flash edits.
- **Engine base:** unchanged. New Flash edits still scaffold from v12; v14 is built on the v12 engine with its own
  section (`v14/work/sec14.py`), and its pieces port from there (§8). Making v14 a `new_edit.py` base is a tools change,
  so it goes through a DEV handoff, and only if the owner wants it (§9).
- **The owner's reasons:** "a different style ... but is still really good"; round 1: "I like the feeling the edit
  presents".

## 2. The edit at a glance
| | |
|---|---|
| Song / window | C418 "Mice on Venus", song 196.56–222.48 s (half-beats h728–h824, P = 0.26997 s, ~111 BPM on the piano). It covers the build, the quiet pause (single notes on e30, e34, e38, e42) and the full theme returning at e46, the part people know. Chosen for the owner's "best parts or most popular parts" |
| Length / format | 25.92 s, 1080×1920, 60 fps |
| Concept | **KEEPSAKES**: nostalgia for where it all began. The night Barry woke from the coma (S1) opens the edit and the owner's achievement toast marks it ("Achievement Made! The Beginning?"). The years run as memories. In the pause his memories sit in a glass ball he looks back through. The loop returns to the dark medical bay, where he wakes again: the question mark is answered by the loop |
| Look | SUNFADE (golden hour on faded film: lifted warm blacks, cream-gold highlights, low saturation with blues fading most, skin protected) under a faint SUPER 8 HAZE: fine and coarse grain, sub-pixel gate weave, halation, two warm edge leaks, a faint flicker, dust and a hair, a soft gate. Unlike every earlier look: warm, faded, quiet |
| Structure | THE WAKE (e0–14) → S1 memories (lab, the first suit, laughing) → THE LENSBALL in the pause (e30–46) → the theme's return on the sun over the water (e46) → shore → EMBLEM GLINT → the years after (S3, S5) → the loop |
| Set pieces | **THE WAKE + THE ACHIEVEMENT**: the lights flicker on, he gasps awake in slow motion, the pixel toast springs up on the gasp. **THE LENSBALL** (focal, the song's pause): the laugh curls into a glass ball, Barry now stands defocused behind it, the ball turns to a new memory on each soft note, we fall in as the theme returns. **EMBLEM GLINT** (2.1 s): push onto the real S1 emblem → the traced bolt lit by a glint → gold lightning → the disc opens on his face → fly through the ring. **THE LIGHTS** (the loop) |
| Transitions | 14 plus the loop. New: `lights_on14`, `lens_in14`, `lens_dive14`, `emblem_glint` (rebuilt), `print_dive` (used once, fast), `focus_rack14`, `double_exp`, `sun_flare`, `film_burn`, `ripple`, `speed_whip14`, `light_leak14`, `afterimage14` (memory echo). Library: `dolly` |
| Text | None but the owner's toast, which is the owner's own request (a reference image) |
| Sound | The song straight, with **five quiet effects**, 8–15 dB under the music: his breath, the toast's soft swish and thock, a paper flick, an air rise into the return, a faint crackle ending in a low whoomp on the emblem. None on beats or small transitions |

## 3. Creative process
- **The window:** the song map found the build into the pause into the theme's return (h728–h824, wrap correlation 0.906). The pause gives a focal set piece its own four notes; the return lands the biggest move.
- **Concept, rev 1:** nostalgia as instant photos, with the print as the hero object (the signature print, THE ALBUM with prints landing on the notes, the print loop). The owner liked the feeling. The print, though, repeated and was slow (§4).
- **Rev 2:** the owner gave the focal point (the wake) and an asset (the toast). The new hero object had to be a different idea from the print. A glass ball lens was chosen because it is a real optical phenomenon (it inverts what's behind it), it reads as "looking back", and it can hold moving memories. Round 3 then asked for the memories upright (§4), so the inversion is gone from the rest state.
- **Rejected on the way:**
  - an eye-match loop: frame 0 has no face;
  - an extreme close-up of his eyes in the dark as the opening: the face is wider than the 9:16 window;
  - the S.T.A.R. Labs monitor as the loop's portal: it is cut off at the frame top and reads as a screen in a room, the v107 TV problem;
  - a particle-accelerator shockwave loop: its wipe edge would cross his face.

## 4. Revision history
- **Rev 1 (first delivery), the concept above.** QC 11/11, seam 0.18. About 1 h 30 min from the song to delivery, on the efficiency loop's pilot.
- **Rev 2, the owner's notes (verbatim):** "I like the feeling the edit presents but I would like a few things to change. Firstly, I want barry waking up for the first time to be the focal point of and in the beginning of the edit. I want the achievement in the attached image to appear in a satifying visually appealing pop up animation. Additionally, the flash symbol on the crest is not an actual lightning bolt and is in the wrong shape I want you to verify that it's the correct shape and change it accordingly. Additionally, the emblem transition is too fast, I would like for you to slow it down and make it more pronounced. Another change I would like made is to remove or change up the picture frame/photo transition graphic. i really like the transition but I don't like that it is too slow and repeats multiple times. I would also like for you to implement a brand new custom graphic and transition/animation."
  - **Diagnosis:**
    - The wake was a 1 s shot at 2.7 s.
    - **The bolt:** the S1 emblem runs off the bottom of every S1 frame (the lower third of the disc is below row 720). Rev 1's push lifted it with `BORDER_REFLECT`, which mirrored the bolt's lower half into a "<" chevron.
    - The emblem transition was 0.5 s.
    - The print was on screen 1.9 s for the signature and came back four times (signature, album, dive, loop).
  - **Change:**
    - **THE WAKE** opens the edit, with the toast drawn from code: our own 5×7 pixel font and 16×16 crate icon, a spring pop, letter hops and a stepped shine, placed under his chin and clear of the TikTok UI.
    - **The bolt:** traced as a 6-point polygon on the real S1 bolt and checked on three source frames. The emblem is template-tracked on the source and drawn as a lit, bevelled asset laid exactly over the real one. The suit below the frame is the bottom band with the emblem inpainted out, then mirrored.
    - **EMBLEM GLINT** runs 2.1 s.
    - The print appears once, as a 0.4 s flick-in and dive.
    - **THE LENSBALL** is the new custom graphic and transition.
    - The loop is the medical bay's lights.
  - **Tried and failed on the way (the studio's stills and the fresh-eyes critique):**
    - the loop's room was dimmed twice, so it was darker than frame 0;
    - the lit bolt blew out to white;
    - the bolt, then lightning, crossed the incoming face;
    - the real bolt's tip showed through as the drawn one dissolved;
    - the lensball's halo was clipped to its bounding box, so a square showed round the glass (critique, HIGH);
    - the loop read as a flicker to near black (critique);
    - the first second was an empty dark room and a smeared rise (critique);
    - the memories sat off-centre in the ball (critique).
- **Round 3, the owner's note (verbatim):** "I just want the little circle orb thing that switches between the pictures. I would like for it to face upright so that Barry's face is facing upwards. And if the correct orientation." (also: "I would like this change made pretty quickly")
  - **Diagnosis:** the ball showed its memories upside down, the way a real ball lens does. Physically right, but the owner wants to see the faces.
  - **Change:** the memories are upright at rest and through the dive (one angle in `ball_rest` and the dive's end angle). One render, QC, delivered.
- **The verdict** followed round 3.

## 5. What made it good / what made it weak
- **Good:**
  - **The owner's view:** the feeling, and "a different style ... but still really good".
  - **The studio's analysis:**
    - The song carries it: five quiet effects, no beat camera punches, a camera that only breathes on the strong notes.
    - The overlay is felt but never in the way.
    - Every set piece is placed on the song's structure: the gasp on a strong onset, the ball's turns on the soft notes, the dive on the pickup, the return on the theme.
    - The owner's own asset (the toast) is faithful to the reference and animated with care.
    - The emblem is the real emblem, shape-checked against the source.
- **Weak:**
  - **The owner's view:** three rounds instead of the target two.
    - Round 2 was mostly a change of direction (a new focal point and asset), plus two defects: the bolt shape, and the print's repetition, which v13 rule 1 already covered.
    - Round 3 was a taste call: physics against readability.
  - **The studio's view:**
    - The S1 pack (1.1 Mb/s) is the softest source; the emblem shot measures SOFT (0.86×).
    - The wake's rise is a fast, motion-blurred source shot played at 0.76×.

## 6. Measured results (round 3, the delivered encode)
| Check | Result |
|---|---|
| QC checkpoint | 12/12 PASS |
| Loudness after AAC | −13.9 LUFS / −4.7 dBTP |
| Loop seam (blurred diff; target ≤ 1) | 0.13; audio seam step 0.039; picture wrap step 0.4 against a local median of 1.89 |
| Flashes (white-out runs, max per second) | none; 1 event, at most 1 a second |
| Softest shots (`tools/sharpness.py`) | emblem 0.86× (SOFT, the S1 pack); the lensball's background 0.82× (defocused by design) |
| Motion | dead spans 0, judder 0. Of the 3 unexplained pops, 2 are the loop's designed light flickers and 1 is a source burst (22–32 grey levels per source frame) |
| Transitions | 14 + the loop. Longest hold: the lensball (3.4 s, with designed turns on each note) |
| Effort | rev 1 about 1.5 h, rev 2 about 2.5 h, round 3 about 15 min. 6 full renders in 3 rounds; QC 20 min in all |

## 7. New rules (adopt in both studios)
1. **Match the style to the song. A calm, nostalgic song gets a calm edit, and that can be a standard.** Use:
   - fewer, slower designed transitions on the song's structure;
   - a camera that breathes instead of punching;
   - five or so quiet effects;
   - a warm faded grade with a low overlay.

   v10–v12 remain the energetic reference; don't force their density or beat camera onto a slow song.
   - **Evidence:** "this edit is a different style from the flash edits we normally create but is still really good" (v14 verdict).
   - **Applies to:** all edits.
2. **Build an asset the owner supplies as a reference faithfully, in our own drawing, with a designed animation.** Match the layout, colours and type, draw it from code (no copied game or show assets), give it a satisfying pop, and keep it readable (~2 s), under the face and clear of the platform UI.
   - **Evidence:** the round-2 toast request, approved.
   - **Applies to:** all edits.
3. **Verify a real symbol's shape on the source before drawing it, and never reflect or mirror a subject the frame cuts off.** Trace the emblem or prop as a polygon on 2–3 source frames. Draw the missing part (or inpaint, then extend). `BORDER_REFLECT` on a push is only for texture.
   - **Evidence:** "the flash symbol on the crest is not an actual lightning bolt and is in the wrong shape" (rev 1 mirrored the cut-off S1 emblem).
   - **Applies to:** all edits (the Dexter equivalent is a badge, a slide or a knife).
4. **A transition the owner likes is used once, and fast.** Don't build a motif out of repeating the same move. Different moves around one object are fine (v13 rule 1), the same move four times is not, and a graphic should be readable in ~0.4–1 s, not 2.
   - **Evidence:** "i really like the transition but I don't like that it is too slow and repeats multiple times".
   - **Applies to:** all edits.
5. **An emblem transition gets about 2 s and visible stages:** push in, light the shape itself, energy on it, open it.
   - **Evidence:** "the emblem transition is too fast ... slow it down and make it more pronounced" (0.5 → 2.1 s, approved).
   - **Applies to:** Flash (it refines v12 and v13 rule 2); Dexter's symbol transitions likewise.
6. **Keep faces and memories upright inside graphics, even when the physics would invert them** (a ball lens, a reflection, a drop).
   - **Evidence:** round 3: "face upright so that Barry's face is facing upwards".
   - **Applies to:** all edits.
7. **When the owner names the moment, it opens the edit as a set piece.** Get the face in frame within about 0.3 s. Never open on a long empty or dark frame, even for a loop.
   - **Evidence:** "I want barry waking up for the first time to be the focal point of and in the beginning of the edit"; the critique's "too dark and blurry" first second.
   - **Applies to:** all edits.
8. **Confirmed:**
   - lean sound: 5 placed effects in 26 s was approved, below the v13 guide of 10–12 for a calm song;
   - a low overlay that is still readable at phone size: grain clumps ~4 px, dust 2–5 px, edge leaks;
   - the fresh-eyes critique before every delivery. It caught the lensball's box, the near-black loop and the face crawl in rev 2, none of which the studio had seen.

## 8. Reusable assets
| Technique / transition | Where the code is | How to restyle it for another show |
|---|---|---|
| **THE LENSBALL** (`lens_ball`, `ball_fx`, `lens_entry`, `lens_in`, `lens_dive`): a per-pixel glass ball that holds any image. It has barrel squeeze, rim dispersion, a Fresnel edge mirroring the room, highlights and a halo. It turns between images with a strip scroll, and enters and dives with an exact identity at both ends | `v14/work/sec14.py` (THE LENSBALL) | Any memory or vision device: a crystal ball, a snow globe, a bubble. Set `phi` 0 for upright. Centre each image's face with `BALL_CC` (YuNet on the content) |
| **THE ACHIEVEMENT** (`toast_draw`, `toast_sprite`, `put_text`, `GLY`, `crate_icon`): a pixel-UI toast with our own 5×7 font, spring pop, letter hops, stepped shine and glow | `v14/work/sec14.py` (THE ACHIEVEMENT) | Any on-screen UI pop-up: change the strings, the colours and the icon map. Add glyphs to `GLY` |
| **The traced emblem** (`emblem_draw`, `emb_canvas`, `EMB_BOLT`, `EMB_TRACK`): a lit, bevelled emblem drawn exactly over the real one, with the bolt lit along its length, a ring light, an opening portal, and a suit extension for a cut-off emblem | `v14/work/sec14.py` (EMBLEM GLINT), `v14/work/edl14.py` (polygon and track) | Other suits or badges: trace the polygon on the source (the overlay check is in the handoff's process), then template-track the centre |
| **EMBLEM GLINT** (2.1 s): push, glint, ring light, `emb_arcs` gold lightning, portal, fly through | `v14/work/sec14.py` | Keep the stages; recolour the light |
| **THE LIGHTS loop** (`lights_on`, `dim`, `loop_lights`): the room's lights flicker on at frame 0 and out at the end, with the room flashing through; the screens keep glowing | `v14/work/sec14.py` | Any loop that starts in a room: a lamp, a neon sign, a police light |
| **PRINT DIVE** (fast) and the instant-film print (`print_card`, `develop`, `dive`) | `v14/work/sec14.py` | Once per edit, about 0.4 s |
| **SUNFADE grade + SUPER 8 HAZE** (`grade`, `finish14`, `edge_leaks`, `dust`, `coarse_grain`, `gate_mask`) | `v14/work/sec14.py` | A nostalgic look that keeps the clips clear |

## 9. For the other studio
- **Adopt rules 1–7.** For Dexter:
  - Rule 3 is the badge, the slide box or the Code's symbols: trace them on the source.
  - Rule 6 matters for any reflection or water transition with a face in it.
- **The scaffold:** we did **not** change `tools/new_edit.py`. Proposal, for the owner to decide and for a DEV handoff if they say yes: add `--base v14` as the "calm/nostalgic" template, with v12 still the Flash default.
- **To try:** the lensball as a Dexter memory device (the Gulf Stream in a glass ball?); the toast drawn in a Dexter-world style if the owner ever sends a UI reference.
- **Technical notes:**
  - `splice_section.py --replace` finds a section by its first line. When we edited our section's header line, it inserted a second copy and left the old one above it. Delete the old block, or keep the header line fixed.
  - Change tracking re-rendered everything for small edits in `sec14.py` this time ("the changes reach 100 % of the frames"), because `prefinish` or `render` reach the edited functions on every frame. That is worth a look in the render-speed update (WP2b).
