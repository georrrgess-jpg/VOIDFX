// End-to-end smoke test in headless Chromium.
//   node test/smoke.mjs            (after `node build.mjs`; test media in test/media, see test/make_media.sh)
// Stubs the claude.ai runtime: `sample` replays scripted Opus replies and records what was sent,
// `downloads.save` hands the exported file back to this script. Writes screenshots and the exported
// MP4 to test/out/ and prints a JSON report.
import { createRequire } from 'node:module';
import http from 'node:http';
import { readFileSync, writeFileSync, mkdirSync, existsSync, statSync } from 'node:fs';
import { join, extname, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const OUT = join(ROOT, 'test', 'out');
mkdirSync(OUT, { recursive: true });

const types = { '.html': 'text/html', '.mp4': 'video/mp4', '.wav': 'audio/wav', '.png': 'image/png', '.js': 'text/javascript' };
const server = http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  const file = url === '/' ? join(ROOT, 'dist', 'index.html') : join(ROOT, url);
  if (!file.startsWith(ROOT) || !existsSync(file) || statSync(file).isDirectory()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'content-type': types[extname(file)] || 'application/octet-stream' });
  res.end(readFileSync(file));
});
await new Promise(r => server.listen(8777, r));

const PLAN = {
  message: 'Scripted test plan.',
  ops: [
    { op: 'clear' },
    { op: 'add', id: 'c1', media: 'm1', track: 'V1', in: 0.5, dur: 2.0, volume: 0.3 },
    { op: 'add', id: 'c2', media: 'm2', track: 'V1', in: 1.0, dur: 1.6, transition: { type: 'whip_left', dur: 0.4 }, kf: { scale: [[0, 1], [1.6, 1.3]] } },
    { op: 'add', id: 'c3', media: 'm3', track: 'V1', in: 0, dur: 1.5, speed: 2, transition: { type: 'crossfade', dur: 0.5 } },
    { op: 'add', id: 'c4', media: 'm5', track: 'V1', dur: 1.2, transition: { type: 'iris', dur: 0.4 }, color: { saturation: 0.5, vignette: 0.4 } },
    { op: 'add', id: 'a1', media: 'm4', track: 'A1', start: 0, in: 0, dur: 6.3, fadeOut: 0.6 },
    { op: 'text', id: 't1', track: 'T1', start: 0.2, dur: 2.2, text: 'VOIDFX STUDIO\nsmoke test', style: { size: 0.06, stroke: 0.08, weight: 900 }, anim: { in: 'words', inDur: 0.8, out: 'fade' } },
    { op: 'bogus' },
  ],
};
const REVIEW = { message: 'Reviewed: tightened nothing.', ops: [] };

