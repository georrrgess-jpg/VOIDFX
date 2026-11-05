// The Opus Director: builds an edit (round 1) or revises it (later rounds) through the `sample`
// capability. It runs inside a background job on the job's own workspace, so the owner can leave
// the editor, open other projects or queue more edits while it works.
// Build: preset + notes + standards → (cast from the database) → read the media → contact sheets →
// Opus plans operations → the studio applies, validates and adds missing sounds → checkpoint →
// rendered frames → Opus review pass(es).
import { BENCHMARK_TEXT, HOUSE_RULES } from './knowledge';
import { checksText, runChecks, Check } from '../engine/qc';
import { cutTimes } from '../engine/evaluate';
import { measureLoopSeam } from '../engine/exporter';
import { attachLibraryItem, whenMediaIdle } from '../media/library';
import { getPreset, LibraryItem, listLibrary, listStandards, Preset, Standard, standardsFor } from '../state/catalog';
import { addTransitionSounds, applyOps, normalize, OpsResult } from '../state/ops';
import { store } from '../state/store';
import { ASPECTS, Effort, Job, JobStep, MediaInfo, Project, Round } from '../state/types';
import { deepClone, projectDuration } from '../state/util';
import { ContextExtras, contextBlock, parseJson, parseReply } from './prompt';
import { libraryMosaic, mediaSheets, Sheet, standardSheets, timelineSheets } from './sheets';
import type { Workspace } from './workspace';

export const MODEL = 'claude-opus-5-5';

type SampleFn = ((input: any, opts?: any) => Promise<{ text: string; truncated: boolean; modelTierApplied: string; modelApplied?: string }>) & {
  limits(): Promise<{ maxPromptBytes: number; images?: { maxCount: number; maxInputBytes: number; mediaTypes: string[] } }>;
};

let sample: SampleFn | null = null;

export const EFFORTS: Record<Effort, { label: string; effort: 'low' | 'medium' | 'high'; reviews: number; images: number; cells: number; hint: string }> = {
  low: { label: 'Low', effort: 'low', reviews: 0, images: 4, cells: 12, hint: 'Fastest. One planning pass with light thinking.' },
  medium: { label: 'Medium', effort: 'medium', reviews: 0, images: 8, cells: 16, hint: 'One planning pass with more thinking.' },
  high: { label: 'High', effort: 'high', reviews: 1, images: 12, cells: 16, hint: 'Deep thinking, then Opus reviews rendered frames of its edit and the checkpoint once.' },
  extra: { label: 'Extra', effort: 'high', reviews: 2, images: 16, cells: 20, hint: 'Deepest: the most footage per call and two review passes on rendered frames and the checkpoint.' },
};

export const ERR: Record<string, string> = {
  not_granted: 'Opus is not allowed to run here. Allow Claude for this artifact when asked, then try again.',
  sampling_disabled: 'Claude is not available on this account right now.',
  not_declared: 'This page is not set up to use Claude.',
  capability_disabled: 'Claude is turned off in this view.',
  capability_removed: 'This viewer app is out of date. Reload or update it.',
  session_expired: 'Sign in to Claude again, then retry.',
  rate_limited: 'Too many requests or your usage limit was reached. Wait a little, then retry.',
  refused: 'Opus declined this request. Try rewording it.',
  empty_completion: 'Opus thought for too long and wrote nothing, even on a lighter retry. Press Retry, or use a lower effort for this edit.',
  invalid_json: 'Opus replied in a shape the studio could not read. Retry.',
  prompt_too_large: 'The request was too large. Use fewer database items or shorten the knowledge text.',
  image_rejected: 'A contact sheet was rejected. Try again with fewer files.',
  images_unavailable: 'Images cannot be sent in this view, so Opus worked from the analysis only.',
  upstream_error: 'Could not reach Opus. Check your connection and retry.',
  no_media: 'Add files or database material first. Opus builds the edit from them.',
  no_project: 'The project was deleted.',
  no_edit: 'There is no edit on this project yet. Build one first.',
};
export const HIDE = new Set(['not_granted', 'sampling_disabled', 'not_declared', 'capability_disabled', 'capability_removed']);

export async function initDirector() {
  try {
    const w = window as any;
    sample = w.claude?.use ? await w.claude.use('sample') : null;
  } catch {
    sample = null;
  }
  if (!sample) {
    store.setDirector({ available: 'no', unavailableReason: 'Opus is available when this studio is opened on claude.ai.' });
    return;
  }
  const lim = await sample.limits().catch(() => null);
  store.setDirector({ available: 'yes', images: !!lim?.images, maxImages: lim?.images?.maxCount ?? 0 });
}

export function directorReady() { return !!sample; }

