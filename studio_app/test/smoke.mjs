// End-to-end test of the studio in headless Chromium (after `node build.mjs`; media from test/make_media.sh).
// Stubs the claude.ai runtime: `sample` answers like Opus would (casting, a plan built from the media
// it is shown, an approving review) and records what it was sent; `downloads.save` hands files back.
// Flow: main menu → database → standards → AI Edit (files + database) → editor → checks → export
// (mastered) → reload → reopen the project from Projects. Writes screenshots and the MP4 to test/out/.
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
  const TRANS = ['logo', 'ink', 'blink', 'slash', 'punch', 'light_leak', 'roll', 'shadow', 'warp', 'burn', 'whip_left'];
  function planFrom(text) {
    const media = [...text.matchAll(/^(m\d+) (video|audio|image) "([^"]+)" ([\d.]+s|still image)/gm)].map(m => ({ id: m[1], kind: m[2], dur: m[4] === 'still image' ? 3 : parseFloat(m[4]) }));
    const ops = [{ op: 'clear' }, { op: 'project', camera: { on: true, every: 'beat', punch: 0.055, kick: 1 } }];
    let t = 0, k = 0;
    const vis = media.filter(m => m.kind !== 'audio');
    // use every visual file twice so there are enough cuts to exercise the transitions
    for (let round = 0; round < 2; round++) for (const m of vis) {
      const dur = 1.6;
      const op = { op: 'add', id: `v${k}`, media: m.id, track: 'V1', in: m.kind === 'image' ? 0 : Math.min(Math.max(0, m.dur - dur - 0.6), round * 1.2 + 0.3), dur };
      if (k > 0) op.transition = { type: TRANS[(k - 1) % TRANS.length] };
      if (k === 1) op.ramp = { fast: 2, slow: 0.5 };
      ops.push(op); t += dur; k++;
    }
    const music = media.find(m => m.kind === 'audio');
    if (music) ops.push({ op: 'add', id: 'mus', media: music.id, track: 'A1', start: 0, in: 0, dur: Math.min(music.dur, t) });
    ops.push({ op: 'text', id: 'cap', track: 'T1', start: 0.3, dur: 2.4, text: 'COULD IT BE\n*HIM*', words: [0, 0.25, 0.5, 0.9], style: { font: 'Inter', weight: 900, uppercase: true, size: 0.046, lineScales: [1, 1.3], stroke: 0.07, shadow: 0.65, scrim: 0.35, emphColor: '#ff2b3a' }, anim: { in: 'words', out: 'fade' }, transform: { y: 0.25 } });
    ops.push({ op: 'text', id: 'hero', track: 'T1', start: 4.0, dur: 1.8, text: 'ALONG', style: { font: 'Inter', weight: 900, size: 0.085, uppercase: true, stroke: 0.06 }, anim: { in: 'letters', out: 'scatter', inDur: 0.8, outDur: 0.5 }, transform: { y: 0.27 } });
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
          window.__calls.push({ roles: turns.map(t => t.role), full, images: (opts.images || []).length, effort: opts.effort, model: opts.model });
          window.__lastImages = opts.images || [];
          await new Promise(r => setTimeout(r, 200));
          let reply;
          if (full.includes('You are casting material')) {
            const ids = [...full.matchAll(/^(lib\S+) /gm)].map(m => m[1]);
            reply = JSON.stringify({ items: ids.map(id => ({ id, why: 'test' })), message: 'Took the song and the landscape clip.' });
          } else if (full.includes('REVIEW 1 of')) {
            reply = JSON.stringify({ message: 'Reviewed: the checkpoint is clean enough; approved.', ops: [] });
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
await page.setInputFiles('.cdrop input[type=file]', [join(MEDIA, 'portrait.mp4'), join(MEDIA, 'rotated.mp4'), join(MEDIA, 'still.png')]);
await page.waitForTimeout(400);
await shot('06-create');
await page.click('.cgo .cta-opus');
await page.waitForSelector('.app', { timeout: 30000 });
await page.waitForFunction(() => { const d = window.__voidfx.store.state.director; return !d.running && d.messages.some(m => m.role === 'opus' || (m.role === 'note' && !m.text.startsWith('Material'))); }, null, { timeout: 240000 });
report.director = await page.evaluate(() => {
  const s = window.__voidfx.store.state;
  return {
    calls: window.__calls.map(c => ({ roles: c.roles.length, images: c.images, chars: c.full.length, house: c.full.includes('VOIDFX HOUSE RULES'), standards: c.full.includes('REFERENCE EDITS THE OWNER ADDED'), checkpoint: c.full.includes('AUTOMATED CHECKPOINT'), casting: c.full.includes('You are casting material') })),
    messages: s.director.messages.map(m => `${m.role}: ${m.text.slice(0, 90)}`),
    steps: s.director.steps.map(x => `${x.id}:${x.state}:${x.detail || ''}`),
    media: s.mediaOrder.map(id => `${id} ${s.media[id].kind} ${s.media[id].name} ${s.media[id].origin}`),
    format: `${s.project.width}x${s.project.height}@${s.project.fps}`,
    transitions: s.project.clips.filter(c => c.transition).map(c => c.transition.type),
    sfx: s.project.clips.filter(c => c.kind === 'sfx').length,
    ramp: s.project.clips.filter(c => c.kf?.speed?.length).map(c => `${c.id}:${c.kf.speed.length} keys`),
    camera: s.project.camera,
    checks: s.checks.map(c => `${c.status} ${c.label}: ${c.detail}`),
    seam: s.seam,
  };
});
writeFileSync(join(OUT, 'prompt-plan.txt'), await page.evaluate(() => window.__calls.find(c => !c.full.includes('casting'))?.full || ''));

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
await page.waitForSelector('.exp-video, .modal .note.bad', { timeout: 400000 });
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
await page.click('.pcard .pcard-open');
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
