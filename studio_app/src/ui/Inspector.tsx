import { TRANSITION_LABELS } from '../engine/transitions';
import { store, useStore } from '../state/store';
import { AnimProp, ASPECTS, Clip, ColorAdjust, FONTS, MediaInfo, TEXT_ANIMS_IN, TEXT_ANIMS_OUT, TextAnimIn, TextAnimOut, TRANSITIONS, TransitionType } from '../state/types';
import { clamp, clipEnd, colorOf, propValue, textAnimOf, textStyleOf, trackClips } from '../state/util';
import { deleteSelected, jumpKeyframe, rampSelected, setAnimProp, setFxParam, toggleKeyframe, updateClip, wordsOnBeats } from './actions';
import { getFx, isColorParam } from '../engine/fxlib';
import { IN_LABEL, OUT_LABEL } from './LeftPanel';
import { STANDARD_CAPTION } from '../state/types';
import { SFX_INFO } from '../engine/sfx';
import { DEFAULT_CAMERA, SFX, SfxType } from '../state/types';
import { hasRamp } from '../state/util';
import { Btn, ColorField, Icon, Section, Seg, Select, Slider, Toggle } from './controls';
import { useEffect, useState } from 'preact/hooks';
import { compileError } from '../engine/custom';
import { BLEND_MODES, REVEALS_IN, REVEALS_OUT } from '../state/types';

const begin = () => store.beginGesture();
const end = () => store.endGesture();

export function Inspector() {
  const sel = useStore(s => s.selection);
  const project = useStore(s => s.project);
  const time = useStore(s => s.time);
  const media = useStore(s => s.media);
  if (sel.length > 1) {
    return (
      <div class="insp">
        <header class="insp-h"><h2>{sel.length} clips selected</h2></header>
        <p class="note">Drag them together on the timeline, or delete them.</p>
        <Btn kind="danger" onClick={deleteSelected}>{Icon.trash}<span>Delete {sel.length} clips</span></Btn>
      </div>
    );
  }
  const clip = sel.length ? project.clips.find(c => c.id === sel[0]) : undefined;
  if (!clip) return <ProjectProps />;
  const m = clip.media ? media[clip.media] : undefined;
  return <ClipProps key={clip.id} clip={clip} m={m} time={time} />;
}

