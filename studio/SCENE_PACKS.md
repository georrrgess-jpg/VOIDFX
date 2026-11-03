# voidfx source library: scene packs, songs, proven shots

Every file lives in `src/` under the name in the first column. That folder is not in git: upload the files and rename them exactly, then run `bash tools/setup_studio.sh` to verify them against `studio/src_manifest.json`.

All times are **seconds in that file**. "w" is the YuNet face width in source pixels on a 1280×720 frame. Above roughly 400 the face is too wide for a 9:16 crop, and text has nowhere to go.

**Cached analysis** (copy it into a new edit instead of re-running):
- shot lists: `v2/work/shots_p2.json`, `shots_p3.json`; `v3/work/shots_p4.json`, `shots_p5.json`, `shots_dk.json`; `v6/work/shots_p6.json`; `v7/work/shots_p7.json`, `shots_p8.json`; `v5/work/shots_fa.json`, `shots_fb.json`;
- transcripts: `v3/work/doakes_transcript.json`, `v6/work/tr_pack6.json`, `v7/work/tr_p8.json`, `v5/work/tr_pack_*.json`.

---

## Dexter scene packs

### `pack8_s1.mp4` (key `p8`): S1 "best and most popular scenes", 1280×720, 60 fps, 6:47, 120 shots

Uploaded as `Dexter_4k_60fps_All_Scenes_Dexter_Morgan_S1_Best__Most_Popular_Scenes_for_Edit_-_Scenepack_1.mp4`. This is the richest pack: clean S1 footage with lots of close-ups and kill room.

| Time | Shot | Notes |
|---|---|---|
| 2.02–5.02 | South Beach street at night, neon hotels, no person | Use `face=None`; good logo backdrop (v7) |
| 28.9–31.6 | Victim on the table, neck cut, lamp | Gore |
| 31.65–33.43 | Overhead of the kill table: Dexter with headlamp over a wrapped victim | Use `face=None` (v7) |
| 44.53–50.6 | Studies a blood slide, big close-up | w311. **Too tight for text** |
| 77.65–83.78 | At the desk lit red (laptop) | v7 "red desk" |
| 110.82–117.4 | Kitchen: intense stare (111.2–113.05), smile (114), rubs eye (115) | v7 ending |
| 117.42–119.6 | Lollipop in the kitchen | Playful |
| **119.78–123.28** | **His eye through a magnifying glass** (eye centred from 121.2) | Soft source. Frame it with `lensframe=True`. v7 opening |
| 142.15–147.6 | Sweaty profile, syringe (M99) | v7 |
| 152.12–153.68 | Green-lit stare | v7 |
| 160.2–166.9 | Lab, Miller Lite sign | |
| 173.5–178.1 | Mangroves / jungle walk | |
| 256.18–258.5 | Plastic-wrapped kill room, apron | v7 |
| 262.13–267.95 | Holds a blood slide up to the light | w318, large face. v7 |
| **283.3–284.48** | **Lab: turns and smirks straight at camera** | Great ending beat (v7 CASE CLOSED) |
| 315.48–321.17 | Night drive lit red | v7 |
| 321.18–327.15 | Confession scene. **Hidden jump cut at 325.217** | User disliked "I'm a serial killer" as an ending |
| 331.88–338.1 | Jar-of-blood monologue | **User disliked this shot.** Next shot starts at 331.883 (watch the boundary) |
| 344.32–349.3 | Red-lit smirk (warm, menacing) | v7 HIM ALL ALONG plate |
| 355.33–357.0 | Looks up, lit red | v7 |
| 388.92–390.37 | Stands over the kill table | v7 |
| 392.15–396.48 | **Sits on the kill-room floor, gloved** | v7 "Could it be him?" |
| 405.9–407.4 | Sunset smile, crowd | |

**Dialogue lines** (Whisper, from the pack audio):

| Time | Line |
|---|---|
| 0.0–4.3 | "Tonight's the night, and it's going to happen again, and again." |
| 33.5–36.2 | "My name is Dexter. Dexter Morgan." |
| 52.2–56.2 | "I don't have feelings about anything, but if I could have feelings at all, I'd have them for Deb." |
| 202.7–207.6 | "I love Halloween, the one time of year when everyone wears a mask, not just me." |
| 225.8–229.9 | "I like to pretend I'm alone, completely alone." |
| 239.3–243.1 | "Somehow it's reassuring to know I'm not the only one pretending to be normal." |
| 296.4–299.6 | "I have a dark side, too." |
| 319.0–326.2 | "I'm gonna tell you something that I've never told anyone before. I'm a serial killer." |
| 336.9–337.8 | **"Could it be him?"** (used in v7) |
| 344.3–348.6 | "Harry's first rule was don't get emotionally involved. I think this is why." |
| 369.6 | "Surprise, motherfucker!" (Doakes) |

### `pack7_4k.mp4` (key `p7`): "4K 60 fps scene pack for edit", 1280×720, 60 fps, 35 s, 14 shots

