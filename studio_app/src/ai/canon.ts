// How every edit is judged: the critic's areas and the canon of top TikTok edits. The director plans
// against the same canon, so the first draft aims at what the critic will score.
export const CRITIC_AREAS: { id: string; label: string }[] = [
  { id: 'hook', label: 'Hook' },
  { id: 'rhythm', label: 'Rhythm & sync' },
  { id: 'transitions', label: 'Transitions' },
  { id: 'motion', label: 'Motion' },
  { id: 'text', label: 'Text' },
  { id: 'sound', label: 'Sound' },
  { id: 'concept', label: 'Concept & story' },
  { id: 'picture', label: 'Picture & framing' },
  { id: 'loop', label: 'Ending & loop' },
];

/** What separates the edits that travel on TikTok from the ones that get scrolled past. */
export const CRITIC_CANON = `THE TIKTOK EDIT CANON (what the top fan edits in the edit community do, and what gets scrolled past)
1. HOOK (0-1 s). The first frame is already striking and something hits within half a second: no fade in from black, no logo first, no slow establishing shot, no dead air. Viewers decide in about a second; a weak first second caps the whole edit.
2. THE SONG CUT. The strongest 15-30 s of the song (the drop, the chorus, the recognisable line), entered on a phrase and left on a phrase end or a hard stop that loops. A cut that starts mid-phrase or wanders through a verse reads as careless.
3. SYNC. Every cut and every effect sits on the beat grid; accents (snare, vocal chop, bass hit, riser peak) each get a visual event. Cuts drifting a few frames off the beat are the fastest tell of an amateur edit.
4. PACING. Contrast: build and release, a held breath before the drop, a burst on it; never one uniform pace. In a hype edit no shot sits for more than about a second without something happening in it.
5. MOTION. Velocity: speed ramps (burst on the hit, smooth slow motion between), shake and zoom punches on hits, motion blur. Static shots laid on a beat are the number-one mark of a weak edit; "smooth" does not mean slow.
6. TRANSITIONS. Purposeful, varied and tied to the content (match cuts on shape, movement or colour; whips matched in direction; objects that wipe the frame; going through something). The same preset transition repeated, or generic flash and glitch spam, looks like a template.
7. CLIP CHOICE. The most iconic, expressive moments of the character; faces readable and centred for 9:16; no soft, blocky or upscaled-looking clips, no burned-in subtitles, watermarks or black bars; consistent quality across sources.
8. COLOUR, LOOK AND FINISH. One cohesive, bold look with real contrast (black-and-white noir with one colour kept, a duotone, a film stock, a themed monochrome) rather than a neutral grade; no flicker; sharp; sources matched; light leaks used with intent.
9. GRAPHICS AND EFFECTS. Depth and flair in every section: light that reacts to the footage, atmosphere and particles, themed overlays, designed graphics and beat moments, each attached to the action and lit like the shot. An edit of bare footage reads flat; random or drawn-looking overlays read cheap.
10. TEXT. Few words, timed to the vocal or the line, readable at phone size, clear of faces and TikTok's interface, designed with intent; never paragraphs, default fonts, typos or text that pops on.
11. CONCEPT. The edit says something about the character (an arc, a rivalry, a turn) and has a moment people would comment on ("the transition at 0:07"). Without a concept it is a montage.
12. ENDING AND LOOP. It ends on its strongest image or hit and loops seamlessly in picture and sound, so the rewatch is invisible; no outro card, no fade to black that kills the loop.
13. SOUND DESIGN. The music leads; effects are punctuation: a riser and impact into the drop, hits on the set pieces, a whoosh only where a move needs one. A whoosh on every cut or stacked effects clutter the mix and read as amateur. Clean, loud, unclipped; dialogue clear when used.
14. ORIGINALITY. A signature move; nothing that looks like a trend template or an earlier edit's look.
SCORING. 9-10: could stand with the best edits in its niche (viral calibre). 7-8: strong, needs polish. 5-6: competent but forgettable. Below 5: amateur flaws. Most edits honestly land between 4 and 7. Never inflate. Any critical issue caps the score at 6.5.`;
