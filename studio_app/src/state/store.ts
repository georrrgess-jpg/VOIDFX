import { useEffect, useReducer, useRef } from 'preact/hooks';
import { MediaInfo, Project, ASPECTS } from './types';
import { deepClone, uid } from './util';

export type LeftTab = 'media' | 'text' | 'transitions';
export type RightTab = 'director' | 'inspector';

export interface DirectorStep { id: string; label: string; state: 'wait' | 'run' | 'done' | 'error' | 'skip'; detail?: string; t0?: number; t1?: number }
export interface DirectorMsg { id: string; role: 'user' | 'opus' | 'note'; text: string; applied?: number; issues?: string[]; model?: string; undoTo?: number }
export type Effort = 'low' | 'medium' | 'high' | 'extra';

export interface DirectorState {
  available: 'checking' | 'yes' | 'no';
  unavailableReason?: string;
  images: boolean;
  maxImages: number;
  running: boolean;
  steps: DirectorStep[];
  messages: DirectorMsg[];
  effort: Effort;
  brief: string;
  knowledge: string;
  lastModel?: string;
  streamChars: number;
}

export interface Toast { id: string; text: string; kind: 'info' | 'error' | 'ok' }

export interface AppState {
  project: Project;
  media: Record<string, MediaInfo>;
  mediaOrder: string[];
  /** Bumped when runtime media data (thumbnails, peaks) changes. */
  mediaRev: number;
  selection: string[];
  time: number;
  playing: boolean;
  zoom: number;
  snap: boolean;
  leftTab: LeftTab;
  rightTab: RightTab;
  toasts: Toast[];
  exportOpen: boolean;
  director: DirectorState;
  histRev: number;
  previewScale: number;
}

export function newProject(): Project {
  const [w, h] = ASPECTS['9:16'];
  return {
    version: 1,
    id: uid('p'),
    name: 'Untitled edit',
    width: w,
    height: h,
    fps: 30,
    background: '#000000',
    tracks: [
      { id: 'T1', kind: 'text', name: 'Text' },
      { id: 'V2', kind: 'video', name: 'Overlay' },
      { id: 'V1', kind: 'video', name: 'Main', main: true },
      { id: 'A1', kind: 'audio', name: 'Audio' },
      { id: 'A2', kind: 'audio', name: 'Audio 2' },
    ],
    clips: [],
  };
}

type Listener = () => void;

class Store {
  state: AppState;
  private listeners = new Set<Listener>();
  private past: Project[] = [];
  private future: Project[] = [];
  private gestureBase: Project | null = null;
  private saveTimer: number | undefined;

  constructor() {
    this.state = {
      project: newProject(),
      media: {},
      mediaOrder: [],
      mediaRev: 0,
      selection: [],
      time: 0,
      playing: false,
      zoom: 60,
      snap: true,
      leftTab: 'media',
      rightTab: 'director',
      toasts: [],
      exportOpen: false,
      histRev: 0,
      previewScale: 0.5,
      director: {
        available: 'checking', images: false, maxImages: 0, running: false, steps: [], messages: [],
        effort: 'extra', brief: '', knowledge: '', streamChars: 0,
      },
    };
  }

  get project() { return this.state.project; }

  subscribe(fn: Listener) {
    this.listeners.add(fn);
    return () => { this.listeners.delete(fn); };
  }

  private emit() {
    for (const fn of this.listeners) fn();
  }

  set(patch: Partial<AppState> | ((s: AppState) => Partial<AppState>)) {
    const p = typeof patch === 'function' ? patch(this.state) : patch;
    this.state = { ...this.state, ...p };
    this.emit();
    if ('project' in p || 'media' in p || 'director' in p) this.scheduleSave();
  }

  setDirector(patch: Partial<DirectorState>) {
    this.set(s => ({ director: { ...s.director, ...patch } }));
  }

  // ---- history ----

  /** Apply a change to the project as one undoable step. */
  commit(mutate: (p: Project) => void | Project) {
    const before = this.state.project;
    const draft = deepClone(before);
    const out = mutate(draft) || draft;
    this.pushPast(before);
    this.future = [];
    this.set({ project: out, histRev: this.state.histRev + 1 });
  }

  /** Replace the project as one undoable step (used for Opus edits). Returns the history depth before. */
  replace(next: Project): number {
    const depth = this.past.length;
    this.pushPast(this.state.project);
    this.future = [];
    this.set({ project: next, histRev: this.state.histRev + 1 });
    return depth;
  }

  private pushPast(p: Project) {
    this.past.push(p);
    if (this.past.length > 300) this.past.shift();
  }

  /** Start a drag: later `live` updates collapse into one undo step at `endGesture`. */
  beginGesture() {
    if (!this.gestureBase) this.gestureBase = this.state.project;
  }

  /** Change the project without a history step (call between beginGesture and endGesture). */
  live(mutate: (p: Project) => void) {
    const draft = deepClone(this.state.project);
    mutate(draft);
    this.set({ project: draft });
  }

