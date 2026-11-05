import { LOGO_URL } from '../../engine/logo';
import { listLibrary, listPresets, listStandards } from '../../state/catalog';
import { createProject, listProjects, openProject, ProjectRecord } from '../../state/projects';
import { store, useStore } from '../../state/store';
import { Icon } from '../controls';
import { ActivityList } from '../ai/Activity';
import { TiltCard, useCatalog } from './common';
import { SECTIONS } from './Home';
import { ProjectCard } from './ProjectCard';

/** How an AI edit moves through the studio; each stage opens where it happens. */
const FLOW = [
  { k: 'Brief', t: 'Pick a preset, add the notes that make this edit yours, attach material or use the database.', icon: Icon.edit, go: 'create' },
  { k: 'Build', t: 'Opus casts, plans and builds the edit in the background. Keep working meanwhile.', icon: Icon.spark, go: 'create' },
  { k: 'Critic', t: 'A harsh review against your standards and the best TikTok edits, with a write-up.', icon: Icon.critic, go: 'standards' },
  { k: 'Revise', t: 'You write round 2: your words plus the critic points you pick. Repeat until it lands.', icon: Icon.pen, go: 'projects' },
] as const;

export function Dashboard() {
  const [projects] = useCatalog<ProjectRecord[]>(listProjects, []);
  const [counts] = useCatalog(async () => ({ lib: (await listLibrary()).length, std: (await listStandards()).filter(s => s.kind === 'video').length, pre: (await listPresets()).length }), { lib: 0, std: 0, pre: 0 });
  const jobs = useStore(s => s.jobs);
  const opus = useStore(s => s.director.available);
  const last = projects[0];
  const running = jobs.filter(j => j.state === 'running' || j.state === 'queued').length;
  const tiles = SECTIONS.filter(s => s.id !== 'home' && s.id !== 'create');
  const meta: Record<string, string> = {
    projects: `${projects.length} saved`,
    presets: `${counts.pre} presets`,
    library: `${counts.lib} items`,
    standards: `${counts.std} reference edits + 10 benchmarks`,
    rules: 'Trained on 16 edits',
  };
  return (
    <div class="dash">
      <section class="hero">
        <p class="hero-kick"><span class={`dotlive${opus === 'yes' ? ' on' : ''}`} aria-hidden="true" />{opus === 'yes' ? 'Opus 5.5 director online' : opus === 'checking' ? 'Connecting to Opus…' : 'Opus offline in this view'}{running ? ` · ${running} job${running > 1 ? 's' : ''} running` : ''}</p>
        <h1 class="hero-logo"><img src={LOGO_URL} alt="voidfx" /><span class="sr">VOIDFX Studio</span></h1>
        <p class="hero-sub">Edits built by an <b>Opus 5.5</b> director trained on your system, judged by a critic that has seen the best of TikTok, and revised until they land.</p>
        <div class="hero-cta">
          <button type="button" class="cta cta-opus cta-lg" onClick={() => store.set({ homeTab: 'create' })}>{Icon.spark}<span>Create with Opus</span></button>
          <button type="button" class="cta cta-ice" onClick={() => void createProject({ name: 'Untitled edit' })}>{Icon.plus}<span>New project</span></button>
          {last && <button type="button" class="cta cta-ghost" onClick={() => void openProject(last.id)}>{Icon.play}<span>Continue “{last.name.length > 22 ? `${last.name.slice(0, 21)}…` : last.name}”</span></button>}
        </div>
      </section>

      <section class="dash-grid">
        <div class="dash-col">
          <div class="dash-row-h"><h2>Recent projects</h2></div>
          {projects.length ? (
            <div class="recent">
              {projects.slice(0, 8).map((p, i) => <ProjectCard p={p} i={i} size="sm" />)}
            </div>
          ) : (
            <div class="empty glass">
              <p class="empty-t">No projects yet</p>
              <p>Create one with Opus, or start a blank project and edit by hand.</p>
            </div>
          )}
        </div>
        <aside class="dash-act glass">
          <div class="dash-row-h"><h2><span class={`dotlive${running ? ' on busy' : ''}`} aria-hidden="true" />Activity</h2></div>
          <ActivityList compact limit={4} empty={
            <div class="act-empty">
              <p><b>Nothing running.</b></p>
              <p class="muted">AI edits, critiques and revisions run here in the background. Start one and keep working: you'll get a notice when it's ready.</p>
            </div>
          } />
        </aside>
      </section>

      <section class="flow" aria-label="How an AI edit runs">
        {FLOW.map((f, i) => (
          <button type="button" class="flow-s" style={{ '--i': i } as any} onClick={() => store.set({ homeTab: f.go as any })}>
            <span class="flow-n">{i + 1}</span>
            <span class="flow-ic" aria-hidden="true">{f.icon}</span>
            <span class="flow-k">{f.k}</span>
            <span class="flow-t">{f.t}</span>
          </button>
        ))}
      </section>

      <section class="dash-row">
        <div class="dash-row-h"><h2>Studio</h2></div>
        <div class="tiles">
          {tiles.map((s, i) => (
            <TiltCard class="tile" i={i} onClick={() => store.set({ homeTab: s.id })} style={{ '--c': s.tint, '--c2': s.tint2 }} label={s.label}>
              <span class="tile-ic" aria-hidden="true">{s.icon}</span>
              <span class="tile-t">{s.label}</span>
              <span class="tile-b">{s.blurb}</span>
              <span class="tile-m">{meta[s.id]}</span>
            </TiltCard>
          ))}
        </div>
      </section>
    </div>
  );
}
