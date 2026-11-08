import { LOGO_URL } from '../../engine/logo';
import { HomeTab, store, useStore } from '../../state/store';
import { Icon } from '../controls';
import { VoidField } from './VoidField';
import { Dashboard } from './Dashboard';
import { ProjectsSection } from './Projects';
import { CreateSection } from './Create';
import { LongformSection } from './Longform';
import { PresetsSection } from './Presets';
import { LibrarySection } from './Library';
import { StandardsSection } from './Standards';
import { RulesSection } from './Rules';
import { ActivityButton } from '../ai/Activity';
import { openPalette } from '../Palette';

export const SECTIONS: { id: HomeTab; label: string; tint: string; tint2: string; icon: any; blurb: string }[] = [
  { id: 'home', label: 'Home', tint: '#7fd3ff', tint2: '#8a5cff', icon: Icon.home, blurb: '' },
  { id: 'create', label: 'AI Edit', tint: '#ffb357', tint2: '#ff2b3a', icon: Icon.spark, blurb: 'Opus builds a complete edit from a preset, your notes and your material.' },
  { id: 'longform', label: 'Long form', tint: '#7fd3ff', tint2: '#52d6a0', icon: Icon.media, blurb: 'A 5-30 minute video edited calmly: trims, chapters, breakdowns of the complicated parts.' },
  { id: 'projects', label: 'Projects', tint: '#7fd3ff', tint2: '#3a6dff', icon: Icon.media, blurb: 'Every edit, saved in this browser with its media.' },
  { id: 'presets', label: 'Presets', tint: '#c084fc', tint2: '#ff5fa2', icon: Icon.sliders, blurb: 'Standing briefs for AI edits. Add notes per edit for its uniqueness.' },
  { id: 'library', label: 'Database', tint: '#52d6a0', tint2: '#2bb3ff', icon: Icon.upload, blurb: 'Scene packs, clips and music Opus can draw from.' },
  { id: 'standards', label: 'Standards', tint: '#ff4d5e', tint2: '#ffb357', icon: Icon.diamond, blurb: 'Reference edits that set the bar, in general or per preset.' },
  { id: 'rules', label: 'House rules', tint: '#cfd6e6', tint2: '#7fd3ff', icon: Icon.text, blurb: 'What Opus has learned about your style, and your own additions.' },
];

export function Home() {
  const tab = useStore(s => s.homeTab);
  const sec = SECTIONS.find(s => s.id === tab) || SECTIONS[0];
  return (
    <div class={`home tab-${tab}`} style={{ '--acc': sec.tint, '--acc2': sec.tint2 } as any}>
      <VoidField tint={sec.tint} tint2={sec.tint2} />
      <nav class="home-nav" aria-label="Studio">
        <button type="button" class="home-brand" onClick={() => store.set({ homeTab: 'home' })} aria-label="VOIDFX Studio home">
          <img src={LOGO_URL} alt="voidfx" />
          <span>STUDIO</span>
        </button>
        <div class="home-links">
          {SECTIONS.map(s => (
            <button type="button" class={`home-link${tab === s.id ? ' is-on' : ''}`} style={{ '--c': s.tint } as any} onClick={() => store.set({ homeTab: s.id })} aria-current={tab === s.id ? 'page' : undefined}>
              <span class="home-link-ic" aria-hidden="true">{s.icon}</span>
              <span>{s.label}</span>
            </button>
          ))}
        </div>
        <ActivityButton variant="nav" />
        <button type="button" class="home-k" onClick={openPalette} title="Jump to anything (Ctrl+K)">{Icon.search}<span>Jump to…</span><kbd>Ctrl K</kbd></button>
        <p class="home-foot">Opus director · everything stays in this browser</p>
      </nav>
      <main class="home-main" key={tab} onPointerMove={spotlight}>
        {tab === 'home' && <Dashboard />}
        {tab === 'projects' && <ProjectsSection />}
        {tab === 'create' && <CreateSection />}
        {tab === 'longform' && <LongformSection />}
        {tab === 'presets' && <PresetsSection />}
        {tab === 'library' && <LibrarySection />}
        {tab === 'standards' && <StandardsSection />}
        {tab === 'rules' && <RulesSection />}
      </main>
    </div>
  );
}

/** Cards marked "spot" carry a light that follows the pointer. */
function spotlight(e: PointerEvent) {
  const el = (e.target as HTMLElement | null)?.closest?.('.spot') as HTMLElement | null;
  if (!el) return;
  const r = el.getBoundingClientRect();
  el.style.setProperty('--mx', `${e.clientX - r.left}px`);
  el.style.setProperty('--my', `${e.clientY - r.top}px`);
}
