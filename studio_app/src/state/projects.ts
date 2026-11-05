// Projects: every edit is saved in this browser (IndexedDB) with its media references, so it
// reopens exactly as left. Media files themselves are stored once and shared between projects.
import { player } from '../engine/player';
import { attachStored, clearRuntime } from '../media/library';
import { normalize } from './ops';
import { idbAll, idbDel, idbGet, idbPut, collectGarbage } from './storage';
import { DirectorMsg, newProject, store } from './store';
import { ASPECTS, MediaInfo, Project } from './types';
import { deepClone, projectDuration, uid } from './util';

export interface ProjectRecord {
  id: string;
  name: string;
  created: number;
  updated: number;
  project: Project;
  media: MediaInfo[];
  director: { messages: DirectorMsg[]; effort: string; brief: string; presetId: string };
  thumb?: string;
  duration: number;
  clips: number;
  aspect: string;
  /** Set when the edit was made by Opus from a preset. */
  presetId?: string;
}

export async function listProjects(): Promise<ProjectRecord[]> {
  const all = await idbAll<ProjectRecord>('projects').catch(() => [] as ProjectRecord[]);
  return all.filter(r => r && r.id && r.project).sort((a, b) => b.updated - a.updated);
}

function aspectOf(p: Project) {
  return Object.entries(ASPECTS).find(([, [w, h]]) => w === p.width && h === p.height)?.[0] || `${p.width}x${p.height}`;
}

function recordFromState(): ProjectRecord | null {
  const s = store.state;
  if (!s.projectId) return null;
  const media = s.mediaOrder.map(id => s.media[id]).filter(Boolean).map(m => ({ ...m, status: m.status === 'error' ? 'error' : 'offline' } as MediaInfo));
  const main = s.project.tracks.find(t => t.main);
  const first = s.project.clips.filter(c => c.track === main?.id).sort((a, b) => a.start - b.start)[0];
  const thumb = (first?.media && s.media[first.media]?.poster) || media.find(m => m.poster)?.poster;
  return {
    id: s.projectId,
    name: s.project.name,
    created: 0,
    updated: Date.now(),
    project: s.project,
    media,
    director: { messages: s.director.messages.slice(-40).map(m => ({ ...m, undoTo: undefined })), effort: s.director.effort, brief: s.director.brief, presetId: s.director.presetId },
    thumb,
    duration: projectDuration(s.project),
    clips: s.project.clips.length,
    aspect: aspectOf(s.project),
  };
}

let saving = Promise.resolve();
export function saveCurrent(): Promise<void> {
  const rec = recordFromState();
  if (!rec) return saving;
  saving = saving.then(async () => {
    const prev = await idbGet<ProjectRecord>('projects', rec.id).catch(() => undefined);
    rec.created = prev?.created || Date.now();
    rec.presetId = prev?.presetId ?? rec.presetId;
    await idbPut('projects', rec.id, rec).catch(e => console.warn('project save failed', e));
  });
  return saving;
}

store.persist = () => { void saveCurrent(); };

export async function openProject(id: string): Promise<boolean> {
  const rec = await idbGet<ProjectRecord>('projects', id).catch(() => undefined);
  if (!rec) { store.toast('That project could not be found.', 'error'); return false; }
  if (store.state.projectId && store.state.projectId !== id) await saveCurrent();
  player.reset();
  clearRuntime();
  store.resetHistory();
  const media: Record<string, MediaInfo> = {};
  const order: string[] = [];
  for (const m of rec.media || []) { media[m.id] = { ...m, status: m.blobId ? 'loading' : 'offline' }; order.push(m.id); }
  store.set({
    projectId: rec.id,
    project: normalize(deepClone(rec.project), media),
    media,
    mediaOrder: order,
    selection: [],
    time: 0,
    playing: false,
    view: 'editor',
    rightTab: 'director',
    director: {
      ...store.state.director,
      messages: rec.director?.messages || [],
      effort: (rec.director?.effort as any) || store.state.director.effort,
      brief: rec.director?.brief || '',
      presetId: rec.director?.presetId || store.state.director.presetId,
      steps: [],
      running: false,
    },
  });
  void idbPut('kv', 'lastProject', rec.id);
  await attachStored(rec.media || []);
  return true;
}

export async function createProject(opts: { name?: string; aspect?: string; fps?: number; presetId?: string; open?: boolean } = {}): Promise<string> {
  const p = newProject();
  if (opts.name) p.name = opts.name;
  const [w, h] = ASPECTS[opts.aspect || '9:16'] || ASPECTS['9:16'];
  p.width = w;
  p.height = h;
  p.fps = opts.fps || 60;
  const rec: ProjectRecord = {
    id: uid('P'), name: p.name, created: Date.now(), updated: Date.now(), project: p, media: [],
    director: { messages: [], effort: store.state.director.effort, brief: '', presetId: opts.presetId || store.state.director.presetId },
    duration: 0, clips: 0, aspect: aspectOf(p), presetId: opts.presetId,
  };
  await idbPut('projects', rec.id, rec);
  if (opts.open !== false) await openProject(rec.id);
  return rec.id;
}

export async function renameProject(id: string, name: string) {
  const rec = await idbGet<ProjectRecord>('projects', id);
  if (!rec) return;
  rec.name = name.slice(0, 80) || 'Untitled edit';
  rec.project.name = rec.name;
  rec.updated = Date.now();
  await idbPut('projects', id, rec);
  if (store.state.projectId === id) store.set(s => ({ project: { ...s.project, name: rec.name } }));
}

export async function duplicateProject(id: string): Promise<string | null> {
  const rec = await idbGet<ProjectRecord>('projects', id);
  if (!rec) return null;
  const copy: ProjectRecord = { ...deepClone(rec), id: uid('P'), name: `${rec.name} (copy)`, created: Date.now(), updated: Date.now() };
  copy.project.name = copy.name;
  await idbPut('projects', copy.id, copy);
  return copy.id;
}

export async function deleteProject(id: string) {
  await idbDel('projects', id);
  if (store.state.projectId === id) closeToHome(false);
  void collectGarbage();
}

export function closeToHome(save = true) {
  if (save) store.flushSave();
  player.pause();
  store.set({ view: 'home', homeTab: 'home', selection: [] });
}

/** Bring the single project of the first studio version (kept in localStorage) into the project list. */
export async function migrateLegacy() {
  try {
    const raw = localStorage.getItem('voidfx.studio.v1');
    if (!raw) return;
    const data = JSON.parse(raw);
    if (data?.project?.clips?.length) {
      const p: Project = data.project;
      const rec: ProjectRecord = {
        id: uid('P'), name: p.name || 'Recovered edit', created: Date.now(), updated: Date.now(), project: p,
        media: (data.media || []).map((m: MediaInfo) => ({ ...m, status: 'offline' })),
        director: { messages: data.director?.messages || [], effort: data.director?.effort || 'extra', brief: data.director?.brief || '', presetId: 'voidfx-dexter' },
        duration: projectDuration(p), clips: p.clips.length, aspect: aspectOf(p),
      };
      await idbPut('projects', rec.id, rec);
    }
    localStorage.removeItem('voidfx.studio.v1');
  } catch { /* nothing to migrate */ }
}
