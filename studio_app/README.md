# VOIDFX Studio

A browser video editor in the style of CapCut, published as a claude.ai artifact, where **Opus 5.5
can build the whole edit** to the voidfx standard. Stages 1 and 2 of [`PLAN.md`](PLAN.md).

- **Live studio:** https://claude.ai/artifact/24udnvqoodFM824UfV4Md1 (private to the owner until shared from claude.ai).
- **Source of truth:** `src/`. The published page is the single file `dist/voidfx-studio.html`.

## Using it

The studio opens on the **main menu**:

- **AI Edit**: pick a preset, write the notes that make this edit unique (and paste lyrics if you
  have them), choose the material (your files, the **Database**, or both), tick the standards to
  follow, set the effort and press **Create edit**. Opus casts, plans, builds, checks and reviews
  the edit, then opens it in the editor.
- **Projects**: open, rename, duplicate or delete projects, or start a blank one.
- **Presets**: standing briefs for AI edits. Built-ins can be duplicated and changed.
- **Database**: scene packs, clips and music Opus can use. Files of any size (well past 100 MB)
  are stored in this browser and read on demand.
- **Standards**: your approved benchmarks and any reference edits you add, for all edits or for
  chosen presets.
- **House rules**: what Opus is told about the voidfx style, plus your own additions.

In the editor: drag files onto the timeline, trim edges, split with **S**, and add text, transitions
and sounds from the left rail (every animation has a moving picture; hover to play it). The **Edit**
tab tunes the selected clip (speed ramps, beat camera, house caption style). The **Checks** tab runs
the voidfx checkpoint as you edit. **Export** renders MP4 (H.264 + AAC, fast-start), masters the sound
to -13 LUFS and reports what it measured; **Save** hands the file to your device.

Opus never hears audio: the studio measures tempo, beats, downbeats, hits, level rises and quiet parts
and passes those numbers, plus labelled contact sheets of every video. Every Opus change is validated
and lands as one undo step. **Effort**: Low, Medium and High set Opus's thinking effort; **Extra** uses
High plus more footage per call and two review passes in which Opus checks frames rendered from its
own edit and the checkpoint results.

Everything (projects, media, database, presets, standards) is stored in this browser's storage for
the artifact. It does not sync to other devices, and clearing site data removes it.

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
previews, export with mastering, and reopening the project after a reload. It writes screenshots and
the export to `test/out/`. `bigfile.mjs` imports a ~2 GB file with
its index at the end and reports time-to-ready, JS heap and export time.

## Layout

| Path | What it holds |
| --- | --- |
| `src/state/` | Project model (`types.ts`), store with undo/redo and autosave, validated edit operations shared by the UI and Opus (`ops.ts`), IndexedDB storage, projects, presets, standards and the database (`catalog.ts`) |
| `src/media/` | Import and probing through Mediabunny, filmstrips, waveforms, streaming audio analysis |
| `src/engine/` | Timeline evaluation, WebGL2 compositor, text renderer, transitions, logo, sound effects, loudness, checkpoint, previews, preview player, WebCodecs fallback, audio mix, exporter |
| `src/ai/` | Opus Director: house rules and benchmarks (`knowledge.ts`), contact sheets, prompt, pipeline |
| `src/ui/` | Preact components; `src/ui/home/` holds the main menu |
| `assets/` | The voidfx logo, used as supplied |

Libraries are bundled (no runtime CDN): Preact 10.29.8, Mediabunny 1.62.0 and its AAC encoder
extension (MPL-2.0). The Inter and display fonts are embedded.
