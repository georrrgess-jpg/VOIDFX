// End-to-end test of the studio in headless Chromium (after `node build.mjs`; media from test/make_media.sh).
// Stubs the claude.ai runtime: `sample` answers like Opus would (casting, a plan built from the media
// it is shown, an approving review) and records what it was sent; `downloads.save` hands files back.
// Flow: main menu → database → standards → AI Edit (files + database) built in the background while a
// blank project is edited (the plan includes a custom graphic, a custom effect and one effect that does not
// compile, which the review must remove) → the critic → its write-up → the round 2 composer → the revision (editor
// locked) → editor → checks → export (mastered) → reload → reopen. Writes screenshots and the MP4 to test/out/.
import { createRequire } from 'node:module';
import http from 'node:http';
import { readFileSync, writeFileSync, mkdirSync, existsSync, statSync } from 'node:fs';
import { join, extname, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const OUT = join(ROOT, 'test', 'out');
const MEDIA = join(ROOT, 'test', 'media');
mkdirSync(OUT, { recursive: true });

const types = { '.html': 'text/html', '.mp4': 'video/mp4', '.wav': 'audio/wav', '.png': 'image/png' };
const server = http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  const file = url === '/' ? join(ROOT, 'dist', 'index.html') : join(ROOT, url);
  if (!file.startsWith(ROOT) || !existsSync(file) || statSync(file).isDirectory()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'content-type': types[extname(file)] || 'application/octet-stream' });
  res.end(readFileSync(file));
});
await new Promise(r => server.listen(8777, r));

const browser = await chromium.launch({ args: ['--autoplay-policy=no-user-gesture-required'] });
const ctx = await browser.newContext({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 1 });
const page = await ctx.newPage();
const errors = [];
const watch = p => {
  p.on('pageerror', e => errors.push('pageerror: ' + e.message));
  p.on('console', m => { if (m.type() === 'error' && !/favicon|fonts\.g/.test(m.text())) errors.push('console: ' + m.text()); });
};
watch(page);

