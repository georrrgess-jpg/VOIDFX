// Presets, standards and the AI database: stored in this browser and read by the Opus Director.
import { BENCHMARKS } from '../ai/knowledge';
import { analyseAudioBlob, detectKind, detectShots, probeBlob } from '../media/library';
import { Effort, store } from './store';
import { idbAll, idbDel, idbGet, idbPut, saveBlob, collectGarbage, blobKeyFor } from './storage';
import { MediaKind } from './types';
import { uid } from './util';

// ---------- presets ----------

export interface Preset {
  id: string;
  name: string;
  description: string;
  /** The standing instruction sent with every edit made from this preset. */
  prompt: string;
  effort: Effort;
  aspect: string;
  fps: number;
  duration: [number, number];
  /** Include the voidfx house rules. */
  houseRules: boolean;
  /** Standards (ids) to show Opus as the bar. */
  standards: string[];
  /** Database tags this preset draws from when Opus picks material. */
  libraryTags: string[];
  accent: string;
  builtIn?: boolean;
  updated: number;
}

export const BUILTIN_PRESETS: Preset[] = [
  {
    id: 'voidfx-dexter', name: 'VOIDFX · Dexter', accent: '#ff2b3a', builtIn: true, updated: 0,
    description: 'A Dexter edit at the voidfx standard: a concept from his world, set pieces, dense themed transitions, the logo once, a seamless loop.',
    prompt: 'Make a Dexter edit at the voidfx standard. Find one concept in Dexter\'s world (kill room, plastic, blood slides, tools, the Code, Harry, the Dark Passenger, his victims) or in the song\'s own words, and carry it through the look, the transitions, the text, the sound and the loop. Use the strongest part of the song with the drop at about 40% of the edit. Build at least three multi-stage set pieces (drop, hook, loop) plus one focal set piece, about one designed transition per second, the voidfx logo transition once, a speed ramp on every montage shot, the beat camera through the drums, a sound for every transition, and captions in the house style only on sung or spoken words. Dark, tense, stylish and intense; never soft or pretty.',
    effort: 'extra', aspect: '9:16', fps: 60, duration: [20, 26], houseRules: true,
    standards: ['bm-v105', 'bm-v104', 'bm-v103', 'bm-v7', 'bm-v6', 'bm-v4', 'bm-v9'], libraryTags: ['dexter'],
  },
  {
    id: 'voidfx-flash', name: 'VOIDFX · The Flash', accent: '#ffb000', builtIn: true, updated: 0,
    description: 'Lightning, the Speed Force and the rivalry: the v10/v11 motion standard with a focal set piece and an exact loop.',
    prompt: 'Make a Flash edit at the voidfx standard. Take the concept from the song\'s own words or the character\'s history (the Speed Force, the emblem, the Reverse-Flash rivalry), with red-vs-gold or another fresh look of its own. Motion is the priority: a speed burst on every beat with slow motion between, the camera punching and kicking on the beat, lightning-strike (bolt) transitions with the zap sound where the footage has lightning or a burst of speed, time-freeze holds (speed keyframes near 0.05) that burst back into motion, warp and whip transitions through the Speed Force, one focal set piece, the voidfx logo transition once, a sound on every transition, and a loop that lands exactly on frame 0.',
    effort: 'extra', aspect: '9:16', fps: 60, duration: [20, 26], houseRules: true,
    standards: ['bm-v11', 'bm-v10'], libraryTags: ['flash'],
  },
  {
    id: 'voidfx-dialogue', name: 'Dialogue cold open', accent: '#7fd3ff', builtIn: true, updated: 0,
    description: 'Opens on one or two short lines played as one continuous take, then the hook answers them.',
    prompt: 'Open with one or two short spoken lines from the footage that set up the song, played as one continuous take (dissolves between lines, never choppy). Hold the music low under the line, then let the hook answer it on the drop with the biggest transition. Show a line as spoken only where his lips move with it. Let the visuals carry the ending; no exposition.',
    effort: 'extra', aspect: '9:16', fps: 60, duration: [20, 26], houseRules: true,
    standards: ['bm-v4', 'bm-v7'], libraryTags: [],
  },
  {
    id: 'voidfx-lyric', name: 'Lyric-led', accent: '#c084fc', builtIn: true, updated: 0,
    description: 'Captions on every clearly sung line, word by word on the onsets, with picture moments landing on sung words.',
    prompt: 'Lead with the lyrics supplied in the notes. Caption every clearly sung line in the house caption style, two lines at a time, each word easing in on its sung onset (use the strongest hits and the beat grid to place them). Land at least three picture moments on sung words (a transition, a punch or a title that acts out the word). Never caption words that are not sung.',
    effort: 'extra', aspect: '9:16', fps: 60, duration: [20, 26], houseRules: true,
    standards: ['bm-v103', 'bm-v10', 'bm-v9'], libraryTags: [],
  },
  {
    id: 'quick-draft', name: 'Quick draft', accent: '#52d6a0', builtIn: true, updated: 0,
    description: 'A fast first pass to try a song or a concept. Lower effort, one planning pass.',
    prompt: 'Make a quick draft of the edit so the owner can judge the concept and the song section. Keep the house rules, but favour a clear structure over detail.',
    effort: 'medium', aspect: '9:16', fps: 60, duration: [20, 26], houseRules: true,
    standards: [], libraryTags: [],
  },
  {
    id: 'open-brief', name: 'Open brief', accent: '#8b8b9b', builtIn: true, updated: 0,
    description: 'No house rules: Opus follows only your notes. Useful for edits outside the voidfx style.',
    prompt: '', effort: 'high', aspect: '9:16', fps: 30, duration: [10, 60], houseRules: false, standards: [], libraryTags: [],
  },
];

