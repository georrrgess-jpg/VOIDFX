// The Opus Director: builds an edit (round 1) or revises it (later rounds) through the `sample`
// capability. It runs inside a background job on the job's own workspace, so the owner can leave
// the editor, open other projects or queue more edits while it works.
// Build: preset + notes + standards → (cast from the database) → read the media → contact sheets →
// Opus directs (concept, look, shots, set pieces, a scorecard against the critic's canon) → two calls
// write the picture and the layers at the same time → the studio applies, validates and adds missing
// sounds → checkpoint → rendered frames → Opus reviews: quality first, then raising the ceiling.
// Every owner note and critic point is numbered, planned, tagged on the operations that carry it out
// and checked in rendered frames, so nothing the owner asked for is dropped.
import { BENCHMARK_TEXT, HOUSE_RULES } from './knowledge';
import { COOKBOOK, CRAFT, EFFICIENT } from './playbook';
import { EXEMPLARS } from './exemplars';
import { CRITIC_AREAS, CRITIC_CANON } from './canon';
import { checksText, runChecks, Check } from '../engine/qc';
import { cutTimes } from '../engine/evaluate';
import { measureLoopSeam } from '../engine/exporter';
import { attachLibraryItem, whenMediaIdle } from '../media/library';
import { getPreset, lessonsText, LibraryItem, listLibrary, listStandards, Preset, Standard, standardsFor } from '../state/catalog';
import { addTransitionSounds, applyOps as applyOpsRaw, normalize, OpsResult, pruneSfx, snapToBeats } from '../state/ops';
import { customIssues } from '../engine/custom';
import { store } from '../state/store';
import { ASPECTS, Effort, Job, JobStep, MediaInfo, NoteCheck, Project, Round } from '../state/types';
import { deepClone, projectDuration } from '../state/util';
import { ContextExtras, contextBlock, parseJson, parseReply } from './prompt';
import { libraryMosaic, mediaSheets, Sheet, standardSheets, timelineSheets } from './sheets';
import type { Workspace } from './workspace';
import { lyricsText, parseLyrics } from '../state/lyrics';
import type { Lyrics } from '../state/types';

export const MODEL = 'claude-opus-5-5';

/** Apply Opus's operations and report custom effects that will not compile, so the review can fix them. */
function applyOps(base: Project, ops: unknown, media: Record<string, MediaInfo>): OpsResult {
  const res = applyOpsRaw(base, ops, media);
  // the studio's own finishing passes: cuts exactly on the beat, sparse sound design
  const snapped = snapToBeats(res.project, media);
  const pruned = pruneSfx(res.project);
  normalize(res.project, media);
  const notes: string[] = [];
  if (snapped) notes.push(`the studio moved ${snapped} cut${snapped > 1 ? 's' : ''} (by up to 90 ms) exactly onto the beat`);
  if (pruned) notes.push(`the studio removed ${pruned} sound effect${pruned > 1 ? 's' : ''} (stacked within 0.3 s of another, more than two in a second, or over the budget of about three every four seconds)`);
  const bad = customIssues(res.project);
  return { ...res, issues: [...res.issues, ...notes, ...bad] };
}

type SampleFn = ((input: any, opts?: any) => Promise<{ text: string; truncated: boolean; modelTierApplied: string; modelApplied?: string }>) & {
  limits(): Promise<{ maxPromptBytes: number; images?: { maxCount: number; maxInputBytes: number; mediaTypes: string[] } }>;
};

let sample: SampleFn | null = null;
/** Text budget per call (the runtime's limit, less a margin for the request's own framing). */
let promptLimit = 240 * 1024;

/**
 * Each level: how hard Opus thinks on the direction, how many times it reviews rendered frames and at
 * what depth, and how much footage it sees. High and Extra review at full depth: the first review
 * fixes and scores the edit, Extra's second raises it.
 */
export const EFFORTS: Record<Effort, { label: string; effort: 'low' | 'medium' | 'high'; reviews: number; review: Effort; images: number; cells: number; hint: string }> = {
  low: { label: 'Low', effort: 'low', reviews: 0, review: 'low', images: 4, cells: 12, hint: 'Fastest. One planning pass with light thinking.' },
  medium: { label: 'Medium', effort: 'medium', reviews: 0, review: 'medium', images: 8, cells: 16, hint: 'One planning pass with more thinking and the worked examples.' },
  high: { label: 'High', effort: 'high', reviews: 1, review: 'high', images: 12, cells: 16, hint: 'Deep thinking on the direction, then a deep review of rendered frames and the checkpoint.' },
  extra: { label: 'Extra', effort: 'high', reviews: 2, review: 'high', images: 16, cells: 20, hint: 'Deepest: the most footage per call, deep thinking on the direction and two deep reviews of rendered frames (quality, then raising the ceiling).' },
};

export const ERR: Record<string, string> = {
  not_granted: 'Opus is not allowed to run here. Allow Claude for this artifact when asked, then try again.',
  sampling_disabled: 'Claude is not available on this account right now.',
  not_declared: 'This page is not set up to use Claude.',
  capability_disabled: 'Claude is turned off in this view.',
  capability_removed: 'This viewer app is out of date. Reload or update it.',
  session_expired: 'Sign in to Claude again, then retry.',
  rate_limited: 'Too many requests or your usage limit was reached. Wait a little, then retry.',
  refused: 'Opus declined this request. Try rewording it.',
  empty_completion: 'Opus thought for too long and wrote nothing, even on a lighter retry. Press Retry, or use a lower effort for this edit.',
  invalid_json: 'Opus replied in a shape the studio could not read. Retry.',
  prompt_too_large: 'The request was too large. Use fewer database items or shorten the knowledge text.',
  image_rejected: 'A contact sheet was rejected. Try again with fewer files.',
  images_unavailable: 'Images cannot be sent in this view, so Opus worked from the analysis only.',
  upstream_error: 'Could not reach Opus. Check your connection and retry.',
  no_media: 'Add files or database material first. Opus builds the edit from them.',
  no_project: 'The project was deleted.',
  no_edit: 'There is no edit on this project yet. Build one first.',
};
export const HIDE = new Set(['not_granted', 'sampling_disabled', 'not_declared', 'capability_disabled', 'capability_removed']);

export async function initDirector() {
  try {
    const w = window as any;
    sample = w.claude?.use ? await w.claude.use('sample') : null;
  } catch {
    sample = null;
  }
  if (!sample) {
    store.setDirector({ available: 'no', unavailableReason: 'Opus is available when this studio is opened on claude.ai.' });
    return;
  }
  const lim = await sample.limits().catch(() => null);
  if (lim?.maxPromptBytes) promptLimit = Math.max(64 * 1024, Math.min(250 * 1024, lim.maxPromptBytes - 8 * 1024));
  store.setDirector({ available: 'yes', images: !!lim?.images, maxImages: lim?.images?.maxCount ?? 0 });
}

export function directorReady() { return !!sample; }

export function errText(e: any): { code: string; text: string } {
  const code = e?.code || (e?.name === 'AbortError' ? 'cancelled' : 'upstream_error');
  return { code, text: ERR[code] || e?.message || ERR.upstream_error };
}

/** What a job hands the Director: step reporting, cancellation and streaming progress. */
export interface JobIO {
  step(id: string, patch: Partial<JobStep>): void;
  signal: AbortSignal;
  stream(chars: number): void;
  model(m: string): void;
}

export type Turn = { role: 'user' | 'assistant'; content: string };

// ---------- prompt budget ----------

const enc = new TextEncoder();
const bytes = (s: string) => enc.encode(s).length;
export const inputBytes = (input: string | Turn[]) => (typeof input === 'string' ? bytes(input) : input.reduce((n, t) => n + bytes(t.content) + 24, 0));

/** An operations reply as one line: the timeline in the context already shows what it did. */
export function compactReply(text: string): string {
  const r = parseReply(text);
  if (!r || !r.ops.length) return text.length > 8000 ? `${text.slice(0, 8000)}…` : text;
  const v: any = parseJson(text);
  const keep: Record<string, unknown> = { message: r.message };
  if (v && Array.isArray(v.notes)) keep.notes = v.notes;
  if (v && v.scores && typeof v.scores === 'object') keep.scores = v.scores;
  return JSON.stringify({ ...keep, ops: `(${r.ops.length} operations, applied: the CURRENT TIMELINE shows the result)` });
}

