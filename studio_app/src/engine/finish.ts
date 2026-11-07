// The studio's finishing pass: deterministic fixes for the defects the critic kept marking down on test
// edits, applied after every pass Opus makes so they never reach the owner. Each fix is reported.
import { Project } from '../state/types';
import { clipEnd, projectDuration, transformAt } from '../state/util';
import { FLASHY } from './transitions';

const FLASH_FX = new Set(['exposure_wash', 'impact_frame', 'flash']);
/** Anchored light, particles and props that must sit off the face. */
const OFF_FACE = new Set(['light_rays', 'lens_flare', 'spotlight', 'flashlight', 'sparks_burst', 'glass_burst', 'shockwave', 'blood_lens', 'lightning_arc']);

export function finishPass(p: Project): string[] {
  const notes: string[] = [];
  const dur = projectDuration(p);
  if (dur <= 0) return notes;
  const mainT = p.tracks.find(t => t.main)?.id;
  const lookIds = new Set(p.tracks.filter(t => t.role === 'look').map(t => t.id));

  // 1. the loop in sound: the song runs to the last frame (a fade that comes back at full level breaks the loop)
  const bed = p.clips.filter(c => c.kind === 'audio' && c.media).sort((a, b) => b.dur - a.dur)[0];
  const stop = p.clips.some(c => c.kind === 'sfx' && c.sfx === 'tapestop' && c.start > dur - 1.5);
  if (bed && (bed.fadeOut ?? 0) > 0.05 && Math.abs(clipEnd(bed) - dur) < 0.15 && !stop) {
    bed.fadeOut = 0;
    notes.push('the studio removed the music fade at the end, so the loop does not come back at full level');
  }

  // 2. one flash per hit: a flash effect on the frames of another flash (effect or transition) is a white card
  const trans = p.clips.filter(c => c.transition);
  const flashes = p.clips.filter(c => c.kind === 'shader' && c.preset && FLASH_FX.has(c.preset)).sort((a, b) => a.start - b.start);
  const kept: typeof flashes = [];
  const removed: string[] = [];
  for (const c of flashes) {
    const clash = kept.some(d => d.start < c.start + c.dur && c.start < d.start + d.dur)
      || trans.some(x => FLASHY.has(x.transition!.type) && Math.abs(x.start - c.start) < Math.max(0.2, (x.transition!.dur || 0.4) / 2));
    if (clash) removed.push(c.id); else kept.push(c);
  }
  if (removed.length) {
    p.clips = p.clips.filter(c => !removed.includes(c.id));
    notes.push(`the studio removed ${removed.length} stacked flash effect${removed.length > 1 ? 's' : ''} (${removed.join(', ')}): one flash per hit, or the hit blows out to a white card`);
  }

  // 3. light and props off the face: an anchored layer in the face zone over a shot framed on a face moves to the side
  const moved: string[] = [];
  for (const c of p.clips) {
    if (c.kind !== 'shader' || !c.preset || !OFF_FACE.has(c.preset) || lookIds.has(c.track)) continue;
    const under = p.clips.find(m => m.track === mainT && m.start <= c.start + 0.05 && m.start + m.dur > c.start + 0.05);
    if (!under?.focus) continue;
    const tr = transformAt(c, Math.min(c.dur, 0.2));
    const x = 0.5 + (tr.x ?? 0), y = 0.5 + (tr.y ?? 0);
    if (x <= 0.36 || x >= 0.64 || y <= 0.28 || y >= 0.56) continue;
    const nx = x < 0.5 ? 0.2 : 0.8;
    const ny = c.preset === 'light_rays' || c.preset === 'lens_flare' || c.preset === 'spotlight' ? 0.14 : y;
    c.transform = { ...(c.transform || {}), x: +(nx - 0.5).toFixed(4), y: +(ny - 0.5).toFixed(4) };
    if (c.kf) { delete c.kf.x; delete c.kf.y; }
    moved.push(`${c.preset} ${c.start.toFixed(2)} s`);
  }
  if (moved.length) notes.push(`the studio moved ${moved.join(', ')} off the face (house rule: nothing over his face)`);
  return notes;
}

/** Moments where more than four picture layers (effects, graphics, shaders, transitions) start within half a second. */
export function clutter(p: Project): number[] {
  const lookIds = new Set(p.tracks.filter(t => t.role === 'look').map(t => t.id));
  const starts = [
    ...p.clips.filter(c => (c.kind === 'shader' || c.kind === 'graphic') && !lookIds.has(c.track) && c.span !== 'all').map(c => c.start),
    ...p.clips.filter(c => c.transition).map(c => c.start),
  ].sort((a, b) => a - b);
  const out: number[] = [];
  for (let i = 0; i < starts.length; i++) {
    const n = starts.filter(t => t >= starts[i] && t < starts[i] + 0.5).length;
    if (n > 4 && !out.some(t => Math.abs(t - starts[i]) < 0.5)) out.push(starts[i]);
  }
  return out;
}
