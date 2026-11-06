// The owner's source library (studio/SCENE_PACKS.md): every scene pack with its measured quality,
// proven shots, dialogue lines and what to avoid, and every song with its tempo and key moments. When a
// project's file is recognised (by name, or by length + size + frame rate), Opus gets that pack's notes
// next to its contact sheets, so it starts from the shots that already worked.
import { MediaInfo } from '../state/types';

type Shot = [number, number, string];
type Line = [number, number, string];
export interface PackInfo {
  key: string; file: string; names: string[]; show: 'Dexter' | 'The Flash';
  duration: number; fps: number; w: number; h: number;
  quality: string; note: string; shots: Shot[]; lines?: Line[]; avoid?: string;
}
export interface SongInfo { key: string; file: string; names: string[]; bpm: number; notes: string; moments: [number, string][] }

export const PACKS: PackInfo[] = [
  {
    key: 'p8', file: 'pack8_s1.mp4', show: 'Dexter', duration: 407, fps: 60, w: 1280, h: 720,
    names: ['Dexter_4k_60fps_All_Scenes_Dexter_Morgan_S1_Best__Most_Popular_Scenes_for_Edit_-_Scenepack_1', 'pack8_s1'],
    quality: '0.43 Mb/s, the most compressed pack (blocks in dark and moving areas): wide or static shots only; detail 0.58',
    note: 'S1 best scenes: the richest pack, lots of close-ups and kill room.',
    shots: [[2.02, 5.02, 'South Beach street at night, neon hotels, no person (good logo backdrop)'], [31.65, 33.43, 'overhead of the kill table: headlamp over a wrapped victim'], [44.53, 50.6, 'studies a blood slide, big close-up (too tight for text)'], [77.65, 83.78, 'at the desk lit red (laptop)'], [110.82, 117.4, 'kitchen: intense stare 111.2-113.05, smile 114, rubs eye 115'], [117.42, 119.6, 'lollipop in the kitchen, playful'], [119.78, 123.28, 'his eye through a magnifying glass (eye centred from 121.2; soft source)'], [142.15, 147.6, 'sweaty profile, syringe (M99)'], [152.12, 153.68, 'green-lit stare'], [160.2, 166.9, 'lab, Miller Lite sign'], [173.5, 178.1, 'mangroves / jungle walk'], [256.18, 258.5, 'plastic-wrapped kill room, apron'], [262.13, 267.95, 'holds a blood slide up to the light (large face)'], [283.3, 284.48, 'lab: turns and smirks straight at camera (great ending beat)'], [315.48, 321.17, 'night drive lit red'], [344.32, 349.3, 'red-lit smirk, warm and menacing'], [355.33, 357.0, 'looks up, lit red'], [388.92, 390.37, 'stands over the kill table'], [392.15, 396.48, 'sits on the kill-room floor, gloved'], [405.9, 407.4, 'sunset smile, crowd']],
    lines: [[0.0, 4.3, '"Tonight\'s the night, and it\'s going to happen again, and again."'], [33.5, 36.2, '"My name is Dexter. Dexter Morgan."'], [202.7, 207.6, '"I love Halloween, the one time of year when everyone wears a mask, not just me."'], [225.8, 229.9, '"I like to pretend I\'m alone, completely alone."'], [296.4, 299.6, '"I have a dark side, too."'], [336.9, 337.8, '"Could it be him?"'], [344.3, 348.6, '"Harry\'s first rule was don\'t get emotionally involved. I think this is why."']],
    avoid: 'the confession 321.18-327.15 has a hidden jump cut at 325.217 and the owner disliked "I\'m a serial killer" as an ending; the jar-of-blood monologue 331.88-338.1 (owner disliked it)',
  },
  {
    key: 'p9', file: 'pack9_s4_best.mp4', show: 'Dexter', duration: 243, fps: 60, w: 1280, h: 720,
    names: ['Dexter_S4_4k_Scenepack_Dexter_Morgan_All_Best__Most_Popular_Clips_1', 'pack9_s4_best'],
    quality: '0.69 Mb/s, static close-ups only; detail 0.55; 24p inside a 60 fps container (no smooth slow motion)',
    note: 'S4 (Trinity season): kills, night exteriors, Trinity.',
    shots: [[0, 5.03, 'red-lit close-up driving at night (tight)'], [26.53, 31.12, 'blue night exterior'], [40.97, 42.02, 'grin (short beat)'], [46.85, 50.9, 'grin beside a police car'], [73.7, 78.3, 'night dock, moody plate'], [88.07, 93.03, 'in the car at night (drive plate)'], [93.05, 97.85, 'gun to the head'], [98.52, 102.87, 'through the blinds (light-slat transition candidate)'], [102.88, 107.57, 'plastic-wrapped table kill (kill-room centrepiece)'], [117.43, 120.58, 'night stare'], [120.6, 124.28, 'camera / photo beat (shutter or flash candidate)'], [124.3, 129.2, 'upside-down face (rotation or flip candidate)'], [134.15, 139.05, 'woods at night with a shovel'], [145.78, 146.73, 'silhouette at the light table'], [157.05, 160.98, 'double face in a reflection (mirror candidate)'], [164.0, 167.65, 'attack, fast action'], [177.3, 180.12, 'knife'], [180.13, 182.83, 'hammer (Trinity\'s weapon)'], [182.85, 184.55, 'Trinity wrapped in plastic'], [184.57, 188.3, 'flashlight in the dark (light-beam reveal candidate)'], [189.83, 191.15, 'Trinity\'s own close-up at Miami Metro'], [222.12, 225.37, 'gloved at night holding Trinity\'s hammer, low angle'], [226.57, 229.95, 'kill'], [229.97, 230.55, 'moon (short; loop or transition plate)'], [230.57, 234.05, 'looks up']],
    lines: [[0.2, 1.4, '"Tonight\'s the night."'], [84.5, 86.5, '"Monsters come in all shapes and sizes."'], [129.7, 133.4, '"I had to evolve. It was the only way to survive." (clean timing)'], [212.8, 214.8, '"How is it I can kill people and feel no regret..."'], [223.0, 224.0, '"Hello, Arthur Mitchell."'], [230.9, 233.4, '"I wonder if Rita\'s looking at this same moon." (ready-made ending or loop line)']],
    avoid: '139.07-145.77 is a run of 0.1-0.4 s micro-shots (flash cuts only); 196.57-198.3 close-up too wide for 9:16; 238.2-239.8 the baby in the blood is heavy; very dark shots at 0, 10, 44, 47, 49, 52 s',
  },
  {
    key: 'p10', file: 'pack10_s4_24p.mp4', show: 'Dexter', duration: 184, fps: 24, w: 1280, h: 720,
    names: ['Dexter_Morgan_Dexter_S4_Scenepack_4K_1', 'pack10_s4_24p'],
    quality: '0.76 Mb/s, OK; native 24 fps (play at its own cadence, never slow it smoothly); the audio is digital silence',
    note: 'S4: longer shots, lab, boat, daylight Miami.',
    shots: [[4.83, 9.25, 'lab'], [31.42, 36.08, 'lab'], [36.12, 36.62, 'gloved hand insert'], [62.04, 67.96, 'night interiors'], [87.83, 91.21, 'drink'], [91.25, 93.0, 'kneeling'], [93.04, 94.38, 'boat, red shirt'], [101.29, 105.75, 'woods (cut at 102.88)'], [113.75, 115.88, 'boat'], [130.33, 132.67, 'pink shirt, palms, Miami daylight'], [160.29, 163.58, 'flashlight'], [163.62, 165.79, 'blood slide (slide-box plate)'], [165.83, 168.58, 'plastic room (cut at 167.42)'], [178.54, 180.92, 'photo wall ("through a photo on the wall")'], [180.96, 183.83, 'under a lamp']],
    avoid: '19.42-23.38 neck brace: too wide for text',
  },
  {
    key: 'p7', file: 'pack7_4k.mp4', show: 'Dexter', duration: 35, fps: 60, w: 1280, h: 720,
    names: ['DEXTER_MORGAN_SCENE_PACK_4K_60_FPS_4k_scenepackforedit', 'pack7_4k'],
    quality: '2.10 Mb/s, good for close-ups; detail 0.59',
    note: '"4K" 60 fps scene pack (really 720p).',
    shots: [[0, 1.18, 'red kill room, Dexter seated (the v7 drop shot)'], [3.5, 10.1, 'wrapped in plastic sheeting, tools'], [10.1, 14.4, 'lab chair, hand to head'], [14.4, 17.6, 'office: walks toward camera with badge'], [19.2, 22.5, 'boat dock'], [22.52, 23.72, 'crime-scene tape crossing the frame as he walks'], [26.0, 28.2, 'palms, looks up startled'], [28.2, 32.2, 'night crime scene, badge'], [32.2, 35.3, 'kneeling with gloves']],
  },
  {
    key: 'p6', file: 'pack6_s5.mp4', show: 'Dexter', duration: 99, fps: 30, w: 1280, h: 720,
    names: ['Dexter_morgan_scenepack_S5E1_2_1080p', 'pack6_s5'],
    quality: '0.71 Mb/s, soft; detail 0.44',
    note: 'S5 episodes 1-2.',
    shots: [[0, 5.13, 'red shirt close-up: "It... was me." (It 1.13, was 2.70-2.92, me 3.06-3.38)'], [5.17, 8.47, 'red shirt at the crime scene'], [13.23, 15.67, 'walks out of the dark'], [15.7, 24.73, 'boat, pastel Miami skyline'], [24.77, 34.9, 'blood-speckled face (30.2-30.86)'], [68.13, 73.93, 'blue night profile (a channel bug at bottom right)'], [80.97, 86.73, 'interrogation']],
    lines: [[17.39, 23.51, '"I\'ve disappeared so many people. My turn now to disappear myself." (VO over the boat)']],
    avoid: '10.2-13.2 police tape mostly shows the back of a cop\'s head; 89.0-99.2 lit interrogation profile, face too wide',
  },
  {
    key: 'p5', file: 'pack5_mixtape120.mp4', show: 'Dexter', duration: 61, fps: 60, w: 1280, h: 720,
    names: ['Mixtape_Scenepack_4K_120FPS', 'pack5_mixtape120'],
    quality: '2.19 Mb/s, OK; detail 0.51',
    note: 'Mixtape scene pack.',
    shots: [[6.3, 7.62, 'grin by a pink wall'], [16.3, 17.1, 'turn'], [31.4, 33.1, 'night walk / night garden'], [36.2, 37.1, 'photos'], [39.85, 40.5, 'cap and sunglasses at night'], [41.3, 42.2, 'lamp'], [51.65, 53.75, 'boat with trash bags, sunlit (the v6 drop shot)']],
  },
  {
    key: 'p4', file: 'pack4_aesthetic.mp4', show: 'Dexter', duration: 79, fps: 29.97, w: 1280, h: 720,
    names: ['Aesthetic_Dexter_Scenepack', 'pack4_aesthetic'],
    quality: '1.70 Mb/s but the softest (filtered/graded): wide shots, not close-ups; detail 0.36',
    note: 'Aesthetic scene pack.',
    shots: [[16.55, 17.05, 'attack'], [33.3, 34.6, 'crime-scene crowd'], [56.6, 57.55, 'tackle / sunlit run through grass (56.8-57.45)'], [65.85, 67.15, 'grinning mid-kill (container)'], [70.7, 71.8, 'club, ice cream'], [72.86, 73.46, 'ice cream'], [74.95, 75.95, 'massacre']],
    avoid: 'four extreme close-ups are too wide for 9:16; 23.05 opens on hair; 30.7-32.0 unreadable macro of lips',
  },
  {
    key: 'p1', file: 'scenepack.mp4', show: 'Dexter', duration: 192, fps: 60, w: 1200, h: 720,
    names: ['135_Scenes_Dexter_Morgan_Scenepack_1', 'scenepack'],
    quality: '1.03 Mb/s, OK; detail 0.50',
    note: '135 scenes, mixed seasons.',
    shots: [[23.7, 24.37, 'container walk'], [43.65, 45.58, 'alibi walk'], [45.65, 47.58, 'black gloves on in daylight, eyes up to the lens'], [58.57, 59.15, 'face shield lowered over blood spatter ("unmask")'], [63.77, 65.68, 'finger-gun at the lens (the classic opener)'], [69.0, 70.33, 'ice cream, eyes go cold'], [70.55, 71.88, 'boat grin / laugh'], [76.3, 79.0, 'hand on face, gloved hands'], [92.7, 93.7, 'photo wall'], [95.0, 97.1, 'masked, "shh" finger to lips'], [102.15, 102.82, 'gloving at night'], [109.8, 110.47, 'blood slide raised to his eye'], [128.3, 128.95, 'victim POV through a slide'], [134.0, 139.1, 'rapture, smile reveal'], [158.3, 158.63, 'knife'], [171.1, 171.77, 'chain-link stare'], [179.98, 180.95, 'slide, cold open'], [186.35, 188.4, 'walks out of darkness']],
  },
  {
    key: 'tg', file: 'trinity_goodbye.mp4', show: 'Dexter', duration: 109, fps: 60, w: 1280, h: 720,
    names: ['Trinity_Finds_Out_Who_Dexter_Is_Goodbye_Dexter_Morgan_', 'trinity_goodbye'],
    quality: '1.46 Mb/s, soft; detail 0.44',
    note: 'S4E11 "Goodbye Dexter Morgan" (Miami Metro). Most close-ups are too wide for 9:16.',
    shots: [[99.75, 105.15, 'Arthur Mitchell in a doorway, chin up, cold stare (103.4 is clean)'], [53.5, 55.5, 'Trinity, medium close-up, looking off right']],
    avoid: 'Trinity close 81.7-85.3 and talking to camera 29.4-34.5 too wide; Dexter reactions 63.0-68.4 and 85.3-89.7 borderline; 106.9-108.9 is a CapCut end card',
  },
  {
    key: 'dk', file: 'doakes.mp4', show: 'Dexter', duration: 100, fps: 60, w: 1280, h: 720,
    names: ['Doakes_Catches_Dexter', 'doakes'],
    quality: '1.07 Mb/s, OK; detail 0.55',
    note: 'Doakes catches Dexter (the v3/v4 dialogue scene).',
    shots: [[46.05, 48.06, 'Dexter still (the scope view)'], [66.72, 67.98, 'Doakes\'s gun'], [95.49, 96.3, 'the barrel; the fight']],
    lines: [[16.2, 18.5, 'Doakes: "Jesus fucking Christ, you\'re the Bay Harbor Butcher." (BAY 18.02, HARBOR 18.22, BUTCHER 18.46)'], [19.06, 20.45, 'Dexter: "I really hate that name."'], [23.2, 25.12, 'Doakes: "I always knew there was something with you."'], [26.86, 28.97, 'Dexter: "What can I say? You were right about me."']],
  },
  {
    key: 'p2', file: 'scenepack2_60fps.mp4', show: 'Dexter', duration: 66, fps: 60, w: 1280, h: 720,
    names: ['4K_PACK', 'scenepack2_60fps'], quality: '2.02 Mb/s, good for close-ups; detail 0.65', note: 'Scene pack 2.', shots: [],
  },
  {
    key: 'p3', file: 'scenepack3_24fps.mp4', show: 'Dexter', duration: 30, fps: 23.976, w: 1280, h: 720,
    names: ['topaz_Dexter_S1-S8', 'scenepack3_24fps'], quality: '1.95 Mb/s, good for close-ups; detail 0.63', note: 'S1-S8 mix.',
    shots: [[24.3, 25.1, 'hooded, cap and sunglasses'], [12.2, 12.6, 'insert']],
  },
  {
    key: 'fb', file: 'flash_b.mp4', show: 'The Flash', duration: 151, fps: 60, w: 1280, h: 720,
    names: ['flash_b', 'The_flash_scenepack_all_seasons', 'THE_FLASH_SCENE_PACK'],
    quality: '1.18 Mb/s, good for close-ups; detail 0.60; 24p inside 60 fps',
    note: 'All seasons.',
    shots: [[38.57, 42.32, 'Barry suited, hood down, dark lab, emblem glowing (calm opener)'], [31.9, 37.1, 'unmasked smile in the dark'], [116.5, 119.38, 'eyes full of lightning (the charge before a drop)'], [83.8, 85.08, 'lightning crawling over the suit; chest emblem at (731,462)->(745,632) source px'], [4.28, 6.22, 'crouched take-off, lightning erupting behind (drop shot)'], [52.82, 54.3, 'masked in the dark: his gold lightning ignites along the suit (stop at 54.30)'], [37.12, 38.55, 'unmasked hood, hard look, blue bokeh'], [136.43, 138.97, 'masked close-up in the garage, calm'], [124.38, 124.78, 'the lightning throw (bolt from his hand, bottom-left)'], [112.48, 116.48, 'garage: lightning run, then lightning arm'], [127.63, 129.15, 'the scream with lightning'], [56.05, 58.32, 'masked grin (S1 suit)'], [109.68, 112.47, 'masked, walking toward camera at night, centred (hero-title plate)'], [10.3, 12.08, 'Barry struck by lightning in the office'], [12.1, 22.55, 'frozen time in the office (Barry crouched at x~870)'], [27.77, 31.88, 'frozen Joe; Barry reaching through lightning at x~960-1000'], [80.82, 82.27, 'sideways run, massive lightning trails']],
    avoid: 'the slow-mo run at the camera and the floating shot; 124.8-127.48 Reverse-Flash by FAST TRACK LABS (different speedster); 139.0-147.3 and 129.2-130.6 purple/green lightning of another speedster; 147.32-150.72 grades magenta',
  },
  {
    key: 'fa', file: 'flash_a.mp4', show: 'The Flash', duration: 102, fps: 25.4, w: 1280, h: 720,
    names: ['flash_a'], quality: '1.78 Mb/s, good; detail 0.58', note: 'Flash pack A (25.4 fps).',
    shots: [],
  },
  {
    key: 's4', file: 'flash_s4.mp4', show: 'The Flash', duration: 186, fps: 60, w: 1280, h: 720,
    names: ['FLASH_SEASON_4_SCENE_PACK_4K_60FPS', 'flash_s4'],
    quality: '1.08 Mb/s, soft: pick the crispest moments, keep zoom low; detail 0.39; 24p content',
    note: 'Season 4. Shots before 28 s are a CGI/fan-render run plus a non-Flash face: skip them.',
    shots: [[28.67, 30.8, 'masked, yellow lenses, gold lightning streaming off him, white sky (the sky clips)'], [31.07, 34.1, 'grinning in the suit, swinging round'], [62.87, 63.98, 'masked smirk close-up, blue-grey'], [79.75, 80.42, 'Barry in a tux disarming a soldier, lightning on his chest (face x~760)'], [93.87, 101.03, 'Barry facing Thawne; Thawne smirking cowl down 95.47-96.75, 98.35-99.25; red streak 99.27-99.70'], [122.9, 125.48, 'running in the dark with lightning'], [137.18, 138.6, 'low-angle lightning run'], [140.7, 143.4, 'low-angle lightning run'], [146.37, 147.7, 'frontal close-up, bright, calm'], [155.5, 157.4, 'masked close-up in a bar, bokeh'], [171.73, 178.95, 'flying through an explosion of fire (wide 171.73-173.25, close 173.27-178.95)'], [178.97, 185.93, 'standing in a burning street with a crowd']],
    avoid: '73.55-75.95 tux run is very orange and blown out',
  },
  {
    key: 'rf', file: 'reverse_flash.mp4', show: 'The Flash', duration: 94, fps: 60, w: 1280, h: 720,
    names: ['Reverse_Flash_CW_Flash_Scenepack_Head_Tracked_Topazed_4K_60fps', 'reverse_flash'],
    quality: '1.25 Mb/s, pre-sharpened (detail 1.18) inside its 600x600 inset',
    note: 'Every clip is a ~600x600 inset (x~340-940, y~60-660) over a blurred copy with "SCENEPACK LINK IN DESC" at the bottom: frame on the inset (focus inside it, scale >= 1.24).',
    shots: [[13.0, 13.98, 'Harrison Wells, bruised, side-lit'], [15.0, 15.98, 'the Reverse-Flash mask, frontal'], [33.97, 34.95, 'Eobard in the suit, cowl down, red eyes, smiling'], [18.0, 18.98, 'Wells with the glowing tachyon device']],
    avoid: '"Intro Clip" cards 37.7-39.7, 64.9-67.3, 80.3-93.8 (end card)',
  },
];

