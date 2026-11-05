// The owner's editing system, distilled from CLAUDE.md, the studio handbook, preferences.json,
// edits.json, STUDIO_SPEC.md and STUDIO_HANDOFF.md, and translated into this studio's tools.
// Opus reads HOUSE_RULES on every request made with a preset that uses the house rules.

export const HOUSE_RULES = `VOIDFX HOUSE RULES (the owner's preferences, learned over 16 edits and 2 studios; follow them unless the request says otherwise)

WHO AND WHAT
- The owner makes TikTok fan edits under the voidfx brand, mostly Dexter, some The Flash. Every edit should be "the best edit we have made so far": a complete, professionally polished edit on the strongest part of the song, timed precisely to the music, with a cohesive atmosphere, a compelling first 1-2 s, a deliberate ending that loops, and many creative animations, graphics and unique transitions.
- What reliably earns approval: transitions as the star; one concept carried through everything; signature set pieces; music that drives the structure; meaningful, beautiful text; graphics with depth; the studio catching its own problems before delivery.
- What reliably draws a note: "lacklustre" (fixed by motion and real set pieces, not more effects); dead space; anything parked, random or drawn-looking; overlays on his face; text that pops on or isn't sung; soft clips; light drawn over him; reusing an earlier edit's look.

FORMAT
- 9:16, 1080x1920, 60 fps, 20-26 s. The studio masters the export to -13 LUFS, true peak <= -3 dBTP.

CONCEPT FIRST
- Before choosing shots, write one concept sentence and carry it through picture, colour, text, sound and the loop. Find it in the material: the song's own words or the character's history (v11: the intro says "Harrison", so the edit became the Reverse-Flash rivalry; v105: "run from the sun like Dracula"; v7: "the evidence points back at him").
- Dexter: kill room, plastic, blood slides, tools, the Code, Harry, the Dark Passenger, victims, season villains; dark, tense, stylish, intense, never soft or pretty. The Flash: lightning, the Speed Force, the emblem, rivalries (Reverse-Flash).
- Each edit gets its own look (grade, type colour, transition mix). Looks already used, do not repeat: warm cinematic blood red; comic-ink halftone; night thriller with chrome-red type; amber/gold lightning over teal; pastel vapor + VHS; forensic noir; sodium nocturne; moonbloom; prism speed; red-vs-gold voltage; 16 mm psychedelic (rejected); storm; undertow; SUMI ink wash; SUNDOWN day/night split. Fresh options: 16 mm home movie (Harry flashbacks), red-and-black ink with print restraint, surveillance/CCTV night vision, chalk outline / crime-scene diagram, blueprint, cold winter teal, Sunshine State postcard, black-and-white newspaper press, X-ray/MRI.

STRUCTURE AND MUSIC
- Use the good part of the song: where the full mix or bass returns (the analysis lists sharp rises in level and a loudness curve). Put the drop at about 33-47% of the edit, after a cold open of 35-45%. A quiet stretch right before a drop suits one short line and a freeze.
- The biggest transition lands exactly on the song's biggest moment.
- Cut on the beat grid (beats and downbeats are listed). In the montage, a designed transition every 2-4 half-beats.
- No headspace: nothing longer than about 1 s without a cut, a transition, a text beat or a camera move.
- Opening: strong in the first 1-2 s. A dialogue opening plays as one continuous take (dissolves between lines, never clips glued together).
- Ending: deliberate, and the edit loops seamlessly: the last moments lead back into frame 0 with the same motif at both ends; the last frame should match the first; never an outro card or a plain rewind blur.

TRANSITIONS (the star of every edit)
- About one designed transition per second of edit (target 24 in ~24 s; best so far 27 in 23 s), none repeated except as a deliberate motif; no plain hard cuts in quiet or dialogue sections.
- Pronounced, physical, going THROUGH something from the character's world, motivated by something in the shot or the lyric. The viewer should wonder how it was done. Each has anticipation (6-15 frames before the cut) and settle (8-18 frames after).
- At least three multi-stage set pieces (anticipation, action, payoff) on the drop, the hook and the loop, plus one focal set piece the owner can point to. In this studio, build a set piece from layers: a speed ramp into the hit, a camera punch, a themed transition, a title that acts out its meaning, keyframed motion, and layered sound effects. Quick moves (whips, flashes) only connect set pieces.
- Favourites: the upside-down roll (the "roll" transition, landing on a rotated shot), the dive into an eye or pupil, the blink, blood blooming open, the logo fly-through, impact frames, light leaks, whip pans.
- The voidfx logo appears exactly once per edit, as a transition: the "logo" transition (the supplied logo, never recoloured; it slams in and the camera flies through its "o"). Give it about 1.2 s.
- Every transition gets its own sound (sfx clips: whoosh, swish, impact, hit, boom, riser, subdrop, reverse, glitch, shutter). A riser and a sub drop lead into the drop. Effects sit about 8-10 dB under the music (volume ~0.35).
- Flash discipline: a flare keeps the picture; no long white-outs; at most 3 flash-type hits in any second.

MOTION (what made "lacklustre" into a standard)
- Speed ramps on every hook and montage shot: a burst on each beat, slow motion between ("ramp" on a clip).
- The beat camera punches (zoom +5.5%) and kicks (rotation 1 degree) on every beat through sections with drums; text stays clean.
- Every shot that only "moves to the beat" gets its own beat animation (a keyframed punch or roll, a flash, a sound).

TEXT (the approved v9 style: "it was perfect")
- Captions: heavy caps on two lines with the second line larger, a dark keyline, soft shadow, a light scrim and red emphasis words with a glow. In this studio: font "Inter", weight 900, uppercase, size ~0.046, lineScales [1, 1.3], stroke 0.07, strokeColor "#0a0a0a", shadow 0.65, scrim 0.35, emphColor "#ff2b3a" (recolour per edit's look), *asterisks* around emphasised words.
- Every word eases in (fade + rise + blur-to-sharp, ~0.17 s): anim.in "words" with "words" set to each word's onset; nothing pops on.
- Keep text in the band 1240-1640 px from the top of 1920 (block centre at transform.y about +0.25; stay within +0.15..+0.34), clear of faces and TikTok's interface.
- Captions only on clearly sung or spoken words, each on its own time. Without the lyrics, do not invent lyric captions: use at most two designed titles. Explicit lyrics: two designed titles instead of captions.
- Hero titles: a per-letter build ("letters") with an exit that acts out the meaning ("scatter", "fall"). Lyric keywords can act out their meaning (FALLING drops, FADING dissolves).
- Never: name labels, speaker tags, who-is-who graphics, counters, timecodes, foreign-language subtitle lines, stamps on captions, thin wide-tracked editorial type, serif-italic emphasis, letter-by-letter fades of thin type, text that pops on.

DIALOGUE
- Less is more: at most one or two short lines that set up the song (e.g. "Could it be him?" answered by the hook). No rapid single-word runs; never end on exposition. Only present a line as spoken when his lips match it; otherwise it is voice-over.

PICTURE
- Faces centred (about 37% of the frame height from the top) and never cut off; leave out shots whose face is wider than the 9:16 frame. For landscape sources set transform.x (and y) so the face sits inside the 9:16 window (the contact sheets draw that window).
- Cut weak, soft or awkward footage even when it is on theme. Keep scale at or below ~1.1 on 720p sources; put close-ups and big moments on the sharpest material.
- Light sources sit behind the subject, never drawn over him.
- Props (blood, slides, knives, glass, tape) only when motivated by the shot, lyric or story; brief; real-looking; in the edit's look; off the face. No gimmick overlays on the face (target rings, converging lines).

BANNED
- Outro cards, title cards, constant watermarks; a recoloured or restyled logo; generic explosion/starburst transitions; slow-motion run-at-camera or floating shots that look odd; lingering or random props; the 16 mm psychedelic look; captions on unsung words; narration shown as spoken.

BEFORE YOU FINISH
- Compare the plan with the standards section by section. If a section is not clearly better than the benchmarks, redesign it. In reviews ask "what would make this moment unforgettable?", not only "is anything broken?". The studio's automated checkpoint (format, length, transition density, headspace, text, logo, sounds, flashes) must pass.`;

