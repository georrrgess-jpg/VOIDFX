import { useEffect, useReducer, useRef } from 'preact/hooks';
import { MediaInfo, Project, ASPECTS, Effort, Job, JobStep, Round } from './types';
import { deepClone, uid } from './util';

export type LeftTab = 'media' | 'text' | 'transitions' | 'looks' | 'effects' | 'sounds';
export type RightTab = 'director' | 'inspector' | 'checks';
export type HomeTab = 'home' | 'projects' | 'create' | 'presets' | 'library' | 'standards' | 'rules';

export type DirectorStep = JobStep;
export type { Effort };
export interface DirectorMsg { id: string; role: 'user' | 'opus' | 'note'; text: string; applied?: number; issues?: string[]; model?: string; undoTo?: number }

export interface Lesson { at: number; area: string; severity: 'critical' | 'major'; problem: string; fix: string; project: string }

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
  /** What the critic keeps finding across edits, fed back into every direction and review. */
  lessons: Lesson[];
  presetId: string;
  lastModel?: string;
  streamChars: number;
}

export interface Toast { id: string; text: string; kind: 'info' | 'error' | 'ok'; action?: { label: string; run: () => void } }

/** The round composer: where the owner writes the instructions for the next Opus pass. */
export interface ComposerState { projectId: string; mode: 'create' | 'revise'; focusRound?: number }

export interface AppState {
  view: 'home' | 'editor';
  homeTab: HomeTab;
  projectId: string | null;
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
  /** Bumped when presets, standards or the database change. */
  catalogRev: number;
  /** Latest automated checkpoint for the open project. */
  checks: import('../engine/qc').Check[];
  /** Loop seam difference (0-255 scale), measured on rendered frames. */
  seam: { seam: number; step: number } | null;
  /** Background Opus jobs (builds, revisions, critiques), newest last. */
  jobs: Job[];
  /** Opus rounds of the open project. */
  rounds: Round[];
  /** Set while a background job works on the open project: the editor is read-only. */
  lock: string | null;
  composer: ComposerState | null;
  /** The critique being read: project and round. */
  critique: { projectId: string; round: number } | null;
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
  /** Called (debounced) when the open project changes; set by the projects module. */
  persist: (() => void) | null = null;

  constructor() {
    this.state = {
      view: 'home',
      homeTab: 'home',
      projectId: null,
      project: newProject(),
      media: {},
      mediaOrder: [],
      mediaRev: 0,
      selection: [],
      time: 0,
      playing: false,
      zoom: 90,
      snap: true,
      leftTab: 'media',
      rightTab: 'director',
      toasts: [],
      exportOpen: false,
      histRev: 0,
      previewScale: 0.5,
      catalogRev: 0,
      checks: [],
      seam: null,
      jobs: [],
      rounds: [],
      lock: null,
      composer: null,
      critique: null,
      director: {
        available: 'checking', images: false, maxImages: 0, running: false, steps: [], messages: [],
        effort: 'extra', brief: '', knowledge: '', lessons: [], presetId: 'voidfx-dexter', streamChars: 0,
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

  /** True (and the owner is told) when a background Opus job owns the open project. */
  blocked(): boolean {
    if (!this.state.lock) return false;
    const now = Date.now();
    if (now - this.lastLockToast > 2500) { this.lastLockToast = now; this.toast(`${this.state.lock} The editor unlocks when it finishes.`, 'info', 3500); }
    return true;
  }
  private lastLockToast = 0;

  /** Apply a change to the project as one undoable step. */
  commit(mutate: (p: Project) => void | Project) {
    if (this.blocked()) return;
    const before = this.state.project;
    const draft = deepClone(before);
    const out = mutate(draft) || draft;
    this.pushPast(before);
    this.future = [];
    this.set({ project: out, histRev: this.state.histRev + 1 });
  }

  /** Replace the project as one undoable step (used for Opus edits). Returns the history depth before. */
  replace(next: Project): number {
    if (this.blocked()) return this.past.length;
    return this.replaceAsJob(next);
  }

  /** Replace the project from a background job (bypasses the lock); one undo step. */
  replaceAsJob(next: Project): number {
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
    if (this.state.lock) return;
    if (!this.gestureBase) this.gestureBase = this.state.project;
  }

  /** Change the project without a history step (call between beginGesture and endGesture). */
  live(mutate: (p: Project) => void) {
    if (this.state.lock) return;
    const draft = deepClone(this.state.project);
    mutate(draft);
    this.set({ project: draft });
  }

  /** Live update computed from the gesture's starting project (avoids drift during drags). */
  liveFromBase(mutate: (p: Project) => void) {
    if (this.state.lock) return;
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
    if (this.blocked()) return;
    const prev = this.past.pop();
    if (!prev) return;
    this.future.push(this.state.project);
    this.set({ project: prev, histRev: this.state.histRev + 1, selection: this.state.selection.filter(id => prev.clips.some(c => c.id === id)) });
  }

  redo() {
    if (this.blocked()) return;
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

  toast(text: string, kind: Toast['kind'] = 'info', ms = 3800, action?: Toast['action']) {
    const t: Toast = { id: uid('t'), text, kind, action };
    this.set(s => ({ toasts: [...s.toasts.slice(-3), t] }));
    window.setTimeout(() => this.set(s => ({ toasts: s.toasts.filter(x => x.id !== t.id) })), ms);
  }

  // ---- persistence: the projects module saves the open project to browser storage ----

  private scheduleSave() {
    if (!this.persist || !this.state.projectId) return;
    window.clearTimeout(this.saveTimer);
    this.saveTimer = window.setTimeout(() => this.persist?.(), 700);
  }

  flushSave() {
    window.clearTimeout(this.saveTimer);
    this.persist?.();
  }

  /** Forget undo history (switching projects). */
  resetHistory() {
    this.past = [];
    this.future = [];
    this.gestureBase = null;
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
