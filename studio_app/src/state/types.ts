// Project model. Everything Opus or the user changes lives in `Project` and is plain JSON.

export type TrackKind = 'video' | 'audio' | 'text';
export type MediaKind = 'video' | 'audio' | 'image';
export type ClipKind = 'video' | 'audio' | 'image' | 'text' | 'sfx' | 'graphic' | 'shader';

export interface Track {
  id: string;
  kind: TrackKind;
  name: string;
  /** The magnetic main video track: clips are packed end to end. */
  main?: boolean;
  muted?: boolean;
  hidden?: boolean;
  locked?: boolean;
  /** 'look': the grade over every video track (under the text); 'over': effects drawn above the look. */
  role?: 'look' | 'over';
}

export type Ease = 'linear' | 'in' | 'out' | 'inOut' | 'hold';
/** A keyframe: time from the clip's start (timeline seconds), value, easing toward the next key. */
export interface Keyframe { t: number; v: number; e?: Ease }
export type AnimProp = 'x' | 'y' | 'scale' | 'rotation' | 'opacity' | 'volume' | 'speed';
export const ANIM_PROPS: AnimProp[] = ['x', 'y', 'scale', 'rotation', 'opacity', 'volume', 'speed'];

export interface Transform {
  /** Offset from centre as a fraction of frame width (+ right). */
  x: number;
  /** Offset from centre as a fraction of frame height (+ down). */
  y: number;
  /** 1 = fitted size (see `fit`). */
  scale: number;
  /** Degrees, clockwise. */
  rotation: number;
  /** 0..1 */
  opacity: number;
}

export interface ColorAdjust {
  brightness: number; // -1..1
  contrast: number; // -1..1
  saturation: number; // -1..1
  temperature: number; // -1..1 (warm +)
  tint: number; // -1..1 (magenta +)
  hue: number; // degrees -180..180
  vignette: number; // 0..1
  blur: number; // 0..1
}

export const TRANSITIONS = [
  'crossfade', 'dip_black', 'dip_white', 'flash',
  'slide_left', 'slide_right', 'slide_up', 'slide_down',
  'push_left', 'push_right', 'push_up', 'push_down',
  'wipe_left', 'wipe_right', 'wipe_up', 'wipe_down',
  'iris', 'zoom_in', 'zoom_out', 'whip_left', 'whip_right', 'whip_up', 'whip_down',
  'spin', 'blur', 'glitch', 'bolt',
  'logo', 'blink', 'ink', 'burn', 'slash', 'punch', 'light_leak', 'roll', 'shadow', 'warp',
  'cube_left', 'cube_right', 'cube_up', 'cube_down', 'flip_h', 'flip_v', 'shatter', 'slices', 'blinds', 'ripple', 'swirl', 'pixelate', 'kaleido',
  'heat', 'datamosh', 'tear', 'shutter', 'wiper', 'dive', 'light_sweep', 'wash',
] as const;
export type TransitionType = typeof TRANSITIONS[number];
export interface TransitionSpec {
  type: TransitionType;
  dur: number;
  /** Anchor on the outgoing picture (frame coordinates 0..1): where a dive, iris, burst or ripple centres. */
  at?: { x: number; y: number };
  /** Anchor on the incoming picture: where it emerges from (an eye, a light). */
  to?: { x: number; y: number };
}

export const TEXT_ANIMS_IN = ['none', 'fade', 'rise', 'drop', 'pop', 'blur', 'typewriter', 'words', 'letters', 'bloom', 'slam', 'fly', 'stamp', 'sweep', 'mask', 'track', 'flicker', 'slide_left', 'slide_right'] as const;
export const TEXT_ANIMS_OUT = ['none', 'fade', 'cap', 'sink', 'lift', 'shrink', 'blur', 'words', 'scatter', 'blowaway', 'streak', 'zoom', 'fall', 'slide_left', 'slide_right'] as const;
export type TextAnimIn = typeof TEXT_ANIMS_IN[number];
export type TextAnimOut = typeof TEXT_ANIMS_OUT[number];

