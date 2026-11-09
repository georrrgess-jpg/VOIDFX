# HANDOFF: v15 OUT OF TIME (The Flash × Eyedress "Jealous"): STANDARD

**From:** the Flash studio · **Date:** 2026-11-09 · **Revisions:** 3 owner rounds (first delivery, round 2, a one-note round 3) · **Folder / branch:** `v15/` on `claude/gallant-planck-pqpczp`

## 1. Verdict, in the owner's words
> "I like this edit, make it a standard."

- **Status:** standard. The newest energetic Flash standard, after v12 BLOOM. It is the reference for:
  - **a time concept carried by set pieces on the song's structure:** the drum break freezes as bullet time; the return discharges it;
  - **a signature emblem transition built from the real emblem's own bolt:** EMBLEM CLOCK;
  - **custom transitions motivated by each pair of shots:** 14 new ones;
  - **a loop that flies down a corridor of the edit's own memories into frame 0:** seam 0.13.
- **Engine base:** unchanged. New Flash edits still scaffold from v12, and v15's pieces port from `v15/work/sec15.py` (§8).
- **The brief:** "make a flash edit using the song above. I want you to try to follow the beat in this and make a really
  amazing edit. Try to make this the best flash edit you've ever made. Use custom graphics, animations, transitions etc."
- **Gripes on the way (all fixed):**
  - **Round 2:** the freeze frame, *"blank space"*, and *"the loop isn't particularly seamless"*.
  - **Round 3:** the particle break-up of his face.

## 2. The edit at a glance
| | |
|---|---|
| Song / window | Eyedress "Jealous", 56.84–82.64 s (half-beats h176–h256, P = 0.32256 s, 93.0 BPM, grid fitted on the Demucs drum stem). Chosen for the song's one structural moment: the drums-only break bar at 67.2 s and the band's return, wrapped in the "I don't got time" run and "Do whatever you want … I don't really want to know" |
| Length / format | 25.80 s, 1080×1920, 60 fps |
| Concept | **OUT OF TIME**: the fastest man alive never has time. "I don't got time" = the watch, the call, the run. The drum break = time stops at the moment it all began (the S1 lab strike, his palm against the bolt). The return = the frozen lightning discharges into his eyes. "Do whatever you want, I don't care" = the jealousy he says he doesn't feel (Iris living her life, seen inside his eye; he turns away and runs; the wind of it in her hair). The loop rewinds through the edit to its first frame |
| Look | VIOLET HOUR: lifted violet shadows, peach-gold highlights, the suit's red kept rich, skin protected. A soft dream bloom, a violet haze in the darks, a faint lens fringe, fine grain. The freeze has its own grade: a cold steel room under molten-gold bolts |
| Structure | The "I don't got time" run (e0–28, a cut on every kick of the groove) → the strike slows (e28–32) → **TIME STOPS** (e32–40, the break) → **TIME RESTARTS** (e40, the return) → Iris / the turn-away / the wind (e42.5–58.5) → **EMBLEM CLOCK** (e58.5–66.5) → the run to the end → **REWIND** (e76–80) into frame 0 |
| Set pieces | **TIME STOPS** (bullet time on the hit: depth layers, the camera stepping on the nine kicks of the drum fill, god rays, rim light, a few hanging drops, the bolts trembling at the end). **TIME RESTARTS** (the bolts discharge, the moment is pulled into the strike, his eyes come out of it, the colour floods back). **EMBLEM CLOCK** (the signature: the real S5 bolt lifted off the disc and wound like a clock hand, twelve gold marks, a clock-wipe sweep). **REWIND** (the loop) |
| Transitions | 28 and the loop in 25.8 s (1.09/s); generic connectors 2 of 28. **New, custom:** VIBRATE, PHONE FLARE, STREAK PASS, STRIKE CUT, TIME STOPS, TIME RESTARTS, TURN AWAY, DUST CLOUD, EMBLEM CLOCK, PENDULUM, FREEFALL, IGNITION, WIND GUST, REWIND. **Ported from v13:** eye iris, time slice, edge current, light leak, speed whip, whip up, focus rack, afterimage. **Library:** light streak, ramp, bolt split, arc link, whip, dolly. **Eight in-shot animations:** suit current, streetlight flares, time remnants, warm bokeh, the urge (lightning gathering on him), wind grit, the shout, embers |
| Text | None |
| Sound | The song straight and circular, plus **nine quiet effects**, none on beats: a phone buzz, a whoosh, the strike's crack, an air-suck into the freeze, an impact and sub drop on the restart, a gust, the emblem clock's watch-crown ratchet, the ignition, and a reversed whoosh into the wrap |

