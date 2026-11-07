// A real AI edit in headless Chromium, with every Opus call answered from outside: each `sample`
// request (its turns and attached images) is written to LIVE/req-N.md and LIVE/req-N-img-K.jpg, a
// line "REQUEST N ..." is printed, and the reply is read from LIVE/res-N.txt when it appears. An agent
// (or a person) answers the requests, so the studio's whole pipeline runs with real decisions:
// casting, contact sheets, direction, operations, reviews of rendered frames, the critic.
// The browser profile persists in LIVE/profile, so later modes continue the same project.
//   LIVE=dir MEDIA="a.mp4,b.wav" MODE=build   node test/live.mjs   build + critic (round 1)
//   LIVE=dir MODE=revise ROUND=2              node test/live.mjs   revise with every critic point, then the critic
//   LIVE=dir MODE=export                      node test/live.mjs   export the edit (720p) and a filmstrip
// Results: LIVE/round-N.json (timeline, notes, critique), LIVE/filmstrip-N.jpg, LIVE/log.jsonl (timings).
import { createRequire } from 'node:module';
import http from 'node:http';
import { readFileSync, writeFileSync, mkdirSync, existsSync, statSync, appendFileSync } from 'node:fs';
import { join, extname, dirname, basename } from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const LIVE = process.env.LIVE;
if (!LIVE) { console.error('set LIVE to a working directory'); process.exit(2); }
mkdirSync(LIVE, { recursive: true });
const MODE = process.env.MODE || 'build';
const MEDIA = (process.env.MEDIA || '').split(',').filter(Boolean);
const NAME = process.env.NAME || 'Live test edit';
const log = o => appendFileSync(join(LIVE, 'log.jsonl'), JSON.stringify({ at: new Date().toISOString(), ...o }) + '\n');

let seq = existsSync(join(LIVE, 'seq')) ? +readFileSync(join(LIVE, 'seq'), 'utf8') : 0;
const wrap = s => s.split('\n').flatMap(line => {
  if (line.length <= 1600) return [line];
  const out = [];
  for (let i = 0; i < line.length; i += 1600) out.push(line.slice(i, i + 1600));
  return out;
}).join('\n');

const types = { '.html': 'text/html', '.mp4': 'video/mp4', '.wav': 'audio/wav', '.png': 'image/png' };
const server = http.createServer(async (req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  if (req.method === 'POST' && url === '/bridge') {
    let body = '';
    for await (const chunk of req) body += chunk;
    const q = JSON.parse(body);
    const n = ++seq;
    writeFileSync(join(LIVE, 'seq'), String(seq));
    const imgs = q.images.map((d, k) => {
      const f = join(LIVE, `req-${n}-img-${k + 1}.jpg`);
      writeFileSync(f, Buffer.from(d.split(',')[1], 'base64'));
      return f;
    });
    const kind = /You are the critic/.test(q.turns[0].content) ? 'critic' : /You are casting material/.test(q.turns[0].content) ? 'cast'
      : (q.turns[q.turns.length - 1].content.match(/REVIEW \d OF \d|CALL 1 OF 2: THE CUT|CALL 2 OF 2: THE DESIGN|THIS CALL CARRIES OUT|NOTES WITH NO APPLIED OPERATIONS/) || ['plan'])[0];
    const md = [
      `# VOIDFX Studio request ${n} (${kind}; effort ${q.opts.effort || '-'})`,
      imgs.length ? `Attached images, in order:\n${imgs.map((f, k) => `${k + 1}. ${f}`).join('\n')}` : 'No images attached.',
      ...q.turns.map((t, k) => `\n=============== TURN ${k + 1} of ${q.turns.length} (${t.role}) ===============\n${wrap(t.content)}`),
      '\n=============== END OF REQUEST ===============',
    ].join('\n');
    writeFileSync(join(LIVE, `req-${n}.md`), md);
    const chars = q.turns.reduce((a, t) => a + t.content.length, 0);
    const t0 = Date.now();
    log({ ev: 'request', n, kind, effort: q.opts.effort, chars, images: imgs.length });
    console.log(`REQUEST ${n} kind=${kind} effort=${q.opts.effort} chars=${chars} images=${imgs.length} file=${join(LIVE, `req-${n}.md`)}`);
    const resFile = join(LIVE, `res-${n}.txt`);
    let closed = false;
    req.on('close', () => { closed = true; });
    while (!existsSync(resFile) && !closed) await new Promise(r => setTimeout(r, 1000));
    if (closed && !existsSync(resFile)) { log({ ev: 'aborted', n }); return; }
    await new Promise(r => setTimeout(r, 300));
    const text = readFileSync(resFile, 'utf8').trim();
    log({ ev: 'reply', n, kind, seconds: Math.round((Date.now() - t0) / 1000), replyChars: text.length });
    console.log(`REPLY ${n} after ${Math.round((Date.now() - t0) / 1000)} s (${text.length} chars)`);
    res.writeHead(200, { 'content-type': 'application/json' });
    res.end(JSON.stringify({ text }));
    return;
  }
  const file = url === '/' ? join(ROOT, 'dist', 'index.html') : url.startsWith('/media/') ? MEDIA.find(m => basename(m) === url.slice(7)) : join(ROOT, url);
  if (!file || !existsSync(file) || statSync(file).isDirectory()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'content-type': types[extname(file)] || 'application/octet-stream' });
  res.end(readFileSync(file));
});
await new Promise(r => server.listen(8779, r));
server.requestTimeout = 0;
server.headersTimeout = 0;

