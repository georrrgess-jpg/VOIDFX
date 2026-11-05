# voidfx edit standard

**Benchmarks (all approved by the user as the standard for new edits; match or exceed them):**
- `v11/`, *BOP* (The Flash × DaBaby "BOP", rev 4): **the newest standard and the engine every new edit is built on.** The reference for **concept, focal set pieces and the loop**: a concept taken from the song's own words (the intro's "Harrison" → the Reverse-Flash rivalry, red vs gold in two grades), very few but designed titles (LET'S GO, BOP), a true focal set piece (THE RIFT: a tear across the frame into the Speed Force, flown through), a detailed procedural emblem revealed physically (the real chest emblem coin-flips into the Reverse-Flash's), beat moments instead of "just moving to the beat" (aura, time remnants, charge-up), and a loop set piece that lands exactly on frame 0 (seam 0.11). The user: "I like this edit and would like for you to make it a standard."
- `v10/`, *LET IT HAPPEN* (The Flash × Tame Impala "Let It Happen", rev 5): the standard for **motion and professional finish** (its engine is inside v11's). The reference for **motion and professional finish**: velocity ramps on every hook shot (a burst on each beat, optical-flow slow motion between, on restored 2× source), a camera that moves with the music (zoom punches, rotation kicks, hit-frame blur), light rays from the lightning, multi-stage character set pieces (emblem dive into the drop wave, time particles, lens shatter, lightning branches, the perimeter lap, phase, whirlwind), bullet time in frozen holds, lyric text on the sung onsets, and a loop that is a set piece (the AROUND ring opens into the Speed Force and flies back through the edit to frame 0). The user: "I like this edit and would like for you to make it a standard."
- `v7/`, *HIM ALL ALONG* (Dexter × Gunna "Him All Along", rev 2): the reference for **creative, well-animated, character-themed transitions** (blood-slide box, plastic burst on the drop, body-bag zipper, blood on the lens, M99 blink, magnifier → pupil loop). The user: "The transitions were creative and well animated."
- `v6/`, *WARMPOP* (Dexter × George Clanton "Warmpop", 9:16): the reference for the **amount and quality of designed transitions, animations and graphics**, how the music drives the structure, and the text. The user: "wonderful transitions, animations, graphics, while maintaining the style that I like… I like how the music correlates to the edit. I like the text."
- `v4/`, *SURPRISE* (Doakes × Need It, 9:16): the reference for dialogue-led openings that play as one continuous take.

**Start with `studio/VOIDFX_STUDIO.md`.** It holds every preference, like, dislike and lesson, the benchmarks, the style bank and the fast workflow. Then read `studio/SCENE_PACKS.md` (every source, the proven shots and dialogue timecodes) and **`docs/TOOLKIT.md`** (engine, transition catalog, pitfalls). Build every new edit on the newest benchmark engine with `python3 tools/new_edit.py N SLUG "TITLE"`, which copies `render11.py`, `audio11.py`, `qc11.py`, `facetrack.py` and `analyze.py`, wired to a new EDL from `tools/edl_template.py` (v10/v11 structure, with the `vel()` speed-ramp helper); it carries every v4–v11 transition and graphic. Rewrite the edit's own `render()` frame function, grade, text and finish. Don't start from scratch, and **don't reuse a benchmark's look**: each edit needs its own style. For a second studio session, see `studio/NEW_STUDIO_SETUP.md`.

## User preferences (learned over several revisions)

- **Format:** 9:16, 1080×1920, 60 fps, TikTok-ready H.264 + AAC with fast-start, plus a high-quality master. About 20–26 s; don't run long.
- **Framing:** faces always centred and never cut off. Face-track every shot (YuNet). Leave out shots whose face is wider than the 9:16 window.
- **Opening:** start strong. Dialogue from the source can open the edit or tie heavily into it. It must play as **one continuous take**: J-cuts, dissolves, a matched-angle morph. Never several clips that feel glued together.
- **No labels:** no name tags, speaker chips or "who is who" graphics. No stamps sitting on top of captions.
- **Text:** every word eases in (fade + rise + blur-to-sharp). Nothing just pops on. **The v9 NIGHT BLOOM text is the approved standard ("it was perfect")**: bold heavy-sans two-line captions with a dark keyline and soft shadow, red emphasis words, word-timed, plus a per-letter designed hero title. Each title or lyric moment gets its own designed animation, and it must be clearly readable (size, contrast, time on screen).
  - Approved examples: footage-in-letters knockout type; a title that fills with blood and drips, then shatters with the glass; light-sweep reveal; fly-in from the camera.
  - Keep text clear of faces and of TikTok's UI areas.
- **Branding:** no constant watermark and no outro card. The voidfx logo (`src/voidfx_logo.webp`) appears **once, as a transition** (e.g. flying through the "o"). **Never recolour, retheme or restyle the logo** (no neon/UV/tint versions). Use the supplied image as-is (`logo_through` / `tin="logo_orig"`) unless the user explicitly asks for a change.
- **Transitions:** pronounced and designed, the kind where the viewer wonders "how did they do that". They should feel like **going through something**: barrel, scope, shattering glass, an eye or pupil, a shadow, the logo's "o", a photo on the wall, a knife slash.
  - Avoid plain hard cuts in quiet or dialogue sections.
  - Every transition gets its own sound.
- **Loop:** the edit must loop seamlessly for TikTok, in picture (e.g. into the pupil to black → iris open from black) and in sound. For sound: room tone and drone continue across the wrap, the timeline is built circularly, mastering runs on a wrapped copy, and audio and video are exactly the same length. An outro card breaks the loop, so don't use one.
- **Sound:** smooth and clean.
  - Dialogue is cleaned and levelled, with equal-power fades at every join.
  - The song is edited on its beat grid; a tape-stop or dead stop is fine for an ending.
  - Mastered to about −13 LUFS with true peak ≤ −2.5 dBTP, measured **after** AAC encoding.
- **Workflow:** the user wants built-in review passes, not repeated rounds of feedback. Before delivering, always run:
  1. automated QC on the **encoded** file (`qcN.py`, from the v6 engine): format/decode, loudness, face centering, text vs faces, cuts, freezes, black frames, audio clicks at every edit, loop seam;
  2. a visual review of contact sheets around every transition and title;
  3. a fix-and-re-render for anything weak;
  4. a final pull of key frames from the encoded file.
- **What v6 got right (do this every time):**
  - one concept tying picture, sound and text together;
  - the song's best part (where the full mix or bass returns) lands on the biggest transition;
  - 15+ designed transitions with no plain cuts;
  - the character's own words as two-line eased captions;
  - graphics that add depth (vapor world tune-in, palm shadows, bokeh, neon light spill, VHS pause).
- **Avoid:** foreign-language subtitle lines (CJK) and on-screen counters or timecodes (the VHS "SP" timer). The user removed both as clutter.
- **Dialogue: less is more.** In v7 the user cut rapid single-word dialogue runs ("Dramatic. Cryptic. Playful."), a talking "jar of blood" shot, and an ending where Dexter just states "I'm a serial killer". Use at most one or two short lines that set up the song (e.g. "Could it be him?" answered by the hook). Let the visuals carry the ending.
- **v8 feedback:**
  - **Liked:** the "Darling," freeze into the comma-drop and blood-in-water transition, the rear-view-mirror open and loop, and the "basic" transitions (streetlight sweep, wiper, whips, plastic wrap, impact frame, rain focus pull, lamp on).
  - **Disliked:** v8's text appearance (thin wide-tracked sans, serif-italic emphasis, letter-by-letter fades). Prefer v6-style bold, high-contrast, two-line captions.
- **v9 feedback (NIGHT BLOOM):** "complete" and "good", but **lacklustre** next to the other builds and Dexter edits in general. The owner's instruction: **go above and beyond with these edits.**
  - **Liked: the text, "it was perfect".** v9's type is now the **standard text style**: reuse it (`text_cap` / `cap_word` / `text_hero` in `v9/work/render9.py`; see the handbook §3), recoloured to each edit's palette but with the same construction and motion.
  - What fell short, so don't repeat it:
    - The hero motif (jasmine petals, a moon) came from the song title, not from Dexter's world. It was soft and pretty where a Dexter edit should be dark and intense. Root the concept and the set pieces in Dexter: kill room, plastic, blood slides, tools, the Code, the Dark Passenger, his victims.
    - Too many quick, generic transitions (strobe, beam, blinds, roll, smear, whip) and too few signature set pieces. **Every edit needs at least three multi-stage, character-themed set pieces** on the level of v7's slide box, plastic burst and zipper, or v8's "Darling," freeze into the falling blood drop. Generic moves are filler between them, not the substance.
    - Thin on graphics compared with v6 and v7: almost no depth graphics or themed overlays in the montage. (The text itself was right; add more designed text moments in that same style.)
    - Reviews fixed defects but didn't raise the ceiling. **Before rendering, compare the plan shot by shot with v6, v7 and v8 and with the best Dexter edits.** If it doesn't clearly beat them, redesign it, then build.
- **v10 standard (LET IT HAPPEN rev 5), do this on every edit:**
  - **Motion pass:** `tmap=vel(...)`, `lin=True`, `interp="flow"` on every hook/montage shot (burst on the beat, smooth slow motion between), the beat camera (zoom punch, rotation kick, hit-frame blur and colour split, type kept clean on top), light rays or another light source that reacts to the footage.
  - **Picture quality:** restore the source with `tools/sr_prep.py` (in the background after prep); never ship a plain 2.7× cubic blow-up of a 720p pack.
  - **Timing:** every lyric word on its sung onset, checked on the vocal stem (pitch + onsets), not just Whisper.
  - **Set pieces from the character's world** on the drop, the hook and the loop, plus signature moves between them; the loop lands exactly on frame 0 (picture seam diff ≤ 1).
  - It was reached through owner notes on rev 1–4 ("lacklustre" twice): the motion pass in rev 5 is what turned it into a standard. Don't stop at effects layered on static shots.
- **v11 standard (BOP rev 4), do this on every edit as well:**
  - **Concept from the material itself:** look for a hook in the song's own words or the character's history (v11: "Harrison" → the Reverse-Flash), and carry it through picture, grade, sound and the loop.
  - **One true focal set piece** the owner can point to (v11: THE RIFT), multi-stage, with its own layered sound, on a structural moment (a bar line after a build).
  - **Detailed, physical assets:** build hero graphics as lit, bevelled procedural assets matched to the shot's light (the Reverse-Flash emblem), and reveal them physically on the real object (the coin flip on the tracked emblem). Check them at full resolution.
  - **No "just moving to the beat" shots:** give each one its own beat animation (aura rings, time remnants, a charge-up), each with its own sound.
  - **The loop lands exactly:** build the last frames from frame 0's own image and measure the seam (blurred diff ≤ 1).
  - **Flash discipline:** measure the brightness of every flash in the encode. A flare should keep the picture (v11's rim flash went from mean luma 178 to 104).
  - **Few words when the lyrics are explicit:** two designed titles, not captions.
- **No "gimmick on the face" effects** (e.g. lines converging on his face with a target ring). Transitions should be physical and themed (slide box, plastic burst, zipper, blood on the lens), not overlays on his face.
- **Props and effects (Studio 2, after FOREVER):** blood slides and the knife across the screen are **no longer banned**. In FOREVER they failed because they lingered (slides drifting round the opening as a constant overlay), were random (drips, spatter and the knife pass on beats with no reason in the shot), looked drawn (flat red circles on grey glass), and didn't land (a glass-shatter web over his face, duct-tape strips that fell flat). Use blood, slides, knives, glass or tape only when they are motivated by the shot, lyric or story; brief; lit like real objects or taken from real footage (the S1 shot of him holding up a slide); in the edit's own look; and off his face. Check each on stills next to the footage and rebuild or cut anything that looks drawn. The v7 blood-slide box and blood on the lens worked. (v10 rev 4 applied this: the frozen-scene glass shatter was replaced.)
- **Efficiency:** the user asks for quality *and* efficiency. Use the fast loop in `docs/TOOLKIT.md`:
  1. song map;
  2. EDL;
  3. `build.sh N prep auto` (review sheets of every cut);
  4. `clip:A:B` for motion;
  5. `audio`;
  6. **one** `video qc` per revision.
  - Check the pitfalls list there before building transitions.
- **Honesty:** you cannot watch or listen. Report what was verified by frames and measurement, and ask the user to watch once with sound.
- **Communication:** short progress updates; no long code in chat.

## Project conventions

- Sources go in `src/` (read-only copies). Each edit gets its own folder (`vN/work`, `vN/out`, ...).
- One EDL file per edit holds every decision, and the renderer reads only that file. The EDL also sets `VER`, `SLUG` and `SONG`, plus the engine knobs (`DROP_TITLE`, `MONTAGE`, `VANISH_T0`, `VO_STEM`, `CAPS`, `END_CAP`); the template is `tools/edl_template.py`.
- Tools: `tools/new_edit.py` (scaffold), `tools/song_map.py` (beat grid, drops, candidate windows), `tools/transcribe.py` (word times), `tools/check_sources.py` (source-range audit), `tools/build.sh` (prep / auto / audio / clip / preview / video / qc), `tools/sr_prep.py` (restores and 2× upscales the 720p source bands an edit uses; run in the background after prep), `tools/setup_studio.sh` (deps, models, source-library check).
- Two studios: each works on its own branch with its own version range (Studio 1 `v8+`, Studio 2 `v101+`); see `studio/NEW_STUDIO_SETUP.md`.
- Media (`src/`, audio, frames, outputs, models) stays out of git. Commit the code, EDL, transcripts, tracks and README, then push to the session's branch.
- Models are downloaded at runtime: YuNet (`v3/models/face_detection_yunet_2023mar.onnx`), MODNet (`Xenova/modnet`), faster-whisper large-v3 for dialogue and lyric timing, and the Real-ESRGAN compact weights (`v3/models/realesr-general-x4v3.pth` and `realesr-general-wdn-x4v3.pth` from the xinntao/Real-ESRGAN v0.2.5.0 release; loaded tensors-only and exported to ONNX by `tools/srnet.py`).
- The older guide `7b769aa4-TIKTOK_EDITING_GUIDE.md` (the beat-grid, colour and QC methods) still applies where it doesn't conflict with this file.