const browser = await chromium.launch({ args: ['--autoplay-policy=no-user-gesture-required'] });
const page = await browser.newPage({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 1 });
const errors = [];
page.on('pageerror', e => errors.push('pageerror: ' + e.message));
page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
await page.addInitScript(([plan, review]) => {
  window.__calls = [];
  window.__saved = [];
  window.__replies = [JSON.stringify(plan), JSON.stringify(review)];
  const toB64 = async blob => {
    const buf = new Uint8Array(await blob.arrayBuffer());
    let s = '';
    for (let i = 0; i < buf.length; i += 0x8000) s += String.fromCharCode.apply(null, buf.subarray(i, i + 0x8000));
    return btoa(s);
  };
  window.claude = {
    use: async name => {
      if (name === 'sample') {
        const f = async (input, opts = {}) => {
          const turns = typeof input === 'string' ? [{ role: 'user', content: input }] : input;
          window.__calls.push({ roles: turns.map(t => t.role), full: turns.map(t => t.content).join('\n\n=====\n\n'), images: (opts.images || []).length, imageBytes: (opts.images || []).map(b => b.size), effort: opts.effort, model: opts.model, modelTier: opts.modelTier, cache: opts.cache });
          window.__lastImages = opts.images || [];
          await new Promise(r => setTimeout(r, 300));
          const reply = window.__replies.shift() || '{"message":"ok","ops":[]}';
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
}, [PLAN, REVIEW]);

const report = {};
await page.goto('http://localhost:8777/');
await page.waitForSelector('.app');
await page.screenshot({ path: join(OUT, '01-empty.png') });

// import media through the library's file input
const files = ['portrait.mp4', 'landscape.mp4', 'rotated.mp4', 'music.wav', 'still.png'].map(f => join(ROOT, 'test', 'media', f));
await page.setInputFiles('.lp input[type=file]', files);
await page.waitForFunction(() => {
  const s = window.__voidfx.store.state;
  return s.mediaOrder.length === 5 && s.mediaOrder.every(id => s.media[id].status === 'ready' && ['done', 'none', 'error'].includes(s.media[id].analysisState));
}, null, { timeout: 120000 });
report.media = await page.evaluate(() => {
  const s = window.__voidfx.store.state;
  return s.mediaOrder.map(id => {
    const m = s.media[id];
    const a = m.analysis;
    return { id, name: m.name, kind: m.kind, dur: +m.duration.toFixed(3), w: m.width, h: m.height, rot: m.rotation, fps: m.fps, audio: m.hasAudio, analysis: m.analysisState, bpm: a?.bpm ?? null, beats: a?.beats?.length ?? 0, firstBeats: a?.beats?.slice(0, 6), down: a?.downbeats?.slice(0, 4), rises: a?.rises, quiet: a?.quiet?.length ?? 0 };
  });
});
await page.waitForTimeout(800);
await page.screenshot({ path: join(OUT, '02-library.png') });

// Opus Director, scripted
await page.click('#brief');
await page.keyboard.type('Smoke-test edit: four shots, a title, music under it.');
await page.click('.dir-actions .btn-opus');
await page.waitForFunction(() => !window.__voidfx.store.state.director.running && window.__voidfx.store.state.director.messages.some(m => m.role !== 'user'), null, { timeout: 120000 });
report.director = await page.evaluate(() => {
  const s = window.__voidfx.store.state;
  const calls = window.__calls.map(c => ({ roles: c.roles, images: c.images, imageKB: c.imageBytes.map(b => Math.round(b / 1024)), effort: c.effort, model: c.model, modelTier: c.modelTier, cache: c.cache, chars: c.full.length, hasMedia: c.full.includes('MEDIA'), hasBeats: c.full.includes('beats:'), hasTimeline: c.full.includes('CURRENT TIMELINE') }));
  return {
    calls,
    messages: s.director.messages.map(m => ({ role: m.role, text: m.text.slice(0, 120), applied: m.applied, issues: m.issues })),
    steps: s.director.steps.map(x => `${x.id}:${x.state}:${x.detail || ''}`),
    clips: s.project.clips.map(c => ({ id: c.id, track: c.track, start: c.start, dur: c.dur, in: c.in, speed: c.speed, tr: c.transition?.type })),
  };
});
writeFileSync(join(OUT, 'prompt-1.txt'), await page.evaluate(() => window.__calls[0]?.full || ''));
// save the contact sheets that were sent
const sheets = await page.evaluate(async () => {
  const out = [];
  for (const b of window.__lastImages || []) {
    const buf = new Uint8Array(await b.arrayBuffer());
    let s = '';
    for (let i = 0; i < buf.length; i += 0x8000) s += String.fromCharCode.apply(null, buf.subarray(i, i + 0x8000));
    out.push(btoa(s));
  }
  return out;
});
sheets.forEach((b, i) => writeFileSync(join(OUT, `review-sheet-${i + 1}.jpg`), Buffer.from(b, 'base64')));

// preview: seek and screenshot mid-transition, then play for a moment
await page.evaluate(() => window.__voidfx.store.set({ zoom: 120 }));
for (const [t, name] of [[1.0, '03-t1.0'], [2.0, '04-whip'], [3.6, '05-crossfade'], [5.1, '06-iris']]) {
  await page.evaluate(t => { window.__voidfx.store.set({ selection: [] }); window.__voidfx.player.seek(t); }, t);
  await page.waitForTimeout(900);
  await page.screenshot({ path: join(OUT, `${name}.png`) });
}
await page.keyboard.press('Home');
await page.keyboard.press('Space');
await page.waitForTimeout(1500);
report.playback = await page.evaluate(() => ({ time: window.__voidfx.store.state.time, playing: window.__voidfx.store.state.playing }));
await page.keyboard.press('Space');

// select a clip and screenshot the inspector
await page.locator('[data-clip="t1"]').click();
await page.waitForTimeout(300);
await page.screenshot({ path: join(OUT, '07-inspector.png') });

// WebCodecs preview fallback: pretend the media element cannot play the landscape file (m2, clip c2)
await page.evaluate(() => { window.__voidfx.runtime.get('m2').elementOk = false; window.__voidfx.player.reset(); window.__voidfx.store.set({ selection: [] }); window.__voidfx.player.seek(2.9); });
await page.waitForTimeout(1500);
await page.screenshot({ path: join(OUT, '09-fallback-still.png') });
await page.evaluate(() => window.__voidfx.player.seek(2.1));
await page.keyboard.press('Space');
await page.waitForTimeout(900);
await page.screenshot({ path: join(OUT, '10-fallback-playing.png') });
report.fallbackPlayback = await page.evaluate(() => ({ time: window.__voidfx.store.state.time, playing: window.__voidfx.store.state.playing }));
await page.keyboard.press('Space');
await page.evaluate(() => { window.__voidfx.runtime.get('m2').elementOk = true; window.__voidfx.player.reset(); });

// export at 720p
await page.click('.top .btn-primary');
await page.click('.modal .seg button:has-text("720p")');
await page.click('.modal .btn-primary');
await page.waitForSelector('.exp-video', { timeout: 240000 });
await page.screenshot({ path: join(OUT, '08-export-done.png') });
report.exportInfo = await page.evaluate(() => [...document.querySelectorAll('.modal .exp-sum dd, .modal .note')].map(e => e.textContent));
await page.click('.modal .btn-primary');
await page.waitForFunction(() => window.__saved.length > 0, null, { timeout: 60000 });
const saved = await page.evaluate(() => window.__saved[0]);
writeFileSync(join(OUT, saved.filename.replace(/[^\w.\- ]/g, '_')), Buffer.from(saved.b64, 'base64'));
report.saved = { filename: saved.filename, size: saved.size };
report.errors = errors;
console.log(JSON.stringify(report, null, 1));
await browser.close();
server.close();
