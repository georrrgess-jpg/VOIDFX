# voidfx edit standard

**Two studios, one code base (`dev/pipeline-v2`, merged 2026-11-07).** The Flash studio (Studio 1, v10–v12+) and the Dexter studio (Studio 2, v101–v107+) share this repo. **Engine bases: Flash edits start from v12 (since the v12 BLOOM verdict, 2026-11-08; was v11), Dexter edits from v107 (since the v107 ALL CAPS verdict, 2026-11-08; was v105)** (`python3 tools/new_edit.py N SLUG "TITLE" --base v12|v11|v107|v105`; without `--base`, a title or slug mentioning Dexter gets v107, anything else v12). Where the two studios' records below overlap, both are kept and labelled; the newer owner verdict wins on a conflict.

**Read first (since 2026-11-08, the efficiency update): `studio/OWNER_RULES.md`** (every owner rule still in force, on one page, newest verdict wins) **and `studio/WORKFLOW.md`** (the fast loop). Before any render, `bash tools/build.sh N plan` checks the EDL against the owner's recurring notes (rejected transitions from `studio/transitions.json`, black occluders, a reused or look-alike clip, spin landings, the loop, a signature graphic transition, the hero as a motif, density, spell-out grid, holds, the sound budget) and `video` stops on a FAIL. One command per revision: `bash tools/build.sh N ship` (audio → plan → video → parallel QC → `signoff` pages from the encode → `report` → deliver). Before delivering, review the sign-off pages and run the fresh-eyes critique (`studio/CRITIQUE_PROMPT.md`). Stills only through the render server (`build.sh N sheet:NAME:f,f`, ~4 s warm), never a scratch script. Plan and measurements: `sync/EFFICIENCY_PLAN.md`.

<!-- Flash studio (Studio 1) -->
**Benchmarks (all approved by the user as the standard for new edits; match or exceed them):**
- `v107/`, *ALL CAPS* (Dexter × Madvillain "All Caps", rev 4; the Dexter studio): **the newest Dexter standard and the engine every new Dexter edit is built on** (`--base v107`: the v12 engine with the restored-source sampler, plus the v107 toolkit). The reference for **a concept from the song's hook word carried by one object** (the name: printed under the BUTCHER headline, stamped in letterpress, flown into the sky as the real WE ♥ DEXTER banner, spelled by the crowd's confetti for the loop), **physical, kinetic transitions** (plastic rip, hot molasses, a headspin landing on a centred face, the front page, a newspaper page turn), **a spell-out on an even rhythm grid**, and **what the owner rejects**: black occluders (letterbox bars, a TV in a dark room, redaction boxes) and graphics converging on a face. The 3 s slot took four tries and ended as a clean downbeat cut. The user: "I like this edit make it a standard." Handoff: `sync/handoffs/2026-11-08_dexter_v107_ALL_CAPS_standard.md`.
- `v12/`, *BLOOM* (The Flash × fakemink "Night Blooming Jasmine", rev 3): **the newest standard and the engine every new Flash edit is built on.** The reference for **one hero asset carried through the edit, an emblem transition on the real tracked emblem, a transition built on a real phenomenon, and restraint in text and sound**:
  - concept LIGHTNING BLOOM: "night blooming" = the night Barry was struck; a procedural five-petal lightning jasmine with Lichtenberg veins runs bud → bloom → full bloom → closing;
  - THE BLOOM out of his pupil on the drop; FULL BLOOM behind him with a light wrap; FRACTAL BURN; EMBLEM BLOOM; a closing-bud dive onto frame 0 (seam 0.19);
  - the NOCTURNE look; **no text**; 37 effects.
  
  The user: "I like this edit make it a standard." Handoff: `sync/handoffs/2026-11-08_flash_v12_BLOOM_standard.md`.
