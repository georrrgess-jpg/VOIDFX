# VOIDFX Studio: plan

A browser video editor, published as a claude.ai artifact, where Opus 5.5 can build the whole edit.
It replaces the single-clip "TikTok Edit Studio" prototype with a multi-track editor.

## Principles

- **Opus edits through the same operations as the user.** Every change (a drag on the timeline or
  an Opus plan) goes through one validated edit-operation layer (`src/state/ops.ts`), so anything
  Opus does can be inspected, changed by hand and undone in one step.
- **The owner's style is data, not code.** Stage 1 shipped with no editing style. Stage 2 adds the
  owner's house rules (`src/ai/knowledge.ts`, distilled from the handbook, preferences, edit history
  and studio specs), presets, standards and the database. Opus receives them as context with every
  edit, and the user can edit or extend all of them in the studio.
- **Large files stream.** Media is never read into memory whole: playback uses object URLs, and
  decoding, analysis and export read byte ranges through Mediabunny (`BlobSource`).
- **Preview and export share one compositor** (WebGL2), so what plays is what renders.

## Stage 1: core studio

| Area | What ships |
| --- | --- |
| Project | 9:16 / 4:5 / 1:1 / 16:9, 24-60 fps, autosave, undo/redo (Ctrl+Z / Ctrl+Shift+Z) |
| Media | Import video, audio and images by drop or picker; streaming metadata, filmstrip thumbnails, waveforms; beat, tempo, energy and quiet-part analysis for anything with sound |
| Timeline | Magnetic main track, overlay video tracks, text and audio tracks; move, trim, split (S), delete, duplicate, snapping to clips, playhead and beats; zoom; keyframes |
| Clip controls | Position, scale, rotation, opacity (keyframeable), fill/fit, speed 0.1-10x with pitch keep, volume and fades, colour (brightness, contrast, saturation, temperature, tint, hue, vignette, blur), transitions in |
| Text | Fonts, size, weight, fill, outline, shadow, box, alignment, case; in/out animations (fade, rise, pop, blur, typewriter, word-by-word) |
| Transitions | Crossfade, dip to black/white, flash, slide/push, wipe, iris, zoom, whip, spin, blur, glitch |
| Preview | Real-time playback with Web Audio mixing; drag and scale the selected layer on the canvas |
| Export | Offline, frame-accurate MP4 (H.264 + AAC, fast-start) via WebCodecs; saved through the `downloads` capability; MediaRecorder fallback |
| Opus Director | One button builds the edit: local analysis, contact sheets of every clip, Opus plans the timeline as edit operations, the app applies and validates them, then renders frames of the result for an Opus review pass. Chat to refine. Effort: Low, Medium, High, Extra (High plus an extra review pass). Shows which model answered. |

## Stage 2: main menu, AI edits and the owner's standard

| Area | What ships |
| --- | --- |
| Main menu | Animated home (live WebGL void that reacts to the pointer and tints per section) with Home, AI Edit, Projects, Presets, Database, Standards and House rules |
| Projects | Any number of projects in IndexedDB with thumbnails; new, open, rename, duplicate, delete; media files are stored with the project and reattach on reopen; stage-1 autosave migrates in |
| AI Edit | Wizard: preset, notes for this edit, optional lyrics, material from your files, the database or both ("Let Opus choose" or pick items), standards to follow, effort, then Create edit |
| Presets | Standing briefs: prompt, house rules on/off, effort, aspect, fps, length range, database tags, standards shown, colour. Six built in (Dexter, The Flash, dialogue cold open, lyric-led, quick draft, open brief); duplicate and edit your own |
| Database | Scene packs, clips and music of any size stored in the browser; packs are split into shots, music is analysed for tempo, beats and drops; roles and tags; Opus casts from it |
| Standards | Your approved benchmarks (v4 to v11, v103 to v105) plus reference edits you add, measured for cuts per second, shot length and on-beat cuts, for all edits or for chosen presets; Opus sees a contact sheet and the numbers |
| House rules | Everything Opus is told about the voidfx style, readable in the studio, with your own additions |
| Director v2 | Casting from the database, shot-based 9:16 contact sheets, the plan, validation, transition sounds, a measured checkpoint, review passes that see the checkpoint; refine by chat |
| Checkpoint | Format, length, transition density, plain cuts, headspace, logo once, text ease and band, transition sounds, flash rate, music coverage, soft 720p blow-ups, loop seam; seek chips and "Fix with Opus" |
| Engine | voidfx logo fly-through (through the "o", logo unaltered), blink, blood bloom, film burn, blade slash, impact frame, light leak, roll 90°, shadow, warp pull; speed ramps (velocity ramp: burst on each beat, slow between); beat camera (zoom punch, rotation kick); procedural transition sounds; v9 house caption type (emphasis, glow, scrim, word timing, letter build, scatter, fall) |
| Sound | Export masters to -13 LUFS with a true-peak limiter (pre-encode ceiling -3.5 dBTP) and reports the measured result |
| Editor | Picture previews of every transition and text animation (play on hover), Sounds panel, database picker in Media, ramp and beat-camera controls, Checks tab |

