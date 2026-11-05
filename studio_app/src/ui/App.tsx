import { useEffect, useRef, useState } from 'preact/hooks';
import { importFiles } from '../media/library';
import { player } from '../engine/player';
import { normalize } from '../state/ops';
import { newProject, store, useStore } from '../state/store';
import { ASPECTS, Project } from '../state/types';
import { isTextInput, projectDuration } from '../state/util';
import { deleteSelected, duplicateSelected, nudgeSelection, splitAtPlayhead } from './actions';
import { Btn, Icon } from './controls';
import { DirectorPanel } from './DirectorPanel';
import { ChecksPanel } from './ChecksPanel';
import { Composer, CritiqueModal } from './ai/Composer';
import { ActivityButton } from './ai/Activity';
import { KebabMenu } from './Menu';
import { Palette } from './Palette';
import { projectMenu } from './ai/actions';
import { activeJobFor, stopJob } from '../ai/jobs';
import { getRecord, ProjectRecord } from '../state/projects';
import { refreshChecks } from '../ai/checkrunner';
import { Home } from './home/Home';
import { closeToHome, createProject } from '../state/projects';
import { LOGO_URL } from '../engine/logo';
import { ExportDialog } from './ExportDialog';
import { Inspector } from './Inspector';
import { LeftPanel, Rail } from './LeftPanel';
import { saveFile } from './save';
import { Timeline } from './Timeline';
import { Viewer } from './Viewer';

export function App() {
  const view = useStore(s => s.view);
  const toasts = useStore(s => s.toasts);
  return (
    <>
      {view === 'home' ? <Home /> : <Editor />}
      <Composer />
      <CritiqueModal />
      <Palette />
      <div class="toasts" aria-live="polite">{toasts.map(t => (
        <div class={`toast t-${t.kind}${t.action ? ' has-act' : ''}`}>
          <span>{t.text}</span>
          {t.action && <button type="button" class="toast-act" onClick={() => { t.action!.run(); store.set(s => ({ toasts: s.toasts.filter(x => x.id !== t.id) })); }}>{t.action.label}</button>}
        </div>
      ))}</div>
    </>
  );
}