- *v106 WONDERWALL* (The Flash × Oasis "Wonderwall", rev 3): **a Flash standard made as a one-off in the Dexter chat** (`v106/`, built on the v11 engine; merged into this branch with `dev/pipeline-v2` on 2026-11-08). The reference for:
  - **a story concept from a lyric line and the show's history:** "Maybe you're gonna be the one that saves me" = Iris bringing Barry back from the Speed Force (S3 finale → S4 premiere);
  - **sound restraint:** 28 → 14 sound moments; transitions may be silent; the song carries the ending;
  - **a loop that lands exactly and keeps moving:** the Speed Force mist dissolves into frame 0's own picture, its drift continuous across the wrap (seam 0.14);
  - **a measured hunt for dead spans, pops and judder before delivery** (`tools/motionqc.py` here);
  - signature pieces: TEAR LENS (Barry's goodbye inside Iris's falling tear), THE WONDERWALL (a wall of tiles cut from the edit's own frames that rises behind him and bursts toward the camera), the lightning rod, the Speed Force mist.

  The user: "I like this edit make it a standard." Handoff: `sync/handoffs/2026-11-08_dexter_v106_WONDERWALL_standard.md`.
- *v107 ALL CAPS* (Dexter × Madvillain "All Caps", rev 4; the Dexter studio, `v107/`, merged into this branch with `dev/pipeline-v2` on 2026-11-08): **the newest Dexter standard and the Dexter scaffold** (`new_edit.py N SLUG "TITLE" --base v107`, built on our v12 engine). The owner: *"I like this edit make it a standard."* The reference for:
  - a concept from the song's hook word carried by one object: the name is printed, stamped and flown into the sky as the real WE ♥ DEXTER banner, then spelled by the crowd's confetti for the loop;
  - a focal set piece that becomes a real object in the footage;
  - spell-outs on an even rhythm grid;
  - what the owner rejects: four tries at one 3 s slot (a press flash, a TV in a dark room read as black bars, a POINT OF ORIGIN graphic converging on his face, redaction boxes). The approved answer was a clean downbeat cut.

  Handoff: `sync/handoffs/2026-11-08_dexter_v107_ALL_CAPS_standard.md`.
- `v11/`, *BOP* (The Flash × DaBaby "BOP", rev 4): the previous standard (its engine is inside v12's). The reference for **concept, focal set pieces and the loop**: a concept taken from the song's own words (the intro's "Harrison" → the Reverse-Flash rivalry, red vs gold in two grades), very few but designed titles (LET'S GO, BOP), a true focal set piece (THE RIFT: a tear across the frame into the Speed Force, flown through), a detailed procedural emblem revealed physically (the real chest emblem coin-flips into the Reverse-Flash's), beat moments instead of "just moving to the beat" (aura, time remnants, charge-up), and a loop set piece that lands exactly on frame 0 (seam 0.11). The user: "I like this edit and would like for you to make it a standard."
- *v105 DRACULA* (Dexter × Tame Impala "Dracula", rev 3; the Dexter studio, `v105/`, here since the 2026-11-08 merge of `dev/pipeline-v2`): approved as a standard, *"I like this edit and would like for you to make it a standard. The only gripe I have is the quality of some of the clips."* The Dexter studio scaffolds from it. Concept **SUNDOWN** from the lyric "run from the sun like Dracula" mapped onto Dexter's double life (day mask / night hunt); two grades split on the drop; five set pieces (SUNDOWN eclipse, BAT BURST, BLOOD MOON, COFFIN, ASHES TO SUN loop); 27 transitions in 23 s. Full handoff: `sync/handoffs/2026-11-07_dexter_v105_DRACULA_standard.md`.
- `v106/`, *WONDERWALL* (The Flash × Oasis "Wonderwall", rev 3; made in the Dexter chat on the v11 engine): *"I like this edit make it a standard."* The reference for **a story concept from a lyric line and the show's history** ("you're gonna be the one that saves me": the S3 finale into the Speed Force, Iris bringing him back), **a focal set piece built from the edit's own frames** (THE WONDERWALL rises behind him and the frame bursts into its tiles on the word), **a custom graphic transition with the reverse shot inside it** (Iris's tear holds Barry's goodbye and we fall through it), **sound restraint** (half the effects cut and approved), and **a loop that lands exactly and keeps moving** (seam 0.14). Rules: "v106 standard" below.
- `v10/`, *LET IT HAPPEN* (The Flash × Tame Impala "Let It Happen", rev 5): the standard for **motion and professional finish** (its engine is inside v11's). The reference for **motion and professional finish**: velocity ramps on every hook shot (a burst on each beat, optical-flow slow motion between, on restored 2× source), a camera that moves with the music (zoom punches, rotation kicks, hit-frame blur), light rays from the lightning, multi-stage character set pieces (emblem dive into the drop wave, time particles, lens shatter, lightning branches, the perimeter lap, phase, whirlwind), bullet time in frozen holds, lyric text on the sung onsets, and a loop that is a set piece (the AROUND ring opens into the Speed Force and flies back through the edit to frame 0). The user: "I like this edit and would like for you to make it a standard."
- `v7/`, *HIM ALL ALONG* (Dexter × Gunna "Him All Along", rev 2): the reference for **creative, well-animated, character-themed transitions** (blood-slide box, plastic burst on the drop, body-bag zipper, blood on the lens, M99 blink, magnifier → pupil loop). The user: "The transitions were creative and well animated."
- `v6/`, *WARMPOP* (Dexter × George Clanton "Warmpop", 9:16): the reference for the **amount and quality of designed transitions, animations and graphics**, how the music drives the structure, and the text. The user: "wonderful transitions, animations, graphics, while maintaining the style that I like… I like how the music correlates to the edit. I like the text."
- `v4/`, *SURPRISE* (Doakes × Need It, 9:16): the reference for dialogue-led openings that play as one continuous take.

**Start with `studio/VOIDFX_STUDIO.md`.** It holds every preference, like, dislike and lesson, the benchmarks, the style bank and the fast workflow. Then read `studio/SCENE_PACKS.md` (every source, the proven shots and dialogue timecodes) and **`docs/TOOLKIT.md`** (engine, transition catalog, pitfalls). Build every new edit on the newest benchmark engine with `python3 tools/new_edit.py N SLUG "TITLE"`, which copies `render12.py`, `audio12.py`, `qc12.py`, `facetrack.py` and `analyze.py`, wired to a new EDL from `tools/edl_template.py` (v10/v11 structure, with the `vel()` speed-ramp helper); it carries every v4–v12 transition and graphic (put the new edit's sections above `# >>> pipeline v2: speed` with `tools/splice_section.py`). Rewrite the edit's own `render()` frame function, grade, text and finish. Don't start from scratch, and **don't reuse a benchmark's look**: each edit needs its own style. For a second studio session, see `studio/NEW_STUDIO_SETUP.md`.

<!-- Dexter studio (Studio 2) -->
**THE STANDARDS: `v107/` *ALL CAPS* (the newest; see the benchmark above and the v107 rules below), `v105/` *DRACULA*, `v104/` *THE PASSENGER* and `v103/` *FOREVER* (Studio 2).** Since 2026-11-08 every new Dexter edit starts from ALL CAPS (`tools/new_edit.py --base v107`: the v12 engine, the v107 toolkit in `fxN.py`, v107's EDL as the worked template; re-splice with `tools/splice_section.py N vN/work/fxN.py --replace`). The v105 base (`--base v105`) still works and carries DRACULA's, THE PASSENGER's and FOREVER's toolkits. Every new edit must **exceed all four**. See the handbook §0.

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
  - **Limits of the tools:** Studio 2's upscale pass (Lanczos plus noise-gated detail) can't invent detail. Studio 1's `tools/sr_prep.py` (Real-ESRGAN compact, 2×, on the CPU) restores the sources and is the fix (see Studio 1's rules below). The large Real-ESRGAN model tried in v105 took about 10 s a frame on the CPU; the compact one is practical.
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

**Workflow from 2026-11-07: two voidfx chats as a coalition.**
- **Roles:**
  - the Flash studio is Studio 1 (v12 onward; its chat works on branch `claude/gallant-planck-pqpczp`);
  - the Dexter studio is Studio 2 (v106 onward; its chat works on `dev/pipeline-v2`).
- **Report format:** both studios write the same 9-section report: verdict, the edit, creative process, revision history, what made it good or bad, caught by review, rules (marked *new*, *changed* or *confirmed*), techniques described well enough to rebuild without the code, and measured numbers. The Flash studio's version of the procedure is in Drift-Master `voidfx-studio-kit/sync/FLASH_STUDIO_EXCHANGE.md`.
- **Conflicts:** when two rules conflict, the newer owner verdict wins; record what it replaces. Shared decisions (the scaffold base, tools with the same name) are the owner's, and are recorded in both chats.
- **Which chat is which:** this file is shared by both chats (one toolchain on `dev/pipeline-v2`, merged into the Flash branch). A chat is the studio its branch and brief say: the chat on `claude/gallant-planck-pqpczp` is the Flash studio, the chat on `dev/pipeline-v2` the Dexter studio. Sections written by one studio say "this chat" or "ours" for themselves; read them by their studio label. The Dexter studio makes every Dexter edit (v106 onward); the Flash studio every Flash edit.
- **The loop:**
  - the owner sends the song (and maybe scene packs);
  - the studio builds;
  - review rounds follow (every note applied in one pass);
  - then a verdict: "good / make it a standard", or "bad, because…".
- **On every verdict, in the same turn, write a handoff.** It goes in Drift-Master `voidfx-studio-kit/sync/handoffs/YYYY-MM-DD_dexter_vNNN_TITLE_<standard|rejected>.md`, follows `sync/HANDOFF_TEMPLATE.md`, and covers:
  - the verdict verbatim;
  - the edit at a glance;
  - the creative process;
  - each revision (note, diagnosis, change, what failed);
  - what made it good or weak;
  - measurements;
  - new rules with evidence;
  - reusable assets;
  - notes for the other studio.
  Then add it to `data/edits.json`, `data/preferences.json` and `sync/LEDGER.md`, update the handbooks, commit and push, and send the owner the file.
- **When the owner brings a handoff from the other chat:** adopt its rules (noting which apply to Dexter), file it, add it to the ledger, commit and push, and confirm briefly what was adopted.
- **The full procedure** is in `voidfx-studio-kit/sync/README.md` (Drift-Master).

**Studio 1's standards as of 2026-11-07: `v11/` *BOP* and `v10/` *LET IT HAPPEN*** (since then: v12 BLOOM, the Flash base, and v106 WONDERWALL; see the benchmarks above). These are recorded from the owner's notes and checked against Studio 1's branch (`claude/gallant-planck-pqpczp`, read at `122013b`), where the code lives. Studio 1's CLAUDE.md, handbook, toolkit and start prompt list BOP first and quote the owner's approval. Every edit must match or beat both, alongside v7, v6 and v4 and Studio 2's standards above.
- **`v11/`, *BOP*** (The Flash × DaBaby "BOP", rev 4): *"I like this edit and would like for you to make it a standard."* It is Studio 1's newest benchmark and the base engine of its scaffold. It's the reference for:
  - **a concept found in the song itself:** the intro's "Harrison" becomes the Reverse-Flash rivalry, red against gold in two grades;
  - **a single focal set piece:** THE RIFT, a tear across the frame into the Speed Force, flown through;
  - **detailed graphics revealed on real objects:** the real chest emblem coin-flips into a lit, bevelled Reverse-Flash emblem;
  - **an animation for every shot that only moved to the beat:** aura rings, time remnants, a charge-up, each with its own sound;
  - **a loop that lands exactly on the first frame** (seam 0.11).
- **`v10/`, *LET IT HAPPEN*** (The Flash × Tame Impala "Let It Happen", rev 5): this is the Flash edit approved in chat 1, recorded earlier without its number. It stays Studio 1's standard for **motion and finish**:
  - speed ramps on every hook shot, with optical-flow slow motion on restored source;
  - the beat camera;
  - light rays;
  - multi-stage set pieces;
  - the AROUND ring loop.
  Two rounds of "lacklustre" were fixed by **the motion pass, not by more effects**.

**Rules from Studio 1's standards (every edit, both studios):**
1. **A motion pass on every hook shot** (v10): speed ramps on every hook and montage shot (a burst on each beat, then about 0.3–0.6× flow slow motion between, over the same source range); a camera that moves with the music (about a 5–6% zoom punch and a ±1° rotation kick per beat, with zoom blur and a slight colour split on the hit frames, type kept clean on top); light that reacts to the footage. Plan the speed curve and the camera with the shot list. Flow only where it stays clean (the owner's v104 brief: no visible interpolation artefacts; Dexter edits otherwise hold the source cadence).
2. **Restore the 720p source** (v10): Studio 1's `tools/sr_prep.py` + `tools/srnet.py` (about 3 s per source frame on the CPU, run in the background after prep). They run a Real-ESRGAN compact model through ONNX Runtime on the CPU, 2×, on only the band each frame is cropped from, in the background after prep.
   - **It is also the fix for the owner's v105 clip-quality note.** Studio 2's v105 note said an AI upscaler needed a GPU; that held for the large model tried, not for this compact one.
   - After the merge, run it on every edit as well as checking `tools/sharpness.py`.
3. **Lyrics on their sung onsets** (v10): check every word on the isolated vocal (pitch and onsets), not just Whisper, which was up to 1 s off in v10. Studio 2's `tools/lyrics.py` snaps word starts to the vocal envelope; also check pitch onsets by ear.
4. **Designed set pieces on the drop, the hook and the loop** (v10).
5. **Find the concept in the song or the character** (v11): a hook in the song's own words or the character's history, carried through picture, grade, sound and the loop.
6. **One focal set piece** the owner can point to (v11): multi-stage, with its own layered sound, on a structural moment such as a bar line after a build.
7. **Hero graphics detailed and lit to the shot** (v11): lit, bevelled procedural assets matched to the shot's light, revealed physically on real objects. Check them at full size.
8. **No "just moving to the beat" shots** (v11): give each its own beat animation, with its own sound.
9. **The loop is a set piece that lands exactly on frame 0** (v10, v11): build the last frames from frame 0's own image, and measure the seam (blurred difference ≤ 1; v10 0.93, v11 0.11). A plain motion-blurred rewind reads as low quality. Studio 2's QC measures the same thing.
   - v104 THE PASSENGER: 0.14.
   - v105 DRACULA: 8.4. The light is still collapsing into frame 0's sun on the last frame.
10. **Flash discipline** (v11): measure every flash in the encode. A flare must keep the picture, with a **peak mean luma of about 110 or less** (v11's rim flash went from 178 to 104). Studio 2's QC section 7b lists every flash over 110. v105 has 9 of 14 flashes over it, partly because its day half is bright overall.
    - Studio 2's `qcN.py` now reports it in section 7b: every white-out run (mean luma ≥ 200) and the most flashes in any second, and it fails above 3 flashes a second.
    - v105 measured two white-outs: the torch blind-out (frames 687–692, peak 236) and the loop flare (1360–1372, peak 223). At most 2 flashes a second.
11. **When the lyrics are explicit, use only a couple of designed titles** (v11: LET'S GO, BOP), not captions.
**Next Dexter edit, from the Flash studio's notes for us:**
- Run the motion pass on the montage: speed ramps with flow in-betweens on restored frames, not only the held source cadence.
- Close the loop seam: make the last frame exactly frame 0's image (in the REVERSE loop, the inside of the disc *is* frame 0, scaled to 1.0 on the last frame).
- Try the coin flip on a real prop: a Miami Metro badge flipping to a blood slide.

12. **Nothing on faces** (v10, v11, confirmed): lightning, seams, particles, streaks and wipe edges are routed around a face/head box. Particles in front of faces are masked off.
13. **Packs labelled 4K are usually 720p** (v11, confirmed by Studio 2): check the specs; frame inside insets; keep watermarks out of the crop.
14. **"Lacklustre" means motion and polish are missing,** not that more overlays are needed (v10, confirmed).
15. **Transform the picture itself; don't solve a moment with an overlay sitting on the frame** (v10, changed: it widens 'props must land'). No glass webs or hanging shards over the frame or face: v10 rev 4 replaced its glass shatter with TIME PARTICLES (the picture breaks into its own pixels), as v103 replaced its glass with the eye dive.
16. **Treat any pack's labels as unknown until probed** (v11): check the resolution, cadence and bitrate; frame inside insets; keep watermarks out of the crop.
17. **Flash discipline means both limits** (v11): flare peaks about 110 mean luma or less, **and** no white-out runs.

**Engines after the merge (2026-11-07; since 2026-11-08 Flash edits start from v12 and Dexter edits from v107, see the top):** the two studios' scaffolds start from different engines.
- **Studio 1:** `tools/new_edit.py` copies the v11 engine (v4–v11, 91 transitions plus the audio builder). Its EDL template adds v11's three timing settings: `E_BEAT` (where the beat drops in), `E_DIP` (the dip before the drop) and `E_LOOP` (where the loop set piece starts). Its setup check confirms v11 loads.
- **Studio 2:** starts from v105 (the v4–v9 engine plus the v103, v104 and v105 toolkits).
- **Agreed by both studios (2026-11-07):** Dexter edits start from v105, Flash edits from v11, and shared effects are ported between them through the edit reports. At the merge, `tools/new_edit.py` needs to support both bases. *(Updated 2026-11-08: Flash edits now start from v12, Dexter edits from v107; `tools/new_edit.py` supports `--base v12|v11|v107|v105`.)*

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
  - Every transition gets its own sound. **Updated by v12 and v106:** at most one sound per transition; small transitions may be silent, and the set pieces carry the layered sound (see the v12 and v106 rules below).
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
- **v12 standard (BLOOM rev 3), do this on every edit as well:**
  - **Text is optional.** Start without titles when the lyrics aren't captioned; a title has to earn its place (the owner removed both NIGHT and BLOOM, then approved).
  - **Fewer, bigger sounds:**
    - one sound per transition;
    - layered hits only at the set pieces;
    - about 35–40 effects in a 23 s edit;
    - **no sounds on beat moments**, and **no chimes or bells** on graphics.

    This updates the v11 rule: beat moments keep their animation and lose their sound. Evidence: "get rid of like half the sound effects", "remove the bell sound on the flower and the whoosh on one of the first transitions".
  - **An emblem transition on the real, tracked emblem** in every Flash edit (`emblem_at`: Hough circle on the source frame through the shot's camera; v12 EMBLEM BLOOM). Evidence: "try to do an emblem transition aswell".
  - **At least one transition built on a real physical phenomenon** tied to the concept (v12 FRACTAL BURN: lightning burning a Lichtenberg figure). Evidence: "implement one more really cool transition", then approval.
  - **One hero asset carries the edit** through the drop, the focal piece, the emblem and the loop (v12's lightning jasmine).
  - Keep the guards: `face_guard` on beat moments, the flash governor (flares stay under mean luma 110), `tame` for coloured light that isn't the suit.
- **v106 standard (WONDERWALL rev 3, The Flash × Oasis "Wonderwall"; a one-off Flash edit made in the Dexter chat on the v11 engine, code in `v106/` on `dev/pipeline-v2`).** The owner: *"I like this edit make it a standard."* Handoff: `sync/handoffs/2026-11-08_dexter_v106_WONDERWALL_standard.md`. Do this on every edit as well:
  - **Sound restraint** (rev 2: *"remove like half of the sound effects mostly the tedious annoying ones like the emblem shine and the few near the end"*): sound the set pieces and structural hits only. No sound on every camera punch, letter, small transition or beat animation; no shimmer, chime or "shine" sounds; let the song carry the ending and the loop. A transition may be silent, and mixcheck's "buried" list is a review list, not a target. Rule 7 (+9–10 dB against a loud master, a 3 dB duck) still applies to the sounds you keep. **This changes "every transition gets its own sound".**
  - **Find dead spans by measurement** (rev 2: *"identify one space where these isn't anything happening"*): the mean frame-to-frame difference of the encode per half-beat. Any span of about 1 s or more near the static floor (about 1–1.5 grey levels, against 5–18 when active) gets a new cut and a designed transition.
  - **A pop audit on every encode:** every frame whose difference exceeds 3× the local median plus 2 is a cut, a designed flash or a beat hit; anything else is a defect (rev 1 shipped six that no still showed).
  - **A signature transition needs about 1 s on screen** (rev 3: *"slow down the tear drop transition so it's more visible"*, 0.6 → 1.0 s). Move the cut to the next sung word to make room rather than squeezing it.
  - **Smooth motion** (rev 2: *"one more polish smooth over the animations"*): flow on 24p held shots where it stays clean; procedural motion sub-pixel, never in integer steps; tremble as smooth per-element sines, not per-frame random; no noise texture wraps inside the edit's time range. Cover transitions are exactly 0 at their ends, and plates dissolve under the cover instead of switching.
  - **The loop keeps moving** (rev 2: *"make sure the loop is seemless"*): dissolve into frame 0's picture under the cover, fade frame 0's finish in, render frame 0's background animation at the wrap's virtual negative frames, keep periodic events off frame 0. Seam ≤ 1 (v106: 0.14) and no frame-difference spike across the wrap.
  - **Probe the source range for VFX colour flashes** (the S3 Speed Force shot flashes pink at 134.37–134.47 s); they become pops under flow and transitions.
  - **Sound, v12 and v106 together (both approved after the owner cut half the effects):** about 35–40 placed effects in a 23 s edit; layered hits only at the set pieces; at most one sound per ordinary transition, and a silent one is fine; no sounds on beat moments, camera punches or letters; no chimes, bells or shimmers; the song carries the ending and the loop. Rule 7's +9–10 dB and 3 dB duck still apply to what is kept.
- **v107 standard (ALL CAPS rev 4, Dexter × Madvillain "All Caps", the Dexter studio, code in `v107/` on `dev/pipeline-v2`).** The owner: *"I like this edit make it a standard."* Handoff: `sync/handoffs/2026-11-08_dexter_v107_ALL_CAPS_standard.md`. Do this on every edit as well:
  - **No black occluders as transitions:** letterbox bars, redaction boxes, a screen floating in a dark room all read as "black bars / a black box". A cover must be content (paper, liquid, light, the picture itself). Evidence: *"I don't like the transition at 3 seconds with the black bars"*; *"remove and replace the black box transition"*.
  - **No gimmick on the face, including graphics that point at where a face will appear** (converging strings, crosshairs, target rings). **Read the banned list before designing any graphic.** Evidence: rev 3's POINT OF ORIGIN, *"get rid of the point of origin graphic/transition"*.
  - **A slot that has failed twice gets no new graphic concept:** use a kinetic, physical transition (rip, pour, spin, page, whip) or a clean cut on the downbeat with the beat camera's punch. Evidence: the 3 s slot was rejected as press flash, TV and POINT OF ORIGIN; the clean downbeat cut was approved.
  - **Spell-outs and per-letter titles run on an even rhythm grid** (a 16th at ~90 BPM ≈ 10 frames a letter); each letter lands on its hit (the descent in the frames before it, the sound on the same frame). Uneven word onsets read as slow. Evidence: *"how slow it writes dexters name … not too fast and not too slow"*.
  - **A spin lands on a centred face and decelerates about it** (rotate the incoming half about the incoming face's centre). Evidence: *"the final shot doesn't have a centered shot of Dexter"*.
  - **Never reuse a clip** in one edit (*"you reuse the same clip around the 17-second mark … and the 19-second mark"*). **Smooth endings:** the beat camera rests through the break and the ending; fewer, longer cuts there (*"smooth out the ending part"*). **The loop is a set piece** (*"the loop is pretty low effort"*): v107's crowd confetti spells DEXTER, holds through the drop-out bar and bursts into frame 0 (seam 0.10).
  - **QC:** the beat-hit colour split clamps at the frame edge (`np.roll` wrapped it into a 2–3 px cyan/magenta edge line on every beat hit; v107's `rgb_split`; the v11/v12 engines have the same code). Face-centring flags inside designed transition windows are listed, not counted (`qc107.py`).
- **From the Dexter studio's v106 WONDERWALL handoff (a Flash edit; adopted 2026-11-08; all apply to Flash and Dexter edits):**
  1. **Sound restraint.** Sound the set pieces and structural hits only. No sound on every camera punch, letter, small transition or beat animation; no shimmer, chime or "shine". Let the song carry the ending and the loop. **A transition may be silent**, and the `mixcheck` "buried" list is a review list, not a target. Dexter rule 7 (effects +9–10 dB against a loud master, music ducked 3 dB under the biggest hits) still applies to the sounds you keep. Evidence: *"remove like half of the sound effects mostly the tedious annoying ones like the emblem shine and the few near the end"* (rev 2), then approval.
     - **Conflict, both kept:** v12 says "one sound per transition, ~35–40 effects in 23 s"; v106 shipped 14 sound moments and silent transitions. Read together: **at most** one sound per transition, layered sound only at set pieces, nothing after the last set piece unless it is structural. The owner cut about half the effects in both edits, so start lean.
  2. **Find dead spans by measurement:** the encode's mean frame-to-frame difference per half-beat (135×240 grey). A span of ~1 s or more near the static floor (~1–1.5 grey levels; 5–18 in an active edit) gets a new cut and a designed transition. Evidence: *"identify one space where these isn't anything happening"* (rev 2): the Iris hold measured 1.2–1.4.
  3. **Pop audit on every encode:** frames whose difference is over 3× the local median (±6 frames) + 2. Each one is a cut, a designed flash or a beat hit, or it is a defect. Evidence: rev 1 shipped six, three invisible on stills.
  4. **A signature transition gets time to read:** about 1 s on screen, the graphic at least ~8 % of the frame width while it is read. Move the cut to the next sung word rather than squeezing the transition. Evidence: *"slow down the tear drop transition so it's more visible"* (rev 3, 0.6 → 1.0 s), then approval.
  5. **Smoothness:** 24p/30p hold-cadence shots between 60p flow shots read as judder, so use `interp="flow"` on held shots wherever the frames stay clean. Procedural motion is sub-pixel (no integer-step drift); tremble is smooth per-element sines (9–15 Hz), not a new random offset each frame; no noise texture wraps inside the edit's time range, the loop's virtual frames included. Evidence: *"one more polish smooth over the animations"* (rev 2).
  6. **Cover transitions start and end at exactly zero:** check `cover.max()` at u = 0 and `cover.min()` at u = 1, keep the cover continuous across the cut, and dissolve the two plates under the cover instead of switching. A transition's progress must reach 1 on the frame before the cut (`/pre`, not `/(pre+1)`). Evidence: the rev 1 pops at both mist transitions and the tear's framing jump.
  7. **The loop lands exactly and keeps moving** (extends v10/v11): dissolve into frame 0's picture under the cover (never switch), fade frame 0's own finish in, render frame 0's background animation at the wrap's virtual negative frames so it carries on, keep periodic events (flickers, flashes) off frame 0. Pass: seam ≤ 1 and no frame-difference spike across the wrap. Evidence: *"make sure the loop is seemless"* (rev 2); seam 0.14.
  8. **Probe each chosen source range for VFX flickers and hidden cuts.** Colour flashes in the source become pops under flow and transitions (S3 Speed Force, `flash_s3.mp4` 134.37–134.47 s). Evidence: v106 rev 2.
  9. **Confirmed:** concept from the song's words and the character's history (v11); one focal set piece (v11); nothing on faces (v10/v11; a prop may touch a face only when the face is its subject, as the tear on Iris's jaw); lyric onsets checked on the vocal stem (v10) **with Whisper large-v3, not small** (small put "I said maybe" 3.4 s early); **the beat map checked against the Demucs drum stem** (the automatic map locked to 116 BPM, 4/3 of the real 87.02, on a swung strum).
  - **The audits are now a tool here:** `python3 tools/motionqc.py N` (run by `build.sh N qc`) lists dead spans, pops (labelled cut / flash / beat / cadence / UNEXPLAINED) and hold-cadence judder per shot, and checks the loop's wrap step. Its first run, on v12 (already approved, left unchanged): two still spans (the storm-sky open 0.29–1.75 s after NIGHT was removed, and the eye before the drop 8.17–9.34 s), 2:3 judder on the held `flash_b_hq` strike shot (frames 111–203) and on the crouch (777–834), and **a ghost frame at 736**, where the street shot crosses a jump cut in `flash_s5.mp4` at 73.50 s that the shot detector missed.
- **v13 EVENT HORIZON (Flash × Brent Faiyaz "Wish You Well", rev 2): approved, NOT a standard.** The owner: *"I like this edit but I do not want you to make it a standard. It does somethings good and somethings bad."* Handoff: `sync/handoffs/2026-11-08_flash_v13_EVENT_HORIZON_approved.md`. Rules from it:
  1. **The hero asset is a motif, not the transition kit.** Give it its set piece(s), and at most the focal piece and the loop: about 2–4 appearances. Every other transition is a different idea. This refines the v12 rule "one hero asset carries the edit". Evidence: *"I don't like that the singularity is the primary object in every transition and animation"* (rev 1).
  2. **An emblem transition is about the emblem itself** (its bolt or its shape, on the real tracked emblem): v13 EMBLEM SPLIT (the bolt ignites, leaps off and splits the frame along its zigzag), v12 EMBLEM BLOOM. Another effect that merely starts at the emblem doesn't count. Evidence: rev 1's black hole in the emblem, then *"make a emblem transition"*.
  3. **A hero graphic earns its transition:** about a second on screen as a graphic (its own motion, in depth behind and in front of him), then it becomes the transition, and it stays off faces. Evidence: *"create a really cool graphic that you use to turn into a transition"* → the LIGHT RIBBON, approved.
  4. **Start sound lean:** the third edit in a row where the owner cut effects (v12, v106, v13). Aim for about 10–12 sound events in 20–23 s; small transitions silent; never drones, swirls, whines or a swell on every move. Evidence: *"remove some of the tedious sound effects"* (rev 1 already had about 16).
  5. **Pull frames of any library transition before using it:** v11 `bolt_trace` samples past its shot and showed the next pack shot.
  6. **Technical:**
     - fast 30p shots: `flowmax` per shot, and `flowfall="blend"` where lightning jumps would warp;
     - warp a clean plate (him inpainted out) when lensing a background behind his matte;
     - QC length and the audio seam are measured on the container duration (now in `qc12.py`, the scaffold).
  - **Dexter studio adoption (2026-11-08):** rules 1, 3, 4, 5 and 6 apply to Dexter edits as they are. Rule 2's Dexter form: when a symbol carries a transition (the slide, the knife, the Code, the badge), the transition comes from the symbol itself. Sound: v107 ALL CAPS shipped 28 placed effects without a sound note, after v12 and v106 had settled on ~35–40; with v13 the owner cut effects a third time, so **start lean (about 10–12 events) and treat v107's 28 as the ceiling**. AAC padding: the container-duration QC fix (now in `qc12.py`) and v107's 96-sample sin² fade at both ends of the mix (it removed a seam click on a loud frame-0 kick) work together.
- **From the Dexter studio's v107 ALL CAPS handoff (adopted 2026-11-08; rules 1–8, 10 and 11 apply to Flash edits; 9 is Dexter's engine base):**
  1. **No black occluders as transitions.** Letterbox bars, redaction boxes, or a screen floating in a dark room read as "black bars" or a "black box". A cover must be content: paper, liquid, light, the picture itself. Evidence: *"the transition at 3 seconds with the black bars"*, *"the black box transition"*.
  2. **No gimmick on the face, including graphics that point at where a face will appear** (converging lines, crosshairs, target rings), even when the face arrives a beat later. Read the banned list (`studio/preferences.json` "rejected") before designing any graphic. Evidence: *"get rid of the point of origin graphic/transition"*.
  3. **When a slot has failed twice, stop adding graphic concepts:** use a kinetic, physical transition (rip, pour, spin, page, whip) or a clean cut on the downbeat with the beat camera's punch.
     - **Conflict, both kept:** our rule is "no plain hard cuts" (v6; *avoid plain hard cuts in quiet or dialogue sections*). Read together: designed transitions remain the default. A clean *downbeat* cut with the camera punch is the approved fallback for a slot the owner has rejected twice, never in a quiet or dialogue section.
  4. **Spell-outs and letter-by-letter titles run on an even rhythm grid**, about a 16th note (≈ 10 frames a letter at 90 BPM). Each letter comes down in the frames before its hit and lands on it, with its sound on the same frame. Uneven sung-word onsets read as slow. Evidence: *"not too fast and not too slow"*, then approval.
  5. **A spin transition lands on a centred face** and decelerates about the incoming face's centre (`face_scr`). Evidence: *"the final shot doesn't have a centered shot"*.
  6. **Never reuse a clip in one edit** (confirmed). Evidence: *"you reuse the same clip around the 17-second mark … and the 19-second mark"*. Note: v13's first and last shots came from the same continuous S1 shot (a bookend). Treat that as a reuse from now on.
  7. **Smooth endings:** through a beat break and the ending, the beat camera rests and the cuts get fewer and longer (a dolly, a soft smear). Evidence: *"smooth out the ending part"*.
  8. **The loop is a creative set piece** (confirmed, v105 rule 3), ideally built from the edit's own material (v107: the parade's confetti spells his name and bursts into frame 0, seam 0.10).
  9. **Dexter edits scaffold from v107** (the v12 engine plus the v107 toolkit; `--base v107`). Flash edits still scaffold from v12.
  10. **The beat camera's colour split clamps at the frame edge.** `np.roll` wrapped it into a 2–3 px cyan/magenta line on every beat hit. This is fixed in `v12/work/render12.py` (`_shift_edge`), the Flash scaffold: only beat-hit frames change, in the edge columns, so the v12 golden references were re-saved. v10, v11 and v13 keep their shipped renderers.
  11. **QC:** face-centring flags inside designed transition windows are listed, not counted (now in `v12/work/qc12.py`).
  - **Sound, a conflict noted:** v107 was approved with about 28 placed effects in 21.9 s (layered only at set pieces, none on beat moments, almost nothing in the loop bar). Our v13 rule says to start at about 10–12 events. Read together: the number follows the set pieces, and the placement rules (no beat-moment sounds, one per transition at most, quiet loop) are shared. Start lean in Flash edits, where the owner cut effects three times.
  - **Text:** v107 captions every clearly sung line in the v9 style, plus one designed title. That is compatible with the v12 rule "text is optional": caption when the lyrics are clean and carry the concept.
  - **Audio tail:** v107 fades the mix 96 samples (sin²) at both ends against the AAC tail padding. Ours crossfades the pre-roll into the end (seam step 0.019 on v13), so it isn't needed here; adopt it if a loop starts on a loud transient.
- **The efficiency update, one toolchain for both studios (2026-11-08):** both studios answered the owner's same request; the Dexter studio merged the two halves on `dev/pipeline-v2` (`34a20d1`, `a32ffce`, handoff `2026-11-08_dexter_DEV_efficiency-merge.md`), and this branch merged that back in. **Pull `dev/pipeline-v2` before each edit; don't keep a separate copy of the tools.**
  1. **`studio/OWNER_RULES.md`** (every rule in force, on one page) and **`studio/WORKFLOW.md`** (the loop, targets: at most 2 owner rounds, at most 2 full renders before a first delivery). Read both before designing and before delivering.
  2. **One plan check:** `tools/plan_check.py N` (= `build.sh N plan`; `preflight.py N` prints the same report, `--own` only the Flash checks). It runs the Dexter checks and ours in one process, one check per rule, and **`video` stops on a FAIL** (`PLAN_FORCE=1`; `PLAN_ACCEPT` in the EDL accepts an item on purpose). EDL fields: `HERO` (drawing functions), `HERO_TINS`, `SIGNATURE`, `SET_PIECES`. Calibrated on the approved v107, v12, v13 and v106 (0 FAIL); v13 rev 1 FAILs (the singularity in 11 transitions, the rejected `emblem_horizon`).
  3. **One registry, `studio/transitions.json`:** generated fields (pre/post, engines, used in) plus the owner's curated verdicts (verdict, tags, evidence, fix, family, studio), which survive `preflight.py registry` rebuilds. **Add a verdict there the turn the owner gives it.** The Flash verdicts are in (v10–v12 standards' transitions `liked`, v13 rev 2 `ok`, `emblem_horizon` `rejected`, `bolt_trace` tagged `leaks`).
  4. **`build.sh`:** `song:`, `plan`, `prep` (plan check as a report, `sr_prep` in the background), `qc` (four passes in parallel, then the sign-off pages), `signoff`, `report`, `splice` (an edited `fxN.py` is re-spliced before anything renders), `rev` = audio → plan → video → qc → signoff → report, `ship` = `rev` + deliver.
  5. **The fresh-eyes critique before every delivery** (`studio/CRITIQUE_PROMPT.md`, one fresh agent; on v107 rev 3 it predicted the owner's next note as its top HIGH item).
  6. **motionqc** labels an impact's designed negative frame as a flash (the Dexter studio's request; v12 and v13 labels unchanged).
  - **Calibrations the merge made, kept:**
    - a clean cut on a beat hit with the camera punch passes "no plain cuts" (v107's approved fallback); a cut off the beat WARNs;
    - **banned sound kinds are a WARN in the tool** (the approved v107 has a swirl, v106 three). **In a Flash edit, treat each one as a fix** (v13 rule 4: the owner cut effects in three Flash edits running).
  - **Still two review tools** (`signoff` pages and our `review` pack). Both run; folding them into one is proposed.
- **Source sharpness (Studio 2, after DRACULA):** some clips look soft because every pack in the library is 720p, including the ones labelled "4K". A 9:16 frame uses about 405×720 source pixels, so every shot is enlarged about 2.7× before any zoom, and several packs are heavily compressed (worst: the S1 pack `pack8_s1.mp4` at 0.43 Mb/s). Restoration can't recover detail that isn't in the file. Studio 2's softest DRACULA shots, measured on the final video: the final walk into the sunrise (also zoomed in, enlarged about 3.5×), the palms shot, the lollipop shot, then the ice cream, hood and pink-wall shots. Rules for every edit:
  - check every shot with `tools/sharpness.py` while picking clips and again on the finished video (`python3 tools/sharpness.py packs`, `python3 tools/sharpness.py N`), and swap any shot it flags as soft;
  - don't zoom in more than about 10 % on 720p clips (z ≤ 1.10; the tool flags more);
  - use the less-compressed packs for close-ups and big moments (the pack table in `studio/SCENE_PACKS.md`);
  - **better copies arrived 2026-11-08** (same frames and timing, so source times carry over): `pack8_s1_hq.mp4` (S1, 0.43 → 2.00 Mb/s), `pack9_s4_best_hq.mp4` (S4, 0.69 → 1.80 Mb/s), `flash_b_hq.mp4` (1.18 → 2.20 Mb/s). New edits use the `_hq` files. The same batch added Flash S1, S2, S3, S5 and Blitzkrieg packs and Dexter S2 and S1–S3 packs; every one is 720p despite its 4K/1440p label;
  - **packs over the upload limit come as Google Drive links in a txt:** `python3 tools/fetch_packs.py LINKS.txt` downloads them, identifies known files by checksum and leaves new ones in `src_incoming/` to catalogue. **Never commit the links: the repo is public.** Keep the list in `src/` (git-ignored) and ask the owner to re-send it to a new session;
  - Studio 1 note: `tools/sr_prep.py` runs a CPU AI upscaler (Real-ESRGAN compact via ONNX) on only the band each frame uses, at about 3 s per source frame, in the background. It helps edges and blocking but also smooths skin texture, and it doesn't replace picking sharp sources.
- **From the Dexter studio's v105 DRACULA handoff (adopted 2026-11-07; all apply to Flash edits):**
  1. **Light sources go behind the subject, not over him.** Give sun, glow, lightning-glow and ray shots the person matte, draw the light only from the background, and add a light wrap on his near edge. Evidence: *"what happened with the sun and the top right part of dexters head?"* (v105 rev 1). For Flash: light rays and Speed Force glows get the matte (v10/v11 drew rays over him).
  2. **Clip quality:** restore 720p sources (`tools/sr_prep.py`); rank shots by sharpness before choosing them (`tools/sharpness.py N --src`) and on the render (`tools/sharpness.py N`), and swap SOFT ones; zoom ≤ ~1.1 on 720p; hero shots and close-ups on the high-bitrate packs; ask the owner for 1080p/4K packs when a hero moment needs one. Evidence: *"The only gripe I have is the quality of some of the clips"* (v105 verdict).
  3. **The loop should be the most creative transition in the edit:** a set piece that pays off the concept and lands in frame 0's own image, not a fade or white-out. Evidence: *"make it a more creative and unique transition"* (v105 rev 2→3), then approval.
  4. **Restyle library transitions before reusing them;** they carry their original edit's look (v6's cube brings a synthwave grid, v9's foliage brings jasmine). Evidence: v105 rev 3 review.
  5. **When a burn, dissolve or disintegration removes the subject, remove him before drawing scene light** (no rays, shadows or wraps reacting to him), and fill the hole with a plausible background, not a flat colour. Evidence: v105 rev 3 review.
  6. **"Add transitions, graphics and animations wherever possible" means replace generic connectors with themed ones and add new cuts with new transitions,** not stack effects on existing shots. Evidence: v105 rev 2 and 3, then approval.
  7. **Mix effects against how loudly the song is mastered.** Measure them against the music at every set piece; on a loud master (−9 to −11 dBFS RMS), push the effects about +9 dB and duck the music about 3 dB under the biggest hits. Evidence: v105's effects first sat 20–25 dB under the song (rev 1 review).
  - **Flash check is now in QC** (`qc11.py` §7b, from the Dexter studio's `qc105`): white-out runs (mean luma ≥ 200 for 2+ frames) and more than 3 flashes a second fail; every flash peaking over mean luma 110 is listed for a visual check. The loop-seam gate is now ≤ 1.
- **No "gimmick on the face" effects** (e.g. lines converging on his face with a target ring). Transitions should be physical and themed (slide box, plastic burst, zipper, blood on the lens), not overlays on his face.
- **Props and effects (Studio 2, after FOREVER):** blood slides and the knife across the screen are **no longer banned**. In FOREVER they failed because they lingered (slides drifting round the opening as a constant overlay), were random (drips, spatter and the knife pass on beats with no reason in the shot), looked drawn (flat red circles on grey glass), and didn't land (a glass-shatter web over his face, duct-tape strips that fell flat). Use blood, slides, knives, glass or tape only when they are motivated by the shot, lyric or story; brief; lit like real objects or taken from real footage (the S1 shot of him holding up a slide); in the edit's own look; and off his face. Check each on stills next to the footage and rebuild or cut anything that looks drawn. The v7 blood-slide box and blood on the lens worked. (v10 rev 4 applied this: the frozen-scene glass shatter was replaced.)
- **Efficiency:** the user asks for quality *and* efficiency (*"this process takes too long whether that be the revisions or the initial creation process"*, 2026-11-08). Most of the time goes into owner rounds spent on rules we already had, so **check the plan before rendering**. Use the fast loop in `docs/TOOLKIT.md` (§1, §1b, **§1c**):
  0. **Read `studio/OWNER_RULES.md`** (every rule in force, on one page, from the Dexter studio) before designing and before delivering, and pick transitions from `studio/transitions.json` (the owner's verdict on each, shared by both studios).
  1. `build.sh N song:src/SONG.mp3[:H0:H1]`: map, Demucs stems, the grid fitted on the drum stem (with the 2/3–3/2 tempo relatives), Whisper large-v3 words on the vocal stem, loop-wrap scores, and the EDL lines to paste (`tools/song_prep.py`);
  2. the EDL, with `HERO = [...]` (the hero asset's drawing functions) and `SET_PIECES`;
  3. `build.sh N audio plan`: **the plan check**, one report in seconds from `tools/plan_check.py`, which runs its own checks and `tools/preflight.py`'s (merged 2026-11-08: one check per rule, calibrated so the approved v107, v12, v13 and v106 pass). **A FAIL stops every `video` step** (`PLAN_FORCE=1` overrides; `PLAN_ACCEPT = {"check": "why"}` in the EDL accepts an item on purpose). It reads `studio/OWNER_RULES.md`'s rules, the owner's verdicts in `studio/transitions.json`, the renderer (TR2, the call graph, the beat camera) and the audio builder's `fx_events.json`. It FAILs, among others:
     - a hero asset in more than 4 transitions;
     - no emblem transition in a Flash edit;
     - a plain cut off the beat (a clean downbeat cut with the camera punch passes: v107's approved fallback);
     - a rejected or banned transition, a look-alike or overlapping clip, a spin landing without a tracked face, no loop set piece;
     - an overlapping clip reuse;
     - a sound on a beat moment;
     - a transition the registry marks rejected.

     It WARNs about banned sound kinds (drone, swirl, whine, chime, bell, shine: a WARN because the approved v107 has a swirl), the same source shot used twice, more than 12 placed sound effects, a swell on every move, zoom over 1.10, held 24p/30p frames, a repeated transition, fewer than 3 set pieces, order-dependent caches, a hero family over 4, holds with no beat, and the registry's `caution` notes.

     **Fix every FAIL before the first render;** decide each WARN. `studio/transitions_usage.json` (`preflight.py registry`) lists where each transition is defined and used. On v13 rev 1 the check FAILs the singularity in 11 transitions; on v107 rev 1 it FAILs the two transitions the owner later rejected, the look-alike clip and the spin landing with no tracked face;
  4. `build.sh N prep auto` (tracks, mattes, preflight again, **the source restoration started in the background**, sheets of every cut);
  5. `sheet:` / `strip:` / `clip:A:B` for stills and motion (warm server: a 24-frame sheet in ~8 s);
  6. `audio` also prints the effects-vs-music table: no transition or set piece more than 12 dB under the music (the shipped v11 had 12 of 17 there, so the Dexter studio's rule 7 applies to Flash edits too). The list is for the sounds you keep: a silent transition is fine (v106 rule 1). The scaffold's audio builder writes `vN/audio/fx_events.json` (every placed effect) for preflight;
  7. **one** `video qc` per revision:
     - `video` **tracks which renderer functions drew each frame**. After a code or EDL change it re-renders only the frames that ran edited code (or read a changed value), verified bit-exact outside them. A global no renderer code reads, such as `SET_PIECES` or audio knobs, renders nothing.
     - `qc` runs `qcN`, `faceqc` and `motionqc` side by side, then writes **the sign-off pages** (`vN/frames/signoff_*.jpg`: a row per transition and cut, per set piece, the loop wrap, the titles and every unexplained pop, from the encode, flagged frames boxed red; `tools/signoff.py`, which absorbed the Flash studio's `review.py` on 2026-11-08). Look at every sheet; you don't need to hand-pick `sheet:` lists any more.
  8. **`build.sh N ship`** (or `rev`, the same without deliver) = audio, plan gate, video, QC with the sign-off pages, `report` (the Measured block → `vN/work/measured.md`), deliver. It is one command per revision. Before delivering, run **the fresh-eyes critique**: one fresh `general-purpose` agent with `studio/CRITIQUE_PROMPT.md` predicts the owner's next notes from the pages; fix every HIGH item. In a revision, apply every note in one pass, then `ship`. Targets (`studio/WORKFLOW.md`): at most 2 owner rounds, at most 2 full renders before a first delivery;
  9. review every run in the faces-vs-effects list (`vN/frames/faceqc.jpg`) and every dead span, UNEXPLAINED pop and judder flag in the motion audit (`vN/work/motionqc.json`, printed by `qc`), then `deliver` (waits for the background master);
  10. at the verdict, `python3 tools/vrender.py N clean` (the frame cache is ~2.2 GB).
  - **Keep `render(f)` a pure function of `f`.** A cache keyed on rounded values but filled from exact ones (v13 `doppler_row`) makes pixels depend on render order. Partial renders then can't verify and fall back to full renders. Compute cached values from the rounded key; preflight warns about the pattern.
  - Check the pitfalls list there before building transitions.
  - **Engine changes:** run `bash tools/build.sh 12 golden`, `bash tools/build.sh 11 golden` and `bash tools/build.sh 10 golden` before and after. A change that moves any reference frame by more than 2/255 (or the mean by 0.2/255) is a look change, not a speed-up. The upgrade plan and its status: `sync/PIPELINE_V2_PLAN.md`. The shared development branch is `dev/pipeline-v2` (the Dexter studio leads). The Dexter studio adopted this studio's Phase 1 tools as the shared ones; since 2026-11-08 (owner's decision) everything, with WP2 items 4–5 (flow cache, cropped sprite blur), is merged into `dev/pipeline-v2`, and **both studios edit from `dev/pipeline-v2`**. Phase 2 is paused: v12 and v106 are the pilots. In `render11.py` and its copies, **add an edit's own sections above `# >>> pipeline v2: speed`** with `python3 tools/splice_section.py N SECTION.py` (a `grade` or `render_shot` defined below the section bypasses the fast grade and the caches: still correct, only slower; `build.sh N prep` and every tool that loads the edit warn about it).
- **Honesty:** you cannot watch or listen. Report what was verified by frames and measurement, and ask the user to watch once with sound.
- **Communication:** short progress updates; no long code in chat.

## Project conventions

- Sources go in `src/` (read-only copies). Each edit gets its own folder (`vN/work`, `vN/out`, ...).
- One EDL file per edit holds every decision, and the renderer reads only that file. The EDL also sets `VER`, `SLUG` and `SONG`, plus the engine knobs (`DROP_TITLE`, `MONTAGE`, `VANISH_T0`, `VO_STEM`, `CAPS`, `END_CAP`); the template is `tools/edl_template.py`.
- Tools: `tools/new_edit.py` (scaffold; `--base v12` for Flash (the default; `--base v11` still works), `--base v107` for Dexter (the default for Dexter titles; `--base v105` still works)), `tools/song_prep.py` (song prep in one command: map, stems, drum-stem grid, vocal-stem words, loop wrap; `build.sh N song:FILE`), `tools/song_map.py` (beat grid, drops, candidate windows), `tools/transcribe.py` (word times), `tools/plan_check.py` (the plan against the owner's rules before rendering, one report: its own checks plus `tools/preflight.py`'s; `preflight.py registry` rebuilds the generated `studio/transitions_usage.json`; the owner's verdicts are curated in `studio/transitions.json`), `tools/signoff.py` (the one review tool: the sign-off pages from the encode, run by `qc`; `tools/review.py` is an alias), `tools/report.py` (the Measured block), `tools/codetrack.py` (which renderer code drew each frame, for partial renders), `tools/check_sources.py` (source-range audit), `tools/build.sh` (song / plan / prep / auto / sheet / strip / clip / audio / video / video:A:B / qc / review / signoff / report / splice / deliver / golden / rev / ship; logs every step to `vN/work/metrics.json`), `tools/vrender.py` (final renders, frame cache, background master, verified partial re-renders), `tools/rsrv.py` (render server), `tools/golden.py` (engine regression frames), `tools/faceqc.py` (effects over faces), `tools/mixcheck.py` (effects vs music), `tools/motionqc.py` (dead spans, pops, hold-cadence judder and the loop's wrap step, on the encode), `tools/metrics.py` (owner rounds, notes, catches), `tools/splice_section.py` (puts an edit's section above the speed section; `--check` warns about overrides below it; `--replace` re-splices an edited section in place), `tools/sr_prep.py` (restores and 2× upscales the 720p source bands an edit uses; run in the background after prep), `tools/sharpness.py` (pack quality table; `N --src` ranks each shot's source before rendering; `N` measures the finished edit; flags soft shots), `tools/fetch_packs.py` (downloads scene packs from a list of share links; links stay out of git), `tools/setup_studio.sh` (deps, models, source-library check).
- Two studios: each works on its own branch with its own version range (Studio 1 `v8+`, Studio 2 `v101+`); see `studio/NEW_STUDIO_SETUP.md`.
- **The Flash studio (Studio 1; the chat on `claude/gallant-planck-pqpczp`)** makes The Flash edits (next: `v14`; the Dexter studio uses `v108+`, its v106 WONDERWALL being a one-off Flash edit). **Engine bases (agreed with the Dexter studio):** Flash edits scaffold from v12 (since 2026-11-08; was v11), Dexter edits from v107 (since its standard, 2026-11-08; was v105); shared effects are ported through handoffs. The v106 report, written before our v12 handoff reached the Dexter studio, still names v11 as the Flash base. Whether the Flash scaffold should move to v106's engine is the owner's call; until then, new Flash edits scaffold from v12 and port v106's pieces from `v106/work/fx106.py` on `dev/pipeline-v2` (`docs/TOOLKIT.md` §5e). On every verdict ("good / make it a standard" or "bad, because…"), in the same turn: write `sync/handoffs/YYYY-MM-DD_flash_vNN_TITLE_<standard|rejected>.md` from the shared `sync/HANDOFF_TEMPLATE.md`, adopt its rules here, add a `sync/LEDGER.md` line, commit, push, and send the owner the file. When the owner attaches a handoff from the Dexter studio, adopt it per `sync/README.md` step 7 and reply in a few lines (adopted, conflicts, what the next Flash edit will try).
- Media (`src/`, audio, frames, outputs, models) stays out of git. Commit the code, EDL, transcripts, tracks and README, then push to the session's branch.
- Models are downloaded at runtime: YuNet (`v3/models/face_detection_yunet_2023mar.onnx`), MODNet (`Xenova/modnet`), faster-whisper large-v3 for dialogue and lyric timing, and the Real-ESRGAN compact weights (`v3/models/realesr-general-x4v3.pth` and `realesr-general-wdn-x4v3.pth` from the xinntao/Real-ESRGAN v0.2.5.0 release; loaded tensors-only and exported to ONNX by `tools/srnet.py`).
- The older guide `7b769aa4-TIKTOK_EDITING_GUIDE.md` (the beat-grid, colour and QC methods) still applies where it doesn't conflict with this file.
