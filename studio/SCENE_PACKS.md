# voidfx source library: scene packs, songs, proven shots

Every file lives in `src/` under the name in the first column. That folder is not in git: upload the files and rename them exactly, then run `bash tools/setup_studio.sh` to verify them against `studio/src_manifest.json`.

All times are **seconds in that file**. "w" is the YuNet face width in source pixels on a 1280×720 frame. Above roughly 400 the face is too wide for a 9:16 crop, and text has nowhere to go.

**Cached analysis** (copy it into a new edit instead of re-running):
- shot lists: `studio/packs/shots_p9.json`, `shots_p10.json`, `v9/work/shots_tg.json`; `v2/work/shots_p2.json`, `shots_p3.json`; `v3/work/shots_p4.json`, `shots_p5.json`, `shots_dk.json`; `v6/work/shots_p6.json`; `v7/work/shots_p7.json`, `shots_p8.json`; `v5/work/shots_fa.json`, `shots_fb.json`;
- transcripts: `studio/packs/tr_p9.json` (p10 has no audio); `v3/work/doakes_transcript.json`, `v6/work/tr_pack6.json`, `v7/work/tr_p8.json`, `v5/work/tr_pack_*.json`.

---

## Dexter scene packs

### `trinity_goodbye.mp4` (key `tg`): "Trinity Finds Out Who Dexter Is (Goodbye Dexter Morgan)", 1280×720, 60 fps, 1:49, 36 shots

Uploaded as `Trinity_Finds_Out_Who_Dexter_Is_Goodbye_Dexter_Morgan_.mp4` (S4E11, Miami Metro). Shot list: `v9/work/shots_tg.json`. Most of the close-ups are too wide for 9:16 (w400–580); the ones that fit:

| Time | Shot | Notes |
|---|---|---|
| **99.75–105.15** | **Arthur Mitchell in a doorway, chin up, a cold stare at Dexter** | w153, fits 9:16 with room for text. **103.4 is clean** (a passer-by blurs the foreground before 102; a door frame enters the right edge after 103.8). v9 "Hello, Arthur Mitchell." freeze |
| 53.5–55.5 | Trinity, medium close-up, looking off right | w322–335 |
| 81.7–85.3 | Trinity, close, side light, a slight smile | w455, too wide |
| 29.4–34.5 | Trinity talking to camera | w465, too wide |
| 85.3–89.7, 63.0–68.4 | Dexter's reaction close-ups | w394–404, borderline |
| 106.9–108.9 | CapCut end card | Don't use |

### `pack9_s4_best.mp4` (key `p9`): S4 "all best and most popular clips" (Trinity season), 1280×720, 60 fps container, 4:03, 102 shots

Uploaded as `Dexter_S4_4k_Scenepack_Dexter_Morgan_All_Best__Most_Popular_Clips_1.mp4`. The footage is **24p inside 60 fps** (near-repeat ratio 0.68, like p8), so use `interp="hold"` and don't slow it with flow. It is dense in S4 kills, night exteriors and Trinity. Shot list: `studio/packs/shots_p9.json`. Very dark shots (index): 0, 10, 44, 47, 49, 52.

