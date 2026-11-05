# VOIDFX Studio

A browser video editor in the style of CapCut, published as a claude.ai artifact, where **Opus 5.5
can build the whole edit**. Stage 1 of the plan in [`PLAN.md`](PLAN.md).

- **Live studio:** https://claude.ai/artifact/24udnvqoodFM824UfV4Md1 (private to the owner until shared from claude.ai).
- **Source of truth:** `src/`. The published page is the single file `dist/voidfx-studio.html`.

## Using it

1. Drop video, audio and images anywhere in the studio (or **Import media**). Large files are read
   from disk on demand; nothing is loaded into memory whole.
2. Either press **Create edit** in the Opus panel (optionally describe what you want), or edit by hand:
   drag files onto the timeline, trim edges, split with **S**, add text and transitions from the left rail,
   and tune any clip in the **Edit** tab.
3. **Export** renders MP4 (H.264 + AAC, fast-start) frame by frame, then **Save** hands it to your device.

Opus never hears audio: the studio measures tempo, beats, downbeats, hits, level rises and quiet parts
and passes those numbers, plus labelled contact sheets of every video. Every Opus change is validated
and lands as one undo step. **Effort**: Low, Medium and High set Opus's thinking effort; **Extra** uses
High plus more footage per call and two review passes in which Opus checks frames rendered from its
own edit. The **Studio knowledge** field is empty by design; it is where editing presets and house
style go (stage 2).

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
stubbed `claude` runtime (scripted Opus replies, captured downloads): import, analysis, the Director
pipeline with contact sheets and a review pass, preview playback (element and WebCodecs fallback),
and a 720p export that it writes to `test/out/` for ffprobe. `bigfile.mjs` imports a ~2 GB file with
its index at the end and reports time-to-ready, JS heap and export time.

## Layout

| Path | What it holds |
| --- | --- |
| `src/state/` | Project model (`types.ts`), store with undo/redo and autosave, validated edit operations shared by the UI and Opus (`ops.ts`) |
| `src/media/` | Import and probing through Mediabunny, filmstrips, waveforms, streaming audio analysis |
| `src/engine/` | Timeline evaluation, WebGL2 compositor, text renderer, transitions, preview player, WebCodecs fallback, audio mix, exporter |
| `src/ai/` | Opus Director: contact sheets, prompt (capabilities only, no style), pipeline |
| `src/ui/` | Preact components |

Libraries are bundled (no runtime CDN): Preact 10.29.8, Mediabunny 1.62.0 and its AAC encoder
extension (MPL-2.0).
