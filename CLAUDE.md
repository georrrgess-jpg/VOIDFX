# voidfx edit standard

**THE STANDARDS: `v105/` *DRACULA* (the newest), `v104/` *THE PASSENGER* and `v103/` *FOREVER* (Studio 2).** Every new edit starts from DRACULA: `tools/new_edit.py` copies its engine, its toolkit (which also carries all of THE PASSENGER's and FOREVER's) and its EDL. Every new edit must **exceed all three**. See the handbook §0.

**`v105/`, *DRACULA*** (Dexter × Tame Impala "Dracula", rev 3). The owner: *"I like this edit and would like for you to make it a standard."*
- **The concept, SUNDOWN:** by day he wears the mask (sunny Miami, the boat, the smile). The last chorus is "run from the sun like Dracula", so the sun sets across the song's one-bar drop-out and night slams in on the drop. At the end the sun takes him.
- **The look:** two looks split on the drop. By day, a bleached warm postcard with the sun **behind him** (his matte, a light wrap on his edge, sunlit dust). By night, cold moonlit silver where only crimson survives.
- **Set pieces:**
  - SUNDOWN with an **eclipse**;
  - THE BAT BURST on the drop, with the per-letter "DRACULA" breaking into bats;
  - THE BLOOD MOON behind his cut-out;
  - THE COFFIN;
  - **ASHES TO SUN, the loop:** he burns like paper, his embers spiral into the sun (frame 0's sun), it flares, and the light collapses into it on the opening shot.
- **Motion:** 27 designed transitions in 23 s, each with its own sound. New this edit: sun flare, card flip, palm sweep, eclipse, bat burst, moon iris, cape, coffin, mist, bat swarm, great bat.
- **Animation:** gathering bats, fog, a crimson backlight, a camera float, beat punches, and speed ramps with ghost trails.
- **Captions:** only the words verified on the vocal stem, on their sung times.
- **The owner's one gripe, a rule from now on:** *"The only gripe I have is the quality of some of the clips."* **Clip quality:**
  - **Every library pack is 720p** (even `pack7_4k`), and several are heavily compressed:
    - p8 (S1) at 0.43 Mb/s;
    - p9, p6 and p10 at about 0.7 Mb/s.
    So every 9:16 crop is enlarged about 2.8×.
  - **Check sharpness twice:** run `tools/sharpness.py N --src` while choosing shots, and `tools/sharpness.py N` on the render. Swap anything flagged SOFT for a sharper moment or pack.
  - **Keep zoom at or under about 1.1** on 720p sources.
  - **Prefer the high-bitrate packs:** p5, p7, p3, p4 and scenepack2 (1.7–2.2 Mb/s).
  - **Ask the owner for 1080p or 4K packs** for the hero shots.
  - **Limits of the tools:** the upscale pass (Lanczos plus noise-gated detail) can't invent detail, and an AI upscaler (Real-ESRGAN class) needs a GPU (about 10 s a frame on this CPU).
  - **v105's softest shots:**
    - the daybreak walk (p9, zoom 1.3, 3.5×);
    - the palms (p10);
    - the lollipop (p8);
    - then the ice cream (p1), hood (p3) and pink-wall (p5) shots.

**`v104/`, *THE PASSENGER*** (Dexter × GLM-RST "still love you (super slowed + reverb)", rev 3). The owner: *"I really like this edit and would like for it to be a standard."*
- **The concept:** "I like to pretend I'm alone. Completely alone." Then "I have a dark side, too." The ink is his Dark Passenger.
- **The look:** SUMI ink wash (ivory paper, ink-blue blacks, only strong reds kept as red ink). One grade unifies five seasons of footage.
- **The opening:** an ink sketch of him draws itself on the paper. A drop falls and blooms into him on the bass entry.
- **Set pieces on every phrase start:**
  - the spatter on his suit;
  - THE PASSENGER: a light comes on, his shadow is thrown on the wall, ember eyes open on "DARK", and it lunges at the lens;
  - the silhouette window into the kill room;
  - the ink-out loop back into the drop.
- **Motion:** 26 designed cuts in 23 s. The upside-down roll and a quarter-turn make rotation a motif. A page turn, ivory and red brush strokes, and the shared standard pieces (eye dive, flashlight blind-out, zipper).
- **Animation:** a camera float on every hold, motion-blurred beat punches on the sub-bass, speed ramps with ink ghost trails, ink motes, and a breathing vignette. Every transition and set piece has its own sound.
- **The owner liked:** the upside-down shot and the roll into it; the rebuilt dark-side moment.
- **The owner's one gripe, a rule from now on:** *"one span of the edit had some headspace that definitely could have had an edit or a cool transition."* **No headspace: no span longer than about a second without a cut, a transition or a designed beat**, even inside a set piece or a dialogue hold. v104's longest spans, all candidates (the owner didn't say which): the pickup 1.60 s, the dark-side shot 1.60 s, the final shot 1.31 s, the floor shot 1.20 s, and the dock, spatter and silhouette shots at 1.07 s each. Plan a cut or a beat inside anything that long.

**`v103/`, *FOREVER*** (Dexter × Foo Fighters "Everlong", rev 5). The owner: *"I like this edit. I would like for you to make it a standard."* New edits must **exceed** it on two counts the owner named: **more animations and transitions**, and **lyric recognition**.
- What it is: a concept from Dexter's world ("How is it I can kill people and feel no regret?"; he keeps every kill forever, the Gulf Stream keeps the rest); three multi-stage set pieces (THE RIP: kill-room plastic tears open on the drop; THE EVIDENCE PHOTOS: the ring flash fires on "IF" and the frame is tossed away as a photo; THE GULF STREAM: the loop sinks and surfaces in the same water); 20 designed transitions in 24 s, each with its own sound (eye dive, flashlight blind-out, camera shutter, flash-photo toss, water ripple, sea spray, rain focus, zipper, logo, bubbles); the camera punching on every beat; graphics in every hold (caustics, marine snow, heartbeat pulse, swinging lamp, anamorphic flare); the narrated line as voice-over; and **every clearly sung lyric captioned word by word on its sung time** in the v9 style.
- **The owner's note for every edit from now on:** *"more animations and transitions moving forward, and that lyric kind of recognition."* In numbers:
  - at least 24 designed transitions per ~24 s (FOREVER had 20);
  - beat-synced camera animation through every section with drums;
  - a designed animation inside any hold longer than about a second;
  - the song window chosen so its lyrics are on screen;
  - every clearly sung line captioned on its words (`tools/lyrics.py`), with key moments landing on sung words.

**Newest benchmark from Studio 1: the Flash edit approved in chat 1.** Recorded here from the owner's notes; the version number, title, song and folder weren't passed to Studio 2. Studio 1's CLAUDE.md, handbook, toolkit and start prompt name it as the newest benchmark and quote the owner's approval. Every edit must match or beat it, alongside v7, v6 and v4 (and Studio 2's standards above).
- **Its specialty is motion and finish:**
  - speed ramps with smooth slow motion;
  - the beat-synced camera;
  - light rays;
  - the multi-stage set pieces;
  - the Speed Force loop.
- **The lesson:** two rounds of "lacklustre" on it were fixed by **the motion pass, not by adding more effects**.
- **Where the code is:** the motion pass and the 720p upscaling are implemented on Studio 1's branch (`claude/gallant-planck-pqpczp`). Fetch them from there before using them; this Studio 2 copy only records the rules.

**Rules from the Flash benchmark (every edit, both studios):**
1. **A motion pass on every hook shot:** speed ramps, smooth slow motion where it's earned, and beat-synced camera moves, before adding any more effects.
2. **Upscale the 720p source:** every pack is 1280×720 and a 9:16 crop is about 405 px wide, so upscale properly rather than stretching the crop.
3. **Lyrics checked against the sung vocal:** the isolated Demucs vocal plus the published lyrics (`tools/lyrics.py` in Studio 2).
4. **Designed set pieces on the drop, the hook and the loop.**
5. **A loop that lands exactly on the first frame**, in picture and in sound.
- **Smooth slow motion vs. interpolation artefacts:** the owner also asked (v104 brief) to *"avoid introducing visible interpolation artifacts."* Use flow-interpolated slow motion only where it stays clean, and check those frames one by one. On fast motion or occlusions, prefer a held 24p cadence, a speed ramp that stays at 1x or faster, or a cut.

**Earlier benchmarks (approved as standards; FOREVER builds on them):**
- `v7/`, *HIM ALL ALONG* (Dexter × Gunna "Him All Along", rev 2): the newest engine, and the reference for **creative, well-animated, character-themed transitions** (blood-slide box, plastic burst on the drop, body-bag zipper, blood on the lens, M99 blink, magnifier → pupil loop). The user: "The transitions were creative and well animated."
- `v6/`, *WARMPOP* (Dexter × George Clanton "Warmpop", 9:16): the reference for the **amount and quality of designed transitions, animations and graphics**, how the music drives the structure, and the text. The user: "wonderful transitions, animations, graphics, while maintaining the style that I like… I like how the music correlates to the edit. I like the text."
- `v4/`, *SURPRISE* (Doakes × Need It, 9:16): the reference for dialogue-led openings that play as one continuous take.

**Start with `studio/VOIDFX_STUDIO.md`.** It holds every preference, like, dislike and lesson, the benchmarks, the style bank and the fast workflow. Then read `studio/SCENE_PACKS.md` (every source, the proven shots and dialogue timecodes) and **`docs/TOOLKIT.md`** (engine, transition catalog, pitfalls). Build every new edit on the standard with `python3 tools/new_edit.py N SLUG "TITLE"`. It copies the v105 engine (`render105.py` with every v4–v9 transition, `audio105.py`, `qc105.py`, `facetrack.py`, `analyze.py`, `big.py`), plus `fx105.py` as the edit's own `fxN.py` section (the FOREVER, THE PASSENGER and DRACULA toolkits, spliced in by `splice.py`) and DRACULA's EDL as the worked template. The scaffold renders DRACULA pixel-for-pixel until you change it (checked on 10 frames across the set pieces and the loop). Restyle the edit's own grade, palette, set pieces, text colours and finish in `fxN.py`. Don't start from scratch, and **don't reuse a benchmark's look**: each edit needs its own style. For a second studio session, see `studio/NEW_STUDIO_SETUP.md`.

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
  - **Rev 3 to 5, replaced because of how they looked in FOREVER.** These ideas are **not banned**. The owner: *"I didn't necessarily hate the blood slide or the knife across the screen, I just don't like how it looked in this specific edit"* (v7's blood-slide box and blood on the lens were liked). What went wrong was the execution:
    - **Lingering:** blood slides drifted around the cold open as a constant overlay ("stick around").
    - **Random:** blood drips and spatter hits fell on beats with no reason in the shot, and the knife pass swept across the lens mid-montage, unmotivated.
    - **Looked drawn, not real:** the slide smear on the drop and the corridor of slides were flat red discs on grey glass, cheap next to the footage and outside the edit's water look.
    - **Didn't land:** the glass shatter (a shard web over his face) and the duct-tape strips.
    - **The lesson:** blood, slides and knives are welcome when they are **motivated** (by the shot, the lyric or the story), **brief** (in and out, never parked on screen), **photographic or physically lit** (real refraction, gloss and shadow; or real footage, like the S1 slide shot), **part of the edit's own look**, and off his face. Judge them on stills next to the footage; if one reads as a drawn graphic, rebuild it or cut it.
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
- Tools: `tools/new_edit.py` (scaffold from the v105 standard), `tools/sharpness.py` (clip quality: soft, over-zoomed and low-bitrate shots, before and after the render), `tools/song_map.py` (beat grid, drops, candidate windows), `tools/lyrics.py` (lyric recognition: Demucs vocals + Whisper word times aligned to the published lyrics, with a ready caption block), `tools/transcribe.py` (dialogue word times), `tools/check_sources.py` (source-range audit), `tools/build.sh` (prep / auto / audio / clip / preview / video / qc), `tools/setup_studio.sh` (deps, models, source-library check).
- Two studios: each works on its own branch with its own version range (Studio 1 `v8+`, Studio 2 `v101+`); see `studio/NEW_STUDIO_SETUP.md`.
- Media (`src/`, audio, frames, outputs, models) stays out of git. Commit the code, EDL, transcripts, tracks and README, then push to the session's branch.
- Models are downloaded at runtime: YuNet (`v3/models/face_detection_yunet_2023mar.onnx`), MODNet (`Xenova/modnet`), and faster-whisper large-v3 for dialogue and lyric timing.
- The older guide `7b769aa4-TIKTOK_EDITING_GUIDE.md` (the beat-grid, colour and QC methods) still applies where it doesn't conflict with this file.