export function errText(e: any): { code: string; text: string } {
  const code = e?.code || (e?.name === 'AbortError' ? 'cancelled' : 'upstream_error');
  return { code, text: ERR[code] || e?.message || ERR.upstream_error };
}

/** What a job hands the Director: step reporting, cancellation and streaming progress. */
export interface JobIO {
  step(id: string, patch: Partial<JobStep>): void;
  signal: AbortSignal;
  stream(chars: number): void;
  model(m: string): void;
}

export type Turn = { role: 'user' | 'assistant'; content: string };

export async function ask(io: JobIO, input: string | Turn[], images: Sheet[], effort: Effort, label: string, describe?: (text: string) => string): Promise<{ text: string; model: string; truncated: boolean }> {
  if (!sample) throw { code: 'not_declared' };
  const e = EFFORTS[effort];
  const opts: any = {
    model: MODEL, modelTier: 'complex', effort: e.effort, cache: false, signal: io.signal,
    onText: ({ text }: { text: string }) => {
      io.stream(text.length);
      if (describe) { io.step(label, { detail: describe(text) }); return; }
      const ops = (text.match(/"op"\s*:/g) || []).length;
      io.step(label, { detail: ops ? `writing… ${ops} operations so far` : 'writing…' });
    },
  };
  if (images.length && store.state.director.images) opts.images = images.map(s => s.blob);
  const res = await sample(input, opts);
  const model = res.modelApplied || `${res.modelTierApplied} tier`;
  io.model(model);
  store.setDirector({ lastModel: model });
  return { text: res.text, model, truncated: res.truncated };
}

const LIGHTER: Record<Effort, Effort> = { extra: 'medium', high: 'medium', medium: 'low', low: 'low' };
const ANSWER_NOW = '\n\n(Answer now: keep your thinking short and write the reply as compact JSON, no extra whitespace.)';

/**
 * `ask`, with one lighter second attempt when Opus writes nothing (it ran out of time thinking) or the
 * connection drops: less effort, half the images, and a request to answer straight away. Never more
 * than one retry; anything else is thrown as it came.
 */
export async function askSafe(io: JobIO, input: string | Turn[], images: Sheet[], effort: Effort, label: string, describe?: (text: string) => string) {
  try {
    return await ask(io, input, images, effort, label, describe);
  } catch (e: any) {
    const code = e?.code;
    if ((code !== 'empty_completion' && code !== 'upstream_error') || io.signal.aborted) throw e;
    const empty = code === 'empty_completion';
    io.step(label, { detail: empty ? 'Opus ran out of time thinking; asking again, lighter' : 'the connection dropped; asking again' });
    const next = typeof input === 'string'
      ? input + (empty ? ANSWER_NOW : '')
      : [...input.slice(0, -1), { role: 'user' as const, content: input[input.length - 1].content + (empty ? ANSWER_NOW : '') }];
    return await ask(io, next, empty ? images.slice(0, Math.ceil(images.length / 2)) : images, empty ? LIGHTER[effort] : effort, label, describe);
  }
}

/** High and Extra split a pass in two calls: decide (with the images), then write the operations. */
export const twoStage = (effort: Effort) => effort === 'high' || effort === 'extra';

/**
 * Two calls instead of one long one, so neither runs out of time: Opus directs the pass (decisions
 * only, short text, with the images), then writes the operations for exactly that direction (lighter
 * thinking, no images). Returns the operations, Opus's message to the owner and the turns so far.
 */