  /** Live update computed from the gesture's starting project (avoids drift during drags). */
  liveFromBase(mutate: (p: Project) => void) {
    const base = this.gestureBase || this.state.project;
    const draft = deepClone(base);
    mutate(draft);
    this.set({ project: draft });
  }

  endGesture() {
    const base = this.gestureBase;
    this.gestureBase = null;
    if (base && base !== this.state.project && JSON.stringify(base) !== JSON.stringify(this.state.project)) {
      this.pushPast(base);
      this.future = [];
      this.set({ histRev: this.state.histRev + 1 });
    }
  }

  cancelGesture() {
    if (this.gestureBase) this.set({ project: this.gestureBase });
    this.gestureBase = null;
  }

  get canUndo() { return this.past.length > 0; }
  get canRedo() { return this.future.length > 0; }
  get historyDepth() { return this.past.length; }

  undo() {
    const prev = this.past.pop();
    if (!prev) return;
    this.future.push(this.state.project);
    this.set({ project: prev, histRev: this.state.histRev + 1, selection: this.state.selection.filter(id => prev.clips.some(c => c.id === id)) });
  }

  redo() {
    const next = this.future.pop();
    if (!next) return;
    this.pushPast(this.state.project);
    this.set({ project: next, histRev: this.state.histRev + 1 });
  }

  /** Undo back to a recorded history depth (used by "Undo Opus edit"). */
  undoTo(depth: number) {
    while (this.past.length > depth) this.undo();
  }

  // ---- toasts ----

  toast(text: string, kind: Toast['kind'] = 'info', ms = 3800) {
    const t: Toast = { id: uid('t'), text, kind };
    this.set(s => ({ toasts: [...s.toasts.slice(-3), t] }));
    window.setTimeout(() => this.set(s => ({ toasts: s.toasts.filter(x => x.id !== t.id) })), ms);
  }

  // ---- persistence (per-viewer convenience; media must be re-linked after reload) ----

  private scheduleSave() {
    window.clearTimeout(this.saveTimer);
    this.saveTimer = window.setTimeout(() => this.save(), 700);
  }

  save() {
    try {
      const s = this.state;
      const media = s.mediaOrder.map(id => s.media[id]).filter(Boolean).map(m => ({ ...m, status: m.status === 'ready' ? 'offline' : m.status }));
      const data = {
        v: 1,
        project: s.project,
        media,
        director: { effort: s.director.effort, brief: s.director.brief, knowledge: s.director.knowledge, messages: s.director.messages.slice(-30) },
      };
      localStorage.setItem('voidfx.studio.v1', JSON.stringify(data));
    } catch { /* storage unavailable or full */ }
  }

  load(): boolean {
    try {
      const raw = localStorage.getItem('voidfx.studio.v1');
      if (!raw) return false;
      const data = JSON.parse(raw);
      if (!data || data.v !== 1 || !data.project || !Array.isArray(data.project.clips)) return false;
      const media: Record<string, MediaInfo> = {};
      const order: string[] = [];
      for (const m of (data.media || []) as MediaInfo[]) {
        if (!m || !m.id) continue;
        media[m.id] = { ...m, status: 'offline' };
        order.push(m.id);
      }
      this.state = {
        ...this.state,
        project: data.project,
        media,
        mediaOrder: order,
        director: {
          ...this.state.director,
          effort: data.director?.effort || 'extra',
          brief: data.director?.brief || '',
          knowledge: data.director?.knowledge || '',
          messages: Array.isArray(data.director?.messages) ? data.director.messages.map((m: any) => ({ ...m, undoTo: undefined })) : [],
        },
      };
      return true;
    } catch {
      return false;
    }
  }

  resetAll() {
    this.past = [];
    this.future = [];
    this.set({ project: newProject(), media: {}, mediaOrder: [], selection: [], time: 0, histRev: this.state.histRev + 1 });
  }
}

export const store = new Store();

/** Subscribe a component to a slice of state. Re-renders when the selected value changes (shallow). */
export function useStore<T>(sel: (s: AppState) => T): T {
  const [, force] = useReducer((x: number) => x + 1, 0);
  const selRef = useRef(sel);
  selRef.current = sel;
  const valRef = useRef<T>(sel(store.state));
  valRef.current = sel(store.state);
  useEffect(() => store.subscribe(() => {
    const next = selRef.current(store.state);
    if (!shallowEqual(next, valRef.current)) {
      valRef.current = next;
      force(0);
    }
  }), []);
  return valRef.current;
}

function shallowEqual(a: any, b: any): boolean {
  if (Object.is(a, b)) return true;
  if (typeof a !== 'object' || typeof b !== 'object' || !a || !b) return false;
  if (Array.isArray(a) !== Array.isArray(b)) return false;
  const ka = Object.keys(a), kb = Object.keys(b);
  if (ka.length !== kb.length) return false;
  for (const k of ka) if (!Object.is(a[k], b[k])) return false;
  return true;
}
