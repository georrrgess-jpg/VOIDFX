# BOP — The Flash × DaBaby "BOP" (voidfx v11, 9:16)

A 20.79 s, 1080×1920, 60 fps TikTok edit. It's built on the v10 LET IT HAPPEN standard engine and loops: the red lightning snatches the last frame back to the first.

**Deliverables:**
- `v11/out/bop_flash_voidfx_9x16.mp4`: H.264 + AAC, fast-start (upload this one).
- `v11/out/bop_flash_voidfx_9x16_master.mov`: CRF 11 + 24-bit PCM master.

## Sources (what was reviewed)

| Pack | What it actually is | Used |
|---|---|---|
| `src/flash_s4.mp4` (attached "FLASH SEASON 4 SCENE PACK 4K 60FPS") | 1280×720 at 60 fps, 186 s, **24p content** (63 % repeated frames), ~1.1 Mbps. 97 shots reviewed on contact sheets. Shots 0–12 are a CGI/fan-render city run plus a non-Flash anime-style face; left out to keep the look live-action and consistent. | 11 shots |
| `src/reverse_flash.mp4` (attached "Reverse Flash … Topazed 4K 60fps") | 1280×720 at 60 fps, 94 s, **true 60 fps**. Every clip is a ~600×600 inset over a blurred, scan-lined copy, with "SCENEPACK LINK IN DESC" under it and "Intro Clip" title cards. 56 shots reviewed; many are dark S1 Wells dialogue. | 3 shots, framed inside the inset (no watermark) |
| Older Flash packs (`flash_b`, `flash_a`) | Reviewed in v10. | Not needed: S4 has stronger action, and the v10 shots stay v10's |

Neither attached pack is actually 4K. Both were restored with `tools/sr_prep.py` (Real-ESRGAN compact, 2×) before rendering.

## Song: the section used and why

`src/bop.mp3` (2:40), 127.0 BPM (half-beat 0.23622 s), checked on the Demucs vocal stem. **Window: half-beats 32 → 120 (7.75 → 28.54 s, 11 bars).**

| Song | What happens | Edit |
|---|---|---|
| 7.75 | The intro talk over the bass-less intro | 0.00 |
| 9.60 | *"I mean, they're like, **Harrison**…"* | 1.85: Harrison Wells is the Reverse-Flash, so the cold open is his |
| 9.64 | The beat drops in (+24.8 dB) | **1.89: the red shudder → his mask** |
| 13.42 | The dip; *"Let's go!"* at 14.34 | 5.67 / 6.59 |
| **15.31** | **The drop:** the verse, *"I needed some shit with some bop in it"* | **7.56: the bolt split** |
| 28.54 | A bar line between two lines (a clean end) | 20.79: tape stop → the loop |

Why this part: the intro's spoken "Harrison" hands the edit a concept, the beat-in at 9.64 gives a first impact within two seconds, and "Let's go!" sets up the real drop exactly where the verse starts. The rest of the verse is explicit, so it carries no captions: as requested, only two designed words appear (LET'S GO, BOP).

## Concept: THE RIVAL

The cold open is Harrison Wells / the Reverse-Flash, in red: Wells' face on "Harrison", his mask's red eyes on the beat, Thawne's smirk, the red lightning. Barry answers on the dip, and on the drop the frame splits along a lightning-bolt seam, red against gold, and the gold breaks through. The verse is Barry's swagger and speed, in gold. At the end the red lightning snatches the frame back to Harrison, so the rivalry loops.

**Look: VOLTAGE / RIVAL** (new): deep clean blacks, the crimson suit, warm gold lightning with bloom, and cool teal in the shadows for Barry. The rival's shots go red (red-shifted highlights, dark red shadows, red halation).

V11_SHOTLIST
