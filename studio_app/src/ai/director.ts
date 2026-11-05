// The Opus Director: builds or refines the whole edit through the `sample` capability.
// Pipeline: preset + notes + standards → (cast material from the database) → read the media →
// contact sheets → Opus plans operations → studio applies, validates and adds missing sounds →
// automated checkpoint → render frames → Opus review pass(es) with the checkpoint → done.
import { BENCHMARK_TEXT, HOUSE_RULES } from './knowledge';
import { checksText } from '../engine/qc';
import { cutTimes } from '../engine/evaluate';
import { attachLibraryItem, whenMediaIdle } from '../media/library';
import { getPreset, LibraryItem, listLibrary, listStandards, Preset, Standard, standardsFor } from '../state/catalog';
import { addTransitionSounds, applyOps, normalize } from '../state/ops';
import { DirectorMsg, DirectorStep, Effort, store } from '../state/store';
import { ASPECTS, Project } from '../state/types';
import { deepClone, projectDuration, uid } from '../state/util';
import { refreshChecks } from './checkrunner';
import { ContextExtras, contextBlock, parseJson, parseReply } from './prompt';
import { libraryMosaic, mediaSheets, Sheet, standardSheets, timelineSheets } from './sheets';

export const MODEL = 'claude-opus-5-5';

type SampleFn = ((input: any, opts?: any) => Promise<{ text: string; truncated: boolean; modelTierApplied: string; modelApplied?: string }>) & {
  limits(): Promise<{ maxPromptBytes: number; images?: { maxCount: number; maxInputBytes: number; mediaTypes: string[] } }>;
};

let sample: SampleFn | null = null;
let ctl: AbortController | null = null;
/** Conversation kept by the page (sample calls are memoryless). */
let turns: { role: 'user' | 'assistant'; content: string }[] = [];

export const EFFORTS: Record<Effort, { label: string; effort: 'low' | 'medium' | 'high'; reviews: number; images: number; cells: number; hint: string }> = {
  low: { label: 'Low', effort: 'low', reviews: 0, images: 4, cells: 12, hint: 'Fastest. One planning pass with light thinking.' },
  medium: { label: 'Medium', effort: 'medium', reviews: 0, images: 8, cells: 16, hint: 'One planning pass with more thinking.' },
  high: { label: 'High', effort: 'high', reviews: 1, images: 12, cells: 16, hint: 'Deep thinking, then Opus reviews rendered frames of its edit and the checkpoint once.' },
  extra: { label: 'Extra', effort: 'high', reviews: 2, images: 16, cells: 20, hint: 'Deepest: the most footage per call and two review passes on rendered frames and the checkpoint.' },
};

const ERR: Record<string, string> = {
  not_granted: 'Opus is not allowed to run here. Allow Claude for this artifact when asked, then try again.',
  sampling_disabled: 'Claude is not available on this account right now.',
  not_declared: 'This page is not set up to use Claude.',
  capability_disabled: 'Claude is turned off in this view.',
  capability_removed: 'This viewer app is out of date. Reload or update it.',
  session_expired: 'Sign in to Claude again, then retry.',
  rate_limited: 'Too many requests or your usage limit was reached. Wait a little, then try again.',
  refused: 'Opus declined this request. Try rewording it.',
  empty_completion: 'Opus returned nothing. Try again with a shorter request.',
  invalid_json: 'Opus replied in a shape the studio could not read. Try again.',
  prompt_too_large: 'The request was too large. Use fewer database items or shorten the knowledge text.',
  image_rejected: 'A contact sheet was rejected. Try again with fewer files.',
  images_unavailable: 'Images cannot be sent in this view, so Opus worked from the analysis only.',
  upstream_error: 'Could not reach Opus. Check your connection and try again.',
};
const HIDE = new Set(['not_granted', 'sampling_disabled', 'not_declared', 'capability_disabled', 'capability_removed']);

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

// ---------- step bookkeeping ----------

function step(id: string, patch: Partial<DirectorStep>) {
  const steps = store.state.director.steps.map(s => (s.id === id ? { ...s, ...patch, ...(patch.state === 'run' ? { t0: Date.now() } : {}), ...(patch.state === 'done' || patch.state === 'error' || patch.state === 'skip' ? { t1: Date.now() } : {}) } : s));
  store.setDirector({ steps });
}
function say(m: Omit<DirectorMsg, 'id'>) {
  store.setDirector({ messages: [...store.state.director.messages, { id: uid('d'), ...m }].slice(-60) });
}

export function stopDirector() { ctl?.abort(); }

export function resetConversation() {
  turns = [];
  store.setDirector({ messages: [], steps: [] });
}

