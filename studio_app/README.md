# VOIDFX Studio

A browser video editor in the style of CapCut, published as a claude.ai artifact, where **Opus
can build the whole edit** to the voidfx standard, a critic can tear it apart, and Opus revises it round by
round in the background. Stages 1 to 3 of [`PLAN.md`](PLAN.md).

- **Live studio:** https://claude.ai/artifact/24udnvqoodFM824UfV4Md1 (private to the owner until shared from claude.ai).
- **Source of truth:** `src/`. The published page is the single file `dist/voidfx-studio.html`.

## Using it

The studio opens on the **main menu**:

- **AI Edit**: pick a preset, write the notes that make this edit unique (and paste lyrics if you
  have them), choose the material (your files, the **Database**, or both), tick the standards to
  follow, choose what happens after (send to the critic; wait for your instructions or revise once or
  twice on its own), set the effort and press **Create edit in the background**. Keep working: the
  **Activity** panel and notices tell you when the edit and the critique are ready.
- **Projects**: every card has a **⋮** menu: open, write the next round, send to the critic, read
  the critique, export, rename, duplicate, delete.
- **Presets**: standing briefs for AI edits. Built-ins can be duplicated and changed.
- **Database**: scene packs, clips and music Opus can use. Files of any size (well past 100 MB)
  are stored in this browser and read on demand.
- **Standards**: your approved benchmarks and any reference edits you add, for all edits or for
  chosen presets.
- **House rules**: what Opus knows about the voidfx style and where it comes from, plus your own
  additions. Every editing file the owner provided (CLAUDE.md, the studio handbook, the spec and
  handoff, preferences and edit history, the toolkit, the scene-pack notes, the TikTok editing guide
  and the v2-v11 edit archive) is distilled into the house rules, a playbook of every approved set
  piece rebuilt from studio operations, beat-by-beat worked examples of the approved edits, and notes
  on 16 scene packs and 10 songs. A pack or song is recognised when it is used, by name or by its
  length, size and frame rate, and Opus gets its proven shots, dialogue timecodes and what to avoid.

**The critic and the revision stage.** The critic judges an edit against your standards, your house
rules and the best TikTok edits of its kind, and writes a scored assessment with timed issues and a
write-up for Opus. In the round composer you write the next round's instructions, tick which critic
points go in, and start the round; it runs in the background and the editor shows it live (read-only
until it finishes). Every round is kept with its brief, Opus's summary, the critic's score and a
snapshot you can restore. **Ctrl/⌘+K** jumps to any section, project or action.

**Looks and effects.** The **Looks** panel holds 21 grades that sit over the whole edit, above every
shot, graphic and effect and under the text and the logo. They include black-and-white noir, noir with
one colour kept, crimson monochrome, duotone, film stocks, VHS, CCTV, thermal and X-ray. The **Effects**
panel holds 44 tested effects:

- finishes (film grain and halation, bloom, anamorphic streaks, CRT);
- light (light rays, lens flare, a streetlight sweep, spotlight, flashlight, police lights, neon spill);
- atmosphere and particles (fog, rain on glass, heat haze, embers, dust, ash, snow, bokeh, spark and glass bursts);
- camera and impact (shake, zoom blur, glitch, an exposure wash, an impact frame, a freeze);
- beat moments (pulse, remnants, edge pulse);
- themed set pieces (aperture open and close, tape static, TV power-off, plastic wrap, blood on the lens, luminol, lightning arcs, the Speed Force, speed streaks, a shockwave).

Every tile previews on a frame of your own footage. The inspector has a slider or colour for each
parameter. Opus uses them by name with an operation each.

There are 21 new transitions:

- dive into an eye or any anchored point;
- radial glass shatter;
- cube turns and card flips;
- tear, aperture shutter, slices, blinds, wiper;
- streetlight sweep, exposure wash, heat haze;
- ripple, swirl, kaleidoscope, pixelate, datamosh.

Captions use the approved v9 construction. The new title animations are hero bloom, slam,
fly-from-camera, stamp, light-sweep write-on, rise-from-box, tracking and neon flicker. Exits include
blow-away particles (blood, ash, glass, sparks or petals), speed streak and past-the-camera, plus
knockout type with the footage inside the letters.