function ProjectProps() {
  const p = useStore(s => s.project);
  const aspect = Object.entries(ASPECTS).find(([, [w, h]]) => w === p.width && h === p.height)?.[0] || 'custom';
  const setAspect = (a: string) => {
    const [w, h] = ASPECTS[a];
    store.commit(pp => { pp.width = w; pp.height = h; });
  };
  return (
    <div class="insp">
      <header class="insp-h"><h2>Project</h2><span class="panel-meta">{p.width}×{p.height} · {p.fps} fps</span></header>
      <Section title="Format">
        <div class="fld fld-wide">
          <label class="fld-l" for="pname">Name</label>
          <input id="pname" type="text" value={p.name} onChange={e => store.commit(pp => { pp.name = (e.target as HTMLInputElement).value.slice(0, 80) || 'Untitled edit'; })} />
        </div>
        <div class="fld fld-wide"><span class="fld-l">Aspect</span>
          <Seg value={aspect} onChange={setAspect} options={Object.keys(ASPECTS).map(a => ({ value: a, label: a }))} />
        </div>
        <div class="fld fld-wide"><span class="fld-l">Frame rate</span>
          <Seg value={p.fps} onChange={v => store.commit(pp => { pp.fps = v; })} options={[24, 25, 30, 50, 60].map(v => ({ value: v, label: String(v) }))} />
        </div>
        <ColorField id="pbg" label="Background" value={p.background} onChange={v => store.commit(pp => { pp.background = v; })} />
      </Section>
      <Section title="Exposure">
        <Toggle id="exp-auto" label="Lift dim shots (auto exposure)" checked={!!p.exposure?.auto} onChange={v => store.commit(pp => { pp.exposure = v ? { auto: true, target: pp.exposure?.target ?? 0.34 } : undefined; })} />
        {p.exposure?.auto && <Slider id="exp-target" label="Target brightness" min={0.2} max={0.5} step={0.01} fmt={v => `${Math.round(v * 100)}%`} parse={x => parseFloat(x) / 100} value={p.exposure.target ?? 0.34} dflt={0.34} onStart={begin} onEnd={end} onInput={v => store.live(pp => { pp.exposure = { auto: true, target: v }; })} />}
        <p class="hint">Dark grey reads as mud on a phone. Shots dimmer than the target are lifted (shadows and mids, highlights kept) before their grade and the look.</p>
      </Section>
      <Section title="Beat camera">
        <p class="hint">Zoom punch and rotation kick on the music's beats (video only; text stays clean). Needs a song on an audio track.</p>
        <Toggle id="cam-on" label="Punch on the beat" checked={!!p.camera?.on} onChange={v => store.commit(pp => { pp.camera = { ...(pp.camera || DEFAULT_CAMERA), on: v }; })} />
        {p.camera?.on && (
          <>
            <div class="fld fld-wide"><span class="fld-l">Hits on</span>
              <Seg small value={p.camera.every} onChange={v => store.commit(pp => { pp.camera = { ...pp.camera!, every: v }; })} options={[{ value: 'beat', label: 'Every beat' }, { value: 'half', label: 'Every other' }, { value: 'downbeat', label: 'Bar starts' }]} />
            </div>
            <Slider id="cam-punch" label="Zoom punch" min={0} max={0.2} step={0.005} fmt={v => `${(v * 100).toFixed(1)}%`} parse={x => parseFloat(x) / 100} value={p.camera.punch} dflt={DEFAULT_CAMERA.punch} onStart={begin} onEnd={end} onInput={v => store.live(pp => { pp.camera = { ...pp.camera!, punch: v }; })} />
            <Slider id="cam-kick" label="Rotation kick" min={0} max={5} step={0.1} fmt={v => `${v.toFixed(1)}°`} value={p.camera.kick} dflt={DEFAULT_CAMERA.kick} onStart={begin} onEnd={end} onInput={v => store.live(pp => { pp.camera = { ...pp.camera!, kick: v }; })} />
            <Slider id="cam-decay" label="Settle" min={0.04} max={0.6} step={0.01} fmt={v => `${v.toFixed(2)}s`} value={p.camera.decay} dflt={DEFAULT_CAMERA.decay} onStart={begin} onEnd={end} onInput={v => store.live(pp => { pp.camera = { ...pp.camera!, decay: v }; })} />
          </>
        )}
      </Section>
      <Section title="Shortcuts" open={false}>
        <dl class="keys">
          <dt>Space</dt><dd>Play / pause</dd>
          <dt>S</dt><dd>Split at playhead</dd>
          <dt>Del</dt><dd>Delete selected</dd>
          <dt>Ctrl Z / Ctrl Shift Z</dt><dd>Undo / redo</dd>
          <dt>Ctrl D</dt><dd>Duplicate</dd>
          <dt>← →</dt><dd>Step one frame (Shift: one second)</dd>
          <dt>Home / End</dt><dd>Jump to start / end</dd>
          <dt>Ctrl + wheel</dt><dd>Zoom the timeline</dd>
        </dl>
      </Section>
      <p class="note">Select a clip on the timeline to edit it.</p>
    </div>
  );
}