/** Keep a request inside the runtime's limit: summarise old operation replies, drop old turns, then trim. */
function fitInput(input: string | Turn[]): string | Turn[] | null {
  if (inputBytes(input) <= promptLimit) return input;
  if (typeof input === 'string') return null;
  const turns = input.map(t => ({ ...t }));
  for (let i = 1; i < turns.length - 1 && inputBytes(turns) > promptLimit; i++) if (turns[i].role === 'assistant') turns[i].content = compactReply(turns[i].content);
  while (turns.length > 5 && inputBytes(turns) > promptLimit) turns.splice(1, 1);
  for (let guard = 0; guard < 8 && inputBytes(turns) > promptLimit; guard++) {
    let k = -1, len = 0;
    for (let i = 1; i < turns.length - 1; i++) if (turns[i].content.length > len) { len = turns[i].content.length; k = i; }
    if (k < 0 || len < 3000) return null;
    const over = inputBytes(turns) - promptLimit;
    turns[k].content = `${turns[k].content.slice(0, Math.max(1500, len - over - 2000))}\n…(shortened to fit)`;
  }
  return inputBytes(turns) <= promptLimit ? turns : null;
}

/** Build a context block that fits next to `reserve` bytes of other turns, dropping the optional extras first. */
function fitContext(make: (x: ContextExtras) => string, x: ContextExtras, reserve = 0): string {
  const lean = [CRAFT, EFFICIENT].join('\n\n');
  const tries: ContextExtras[] = [
    x,
    { ...x, exemplars: '' },
    { ...x, exemplars: '', canon: '' },
    { ...x, exemplars: '', canon: '', craft: lean },
    { ...x, exemplars: '', canon: '', craft: EFFICIENT, benchmarks: '' },
  ];
  let last = '';
  for (const t of tries) {
    last = make(t);
    if (bytes(last) + reserve <= promptLimit) return last;
  }
  return last;
}

export async function ask(io: JobIO, input: string | Turn[], images: Sheet[], effort: Effort, label: string, describe?: (text: string) => string): Promise<{ text: string; model: string; truncated: boolean }> {
  if (!sample) throw { code: 'not_declared' };
  const fitted = fitInput(input);
  if (!fitted) throw { code: 'prompt_too_large' };
  const e = EFFORTS[effort];
  const opts: any = {
    model: MODEL, modelTier: 'complex', effort: e.effort, cache: false, signal: io.signal,
    onText: ({ text }: { text: string }) => {
      io.stream(text.length);
      if (describe) { io.step(label, { detail: describe(text) }); return; }
      const ops = (text.match(/"op"\s*:/g) || []).length;
      io.step(label, { detail: ops ? `writing… ${ops} operations so far` : 'writing…' });
    },
  };
  if (images.length && store.state.director.images) opts.images = images.map(s => s.blob);
  const res = await sample(fitted, opts);
  const model = res.modelApplied || `${res.modelTierApplied} tier`;
  io.model(model);
  store.setDirector({ lastModel: model });
  return { text: res.text, model, truncated: res.truncated };
}

const LIGHTER: Record<Effort, Effort> = { extra: 'medium', high: 'medium', medium: 'low', low: 'low' };
const ANSWER_NOW = '\n\n(Answer now: keep your thinking short and write the reply as compact JSON, no extra whitespace.)';

/**
 * `ask`, with one lighter second attempt when Opus writes nothing (it ran out of time thinking) or the
 * connection drops: less effort, half the images, and a request to answer straight away. Never more
 * than one retry; anything else is thrown as it came.
 */
export async function askSafe(io: JobIO, input: string | Turn[], images: Sheet[], effort: Effort, label: string, describe?: (text: string) => string) {
  try {
    return await ask(io, input, images, effort, label, describe);
  } catch (e: any) {
    const code = e?.code;
    if ((code !== 'empty_completion' && code !== 'upstream_error') || io.signal.aborted) throw e;
    const empty = code === 'empty_completion';
    io.step(label, { detail: empty ? 'Opus ran out of time thinking; asking again, lighter' : 'the connection dropped; asking again' });
    const next = typeof input === 'string'
      ? input + (empty ? ANSWER_NOW : '')
      : [...input.slice(0, -1), { role: 'user' as const, content: input[input.length - 1].content + (empty ? ANSWER_NOW : '') }];
    return await ask(io, next, empty ? images.slice(0, Math.ceil(images.length / 2)) : images, empty ? LIGHTER[effort] : effort, label, describe);
  }
}

/** High and Extra split a pass in two steps: direct (with the images), then write the operations. */
export const twoStage = (effort: Effort) => effort === 'high' || effort === 'extra';
/** The thinking used to turn a finished direction into operations. */
const writeEffort = (effort: Effort): Effort => (twoStage(effort) ? 'medium' : effort);

// ---------- numbered notes ----------

