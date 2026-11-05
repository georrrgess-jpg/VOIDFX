import { TRANSITION_LABELS } from '../engine/transitions';
import { store, useStore } from '../state/store';
import { AnimProp, ASPECTS, Clip, ColorAdjust, FONTS, MediaInfo, TEXT_ANIMS_IN, TEXT_ANIMS_OUT, TextAnimIn, TextAnimOut, TRANSITIONS, TransitionType } from '../state/types';
import { clamp, clipEnd, colorOf, propValue, textAnimOf, textStyleOf, trackClips } from '../state/util';
import { deleteSelected, jumpKeyframe, setAnimProp, toggleKeyframe, updateClip } from './actions';
import { Btn, ColorField, Icon, Section, Seg, Select, Slider, Toggle } from './controls';

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
  const visual = c.kind !== 'audio';
  const hasSound = isMedia && !!m?.hasAudio;
  const color = colorOf(c);
  const kindLabel = c.kind === 'text' ? 'Text' : c.kind === 'audio' ? 'Audio' : c.kind === 'image' ? 'Image' : 'Video';
  return (
    <div class="insp">
      <header class="insp-h">
        <h2><span class={`kdot k-${c.kind}`} />{kindLabel} <em>{c.id}</em></h2>
        <span class="panel-meta">at {c.start.toFixed(2)}s · {c.dur.toFixed(2)}s long</span>
        <Btn title="Delete clip (Del)" onClick={deleteSelected}>{Icon.trash}</Btn>
      </header>
      {m && <p class="note mono">{m.name}{isMedia ? ` · source ${(c.in ?? 0).toFixed(2)}–${((c.in ?? 0) + c.dur * (c.speed ?? 1)).toFixed(2)}s` : ''}</p>}

      {c.kind === 'text' && <TextProps c={c} />}

      {visual && (
        <Section title="Transform" right={<Btn title="Reset transform" onClick={() => store.commit(pp => { const x = pp.clips.find(y => y.id === c.id); if (x) { delete x.transform; if (x.kf) { for (const k of ['x', 'y', 'scale', 'rotation', 'opacity'] as const) delete x.kf[k]; } } })}>Reset</Btn>}>
          <Slider id="tx" label="Position X" min={-1.5} max={1.5} step={0.001} fmt={v => `${Math.round(v * 100)}%`} parse={s => parseFloat(s) / 100} dflt={0} {...anim('x')} />
          <Slider id="ty" label="Position Y" min={-1.5} max={1.5} step={0.001} fmt={v => `${Math.round(v * 100)}%`} parse={s => parseFloat(s) / 100} dflt={0} {...anim('y')} />
          <Slider id="ts" label="Scale" min={0.05} max={8} log fmt={v => `${Math.round(v * 100)}%`} parse={s => parseFloat(s) / 100} dflt={1} {...anim('scale')} />
          <Slider id="tr" label="Rotation" min={-180} max={180} step={0.5} fmt={v => `${v.toFixed(1)}°`} dflt={0} {...anim('rotation')} />
          <Slider id="to" label="Opacity" min={0} max={1} step={0.01} fmt={v => `${Math.round(v * 100)}%`} parse={s => parseFloat(s) / 100} dflt={1} {...anim('opacity')} />
          {c.kind !== 'text' && (
            <div class="fld fld-wide"><span class="fld-l">Fit</span>
              <Seg value={c.fit || 'cover'} onChange={v => updateClip(c.id, { fit: v })} options={[{ value: 'cover', label: 'Fill frame' }, { value: 'contain', label: 'Whole picture' }]} />
            </div>
          )}
          <p class="hint">Drag the box on the preview to move; drag a corner to scale. ◆ adds a keyframe at the playhead.</p>
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

      {(c.kind === 'video' || c.kind === 'image') && (
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

      {c.kind !== 'text' && (
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
        <Select id="tfont" label="Font" value={s.font} onChange={v => set({ font: v })} options={FONTS.map(f => ({ value: f, label: f }))} />
        <div class="fld fld-wide"><span class="fld-l">Weight</span>
          <Seg small value={s.weight} onChange={v => set({ weight: v })} options={[400, 600, 700, 800, 900].map(w => ({ value: w, label: String(w) }))} />
        </div>
        <Slider id="tsize" label="Size" min={0.01} max={0.25} log fmt={v => `${(v * 100).toFixed(1)}`} parse={x => parseFloat(x) / 100} value={s.size} onStart={begin} onEnd={end} onInput={v => live({ size: v })} dflt={0.045} />
        <ColorField id="tcol" label="Fill" value={s.color} onChange={v => live({ color: v })} />
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
  const map: Record<string, string> = { none: 'None', fade: 'Fade', rise: 'Rise', drop: 'Drop', pop: 'Pop', blur: 'Blur', typewriter: 'Typewriter', words: 'Word by word', slide_left: 'Slide left', slide_right: 'Slide right', sink: 'Sink', lift: 'Lift', shrink: 'Shrink' };
  return map[x] || x;
}

