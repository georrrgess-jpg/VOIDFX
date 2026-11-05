// A project card (recent row and the project grid): thumbnail, live Opus status, critic score and a
// "⋮" menu with every action.
import { useState } from 'preact/hooks';
import { activeJobFor, markSeen } from '../../ai/jobs';
import { openProject, ProjectRecord, renameProject } from '../../state/projects';
import { useStore } from '../../state/store';
import { Icon } from '../controls';
import { KebabMenu } from '../Menu';
import { projectMenu } from '../ai/actions';
import { fmtDur, timeAgo, TiltCard } from './common';

export function ProjectCard({ p, i, size }: { p: ProjectRecord; i: number; size?: 'sm' | 'md' }) {
  useStore(s => s.jobs);
  const [renaming, setRenaming] = useState(false);
  const job = activeJobFor(p.id);
  const rounds = p.rounds || [];
  const last = rounds[rounds.length - 1];
  const crit = [...rounds].reverse().find(r => r.critique)?.critique;
  const cur = job?.steps.find(s => s.state === 'run');
  const frac = job && job.steps.length ? job.steps.filter(s => s.state === 'done' || s.state === 'skip').length / job.steps.length : 0;
  const open = () => { if (!renaming) { markSeen(p.id); void openProject(p.id); } };
  return (
    <TiltCard class={`pcard${size === 'sm' ? ' sm' : ''}${job ? ' busy' : ''}`} i={i} onClick={open} label={`Open ${p.name}`}>
      <div class={`pcard-thumb a-${p.aspect.replace(':', 'x')}`}>
        {p.thumb ? <img src={p.thumb} alt="" loading="lazy" /> : <span class="recent-ph">{job ? Icon.spark : Icon.media}</span>}
        <span class="recent-dur">{fmtDur(p.duration)}</span>
        {last && !job && <span class="pbadge round">R{last.n}</span>}
        {crit && !job && <span class={`pbadge score s-${crit.score >= 8.5 ? 'hi' : crit.score >= 7 ? 'mid' : 'lo'}`} title={crit.headline}>{crit.score.toFixed(1)}</span>}
        {job && (
          <span class="pjob">
            <span class="pjob-ring" style={{ '--p': `${Math.max(6, frac * 100)}%` } as any} aria-hidden="true" />
            <span class="pjob-t"><b>{job.state === 'queued' ? 'Waiting' : job.kind === 'critique' ? 'Critic watching' : job.kind === 'create' ? 'Building' : `Round ${job.round}`}</b><em>{cur?.label || 'in the queue'}</em></span>
          </span>
        )}
      </div>
      <div class="pcard-row">
        {renaming ? (
          <input class="pcard-rename" type="text" value={p.name} autoFocus aria-label="Project name" onClick={e => e.stopPropagation()}
            onBlur={e => { void renameProject(p.id, (e.target as HTMLInputElement).value); setRenaming(false); }}
            onKeyDown={e => { e.stopPropagation(); if (e.key === 'Enter') (e.target as HTMLInputElement).blur(); if (e.key === 'Escape') setRenaming(false); }} />
        ) : (
          <div class="pcard-txt">
            <div class="pcard-name">{p.name}</div>
            <div class="pcard-meta">{p.clips ? `${p.clips} clips` : 'empty'} · {timeAgo(p.updated)}</div>
          </div>
        )}
        <KebabMenu items={projectMenu(p, { rename: () => setRenaming(true) })} label={`Actions for ${p.name}`} />
      </div>
    </TiltCard>
  );
}