export interface TextStyle {
  font: string;
  weight: number;
  italic: boolean;
  /** Font size as a fraction of frame height. */
  size: number;
  color: string;
  strokeColor: string;
  /** Outline width as a fraction of font size. */
  stroke: number;
  /** Shadow strength 0..1. */
  shadow: number;
  /** Background box. */
  bg: boolean;
  bgColor: string;
  align: 'left' | 'center' | 'right';
  uppercase: boolean;
  /** Letter spacing in em. */
  tracking: number;
  lineHeight: number;
  /** Wrap width as a fraction of frame width. */
  maxWidth: number;
  /** Colour of *emphasised* words (wrap a word in asterisks). */
  emphColor: string;
  /** Glow around emphasised words, 0..1. */
  emphGlow: number;
  /** Soft dark scrim behind the block, 0..1. */
  scrim: number;
  /** Size multiplier per line (lines split by \n), e.g. [1, 1.3]. */
  lineScales?: number[];
  /** Shrink each line to fit maxWidth instead of wrapping (the v9 caption rule: a line never wraps). */
  fit?: boolean;
  /** Footage-in-letters: the words become windows onto the picture, the rest of the frame darkens. */
  knockout?: boolean;
  /** How dark the frame goes around knockout letters, 0..1. */
  knockDark?: number;
  /** Particles thrown by the blow-away exit: the edit's own motif. */
  motif?: 'blood' | 'ash' | 'glass' | 'sparks' | 'petals';
}

export interface TextAnim { in: TextAnimIn; out: TextAnimOut; inDur: number; outDur: number }

export interface Clip {
  id: string;
  track: string;
  kind: ClipKind;
  /** Timeline start, seconds. */
  start: number;
  /** Timeline duration, seconds. */
  dur: number;
  name?: string;
  // media clips
  media?: string;
  /** Source in-point, seconds. Source out = in + dur * speed. */
  in?: number;
  speed?: number;
  keepPitch?: boolean;
  volume?: number;
  fadeIn?: number;
  fadeOut?: number;
  muted?: boolean;
  fit?: 'cover' | 'contain';
  transform?: Partial<Transform>;
  /** Where the subject (usually the face) is in the source picture, 0..1 from the top-left. The studio
   * crops the frame around it at any zoom, so it stays centred. */
  focus?: { x: number; y: number };
  color?: Partial<ColorAdjust>;
  /** Transition from the previous adjacent clip on the same track into this one. */
  transition?: TransitionSpec | null;
  kf?: Partial<Record<AnimProp, Keyframe[]>>;
  // sound-effect clips (generated by the studio)
  sfx?: SfxType;
  // text clips
  text?: string;
  /** Start time of each word, seconds from the clip start, for word-timed reveals. */
  words?: number[];
  style?: Partial<TextStyle>;
  anim?: Partial<TextAnim>;
  // custom layers written by Opus (or the owner): vector graphics and GPU effects
  /** Graphic: sanitized SVG markup. */
  svg?: string;
  /** Graphic width as a fraction of the frame width (height follows the SVG's viewBox). */
  gw?: number;
  /** Graphic and effect: how the layer combines with the picture under it. */
  blend?: BlendMode;
  /** Graphic: soft outer glow, 0..1. */
  glow?: number;
  /** Graphic: how it appears and leaves. */
  reveal?: Partial<GraphicReveal>;
  /** Effect: GLSL ES 3.0 source that defines `vec4 effect(vec2 uv, float t, float p)`. */
  code?: string;
  /** Effect from the studio's library: its id and parameters (the code is generated from them). */
  preset?: string;
  params?: Record<string, number | string>;
  /** 'all': the layer covers the edit from its start to the end, following its length (looks). */
  span?: 'all';
}

export type BlendMode = 'normal' | 'add' | 'screen';
export const BLEND_MODES: BlendMode[] = ['normal', 'add', 'screen'];
export const REVEALS_IN = ['none', 'fade', 'pop', 'iris', 'wipe', 'flicker'] as const;
export const REVEALS_OUT = ['none', 'fade', 'shrink', 'wipe', 'flicker'] as const;
export interface GraphicReveal { in: typeof REVEALS_IN[number]; out: typeof REVEALS_OUT[number]; inDur: number; outDur: number }

