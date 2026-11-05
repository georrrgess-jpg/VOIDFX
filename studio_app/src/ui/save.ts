// Saving files: through the artifact `downloads` capability inside claude.ai, or a plain download
// link when the studio runs as a standalone page.
import { store } from '../state/store';

let downloads: any = undefined;

export async function initDownloads() {
  try {
    const w = window as any;
    downloads = w.claude?.use ? await w.claude.use('downloads') : null;
  } catch {
    downloads = null;
  }
}

const MSG: Record<string, string> = {
  declined: 'Save cancelled.',
  rate_limited: 'A save prompt is already open. Try again in a moment.',
  rejected_extension: 'This file type cannot be saved here.',
  too_large: 'The file is too large for this app. Export at a lower resolution or quality.',
};

export async function saveFile(filename: string, data: Blob | string) {
  if (downloads) {
    try {
      await downloads.save({ filename, data });
      store.toast(`Saved ${filename}`, 'ok');
    } catch (e: any) {
      const code = e?.code;
      store.toast(MSG[code] || 'Could not save the file here.', code === 'declined' ? 'info' : 'error');
    }
    return;
  }
  if ((window as any).claude) {
    store.toast('Saving is not available in this view.', 'error');
    return;
  }
  // standalone page: an ordinary download link works
  const blob = typeof data === 'string' ? new Blob([data], { type: 'application/json' }) : data;
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 4000);
}
