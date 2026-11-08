// The critic: a second Opus pass with one job, to judge the edit as exactingly as the best editors in
// TikTok's edit community would, against the owner's standards and the canon of top TikTok edits.
// It sees frames rendered from the edit (a dense filmstrip plus every transition), measured timing,
// the checkpoint and the owner's brief, and writes an assessment plus a write-up for the next round.
import { BENCHMARK_TEXT, HOUSE_RULES } from './knowledge';
import { EXEMPLARS } from './exemplars';
import { checksText, runChecks } from '../engine/qc';
import { cutTimes, timelineBeats } from '../engine/evaluate';
import { measureLoopSeam } from '../engine/exporter';
import { TRANSITION_LABELS } from '../engine/transitions';
import { FX_LIBRARY } from '../engine/fxlib';
import { SFX, TEXT_ANIMS_IN, TEXT_ANIMS_OUT, TRANSITIONS } from '../state/types';
import { whenMediaIdle } from '../media/library';
import { addLessons, calibrationText, getPreset, tasteText } from '../state/catalog';
import { Critique, CritiqueIssue, Effort, FollowUp, Job, PathStep } from '../state/types';
import { projectDuration } from '../state/util';
import { askSafe, brightnessNote, JobIO, maxImagesFor, ownerLedger, standardsForPreset, standardsText } from './director';
import { parseJson, timelineJson } from './prompt';
import { Sheet, standardSheets, timelineSheets } from './sheets';
import { PIECES } from '../state/pieces';
import { layerReport, loopStripTimes, transitionReport, transitionTimes } from './measure';
import type { Workspace } from './workspace';

export { CRITIC_AREAS, CRITIC_CANON } from './canon';
import { CRITIC_AREAS, CRITIC_CANON } from './canon';

function fmtT(t: number) { return `${t.toFixed(2)}s`; }

