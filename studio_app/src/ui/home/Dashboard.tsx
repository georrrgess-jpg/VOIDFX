// The director's desk: the main menu's home. A featured project with its Brief → Build → Critic →
// Revise progress, live Opus activity that flags what needs attention, recent projects and the
// studio's sections.
import { useState } from 'preact/hooks';
import { activeJobFor, jobTitle, markSeen, resumeJob, stopJob } from '../../ai/jobs';
import { listLibrary, listPresets, listStandards } from '../../state/catalog';
import { createProject, listProjects, openProject, ProjectRecord, renameProject } from '../../state/projects';
import { HomeTab, store, useStore } from '../../state/store';
import { Job } from '../../state/types';
import { Icon } from '../controls';
import { KebabMenu } from '../Menu';
import { openComposer, projectMenu, sendToCritic } from '../ai/actions';
import { jobClock, useNow } from '../ai/Activity';
import { fmtDur, timeAgo, useCatalog } from './common';
import { SECTIONS } from './Home';

const KIND_ICON = { create: Icon.spark, revise: Icon.pen, critique: Icon.critic };

/** "The Flash edit" → Continue <i>The Flash</i> edit. */
function FeaturedTitle({ name }: { name: string }) {
  const m = name.match(/^(.*\S)\s+(edit)$/i);
  return <h2 class="feat-t">Continue <i>{m ? m[1] : name}</i>{m ? ` ${m[2]}` : ''}</h2>;
}

function Pipeline({ rec, job }: { rec: ProjectRecord; job?: Job }) {
  const rounds = rec.rounds || [];
  const built = rounds.length > 0 || rec.clips > 0;
  const critiqued = rounds.some(r => r.critique);
  const revised = rounds.some(r => r.kind === 'revise');
  const steps: { k: string; done: boolean; go: () => void; title: string }[] = [
    { k: 'Brief', done: built || !!job, go: () => openComposer(rec.id, built ? 'revise' : 'create'), title: 'Write the brief' },
    { k: 'Build', done: built, go: () => void openProject(rec.id), title: 'Open the edit' },
    { k: 'Critic', done: critiqued, go: () => { const last = [...rounds].reverse().find(r => r.critique); if (last) store.set({ critique: { projectId: rec.id, round: last.n } }); else void sendToCritic(rec.id); }, title: critiqued ? 'Read the critique' : 'Send to the critic' },
    { k: 'Revise', done: revised, go: () => openComposer(rec.id, 'revise'), title: 'Write the next round' },
  ];
  const current = steps.findIndex(s => !s.done);
  return (
    <ol class="pipe" aria-label="Progress">
      {steps.map((s, i) => (
        <li>
          {i > 0 && <span class="pipe-line" aria-hidden="true" />}
          <button type="button" class={`pipe-s${s.done ? ' done' : i === current ? ' now' : ''}`} onClick={s.go} title={s.title} disabled={!!job && i > 0 && !s.done}>
            <span class="pipe-ic" aria-hidden="true">{s.done ? Icon.check : <i />}</span>{s.k}
          </button>
        </li>
      ))}
    </ol>
  );
}

function Featured({ rec }: { rec: ProjectRecord }) {
  useStore(s => s.jobs);
  const job = activeJobFor(rec.id);
  const now = useNow(job?.state === 'running');
  const rounds = rec.rounds || [];
  const last = rounds[rounds.length - 1];
  const cur = job?.steps.find(s => s.state === 'run');
  const sub = job ? `${jobTitle(job)} · ${job.state === 'queued' ? 'waiting' : cur ? cur.label : 'starting'}`
    : last ? `Round ${last.n} · ${last.kind === 'create' ? 'build' : 'revision'}${last.critique ? ` · critic ${last.critique.score}/10` : ''}`
    : rec.clips ? `Edited by hand · ${rec.clips} clip${rec.clips === 1 ? '' : 's'}` : 'Empty project';
  const open = () => { markSeen(rec.id); void openProject(rec.id); };
  return (
    <section class="feat glass" aria-label="Featured project">
      <button type="button" class="feat-thumb" onClick={open} aria-label={`Open ${rec.name}`}>
        {rec.thumb ? <img src={rec.thumb} alt="" /> : <span class="recent-ph">{Icon.media}</span>}
        <span class="feat-dur">{Icon.play}{fmtDur(rec.duration)}</span>
      </button>
      <div class="feat-b">
        <p class="desk-eyebrow">Featured project</p>
        <FeaturedTitle name={rec.name} />
        <p class="feat-sub">{sub}</p>
        {job?.state === 'running' && <p class="feat-clock">{jobClock(job, now)}</p>}
        <button type="button" class="feat-go" onClick={open}>{Icon.play}<span>Continue editing</span><span class="feat-arrow" aria-hidden="true">{Icon.arrowR}</span></button>
        <Pipeline rec={rec} job={job} />
      </div>
    </section>
  );
}