async function directThenBuild(io: JobIO, o: { ctx: string; ctxNoImages: string; history: Turn[]; request: string; images: Sheet[]; effort: Effort; revision: boolean }) {
  const step1 = o.revision
    ? 'STEP 1 OF 2: DECIDE THE CHANGES. Do not write operations yet. For every instruction and critic point, write down exactly what you will change: the time, the clip, the new shot or value, the transition and its sound, the text. Add anything else the edit needs to clear the standards. Be compact.'
    : 'STEP 1 OF 2: DIRECT THE EDIT. Do not write operations yet. Decide everything and write it down compactly: CONCEPT (one sentence); SONG (media id, source in and out, where the drop or hook lands on the timeline); STRUCTURE (sections with timeline times); SHOTS in order ("t0-t1 media id, shot number, source in -> what it shows, framing, speed or ramp"); TRANSITIONS ("time, type, why, its sound"); SET PIECES (each step by step); TEXT ("t0-t1 words, animation in and out, style"); CAMERA; SOUNDS; LOOP.';
  const t1: Turn[] = [{ role: 'user', content: o.ctx }, ...o.history, { role: 'user', content: `${o.request}

${step1}
Reply with only JSON: {"message": "${o.revision ? 'what will change, for the owner' : 'the concept sentence and the set pieces, for the owner'}", "direction": "the full plan as compact text"}` }];
  io.step('direct', { state: 'run', detail: 'thinking…' });
  const a = await askSafe(io, t1, o.images, o.effort, 'direct', t => `writing the direction… ${t.length} characters`);
  const av: any = parseJson(a.text);
  const direction = typeof av?.direction === 'string' && av.direction.trim() ? av.direction : a.text;
  const note = typeof av?.message === 'string' ? av.message : '';
  io.step('direct', { state: 'done', detail: `${direction.length} characters${a.truncated ? ' (cut short)' : ''}` });

  const step2 = o.revision
    ? 'STEP 2 OF 2: Write the operations for exactly the changes you decided, against the CURRENT TIMELINE. Keep everything else. Reply with only JSON: {"message": "what you changed", "ops": [...]}.'
    : 'STEP 2 OF 2: BUILD IT. Turn your direction into operations exactly, in the studio\'s operation format. Start with {"op":"clear"}. Reply with only JSON: {"message": "the concept sentence and the set pieces", "ops": [...]}.';
  const t2: Turn[] = [{ role: 'user', content: o.ctxNoImages }, ...o.history, { role: 'user', content: `${o.request}

${step1}` }, { role: 'assistant', content: a.text }, { role: 'user', content: step2 }];
  io.step('plan', { state: 'run', detail: 'writing operations…' });
  const b = await askSafe(io, t2, [], o.effort === 'extra' || o.effort === 'high' ? 'medium' : 'low', 'plan');
  const plan = parseReply(b.text);
  if (!plan || !plan.ops.length) throw { code: b.truncated ? 'empty_completion' : 'invalid_json' };
  io.step('plan', { state: 'done', detail: `${plan.ops.length} operations${(plan as any).salvaged ? ' (kept what was written before it was cut short)' : ''}` });
  return { plan: { message: plan.message || note, ops: plan.ops }, turns: [...t2, { role: 'assistant' as const, content: b.text }] };
}

export function maxImagesFor(effort: Effort) {
  const d = store.state.director;
  const cfg = EFFORTS[effort];
  return d.images ? Math.min(cfg.images, d.maxImages || cfg.images) : 0;
}

export function reviewTimes(p: Project, max: number): number[] {
  const dur = projectDuration(p);
  if (dur <= 0) return [];
  const set = new Set<number>();
  const sweep = Math.min(max / 2, Math.max(6, Math.round(dur / 1.5)));
  for (let i = 0; i < sweep; i++) set.add(+(((i + 0.5) / sweep) * dur).toFixed(2));
  for (const c of p.clips) {
    if (c.transition) set.add(+c.start.toFixed(2));
    if (c.kind === 'text') set.add(+(c.start + Math.min(c.dur * 0.6, (c.anim?.inDur ?? 0.3) + 0.25)).toFixed(2));
  }
  for (const t of cutTimes(p)) if (t + 0.1 < dur) set.add(+(t + 0.1).toFixed(2));
  set.add(+(Math.max(0, dur - 1 / p.fps)).toFixed(3));
  let times = [...set].filter(t => t >= 0 && t < dur).sort((a, b) => a - b);
  if (times.length > max) {
    const keep: number[] = [];
    for (let i = 0; i < max; i++) keep.push(times[Math.floor((i * times.length) / max)]);
    times = keep;
  }
  return times;
}

export async function standardsForPreset(preset: Preset, ids?: string[]): Promise<Standard[]> {
  const all = await listStandards();
  if (ids) return all.filter(s => ids.includes(s.id));
  const out = [...all.filter(s => preset.standards.includes(s.id)), ...standardsFor(all, preset.id)];
  return out.filter((s, i) => out.findIndex(x => x.id === s.id) === i);
}

export function standardsText(standards: Standard[]): string {
  return standards.map(s => {
    const pr = s.profile;
    const prof = pr ? ` Measured: ${pr.duration.toFixed(1)} s, ${pr.cuts} cuts (${pr.cutsPerSec.toFixed(2)} per second, average shot ${pr.avgShot.toFixed(2)} s)${pr.bpm ? `, ${pr.bpm} BPM` : ''}${pr.onBeat !== null ? `, ${Math.round(pr.onBeat * 100)}% of cuts on a beat` : ''}.` : '';
    return `- "${s.name}"${s.url ? ` (${s.url})` : ''}: ${s.notes || 'the owner considers this a standard of what an edit should be.'}${prof}`;
  }).join('\n');
}

