import { useState } from 'preact/hooks';
import { createProject, deleteProject, duplicateProject, listProjects, openProject, ProjectRecord, renameProject } from '../../state/projects';
import { store } from '../../state/store';
import { ASPECTS } from '../../state/types';
import { Icon, Seg } from '../controls';
import { fmtDur, SectionHead, timeAgo, TiltCard, useCatalog, useConfirm } from './common';

export function ProjectsSection() {
  const [projects, reload] = useCatalog<ProjectRecord[]>(listProjects, []);
  const [q, setQ] = useState('');
  const [newOpen, setNewOpen] = useState(false);
  const [name, setName] = useState('');
  const [aspect, setAspect] = useState('9:16');
  const [fps, setFps] = useState(60);
  const [confirm, setConfirm] = useConfirm();
  const [editing, setEditing] = useState<string | null>(null);
  const list = projects.filter(p => !q || p.name.toLowerCase().includes(q.toLowerCase()));
  const make = async () => { await createProject({ name: name.trim() || 'Untitled edit', aspect, fps }); };
  return (
    <div class="hs">
      <SectionHead eyebrow="Projects" title="Your edits" text="Each project keeps its timeline, its media and its Opus conversation in this browser."
        right={<button type="button" class="cta cta-ice" onClick={() => setNewOpen(!newOpen)}>{Icon.plus}<span>New project</span></button>} />
      {newOpen && (
        <div class="glass newproj">
          <div class="fld fld-wide"><label class="fld-l" for="np-name">Name</label><input id="np-name" type="text" value={name} placeholder="Untitled edit" onInput={e => setName((e.target as HTMLInputElement).value)} onKeyDown={e => { if (e.key === 'Enter') void make(); }} /></div>
          <div class="fld fld-wide"><span class="fld-l">Aspect</span><Seg value={aspect} onChange={setAspect} options={Object.keys(ASPECTS).map(a => ({ value: a, label: a }))} /></div>
          <div class="fld fld-wide"><span class="fld-l">Frame rate</span><Seg value={fps} onChange={setFps} options={[24, 25, 30, 50, 60].map(v => ({ value: v, label: String(v) }))} /></div>
          <div class="row-end"><button type="button" class="cta cta-ice" onClick={() => void make()}>Create and open</button></div>
        </div>
      )}
      <div class="toolbar-row">
        <input class="search" type="search" placeholder="Search projects" value={q} onInput={e => setQ((e.target as HTMLInputElement).value)} aria-label="Search projects" />
        <span class="muted">{projects.length} project{projects.length === 1 ? '' : 's'}</span>
      </div>
      {!projects.length && (
        <div class="empty glass">
          <p class="empty-t">No projects yet</p>
          <p>Start one by hand, or let Opus build an edit from a preset.</p>
          <div class="row"><button type="button" class="cta cta-opus" onClick={() => store.set({ homeTab: 'create' })}>{Icon.spark}<span>Create with Opus</span></button></div>
        </div>
      )}
      <div class="pgrid">
        {list.map((p, i) => (
          <TiltCard class="pcard" i={i}>
            <button type="button" class="pcard-open" onClick={() => void openProject(p.id)} aria-label={`Open ${p.name}`}>
              <div class={`pcard-thumb a-${p.aspect.replace(':', 'x')}`}>{p.thumb ? <img src={p.thumb} alt="" /> : <span class="recent-ph">{Icon.media}</span>}<span class="recent-dur">{fmtDur(p.duration)}</span></div>
            </button>
            {editing === p.id ? (
              <input class="pcard-rename" type="text" value={p.name} autoFocus aria-label="Project name"
                onBlur={e => { void renameProject(p.id, (e.target as HTMLInputElement).value).then(reload); setEditing(null); }}
                onKeyDown={e => { if (e.key === 'Enter') (e.target as HTMLInputElement).blur(); if (e.key === 'Escape') setEditing(null); }} />
            ) : <div class="pcard-name">{p.name}</div>}
            <div class="pcard-meta">{p.aspect} · {p.clips} clips · {timeAgo(p.updated)}</div>
            <div class="pcard-acts">
              <button type="button" class="chipbtn" onClick={() => void openProject(p.id)}>Open</button>
              <button type="button" class="chipbtn" onClick={() => setEditing(p.id)}>Rename</button>
              <button type="button" class="chipbtn" onClick={() => void duplicateProject(p.id).then(reload)}>Duplicate</button>
              {confirm === p.id
                ? <button type="button" class="chipbtn danger" onClick={() => { setConfirm(null); void deleteProject(p.id).then(reload); }}>Confirm delete</button>
                : <button type="button" class="chipbtn" onClick={() => setConfirm(p.id)}>Delete</button>}
            </div>
          </TiltCard>
        ))}
      </div>
    </div>
  );
}
