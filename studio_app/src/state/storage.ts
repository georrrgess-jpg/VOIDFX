// Local persistence in this browser (IndexedDB). Holds projects, media files (as Blobs, written to
// disk by the browser), derived data (waveforms, analysis, shot lists), the AI database, standards
// and presets. Large files are stored once and shared by every project that uses them.
const DB_NAME = 'voidfx-studio';
const DB_VERSION = 1;
export const STORES = ['kv', 'projects', 'blobs', 'derived', 'library', 'standards', 'presets'] as const;
export type StoreName = typeof STORES[number];

let dbp: Promise<IDBDatabase | null> | null = null;

function open(): Promise<IDBDatabase | null> {
  if (dbp) return dbp;
  dbp = new Promise(resolve => {
    try {
      const req = indexedDB.open(DB_NAME, DB_VERSION);
      req.onupgradeneeded = () => {
        const db = req.result;
        for (const s of STORES) if (!db.objectStoreNames.contains(s)) db.createObjectStore(s);
      };
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => resolve(null);
      req.onblocked = () => resolve(null);
    } catch {
      resolve(null);
    }
  });
  return dbp;
}

export async function storageAvailable(): Promise<boolean> {
  return !!(await open());
}

function tx<T>(store: StoreName, mode: IDBTransactionMode, fn: (s: IDBObjectStore) => IDBRequest<T>): Promise<T | undefined> {
  return open().then(db => new Promise<T | undefined>((resolve, reject) => {
    if (!db) { resolve(undefined); return; }
    try {
      const t = db.transaction(store, mode);
      const r = fn(t.objectStore(store));
      t.oncomplete = () => resolve(r.result);
      t.onerror = () => reject(t.error || r.error);
      t.onabort = () => reject(t.error || new Error('Storage write was aborted.'));
    } catch (e) {
      reject(e);
    }
  }));
}

export const idbGet = <T = any>(store: StoreName, key: string) => tx<T>(store, 'readonly', s => s.get(key) as IDBRequest<T>);
export const idbPut = (store: StoreName, key: string, value: unknown) => tx(store, 'readwrite', s => s.put(value, key));
export const idbDel = (store: StoreName, key: string) => tx(store, 'readwrite', s => s.delete(key));
export const idbKeys = async (store: StoreName) => ((await tx<IDBValidKey[]>(store, 'readonly', s => s.getAllKeys())) || []).map(String);
export async function idbAll<T = any>(store: StoreName): Promise<T[]> {
  return (await tx<T[]>(store, 'readonly', s => s.getAll() as IDBRequest<T[]>)) || [];
}

/** Stable key for a file, so the same file is stored once however often it is imported. */
export function blobKeyFor(f: { name: string; size: number; lastModified?: number }) {
  return `b:${f.size}:${f.lastModified || 0}:${f.name}`.slice(0, 400);
}

/** Store a file's bytes. Resolves the key, or null when the browser has no room. */
export async function saveBlob(file: Blob & { name?: string; lastModified?: number }, key?: string): Promise<string | null> {
  const k = key || blobKeyFor({ name: file.name || 'file', size: file.size, lastModified: file.lastModified });
  try {
    const have = await idbKeys('blobs').then(keys => keys.includes(k));
    if (!have) await idbPut('blobs', k, file);
    return k;
  } catch (e) {
    console.warn('could not store file', e);
    return null;
  }
}

export const getBlob = (key: string) => idbGet<Blob>('blobs', key);

/** Remove stored files that no project, database item or standard uses any more. */
/** Files a background job has stored but not yet listed in a project (never collected). */
export const pinnedBlobs = new Set<string>();

export async function collectGarbage() {
  const used = new Set<string>(pinnedBlobs);
  for (const p of await idbAll<any>('projects')) for (const m of p.media || []) if (m.blobId) used.add(m.blobId);
  for (const d of await idbAll<any>('library')) if (d.blobId) used.add(d.blobId);
  for (const s of await idbAll<any>('standards')) if (s.blobId) used.add(s.blobId);
  for (const k of await idbKeys('blobs')) if (!used.has(k)) { await idbDel('blobs', k); await idbDel('derived', k); }
}

export async function storageEstimate(): Promise<{ used: number; quota: number } | null> {
  try {
    const e = await navigator.storage?.estimate?.();
    return e ? { used: e.usage || 0, quota: e.quota || 0 } : null;
  } catch {
    return null;
  }
}

/** Ask the browser not to evict the studio's data under storage pressure. */
export async function requestPersistence() {
  try { await navigator.storage?.persist?.(); } catch { /* not offered here */ }
}
