// What Opus reads. This describes the studio's capabilities and data formats only; it deliberately
// contains no editing style. House style and presets come from the user's Studio knowledge.
import { store } from '../state/store';
import { AudioAnalysis, FONTS, MediaInfo, Project, TEXT_ANIMS_IN, TEXT_ANIMS_OUT, TRANSITIONS } from '../state/types';
import { projectDuration } from '../state/util';

export function reference(p: Project): string {
  return `HOW THE STUDIO WORKS
- Times are in seconds. The project is ${p.width}x${p.height} at ${p.fps} fps.
- Tracks are listed top to bottom; higher tracks draw on top. The video track marked "main" is magnetic: its clips always play back to back with no gaps, in order of their start times. Clips on other tracks sit exactly at their start time and may leave gaps. Text clips go on text tracks; sound-only clips go on audio tracks (a video file placed on an audio track contributes only its sound).
- A media clip plays source seconds [in, in + dur*speed) of its file, starting at timeline time start, for dur seconds of timeline. Video clips also play their own sound unless muted.
- A clip may not run past the end of its file: in + dur*speed must not exceed the media length.
- Clips on the same non-magnetic track must not overlap; an overlapping clip is moved to another track.

REPLY FORMAT
Reply with only one JSON object: {"message": string, "ops": [operation, ...]}
"message" is a few sentences for the user about what you did. The studio applies "ops" in order, as one undoable step, and reports any operation it had to reject or adjust.

OPERATIONS
{"op":"clear"}  remove every clip and reset the tracks (use it first when rebuilding from scratch)
{"op":"project","name":"..","width":1080,"height":1920,"fps":30,"background":"#000000"}
{"op":"track","id":"V3","kind":"video|audio|text","name":".."}  add a track; on an existing id it can set "name", "muted", "hidden"
{"op":"add","id":"c1","media":"m1","track":"V1","start":0,"in":12.5,"dur":2.0, ...clip fields}
{"op":"text","id":"t1","track":"T1","start":0.5,"dur":2.0,"text":"..", ...text fields}
{"op":"set","id":"c1", ...fields to change}  (start, dur, in, track and any clip or text field)
{"op":"remove","id":"c1"}  or  {"op":"remove","ids":["c1","c2"]}
{"op":"split","id":"c1","at":3.2,"newId":"c1b"}  split at timeline time "at"
Ids you give must be new and unique (letters, digits, - or _).

CLIP FIELDS (all optional)
speed 0.1-10 (default 1); keepPitch true|false (default true)
volume 0-4 (1 = as recorded); fadeIn, fadeOut (seconds); muted true|false
fit "cover" (fills the frame, crops; default) | "contain" (whole picture, may leave bars)
transform {x, y, scale, rotation, opacity}: x and y offset the centre in frame widths and heights (0,0 = centred); scale 1 = fitted size; rotation in degrees clockwise; opacity 0-1
kf {"scale": [[t, value, ease], ...], ...}: keyframes for x, y, scale, rotation, opacity, volume; t is seconds from the clip's start; ease is linear|in|out|inOut|hold (default inOut) and shapes the move to the next key
color {brightness, contrast, saturation, temperature, tint: -1..1; hue: -180..180; vignette, blur: 0..1}
transition {"type": .., "dur": seconds}: transition from the previous clip on the same track into this clip, centred on the cut; the previous clip must end exactly where this one starts. Types: ${TRANSITIONS.join(', ')}

TEXT FIELDS
text: the words (use \\n for a line break)
style {font, weight 100-900, italic, size (fraction of frame height), color, stroke (outline width as a fraction of size), strokeColor, shadow 0-1, bg (box behind each line), bgColor, align left|center|right, uppercase, tracking (em), lineHeight, maxWidth (fraction of frame width)}; colours are hex. Fonts: ${FONTS.join(', ')}
anim {in: ${TEXT_ANIMS_IN.join('|')}; out: ${TEXT_ANIMS_OUT.join('|')}; inDur; outDur}; "words" reveals one word after another across inDur
transform and kf work as for media clips; x and y move the text block's centre`;
}

const r2 = (v: number) => Math.round(v * 100) / 100;
const list = (a: number[], max = 9999) => a.slice(0, max).map(r2).join(', ') + (a.length > max ? ` … (${a.length} total)` : '');