const SENTENCE = /(?<=[.!?])\s+(?=["'(A-Z0-9])/;

/** A time a note names: "@ 7.80s", "at 7.8 s", "0:07". */
export function timeIn(t: string): number | undefined {
  const a = t.match(/@\s*(\d+(?:\.\d+)?)\s*s\b/) || t.match(/\bat\s+(\d+(?:\.\d+)?)\s*s(?:ec(?:onds?)?)?\b/i);
  if (a) return +a[1];
  // mm:ss, but not an aspect ratio such as 9:16
  const b = t.match(/\b(\d{1,2}):(\d{2}(?:\.\d+)?)\b(?!\s*(?:aspect|ratio|format|vertical|portrait))/);
  if (!b || /^(9:16|16:9|21:9)$/.test(b[0])) return undefined;
  const v = +b[1] * 60 + +b[2];
  return +b[2] < 60 && v <= 180 ? v : undefined;
}

/** The owner's instructions as separate asks: one per line, a long paragraph one per sentence. */
export function ownerAsks(text: string): string[] {
  const lines = text.split(/\n+/).map(l => l.replace(/^\s*(?:[-*•]|\d{1,2}[.)]|\(\d{1,2}\))\s+/, '').trim()).filter(l => l.length > 2);
  const out: string[] = [];
  for (const l of lines) {
    const parts = l.split(SENTENCE).map(s => s.trim()).filter(Boolean);
    if (parts.length < 2) { out.push(l); continue; }
    for (const s of parts) {
      // a fragment such as "Love it." stays with the sentence before; every real ask gets its own number
      if (out.length && s.length < 16 && !/^(add|use|make|cut|keep|remove|move|put|try|change|fix|swap|no|less|more)\b/i.test(s)) out[out.length - 1] += ` ${s}`;
      else out.push(s);
    }
  }
  if (out.length > 16) { const rest = out.splice(15); out.push(rest.join(' ')); }
  return out;
}

/** The round's numbered notes: the owner's asks, then the critic points they passed on. */
export function roundNotes(brief: string, fromCritic?: string[]): NoteCheck[] {
  const auto = /^\s*Automatic round/i.test(brief);
  const notes: NoteCheck[] = [];
  // notes carry their full text (a critic point's fix is at its end): the reminders later are shortened, never this
  for (const t of auto ? [] : ownerAsks(brief)) notes.push({ id: `N${notes.length + 1}`, text: t.slice(0, 3000), from: 'owner', at: timeIn(t) });
  for (const t of fromCritic || []) notes.push({ id: `N${notes.length + 1}`, text: t.replace(/\s*\n\s*/g, ' ').slice(0, 3000), from: 'critic', at: timeIn(t) });
  return notes.slice(0, 24);
}

function notesBlock(notes: NoteCheck[], heading = 'NOTES TO CARRY OUT'): string {
  if (!notes.length) return '';
  return `${heading} (numbered; do every one in full. The studio counts the operations you tag with each note, renders frames at its time to check it, and the critic checks every one again. A note that asks for something bigger, such as more flair, a new look or a stronger set piece, gets a big change, not a token one.)\n${notes.map(n => `${n.id} [${n.from === 'owner' ? 'owner' : 'critic'}${n.at !== undefined ? ` @ ${n.at.toFixed(2)}s` : ''}] ${n.text}`).join('\n')}`;
}

function noteTable(notes: NoteCheck[]): string {
  return notes.map(n => `${n.id} [${n.from}${n.at !== undefined ? ` @ ${n.at.toFixed(2)}s` : ''}] ${n.text.slice(0, 260)}${n.plan ? ` | your plan: ${n.plan.slice(0, 220)}` : ''} | operations applied: ${n.ops || 0}${n.status ? ` | last check: ${n.status}${n.check ? ` (${n.check.slice(0, 160)})` : ''}` : ''}`).join('\n');
}

function addCounts(notes: NoteCheck[], counts?: Record<string, number>) {
  if (!counts) return;
  for (const n of notes) if (counts[n.id]) n.ops = (n.ops || 0) + counts[n.id];
}

/** Plans or checks Opus wrote for the notes ({"notes": [{"id", "plan" | "status", "check"}]}). */
function readNotes(notes: NoteCheck[], v: any, kind: 'plan' | 'check') {
  if (!v || !Array.isArray(v.notes)) return;
  for (const x of v.notes) {
    const n = notes.find(k => k.id === String(x?.id ?? '').trim().toUpperCase());
    if (!n) continue;
    if (kind === 'plan' && typeof x.plan === 'string') n.plan = x.plan.slice(0, 600);
    if (kind === 'check') {
      const st = String(x.status || '').toLowerCase();
      n.status = st.startsWith('done') ? 'done' : st.startsWith('part') ? 'partial' : st.startsWith('not') || st === 'missing' ? 'not' : n.status;
      if (typeof x.check === 'string') n.check = x.check.slice(0, 400);
    }
  }
}

function readScores(v: any): Record<string, number> | undefined {
  if (!v || !v.scores || typeof v.scores !== 'object') return undefined;
  const out: Record<string, number> = {};
  for (const a of CRITIC_AREAS) { const n = Number(v.scores[a.id]); if (Number.isFinite(n)) out[a.id] = Math.max(0, Math.min(10, Math.round(n * 10) / 10)); }
  return Object.keys(out).length ? out : undefined;
}

const SCORE_FORMAT = `{${CRITIC_AREAS.map(a => `"${a.id}": 0-10`).join(', ')}}`;

// ---------- the steps' instructions ----------

function buildStep1(notes: NoteCheck[]) {
  return `STEP 1 OF 2: DIRECT THE EDIT. Do not write operations yet. Clear the PRE-BUILD GATE, use the worked examples and the playbook, then decide everything and write it down compactly (short lines, timeline times in seconds). Work fast where the studio already did the work: take every time from the song window's timeline grid in MEDIA (bars, the drop, the beat length; a beat is a bar time + k x the beat), never list or recompute beats, and take shots from the shot list and the pack notes. Keep the whole direction under about 10,000 characters: terse lines, no restating of the rules. In this order:
CONCEPT: one sentence from the character's world and the song's words, and how picture, look, text, sound and the loop carry it.
LOOK: the library look with its params (or your own grade), the accent colour for emphasis words and lights, and why it suits the concept. Be bold: black-and-white with one colour kept, a duotone, a film stock or a themed monochrome beats a neutral grade.
SONG: media id, source in -> out, where the drop and the hook land on the timeline; SECTIONS with timeline times.
SHOTS in order: "t0-t1 media #shot source-in: what it shows | focus x,y | speed, ramp or freeze | move".
TRANSITIONS, one per cut: "time type (at x,y -> to x,y): what it goes through and why | sound".
SET PIECES (three or more multi-stage, plus the focal one the owner will point to): each as anticipation -> action -> payoff with times and every layer: ramp or freeze, camera, the transition, fx presets with params and anchors, your own shader or SVG graphic where no preset fits, the title, the sound.
TEXT: "t0-t1 words | anim in/out | style | position" (captions only on sung or spoken words; two or more designed titles that act out their meaning).
GRAPHICS AND EFFECTS per section: light, atmosphere, particles, themed overlays and beat moments (fx presets with params and anchors, your own shaders or graphics), so no section is bare footage.
CAMERA: the beat camera (every, punch, kick, from, to).
SOUND: every effect with its time (8-16 moments; the material sound for each set piece).
LOOP: how the last frame lands on frame 0, in picture and sound.${notes.length ? '\nNOTES: for each N#, how the plan carries it out.' : ''}
SCORECARD: score this plan 0-10 in each area the critic scores (hook, rhythm, transitions, motion, text, sound, concept, picture, loop), one line each, against the benchmarks and the worked examples. Redesign anything under 8 before you finish, then give the final scores.
Reply with only JSON: {"message": "the concept sentence and the set pieces, for the owner", "direction": "the full plan as compact text"${notes.length ? ', "notes": [{"id": "N1", "plan": "one line"}]' : ''}}`;
}

function reviseStep1(notes: NoteCheck[]) {
  return `STEP 1 OF 2: DECIDE THE CHANGES. Do not write operations yet.${notes.length ? `
For EVERY note N1-${notes[notes.length - 1].id}, write "N#: the exact change" with the time, the clip ids, the new shot or value, the transition with its anchors and sound, the library effect with its params, the text and its animation, and what the frame will show after it. Do each note the way the owner or critic meant it, in full; when a note names a problem without a fix, choose the strongest fix the studio has.` : ''}
Then anything else the edit needs to clear the standards, and a SCORECARD of the edit after these changes (each critic area 0-10, one line each); raise any area under 8 with further changes.
Keep what already works. Be compact.
Reply with only JSON: {"message": "what will change, note by note, for the owner", "direction": "the full decisions as compact text"${notes.length ? ', "notes": [{"id": "N1", "plan": "one line"}]' : ''}}`;
}

const TAG_NOTES = 'Tag every operation that carries out a numbered note with it: "note":"N2" (or "note":["N1","N3"]); leave it out on other operations.';

const PARTS_BUILD = [
  { key: 'a', label: 'picture', text: 'STEP 2 OF 2, PART A: THE PICTURE (part B writes the layers at the same time). Write exactly these operations from your direction: {"op":"clear"} first; "project" (name, camera); the music and any dialogue clips on audio tracks; every main-track shot in order with its media, in, dur, focus, speed, ramp or speed keys, transform and kf; every other media clip (a copy of a shot on an overlay track for a polaroid, a mirror or the loop, dialogue); every transition with its anchors; the look. Do not write text, lyrics, fx, graphic, shader or sfx operations.' },
  { key: 'b', label: 'layers', text: 'STEP 2 OF 2, PART B: THE LAYERS (part A writes the clear, the shots, the music, the transitions and the look at the same time, exactly on the times in your direction). Write exactly these operations from your direction: every text and lyrics operation, every fx (library effect), graphic and shader operation, and every sfx, with any text or overlay "track" operations they need. Do not write clear, project, look or add operations (part A writes every media clip), and do not change the shots. Start every id you create with "b" (bt1, bfx2).' },
];
const PARTS_REVISE = [
  { key: 'a', label: 'picture', text: 'STEP 2 OF 2, PART A: THE PICTURE (part B writes the layer changes at the same time). Write the operations for exactly the changes you decided to the shots (order, timing, framing, speed, keyframes), the transitions, the music, the camera and the look, against the CURRENT TIMELINE. Do not change text, lyrics, effects, graphics, shaders or sound effects.' },
  { key: 'b', label: 'layers', text: 'STEP 2 OF 2, PART B: THE LAYERS (part A changes the shots, transitions, music, camera and look at the same time, to the times in your decisions). Write the operations for exactly the changes you decided to text and lyrics, library effects, graphics, shaders and sound effects, against the CURRENT TIMELINE. Do not write clear, and do not change the shots, transitions or look. Start every id you create with "b".' },
];
const PART_TAIL = `${TAG_NOTES} Reply with only JSON: {"message": "what this part does", "ops": [...]}, written compactly (no indentation or blank lines).`;

/**
 * Turn a finished direction into operations: the picture and the layers are written by two calls at
 * the same time (each half the length, so the round finishes sooner and neither runs out of time). A
 * part that fails is asked again on its own; the picture is required, the layers are reported if lost.
 */
async function writeOps(io: JobIO, base: Turn[], parts: { key: string; label: string; text: string }[], effort: Effort, revision: boolean) {
  const prog: Record<string, { ops: number; chars: number }> = {};
  for (const p of parts) prog[p.key] = { ops: 0, chars: 0 };
  const detail = () => `writing operations… ${parts.map(p => `${p.label} ${prog[p.key].ops}`).join(' · ')}`;
  const run = (p: typeof parts[number]) => {
    const pio: JobIO = { ...io, stream: n => { prog[p.key].chars = n; io.stream(Object.values(prog).reduce((s, x) => s + x.chars, 0)); } };
    return askSafe(pio, [...base, { role: 'user', content: `${p.text}\n${PART_TAIL}` }], [], effort, 'plan', t => { prog[p.key].ops = (t.match(/"op"\s*:/g) || []).length; return detail(); });
  };
  const fatal = (e: any) => e?.code === 'cancelled' || e?.name === 'AbortError' || io.signal.aborted || e?.code === 'not_granted' || e?.code === 'session_expired';
  const settled = await Promise.allSettled(parts.map(run));
  const out: { key: string; message: string; ops: unknown[]; salvaged: boolean }[] = [];
  const lost: string[] = [];
  for (let i = 0; i < parts.length; i++) {
    const p = parts[i];
    let s: PromiseSettledResult<{ text: string; truncated: boolean }> = settled[i];
    let reply = s.status === 'fulfilled' ? parseReply(s.value.text) : null;
    if (s.status === 'rejected' && fatal(s.reason)) throw s.reason;
    // a revision part may rightly change nothing; a build needs its picture
    const needsOps = !revision && p.key === 'a';
    if (!reply || (needsOps && !reply.ops.length)) {
      // once more on its own (a rate limit or a dropped reply on one of two parallel calls)
      io.step('plan', { detail: `asking again for the ${p.label}` });
      try { s = { status: 'fulfilled', value: await run(p) }; reply = parseReply(s.value.text); } catch (e: any) { if (fatal(e)) throw e; s = { status: 'rejected', reason: e }; reply = null; }
    }
    if (!reply || (needsOps && !reply.ops.length)) {
      if (p.key === 'a') throw s.status === 'rejected' ? s.reason : { code: 'invalid_json' };
      lost.push(p.label);
      continue;
    }
    const ops = p.key === 'a' ? reply.ops : reply.ops.filter((o: any) => o?.op !== 'clear');
    out.push({ key: p.key, message: reply.message, ops, salvaged: !!(reply as any).salvaged });
  }
  return {
    ops: out.flatMap(x => x.ops),
    message: out.find(x => x.message)?.message || '',
    salvaged: out.some(x => x.salvaged),
    lost,
  };
}

/**
 * Two steps instead of one long call: Opus directs the pass (decisions only, with the images), then
 * the operations are written for exactly that direction (lighter thinking, no images).
 */
async function directThenBuild(io: JobIO, o: { ctx: string; ctxNoImages: string; history: Turn[]; request: string; images: Sheet[]; effort: Effort; revision: boolean; notes: NoteCheck[] }) {
  const step1 = o.revision ? reviseStep1(o.notes) : buildStep1(o.notes);
  const ask1 = `${o.request}\n\n${step1}`;
  const t1: Turn[] = [{ role: 'user', content: o.ctx }, ...o.history, { role: 'user', content: ask1 }];
  io.step('direct', { state: 'run', detail: 'thinking…' });
  const a = await askSafe(io, t1, o.images, o.effort, 'direct', t => `writing the direction… ${t.length} characters`);
  const av: any = parseJson(a.text);
  const direction = typeof av?.direction === 'string' && av.direction.trim() ? av.direction : a.text;
  const note = typeof av?.message === 'string' ? av.message : '';
  readNotes(o.notes, av, 'plan');
  io.step('direct', { state: 'done', detail: `${direction.length} characters${a.truncated ? ' (cut short)' : ''}` });

  const base: Turn[] = [{ role: 'user', content: o.ctxNoImages }, ...o.history, { role: 'user', content: ask1 }, { role: 'assistant', content: a.text }];
  io.step('plan', { state: 'run', detail: 'writing operations…' });
  const split = !o.revision || direction.length > 2400;
  let message: string, ops: unknown[], salvaged = false, lost: string[] = [];
  if (split) {
    ({ message, ops, salvaged, lost } = await writeOps(io, base, o.revision ? PARTS_REVISE : PARTS_BUILD, writeEffort(o.effort), o.revision));
  } else {
    const step2 = `STEP 2 OF 2: Write the operations for exactly the changes you decided, against the CURRENT TIMELINE. Keep everything else. ${TAG_NOTES} Reply with only JSON: {"message": "what you changed, note by note", "ops": [...]}, written compactly.`;
    const b = await askSafe(io, [...base, { role: 'user', content: step2 }], [], writeEffort(o.effort), 'plan');
    const plan = parseReply(b.text);
    if (!plan) throw { code: b.truncated ? 'empty_completion' : 'invalid_json' };
    ({ message, ops } = plan);
    salvaged = !!(plan as any).salvaged;
  }
  if (!ops.length && !o.revision) throw { code: 'invalid_json' };
  io.step('plan', { state: 'done', detail: `${ops.length} operations${split ? ' (picture and layers written together)' : ''}${salvaged ? ' (kept what was written before it was cut short)' : ''}${lost.length ? `; the ${lost.join(' and ')} could not be written, the review adds them` : ''}` });
  const reply = JSON.stringify({ message: message || note, ops: `(${ops.length} operations, applied: the CURRENT TIMELINE shows the result)` });
  return {
    plan: { message: message || note, ops },
    lost,
    turns: [...base, { role: 'user' as const, content: 'STEP 2 OF 2: write the operations for exactly this direction.' }, { role: 'assistant' as const, content: reply }],
  };
}

export function maxImagesFor(effort: Effort) {
  const d = store.state.director;
  const cfg = EFFORTS[effort];
  return d.images ? Math.min(cfg.images, d.maxImages || cfg.images) : 0;
}

/** Frame times for a review: a sweep, every transition and title, after every cut, the last frame, and the notes' times. */
export function reviewTimes(p: Project, max: number, must: number[] = []): number[] {
  const dur = projectDuration(p);
  if (dur <= 0) return [];
  const keep = [...new Set(must.filter(t => t >= 0 && t < dur).flatMap(t => [t, t + 0.3]).map(t => +Math.min(dur - 0.01, t).toFixed(2)))].slice(0, Math.floor(max / 3));
  const room = Math.max(1, max - keep.length);
  const set = new Set<number>();
  const sweep = Math.min(room / 2, Math.max(6, Math.round(dur / 1.5)));
  for (let i = 0; i < sweep; i++) set.add(+(((i + 0.5) / sweep) * dur).toFixed(2));
  for (const c of p.clips) {
    if (c.transition) set.add(+c.start.toFixed(2));
    if (c.kind === 'text') set.add(+(c.start + Math.min(c.dur * 0.6, (c.anim?.inDur ?? 0.3) + 0.25)).toFixed(2));
  }
  for (const t of cutTimes(p)) if (t + 0.1 < dur) set.add(+(t + 0.1).toFixed(2));
  set.add(+(Math.max(0, dur - 1 / p.fps)).toFixed(3));
  let times = [...set].filter(t => t >= 0 && t < dur && !keep.includes(t)).sort((a, b) => a - b);
  if (times.length > room) {
    const pick: number[] = [];
    for (let i = 0; i < room; i++) pick.push(times[Math.floor((i * times.length) / room)]);
    times = pick;
  }
  return [...times, ...keep].sort((a, b) => a - b);
}

/** Frame labels: the notes a frame checks, else its time. */
function frameLabels(times: number[], notes: NoteCheck[]): string[] {
  return times.map(t => {
    const ns = notes.filter(n => n.at !== undefined && t >= n.at - 0.01 && t <= n.at + 0.31).map(n => n.id);
    return ns.length ? `${ns.slice(0, 3).join(' ')} · ${t.toFixed(2)}s` : `T ${t.toFixed(2)}s`;
  });
}

export async function standardsForPreset(preset: Preset, ids?: string[]): Promise<Standard[]> {
  const all = await listStandards();
  if (ids) return all.filter(s => ids.includes(s.id));
  const out = [...all.filter(s => preset.standards.includes(s.id)), ...standardsFor(all, preset.id)];
  return out.filter((s, i) => out.findIndex(x => x.id === s.id) === i);
}

export function standardsText(standards: Standard[]): string {
  return standards.map(s => {
    const pr = s.profile;
    const prof = pr ? ` Measured: ${pr.duration.toFixed(1)} s, ${pr.cuts} cuts (${pr.cutsPerSec.toFixed(2)} per second, average shot ${pr.avgShot.toFixed(2)} s)${pr.bpm ? `, ${pr.bpm} BPM` : ''}${pr.onBeat !== null ? `, ${Math.round(pr.onBeat * 100)}% of cuts on a beat` : ''}.` : '';
    return `- "${s.name}"${s.url ? ` (${s.url})` : ''}: ${s.notes || 'the owner considers this a standard of what an edit should be.'}${prof}`;
  }).join('\n');
}

/**
 * What a call knows beyond the studio reference: the house rules and benchmarks, the craft and the
 * set-piece playbook, and for the calls that direct or judge an edit the worked examples and the
 * critic's canon.
 */
export function extrasFor(preset: Preset, standards: Standard[], checks?: string, o: { exemplars?: boolean; canon?: boolean } = {}): ContextExtras {
  return {
    houseRules: preset.houseRules ? HOUSE_RULES : '',
    benchmarks: preset.houseRules ? BENCHMARK_TEXT : '',
    craft: preset.houseRules ? [CRAFT, COOKBOOK, EFFICIENT].join('\n\n') : [CRAFT, EFFICIENT].join('\n\n'),
    exemplars: o.exemplars && preset.houseRules ? EXEMPLARS : '',
    canon: o.canon ? CRITIC_CANON : '',
    lessons: o.canon ? lessonsText() : '',
    presetName: preset.name,
    presetPrompt: preset.prompt,
    standards: standardsText(standards),
    knowledge: store.state.director.knowledge,
    checks,
  };
}

/** Opus picks material from the database for this edit. */
async function castFromLibrary(io: JobIO, req: NonNullable<Job['request']>, preset: Preset): Promise<{ items: LibraryItem[]; note?: string }> {
  const all = (await listLibrary()).filter(i => i.state === 'ready');
  let pool = req.library.mode === 'picked' ? all.filter(i => req.library.ids.includes(i.id)) : all;
  if (req.library.mode === 'auto' && preset.libraryTags.length) {
    const tagged = pool.filter(i => i.tags.some(t => preset.libraryTags.includes(t)) || i.role === 'music');
    if (tagged.length >= 2) pool = tagged;
  }
  if (!pool.length) return { items: [] };
  if (req.library.mode === 'picked' || pool.length <= 4) return { items: pool };
  io.step('cast', { detail: `choosing from ${pool.length} items` });
  const mosaic = await libraryMosaic(pool);
  const catalog = pool.slice(0, 300).map(i => `${i.id} ${i.role} ${i.kind} "${i.name}" ${i.duration.toFixed(1)}s${i.width ? ` ${i.width}x${i.height}` : ''}${i.bpm ? ` ${i.bpm} BPM` : ''}${i.shots ? ` ${i.shots} shots` : ''}${i.tags.length ? ` tags: ${i.tags.join(', ')}` : ''}${i.notes ? ` notes: ${i.notes}` : ''}`).join('\n');
  const prompt = [
    'You are casting material for a video edit in VOIDFX Studio. Pick the database items the edit should use.',
    `PRESET "${preset.name}": ${preset.prompt || preset.description}`,
    `OWNER'S NOTES FOR THIS EDIT: ${req.notes || '(none)'}`,
    req.lyrics ? `LYRICS SUPPLIED: ${req.lyrics.slice(0, 2000)}` : '',
    `DATABASE (${pool.length} items)\n${catalog}`,
    mosaic ? 'The attached image shows each item\'s poster frame, labelled with its id.' : '',
    'Pick one music item (unless the notes or attached files already supply the song) and the scene packs or clips with the strongest material for this concept: prefer the least-compressed packs for close-ups and the packs with the proven shots the concept needs; at most 6 items in total. Reply with only JSON: {"items": [{"id": "...", "why": "..."}], "message": "one sentence on the choice"}',
  ].filter(Boolean).join('\n\n');
  // picking up to six items from a labelled list needs little thinking
  const r = await askSafe(io, prompt, mosaic ? [mosaic] : [], 'low', 'cast');
  const raw: any = parseJson(r.text);
  const ids: string[] = Array.isArray(raw?.items) ? raw.items.map((x: any) => String(x?.id ?? x)) : [];
  const chosen = pool.filter(i => ids.includes(i.id)).slice(0, 6);
  return { items: chosen.length ? chosen : pool.slice(0, 4), note: typeof raw?.message === 'string' ? raw.message : undefined };
}

/** When Opus placed no sound effects at all, sound the designed transitions (soft joins stay silent). */
function withSounds(p: Project, media: Record<string, MediaInfo>): Project {
  const trans = p.clips.filter(c => c.transition);
  const sfx = p.clips.filter(c => c.kind === 'sfx');
  const silent = trans.filter(c => !sfx.some(s => s.start >= c.start - 2.2 && s.start <= c.start + 0.4));
  if (!silent.length || sfx.length) return p;
  const q = deepClone(p);
  addTransitionSounds(q);
  return normalize(q, media);
}

async function checkpoint(ws: Workspace, preset: Preset, seam: boolean): Promise<Check[]> {
  const s = seam ? await measureLoopSeam(ws.project, ws.media()).catch(() => null) : null;
  return runChecks(ws.project, ws.media(), { houseRules: preset.houseRules, duration: preset.duration, fps: preset.fps, seam: s });
}

/** Wait for the job's media, failing clearly if nothing usable is there. */
async function readMedia(ws: Workspace, io: JobIO) {
  io.step('media', { state: 'run', detail: 'opening files and sound analysis' });
  await ws.attach();
  await whenMediaIdle(240000, ws, io.signal);
  if (io.signal.aborted) throw { name: 'AbortError' };
  const n = ws.ready().length;
  if (!n) throw { code: 'no_media' };
  io.step('media', { state: 'done', detail: `${n} file${n > 1 ? 's' : ''}` });
}

/** How Opus should use the owner's lyrics: timed lines go through the "lyrics" operation; plain ones only inform. */
export function lyricsBrief(l?: Lyrics): string {
  if (!l?.lines.length) return '';
  if (l.timed) return `TIMED LYRICS (synced lyrics from the owner; times are SONG times, seconds into the song file, not timeline times)
Caption sung lines with the "lyrics" operation only: it puts each line on its sung time through the music clip, in the house caption style, each word easing in on its own time, and keeps them there when cuts move. Caption the lines that fall inside your song window and carry the concept (not necessarily every line); add *emphasis* with "text" overrides; never type sung words as plain text clips. Designed titles (a hero word that acts out its meaning) still go on sung words: take their time from these lines.
${lyricsText(l)}`;
  return `LYRICS WITHOUT TIMES (the owner pasted plain lyrics)
You cannot hear when each line is sung, so do not caption them line by line. Use them for the concept, and at most two designed titles on words you can place with confidence (the hook word on the drop's downbeat). Say in one line of "message" that pasting synced lyrics (LRC: "[mm:ss.xx] line", from a lyrics site or app) puts captions on the sung words.
${l.lines.map(x => x.text).join('\n').slice(0, 3000)}`;
}

const REVIEW_NOTE = 'The full contact sheets of the media were attached to the first request. The images attached to the latest message are frames rendered from the edit as it stands now, labelled with timeline time (and with the notes a frame checks), followed by a palette of the footage (one frame per shot) for choosing shots to swap in.';

/** Notes that got no operations: one quick call writes them before anything is reviewed. */
async function fillMissingNotes(ws: Workspace, io: JobIO, o: { preset: Preset; standards: Standard[]; turns: Turn[]; notes: NoteCheck[]; effort: Effort; mediaImages: boolean }): Promise<OpsResult | null> {
  const missing = o.notes.filter(n => !n.ops);
  if (!missing.length) return null;
  io.step('apply', { state: 'run', detail: `${missing.length} note${missing.length > 1 ? 's' : ''} had no operations; Opus is adding ${missing.length > 1 ? 'them' : 'it'}` });
  const msg = `THE STUDIO FOUND NOTES WITH NO APPLIED OPERATIONS\n${noteTable(missing)}\nWrite the operations for each of them now, against the CURRENT TIMELINE (your other changes are already applied), and tag each with its note. If a note truly needs no change, leave it out and say why in "message". ${TAG_NOTES} Reply with only JSON: {"message": "...", "notes": [{"id": "N1", "plan": "one line"}], "ops": [...]}, compact.`;
  const rest: Turn[] = [...o.turns.slice(1), { role: 'user', content: msg }];
  const ctx = fitContext(x => contextBlock(ws.ctx, [], o.mediaImages ? REVIEW_NOTE : undefined, x), extrasFor(o.preset, o.standards), inputBytes(rest));
  try {
    const r = await askSafe(io, [{ role: 'user', content: ctx }, ...rest], [], writeEffort(o.effort), 'apply');
    const rep = parseReply(r.text);
    readNotes(o.notes, parseJson(r.text), 'plan');
    o.turns.push({ role: 'user', content: msg }, { role: 'assistant', content: compactReply(r.text) });
    if (!rep || !rep.ops.length) return null;
    const res = applyOps(ws.project, rep.ops, ws.media());
    addCounts(o.notes, res.notes);
    ws.setProject(o.preset.houseRules ? withSounds(res.project, ws.media()) : res.project);
    await ws.save();
    return res;
  } catch (e: any) {
    if (e?.code === 'cancelled' || io.signal.aborted || e?.code === 'not_granted') throw e;
    return null;
  }
}

/** Measured brightness of the rendered frames: an edit that reads as black on a phone is a mistake. */
export function brightnessNote(sheets: Sheet[]): string {
  const all = sheets.flatMap(s => s.lumas || []);
  if (all.length < 6) return '';
  const avg = all.reduce((a, [, l]) => a + l, 0) / all.length;
  const dark = all.filter(([, l]) => l < 0.1).map(([t]) => t);
  const bright = all.filter(([, l]) => l > 0.82).map(([t]) => t);
  if (avg >= 0.2 && dark.length <= Math.max(1, all.length * 0.08) && !bright.length) return `MEASURED BRIGHTNESS of the rendered frames: average ${Math.round(avg * 100)}%, no run of near-black or blown-out frames: fine.`;
  return `MEASURED BRIGHTNESS of the rendered frames: average ${Math.round(avg * 100)}% (a strong edit sits around 25-45% with real blacks and bright highlights).${dark.length ? ` Near-black frames (under 10%): ${dark.slice(0, 16).map(t => `${t.toFixed(2)}s`).join(', ')}.` : ''}${bright.length ? ` Blown-out frames (over 82%): ${bright.slice(0, 10).map(t => `${t.toFixed(2)}s`).join(', ')}.` : ''} On a phone, a frame this dark or bright reads as a mistake unless it is a designed beat (the black of a blink, a dive or the loop; the peak of a wash). Lift dark shots (color brightness/contrast on the clip, or the look's params) and keep faces readable.`;
}

function reviewMessage(k: number, total: number, o: { issues: string[]; checks: Check[]; sheets: Sheet[]; notes: NoteCheck[]; revision: boolean; lost?: string[] }): string {
  const issuesText = o.issues.length ? `The studio adjusted or rejected these operations:\n- ${o.issues.slice(0, 40).join('\n- ')}` : 'All operations were applied without problems.';
  const raise = total > 1 && k === total;
  const head = raise
    ? `REVIEW ${k} OF ${total}: RAISE THE CEILING. The edit works; now make it one the owner calls the best so far. Look at the frames as the critic will and find the three weakest moments: a set piece that is only one move; a section of bare footage (no look, light, atmosphere, graphics or beat moments); a generic transition where a designed one belongs; a held shot with no motion; a title that does not act out its meaning; a weak loop. Rebuild those moments in layers (a ramp or freeze, the camera, a designed transition with anchors, library effects, your own shader or graphic, the title, a sound), then check the rest again. Keep everything that already works.`
    : o.revision
      ? `REVIEW ${k} OF ${total}: CHECK EVERY NOTE, THEN THE QUALITY. Look at each note's frames (labelled with its id): a note is done only when the frame visibly shows the change the owner or critic asked for, in full. For every note that is partly done or not done, write its operations now. Then fix every failed or warning gate and check the frames as below.`
      : `REVIEW ${k} OF ${total}: QUALITY. Fix every failed or warning gate, then check the frames in this order.`;
  const checklist = 'FRAMING (a face cut off or off-centre: set or correct "focus"); TEXT (every caption a sung or spoken line on its time, never invented words; readable; nothing over a face); FLOW (does movement, position and light carry across each cut, or do shots feel shuffled? reorder or swap shots); TRANSITIONS (generic library moves replaced with designed ones that go through something, with anchors); MOTION (ramps, freezes, the beat camera, push-ins: no static stretch); LOOK AND LAYERS (the look reads in every frame; each section has its light, atmosphere, graphics or beat moments; nothing looks drawn on, nothing sits on a face); SOUND (only the moments that matter, each set piece with its material sound); the LOOP.';
  return [
    head,
    o.lost?.length ? `The ${o.lost.join(' and ')} of your direction could not be written: write them now, in full, from your direction.` : '',
    brightnessNote(o.sheets),
    issuesText,
    `AUTOMATED CHECKPOINT\n${checksText(o.checks)}`,
    o.sheets.length ? `IMAGES attached to this message: ${o.sheets.map((x, i) => `${i + 1}. ${x.caption}`).join('; ')}` : 'No rendered frames are attached.',
    o.notes.length ? `THE ROUND'S NOTES (what was planned and how many operations carried each one)\n${noteTable(o.notes)}` : '',
    raise ? '' : `CHECK: ${checklist}`,
    `Then SCORE the edit as it now stands in each critic area, honestly, the way the critic will; for every area under 8, make the change that raises it now.
Reply with only JSON: {"message": "what you fixed or raised, for the owner", "scores": ${SCORE_FORMAT}${o.notes.length ? ', "notes": [{"id": "N1", "status": "done" | "partial" | "not", "check": "what its frames show now, after your operations"}]' : ''}, "ops": [...]} (ops empty if it is ready). ${o.notes.length ? `${TAG_NOTES} ` : ''}The CURRENT TIMELINE in the first message is the edit as it stands. Write compact JSON. Do not start with clear unless you are rebuilding everything.`,
  ].filter(Boolean).join('\n\n');
}

/** Opus looks at frames rendered from its own edit and the checkpoint, and fixes or raises it. */
async function reviewPasses(ws: Workspace, io: JobIO, opts: { preset: Preset; standards: Standard[]; effort: Effort; turns: Turn[]; res: OpsResult; checks: Check[]; mediaImages: boolean; notes: NoteCheck[]; revision: boolean; lost?: string[] }) {
  const cfg = EFFORTS[opts.effort];
  const maxImg = maxImagesFor(opts.effort);
  let { res, checks } = opts;
  let total = 0, message = '';
  let scores: Record<string, number> | undefined;
  const issues: string[] = [];
  // a compact palette of the footage (one frame per shot) so a review that swaps or adds shots sees them
  let palette: Sheet[] = [];
  if (cfg.reviews && maxImg >= 8) {
    io.step('review1', { state: 'run', detail: 'a palette of the footage' });
    palette = (await mediaSheets(ws.ctx, 2, 40, io.signal).catch(() => [] as Sheet[])).map(s => ({ ...s, caption: `${s.caption} (the footage palette, for swapping or adding shots)` }));
  }
  for (let k = 1; k <= cfg.reviews; k++) {
    const id = `review${k}`;
    io.step(id, { state: 'run', detail: 'rendering frames' });
    const p = ws.project;
    const nSheets = Math.min(4, Math.max(1, maxImg));
    const must = opts.notes.filter(n => n.at !== undefined).map(n => n.at!);
    const times = reviewTimes(p, nSheets * 20, must);
    const frames = maxImg ? await timelineSheets(p, ws.media(), times, 20, nSheets, io.signal, undefined, frameLabels(times, opts.notes)) : [];
    const rSheets = [...frames, ...palette.slice(0, Math.max(0, maxImg - frames.length))];
    io.step(id, { detail: 'thinking…' });
    const msg = reviewMessage(k, cfg.reviews, { issues: res.issues, checks, sheets: rSheets, notes: opts.notes, revision: opts.revision, lost: k === 1 ? opts.lost : undefined });
    const rest: Turn[] = [...opts.turns.slice(1), { role: 'user', content: msg }];
    const ctxNow = fitContext(x => contextBlock(ws.ctx, [], opts.mediaImages ? REVIEW_NOTE : undefined, x), extrasFor(opts.preset, opts.standards, undefined, { canon: true, exemplars: cfg.reviews > 1 && k === cfg.reviews }), inputBytes(rest));
    let rk: { text: string; truncated: boolean };
    try {
      rk = await askSafe(io, [{ role: 'user', content: ctxNow }, ...rest], rSheets, cfg.review, id);
    } catch (e: any) {
      if (e?.code === 'cancelled' || io.signal.aborted || e?.code === 'not_granted' || e?.code === 'rate_limited') throw e;
      // the edit is already built: a review that fails is reported and the next one still runs
      io.step(id, { state: 'skip', detail: `could not run: ${errText(e).code}` });
      continue;
    }
    const rev = parseReply(rk.text);
    if (!rev) {
      io.step(id, { state: 'skip', detail: 'unreadable reply' });
      continue;
    }
    const v: any = parseJson(rk.text);
    readNotes(opts.notes, v, 'check');
    scores = readScores(v) || scores;
    opts.turns.push({ role: 'user', content: msg }, { role: 'assistant', content: compactReply(rk.text) });
    if (rev.ops.length) {
      res = applyOps(ws.project, rev.ops, ws.media());
      addCounts(opts.notes, res.notes);
      ws.setProject(opts.preset.houseRules ? withSounds(res.project, ws.media()) : res.project);
      total += res.applied;
      issues.push(...res.issues);
      checks = await checkpoint(ws, opts.preset, true);
      await ws.save();
    } else {
      res = { ...res, issues: [] };
    }
    if (rev.message) message = rev.message;
    const sc = scores ? Object.values(scores) : [];
    const low = sc.length ? Math.min(...sc) : undefined;
    io.step(id, { state: 'done', detail: `${rev.ops.length ? `${rev.ops.length} changes` : 'approved'}${low !== undefined ? ` · lowest area ${low}/10` : ''}` });
  }
  return { applied: total, issues, message, checks, scores };
}

/** The steps a build or revision shows, before it starts. */
export function stepsFor(job: Job, hasFiles: boolean): JobStep[] {
  const reviews = EFFORTS[job.effort].reviews;
  const rev = Array.from({ length: reviews }, (_, i) => ({ id: `review${i + 1}`, label: reviews > 1 ? (i === reviews - 1 ? `Opus reviews the render: raise the ceiling (${i + 1}/${reviews})` : `Opus reviews the render: quality${job.kind === 'create' ? '' : ' and every note'} (${i + 1}/${reviews})`) : `Opus reviews the render${job.kind === 'create' ? '' : ' and checks every note'}`, state: 'wait' as const }));
  if (job.kind === 'create') {
    return [
      ...(hasFiles ? [{ id: 'files', label: 'Store your files', state: 'wait' as const }] : []),
      ...(job.request && job.request.library.mode !== 'none' ? [{ id: 'cast', label: 'Pick material from the database', state: 'wait' as const }] : []),
      { id: 'media', label: 'Read the media', state: 'wait' },
      { id: 'sheets', label: 'Make contact sheets', state: 'wait' },
      ...(twoStage(job.effort) ? [{ id: 'direct', label: 'Opus directs: concept, look, shots, set pieces, scorecard', state: 'wait' as const }, { id: 'plan', label: 'Opus writes the picture and the layers', state: 'wait' as const }] : [{ id: 'plan', label: 'Opus plans the edit', state: 'wait' as const }]),
      { id: 'apply', label: 'Apply, validate, add sounds', state: 'wait' },
      { id: 'check', label: 'Run the checkpoint', state: 'wait' },
      ...rev,
    ];
  }
  return [
    { id: 'media', label: 'Read the media', state: 'wait' },
    { id: 'look', label: 'Render the current edit', state: 'wait' },
    ...(twoStage(job.effort) ? [{ id: 'direct', label: `Opus plans every note of round ${job.round}`, state: 'wait' as const }, { id: 'plan', label: 'Opus writes the operations', state: 'wait' as const }] : [{ id: 'plan', label: `Opus works on round ${job.round}`, state: 'wait' as const }]),
    { id: 'apply', label: 'Apply, validate, add sounds', state: 'wait' },
    { id: 'check', label: 'Run the checkpoint', state: 'wait' },
    ...rev,
  ];
}

export interface RoundResult { summary: string; applied: number; issues: string[]; model?: string; checks: Check[] }

const SINGLE_BUILD = `Direct it first in your thinking, clearing the PRE-BUILD GATE with the worked examples and the playbook: the concept sentence; a bold look; the song section and drop; three or more multi-stage set pieces plus the focal one; the shot list with focus and ramps; a designed transition with anchors and its sound on every cut; the captions and two or more designed titles; graphics and effects in every section; the beat camera; the loop. Score it the way the critic will (every area 8 or more, redesign anything lower), then build it exactly. Start with {"op":"clear"} unless the request asks you to keep the current timeline. ${TAG_NOTES} Put the concept sentence and the set pieces in "message".`;

/** Round 1: build the whole edit from the project's media, the database and the brief. */
export async function buildEdit(job: Job, ws: Workspace, io: JobIO): Promise<RoundResult> {
  const req = job.request || { notes: '', lyrics: '', library: { mode: 'none' as const, ids: [] } };
  const preset = await getPreset(job.presetId);
  const standards = await standardsForPreset(preset, req.standards);
  const effort = job.effort;
  const cfg = EFFORTS[effort];
  let model: string | undefined;
  const io2: JobIO = { ...io, model: m => { model = m; io.model(m); } };
  const notes = roundNotes(req.notes || '');

  // the preset sets the format before anything is planned
  const [w, h] = ASPECTS[preset.aspect] || ASPECTS['9:16'];
  if (ws.project.width !== w || ws.project.height !== h || ws.project.fps !== preset.fps) ws.setProject({ ...ws.project, width: w, height: h, fps: preset.fps });
  // dark grey is mud on a phone: house-style edits lift dim shots unless Opus turns it off
  if (preset.houseRules && !ws.project.exposure) ws.setProject({ ...ws.project, exposure: { auto: true, target: 0.34 } });
  if (req.lyrics?.trim()) ws.setProject({ ...ws.project, lyrics: parseLyrics(req.lyrics) });

  let castNote = '';
  if (req.library.mode !== 'none') {
    io.step('cast', { state: 'run' });
    const { items, note } = await castFromLibrary(io2, req, preset).catch(async (e: any) => {
      if (e?.code === 'cancelled' || io.signal.aborted || e?.code === 'not_granted') throw e;
      // casting failed: use the database items the preset favours rather than stopping the build
      const all = (await listLibrary()).filter(i => i.state === 'ready');
      const pool = req.library.mode === 'picked' ? all.filter(i => req.library.ids.includes(i.id)) : all;
      const music = pool.filter(i => i.role === 'music').slice(0, 1);
      const rest = pool.filter(i => i.role !== 'music' && (!preset.libraryTags.length || i.tags.some(t => preset.libraryTags.includes(t)))).slice(0, 4);
      return { items: [...music, ...(rest.length ? rest : pool.filter(i => i.role !== 'music').slice(0, 4))], note: 'Picked by the studio (Opus could not answer the casting call).' };
    });
    for (const it of items) await attachLibraryItem(it, ws);
    castNote = note || '';
    io.step('cast', { state: items.length ? 'done' : 'skip', detail: items.length ? items.map(i => i.name).slice(0, 4).join(', ') + (items.length > 4 ? '…' : '') : 'the database is empty' });
    await ws.save();
  }
  await readMedia(ws, io);

  io.step('sheets', { state: 'run' });
  const maxImg = maxImagesFor(effort);
  const stdVideos = standards.filter(x => x.kind === 'video' && x.state === 'ready');
  const stdImgs = maxImg > 4 ? await standardSheets(stdVideos, Math.min(3, Math.floor(maxImg / 4))) : [];
  const sheets = maxImg ? await mediaSheets(ws.ctx, maxImg - stdImgs.length, cfg.cells, io.signal, msg => io.step('sheets', { detail: msg })) : [];
  const images = [...stdImgs, ...sheets];
  io.step('sheets', { state: images.length ? 'done' : 'skip', detail: images.length ? `${images.length} image${images.length > 1 ? 's' : ''}` : 'images not available here' });

  const request = [
    'OWNER\'S REQUEST FOR THIS EDIT (round 1: the build)',
    req.notes || 'No extra notes: make the best edit you can from this material.',
    notesBlock(notes, 'THE OWNER\'S NOTES, NUMBERED'),
    castNote ? `MATERIAL CHOSEN FROM THE DATABASE: ${castNote}` : '',
    lyricsBrief(ws.project.lyrics),
  ].filter(Boolean).join('\n\n');
  const reserve = bytes(request) + 6000;
  const ctx = fitContext(x => contextBlock(ws.ctx, images.map(s => s.caption), undefined, x), extrasFor(preset, standards, undefined, { exemplars: effort !== 'low', canon: true }), reserve);
  let plan: { message: string; ops: unknown[] };
  let turns: Turn[];
  let lost: string[] = [];
  if (twoStage(effort)) {
    const ctxNoImages = fitContext(x => contextBlock(ws.ctx, [], images.length ? 'Contact sheets of the media were attached in step 1 and are not repeated: use the media ids, shots and source times from your direction.' : undefined, x), extrasFor(preset, standards), reserve + 16000);
    ({ plan, turns, lost } = await directThenBuild(io2, { ctx, ctxNoImages, history: [], request, images, effort, revision: false, notes }));
  } else {
    io.step('plan', { state: 'run', detail: 'thinking…' });
    turns = [{ role: 'user', content: ctx }, { role: 'user', content: `${request}\n\n${SINGLE_BUILD}` }];
    const r1 = await askSafe(io2, turns, images, effort, 'plan');
    const p1 = parseReply(r1.text);
    if (!p1 || !p1.ops.length) throw { code: 'invalid_json' };
    plan = p1;
    turns.push({ role: 'assistant', content: compactReply(r1.text) });
    io.step('plan', { state: 'done', detail: `${plan.ops.length} operations${(p1 as any).salvaged ? ' (kept what was written before it was cut short)' : r1.truncated ? ' (cut short)' : ''}` });
  }

  io.step('apply', { state: 'run' });
  const res = applyOps(ws.project, plan.ops, ws.media());
  addCounts(notes, res.notes);
  ws.setProject(preset.houseRules ? withSounds(res.project, ws.media()) : res.project);
  await ws.save();
  const extra = await fillMissingNotes(ws, io2, { preset, standards, turns, notes, effort, mediaImages: images.length > 0 });
  const applied = res.applied + (extra?.applied || 0);
  const adjusted = [...res.issues, ...(extra?.issues || [])];
  io.step('apply', { state: 'done', detail: `${applied} applied${adjusted.length ? `, ${adjusted.length} adjusted` : ''}${notes.length ? ` · ${notes.filter(n => n.ops).length}/${notes.length} notes carried` : ''}` });

  io.step('check', { state: 'run' });
  let checks = await checkpoint(ws, preset, true);
  const failing = checks.filter(c => c.status === 'fail' || c.status === 'warn').length;
  io.step('check', { state: 'done', detail: failing ? `${failing} to look at` : 'all gates pass' });

  const rv = await reviewPasses(ws, io2, { preset, standards, effort, turns, res: { ...res, issues: adjusted }, checks, mediaImages: images.length > 0, notes, revision: false, lost });
  checks = rv.checks;
  const summary = rv.message || plan.message || 'The edit is on the timeline.';
  await finishRound(ws, job, { summary, applied: applied + rv.applied, model, notes, scores: rv.scores }, turns);
  return { summary, applied: applied + rv.applied, issues: [...adjusted, ...rv.issues], model, checks };
}

/** Later rounds: the owner's instructions (and the critic points they passed on) applied to the current edit. */
export async function reviseEdit(job: Job, ws: Workspace, io: JobIO): Promise<RoundResult> {
  const preset = await getPreset(job.presetId);
  const standards = await standardsForPreset(preset);
  const effort = job.effort;
  const cfg = EFFORTS[effort];
  let model: string | undefined;
  const io2: JobIO = { ...io, model: m => { model = m; io.model(m); } };
  await readMedia(ws, io);
  if (!ws.project.clips.length) throw { code: 'no_edit' };
  if (job.lyrics?.trim()) ws.setProject({ ...ws.project, lyrics: parseLyrics(job.lyrics) });
  const brief = job.brief?.trim() || '';
  const notes = roundNotes(brief, job.fromCritic);

  io.step('look', { state: 'run' });
  const maxImg = maxImagesFor(effort);
  const p = ws.project;
  const must = notes.filter(n => n.at !== undefined).map(n => n.at!);
  const nLook = Math.min(3, maxImg);
  const times = reviewTimes(p, nLook * 20, must);
  const timeSheets = maxImg ? await timelineSheets(p, ws.media(), times, 20, nLook, io.signal, undefined, frameLabels(times, notes)) : [];
  const footage = maxImg > timeSheets.length ? await mediaSheets(ws.ctx, Math.max(1, Math.floor((maxImg - timeSheets.length) * 0.7)), cfg.cells, io.signal, msg => io.step('look', { detail: msg })) : [];
  const sheets = [...timeSheets, ...footage];
  io.step('look', { state: sheets.length ? 'done' : 'skip', detail: sheets.length ? `${sheets.length} image${sheets.length > 1 ? 's' : ''}` : 'no images' });

  const checks0 = await checkpoint(ws, preset, true);
  const rounds = ws.rec.rounds || [];
  const history: Turn[] = (ws.rec.aiTurns || []).slice(-6);
  const past = rounds.map(r => `Round ${r.n} (${r.kind}): owner asked "${r.brief.slice(0, 400)}"${r.summary ? `; you answered "${r.summary.slice(0, 300)}"` : ''}${r.critique ? `; the critic scored it ${r.critique.score}/10: ${r.critique.headline}` : ''}`).join('\n');
  const lastCrit = [...rounds].reverse().find(r => r.critique)?.critique;
  const weakest = lastCrit ? CRITIC_AREAS.filter(a => lastCrit.scores[a.id] !== undefined).sort((x, y) => lastCrit.scores[x.id] - lastCrit.scores[y.id]).map(a => `${a.label} ${lastCrit.scores[a.id]}`).join(', ') : '';
  const auto = /^\s*Automatic round/i.test(brief);
  const instruction = [
    `ROUND ${job.round} INSTRUCTIONS FROM THE OWNER`,
    auto ? 'Automatic round: carry out every critic point below.' : brief || '(no extra words: work through the critic\'s points)',
    notesBlock(notes),
    auto && lastCrit?.brief ? `THE CRITIC'S WRITE-UP (context for the notes)\n${lastCrit.brief}` : '',
    lastCrit ? `THE CRITIC'S LAST SCORE: ${lastCrit.score}/10 ("${lastCrit.headline}"); areas from weakest: ${weakest}. Raise the weakest areas with real changes; the critic checks every note again and scores the result.` : '',
    past ? `EARLIER ROUNDS\n${past}` : '',
    lyricsBrief(ws.project.lyrics),
    'Change the current timeline to do all of this. Keep what already works unless the instructions say otherwise; rebuild a section completely when that is what it takes. The first images are frames rendered from the edit as it stands (frames labelled with a note id show that note\'s moment); the rest are contact sheets of the media for finding better shots.',
  ].filter(Boolean).join('\n\n');
  const reserve = bytes(instruction) + history.reduce((n, t) => n + bytes(t.content), 0) + 6000;
  const ctx = fitContext(x => contextBlock(ws.ctx, sheets.map(x2 => x2.caption), undefined, x), extrasFor(preset, standards, checksText(checks0), { canon: true, exemplars: effort === 'extra' }), reserve);
  let plan: { message: string; ops: unknown[] };
  let turns: Turn[];
  let lost: string[] = [];
  if (twoStage(effort)) {
    const ctxNoImages = fitContext(x => contextBlock(ws.ctx, [], sheets.length ? 'The rendered frames and contact sheets were attached in step 1 and are not repeated: use the times, media ids and shots from your decisions.' : undefined, x), extrasFor(preset, standards, checksText(checks0)), reserve + 16000);
    ({ plan, turns, lost } = await directThenBuild(io2, { ctx, ctxNoImages, history, request: instruction, images: sheets, effort, revision: true, notes }));
  } else {
    io.step('plan', { state: 'run', detail: 'thinking…' });
    turns = [{ role: 'user', content: ctx }, ...history, { role: 'user', content: `${instruction}\n\nWork through the notes one by one in your thinking (what exactly changes, where, and how the frame will look), then write the operations. ${TAG_NOTES} Put what you changed, note by note, in "message".` }];
    const r = await askSafe(io2, turns, sheets, effort, 'plan');
    const p1 = parseReply(r.text);
    if (!p1) throw { code: 'invalid_json' };
    plan = p1;
    turns.push({ role: 'assistant', content: compactReply(r.text) });
    io.step('plan', { state: 'done', detail: `${plan.ops.length} operations${(p1 as any).salvaged ? ' (kept what was written before it was cut short)' : r.truncated ? ' (cut short)' : ''}` });
  }

  io.step('apply', { state: 'run' });
  const res = applyOps(ws.project, plan.ops, ws.media());
  addCounts(notes, res.notes);
  if (plan.ops.length) ws.setProject(preset.houseRules ? withSounds(res.project, ws.media()) : res.project);
  await ws.save();
  const extra = await fillMissingNotes(ws, io2, { preset, standards, turns, notes, effort, mediaImages: footage.length > 0 });
  const applied = res.applied + (extra?.applied || 0);
  const adjusted = [...res.issues, ...(extra?.issues || [])];
  io.step('apply', { state: 'done', detail: `${applied} applied${adjusted.length ? `, ${adjusted.length} adjusted` : ''}${notes.length ? ` · ${notes.filter(n => n.ops).length}/${notes.length} notes carried` : ''}` });

  io.step('check', { state: 'run' });
  let checks = await checkpoint(ws, preset, true);
  const failing = checks.filter(c => c.status === 'fail' || c.status === 'warn').length;
  io.step('check', { state: 'done', detail: failing ? `${failing} to look at` : 'all gates pass' });

  const rv = await reviewPasses(ws, io2, { preset, standards, effort, turns, res: { ...res, issues: adjusted }, checks, mediaImages: footage.length > 0, notes, revision: true, lost });
  checks = rv.checks;
  const summary = rv.message || plan.message || (plan.ops.length ? 'Done.' : 'No changes were needed.');
  await finishRound(ws, job, { summary, applied: applied + rv.applied, model, notes, scores: rv.scores }, turns);
  return { summary, applied: applied + rv.applied, issues: [...adjusted, ...rv.issues], model, checks };
}

/** Record the round on the project, with a short memory of the exchange for later rounds. */
async function finishRound(ws: Workspace, job: Job, out: { summary: string; applied: number; model?: string; notes: NoteCheck[]; scores?: Record<string, number> }, turns: Turn[]) {
  const round: Round = {
    n: job.round, kind: job.kind === 'create' ? 'create' : 'revise', at: Date.now(), jobId: job.id, effort: job.effort, presetId: job.presetId,
    brief: job.kind === 'create' ? job.request?.notes || '' : job.brief || '', fromCritic: job.fromCritic, summary: out.summary, applied: out.applied, model: out.model,
    ...(out.notes.length ? { notes: out.notes } : {}),
    ...(out.scores ? { selfScores: out.scores } : {}),
    snapshot: deepClone(ws.project),
  };
  // the memory later rounds read: this round's request, Opus's direction for it, and the last review's verdict
  const body = turns.filter((t, i) => i > 0 && !t.content.startsWith('You are the editor'));
  const ask0 = body.find(t => t.role === 'user');
  const plan0 = body.find(t => t.role === 'assistant');
  const lastRev = [...body].reverse().find(t => t.role === 'assistant' && t !== plan0);
  const memory: Turn[] = [];
  if (ask0) memory.push({ role: 'user', content: ask0.content.slice(0, 4000) });
  if (plan0) { const d = compactReply(plan0.content); memory.push({ role: 'assistant', content: d.length > 14000 ? `${d.slice(0, 14000)}… (the rest of the direction is shortened here; the CURRENT TIMELINE shows what was built)` : d }); }
  if (lastRev) memory.push({ role: 'user', content: 'Then the studio applied it and you reviewed the rendered frames.' }, { role: 'assistant', content: compactReply(lastRev.content).slice(0, 3000) });
  await ws.save(rec => {
    const rounds = (rec.rounds || []).filter(r => r.n !== round.n);
    rec.rounds = [...rounds, round].sort((a, b) => a.n - b.n);
    rec.aiTurns = memory;
    rec.director = { ...rec.director, presetId: job.presetId, effort: job.effort };
    if (job.kind === 'revise') rec.draft = '';
  });
}