async function ask(input: string | { role: 'user' | 'assistant'; content: string }[], images: Sheet[], effort: Effort, label: string): Promise<{ text: string; model?: string; truncated: boolean }> {
  if (!sample) throw { code: 'not_declared' };
  const e = EFFORTS[effort];
  const opts: any = {
    model: MODEL, modelTier: 'complex', effort: e.effort, cache: false, signal: ctl!.signal,
    onText: ({ text }: { text: string }) => {
      const ops = (text.match(/"op"\s*:/g) || []).length;
      store.setDirector({ streamChars: text.length });
      step(label, { detail: ops ? `writing… ${ops} operations so far` : 'writing…' });
    },
  };
  if (images.length && store.state.director.images) opts.images = images.map(s => s.blob);
  const res = await sample(input, opts);
  store.setDirector({ lastModel: res.modelApplied || `${res.modelTierApplied} tier` });
  return { text: res.text, model: res.modelApplied || `${res.modelTierApplied} tier`, truncated: res.truncated };
}

function reviewTimes(p: Project, max: number): number[] {
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

function errText(e: any): { code: string; text: string } {
  const code = e?.code || (e?.name === 'AbortError' ? 'cancelled' : 'upstream_error');
  return { code, text: ERR[code] || e?.message || ERR.upstream_error };
}

async function extrasFor(preset: Preset, standards: Standard[], checks?: string): Promise<ContextExtras> {
  const stdText = standards.map(s => {
    const pr = s.profile;
    const prof = pr ? ` Measured: ${pr.duration.toFixed(1)} s, ${pr.cuts} cuts (${pr.cutsPerSec.toFixed(2)} per second, average shot ${pr.avgShot.toFixed(2)} s)${pr.bpm ? `, ${pr.bpm} BPM` : ''}${pr.onBeat !== null ? `, ${Math.round(pr.onBeat * 100)}% of cuts on a beat` : ''}.` : '';
    return `- "${s.name}"${s.url ? ` (${s.url})` : ''}: ${s.notes || 'the owner considers this a standard of what an edit should be.'}${prof}`;
  }).join('\n');
  return {
    houseRules: preset.houseRules ? HOUSE_RULES : '',
    benchmarks: preset.houseRules ? BENCHMARK_TEXT : '',
    presetName: preset.name,
    presetPrompt: preset.prompt,
    standards: stdText,
    knowledge: store.state.director.knowledge,
    checks,
  };
}

export interface EditRequest {
  presetId: string;
  notes: string;
  lyrics: string;
  effort: Effort;
  /** Database use: none, let Opus choose (auto), or the picked item ids. */
  library: { mode: 'none' | 'auto' | 'picked'; ids: string[] };
  /** Standards to show (ids); defaults to the preset's plus general reference edits. */
  standards?: string[];
}

/** Opus picks material from the database for this edit. */
async function castFromLibrary(req: EditRequest, preset: Preset, effort: Effort): Promise<LibraryItem[]> {
  const all = (await listLibrary()).filter(i => i.state === 'ready');
  let pool = req.library.mode === 'picked' ? all.filter(i => req.library.ids.includes(i.id)) : all;
  if (req.library.mode === 'auto' && preset.libraryTags.length) {
    const tagged = pool.filter(i => i.tags.some(t => preset.libraryTags.includes(t)) || i.role === 'music');
    if (tagged.length >= 2) pool = tagged;
  }
  if (!pool.length) return [];
  if (req.library.mode === 'picked' || pool.length <= 4) return pool;
  step('cast', { detail: `choosing from ${pool.length} items` });
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
  const r = await ask(prompt, mosaic ? [mosaic] : [], effort === 'extra' ? 'high' : effort, 'cast');
  const raw: any = parseJson(r.text);
  const ids: string[] = Array.isArray(raw?.items) ? raw.items.map((x: any) => String(x?.id ?? x)) : [];
  const chosen = pool.filter(i => ids.includes(i.id)).slice(0, 6);
  if (raw?.message) say({ role: 'note', text: `Material: ${raw.message}` });
  return chosen.length ? chosen : pool.slice(0, 4);
}

/** Build the whole edit (or rebuild it) from the project's media, the database and the brief. */
export async function createEdit(partial: Partial<EditRequest> = {}) {
  const d = store.state.director;
  if (d.running || !sample) return;
  const req: EditRequest = {
    presetId: partial.presetId ?? d.presetId,
    notes: partial.notes ?? d.brief,
    lyrics: partial.lyrics ?? '',
    effort: partial.effort ?? d.effort,
    library: partial.library ?? { mode: 'none', ids: [] },
    standards: partial.standards,
  };
  const preset = await getPreset(req.presetId);
  const allStd = await listStandards();
  const standards = req.standards ? allStd.filter(s => req.standards!.includes(s.id)) : [...allStd.filter(s => preset.standards.includes(s.id)), ...standardsFor(allStd, preset.id)];
  const effort = req.effort;
  const cfg = EFFORTS[effort];
  const useLibrary = req.library.mode !== 'none';
  ctl = new AbortController();
  turns = [];
  const steps: DirectorStep[] = [
    ...(useLibrary ? [{ id: 'cast', label: 'Pick material from the database', state: 'wait' as const }] : []),
    { id: 'media', label: 'Read the media', state: 'wait' },
    { id: 'sheets', label: 'Make contact sheets', state: 'wait' },
    { id: 'plan', label: 'Opus plans the edit', state: 'wait' },
    { id: 'apply', label: 'Apply, validate, add sounds', state: 'wait' },
    { id: 'check', label: 'Run the checkpoint', state: 'wait' },
    ...Array.from({ length: cfg.reviews }, (_, i) => ({ id: `review${i + 1}`, label: `Opus reviews the render${cfg.reviews > 1 ? ` (${i + 1}/${cfg.reviews})` : ''}`, state: 'wait' as const })),
  ];
  store.setDirector({ running: true, steps, streamChars: 0, presetId: preset.id, brief: req.notes, effort });
  say({ role: 'user', text: `${preset.name}${req.notes ? `: ${req.notes}` : ''}` });
  const startDepth = store.historyDepth;
  let total = 0;
  const allIssues: string[] = [];
  try {
    // the preset sets the format before anything is planned
    if (preset.houseRules || preset.fps) {
      const [w, h] = ASPECTS[preset.aspect] || ASPECTS['9:16'];
      const p0 = store.state.project;
      if (p0.width !== w || p0.height !== h || p0.fps !== preset.fps) store.commit(p => { p.width = w; p.height = h; p.fps = preset.fps; });
    }
    if (useLibrary) {
      step('cast', { state: 'run' });
      const items = await castFromLibrary(req, preset, effort);
      for (const it of items) await attachLibraryItem(it);
      step('cast', { state: items.length ? 'done' : 'skip', detail: items.length ? items.map(i => i.name).slice(0, 4).join(', ') + (items.length > 4 ? '…' : '') : 'the database is empty' });
    }
    const s = store.state;
    const ready = () => store.state.mediaOrder.map(id => store.state.media[id]).filter(m => m && m.status !== 'error');
    if (!ready().length) throw { code: 'no_media', message: 'Add files or database material first. Opus builds the edit from them.' };

    step('media', { state: 'run', detail: 'waiting for thumbnails and sound analysis' });
    await whenMediaIdle(240000);
    step('media', { state: 'done', detail: `${ready().length} file${ready().length > 1 ? 's' : ''}` });

    step('sheets', { state: 'run' });
    const maxImg = s.director.images ? Math.min(cfg.images, s.director.maxImages || cfg.images) : 0;
    const stdVideos = standards.filter(x => x.kind === 'video' && x.state === 'ready');
    const stdImgs = maxImg > 4 ? await standardSheets(stdVideos, Math.min(3, Math.floor(maxImg / 4))) : [];
    const sheets = maxImg ? await mediaSheets(maxImg - stdImgs.length, cfg.cells, ctl.signal, msg => step('sheets', { detail: msg })) : [];
    const images = [...stdImgs, ...sheets];
    step('sheets', { state: images.length ? 'done' : 'skip', detail: images.length ? `${images.length} image${images.length > 1 ? 's' : ''}` : 'images not available here' });

    step('plan', { state: 'run', detail: 'thinking…' });
    const extras = await extrasFor(preset, standards);
    const ctx = contextBlock(store.state.project, images.map(x => x.caption), undefined, extras);
    const request = [
      'OWNER\'S REQUEST FOR THIS EDIT',
      req.notes || 'No extra notes: make the best edit you can from this material.',
      req.lyrics ? `LYRICS (the owner supplied them; caption only what is sung, on its time)\n${req.lyrics}` : '',
      'Plan it first in your head: the concept sentence, the song section and drop, the set pieces, the shot list, the transitions and sounds, the text and the loop; compare it with the standards; then build it. Start with {"op":"clear"} unless the request asks you to keep the current timeline. Put the concept sentence and the set pieces in "message".',
    ].filter(Boolean).join('\n\n');
    turns = [{ role: 'user', content: ctx }, { role: 'user', content: request }];
    const r1 = await ask(turns, images, effort, 'plan');
    const plan = parseReply(r1.text);
    if (!plan) throw { code: 'invalid_json' };
    turns.push({ role: 'assistant', content: r1.text });
    step('plan', { state: 'done', detail: `${plan.ops.length} operations${r1.truncated ? ' (cut short)' : ''}` });

    step('apply', { state: 'run' });
    let res = applyOps(store.state.project, plan.ops, store.state.media);
    let next = res.project;
    if (preset.houseRules) next = withSounds(next);
    store.replace(next);
    total += res.applied;
    allIssues.push(...res.issues);
    step('apply', { state: 'done', detail: `${res.applied} applied${res.issues.length ? `, ${res.issues.length} adjusted` : ''}` });
    let lastMessage = plan.message;

    step('check', { state: 'run' });
    let checks = await refreshChecks({ seam: true });
    const failing = checks.filter(c => c.status === 'fail' || c.status === 'warn').length;
    step('check', { state: 'done', detail: failing ? `${failing} to look at` : 'all gates pass' });

    for (let k = 1; k <= cfg.reviews; k++) {
      const id = `review${k}`;
      step(id, { state: 'run', detail: 'rendering frames' });
      const p = store.state.project;
      const times = reviewTimes(p, Math.min(4, Math.max(1, maxImg)) * 20);
      const rSheets = maxImg ? await timelineSheets(p, times, 20, Math.min(4, maxImg), ctl.signal) : [];
      step(id, { detail: 'thinking…' });
      const issuesText = res.issues.length ? `The studio adjusted or rejected these operations:\n- ${res.issues.slice(0, 40).join('\n- ')}` : 'All operations were applied without problems.';
      const reviewMsg = [
        `REVIEW ${k} of ${cfg.reviews}`,
        issuesText,
        `AUTOMATED CHECKPOINT\n${checksText(checks)}`,
        rSheets.length ? `IMAGES attached to this message: ${rSheets.map((x, i) => `${i + 1}. ${x.caption}`).join('; ')}` : 'No rendered frames are attached.',
        'The CURRENT TIMELINE in the first message is the edit after your operations. Fix every failed gate, then look at the frames: is any face cut off or off-centre, any text over a face, any shot weak, any moment flat? Ask what would make each set piece unforgettable. Reply with operations that fix or raise the edit, or {"message": "...", "ops": []} if it is ready. Do not start with clear unless you are rebuilding everything.',
      ].join('\n\n');
      turns.push({ role: 'user', content: reviewMsg });
      const ctxNow = contextBlock(p, [], images.length ? 'Contact sheets of the media were attached to the first request and are not repeated. The images attached to the latest message are frames rendered from the edit as it stands now, labelled with timeline time.' : undefined, await extrasFor(preset, standards));
      const rk = await ask([{ role: 'user', content: ctxNow }, ...turns.slice(1)], rSheets, effort, id);
      const rev = parseReply(rk.text);
      if (!rev) throw { code: 'invalid_json' };
      turns.push({ role: 'assistant', content: rk.text });
      if (rev.ops.length) {
        res = applyOps(store.state.project, rev.ops, store.state.media);
        next = preset.houseRules ? withSounds(res.project) : res.project;
        store.replace(next);
        total += res.applied;
        allIssues.push(...res.issues);
        checks = await refreshChecks({ seam: true });
      } else {
        res = { ...res, issues: [] };
      }
      if (rev.message) lastMessage = rev.message;
      step(id, { state: 'done', detail: rev.ops.length ? `${rev.ops.length} changes` : 'approved' });
      if (!rev.ops.length) {
        for (let j = k + 1; j <= cfg.reviews; j++) step(`review${j}`, { state: 'skip', detail: 'not needed' });
        break;
      }
    }
    say({ role: 'opus', text: lastMessage || 'The edit is on the timeline.', applied: total, issues: allIssues.slice(0, 30), model: store.state.director.lastModel, undoTo: startDepth });
    store.set({ selection: [], rightTab: 'director' });
  } catch (e: any) {
    const { code, text } = e?.code === 'no_media' ? { code: 'no_media', text: e.message } : errText(e);
    const cur = store.state.director.steps.find(x => x.state === 'run');
    if (cur) step(cur.id, { state: 'error', detail: code === 'cancelled' ? 'stopped' : code });
    say({ role: 'note', text: code === 'cancelled' ? 'Stopped.' : text, undoTo: store.historyDepth > startDepth ? startDepth : undefined });
    if (HIDE.has(code)) store.setDirector({ available: 'no', unavailableReason: text });
  } finally {
    store.setDirector({ running: false });
    ctl = null;
  }
}

/** Every transition gets its own sound: add matched sounds where Opus left a transition silent. */
function withSounds(p: Project): Project {
  const trans = p.clips.filter(c => c.transition);
  const sfx = p.clips.filter(c => c.kind === 'sfx');
  const silent = trans.filter(c => !sfx.some(s => s.start >= c.start - 2.2 && s.start <= c.start + 0.4));
  if (!silent.length) return p;
  if (!sfx.length) {
    const q = deepClone(p);
    addTransitionSounds(q);
    return normalize(q, store.state.media);
  }
  return p;
}

/** Follow-up instruction in the chat ("make the intro faster"). Sees fresh frames and the checkpoint. */
export async function refineEdit(message: string) {
  const d = store.state.director;
  const text = message.trim();
  if (!text || d.running || !sample) return;
  const effort = d.effort;
  const cfg = EFFORTS[effort];
  const preset = await getPreset(d.presetId);
  const allStd = await listStandards();
  const standards = [...allStd.filter(s => preset.standards.includes(s.id)), ...standardsFor(allStd, preset.id)];
  ctl = new AbortController();
  store.setDirector({ running: true, streamChars: 0, steps: [
    { id: 'look', label: 'Render frames of the edit', state: 'wait' },
    { id: 'plan', label: 'Opus works on it', state: 'wait' },
    { id: 'apply', label: 'Apply and check', state: 'wait' },
  ] });
  say({ role: 'user', text });
  const startDepth = store.historyDepth;
  try {
    await whenMediaIdle(60000);
    const p = store.state.project;
    const maxImg = d.images ? Math.min(cfg.images, d.maxImages || cfg.images) : 0;
    step('look', { state: 'run' });
    const hasEdit = p.clips.length > 0;
    let sheets: Sheet[] = [];
    if (maxImg && hasEdit) sheets = await timelineSheets(p, reviewTimes(p, Math.min(3, maxImg) * 20), 20, Math.min(3, maxImg), ctl.signal);
    if (maxImg && (!turns.length || !hasEdit)) sheets = [...sheets, ...(await mediaSheets(Math.max(1, maxImg - sheets.length), cfg.cells, ctl.signal))];
    step('look', { state: sheets.length ? 'done' : 'skip', detail: sheets.length ? `${sheets.length} image${sheets.length > 1 ? 's' : ''}` : 'no images' });
    step('plan', { state: 'run', detail: 'thinking…' });
    const checks = await refreshChecks();
    const ctx = contextBlock(p, sheets.map(x => x.caption), undefined, await extrasFor(preset, standards, checksText(checks)));
    const history = turns.filter(t => t.role === 'assistant' || !t.content.startsWith('You are the editor')).slice(-6);
    const input: { role: 'user' | 'assistant'; content: string }[] = [
      { role: 'user', content: ctx },
      ...history,
      { role: 'user', content: `OWNER'S REQUEST\n${text}\n\nChange the current timeline to do this. Keep everything else as it is unless the request says otherwise.` },
    ];
    const r = await ask(input, sheets, effort, 'plan');
    const plan = parseReply(r.text);
    if (!plan) throw { code: 'invalid_json' };
    step('plan', { state: 'done', detail: `${plan.ops.length} operations` });
    step('apply', { state: 'run' });
    const res = applyOps(store.state.project, plan.ops, store.state.media);
    if (plan.ops.length) store.replace(res.project);
    await refreshChecks();
    step('apply', { state: 'done', detail: `${res.applied} applied${res.issues.length ? `, ${res.issues.length} adjusted` : ''}` });
    const next: typeof turns = [...input.slice(1), { role: 'assistant' as const, content: r.text }];
    turns = next.filter(t => !t.content.startsWith('You are the editor')).slice(-8);
    say({ role: 'opus', text: plan.message || (plan.ops.length ? 'Done.' : 'No changes.'), applied: res.applied, issues: res.issues.slice(0, 30), model: store.state.director.lastModel, undoTo: plan.ops.length ? startDepth : undefined });
  } catch (e: any) {
    const { code, text: msg } = errText(e);
    const cur = store.state.director.steps.find(x => x.state === 'run');
    if (cur) step(cur.id, { state: 'error', detail: code === 'cancelled' ? 'stopped' : code });
    say({ role: 'note', text: code === 'cancelled' ? 'Stopped.' : msg });
    if (HIDE.has(code)) store.setDirector({ available: 'no', unavailableReason: msg });
  } finally {
    store.setDirector({ running: false });
    ctl = null;
  }
}

export function directorReady() { return !!sample; }
