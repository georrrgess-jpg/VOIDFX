// Project model. Everything Opus or the user changes lives in `Project` and is plain JSON.

export type TrackKind = 'video' | 'audio' | 'text';
export type MediaKind = 'video' | 'audio' | 'image';
export type ClipKind = 'video' | 'audio' | 'image' | 'text';

export interface Track {
  id: string;
  kind: TrackKind;
  name: string;
  /** The magnetic main video track: clips are packed end to end. */
  main?: boolean;
  muted?: boolean;
  hidden?: boolean;
  locked?: boolean;
}

export type Ease = 'linear' | 'in' | 'out' | 'inOut' | 'hold';
/** A keyframe: time from the clip's start (timeline seconds), value, easing toward the next key. */
export interface Keyframe { t: number; v: number; e?: Ease }
export type AnimProp = 'x' | 'y' | 'scale' | 'rotation' | 'opacity' | 'volume';
export const ANIM_PROPS: AnimProp[] = ['x', 'y', 'scale', 'rotation', 'opacity', 'volume'];

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
  'spin', 'blur', 'glitch',
] as const;
export type TransitionType = typeof TRANSITIONS[number];
export interface TransitionSpec { type: TransitionType; dur: number }

export const TEXT_ANIMS_IN = ['none', 'fade', 'rise', 'drop', 'pop', 'blur', 'typewriter', 'words', 'slide_left', 'slide_right'] as const;
export const TEXT_ANIMS_OUT = ['none', 'fade', 'sink', 'lift', 'shrink', 'blur', 'words', 'slide_left', 'slide_right'] as const;
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
  color?: Partial<ColorAdjust>;
  /** Transition from the previous adjacent clip on the same track into this one. */
  transition?: TransitionSpec | null;
  kf?: Partial<Record<AnimProp, Keyframe[]>>;
  // text clips
  text?: string;
  style?: Partial<TextStyle>;
  anim?: Partial<TextAnim>;
}

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
}

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
  error?: string;
  analysis?: AudioAnalysis | null;
  analysisState?: 'pending' | 'running' | 'done' | 'none' | 'error';
}

export const DEFAULT_TRANSFORM: Transform = { x: 0, y: 0, scale: 1, rotation: 0, opacity: 1 };
export const DEFAULT_COLOR: ColorAdjust = { brightness: 0, contrast: 0, saturation: 0, temperature: 0, tint: 0, hue: 0, vignette: 0, blur: 0 };
export const DEFAULT_TEXT_STYLE: TextStyle = {
  font: 'Montserrat', weight: 800, italic: false, size: 0.045, color: '#ffffff', strokeColor: '#000000',
  stroke: 0, shadow: 0.5, bg: false, bgColor: '#000000', align: 'center', uppercase: false, tracking: 0, lineHeight: 1.12, maxWidth: 0.86,
};
export const DEFAULT_TEXT_ANIM: TextAnim = { in: 'fade', out: 'fade', inDur: 0.3, outDur: 0.25 };

export const FONTS = [
  'Montserrat', 'Poppins', 'Anton', 'Bebas Neue', 'Archivo Black', 'Oswald', 'Playfair Display', 'Permanent Marker', 'Space Mono', 'Geist',
];

export const ASPECTS: Record<string, [number, number]> = {
  '9:16': [1080, 1920], '4:5': [1080, 1350], '1:1': [1080, 1080], '16:9': [1920, 1080],
};
