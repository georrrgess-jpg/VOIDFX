import { render } from 'preact';
import { initDirector } from './ai/director';
import { loadJobs } from './ai/jobs';
import { loadLogo } from './engine/logo';
import { player } from './engine/player';
import { runtime } from './media/library';
import { loadKnowledge } from './state/catalog';
import { migrateLegacy, openProject } from './state/projects';
import { applyOps } from './state/ops';
import { compileError, customIssues } from './engine/custom';
import { FX_PRESETS } from './engine/fxlibrary';
import { FX_LIBRARY, fxCode, fxParams } from './engine/fxlib';
import { renderStills } from './engine/exporter';
import { requestPersistence } from './state/storage';
import { store } from './state/store';
import { App } from './ui/App';
import { initDownloads } from './ui/save';

render(<App />, document.getElementById('app')!);

void loadLogo();
void initDirector();
void initDownloads();
void (async () => {
  await migrateLegacy();
  await loadKnowledge();
  await loadJobs();
  store.set(s => ({ catalogRev: s.catalogRev + 1 }));
  void requestPersistence();
})();

// keep the open project saved when the page is hidden or closed
document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') store.flushSave(); });
window.addEventListener('pagehide', () => store.flushSave());

// test hook for the automated smoke test (harmless in production)
(window as any).__voidfx = { store, player, runtime, open: openProject, applyOps, customIssues, compileError, FX_PRESETS, FX_LIBRARY, fxCode, fxParams, renderStills };
