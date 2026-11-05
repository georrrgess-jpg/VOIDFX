# Starting a new edit: paste this into a new studio session

Fill in the brackets, attach the files, and send it all in **one message**. The studio has everything else in the repo.

```
New voidfx edit: [SHOW] × [ARTIST – SONG]. Studio [1|2], edit number v[N].

Read studio/VOIDFX_STUDIO.md, studio/SCENE_PACKS.md, docs/TOOLKIT.md and CLAUDE.md first,
then build it on the newest standard, v105 DRACULA (python3 tools/new_edit.py [N] [slug] "[TITLE]").

Sources: [new packs attached: …] + any of the library packs in studio/SCENE_PACKS.md.
Song: [attached / src/…]. Use the good part (song_map). Length 20–26 s, 9:16, loops.
Theme / concept ideas (optional): [e.g. "Trinity winter", "the code of Harry", …]
Must-haves (optional): [a line of dialogue, a lyric, a shot, a transition idea]
Avoid (optional): [anything beyond the handbook's rejected list]

Exceed the standards, v105 DRACULA, v104 THE PASSENGER and v103 FOREVER (handbook §0), and the benchmarks (v7 HIM ALL ALONG, v6 WARMPOP, v4 SURPRISE).
No headspace: no span longer than about a second without a cut, a transition or a designed beat.
Clip quality: check every shot with tools/sharpness.py (--src before the render, then on the MP4), swap soft shots, keep zoom
at or under about 1.1 on 720p packs, and put the hero shots on the sharpest, highest-bitrate packs.
Match or beat Studio 1's newest benchmark, the Flash edit (motion and finish: speed ramps with smooth slow motion, a beat-synced
camera, light rays, multi-stage set pieces, a loop that lands exactly on the first frame). Do a motion pass on every hook shot,
upscale the 720p source, and check the lyrics against the sung vocal.
More animations and transitions than FOREVER: 24+ designed transitions per ~24 s, the camera punching on the beat through
every section with drums, and no dead holds. Lyric recognition: a window with sung lyrics, every clearly sung line captioned
word by word on its sung time (tools/lyrics.py with the published lyrics), and key moments landing on sung words.
Many creative, themed transitions
that go through something (each with its own sound), new graphics, eased text, and a hero transition on the drop.
Go above and beyond: clear the handbook's pre-build gate (§5a) before the first render. That means a concept rooted in
Dexter's world, three or more signature multi-stage set pieces (drop, hook, loop), the approved v9 text style
(keyline captions + a per-letter hero title), graphics in
every section, and a written comparison with v6/v7/v8. If the plan doesn't clearly beat them, redesign it.
Own look, not a copy. Run the built-in review passes and the ship checkpoint, fix anything weak, then deliver
the MP4 with a short summary. Work efficiently: one full render per revision.
```

## Feedback template (one message per revision)

```
Revision notes for v[N]:
- Remove: …
- Change: … (what I don't like → what I want instead)
- Add: more [transitions / graphics / sound effects / text animation] around …
- Keep: …
Make all changes in one pass, run the checkpoint, and send the new MP4.
```

## Approval template (to grow the standard)

```
I like v[N]; make it a standard. What I liked: … Add it to the handbook and CLAUDE.md.
```