export function extrasFor(preset: Preset, standards: Standard[], checks?: string): ContextExtras {
  return {
    houseRules: preset.houseRules ? HOUSE_RULES : '',
    benchmarks: preset.houseRules ? BENCHMARK_TEXT : '',
    presetName: preset.name,
    presetPrompt: preset.prompt,
    standards: standardsText(standards),
    knowledge: store.state.director.knowledge,
    checks,
  };
}

/** Opus picks material from the database for this edit. */
async function castFromLibrary(io: JobIO, req: NonNullable<Job['request']>, preset: Preset, effort: Effort): Promise<{ items: LibraryItem[]; note?: string }> {
  const all = (await listLibrary()).filter(i => i.state === 'ready');
  let pool = req.library.mode === 'picked' ? all.filter(i => req.library.ids.includes(i.id)) : all;
  if (req.library.mode === 'auto' && preset.libraryTags.length) {
    const tagged = pool.filter(i => i.tags.some(t => preset.libraryTags.includes(t)) || i.role === 'music');
    if (tagged.length >= 2) pool = tagged;
  }
  if (!pool.length) return { items: [] };
  if (req.library.mode === 'picked' || pool.length <= 4) return { items: pool };
  io.step('cast', { detail: `choosing from ${pool.length} items` });
  const mosaic = await libraryMosaic(pool);
  const catalog = pool.slice(0, 300).map(i => `${i.id} ${i.role} ${i.kind} "${i.name}" ${i.duration.toFixed(1)}s${i.width ? ` ${i.width}x${i.height}` : ''}${i.bpm ? ` ${i.bpm} BPM` : ''}${i.shots ? ` ${i.shots} shots` : ''}${i.tags.length ? ` tags: ${i.tags.join(', ')}` : ''}${i.notes ? ` notes: ${i.notes}` : ''}`).join('\n');
  const prompt = [
    'You are casting material for a video edit in VOIDFX Studio. Pick the database items the edit should use.',
    `PRESET "${preset.name}": ${preset.prompt || preset.description}`,
    `OWNER'S NOTES FOR THIS EDIT: ${req.notes || '(none)'}`,
    req.lyrics ? `LYRICS SUPPLIED: ${req.lyrics.slice(0, 2000)}` : '',
    `DATABASE (${pool.length} items)\n${catalog}`,
    mosaic ? 'The attached image shows each item\'s poster frame, labelled with its id.' : '',
    'Pick one music item (unless the notes or attached files already supply the song) and the scene packs or clips with the strongest material for this concept; at most 6 items in total. Reply with only JSON: {"items": [{"id": "...", "why": "..."}], "message": "one sentence on the choice"}',
  ].filter(Boolean).join('\n\n');
  const r = await askSafe(io, prompt, mosaic ? [mosaic] : [], effort === 'extra' || effort === 'high' ? 'medium' : effort, 'cast');
  const raw: any = parseJson(r.text);
  const ids: string[] = Array.isArray(raw?.items) ? raw.items.map((x: any) => String(x?.id ?? x)) : [];
  const chosen = pool.filter(i => ids.includes(i.id)).slice(0, 6);
  return { items: chosen.length ? chosen : pool.slice(0, 4), note: typeof raw?.message === 'string' ? raw.message : undefined };
}

/** Every transition gets its own sound: add matched sounds where Opus left every transition silent. */
function withSounds(p: Project, media: Record<string, MediaInfo>): Project {
  const trans = p.clips.filter(c => c.transition);
  const sfx = p.clips.filter(c => c.kind === 'sfx');
  const silent = trans.filter(c => !sfx.some(s => s.start >= c.start - 2.2 && s.start <= c.start + 0.4));
  if (!silent.length || sfx.length) return p;
  const q = deepClone(p);
  addTransitionSounds(q);
  return normalize(q, media);
}

async function checkpoint(ws: Workspace, preset: Preset, seam: boolean): Promise<Check[]> {
  const s = seam ? await measureLoopSeam(ws.project, ws.media()).catch(() => null) : null;
  return runChecks(ws.project, ws.media(), { houseRules: preset.houseRules, duration: preset.duration, fps: preset.fps, seam: s });
}

/** Wait for the job's media, failing clearly if nothing usable is there. */
async function readMedia(ws: Workspace, io: JobIO) {
  io.step('media', { state: 'run', detail: 'opening files and sound analysis' });
  await ws.attach();
  await whenMediaIdle(240000, ws, io.signal);
  if (io.signal.aborted) throw { name: 'AbortError' };
  const n = ws.ready().length;
  if (!n) throw { code: 'no_media' };
  io.step('media', { state: 'done', detail: `${n} file${n > 1 ? 's' : ''}` });
}

const REVIEW_NOTE = 'Contact sheets of the media were attached to the first request and are not repeated. The images attached to the latest message are frames rendered from the edit as it stands now, labelled with timeline time.';