/** Numbers the critic cannot see in stills: cut timing against the beat, pacing, density, events in the hook. */
export function editMetrics(ws: Workspace): string {
  const p = ws.project, media = ws.media();
  const dur = projectDuration(p);
  const cuts = cutTimes(p).filter(t => t > 0.01 && t < dur - 0.01);
  const beats = timelineBeats(p, media).map(b => b.t);
  const near = (t: number, tol: number) => beats.some(b => Math.abs(b - t) <= tol);
  const onBeat = beats.length ? cuts.filter(t => near(t, 0.05)).length : null;
  const offBeat = beats.length ? cuts.filter(t => !near(t, 0.08)).map(fmtT) : [];
  const bounds = [0, ...cuts, dur];
  const shots = bounds.slice(1).map((t, i) => t - bounds[i]);
  const longest = shots.length ? Math.max(...shots) : dur;
  const longestAt = shots.length ? bounds[shots.indexOf(longest)] : 0;
  const trans = p.clips.filter(c => c.transition).sort((a, b) => a.start - b.start);
  const texts = p.clips.filter(c => c.kind === 'text').sort((a, b) => a.start - b.start);
  const sfx = p.clips.filter(c => c.kind === 'sfx');
  const ramps = p.clips.filter(c => c.kf?.speed?.length);
  const music = p.clips.filter(c => c.kind === 'audio' && c.media && media[c.media]?.analysis?.bpm);
  const lookTrackIds = new Set(p.tracks.filter(t => t.role === 'look').map(t => t.id));
  const looks = p.clips.filter(c => c.kind === 'shader' && lookTrackIds.has(c.track));
  const libFx = p.clips.filter(c => c.kind === 'shader' && c.preset && !lookTrackIds.has(c.track));
  const custom = p.clips.filter(c => (c.kind === 'graphic' || c.kind === 'shader') && !c.preset && !lookTrackIds.has(c.track));
  const layered = p.clips.filter(c => (c.kind === 'graphic' || c.kind === 'shader') && !lookTrackIds.has(c.track));
  const bare: string[] = [];
  for (let s0 = 0; s0 < Math.floor(dur); s0++) if (!layered.some(c => c.start < s0 + 1 && c.start + c.dur > s0)) bare.push(`${s0}-${s0 + 1}s`);
  const hookEvents = [
    ...cuts.filter(t => t < 1).map(t => `cut ${fmtT(t)}`),
    ...trans.filter(c => c.start < 1).map(c => `${c.transition!.type} ${fmtT(c.start)}`),
    ...texts.filter(c => c.start < 1).map(c => `text ${fmtT(c.start)}`),
    ...(p.camera?.on && beats.some(b => b < 1) ? ['beat camera hits'] : []),
  ];
  const perSec: number[] = Array.from({ length: Math.ceil(dur) }, () => 0);
  for (const t of cuts) perSec[Math.min(perSec.length - 1, Math.floor(t))]++;
  const drops = music.flatMap(c => (media[c.media!]?.analysis?.rises || []).map(r => c.start + (r - (c.in || 0))).filter(t => t >= 0 && t <= dur)).map(fmtT);
  return [
    `Length ${dur.toFixed(2)} s at ${p.width}x${p.height}, ${p.fps} fps.`,
    `Cuts on the main track: ${cuts.length} (${(cuts.length / Math.max(1, dur)).toFixed(2)} per second); cuts per second, second by second: ${perSec.join(' ')}.`,
    `Shot lengths: average ${(dur / Math.max(1, shots.length)).toFixed(2)} s, longest ${longest.toFixed(2)} s starting at ${fmtT(longestAt)}.`,
    beats.length ? `Beat grid: ${beats.length} beats under the edit; ${onBeat}/${cuts.length} cuts within 50 ms of a beat${offBeat.length ? `; off the beat (more than 80 ms): ${offBeat.slice(0, 20).join(', ')}` : ''}.` : 'No beat grid: the music has no steady pulse or no analysed music is used.',
    drops.length ? `Level rises (likely drops) in the music at: ${drops.slice(0, 8).join(', ')}.` : '',
    `Transitions (${trans.length}): ${trans.map(c => `${fmtT(c.start)} ${TRANSITION_LABELS[c.transition!.type] || c.transition!.type}`).join(', ') || 'none'}.`,
    `Text (${texts.length}): ${texts.map(c => `${fmtT(c.start)}-${fmtT(c.start + c.dur)} "${(c.text || '').replace(/\s+/g, ' ').slice(0, 60)}" (${c.anim?.in || 'none'} in)`).join('; ') || 'none'}.`,
    `Sound effects: ${sfx.length}. Speed-ramped clips: ${ramps.length}. Beat camera: ${p.camera?.on ? `on (punch ${p.camera.punch}, kick ${p.camera.kick})` : 'off'}.`,
    `Look: ${looks.map(c => `${c.preset}${c.span === 'all' ? ' over the whole edit' : ` ${fmtT(c.start)}-${fmtT(c.start + c.dur)}`}`).join(', ') || 'none (no library look: the footage keeps its own grade)'}.`,
    `Library effects (${libFx.length}): ${libFx.map(c => `${fmtT(c.start)}-${fmtT(c.start + c.dur)} ${c.preset}`).join(', ') || 'none'}.`,
    `Custom graphics and effects designed for this edit (${custom.length}): ${custom.map(c => `${fmtT(c.start)}-${fmtT(c.start + c.dur)} ${c.kind === 'shader' ? 'effect' : 'graphic'} ${c.id}${c.name ? ` "${c.name}"` : ''}${c.blend && c.blend !== 'normal' ? ` (${c.blend})` : ''}`).join(', ') || 'none'}. Judge in the frames whether each looks designed, attached to the action and lit like the shot, or drawn on top.`,
    `Seconds with no graphic or effect layer at all: ${bare.length ? bare.join(', ') : 'none'}.`,
    `In the first second: ${hookEvents.join(', ') || 'nothing but the opening shot'}.`,
  ].filter(Boolean).join('\n');
}