export async function listPresets(): Promise<Preset[]> {
  const custom = await idbAll<Preset>('presets').catch(() => [] as Preset[]);
  const overrides = new Map(custom.map(p => [p.id, p]));
  const merged = BUILTIN_PRESETS.map(b => ({ ...b, ...(overrides.get(b.id) || {}), builtIn: true }));
  return [...merged, ...custom.filter(p => !BUILTIN_PRESETS.some(b => b.id === p.id)).sort((a, b) => b.updated - a.updated)];
}

export async function getPreset(id: string): Promise<Preset> {
  const all = await listPresets();
  return all.find(p => p.id === id) || all[0];
}

export async function savePreset(p: Preset) {
  p.updated = Date.now();
  await idbPut('presets', p.id, p);
  store.set(s => ({ catalogRev: s.catalogRev + 1 }));
}

export async function deletePreset(id: string) {
  await idbDel('presets', id);
  store.set(s => ({ catalogRev: s.catalogRev + 1 }));
}

export function blankPreset(): Preset {
  return { id: uid('pr'), name: 'New preset', description: '', prompt: '', effort: 'extra', aspect: '9:16', fps: 60, duration: [20, 26], houseRules: true, standards: [], libraryTags: [], accent: '#7fd3ff', updated: Date.now() };
}

// ---------- standards ----------

export interface StandardProfile { duration: number; cuts: number; cutsPerSec: number; avgShot: number; bpm: number | null; onBeat: number | null }
export interface Standard {
  id: string;
  name: string;
  kind: 'benchmark' | 'video';
  /** 'general' or the preset ids it applies to. */
  scope: 'general' | string[];
  notes: string;
  quote?: string;
  url?: string;
  blobId?: string;
  poster?: string;
  shots?: [number, number][];
  profile?: StandardProfile;
  state?: 'processing' | 'ready' | 'error';
  progress?: number;
  added: number;
}

export const BUILTIN_STANDARDS: Standard[] = BENCHMARKS.map(b => ({
  id: `bm-${b.id}`, name: `${b.id} ${b.title}`, kind: 'benchmark', scope: 'general',
  notes: `${b.show} x ${b.song}: ${b.verdict}. The reference for ${b.referenceFor}.${b.lessons ? ` Lesson: ${b.lessons}.` : ''}`,
  quote: b.quote, added: 0,
}));

export async function listStandards(): Promise<Standard[]> {
  const user = await idbAll<Standard>('standards').catch(() => [] as Standard[]);
  return [...user.sort((a, b) => b.added - a.added), ...BUILTIN_STANDARDS];
}