**Custom graphics and effects.** Opus is not limited to the built-in library: for each edit it can
draw its own vector graphics (emblems, bolts, marks) and write its own GPU effects (lightning, speed
streaks, Speed Force distortion, energy rings, glows) that react to the music and can bend the picture
underneath. They render the same in the preview, the export and the frames Opus and the critic review.
The **Effects** panel has starters you can drop in, and the Edit tab lets you tune them or edit their
SVG or code directly.

In the editor: drag files onto the timeline, trim edges, split with **S**, and add text, transitions
and sounds from the left rail (every animation has a moving picture; hover to play it). The **Edit**
tab tunes the selected clip (speed ramps, beat camera, house caption style). The **Checks** tab runs
the voidfx checkpoint as you edit. **Export** renders MP4 (H.264 + AAC, fast-start), masters the sound
to -13 LUFS and reports what it measured; **Save** hands the file to your device.

Opus never hears audio: the studio measures tempo, beats, downbeats, hits, level rises and quiet parts
and passes those numbers, plus labelled contact sheets of every video. Every Opus change is validated
and lands as one undo step.

**How an edit is built.** Medium, High and Extra build in two calls, so each call fits the time the
runtime allows per call:

1. **The cut.** Opus directs the whole edit (concept, look, song window, set pieces) and writes the
   picture as operations: the song, every shot with its focus, ramps and moves, the beat camera and
   the look. It also writes the plan for the design.
2. **The storyboard.** The studio applies the cut and renders each shot's first, middle and last
   frame, labelled with clip ids and times, with a 0..1 frame ruler for placing anchors.
3. **The design.** Opus writes the transitions, set pieces, text, effects and sound against those
   real frames. Shots that have nothing on them yet are listed, so each one gets a reason.

Every call runs at the job's effort. A call that runs out of time is asked again at the same effort
with a tighter brief and half the images. A design that still does not fit is written as two halves
at the same time. Low plans in one pass.

- **High** then runs one deep review of frames rendered from the edit, every transition's close-ups
  and the checkpoint.
- **Extra** adds more footage per call and a second deep review that raises the ceiling: it rebuilds
  the three weakest moments.

**Revisions** are one call that sees the rendered frames and writes the operations for every note.
With more than 8 notes, or when one call runs out of time, two calls share the notes at the same
effort.

**Notes are followed one by one.** Every owner instruction and every critic point is numbered (N1,
N2, …). Opus plans each note and tags the operations that carry it out. The studio counts them and
asks again for any note left without an operation. The review checks each note in frames rendered
at its moment. The round shows each note's plan, operations and checks. The critic then checks every
point again, credits real fixes against the last round's score, and writes its fixes in the studio's
own terms (the transition, effect or look by name, with times and values). The Opus tab charts the
critic's score across rounds.

The checkpoint also gates the **look and layers**: whether the edit has its own look, and which
seconds are bare footage with no graphic or effect. Further gates catch:

- repeated set-ups;
- three moves of the same family within 5 s;
- stacked flashes that blow a hit out to a white card;
- overlays anchored on a face;
- music that fades at the loop wrap;
- shots of 0.9 s or more with nothing designed on them (no move, ramp or freeze, no text, graphic,
  effect or overlay), which feel purposeless.

The reviews and the critic also get the measured brightness of the rendered frames, since dark grey
is mud on a phone. They also get every transition measured on its three frames (before, middle,
after): a middle that is an empty card, a move that is invisible, a plain crossfade, or a type used
three or more times is flagged for replacement with a different designed move.

**Set pieces in one operation.** `{"op":"piece","kind":…}` expands into a tested, multi-stage build of
an approved set piece on the shots at that time: the freeze or ramp, the transition, the effects with
their anchors and amounts, the title and the sounds. The kinds are `freeze_hit`, `blood_drop`,
`plastic_burst`, `crt_dive`, `polaroid_toss`, `glass_shatter`, `lens_blood`, `light_title` and
`pupil_loop`. Opus builds the drop, the focal moment and the loop with them, then adds its own layers
around them.

