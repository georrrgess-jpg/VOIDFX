# voidfx edit standard

**Benchmark:** `v4/` — *SURPRISE* (Doakes × Need It, 9:16). The user approved it as the standard for new edits.
New edits must match or exceed it. Read `v4/README.md` and `v4/work/` before starting, and reuse the engine (`render4.py`,
`audio4.py`, `qc4.py`, `facetrack.py`) instead of starting from scratch. Do not reuse its *look*: each edit needs its own style.

## User preferences (learned over several revisions)

- **Format:** 9:16, 1080×1920, 60 fps, TikTok-ready H.264 + AAC with fast-start, plus a high-quality master. About 20–26 s; don't run long.
- **Framing:** faces always centred and never cut off. Face-track every shot (YuNet). Leave out shots whose face is wider than the 9:16 window.
- **Opening:** start strong. Dialogue from the source can open the edit or tie heavily into it. It must play as **one continuous take**: J-cuts, dissolves, a matched-angle morph. Never several clips that feel glued together.
- **No labels:** no name tags, speaker chips or "who is who" graphics. No stamps sitting on top of captions.
- **Text:** every word eases in (fade + rise + blur-to-sharp). Nothing just pops on. Each title or lyric moment gets its own designed animation, and it must be clearly readable (size, contrast, time on screen).
  - Approved examples: footage-in-letters knockout type; a title that fills with blood and drips, then shatters with the glass; light-sweep reveal; fly-in from the camera.
  - Keep text clear of faces and of TikTok's UI areas.
- **Branding:** no constant watermark and no outro card. The voidfx logo (`src/voidfx_logo.webp`) appears **once, as a transition** (e.g. flying through the "o").
- **Transitions:** pronounced and designed, the kind where the viewer wonders "how did they do that". They should feel like **going through something**: barrel, scope, shattering glass, an eye or pupil, a shadow, the logo's "o", a photo on the wall, a knife slash.
  - Avoid plain hard cuts in quiet or dialogue sections.
  - Every transition gets its own sound.
- **Loop:** the edit must loop seamlessly for TikTok, in picture (e.g. into the pupil to black → iris open from black) and in sound. For sound: room tone and drone continue across the wrap, the timeline is built circularly, mastering runs on a wrapped copy, and audio and video are exactly the same length. An outro card breaks the loop, so don't use one.
- **Sound:** smooth and clean.
  - Dialogue is cleaned and levelled, with equal-power fades at every join.
  - The song is edited on its beat grid; a tape-stop or dead stop is fine for an ending.
  - Mastered to about −13 LUFS with true peak ≤ −2.5 dBTP, measured **after** AAC encoding.
- **Workflow:** the user wants built-in review passes, not repeated rounds of feedback. Before delivering, always run:
  1. automated QC on the **encoded** file (`qc4.py`): format/decode, loudness, face centering, text vs faces, cuts, freezes, black frames, audio clicks at every edit, loop seam;
  2. a visual review of contact sheets around every transition and title;
  3. a fix-and-re-render for anything weak;
  4. a final pull of key frames from the encoded file.
- **Honesty:** you cannot watch or listen. Report what was verified by frames and measurement, and ask the user to watch once with sound.
- **Communication:** short progress updates; no long code in chat.

## Project conventions

- Sources go in `src/` (read-only copies). Each edit gets its own folder (`vN/work`, `vN/out`, ...).
- One EDL file per edit holds every decision, and the renderer reads only that file.
- Media (`src/`, audio, frames, outputs, models) stays out of git. Commit the code, EDL, transcripts, tracks and README, then push to the session's branch.
- Models are downloaded at runtime: YuNet (`v3/models/face_detection_yunet_2023mar.onnx`), MODNet (`Xenova/modnet`), and faster-whisper large-v3 for dialogue and lyric timing.
- The older guide `7b769aa4-TIKTOK_EDITING_GUIDE.md` (the beat-grid, colour and QC methods) still applies where it doesn't conflict with this file.