## 3. Creative process
- **Window:** the song map found no drops (steady lo-fi energy), so the whole song was prepped. The bar-energy profile
  showed one structural moment, the drum break, and the window was built around it. The concept came from the hook ("I
  don't got time") and the break: time running out, stopping and restarting.
- **The hero is time itself, as a motif in 4 transitions:**
  - the frozen strike;
  - the restart;
  - the emblem as a clock;
  - the loop's rewind.
- **The watch dive was dropped:** the watch sits outside the 9:16 crop. The emblem clock became the signature instead,
  with the real S5 emblem as the timepiece.
- **Every cut sits on a kick** of the groove (strong kicks on e0, 2.5, 4 and 6.5 of each bar; soft on 1 and 5). In the
  break, the camera steps on the drum fill's nine kicks.
- **A fresh-eyes critique ran before each delivery.** Before the first, it predicted the owner's notes:
  - the two Iris shots read as one clip;
  - the loop was "low effort";
  - the emblem's bolt was wrong;
  - effects crossed faces.

  All of it was fixed before the owner saw it.

## 4. Revision history
- **First delivery (after the critique pass):**
  - **Shots:** Iris from S4 (the S1 pair read as one clip), and the fire flight from S4 (in place of a look-alike masked shot).
  - **Cuts:** every cut after the return moved onto a kick.
  - **EMBLEM CLOCK:** the bolt traced as a polygon on the source. Cutting it out by colour had missed its pale faces, which left a ghost bolt on the disc.
  - **TIME RESTARTS:** rebuilt without a ring.
  - **New:** TURN AWAY and PENDULUM, plus a first loop.
- **Round 2, the owner (verbatim):** *"The first thing I'd like to change is to the Freeze frame. I want you to see if there's any other freeze frame shots that could be better selected ... emphasize it more and make the scene a little bit cooler. Next, I would like for you to add more custom graphics, animations, and transitions ... some scenes where there's blank space or just room for improvement ... at the end, the loop isn't particularly seamless ... make it more visually appealing and detailed."*
  - **Diagnosis:**
    - The freeze sat on his upward look; the stronger instant is the hit itself, his palm open against the bolt.
    - The freeze was a flat 2D hold.
    - Several shots played plain for a second.
    - The loop's destination came from behind the camera as a huge, blurry card that faded in.
  - **Change:**
    - **The freeze:** frozen on `fbh` 12.017 s (a real 24p frame) as layered bullet time. The strike now pans and pushes into the same framing.
    - **New transitions:** PHONE FLARE (a new cut onto the night city), DUST CLOUD and FREEFALL (in place of generic moves).
    - **In-shot animations:** eight, each motivated by its shot and kept off faces.
    - **The loop:** REWIND rebuilt as a fly-forward corridor. Frame 0 is visible at the far end the whole way and grows to fill the screen.
  - **Tried and failed on the way:**
    - **The freeze:**
      - YuNet took his open palm for the largest face and centred the crop on the hand; it is now framed by hand with a face hint.
      - 12.04 s fell between two 24p frames, so interpolation ghosted the palm.
      - The strike ended at a different zoom and pivot than the freeze (a ghost at the time stop).
      - The first grade was flat grey with white bolts.
      - 18 big refractive drops read like a droplet filter (v108's rejection); four remain.
    - **The loop:**
      - The first corridor had stepped zoom-blur combs on faces and floated in an empty void.
      - A second time-stop at the end repeated the freeze idea.
    - **The animations:**
      - The first pass was too subtle to notice.
      - The urge's arcs were removed by the face mask until arcs were born only below the chin.
      - The dust read as a flat sand wall, then popped in 4 frames.
- **Round 3, the owner (verbatim):** *"[the 23] Second mark, where [Barry] kind of like breaks down into many pieces. I'd like you to change that into another transition. Next, I would like for you to add a focal point graphic to the transition. This could be a custom transition or a custom graphic. The really, really smooth animation. Just try to make it smooth and complete this update with efficiency."*
  - **Diagnosis:** TIME PARTICLES (v10's approved replacement for glass) takes his face apart into noise mid-way.
  - **Change:** **IGNITION**:
    - in the cold close-up one ember catches on his shoulder, glows and pulses on the kick (the focal point);
    - it burns the frame open onto the real fire of the next shot, with a white-hot front, a scorched rim and embers on smooth analytic paths;
    - the face passes under one soft warm edge;
    - it has one quiet whoosh.
  - **Tried and failed on the way:**
    - A face bias on an extreme close-up stalled the burn, then swept it across the face at once.
    - A noisy bias opened fire holes in his face (too close to the break-up the owner had just removed).
    - An oval protection read as a cut-out.

    The answer: no grain inside the face, one soft edge, no scorch or white line on a face, and a warm flash for the last of it.

## 5. What made it good / what made it weak
- **Good (the owner: "I like this edit"; "I like this art for the most part ... I like the overall flow"):**
  - one concept (time) carried by four set pieces placed on the song's only structural moments;
  - a cut on every kick;
  - transitions motivated by each pair of shots: the phone's light, his departure turning the frame away, the dust of his run, the pendulum as a clock, the drop off the roof, the ember catching into the fire;
  - a signature built from the real emblem;
  - a loop that lands on frame 0's own moving picture.
- **Weak, measured:**
  - Two shots keep their source cadence, so they may look slightly stuttery: the S4 city run (stutter-cut in the source) and the S5 run (it flickers in the source).
  - The embers in the fire flight barely read against the bright fire.
  - Density is 1.09/s, against v108's ≥ 1.1/s target.

## 6. Measured results
| Check | Result |
|---|---|
| QC checkpoint | 11/11 on the encode |
| Loudness after AAC | −13.0 LUFS / −4.5 dBTP |
| Loop seam (blurred diff; target ≤ 1) | **0.13**; the step across the wrap is 0.78, against 1.89 for the frames around it |
| Flashes (white-out runs, max per second) | none, 0 |
| Dead spans | none (round 1 had the 2D freeze) |
| Motion audit | every pop is a cut, a beat, the hold cadence or a designed move: the bullet-time steps on the fill kicks, the dust front. None inside IGNITION |
| Transitions / density | 28 and the loop in 25.8 s (1.09/s), 8 in-shot animations, generic 2/28, the hero in 4 |
| Effort | 6 full renders over 3 rounds (47.5 min of video); QC 21 min. Round 3 needed 1 render: a new TR2 registration re-renders every frame (WP2b) |

## 7. New rules (adopt in both studios)
1. **Freeze on the hit, and freeze a real frame.**
   - Choose the instant of most action (contact, the hand up against the bolt), not the moment before.
   - On 24p content in a 60p file, freeze on a unique source frame (`UNIQ`), never an interpolated one.
   - Run the shot before the freeze into the same framing (crop, zoom and pivot), so time stops without a jump.

   Evidence: round 2, *"see if there's any other freeze frame shots that could be better selected ... emphasize it more and make the scene a little bit cooler"*, then approval. Applies to: all edits.
2. **"Emphasize a still" means taking it apart in depth, not overlays on a flat frame.**
   - Plate, subject and light layers, and a camera that moves between them on the beat (bullet time).
   - Light from the scene's own source (rays behind the matte, a rim).
   - A few physical particles, never a lens-drop field (v108).

   Evidence: round 2, then approval. Applies to: all edits.
3. **"Blank space" is filled two ways at once:**
   - new cuts with motivated custom transitions;
   - a visible in-shot animation in each remaining plain hold, motivated by the shot (light from its lights, its fire's embers, its wind's grit, lightning gathering when he's about to run), off faces, and big enough to read at phone size. The first, subtle pass would not have answered the note.

   Evidence: round 2, *"some scenes where there's blank space or just room for improvement"*. Applies to: all edits.
4. **A seamless loop shows its destination early.**
   - Frame 0 visible at the end of a corridor or tunnel the whole way, growing to fill the frame on a smooth landing.
   - The surround becomes frame 0's own blurred light, so no margin reads.
   - Never a giant card fading in from behind the camera, and no second time-stop (a repeat).

   Evidence: round 2, *"the loop isn't particularly seamless ... more visually appealing and detailed"*, then approval (seam 0.13). Applies to: all edits.
5. **Never take a face apart.** No particle dissolve of a face, no fire holes in a face. A burn or cover passes a face as one soft edge, with no scorch, line or particles on it.
   - `time_particles` is now `caution` in the registry, with the owner's words.

   Evidence: round 3, *"where [Barry] kind of like breaks down into many pieces ... change that into another transition"*. Applies to: all edits.
6. **When the owner asks for "a focal point" in a transition, give it one small, bright, motivated thing to look at** (an ember, a light) that grows into the move, with every part a smooth function of time: fixed noise, eased fronts, analytic particle paths, no per-frame randomness. Evidence: round 3, *"a focal point graphic ... The really, really smooth animation"*, then *"I like this edit"*. Applies to: all edits.
7. **Technical, confirmed:**
   - YuNet can take an open palm for the largest face: check tracks on frames with hands, and use `face=None`, `cx` and a face hint;
   - flow on a source that flickers frame to frame ghosts, so hold its cadence;
   - a stylized stutter-cut source plays straight (`interp="hold"`);
   - a new TR2 registration re-renders every frame (WP2b);
   - the writable disk allowance fills up, so clean the frame cache at each verdict.

## 8. Reusable assets
| Technique / transition | Where the code is | How to restyle it for another show |
|---|---|---|
| EMBLEM CLOCK (`emblem_clock`, `bolt_lift`, `ec_theta`) | `v15/work/sec15.py` | Trace any symbol as a polygon on the source (`EMB15_BOLT`), lift it off its disc (fill from the disc's own colour), wind it with rotational blur; Dexter: a watch hand, a knife on a turntable |
| Bullet-time still (`still_layers`, `still_cam`, `still_fx`, `lens_drop`) | `v15/work/sec15.py` | Any frozen moment: plate, subject matte and light layers, steps on the beat, rays from the light source, a few lens drops |
| REWIND corridor loop (`loop_out`, `rew_quad`, `rew_card`) | `v15/work/sec15.py` | Memory cards in perspective along the walls, frame 0 at the end growing to fill; swap the thread and spark colours |
| IGNITION (`ignition`) | `v15/work/sec15.py` | A focal ember burning the frame open onto the next shot; any source of fire or light; the face handling is general |
| TURN AWAY, PENDULUM, FREEFALL, PHONE FLARE, DUST CLOUD | `v15/work/sec15.py` | Kinetic, physical moves with exact ends (`/(pre+post-1)`), generic to any show |
| In-shot animations (`ANIMS`: bokeh, urge, grit, shout, embers, flares, current, remnants; `off_face`, `body_only`) | `v15/work/sec15.py` | Add `anim=` to a shot; each is kept off the face, and arcs start below the chin |

## 9. For the other studio
- Rules 1–6 apply to Dexter edits as they are. Rule 5's Dexter form: no blood or plastic "eating" a face; a cover passes it as one soft edge.
- The bullet-time still and the corridor loop are show-agnostic. A Dexter version could freeze a kill-room moment on the hit, or run a corridor of kill-room memories.
- The registry now carries v15's verdicts (14 new liked, 8 ported ok) and `time_particles` → caution.
