import { useEffect, useRef, useState } from 'preact/hooks';
import { addToLibrary, deleteLibraryItem, LibraryItem, LibraryRole, listLibrary, updateLibraryItem } from '../../state/catalog';
import { requestPersistence, storageEstimate } from '../../state/storage';
import { fmtBytes } from '../../state/util';
import { Icon, Seg } from '../controls';
import { fmtDur, SectionHead, TiltCard, useCatalog, useConfirm } from './common';

const ROLES: { value: LibraryRole | ''; label: string }[] = [{ value: '', label: 'All' }, { value: 'pack', label: 'Scene packs' }, { value: 'clip', label: 'Clips' }, { value: 'music', label: 'Music' }, { value: 'other', label: 'Other' }];

export function LibrarySection() {
  const [items] = useCatalog<LibraryItem[]>(listLibrary, []);
  const [est, setEst] = useState<{ used: number; quota: number } | null>(null);
  const [role, setRole] = useState<LibraryRole | ''>('');
  const [tag, setTag] = useState('');
  const [defRole, setDefRole] = useState<LibraryRole | 'auto'>('auto');
  const [defTags, setDefTags] = useState('');
  const [drag, setDrag] = useState(false);
  const [confirm, setConfirm] = useConfirm();
  const fileRef = useRef<HTMLInputElement>(null);
  useEffect(() => { void storageEstimate().then(setEst); }, [items.length]);
  useEffect(() => {
    if (!items.some(i => i.state === 'processing')) return;
    const t = setInterval(() => void storageEstimate().then(setEst), 3000);
    return () => clearInterval(t);
  }, [items]);
  const tags = [...new Set(items.flatMap(i => i.tags))].sort();
  const shown = items.filter(i => (!role || i.role === role) && (!tag || i.tags.includes(tag)));
  const add = (files: FileList | File[]) => {
    void requestPersistence();
    void addToLibrary(files, { role: defRole === 'auto' ? undefined : defRole, tags: defTags.split(',').map(t => t.trim().toLowerCase()).filter(Boolean) });
  };
  return (
    <div class="hs">
      <SectionHead eyebrow="Database" title="Material for AI edits" text="Scene packs, clips and music Opus can draw from when it builds an edit. Files of any size are stored in this browser; packs are split into shots and music is analysed for tempo, beats and drops."
        right={est ? <div class="meter" title="Browser storage used by the studio"><span>{fmtBytes(est.used)} used</span><b class="meter-t"><i style={{ width: `${Math.max(1.5, Math.min(100, (est.used / Math.max(1, est.quota)) * 100)).toFixed(1)}%` }} /></b><span class="muted">of {fmtBytes(est.quota)} available to the studio</span></div> : null} />
      <div class={`ldrop glass${drag ? ' is-drag' : ''}`}
        onDragOver={e => { e.preventDefault(); e.stopPropagation(); setDrag(true); }} onDragLeave={() => setDrag(false)}
        onDrop={e => { e.preventDefault(); e.stopPropagation(); setDrag(false); if (e.dataTransfer?.files.length) add(e.dataTransfer.files); }}>
        <input ref={fileRef} type="file" multiple hidden accept="video/*,audio/*,image/*,.mov,.mkv,.m4a,.flac" onChange={e => { const f = (e.target as HTMLInputElement).files; if (f) add(f); (e.target as HTMLInputElement).value = ''; }} />
        <button type="button" class="cdrop-btn" onClick={() => fileRef.current?.click()}>{Icon.upload}<span>Add to the database</span></button>
        <div class="ldrop-opts">
          <div class="fld fld-wide"><span class="fld-l">Add as</span><Seg value={defRole} onChange={setDefRole} small options={[{ value: 'auto', label: 'Auto' }, { value: 'pack', label: 'Scene pack' }, { value: 'clip', label: 'Clip' }, { value: 'music', label: 'Music' }]} /></div>
          <div class="fld fld-wide"><label class="fld-l" for="lib-tags">Tags</label><input id="lib-tags" type="text" value={defTags} placeholder="e.g. dexter, s4, trinity" onInput={e => setDefTags((e.target as HTMLInputElement).value)} /></div>
        </div>
        <p class="muted">Drop files here. Names with Dexter or Flash words are tagged automatically.</p>
      </div>
      <div class="toolbar-row">
        <Seg value={role} onChange={setRole} small options={ROLES.map(r => ({ value: r.value, label: `${r.label}${r.value ? ` ${items.filter(i => i.role === r.value).length}` : ` ${items.length}`}` }))} />
        {tags.length > 0 && <div class="chips-row">{['', ...tags].map(t => <button type="button" class={`chipbtn${tag === t ? ' is-on' : ''}`} onClick={() => setTag(t)}>{t || 'All tags'}</button>)}</div>}
      </div>
      {!items.length && <div class="empty glass"><p class="empty-t">The database is empty</p><p>Add the scene packs and songs you edit with. Opus can then build edits from them without you attaching files each time.</p></div>}
      <div class="lgrid">
        {shown.map((it, i) => (
          <TiltCard class={`litem r-${it.role}`} i={i}>
            <div class="litem-img">
              {it.poster ? <img src={it.poster} alt="" /> : <span class="recent-ph">{it.kind === 'audio' ? Icon.vol : Icon.media}</span>}
              <span class="litem-role">{it.role}</span>
              {it.duration > 0 && <span class="recent-dur">{fmtDur(it.duration)}</span>}
              {it.state === 'processing' && <span class="litem-prog"><i style={{ width: `${Math.round((it.progress || 0) * 100)}%` }} /><em>{it.stage || 'Working'}…</em></span>}
            </div>
            <input class="litem-name" type="text" value={it.name} aria-label="Name" onChange={e => void updateLibraryItem(it.id, { name: (e.target as HTMLInputElement).value })} />
            <div class="litem-meta">
              {it.width ? `${it.width}×${it.height}` : it.kind}{it.fps ? ` · ${Math.round(it.fps)} fps` : ''}{it.shots ? ` · ${it.shots} shots` : ''}{it.bpm ? ` · ${Math.round(it.bpm)} BPM` : ''} · {fmtBytes(it.size)}
              {it.state === 'error' && <span class="bad"> · {it.stage || 'failed'}</span>}
            </div>
            <input class="litem-tags" type="text" value={it.tags.join(', ')} placeholder="tags" aria-label="Tags" onChange={e => void updateLibraryItem(it.id, { tags: (e.target as HTMLInputElement).value.split(',').map(t => t.trim().toLowerCase()).filter(Boolean) })} />
            <div class="litem-acts">
              <select aria-label="Role" value={it.role} onChange={e => void updateLibraryItem(it.id, { role: (e.target as HTMLSelectElement).value as LibraryRole })}>
                {ROLES.slice(1).map(r => <option value={r.value}>{r.label}</option>)}
              </select>
              {confirm === it.id
                ? <button type="button" class="chipbtn danger" onClick={() => { setConfirm(null); void deleteLibraryItem(it.id); }}>Confirm</button>
                : <button type="button" class="chipbtn" onClick={() => setConfirm(it.id)}>Delete</button>}
            </div>
          </TiltCard>
        ))}
      </div>
    </div>
  );
}