function soundLine(a: AudioAnalysis): string {
  const parts: string[] = [];
  if (a.bpm) {
    parts.push(`tempo ${a.bpm} BPM (pulse strength ${a.pulse})`);
    parts.push(`beats: ${list(a.beats, 600)}`);
    parts.push(`downbeats: ${list(a.downbeats, 200)}`);
  } else {
    parts.push('no steady beat');
  }
  if (a.rises.length) parts.push(`sharp rises in level at: ${list(a.rises)}`);
  if (a.hits.length) parts.push(`strongest hits (strongest first): ${list(a.hits, 32)}`);
  if (a.quiet.length) parts.push(`quiet stretches: ${a.quiet.slice(0, 80).map(([s, e]) => `${r2(s)}-${r2(e)}`).join(', ')}`);
  // loudness as digits 0-9, one per half second
  const step = Math.max(1, Math.round(a.energyRate / 2));
  const digits: string[] = [];
  for (let i = 0; i < a.energy.length; i += step) {
    let s = 0, n = 0;
    for (let k = i; k < Math.min(a.energy.length, i + step); k++) { s += a.energy[k]; n++; }
    digits.push(String(Math.min(9, Math.round((s / Math.max(1, n)) * 9))));
  }
  if (digits.length) parts.push(`loudness 0-9 per half second from 0s: ${digits.join('').slice(0, 2400)}`);
  parts.push(`average level ${a.rmsDb} dBFS`);
  return parts.join('\n    ');
}

export function mediaCatalog(): string {
  const s = store.state;
  const rows: string[] = [];
  for (const id of s.mediaOrder) {
    const m: MediaInfo | undefined = s.media[id];
    if (!m || m.status !== 'ready') continue;
    const dims = m.kind !== 'audio' ? ` ${m.width}x${m.height}` : '';
    const len = m.kind === 'image' ? 'still image' : `${m.duration.toFixed(2)}s`;
    const fps = m.kind === 'video' ? ` ${m.fps}fps` : '';
    const snd = m.kind === 'image' ? '' : m.hasAudio ? ' with sound' : ' no sound';
    rows.push(`${m.id} ${m.kind} "${m.name}" ${len}${dims}${fps}${snd}`);
    if (m.analysis && m.hasAudio) rows.push(`    ${soundLine(m.analysis)}`);
    else if (m.hasAudio && m.analysisState !== 'done') rows.push('    (sound not analysed)');
  }
  return rows.length ? rows.join('\n') : '(the library is empty)';
}

export function timelineJson(p: Project): string {
  const tracks = p.tracks.map(t => ({ id: t.id, kind: t.kind, name: t.name, ...(t.main ? { main: true } : {}), ...(t.muted ? { muted: true } : {}), ...(t.hidden ? { hidden: true } : {}) }));
  const clips = [...p.clips].sort((a, b) => a.start - b.start).map(c => {
    const { track, ...rest } = c;
    return { ...rest, track };
  });
  return JSON.stringify({ name: p.name, width: p.width, height: p.height, fps: p.fps, background: p.background, duration: +projectDuration(p).toFixed(3), tracks, clips });
}

export function contextBlock(p: Project, imageCaptions: string[], imageNote?: string): string {
  const k = store.state.director.knowledge.trim();
  return [
    'You are the editor inside VOIDFX Studio, a video editing app. You build and change the user\'s edit by replying with operations that the studio applies to its timeline. You cannot watch or hear the media: the images and the sound analysis below are how you perceive it.',
    k ? `STUDIO KNOWLEDGE (from the user; follow it)\n${k}` : '',
    reference(p),
    `MEDIA\n${mediaCatalog()}`,
    imageNote ? `IMAGES\n${imageNote}` : imageCaptions.length ? `IMAGES (attached, in this order)\n${imageCaptions.map((c, i) => `${i + 1}. ${c}`).join('\n')}` : 'IMAGES: none attached.',
    `CURRENT TIMELINE\n${timelineJson(p)}`,
  ].filter(Boolean).join('\n\n');
}

/** Parse the JSON object Opus replies with. */
export function parseReply(text: string): { message: string; ops: unknown[] } | null {
  const tryParse = (s: string) => { try { return JSON.parse(s); } catch { return undefined; } };
  let v = tryParse(text.trim());
  if (v === undefined) {
    const fence = text.match(/```(?:json)?\s*([\s\S]*?)```/);
    if (fence) v = tryParse(fence[1]);
  }
  if (v === undefined) {
    const a = text.indexOf('{'), b = text.lastIndexOf('}');
    if (a >= 0 && b > a) v = tryParse(text.slice(a, b + 1));
  }
  if (!v || typeof v !== 'object') return null;
  if (Array.isArray(v)) return { message: '', ops: v };
  return { message: typeof v.message === 'string' ? v.message : '', ops: Array.isArray(v.ops) ? v.ops : [] };
}