export interface Project {
  version: 1;
  id: string;
  name: string;
  width: number;
  height: number;
  fps: number;
  background: string;
  tracks: Track[];
  clips: Clip[];
  /** Camera that punches and kicks on the music's beats (video layers only; text stays clean). */
  camera?: BeatCamera;
  /** The song's lyrics as the owner supplied them (song times when timed). */
  lyrics?: Lyrics;
}

export interface LyricLine { t: number; text: string; end?: number; words?: number[] }
export interface Lyrics { timed: boolean; lines: LyricLine[]; raw: string }

export interface BeatCamera {
  on: boolean;
  /** Which beats hit: every beat, every other beat, or bar downbeats. */
  every: 'beat' | 'half' | 'downbeat';
  /** Zoom punch, e.g. 0.055 = +5.5 %. */
  punch: number;
  /** Rotation kick in degrees, alternating sides. */
  kick: number;
  /** Seconds for a hit to settle. */
  decay: number;
  /** Optional active range on the timeline. */
  from?: number;
  to?: number;
}

export const SFX = ['whoosh', 'swish', 'impact', 'hit', 'boom', 'riser', 'subdrop', 'reverse', 'glitch', 'shutter', 'tick', 'tapestop', 'zap', 'glass', 'rip'] as const;
export type SfxType = typeof SFX[number];

export interface AudioAnalysis {
  /** Estimated tempo, null when there is no steady pulse. */
  bpm: number | null;
  /** Confidence 0..1 of the tempo estimate. */
  pulse: number;
  beats: number[];
  downbeats: number[];
  /** Strongest transients (seconds), strongest first. */
  hits: number[];
  /** Loudness envelope, 0..1, sampled at `energyRate` Hz. */
  energy: number[];
  energyRate: number;
  /** Moments where the level jumps up sharply (likely drops / section starts). */
  rises: number[];
  /** Quiet stretches [start, end] of at least 0.25 s. */
  quiet: [number, number][];
  /** Overall loudness, dBFS RMS. */
  rmsDb: number;
}

/** Library entry. Runtime-only fields (file, url, thumbs) are not saved. */
export interface MediaInfo {
  id: string;
  name: string;
  kind: MediaKind;
  size: number;
  lastModified: number;
  mime: string;
  duration: number;
  width: number;
  height: number;
  fps: number;
  hasVideo: boolean;
  hasAudio: boolean;
  codec?: string;
  audioCodec?: string;
  /** Clockwise rotation from file metadata. */
  rotation: number;
  status: 'loading' | 'ready' | 'offline' | 'error';
  /** Key of the stored file in this browser's storage. */
  blobId?: string;
  /** Small JPEG data URL for cards. */
  poster?: string;
  /** Shots found in the file (scene packs). */
  shots?: [number, number][];
  /** Where it came from: imported by hand or taken from the AI database. */
  origin?: 'file' | 'library';
  libraryId?: string;
  tags?: string[];
  error?: string;
  analysis?: AudioAnalysis | null;
  analysisState?: 'pending' | 'running' | 'done' | 'none' | 'error';
}

export const DEFAULT_TRANSFORM: Transform = { x: 0, y: 0, scale: 1, rotation: 0, opacity: 1 };
export const DEFAULT_COLOR: ColorAdjust = { brightness: 0, contrast: 0, saturation: 0, temperature: 0, tint: 0, hue: 0, vignette: 0, blur: 0 };
export const DEFAULT_TEXT_STYLE: TextStyle = {
  font: 'Montserrat', weight: 800, italic: false, size: 0.045, color: '#ffffff', strokeColor: '#000000',
  stroke: 0, shadow: 0.5, bg: false, bgColor: '#000000', align: 'center', uppercase: false, tracking: 0, lineHeight: 1.12, maxWidth: 0.86,
  emphColor: '#ff2b3a', emphGlow: 0.6, scrim: 0,
};
/** The approved caption construction (v9 NIGHT BLOOM): heavy caps, keyline, soft shadow, red emphasis. */
export const STANDARD_CAPTION: Partial<TextStyle> = {
  font: 'Inter', weight: 900, uppercase: true, size: 0.046, lineScales: [1, 1.3], stroke: 0.035, strokeColor: '#080506', color: '#f5f7f7',
  shadow: 1, scrim: 0.34, emphColor: '#ff2b33', emphGlow: 0.7, lineHeight: 1.14, maxWidth: 0.87, fit: true, tracking: 0.01,
};
export const DEFAULT_CAMERA: BeatCamera = { on: true, every: 'beat', punch: 0.055, kick: 1.0, decay: 0.16 };
export const DEFAULT_TEXT_ANIM: TextAnim = { in: 'fade', out: 'fade', inDur: 0.3, outDur: 0.25 };

