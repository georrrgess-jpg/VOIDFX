// The owner's craft, translated into this studio's tools: the TikTok editing guide's recipes, every
// approved set piece from the voidfx archive (v4-v11, Studio 2) rebuilt from studio operations, and
// how to work fast. Opus reads the CRAFT and COOKBOOK on every planning call; the worked examples of the
// approved edits (exemplars.ts) go with the direction and the critic.

export const CRAFT = `CRAFT (the owner's TikTok editing guide, with the numbers that work)
- Hook first: a readable face, eyes or the subject within 0.5 s; something hits within the first second. Viewers decide in about a second.
- Edit to the music's structure, not a fixed rate: holds in the build, impact on the drop, rhythm in the montage (base unit 2 beats, a few 1-beat accents, one 4-beat hero hold), holds again in breaks. In quiet breaks hold longer; don't fill silence with cuts.
- Peak alignment: an effect feels on the beat when its PEAK lands on the accent, not its start. Place a whoosh so its peak is on the cut, a slam so it lands on the downbeat, a wash so its brightest frame is the drop.
- Motivated transitions: a circle wipe grows from a real light (iris with "at" on the lamp/sun, "to" on the next face), a whip keeps the face in the same place across the cut (focus both shots), a glitch match cut lands on an eye-aligned shot.
- Contrast creates story: pair opposites (smile -> cold stare, calm hands -> tense gloving, day -> night).
- Consistency of look, variety of content: one grade (a look over the whole edit), varied scale, action and place.
- Fewer, better effects: every effect must connect shots, mark the drop or sell motion. A handful of excellent transitions beats constant flashes.
- Recipes (60 fps): exposure wash on the drop = fx exposure_wash 0.45 s with its peak on the drop (or transition wash), face readable again within ~0.2 s, never white text on the white peak · whip = whip_<dir> 0.3-0.4 s in the subject's direction, faces matched · circle reveal = iris with at/to · monochrome glitch match cut = glitch 0.35 s onto an eye-aligned shot · zoom punch 105-110% eased back over 6-10 frames (the beat camera does this) · shake 0.5-1.5% with a 80-150 ms decay, only on 1-3 major hits (fx shake onbeat 0, 0.2-0.4 s) · flash 2-4 frames, never repeated strobing · push-in 3-6% over a held shot (kf scale) · speed ramp into a cut (ramp, or speed keys 1 -> 2.3) · the hard cut is often the strongest move for the final hero image.`;

