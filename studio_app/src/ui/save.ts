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
  rate_limited: 'A save prompt is already open. Close it or wait a moment, then press Save again.',
  rejected_extension: 'This file type cannot be saved here.',
  too_large: 'The file is too large for this app (the Android app saves up to 200 MB). Export at 720p or Standard quality, or save from claude.ai on a computer.',
  unavailable: 'Saving files is not available in this view. Open the studio in claude.ai on a computer and save from there.',
  bad_request: 'The save was refused as malformed. Rename the project to plain letters and numbers, then save again.',
};

export async function saveFile(filename: string, data: Blob | string) {
  if (downloads) {
    try {
      await downloads.save({ filename, data });
      store.toast(`Saved ${filename}`, 'ok');
      return true;
    } catch (e: any) {
      const code = e?.code;
      store.toast(MSG[code] || `Could not save the file${code ? ` (${code}${e?.message ? `: ${e.message}` : ''})` : e?.message ? `: ${e.message}` : ''}.`, code === 'declined' ? 'info' : 'error', 9000);
      return false;
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
