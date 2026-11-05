import { render } from 'preact';
import { initDirector } from './ai/director';
import { store } from './state/store';
import { player } from './engine/player';
import { runtime } from './media/library';
import { App } from './ui/App';
import { initDownloads } from './ui/save';

// restore the last session's project (media comes back offline until re-linked)
store.load();

const root = document.getElementById('app')!;
render(<App />, root);

void initDirector();
void initDownloads();

// test hook for the automated smoke test (harmless in production)
(window as any).__voidfx = { store, player, runtime };