## Stage 3: autonomous rounds, the critic, the revision stage (this build)

| Area | What ships |
| --- | --- |
| Background jobs | Builds, revisions and critiques run in a queue, each on its own copy of its project (`src/ai/workspace.ts`, `src/ai/jobs.ts`). Leave the editor, open or edit other projects, queue more edits; notices (with an Open or Read button) and the tab title say when work is ready. A project being revised is read-only in the editor with a progress bar, and the timeline updates live. Jobs stop if the studio is closed and can be resumed |
| Shared media | Media ids are unique across projects, and loaded files are shared by reference count between the editor and jobs (`MediaBay` in `src/media/library.ts`); older projects are migrated on open |
| The critic | A harsh second Opus pass (`src/ai/critic.ts`) with the TikTok edit canon, the owner's rules, benchmarks and standards, a dense rendered filmstrip, every transition as three frames, measured cut timing against the beat, pacing, the hook's first second and the checkpoint. Returns a score, nine category scores, what works, issues with times and fixes, a comparison with the standards and a write-up for Opus |
| Autonomy | AI Edit and every round: send to the critic when done, then wait for instructions or revise once or twice on its own from the write-up |
| Revision stage | The round composer: "You're writing the instructions for round N", the critic's issues as checkboxes (critical and major pre-picked), the write-up toggle, quick instructions, effort, what happens after, and a preview of exactly what Opus will receive |
| Rounds | Every round is kept on the project: the owner's words, the critic points passed on, Opus's summary, the critic's score, and a snapshot of the timeline that can be restored |
| Menus | "⋮" on every project card and in the editor: open, the next round, send to the critic, read the critique, export, rename, duplicate, delete (confirmed) |
| Main menu | A lensed black hole (starfield Einstein ring, Keplerian accretion disk with Doppler brightening, the far side lensed over the shadow, infalling matter, photon ring) tinted per section; dashboard with live Activity, recent projects with live job status and critic scores, the Brief → Build → Critic → Revise flow |
| Everywhere | Ctrl/⌘+K command palette; segmented controls wrap instead of overlapping; toasts with actions sit clear of dialogs |

## Stage 4: custom graphics and effects (this build)

| Area | What ships |
| --- | --- |
| Graphics | Opus (or the owner) draws vector art as SVG for an edit: emblems, bolts, marks, frames, speed lines. The studio keeps drawing elements only (no scripts, images, text or outside links), draws it once at the right size, and animates it with transform keyframes, a reveal (pop, iris, wipe, flicker, fade) and a glow; it rides with the beat camera |
| Effects | Opus writes a GLSL function `vec4 effect(vec2 uv, float t, float p)` that runs over the frame: procedural lightning, streaks, rings, particles, or distortions that read the picture underneath (`frame(uv)`). It reacts to the music (`uBeat`, `uBeatAge`, `uEnergy`) and follows a keyframed anchor (`uPos`). A helper library (noise, fbm, shapes, `boltDist` lightning paths, glow) comes with it. Code is limited to a safe subset (no preprocessor, no while loops, bounded for loops) and compiled before use; a failure is skipped and reported back to Opus in its review |
| Everywhere | Preview, export, Opus's review frames and the critic's filmstrip draw these layers the same way; effects over a cut count as designed transitions; a new checkpoint gate asks for custom work on set pieces; the critic judges whether it looks designed and attached to the action |
| Editor | Timeline styling for graphics and effects; Inspector with blend (normal, add light, screen), glow, reveal, width, live SVG and code editing with compile status; an Effects panel with 12 starters (lightning arc, Speed Force pull, speed streaks, electric edges, ghost echo, beat shockwave, rising sparks, chroma punch, lightning emblem, bolt, speed lines, blood slide) with moving previews |

## Stage 5 candidates

- Freeze frames and reverse; optical-flow slow motion.
- Face tracking for framing checks (no face model runs in the artifact yet).
- Proxy generation for 4K/HEVC sources; background export in a worker.
- Lyric/dialogue timing (needs a transcription source the artifact can reach).
- Tool-driven editing rounds (`sample` tools) once the operation format is stable.
- Run jobs when the studio is closed (needs a server-side runner; the artifact runs only while open).

## Layout

```
studio_app/
  build.mjs            esbuild -> dist/voidfx-studio.html (single file, published as the artifact)
  assets/              voidfx logo (as supplied)
  src/state/           project model, store + history, edit operations, storage, projects, catalog
  src/media/           import, thumbnails, waveforms, audio analysis
  src/engine/          WebGL compositor, text renderer, transitions, preview player, exporter
  src/ai/              Opus Director: house rules, context, contact sheets, prompts, pipeline, checks
  src/ui/              Preact components (src/ui/home/: the main menu sections)
  test/smoke.mjs       headless Chromium test with a stubbed claude runtime
```
