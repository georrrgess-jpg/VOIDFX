// The automated ship checkpoint: the owner's measurable gates, run on the timeline.
// Gates that need eyes (faces, set-piece quality, "does it look drawn") stay with the reviewer.
import { Clip, MediaInfo, Project } from '../state/types';
import { clipEnd, projectDuration, textStyleOf, transformAt } from '../state/util';
import { timelineBeats } from './evaluate';
import { textBlockHeight } from './text';
import { FLASHY, TRANSITION_LABELS } from './transitions';
import { customIssues } from './custom';

export interface Check { id: string; label: string; status: 'pass' | 'warn' | 'fail' | 'info'; detail: string; at?: number[] }
export interface CheckOptions { houseRules: boolean; duration?: [number, number]; fps?: number; seam?: number | null }

const f2 = (t: number) => t.toFixed(2);

export function runChecks(p: Project, media: Record<string, MediaInfo>, o: CheckOptions): Check[] {
  const out: Check[] = [];
  const dur = projectDuration(p);
  if (dur <= 0) return [{ id: 'empty', label: 'Timeline', status: 'info', detail: 'The timeline is empty.' }];
  const visual = p.clips.filter(c => c.kind === 'video' || c.kind === 'image');
  const trans = p.clips.filter(c => c.transition);
  const main = p.tracks.find(t => t.main);
  const mainClips = p.clips.filter(c => c.track === main?.id).sort((a, b) => a.start - b.start);

  // format
  if (o.houseRules) {
    const okSize = p.width === 1080 && p.height === 1920;
    const okFps = p.fps === (o.fps || 60);
    out.push({ id: 'format', label: 'Format', status: okSize && okFps ? 'pass' : 'fail', detail: `${p.width}x${p.height} at ${p.fps} fps${okSize && okFps ? '' : ` (house standard: 1080x1920 at ${o.fps || 60} fps)`}` });
  }
  // length
  if (o.duration) {
    const [lo, hi] = o.duration;
    out.push({ id: 'length', label: 'Length', status: dur >= lo - 0.05 && dur <= hi + 0.05 ? 'pass' : 'warn', detail: `${f2(dur)} s (target ${lo}-${hi} s)` });
  }
  // transition density: library transitions plus custom effects or graphics laid over a cut
  const custom = p.clips.filter(c => c.kind === 'shader' || c.kind === 'graphic');
  const overCut = (t: number) => custom.some(c => c.start <= t + 0.02 && c.start + c.dur >= t - 0.02);
  const customCuts = mainClips.slice(1).filter(c => !c.transition && overCut(c.start)).length;
  const designed = trans.length + customCuts;
  const target = Math.max(15, Math.round(dur));
  const types = new Set(trans.map(c => c.transition!.type));
  out.push({
    id: 'density', label: 'Designed transitions', status: designed >= target ? 'pass' : designed >= 15 || !o.houseRules ? 'warn' : 'fail',
    detail: `${designed} in ${f2(dur)} s, ${types.size + (customCuts ? 1 : 0)} different${customCuts ? ` (${customCuts} are custom effects over a cut)` : ''} (target about ${target}: one per second)`,
  });
  // custom graphics and effects
  if (custom.length || o.houseRules) {
    const broken = customIssues(p);
    out.push({
      id: 'custom', label: 'Custom graphics and effects', status: broken.length ? 'fail' : custom.length ? 'pass' : 'warn',
      detail: broken.length ? broken.slice(0, 3).join('; ') : custom.length ? `${custom.filter(c => c.kind === 'shader').length} effects and ${custom.filter(c => c.kind === 'graphic').length} graphics designed for this edit.` : 'None yet: set pieces should carry at least one effect or graphic designed for this edit.',
      at: custom.map(c => c.start),
    });
  }
  // plain cuts
  const plain: number[] = [];
  for (let i = 1; i < mainClips.length; i++) if (!mainClips[i].transition && !overCut(mainClips[i].start)) plain.push(mainClips[i].start);
  const music = p.clips.filter(c => c.kind === 'audio' && c.media && media[c.media]?.analysis);
  const quietAt = (t: number) => music.every(c => {
    const a = media[c.media!].analysis!;
    if (t < c.start || t > clipEnd(c)) return true;
    const src = (c.in ?? 0) + (t - c.start) * (c.speed ?? 1);
    return (a.energy[Math.floor(src * a.energyRate)] ?? 0) < 0.3;
  });
  const quietPlain = plain.filter(quietAt);
  out.push({
    id: 'cuts', label: 'Plain cuts', status: quietPlain.length ? 'warn' : plain.length > dur / 2 ? 'warn' : 'pass',
    detail: plain.length ? `${plain.length} plain cut${plain.length > 1 ? 's' : ''} on the main track${quietPlain.length ? `, ${quietPlain.length} in quiet parts (the house rule wants a designed join there)` : ''}` : 'Every cut on the main track is a designed transition.',
    at: quietPlain.length ? quietPlain : plain,
  });
  // headspace: spans without any event
  const events: number[] = [0, dur];
  for (const c of p.clips) {
    if (c.kind === 'sfx' || c.kind === 'audio') continue;
    events.push(c.start);
    if (c.kind === 'shader' || c.kind === 'graphic') events.push(c.start + c.dur);
    if (c.transition) events.push(c.start);
    for (const keys of Object.values(c.kf || {})) for (const k of keys || []) if (c.kind !== 'text' || true) events.push(c.start + k.t);
    if (c.kind === 'text' && c.words) for (const w of c.words) events.push(c.start + w);
  }
  if (p.camera?.on) for (const b of timelineBeats(p, media)) if ((p.camera.from ?? 0) <= b.t && b.t <= (p.camera.to ?? Infinity)) events.push(b.t);
  events.sort((a, b) => a - b);
  const gaps: number[] = [];
  for (let i = 1; i < events.length; i++) if (events[i] - events[i - 1] > 1.1) gaps.push(events[i - 1]);
  out.push({ id: 'headspace', label: 'Headspace', status: gaps.length ? 'warn' : 'pass', detail: gaps.length ? `${gaps.length} span${gaps.length > 1 ? 's' : ''} longer than 1.1 s with no cut, transition, text beat or camera move` : 'Something happens at least every 1.1 s.', at: gaps });
  // logo
  const logos = trans.filter(c => c.transition!.type === 'logo');
  if (o.houseRules) out.push({ id: 'logo', label: 'voidfx logo', status: logos.length === 1 ? 'pass' : logos.length > 1 ? 'fail' : 'warn', detail: logos.length === 1 ? `Once, as a transition at ${f2(logos[0].start)} s.` : logos.length ? `${logos.length} times; the rule is exactly once.` : 'Not used yet; the rule is exactly once, as a transition.', at: logos.map(c => c.start) });
  // text
  const texts = p.clips.filter(c => c.kind === 'text');
  const pops = texts.filter(c => (c.anim?.in ?? 'fade') === 'none');
  const outBand: number[] = [];
  const small: number[] = [];
  for (const c of texts) {
    const s = textStyleOf(c);
    const tr = transformAt(c, Math.min(c.dur, 0.5));
    const h = textBlockHeight(c, p.width, p.height);
    const top = (0.5 + tr.y - h / 2) * 1920, bot = (0.5 + tr.y + h / 2) * 1920;
    if (o.houseRules && (top < 1240 - 40 || bot > 1640 + 40) && !(c.anim?.in === 'letters')) outBand.push(c.start);
    if (s.size * 1920 * Math.max(1, ...(s.lineScales || [1])) < 56) small.push(c.start);
  }
  if (texts.length) {
    const st = pops.length ? 'fail' : outBand.length || small.length ? 'warn' : 'pass';
    const parts = [`${texts.length} text clip${texts.length > 1 ? 's' : ''}`];
    if (pops.length) parts.push(`${pops.length} pop on with no ease-in`);
    if (outBand.length) parts.push(`${outBand.length} outside the 1240-1640 px caption band`);
    if (small.length) parts.push(`${small.length} may be too small to read on a phone`);
    out.push({ id: 'text', label: 'Text', status: st, detail: parts.join('; ') + '.', at: [...pops.map(c => c.start), ...outBand, ...small] });
  }
  // sounds for transitions
  const sfx = p.clips.filter(c => c.kind === 'sfx');
  const silent = trans.filter(c => !sfx.some(s => s.start >= c.start - 2.2 && s.start <= c.start + 0.4));
  if (trans.length) out.push({ id: 'sound', label: 'Transition sounds', status: silent.length ? (o.houseRules ? 'warn' : 'info') : 'pass', detail: silent.length ? `${silent.length} of ${trans.length} transitions have no sound effect (rule: every transition has its own sound).` : `All ${trans.length} transitions have a sound.`, at: silent.map(c => c.start) });
  // flashes
  const flashes = trans.filter(c => FLASHY.has(c.transition!.type)).map(c => c.start).sort((a, b) => a - b);
  let worst = 0, worstAt = 0;
  for (let i = 0; i < flashes.length; i++) {
    const n = flashes.filter(t => t >= flashes[i] && t < flashes[i] + 1).length;
    if (n > worst) { worst = n; worstAt = flashes[i]; }
  }
  out.push({ id: 'flash', label: 'Flash rate', status: worst > 3 ? 'fail' : 'pass', detail: worst > 3 ? `${worst} flash-type hits within one second at ${f2(worstAt)} s (limit 3).` : `At most ${worst} flash-type hit${worst === 1 ? '' : 's'} in any second.`, at: worst > 3 ? [worstAt] : [] });
  // music coverage
  const audioSpans = p.clips.filter(c => c.kind === 'audio').map(c => [c.start, clipEnd(c)] as [number, number]).sort((a, b) => a[0] - b[0]);
  let covered = 0, cur = 0;
  for (const [a, b] of audioSpans) { if (b > cur) { covered += b - Math.max(a, cur); cur = b; } }
  if (o.houseRules) out.push({ id: 'music', label: 'Music bed', status: covered >= dur - 0.1 ? 'pass' : audioSpans.length ? 'warn' : 'warn', detail: audioSpans.length ? `Music covers ${f2(covered)} of ${f2(dur)} s.` : 'No music clip on an audio track yet.' });
  // zoom on low-resolution sources
  const zoomed = visual.filter(c => {
    const m = c.media ? media[c.media] : undefined;
    if (!m || Math.min(m.width, m.height) > 760) return false;
    const keys = c.kf?.scale || [];
    const maxS = Math.max(c.transform?.scale ?? 1, ...keys.map(k => k.v));
    return maxS > 1.12;
  });
  if (zoomed.length) out.push({ id: 'zoom', label: 'Zoom on 720p', status: 'warn', detail: `${zoomed.length} clip${zoomed.length > 1 ? 's' : ''} zoom past 1.1x on 720p footage and may look soft.`, at: zoomed.map(c => c.start) });
  // loop seam (measured on rendered frames)
  if (o.seam !== undefined && o.seam !== null) out.push({ id: 'loop', label: 'Loop seam', status: o.seam <= 1 ? 'pass' : o.seam <= 8 ? 'warn' : 'fail', detail: `Last frame vs frame 0 differ by ${o.seam.toFixed(1)} (house standard <= 1; blurred mean difference).` });
  else if (o.houseRules) out.push({ id: 'loop', label: 'Loop seam', status: 'info', detail: 'Measured when Opus reviews, or press Measure.' });
  out.push({ id: 'eyes', label: 'Needs eyes', status: 'info', detail: 'Faces centred and uncut, set-piece quality and anything that looks drawn are checked by the review on rendered frames.' });
  return out;
}

export function checksText(checks: Check[]): string {
  return checks.filter(c => c.status !== 'pass').map(c => `- [${c.status.toUpperCase()}] ${c.label}: ${c.detail}${c.at?.length ? ` (at ${c.at.slice(0, 12).map(t => t.toFixed(2)).join(', ')} s)` : ''}`).join('\n') || '- Every automated gate passes.';
}

export function transitionName(c: Clip) { return c.transition ? TRANSITION_LABELS[c.transition.type] : ''; }
