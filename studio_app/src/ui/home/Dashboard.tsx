import { LOGO_URL } from '../../engine/logo';
import { listLibrary, listPresets, listStandards } from '../../state/catalog';
import { createProject, listProjects, openProject, ProjectRecord } from '../../state/projects';
import { store } from '../../state/store';
import { Icon } from '../controls';
import { fmtDur, timeAgo, TiltCard, useCatalog } from './common';
import { SECTIONS } from './Home';

export function Dashboard() {
  const [projects] = useCatalog<ProjectRecord[]>(listProjects, []);
  const [counts] = useCatalog(async () => ({ lib: (await listLibrary()).length, std: (await listStandards()).filter(s => s.kind === 'video').length, pre: (await listPresets()).length }), { lib: 0, std: 0, pre: 0 });
  const last = projects[0];
  const tiles = SECTIONS.filter(s => s.id !== 'home');
  const meta: Record<string, string> = {
    create: 'Preset + notes + material',
    projects: `${projects.length} saved`,
    presets: `${counts.pre} presets`,
    library: `${counts.lib} items`,
    standards: `${counts.std} reference edits + 10 benchmarks`,
    rules: 'Trained on 16 edits',
  };
  return (
    <div class="dash">
      <section class="hero">
        <div class="hero-logo"><img src={LOGO_URL} alt="voidfx" /></div>
        <p class="hero-sub">An edit studio with an <b>Opus 5.5</b> director, trained on your system: concept first, set pieces, a transition every second, the logo once, a seamless loop.</p>
        <div class="hero-cta">
          <button type="button" class="cta cta-opus" onClick={() => store.set({ homeTab: 'create' })}>{Icon.spark}<span>Create with Opus</span></button>
          <button type="button" class="cta cta-ice" onClick={() => void createProject({ name: 'Untitled edit' })}>{Icon.plus}<span>New project</span></button>
          {last && <button type="button" class="cta cta-ghost" onClick={() => void openProject(last.id)}>{Icon.play}<span>Continue “{last.name}”</span></button>}
        </div>
      </section>
      {projects.length > 0 && (
        <section class="dash-row">
          <div class="dash-row-h"><h2>Recent projects</h2><button type="button" class="linkbtn" onClick={() => store.set({ homeTab: 'projects' })}>All projects</button></div>
          <div class="recent">
            {projects.slice(0, 6).map((p, i) => (
              <TiltCard class="recent-card" i={i} onClick={() => void openProject(p.id)} label={`Open ${p.name}`}>
                <div class="recent-thumb">{p.thumb ? <img src={p.thumb} alt="" /> : <span class="recent-ph">{Icon.media}</span>}<span class="recent-dur">{fmtDur(p.duration)}</span></div>
                <div class="recent-name">{p.name}</div>
                <div class="recent-meta">{p.clips} clips · {timeAgo(p.updated)}</div>
              </TiltCard>
            ))}
          </div>
        </section>
      )}
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