/** Opus looks at frames rendered from its own edit and the checkpoint, and fixes or raises it. */
async function reviewPasses(ws: Workspace, io: JobIO, opts: { preset: Preset; standards: Standard[]; effort: Effort; turns: Turn[]; res: OpsResult; checks: Check[]; mediaImages: boolean }) {
  const cfg = EFFORTS[opts.effort];
  const maxImg = maxImagesFor(opts.effort);
  let { res, checks } = opts;
  let total = 0, message = '';
  const issues: string[] = [];
  for (let k = 1; k <= cfg.reviews; k++) {
    const id = `review${k}`;
    io.step(id, { state: 'run', detail: 'rendering frames' });
    const p = ws.project;
    const times = reviewTimes(p, Math.min(4, Math.max(1, maxImg)) * 20);
    const rSheets = maxImg ? await timelineSheets(p, ws.media(), times, 20, Math.min(4, maxImg), io.signal) : [];
    io.step(id, { detail: 'thinking…' });
    const issuesText = res.issues.length ? `The studio adjusted or rejected these operations:\n- ${res.issues.slice(0, 40).join('\n- ')}` : 'All operations were applied without problems.';
    const reviewMsg = [
      `REVIEW ${k} of ${cfg.reviews}`,
      issuesText,
      `AUTOMATED CHECKPOINT\n${checksText(checks)}`,
      rSheets.length ? `IMAGES attached to this message: ${rSheets.map((x, i) => `${i + 1}. ${x.caption}`).join('; ')}` : 'No rendered frames are attached.',
      'The CURRENT TIMELINE in the first message is the edit after your operations. Fix every failed gate, then look at the frames: is any face cut off or off-centre, any text over a face, any shot weak, any moment flat? Ask what would make each set piece unforgettable. Reply with operations that fix or raise the edit, or {"message": "...", "ops": []} if it is ready. Do not start with clear unless you are rebuilding everything.',
    ].join('\n\n');
    opts.turns.push({ role: 'user', content: reviewMsg });
    const ctxNow = contextBlock(ws.ctx, [], opts.mediaImages ? REVIEW_NOTE : undefined, extrasFor(opts.preset, opts.standards));
    let rk: { text: string; truncated: boolean };
    try {
      rk = await askSafe(io, [{ role: 'user', content: ctxNow }, ...opts.turns.slice(1)], rSheets, opts.effort, id);
    } catch (e: any) {
      if (e?.code === 'cancelled' || io.signal.aborted || e?.code === 'not_granted' || e?.code === 'rate_limited') throw e;
      // the edit is already built: a review that fails is skipped, not fatal
      opts.turns.pop();
      io.step(id, { state: 'skip', detail: `skipped: ${errText(e).code}` });
      for (let j = k + 1; j <= cfg.reviews; j++) io.step(`review${j}`, { state: 'skip', detail: 'not run' });
      break;
    }
    const rev = parseReply(rk.text);
    if (!rev) {
      opts.turns.pop();
      io.step(id, { state: 'skip', detail: 'skipped: unreadable reply' });
      for (let j = k + 1; j <= cfg.reviews; j++) io.step(`review${j}`, { state: 'skip', detail: 'not run' });
      break;
    }
    opts.turns.push({ role: 'assistant', content: rk.text });
    if (rev.ops.length) {
      res = applyOps(ws.project, rev.ops, ws.media());
      ws.setProject(opts.preset.houseRules ? withSounds(res.project, ws.media()) : res.project);
      total += res.applied;
      issues.push(...res.issues);
      checks = await checkpoint(ws, opts.preset, true);
      await ws.save();
    } else {
      res = { ...res, issues: [] };
    }
    if (rev.message) message = rev.message;
    io.step(id, { state: 'done', detail: rev.ops.length ? `${rev.ops.length} changes` : 'approved' });
    if (!rev.ops.length) {
      for (let j = k + 1; j <= cfg.reviews; j++) io.step(`review${j}`, { state: 'skip', detail: 'not needed' });
      break;
    }
  }
  return { applied: total, issues, message, checks };
}

