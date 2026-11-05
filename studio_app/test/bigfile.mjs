// Large-file check: import a multi-GB file, measure readiness and memory, export a cut from its middle.
//   node test/bigfile.mjs [path-to-big-file]
import { createRequire } from 'node:module';
import http from 'node:http';
import { readFileSync, writeFileSync, mkdirSync, existsSync, statSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const BIG = process.argv[2] || join(ROOT, 'test', 'media', 'big.mp4');
const OUT = join(ROOT, 'test', 'out');
mkdirSync(OUT, { recursive: true });
const server = http.createServer((req, res) => {
  const f = req.url === '/' ? join(ROOT, 'dist', 'index.html') : null;
  if (!f || !existsSync(f)) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'content-type': 'text/html' }); res.end(readFileSync(f));
});
await new Promise(r => server.listen(8778, r));
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1500, height: 950 } });
const errors = [];
page.on('pageerror', e => errors.push(e.message));
page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
await page.addInitScript(() => {
  window.__saved = [];
  window.claude = { use: async n => n === 'downloads' ? { save: async ({ filename, data }) => { const b = new Uint8Array(await data.arrayBuffer()); let s = ''; for (let i = 0; i < b.length; i += 0x8000) s += String.fromCharCode.apply(null, b.subarray(i, i + 0x8000)); window.__saved.push({ filename, b64: btoa(s) }); return { status: 'saved' }; } } : null };
});
const cdp = await page.context().newCDPSession(page);
await cdp.send('Performance.enable');
const heap = async () => { const m = (await cdp.send('Performance.getMetrics')).metrics; return Math.round(m.find(x => x.name === 'JSHeapUsedSize').value / 1048576); };
await page.goto('http://localhost:8778/');
await page.waitForSelector('.app');
const r = { fileGB: +(statSync(BIG).size / 1073741824).toFixed(2), heapStartMB: await heap() };
const t0 = Date.now();
await page.setInputFiles('.lp input[type=file]', BIG);
await page.waitForFunction(() => { const s = window.__voidfx.store.state; return s.mediaOrder.length && s.media[s.mediaOrder[0]].status === 'ready'; }, null, { timeout: 120000 });
r.readySec = (Date.now() - t0) / 1000;
await page.waitForFunction(() => { const s = window.__voidfx.store.state; const m = s.media[s.mediaOrder[0]]; return ['done', 'none', 'error'].includes(m.analysisState); }, null, { timeout: 300000 });
r.analysedSec = (Date.now() - t0) / 1000;
r.heapAfterImportMB = await heap();
r.media = await page.evaluate(() => { const s = window.__voidfx.store.state; const m = s.media[s.mediaOrder[0]]; return { dur: m.duration, w: m.width, h: m.height, fps: m.fps, analysis: m.analysisState }; });
// cut 2 s from the middle and export at 720p
await page.evaluate(() => {
  const { store } = window.__voidfx;
  const id = store.state.mediaOrder[0];
  store.commit(p => { p.clips.push({ id: 'c1', track: 'V1', kind: 'video', start: 0, dur: 2, media: id, in: 12, fit: 'cover' }); });
  window.__voidfx.player.seek(1);
});
await page.waitForTimeout(6000);
await page.screenshot({ path: join(OUT, 'big-preview.png') });
const t1 = Date.now();
await page.click('.top .btn-primary');
await page.click('.modal .seg button:has-text("720p")');
await page.click('.modal .btn-primary');
await page.waitForSelector('.exp-video', { timeout: 240000 });
r.exportSec = (Date.now() - t1) / 1000;
r.heapAfterExportMB = await heap();
await page.click('.modal .btn-primary');
await page.waitForFunction(() => window.__saved.length > 0, null, { timeout: 60000 });
const saved = await page.evaluate(() => window.__saved[0]);
writeFileSync(join(OUT, 'big-cut.mp4'), Buffer.from(saved.b64, 'base64'));
r.errors = errors;
console.log(JSON.stringify(r, null, 1));
await browser.close();
server.close();
