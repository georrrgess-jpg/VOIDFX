// The Opus Director: builds or refines the whole edit through the `sample` capability.
// Pipeline: wait for analysis → contact sheets → Opus plans operations → studio applies and
// validates them → render frames of the result → Opus review pass(es) (High and Extra).
import { applyOps } from '../state/ops';
import { DirectorMsg, DirectorStep, Effort, store } from '../state/store';
import { Project } from '../state/types';
import { projectDuration, uid } from '../state/util';
import { cutTimes } from '../engine/evaluate';
import { whenMediaIdle } from '../media/library';
import { contextBlock, parseReply } from './prompt';
import { mediaSheets, Sheet, timelineSheets } from './sheets';

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
  high: { label: 'High', effort: 'high', reviews: 1, images: 12, cells: 16, hint: 'Deep thinking, then Opus reviews rendered frames of its edit once.' },
  extra: { label: 'Extra', effort: 'high', reviews: 2, images: 16, cells: 20, hint: 'Deepest: the most footage per call and two review passes on rendered frames.' },
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
  prompt_too_large: 'The request was too large. Remove some media or shorten the knowledge text.',
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
  const steps = store.state.director.steps.map(s => (s.id === id ? { ...s, ...patch, ...(patch.state === 'run' ? { t0: Date.now() } : {}), ...(patch.state === 'done' || patch.state === 'error' ? { t1: Date.now() } : {}) } : s));
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
  if (res.modelApplied) store.setDirector({ lastModel: res.modelApplied });
  else store.setDirector({ lastModel: `${res.modelTierApplied} tier` });
  return { text: res.text, model: res.modelApplied || `${res.modelTierApplied} tier`, truncated: res.truncated };
}