/** The steps a build or revision shows, before it starts. */
export function stepsFor(job: Job, hasFiles: boolean): JobStep[] {
  const reviews = EFFORTS[job.effort].reviews;
  const rev = Array.from({ length: reviews }, (_, i) => ({ id: `review${i + 1}`, label: `Opus reviews the render${reviews > 1 ? ` (${i + 1}/${reviews})` : ''}`, state: 'wait' as const }));
  if (job.kind === 'create') {
    return [
      ...(hasFiles ? [{ id: 'files', label: 'Store your files', state: 'wait' as const }] : []),
      ...(job.request && job.request.library.mode !== 'none' ? [{ id: 'cast', label: 'Pick material from the database', state: 'wait' as const }] : []),
      { id: 'media', label: 'Read the media', state: 'wait' },
      { id: 'sheets', label: 'Make contact sheets', state: 'wait' },
      ...(twoStage(job.effort) ? [{ id: 'direct', label: 'Opus directs: concept, song, shots, set pieces', state: 'wait' as const }, { id: 'plan', label: 'Opus writes the operations', state: 'wait' as const }] : [{ id: 'plan', label: 'Opus plans the edit', state: 'wait' as const }]),
      { id: 'apply', label: 'Apply, validate, add sounds', state: 'wait' },
      { id: 'check', label: 'Run the checkpoint', state: 'wait' },
      ...rev,
    ];
  }
  return [
    { id: 'media', label: 'Read the media', state: 'wait' },
    { id: 'look', label: 'Render the current edit', state: 'wait' },
    ...(twoStage(job.effort) ? [{ id: 'direct', label: `Opus decides the round ${job.round} changes`, state: 'wait' as const }, { id: 'plan', label: 'Opus writes the operations', state: 'wait' as const }] : [{ id: 'plan', label: `Opus works on round ${job.round}`, state: 'wait' as const }]),
    { id: 'apply', label: 'Apply, validate, add sounds', state: 'wait' },
    { id: 'check', label: 'Run the checkpoint', state: 'wait' },
    ...rev,
  ];
}

export interface RoundResult { summary: string; applied: number; issues: string[]; model?: string; checks: Check[] }

/** Round 1: build the whole edit from the project's media, the database and the brief. */
export async function buildEdit(job: Job, ws: Workspace, io: JobIO): Promise<RoundResult> {
  const req = job.request || { notes: '', lyrics: '', library: { mode: 'none' as const, ids: [] } };
  const preset = await getPreset(job.presetId);
  const standards = await standardsForPreset(preset, req.standards);
  const effort = job.effort;
  const cfg = EFFORTS[effort];
  let model: string | undefined;
  const io2: JobIO = { ...io, model: m => { model = m; io.model(m); } };

  // the preset sets the format before anything is planned
  const [w, h] = ASPECTS[preset.aspect] || ASPECTS['9:16'];
  if (ws.project.width !== w || ws.project.height !== h || ws.project.fps !== preset.fps) ws.setProject({ ...ws.project, width: w, height: h, fps: preset.fps });

  let castNote = '';
  if (req.library.mode !== 'none') {
    io.step('cast', { state: 'run' });
    const { items, note } = await castFromLibrary(io2, req, preset, effort).catch(async (e: any) => {
      if (e?.code === 'cancelled' || io.signal.aborted || e?.code === 'not_granted') throw e;
      // casting failed: use the database items the preset favours rather than stopping the build
      const all = (await listLibrary()).filter(i => i.state === 'ready');
      const pool = req.library.mode === 'picked' ? all.filter(i => req.library.ids.includes(i.id)) : all;
      const music = pool.filter(i => i.role === 'music').slice(0, 1);
      const rest = pool.filter(i => i.role !== 'music' && (!preset.libraryTags.length || i.tags.some(t => preset.libraryTags.includes(t)))).slice(0, 4);
      return { items: [...music, ...(rest.length ? rest : pool.filter(i => i.role !== 'music').slice(0, 4))], note: 'Picked by the studio (Opus could not answer the casting call).' };
    });
    for (const it of items) await attachLibraryItem(it, ws);
    castNote = note || '';
    io.step('cast', { state: items.length ? 'done' : 'skip', detail: items.length ? items.map(i => i.name).slice(0, 4).join(', ') + (items.length > 4 ? '…' : '') : 'the database is empty' });
    await ws.save();
  }
  await readMedia(ws, io);

  io.step('sheets', { state: 'run' });
  const maxImg = maxImagesFor(effort);
  const stdVideos = standards.filter(x => x.kind === 'video' && x.state === 'ready');
  const stdImgs = maxImg > 4 ? await standardSheets(stdVideos, Math.min(3, Math.floor(maxImg / 4))) : [];
  const sheets = maxImg ? await mediaSheets(ws.ctx, maxImg - stdImgs.length, cfg.cells, io.signal, msg => io.step('sheets', { detail: msg })) : [];
  const images = [...stdImgs, ...sheets];
  io.step('sheets', { state: images.length ? 'done' : 'skip', detail: images.length ? `${images.length} image${images.length > 1 ? 's' : ''}` : 'images not available here' });

  const extras = extrasFor(preset, standards);
  const ctx = contextBlock(ws.ctx, images.map(x => x.caption), undefined, extras);
  const request = [
    'OWNER\'S REQUEST FOR THIS EDIT (round 1: the build)',
    req.notes || 'No extra notes: make the best edit you can from this material.',
    castNote ? `MATERIAL CHOSEN FROM THE DATABASE: ${castNote}` : '',
    req.lyrics ? `LYRICS (the owner supplied them; caption only what is sung, on its time)\n${req.lyrics}` : '',
  ].filter(Boolean).join('\n\n');
  let plan: { message: string; ops: unknown[] };
  let turns: Turn[];
  if (twoStage(effort)) {
    const ctxNoImages = contextBlock(ws.ctx, [], images.length ? 'Contact sheets of the media were attached in step 1 and are not repeated: use the media ids, shots and source times from your direction.' : undefined, extras);
    ({ plan, turns } = await directThenBuild(io2, { ctx, ctxNoImages, history: [], request, images, effort, revision: false }));
  } else {
    io.step('plan', { state: 'run', detail: 'thinking…' });
    turns = [{ role: 'user', content: ctx }, { role: 'user', content: `${request}\n\nPlan it first in your head: the concept sentence, the song section and drop, the set pieces, the shot list, the transitions and sounds, the text and the loop; compare it with the standards; then build it. Start with {"op":"clear"} unless the request asks you to keep the current timeline. Put the concept sentence and the set pieces in "message".` }];
    const r1 = await askSafe(io2, turns, images, effort, 'plan');
    const p1 = parseReply(r1.text);
    if (!p1 || !p1.ops.length) throw { code: 'invalid_json' };
    plan = p1;
    turns.push({ role: 'assistant', content: r1.text });
    io.step('plan', { state: 'done', detail: `${plan.ops.length} operations${(p1 as any).salvaged ? ' (kept what was written before it was cut short)' : r1.truncated ? ' (cut short)' : ''}` });
  }

  io.step('apply', { state: 'run' });
  const res = applyOps(ws.project, plan.ops, ws.media());
  ws.setProject(preset.houseRules ? withSounds(res.project, ws.media()) : res.project);
  await ws.save();
  io.step('apply', { state: 'done', detail: `${res.applied} applied${res.issues.length ? `, ${res.issues.length} adjusted` : ''}` });

  io.step('check', { state: 'run' });
  let checks = await checkpoint(ws, preset, true);
  const failing = checks.filter(c => c.status === 'fail' || c.status === 'warn').length;
  io.step('check', { state: 'done', detail: failing ? `${failing} to look at` : 'all gates pass' });

  const rv = await reviewPasses(ws, io2, { preset, standards, effort, turns, res, checks, mediaImages: images.length > 0 });
  checks = rv.checks;
  const summary = rv.message || plan.message || 'The edit is on the timeline.';
  await finishRound(ws, job, { summary, applied: res.applied + rv.applied, model }, turns);
  return { summary, applied: res.applied + rv.applied, issues: [...res.issues, ...rv.issues], model, checks };
}