**The studio's finishing pass.** After every Opus pass the studio fixes, and reports, the defects the
critic kept marking down:

- a music fade at the loop;
- a flash effect stacked on another flash;
- light or props anchored on a face, which are moved to the side;
- a loop that still jumps, which gets `{"op":"loop"}`.

The checkpoint also flags clutter (more than four layers starting within half a second). Every effect,
graphic and shader is rendered with and without itself. A layer that does not show, or that turns a lit
frame into a white or black card, is listed for the review and the critic.

**The element workshop.** This is the chat loop, inside the studio. After the design, each of Opus's
own effects and graphics is rendered large through its whole life (six frames), next to the same
moment without it. Opus scores each against a craft standard:

- layered, not flat;
- lit like the shot;
- anticipation, an eased main move and follow-through;
- secondary motion;
- placed for a phone;
- finished edges.

It rebuilds every element under 8. High runs one pass, Extra two, and revisions workshop the elements
they changed.

**The animation toolkit.** Custom effects get staged timing (`stage`, `envelope`), easing with
overshoot (`easeOutBack`, `easeOutExpo`, `easeOutElastic`), antialiased shapes and strokes, `sparks`,
`smoke`, `lightSpill` and `refractFrame`. Opus also gets three complete example elements built to the
chat edits' standard, each compiled and rendered by the tests: a stamped emblem, blood running down the
glass, and a luminol sweep.

**Your notes are binding and remembered.** Every instruction you write in any round is listed for
every later round, and for the critic, as a binding decision. The critic never writes a point that
contradicts one. When a critic point conflicts with you, Opus follows you and marks the point
skipped. The critic also sees its own points from the last round, so it does not flip-flop. Every note
you write, in any project, is remembered and sent with every later edit as your taste in your own
words.

**The lyric guard.** After every Opus pass, each caption Opus wrote is checked against the owner's
lyrics:

- a sung caption must be the real line, word for word, so wrong words are corrected to the line;
- a caption off its sung time is moved onto it;
- a line that is not sung in this part of the song, or words that are not in the lyrics, are removed;
- with no lyrics supplied, only one- or two-word titles and the character's own dialogue may stand.

**Transitions with a reason.** A clean cut on the beat with the camera punch counts as a designed
join, so cuts are not filled with moves that have no reason. After the last review the studio measures
every transition once more. Any that is still empty, invisible, a plain crossfade or a third repeat is
replaced with a tested move that differs from its neighbours. A replacement that also fails becomes a
clean cut.

**Revisions rebuild.** Each note about a moment lists what is on screen there now (the shot, the
transition, the layers, the text). The revision call also gets the measured transitions and layers,
and is told to remove and rebuild weak moments rather than add on top. After the changes the studio
renders every note's moment again. A note whose frame looks the same is marked not done, and the review
writes it.

**The critic's scale.** Scores are calibrated to the owner's approved benchmarks (an edit at their
level is an 8). The overall score stays within half a point of the weighted area scores. "Critical" is
kept for defects that break the edit on the first watch, and caps the score at 7 while it remains.