export const SONGS: SongInfo[] = [
  { key: 'bop', file: 'bop.mp3', names: ['Dababy_-_BOP_Official_Audio', 'bop'], bpm: 127, notes: 'explicit verse: two designed titles, no captions', moments: [[9.6, 'spoken "Harrison"'], [9.64, 'beat drops in (+24.8 dB)'], [13.42, 'dip'], [14.34, '"Let\'s go!"'], [15.31, 'drop (the verse)'], [121, 'bridge, bass out'], [140.03, 'return']] },
  { key: 'let_it_happen', file: 'let_it_happen.mp3', names: ['Tame_Impala_-_Let_It_Happen_Official_Video', 'let_it_happen'], bpm: 125, notes: 'radio edit', moments: [[90.4, 'whirlwind breakdown (no bass) to 101.9'], [101.94, 'drop (+26.5 dB) "...when it happens"'], [107.7, '"So let it happen"'], [112.04, 'gated stutter to 115.41 (a ready-made time freeze)'], [115.24, '"All this running around" (+15 dB)']] },
  { key: 'jasmine', file: 'night_blooming_jasmine.mp3', names: ['fakemink_-_Night__Blooming_Jasmine', 'night_blooming_jasmine'], bpm: 102.8, notes: 'repeats on a 4-bar cycle', moments: [[74.8, 'hook "night bloom jasmine, second name Yasmin"'], [112, 'filtered breakdown to 137.8'], [137.78, 'build'], [139.38, 'dead silence to 140.83'], [140.84, 'drop (+26 dB)'], [187.12, 'hook again']] },
  { key: 'paint_it_black', file: 'paint_it_black.mp3', names: ['The_Rolling_Stones_-_Paint_It_Black_Official_Lyric_Video', 'paint_it_black'], bpm: 160, notes: 'not used yet', moments: [[7.55, 'drums enter (+22 dB) after the sitar intro'], [14.0, '"I see a red door..."'], [87, 'bridge dip to 96.5'], [97.54, 'return'], [157.4, 'climax "painted, painted black" to 175.7']] },
  { key: 'wish_you_well', file: 'wish_you_well_rec.wav', names: ['wish_you_well_rec', 'wish_you_well_screenrec'], bpm: 138.05, notes: '36 s screen recording', moments: [[19.17, 'beat returns'], [27.86, 'break'], [30.04, '"Darling,"'], [33.08, 'drop'], [34.16, 'hook "I don\'t wish you well" to 35.12']] },
  { key: 'him_all_along', file: 'him_all_along.mp3', names: ['Gunna_-_Him_All_Along_Official_Visualizer', 'him_all_along'], bpm: 130, notes: '', moments: [[121.9, 'breakdown'], [131.92, 'hook "HIM ALL ALONG" to 132.30'], [133.0, 'return (+17 dB): the good part']] },
  { key: 'warmpop', file: 'warmpop.mp3', names: ['ESPRIT____George_Clanton_-_Warmpop', 'warmpop'], bpm: 90, notes: '', moments: [[117, 'filtered build to 148.5'], [149.54, 'the full mix returns']] },
  { key: 'need_it', file: 'need_it.mp3', names: ['Migos_-_Need_It', 'need_it'], bpm: 74, notes: '', moments: [] },
  { key: 'duvet', file: 'duvet.mp3', names: ['B_a_-_Duvet_Lyrics', 'duvet'], bpm: 93, notes: 'the lyric is "you don\'t even FEEL a thing"', moments: [] },
  { key: 'blood_theme', file: 'blood_theme.mp3', names: ['Blood_Theme_Instrumental', 'blood_theme'], bpm: 0, notes: 'Dexter theme', moments: [[113.047, 'hard stop']] },
];