function ClipProps({ clip: c, m, time }: { clip: Clip; m?: MediaInfo; time: number }) {
  const lt = clamp(time - c.start, 0, c.dur);
  const inClip = time >= c.start && time <= clipEnd(c);
  const kfFor = (prop: AnimProp) => {
    const keys = c.kf?.[prop] || [];
    const eps = 0.5 / store.state.project.fps;
    return { has: keys.length > 0, at: inClip && keys.some(k => Math.abs(k.t - (time - c.start)) <= eps), toggle: () => toggleKeyframe(c, prop), prev: () => jumpKeyframe(c, prop, -1), next: () => jumpKeyframe(c, prop, 1) };
  };
  const anim = (prop: AnimProp) => ({
    value: propValue(c, prop, lt),
    onInput: (v: number) => setAnimProp(store.state.project.clips.find(x => x.id === c.id)!, prop, v, true),
    onStart: begin, onEnd: end, kf: kfFor(prop),
  });
  const live = (props: Record<string, any>) => updateClip(c.id, props, true);
  const p = store.state.project;
  const prev = trackClips(p, c.track).find(x => Math.abs(clipEnd(x) - c.start) < 1.5 / p.fps && x.id !== c.id);
  const isMedia = c.kind === 'video' || c.kind === 'audio';
  const visual = c.kind !== 'audio' && c.kind !== 'sfx';
  const hasSound = isMedia && !!m?.hasAudio;
  const color = colorOf(c);
  const onLook = store.state.project.tracks.find(t => t.id === c.track)?.role === 'look';
  const kindLabel = c.kind === 'text' ? 'Text' : c.kind === 'audio' ? 'Audio' : c.kind === 'image' ? 'Image' : c.kind === 'sfx' ? 'Sound' : c.kind === 'graphic' ? 'Graphic' : c.kind === 'shader' ? (onLook ? 'Look' : 'Effect') : 'Video';
  const custom = c.kind === 'graphic' || c.kind === 'shader';
  return (
    <div class="insp">
      <header class="insp-h">
        <h2><span class={`kdot k-${c.kind}`} />{kindLabel} <em>{c.id}</em></h2>
        <span class="panel-meta">at {c.start.toFixed(2)}s · {c.dur.toFixed(2)}s long</span>
        <Btn title="Delete clip (Del)" onClick={deleteSelected}>{Icon.trash}</Btn>
      </header>
      {m && <p class="note mono">{m.name}{isMedia ? ` · source ${(c.in ?? 0).toFixed(2)}–${((c.in ?? 0) + c.dur * (c.speed ?? 1)).toFixed(2)}s` : ''}</p>}

      {c.kind === 'text' && <TextProps c={c} />}
      {c.kind === 'graphic' && <GraphicProps c={c} />}
      {c.kind === 'shader' && <EffectProps c={c} />}

      {c.kind === 'sfx' && (
        <Section title="Sound">
          <Select<SfxType> id="sfx-type" label="Sound" value={c.sfx || 'whoosh'} onChange={v => updateClip(c.id, { sfx: v, in: 0, dur: SFX_INFO[v].dur })} options={SFX.map(t => ({ value: t, label: SFX_INFO[t].label }))} />
          <p class="hint">{c.sfx ? SFX_INFO[c.sfx].hint : ''}</p>
          <Slider id="sfx-vol" label="Volume" min={0} max={2} step={0.01} fmt={v => `${Math.round(v * 100)}%`} parse={x => parseFloat(x) / 100} dflt={0.35} {...anim('volume')} />
          <Toggle id="sfx-mute" label="Mute" checked={!!c.muted} onChange={v => updateClip(c.id, { muted: v })} />
        </Section>
      )}

      {visual && (
        <Section title="Transform" right={<Btn title="Reset transform" onClick={() => store.commit(pp => { const x = pp.clips.find(y => y.id === c.id); if (x) { delete x.transform; if (x.kf) { for (const k of ['x', 'y', 'scale', 'rotation', 'opacity'] as const) delete x.kf[k]; } } })}>Reset</Btn>}>
          <Slider id="tx" label="Position X" min={-1.5} max={1.5} step={0.001} fmt={v => `${Math.round(v * 100)}%`} parse={s => parseFloat(s) / 100} dflt={0} {...anim('x')} />
          <Slider id="ty" label="Position Y" min={-1.5} max={1.5} step={0.001} fmt={v => `${Math.round(v * 100)}%`} parse={s => parseFloat(s) / 100} dflt={0} {...anim('y')} />
          <Slider id="ts" label="Scale" min={0.05} max={8} log fmt={v => `${Math.round(v * 100)}%`} parse={s => parseFloat(s) / 100} dflt={1} {...anim('scale')} />
          <Slider id="tr" label="Rotation" min={-180} max={180} step={0.5} fmt={v => `${v.toFixed(1)}°`} dflt={0} {...anim('rotation')} />
          <Slider id="to" label="Opacity" min={0} max={1} step={0.01} fmt={v => `${Math.round(v * 100)}%`} parse={s => parseFloat(s) / 100} dflt={1} {...anim('opacity')} />
          {c.kind !== 'text' && !custom && (
            <div class="fld fld-wide"><span class="fld-l">Fit</span>
              <Seg value={c.fit || 'cover'} onChange={v => updateClip(c.id, { fit: v })} options={[{ value: 'cover', label: 'Fill frame' }, { value: 'contain', label: 'Whole picture' }]} />
            </div>
          )}
          {(c.kind === 'video' || c.kind === 'image') && (c.fit || 'cover') === 'cover' && (
            <>
              <Toggle id="foc-on" label="Keep the subject in frame" checked={!!c.focus} onChange={v => updateClip(c.id, { focus: v ? { x: 0.5, y: 0.4 } : null })} />
              {c.focus && <>
                <Slider id="foc-x" label="Subject across" min={0} max={1} step={0.005} fmt={v => `${Math.round(v * 100)}%`} parse={s => parseFloat(s) / 100} dflt={0.5} value={c.focus.x} onStart={begin} onEnd={end} onInput={v => live({ focus: { x: v, y: c.focus!.y } })} />
                <Slider id="foc-y" label="Subject down" min={0} max={1} step={0.005} fmt={v => `${Math.round(v * 100)}%`} parse={s => parseFloat(s) / 100} dflt={0.4} value={c.focus.y} onStart={begin} onEnd={end} onInput={v => live({ focus: { x: c.focus!.x, y: v } })} />
                <p class="hint">Where the face is in the source picture. The crop follows it at any zoom.</p>
              </>}
            </>
          )}
          <p class="hint">{c.kind === 'shader' ? 'Position, scale and rotation move the effect\'s anchor (uPos, uScale, uRot); keyframe them to follow the action.' : 'Drag the box on the preview to move; drag a corner to scale. ◆ adds a keyframe at the playhead.'}</p>
        </Section>
      )}

      {isMedia && (
        <Section title="Speed">
          <Slider id="sp" label="Speed" min={0.1} max={10} log fmt={v => `${v.toFixed(2)}x`} parse={s => parseFloat(s)} dflt={1}
            value={c.speed ?? 1} onStart={begin} onEnd={end}
            onInput={v => {
              // keep the same source range length visible: duration scales with speed
              const cur = store.state.project.clips.find(x => x.id === c.id)!;
              const src = cur.dur * (cur.speed ?? 1);
              const lim = m ? (m.duration - (cur.in ?? 0)) : Infinity;
              live({ speed: +v.toFixed(3), dur: Math.max(1 / p.fps, Math.min(src, lim) / v) });
            }} />
          <div class="chips-row">
            {[0.25, 0.5, 1, 1.5, 2, 4].map(v => (
              <button type="button" class={`chipbtn${(c.speed ?? 1) === v ? ' is-on' : ''}`} onClick={() => {
                const src = c.dur * (c.speed ?? 1);
                updateClip(c.id, { speed: v, dur: Math.max(1 / p.fps, src / v) });
              }}>{v}x</button>
            ))}
          </div>
          {hasSound && <Toggle id="kp" label="Keep pitch" checked={c.keepPitch !== false} onChange={v => updateClip(c.id, { keepPitch: v })} />}
          {c.kind === 'video' && (
            <div class="ramp">
              <span class="fld-l">Velocity ramp</span>
              <p class="hint">{hasRamp(c) ? `A speed curve with ${c.kf?.speed?.length} keys is on this clip.` : 'A burst on every beat, slow motion between: the motion pass that turned "lacklustre" into a standard.'}</p>
              <div class="chips-row">
                <button type="button" class="chipbtn" onClick={() => rampSelected()}>{hasRamp(c) ? 'Rebuild on the beat' : 'Ramp on the beat'}</button>
                {hasRamp(c) && <button type="button" class="chipbtn" onClick={() => rampSelected(true)}>Clear ramp</button>}
              </div>
            </div>
          )}
        </Section>
      )}

      {hasSound && (
        <Section title="Audio">
          <Slider id="vol" label="Volume" min={0} max={4} step={0.01} fmt={v => `${Math.round(v * 100)}%`} parse={s => parseFloat(s) / 100} dflt={1} {...anim('volume')} />
          <Slider id="fin" label="Fade in" min={0} max={Math.min(10, c.dur)} step={0.01} fmt={v => `${v.toFixed(2)}s`} value={c.fadeIn ?? 0} onStart={begin} onEnd={end} onInput={v => live({ fadeIn: v })} dflt={0} />
          <Slider id="fout" label="Fade out" min={0} max={Math.min(10, c.dur)} step={0.01} fmt={v => `${v.toFixed(2)}s`} value={c.fadeOut ?? 0} onStart={begin} onEnd={end} onInput={v => live({ fadeOut: v })} dflt={0} />
          <Toggle id="mute" label="Mute this clip" checked={!!c.muted} onChange={v => updateClip(c.id, { muted: v })} />
        </Section>
      )}

      {(c.kind === 'video' || c.kind === 'image' || c.kind === 'graphic') && (
        <Section title="Color" right={<Btn title="Reset colour" onClick={() => updateClip(c.id, { color: { brightness: 0, contrast: 0, saturation: 0, temperature: 0, tint: 0, hue: 0, vignette: 0, blur: 0 } })}>Reset</Btn>}>
          {([
            ['brightness', 'Brightness', -1, 1], ['contrast', 'Contrast', -1, 1], ['saturation', 'Saturation', -1, 1],
            ['temperature', 'Temperature', -1, 1], ['tint', 'Tint', -1, 1], ['hue', 'Hue', -180, 180], ['vignette', 'Vignette', 0, 1], ['blur', 'Blur', 0, 1],
          ] as [keyof ColorAdjust, string, number, number][]).map(([k, label, lo, hi]) => (
            <Slider id={`c-${k}`} label={label} min={lo} max={hi} step={k === 'hue' ? 1 : 0.01} fmt={v => (k === 'hue' ? `${Math.round(v)}°` : `${Math.round(v * 100)}`)} parse={s => (k === 'hue' ? parseFloat(s) : parseFloat(s) / 100)} dflt={0}
              value={color[k]} onStart={begin} onEnd={end} onInput={v => live({ color: { [k]: v } })} />
          ))}
        </Section>
      )}

      {c.kind !== 'text' && c.kind !== 'sfx' && !custom && (
        <Section title="Transition in">
          {prev ? (
            <>
              <Select<TransitionType | 'none'> id="trt" label="Type" value={c.transition?.type || 'none'} onChange={v => updateClip(c.id, { transition: v === 'none' ? null : { type: v, dur: c.transition?.dur ?? 0.5 } })}
                options={[{ value: 'none', label: 'None (cut)' }, ...TRANSITIONS.map(t => ({ value: t, label: TRANSITION_LABELS[t] }))]} />
              {c.transition && (
                <Slider id="trd" label="Duration" min={0.05} max={Math.max(0.1, Math.min(3, c.dur, prev.dur))} step={0.01} fmt={v => `${v.toFixed(2)}s`}
                  value={c.transition.dur} onStart={begin} onEnd={end} onInput={v => live({ transition: { type: c.transition!.type, dur: v } })} />
              )}
            </>
          ) : <p class="note">This clip has no clip right before it on its track.</p>}
        </Section>
      )}
    </div>
  );
}