await ctx.addInitScript(() => {
  window.__calls = [];
  window.__saved = [];
  const toB64 = async blob => {
    const buf = new Uint8Array(await blob.arrayBuffer());
    let s = '';
    for (let i = 0; i < buf.length; i += 0x8000) s += String.fromCharCode.apply(null, buf.subarray(i, i + 0x8000));
    return btoa(s);
  };
  const TRANS = ['logo', 'ink', 'dive', 'shatter', 'blink', 'slash', 'cube_left', 'punch', 'light_leak', 'shadow', 'tear', 'burn', 'whip_left'];
  const PICTURE = new Set(['clear', 'project', 'add', 'look', 'track']);
  function planFrom(text) {
    const media = [...text.matchAll(/^(m[a-z0-9]+) (video|audio|image) "([^"]+)" ([\d.]+s|still image)/gm)].map(m => ({ id: m[1], kind: m[2], dur: m[4] === 'still image' ? 3 : parseFloat(m[4]) }));
    const ops = [{ op: 'clear' }, { op: 'project', camera: { on: true, every: 'beat', punch: 0.055, kick: 1 } }];
    let t = 0, k = 0;
    const vis = media.filter(m => m.kind !== 'audio');
    // use every visual file twice so there are enough cuts to exercise the transitions
    for (let round = 0; round < 2; round++) for (const m of vis) {
      const dur = 1.6;
      const op = { op: 'add', id: `v${k}`, media: m.id, track: 'V1', in: m.kind === 'image' ? 0 : Math.min(Math.max(0, m.dur - dur - 0.6), round * 1.2 + 0.3), dur };
      if (k > 0) op.transition = { type: TRANS[(k - 1) % TRANS.length] };
      if (op.transition?.type === 'dive') op.transition = { type: 'dive', at: { x: 0.5, y: 0.4 }, to: { x: 0.52, y: 0.42 } };
      if (op.transition?.type === 'shatter') op.transition = { type: 'shatter', at: { x: 0.6, y: 0.7 } };
      if (k === 1) op.ramp = { fast: 2, slow: 0.5 };
      if (k === 2) op.focus = { x: 0.62, y: 0.38 };
      ops.push(op); t += dur; k++;
    }
    const music = media.find(m => m.kind === 'audio');
    if (music) ops.push({ op: 'add', id: 'mus', media: music.id, track: 'A1', start: 0, in: 0, dur: Math.min(music.dur, t) });
    ops.push({ op: 'text', id: 'cap', track: 'T1', start: 0.3, dur: 2.4, text: 'COULD IT BE\n*HIM*', words: [0, 0.25, 0.5, 0.9], style: { font: 'Inter', weight: 900, uppercase: true, size: 0.046, lineScales: [1, 1.3], stroke: 0.07, shadow: 0.65, scrim: 0.35, emphColor: '#ff2b3a' }, anim: { in: 'words', out: 'fade' }, transform: { y: 0.25 } });
    ops.push({ op: 'text', id: 'hero', track: 'T1', start: 4.0, dur: 1.8, text: '*ALONG*', style: { font: 'Inter', weight: 900, size: 0.085, uppercase: true, stroke: 0.06, motif: 'blood' }, anim: { in: 'bloom', out: 'blowaway', inDur: 0.9, outDur: 0.7 }, transform: { y: 0.27 } });
    ops.push({ op: 'text', id: 'knock', start: 6.2, dur: 1.4, text: 'BAY HARBOR\nBUTCHER', style: { font: 'Inter', weight: 900, size: 0.09, uppercase: true, knockout: true, fit: true }, anim: { in: 'slam', out: 'zoom', inDur: 0.4, outDur: 0.35 } });
    ops.push({ op: 'look', preset: 'noir_red', params: { keep: '#c70f14' } });
    ops.push({ op: 'fx', id: 'rays', preset: 'light_rays', start: 0.2, dur: 2.4, at: { x: 0.62, y: 0.18 } });
    ops.push({ op: 'fx', id: 'wash', preset: 'exposure_wash', start: 3.0, dur: 0.45, over: true });
    ops.push({ op: 'fx', id: 'bl', preset: 'blood_lens', start: 7.0, dur: 1.4, params: { size: 1.2, nope: 3 } });
    ops.push({ op: 'graphic', id: 'emb', start: 0.4, dur: 1.2, gw: 0.45, glow: 0.6, reveal: { in: 'pop', out: 'fade' }, transform: { y: -0.12 },
      svg: '<svg viewBox="0 0 400 400"><circle cx="200" cy="200" r="170" fill="none" stroke="#ffd23f" stroke-width="16"/><path d="M230 40 L120 220 L195 220 L160 360 L290 160 L210 160 Z" fill="#ffd23f" stroke="#fff" stroke-width="5"/></svg>' });
    ops.push({ op: 'shader', id: 'arc', start: 3.0, dur: 0.6, blend: 'add', code: 'vec4 effect(vec2 uv, float t, float p) { vec2 q = aspectUv(uv); float d = boltDist(q, vec2(-0.18, -0.42), vec2(0.12, 0.35), floor(t * 14.0), 0.3); float core = glow(d - 0.002, 0.003), halo = glow(d, 0.035) * 0.55; float a = (core + halo) * (0.55 + 0.45 * uBeat) * smoothstep(0.0, 0.08, p) * smoothstep(1.0, 0.75, p); return vec4(mix(vec3(1.0, 0.72, 0.18), vec3(1.0), core), a); }' });
    ops.push({ op: 'shader', id: 'oops', start: 5.0, dur: 0.4, code: 'vec4 effect(vec2 uv, float t, float p) { return vec4(nope(uv), 1.0); }' });
    if (text.includes('TIMED LYRICS')) ops.push({ op: 'lyrics', from: 1, to: 3, text: { 2: 'THE EVIDENCE\nPOINTS *BACK*' } });
    ops.push({ op: 'sounds', volume: 0.35 });
    ops.push({ op: 'sfx', sound: 'riser', start: 1.4, volume: 0.3 });
    return { message: 'Concept: the evidence points back at him. Set pieces: the logo dive, the blood bloom, the blink.', ops };
  }
  window.claude = {
    use: async name => {
      if (name === 'sample') {
        const f = async (input, opts = {}) => {
          const turns = typeof input === 'string' ? [{ role: 'user', content: input }] : input;
          const full = turns.map(t => t.content).join('\n\n=====\n\n');
          const last = turns[turns.length - 1].content;
          window.__calls.push({ roles: turns.map(t => t.role), full, images: (opts.images || []).length, effort: opts.effort, model: opts.model });
          window.__lastImages = opts.images || [];
          await new Promise(r => setTimeout(r, 200));
          let reply;
          if (full.includes('You are casting material')) {
            const ids = [...full.matchAll(/^(lib\S+) /gm)].map(m => m[1]);
            reply = JSON.stringify({ items: ids.map(id => ({ id, why: 'test' })), message: 'Took the song and the landscape clip.' });
          } else if (full.includes('You are the critic for VOIDFX Studio')) {
            reply = JSON.stringify({
              score: 6.2, verdict: 'not ready', headline: 'Competent, but the hook is soft and three cuts drift off the beat.',
              scores: { hook: 5, rhythm: 5.5, transitions: 7, motion: 6, text: 7.5, sound: 6, concept: 6.5, picture: 6, loop: 3 },
              strengths: ['The logo dive lands on a downbeat.', 'Captions are clean and well timed.'],
              issues: [
                { severity: 'critical', at: 0, area: 'hook', problem: 'The first second is a static shot with nothing hitting.', fix: 'Open on the strongest shot with a zoom punch on the first downbeat.' },
                { severity: 'major', at: 3.2, area: 'rhythm', problem: 'The blood bloom starts 90 ms after the snare.', fix: 'Move the cut onto the beat at 3.20 s.' },
                { severity: 'major', at: null, area: 'loop', problem: 'The last frame does not match frame 0.', fix: 'End on the opening shot so the loop is invisible.' },
                { severity: 'minor', at: 8.0, area: 'text', problem: 'ALONG sits close to the face.', fix: 'Move it up to y 0.3.' },
              ],
              versus: 'Below the v7 and v10 benchmarks: fewer set pieces and no motion pass on the montage.',
              brief: '1. Rebuild the first second around a hit.\n2. Snap every cut to the beat grid.\n3. Close the loop on frame 0.',
              ...(full.includes('WHAT THIS ROUND WAS ASKED TO FIX') ? { followUp: [...full.matchAll(/^(N\d+)(?: @ [\d.]+s)?: /gm)].map((m, i) => ({ id: m[1], status: i % 2 ? 'partly' : 'fixed', comment: 'checked in the frames' })) } : {}),
            });
            window.__critics = [...(window.__critics || []), { follow: full.includes('WHAT THIS ROUND WAS ASKED TO FIX'), anchored: full.includes('THE LAST ROUND SCORED'), tools: full.includes("THE STUDIO'S TOOLS"), exemplars: full.includes('WORKED EXAMPLES') }];
          } else if (last.includes('NOTES WITH NO APPLIED OPERATIONS')) {
            const ids = [...last.matchAll(/^(N\d+) \[/gm)].map(m => m[1]);
            window.__filledNotes = (window.__filledNotes || 0) + 1;
            reply = JSON.stringify({ message: `Carried ${ids.join(', ')}.`, notes: ids.map(id => ({ id, plan: 'dust in the light' })), ops: [{ op: 'fx', preset: 'dust', start: 0.5, dur: 2, note: ids }] });
          } else if (last.includes('CALL 1 OF 2: THE CUT')) {
            // the first cut call comes back empty, as it did for the owner: the studio must ask again at the same effort
            if (!window.__failedOnce) { window.__failedOnce = true; window.__calls[window.__calls.length - 1].failed = 'empty_completion'; throw { code: 'empty_completion', message: 'no text' }; }
            window.__parts = [...(window.__parts || []), 'cut'];
            const plan = planFrom(full);
            reply = JSON.stringify({ message: plan.message, design: 'CONCEPT: the evidence points back at him. Logo dive on the first downbeat.', ops: plan.ops.filter(o => PICTURE.has(o.op)) });
          } else if (last.includes('CALL 2 OF 2: THE DESIGN')) {
            window.__parts = [...(window.__parts || []), 'design'];
            const plan = planFrom(full);
            reply = JSON.stringify({ message: 'Designed the transitions, titles and light.', ops: plan.ops.filter(o => !PICTURE.has(o.op)) });
          } else if (/ROUND \d+ INSTRUCTIONS FROM THE OWNER/.test(full) && !/REVIEW \d OF/.test(last)) {
            reply = JSON.stringify({ message: 'Round 2: re-cut the opening on the downbeat and closed the loop.', ops: [{ op: 'project', camera: { on: true, every: 'beat', punch: 0.07, kick: 1.2 } }] });
          } else if (last.includes('YOUR CUSTOM ELEMENTS, RENDERED')) {
            const els = [...last.matchAll(/^ELEMENT (\S+) \(/gm)].map(m => m[1]);
            reply = JSON.stringify({ message: 'Workshop: the elements read.', elements: els.map(id => ({ id, score: 8, frames: 'fine' })), ops: [] });
          } else if (/REVIEW \d OF/.test(last)) {
            const ids = [...last.matchAll(/^(N\d+) \[/gm)].map(m => m[1]);
            window.__reviews = [...(window.__reviews || []), last.slice(0, 60)];
            const notes = ids.map(id => ({ id, status: 'done', check: 'visible in its frames' }));
            const scores = { hook: 7, rhythm: 7.5, transitions: 8, motion: 7, text: 8, sound: 7, concept: 7.5, picture: 7.5, loop: 6 };
            if (last.includes('effect oops does not compile')) {
              window.__sawCompileError = true;
              reply = JSON.stringify({ message: 'Removed the effect that did not compile.', scores, notes, ops: [{ op: 'remove', id: 'oops' }] });
            } else reply = JSON.stringify({ message: 'Reviewed: the checkpoint is clean enough; approved.', scores, notes, ops: [] });
          } else {
            reply = JSON.stringify(planFrom(full));
          }
          opts.onText?.({ text: reply, delta: reply });
          return { text: reply, truncated: false, modelTierApplied: 'complex', modelApplied: opts.model };
        };
        f.limits = async () => ({ maxPromptBytes: 262144, images: { maxCount: 20, maxInputBytes: 20e6, mediaTypes: ['image/jpeg', 'image/png'] } });
        return f;
      }
      if (name === 'downloads') return { save: async ({ filename, data }) => { window.__saved.push({ filename, size: data.size ?? data.length, b64: typeof data === 'string' ? btoa(data) : await toB64(data) }); return { status: 'saved' }; } };
      return null;
    },
  };
});

const report = {};
const shot = name => page.screenshot({ path: join(OUT, `${name}.png`) });
await page.goto('http://localhost:8777/');
await page.waitForSelector('.home');
await page.waitForTimeout(1200);
await shot('01-home');

// ---- database ----
await page.click('.home-link:has-text("Database")');
await page.setInputFiles('.ldrop input[type=file]', [join(MEDIA, 'music.wav'), join(MEDIA, 'pack.mp4')]);
await page.waitForFunction(() => document.querySelectorAll('.litem').length === 2 && !document.querySelector('.litem-prog'), null, { timeout: 120000 });
await page.waitForTimeout(500);
await shot('02-database');
report.database = await page.evaluate(() => [...document.querySelectorAll('.litem')].map(e => e.querySelector('.litem-meta')?.textContent));

// ---- standards ----
await page.click('.home-link:has-text("Standards")');
await page.setInputFiles('.stdadd input[type=file]', join(MEDIA, 'portrait.mp4'));
await page.fill('#sd-notes', 'Every cut lands on a beat and the title acts out the lyric.');
await page.click('.stdadd .cta-red');
await page.waitForFunction(() => document.querySelector('.scard .sprof'), null, { timeout: 120000 });
await shot('03-standards');

// ---- presets ----
await page.click('.home-link:has-text("Presets")');
await page.waitForTimeout(600);
await shot('04-presets');
await page.click('.home-link:has-text("House rules")');
await page.waitForTimeout(600);
await shot('05-rules');

// ---- AI Edit ----
await page.click('.home-link:has-text("AI Edit")');
await page.waitForSelector('.preset-card');
await page.click('.preset-card:has-text("VOIDFX · Dexter")');
await page.fill('#c-notes', 'Smoke test: the evidence points back at him.');
await page.click('.seg-big button:has-text("Both")');
if (!(await page.$('#c-lyrics'))) await page.click('.linkbtn:has-text("Lyrics for captions")');
await page.fill('#c-lyrics', '[00:00.50] Could it be him\n[00:02.10] The evidence points back\n[00:04.00] All along\n[00:06.00]');
await page.setInputFiles('.cdrop input[type=file]', [join(MEDIA, 'portrait.mp4'), join(MEDIA, 'rotated.mp4'), join(MEDIA, 'still.png')]);
await page.waitForTimeout(400);
await shot('06-create');
await page.click('.cgo .cta-opus');
// the build runs in the background: the wizard says so and the owner is free to do other things
await page.waitForSelector('.started', { timeout: 30000 });
await page.waitForTimeout(800);
await shot('06b-started');
report.backgroundStart = await page.evaluate(() => ({ view: window.__voidfx.store.state.view, jobs: window.__voidfx.store.state.jobs.map(j => `${j.kind}:${j.state}`) }));
// meanwhile: open a blank project, edit it, go back to the menu
await page.click('.home-link:has-text("Home")');
await page.waitForTimeout(700);
await shot('07a-dashboard-running');
await page.click('.desk-cta .cta-ice');
await page.waitForSelector('.app');
await page.evaluate(() => window.__voidfx.store.commit(p => { p.name = 'Side project'; }));
report.whileBuilding = await page.evaluate(() => ({ lock: window.__voidfx.store.state.lock, name: window.__voidfx.store.state.project.name, job: window.__voidfx.store.state.jobs.map(j => `${j.kind}:${j.state}:${(j.steps.find(s => s.state === 'run') || {}).id || ''}`) }));
await page.click('.top .brand');
await page.waitForSelector('.home');
// wait for the build and the automatic critique
await page.waitForFunction(() => { const j = window.__voidfx.store.state.jobs; return j.some(x => x.kind === 'critique' && ['done', 'error'].includes(x.state)) || j.some(x => x.state === 'error'); }, null, { timeout: 300000 });
await page.waitForTimeout(1200);
report.jobs = await page.evaluate(() => window.__voidfx.store.state.jobs.map(j => ({ kind: j.kind, state: j.state, round: j.round, summary: (j.summary || j.error || '').slice(0, 120), steps: j.steps.map(x => `${x.id}:${x.state}${x.detail ? `(${x.detail})` : ''}`) })));
await shot('07b-dashboard-done');
// the "⋮" menu on the recent card
await page.click('.prows .prow:has-text("Dexter") .kebab-b');
await page.waitForTimeout(300);
await shot('07c-kebab');
report.menu = await page.evaluate(() => [...document.querySelectorAll('.kebab-pop button')].map(b => b.textContent));
await page.click('.kebab-pop button:has-text("Read the critique")');
await page.waitForSelector('.crit-modal .crit');
await page.waitForTimeout(600);
await shot('07d-critique');
await page.click('.crit-modal .comp-foot .cta-opus');
await page.waitForSelector('.comp .comp-right');
await page.waitForTimeout(500);
await page.fill('.comp-right textarea.ta.big', 'Open on the bathtub shot and make the drop hit harder.');
await page.click('.comp .quick .chipbtn:has-text("Keep everything")');
await page.click('.comp-right .linkbtn:has-text("What Opus will receive")');
await page.waitForTimeout(300);
await shot('07e-composer');
report.composer = await page.evaluate(() => ({ title: document.querySelector('#comp-title')?.textContent, count: document.querySelector('.comp-count')?.textContent, preview: document.querySelector('.comp-preview')?.textContent?.slice(0, 600) }));
await page.click('.comp-go .cta-opus');
await page.waitForFunction(() => !document.querySelector('.comp-right'), null, { timeout: 10000 });
// open the project while round 2 runs: the editor is locked and says so
const builtId = await page.evaluate(() => window.__voidfx.store.state.jobs.find(j => j.kind === 'create').projectId);
await page.evaluate(id => window.__voidfx.open(id), builtId);
await page.waitForSelector('.app', { timeout: 30000 });
await page.waitForSelector('.lockbar', { timeout: 30000 }).catch(() => {});
await page.waitForTimeout(400);
await shot('07f-locked');
report.locked = await page.evaluate(() => ({ lock: window.__voidfx.store.state.lock, banner: document.querySelector('.lockbar')?.textContent?.slice(0, 160) || null }));
await page.waitForFunction(() => { const j = window.__voidfx.store.state.jobs; return j.filter(x => x.kind === 'critique' && ['done', 'error'].includes(x.state)).length >= 2 || j.some(x => x.state === 'error'); }, null, { timeout: 300000 });
await page.waitForTimeout(800);
report.director = await page.evaluate(() => {
  const s = window.__voidfx.store.state;
  return {
    calls: window.__calls.map(c => ({ failed: c.failed, effort: c.effort, last: c.full.slice(-80).replace(/\s+/g, ' '), roles: c.roles.length, images: c.images, chars: c.full.length, house: c.full.includes('VOIDFX HOUSE RULES'), standards: c.full.includes('REFERENCE EDITS THE OWNER ADDED'), checkpoint: c.full.includes('AUTOMATED CHECKPOINT'), casting: c.full.includes('You are casting material'), critic: c.full.includes('You are the critic'), round2: c.full.includes('ROUND 2 INSTRUCTIONS') })),
    rounds: s.rounds.map(r => `R${r.n} ${r.kind} applied=${r.applied} critique=${r.critique ? r.critique.score : '-'} fromCritic=${(r.fromCritic || []).length}`),
    custom: s.project.clips.filter(c => c.kind === 'graphic' || c.kind === 'shader').map(c => `${c.id}:${c.kind}:${c.track}`),
    sawCompileError: !!window.__sawCompileError,
    criticSawCustom: window.__calls.some(c => c.full.includes('You are the critic') && c.full.includes('Custom graphics and effects designed for this edit (2)')),
    opusSawApi: window.__calls.some(c => c.full.includes('CUSTOM GRAPHICS AND EFFECTS')),
    lockAfter: s.lock,
    jobs: s.jobs.map(j => `${j.kind}:${j.state}:R${j.round}`),
    media: s.mediaOrder.map(id => `${id} ${s.media[id].kind} ${s.media[id].name} ${s.media[id].origin} ${s.media[id].status}`),
    format: `${s.project.width}x${s.project.height}@${s.project.fps}`,
    transitions: s.project.clips.filter(c => c.transition).map(c => c.transition.type),
    sfx: s.project.clips.filter(c => c.kind === 'sfx').length,
    ramp: s.project.clips.filter(c => c.kf?.speed?.length).map(c => `${c.id}:${c.kf.speed.length} keys`),
    lyrics: s.project.lyrics ? `${s.project.lyrics.timed ? 'timed' : 'plain'} ${s.project.lyrics.lines.length} lines` : null,
    lyricClips: s.project.clips.filter(c => c.name?.startsWith('lyric')).map(c => `${c.id} ${c.start.toFixed(2)}+${c.dur.toFixed(2)} ${JSON.stringify(c.text)} words=${(c.words || []).length}`),
    focus: s.project.clips.filter(c => c.focus).map(c => `${c.id}:${c.focus.x},${c.focus.y}`),
    opusSawLyrics: window.__calls.some(c => c.full.includes('TIMED LYRICS') && c.full.includes('L2 2.10')),
    opusSawWindows: window.__calls.some(c => c.full.includes('best windows for a ~23 s edit')),
    camera: s.project.camera,
    parts: window.__parts || [],
    reviews: window.__reviews || [],
    filledNotes: window.__filledNotes || 0,
    critics: window.__critics || [],
    notes: s.rounds.map(r => `R${r.n}: ${(r.notes || []).map(n => `${n.id}[${n.from}] ops=${n.ops || 0} ${n.status || '-'}`).join('; ')} self=${r.selfScores ? Object.values(r.selfScores).join('/') : '-'} follow=${r.critique?.followUp ? r.critique.followUp.map(f => `${f.id}:${f.status}`).join(',') : '-'} prev=${r.critique?.prevScore ?? '-'}`),
    looks: s.project.clips.filter(c => c.preset).map(c => `${c.id}:${c.preset}:${c.track}${c.span ? ':' + c.span : ''}`),
    tracks: s.project.tracks.map(t => `${t.id}:${t.kind}${t.role ? ':' + t.role : ''}${t.main ? ':main' : ''}`),
    knowledge: { exemplars: window.__calls.some(c => c.full.includes('WORKED EXAMPLES')), cookbook: window.__calls.some(c => c.full.includes('PLAYBOOK: THE APPROVED SET PIECES')), canon: window.__calls.some(c => c.full.includes('HOW THE EDIT WILL BE JUDGED')), fxCatalog: window.__calls.some(c => c.full.includes('LOOKS AND THE EFFECT LIBRARY')), maxChars: Math.max(...window.__calls.map(c => c.full.length)) },
  };
});
await page.click('.rp-tabs button:has-text("Opus")').catch(() => {});
await page.waitForTimeout(500);
await shot('07g-rounds');
writeFileSync(join(OUT, 'prompt-plan.txt'), await page.evaluate(() => window.__calls.find(c => !c.full.includes('casting') && !c.full.includes('You are the critic'))?.full || ''));
writeFileSync(join(OUT, 'prompt-critic.txt'), await page.evaluate(() => window.__calls.find(c => c.full.includes('You are the critic'))?.full || ''));
writeFileSync(join(OUT, 'prompt-round2.txt'), await page.evaluate(() => window.__calls.find(c => c.full.includes('ROUND 2 INSTRUCTIONS'))?.full || ''));
report.checks = await page.evaluate(() => window.__voidfx.store.state.checks.map(c => `${c.status} ${c.label}: ${c.detail}`));

// editor frames at signature transitions
const tAt = await page.evaluate(() => Object.fromEntries(window.__voidfx.store.state.project.clips.filter(c => c.transition).map(c => [c.transition.type, c.start])));
report.transitionTimes = tAt;
for (const [name, dt] of [['logo', 0.05], ['ink', 0.1], ['blink', 0.12], ['slash', 0.06]]) {
  if (tAt[name] === undefined) continue;
  await page.evaluate(t => { window.__voidfx.store.set({ selection: [] }); window.__voidfx.player.seek(t); }, tAt[name] + dt);
  await page.waitForTimeout(900);
  await shot(`07-tr-${name}`);
}
await page.click('.rail-b:has-text("Transitions")');
await page.waitForTimeout(1500);
await shot('08-transitions-panel');
await page.click('.rail-b:has-text("Text")');
await page.waitForTimeout(1200);
await shot('09-text-panel');
await page.click('.rail-b:has-text("Looks")');
await page.waitForTimeout(2500);
await shot('09b-looks-panel');
await page.click('.rail-b:has-text("Effects")');
await page.waitForTimeout(3000);
await shot('09c-effects-panel');
const lookId = await page.evaluate(() => window.__voidfx.store.state.project.clips.find(c => c.preset === 'noir_red')?.id);
if (lookId) { await page.evaluate(id => window.__voidfx.store.set({ selection: [id], rightTab: 'inspector' }), lookId); await page.waitForTimeout(600); await shot('09d-look-inspector'); }
await page.click('.rp-tabs button:has-text("Checks")');
await page.waitForTimeout(800);
await shot('10-checks');
await page.keyboard.press('Home');
await page.keyboard.press('Space');
await page.waitForTimeout(1500);
report.playback = await page.evaluate(() => ({ time: window.__voidfx.store.state.time, playing: window.__voidfx.store.state.playing }));
await page.keyboard.press('Space');

// ---- export (mastered) ----
await page.click('.top .btn-primary');
await page.click('.modal .seg button:has-text("720p")');
await page.click('.modal .btn-primary');
await page.waitForSelector('.exp-video, .modal .note.bad', { timeout: 900000 });
const expErr = await page.evaluate(() => document.querySelector('.modal .note.bad')?.textContent || null);
if (expErr) { console.log(JSON.stringify({ exportError: expErr, director: report.director, errors }, null, 1)); await shot('11-export-error'); process.exit(2); }
report.exportInfo = await page.evaluate(() => [...document.querySelectorAll('.modal .exp-sum dd, .modal .note')].map(e => e.textContent));
await shot('11-export');
await page.click('.modal .btn-primary');
await page.waitForFunction(() => window.__saved.length > 0, null, { timeout: 60000 });
const saved = await page.evaluate(() => window.__saved[0]);
writeFileSync(join(OUT, 'export.mp4'), Buffer.from(saved.b64, 'base64'));
report.saved = { filename: saved.filename, size: saved.size };
await page.keyboard.press('Escape');
await page.evaluate(() => window.__voidfx.store.set({ exportOpen: false }));

// ---- persistence: reload, reopen the project ----
const before = await page.evaluate(() => ({ clips: window.__voidfx.store.state.project.clips.length, id: window.__voidfx.store.state.projectId }));
await page.evaluate(() => window.__voidfx.store.flushSave());
await page.waitForTimeout(800);
await page.reload();
await page.waitForSelector('.home');
await page.click('.home-link:has-text("Projects")');
await page.waitForSelector('.pcard');
await shot('12-projects');
await page.click(`.pcard:has-text("Dexter") .pcard-thumb`);
await page.waitForSelector('.app');
await page.waitForFunction(() => { const s = window.__voidfx.store.state; return s.mediaOrder.length && s.mediaOrder.every(id => ['ready', 'error'].includes(s.media[id].status)); }, null, { timeout: 120000 });
report.reopened = await page.evaluate(b => {
  const s = window.__voidfx.store.state;
  return { sameProject: s.projectId === b.id, clips: s.project.clips.length, clipsBefore: b.clips, media: s.mediaOrder.map(id => `${id}:${s.media[id].status}`) };
}, before);
await page.waitForTimeout(1200);
await shot('13-reopened');
report.errors = errors;
console.log(JSON.stringify(report, null, 1));
await browser.close();
server.close();
