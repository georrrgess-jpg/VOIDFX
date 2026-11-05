// The critic: a second Opus pass with one job, to judge the edit as harshly as the best editors in
// TikTok's edit community would, against the owner's standards and the canon of top TikTok edits.
// It sees frames rendered from the edit (a dense filmstrip plus every transition), measured timing,
// the checkpoint and the owner's brief, and writes an assessment plus a write-up for the next round.
import { BENCHMARK_TEXT, HOUSE_RULES } from './knowledge';
import { checksText, runChecks } from '../engine/qc';
import { cutTimes, timelineBeats } from '../engine/evaluate';
import { measureLoopSeam } from '../engine/exporter';
import { TRANSITION_LABELS } from '../engine/transitions';
import { whenMediaIdle } from '../media/library';
import { getPreset } from '../state/catalog';
import { Critique, CritiqueIssue, Effort, Job } from '../state/types';
import { projectDuration } from '../state/util';
import { askSafe, JobIO, maxImagesFor, standardsForPreset, standardsText } from './director';
import { parseJson, timelineJson } from './prompt';
import { standardSheets, timelineSheets } from './sheets';
import type { Workspace } from './workspace';

export const CRITIC_AREAS: { id: string; label: string }[] = [
  { id: 'hook', label: 'Hook' },
  { id: 'rhythm', label: 'Rhythm & sync' },
  { id: 'transitions', label: 'Transitions' },
  { id: 'motion', label: 'Motion' },
  { id: 'text', label: 'Text' },
  { id: 'sound', label: 'Sound' },
  { id: 'concept', label: 'Concept & story' },
  { id: 'picture', label: 'Picture & framing' },
  { id: 'loop', label: 'Ending & loop' },
];

/** What separates the edits that travel on TikTok from the ones that get scrolled past. */
export const CRITIC_CANON = `THE TIKTOK EDIT CANON (what the top fan edits in the edit community do, and what gets scrolled past)
1. HOOK (0-1 s). The first frame is already striking and something hits within half a second: no fade in from black, no logo first, no slow establishing shot, no dead air. Viewers decide in about a second; a weak first second caps the whole edit.
2. THE SONG CUT. The strongest 15-30 s of the song (the drop, the chorus, the recognisable line), entered on a phrase and left on a phrase end or a hard stop that loops. A cut that starts mid-phrase or wanders through a verse reads as careless.
3. SYNC. Every cut and every effect sits on the beat grid; accents (snare, vocal chop, bass hit, riser peak) each get a visual event. Cuts drifting a few frames off the beat are the fastest tell of an amateur edit.
4. PACING. Contrast: build and release, a held breath before the drop, a burst on it; never one uniform pace. In a hype edit no shot sits for more than about a second without something happening in it.
5. MOTION. Velocity: speed ramps (burst on the hit, smooth slow motion between), shake and zoom punches on hits, motion blur. Static shots laid on a beat are the number-one mark of a weak edit; "smooth" does not mean slow.
6. TRANSITIONS. Purposeful, varied and tied to the content (match cuts on shape, movement or colour; whips matched in direction; objects that wipe the frame; going through something). The same preset transition repeated, or generic flash and glitch spam, looks like a template.
7. CLIP CHOICE. The most iconic, expressive moments of the character; faces readable and centred for 9:16; no soft, blocky or upscaled-looking clips, no burned-in subtitles, watermarks or black bars; consistent quality across sources.
8. COLOUR AND FINISH. One cohesive grade with real contrast; no flicker; sharp; sources matched; overlays and light leaks used sparingly and with intent.
9. TEXT. Few words, timed to the vocal or the line, readable at phone size, clear of faces and TikTok's interface, designed with intent; never paragraphs, default fonts, typos or text that pops on.
10. CONCEPT. The edit says something about the character (an arc, a rivalry, a turn) and has a moment people would comment on ("the transition at 0:07"). Without a concept it is a montage.
11. ENDING AND LOOP. It ends on its strongest image or hit and loops seamlessly in picture and sound, so the rewatch is invisible; no outro card, no fade to black that kills the loop.
12. SOUND DESIGN. Whooshes, impacts, risers and reverses placed exactly on the transitions; a clean, loud, unclipped mix; dialogue clear when used.
13. ORIGINALITY. A signature move; nothing that looks like a trend template or an earlier edit's look.
SCORING. 9-10: could stand with the best edits in its niche (viral calibre). 7-8: strong, needs polish. 5-6: competent but forgettable. Below 5: amateur flaws. Most edits honestly land between 4 and 7. Never inflate. Any critical issue caps the score at 6.5.`;

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
    `In the first second: ${hookEvents.join(', ') || 'nothing but the opening shot'}.`,
  ].filter(Boolean).join('\n');
}