export const COOKBOOK = `PLAYBOOK: THE APPROVED SET PIECES, BUILT FROM STUDIO OPERATIONS
Each line: the move (edit, verdict) -> how to build it here. Anchors are frame coordinates (0..1 from the top-left). "Overlay" means a clip on a video track above the main track. Combine with your own shaders/graphics when a move needs a shape no preset has; recipes are starting points, not ceilings. Keep every prop motivated, brief, lit and off the face.

DEXTER
- Dive into the eye (v4 eye portal, v6 eye dive, v11 red eye dive; approved): transition {"type":"dive","dur":0.8,"at":{eye on the outgoing},"to":{eye on the incoming}}; focus both shots on the eyes first so the anchors are known (~(0.5,0.4)). Sound: whoosh + subdrop. It is also the loop: dive into his eye at the end.
- Pupil to iris loop (v4, v7; approved): the last 0.6-0.9 s of the last shot pushes into the eye (kf scale 1 -> 2.2, focus on the eye) under fx aperture mode 1 (closing to black on the eye, ending exactly at the edit's end); frame 0: fx aperture mode 0 on the first shot's eye over 0.4-0.6 s. Black to black: the seam is invisible. Sound: a hit (heartbeat) under the close, nothing on frame 0.
- Magnifying glass open (v7 open; approved): frame 0 = fx aperture mode 0 (shape 0) on his eye as a lens opening, plus a thin lens-rim graphic (SVG ring with a metallic linear gradient, glow 0.3) riding the frame for the first 1-2 s.
- Blood-slide box on a sung word (v7 CLOSE; approved, replaced plain doors): a rosewood lid graphic (SVG: warm wood linear gradients + a few grain paths, brass corners and a brass plate) drops from the top over 11 frames (kf y -0.7 -> 0, ease "in"), slams on the word (fx shake 0.25 s, fx dust 0.5 s at the seam), the word engraves on the plate (text "CLOSE", anim.in "stamp", color #3a2412, emphColor #d19438, small, on the plate's position), then the lid lifts and the camera dives into a blood drop on a slide (transition dive at the drop). Sound: impact on the slam, hit, shutter (latch).
- Plastic sheet to plastic burst on the drop (v7 hero; approved): 0.5-1 s before the drop the shot is behind kill-room plastic (fx plastic_wrap held, or your own shader: milky refraction + a few soft folds; with the hook title revealed on it in UV blue #6bccff by anim "sweep"); the plastic bulges toward the camera (kf scale 1 -> 1.08 on the shot, centre-weighted shader optional); on the drop: transition tear or shatter at the centre + fx shockwave + fx sparks_burst (color #9a0010, fast) + a 2-frame fx impact_frame. Sound: riser into it, rip + impact on the drop.
- Blood on the lens (v7; approved): fx blood_lens over the cut, anchor off his face (a top corner or the lower third), size 1-1.4, 1.2-1.6 s, clear 0.5; the next shot is seen through it as it runs. Sound: hit + rip (squelch) at the splat.
- Body-bag zipper (v7; approved): your own shader over the cut: a black bag closes over the frame along a zip line that travels top -> bottom (opening half-width proportional to the distance from the slider, teeth as a dotted edge, frame() visible in the opening), then reopens on the next shot. Sound: rip twice (zip rasps) + hit.
- M99 sedative blink (v7; liked again later): transition blink 0.7-0.9 s. Sound: hit (heartbeat) x2 at low volume.
- UV luminol sweep (v7): fx luminol 1 s on a dark scene + fx light_sweep (tint #6bccff) as the blacklight passing; hidden traces glow in its wake. Title in luminol blue with anim.in "sweep".
- Evidence markers (v7): small yellow (#facc0d) tent graphics with numbers dropping in on three beats (reveal pop, kf y -0.1 -> 0 with a small bounce) at the bottom of the frame, clear of faces. Sound: tick each.
- CASE CLOSED stamp (v7 ending; approved): text "CASE\\n*CLOSED*" anim.in "stamp", emphColor #c70f14, rotation 7, plus a double-border graphic (two rounded rects, stroke #c70f14) with the same rotation and the same stamp timing; fx shake 0.2 s. Sound: impact.
- Crime-scene tape snaps (v7): a yellow tape graphic (#facc0d band with black blocks) crosses at -14 degrees, then two halves fly apart (two graphics, kf rotation +35/-40, x +-0.9) as the shot pushes 8%. Sound: rip.
- "Darling," freeze into the falling blood drop, blooming in water on the drop (v8 hero; liked): on the word: freeze (speed keys to 0.05) + fx freeze (drain 0.9, rim #ffb060) + the word in blood red with anim.in "sweep" (a write-on); the drop: fx blood_lens anchored just under the word, timed so its splat lands on the drop (its first 14% is the fall, refracting the frame); on the drop transition ink (the blood blooms open) + fx shockwave (rim #ff2b33). Sound: hit (heartbeat) during the fall, subdrop/boom on the drop.
- Rear-view mirror open and loop (v8; liked): the first shot sits inside a rounded mirror graphic (dark car interior frame with a chrome edge, glow 0.2) while fx rain_glass and fx bokeh run behind; the shot pushes in to full frame (kf scale 0.55 -> 1, x/y onto the mirror) over ~1 s; the loop pulls back into the same mirror.
- The "basic" moves the owner liked (v8): streetlight sweep = transition light_sweep; windscreen wiper = transition wiper; whip pans along his gaze = whip_<dir>; plastic wrap = fx plastic_wrap centred on the cut; impact negative = transition punch or fx impact_frame; rain focus pull = fx rain_glass over the cut (opacity kf 0 -> 1 -> 0, the cut at full coverage); lamp switching on = fx spotlight with opacity kf flicker (0, 0.6, 0.1, 0.9, 1 over 0.25 s) + sound tick; one cut per syllable on the hook (0.2-0.3 s each, a slam per word).
- Barrel to scope (v4; approved): dive into the gun barrel's muzzle (at = muzzle) to black, then fx aperture mode 0 opens a round scope view on the next shot with a vignette; keep any reticle thin and off-centre (no target ring on his face).
- Gunshot glass shatter (v4 drop; approved): transition shatter at the muzzle flash or the impact point (never on his face), on the gunshot beat; the hook title rides into it and exits with "blowaway" (motif glass) exactly on the shatter. Sound: impact + glass.
- Knife slash (v4, v6; approved): transition slash (+ fx light_sweep tint white 0.2 s as the glint just before). Sound: swish + hit.
- Polaroid toss (v4, v6): at the cut, a 0.6-0.8 s copy of the outgoing shot's last moment (speed 0.05) on an overlay track above the incoming: kf scale 1 -> 0.62, rotation 0 -> -31, x 0 -> -1.3 (ease "in"), a white print-border graphic riding with the same keyframes, fx exposure_wash (0.15 s) as the camera flash at its start. Sound: shutter + whoosh.
- Through the photo on the wall (v4, v7 evidence board): dive with at = the photo; the next shot emerges from it.
- CRT fly-through on the drop (v6 hero; approved): the outgoing shot's last ~0.9 s becomes a TV picture: fx crt (curve 0.7) + kf scale 1 -> 0.6 over a background (a duotone gradient graphic or another shot on the track below); then transition dive (at = the screen centre) exactly on the drop + fx speed_streaks + fx exposure_wash. Sound: riser over the shrink, impact on the dive.
- Finger-gun to CRT power-off/on (v6; approved): fx sparks_burst at the fingertip (muzzle flash) then fx tv_off mode 0 (0.3 s) on the outgoing and fx tv_off mode 1 (0.3 s) on the incoming. Sound: impact (shot), glitch (power off).
- Cube over the world (v6; approved): transition cube_left/right/up/down 0.6 s. Sound: whoosh + hit (landing).
- Film burn / shadow pass (v6): transitions burn and shadow.
- Vanish into pixels on "disappear" (v6; approved): fx glitch (amount 0.8) + transition pixelate onto the next shot; caption exits "blowaway" (motif ash).
- Neon words IT / WAS / ME. (v6 ending; approved): text anim.in "flicker" per spoken word, colours cyan #4de6ff / pink #ff5cb8, emphGlow 0.9, plus fx neon_spill (same colour) on the side of his face the sign is on.
- Tape load / rewind loop (v6; approved): frame 0 = fx static mode 0 (0.6-0.7 s); the end = a fast reverse (speed keys negative are not supported: use a short shot played fast, or the vhs look) into fx static mode 1 over the last 0.5 s. Sound: glitch at both ends.
- Knockout BAY HARBOR BUTCHER (v4; approved): a big three-word stack mid-frame in style.knockout true (size 0.085-0.11, fit, knockDark 0.82), anim.in "slam" with each word on its spoken syllable, anim.out "zoom" (flies past the camera). Sound: hit per word.
- BLEED IT blood fill (v4): the title in white with anim.in "bloom" on a single line marked emphasis so it floods red from the bottom, then it rides into the shatter.
- Kill-room light, the Dark Passenger's shadow: fx spotlight (anchor at the top, dark 0.7) + fx dust; transition shadow for the darkness swallowing the frame.

THE FLASH
- Emblem dive + drop wave (v10 drop; approved): dive with at = the chest emblem (to = centre), fx lightning_arc on the emblem 0.4 s before, fx shockwave (amount 0.9, rim #ffd27a) + fx light_rays on the incoming. The pre-drop words ride into the dive.
- Lens shatter (v10; approved): fx lightning_arc thrown toward the lens, then transition shatter where it hits + fx sparks_burst. Sound: zap + glass + impact.
- Time stops in the stutter (v10; approved): speed keys to 0.05 + fx freeze (rim #ffc74d, drain 0.8) + fx embers hanging (speed 0.3) + fx pulse only on the music's hits; restart with fx shockwave.
- THE RIFT (v11 focal; approved): your own shader: a jagged tear opens across the frame below his face with electric white-gold edges and the Speed Force churning inside, then the camera flies through (transition dive at the tear's centre) and the next shot rushes out. Or: fx speed_force + transition tear + fx edge_pulse gold. Sound: rip + subdrop + boom.
- Bolt split (v11 drop; approved): transition bolt on the drop (with zap), the left/right grades split by two looks or your own shader.
- Beat moments for shots that only move to the beat (v11; approved): AURA = fx edge_pulse in the edit's colour; REMNANTS = fx remnants; CHARGE = fx lightning_arc + fx embers drawn in toward the chest.
- Phase / whirlwind / speed slices / heat haze / clash (v10-v11): fx remnants + glitch over the cut / transition swirl / transition slices / transition heat / two lightning_arc effects from opposite sides + fx shockwave + fx impact_frame.
- Coin flip of the emblem (v11 loop; approved): transition flip_h between the emblem close-up and the rival's, + fx lens_flare at the edge-on moment.
- AROUND ring into the Speed Force, back to frame 0 (v10 loop; approved): fx speed_force + speed_streaks over the last second, then dive into the centre, landing on frame 0's picture (the first shot's first frame).

ANY SHOW
- Window/letterbox reveal opening (guide): frame 0 opens as a horizontal band centred on the face (your own shader, ~1 s, ease out) or fx aperture mode 0.
- Exposure wash on the drop (guide): fx exposure_wash, peak on the drop.
- A beat-synced light: fx light_rays with beat 0.5 from the real light behind him; fx lens_flare on a practical light.
- Depth graphics in every section (v6 approved): fx bokeh, dust, embers, ash, rain, fog, neon_spill, spotlight, chosen to fit the look and the scene.`;

