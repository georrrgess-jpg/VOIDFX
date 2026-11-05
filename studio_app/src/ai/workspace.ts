// A background job's own copy of a project: its timeline and its media bay. Jobs never touch the
// editor's state directly; when the project they work on is open in the editor, each step is
// mirrored there (one undo step) so the owner can watch it build.
import { attachStored, MediaBay, registerBay, releaseBay, uiBay } from '../media/library';
import { normalize } from '../state/ops';
import { ensureUniqueMediaIds, getRecord, ProjectRecord, saveCurrent, updateRecord } from '../state/projects';
import { store } from '../state/store';
import { MediaInfo, Project } from '../state/types';
import { deepClone, projectDuration } from '../state/util';
import type { EditCtx } from './sheets';

export class Workspace implements MediaBay {
  readonly key: string;
  readonly thumbs = false;
  rec!: ProjectRecord;
  project!: Project;
  private map: Record<string, MediaInfo> = {};
  private ids: string[] = [];

  private constructor(jobId: string) {
    this.key = `job:${jobId}`;
    registerBay(this);
  }

  /** Load a project for a job. If the editor has it open, its latest state is saved first. */
  static async open(jobId: string, projectId: string): Promise<Workspace> {
    if (store.state.projectId === projectId) await saveCurrent();
    let rec = await getRecord(projectId);
    if (!rec) throw { code: 'no_project', message: 'The project was deleted.' };
    rec = await ensureUniqueMediaIds(rec);
    const ws = new Workspace(jobId);
    ws.rec = rec;
    for (const m of rec.media || []) { ws.map[m.id] = { ...m, status: m.blobId ? 'loading' : 'offline' }; ws.ids.push(m.id); }
    ws.project = normalize(deepClone(rec.project), ws.map);
    return ws;
  }

  // ---- MediaBay ----
  media() { return this.map; }
  order() { return this.ids; }
  add(info: MediaInfo) {
    this.map = { ...this.map, [info.id]: info };
    if (!this.ids.includes(info.id)) this.ids = [...this.ids, info.id];
  }
  patch(id: string, patch: Partial<MediaInfo>) {
    if (!this.map[id]) return;
    this.map = { ...this.map, [id]: { ...this.map[id], ...patch } };
  }

  get ctx(): EditCtx { return { project: this.project, media: this.map, order: this.ids }; }
  get id() { return this.rec.id; }
  get openInEditor() { return store.state.projectId === this.rec.id; }

  /** Bring the project's stored files online for this job (`files` are fresh uploads still in memory). */
  async attach(files?: Map<string, Blob>) {
    await attachStored(this.ids.map(id => this.map[id]), this, files);
  }

  ready(): MediaInfo[] { return this.ids.map(id => this.map[id]).filter(m => m && m.status !== 'error' && m.status !== 'offline'); }

  /** Replace the timeline. Mirrors to the editor when the project is open there. */
  setProject(p: Project) {
    this.project = p;
    if (!this.openInEditor) return;
    const missing = this.ids.filter(id => !store.state.media[id]).map(id => this.map[id]);
    if (missing.length) {
      for (const m of missing) uiBay.add({ ...m, status: m.status === 'ready' ? 'loading' : m.status });
      void attachStored(missing, uiBay);
    }
    store.replaceAsJob(p);
  }

  /** Write the job's state into the project record (and anything else the job changes). */
  async save(extra?: (rec: ProjectRecord) => void) {
    const media = this.ids.map(id => this.map[id]).filter(Boolean).map(m => ({ ...m, status: m.status === 'error' ? 'error' : 'offline' } as MediaInfo));
    const p = this.project;
    const main = p.tracks.find(t => t.main);
    const first = p.clips.filter(c => c.track === main?.id).sort((a, b) => a.start - b.start)[0];
    const thumb = (first?.media && this.map[first.media]?.poster) || media.find(m => m.poster)?.poster;
    const rec = await updateRecord(this.rec.id, r => {
      r.project = p;
      r.media = media;
      r.thumb = thumb || r.thumb;
      r.duration = projectDuration(p);
      r.clips = p.clips.length;
      r.updated = Date.now();
      extra?.(r);
    });
    if (rec) {
      this.rec = rec;
      if (this.openInEditor) store.set({ rounds: rec.rounds || [] });
    }
  }

  dispose() { releaseBay(this.key); }
}