const ctx = await chromium.launchPersistentContext(join(LIVE, 'profile'), { viewport: { width: 1600, height: 1000 }, args: ['--autoplay-policy=no-user-gesture-required'] });
const page = ctx.pages()[0] || await ctx.newPage();
page.on('pageerror', e => { console.log('PAGEERROR ' + e.message); log({ ev: 'pageerror', msg: e.message }); });
page.on('console', m => { if (m.type() === 'error' && !/favicon|fonts\.g/.test(m.text())) log({ ev: 'console', msg: m.text() }); });
await ctx.addInitScript(() => {
  window.__saved = [];
  const toB64 = async blob => {
    const buf = new Uint8Array(await blob.arrayBuffer());
    let s = '';
    for (let i = 0; i < buf.length; i += 0x8000) s += String.fromCharCode.apply(null, buf.subarray(i, i + 0x8000));
    return btoa(s);
  };
  const jpeg = async blob => {
    const bmp = await createImageBitmap(blob);
    const c = new OffscreenCanvas(bmp.width, bmp.height);
    c.getContext('2d').drawImage(bmp, 0, 0);
    const out = await c.convertToBlob({ type: 'image/jpeg', quality: 0.9 });
    return `data:image/jpeg;base64,${await toB64(out)}`;
  };
  window.claude = {
    use: async name => {
      if (name === 'sample') {
        const f = async (input, opts = {}) => {
          const turns = typeof input === 'string' ? [{ role: 'user', content: input }] : input;
          const images = await Promise.all((opts.images || []).map(jpeg));
          const ac = new AbortController();
          opts.signal?.addEventListener('abort', () => ac.abort());
          const r = await fetch('/bridge', { method: 'POST', body: JSON.stringify({ turns, images, opts: { effort: opts.effort, model: opts.model } }), signal: ac.signal });
          const { text } = await r.json();
          if (!text) throw { code: 'empty_completion', message: 'empty reply' };
          opts.onText?.({ text, delta: text });
          return { text, truncated: false, modelTierApplied: 'complex', modelApplied: opts.model };
        };
        f.limits = async () => ({ maxPromptBytes: 262144, images: { maxCount: 20, maxInputBytes: 20e6, mediaTypes: ['image/jpeg', 'image/png'] } });
        return f;
      }
      if (name === 'downloads') return { save: async ({ filename, data }) => { window.__saved.push({ filename, b64: await toB64(data) }); return { status: 'saved' }; } };
      return null;
    },
  };
});
await page.goto('http://localhost:8779/');
await page.waitForSelector('.home');
await page.waitForFunction(() => window.__voidfx?.store.state.director.available === 'yes', null, { timeout: 30000 });
await page.waitForTimeout(1500);

