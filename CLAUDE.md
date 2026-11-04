# voidfx edit standard

**THE STANDARD: `v103/`, *FOREVER* (Dexter × Foo Fighters "Everlong", rev 5, Studio 2).** The owner: *"I like this edit. I would like for you to make it a standard."* Every new edit starts from it (`tools/new_edit.py` copies its engine, toolkit and EDL) and must **exceed** it on two counts the owner named: **more animations and transitions**, and **lyric recognition**. See the handbook §0.
- What it is: a concept from Dexter's world ("How is it I can kill people and feel no regret?"; he keeps every kill forever, the Gulf Stream keeps the rest); three multi-stage set pieces (THE RIP: kill-room plastic tears open on the drop; THE EVIDENCE PHOTOS: the ring flash fires on "IF" and the frame is tossed away as a photo; THE GULF STREAM: the loop sinks and surfaces in the same water); 20 designed transitions in 24 s, each with its own sound (eye dive, flashlight blind-out, camera shutter, flash-photo toss, water ripple, sea spray, rain focus, zipper, logo, bubbles); the camera punching on every beat; graphics in every hold (caustics, marine snow, heartbeat pulse, swinging lamp, anamorphic flare); the narrated line as voice-over; and **every clearly sung lyric captioned word by word on its sung time** in the v9 style.
- **The owner's note for every edit from now on:** *"more animations and transitions moving forward, and that lyric kind of recognition."* In numbers:
  - at least 24 designed transitions per ~24 s (FOREVER had 20);
  - beat-synced camera animation through every section with drums;
  - a designed animation inside any hold longer than about a second;
  - the song window chosen so its lyrics are on screen;
  - every clearly sung line captioned on its words (`tools/lyrics.py`), with key moments landing on sung words.

**Earlier benchmarks (approved as standards; FOREVER builds on them):**
- `v7/`, *HIM ALL ALONG* (Dexter × Gunna "Him All Along", rev 2): the newest engine, and the reference for **creative, well-animated, character-themed transitions** (blood-slide box, plastic burst on the drop, body-bag zipper, blood on the lens, M99 blink, magnifier → pupil loop). The user: "The transitions were creative and well animated."
- `v6/`, *WARMPOP* (Dexter × George Clanton "Warmpop", 9:16): the reference for the **amount and quality of designed transitions, animations and graphics**, how the music drives the structure, and the text. The user: "wonderful transitions, animations, graphics, while maintaining the style that I like… I like how the music correlates to the edit. I like the text."
- `v4/`, *SURPRISE* (Doakes × Need It, 9:16): the reference for dialogue-led openings that play as one continuous take.

**Start with `studio/VOIDFX_STUDIO.md`.** It holds every preference, like, dislike and lesson, the benchmarks, the style bank and the fast workflow. Then read `studio/SCENE_PACKS.md` (every source, the proven shots and dialogue timecodes) and **`docs/TOOLKIT.md`** (engine, transition catalog, pitfalls). Build every new edit on the standard with `python3 tools/new_edit.py N SLUG "TITLE"`. It copies the v103 engine (`render103.py` with every v4–v9 transition, `audio103.py`, `qc103.py`, `facetrack.py`, `analyze.py`), plus `fx103.py` as the edit's own `fxN.py` section (spliced in by `splice.py`) and FOREVER's EDL as the worked template. The scaffold renders FOREVER pixel-for-pixel until you change it. Restyle the edit's own grade, palette, set pieces, text colours and finish in `fxN.py`. Don't start from scratch, and **don't reuse a benchmark's look**: each edit needs its own style. For a second studio session, see `studio/NEW_STUDIO_SETUP.md`.

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
- **Studio 2 feedback (v101, v102):**
  - **v101 THE LESS YOU KNOW:** the style was largely disliked (16 mm psychedelic look, 70s serif type). Some transitions were good.
  - **Lip-sync must be real.** v101 put Dexter's *narrated* line over a shot where he isn't speaking, and the owner rejected it. Present a line as spoken only when his lips match it. Check with `tools/lipcheck.py` and on frames; otherwise play it as voice-over.
  - **v102 LET GO (The Flash):** good and complete, but **lacklustre** next to the other builds. The gaps were the same as v9's: the concept, the number of standout set pieces, and graphics that read at phone size. Clear the §5a gate.
- **v103 FOREVER feedback (Studio 2, five revisions, then approved as the standard):**
  - **Rev 1 → 2:**
    - A narrated line that ended mid-sentence sounded "cut off". Pick lines that end on a full stop or question with silence after them.
    - A soft, low-quality shot was swapped out. Check every shot at full resolution.
    - Captions on parts where the song wasn't singing were rejected. **Text only on clearly sung or spoken words**, each on its time.
    - The owner asked for more transitions, animations and graphics, with very little dead space.
  - **Rev 3 to 5, rejected; don't use these again:**
    - blood slides drifting around the frame;
    - random blood drips from the top edge and blood-spatter hits;
    - a big knife slicing across the lens;
    - the scalpel-cut / blood-bead / slide-smear drop;
    - the drawn corridor of blood slides;
    - a glass shatter;
    - duct-tape strips.
    Blood and slide **graphics** read as clutter or as cheap next to the footage. Keep blood to what is in the footage and the grade.
  - **What replaced them and stayed:**
    - the plastic rip on the drop;
    - the evidence-camera flash and photo toss on the lyric;
    - the camera shutter;
    - the eye dive (into the pupil, a round iris opens);
    - the flashlight blind-out (a light in the shot flares into the lens and the next shot burns in);
    - a clear water-drop ripple;
    - beat punches.
    Transitions motivated by something in the shot or the lyric are the ones that land.
- **No "gimmick on the face" effects** (e.g. lines converging on his face with a target ring). Transitions should be physical and themed (slide box, plastic burst, zipper, blood on the lens), not overlays on his face.
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
- Tools: `tools/new_edit.py` (scaffold from the v103 standard), `tools/song_map.py` (beat grid, drops, candidate windows), `tools/lyrics.py` (lyric recognition: Demucs vocals + Whisper word times aligned to the published lyrics, with a ready caption block), `tools/transcribe.py` (dialogue word times), `tools/check_sources.py` (source-range audit), `tools/build.sh` (prep / auto / audio / clip / preview / video / qc), `tools/setup_studio.sh` (deps, models, source-library check).
- Two studios: each works on its own branch with its own version range (Studio 1 `v8+`, Studio 2 `v101+`); see `studio/NEW_STUDIO_SETUP.md`.
- Media (`src/`, audio, frames, outputs, models) stays out of git. Commit the code, EDL, transcripts, tracks and README, then push to the session's branch.
- Models are downloaded at runtime: YuNet (`v3/models/face_detection_yunet_2023mar.onnx`), MODNet (`Xenova/modnet`), and faster-whisper large-v3 for dialogue and lyric timing.
- The older guide `7b769aa4-TIKTOK_EDITING_GUIDE.md` (the beat-grid, colour and QC methods) still applies where it doesn't conflict with this file.