**Export on every machine.** The exporter asks the browser which audio settings it can encode
(Windows' AAC encoder stops at 192 kbps) and steps down the bitrate. If platform AAC is unavailable
it falls back to the bundled AAC encoder, then to Opus audio. If an encoder still refuses mid-render,
the export retries once at safe settings.

**Auto exposure and the loop.** House-style edits lift dim shots toward a readable brightness automatically. Each shot's mean is read on the GPU; shadows and mids are raised and highlights kept, before the shot's grade and the look. It can be turned off per project or per clip. `{"op":"loop"}` lands the last frame on frame 0's exact source frame and framing, and the loop-seam gate judges the wrap against a normal frame-to-frame step.

**Lessons from the critic.** Every critique's critical and major findings are remembered (House rules page) and sent with every later direction and review, so the studio does not repeat what was marked down.

The song analysis takes the half tempo when busy hi-hats double it. It finds drops where the bass returns, and snaps them onto the downbeat. For each suggested window it lists where the bars and the drop fall on the timeline. A long video added straight to a project is split into shots like a database pack, with a cut detector that also works on black-and-white and night footage.

Everything (projects, media, database, presets, standards, rounds, critiques) is stored in this
browser's storage for the artifact. It does not sync to other devices, and clearing site data removes
it. Background jobs run while the studio is open; closing it stops them, and they can be resumed.

## Keyboard

Space play/pause · S split · Del delete · Ctrl+Z / Ctrl+Shift+Z undo/redo · Ctrl+D duplicate ·
←/→ frame step (Shift: 1 s, Alt: nudge clip) · Home/End · Ctrl+wheel zoom timeline · Ctrl+E export.

## Develop

```bash
npm install
```

```bash
node build.mjs
```

```bash
bash test/make_media.sh && node test/smoke.mjs && node test/bigfile.mjs
```

`npx tsc --noEmit` type-checks. The smoke test runs the whole studio in headless Chromium with a
stubbed `claude` runtime (scripted Opus replies, captured downloads): the main menu sections, the
database (a scene pack split into shots, music analysed), a standard, the AI Edit wizard and the
Director pipeline with casting, contact sheets, the checkpoint and a review pass, transition and text
previews, the build running in the background while another project is edited, the automatic
critique, its write-up, the round 2 composer, the locked editor during the revision, export with
mastering, and reopening the project after a reload. It writes screenshots and
the export to `test/out/`. `bigfile.mjs` imports a ~2 GB file with
its index at the end and reports time-to-ready, JS heap and export time.

```bash
node test/suite.mjs
```

The suite has pass/fail checks and exits non-zero if any fail (`ONLY=build,revise,cancel,export,render,units,persist` runs a part). It covers:

- four AI edits at once, one per effort level, while another project is edited;
- the critic, a revision with numbered notes, an automatic round, and cancel and resume;
- a layers call that fails twice;
- an export decoded and measured with ffprobe/ffmpeg (codecs, length, loudness, true peak, picture);
- every transition, look, effect and text animation rendering and changing the picture;
- id handling, camera sections, the newer gates, velocity ramps and the critic's lessons;
- persistence across a reload.

```bash
LIVE=/path/to/dir MEDIA="pack.mp4,song.wav" MODE=build node test/live.mjs
```

`live.mjs` runs a real AI edit with every Opus call answered from outside. Each request (its turns and images) is written to `LIVE/req-N.md`, and the reply is read from `LIVE/res-N.txt`, so an agent can stand in for Opus. `MODE=revise` continues with every critic point, and `MODE=export` renders the MP4. It saves the timeline, notes, critique, timings and a filmstrip per round.

## Layout

| Path | What it holds |
| --- | --- |
| `src/state/` | Project model (`types.ts`), store with undo/redo and autosave, validated edit operations shared by the UI and Opus (`ops.ts`), IndexedDB storage, projects, presets, standards and the database (`catalog.ts`) |
| `src/media/` | Import and probing through Mediabunny, filmstrips, waveforms, streaming audio analysis |
| `src/engine/` | Timeline evaluation, WebGL2 compositor (with the warp stage for 3D, shatter and distortion transitions), text renderer, transitions, the looks and effects library (`fxlib.ts`), logo, sound effects, loudness, checkpoint, previews, preview player, WebCodecs fallback, audio mix, exporter |
| `src/ai/` | Opus Director: house rules and benchmarks (`knowledge.ts`), the set-piece playbook (`playbook.ts`), worked examples of the approved edits (`exemplars.ts`), scene packs and songs (`sources.ts`), the critic's canon (`canon.ts`), contact sheets, prompt, build and revision with numbered notes (`director.ts`), the critic (`critic.ts`), background jobs (`jobs.ts`, `workspace.ts`) |
| `src/ui/` | Preact components; `src/ui/home/` holds the main menu, `src/ui/ai/` the activity list, the critique and the round composer |
| `assets/` | The voidfx logo, used as supplied |

Libraries are bundled (no runtime CDN): Preact 10.29.8, Mediabunny 1.62.0 and its AAC encoder
extension (MPL-2.0). The Inter and display fonts are embedded.
