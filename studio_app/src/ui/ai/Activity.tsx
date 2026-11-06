// Background Opus work: what is running, waiting, finished or stopped, with the next action for each.
import { useEffect, useRef, useState } from 'preact/hooks';
import { clearFinishedJobs, dismissJob, jobTitle, markSeen, parallelLimit, resumeJob, setParallelLimit, stopJob } from '../../ai/jobs';
import { openProject } from '../../state/projects';
import { store, useStore } from '../../state/store';
import { Job } from '../../state/types';
import { Icon } from '../controls';
import { timeAgo } from '../home/common';
import { Floating } from '../Menu';
import { openComposer } from './actions';

const KIND_ICON = { create: Icon.spark, revise: Icon.pen, critique: Icon.critic };

// one shared clock for every job display, so timers move every second even while Opus thinks silently
const clockSubs = new Set<() => void>();
let clock = 0;
/** Re-render once a second while `on`; returns the current time. */
export function useNow(on = true): number {
  const [, tick] = useState(0);
  useEffect(() => {
    if (!on) return;
    const f = () => tick(x => x + 1);
    clockSubs.add(f);
    if (!clock) clock = window.setInterval(() => clockSubs.forEach(g => g()), 1000);
    return () => { clockSubs.delete(f); if (!clockSubs.size) { clearInterval(clock); clock = 0; } };
  }, [on]);
  return Date.now();
}
const useTicker = (on: boolean) => useNow(on);

export function elapsed(ms: number) {
  const s = Math.max(0, Math.round(ms / 1000));
  if (s < 60) return `${s}s`;
  if (s < 3600) return `${Math.floor(s / 60)}m ${String(s % 60).padStart(2, '0')}s`;
  return `${Math.floor(s / 3600)}h ${String(Math.floor((s % 3600) / 60)).padStart(2, '0')}m`;
}

/** "1m 20s on this step · 6m 02s in total" for a running job. */
export function jobClock(job: Job, now = Date.now()): string {
  const cur = job.steps.find(s => s.state === 'run');
  const parts: string[] = [];
  if (cur?.t0) parts.push(`${elapsed(now - cur.t0)} on this step`);
  if (job.started) parts.push(`${elapsed(now - job.started)} in total`);
  return parts.join(' · ');
}

/** Where a finished job's time went: the total and its three longest steps. */
export function jobBreakdown(job: Job): string {
  if (!job.started || !job.finished) return '';
  const steps = job.steps.filter(s => s.t0 && s.t1).map(s => ({ l: s.label, ms: s.t1! - s.t0! })).sort((a, b) => b.ms - a.ms).slice(0, 3);
  return `Took ${elapsed(job.finished - job.started)}${steps.length ? `: ${steps.map(s => `${s.l.replace(/^Opus /, '')} ${elapsed(s.ms)}`).join(', ')}` : ''}`;
}

/** How many Opus jobs run at once (on different projects). */
export function ParallelSetting() {
  useStore(s => s.catalogRev);
  const n = parallelLimit();
  return (
    <div class="par" title="Opus can work on several projects at once. Each project's own rounds still run one after another.">
      <span>Run at once</span>
      <div class="seg seg-sm" role="radiogroup" aria-label="Jobs at once">
        {[1, 2, 3].map(v => <button type="button" role="radio" aria-checked={n === v} class={n === v ? 'is-on' : ''} onClick={() => setParallelLimit(v)}>{v}</button>)}
      </div>
    </div>
  );
}