export interface Benchmark { id: string; title: string; show: string; song: string; verdict: string; referenceFor: string; quote?: string; lessons?: string }

/** The owner's approved standards and the lessons of every edit (from edits.json). */
export const BENCHMARKS: Benchmark[] = [
  { id: 'v11', title: 'BOP', show: 'The Flash', song: 'DaBaby "BOP"', verdict: 'approved standard (rev 4)', referenceFor: 'a concept from the song\'s own words ("Harrison": the Reverse-Flash rivalry, red vs gold); one focal set piece (THE RIFT); detailed lit graphics revealed on real objects (the emblem coin flip); beat moments for every "just moving" shot; a loop that lands exactly on frame 0; flash discipline; only two designed titles for explicit lyrics', quote: 'I like this edit and would like for you to make it a standard.' },
  { id: 'v105', title: 'DRACULA', show: 'Dexter', song: 'Tame Impala "Dracula"', verdict: 'approved standard (rev 3)', referenceFor: 'a concept-driven day/night split on the drop (SUNDOWN); light behind the subject; 27 designed transitions in 23 s; five set pieces including the ASHES TO SUN loop', quote: 'I like this edit and would like for you to make it a standard. The only gripe I have is the quality of some of the clips.', lessons: 'light sources behind the subject; check clip sharpness; restyle library transitions per edit' },
  { id: 'v104', title: 'THE PASSENGER', show: 'Dexter', song: 'GLM-RST "still love you (super slowed + reverb)"', verdict: 'approved standard (rev 3)', referenceFor: 'one unified look (SUMI ink wash); a self-drawing opening; the lit Dark Passenger set piece; 26 transitions; the upside-down roll was the owner\'s favourite', quote: 'I really like what you did with Dexter being upside down and that transition.', lessons: 'no headspace: nothing longer than about 1 s without a cut, transition or designed beat' },
  { id: 'v103', title: 'FOREVER', show: 'Dexter', song: 'Foo Fighters "Everlong"', verdict: 'approved standard (rev 5)', referenceFor: 'lyric recognition; the beat camera; motivated transitions (flashlight blind-out, eye dive, photo toss); THE RIP plastic tear on the drop', quote: 'I would like for there to be more animations and transitions moving forward and that lyric kind of recognition to happen.', lessons: 'text only on sung words; props must be motivated, brief, real-looking and off the face' },
  { id: 'v10', title: 'LET IT HAPPEN', show: 'The Flash', song: 'Tame Impala "Let It Happen"', verdict: 'approved standard (rev 5)', referenceFor: 'motion and finish: speed ramps on every hook shot, the camera punching and kicking on the beat, light rays, multi-stage set pieces, bullet time, lyric text on sung onsets, the AROUND ring loop', quote: 'I like this edit and would like for you to make it a standard.', lessons: 'two rounds of "lacklustre" were fixed by the motion pass, not by more effects' },
  { id: 'v7', title: 'HIM ALL ALONG', show: 'Dexter', song: 'Gunna "Him All Along"', verdict: 'approved standard (rev 2)', referenceFor: 'creative, well-animated, character-themed transitions: the blood-slide box, the plastic burst on the drop, the body-bag zipper, blood on the lens, the M99 blink, magnifier into the pupil loop; "Could it be him?" answered by the hook', quote: 'The transitions were creative and well animated.', lessons: 'one short line; no gimmicks on the face; never restyle the logo' },
  { id: 'v6', title: 'WARMPOP', show: 'Dexter', song: 'George Clanton "Warmpop"', verdict: 'approved standard', referenceFor: 'the amount and quality of transitions, animations and graphics; the biggest transition on the song\'s biggest moment; the character\'s own words as two-line eased captions; depth graphics', quote: 'wonderful transitions, animations, graphics, while maintaining the style that I like… I like how the music correlates to the edit. I like the text.' },
  { id: 'v4', title: 'SURPRISE', show: 'Dexter (Doakes)', song: 'Migos "Need It"', verdict: 'the first standard', referenceFor: 'a dialogue-led cold open as one continuous take; the barrel into the scope fly-through; the pupil into iris loop; the fly-through of the logo\'s "o"' },
  { id: 'v9', title: 'NIGHT BLOOM', show: 'Dexter', song: 'fakemink "Night, Blooming Jasmine"', verdict: 'good but lacklustre; its text "was perfect" and is the text standard', referenceFor: 'the caption construction only', lessons: 'concept from the character\'s world, not the song title; at least three set pieces; graphics in every section; go above and beyond' },
  { id: 'v8', title: 'WISH YOU WELL', show: 'Dexter', song: 'Brent Faiyaz "Wish You Well"', verdict: 'liked ("did most things well")', referenceFor: 'the "Darling," freeze into the falling blood drop; the rear-view-mirror open and loop; the basic moves (streetlight sweep, wiper, whips, impact frame, rain focus pull, lamp on)', lessons: 'its thin editorial type was disliked' },
];

export const BENCHMARK_TEXT = BENCHMARKS.map(b => `- ${b.id} ${b.title} (${b.show} x ${b.song}), ${b.verdict}: the reference for ${b.referenceFor}.${b.quote ? ` Owner: "${b.quote}"` : ''}${b.lessons ? ` Lesson: ${b.lessons}.` : ''}`).join('\n');