/** Later rounds: the owner's instructions (and the critic points they passed on) applied to the current edit. */
export async function reviseEdit(job: Job, ws: Workspace, io: JobIO): Promise<RoundResult> {
  const preset = await getPreset(job.presetId);
  const standards = await standardsForPreset(preset);
  const effort = job.effort;
  const cfg = EFFORTS[effort];
  let model: string | undefined;
  const io2: JobIO = { ...io, model: m => { model = m; io.model(m); } };
  await readMedia(ws, io);
  if (!ws.project.clips.length) throw { code: 'no_edit' };

  io.step('look', { state: 'run' });
  const maxImg = maxImagesFor(effort);
  const p = ws.project;
  const timeSheets = maxImg ? await timelineSheets(p, ws.media(), reviewTimes(p, Math.min(3, maxImg) * 20), 20, Math.min(3, maxImg), io.signal) : [];
  const footage = maxImg > timeSheets.length ? await mediaSheets(ws.ctx, Math.max(1, Math.floor((maxImg - timeSheets.length) * 0.7)), cfg.cells, io.signal, msg => io.step('look', { detail: msg })) : [];
  const sheets = [...timeSheets, ...footage];
  io.step('look', { state: sheets.length ? 'done' : 'skip', detail: sheets.length ? `${sheets.length} image${sheets.length > 1 ? 's' : ''}` : 'no images' });

  const checks0 = await checkpoint(ws, preset, true);
  const extras = extrasFor(preset, standards, checksText(checks0));
  const ctx = contextBlock(ws.ctx, sheets.map(x => x.caption), undefined, extras);
  const rounds = ws.rec.rounds || [];
  const history: Turn[] = (ws.rec.aiTurns || []).slice(-6);
  const past = rounds.map(r => `Round ${r.n} (${r.kind}): owner asked "${r.brief.slice(0, 400)}"${r.summary ? `; you answered "${r.summary.slice(0, 300)}"` : ''}${r.critique ? `; the critic scored it ${r.critique.score}/10: ${r.critique.headline}` : ''}`).join('\n');
  const fromCritic = job.fromCritic?.length ? `THE CRITIC'S POINTS THE OWNER PASSED ON (fix every one)\n${job.fromCritic.map((x, i) => `${i + 1}. ${x}`).join('\n')}` : '';
  const instruction = [
    `ROUND ${job.round} INSTRUCTIONS FROM THE OWNER`,
    job.brief?.trim() || '(no extra words: work through the critic\'s points)',
    fromCritic,
    past ? `EARLIER ROUNDS\n${past}` : '',
    'Change the current timeline to do all of this. Keep what already works unless the instructions say otherwise; rebuild a section completely when that is what it takes. The first images are frames rendered from the edit as it stands; the rest are contact sheets of the media for finding better shots.',
  ].filter(Boolean).join('\n\n');
  let plan: { message: string; ops: unknown[] };
  let turns: Turn[];
  if (twoStage(effort)) {
    const ctxNoImages = contextBlock(ws.ctx, [], sheets.length ? 'The rendered frames and contact sheets were attached in step 1 and are not repeated: use the times, media ids and shots from your decisions.' : undefined, extras);
    ({ plan, turns } = await directThenBuild(io2, { ctx, ctxNoImages, history, request: instruction, images: sheets, effort, revision: true }));
  } else {
    io.step('plan', { state: 'run', detail: 'thinking…' });
    turns = [{ role: 'user', content: ctx }, ...history, { role: 'user', content: `${instruction}\n\nPut what you changed, point by point, in "message".` }];
    const r = await askSafe(io2, turns, sheets, effort, 'plan');
    const p1 = parseReply(r.text);
    if (!p1) throw { code: 'invalid_json' };
    plan = p1;
    turns.push({ role: 'assistant', content: r.text });
    io.step('plan', { state: 'done', detail: `${plan.ops.length} operations${(p1 as any).salvaged ? ' (kept what was written before it was cut short)' : r.truncated ? ' (cut short)' : ''}` });
  }

  io.step('apply', { state: 'run' });
  const res = applyOps(ws.project, plan.ops, ws.media());
  if (plan.ops.length) ws.setProject(preset.houseRules ? withSounds(res.project, ws.media()) : res.project);
  await ws.save();
  io.step('apply', { state: 'done', detail: `${res.applied} applied${res.issues.length ? `, ${res.issues.length} adjusted` : ''}` });

  io.step('check', { state: 'run' });
  let checks = await checkpoint(ws, preset, true);
  const failing = checks.filter(c => c.status === 'fail' || c.status === 'warn').length;
  io.step('check', { state: 'done', detail: failing ? `${failing} to look at` : 'all gates pass' });

  const rv = await reviewPasses(ws, io2, { preset, standards, effort, turns, res, checks, mediaImages: footage.length > 0 });
  checks = rv.checks;
  const summary = rv.message || plan.message || (plan.ops.length ? 'Done.' : 'No changes were needed.');
  await finishRound(ws, job, { summary, applied: res.applied + rv.applied, model }, turns);
  return { summary, applied: res.applied + rv.applied, issues: [...res.issues, ...rv.issues], model, checks };
}

/** Record the round on the project, with a short memory of the exchange for later rounds. */
async function finishRound(ws: Workspace, job: Job, out: { summary: string; applied: number; model?: string }, turns: Turn[]) {
  const round: Round = {
    n: job.round, kind: job.kind === 'create' ? 'create' : 'revise', at: Date.now(), jobId: job.id, effort: job.effort, presetId: job.presetId,
    brief: job.kind === 'create' ? job.request?.notes || '' : job.brief || '', fromCritic: job.fromCritic, summary: out.summary, applied: out.applied, model: out.model,
    snapshot: deepClone(ws.project),
  };
  // keep the owner's requests and Opus's replies, not the large context blocks
  const memory = turns.filter((t, i) => i > 0 && !t.content.startsWith('You are the editor')).map(t => ({ role: t.role, content: t.content.slice(0, 6000) })).slice(-6);
  await ws.save(rec => {
    const rounds = (rec.rounds || []).filter(r => r.n !== round.n);
    rec.rounds = [...rounds, round].sort((a, b) => a.n - b.n);
    rec.aiTurns = memory;
    rec.director = { ...rec.director, presetId: job.presetId, effort: job.effort };
    if (job.kind === 'revise') rec.draft = '';
  });
}