export function JobCard({ job, compact }: { job: Job; compact?: boolean }) {
  const running = job.state === 'running';
  useTicker(running);
  const done = job.steps.filter(s => s.state === 'done' || s.state === 'skip').length;
  const cur = job.steps.find(s => s.state === 'run');
  const frac = job.steps.length ? (done + (cur ? 0.5 : 0)) / job.steps.length : 0;
  const stateLabel = { queued: 'Waiting', running: 'Working', done: 'Ready', error: 'Failed', stopped: 'Stopped', interrupted: 'Interrupted' }[job.state];
  const open = () => { markSeen(job.projectId); void openProject(job.projectId); };
  return (
    <div class={`job j-${job.state} k-${job.kind}${compact ? ' compact' : ''}${job.state === 'done' && !job.seen ? ' unseen' : ''}`}>
      <div class="job-h">
        <span class="job-ic" aria-hidden="true">{KIND_ICON[job.kind]}</span>
        <div class="job-t">
          <b>{job.projectName}</b>
          <span>{jobTitle(job)}</span>
        </div>
        <span class={`job-state s-${job.state}`}>{stateLabel}</span>
        {!running && job.state !== 'queued' && <button type="button" class="job-x" title="Remove from the list" aria-label="Remove from the list" onClick={() => dismissJob(job.id)}>{Icon.close}</button>}
      </div>
      {(running || job.state === 'queued') && (
        <>
          <div class="job-bar" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(frac * 100)}><i style={{ width: `${Math.max(4, frac * 100)}%` }} /></div>
          <p class="job-now">{running ? (cur ? <><b>{cur.label}</b>{cur.detail ? ` · ${cur.detail}` : ''}</> : 'Starting…') : 'Waits for a free slot or for this project\'s earlier job.'}</p>
          {running && <p class="job-clock">{jobClock(job)}</p>}
          {!compact && running && (
            <ol class="job-steps">
              {job.steps.map(s => <li class={`st-${s.state}`}><span class="step-dot" aria-hidden="true" />{s.label}{s.detail && s.state !== 'run' ? <em> · {s.detail}</em> : null}</li>)}
            </ol>
          )}
        </>
      )}
      {job.state === 'done' && job.summary && <p class="job-sum">{job.summary}</p>}
      {job.state === 'done' && !compact && <p class="job-clock">{jobBreakdown(job)}</p>}
      {(job.state === 'error' || job.state === 'interrupted') && <p class="job-err">{job.error || 'The studio was closed while this ran.'}</p>}
      <div class="job-acts">
        {running && <button type="button" class="chipbtn" onClick={() => stopJob(job.id)}>{Icon.stop}<span>Stop</span></button>}
        {job.state === 'queued' && <button type="button" class="chipbtn" onClick={() => stopJob(job.id)}>Cancel</button>}
        {job.state === 'done' && job.kind === 'critique' && <button type="button" class="chipbtn hot" onClick={() => { markSeen(job.projectId); store.set({ critique: { projectId: job.projectId, round: job.round } }); }}>{Icon.diamond}<span>Read the critique</span></button>}
        {job.state === 'done' && job.kind === 'critique' && <button type="button" class="chipbtn" onClick={() => { markSeen(job.projectId); openComposer(job.projectId, 'revise'); }}>{Icon.pen}<span>Write round {job.round + 1}</span></button>}
        {job.state === 'done' && job.kind !== 'critique' && <button type="button" class="chipbtn hot" onClick={open}>{Icon.play}<span>Open</span></button>}
        {(job.state === 'error' || job.state === 'stopped' || job.state === 'interrupted') && <button type="button" class="chipbtn" onClick={() => resumeJob(job.id)}>{Icon.retry}<span>{job.state === 'error' ? 'Retry' : 'Resume'}</span></button>}
        {job.state === 'error' && job.effort !== 'low' && <button type="button" class="chipbtn" title="Run it again one effort level lower" onClick={() => resumeJob(job.id, { lighter: true })}>Retry lighter</button>}
        {!running && job.state !== 'done' && <button type="button" class="chipbtn" onClick={open}>Open project</button>}
        <span class="job-when">{job.finished ? timeAgo(job.finished) : job.started ? `started ${timeAgo(job.started)}` : timeAgo(job.created)}</span>
      </div>
    </div>
  );
}

export function ActivityList({ compact, limit, empty }: { compact?: boolean; limit?: number; empty?: any }) {
  const jobs = useStore(s => s.jobs);
  const order = { running: 0, queued: 1, done: 2, error: 3, interrupted: 4, stopped: 5 };
  const list = [...jobs].sort((a, b) => order[a.state] - order[b.state] || (b.finished || b.created) - (a.finished || a.created)).slice(0, limit || 50);
  if (!list.length) return empty || <p class="muted act-empty">Nothing running. Opus edits, revisions and critiques run here in the background while you keep working.</p>;
  return <div class={`act-list${compact ? ' compact' : ''}`}>{list.map(j => <JobCard job={j} compact={compact} />)}</div>;
}

/** The activity button in the editor's top bar and the menu's sidebar. */
export function ActivityButton({ variant }: { variant: 'top' | 'nav' }) {
  const jobs = useStore(s => s.jobs);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const btn = useRef<HTMLButtonElement>(null);
  const pop = useRef<HTMLDivElement | null>(null);
  const active = jobs.filter(j => j.state === 'running' || j.state === 'queued').length;
  const running = jobs.filter(j => j.state === 'running').length;
  const unseen = jobs.filter(j => j.state === 'done' && !j.seen).length;
  useEffect(() => {
    if (!open) return;
    const outside = (e: PointerEvent) => { if (!ref.current?.contains(e.target as Node) && !pop.current?.contains(e.target as Node)) setOpen(false); };
    const esc = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false); };
    window.addEventListener('pointerdown', outside, true);
    window.addEventListener('keydown', esc);
    return () => { window.removeEventListener('pointerdown', outside, true); window.removeEventListener('keydown', esc); };
  }, [open]);
  const label = active ? `${active} Opus job${active > 1 ? 's' : ''} running` : unseen ? `${unseen} result${unseen > 1 ? 's' : ''} ready` : 'Activity';
  return (
    <div class={`actbtn v-${variant}${open ? ' is-open' : ''}`} ref={ref}>
      <button ref={btn} type="button" class={`actbtn-b${running > 0 ? ' busy' : active ? ' queued' : ''}${unseen ? ' ready' : ''}`} onClick={() => setOpen(!open)} aria-expanded={open} title={label} aria-label={label}>
        {running > 0 && <span class="actbtn-fx" aria-hidden="true"><i /><i /><i /></span>}
        <span class="actbtn-ic" aria-hidden="true">{Icon.bolt}</span>
        {variant === 'nav' && <span class="actbtn-l">Activity</span>}
        {(active > 0 || unseen > 0) && <span class="actbtn-n">{active || unseen}</span>}
      </button>
      {open && (
        <Floating anchor={btn.current} place={variant === 'nav' ? 'beside' : 'below'} align="end" class="actpop" role="dialog" label="Opus activity" popRef={pop}>
          <div class="actpop-h"><b>Opus activity</b>{jobs.some(j => j.state !== 'running' && j.state !== 'queued') && <button type="button" class="linkbtn" onClick={clearFinishedJobs}>Clear finished</button>}</div>
          <ParallelSetting />
          <ActivityList compact />
        </Floating>
      )}
    </div>
  );
}