/** Frame times for the critic: a dense sweep plus three frames around every transition. */
function filmstrip(ws: Workspace, maxFrames: number) {
  const p = ws.project, dur = projectDuration(p);
  const step = Math.max(1 / 3, dur / maxFrames);
  const sweep: number[] = [];
  for (let t = 0; t < dur - 1e-3; t += step) sweep.push(+t.toFixed(3));
  sweep.push(+Math.max(0, dur - 1 / p.fps).toFixed(3));
  const trans = p.clips.filter(c => c.transition).sort((a, b) => a.start - b.start).slice(0, 10);
  const close: { t: number; label: string }[] = [];
  for (const c of trans) {
    const d = c.transition!.dur || 0.4;
    const name = (TRANSITION_LABELS[c.transition!.type] || c.transition!.type).slice(0, 14);
    for (const [k, dt] of [['a', -d * 0.45], ['b', 0], ['c', d * 0.45]] as [string, number][]) {
      const t = Math.min(dur - 0.01, Math.max(0, c.start + dt));
      close.push({ t, label: `${name} ${k} ${t.toFixed(2)}s` });
    }
  }
  return { sweep, close };
}

function clampScore(v: any, d = 5) { const n = Number(v); return Number.isFinite(n) ? Math.max(0, Math.min(10, Math.round(n * 10) / 10)) : d; }

export function parseCritique(text: string, round: number, duration: number, model?: string): Critique | null {
  const v = parseJson(text);
  if (!v || typeof v !== 'object') return null;
  const scores: Record<string, number> = {};
  for (const a of CRITIC_AREAS) if (v.scores && v.scores[a.id] !== undefined) scores[a.id] = clampScore(v.scores[a.id]);
  const sev = (s: any): CritiqueIssue['severity'] => (s === 'critical' || s === 'major' || s === 'minor' ? s : 'major');
  const issues: CritiqueIssue[] = (Array.isArray(v.issues) ? v.issues : []).slice(0, 24).map((x: any) => ({
    severity: sev(x?.severity), at: Number.isFinite(Number(x?.at)) && x?.at !== null && x?.at !== '' ? Math.max(0, Number(x.at)) : undefined,
    area: String(x?.area || 'edit'), problem: String(x?.problem || x?.issue || '').trim(), fix: String(x?.fix || '').trim(),
  })).filter((x: CritiqueIssue) => x.problem);
  const order = { critical: 0, major: 1, minor: 2 };
  issues.sort((a, b) => order[a.severity] - order[b.severity] || (a.at ?? 999) - (b.at ?? 999));
  let score = clampScore(v.score);
  if (issues.some(i => i.severity === 'critical')) score = Math.min(score, 6.5);
  const verdict = v.verdict === 'ready' || v.verdict === 'close' || v.verdict === 'not ready' ? v.verdict : score >= 8.5 ? 'ready' : score >= 7 ? 'close' : 'not ready';
  return {
    at: Date.now(), model, score, verdict, headline: String(v.headline || '').trim() || 'No headline.', scores,
    strengths: (Array.isArray(v.strengths) ? v.strengths : []).map(String).filter(Boolean).slice(0, 8),
    issues, versus: String(v.versus || '').trim(), brief: String(v.brief || '').trim(), duration, round,
  };
}

