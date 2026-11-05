import { render } from 'preact';
import { initDirector } from './ai/director';
import { loadLogo } from './engine/logo';
import { player } from './engine/player';
import { runtime } from './media/library';
import { loadKnowledge } from './state/catalog';
import { migrateLegacy } from './state/projects';
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
  store.set(s => ({ catalogRev: s.catalogRev + 1 }));
  void requestPersistence();
})();

// keep the open project saved when the page is hidden or closed
document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') store.flushSave(); });
window.addEventListener('pagehide', () => store.flushSave());

// test hook for the automated smoke test (harmless in production)
(window as any).__voidfx = { store, player, runtime };
