# VOIDFX Studio: plan

A browser video editor, published as a claude.ai artifact, where Opus 5.5 can build the whole edit.
It replaces the single-clip "TikTok Edit Studio" prototype with a multi-track editor.

## Principles

- **Opus edits through the same operations as the user.** Every change (a drag on the timeline or
  an Opus plan) goes through one validated edit-operation layer (`src/state/ops.ts`), so anything
  Opus does can be inspected, changed by hand and undone in one step.
- **No built-in editing style.** Opus gets the studio's capabilities, the media, the analysis and the
  user's request. Presets, house style and editing knowledge are supplied by the user later
  (stage 2) through the "Studio knowledge" slot, which ships empty.
- **Large files stream.** Media is never read into memory whole: playback uses object URLs, and
  decoding, analysis and export read byte ranges through Mediabunny (`BlobSource`).
- **Preview and export share one compositor** (WebGL2), so what plays is what renders.

## Stage 1: core studio (this build)

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

## Stage 2: the user's editing knowledge

- Load the presets, style rules and editing information the user provides into the Studio knowledge
  slot (and as named preset files Opus can pick from).
- Tune the Director prompts and review checks to those rules.

## Stage 3 candidates

- Speed ramps as curves (not just per-clip speed); freeze frames; reverse.
- Proxy generation for 4K/HEVC sources; background export in a worker.
- Lyric/dialogue timing (needs a transcription source the artifact can reach).
- Tool-driven editing rounds (`sample` tools) once the operation format is stable.

## Layout

```
studio_app/
  build.mjs            esbuild -> dist/voidfx-studio.html (single file, published as the artifact)
  src/state/           project model, store + history, edit operations, timeline evaluation
  src/media/           import, thumbnails, waveforms, audio analysis
  src/engine/          WebGL compositor, text renderer, transitions, preview player, exporter
  src/ai/              Opus Director: context, contact sheets, prompts, pipeline
  src/ui/              Preact components
  test/smoke.mjs       headless Chromium test with a stubbed claude runtime
```