function JobRow({ job }: { job: Job }) {
  const running = job.state === 'running';
  const now = useNow(running);
  const cur = job.steps.find(s => s.state === 'run');
  const label = { queued: 'Waiting', running: 'Working', done: 'Ready', error: 'Failed', stopped: 'Stopped', interrupted: 'Interrupted' }[job.state];
  const msg = job.state === 'error' || job.state === 'interrupted' ? job.error || 'The studio was closed while this ran.'
    : running ? `${cur?.label || 'Starting'}${cur?.detail ? ` · ${cur.detail}` : ''}`
    : job.state === 'queued' ? 'Waits for the job before it.' : job.summary || '';
  const action = job.state === 'error' || job.state === 'interrupted' || job.state === 'stopped'
    ? <button type="button" class="jr-act" onClick={() => resumeJob(job.id)}>{Icon.retry}<span>{job.state === 'error' ? 'Retry' : 'Resume'}</span></button>
    : running || job.state === 'queued' ? <button type="button" class="jr-act" onClick={() => stopJob(job.id)}>{Icon.stop}<span>Stop</span></button>
    : job.kind === 'critique' ? <button type="button" class="jr-act hot" onClick={() => { markSeen(job.projectId); store.set({ critique: { projectId: job.projectId, round: job.round } }); }}>Read</button>
    : <button type="button" class="jr-act hot" onClick={() => { markSeen(job.projectId); void openProject(job.projectId); }}>Open</button>;
  return (
    <div class={`jr j-${job.state} k-${job.kind}`}>
      <span class="jr-ic" aria-hidden="true">{KIND_ICON[job.kind]}</span>
      <div class="jr-t"><b>{job.projectName}</b><span>{jobTitle(job)}</span></div>
      <span class={`job-state s-${job.state}`}>{label}</span>
      {action}
      {msg && <p class="jr-msg">{msg}</p>}
      {running && <p class="jr-clock">{jobClock(job, now)}</p>}
      {running && <div class="jr-bar" aria-hidden="true"><i style={{ width: `${Math.max(5, (job.steps.filter(s => s.state === 'done' || s.state === 'skip').length / Math.max(1, job.steps.length)) * 100)}%` }} /></div>}
    </div>
  );
}

function ActivityCard() {
  const jobs = useStore(s => s.jobs);
  const attention = jobs.filter(j => j.state === 'error' || j.state === 'interrupted');
  const live = jobs.filter(j => j.state === 'running' || j.state === 'queued');
  const order = { running: 0, queued: 1, error: 2, interrupted: 3, done: 4, stopped: 5 };
  const list = [...jobs].sort((a, b) => order[a.state] - order[b.state] || (b.finished || b.created) - (a.finished || a.created)).slice(0, 3);
  return (
    <section class="desk-act glass" aria-label="Activity">
      <header class="desk-h">
        <h2><span aria-hidden="true">{Icon.bolt}</span>Activity</h2>
        {attention.length > 0 ? <span class="desk-badge bad">Needs attention ({attention.length})</span> : live.length > 0 ? <span class="desk-badge live">Live ({live.length})</span> : null}
      </header>
      {list.length ? <div class="jr-list">{list.map(j => <JobRow job={j} />)}</div> : (
        <div class="act-empty">
          <p><b>Nothing running.</b></p>
          <p class="muted">AI edits, critiques and revisions run here in the background. Start one and keep working: you'll get a notice when it's ready.</p>
        </div>
      )}
    </section>
  );
}

function ProjectRow({ p, i }: { p: ProjectRecord; i: number }) {
  useStore(s => s.jobs);
  const [renaming, setRenaming] = useState(false);
  const job = activeJobFor(p.id);
  const rounds = p.rounds || [];
  const crit = [...rounds].reverse().find(r => r.critique)?.critique;
  const open = () => { if (!renaming) { markSeen(p.id); void openProject(p.id); } };
  return (
    <div class="prow" style={{ '--i': i } as any}>
      <button type="button" class="prow-thumb" onClick={open} aria-label={`Open ${p.name}`}>
        {p.thumb ? <img src={p.thumb} alt="" loading="lazy" /> : <span class="recent-ph">{Icon.media}</span>}
        <span class="recent-dur">{fmtDur(p.duration)}</span>
      </button>
      <div class="prow-b">
        {renaming ? (
          <input class="pcard-rename" type="text" value={p.name} autoFocus aria-label="Project name"
            onBlur={e => { void renameProject(p.id, (e.target as HTMLInputElement).value); setRenaming(false); }}
            onKeyDown={e => { e.stopPropagation(); if (e.key === 'Enter') (e.target as HTMLInputElement).blur(); if (e.key === 'Escape') setRenaming(false); }} />
        ) : <button type="button" class="prow-name" onClick={open}>{p.name}</button>}
        <p class="prow-meta">{p.clips ? `${p.clips} clip${p.clips === 1 ? '' : 's'}` : 'empty'} · {timeAgo(p.updated)}</p>
        <div class="prow-tags">
          {job && <span class="ptag busy">{job.state === 'queued' ? 'Waiting' : job.kind === 'critique' ? 'Critic watching' : 'Opus working'}</span>}
          {!job && rounds.length > 0 && <span class="ptag">Round {rounds[rounds.length - 1].n}</span>}
          {!job && crit && <span class={`ptag score s-${crit.score >= 8.5 ? 'hi' : crit.score >= 7 ? 'mid' : 'lo'}`} title={`Critic: ${crit.score}/10`}>{crit.score.toFixed(1)}</span>}
        </div>
      </div>
      <KebabMenu class="prow-k" items={projectMenu(p, { rename: () => setRenaming(true) })} label={`Actions for ${p.name}`} />
    </div>
  );
}

