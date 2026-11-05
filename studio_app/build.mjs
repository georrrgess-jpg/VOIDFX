// Builds the studio into one self-contained HTML file for the claude.ai artifact.
//   dist/voidfx-studio.html  page body as published (the artifact service adds the document skeleton)
//   dist/index.html          the same page wrapped in a full document, for local testing
import * as esbuild from 'esbuild';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';

const watch = process.argv.includes('--watch');
const FONTS = 'https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500&family=Unbounded:wght@600;800&family=Anton&family=Archivo+Black&family=Bebas+Neue&family=Montserrat:ital,wght@0,600;0,800;0,900;1,800&family=Oswald:wght@500;700&family=Permanent+Marker&family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=Poppins:wght@600;800&family=Space+Mono:wght@700&display=swap';

function page(js, css) {
  const safeJs = js.replace(/<\/script/gi, '<\\/script');
  return `<title>VOIDFX Studio</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="${FONTS}">
<style>${css}</style>
<div id="app"></div>
<script>${safeJs}</script>
`;
}

async function build() {
  const t0 = Date.now();
  const res = await esbuild.build({
    entryPoints: ['src/main.tsx'],
    bundle: true,
    minify: !watch,
    format: 'iife',
    target: ['chrome110', 'safari16.4', 'firefox115'],
    jsx: 'automatic',
    jsxImportSource: 'preact',
    write: false,
    legalComments: 'none',
    define: { 'process.env.NODE_ENV': '"production"' },
    logLevel: 'warning',
  });
  const js = res.outputFiles[0].text;
  const css = readFileSync('src/styles.css', 'utf8');
  mkdirSync('dist', { recursive: true });
  const body = page(js, css);
  writeFileSync('dist/voidfx-studio.html', body);
  writeFileSync('dist/index.html', `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"></head><body>${body}</body></html>`);
  console.log(`built dist/voidfx-studio.html ${(body.length / 1024).toFixed(0)} KiB in ${Date.now() - t0} ms`);
}

await build();
if (watch) {
  const { watch: fsWatch } = await import('node:fs');
  let timer = null;
  fsWatch('src', { recursive: true }, () => { clearTimeout(timer); timer = setTimeout(() => build().catch(e => console.error(e.message)), 120); });
}