| Time | Shot | Notes |
|---|---|---|
| 0.00–5.03 | Red-lit close-up, driving at night | w301, tight; little room for text. Under "Tonight's the night." |
| 21.60–26.52 | Boxing ring | |
| 26.53–31.12 | Blue night exterior | |
| 40.97–42.02 | Grin | Short beat |
| 46.85–50.90 | Grin beside a police car | |
| 73.70–78.30 | Night dock | Moody plate |
| 80.87–84.25 | Night garden | |
| 88.07–93.03 | In the car at night | Drive plate (pairs with p8 night drives) |
| 93.05–97.85 | Gun to the head | |
| 98.52–102.87 | Through the blinds | Light-slat transition candidate |
| **102.88–107.57** | **Plastic-wrapped table kill** | Kill-room centrepiece |
| 117.43–120.58 | Night stare | |
| 120.60–124.28 | Camera / photo beat | Shutter or flash transition candidate |
| 124.30–129.20 | Upside-down face | Rotation or flip transition candidate |
| 134.15–139.05 | Woods at night with a shovel | |
| 139.07–145.77 | Run of 0.1–0.4 s micro-shots | Flash-cut montage only; `check_sources.py` will flag ranges that cross them |
| 145.78–146.73 | Silhouette at the light table | Graphic silhouette |
| 157.05–160.98 | Double face in a reflection | Mirror/reflection transition candidate |
| 164.00–167.65 | Attack | Fast action |
| 177.30–180.12 | Knife | |
| 180.13–182.83 | Hammer | Trinity's weapon |
| 182.85–184.55 | Trinity wrapped in plastic | |
| 184.57–188.30 | Flashlight in the dark | Light-beam reveal candidate |
| 189.83–196.55 | Trinity at Miami Metro: the office stare-down | Cuts at 191.17, 192.58 and 194.43. 189.83–191.15 is Trinity's own close-up |
| 196.57–198.30 | Close-up | **w426, too wide for 9:16** |
| 198.32–199.25 | Car | |
| 203.23–211.72 | Parking-garage fight | Many short cuts |
| 222.12–225.37 | Gloved at night, holding Trinity's hammer, low angle | Under "Hello, Arthur Mitchell." |
| 226.57–229.95 | Kill | |
| 229.97–230.55 | Moon | Short; good loop or transition plate |
| 230.57–234.05 | Looks up | |
| 238.20–239.80 | Baby in the blood (the S4 finale) | Heavy; use with care |

**Dialogue lines** (Whisper on the pack audio, `studio/packs/tr_p9.json`). The pack has music under the voices, so these times are approximate, especially where Whisper spread one segment over many seconds. Before cutting a line, transcribe the Demucs vocal stem of that range (`tools/transcribe.py … --start S --dur D`).

| Time | Line | Notes |
|---|---|---|
| 0.2–1.4 | "Tonight's the night." | |
| 64.2–68.7 | "Loners are looked upon with suspicion. Those of us who prefer to work by ourselves…" | Whisper heard "Long are" |
| 84.5–86.5 | "Monsters come in all shapes and sizes." | Strong hook-setter; over him at Miami Metro |
| 118.6–120.2 | "…pieces of the puzzle were missing." | |
| **129.7–133.4** | **"I had to evolve. It was the only way to survive."** | Clean, tight timing; over him hugging Rita |
| ~138–144.5 | "Nothing lasts forever." | Words spread out; check the stem |
| ~155.2–156.3 | "I really do need to stab something." | Check the stem |
| 161.0–162.4 | "This is his solution to remorse: suicide." | |
| ~189–193 | "Hello, Dexter Morgan." (Trinity) | Over the office stare-down; spread timing, check the stem |
| **212.8–214.8** | **"How is it I can kill people and feel no regret…"** | |
| **223.0–224.0** | **"Hello, Arthur Mitchell."** | Over the gloved night shot (222.12–225.37), before the Trinity kill |
| **230.9–233.4** | **"I wonder if Rita's looking at this same moon."** | Over the moon (229.97) and looks-up (230.57) shots: a ready-made ending or loop line |

### `pack10_s4_24p.mp4` (key `p10`): S4 scene pack, 1280×720, **native 24 fps**, 3:04, 59 shots

Uploaded as `Dexter_Morgan_Dexter_S4_Scenepack_4K_1.mp4`. A true 24p file: play it at its own cadence (`interp="hold"`, the renderer repeats frames at 60) and never flow-interpolate it. Longer shots than p9, with more lab, boat and daylight Miami material. Shot list: `studio/packs/shots_p10.json`.

| Time | Shot | Notes |
|---|---|---|
| 4.83–9.25 | Lab | |
| 19.42–23.38 | Neck brace | **w355, too wide for text** |
| 31.42–36.08 | Lab | |
| 36.12–36.62 | Gloved hand | Short insert |
| 62.04–67.96 | Night interiors | |
| 87.83–91.21 | Drink | |
| 91.25–93.00 | Kneeling | |
| 93.04–94.38 | Boat, red shirt | |
| 101.29–105.75 | Woods | Two shots (cut at 102.88) |
| 111.00–112.38 | Dark shot | |
| 113.75–115.88 | Boat | |
| 130.33–132.67 | Pink shirt, palms | Miami daylight |
| 160.29–163.58 | Flashlight | |
| **163.62–165.79** | **Blood slide** | w267; slide-box transition plate (v7) |
| 165.83–168.58 | Plastic room | Cut at 167.42 |
| 178.54–180.92 | Photo wall | "Through a photo on the wall" transition |
| 180.96–183.83 | Under a lamp | |

