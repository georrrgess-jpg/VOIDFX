// Background Opus work: what is running, waiting, finished or stopped, with the next action for each.
import { useEffect, useRef, useState } from 'preact/hooks';
import { clearFinishedJobs, dismissJob, jobTitle, markSeen, resumeJob, stopJob } from '../../ai/jobs';
import { openProject } from '../../state/projects';
import { store, useStore } from '../../state/store';
import { Job } from '../../state/types';
import { Icon } from '../controls';
import { timeAgo } from '../home/common';
import { openComposer } from './actions';

const KIND_ICON = { create: Icon.spark, revise: Icon.pen, critique: Icon.critic };

function useTicker(on: boolean) {
  const [, tick] = useState(0);
  useEffect(() => { if (!on) return; const t = setInterval(() => tick(x => x + 1), 1000); return () => clearInterval(t); }, [on]);
}

export function elapsed(ms: number) {
  const s = Math.max(0, Math.round(ms / 1000));
  return s < 60 ? `${s}s` : `${Math.floor(s / 60)}m ${String(s % 60).padStart(2, '0')}s`;
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
          <p class="job-now">{running ? (cur ? <><b>{cur.label}</b>{cur.detail ? ` · ${cur.detail}` : ''} · {elapsed(Date.now() - (cur.t0 || Date.now()))}</> : 'Starting…') : 'Waits for the job before it.'}</p>
          {!compact && running && (
            <ol class="job-steps">
              {job.steps.map(s => <li class={`st-${s.state}`}><span class="step-dot" aria-hidden="true" />{s.label}{s.detail && s.state !== 'run' ? <em> · {s.detail}</em> : null}</li>)}
            </ol>
          )}
        </>
      )}
      {job.state === 'done' && job.summary && <p class="job-sum">{job.summary}</p>}
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
  const active = jobs.filter(j => j.state === 'running' || j.state === 'queued').length;
  const unseen = jobs.filter(j => j.state === 'done' && !j.seen).length;
  useEffect(() => {
    if (!open) return;
    const outside = (e: PointerEvent) => { if (!ref.current?.contains(e.target as Node)) setOpen(false); };
    const esc = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false); };
    window.addEventListener('pointerdown', outside, true);
    window.addEventListener('keydown', esc);
    return () => { window.removeEventListener('pointerdown', outside, true); window.removeEventListener('keydown', esc); };
  }, [open]);
  const label = active ? `${active} Opus job${active > 1 ? 's' : ''} running` : unseen ? `${unseen} result${unseen > 1 ? 's' : ''} ready` : 'Activity';
  return (
    <div class={`actbtn v-${variant}${open ? ' is-open' : ''}`} ref={ref}>
      <button type="button" class={`actbtn-b${active ? ' busy' : ''}${unseen ? ' ready' : ''}`} onClick={() => setOpen(!open)} aria-expanded={open} title={label} aria-label={label}>
        <span class="actbtn-ic" aria-hidden="true">{Icon.bolt}</span>
        {variant === 'nav' && <span class="actbtn-l">Activity</span>}
        {(active > 0 || unseen > 0) && <span class="actbtn-n">{active || unseen}</span>}
      </button>
      {open && (
        <div class="actpop" role="dialog" aria-label="Opus activity">
          <div class="actpop-h"><b>Opus activity</b>{jobs.some(j => j.state !== 'running' && j.state !== 'queued') && <button type="button" class="linkbtn" onClick={clearFinishedJobs}>Clear finished</button>}</div>
          <ActivityList compact />
        </div>
      )}
    </div>
  );
}