function Editor() {
  const [dragging, setDragging] = useState(false);
  const [tlH, setTlH] = useState(() => {
    try { return Math.max(180, Math.min(600, +(localStorage.getItem('voidfx.tlh') || 300))); } catch { return 300; }
  });
  // keyboard shortcuts
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (isTextInput(e.target)) return;
      const mod = e.metaKey || e.ctrlKey;
      const k = e.key;
      if (k === ' ' || e.code === 'Space') { e.preventDefault(); player.toggle(); return; }
      if (mod && (k === 'z' || k === 'Z')) { e.preventDefault(); player.pause(); if (e.shiftKey) store.redo(); else store.undo(); return; }
      if (mod && (k === 'y' || k === 'Y')) { e.preventDefault(); store.redo(); return; }
      if (mod && (k === 'd' || k === 'D')) { e.preventDefault(); duplicateSelected(); return; }
      if (mod && (k === 'b' || k === 'B')) { e.preventDefault(); splitAtPlayhead(); return; }
      if (mod && (k === 'a' || k === 'A')) { e.preventDefault(); store.set({ selection: store.state.project.clips.map(c => c.id) }); return; }
      if (mod && (k === 'e' || k === 'E')) { e.preventDefault(); store.set({ exportOpen: true }); return; }
      if (mod) return;
      const fps = store.state.project.fps;
      switch (k) {
        case 's': case 'S': splitAtPlayhead(); break;
        case 'Delete': case 'Backspace': e.preventDefault(); deleteSelected(); break;
        case 'ArrowLeft': e.preventDefault(); if (e.altKey) nudgeSelection(-1 / fps); else player.seek(player.time - (e.shiftKey ? 1 : 1 / fps)); break;
        case 'ArrowRight': e.preventDefault(); if (e.altKey) nudgeSelection(1 / fps); else player.seek(player.time + (e.shiftKey ? 1 : 1 / fps)); break;
        case 'Home': e.preventDefault(); player.seek(0); break;
        case 'End': e.preventDefault(); player.seek(projectDuration(store.state.project)); break;
        case 'Escape': store.set({ selection: [] }); break;
        case '=': case '+': store.set({ zoom: Math.min(800, store.state.zoom * 1.4) }); break;
        case '-': case '_': store.set({ zoom: Math.max(2, store.state.zoom / 1.4) }); break;
        default: return;
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  // drop files anywhere to import
  useEffect(() => {
    let depth = 0;
    const hasFiles = (e: DragEvent) => !!e.dataTransfer && Array.from(e.dataTransfer.types).includes('Files');
    const enter = (e: DragEvent) => { if (hasFiles(e)) { depth++; setDragging(true); } };
    const leave = (e: DragEvent) => { if (hasFiles(e)) { depth = Math.max(0, depth - 1); if (!depth) setDragging(false); } };
    const over = (e: DragEvent) => { if (hasFiles(e)) e.preventDefault(); };
    const drop = (e: DragEvent) => {
      if (!hasFiles(e)) return;
      e.preventDefault();
      depth = 0;
      setDragging(false);
      if (e.dataTransfer?.files.length) void importFiles(e.dataTransfer.files);
    };
    window.addEventListener('dragenter', enter);
    window.addEventListener('dragleave', leave);
    window.addEventListener('dragover', over);
    window.addEventListener('drop', drop);
    return () => {
      window.removeEventListener('dragenter', enter);
      window.removeEventListener('dragleave', leave);
      window.removeEventListener('dragover', over);
      window.removeEventListener('drop', drop);
    };
  }, []);

  // resizable timeline
  const onSplitter = (e: PointerEvent) => {
    const y0 = e.clientY, h0 = tlH;
    const el = e.currentTarget as HTMLElement;
    el.setPointerCapture(e.pointerId);
    const move = (ev: PointerEvent) => setTlH(Math.max(160, Math.min(window.innerHeight - 240, h0 - (ev.clientY - y0))));
    const up = () => {
      el.removeEventListener('pointermove', move);
      el.removeEventListener('pointerup', up);
      try { localStorage.setItem('voidfx.tlh', String(Math.round(tlHRef.current))); } catch { /* ignore */ }
    };
    el.addEventListener('pointermove', move);
    el.addEventListener('pointerup', up);
  };
  const tlHRef = useRef(tlH);
  tlHRef.current = tlH;

  return (
    <div class="app" style={{ '--tl-h': `${tlH}px` } as any}>
      <TopBar />
      <Rail />
      <LeftPanel />
      <main class="center"><Viewer /></main>
      <RightPanel />
      <div class="splitter" role="separator" aria-orientation="horizontal" aria-label="Resize timeline" onPointerDown={onSplitter as any} />
      <section class="bottom"><Timeline /><LockBanner /></section>
      <ExportDialog />
      {dragging && <div class="dropzone"><div><b>Drop to import</b><span>Video, audio and images. Large files are read from disk as needed.</span></div></div>}
    </div>
  );
}

/** While a background round works on this project the editor is read-only; say so where the work happens. */
function LockBanner() {
  const lock = useStore(s => s.lock);
  const pid = useStore(s => s.projectId);
  const jobs = useStore(s => s.jobs);
  if (!lock || !pid) return null;
  const job = activeJobFor(pid);
  const cur = job?.steps.find(x => x.state === 'run');
  const done = job ? job.steps.filter(x => x.state === 'done' || x.state === 'skip').length : 0;
  return (
    <div class="lockbar" role="status">
      <span class="lock-spin" aria-hidden="true" />
      <div class="lock-t"><b>{lock}</b><span>{cur ? `${cur.label}${cur.detail ? ` · ${cur.detail}` : ''}` : 'Starting…'} · step {Math.min(done + 1, job?.steps.length || 1)} of {job?.steps.length || 1}. The timeline updates as it works; editing unlocks when it finishes.</span></div>
      <button type="button" class="chipbtn" onClick={() => store.set({ rightTab: 'director' })}>Progress</button>
      {job && <button type="button" class="chipbtn" onClick={() => stopJob(job.id)}>{Icon.stop}<span>Stop</span></button>}
      <span hidden>{jobs.length}</span>
    </div>
  );
}

function RightPanel() {
  const tab = useStore(s => s.rightTab);
  const sel = useStore(s => s.selection.length);
  const running = useStore(s => !!s.projectId && s.jobs.some(j => j.projectId === s.projectId && j.state === 'running'));
  const bad = useStore(s => s.checks.filter(c => c.status === 'fail' || c.status === 'warn').length);
  const project = useStore(s => s.project);
  const media = useStore(s => s.media);
  // the checkpoint follows every edit (debounced), so the tab badge is current without opening it
  useEffect(() => { const t = setTimeout(() => void refreshChecks(), tab === 'checks' ? 250 : 700); return () => clearTimeout(t); }, [project, media, tab]);
  return (
    <aside class="rp">
      <div class="rp-tabs" role="tablist">
        <button type="button" role="tab" aria-selected={tab === 'director'} class={tab === 'director' ? 'is-on' : ''} onClick={() => store.set({ rightTab: 'director' })}>
          {Icon.spark}<span>Opus</span>{running && <i class="pulse" aria-label="working" />}
        </button>
        <button type="button" role="tab" aria-selected={tab === 'inspector'} class={tab === 'inspector' ? 'is-on' : ''} onClick={() => store.set({ rightTab: 'inspector' })}>
          {Icon.sliders}<span>Edit</span>{sel > 0 && <b class="count">{sel}</b>}
        </button>
        <button type="button" role="tab" aria-selected={tab === 'checks'} class={tab === 'checks' ? 'is-on' : ''} onClick={() => store.set({ rightTab: 'checks' })}>
          {Icon.diamond}<span>Checks</span>{bad > 0 && <b class="count warn">{bad}</b>}
        </button>
      </div>
      <div class="rp-body">{tab === 'director' ? <DirectorPanel /> : tab === 'checks' ? <ChecksPanel /> : <Inspector />}</div>
    </aside>
  );
}

/** The open project's Opus actions (same as the menu's "⋮" on project cards). */
function ProjectKebab() {
  const pid = useStore(s => s.projectId);
  const rev = useStore(s => s.catalogRev);
  useStore(s => s.jobs);
  const clips = useStore(s => s.project.clips.length);
  const [rec, setRec] = useState<ProjectRecord | null>(null);
  useEffect(() => { if (pid) void getRecord(pid).then(r => setRec(r || null)); }, [pid, rev, clips > 0]);
  if (!rec) return null;
  const items = projectMenu({ ...rec, clips }, { inEditor: true }).filter(i => i.label !== 'Export video');
  return <KebabMenu items={items} label="Opus and project actions" />;
}

function TopBar() {
  const name = useStore(s => s.project.name);
  const w = useStore(s => s.project.width);
  const h = useStore(s => s.project.height);
  useStore(s => s.histRev);
  const hasClips = useStore(s => s.project.clips.length > 0);
  const [menu, setMenu] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const aspect = Object.entries(ASPECTS).find(([, [aw, ah]]) => aw === w && ah === h)?.[0] || 'custom';
  const saveProject = () => {
    const s = store.state;
    const data = { app: 'voidfx-studio', v: 1, project: s.project, media: s.mediaOrder.map(id => s.media[id]) };
    void saveFile(`${s.project.name.replace(/[^\w\- ]+/g, '').trim() || 'project'}.voidfx.json`, JSON.stringify(data, null, 1));
    setMenu(false);
  };
  const openProject = async (f: File) => {
    try {
      const data = JSON.parse(await f.text());
      const p: Project = data.project;
      if (!p || !Array.isArray(p.clips) || !Array.isArray(p.tracks)) throw new Error('not a VOIDFX project');
      const media = { ...store.state.media };
      const order = [...store.state.mediaOrder];
      for (const m of data.media || []) if (m?.id && !media[m.id]) { media[m.id] = { ...m, status: 'offline' }; order.push(m.id); }
      store.set({ media, mediaOrder: order });
      store.replace(normalize(p, media));
      store.toast('Project opened. Import its media files to re-link them.', 'ok', 6000);
    } catch (e: any) {
      store.toast(`Could not open the project: ${e?.message || e}`, 'error');
    }
  };
  return (
    <header class="top">
      <button type="button" class="brand" onClick={() => closeToHome()} title="Back to the main menu (your edit is saved)" aria-label="Main menu"><img src={LOGO_URL} alt="voidfx" /><span class="brand-s">Studio</span></button>
      <input class="pname" type="text" value={name} aria-label="Project name" onChange={e => store.commit(p => { p.name = (e.target as HTMLInputElement).value.slice(0, 80) || 'Untitled edit'; })} />
      <span class="top-grow" />
      <label class="aspect">
        <span class="sr">Aspect ratio</span>
        <select value={aspect} onChange={e => { const a = (e.target as HTMLSelectElement).value; const [aw, ah] = ASPECTS[a]; store.commit(p => { p.width = aw; p.height = ah; }); }}>
          {Object.keys(ASPECTS).map(a => <option value={a}>{a}</option>)}
          {aspect === 'custom' && <option value="custom">{w}×{h}</option>}
        </select>
      </label>
      <Btn title="Undo (Ctrl+Z)" disabled={!store.canUndo} onClick={() => store.undo()}>{Icon.undo}</Btn>
      <Btn title="Redo (Ctrl+Shift+Z)" disabled={!store.canRedo} onClick={() => store.redo()}>{Icon.redo}</Btn>
      <div class="menu">
        <Btn title="Project menu" onClick={() => setMenu(!menu)} active={menu}>{Icon.menu}</Btn>
        {menu && (
          <div class="menu-pop" onMouseLeave={() => setMenu(false)}>
            <button type="button" onClick={() => { setMenu(false); closeToHome(); }}>Main menu</button>
            <button type="button" onClick={() => { setMenu(false); void createProject({ name: 'Untitled edit' }); }}>New project</button>
            <button type="button" onClick={() => { store.replace(newProject()); store.set({ selection: [], time: 0 }); player.seek(0); setMenu(false); }}>Clear this timeline</button>
            <button type="button" onClick={saveProject}>Save project file…</button>
            <button type="button" onClick={() => { fileRef.current?.click(); setMenu(false); }}>Open project file…</button>
          </div>
        )}
        <input ref={fileRef} type="file" accept=".json,application/json" hidden onChange={e => { const f = (e.target as HTMLInputElement).files?.[0]; if (f) void openProject(f); (e.target as HTMLInputElement).value = ''; }} />
      </div>
      <ActivityButton variant="top" />
      <ProjectKebab />
      <Btn kind="primary" disabled={!hasClips} onClick={() => store.set({ exportOpen: true })}>{Icon.download}<span>Export</span></Btn>
    </header>
  );
}