**No dialogue: the audio track is digital silence** (−91 dB). Use it for picture only, and take sound from the song, room-tone beds or another pack.

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

More fb shots, verified in v10 (fb is 24p in a 60 fps container: use `interp="hold"`; `blend` only under afterimages):

| Time | Shot | Notes |
|---|---|---|
| 38.57–42.32 | Barry, suited with the hood down, standing in the dark lab, emblem glowing | Calm opener (v10) |
| 31.9–37.1 | Unmasked smile in the dark | v10 |
| 116.5–119.38 | **Eyes full of lightning** | w353; the charge before a drop (v10) |
| 83.8–85.08 | Lightning crawling over the suit; **chest emblem tracked at (731,462) → (745,632) source px** | v10 emblem dive |
| 4.28–6.22 | Crouched take-off, lightning erupting behind | v10 drop shot |
| **52.82–54.35** | **Masked Flash in the dark: his own gold lightning ignites along the suit, arcs across the shoulders** | w172; a real charge-up (v10 rev 2). The shot cuts at 54.35 to another speedster: stop at 54.30 |
| 37.12–38.55 | Unmasked (hood), a hard look, blue bokeh | v10 rev 2 |
| 136.43–138.97 | Masked close-up in the garage, calm, blue bokeh | w230 (v10 rev 2). 133.77–136.42 before it has purple/green lightning |
| 147.32–150.72 | Masked profile in deep red light | Grades magenta, suit lenses glow green: off-palette for the gold look |
| 124.38–124.78 | The lightning throw (bolt from his hand, bottom-left) | v10 |
| 112.48–116.48 | Garage: lightning run, then lightning arm | Magnus Labs sign in frame (v10) |
| 127.63–129.15 | The scream with lightning | v10 |
| 56.05–58.32 | Masked grin (S1 suit) | v10 |
| 109.68–112.47 | Masked, walking toward camera at night, centred | Hero-title plate (v10) |
| 10.30–12.08 | Barry (civilian) struck by lightning in the office | v10 |
| **12.10–22.55** | **Frozen time in the office:** the falling man frozen, Barry crouched with lightning at **x≈870** (w43: lock framing with `cx`) | v10 time freeze |
| 27.77–31.88 | Frozen Joe in the foreground; Barry at **x≈960–1000** reaching through lightning | v10 |
| 80.82–82.27 | **Sideways run, massive lightning trails** (dutch angle) | Face not detected: frame with `cx` (v10 finale) |
| 124.8–127.48 | Reverse-Flash (yellow suit) by a "FAST TRACK LABS" sign | Different speedster: avoid unless the concept needs him |
| 139.0–147.3, 129.2–130.6 | Purple/blue/green lightning; another speedster | Off-colour for Barry's gold: avoid or regrade |

### `flash_s4.mp4` (key `s4`): "FLASH SEASON 4 SCENE PACK 4K 60FPS", really 1280×720, 60 fps container with **24p content**, 3:06, 97 shots (v11)

Shots 0–12 are a CGI/fan-render city run plus a non-Flash face: skip them for live-action edits. Shot list: `v11/work/shots_s4.json`.

| Time | Shot | Notes |
|---|---|---|
| 28.67–30.80 | Masked, yellow lenses, gold lightning streaming off him, white sky | v11 drop shot (`ev=-0.15`: the sky clips) |
| 31.07–34.10 | **Grinning in the suit, swinging round** (S4 return) | v11 swagger shot |
| 62.87–63.98 | **Masked smirk close-up**, blue-grey | v11 |
| 79.75–80.42 | Barry in a tux disarming an Earth-X soldier, lightning on his chest; face at x≈760, y≈220 | v11 time freeze (`cx=760`) |
| 73.55–75.95 | Tux run through the wedding with lightning | Very orange and blown out: avoid or grade hard |
| 93.87–101.03 | Barry's intense close-ups facing Thawne (blue-grey), Thawne smirking in the Reverse-Flash suit, cowl down (95.47–96.75, 98.35–99.25); his **red streak** 99.27–99.70 | v11 cold open / the answer |
| 122.90–125.48 | Running in the dark with lightning, a guard behind | v11 (mixed cadence, 45 unique fps) |
| 137.18–138.60, 140.70–143.40 | **Low-angle lightning run** (the same S4E1 scene as fb 80.8) | v11 `cx=(500, 540)` |
| 146.37–147.70 | Frontal close-up, bright, calm | v11 final stare |
| 155.5–157.4 | Masked close-up in a bar, bokeh | v11 |
| 171.73–178.95 | **Flying through an explosion of fire** (wide 171.73–173.25, close 173.27–178.95) | v11 Speed Force moment |
| 178.97–185.93 | Standing in a burning street with a crowd | Not used yet |
| 57.77–61.75, 85.60–89.17, 160–167 | Moody masked close-ups (blue, cortex, night) | Spare |