export const FONTS = [
  'Inter', 'Montserrat', 'Poppins', 'Anton', 'Bebas Neue', 'Archivo Black', 'Oswald', 'Playfair Display', 'Permanent Marker', 'Space Mono', 'Geist',
];

export const ASPECTS: Record<string, [number, number]> = {
  '9:16': [1080, 1920], '4:5': [1080, 1350], '1:1': [1080, 1080], '16:9': [1920, 1080],
};

// ---------- AI rounds, critiques and background jobs ----------

export type Effort = 'low' | 'medium' | 'high' | 'extra';

export interface JobStep { id: string; label: string; state: 'wait' | 'run' | 'done' | 'error' | 'skip'; detail?: string; t0?: number; t1?: number }

/** One issue the critic found. `at` is timeline seconds when the issue is at a moment. */
export interface CritiqueIssue { severity: 'critical' | 'major' | 'minor'; at?: number; area: string; problem: string; fix: string }

/** The critic's assessment of one round of an edit. */
export interface Critique {
  at: number;
  model?: string;
  /** 0-10, one decimal. */
  score: number;
  verdict: 'not ready' | 'close' | 'ready';
  headline: string;
  /** Category scores 0-10 (hook, rhythm, transitions, motion, text, sound, concept, picture, loop). */
  scores: Record<string, number>;
  strengths: string[];
  issues: CritiqueIssue[];
  /** How it compares with the owner's standards and the best TikTok edits of its kind. */
  versus: string;
  /** The critic's write-up for Opus: what the next round must do. */
  brief: string;
  /** Edit length and round the critique looked at. */
  duration: number;
  round: number;
}

/** One pass of Opus on a project: the build (round 1) or a revision. */
export interface Round {
  n: number;
  kind: 'create' | 'revise';
  at: number;
  jobId: string;
  effort: Effort;
  presetId: string;
  /** The owner's instructions for this round (notes for the build, the brief for a revision). */
  brief: string;
  /** Critic points the owner chose to pass on (revisions). */
  fromCritic?: string[];
  /** Opus's own summary: the concept and what changed. */
  summary?: string;
  applied?: number;
  model?: string;
  /** The critic's assessment of the result of this round. */
  critique?: Critique;
  /** The timeline as this round left it, so it can be restored. */
  snapshot?: Project;
}

export type JobKind = 'create' | 'revise' | 'critique';
export type JobState = 'queued' | 'running' | 'done' | 'error' | 'stopped' | 'interrupted';

export interface Job {
  id: string;
  kind: JobKind;
  projectId: string;
  projectName: string;
  state: JobState;
  steps: JobStep[];
  created: number;
  started?: number;
  finished?: number;
  round: number;
  effort: Effort;
  presetId: string;
  /** Round 1: the owner's notes, lyrics, database use and standards. */
  request?: { notes: string; lyrics: string; library: { mode: 'none' | 'auto' | 'picked'; ids: string[] }; standards?: string[] };
  /** Revisions: the owner's instructions and the critic points passed on. */
  brief?: string;
  fromCritic?: string[];
  /** Revisions: lyrics pasted in the revision stage (replace the project's lyrics). */
  lyrics?: string;
  /** What happens after this job: send to the critic, then revise automatically this many more times. */
  follow?: { critic: boolean; autoRounds: number };
  summary?: string;
  error?: string;
  /** The owner has seen the result. */
  seen?: boolean;
  streamChars?: number;
}