const projectId = async () => page.evaluate(async name => (await window.__voidfx.listProjects()).find(p => p.name === name)?.id, NAME);
// finished when nothing is queued or running and the critic has looked at the round (or a job failed)
const waitIdle = round => page.waitForFunction(round => {
  const j = window.__voidfx.store.state.jobs;
  const idle = j.length && j.every(x => ['done', 'error', 'stopped', 'interrupted'].includes(x.state));
  return idle && (j.some(x => x.kind === 'critique' && x.round >= round && x.state === 'done') || j.some(x => x.state === 'error'));
}, round, { timeout: 0, polling: 2000 });

async function saveRound(n) {
  const pid = await projectId();
  const data = await page.evaluate(async pid => {
    const v = window.__voidfx;
    const r = await v.getRecord(pid);
    return { project: r.project, rounds: (r.rounds || []).map(({ snapshot, ...x }) => x), jobs: v.store.state.jobs.filter(j => j.projectId === pid).map(j => ({ kind: j.kind, round: j.round, state: j.state, error: j.error, started: j.started, finished: j.finished, steps: j.steps })) };
  }, pid);
  writeFileSync(join(LIVE, `round-${n}.json`), JSON.stringify(data, null, 1));
  // a filmstrip of the edit, four frames a second, for looking at it
  await page.evaluate(pid => window.__voidfx.open(pid), pid);
  await page.waitForSelector('.app');
  await page.waitForFunction(() => { const s = window.__voidfx.store.state; return s.mediaOrder.length && s.mediaOrder.every(id => ['ready', 'error'].includes(s.media[id].status)); }, null, { timeout: 300000 });
  const sheets = await page.evaluate(async () => {
    const { store, renderStills } = window.__voidfx;
    const p = store.state.project;
    const dur = p.clips.reduce((a, c) => Math.max(a, c.start + c.dur), 0);
    const times = [];
    for (let t = 0; t < dur; t += 0.25) times.push(+t.toFixed(2));
    const stills = await renderStills(p, times, 320, undefined, store.state.media);
    const per = 40, cols = 10, w = stills[0].width, h = stills[0].height;
    const out = [];
    for (let s = 0; s < stills.length; s += per) {
      const part = stills.slice(s, s + per);
      const rows = Math.ceil(part.length / cols);
      const c = new OffscreenCanvas(cols * w, rows * (h + 18));
      const g = c.getContext('2d');
      g.fillStyle = '#111'; g.fillRect(0, 0, c.width, c.height);
      g.font = '14px monospace'; g.fillStyle = '#ffd23f';
      part.forEach((im, k) => { const x = (k % cols) * w, y = Math.floor(k / cols) * (h + 18); g.drawImage(im, x, y + 18); g.fillText(`${times[s + k].toFixed(2)}s`, x + 4, y + 14); });
      const b = await c.convertToBlob({ type: 'image/jpeg', quality: 0.85 });
      const buf = new Uint8Array(await b.arrayBuffer()); let str = ''; for (let i = 0; i < buf.length; i += 0x8000) str += String.fromCharCode.apply(null, buf.subarray(i, i + 0x8000));
      out.push(btoa(str));
    }
    return out;
  });
  sheets.forEach((b, k) => writeFileSync(join(LIVE, `filmstrip-${n}-${k + 1}.jpg`), Buffer.from(b, 'base64')));
  await page.evaluate(() => window.__voidfx.store.flushSave());
  console.log(`SAVED round ${n}: ${join(LIVE, `round-${n}.json`)}, ${sheets.length} filmstrip sheets`);
}

