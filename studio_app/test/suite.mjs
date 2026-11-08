// Automated pass/fail suite (after `node build.mjs`; media from test/make_media.sh).
// A scripted stand-in for Opus answers every call the way the studio expects, so every path runs:
//  1. four AI edits at once, one per effort level (multitasking), while another project is edited
//  2. the critic, a revision with numbered notes, an automatic round chained after it
//  3. cancel and resume a running build; a build whose layers call fails twice
//  4. export: the MP4 is decoded and measured (streams, length, loudness, true peak, not black)
//  5. every transition, look, effect and text animation renders (compiles, visible, changes the picture)
//  6. everything survives a reload
// Prints one line per check and exits 1 if any fails. Writes the export and a report to test/out/.
import { createRequire } from 'node:module';
import http from 'node:http';
import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync, mkdirSync, existsSync, statSync } from 'node:fs';
import { join, extname, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const OUT = join(ROOT, 'test', 'out');
mkdirSync(OUT, { recursive: true });
const ONLY = process.env.ONLY ? process.env.ONLY.split(',') : null;
const on = name => !ONLY || ONLY.includes(name);

const types = { '.html': 'text/html', '.mp4': 'video/mp4', '.wav': 'audio/wav', '.png': 'image/png' };
const server = http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  const file = url === '/' ? join(ROOT, 'dist', 'index.html') : join(ROOT, url);
  if (!file.startsWith(ROOT) || !existsSync(file) || statSync(file).isDirectory()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'content-type': types[extname(file)] || 'application/octet-stream' });
  res.end(readFileSync(file));
});
await new Promise(r => server.listen(8778, r));