const norm = (s: string) => s.toLowerCase().replace(/\.[a-z0-9]{2,4}$/, '').replace(/[^a-z0-9]+/g, ' ').trim();

/** The scene pack a media file is, if the studio knows it (by name, or by its length, size and frame rate). */
export function recognizePack(m: MediaInfo): PackInfo | undefined {
  if (m.kind !== 'video') return undefined;
  const n = norm(m.name);
  const byName = PACKS.find(p => p.names.some(x => { const k = norm(x); return n === k || (k.length > 12 && n.includes(k)); }));
  if (byName) return byName;
  const byShape = PACKS.filter(p => Math.abs(p.duration - m.duration) < 1.6 && p.w === m.width && p.h === m.height && Math.abs(p.fps - (m.fps || 0)) < 1.5);
  return byShape.length === 1 ? byShape[0] : undefined;
}

/** The song a media file is, if the studio knows it (by name; tempo must agree when analysed). */
export function recognizeSong(m: MediaInfo): SongInfo | undefined {
  if (!m.hasAudio) return undefined;
  const n = norm(m.name);
  const hit = SONGS.find(s => s.names.some(x => { const k = norm(x); return n === k || (k.length > 4 && n.includes(k)); }));
  if (!hit) return undefined;
  const bpm = m.analysis?.bpm;
  if (bpm && hit.bpm && Math.abs(bpm - hit.bpm) > 4 && Math.abs(bpm - hit.bpm * 2) > 6 && Math.abs(bpm * 2 - hit.bpm) > 6) return undefined;
  return hit;
}

const r2 = (v: number) => (Math.round(v * 100) / 100).toString();

/** Notes for Opus about a recognised file, in the media catalog. */
export function sourceNotes(m: MediaInfo): string {
  const p = recognizePack(m);
  if (p) {
    const out = [`recognised scene pack "${p.file}" (${p.show}): ${p.note} Quality: ${p.quality}.`];
    if (p.shots.length) out.push(`proven shots (source seconds): ${p.shots.map(([a, b, d]) => `${r2(a)}-${r2(b)} ${d}`).join('; ')}`);
    if (p.lines?.length) out.push(`dialogue lines: ${p.lines.map(([a, b, d]) => `${r2(a)}-${r2(b)} ${d}`).join('; ')}`);
    if (p.avoid) out.push(`avoid: ${p.avoid}`);
    return out.join('\n    ');
  }
  const s = recognizeSong(m);
  if (s) return `recognised song "${s.file}"${s.bpm ? ` (${s.bpm} BPM)` : ''}${s.notes ? `: ${s.notes}` : ''}. Key moments (song seconds): ${s.moments.map(([t, d]) => `${r2(t)} ${d}`).join('; ') || 'none noted'}`;
  return '';
}