function reviewTimes(p: Project, max: number): number[] {
  const dur = projectDuration(p);
  if (dur <= 0) return [];
  const set = new Set<number>();
  // a steady sweep plus the moments right after every cut and inside transitions
  const sweep = Math.min(max / 2, Math.max(6, Math.round(dur / 1.5)));
  for (let i = 0; i < sweep; i++) set.add(+(((i + 0.5) / sweep) * dur).toFixed(2));
  for (const c of p.clips) {
    if (c.transition) set.add(+c.start.toFixed(2));
    if (c.kind === 'text') set.add(+(c.start + Math.min(c.dur * 0.6, (c.anim?.inDur ?? 0.3) + 0.25)).toFixed(2));
  }
  for (const t of cutTimes(p)) if (t + 0.1 < dur) set.add(+(t + 0.1).toFixed(2));
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

/** Build the whole edit (or rebuild it) from the library and the user's brief. */
export async function createEdit() {
  const d = store.state.director;
  if (d.running || !sample) return;
  const s = store.state;
  const ready = s.mediaOrder.map(id => s.media[id]).filter(m => m && m.status === 'ready');
  if (!ready.length) { store.toast('Import some media first. Opus builds the edit from your library.', 'error'); return; }
  const effort = d.effort;
  const cfg = EFFORTS[effort];
  const brief = d.brief.trim();
  ctl = new AbortController();
  turns = [];
  const steps: DirectorStep[] = [
    { id: 'media', label: 'Read the media', state: 'wait' },
    { id: 'sheets', label: 'Make contact sheets', state: 'wait' },
    { id: 'plan', label: 'Opus plans the edit', state: 'wait' },
    { id: 'apply', label: 'Apply and check', state: 'wait' },
    ...Array.from({ length: cfg.reviews }, (_, i) => ({ id: `review${i + 1}`, label: `Opus reviews the render${cfg.reviews > 1 ? ` (${i + 1}/${cfg.reviews})` : ''}`, state: 'wait' as const })),
  ];
  store.setDirector({ running: true, steps, streamChars: 0 });
  say({ role: 'user', text: brief || 'Make an edit from my media.' });
  const startDepth = store.historyDepth;
  let total = 0;
  const allIssues: string[] = [];
  try {
    step('media', { state: 'run', detail: 'waiting for thumbnails and sound analysis' });
    await whenMediaIdle(180000);
    step('media', { state: 'done', detail: `${ready.length} file${ready.length > 1 ? 's' : ''}` });

    step('sheets', { state: 'run' });
    const maxImg = d.images ? Math.min(cfg.images, d.maxImages || cfg.images) : 0;
    const sheets = maxImg ? await mediaSheets(maxImg, cfg.cells, ctl.signal, msg => step('sheets', { detail: msg })) : [];
    step('sheets', { state: sheets.length ? 'done' : 'skip', detail: sheets.length ? `${sheets.length} image${sheets.length > 1 ? 's' : ''}` : 'images not available here' });

    step('plan', { state: 'run', detail: 'thinking…' });
    const base = store.state.project;
    const ctx = contextBlock(base, sheets.map(x => x.caption));
    const request = `USER REQUEST\n${brief || 'No specific request: make the best edit you can from this media.'}\n\nBuild the edit now. Start with {"op":"clear"} unless the request asks you to keep the current timeline.`;
    turns = [{ role: 'user', content: ctx }, { role: 'user', content: request }];
    const r1 = await ask(turns, sheets, effort, 'plan');
    const plan = parseReply(r1.text);
    if (!plan) throw { code: 'invalid_json' };
    turns.push({ role: 'assistant', content: r1.text });
    step('plan', { state: 'done', detail: `${plan.ops.length} operations${r1.truncated ? ' (cut short)' : ''}` });

    step('apply', { state: 'run' });
    let res = applyOps(store.state.project, plan.ops, store.state.media);
    store.replace(res.project);
    total += res.applied;
    allIssues.push(...res.issues);
    step('apply', { state: 'done', detail: `${res.applied} applied${res.issues.length ? `, ${res.issues.length} adjusted` : ''}` });
    let lastMessage = plan.message;

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
        rSheets.length ? `IMAGES attached to this message: ${rSheets.map((x, i) => `${i + 1}. ${x.caption}`).join('; ')}` : 'No rendered frames are attached.',
        'The CURRENT TIMELINE in the first message is the edit after your operations. Check it against the request and your plan. Reply with operations that fix or improve it, or {"message": "...", "ops": []} if it is ready. Do not start with clear unless you are rebuilding everything.',
      ].join('\n\n');
      turns.push({ role: 'user', content: reviewMsg });
      // fresh context: the current timeline, and a note that the media sheets are not re-sent
      const ctxNow = contextBlock(p, [], sheets.length ? 'Contact sheets of the media were attached to the first request and are not repeated. The images attached to the latest message are frames rendered from the edit as it stands now, labelled with timeline time.' : undefined);
      const rk = await ask([{ role: 'user', content: ctxNow }, ...turns.slice(1)], rSheets, effort, id);
      const rev = parseReply(rk.text);
      if (!rev) throw { code: 'invalid_json' };
      turns.push({ role: 'assistant', content: rk.text });
      if (rev.ops.length) {
        res = applyOps(store.state.project, rev.ops, store.state.media);
        store.replace(res.project);
        total += res.applied;
        allIssues.push(...res.issues);
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
    const { code, text } = errText(e);
    const cur = store.state.director.steps.find(x => x.state === 'run');
    if (cur) step(cur.id, { state: 'error', detail: code === 'cancelled' ? 'stopped' : code });
    if (code !== 'cancelled') say({ role: 'note', text, undoTo: store.historyDepth > startDepth ? startDepth : undefined });
    else say({ role: 'note', text: 'Stopped.', undoTo: store.historyDepth > startDepth ? startDepth : undefined });
    if (HIDE.has(code)) store.setDirector({ available: 'no', unavailableReason: text });
  } finally {
    store.setDirector({ running: false });
    ctl = null;
  }
}

/** Follow-up instruction in the chat ("make the intro faster"). Sees fresh frames of the edit. */
export async function refineEdit(message: string) {
  const d = store.state.director;
  const text = message.trim();
  if (!text || d.running || !sample) return;
  const effort = d.effort;
  const cfg = EFFORTS[effort];
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
    if (maxImg && (!turns.length || !hasEdit)) {
      const media = await mediaSheets(Math.max(1, maxImg - sheets.length), cfg.cells, ctl.signal);
      sheets = [...sheets, ...media];
    }
    step('look', { state: sheets.length ? 'done' : 'skip', detail: sheets.length ? `${sheets.length} image${sheets.length > 1 ? 's' : ''}` : 'no images' });
    step('plan', { state: 'run', detail: 'thinking…' });
    const ctx = contextBlock(p, sheets.map(x => x.caption));
    // keep the conversation short: instructions + the last few exchanges + the new request
    const history = turns.filter(t => t.role === 'assistant' || !t.content.startsWith('You are the editor')).slice(-6);
    const input: { role: 'user' | 'assistant'; content: string }[] = [
      { role: 'user', content: ctx },
      ...history,
      { role: 'user', content: `USER REQUEST\n${text}\n\nChange the current timeline to do this. Keep everything else as it is unless the request says otherwise.` },
    ];
    const r = await ask(input, sheets, effort, 'plan');
    const plan = parseReply(r.text);
    if (!plan) throw { code: 'invalid_json' };
    step('plan', { state: 'done', detail: `${plan.ops.length} operations` });
    step('apply', { state: 'run' });
    const res = applyOps(store.state.project, plan.ops, store.state.media);
    if (plan.ops.length) store.replace(res.project);
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