/** Frame times for the critic: a dense sweep plus three frames around every transition. */
function filmstrip(ws: Workspace, maxFrames: number, follow: { id: string; at: number }[] = []) {
  const p = ws.project, dur = projectDuration(p);
  const step = Math.max(1 / 3, dur / maxFrames);
  const sweep: number[] = [];
  for (let t = 0; t < dur - 1e-3; t += step) sweep.push(+t.toFixed(3));
  sweep.push(+Math.max(0, dur - 1 / p.fps).toFixed(3));
  const close: { t: number; label: string }[] = [];
  // the moments earlier points were about, so the critic can see whether they were fixed
  for (const f of follow.slice(0, 8)) { const t = Math.min(dur - 0.01, Math.max(0, f.at)); close.push({ t, label: `${f.id} ${t.toFixed(2)}s` }); }
  const tframes = transitionTimes(p, 30 - close.length);
  for (const f of tframes) close.push({ t: f.t, label: f.label });
  return { sweep, close, tframes };
}

function clampScore(v: any, d = 5) { const n = Number(v); return Number.isFinite(n) ? Math.max(0, Math.min(10, Math.round(n * 10) / 10)) : d; }

export function parseCritique(text: string, round: number, duration: number, model?: string, prev?: { id: string; text: string }[], prevScore?: number): Critique | null {
  const v = parseJson(text);
  if (!v || typeof v !== 'object') return null;
  const scores: Record<string, number> = {};
  for (const a of CRITIC_AREAS) if (v.scores && v.scores[a.id] !== undefined) scores[a.id] = clampScore(v.scores[a.id]);
  const sev = (s: any): CritiqueIssue['severity'] => (s === 'critical' || s === 'major' || s === 'minor' ? s : 'major');
  const issues: CritiqueIssue[] = (Array.isArray(v.issues) ? v.issues : []).slice(0, 24).map((x: any) => ({
    severity: sev(x?.severity), at: Number.isFinite(Number(x?.at)) && x?.at !== null && x?.at !== '' ? Math.max(0, Number(x.at)) : undefined,
    area: String(x?.area || 'edit'), problem: String(x?.problem || x?.issue || '').trim(), fix: String(x?.fix || '').trim(),
    ...(Number.isFinite(Number(x?.gain)) && Number(x.gain) > 0 ? { gain: Math.min(3, Math.round(Number(x.gain) * 10) / 10) } : {}),
  })).filter((x: CritiqueIssue) => x.problem);
  const order = { critical: 0, major: 1, minor: 2 };
  // the biggest wins first: what fixing it is worth, then severity
  issues.sort((a, b) => (b.gain ?? 0) - (a.gain ?? 0) || order[a.severity] - order[b.severity] || (a.at ?? 999) - (b.at ?? 999));
  const num = (x: any) => (Number.isFinite(Number(x)) && x !== null && x !== '' ? Number(x) : undefined);
  const path: PathStep[] = (Array.isArray(v.path) ? v.path : []).slice(0, 6).map((x: any) => ({ change: String(x?.change || '').trim(), at: num(x?.at), to: num(x?.to), gain: Math.max(0, Math.min(3, num(x?.gain) ?? 0)) })).filter((x: PathStep) => x.change);
  let score = clampScore(v.score);
  // the overall score follows the area scores (weighted toward hook, transitions, motion, concept), within half a point
  const W: Record<string, number> = { hook: 1.25, transitions: 1.2, motion: 1.15, concept: 1.1 };
  const areas = Object.entries(scores);
  if (areas.length >= 5) {
    const mean = areas.reduce((a, [k, v]) => a + v * (W[k] || 1), 0) / areas.reduce((a, [k]) => a + (W[k] || 1), 0);
    score = Math.round(Math.max(mean - 0.5, Math.min(mean + 0.5, score)) * 10) / 10;
  }
  if (issues.some(i => i.severity === 'critical')) score = Math.min(score, 7);
  const verdict = v.verdict === 'ready' || v.verdict === 'close' || v.verdict === 'not ready' ? v.verdict : score >= 8.5 ? 'ready' : score >= 7 ? 'close' : 'not ready';
  const st = (x: any): FollowUp['status'] => { const k = String(x || '').toLowerCase(); return k.startsWith('fix') || k === 'done' ? 'fixed' : k.startsWith('part') ? 'partly' : 'not'; };
  const followUp: FollowUp[] = (Array.isArray(v.followUp) ? v.followUp : []).slice(0, 30).map((x: any) => ({
    id: String(x?.id || '').trim().toUpperCase(), status: st(x?.status), comment: String(x?.comment || '').trim(),
  })).filter((x: FollowUp) => x.id);
  if (prev) for (const f of followUp) f.text = prev.find(q => q.id === f.id)?.text;
  return {
    at: Date.now(), model, score, verdict, headline: String(v.headline || '').trim() || 'No headline.', scores,
    strengths: (Array.isArray(v.strengths) ? v.strengths : []).map(String).filter(Boolean).slice(0, 8),
    issues, versus: String(v.versus || '').trim(), brief: String(v.brief || '').trim(), duration, round,
    ...(followUp.length ? { followUp } : {}), ...(prevScore !== undefined ? { prevScore } : {}), ...(path.length ? { path } : {}),
  };
}