### `reverse_flash.mp4` (key `rf`): "Reverse Flash CW Flash Scenepack Head Tracked Topazed 4K 60fps", really 1280×720, **true 60 fps**, 94 s, 56 shots (v11)

Every clip is a ~600×600 inset (x≈340–940, y≈60–660) over a blurred, scan-lined copy, with "SCENEPACK LINK IN DESC" at y≈680–705 and "Intro Clip" cards (37.7–39.7, 64.9–67.3, 80.3–93.8 end card). Frame inside the inset: `face=None`, `cx` on the panel, `z ≥ 1.24` (no watermark).

| Time | Shot | Notes |
|---|---|---|
| 13.00–13.98 | Harrison Wells (bruised), lit from the side, studded wall | v11 opener (`ev=0.55`: it's dark) |
| 15.00–15.98 | **The Reverse-Flash mask, frontal** | v11 |
| 33.97–34.95 | Eobard in the suit, cowl down, **red eyes**, smiling | v11 |
| 4.0–11.98, 19–22, 52–53, 75–76.5 | Red-eyed masked shots | Dark and soft |
| 18.00–18.98 | Wells with the glowing tachyon device | Spare |

---

## Songs (`src/`)

| File | Uploaded as | Notes |
|---|---|---|
| `bop.mp3` | `Dababy_-_BOP_Official_Audio.mp3` | 2:40, 127.0 BPM, P=0.23622, offset 0.1890. Spoken intro "…they're like, **Harrison**" 9.60; **beat drops in 9.64 (+24.8 dB)**; dip 13.42 with "Let's go!" 14.34; **drop 15.31** (the verse). Explicit verse (no captions). Bridge 121–138 (bass out) → return 140.03 (v11) |
| `let_it_happen.mp3` | `Tame_Impala_-_Let_It_Happen_Official_Video.mp3` | Radio edit, 4:16. 125.0 BPM, P=0.24003, offset 0.1920. Whirlwind breakdown 90.4–101.9 (no bass); **drop 101.94 (+26.5 dB)** "...when it happens"; "So let it happen" 107.7; **gated stutter 112.04–115.41** (silence every 4th half-beat); "All this running around" 115.24 (+15 dB) (v10) |
| `night_blooming_jasmine.mp3` | `fakemink_-_Night__Blooming_Jasmine_._official_music_video.mp3` | 102.8 BPM, P=0.29185. The second half is on its own grid (HB_OFF 0.1673: h482 = the drop at 140.839). Filtered breakdown 112–137.8 s, build 137.78, **dead silence 139.38–140.83, drop 140.84 (+26 dB)**. The instrumental repeats on a 4-bar cycle (bar h506 = bar h634). Hook *"night bloom jasmine, second name Yasmin"* at 74.8 and 187.12 (v9) |
| `paint_it_black.mp3` | `The_Rolling_Stones_-_Paint_It_Black_Official_Lyric_Video.mp3` | 160 BPM, P=0.18748, offset 0.0469. Sitar intro; **drums enter at 7.55 s (+22 dB)**; "I see a red door…" 14.0; bridge dip 87–96.5 → return 97.54; climax "painted, painted black" 157.4–175.7. Map and lyrics in `studio/songs/paint_it_black/` (not used yet) |
| `wish_you_well_rec.wav` | extracted from the screen recording `wish_you_well_screenrec.mov` | Brent Faiyaz "Wish You Well", 36 s. 138.05 BPM, P=0.21731, offset 0.0489. Beat returns at 19.17 s; break 27.86; "Darling," 30.04; **drop 33.08**; hook "I don't wish you well" 34.16–35.12 (v8) |
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
