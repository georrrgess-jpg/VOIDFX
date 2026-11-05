import { useState } from 'preact/hooks';
import { createProject, listProjects, ProjectRecord } from '../../state/projects';
import { store } from '../../state/store';
import { ASPECTS } from '../../state/types';
import { Icon, Seg } from '../controls';
import { SectionHead, useCatalog } from './common';
import { ProjectCard } from './ProjectCard';

export function ProjectsSection() {
  const [projects] = useCatalog<ProjectRecord[]>(listProjects, []);
  const [q, setQ] = useState('');
  const [newOpen, setNewOpen] = useState(false);
  const [name, setName] = useState('');
  const [aspect, setAspect] = useState('9:16');
  const [fps, setFps] = useState(60);
  const list = projects.filter(p => !q || p.name.toLowerCase().includes(q.toLowerCase()));
  const make = async () => { await createProject({ name: name.trim() || 'Untitled edit', aspect, fps }); };
  return (
    <div class="hs">
      <SectionHead eyebrow="Projects" title="Your edits" text="Each project keeps its timeline, its media, its Opus rounds and the critic's reviews in this browser. The menu on each card has every action: open, the next round, the critic, export, rename, duplicate, delete."
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
        {list.map((p, i) => <ProjectCard p={p} i={i} />)}
      </div>
    </div>
  );
}
