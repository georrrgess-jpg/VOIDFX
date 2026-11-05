// Ctrl/⌘+K: jump anywhere. Sections, projects by name, and Opus actions for the open project.
import { useEffect, useMemo, useRef, useState } from 'preact/hooks';
import { activeJobFor } from '../ai/jobs';
import { closeToHome, createProject, listProjects, openProject, ProjectRecord } from '../state/projects';
import { HomeTab, store, useStore } from '../state/store';
import { Icon } from './controls';
import { openComposer, sendToCritic } from './ai/actions';

interface Cmd { id: string; label: string; group: string; icon: any; hint?: string; run: () => void }

const SECTIONS: [HomeTab, string, any][] = [
  ['home', 'Home', Icon.home], ['create', 'AI Edit: create with Opus', Icon.spark], ['projects', 'Projects', Icon.media],
  ['presets', 'Presets', Icon.sliders], ['library', 'Database', Icon.upload], ['standards', 'Standards', Icon.diamond], ['rules', 'House rules', Icon.text],
];

export function Palette() {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState('');
  const [sel, setSel] = useState(0);
  const [projects, setProjects] = useState<ProjectRecord[]>([]);
  const view = useStore(s => s.view);
  const pid = useStore(s => s.projectId);
  const clips = useStore(s => s.project.clips.length);
  const inRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && (e.key === 'k' || e.key === 'K')) { e.preventDefault(); setOpen(o => !o); }
    };
    const onOpen = () => setOpen(true);
    window.addEventListener('keydown', onKey);
    window.addEventListener('voidfx:palette', onOpen);
    return () => { window.removeEventListener('keydown', onKey); window.removeEventListener('voidfx:palette', onOpen); };
  }, []);
  useEffect(() => {
    if (!open) return;
    setQ(''); setSel(0);
    void listProjects().then(setProjects);
    setTimeout(() => inRef.current?.focus(), 30);
  }, [open]);

  const cmds = useMemo<Cmd[]>(() => {
    const go = (tab: HomeTab) => () => { if (view === 'editor') closeToHome(); store.set({ view: 'home', homeTab: tab }); };
    const out: Cmd[] = [];
    if (view === 'editor' && pid) {
      const busy = !!activeJobFor(pid);
      if (!busy) out.push({ id: 'round', label: clips ? 'Write the next round brief' : 'Build this edit with Opus', group: 'This edit', icon: clips ? Icon.pen : Icon.spark, run: () => openComposer(pid) });
      if (clips && !busy) out.push({ id: 'critic', label: 'Send this edit to the critic', group: 'This edit', icon: Icon.critic, run: () => void sendToCritic(pid) });
      if (clips) out.push({ id: 'export', label: 'Export video', group: 'This edit', icon: Icon.download, hint: 'Ctrl+E', run: () => store.set({ exportOpen: true }) });
      out.push({ id: 'menu', label: 'Back to the main menu', group: 'This edit', icon: Icon.home, run: () => closeToHome() });
    }
    out.push({ id: 'new', label: 'New project', group: 'Create', icon: Icon.plus, run: () => void createProject({ name: 'Untitled edit' }) });
    for (const [tab, label, icon] of SECTIONS) out.push({ id: `s-${tab}`, label, group: 'Go to', icon, run: go(tab) });
    for (const p of projects) if (p.id !== pid || view !== 'editor') out.push({ id: `p-${p.id}`, label: p.name, group: 'Open project', icon: Icon.play, hint: `${p.clips} clips`, run: () => void openProject(p.id) });
    return out;
  }, [projects, view, pid, clips]);

  const words = q.toLowerCase().split(/\s+/).filter(Boolean);
  const shown = cmds.filter(c => words.every(w => `${c.label} ${c.group}`.toLowerCase().includes(w))).slice(0, 40);
  useEffect(() => { setSel(0); }, [q]);
  useEffect(() => { listRef.current?.querySelector('.pal-i.on')?.scrollIntoView({ block: 'nearest' }); }, [sel]);
  if (!open) return null;
  const run = (c?: Cmd) => { if (!c) return; setOpen(false); c.run(); };
  let lastGroup = '';
  return (
    <div class="modal-bg pal-bg" onClick={e => { if (e.target === e.currentTarget) setOpen(false); }}>
      <div class="pal" role="dialog" aria-modal="true" aria-label="Command palette">
        <div class="pal-in">
          <span aria-hidden="true">{Icon.search}</span>
          <input ref={inRef} type="text" autoFocus value={q} placeholder="Jump to a section, a project or an action…" aria-label="Search commands"
            onInput={e => setQ((e.target as HTMLInputElement).value)}
            onKeyDown={e => {
              if (e.key === 'ArrowDown') { e.preventDefault(); setSel(i => Math.min(shown.length - 1, i + 1)); }
              else if (e.key === 'ArrowUp') { e.preventDefault(); setSel(i => Math.max(0, i - 1)); }
              else if (e.key === 'Enter') { e.preventDefault(); run(shown[sel]); }
              else if (e.key === 'Escape') { e.preventDefault(); setOpen(false); }
            }} />
          <kbd>Esc</kbd>
        </div>
        <div class="pal-list" ref={listRef} role="listbox">
          {shown.map((c, i) => {
            const head = c.group !== lastGroup ? <p class="pal-g">{c.group}</p> : null;
            lastGroup = c.group;
            return (
              <>
                {head}
                <button type="button" role="option" aria-selected={i === sel} class={`pal-i${i === sel ? ' on' : ''}`} onMouseMove={() => setSel(i)} onClick={() => run(c)}>
                  <span class="pal-ic" aria-hidden="true">{c.icon}</span>
                  <span class="pal-l">{c.label}</span>
                  {c.hint && <span class="pal-h">{c.hint}</span>}
                </button>
              </>
            );
          })}
          {!shown.length && <p class="muted pal-none">Nothing matches “{q}”.</p>}
        </div>
      </div>
    </div>
  );
}

/** Opens the palette (for a visible button). */
export const openPalette = () => window.dispatchEvent(new Event('voidfx:palette'));
