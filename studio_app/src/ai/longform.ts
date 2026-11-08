// Long form: 5-30 minute videos (talks, commentary, video essays, tutorials), edited the calm way. One
// Opus call reads the transcript and plans the edit (chapters, breakdown panels for the complicated
// parts, key-term callouts, a few emphasis zooms, the pauses to trim); the studio then builds it from
// tested templates, so every graphic is polished and the timeline stays uncluttered.
import { applyOps, normalize } from '../state/ops';
import { Job, JobStep, MediaInfo, Project } from '../state/types';
import { parseTranscript, Transcript, transcriptText } from '../state/transcript';
import { runChecks } from '../engine/qc';
import { askSafe, errText, finishRound, JobIO, readMedia } from './director';
import { parseJson } from './prompt';
import { mediaSheets } from './sheets';
import type { Workspace } from './workspace';
import { addTaste, tasteText } from '../state/catalog';

export interface LongformOptions { captions: boolean; chapters: boolean; breakdowns: boolean; zooms: boolean; trim: boolean; pace: 'calm' | 'lively'; accent: string }
export interface LongformRequest { notes: string; transcript: string; options: LongformOptions }
export const DEFAULT_LONGFORM: LongformOptions = { captions: false, chapters: true, breakdowns: true, zooms: true, trim: true, pace: 'calm', accent: '#7fd3ff' };

export function longformSteps(hasFiles: boolean): JobStep[] {
  return [
    ...(hasFiles ? [{ id: 'files', label: 'Store your video', state: 'wait' as const }] : []),
    { id: 'media', label: 'Read the video and its sound', state: 'wait' },
    { id: 'read', label: 'Read the transcript and sample the picture', state: 'wait' },
    { id: 'plan', label: 'Opus plans chapters, breakdowns, callouts and trims', state: 'wait' },
    { id: 'build', label: 'Build the edit from the studio templates', state: 'wait' },
  ];
}

/** How the owner wants long-form edited: Opus's training for this mode. */
export const LONGFORM_PLAYBOOK = `LONG-FORM EDITING (5-30 minute videos: talks, commentary, essays, tutorials, podcasts)
The goal is clarity and retention, edited calmly. This is not a TikTok edit: no beat cuts, no flashes, no stacked effects, no transition on every cut. The viewer should feel the video got tighter and easier to follow, not busier.
- TRIM: remove dead air (pauses over about 0.6 s), false starts and repeated takes (the same sentence started again: keep the last, complete take), and long "um" stretches you can see in the transcript. Never cut inside a sentence. Keep the first 30 seconds especially tight: it is the hook.
- CHAPTERS: one at each real change of topic, usually every 2-5 minutes, plus one at the start that names the video's subject. Titles of 2-5 words, plain and specific ("How the engine works", not "Part 2").
- BREAKDOWNS: an animated panel beside the speaker for the parts that are hard to follow by ear: a definition, a process in steps, a comparison, a list, numbers. A short title and 2-4 points of at most 8 words each, in the order the speaker says them, starting when they start explaining and held for the explanation (8-20 s). At most one every 60-90 s; never two at once; skip them where the speaker is telling a story.
- CALLOUTS: a key term, name or number popping in as a small label, 1-4 words, when it is first said; at most one every 30-45 s, never during a breakdown.
- EMPHASIS ZOOMS: a slow push-in (1.08-1.15) on a punchline, a key claim or an emotional beat, 3-6 s, every 45-120 s; they are the pattern interrupts that keep attention. The studio already alternates a subtle punch-in on jump cuts.
- THE OWNER'S COMMENTS decide: features they ask for are added; features they say to drop are not used at all.
- Everything you place must be supported by the transcript: never invent facts, numbers or quotes for a breakdown; use the speaker's own points in short form.`;

interface Plan {
  message: string;
  title?: string;
  chapters: { t: number; title: string }[];
  breakdowns: { start: number; dur: number; title: string; points: string[] }[];
  callouts: { t: number; text: string }[];
  zooms: { t: number; dur: number; zoom: number }[];
  remove: { from: number; to: number }[];
}