/** One line per issue, as it is handed to Opus in a revision. */
export function issueLine(i: CritiqueIssue): string {
  return `[${i.severity}${i.at !== undefined ? ` @ ${i.at.toFixed(2)}s` : ''}, ${i.area}] ${i.problem}${i.fix ? ` Fix: ${i.fix}` : ''}`;
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

  io.step('render', { state: 'run' });
  const maxImg = Math.max(0, Math.min(maxImagesFor('extra'), 9));
  const stdImgs = maxImg >= 6 ? await standardSheets(standards.filter(s => s.kind === 'video' && s.state === 'ready'), 2) : [];
  const budget = Math.max(0, maxImg - stdImgs.length);
  const { sweep, close } = filmstrip(ws, Math.max(20, (budget - 1) * 20));
  const p = ws.project;
  const sweepSheets = budget ? await timelineSheets(p, ws.media(), sweep, 20, Math.max(1, budget - (close.length ? 1 : 0)), io.signal) : [];
  const closeSheets = budget > 1 && close.length ? await timelineSheets(p, ws.media(), close.map(c => c.t), 30, 1, io.signal, p.width / p.height < 1 ? 300 : 220, close.map(c => c.label)) : [];
  if (closeSheets[0]) closeSheets[0].caption = 'every transition as three frames (a: just before, b: the middle, c: just after), labelled with the transition name and timeline time';
  const images = [...sweepSheets, ...closeSheets, ...stdImgs];
  io.step('render', { state: images.length ? 'done' : 'skip', detail: images.length ? `${sweep.length + close.length} frames on ${images.length} sheets` : 'images not available here' });

  io.step('measure', { state: 'run' });
  const seam = await measureLoopSeam(p, ws.media()).catch(() => null);
  const checks = runChecks(p, ws.media(), { houseRules: preset.houseRules, duration: preset.duration, fps: preset.fps, seam });
  const metrics = editMetrics(ws);
  io.step('measure', { state: 'done', detail: `${checks.filter(c => c.status === 'fail').length} gates failing` });

  io.step('critic', { state: 'run', detail: 'watching…' });
  const rounds = ws.rec.rounds || [];
  const last = rounds[rounds.length - 1];
  const music = ws.order().map(id => ws.media()[id]).filter(m => m?.kind === 'audio' || (m?.hasAudio && m.analysis?.bpm));
  const prompt = [
    'You are the critic for VOIDFX Studio: the harshest, most knowledgeable judge in TikTok\'s edit community. You have studied thousands of fan edits (velocity edits, character edits, movie and TV edits, AMV-style and After Effects or CapCut work) and you know exactly why the top ones travel and the rest get scrolled past. Your job is not to encourage: it is to find everything that keeps this edit from being one of the best in its niche, say it plainly, and say how to fix it. Judge only what you can see in the frames and the measurements; you cannot hear the audio, so judge sound from the timing data and the sound effects placed.',
    CRITIC_CANON,
    preset.houseRules ? `THE OWNER'S TASTE (their house rules: an edit that breaks these fails, however good it looks)\n${HOUSE_RULES}` : '',
    preset.houseRules ? `THE OWNER'S APPROVED BENCHMARKS (the bar this edit must clear)\n${BENCHMARK_TEXT}` : '',
    standards.length ? `REFERENCE EDITS THE OWNER ADDED AS STANDARDS\n${standardsText(standards)}` : '',
    `PRESET "${preset.name}": ${preset.prompt || preset.description}`,
    last ? `WHAT THE OWNER ASKED FOR IN ROUND ${last.n}: ${last.brief || '(no extra notes)'}${last.fromCritic?.length ? `\nCritic points passed on for that round:\n- ${last.fromCritic.join('\n- ')}` : ''}${last.summary ? `\nTHE EDITOR (Opus) SAYS IT DID: ${last.summary}` : ''}` : '',
    rounds.filter(r => r.critique).length ? `EARLIER CRITIQUES (check whether their points were fixed)\n${rounds.filter(r => r.critique).map(r => `Round ${r.n}: ${r.critique!.score}/10, "${r.critique!.headline}"; issues: ${r.critique!.issues.slice(0, 8).map(i => i.problem).join(' | ')}`).join('\n')}` : '',
    `MEASURED\n${metrics}`,
    `AUTOMATED CHECKPOINT\n${checksText(checks)}`,
    music.length ? `MUSIC\n${music.map(m => `${m.id} "${m.name}" ${m.analysis?.bpm ? `${m.analysis.bpm} BPM` : ''}`).join('\n')}` : '',
    `THE TIMELINE (what the studio will render)\n${timelineJson(p).slice(0, 24000)}`,
    images.length ? `IMAGES (attached, in this order)\n${images.map((x, i) => `${i + 1}. ${x.caption}`).join('\n')}` : 'IMAGES: none attached; judge from the timeline and the measurements, and say that you could not see the picture.',
    `Write the assessment. Be specific: name the time, the shot, the transition. Every fix must be something the studio can do (re-cut on the beat, swap a shot, speed ramp, beat camera, a named transition, text timing or style, a sound, the loop). Reply with only JSON:
{"score": 0-10 with one decimal,
 "verdict": "not ready" | "close" | "ready",
 "headline": "one blunt sentence: the verdict in plain words",
 "scores": {${CRITIC_AREAS.map(a => `"${a.id}": 0-10`).join(', ')}},
 "strengths": ["what genuinely works (at most 4; empty if nothing does)"],
 "issues": [{"severity": "critical" | "major" | "minor", "at": seconds or null, "area": one of ${CRITIC_AREAS.map(a => a.id).join('/')}, "problem": "what is wrong and why it hurts the edit", "fix": "exactly what to change"}],
 "versus": "two or three sentences: how it stands against the owner's benchmarks and the best TikTok edits of this kind",
 "brief": "the write-up for the editor's next round: numbered, imperative instructions in priority order, ready to paste"}
Order issues by severity. Up to 14 issues.`,
  ].filter(Boolean).join('\n\n');
  const r = await askSafe(io2, prompt, images, effort, 'critic', t => {
    const n = (t.match(/"problem"\s*:/g) || []).length;
    return n ? `writing… ${n} issue${n > 1 ? 's' : ''} so far` : 'writing…';
  });
  const crit = parseCritique(r.text, job.round, projectDuration(p), model);
  if (!crit) throw { code: 'invalid_json' };
  io.step('critic', { state: 'done', detail: `${crit.score}/10 · ${crit.issues.length} issues` });

  await ws.save(rec => {
    const rs = rec.rounds || [];
    const target = rs.find(x => x.n === job.round) || rs[rs.length - 1];
    if (target) target.critique = crit;
    else rec.rounds = [{ n: job.round, kind: 'create', at: Date.now(), jobId: job.id, effort: job.effort, presetId: job.presetId, brief: '(edited by hand)', critique: crit }];
  });
  return crit;
}
