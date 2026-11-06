// The automated ship checkpoint: the owner's measurable gates, run on the timeline.
// Gates that need eyes (faces, set-piece quality, "does it look drawn") stay with the reviewer.
import { Clip, MediaInfo, Project } from '../state/types';
import { clipEnd, projectDuration, textStyleOf, transformAt } from '../state/util';
import { timelineBeats } from './evaluate';
import { textBlockHeight } from './text';
import { FLASHY, GENERIC, TRANSITION_LABELS } from './transitions';
import { QUIET_TRANSITIONS, sfxBudget, sfxEvents } from '../state/ops';
import { customIssues } from './custom';
import { getFx } from './fxlib';

export interface Check { id: string; label: string; status: 'pass' | 'warn' | 'fail' | 'info'; detail: string; at?: number[]; /** A one-click fix the panel can offer. */ action?: 'thin-sfx' | 'add-sfx' }
export interface CheckOptions { houseRules: boolean; duration?: [number, number]; fps?: number; seam?: number | { seam: number; step: number } | null }

const f2 = (t: number) => t.toFixed(2);

export function runChecks(p: Project, media: Record<string, MediaInfo>, o: CheckOptions): Check[] {
  const out: Check[] = [];
  const dur = projectDuration(p);
  if (dur <= 0) return [{ id: 'empty', label: 'Timeline', status: 'info', detail: 'The timeline is empty.' }];
  const visual = p.clips.filter(c => c.kind === 'video' || c.kind === 'image');
  const trans = p.clips.filter(c => c.transition);
  const main = p.tracks.find(t => t.main);
  const mainClips = p.clips.filter(c => c.track === main?.id).sort((a, b) => a.start - b.start);
  const music = p.clips.filter(c => c.kind === 'audio' && c.media && media[c.media]?.analysis);

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
  // the benchmarks: 16-27 designed joins in 21-27 s, i.e. about three for every four seconds or more
  const target = Math.max(15, Math.round(dur * 0.72));
  const types = new Set(trans.map(c => c.transition!.type));
  out.push({
    id: 'density', label: 'Designed transitions', status: designed >= target ? 'pass' : designed >= 15 || !o.houseRules ? 'warn' : 'fail',
    detail: `${designed} in ${f2(dur)} s, ${types.size + (customCuts ? 1 : 0)} different${customCuts ? ` (${customCuts} are custom effects over a cut)` : ''} (target ${target} or more: the benchmarks have 16-27 in 21-27 s)`,
  });
  // variety: generic library moves are filler, and the same move twice in a row reads as a template
  if (o.houseRules && designed >= 4) {
    const generic = trans.filter(c => GENERIC.has(c.transition!.type));
    const seq = mainClips.filter(c => c.transition);
    const repeats: number[] = [];
    for (let i = 1; i < seq.length; i++) if (seq[i].transition!.type === seq[i - 1].transition!.type && seq[i].transition!.type !== 'logo') repeats.push(seq[i].start);
    const share = generic.length / designed;
    out.push({
      id: 'variety', label: 'Transition variety', status: share > 0.4 ? 'fail' : share > 0.25 || repeats.length > 1 ? 'warn' : 'pass',
      detail: `${generic.length} of ${designed} joins are generic library moves (${Math.round(share * 100)}%; house limit a quarter: signature transitions, custom effects over the cut and motion-matched cuts carry the edit)${repeats.length ? `; the same move twice in a row ${repeats.length} time${repeats.length > 1 ? 's' : ''}` : ''}.`,
      at: [...generic.map(c => c.start), ...repeats].sort((a, b) => a - b),
    });
  }
  // framing: a wide source without a focus point crops to its middle, which is rarely where the face is
  if (p.height > p.width) {
    const unframed = p.clips.filter(c => {
      if ((c.kind !== 'video' && c.kind !== 'image') || !c.media || c.focus || (c.fit ?? 'cover') !== 'cover') return false;
      if (p.tracks.find(t => t.id === c.track)?.kind !== 'video') return false;
      const m = media[c.media];
      if (!m?.width || !m.height || m.width / m.height < (p.width / p.height) * 1.3) return false;
      return Math.abs(c.transform?.x ?? 0) < 0.005 && !(c.kf?.x?.length);
    });
    out.push({
      id: 'framing', label: 'Framing', status: unframed.length ? 'warn' : 'pass',
      detail: unframed.length ? `${unframed.length} shot${unframed.length > 1 ? 's' : ''} from wide sources have no focus point, so they crop to the middle of the source: set "focus" on the face (read it off the cyan ruler on the contact sheets).` : 'Every shot from a wide source is framed on its subject.',
      at: unframed.map(c => c.start),
    });
  }
  // pacing: an arc, not one uniform pace; flash cuts only as a burst on the drop
  if (o.houseRules && mainClips.length >= 4) {
    const shots = mainClips.map(c => c.dur);
    const avg = shots.reduce((a, b) => a + b, 0) / shots.length;
    const sd = Math.sqrt(shots.reduce((a, b) => a + (b - avg) ** 2, 0) / shots.length);
    const drops = music.flatMap(c => (media[c.media!].analysis!.rises || []).map(r => c.start + (r - (c.in ?? 0)) / (c.speed ?? 1))).filter(t => t > dur * 0.2 && t < dur * 0.75);
    const drop = drops[0];
    const flash = mainClips.filter(c => c.dur < 0.3);
    const stray = flash.filter(c => drop === undefined || c.start < drop - 0.6 || c.start > drop + 3.5);
    const lo = Math.round(dur * 0.68), hi = Math.round(dur * 1.55);
    const uniform = shots.length >= 10 && sd / avg < 0.22;
    const bad = flash.length > 4 || stray.length > 0 || shots.length < lo || shots.length > hi || uniform;
    const parts = [`${shots.length} shots, average ${avg.toFixed(2)} s (house range about ${lo}-${hi} for ${f2(dur)} s)`];
    if (flash.length) parts.push(`${flash.length} flash cut${flash.length > 1 ? 's' : ''} under 0.3 s${stray.length ? `, ${stray.length} outside the drop burst` : ''} (limit 4, on the drop only)`);
    if (uniform) parts.push('one uniform pace: hold the cold open and a breath after the drop, tighten into the drop');
    out.push({ id: 'pacing', label: 'Pacing', status: bad ? 'warn' : 'pass', detail: parts.join('; ') + '.', at: stray.length ? stray.map(c => c.start) : flash.map(c => c.start) });
  }
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
    for (const [prop, keys] of Object.entries(c.kf || {})) {
      if (!keys?.length) continue;
      for (const k of keys) events.push(c.start + k.t);
      // a keyframed move (push-in, drift, ramp) is happening all the way between its keys
      if (['scale', 'x', 'y', 'rotation', 'speed'].includes(prop)) for (let i = 1; i < keys.length; i++) {
        if (keys[i - 1].e === 'hold' || Math.abs(keys[i].v - keys[i - 1].v) < (prop === 'scale' ? 0.02 : prop === 'rotation' ? 1 : prop === 'speed' ? 0.15 : 0.01)) continue;
        for (let t = keys[i - 1].t + 0.5; t < keys[i].t; t += 0.5) events.push(c.start + t);
      }
    }
    if (c.kind === 'text' && c.words) for (const w of c.words) events.push(c.start + w);
  }
  const beatsAll = timelineBeats(p, media);
  // effects that react to the beat are a beat moment on every beat they span
  for (const c of p.clips) if (c.kind === 'shader' && c.preset && getFx(c.preset)?.beat) for (const b of beatsAll) if (b.t >= c.start && b.t <= c.start + c.dur) events.push(b.t);
  const camOn = (t: number) => !!p.camera?.on && (p.camera.from ?? 0) <= t && t <= (p.camera.to ?? Infinity) && (!p.camera.sections?.length || p.camera.sections.some(x => t >= x.from && t <= x.to));
  for (const b of beatsAll) if (camOn(b.t)) events.push(b.t);
  events.sort((a, b) => a - b);
  const gaps: number[] = [];
  for (let i = 1; i < events.length; i++) if (events[i] - events[i - 1] > 1.1) gaps.push(events[i - 1]);
  out.push({ id: 'headspace', label: 'Headspace', status: gaps.length ? 'warn' : 'pass', detail: gaps.length ? `${gaps.length} span${gaps.length > 1 ? 's' : ''} longer than 1.1 s with no cut, transition, text beat, camera move, keyframed move or beat effect` : 'Something happens at least every 1.1 s.', at: gaps });
  // logo
  const logos = trans.filter(c => c.transition!.type === 'logo');
  if (o.houseRules) out.push({ id: 'logo', label: 'voidfx logo', status: logos.length === 1 ? 'pass' : logos.length > 1 ? 'fail' : 'warn', detail: logos.length === 1 ? `Once, as a transition at ${f2(logos[0].start)} s.` : logos.length ? `${logos.length} times; the rule is exactly once.` : 'Not used yet; the rule is exactly once, as a transition.', at: logos.map(c => c.start) });
  // look and layers: one grade over the edit and depth in every section (bare footage reads flat)
  if (o.houseRules && dur > 2) {
    const lookIds = new Set(p.tracks.filter(t => t.role === 'look').map(t => t.id));
    const looks = p.clips.filter(c => lookIds.has(c.track));
    const shots = p.clips.filter(c => (c.kind === 'video' || c.kind === 'image') && p.tracks.find(t => t.id === c.track)?.main);
    const graded = shots.filter(c => c.color && Object.values(c.color).some(v => Math.abs(Number(v) || 0) > 0.02)).length;
    const layers = p.clips.filter(c => (c.kind === 'graphic' || c.kind === 'shader') && !lookIds.has(c.track));
    const secs = Math.floor(dur);
    const bare: number[] = [];
    for (let s0 = 0; s0 < secs; s0++) if (!layers.some(c => c.start < s0 + 1 && c.start + c.dur > s0)) bare.push(s0);
    let run = 0, longest = 0;
    for (let s0 = 0; s0 < secs; s0++) { run = bare.includes(s0) ? run + 1 : 0; longest = Math.max(longest, run); }
    const share = secs ? bare.length / secs : 0;
    const noLook = !looks.length && graded < shots.length / 2;
    const lib = layers.filter(c => c.preset).length;
    out.push({
      id: 'layers', label: 'Look and layers', status: noLook && share > 0.7 ? 'fail' : noLook || share > 0.4 || longest >= 4 ? 'warn' : 'pass',
      detail: `${looks.length ? `Look: ${[...new Set(looks.map(c => c.preset || c.name || 'custom'))].join(', ')}` : graded ? `No library look; ${graded} of ${shots.length} shots graded by hand` : 'No look: the footage keeps its own grade (give the edit its own look)'}; ${lib} library effect${lib === 1 ? '' : 's'} and ${layers.length - lib} custom graphic${layers.length - lib === 1 ? '' : 's'} or effect${layers.length - lib === 1 ? '' : 's'}; ${bare.length} of ${secs} seconds have no graphic or effect layer${longest >= 3 ? ` (longest bare stretch ${longest} s)` : ''}.`,
      at: bare.map(x => x + 0.5),
    });
  }
  // nothing drawn over his face: an anchored overlay effect in the face zone (with focus set, the face
  // sits near (0.5, 0.42) of the frame) breaks the house rule
  if (o.houseRules) {
    const OVER_FACE = new Set(['lens_flare', 'sparks_burst', 'glass_burst', 'shockwave', 'blood_lens', 'lightning_arc', 'light_rays', 'flashlight', 'spotlight']);
    const mainT = p.tracks.find(t => t.main)?.id;
    const onFace = p.clips.filter(c => {
      if (c.kind !== 'shader' && c.kind !== 'graphic') return false;
      if (c.kind === 'shader' && !(c.preset && OVER_FACE.has(c.preset))) return false;
      const tr = transformAt(c, Math.min(c.dur, 0.2));
      const x = 0.5 + (tr.x ?? 0), y = 0.5 + (tr.y ?? 0);
      if (c.kind === 'graphic' && (c.gw ?? 0.6) > 0.7) return false; // frames and full-width marks
      // only over shots framed on a face (focus set)
      const under = p.clips.find(m => m.track === mainT && m.start <= c.start + 0.05 && m.start + m.dur > c.start + 0.05);
      return !!under?.focus && x > 0.36 && x < 0.64 && y > 0.28 && y < 0.56;
    });
    if (onFace.length) out.push({ id: 'face', label: 'Over the face', status: 'warn', detail: `${onFace.length} overlay${onFace.length > 1 ? 's' : ''} anchored where the face sits (${onFace.map(c => `${c.preset || c.kind} ${f2(c.start)} s`).join(', ')}): move ${onFace.length > 1 ? 'them' : 'it'} off the face (to the light source, the impact point or a corner); the house rule is nothing drawn over his face.`, at: onFace.map(c => c.start) });
  }
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
    // the knockout title (footage in the letters) is the one deliberate mid-frame exception
    if (o.houseRules && (top < 1240 - 40 || bot > 1640 + 40) && !(c.anim?.in === 'letters') && !s.knockout) outBand.push(c.start);
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
  // sound design: punctuation, not a click on every cut
  const ev = sfxEvents(p);
  const hard = trans.filter(c => !QUIET_TRANSITIONS.has(c.transition!.type));
  if (ev.length || hard.length) {
    const stacked = ev.filter((e, i) => i > 0 && e.t - ev[i - 1].t < 0.3).map(e => e.t);
    const thick = ev.filter(e => e.clips.length > 2).map(e => e.t);
    let peak = 0, peakAt = 0;
    for (const e of ev) { const n = ev.filter(x => x.t >= e.t && x.t < e.t + 1).length; if (n > peak) { peak = n; peakAt = e.t; } }
    const budget = sfxBudget(dur);
    const tooMany = ev.length > budget || stacked.length > 0 || thick.length > 0 || peak > 2;
    const none = !ev.length && hard.length > 0;
    out.push({
      id: 'sound', label: 'Sound effects',
      status: tooMany ? 'warn' : none ? (o.houseRules ? 'warn' : 'info') : 'pass',
      detail: none ? `No sound effects yet: the drop wants a riser and an impact, and the hard hits (${hard.length}) a sound where they land.`
        : `${ev.length} sound moments in ${f2(dur)} s (budget ${budget}: punctuation on the drop, set pieces and hard hits, never a sound on every cut)${stacked.length ? `; ${stacked.length} within 0.3 s of another` : ''}${thick.length ? `; ${thick.length} with more than two layers` : ''}${peak > 2 ? `; ${peak} within one second at ${f2(peakAt)} s` : ''}.`,
      at: tooMany ? [...stacked, ...thick, ...(peak > 2 ? [peakAt] : [])].sort((a, b) => a - b) : [],
      action: tooMany ? 'thin-sfx' : none ? 'add-sfx' : undefined,
    });
  }
  // flashes: flash-type transitions and the library's flash effects
  const FLASH_FX = new Set(['exposure_wash', 'impact_frame', 'flash']);
  const flashFx = p.clips.filter(c => c.kind === 'shader' && c.preset && FLASH_FX.has(c.preset));
  const flashes = [...trans.filter(c => FLASHY.has(c.transition!.type)).map(c => c.start), ...flashFx.map(c => c.start)].sort((a, b) => a - b);
  // two flash moves on the same frames add up to a white card (a negative of a dark frame is already white)
  const stackedFlash = flashFx.filter(c => flashFx.some(d => d !== c && d.start < c.start + c.dur && c.start < d.start + d.dur) || trans.some(x => FLASHY.has(x.transition!.type) && Math.abs(x.start - c.start) < Math.max(0.2, (x.transition!.dur || 0.4) / 2)));
  if (stackedFlash.length) out.push({ id: 'flash-stack', label: 'Stacked flashes', status: 'warn', detail: `${stackedFlash.map(c => `${c.preset} ${f2(c.start)} s`).join(', ')} overlap${stackedFlash.length === 1 ? 's' : ''} another flash move: together they blow the hit out to a white card and hide the transition and the title. Keep one flash per hit, its peak readable (the ink style of impact_frame on dark footage).`, at: stackedFlash.map(c => c.start) });
  let worst = 0, worstAt = 0;
  for (let i = 0; i < flashes.length; i++) {
    const n = flashes.filter(t => t >= flashes[i] && t < flashes[i] + 1).length;
    if (n > worst) { worst = n; worstAt = flashes[i]; }
  }
  out.push({ id: 'flash', label: 'Flash rate', status: worst > 3 ? 'fail' : 'pass', detail: worst > 3 ? `${worst} flash-type hits within one second at ${f2(worstAt)} s (limit 3).` : `At most ${worst} flash-type hit${worst === 1 ? '' : 's'} in any second.`, at: worst > 3 ? [worstAt] : [] });
  // the same set-up used again: a montage of a handful of images on rotation
  if (o.houseRules && mainClips.length >= 6) {
    const repeats: number[] = [];
    mainClips.forEach((c, i) => {
      if (!c.media) return;
      const a0 = c.in ?? 0, a1 = a0 + c.dur * (c.speed ?? 1);
      // the same moment shown again later (a scene playing on across consecutive cuts is continuity, not a repeat)
      const twin = mainClips.slice(0, Math.max(0, i - 1)).find(d => d.media === c.media && Math.max(a0, d.in ?? 0) < Math.min(a1, (d.in ?? 0) + d.dur * (d.speed ?? 1)) + 1);
      if (twin) repeats.push(c.start);
    });
    out.push({ id: 'repeats', label: 'Repeated shots', status: repeats.length > 1 ? 'warn' : 'pass', detail: repeats.length ? `${repeats.length} shot${repeats.length > 1 ? 's' : ''} show a moment already shown earlier (the same file, source ranges within 1 s of each other, with other shots between; ${repeats.map(f2).join(', ')} s): one deliberate callback is fine; more reads as a few images on rotation. Find new moments in the shot list. A scene playing on across consecutive cuts is fine.` : 'Every shot is a new moment.', at: repeats });
    // the same family of moves crowded together reads as a template
    const FAMILY: Record<string, string> = { flip_h: 'turn', flip_v: 'turn', roll: 'turn', spin: 'turn', cube_left: 'turn', cube_right: 'turn', cube_up: 'turn', cube_down: 'turn', whip_left: 'whip', whip_right: 'whip', whip_up: 'whip', whip_down: 'whip', slide_left: 'slide', slide_right: 'slide', push_left: 'slide', push_right: 'slide' };
    const fam = trans.filter(c => FAMILY[c.transition!.type]).sort((a, b) => a.start - b.start);
    const crowd = fam.filter(c => fam.filter(d => FAMILY[d.transition!.type] === FAMILY[c.transition!.type] && d.start >= c.start && d.start < c.start + 5).length >= 3).map(c => c.start);
    if (crowd.length) out.push({ id: 'family', label: 'Move families', status: 'warn', detail: `Three or more ${[...new Set(fam.filter(c => crowd.includes(c.start)).map(c => FAMILY[c.transition!.type]))].join('/')} moves within 5 s from ${crowd.map(f2).join(', ')} s: vary them (a slash, a burn, a dive, a light sweep).`, at: crowd });
  }
  // the loop in sound: the song runs to the last frame (a tape stop or a dead stop on the bar is fine; a fade is not)
  if (o.houseRules) {
    const bed = p.clips.filter(c => c.kind === 'audio' && c.media && media[c.media]?.analysis).sort((a, b) => b.dur - a.dur)[0];
    if (bed) {
      const endsAtEnd = Math.abs(clipEnd(bed) - dur) < 0.1;
      const stop = p.clips.some(c => c.kind === 'sfx' && c.sfx === 'tapestop' && c.start > dur - 1.5);
      const fades = (bed.fadeOut ?? 0) > 0.05 && endsAtEnd && !stop;
      const short = clipEnd(bed) < dur - 0.1;
      if (fades || short) out.push({ id: 'loop-sound', label: 'Loop in sound', status: 'warn', detail: fades ? `The music fades out over its last ${f2(bed.fadeOut!)} s and comes back at full level on the wrap: let it run to the last frame (fadeOut 0), or end on a tape stop or a dead stop on the bar.` : `The music ends at ${f2(clipEnd(bed))} s, before the edit does (${f2(dur)} s): the loop drops out of the song.`, at: [Math.max(0, dur - 0.5)] });
    }
  }
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
  const seamM = o.seam === undefined || o.seam === null ? null : typeof o.seam === 'number' ? { seam: o.seam, step: 0 } : o.seam;
  if (seamM) {
    // the wrap is invisible when its jump is no bigger than a normal frame step here (grain and moving
    // layers change every frame anyway)
    const ok = seamM.seam <= 1 || seamM.seam <= seamM.step * 1.5 + 0.3;
    // say why when it can: the shots on both sides of the wrap and the source times they show
    let why = '';
    const first = mainClips[0], last = mainClips[mainClips.length - 1];
    if (first && last) {
      const srcEnd = (last.in ?? 0) + last.dur * (last.speed ?? 1), src0 = first.in ?? 0;
      why = first.media && first.media === last.media
        ? ` The last shot ends on source ${f2(srcEnd)} s of the same file frame 0 shows at ${f2(src0)} s${Math.abs(srcEnd - src0) > 0.05 ? ' (a different frame)' : ''}${JSON.stringify([first.focus, first.transform?.scale ?? 1, first.color]) !== JSON.stringify([last.focus, last.transform?.scale ?? 1, last.color]) ? '; its focus, scale or colour differ from the first shot' : ''}: {"op":"loop"} lands it exactly, then keep the layers over the last frames the same as over frame 0.`
        : ` Frame 0 is ${first.media || 'a'} at ${f2(src0)} s and the last frame is ${last.media || 'another shot'}: {"op":"loop"} dissolves a twin of the first shot in over the last frames; keep the layers there the same as over frame 0.`;
    }
    out.push({ id: 'loop', label: 'Loop seam', status: ok ? 'pass' : seamM.seam <= 8 ? 'warn' : 'fail', detail: `Last frame vs frame 0 differ by ${seamM.seam.toFixed(1)}${seamM.step ? `; a normal frame step here is ${seamM.step.toFixed(1)}` : ''} (blurred mean difference; the wrap is invisible at 1 or less, or when it is no bigger than one and a half normal steps): ${ok ? 'the loop is seamless.' : `the wrap jumps.${why}`}` });
  }
  else if (o.houseRules) out.push({ id: 'loop', label: 'Loop seam', status: 'info', detail: 'Measured when Opus reviews, or press Measure.' });
  out.push({ id: 'eyes', label: 'Needs eyes', status: 'info', detail: 'Faces centred and uncut, set-piece quality and anything that looks drawn are checked by the review on rendered frames.' });
  return out;
}

export function checksText(checks: Check[]): string {
  return checks.filter(c => c.status !== 'pass').map(c => `- [${c.status.toUpperCase()}] ${c.label}: ${c.detail}${c.at?.length ? ` (at ${c.at.slice(0, 12).map(t => t.toFixed(2)).join(', ')} s)` : ''}`).join('\n') || '- Every automated gate passes.';
}

export function transitionName(c: Clip) { return c.transition ? TRANSITION_LABELS[c.transition.type] : ''; }