/** One line per issue, as it is handed to Opus in a revision. */
export function issueLine(i: CritiqueIssue): string {
  return `[${i.severity}${i.at !== undefined ? ` @ ${i.at.toFixed(2)}s` : ''}, ${i.area}${i.gain ? `, worth +${i.gain.toFixed(1)}` : ''}] ${i.problem}${i.fix ? ` Fix: ${i.fix}` : ''}`;
}

/** One step of the path to 8, as it is handed to Opus: the biggest changes come first in a revision. */
export function pathLine(s: PathStep): string {
  return `[PATH TO 8${s.at !== undefined ? ` @ ${s.at.toFixed(2)}s${s.to !== undefined ? `-${s.to.toFixed(2)}s` : ''}` : ''}, worth +${s.gain.toFixed(1)}] ${s.change}`;
}

/** The studio's vocabulary, so every fix the critic writes is one the editor can carry out exactly. */
export function toolsLine(): string {
  const groups = new Map<string, string[]>();
  for (const d of FX_LIBRARY) groups.set(d.group, [...(groups.get(d.group) || []), d.id]);
  return `THE STUDIO'S TOOLS (write every fix in these terms)
- Transitions: ${TRANSITIONS.join(', ')} (dive, shatter, shutter, iris, ripple, swirl take anchors "at"/"to").
- Library looks (one grade over the edit or a section): ${(groups.get('look') || []).join(', ')}.
- Library effects: ${[...groups.entries()].filter(([g]) => g !== 'look').map(([g, ids]) => `${g}: ${ids.join(', ')}`).join('; ')}.
- Text animations in: ${TEXT_ANIMS_IN.join(', ')}; out: ${TEXT_ANIMS_OUT.join(', ')}; knockout type, motif particles, the house caption style, timed lyric captions.
- Sounds: ${SFX.join(', ')}.
- Set pieces in one operation (tested builds): ${PIECES.map(d => d.id).join(', ')}.
- Also: velocity ramps, freezes (speed keys to 0.05), the beat camera (punch, kick), focus framing, push-ins (scale keys), custom GLSL effects and SVG graphics written for the edit.`;
}

export function criticSteps(): Job['steps'] {
  return [
    { id: 'media', label: 'Open the edit', state: 'wait' },
    { id: 'render', label: 'Render a filmstrip of every moment', state: 'wait' },
    { id: 'measure', label: 'Measure timing, sync and the checkpoint', state: 'wait' },
    { id: 'critic', label: 'The critic watches and writes', state: 'wait' },
  ];
}

