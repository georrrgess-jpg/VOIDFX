import { useEffect, useState } from 'preact/hooks';
import { EFFORTS } from '../../ai/director';
import { blankPreset, BUILTIN_PRESETS, deletePreset, listPresets, listStandards, Preset, savePreset, Standard } from '../../state/catalog';
import { Effort, store } from '../../state/store';
import { ASPECTS } from '../../state/types';
import { Icon, Seg, Toggle } from '../controls';
import { SectionHead, TiltCard, useCatalog, useConfirm } from './common';

export function PresetsSection() {
  const [presets] = useCatalog<Preset[]>(listPresets, []);
  const [standards] = useCatalog<Standard[]>(listStandards, []);
  const [sel, setSel] = useState<string | null>(null);
  const [draft, setDraft] = useState<Preset | null>(null);
  const [confirm, setConfirm] = useConfirm();
  useEffect(() => { if (!sel && presets.length) setSel(presets[0].id); }, [presets.length]);
  useEffect(() => { const p = presets.find(x => x.id === sel); setDraft(p ? { ...p } : null); }, [sel, presets]);
  const set = (patch: Partial<Preset>) => setDraft(d => (d ? { ...d, ...patch } : d));
  const dirty = draft && JSON.stringify(draft) !== JSON.stringify(presets.find(x => x.id === draft.id));
  const save = async () => { if (draft) { await savePreset(draft); store.toast(`Saved preset “${draft.name}”`, 'ok'); } };
  const add = async () => { const p = blankPreset(); await savePreset(p); setSel(p.id); };
  const dup = async () => { if (!draft) return; const p = { ...draft, id: blankPreset().id, name: `${draft.name} (copy)`, builtIn: false }; await savePreset(p); setSel(p.id); };
  const isBuilt = !!draft && BUILTIN_PRESETS.some(b => b.id === draft.id);
  return (
    <div class="hs">
      <SectionHead eyebrow="Presets" title="Standing briefs" text="A preset is the pre-established prompt for an AI edit: its brief, format, effort, standards and the database tags it draws from. Each new edit adds its own notes on top."
        right={<button type="button" class="cta cta-violet" onClick={() => void add()}>{Icon.plus}<span>New preset</span></button>} />
      <div class="split">
        <div class="plist">
          {presets.map((p, i) => (
            <TiltCard class={`plist-i${p.id === sel ? ' is-on' : ''}`} i={i} onClick={() => setSel(p.id)} style={{ '--c': p.accent }} label={p.name}>
              <span class="preset-dot" aria-hidden="true" />
              <span class="plist-n">{p.name}{p.builtIn ? <em> built in</em> : null}</span>
              <span class="plist-d">{p.description || 'No description yet'}</span>
            </TiltCard>
          ))}
        </div>
        {draft && (
          <div class="glass peditor" style={{ '--c': draft.accent } as any}>
            <div class="fld fld-wide"><label class="fld-l" for="pe-name">Name</label><input id="pe-name" type="text" value={draft.name} onInput={e => set({ name: (e.target as HTMLInputElement).value })} /></div>
            <div class="fld fld-wide"><label class="fld-l" for="pe-desc">Description</label><input id="pe-desc" type="text" value={draft.description} onInput={e => set({ description: (e.target as HTMLInputElement).value })} /></div>
            <label class="fld-l" for="pe-prompt">Prompt (sent with every edit made from this preset)</label>
            <textarea id="pe-prompt" class="ta big" rows={8} value={draft.prompt} onInput={e => set({ prompt: (e.target as HTMLTextAreaElement).value })} placeholder="The standing brief: concept rules, structure, look, what to always do." />
            <Toggle id="pe-house" label="Include the voidfx house rules and benchmarks" checked={draft.houseRules} onChange={v => set({ houseRules: v })} />
            <div class="fld fld-wide"><span class="fld-l">Effort</span><Seg value={draft.effort} onChange={(v: Effort) => set({ effort: v })} options={(Object.keys(EFFORTS) as Effort[]).map(k => ({ value: k, label: EFFORTS[k].label }))} /></div>
            <div class="fld fld-wide"><span class="fld-l">Aspect</span><Seg value={draft.aspect} onChange={v => set({ aspect: v })} options={Object.keys(ASPECTS).map(a => ({ value: a, label: a }))} /></div>
            <div class="fld fld-wide"><span class="fld-l">Frame rate</span><Seg value={draft.fps} onChange={v => set({ fps: v })} options={[24, 30, 60].map(v => ({ value: v, label: String(v) }))} /></div>
            <div class="fld fld-wide"><span class="fld-l">Length</span>
              <span class="row"><input class="num" type="number" min={3} max={180} value={draft.duration[0]} aria-label="Minimum length" onInput={e => set({ duration: [+(e.target as HTMLInputElement).value || 1, draft.duration[1]] })} /> to <input class="num" type="number" min={3} max={180} value={draft.duration[1]} aria-label="Maximum length" onInput={e => set({ duration: [draft.duration[0], +(e.target as HTMLInputElement).value || 1] })} /> seconds</span>
            </div>
            <div class="fld fld-wide"><label class="fld-l" for="pe-tags">Database tags</label><input id="pe-tags" type="text" value={draft.libraryTags.join(', ')} placeholder="e.g. dexter, s4" onInput={e => set({ libraryTags: (e.target as HTMLInputElement).value.split(',').map(t => t.trim().toLowerCase()).filter(Boolean) })} /></div>
            <div class="fld fld-wide"><label class="fld-l" for="pe-acc">Colour</label><input id="pe-acc" type="color" value={draft.accent} onInput={e => set({ accent: (e.target as HTMLInputElement).value })} /></div>
            <span class="fld-l">Standards Opus is shown</span>
            <div class="chips-row">
              {standards.map(s => {
                const on = draft.standards.includes(s.id);
                return <button type="button" class={`chipbtn${on ? ' is-on' : ''}`} aria-pressed={on} onClick={() => set({ standards: on ? draft.standards.filter(x => x !== s.id) : [...draft.standards, s.id] })}>{s.name}</button>;
              })}
            </div>
            <div class="row-end">
              {!isBuilt && (confirm === draft.id
                ? <button type="button" class="cta cta-danger" onClick={() => { setConfirm(null); void deletePreset(draft.id); setSel(null); }}>Confirm delete</button>
                : <button type="button" class="cta cta-ghost" onClick={() => setConfirm(draft.id)}>Delete</button>)}
              {isBuilt && dirty === false && presets.find(x => x.id === draft.id)?.updated ? <button type="button" class="cta cta-ghost" onClick={() => void deletePreset(draft.id)}>Restore default</button> : null}
              <button type="button" class="cta cta-ghost" onClick={() => void dup()}>Duplicate</button>
              <button type="button" class="cta cta-violet" disabled={!dirty} onClick={() => void save()}>Save preset</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