if (MODE === 'build') {
  const presetId = await page.evaluate(async () => {
    const v = window.__voidfx;
    const p = {
      ...v.blankPreset(), name: 'VOIDFX · Noir (Detour test)', effort: 'extra', fps: 60, duration: [20, 26], houseRules: true,
      description: 'A noir character edit of Al Roberts from Detour (1945).',
      prompt: 'Make a character edit of Al Roberts, the doomed pianist of Detour (1945), at the voidfx standard. His world: the road, hitchhiking, the night drive, the dead man\'s car and name he takes, Vera who blackmails him, the phone cord, the fog, the piano, the diner, fate that keeps detouring him. Dark, tense, stylish; the black-and-white footage is the material, so design the look around it. Treat the scene pack like the owner\'s Dexter and Flash packs: the same house rules, set pieces from his world, the same standards.',
    };
    await v.savePreset(p);
    return p.id;
  });
  const jobId = await page.evaluate(async ({ presetId, media, name }) => {
    const files = await Promise.all(media.map(async n => { const b = await (await fetch(`/media/${n}`)).blob(); return new File([b], n, { type: b.type }); }));
    const j = await window.__voidfx.startAiEdit({ name, presetId, effort: 'extra', files, follow: { critic: true, autoRounds: 0 },
      request: { notes: 'Fate keeps detouring him: build the edit around that. Open strong on his face. The drop should hit like the moment everything goes wrong. Give it a bold look and real set pieces, not just cuts.', lyrics: '', library: { mode: 'none', ids: [] } } });
    return j?.id;
  }, { presetId, media: MEDIA.map(m => basename(m)), name: NAME });
  log({ ev: 'start', mode: MODE, jobId });
  console.log(`STARTED build ${jobId}`);
  await waitIdle(1);
  await saveRound(1);
} else if (MODE === 'revise') {
  const round = +(process.env.ROUND || 2);
  const pid = await projectId();
  const jobId = await page.evaluate(async ({ pid, brief }) => {
    const v = window.__voidfx;
    const r = await v.getRecord(pid);
    const crit = r.rounds[r.rounds.length - 1].critique;
    const lines = crit.issues.map(i => `[${i.severity}${i.at !== undefined ? ` @ ${i.at.toFixed(2)}s` : ''}, ${i.area}] ${i.problem}${i.fix ? ` Fix: ${i.fix}` : ''}`);
    const j = await v.enqueue({ kind: 'revise', projectId: pid, effort: 'extra', presetId: r.presetId, brief, fromCritic: [`The critic's write-up: ${crit.brief}`, ...lines], follow: { critic: true, autoRounds: 0 } });
    return j?.id;
  }, { pid, brief: process.env.BRIEF || '' });
  log({ ev: 'start', mode: MODE, jobId, round });
  console.log(`STARTED revise ${jobId}`);
  await waitIdle(round);
  await saveRound(round);
} else if (MODE === 'export') {
  const pid = await projectId();
  await page.evaluate(pid => window.__voidfx.open(pid), pid);
  await page.waitForSelector('.app');
  await page.waitForFunction(() => { const s = window.__voidfx.store.state; return s.mediaOrder.length && s.mediaOrder.every(id => ['ready', 'error'].includes(s.media[id].status)); }, null, { timeout: 300000 });
  await page.click('.top .btn-primary');
  await page.click('.modal .seg button:has-text("720p")');
  const t0 = Date.now();
  await page.click('.modal .btn-primary');
  await page.waitForSelector('.exp-video, .modal .note.bad', { timeout: 0 });
  await page.click('.modal .btn-primary').catch(() => {});
  await page.waitForFunction(() => window.__saved.length > 0, null, { timeout: 120000 });
  const saved = await page.evaluate(() => window.__saved[window.__saved.length - 1]);
  writeFileSync(join(LIVE, `export.mp4`), Buffer.from(saved.b64, 'base64'));
  console.log(`EXPORTED in ${Math.round((Date.now() - t0) / 1000)} s: ${join(LIVE, 'export.mp4')}`);
}
console.log('FINISHED');
await ctx.close();
server.close();