Uploaded as `DEXTER_MORGAN_SCENE_PACK_4K_60_FPS_4k_scenepackforedit.mp4`.

| Time | Shot |
|---|---|
| 0.0–1.18 | **Red kill room, Dexter seated**: the v7 drop shot |
| 3.5–5.0 / 5.0–10.1 | Wrapped in plastic sheeting, tools |
| 10.1–14.4 | Lab chair, hand to head |
| 14.4–17.6 | Office: walks toward camera with badge |
| 19.2–22.5 | Boat dock |
| **22.52–23.72** | **Crime-scene tape crossing the frame as he walks**: v7 evidence-marker shot |
| 26.0–28.2 | Palms, looks up startled |
| 28.2–32.2 | Night crime scene, badge |
| 32.2–35.3 | Kneeling with gloves |

### `pack6_s5.mp4` (key `p6`): S5 episodes 1–2, 1280×720, 30 fps, 99 s, 24 shots

Uploaded as `Dexter_morgan_scenepack_S5E1_2_1080p…mp4`. The 30p footage is flow-interpolated to 60.

| Time | Shot | Notes |
|---|---|---|
| 0–5.13 | **Red shirt close-up: "It… was me."** ("It" 1.13, "was" 2.70–2.92, "me" 3.06–3.38) | v6 ending |
| 5.17–8.47 | Red shirt at the crime scene | |
| 10.2–13.2 | Police tape, but mostly the back of a cop's head | **Weak** |
| 13.23–15.67 | Walks out of the dark | |
| **15.7–24.73** | **Boat, pastel Miami skyline.** VO: *"I've disappeared so many people. My turn now to disappear myself."* (17.39–23.51) | v6 cold open |
| 24.77–34.9 | Blood-speckled face (30.2–30.86) | v6 |
| 68.13–73.93 | Blue night profile | Showtime bug at bottom right |
| 80.97–86.73 | Interrogation | |
| 89.0–99.2 | Lit interrogation profile | **Face too wide** |

### `pack5_mixtape120.mp4` (key `p5`): "Mixtape scene pack 4K 120 fps", 1280×720, 60 fps, 61 s

Uploaded as `Mixtape_Scenepack_4K_120FPS.mp4`.

| Time | Shot |
|---|---|
| 6.3–7.62 | Grin by a pink wall |
| 16.3–17.1 | Turn |
| 24.95–25.35 | Insert (flash cut) |
| 31.4–33.1 | Night walk / night garden |
| 36.2–37.1 | Photos |
| 39.85–40.5 | Cap and sunglasses at night (thin wraparound shades, so `lens=(0.06, 0.19, 0.075)`) |
| 41.3–42.2 | Lamp |
| **51.65–53.75** | **Boat with trash bags, sunlit**: the v6 drop shot |
| 59.2–59.6 | Insert |

### `pack4_aesthetic.mp4` (key `p4`): "Aesthetic Dexter scene pack", 1280×720, 29.97 fps, 79 s

Uploaded as `Aesthetic_Dexter_Scenepack.mp4`. **Four extreme close-ups are too wide for 9:16.** Check w before using.

| Time | Shot |
|---|---|
| 16.55–17.05 | Attack |
| 23.05 | "Shades": opens on hair. **Weak** |
| 30.7–32.0 | Unreadable macro of lips. **Weak** |
| 33.3–34.6 | Crime-scene crowd |
| 56.6–57.55 | Tackle / run through grass (56.8–57.45 sunlit run) |
| 65.85–67.15 | **Grinning mid-kill (container)** |
| 70.7–71.8 | Club, ice cream (ends on a blurred pan after 71.8) |
| 72.86–73.46 | Ice cream |
| 74.95–75.95 | Massacre |

### `scenepack.mp4` (key `p1`): "135 Scenes Dexter Morgan Scenepack 1", 1200×720, 60 fps, 3:12

Uploaded as `135_Scenes_Dexter_Morgan_Scenepack_1.mp4`. The shot numbers come from the v1 shot list.

