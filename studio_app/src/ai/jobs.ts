// Background jobs: Opus builds, revisions and critiques run one at a time in a queue, each on its own
// copy of its project (a Workspace). The owner can leave the editor, open other projects, queue more
// edits or browse the menu while they run; finished work is saved to the project and announced.
// Jobs live as long as this page: closing the studio stops them (they can be resumed).
import { addFileToBay } from '../media/library';
import { getPreset } from '../state/catalog';
import { createProject, getRecord, openProject, setOnProjectOpened } from '../state/projects';
import { idbGet, idbPut } from '../state/storage';
import { store } from '../state/store';
import { Effort, Job, JobKind, JobStep } from '../state/types';
import { uid } from '../state/util';
import { critiqueEdit, criticSteps, issueLine, pathLine } from './critic';
import { buildEdit, errText, HIDE, JobIO, reviseEdit, stepsFor } from './director';
import { Workspace } from './workspace';

const files = new Map<string, File[]>();
/** Jobs running now (one per project at most), with their stop handles. */
const running = new Map<string, AbortController>();

/** How many jobs may run at once (different projects only). Kept in this browser. */
export function parallelLimit(): number {
  try { const v = Number(localStorage.getItem('voidfx.parallel')); if (v >= 1 && v <= 3) return v; } catch { /* storage blocked */ }
  return 2;
}
export function setParallelLimit(n: number) {
  try { localStorage.setItem('voidfx.parallel', String(Math.max(1, Math.min(3, Math.round(n))))); } catch { /* storage blocked */ }
  store.set(s => ({ catalogRev: s.catalogRev + 1 }));
  pump();
}

const LABEL: Record<JobKind, string> = { create: 'Build', revise: 'Revision', critique: 'Critique' };
export function jobTitle(j: Job) {
  return j.kind === 'critique' ? `Critique of round ${j.round}` : j.kind === 'create' ? 'Round 1 · build' : `Round ${j.round} · revision`;
}
export { LABEL as JOB_LABEL };

// ---------- state ----------

function setJobs(jobs: Job[]) {
  store.set({ jobs });
  syncLock();
  syncTitle();
  void persist();
}

export function patchJob(id: string, patch: Partial<Job> | ((j: Job) => Partial<Job>)) {
  setJobs(store.state.jobs.map(j => (j.id === id ? { ...j, ...(typeof patch === 'function' ? patch(j) : patch) } : j)));
}

let persistTimer: number | undefined;
function persist() {
  window.clearTimeout(persistTimer);
  persistTimer = window.setTimeout(() => {
    const keep = store.state.jobs.slice(-60).map(j => ({ ...j, streamChars: undefined }));
    void idbPut('kv', 'jobs', keep).catch(() => undefined);
  }, 400);
}

/** The editor is read-only while a build or revision runs on the project it shows. */
function syncLock() {
  const pid = store.state.projectId;
  const j = pid ? store.state.jobs.find(x => x.state === 'running' && x.projectId === pid && x.kind !== 'critique') : undefined;
  const lock = j ? `Opus is working on ${j.kind === 'create' ? 'this edit' : `round ${j.round} of this edit`} in the background.` : null;
  if (lock !== store.state.lock) store.set({ lock });
}

const BASE_TITLE = document.title || 'VOIDFX Studio';
function syncTitle() {
  const ready = store.state.jobs.filter(j => j.state === 'done' && !j.seen).length;
  const running = store.state.jobs.some(j => j.state === 'running');
  document.title = `${ready ? `(${ready}) ` : running ? '● ' : ''}${BASE_TITLE}`;
}

export async function loadJobs() {
  const saved = (await idbGet<Job[]>('kv', 'jobs').catch(() => undefined)) || [];
  // a page reload stops whatever was running or waiting; those can be resumed
  const jobs = saved.map(j => (j.state === 'running' || j.state === 'queued' ? { ...j, state: 'interrupted' as const, steps: j.steps.map(s => (s.state === 'run' ? { ...s, state: 'error' as const, detail: 'the studio was closed' } : s)) } : j));
  store.set({ jobs });
  syncTitle();
  setOnProjectOpened(() => syncLock());
  window.addEventListener('beforeunload', e => {
    if (store.state.jobs.some(j => j.state === 'running' || j.state === 'queued')) { e.preventDefault(); e.returnValue = ''; }
  });
}

// ---------- queueing ----------

export interface QueueOpts {
  kind: JobKind;
  projectId: string;
  round?: number;
  effort: Effort;
  presetId: string;
  request?: Job['request'];
  brief?: string;
  fromCritic?: string[];
  lyrics?: string;
  follow?: Job['follow'];
  files?: File[];
}