function CodeBox(props: { id: string; label: string; value: string; rows: number; apply: (v: string) => void; hint: string }) {
  const [draft, setDraft] = useState(props.value);
  useEffect(() => setDraft(props.value), [props.value]);
  const dirty = draft !== props.value;
  return (
    <details class="codebox">
      <summary>{props.label}</summary>
      <textarea id={props.id} class="ta code" rows={props.rows} spellcheck={false} value={draft} onInput={e => setDraft((e.target as HTMLTextAreaElement).value)} />
      <div class="row-end"><span class="hint">{props.hint}</span><Btn kind="solid" disabled={!dirty} onClick={() => props.apply(draft)}>Apply</Btn></div>
    </details>
  );
}

function GraphicProps({ c }: { c: Clip }) {
  const live = (props: Record<string, any>) => updateClip(c.id, props, true);
  const r = { in: 'fade', out: 'fade', inDur: 0.25, outDur: 0.2, ...(c.reveal || {}) };
  const src = c.svg ? `data:image/svg+xml;charset=utf-8,${encodeURIComponent(c.svg)}` : '';
  return (
    <Section title="Graphic">
      {src && <div class="gfx-prev"><img src={src} alt="The graphic" /></div>}
      <Slider id="g-w" label="Width" min={0.05} max={2} step={0.01} fmt={v => `${Math.round(v * 100)}%`} parse={x => parseFloat(x) / 100} dflt={0.6} value={c.gw ?? 0.6} onStart={begin} onEnd={end} onInput={v => live({ gw: v })} />
      <Slider id="g-glow" label="Glow" min={0} max={1} step={0.01} fmt={v => `${Math.round(v * 100)}%`} parse={x => parseFloat(x) / 100} dflt={0} value={c.glow ?? 0} onStart={begin} onEnd={end} onInput={v => live({ glow: v })} />
      <div class="fld fld-wide"><span class="fld-l">Blend</span><Seg value={c.blend || 'normal'} onChange={v => updateClip(c.id, { blend: v })} options={BLEND_MODES.map(b => ({ value: b, label: b === 'add' ? 'Add light' : b === 'screen' ? 'Screen' : 'Normal' }))} /></div>
      <Select id="g-in" label="Appear" value={r.in} onChange={v => updateClip(c.id, { reveal: { in: v } })} options={REVEALS_IN.map(x => ({ value: x, label: x }))} />
      <Slider id="g-ind" label="Appear time" min={0} max={2} step={0.01} fmt={v => `${v.toFixed(2)}s`} dflt={0.25} value={r.inDur} onStart={begin} onEnd={end} onInput={v => live({ reveal: { inDur: v } })} />
      <Select id="g-out" label="Leave" value={r.out} onChange={v => updateClip(c.id, { reveal: { out: v } })} options={REVEALS_OUT.map(x => ({ value: x, label: x }))} />
      <Slider id="g-outd" label="Leave time" min={0} max={2} step={0.01} fmt={v => `${v.toFixed(2)}s`} dflt={0.2} value={r.outDur} onStart={begin} onEnd={end} onInput={v => live({ reveal: { outDur: v } })} />
      <CodeBox id="g-svg" label="Edit the vector art (SVG)" value={c.svg || ''} rows={10} hint="Drawing elements only; scripts, images and text are removed." apply={v => updateClip(c.id, { svg: v })} />
    </Section>
  );
}