export async function saveStandard(s: Standard) {
  await idbPut('standards', s.id, s);
  store.set(st => ({ catalogRev: st.catalogRev + 1 }));
}

export async function deleteStandard(id: string) {
  await idbDel('standards', id);
  store.set(st => ({ catalogRev: st.catalogRev + 1 }));
  void collectGarbage();
}

/** Add a reference edit: store it, find its cuts, tempo and how many cuts land on the beat. */
export async function addStandardVideo(file: File, opts: { name?: string; notes?: string; scope?: Standard['scope']; url?: string }): Promise<Standard | null> {
  const key = await saveBlob(file);
  if (!key) { store.toast('This browser has no room to store that video.', 'error'); return null; }
  const st: Standard = { id: uid('st'), name: opts.name || file.name.replace(/\.[^.]+$/, ''), kind: 'video', scope: opts.scope || 'general', notes: opts.notes || '', url: opts.url, blobId: key, state: 'processing', progress: 0, added: Date.now() };
  await saveStandard(st);
  void (async () => {
    try {
      const meta = await probeBlob(file, file.name);
      st.poster = meta.poster;
      await saveStandard({ ...st });
      const shots = await detectShots(file, f => { st.progress = f * 0.7; void saveStandard({ ...st }); });
      const audio = meta.hasAudio ? await analyseAudioBlob(file).catch(() => null) : null;
      const dur = meta.duration || 0;
      const cuts = shots.slice(1).map(s => s[0]);
      const beats = audio?.analysis.beats || [];
      const onBeat = beats.length && cuts.length ? cuts.filter(c => beats.some(b => Math.abs(b - c) < 0.07)).length / cuts.length : null;
      st.shots = shots;
      st.profile = { duration: dur, cuts: cuts.length, cutsPerSec: dur ? cuts.length / dur : 0, avgShot: shots.length ? dur / shots.length : dur, bpm: audio?.analysis.bpm ?? null, onBeat };
      st.state = 'ready';
      st.progress = 1;
      await saveStandard({ ...st });
    } catch (e) {
      console.warn(e);
      st.state = 'error';
      await saveStandard({ ...st });
    }
  })();
  return st;
}

export function standardsFor(all: Standard[], presetId: string, picked?: string[]): Standard[] {
  if (picked) return all.filter(s => picked.includes(s.id));
  return all.filter(s => s.kind === 'video' && (s.scope === 'general' || (Array.isArray(s.scope) && s.scope.includes(presetId))));
}

// ---------- the AI database (scene packs, clips, music) ----------

export type LibraryRole = 'pack' | 'clip' | 'music' | 'other';
export interface LibraryItem {
  id: string;
  name: string;
  kind: MediaKind;
  role: LibraryRole;
  tags: string[];
  notes: string;
  blobId: string;
  size: number;
  duration: number;
  width: number;
  height: number;
  fps: number;
  hasAudio: boolean;
  poster?: string;
  bpm?: number | null;
  shots?: number;
  state: 'processing' | 'ready' | 'error';
  stage?: string;
  progress?: number;
  added: number;
}

export async function listLibrary(): Promise<LibraryItem[]> {
  return (await idbAll<LibraryItem>('library').catch(() => [] as LibraryItem[])).sort((a, b) => b.added - a.added);
}

async function putItem(it: LibraryItem) {
  await idbPut('library', it.id, it);
  store.set(s => ({ catalogRev: s.catalogRev + 1 }));
}

export async function updateLibraryItem(id: string, patch: Partial<LibraryItem>) {
  const it = await idbGet<LibraryItem>('library', id);
  if (!it) return;
  await putItem({ ...it, ...patch });
}

export async function deleteLibraryItem(id: string) {
  await idbDel('library', id);
  store.set(s => ({ catalogRev: s.catalogRev + 1 }));
  void collectGarbage();
}

function guessRole(name: string, kind: MediaKind, duration: number): LibraryRole {
  if (kind === 'audio') return 'music';
  if (/pack|scenes?|scenepack/i.test(name) || duration > 90) return 'pack';
  return 'clip';
}