export async function enqueue(o: QueueOpts): Promise<Job | null> {
  if (store.state.director.available !== 'yes') { store.toast(store.state.director.unavailableReason || 'Opus is not available in this view.', 'error', 6000); return null; }
  const rec = await getRecord(o.projectId);
  if (!rec) { store.toast('That project could not be found.', 'error'); return null; }
  const lastRound = (rec.rounds || []).reduce((a, r) => Math.max(a, r.n), 0);
  const round = o.round ?? (o.kind === 'critique' ? Math.max(1, lastRound) : o.kind === 'create' ? 1 : lastRound + 1);
  const job: Job = {
    id: uid('J'), kind: o.kind, projectId: o.projectId, projectName: rec.name, state: 'queued', steps: [], created: Date.now(), round,
    effort: o.effort, presetId: o.presetId, request: o.request, brief: o.brief, fromCritic: o.fromCritic, follow: o.follow, ...(o.lyrics ? { lyrics: o.lyrics } : {}),
  };
  if (o.files?.length) files.set(job.id, o.files);
  job.steps = job.kind === 'critique' ? criticSteps() : stepsFor(job, !!o.files?.length);
  setJobs([...store.state.jobs, job]);
  pump();
  return job;
}

/** Start an AI edit in the background: a new project, the owner's files stored with it, then the build. */
export async function startAiEdit(o: { name: string; presetId: string; effort: Effort; request: NonNullable<Job['request']>; files: File[]; follow: Job['follow'] }): Promise<Job | null> {
  const preset = await getPreset(o.presetId);
  const projectId = await createProject({ name: o.name, aspect: preset.aspect, fps: preset.fps, presetId: preset.id, open: false });
  store.set(s => ({ catalogRev: s.catalogRev + 1 }));
  return enqueue({ kind: 'create', projectId, effort: o.effort, presetId: o.presetId, request: o.request, files: o.files, follow: o.follow });
}

export function stopJob(id: string) {
  const j = store.state.jobs.find(x => x.id === id);
  if (!j) return;
  if (j.state === 'queued') { patchJob(id, { state: 'stopped', finished: Date.now() }); files.delete(id); return; }
  running.get(id)?.abort();
}

const LOWER: Record<Effort, Effort> = { extra: 'high', high: 'medium', medium: 'low', low: 'low' };

/** Run a stopped or failed job again; `lighter` steps its effort down one level first. */
export function resumeJob(id: string, opts: { lighter?: boolean } = {}) {
  const j = store.state.jobs.find(x => x.id === id);
  if (!j || !['error', 'stopped', 'interrupted'].includes(j.state)) return;
  const effort = opts.lighter ? LOWER[j.effort] : j.effort;
  const fresh = j.kind === 'critique' ? criticSteps() : stepsFor({ ...j, effort }, files.has(j.id));
  patchJob(id, { state: 'queued', error: undefined, steps: fresh, started: undefined, finished: undefined, effort });
  pump();
}

export function dismissJob(id: string) {
  setJobs(store.state.jobs.filter(j => j.id !== id || j.state === 'running' || j.state === 'queued'));
}

export function clearFinishedJobs() {
  setJobs(store.state.jobs.filter(j => j.state === 'running' || j.state === 'queued'));
}

export function markSeen(projectId?: string) {
  if (!store.state.jobs.some(j => j.state === 'done' && !j.seen && (!projectId || j.projectId === projectId))) return;
  setJobs(store.state.jobs.map(j => (j.state === 'done' && (!projectId || j.projectId === projectId) ? { ...j, seen: true } : j)));
}

export const jobsFor = (projectId: string) => store.state.jobs.filter(j => j.projectId === projectId);
export const activeJobFor = (projectId: string) => store.state.jobs.find(j => j.projectId === projectId && (j.state === 'running' || j.state === 'queued'));

// ---------- running ----------

/**
 * Start queued jobs while there is room: up to the parallel limit, never two on the same project
 * (a project's rounds stay in order). Each finished job pumps again.
 */
function pump() {
  const limit = parallelLimit();
  for (;;) {
    if (running.size >= limit) return;
    const busy = new Set(store.state.jobs.filter(j => running.has(j.id)).map(j => j.projectId));
    const next = store.state.jobs.find(j => j.state === 'queued' && !busy.has(j.projectId));
    if (!next) return;
    const ctl = new AbortController();
    running.set(next.id, ctl);
    void run(next, ctl).finally(() => { running.delete(next.id); pump(); });
  }
}