/** Run the critic on the project's current edit and attach the critique to the latest round. */
export async function critiqueEdit(job: Job, ws: Workspace, io: JobIO): Promise<Critique> {
  const preset = await getPreset(job.presetId);
  const standards = await standardsForPreset(preset);
  const effort: Effort = job.effort === 'low' || job.effort === 'medium' ? 'high' : job.effort;
  let model: string | undefined;
  const io2: JobIO = { ...io, model: m => { model = m; io.model(m); } };

  io.step('media', { state: 'run' });
  await ws.attach();
  await whenMediaIdle(240000, ws, io.signal);
  if (!ws.project.clips.length) throw { code: 'no_edit' };
  io.step('media', { state: 'done', detail: `${ws.ready().length} files` });

  const rounds = ws.rec.rounds || [];
  const last = rounds.find(r => r.n === job.round) || rounds[rounds.length - 1];
  const prevCrit = [...rounds].filter(r => r.critique && r.n < (last?.n ?? job.round)).sort((a, b) => b.n - a.n)[0]?.critique;
  // what this round was asked to fix: its numbered notes, else the last critique's points
  const follow: { id: string; text: string; at?: number; plan?: string; check?: string }[] = last?.notes?.length
    ? last.notes.map(n => ({ id: n.id, text: n.text, at: n.at, plan: n.plan, check: n.status ? `${n.status}${n.check ? `: ${n.check}` : ''}` : undefined }))
    : prevCrit ? prevCrit.issues.map((i, k) => ({ id: `P${k + 1}`, text: issueLine(i), at: i.at })) : [];

  io.step('render', { state: 'run' });
  const maxImg = Math.max(0, Math.min(maxImagesFor('extra'), 9));
  const stdImgs = maxImg >= 6 ? await standardSheets(standards.filter(s => s.kind === 'video' && s.state === 'ready'), 2) : [];
  const budget = Math.max(0, maxImg - stdImgs.length);
  const { sweep, close, tframes } = filmstrip(ws, Math.max(20, (budget - 1) * 20), follow.filter(f => f.at !== undefined).map(f => ({ id: f.id, at: f.at! })));
  const p = ws.project;
  const sweepSheets = budget ? await timelineSheets(p, ws.media(), sweep, 20, Math.max(1, budget - (close.length ? 1 : 0) - (budget >= 4 ? 1 : 0)), io.signal) : [];
  // motion strips: consecutive frames (1/12 s apart) at the hook, the drop and across the loop, so movement and flow are judged, not guessed from stills
  const motion: { t: number; label: string }[] = [];
  if (budget >= 4) {
    const dur = projectDuration(p);
    for (let k = 0; k < 7; k++) motion.push({ t: +(k / 12).toFixed(3), label: `HOOK +${(k / 12).toFixed(2)}` });
    const bed = p.clips.filter(c => c.kind === 'audio' && c.media && ws.media()[c.media]?.analysis).sort((a, b) => b.dur - a.dur)[0];
    const drop = bed ? (ws.media()[bed.media!].analysis!.rises || []).map(r => bed.start + (r - (bed.in ?? 0)) / (bed.speed ?? 1)).find(t => t > dur * 0.2 && t < dur * 0.8) : undefined;
    if (drop !== undefined) for (let k = -3; k <= 4; k++) motion.push({ t: +Math.max(0, Math.min(dur - 0.01, drop + k / 12)).toFixed(3), label: `DROP ${k >= 0 ? '+' : ''}${(k / 12).toFixed(2)}` });
    const ls = loopStripTimes(p);
    ls.times.forEach((t, k) => motion.push({ t, label: ls.labels[k] }));
  }
  const motionSheets = motion.length ? await timelineSheets(p, ws.media(), motion.map(m => m.t), 32, 1, io.signal, p.width / p.height < 1 ? 300 : 220, motion.map(m => m.label)).catch(() => [] as Sheet[]) : [];
  if (motionSheets[0]) motionSheets[0].caption = 'MOTION STRIPS: consecutive frames 1/12 s apart at the hook (HOOK), across the drop (DROP), and across the loop (the last second of the edit, LAST FRAME, then FRAME 0 and the first 0.4 s): judge movement, rhythm and the loop landing from these, as a viewer would see them play';
  const closeSheets = budget > 1 && close.length ? await timelineSheets(p, ws.media(), close.map(c => c.t), 30, 1, io.signal, p.width / p.height < 1 ? 300 : 220, close.map(c => c.label)) : [];
  if (closeSheets[0]) closeSheets[0].caption = `${close.some(c => /^[NP]\d/.test(c.label)) ? 'the moments of the points this round was asked to fix (labelled with their ids), then ' : ''}every transition as three frames (a: just before, b: the middle, c: just after), labelled with the transition name and timeline time`;
  const images = [...sweepSheets, ...closeSheets, ...motionSheets, ...stdImgs];
  io.step('render', { state: images.length ? 'done' : 'skip', detail: images.length ? `${sweep.length + close.length} frames on ${images.length} sheets` : 'images not available here' });

  io.step('measure', { state: 'run' });
  const seam = await measureLoopSeam(p, ws.media()).catch(() => null);
  const checks = runChecks(p, ws.media(), { houseRules: preset.houseRules, duration: preset.duration, fps: preset.fps, seam });
  const metrics = editMetrics(ws);
  const layers = await layerReport(p, ws.media(), io.signal).catch(() => ({ text: '' }));
  io.step('measure', { state: 'done', detail: `${checks.filter(c => c.status === 'fail').length} gates failing` });

  io.step('critic', { state: 'run', detail: 'watching…' });
  const music = ws.order().map(id => ws.media()[id]).filter(m => m?.kind === 'audio' || (m?.hasAudio && m.analysis?.bpm));
  const prompt = [
    'You are the critic for VOIDFX Studio: the most knowledgeable, exacting judge in TikTok\'s edit community. You have studied thousands of fan edits (velocity edits, character edits, movie and TV edits, AMV-style and After Effects or CapCut work) and you know exactly why the top ones travel and the rest get scrolled past. Your job is to score the edit honestly against the owner\'s approved benchmarks (an edit at their level is an 8), credit what works, find everything that keeps it from the best in its niche, say it plainly, and say exactly how to fix it. Judge only what you can see in the frames and the measurements; you cannot hear the audio, so judge sound from the timing data and the sound effects placed.',
    CRITIC_CANON,
    preset.houseRules ? `THE OWNER'S TASTE (their house rules: an edit that breaks these fails, however good it looks)\n${HOUSE_RULES}` : '',
    preset.houseRules ? `THE OWNER'S APPROVED BENCHMARKS (the bar this edit must clear)\n${BENCHMARK_TEXT}` : '',
    preset.houseRules ? EXEMPLARS : '',
    standards.length ? `REFERENCE EDITS THE OWNER ADDED AS STANDARDS\n${standardsText(standards)}` : '',
    `PRESET "${preset.name}": ${preset.prompt || preset.description}`,
    last ? `WHAT THE OWNER ASKED FOR IN ROUND ${last.n}: ${last.brief || '(no extra notes)'}${last.fromCritic?.length ? `\nCritic points passed on for that round:\n- ${last.fromCritic.join('\n- ')}` : ''}${last.summary ? `\nTHE EDITOR (Opus) SAYS IT DID: ${last.summary}` : ''}` : '',
    ownerLedger(rounds) ? `${ownerLedger(rounds)}\nNever write an issue or a fix that undoes or contradicts these; where the owner chose something (a song section, a look, a shot, a text style), judge how well it is done, not whether it was chosen. A point that conflicts with them is left out.` : '',
    await calibrationText(),
    tasteText() ? `THE OWNER'S OWN NOTES ON RECENT EDITS (their taste, across projects)\n${tasteText(3000)}` : '',
    prevCrit?.path?.length ? `YOUR PATH TO 8 LAST ROUND (check each step in the frames; a step not done stays on the path, first)\n${prevCrit.path.map(s => `- +${s.gain.toFixed(1)}${s.at !== undefined ? ` @ ${s.at.toFixed(2)}s` : ''}: ${s.change}`).join('\n')}` : '',
    prevCrit?.issues?.length ? `YOUR POINTS LAST ROUND (stay consistent: never ask for the opposite of a point that was carried out, and do not move the goalposts on a point that is now fixed)\n${prevCrit.issues.slice(0, 12).map(i => `- [${i.severity}${i.at !== undefined ? ` @ ${i.at.toFixed(2)}s` : ''}] ${i.problem.slice(0, 160)} Fix: ${i.fix.slice(0, 140)}`).join('\n')}` : '',
    rounds.filter(r => r.critique && r.n !== last?.n).length ? `EARLIER CRITIQUES\n${rounds.filter(r => r.critique && r.n !== last?.n).map(r => `Round ${r.n}: ${r.critique!.score}/10, "${r.critique!.headline}"`).join('\n')}` : '',
    follow.length ? `WHAT THIS ROUND WAS ASKED TO FIX (check every item in the frames and the timeline; frames labelled with an item's id show its moment)\n${follow.map(f => `${f.id}${f.at !== undefined ? ` @ ${f.at.toFixed(2)}s` : ''}: ${f.text.slice(0, 320)}${f.plan ? ` | the editor's plan: ${f.plan.slice(0, 200)}` : ''}${f.check ? ` | the editor's own check: ${f.check.slice(0, 160)}` : ''}`).join('\n')}\nGive each item's status in "followUp": fixed (the frames or timeline show it done in full), partly, or not.` : '',
    prevCrit ? `THE LAST ROUND SCORED ${prevCrit.score}/10 (${CRITIC_AREAS.filter(a => prevCrit.scores[a.id] !== undefined).map(a => `${a.id} ${prevCrit.scores[a.id]}`).join(', ')}). That number is context, not a starting point: score the edit as it is now, fresh, on the calibrated scale. If the round rebuilt its weak moments well, the score moves by as much as the edit got better, and a point or more is normal when the big problems are gone; if it got worse, it goes down. Credit every fix you can see; a fix you cannot see in the frames or the timeline does not count.` : '',
    p.lyrics?.lines.length ? `THE SONG'S LYRICS (from the owner${p.lyrics.timed ? '; song times' : ', untimed'}): check that every caption is a sung line on its time, never invented words\n${p.lyrics.lines.slice(0, 80).map((l, i) => `${p.lyrics!.timed ? `L${i + 1} ${l.t.toFixed(2)} ` : ''}${l.text}`).join('\n')}` : 'NO LYRICS WERE SUPPLIED: any caption that claims to be a sung line is a guess; flag captions that do not read as dialogue, a designed title or a likely sung hook.',
    `MEASURED\n${metrics}${brightnessNote(sweepSheets) ? `\n${brightnessNote(sweepSheets).replace(/ On a phone,.*$/, '').replace(/: fine\.$/, '.')}` : ''}${closeSheets.length ? `\n${transitionReport(p, tframes, closeSheets).text}` : ''}${layers.text ? `\n${layers.text}` : ''}`,
    `AUTOMATED CHECKPOINT\n${checksText(checks)}`,
    music.length ? `MUSIC\n${music.map(m => `${m.id} "${m.name}" ${m.analysis?.bpm ? `${m.analysis.bpm} BPM` : ''}`).join('\n')}` : '',
    `THE TIMELINE (what the studio will render)\n${timelineJson(p).slice(0, 24000)}`,
    images.length ? `IMAGES (attached, in this order)\n${images.map((x, i) => `${i + 1}. ${x.caption}`).join('\n')}` : 'IMAGES: none attached; judge from the timeline and the measurements, and say that you could not see the picture.',
    toolsLine(),
    `Write the assessment. Be specific: name the time, the shot, the transition. Look hard at the animation itself: name every transition or animation that is weak (empty or invisible in its close-up, badly timed, looks drawn on), repetitive (the same move, effect or title animation again, or the same family crowded together) or generic (a stock library move where the shot offers something to go through), and give each its replacement: a different designed move in studio terms with its anchor and sound, never "make it better". Name every shot that just sits there with nothing designed on it (the checkpoint lists them) and the moment to add there. Judge the edit as a whole, the way the owner watches it: cohesion (one look, one concept, shots and moves that belong together, a flow that carries across the cuts) and motion are read from the motion strips and the order of the filmstrip, not from single stills; an edit that holds together as one piece earns that in concept, rhythm and picture even where a single still looks plain. Judge the loop from its strip: it must play as one designed move landing on frame 0. Every fix must be something the studio can do, named in its terms above, with the time and the values (for example: "transition dive at 7.80 with at (0.50, 0.41) and to (0.50, 0.43), sound whoosh + subdrop", "fx light_rays 0-2.4 s anchored at (0.62, 0.18)", "look noir_red with keep #c70f14"). Reply with only JSON:
{"score": 0-10 with one decimal,
 "verdict": "not ready" | "close" | "ready",
 "headline": "one blunt sentence: the verdict in plain words",
 "scores": {${CRITIC_AREAS.map(a => `"${a.id}": 0-10`).join(', ')}},
 "strengths": ["what genuinely works (at most 4; empty if nothing does)"],
 "issues": [{"severity": "critical" | "major" | "minor", "at": seconds or null, "area": one of ${CRITIC_AREAS.map(a => a.id).join('/')}, "problem": "what is wrong and why it hurts the edit", "fix": "exactly what to change", "gain": the score this fix is worth when done well (0.1-1.5), "lesson": "for critical and major issues: the general rule it breaks, one sentence true for any edit (no clip ids or times), so the studio can learn it"}],
 "versus": "two or three sentences: how it stands against the owner's benchmarks and the best TikTok edits of this kind",${follow.length ? `
 "followUp": [{"id": "${follow[0].id}", "status": "fixed" | "partly" | "not", "comment": "what the frames show"}],` : ''}
 "path": [{"change": "one big change, a section rebuilt or a set piece redesigned, in the studio's terms", "at": start seconds or null, "to": end seconds or null, "gain": the score it is worth}],
 "brief": "the write-up for the editor's next round: numbered, imperative instructions in priority order (the path first), each with its time and the studio tool that does it, ready to paste"}
THE PATH TO 8: three to five changes, biggest first, whose gains add up to what takes this edit to 8 or more. Think in sections and set pieces (rebuild the hook, redesign the drop, make the loop a set piece, one look across the edit), not in tweaks. Issues: up to 10; merge points that share a cause into one; every issue names its gain. Order issues by gain.`,
  ].filter(Boolean).join('\n\n');
  const r = await askSafe(io2, prompt, images, effort, 'critic', t => {
    const n = (t.match(/"problem"\s*:/g) || []).length;
    return n ? `writing… ${n} issue${n > 1 ? 's' : ''} so far` : 'writing…';
  });
  const crit = parseCritique(r.text, job.round, projectDuration(p), model, follow.map(f => ({ id: f.id, text: f.text })), prevCrit?.score);
  if (!crit) throw { code: 'invalid_json' };
  // the studio learns from it: serious findings go into the lessons every later edit is directed with
  // (the critic's general rule when it wrote one; else the problem's first sentence)
  const raw: any = parseJson(r.text);
  const lessonOf = (i: CritiqueIssue, k: number) => { const x = Array.isArray(raw?.issues) ? raw.issues.find((y: any) => String(y?.problem || '').trim() === i.problem) : undefined; return typeof x?.lesson === 'string' && x.lesson.trim() ? x.lesson.trim() : ''; };
  void addLessons(crit.issues.filter(i => i.severity !== 'minor').slice(0, 8).map((i, k) => ({ area: i.area, severity: i.severity as 'critical' | 'major', problem: lessonOf(i, k) || i.problem, fix: lessonOf(i, k) ? '' : i.fix, project: ws.rec.name })));
  const fixed = crit.followUp?.filter(f => f.status === 'fixed').length || 0;
  io.step('critic', { state: 'done', detail: `${crit.score}/10${prevCrit ? ` (was ${prevCrit.score})` : ''} · ${crit.issues.length} issues${crit.followUp?.length ? ` · ${fixed}/${crit.followUp.length} points fixed` : ''}` });

  await ws.save(rec => {
    const rs = rec.rounds || [];
    const target = rs.find(x => x.n === job.round) || rs[rs.length - 1];
    if (target) target.critique = crit;
    else rec.rounds = [{ n: job.round, kind: 'create', at: Date.now(), jobId: job.id, effort: job.effort, presetId: job.presetId, brief: '(edited by hand)', critique: crit }];
  });
  return crit;
}