function guessTags(name: string): string[] {
  const n = name.toLowerCase();
  const out: string[] = [];
  if (/dexter|doakes|trinity|harry|debra|deb\b|rita|bay ?harbor/.test(n)) out.push('dexter');
  if (/flash|barry|allen|reverse|zoom|speed ?force|thawne/.test(n)) out.push('flash');
  const m = n.match(/s(\d{1,2})/);
  if (m && out.length) out.push(`s${+m[1]}`);
  return out;
}

const ingestQueue: (() => Promise<void>)[] = [];
let ingesting = false;
async function pumpIngest() {
  ingesting = true;
  while (ingestQueue.length) { const j = ingestQueue.shift()!; try { await j(); } catch (e) { console.warn(e); } }
  ingesting = false;
}

/** Add files to the AI database: store them, then probe, find shots and analyse the sound in the background. */
export async function addToLibrary(files: File[] | FileList, defaults: { role?: LibraryRole; tags?: string[] } = {}): Promise<number> {
  // copy now: a file input's live FileList empties when the input is reset
  const list = Array.from(files);
  let n = 0;
  const existing = await listLibrary();
  for (const file of list) {
    const kind = detectKind(file);
    if (!kind) { store.toast(`${file.name} is not a video, audio or image file.`, 'error'); continue; }
    const key = blobKeyFor(file);
    if (existing.some(x => x.blobId === key)) { store.toast(`${file.name} is already in the database.`); continue; }
    const it: LibraryItem = {
      id: uid('lib'), name: file.name.replace(/\.[^.]+$/, ''), kind, role: defaults.role || (kind === 'audio' ? 'music' : 'clip'),
      tags: [...new Set([...(defaults.tags || []), ...guessTags(file.name)])], notes: '', blobId: key, size: file.size,
      duration: 0, width: 0, height: 0, fps: 0, hasAudio: kind !== 'image', state: 'processing', stage: 'Saving', progress: 0, added: Date.now(),
    };
    await putItem(it);
    n++;
    ingestQueue.push(async () => {
      const saved = await saveBlob(file, key);
      if (!saved) { await putItem({ ...it, state: 'error', stage: 'No room to store this file in the browser' }); return; }
      await putItem({ ...it, stage: 'Reading' });
      const meta = await probeBlob(file, file.name);
      const cur: LibraryItem = { ...it, kind: meta.kind, duration: meta.duration || 0, width: meta.width || 0, height: meta.height || 0, fps: meta.fps || 0, hasAudio: !!meta.hasAudio, poster: meta.poster };
      if (!defaults.role) cur.role = guessRole(file.name, cur.kind, cur.duration);
      await putItem({ ...cur, stage: 'Finding shots' });
      const derived: Record<string, unknown> = { poster: meta.poster };
      if (cur.kind === 'video') {
        const shots = await detectShots(file, f => { void updateLibraryItem(it.id, { progress: f * 0.6 }); }).catch(() => []);
        derived.shots = shots;
        cur.shots = shots.length;
      }
      if (cur.hasAudio && (cur.role === 'music' || cur.kind === 'audio' || cur.duration < 600)) {
        await putItem({ ...cur, stage: 'Analysing sound', progress: 0.6 });
        const a = await analyseAudioBlob(file).catch(() => null);
        if (a) { derived.analysis = a.analysis; derived.peaks = a.peaks; cur.bpm = a.analysis.bpm; }
      }
      await idbPut('derived', key, { ...((await idbGet('derived', key)) || {}), ...derived });
      await putItem({ ...cur, state: 'ready', stage: undefined, progress: 1 });
    });
    if (!ingesting) void pumpIngest();
  }
  return n;
}

export function libraryBusy() { return ingesting || ingestQueue.length > 0; }

// ---------- the owner's own standing knowledge (free text, in addition to the house rules) ----------

export async function loadKnowledge() {
  const k = await idbGet<string>('kv', 'knowledge').catch(() => undefined);
  if (typeof k === 'string') store.setDirector({ knowledge: k });
}

export async function saveKnowledge(text: string) {
  store.setDirector({ knowledge: text });
  await idbPut('kv', 'knowledge', text).catch(() => {});
}