async function run(job: Job, ctl: AbortController) {
  patchJob(job.id, { state: 'running', started: Date.now() });
  const step = (sid: string, patch: Partial<JobStep>) => patchJob(job.id, j => ({
    steps: j.steps.map(s => (s.id === sid ? {
      ...s, ...patch,
      // the clock starts when a step starts (not again if it is re-announced) and stops when it ends
      ...(patch.state === 'run' && s.state !== 'run' ? { t0: Date.now(), t1: undefined } : {}),
      ...(patch.state && patch.state !== 'run' && patch.state !== 'wait' ? { t1: Date.now() } : {}),
    } : s)),
  }));
  let lastStream = 0;
  const io: JobIO = {
    step, signal: ctl.signal,
    stream: n => { const now = Date.now(); if (now - lastStream > 250) { lastStream = now; patchJob(job.id, { streamChars: n }); } },
    model: () => undefined,
  };
  let ws: Workspace | null = null;
  try {
    ws = await Workspace.open(job.id, job.projectId);
    patchJob(job.id, { projectName: ws.rec.name });
    const pending = files.get(job.id);
    if (pending?.length) {
      step('files', { state: 'run' });
      let k = 0;
      for (const f of pending) {
        if (ctl.signal.aborted) throw { name: 'AbortError' };
        step('files', { detail: `${++k}/${pending.length} ${f.name}` });
        await addFileToBay(f, ws);
        await ws.save();
      }
      files.delete(job.id);
      step('files', { state: 'done', detail: `${pending.length} file${pending.length > 1 ? 's' : ''}` });
    }
    let summary = '';
    if (job.kind === 'create') summary = (await buildEdit(job, ws, io)).summary;
    else if (job.kind === 'revise') summary = (await reviseEdit(job, ws, io)).summary;
    else {
      const c = await critiqueEdit(job, ws, io);
      summary = `${c.score}/10 · ${c.headline}`;
    }
    const seen = store.state.projectId === job.projectId && store.state.view === 'editor';
    patchJob(job.id, { state: 'done', finished: Date.now(), summary, seen });
    announce(job, summary);
    followUp({ ...job, state: 'done' }, ws);
  } catch (e: any) {
    const { code, text } = errText(e);
    const cancelled = code === 'cancelled' || ctl.signal.aborted;
    const failedAt = store.state.jobs.find(j => j.id === job.id)?.steps.find(s => s.state === 'run')?.label;
    patchJob(job.id, j => ({
      state: cancelled ? 'stopped' : 'error', finished: Date.now(), error: cancelled ? 'Stopped.' : failedAt ? `${failedAt}: ${text}` : text,
      steps: j.steps.map(s => (s.state === 'run' ? { ...s, state: 'error' as const, detail: cancelled ? 'stopped' : code } : s)),
    }));
    if (!cancelled) store.toast(`${job.projectName}: ${text}`, 'error', 8000, { label: 'Open', run: () => void openProject(job.projectId) });
    if (HIDE.has(code)) store.setDirector({ available: 'no', unavailableReason: text });
  } finally {
    ws?.dispose();
    syncLock();
    store.set(s => ({ catalogRev: s.catalogRev + 1 }));
  }
}

function announce(job: Job, summary: string) {
  const name = store.state.jobs.find(j => j.id === job.id)?.projectName || job.projectName;
  const openIt = () => { void openProject(job.projectId); };
  if (job.kind === 'critique') {
    const willRevise = (job.follow?.autoRounds || 0) > 0;
    store.toast(`The critic finished “${name}”: ${summary}${willRevise ? ' Opus revises it next.' : ''}`, 'ok', 9000,
      willRevise ? { label: 'Open', run: openIt } : { label: 'Read it', run: () => store.set({ critique: { projectId: job.projectId, round: job.round } }) });
  } else {
    const critic = job.follow?.critic;
    store.toast(`“${name}” round ${job.round} is ready.${critic ? ' The critic reviews it next.' : ''}`, 'ok', 9000, { label: 'Open', run: openIt });
  }
}

/** The owner's autonomy settings: critic after each round, then automatic revisions from the write-up. */
function followUp(job: Job, ws: Workspace) {
  const f = job.follow;
  if (!f) return;
  if (job.kind !== 'critique' && f.critic) {
    void enqueue({ kind: 'critique', projectId: job.projectId, round: job.round, effort: job.effort, presetId: job.presetId, follow: f });
    return;
  }
  if (job.kind === 'critique' && f.autoRounds > 0) {
    const crit = (ws.rec.rounds || []).find(r => r.n === job.round)?.critique;
    if (!crit) return;
    // every point, minor ones too: each fix the critic can see moves the score
    void enqueue({
      kind: 'revise', projectId: job.projectId, round: job.round + 1, effort: job.effort, presetId: job.presetId,
      brief: `Automatic round: apply the critic's write-up.\n${crit.brief}`, fromCritic: [...(crit.path || []).map(pathLine), ...crit.issues.map(issueLine)],
      follow: { critic: f.critic, autoRounds: f.autoRounds - 1 },
    });
  }
}