const TILE_META: Record<string, (c: { lib: number; std: number; pre: number }) => string> = {
  presets: c => `${c.pre} presets`,
  library: c => `${c.lib} items`,
  standards: c => `${c.std} reference edits · 10 benchmarks`,
  rules: () => 'Trained on 18 edits',
};

export function Dashboard() {
  const [projects] = useCatalog<ProjectRecord[]>(listProjects, []);
  const [counts] = useCatalog(async () => ({ lib: (await listLibrary()).length, std: (await listStandards()).filter(s => s.kind === 'video').length, pre: (await listPresets()).length }), { lib: 0, std: 0, pre: 0 });
  const jobs = useStore(s => s.jobs);
  const opus = useStore(s => s.director.available);
  // feature the project Opus is working on, else the most recent
  const busyId = jobs.find(j => j.state === 'running' || j.state === 'queued')?.projectId;
  const featured = projects.find(p => p.id === busyId) || projects[0];
  const tiles = SECTIONS.filter(s => s.id in TILE_META);
  const status = opus === 'yes' ? 'Director online' : opus === 'checking' ? 'Connecting to Opus' : 'Director offline in this view';
  return (
    <div class="desk">
      <header class="desk-top">
        <div class="desk-hello">
          <p class="desk-eyebrow"><span class="dotlive on" aria-hidden="true" />VOIDFX Studio — Director's desk</p>
          <h1 class="desk-title">{projects.length ? 'Welcome back.' : 'Welcome to the studio.'}</h1>
          <p class="desk-status"><span class={`dotlive${opus === 'yes' ? ' on' : ''}`} aria-hidden="true" />{status}</p>
        </div>
        <div class="desk-cta">
          <button type="button" class="cta cta-opus" onClick={() => store.set({ homeTab: 'create' })}>{Icon.plus}<span>Create with Opus</span></button>
          <button type="button" class="cta cta-ice" onClick={() => void createProject({ name: 'Untitled edit' })}>{Icon.plus}<span>New project</span></button>
        </div>
      </header>

      <div class="desk-row">
        {featured ? <Featured rec={featured} /> : (
          <section class="feat glass feat-empty">
            <div class="feat-b">
              <p class="desk-eyebrow">Start here</p>
              <h2 class="feat-t">Make your first edit</h2>
              <p class="feat-sub">Pick a preset, add your notes and material, and Opus builds the edit in the background. The critic reviews it; you write the next round.</p>
              <button type="button" class="feat-go" onClick={() => store.set({ homeTab: 'create' })}>{Icon.spark}<span>Create with Opus</span><span class="feat-arrow" aria-hidden="true">{Icon.arrowR}</span></button>
            </div>
          </section>
        )}
        <ActivityCard />
      </div>

      <section class="desk-recent glass" aria-label="Recent projects">
        <header class="desk-h">
          <h2><span aria-hidden="true">{Icon.media}</span>Recent projects</h2>
          {projects.length > 0 && <button type="button" class="desk-link" onClick={() => store.set({ homeTab: 'projects' })}>View all projects<span aria-hidden="true">{Icon.arrowR}</span></button>}
        </header>
        {projects.length ? (
          <div class="prows">{projects.slice(0, 4).map((p, i) => <ProjectRow p={p} i={i} />)}</div>
        ) : <p class="muted desk-none">No projects yet. Create one with Opus, or start a blank project and edit by hand.</p>}
      </section>

      <nav class="desk-tiles" aria-label="Studio sections">
        {tiles.map((s, i) => (
          <button type="button" class="dtile" style={{ '--c': s.tint, '--i': i } as any} onClick={() => store.set({ homeTab: s.id as HomeTab })}>
            <span class="dtile-top">
              <span class="dtile-ic" aria-hidden="true">{s.icon}</span>
              <span class="dtile-t">{s.label}</span>
              <span class="dtile-go" aria-hidden="true">{Icon.arrowR}</span>
            </span>
            <span class="dtile-b">{s.blurb}</span>
            <span class="dtile-m">{TILE_META[s.id](counts)}</span>
          </button>
        ))}
      </nav>
    </div>
  );
}