function EffectProps({ c }: { c: Clip }) {
  const err = c.code ? compileError(c.code) : 'no code';
  const def = c.preset ? getFx(c.preset) : undefined;
  const isLook = useStore(s => s.project.tracks.find(t => t.id === c.track)?.role === 'look');
  return (
    <Section title={def ? (isLook ? 'Look' : 'Library effect') : 'Effect'}>
      <p class={`fx-status ${err ? 'bad' : 'ok'}`}>{err ? `Skipped: ${err}` : 'Compiles and renders in the preview, the export and Opus\'s review frames.'}</p>
      {def && <p class="hint"><b>{def.name}</b>: {def.hint}{isLook ? ' It grades every shot, graphic and effect under the text.' : def.anchor ? ' Position moves its anchor (the light, the impact point).' : ''}</p>}
      {def && def.params.map(prm => {
        const v = c.params?.[prm.id];
        if (isColorParam(prm)) return <ColorField id={`fxp-${prm.id}`} label={prm.label} value={typeof v === 'string' ? v : prm.color} onChange={x => setFxParam(c.id, prm.id, x)} />;
        const range = prm.max - prm.min;
        const step = range <= 2 ? 0.01 : range <= 20 ? 0.1 : 1;
        return <Slider id={`fxp-${prm.id}`} label={prm.label} min={prm.min} max={prm.max} step={step} fmt={x => (step < 0.1 ? x.toFixed(2) : step < 1 ? x.toFixed(1) : String(Math.round(x)))} value={typeof v === 'number' ? v : prm.def} onStart={begin} onEnd={end} onInput={x => setFxParam(c.id, prm.id, x)} dflt={prm.def} />;
      })}
      <div class="fld fld-wide"><span class="fld-l">Blend</span><Seg value={c.blend || 'normal'} onChange={v => updateClip(c.id, { blend: v })} options={BLEND_MODES.map(b => ({ value: b, label: b === 'add' ? 'Add light' : b === 'screen' ? 'Screen' : 'Normal' }))} /></div>
      <CodeBox id="e-code" label={def ? 'Edit the code (detaches it from the library preset)' : 'Edit the effect code (GLSL)'} value={c.code || ''} rows={def ? 8 : 14} hint="vec4 effect(vec2 uv, float t, float p): see the Effects panel for the helpers." apply={v => updateClip(c.id, { code: v })} />
    </Section>
  );
}