const num = (v: any, d = 0) => (Number.isFinite(+v) ? +v : d);
const clampN = (v: number, a: number, b: number) => Math.max(a, Math.min(b, v));
const r3 = (v: number) => Math.round(v * 1000) / 1000;
const esc = (s: string) => s.replace(/[<>&"]/g, '');

/** Pauses in the speech (from the loudness envelope): candidates for a trim. */
export function speechPauses(m: MediaInfo, minGap = 0.7): { from: number; to: number }[] {
  const a = m.analysis;
  if (!a?.energy?.length) return [];
  const e = a.energy, rate = a.energyRate;
  const sorted = [...e].sort((x, y) => x - y);
  const med = sorted[Math.floor(sorted.length / 2)] || 0;
  const th = Math.max(0.02, med * 0.22);
  const out: { from: number; to: number }[] = [];
  let s = -1;
  for (let i = 0; i <= e.length; i++) {
    const quiet = i < e.length && e[i] < th;
    if (quiet && s < 0) s = i;
    if (!quiet && s >= 0) {
      const from = s / rate, to = i / rate;
      if (to - from >= minGap) out.push({ from: r3(from + 0.18), to: r3(to - 0.18) });
      s = -1;
    }
  }
  return out;
}

function parsePlan(text: string, dur: number): Plan | null {
  const v: any = parseJson(text);
  if (!v || typeof v !== 'object') return null;
  const arr = (x: any) => (Array.isArray(x) ? x : []);
  return {
    message: String(v.message || ''),
    title: typeof v.title === 'string' ? v.title : undefined,
    chapters: arr(v.chapters).map((c: any) => ({ t: clampN(num(c?.t), 0, dur), title: String(c?.title || '').slice(0, 48) })).filter((c: any) => c.title).sort((a: any, b: any) => a.t - b.t).slice(0, 24),
    breakdowns: arr(v.breakdowns).map((b: any) => ({ start: clampN(num(b?.start), 0, dur), dur: clampN(num(b?.dur, 12), 4, 30), title: String(b?.title || '').slice(0, 48), points: arr(b?.points).map((p: any) => String(p).slice(0, 70)).filter(Boolean).slice(0, 4) })).filter((b: any) => b.title && b.points.length).sort((a: any, b: any) => a.start - b.start).slice(0, 40),
    callouts: arr(v.callouts).map((c: any) => ({ t: clampN(num(c?.t), 0, dur), text: String(c?.text || '').slice(0, 32) })).filter((c: any) => c.text).slice(0, 60),
    zooms: arr(v.zooms).map((z: any) => ({ t: clampN(num(z?.t), 0, dur), dur: clampN(num(z?.dur, 4), 2, 8), zoom: clampN(num(z?.zoom, 1.1), 1.03, 1.2) })).slice(0, 60),
    remove: arr(v.remove).map((r: any) => ({ from: clampN(num(r?.from), 0, dur), to: clampN(num(r?.to), 0, dur) })).filter((r: any) => r.to - r.from >= 0.15).slice(0, 600),
  };
}

/** Source time ranges kept after the trims (merged, sorted). */
function keptRanges(dur: number, remove: { from: number; to: number }[]): [number, number][] {
  const rm = [...remove].sort((a, b) => a.from - b.from);
  const out: [number, number][] = [];
  let cur = 0;
  for (const r of rm) {
    if (r.from > cur + 0.3) out.push([cur, r.from]);
    cur = Math.max(cur, r.to);
  }
  if (dur > cur + 0.3) out.push([cur, dur]);
  return out;
}

// ---------- the templates ----------

function chapterSvg(accent: string) {
  return `<svg viewBox='0 0 1000 220'><defs><linearGradient id='g' x1='0' x2='1'><stop offset='0' stop-color='#0a0b11' stop-opacity='0.88'/><stop offset='1' stop-color='#0a0b11' stop-opacity='0.62'/></linearGradient><linearGradient id='a' x1='0' x2='1'><stop offset='0' stop-color='${accent}'/><stop offset='1' stop-color='${accent}' stop-opacity='0'/></linearGradient></defs><rect width='1000' height='220' rx='30' fill='url(#g)'/><rect x='1' y='1' width='998' height='218' rx='29' fill='none' stroke='#ffffff' stroke-opacity='0.13' stroke-width='2'/><rect x='220' y='176' width='560' height='6' rx='3' fill='url(#a)'/></svg>`;
}

function panelSvg(accent: string, h: number) {
  return `<svg viewBox='0 0 700 ${h}'><defs><linearGradient id='g' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#11131c' stop-opacity='0.9'/><stop offset='1' stop-color='#07080c' stop-opacity='0.82'/></linearGradient><linearGradient id='a' x1='0' x2='1'><stop offset='0' stop-color='${accent}'/><stop offset='1' stop-color='${accent}' stop-opacity='0.15'/></linearGradient></defs><rect width='700' height='${h}' rx='34' fill='url(#g)'/><rect x='1' y='1' width='698' height='${h - 2}' rx='33' fill='none' stroke='#ffffff' stroke-opacity='0.12' stroke-width='2'/><rect x='0' y='0' width='700' height='8' rx='4' fill='url(#a)'/><rect x='290' y='108' width='120' height='5' rx='2.5' fill='${accent}'/></svg>`;
}

/** The operations for the planned edit: trimmed segments, chapter cards, breakdown panels, callouts, zooms, captions. */
export function longformOps(p: Project, m: MediaInfo, plan: Plan, t: Transcript, o: LongformOptions): unknown[] {
  const dur = m.duration;
  const portrait = p.height > p.width;
  const ranges = o.trim ? keptRanges(dur, plan.remove) : [[0, dur] as [number, number]];
  // source time -> timeline time
  const starts: number[] = [];
  let acc = 0;
  for (const [a, b] of ranges) { starts.push(acc); acc += b - a; }
  const toTl = (s: number) => {
    for (let i = 0; i < ranges.length; i++) {
      const [a, b] = ranges[i];
      if (s < a) return starts[i];
      if (s <= b) return starts[i] + (s - a);
    }
    return acc;
  };
  const ops: any[] = [{ op: 'clear' }];
  const zoomAt = (tl: number) => plan.zooms.find(z => { const zt = toTl(z.t); return tl >= zt && tl < zt + z.dur; });
  ranges.forEach(([a, b], i) => {
    const clip: any = { op: 'add', id: `seg${i + 1}`, media: m.id, in: r3(a), dur: r3(b - a) };
    // a subtle punch-in on every other jump cut hides the cut
    const base = o.zooms && o.trim && i % 2 === 1 ? 1.06 : 1;
    if (base !== 1) clip.transform = { scale: base };
    if (o.zooms) {
      const z = plan.zooms.find(z0 => z0.t >= a && z0.t < b);
      if (z) {
        const lt = z.t - a, end = Math.min(b - a, lt + z.dur);
        clip.kf = { scale: [{ t: r3(lt), v: base, e: 'inOut' }, { t: r3(Math.min(end, lt + 0.9)), v: r3(base * z.zoom) }, { t: r3(Math.max(lt + 0.9, end - 0.9)), v: r3(base * z.zoom), e: 'inOut' }, { t: r3(end), v: base }] };
      }
    }
    ops.push(clip);
  });
  void zoomAt;
  const total = acc;
  const W = p.width, H = p.height;
  const acc1 = o.accent || '#7fd3ff';
  // chapter cards
  if (o.chapters) plan.chapters.forEach((c, k) => {
    const t0 = Math.max(0.4, toTl(c.t) + 0.3);
    if (t0 > total - 3) return;
    const gw = portrait ? 0.86 : 0.46;
    const ph = (gw * W * 0.22) / H;
    const y = portrait ? 0.18 : 0.26;
    ops.push({ op: 'graphic', start: r3(t0), dur: 3.4, gw, svg: chapterSvg(acc1), transform: { x: 0, y }, reveal: { in: 'wipe', out: 'fade', inDur: 0.45, outDur: 0.35 } });
    ops.push({ op: 'text', start: r3(t0 + 0.2), dur: 3.0, text: `CHAPTER ${String(k + 1).padStart(2, '0')}`, style: { font: 'Inter', weight: 700, size: portrait ? 0.016 : 0.022, color: acc1, uppercase: true, tracking: 0.32, shadow: 0, stroke: 0 }, anim: { in: 'rise', out: 'fade', inDur: 0.4, outDur: 0.3 }, transform: { y: r3(y - ph * 0.27) } });
    ops.push({ op: 'text', start: r3(t0 + 0.35), dur: 2.85, text: esc(c.title), style: { font: 'Inter', weight: 800, size: portrait ? 0.03 : 0.048, color: '#f4f6fa', shadow: 0.4, stroke: 0, maxWidth: gw * 0.86, fit: true }, anim: { in: 'blur', out: 'fade', inDur: 0.5, outDur: 0.3 }, transform: { y: r3(y + ph * 0.08) } });
    ops.push({ op: 'sfx', sound: 'swish', start: r3(t0), volume: 0.16 });
    // a calm join where a chapter starts on a cut
    const seg = ranges.findIndex(([a]) => Math.abs(toTl(a) - toTl(c.t)) < 0.6);
    if (seg > 0) ops.push({ op: 'set', id: `seg${seg + 1}`, transition: { type: 'crossfade', dur: 0.3 } });
  });
  // breakdown panels beside the speaker
  const busy: [number, number][] = [];
  const cards = o.chapters ? plan.chapters.map(c => Math.max(0.4, toTl(c.t) + 0.3)) : [];
  if (o.breakdowns) plan.breakdowns.forEach(b => {
    // a breakdown waits for a chapter card on screen to finish
    let t0 = toTl(b.start);
    const card = cards.find(c => t0 >= c - 0.2 && t0 < c + 3.4);
    let d0 = b.dur;
    if (card !== undefined) { d0 = Math.max(6, d0 - (card + 3.5 - t0)); t0 = card + 3.5; }
    const d = Math.min(d0, total - t0 - 0.2);
    if (d < 3 || busy.some(([x, y]) => t0 < y && t0 + d > x)) return;
    busy.push([t0, t0 + d]);
    const n = b.points.length;
    const vbH = 150 + n * 58 + 46;
    const gw = portrait ? 0.84 : 0.38;
    const ph = (gw * W * (vbH / 700)) / H;
    const x = portrait ? 0 : 0.27, yc = portrait ? -0.18 : 0;
    const top = yc - ph / 2;
    const ts = portrait ? 0.024 : 0.04, ps = portrait ? 0.019 : 0.03;
    ops.push({ op: 'graphic', start: r3(t0), dur: r3(d), gw, svg: panelSvg(acc1, vbH), transform: { x, y: yc }, reveal: { in: 'wipe', out: 'fade', inDur: 0.5, outDur: 0.4 } });
    ops.push({ op: 'text', start: r3(t0 + 0.25), dur: r3(d - 0.25), text: esc(b.title), style: { font: 'Inter', weight: 800, size: ts, color: '#ffffff', shadow: 0, stroke: 0, maxWidth: gw * 0.84, fit: true }, anim: { in: 'rise', out: 'fade', inDur: 0.45, outDur: 0.35 }, transform: { x: r3(x), y: r3(top + ph * (66 / vbH)) } });
    const lines = b.points.map(pt => `— ${esc(pt)}`);
    const step = Math.min(2.2, Math.max(0.7, (d - 2) / n));
    const words: number[] = [];
    lines.forEach((l, k) => l.split(/\s+/).filter(Boolean).forEach((_, j) => words.push(r3(0.3 + k * step + j * 0.04))));
    ops.push({ op: 'text', start: r3(t0 + 0.6), dur: r3(d - 0.6), text: lines.join('\n'), words, style: { font: 'Inter', weight: 600, size: ps, color: '#dfe4ee', align: 'left', lineHeight: 1.6, shadow: 0, stroke: 0, maxWidth: gw * 0.86, emphColor: acc1 }, anim: { in: 'words', out: 'fade', inDur: 0.35, outDur: 0.35 }, transform: { x: r3(x), y: r3(top + ph * ((146 + n * 29) / vbH)) } });
    ops.push({ op: 'sfx', sound: 'swish', start: r3(t0), volume: 0.14 });
  });
  // key-term callouts
  plan.callouts.forEach(c => {
    const t0 = toTl(c.t);
    if (t0 > total - 2.5 || busy.some(([x, y]) => t0 < y + 0.5 && t0 + 2.4 > x)) return;
    ops.push({ op: 'text', start: r3(t0), dur: 2.4, text: esc(c.text), style: { font: 'Inter', weight: 800, size: portrait ? 0.022 : 0.03, color: '#0a0b11', bg: true, bgColor: acc1, uppercase: true, tracking: 0.06, shadow: 0, stroke: 0 }, anim: { in: 'pop', out: 'fade', inDur: 0.3, outDur: 0.25 }, transform: { x: portrait ? 0 : -0.3, y: portrait ? 0.24 : 0.3 } });
  });
  // captions from the transcript
  if (o.captions && t.timed) for (const s of t.segments) {
    const a = toTl(s.t), b = toTl(s.end ?? s.t + 3);
    if (b - a < 0.3) continue;
    ops.push({ op: 'text', start: r3(a), dur: r3(Math.min(6, b - a)), text: esc(s.text).slice(0, 120), style: { font: 'Inter', weight: 700, size: portrait ? 0.026 : 0.036, color: '#ffffff', stroke: 0.08, strokeColor: '#000000', shadow: 0.7, maxWidth: portrait ? 0.86 : 0.72 }, anim: { in: 'fade', out: 'fade', inDur: 0.1, outDur: 0.1 }, transform: { y: portrait ? 0.32 : 0.41 } });
  }
  return ops;
}

/** The long-form job: read, plan in one call, build from templates. */
export async function longformEdit(job: Job, ws: Workspace, io: JobIO): Promise<{ summary: string }> {
  const req = job.longform!;
  const o = { ...DEFAULT_LONGFORM, ...(req.options || {}) };
  let model: string | undefined;
  const io2: JobIO = { ...io, model: m => { model = m; io.model(m); } };
  void addTaste(req.notes, ws.rec.name, 'create');
  await readMedia(ws, io);
  const vids = ws.ready().filter(m => m.kind === 'video' && m.hasVideo).sort((a, b) => b.duration - a.duration);
  const m = vids[0];
  if (!m) throw { code: 'no_media' };
  // the project takes the video's shape: 16:9 at 1920x1080 (or 9:16), 30 fps
  const portrait = (m.height || 9) > (m.width || 16);
  ws.setProject({ ...ws.project, width: portrait ? 1080 : 1920, height: portrait ? 1920 : 1080, fps: Math.min(60, Math.max(24, Math.round(m.fps || 30))) });

  io.step('read', { state: 'run', detail: 'transcript' });
  const t = parseTranscript(req.transcript || '');
  const pauses = speechPauses(m);
  const images = await mediaSheets(ws.ctx, 2, 24, io.signal).catch(() => []);
  io.step('read', { state: 'done', detail: `${t.segments.length ? `${t.words} words${t.timed ? ', timed' : ', no times'}` : 'no transcript'} · ${pauses.length} pauses · ${images.length} sheets` });

  io.step('plan', { state: 'run', detail: 'thinking…' });
  const mins = m.duration / 60;
  const prompt = [
    'You are the editor inside VOIDFX Studio, planning a long-form edit. You cannot hear the video: the transcript and the measured pauses are how you know what is said and when; the images are frames sampled across the video.',
    LONGFORM_PLAYBOOK,
    tasteText(2500) ? `THE OWNER'S NOTES ON RECENT EDITS (their taste)\n${tasteText(2500)}` : '',
    `THE VIDEO: ${m.name}, ${mins.toFixed(1)} minutes (${m.duration.toFixed(1)} s), ${m.width}x${m.height}. Pace asked for: ${o.pace}${o.pace === 'calm' ? ' (fewer zooms and callouts, longer holds)' : ' (more pattern interrupts: zooms about every 45 s, more callouts)'}.`,
    `FEATURES THE OWNER TURNED ON: ${[o.chapters && 'chapter cards', o.breakdowns && 'breakdown panels', o.zooms && 'emphasis zooms', o.trim && 'trimming pauses and false starts', o.captions && 'captions'].filter(Boolean).join(', ') || 'none'}. Write nothing for a feature that is off.`,
    req.notes.trim() ? `THE OWNER'S COMMENTS (features to add or remove, and anything else; these decide)\n${req.notes.trim()}` : '',
    o.trim && pauses.length ? `MEASURED PAUSES IN THE SPEECH (source seconds, from the sound; trim the ones that are dead air, keep a beat where a pause lands a point)\n${pauses.slice(0, 500).map(x => `${x.from.toFixed(2)}-${x.to.toFixed(2)}`).join(', ')}` : '',
    t.segments.length ? `TRANSCRIPT${t.timed ? ' (source seconds)' : ' (no times: place things by the order of what is said, spread across the video)'}\n${transcriptText(t)}` : 'NO TRANSCRIPT: you cannot know what is said. Plan only trims of measured pauses, a single opening chapter card named after the video, and two or three emphasis zooms; say in "message" that a transcript (SRT or VTT) unlocks chapters, breakdowns and callouts.',
    images.length ? `IMAGES: ${images.map((s, i) => `${i + 1}. ${s.caption}`).join('; ')}` : '',
    `Reply with only JSON, compact (all times in SOURCE seconds):
{"message": "what the edit does, for the owner, in two or three sentences", "title": "the video's subject in 2-5 words",
 "chapters": [{"t": 0, "title": "2-5 words"}],
 "breakdowns": [{"start": 120.5, "dur": 12, "title": "short title", "points": ["at most 8 words", "..."]}],
 "callouts": [{"t": 45.2, "text": "1-4 words"}],
 "zooms": [{"t": 300.1, "dur": 4, "zoom": 1.1}],
 "remove": [{"from": 12.3, "to": 13.4}]}`,
  ].filter(Boolean).join('\n\n');
  const r = await askSafe(io2, prompt, images, job.effort === 'low' ? 'medium' : job.effort === 'extra' ? 'high' : job.effort, 'plan', txt => {
    const n = (txt.match(/"(t|start|from)"\s*:/g) || []).length;
    return n ? `planning… ${n} moments so far` : 'thinking…';
  });
  const plan = parsePlan(r.text, m.duration);
  if (!plan) throw { code: 'invalid_json' };
  io.step('plan', { state: 'done', detail: `${plan.chapters.length} chapters · ${plan.breakdowns.length} breakdowns · ${plan.callouts.length} callouts · ${plan.zooms.length} zooms · ${plan.remove.length} trims` });

  io.step('build', { state: 'run' });
  const res = applyOps(ws.project, longformOps(ws.project, m, plan, t, o), ws.media());
  normalize(res.project, ws.media());
  ws.setProject({ ...res.project, name: ws.project.name });
  await ws.save();
  const checks = runChecks(ws.project, ws.media(), { houseRules: false });
  const cut = m.duration - ws.project.clips.filter(c => c.media === m.id).reduce((a, c) => a + c.dur, 0);
  io.step('build', { state: 'done', detail: `${res.applied} operations · ${cut > 1 ? `${(cut / 60 >= 1 ? `${(cut / 60).toFixed(1)} min` : `${cut.toFixed(0)} s`)} trimmed` : 'nothing trimmed'}${res.issues.length ? ` · ${res.issues.length} adjusted` : ''}` });
  void checks;
  const summary = plan.message || 'The long-form edit is on the timeline.';
  await finishRound(ws, job, { summary, applied: res.applied, model, notes: [] }, [{ role: 'user', content: 'long-form plan' }, { role: 'user', content: prompt.slice(0, 3000) }, { role: 'assistant', content: r.text.slice(0, 8000) }]).catch(e => console.warn(errText(e)));
  return { summary };
}