const results = [];
const t0 = Date.now();
function check(name, ok, detail = '') {
  results.push({ name, ok: !!ok, detail });
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? `  (${detail})` : ''}`);
}

const browser = await chromium.launch({ args: ['--autoplay-policy=no-user-gesture-required'] });
const ctx = await browser.newContext({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 1 });
const page = await ctx.newPage();
const errors = [];
page.on('pageerror', e => errors.push('pageerror: ' + e.message));
page.on('console', m => { if (m.type() === 'error' && !/favicon|fonts\.g/.test(m.text())) errors.push('console: ' + m.text()); });

// ---------- the scripted stand-in for Opus ----------
await ctx.addInitScript(() => {
  window.__calls = [];
  window.__saved = [];
  window.__parts = [];
  const toB64 = async blob => {
    const buf = new Uint8Array(await blob.arrayBuffer());
    let s = '';
    for (let i = 0; i < buf.length; i += 0x8000) s += String.fromCharCode.apply(null, buf.subarray(i, i + 0x8000));
    return btoa(s);
  };
  const TRANS = ['dive', 'shatter', 'ink', 'cube_left', 'blink', 'tear', 'slash', 'light_sweep', 'logo', 'punch', 'wash', 'shutter'];
  const PICTURE = new Set(['clear', 'project', 'add', 'look', 'track']);
  function planFrom(text) {
    const media = [...text.matchAll(/^(m[a-z0-9]+) (video|audio|image) "([^"]+)" ([\d.]+s|still image)/gm)].map(m => ({ id: m[1], kind: m[2], dur: m[4] === 'still image' ? 3 : parseFloat(m[4]) }));
    const ops = [{ op: 'clear' }, { op: 'project', camera: { on: true, every: 'beat', punch: 0.055, kick: 1 } }];
    let t = 0, k = 0;
    const vis = media.filter(m => m.kind !== 'audio');
    for (let round = 0; round < 3; round++) for (const m of vis) {
      if (k >= 7) break;
      const dur = 1.5;
      const op = { op: 'add', id: `v${k}`, media: m.id, track: 'V1', in: m.kind === 'image' ? 0 : Math.min(Math.max(0, m.dur - dur - 0.6), round * 0.9 + 0.2), dur, focus: { x: 0.5, y: 0.42 } };
      if (k > 0) op.transition = { type: TRANS[(k - 1) % TRANS.length] };
      if (op.transition?.type === 'dive') op.transition.at = { x: 0.5, y: 0.4 };
      if (op.transition?.type === 'shatter') op.transition.at = { x: 0.6, y: 0.7 };
      if (k === 1) op.ramp = { fast: 2, slow: 0.5 };
      ops.push(op); t += dur; k++;
    }
    const music = media.find(m => m.kind === 'audio');
    if (music) ops.push({ op: 'add', id: 'mus', media: music.id, track: 'A1', start: 0, in: 0, dur: Math.min(music.dur, t) });
    ops.push({ op: 'look', preset: 'noir_red' });
    ops.push({ op: 'text', id: 'cap', start: 0.3, dur: 2.2, text: 'COULD IT BE\n*HIM*', words: [0, 0.25, 0.5, 0.9], style: { font: 'Inter', weight: 900, uppercase: true, size: 0.046, lineScales: [1, 1.3] }, anim: { in: 'words', out: 'cap' }, transform: { y: 0.25 } });
    ops.push({ op: 'text', id: 'hero', start: 3.2, dur: 1.6, text: '*ALONG*', style: { size: 0.085, uppercase: true, motif: 'blood' }, anim: { in: 'bloom', out: 'blowaway', inDur: 0.8, outDur: 0.6 }, transform: { y: 0.27 } });
    ops.push({ op: 'text', id: 'knock', start: 6.0, dur: 1.4, text: 'BAY HARBOR\nBUTCHER', style: { size: 0.09, uppercase: true, knockout: true, fit: true }, anim: { in: 'slam', out: 'zoom', inDur: 0.4, outDur: 0.35 } });
    ops.push({ op: 'fx', id: 'rays', preset: 'light_rays', start: 0.2, dur: 2.0, at: { x: 0.62, y: 0.18 } });
    ops.push({ op: 'fx', id: 'wash', preset: 'exposure_wash', start: 4.3, dur: 0.45, over: true });
    ops.push({ op: 'shader', id: 'oops', start: 5.0, dur: 0.4, code: 'vec4 effect(vec2 uv, float t, float p) { return vec4(nope(uv), 1.0); }' });
    ops.push({ op: 'graphic', id: 'emb', start: 0.4, dur: 1.0, gw: 0.4, svg: '<svg viewBox="0 0 400 400"><circle cx="200" cy="200" r="170" fill="none" stroke="#ffd23f" stroke-width="16"/></svg>' });
    ops.push({ op: 'sfx', sound: 'riser', start: 1.4, volume: 0.3 });
    ops.push({ op: 'sounds', volume: 0.3 });
    return { message: 'Concept: the evidence points back at him.', ops };
  }
  const reply = (text, opts) => { opts.onText?.({ text, delta: text }); return { text, truncated: false, modelTierApplied: 'complex', modelApplied: opts.model }; };
  window.claude = {
    use: async name => {
      if (name === 'sample') {
        const f = async (input, opts = {}) => {
          const turns = typeof input === 'string' ? [{ role: 'user', content: input }] : input;
          const full = turns.map(t => t.content).join('\n\n=====\n\n');
          const last = turns[turns.length - 1].content;
          const call = { roles: turns.length, chars: full.length, images: (opts.images || []).length, effort: opts.effort, last: last.slice(0, 80) };
          window.__calls.push(call);
          const wait = window.__slow || 120;
          await new Promise((r, j) => {
            const tm = setTimeout(r, wait);
            opts.signal?.addEventListener('abort', () => { clearTimeout(tm); j(Object.assign(new Error('aborted'), { name: 'AbortError' })); });
          });
          if (full.includes('You are casting material')) {
            const ids = [...full.matchAll(/^(lib\S+) /gm)].map(m => m[1]);
            return reply(JSON.stringify({ items: ids.map(id => ({ id, why: 'test' })), message: 'Took everything.' }), opts);
          }
          if (full.includes('You are the critic for VOIDFX Studio')) {
            call.critic = true;
            call.anchored = full.includes('THE LAST ROUND SCORED');
            call.fresh = !full.includes('starting from that score');
            const follow = [...full.matchAll(/^(N\d+)(?: @ [\d.]+s)?: /gm)].map(m => m[1]);
            return reply(JSON.stringify({
              score: call.anchored ? 7.1 : 6.2, verdict: 'not ready', headline: 'Competent, but the hook is soft.',
              scores: call.anchored ? { hook: 7, rhythm: 7, transitions: 7.5, motion: 7, text: 7.5, sound: 7, concept: 7, picture: 7, loop: 6.5 } : { hook: 5, rhythm: 6, transitions: 7, motion: 6, text: 7.5, sound: 6, concept: 6.5, picture: 6, loop: 4 },
              strengths: ['The dive lands on a downbeat.'],
              issues: [
                // a critical issue caps the score at 6.5, so the re-scored round has none
                { severity: call.anchored ? 'major' : 'critical', at: 0, area: 'hook', problem: 'The first second is static.', fix: 'Open on the strongest shot with a zoom punch.', gain: 0.9 },
                { severity: 'major', at: 3.0, area: 'rhythm', problem: 'The bloom starts late.', fix: 'Move the cut onto the beat at 3.00 s.' },
                { severity: 'minor', at: 6.0, area: 'text', problem: 'The knockout title is small.', fix: 'size 0.11.' },
              ],
              versus: 'Below v7.', brief: '1. Rebuild the first second.\n2. Snap every cut.',
              path: [{ change: 'Rebuild the hook as a set piece.', at: 0, to: 1.5, gain: 1.0 }, { change: 'Make the loop a push landing.', at: null, gain: 0.6 }],
              ...(follow.length ? { followUp: follow.map((id, i) => ({ id, status: i % 2 ? 'partly' : 'fixed', comment: 'checked' })) } : {}),
            }), opts);
          }
          if (last.includes('NOTES WITH NO APPLIED OPERATIONS')) {
            const ids = [...last.matchAll(/^(N\d+) \[/gm)].map(m => m[1]);
            window.__filled = (window.__filled || 0) + 1;
            return reply(JSON.stringify({ message: `Carried ${ids.join(', ')}.`, ops: [{ op: 'fx', preset: 'dust', start: 0.5, dur: 2, note: ids }] }), opts);
          }
          if (full.includes('planning a long-form edit')) {
            window.__longform = { transcript: full.includes('[2.0] Today we break down'), pauses: full.includes('MEASURED PAUSES'), comments: full.includes('No zooms in the intro'), effort: opts.effort };
            return reply(JSON.stringify({ message: 'Tightened the pauses, two chapters and a breakdown of the process.', title: 'How it works',
              chapters: [{ t: 0, title: 'How it works' }, { t: 5, title: 'The three steps' }],
              breakdowns: [{ start: 5.5, dur: 5, title: 'The process', points: ['Collect the evidence', 'Test every sample', 'Close the case'] }],
              callouts: [{ t: 2.3, text: 'Key term' }], zooms: [{ t: 2.5, dur: 3, zoom: 1.1 }], remove: [{ from: 1.0, to: 1.6 }] }), opts);
          }
          if (last.includes('CALL 1 OF 2: THE CUT')) {
            const tight = last.includes('Your last attempt used its whole time');
            window.__cutCalls = [...(window.__cutCalls || []), { effort: opts.effort, tight, images: call.images }];
            if (!window.__failedOnce) { window.__failedOnce = true; call.failed = 'empty_completion'; throw { code: 'empty_completion', message: 'no text' }; }
            window.__parts.push('cut');
            const ids = [...full.matchAll(/^(N\d+) \[/gm)].map(m => m[1]);
            const plan = planFrom(full);
            const ops = plan.ops.filter(o => PICTURE.has(o.op)).map((o, i) => (o.op === 'look' ? { ...o, note: 'N2' } : o.op === 'add' && i === 2 ? { ...o, note: 'N1' } : o));
            return reply(JSON.stringify({ message: plan.message, design: 'CONCEPT: the evidence points back at him. SET PIECES: dive 1.5, shatter 3.0. TEXT: COULD IT BE HIM 0.3.', notes: ids.map(id => ({ id, plan: 'do it' })), ops }), opts);
          }
          if (last.includes('CALL 2 OF 2: THE DESIGN')) {
            const half = last.match(/THIS CALL DESIGNS ([\d.]+)-([\d.]+) s ONLY/);
            window.__designCalls = [...(window.__designCalls || []), { effort: opts.effort, images: call.images, board: full.includes('STORYBOARD of your cut') && full.includes('cyan ticks'), idle: last.includes('SHOTS WITH NOTHING ON THEM YET'), half: half ? half[0] : null }];
            if (!half && window.__breakDesign > 0) { window.__breakDesign--; call.failed = 'empty_completion'; throw { code: 'empty_completion', message: 'no text' }; }
            if (half && +half[1] > 0 && window.__breakHalf2 > 0) { window.__breakHalf2--; return reply('this is not json', opts); }
            window.__parts.push(half ? `half@${half[1]}` : 'design');
            const plan = planFrom(full);
            let ops = plan.ops.filter(o => !PICTURE.has(o.op));
            if (half) { const a = +half[1], b = +half[2]; ops = ops.filter(o => o.start === undefined || (o.start >= a && o.start < b)).map(o => (o.id ? { ...o, id: `${a > 0 ? 'e' : 'd'}${o.id}` } : o)); }
            return reply(JSON.stringify({ message: 'Designed the transitions, titles and light.', ops }), opts);
          }
          if (/ROUND \d+ INSTRUCTIONS FROM THE OWNER/.test(full) && last.includes('Work through')) {
            if (last.includes('CLEARED FOR REBUILD')) window.__sawRebuild = true;
            if (last.includes('[PATH TO 8')) window.__sawPath = true;
            const part = last.match(/THIS CALL CARRIES OUT (N\d+)(?:-(N\d+))? ONLY/);
            window.__reviseCalls = [...(window.__reviseCalls || []), { effort: opts.effort, images: call.images, part: part ? part[0] : null }];
            if (!part && window.__breakRevise > 0) { window.__breakRevise--; call.failed = 'empty_completion'; throw { code: 'empty_completion', message: 'no text' }; }
            const all = [...full.matchAll(/^(N\d+) \[/gm)].map(m => m[1]);
            let ids = [...new Set(all)];
            if (part) { const a = +part[1].slice(1), b = +(part[2] || part[1]).slice(1); ids = ids.filter(id => +id.slice(1) >= a && +id.slice(1) <= b); }
            const ops = ids.map((id, i) => ({ op: 'fx', id: `${part ? (part[1] === 'N1' ? 'r' : 's') : ''}fx${i}`, preset: 'dust', start: 0.5 + i, dur: 1, note: id }));
            ops.push({ op: 'project', camera: { on: true, every: 'beat', punch: 0.07, kick: 1.2 } });
            return reply(JSON.stringify({ message: `Revised ${ids.join(', ')}.`, notes: ids.map(id => ({ id, plan: 'do it' })), ops }), opts);
          }
          if (last.includes('YOUR CUSTOM ELEMENTS, RENDERED')) {
            const els = [...last.matchAll(/^ELEMENT (\S+) \(/gm)].map(m => m[1]);
            window.__workshop = [...(window.__workshop || []), { els, images: call.images, effort: opts.effort, standard: last.includes('THE CRAFT STANDARD') }];
            return reply(JSON.stringify({ message: 'Rebuilt the emblem with layers.', elements: els.map(id => ({ id, score: 6, frames: 'flat' })), ops: els.filter(id => /emb/.test(id)).map(id => ({ op: 'set', id, glow: 0.5 })) }), opts);
          }
          if (/REVIEW \d OF/.test(last)) {
            const ids = [...last.matchAll(/^(N\d+) \[/gm)].map(m => m[1]);
            window.__reviews = [...(window.__reviews || []), last.slice(0, 40)];
            if (last.includes('could not be written')) window.__sawLost = true;
            if (last.includes('MEASURED TRANSITIONS')) window.__sawMeasured = true;
            if (/transition close-ups/.test(full)) window.__sawClose = true;
            const scores = { hook: 7, rhythm: 7.5, transitions: 8, motion: 7, text: 8, sound: 7, concept: 7.5, picture: 7.5, loop: 6 };
            const notes = ids.map(id => ({ id, status: 'done', check: 'visible' }));
            if (last.includes('effect oops does not compile')) { window.__sawCompile = true; return reply(JSON.stringify({ message: 'Removed oops.', scores, notes, ops: [{ op: 'remove', id: 'oops' }] }), opts); }
            return reply(JSON.stringify({ message: 'Approved.', scores, notes, ops: [] }), opts);
          }
          if (/ROUND \d+ INSTRUCTIONS FROM THE OWNER/.test(full)) {
            return reply(JSON.stringify({ message: 'Revised.', ops: [{ op: 'project', camera: { on: true, every: 'beat', punch: 0.07, kick: 1.2 } }] }), opts);
          }
          return reply(JSON.stringify(planFrom(full)), opts);
        };
        f.limits = async () => ({ maxPromptBytes: 262144, images: { maxCount: 20, maxInputBytes: 20e6, mediaTypes: ['image/jpeg', 'image/png'] } });
        return f;
      }
      if (name === 'downloads') return { save: async ({ filename, data }) => { window.__saved.push({ filename, size: data.size ?? data.length, b64: await toB64(data) }); return { status: 'saved' }; } };
      return null;
    },
  };
});

await page.goto('http://localhost:8778/');
await page.waitForSelector('.home');
await page.waitForFunction(() => window.__voidfx?.store.state.director.available === 'yes', null, { timeout: 30000 });

const S = fn => page.evaluate(fn);
const waitJobs = async (pred, timeout = 600000) => page.waitForFunction(pred, null, { timeout, polling: 500 });
const jobsSnapshot = () => S(() => window.__voidfx.store.state.jobs.map(j => ({ id: j.id, kind: j.kind, state: j.state, round: j.round, effort: j.effort, projectId: j.projectId, error: j.error, steps: j.steps.map(s => ({ id: s.id, state: s.state, detail: s.detail })) })));

// a preset at 30 fps keeps the export short
const presetId = await S(async () => {
  const v = window.__voidfx;
  const p = { ...v.blankPreset(), name: 'Suite preset', prompt: 'Test edit.', fps: 30 };
  await v.savePreset(p);
  v.setParallelLimit(3);
  return p.id;
});

const startEdit = (effort, opts = {}) => page.evaluate(async ({ effort, presetId, opts }) => {
  const files = await Promise.all(['portrait.mp4', 'landscape.mp4', 'music.wav'].map(async n => { const b = await (await fetch(`/test/media/${n}`)).blob(); return new File([b], n, { type: b.type }); }));
  const job = await window.__voidfx.startAiEdit({ name: `Suite ${effort}${opts.tag || ''}`, presetId, effort, files, follow: opts.follow || { critic: false, autoRounds: 0 },
    request: { notes: 'Open on the strongest shot. Add a black and white look with red kept.', lyrics: '', library: { mode: 'none', ids: [] } } });
  return job?.id;
}, { effort, presetId, opts });

// ---------- 1. four builds at once, one per effort, while another project is edited ----------
if (on('build')) {
  const ids = {};
  for (const e of ['low', 'medium', 'high', 'extra']) ids[e] = await startEdit(e, e === 'extra' ? { follow: { critic: true, autoRounds: 0 } } : {});
  check('four builds queued', Object.values(ids).every(Boolean));
  await page.waitForFunction(() => window.__voidfx.store.state.jobs.filter(j => j.state === 'running').length >= 2, null, { timeout: 60000 }).then(() => true, () => false)
    .then(ok => check('jobs run in parallel', ok));
  // edit another project meanwhile
  const side = await S(async () => {
    const v = window.__voidfx;
    const id = await v.createProject({ name: 'Side project', open: true });
    v.store.commit(p => { p.name = 'Side project edited'; });
    return { id, lock: v.store.state.lock, name: v.store.state.project.name };
  });
  check('editing another project while jobs run', !side.lock && side.name === 'Side project edited', JSON.stringify(side));
  await waitJobs(() => { const j = window.__voidfx.store.state.jobs; return j.filter(x => x.kind === 'create').every(x => ['done', 'error', 'stopped'].includes(x.state)) && !j.some(x => x.kind === 'critique' && ['queued', 'running'].includes(x.state)) && j.some(x => x.kind === 'critique'); });
  const jobs = await jobsSnapshot();
  for (const e of ['low', 'medium', 'high', 'extra']) {
    const j = jobs.find(x => x.id === ids[e]);
    const reviews = j.steps.filter(s => s.id.startsWith('review'));
    const unfinished = j.steps.filter(s => !['done', 'skip'].includes(s.state));
    check(`${e}: build finished`, j.state === 'done', j.error || '');
    check(`${e}: every step finished`, !unfinished.length, unfinished.map(s => `${s.id}:${s.state}`).join(' '));
    check(`${e}: ${({ low: 0, medium: 0, high: 1, extra: 2 })[e]} review(s)`, reviews.length === ({ low: 0, medium: 0, high: 1, extra: 2 })[e] && reviews.every(s => s.state === 'done'), reviews.map(s => `${s.id}:${s.state}`).join(' '));
    const rec = await page.evaluate(async id => { const r = await window.__voidfx.getRecord(id); return { clips: r.project.clips.length, notes: r.rounds?.[0]?.notes, self: r.rounds?.[0]?.selfScores, look: r.project.clips.some(c => c.preset === 'noir_red'), crit: r.rounds?.[0]?.critique?.score }; }, j.projectId);
    check(`${e}: timeline built`, rec.clips >= 10, `${rec.clips} clips`);
    check(`${e}: both owner notes carried`, rec.notes?.length === 2 && rec.notes.every(n => n.ops > 0), JSON.stringify(rec.notes?.map(n => `${n.id}:${n.ops}`)));
    check(`${e}: look applied`, rec.look);
    if (e === 'high' || e === 'extra') check(`${e}: self-scores recorded`, !!rec.self && Object.keys(rec.self).length === 9);
    if (e === 'extra') check('extra: critic ran after the build', typeof rec.crit === 'number', String(rec.crit));
  }
  const calls = await S(() => ({ parts: window.__parts, cut: window.__cutCalls || [], design: window.__designCalls || [], measured: !!window.__sawMeasured, close: !!window.__sawClose, compile: !!window.__sawCompile, filled: window.__filled || 0, maxChars: Math.max(...window.__calls.map(c => c.chars)) }));
  check('medium/high/extra: the cut, then the design', calls.parts.filter(p => p === 'cut').length >= 3 && calls.parts.filter(p => p === 'design').length >= 3, calls.parts.join(' '));
  const retry = calls.cut.find(c => c.tight);
  check('a call that runs out of time is asked again at the same effort', !!retry && calls.cut.filter(c => !c.tight).some(c => c.effort === retry.effort) && retry.images <= Math.ceil(calls.cut[0].images / 2), JSON.stringify(calls.cut));
  check('the design sees a storyboard with the frame ruler', calls.design.length >= 3 && calls.design.every(d => d.board && d.images > 0), JSON.stringify(calls.design));
  check('the design is told which shots have nothing on them', calls.design.some(d => d.idle));
  check('the design runs at the job effort', calls.design.every(d => d.effort !== 'low'), JSON.stringify(calls.design.map(d => d.effort)));
  check('the reviews measure every transition and see the close-ups', calls.measured && calls.close);
  const wk = await S(() => window.__workshop || []);
  check('the workshop shows Opus its custom elements rendered large, against the craft standard', wk.length >= 2 && wk.every(w => w.standard && w.images >= 1 && w.els.length >= 1 && w.effort !== 'low'), JSON.stringify(wk));
  check('a broken custom effect is fixed by the review', calls.compile);
  check('prompts stay under the limit', calls.maxChars < 250 * 1024, `${calls.maxChars} chars`);
  writeFileSync(join(OUT, 'suite-build-jobs.json'), JSON.stringify(jobs, null, 1));
}

// ---------- 2. revision with numbered notes, then an automatic round ----------
if (on('build') && on('revise')) {
  const pid = await S(() => window.__voidfx.store.state.jobs.find(j => j.kind === 'create' && j.effort === 'extra').projectId);
  await S(() => { window.__breakRevise = 2; });
  const jid = await page.evaluate(async pid => {
    const v = window.__voidfx;
    const r = await v.getRecord(pid);
    const crit = r.rounds[0].critique;
    const lines = crit.issues.map(i => `[${i.severity}${i.at !== undefined ? ` @ ${i.at.toFixed(2)}s` : ''}, ${i.area}] ${i.problem} Fix: ${i.fix}`);
    const j = await v.enqueue({ kind: 'revise', projectId: pid, effort: 'extra', presetId: r.presetId, brief: 'Make the drop hit harder. The text is too small.', fromCritic: lines, follow: { critic: true, autoRounds: 1 } });
    return j.id;
  }, pid);
  await waitJobs(() => { const j = window.__voidfx.store.state.jobs.filter(x => x.kind !== 'create'); return j.length >= 5 && j.every(x => ['done', 'error', 'stopped'].includes(x.state)); });
  const rec = await page.evaluate(async pid => { const r = await window.__voidfx.getRecord(pid); return r.rounds.map(x => ({ n: x.n, kind: x.kind, notes: x.notes, crit: x.critique && { score: x.critique.score, prev: x.critique.prevScore, follow: x.critique.followUp } })); }, pid);
  const r2 = rec.find(r => r.n === 2), r3 = rec.find(r => r.n === 3);
  check('revision: round 2 recorded', !!r2, jid);
  check('revision: owner asks and critic points numbered', r2?.notes?.length === 5 && r2.notes.filter(n => n.from === 'owner').length === 2, JSON.stringify(r2?.notes?.map(n => `${n.id}:${n.from}`)));
  check('revision: every note carried and checked', r2?.notes?.every(n => n.ops > 0 && n.status === 'done'), JSON.stringify(r2?.notes?.map(n => `${n.id}:${n.ops}:${n.status}`)));
  check('revision: notes with timed critic points keep their time', r2?.notes?.some(n => n.at === 3), JSON.stringify(r2?.notes?.map(n => n.at)));
  check('critic: scores against the last round', r2?.crit?.prev === 6.2 && r2.crit.score === 7.1, JSON.stringify(r2?.crit));
  check('critic: follows up every note', r2?.crit?.follow?.length === 5, JSON.stringify(r2?.crit?.follow?.map(f => f.id)));
  const rb = await S(() => ({ rebuild: !!window.__sawRebuild, path: !!window.__sawPath, fresh: window.__calls.filter(c => c.critic).every(c => c.fresh !== false) }));
  check('revisions clear the weakest sections and rebuild them; the path to 8 leads the notes', rb.rebuild && rb.path, JSON.stringify(rb));
  check('the critic scores each round fresh (no building up from the last score)', rb.fresh, JSON.stringify(rb));
  check('automatic round ran after the critique', !!r3 && r3.kind === 'revise' && r3.notes?.every(n => n.from === 'critic') && !!r3.crit, JSON.stringify(r3 && { notes: r3.notes?.length, crit: r3.crit?.score }));
  const rc = await S(() => window.__reviseCalls || []);
  check('revision: one call writes every note; when it runs out of time two calls share the notes at the same effort', rc.filter(c => c.part).length === 2 && rc.every(c => c.effort === 'high'), JSON.stringify(rc));
}

// ---------- 3. cancel and resume; a layers call that fails twice ----------
if (on('cancel')) {
  await S(() => { window.__slow = 2500; });
  const id = await startEdit('high', { tag: ' cancel' });
  await page.waitForFunction(id => { const j = window.__voidfx.store.state.jobs.find(x => x.id === id); return j && j.steps.some(s => s.id === 'cut' && s.state === 'run'); }, id, { timeout: 120000 });
  await S(() => { window.__slow = 120; });
  await page.evaluate(id => window.__voidfx.stopJob(id), id);
  await page.waitForFunction(id => ['stopped', 'error'].includes(window.__voidfx.store.state.jobs.find(x => x.id === id).state), id, { timeout: 30000 });
  check('a running build can be stopped', await page.evaluate(id => window.__voidfx.store.state.jobs.find(x => x.id === id).state === 'stopped', id));
  await page.evaluate(id => window.__voidfx.resumeJob(id), id);
  await page.waitForFunction(id => ['done', 'error'].includes(window.__voidfx.store.state.jobs.find(x => x.id === id).state), id, { timeout: 300000 });
  check('a stopped build resumes and finishes', await page.evaluate(id => window.__voidfx.store.state.jobs.find(x => x.id === id).state === 'done', id));

  await S(() => { window.__breakDesign = 2; window.__breakHalf2 = 2; window.__sawLost = false; window.__designCalls = []; });
  const id2 = await startEdit('high', { tag: ' lost layers' });
  await page.waitForFunction(id => ['done', 'error'].includes(window.__voidfx.store.state.jobs.find(x => x.id === id).state), id2, { timeout: 300000 });
  const j2 = await page.evaluate(id => window.__voidfx.store.state.jobs.find(x => x.id === id), id2);
  const dc = await S(() => window.__designCalls);
  check('a design that runs out of time is split in two halves at the same effort', dc.filter(d => d.half).length >= 2 && dc.every(d => d.effort === 'high'), JSON.stringify(dc));
  check('a lost half does not stop the build', j2.state === 'done', j2.error || '');
  check('the review is told to write the lost half', await S(() => window.__sawLost) && /could not be written/.test(j2.steps.find(s => s.id === 'design')?.detail || ''), j2.steps.find(s => s.id === 'design')?.detail);
}

// ---------- 4. export: decode and measure ----------
if (on('build') && on('export')) {
  const pid = await S(() => window.__voidfx.store.state.jobs.find(j => j.kind === 'create' && j.effort === 'low').projectId);
  await page.evaluate(pid => window.__voidfx.open(pid), pid);
  await page.waitForSelector('.app');
  await page.waitForFunction(() => { const s = window.__voidfx.store.state; return s.mediaOrder.length && s.mediaOrder.every(id => ['ready', 'error'].includes(s.media[id].status)); }, null, { timeout: 120000 });
  const dur = await S(() => { const p = window.__voidfx.store.state.project; return p.clips.reduce((a, c) => Math.max(a, c.start + c.dur), 0); });
  // behave like Windows' AAC encoder, which refuses anything above 192 kbps (the owner's export failure)
  await S(() => {
    const orig = AudioEncoder.isConfigSupported.bind(AudioEncoder);
    AudioEncoder.isConfigSupported = async c => (String(c.codec).startsWith('mp4a') && (c.bitrate || 0) > 192000 ? { supported: false, config: c } : orig(c));
    const Orig = window.AudioEncoder;
    window.AudioEncoder = class extends Orig { configure(c) { if (String(c.codec).startsWith('mp4a') && (c.bitrate || 0) > 192000) throw new DOMException('Unsupported configuration', 'NotSupportedError'); return super.configure(c); } };
    window.AudioEncoder.isConfigSupported = AudioEncoder.isConfigSupported;
  });
  await page.click('.top .btn-primary');
  await page.click('.modal .seg button:has-text("720p")');
  const te = Date.now();
  await page.click('.modal .btn-primary');
  await page.waitForSelector('.exp-video, .modal .note.bad', { timeout: 900000 });
  const bad = await S(() => document.querySelector('.modal .note.bad')?.textContent || null);
  check('export finishes', !bad, bad || `${((Date.now() - te) / 1000).toFixed(0)} s`);
  if (!bad) {
    await page.click('.modal .btn-primary');
    await page.waitForFunction(() => window.__saved.length > 0, null, { timeout: 60000 });
    const saved = await S(() => window.__saved[window.__saved.length - 1]);
    const file = join(OUT, 'suite-export.mp4');
    writeFileSync(file, Buffer.from(saved.b64, 'base64'));
    const probe = JSON.parse(execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration:stream=codec_type,codec_name,width,height,avg_frame_rate', '-of', 'json', file]).toString());
    const v = probe.streams.find(s => s.codec_type === 'video'), a = probe.streams.find(s => s.codec_type === 'audio');
    check('export: H.264 video and AAC audio, even where AAC tops out at 192 kbps', v?.codec_name === 'h264' && a?.codec_name === 'aac', `${v?.codec_name} ${v?.width}x${v?.height} ${v?.avg_frame_rate} + ${a?.codec_name}`);
    check('export: length matches the edit', Math.abs(+probe.format.duration - dur) < 0.15, `${(+probe.format.duration).toFixed(3)} s vs ${dur.toFixed(3)} s`);
    const stderr = execFileSync('bash', ['-c', `ffmpeg -hide_banner -nostats -i '${file}' -af ebur128=peak=true -f null - 2>&1`]).toString();
    const I = +(stderr.match(/I:\s+(-?[\d.]+) LUFS/g)?.pop()?.match(/-?[\d.]+/)?.[0] ?? NaN);
    const TP = +(stderr.match(/Peak:\s+(-?[\d.]+) dBFS/g)?.pop()?.match(/-?[\d.]+/)?.[0] ?? NaN);
    check('export: mastered to about -13 LUFS', Math.abs(I + 13) <= 1.2, `${I} LUFS`);
    check('export: true peak at or under -1 dBTP', TP <= -1, `${TP} dBTP`);
    const lumas = execFileSync('bash', ['-c', `ffmpeg -hide_banner -i '${file}' -vf "fps=2,scale=64:-1,signalstats,metadata=print:key=lavfi.signalstats.YAVG" -f null - 2>&1 | grep -o 'YAVG=[0-9.]*' | cut -d= -f2`]).toString().trim().split('\n').map(Number).filter(Number.isFinite);
    check('export: picture is not black', lumas.length > 3 && lumas.filter(l => l > 8).length >= lumas.length * 0.8, `luma ${lumas.map(l => l.toFixed(0)).join(' ')}`);
  }
  await page.keyboard.press('Escape');
  await S(() => window.__voidfx.store.set({ exportOpen: false }));
}

// ---------- 5. every transition, look, effect and text animation renders ----------
if (on('render')) {
  await S(() => window.__voidfx.store.set({ view: 'home' }));
  const pid = await S(async () => { const v = window.__voidfx; return v.createProject({ name: 'Render coverage', open: true }); });
  void pid;
  await page.waitForSelector('.app');
  await page.setInputFiles('.lp input[type=file]', [join(ROOT, 'test/media/nat_astronaut.mp4'), join(ROOT, 'test/media/nat_rocket.mp4'), join(ROOT, 'test/media/music.wav')]);
  await page.waitForFunction(() => { const s = window.__voidfx.store.state; return s.mediaOrder.length === 3 && s.mediaOrder.every(id => s.media[id].status === 'ready' && (s.media[id].kind !== 'audio' || s.media[id].analysisState === 'done')); }, null, { timeout: 120000 });
  const cov = await page.evaluate(async () => {
    const { store, applyOps, renderStills, FX_LIBRARY, fxCode, fxParams, compileError } = window.__voidfx;
    const media = store.state.media;
    const [a, b, mus] = store.state.mediaOrder;
    // music under the shots, so beat effects have beats to react to
    const base = [{ op: 'clear' }, { op: 'project', width: 1080, height: 1920, fps: 30 }, { op: 'add', id: 'c1', media: a, track: 'V1', in: 0, dur: 2.4 }, { op: 'add', id: 'c2', media: b, track: 'V1', in: 0, dur: 2.4 }, { op: 'add', id: 'mu', media: mus, track: 'A1', start: 0, in: 0, dur: 4.8 }];
    const beatAfter = t => { const bs = media[mus].analysis?.beats || []; const k = bs.find(x => x >= t - 0.02); return k !== undefined ? k + 0.03 : t; };
    const stats = cv => {
      const g = cv.getContext('2d'); const d = g.getImageData(0, 0, cv.width, cv.height).data;
      let s = 0; for (let i = 0; i < d.length; i += 4) s += d[i] * 0.2126 + d[i + 1] * 0.7152 + d[i + 2] * 0.0722;
      return { luma: s / (d.length / 4), data: d };
    };
    const diff = (x, y) => { let s = 0; for (let i = 0; i < x.length; i += 4) s += Math.abs(x[i] - y[i]) + Math.abs(x[i + 1] - y[i + 1]) + Math.abs(x[i + 2] - y[i + 2]); return s / (x.length / 4) / 3; };
    const render = async (ops, t, h = 240) => { const r = applyOps(store.state.project, ops, media); const [cv] = await renderStills(r.project, [t], h, undefined, media); return { cv, issues: r.issues }; };
    const out = { transitions: [], fx: [], text: [] };
    const plainA = stats((await render(base, 2.25)).cv);
    const plainB = stats((await render(base, 2.55)).cv);
    const TR = ['crossfade', 'dip_black', 'dip_white', 'flash', 'slide_left', 'slide_right', 'slide_up', 'slide_down', 'push_left', 'push_right', 'push_up', 'push_down', 'wipe_left', 'wipe_right', 'wipe_up', 'wipe_down', 'iris', 'zoom_in', 'zoom_out', 'whip_left', 'whip_right', 'whip_up', 'whip_down', 'spin', 'blur', 'glitch', 'bolt', 'logo', 'blink', 'ink', 'burn', 'slash', 'punch', 'light_leak', 'roll', 'shadow', 'warp', 'cube_left', 'cube_right', 'cube_up', 'cube_down', 'flip_h', 'flip_v', 'shatter', 'slices', 'blinds', 'ripple', 'swirl', 'pixelate', 'kaleido', 'heat', 'datamosh', 'tear', 'shutter', 'wiper', 'dive', 'light_sweep', 'wash'];
    const plainM = stats((await render(base, 2.4)).cv);
    for (const t of TR) {
      const ops = [...base.slice(0, 3), { ...base[3], transition: { type: t, dur: 0.8 } }, base[4]];
      // before, at and after the cut: some moves (a wiper, a stain) do their work around the middle
      const s1 = stats((await render(ops, 2.25)).cv), sm = stats((await render(ops, 2.4)).cv), s2 = stats((await render(ops, 2.55)).cv);
      out.transitions.push({ t, d: Math.max(diff(s1.data, plainA.data), diff(sm.data, plainM.data), diff(s2.data, plainB.data)), luma: Math.max(s1.luma, sm.luma, s2.luma) });
    }
    for (const def of FX_LIBRARY) {
      const err = compileError(fxCode(def, fxParams(def)));
      const look = def.group === 'look';
      const op = look ? { op: 'look', preset: def.id } : { op: 'fx', preset: def.id, start: 0.6, dur: Math.min(def.dur, 1.4), at: { x: 0.55, y: 0.35 } };
      // beat effects are sampled just after a beat; the rest where they are in full swing
      const tt0 = look ? 1.2 : 0.6 + Math.min(def.dur, 1.4) * 0.45;
      const tb = beatAfter(0.6 + Math.min(def.dur, 1.4) * 0.3);
      const tt = def.beat && tb < 0.6 + Math.min(def.dur, 1.4) * 0.8 ? tb : tt0;
      const plain = stats((await render(base, tt, 480)).cv);
      const { cv, issues } = await render([...base, op], tt, 480);
      const s = stats(cv);
      out.fx.push({ id: def.id, err, issues, d: diff(s.data, plain.data), luma: s.luma });
    }
    const IN = ['fade', 'rise', 'drop', 'pop', 'blur', 'typewriter', 'words', 'letters', 'bloom', 'slam', 'fly', 'stamp', 'sweep', 'mask', 'track', 'flicker', 'slide_left', 'slide_right'];
    const OUTS = ['fade', 'cap', 'sink', 'lift', 'shrink', 'blur', 'words', 'scatter', 'blowaway', 'streak', 'zoom', 'fall', 'slide_left', 'slide_right'];
    const plainT = stats((await render(base, 1.0)).cv);
    for (const a2 of IN) {
      const { cv } = await render([...base, { op: 'text', start: 0.2, dur: 2, text: 'COULD IT BE\n*HIM*', style: { font: 'Inter', weight: 900, uppercase: true, size: 0.06 }, anim: { in: a2, out: 'none', inDur: 0.5 }, transform: { y: 0.2 } }], 1.0);
      out.text.push({ a: `in ${a2}`, d: diff(stats(cv).data, plainT.data) });
    }
    for (const a2 of OUTS) {
      const { cv } = await render([...base, { op: 'text', start: 0.2, dur: 1.2, text: 'COULD IT BE\n*HIM*', style: { font: 'Inter', weight: 900, uppercase: true, size: 0.06 }, anim: { in: 'none', out: a2, outDur: 0.6 }, transform: { y: 0.2 } }], 1.15);
      out.text.push({ a: `out ${a2}`, d: diff(stats(cv).data, plainT.data) });
    }
    const { cv: kc } = await render([...base, { op: 'text', start: 0.2, dur: 2, text: 'BAY HARBOR\nBUTCHER', style: { size: 0.1, uppercase: true, knockout: true }, anim: { in: 'none', out: 'none' } }], 1.0);
    out.text.push({ a: 'knockout', d: diff(stats(kc).data, plainT.data) });
    return out;
  });
  const flatT = cov.transitions.filter(x => x.d < 2 || x.luma < 3);
  check(`all ${cov.transitions.length} transitions render and change the cut`, !flatT.length, flatT.map(x => `${x.t} d=${x.d.toFixed(1)}`).join(', '));
  const badFx = cov.fx.filter(x => x.err || x.d < 0.3 || x.luma < 2 || x.issues.length);
  check(`all ${cov.fx.length} looks and effects compile and change the picture`, !badFx.length, badFx.map(x => `${x.id} ${x.err || ''} d=${x.d.toFixed(2)} ${x.issues.join(';')}`).join(', '));
  const flatText = cov.text.filter(x => x.d < 0.4);
  check(`all ${cov.text.length} text animations draw`, !flatText.length, flatText.map(x => `${x.a} d=${x.d.toFixed(2)}`).join(', '));
  writeFileSync(join(OUT, 'suite-coverage.json'), JSON.stringify(cov, null, 1));
}

// ---------- 5b. operations and gates added from the live test edit ----------
if (on('units')) {
  // the chat-quality example elements in Opus's reference compile and render
  const refSrc = readFileSync(join(ROOT, 'src/ai/prompt.ts'), 'utf8');
  const examples = ['A stamped emblem', 'Blood running down the glass', 'A luminol sweep'].map(k => { const line = refSrc.split('\n').find(l => l.includes(k)) || ''; return { k, code: line.slice(line.indexOf('vec4 effect')).trim() }; });
  const ex = await page.evaluate(async examples => {
    const { store, applyOps, customIssues, renderStills } = window.__voidfx;
    const media = store.state.media, ids = store.state.mediaOrder;
    const vid = ids.find(id => media[id].kind === 'video');
    const out = [];
    const cv = document.createElement('canvas'); const W = 203, H = 360; cv.width = W * 4; cv.height = H * examples.length; const g = cv.getContext('2d');
    for (let r = 0; r < examples.length; r++) {
      const e = examples[r];
      const res = applyOps(store.state.project, [{ op: 'clear' }, { op: 'add', media: vid, track: 'V1', in: 0, dur: 3, focus: { x: 0.5, y: 0.42 } }, { op: 'shader', id: 'ex', start: 0.5, dur: 1.6, code: e.code, at: { x: 0.5, y: 0.72 } }], media);
      const bad = customIssues(res.project);
      const frames = await renderStills(res.project, [0.6, 0.85, 1.2, 1.8], H, undefined, media);
      frames.forEach((f, c) => { if (f) g.drawImage(f, c * W, r * H, W, H); });
      out.push({ k: e.k, len: e.code.length, bad });
    }
    return { out, sheet: cv.toDataURL('image/jpeg', 0.8) };
  }, examples);
  writeFileSync(join(OUT, 'examples.jpg'), Buffer.from(ex.sheet.split(',')[1], 'base64'));
  check('the example elements in the reference compile', ex.out.every(x => x.len > 200 && !x.bad.length), JSON.stringify(ex.out));
  const u = await page.evaluate(async () => {
    const { store, applyOps, runChecks, idleShots, transitionReport, layerReport, renderStills, lyricGuard, parseLyrics, addLessons, clearLessons, lessonsText } = window.__voidfx;
    const media = store.state.media;
    const ids = store.state.mediaOrder;
    const vid = ids.find(id => media[id].kind === 'video'), mus = ids.find(id => media[id].kind === 'audio');
    const out = {};
    // a reused id inside one reply: the later set goes to the new clip, not the old one
    let r = applyOps(store.state.project, [{ op: 'clear' }, { op: 'add', id: 'c1', media: vid, track: 'V1', in: 0, dur: 2 }, { op: 'look', id: 'e1', preset: 'noir' }], media);
    r = applyOps(r.project, [{ op: 'fx', id: 'e1', preset: 'dust', start: 0, dur: 1 }, { op: 'set', id: 'e1', params: { amount: 0.3 } }], media);
    const look = r.project.clips.find(c => c.preset === 'noir'), dust = r.project.clips.find(c => c.preset === 'dust');
    out.alias = { lookUntouched: !look.params.amount, dustSet: dust.params.amount === 0.3, reported: r.issues.some(x => /already belongs/.test(x)), autoId: /^X_\d+$/.test(dust.id) };
    // camera sections
    r = applyOps(r.project, [{ op: 'project', camera: { on: true, sections: [{ from: 0, to: 1 }, { from: 1.5, to: 2, punch: 0.03, every: 'half' }] } }], media);
    out.sections = r.project.camera.sections;
    // gates: repeats, stacked flashes, the loop in sound
    r = applyOps(store.state.project, [{ op: 'clear' }, ...[0, 1, 2, 3, 4, 5].map(k => ({ op: 'add', media: vid, track: 'V1', in: k < 3 ? 0.2 : 0.3, dur: 1 })), { op: 'add', media: mus, track: 'A1', start: 0, in: 0, dur: 6, fadeOut: 0.5 },
      { op: 'fx', preset: 'impact_frame', start: 2, dur: 0.2 }, { op: 'fx', preset: 'exposure_wash', start: 1.95, dur: 0.4 }], media);
    const checks = runChecks(r.project, media, { houseRules: true, duration: [20, 26], fps: 60 });
    out.gates = Object.fromEntries(['repeats', 'flash-stack', 'loop-sound', 'layers'].map(id => [id, checks.find(c => c.id === id)?.status || 'none']));
    // the loop operation lands the last frame on frame 0's source frame and framing
    r = applyOps(store.state.project, [{ op: 'clear' }, { op: 'add', id: 'f', media: vid, track: 'V1', in: 0.8, dur: 1, focus: { x: 0.4, y: 0.4 }, color: { brightness: 0.1 } }, { op: 'add', media: vid, track: 'V1', in: 2.5, dur: 1 }, { op: 'loop', dur: 0.4 }], media);
    const tw = r.project.clips.find(c => c.name === 'loop twin');
    out.loop = tw && { end: +(tw.start + tw.dur).toFixed(3), srcEnd: +((tw.in ?? 0) + tw.dur * (tw.speed ?? 1)).toFixed(3), focus: tw.focus, color: tw.color, issues: r.issues };
    // a velocity ramp bursts on the clip's own cut
    r = applyOps(store.state.project, [{ op: 'clear' }, { op: 'add', id: 'm', media: mus, track: 'A1', start: 0, in: 0, dur: 6 }, { op: 'add', id: 'v', media: vid, track: 'V1', in: 0, dur: 1, ramp: { fast: 2, slow: 0.5 } }], media);
    out.ramp = r.project.clips.find(c => c.id === 'v').kf?.speed?.[0];
    // shots with nothing designed on them: a push-in or a title over it gives a shot its reason
    r = applyOps(store.state.project, [{ op: 'clear' }, { op: 'add', id: 'p1', media: vid, track: 'V1', in: 0, dur: 1.2, kf: { scale: [{ t: 0, v: 1 }, { t: 1.2, v: 1.12 }] } }, { op: 'add', id: 'p2', media: vid, track: 'V1', in: 1.5, dur: 1.2 }, { op: 'add', id: 'p3', media: vid, track: 'V1', in: 3, dur: 1.2 }, { op: 'add', id: 'p4', media: vid, track: 'V1', in: 4.5, dur: 0.5 },
      { op: 'text', start: 1.3, dur: 1.2, text: 'WORD', anim: { in: 'words' } }], media);
    out.idle = idleShots(r.project).map(c => c.id);
    out.idleGate = runChecks(r.project, media, { houseRules: true }).find(c => c.id === 'idle')?.status;
    // transitions measured on their three frames: an empty middle and a type used three times are flagged
    const grid = (f) => Float32Array.from({ length: 256 }, (_, i) => f(i));
    const A = grid(i => (i % 16) / 16), C = grid(i => Math.floor(i / 16) / 16), B = grid(() => 0.02);
    const st = (t, px) => { const m = px.reduce((a, b) => a + b, 0) / 256; return { t, luma: m, sd: Math.sqrt(px.reduce((a, b) => a + (b - m) ** 2, 0) / 256), px }; };
    r = applyOps(store.state.project, [{ op: 'clear' }, ...[0, 1, 2, 3].map(k => ({ op: 'add', id: `q${k}`, media: vid, track: 'V1', in: k, dur: 1, ...(k ? { transition: { type: 'whip_left', dur: 0.4 } } : {}) }))], media);
    const q1 = r.project.clips.find(c => c.id === 'q1');
    const fr = [['a', q1.start - 0.18], ['b', q1.start], ['c', q1.start + 0.18]].map(([k, t]) => ({ t, k, clip: 'q1', label: k }));
    const rep = transitionReport(r.project, fr, [{ blob: null, caption: '', stats: [st(fr[0].t, A), st(fr[1].t, B), st(fr[2].t, C)] }]);
    out.trans = { text: rep.text, weak: rep.weak };
    // set pieces: each one expands into its tested build on the shots at its time
    const base = [{ op: 'clear' }, ...[0, 1, 2, 3, 4, 5].map(k => ({ op: 'add', id: `s${k}`, media: vid, track: 'V1', in: k * 0.4, dur: 1.5, focus: { x: 0.5, y: 0.42 } })), { op: 'add', media: mus, track: 'A1', start: 0, in: 0, dur: 9 }];
    out.pieces = {};
    const sheets = [];
    for (const [kind, extra] of [['freeze_hit', { at: 2.0, word: 'HIM' }], ['blood_drop', { at: 4.5, word: 'DARLING' }], ['plastic_burst', { at: 3.0 }], ['crt_dive', { at: 6.0 }], ['polaroid_toss', { at: 1.5 }], ['glass_shatter', { at: 7.5, anchor: { x: 0.7, y: 0.75 } }], ['lens_blood', { at: 4.6 }], ['light_title', { at: 5.0, word: 'ALONG' }], ['pupil_loop', {}], ['emblem_dive', { at: 3.0 }], ['lightning_strike', { at: 4.5 }], ['time_stop', { at: 2.0 }], ['speed_rift', { at: 6.0 }], ['bolt_split', { at: 7.5 }], ['speedforce_loop', {}]]) {
      const before = applyOps(store.state.project, base, media).project;
      const res = applyOps(before, [{ op: 'piece', kind, ...extra }], media);
      const lr = await layerReport(res.project, media);
      out.pieces[kind] = { added: res.project.clips.length - before.clips.length, changed: res.applied, bad: res.issues.filter(x => !/moved|removed|cut|landed/.test(x)), invisible: lr.invisible, blown: lr.blown };
      const T = extra.at ?? 8.8;
      const ts = kind === 'pupil_loop' || kind === 'speedforce_loop' ? [8.2, 8.55, 8.85, 0.05] : kind === 'speed_rift' ? [5.45, 5.75, 5.95, 6.15] : kind === 'time_stop' ? [2.05, 2.4, 2.85, 3.0] : kind === 'blood_drop' ? [3.4, 4.2, 4.5, 4.75] : [T - 0.3, T, T + 0.15, T + 0.4];
      const frames = await renderStills(res.project, ts, 360, undefined, media);
      sheets.push({ kind, frames });
    }
    const W = 203, H = 360, cv = document.createElement('canvas');
    cv.width = W * 4; cv.height = H * sheets.length;
    const g = cv.getContext('2d');
    sheets.forEach((sh, r) => sh.frames.forEach((f, c) => { if (f) g.drawImage(f, c * W, r * H, W, H); g.fillStyle = '#000a'; g.fillRect(c * W, r * H, W, 22); g.fillStyle = '#fff'; g.font = '14px monospace'; g.fillText(sh.kind, c * W + 4, r * H + 16); }));
    out.pieceSheet = cv.toDataURL('image/jpeg', 0.8);
    // the lyric guard: wrong words corrected, captions moved onto the sung time, invented lines removed
    r = applyOps(store.state.project, [{ op: 'clear' }, { op: 'add', media: vid, track: 'V1', in: 0, dur: 6 }, { op: 'add', id: 'mus', media: mus, track: 'A1', start: 0, in: 0, dur: 6 },
      { op: 'text', id: 'wrong', start: 0.4, dur: 1.2, text: 'you were always\nby *my* side' }, { op: 'text', id: 'made', start: 3.0, dur: 1.2, text: 'the night is young tonight' },
      { op: 'text', id: 'title', start: 4.5, dur: 1, text: 'BUTCHER' }, { op: 'text', id: 'late', start: 1.0, dur: 1, text: 'I never left' }], media);
    const lp = { ...r.project, lyrics: parseLyrics('[00:02.00] you were always by my side\n[00:04.00] dark rivers run\n[00:30.00] I never left') };
    const lnotes = lyricGuard(lp, media);
    const tx = id => lp.clips.find(c => c.id === id);
    out.lyr = { wrongStart: tx('wrong')?.start, wrongText: tx('wrong')?.text, made: !!tx('made'), title: !!tx('title'), late: !!tx('late'), notes: lnotes };
    const np = { ...r.project, lyrics: undefined };
    lyricGuard(np, media);
    out.lyrNone = np.clips.filter(c => c.kind === 'text').map(c => c.id);
    // the edit ends with its picture: a sound or caption past the last shot never adds black frames
    r = applyOps(store.state.project, [{ op: 'clear' }, { op: 'add', media: vid, track: 'V1', in: 0, dur: 2 }, { op: 'add', media: mus, track: 'A1', start: 0, in: 0, dur: 5 }, { op: 'sfx', sound: 'boom', start: 1.9 }, { op: 'text', start: 1.5, dur: 2, text: 'X' }], media);
    out.tail = { dur: r.project.clips.reduce((a, c) => Math.max(a, (c.kind === 'video' || c.kind === 'image') ? c.start + c.dur : 0), 0) };
    const { projectDuration: pd } = window.__voidfx;
    out.tail.len = pd ? pd(r.project) : null;
    // designed loops: each style lands exactly on frame 0's frame and framing
    out.loops = {};
    for (const style of ['push', 'light', 'whip']) {
      const lr = applyOps(store.state.project, [{ op: 'clear' }, { op: 'add', id: 'f0', media: vid, track: 'V1', in: 0.8, dur: 1.2, focus: { x: 0.5, y: 0.42 }, transform: { scale: 1.1 } }, { op: 'add', id: 'f1', media: vid, track: 'V1', in: 2.5, dur: 1.2 }, { op: 'loop', style }], media);
      const tw = lr.project.clips.find(c => c.name === 'loop twin');
      const end = (k) => (tw.kf?.[k] || []).slice(-1)[0]?.v;
      out.loops[style] = { twin: !!tw, endScale: end('scale'), endX: end('x'), landing: lr.project.clips.filter(c => c.name === 'loop landing').map(c => c.preset), lastKf: Object.keys(lr.project.clips.find(c => c.id === 'f1')?.kf || {}), srcEnd: tw ? +((tw.in ?? 0) + tw.dur * (tw.speed ?? 1)).toFixed(3) : null };
      if (style === 'push') {
        const frames = await renderStills(lr.project, [1.95, 2.05, 2.15, 2.25, 2.3, 2.38, 0, 0.1], 300, undefined, media);
        const cv = document.createElement('canvas'); cv.width = 169 * 8; cv.height = 300; const g = cv.getContext('2d');
        frames.forEach((f, i) => f && g.drawImage(f, i * 169, 0, 169, 300));
        out.loopSheet = cv.toDataURL('image/jpeg', 0.8);
      }
    }
    // lessons from the critic are remembered and read back
    await clearLessons();
    await addLessons([{ area: 'picture', severity: 'critical', problem: 'The drop is a white card. More words.', fix: 'Delete the wash. More.', project: 'x' }]);
    out.lessons = lessonsText();
    await clearLessons();
    return out;
  });
  check('a reused id goes to the new clip and is reported', u.alias.lookUntouched && u.alias.dustSet && u.alias.reported && u.alias.autoId, JSON.stringify(u.alias));
  check('beat camera sections', u.sections?.length === 2 && u.sections[1].punch === 0.03 && u.sections[1].every === 'half', JSON.stringify(u.sections));
  check('gates: repeated shots, stacked flashes, loop in sound', u.gates.repeats === 'warn' && u.gates['flash-stack'] === 'warn' && u.gates['loop-sound'] === 'warn', JSON.stringify(u.gates));
  check('the loop operation lands on frame 0', u.loop && Math.abs(u.loop.end - 2) < 0.01 && Math.abs(u.loop.srcEnd - 0.8) < 0.01 && u.loop.focus?.x === 0.4 && u.loop.color?.brightness === 0.1, JSON.stringify(u.loop));
  check('velocity ramps burst on the cut', u.ramp && u.ramp.t < 0.03 && u.ramp.v >= 1.5, JSON.stringify(u.ramp));
  check('idle shots: only the shot with nothing on it is flagged', JSON.stringify(u.idle) === '["p3"]' && u.idleGate === 'warn', JSON.stringify({ idle: u.idle, gate: u.idleGate }));
  check('transitions measured: an empty middle and a type used three times are flagged', u.trans.weak.length === 1 && /empty black frame/.test(u.trans.text) && /used 3 times/.test(u.trans.text), u.trans.text);
  writeFileSync(join(OUT, 'pieces.jpg'), Buffer.from(u.pieceSheet.split(',')[1], 'base64'));
  delete u.pieceSheet;
  check('every set piece expands into its build with no problems', Object.values(u.pieces).every(x => x.added >= 1 && !x.bad.length), JSON.stringify(u.pieces));
    check('lyric guard: a caption is the real line on its sung time; invented or unsung lines are removed', Math.abs(u.lyr.wrongStart - 1.94) < 0.02 && /by \*my\* side/.test(u.lyr.wrongText) && !u.lyr.made && u.lyr.title && !u.lyr.late, JSON.stringify(u.lyr));
  check('lyric guard: with no lyrics only short titles stay', JSON.stringify(u.lyrNone) === '["title"]', JSON.stringify(u.lyrNone));
    check('the edit ends with its picture (no black tail after the last shot)', u.tail.len !== null && Math.abs(u.tail.len - u.tail.dur) < 0.01, JSON.stringify(u.tail));
  writeFileSync(join(OUT, 'loop-push.jpg'), Buffer.from(u.loopSheet.split(',')[1], 'base64')); delete u.loopSheet;
  check('designed loops land on frame 0 (push, light, whip)', u.loops.push.endScale === 1.1 && u.loops.push.landing.includes('zoom_blur') && u.loops.push.lastKf.includes('scale') && u.loops.light.landing.includes('exposure_wash') && u.loops.whip.endX === 0 && Object.values(u.loops).every(l => l.twin && Math.abs(l.srcEnd - 0.8) < 0.01), JSON.stringify(u.loops));
    check('critic lessons are remembered for later edits', /white card/.test(u.lessons) && /Delete the wash/.test(u.lessons), u.lessons);
}

// ---------- 5b. long form: one planning call, built from templates ----------
if (on('longform')) {
  await S(() => window.__voidfx.store.set({ view: 'home', homeTab: 'longform' }));
  const jid = await page.evaluate(async () => {
    const b = await (await fetch('/test/media/talk.mp4')).blob();
    const file = new File([b], 'talk.mp4', { type: 'video/mp4' });
    const tr = '1\n00:00:02,000 --> 00:00:04,500\nToday we break down the process\n\n2\n00:00:05,000 --> 00:00:08,000\nThere are three steps to it\n';
    const j = await window.__voidfx.startLongform({ name: 'Long talk', effort: 'medium', file, longform: { notes: 'No zooms in the intro.', transcript: tr, options: { captions: true, chapters: true, breakdowns: true, zooms: true, trim: true, pace: 'calm', accent: '#7fd3ff' } } });
    return j?.id;
  });
  await page.waitForFunction(id => ['done', 'error'].includes(window.__voidfx.store.state.jobs.find(x => x.id === id)?.state), jid, { timeout: 300000 });
  const lj = await page.evaluate(id => window.__voidfx.store.state.jobs.find(x => x.id === id), jid);
  const lf = await page.evaluate(async pid => {
    const v = window.__voidfx; const r = await v.getRecord(pid); const p = r.project;
    const media = Object.fromEntries((r.media || []).map(m => [m.id, m]));
    return { w: p.width, h: p.height, segs: p.clips.filter(c => c.kind === 'video').length, graphics: p.clips.filter(c => c.kind === 'graphic').length, texts: p.clips.filter(c => c.kind === 'text').map(c => c.text.slice(0, 30)), trans: p.clips.filter(c => c.transition).map(c => c.transition.type), stub: window.__longform, rounds: (r.rounds || []).length };
  }, lj.projectId);
  check('long form: the edit is planned in one call and built', lj.state === 'done' && lf.segs >= 2 && lf.graphics >= 2, JSON.stringify({ state: lj.state, error: lj.error, steps: lj.steps.map(s => `${s.id}:${s.state}`), ...lf }));
  check('long form: Opus reads the transcript, the pauses and the owner\'s comments', lf.stub?.transcript && lf.stub?.comments, JSON.stringify(lf.stub));
  check('long form: chapters, a breakdown, a callout and captions are placed; the timeline stays calm', lf.texts.some(t => /CHAPTER 01/.test(t)) && lf.texts.some(t => /Collect the evidence/.test(t)) && lf.texts.some(t => /Key term/.test(t)) && lf.texts.some(t => /Today we break down/.test(t)) && lf.trans.every(t => t === 'crossfade') && lf.w === 1920, JSON.stringify(lf));
  // a frame of the breakdown panel, for review
  const shot = await page.evaluate(async pid => {
    const v = window.__voidfx; await v.open(pid);
    await new Promise(r => setTimeout(r, 1500));
    const p = v.store.state.project;
    const fr = await v.renderStills(p, [0.9, 4.9, 9.2, 10.4], 360, undefined, v.store.state.media);
    const cv = document.createElement('canvas'); cv.width = 640 * 2; cv.height = 360 * 2; const g = cv.getContext('2d');
    fr.forEach((f, i) => f && g.drawImage(f, (i % 2) * 640, Math.floor(i / 2) * 360, 640, 360));
    return cv.toDataURL('image/jpeg', 0.85);
  }, lj.projectId);
  writeFileSync(join(OUT, 'longform.jpg'), Buffer.from(shot.split(',')[1], 'base64'));
  await S(() => window.__voidfx.store.set({ view: 'home' }));
}

// ---------- 6. persistence ----------
if (on('build') && on('persist')) {
  const before = await S(async () => { const v = window.__voidfx; v.store.flushSave(); const ps = await v.listProjects(); return { projects: ps.length, jobs: v.store.state.jobs.length, extra: v.store.state.jobs.find(j => j.kind === 'create' && j.effort === 'extra').projectId }; });
  await page.waitForTimeout(1200);
  await page.reload();
  await page.waitForSelector('.home');
  await page.waitForFunction(() => window.__voidfx?.store.state.jobs.length > 0, null, { timeout: 30000 }).catch(() => {});
  const after = await page.evaluate(async extra => { const v = window.__voidfx; const ps = await v.listProjects(); const r = await v.getRecord(extra); return { projects: ps.length, jobs: v.store.state.jobs.length, rounds: r.rounds?.length, notes: r.rounds?.[1]?.notes?.length, crit: !!r.rounds?.[0]?.critique }; }, before.extra);
  check('projects survive a reload', after.projects === before.projects, `${after.projects}/${before.projects}`);
  check('jobs, rounds, notes and critiques survive a reload', after.jobs === before.jobs && after.rounds >= 2 && after.notes >= 2 && after.crit, JSON.stringify(after));
}

check('no page errors', !errors.length, errors.slice(0, 5).join(' | '));
const failed = results.filter(r => !r.ok);
writeFileSync(join(OUT, 'suite-report.json'), JSON.stringify({ seconds: Math.round((Date.now() - t0) / 1000), results, errors }, null, 1));
console.log(`\n${results.length - failed.length}/${results.length} checks passed in ${Math.round((Date.now() - t0) / 1000)} s`);
await browser.close();
server.close();
process.exit(failed.length ? 1 : 0);