function TextProps({ c }: { c: Clip }) {
  const s = textStyleOf(c);
  const a = textAnimOf(c);
  const live = (style: Record<string, any>) => updateClip(c.id, { style }, true);
  const set = (style: Record<string, any>) => updateClip(c.id, { style });
  return (
    <>
      <Section title="Text">
        <textarea id="ttext" class="ta" rows={3} value={c.text || ''} aria-label="Text"
          onFocus={begin} onBlur={end}
          onInput={e => updateClip(c.id, { text: (e.target as HTMLTextAreaElement).value }, true)} />
        <p class="hint">*Asterisks* mark emphasis words (drawn in the emphasis colour with a glow). A new line starts the second line.</p>
        <div class="chips-row">
          <button type="button" class="chipbtn" onClick={() => updateClip(c.id, { style: { ...STANDARD_CAPTION, emphColor: s.emphColor || STANDARD_CAPTION.emphColor }, anim: { in: 'words', out: 'cap', inDur: 0.6, outDur: 0.28 }, transform: { y: 0.25 } })}>House caption style</button>
          <button type="button" class="chipbtn" onClick={wordsOnBeats}>Words on the beats</button>
          {c.words?.length ? <button type="button" class="chipbtn" onClick={() => updateClip(c.id, { words: null })}>Clear word times</button> : null}
        </div>
        <Select id="tfont" label="Font" value={s.font} onChange={v => set({ font: v })} options={FONTS.map(f => ({ value: f, label: f }))} />
        <div class="fld fld-wide"><span class="fld-l">Weight</span>
          <Seg small value={s.weight} onChange={v => set({ weight: v })} options={[400, 600, 700, 800, 900].map(w => ({ value: w, label: String(w) }))} />
        </div>
        <Slider id="tsize" label="Size" min={0.01} max={0.25} log fmt={v => `${(v * 100).toFixed(1)}`} parse={x => parseFloat(x) / 100} value={s.size} onStart={begin} onEnd={end} onInput={v => live({ size: v })} dflt={0.045} />
        <ColorField id="tcol" label="Fill" value={s.color} onChange={v => live({ color: v })} />
        <ColorField id="tecol" label="Emphasis" value={s.emphColor} onChange={v => live({ emphColor: v })} />
        <Slider id="teglow" label="Emphasis glow" min={0} max={1} step={0.01} fmt={v => `${Math.round(v * 100)}`} parse={x => parseFloat(x) / 100} value={s.emphGlow} onStart={begin} onEnd={end} onInput={v => live({ emphGlow: v })} dflt={0.6} />
        <Slider id="tscrim" label="Scrim" min={0} max={1} step={0.01} fmt={v => `${Math.round(v * 100)}`} parse={x => parseFloat(x) / 100} value={s.scrim} onStart={begin} onEnd={end} onInput={v => live({ scrim: v })} dflt={0} />
        <Slider id="tl2" label="Line 2 size" min={0.5} max={2} step={0.01} fmt={v => `${Math.round(v * 100)}%`} parse={x => parseFloat(x) / 100} value={s.lineScales?.[1] ?? 1} onStart={begin} onEnd={end} onInput={v => live({ lineScales: [s.lineScales?.[0] ?? 1, v] })} dflt={1} />
        <Slider id="tstroke" label="Outline" min={0} max={0.4} step={0.005} fmt={v => `${Math.round(v * 100)}`} parse={x => parseFloat(x) / 100} value={s.stroke} onStart={begin} onEnd={end} onInput={v => live({ stroke: v })} dflt={0} />
        {s.stroke > 0 && <ColorField id="tscol" label="Outline colour" value={s.strokeColor} onChange={v => live({ strokeColor: v })} />}
        <Slider id="tshadow" label="Shadow" min={0} max={1} step={0.01} fmt={v => `${Math.round(v * 100)}`} parse={x => parseFloat(x) / 100} value={s.shadow} onStart={begin} onEnd={end} onInput={v => live({ shadow: v })} dflt={0.5} />
        <Toggle id="tbg" label="Box behind text" checked={s.bg} onChange={v => set({ bg: v })} />
        {s.bg && <ColorField id="tbgc" label="Box colour" value={s.bgColor} onChange={v => live({ bgColor: v })} />}
        <div class="fld fld-wide"><span class="fld-l">Align</span>
          <Seg small value={s.align} onChange={v => set({ align: v })} options={[{ value: 'left', label: 'Left' }, { value: 'center', label: 'Centre' }, { value: 'right', label: 'Right' }]} />
        </div>
        <Toggle id="tup" label="Uppercase" checked={s.uppercase} onChange={v => set({ uppercase: v })} />
        <Toggle id="tit" label="Italic" checked={s.italic} onChange={v => set({ italic: v })} />
        <Slider id="ttrack" label="Letter spacing" min={-0.1} max={0.6} step={0.005} fmt={v => v.toFixed(2)} value={s.tracking} onStart={begin} onEnd={end} onInput={v => live({ tracking: v })} dflt={0} />
        <Slider id="tlh" label="Line height" min={0.7} max={2} step={0.01} fmt={v => v.toFixed(2)} value={s.lineHeight} onStart={begin} onEnd={end} onInput={v => live({ lineHeight: v })} dflt={1.12} />
        <Slider id="tmw" label="Wrap width" min={0.2} max={1} step={0.01} fmt={v => `${Math.round(v * 100)}%`} parse={x => parseFloat(x) / 100} value={s.maxWidth} onStart={begin} onEnd={end} onInput={v => live({ maxWidth: v })} dflt={0.86} />
        <Toggle id="tfit" label="Shrink lines to fit" checked={!!s.fit} onChange={v => set({ fit: v })} />
        <Toggle id="tknock" label="Footage in the letters (knockout)" checked={!!s.knockout} onChange={v => set({ knockout: v })} />
        {s.knockout && <Slider id="tknockd" label="Darken the rest" min={0} max={1} step={0.01} fmt={v => `${Math.round(v * 100)}`} parse={x => parseFloat(x) / 100} value={s.knockDark ?? 0.82} onStart={begin} onEnd={end} onInput={v => live({ knockDark: v })} dflt={0.82} />}
        <Select id="tmotif" label="Blow-away particles" value={s.motif || 'ash'} onChange={v => set({ motif: v })} options={['ash', 'blood', 'glass', 'sparks', 'petals'].map(m => ({ value: m, label: m[0].toUpperCase() + m.slice(1) }))} />
      </Section>
      <Section title="Animation">
        <Select<TextAnimIn> id="tain" label="In" value={a.in} onChange={v => updateClip(c.id, { anim: { in: v } })} options={TEXT_ANIMS_IN.map(x => ({ value: x, label: animLabel(x) }))} />
        <Slider id="taind" label="In duration" min={0} max={3} step={0.01} fmt={v => `${v.toFixed(2)}s`} value={a.inDur} onStart={begin} onEnd={end} onInput={v => updateClip(c.id, { anim: { inDur: v } }, true)} dflt={0.3} />
        <Select<TextAnimOut> id="taout" label="Out" value={a.out} onChange={v => updateClip(c.id, { anim: { out: v } })} options={TEXT_ANIMS_OUT.map(x => ({ value: x, label: animLabel(x) }))} />
        <Slider id="taoutd" label="Out duration" min={0} max={3} step={0.01} fmt={v => `${v.toFixed(2)}s`} value={a.outDur} onStart={begin} onEnd={end} onInput={v => updateClip(c.id, { anim: { outDur: v } }, true)} dflt={0.25} />
      </Section>
    </>
  );
}

function animLabel(x: string) {
  return IN_LABEL[x] || OUT_LABEL[x] || x;
}