| Time | Shot (#) |
|---|---|
| 23.70–24.37 | Container walk (#10) |
| 43.65–45.58 | Alibi walk (#21) |
| 45.65–47.58 | Black gloves on in daylight, eyes up to the lens (#22) |
| 58.57–59.15 | Face shield lowered over blood spatter, "unmask" (#32) |
| **63.77–65.68** | **Finger-gun at the lens** (#36), the classic opener; used in v1, v3, v4 and v6 |
| 69.0–70.33 | Ice cream, eyes go cold (#39) |
| 70.55–71.88 | Boat grin / laugh (#40) |
| 76.3–79.0 | Hand on face (#46), gloved hands (#47) |
| 92.7–93.7 | Photo wall (#59) |
| 95.0–97.1 | Masked (#60), "shh" finger to lips (#62) |
| 102.15–102.82 | Gloving at night (#67) |
| 109.8–110.47 | Blood slide raised to his eye (#75) |
| 128.3–128.95 | Victim POV through a slide (#88) |
| 134.0–139.1 | Rapture (#93), smile reveal (#96) |
| 158.3–158.63 | Knife (#110) |
| 171.1–171.77 | Chain-link stare (#119) |
| 179.98–180.95 | Slide, cold open (#126) |
| 186.35–188.4 | Walks out of darkness (#130) |

### `scenepack2_60fps.mp4` (key `p2`, 66 s, 60 fps) and `scenepack3_24fps.mp4` (key `p3`, 30 s, 23.976 fps)

Uploaded for v2 as `4K_PACK.mp4` and `topaz_Dexter_S1-S8.mp4`. The shot lists are in `v2/work/`.
- **p3:** 24.3–25.1 hooded, in a cap and sunglasses (v3, v4, v6); 12.2–12.6 insert.

### `doakes.mp4` (key `dk`): "Doakes catches Dexter", 1280×720, 60 fps, 100 s

Uploaded as `Doakes_Catches_Dexter…mp4`. This is the v3/v4 dialogue scene.

| Time | Line / shot |
|---|---|
| 16.2–18.5 | Doakes: **"Jesus fucking Christ, you're the Bay Harbor Butcher."** ("BAY" 18.02, "HARBOR" 18.22, "BUTCHER" 18.46) |
| 19.06–20.45 | Dexter: **"I really hate that name."** |
| 23.2–25.12 | Doakes: "I always knew there was something with you." |
| 26.86–28.97 | Dexter: **"What can I say? You were right about me."** |
| 46.05–48.06 | Dexter still (the scope view) |
| 66.72–67.98 | Doakes's gun |
| 95.49–96.30 | The barrel; the fight |

---

## The Flash scene packs (v5)

| File | Specs | Uploaded as |
|---|---|---|
| `flash_b.mp4` (key `fb`) | 1280×720, 60 fps, 151 s | one of `THE_FLASH_SCENE_PACK….mp4` / `The_flash_scenepack_all_seasons….mp4` |
| `flash_a.mp4` (key `fa`) | 1280×720, 25.4 fps, 102 s | the other one |

Proven shots (fb):
- masked close-up 54.45–55.75;
- unmasked in the dark 33.10–34.40;
- cowl 69.00–70.30;
- smile 56.05–57.35;
- emblem bolt 129.25–129.90;
- lightning face 83.85–85.05;
- glowing eyes 116.60–119.20;
- scream 127.70–128.34;
- white suit 89.75–91.05;
- final eye 85.20–86.50.

**Avoid:** the slow-mo run at the camera, and the floating shot.

---

## Songs (`src/`)

| File | Uploaded as | Notes |
|---|---|---|
| `him_all_along.mp3` | `Gunna_-_Him_All_Along_Official_Visualizer.mp3` | 130 BPM, half-beat P=0.23075 s, offset 0.0808. Good part: 2:01.9 breakdown → **2:13.0 return (+17 dB)**. Hook "HIM ALL ALONG" at 131.92–132.30 |
| `warmpop.mp3` | `ESPRIT____George_Clanton_-_Warmpop.mp3` | 90 BPM, P=0.33335, offset 0.1883. Filtered build 117–148.5 s; **full mix returns at 149.54 s** |
| `need_it.mp3` | `Migos_-_Need_It…mp3` | 74 BPM (v3/v4) |
| `duvet.mp3` | `B_a_-_Duvet_Lyrics.mp3` | 93 BPM, P=0.32211, offset 0.2085. Lyric is "you don't even **feel** a thing" |
| `blood_theme.mp3` | `Blood_Theme_Instrumental.mp3` | Dexter theme; hard stop at 113.047 s |
| `matrix_funk_slowed.mp3` | `MATRIX_FUNK_SLOWED.mp3` | Slow again by ×1.12644 (vinyl) → 102.8 BPM |

## Other assets

| File | Uploaded as | Notes |
|---|---|---|
| `voidfx_logo.webp` | the logo image | 2000×541, transparent. **Use as-is, never restyle.** The "o" counter centre is at (645/1982, 327/523) of the cropped logo |
| `reference_tiktok.mp4` | `v12044gd0000d9vh707og65vbajocleg.mp4` | The owner's reference TikTok edit (864×576, 23.5 s), Matrix Funk without vocals; analysed in `v2/README.md` |
| `7b769aa4-TIKTOK_EDITING_GUIDE.md` | the owner's guide | Beat-grid, colour and QC methods; still applies where it doesn't conflict with `CLAUDE.md` |

## Fonts and models (installed or downloaded by `tools/setup_studio.sh`)

**Fonts:**
- Inter / Inter Display (all weights): `/usr/share/fonts/opentype/inter/`
- JetBrains Mono Bold, for the case-note type.

**Models:**
- YuNet `v3/models/face_detection_yunet_2023mar.onnx`
- MODNet `v3/models/modnet/onnx/model.onnx` (`Xenova/modnet`)
- faster-whisper large-v3, which downloads itself on first use
- Demucs `htdemucs`, which downloads itself on first use