export const EFFICIENT = `WORKING FAST WITHOUT CUTTING CORNERS
- Spend your thinking on the creative decisions: concept, song window, shot choice and order, set pieces, titles, the loop. The studio does the mechanics for you: it snaps cuts onto beats, fits velocity ramps to the source, places lyric captions on their sung times, keeps faces framed from "focus", thins sound effects, keeps text and effects on the right tracks, grades everything under the text, and checks the result.
- Use library looks and effects by name with a few parameters (the "look" and "fx" operations): they are tested and cost a line each. Write your own shader or SVG only for the signature moments no preset covers.
- Write compact JSON: omit fields that keep their defaults, no indentation, no comments.
- Use the pack notes: when the studio recognises a scene pack, it lists the proven shots with their timecodes, the dialogue lines and what to avoid. Start from them instead of searching every contact sheet.
- Decide once: write the direction completely (every shot, transition, title, effect and sound with its time), then build it exactly.`;

/** Where the knowledge comes from (shown on the knowledge page). */
export const KNOWLEDGE_SOURCES: { name: string; what: string }[] = [
  { name: 'CLAUDE.md (the binding rules)', what: 'benchmarks, every owner preference, the v9 text standard, the v10/v11 standards, props and sharpness rules' },
  { name: 'Studio handbook (VOIDFX_STUDIO.md)', what: 'likes with evidence, the rejected list, craft lessons, the pre-build gate, the style bank, songs used' },
  { name: 'Studio spec and handoff', what: 'what earns approval and what draws notes, per-edit lessons, the pipeline, quality gates' },
  { name: 'preferences.json and edits.json', what: 'every threshold, banned item and benchmark; all 16 edits with verdicts, quotes and lessons' },
  { name: 'Toolkit (TOOLKIT.md)', what: 'the 90-transition catalogue, graphics, pitfalls, what made v6/v10/v11 the standard' },
  { name: 'Scene packs (SCENE_PACKS.md)', what: 'every pack with quality, proven shots, timecodes, dialogue lines and what to avoid; every song with its tempo and drop' },
  { name: 'TikTok editing guide', what: 'hook, structure, rhythm, effect recipes with numbers, loops, colour and QC methods' },
  { name: 'Edit archive v2-v11 (READMEs, EDLs, renderers)', what: 'set pieces stage by stage, beat-by-beat breakdowns of the approved edits, grade and text algorithms' },
];
