import { ComponentChildren } from 'preact';
import { useEffect, useRef, useState } from 'preact/hooks';

// ---------- icons (inline SVG, 16px grid) ----------
const P = (d: string) => <path d={d} />;
export const Icon = {
  play: <svg viewBox="0 0 16 16" class="ic"><path d="M4.5 2.8v10.4L13 8z" fill="currentColor" stroke="none" /></svg>,
  pause: <svg viewBox="0 0 16 16" class="ic"><path d="M4 2.5h3v11H4zM9 2.5h3v11H9z" fill="currentColor" stroke="none" /></svg>,
  undo: <svg viewBox="0 0 16 16" class="ic">{P('M5.5 3.5 2.5 6.5l3 3')}{P('M2.8 6.5h6.7a3.5 3.5 0 0 1 0 7H7')}</svg>,
  redo: <svg viewBox="0 0 16 16" class="ic">{P('m10.5 3.5 3 3-3 3')}{P('M13.2 6.5H6.5a3.5 3.5 0 0 0 0 7H9')}</svg>,
  split: <svg viewBox="0 0 16 16" class="ic">{P('M8 1.5v13')}{P('M3 4.5h3.5v7H3zM9.5 4.5H13v7H9.5z')}</svg>,
  trash: <svg viewBox="0 0 16 16" class="ic">{P('M2.5 4h11M6 4V2.5h4V4M4 4l.7 9.5h6.6L12 4')}</svg>,
  copy: <svg viewBox="0 0 16 16" class="ic">{P('M5.5 5.5h8v8h-8z')}{P('M10.5 5.5v-3h-8v8h3')}</svg>,
  magnet: <svg viewBox="0 0 16 16" class="ic">{P('M3.5 2.5v5a4.5 4.5 0 0 0 9 0v-5h-3v5a1.5 1.5 0 0 1-3 0v-5z')}</svg>,
  snap: <svg viewBox="0 0 16 16" class="ic">{P('M8 1.5v13M3 5l2.5 3L3 11M13 5l-2.5 3 2.5 3')}</svg>,
  plus: <svg viewBox="0 0 16 16" class="ic">{P('M8 3v10M3 8h10')}</svg>,
  minus: <svg viewBox="0 0 16 16" class="ic">{P('M3 8h10')}</svg>,
  fit: <svg viewBox="0 0 16 16" class="ic">{P('M2.5 5.5v-3h3M10.5 2.5h3v3M13.5 10.5v3h-3M5.5 13.5h-3v-3')}</svg>,
  media: <svg viewBox="0 0 16 16" class="ic">{P('M2 3.5h12v9H2z')}{P('m6.5 6 3.5 2-3.5 2z')}</svg>,
  text: <svg viewBox="0 0 16 16" class="ic">{P('M3 4V2.5h10V4M8 2.5v11M6 13.5h4')}</svg>,
  transition: <svg viewBox="0 0 16 16" class="ic">{P('M2.5 3.5h5v9h-5zM8.5 3.5h5v9h-5z')}{P('m6 6 4 4M10 6 6 10')}</svg>,
  spark: <svg viewBox="0 0 16 16" class="ic">{P('M8 1.5 9.4 6.6 14.5 8 9.4 9.4 8 14.5 6.6 9.4 1.5 8l5.1-1.4z')}</svg>,
  sliders: <svg viewBox="0 0 16 16" class="ic">{P('M2.5 4h7M12.5 4h1M2.5 12h1M6.5 12h7')}<circle cx="11" cy="4" r="1.5" /><circle cx="5" cy="12" r="1.5" /></svg>,
  eye: <svg viewBox="0 0 16 16" class="ic">{P('M1.5 8s2.4-4.5 6.5-4.5S14.5 8 14.5 8 12.1 12.5 8 12.5 1.5 8 1.5 8z')}<circle cx="8" cy="8" r="2" /></svg>,
  eyeOff: <svg viewBox="0 0 16 16" class="ic">{P('M2.5 2.5l11 11M6.4 4A6.7 6.7 0 0 1 8 3.5c4.1 0 6.5 4.5 6.5 4.5a11 11 0 0 1-1.9 2.4M10 11.9a5 5 0 0 1-2 .6C3.9 12.5 1.5 8 1.5 8a11 11 0 0 1 2.4-3')}</svg>,
  vol: <svg viewBox="0 0 16 16" class="ic">{P('M2.5 6h2.5L8.5 3v10L5 10H2.5z')}{P('M11 5.5a3.5 3.5 0 0 1 0 5M12.8 3.6a6 6 0 0 1 0 8.8')}</svg>,
  mute: <svg viewBox="0 0 16 16" class="ic">{P('M2.5 6h2.5L8.5 3v10L5 10H2.5z')}{P('m11 6 3.5 4M14.5 6 11 10')}</svg>,
  loop: <svg viewBox="0 0 16 16" class="ic">{P('M3 7.5V6.5a2 2 0 0 1 2-2h7.5M10.5 2.5l2 2-2 2M13 8.5v1a2 2 0 0 1-2 2H3.5M5.5 13.5l-2-2 2-2')}</svg>,
  close: <svg viewBox="0 0 16 16" class="ic">{P('M3.5 3.5l9 9M12.5 3.5l-9 9')}</svg>,
  diamond: <svg viewBox="0 0 16 16" class="ic">{P('M8 2.5 13.5 8 8 13.5 2.5 8z')}</svg>,
  chevL: <svg viewBox="0 0 16 16" class="ic">{P('M10 3.5 5.5 8l4.5 4.5')}</svg>,
  chevR: <svg viewBox="0 0 16 16" class="ic">{P('M6 3.5 10.5 8 6 12.5')}</svg>,
  upload: <svg viewBox="0 0 16 16" class="ic">{P('M8 10.5V2.5M4.5 6 8 2.5 11.5 6M2.5 10.5v3h11v-3')}</svg>,
  download: <svg viewBox="0 0 16 16" class="ic">{P('M8 2.5v8M4.5 7 8 10.5 11.5 7M2.5 10.5v3h11v-3')}</svg>,
  menu: <svg viewBox="0 0 16 16" class="ic">{P('M2.5 4h11M2.5 8h11M2.5 12h11')}</svg>,
  stop: <svg viewBox="0 0 16 16" class="ic"><path d="M4 4h8v8H4z" fill="currentColor" stroke="none" /></svg>,
  frameBack: <svg viewBox="0 0 16 16" class="ic">{P('M11.5 3.5 6 8l5.5 4.5M4 3.5v9')}</svg>,
  frameFwd: <svg viewBox="0 0 16 16" class="ic">{P('M4.5 3.5 10 8l-5.5 4.5M12 3.5v9')}</svg>,
};

export function Btn(props: { onClick?: (e: MouseEvent) => void; title?: string; children?: ComponentChildren; kind?: 'ghost' | 'solid' | 'primary' | 'opus' | 'danger'; active?: boolean; disabled?: boolean; class?: string; id?: string; type?: 'button' | 'submit' }) {
  const { kind = 'ghost', active, disabled, title, children, onClick } = props;
  return (
    <button id={props.id} type={props.type || 'button'} class={`btn btn-${kind}${active ? ' is-on' : ''} ${props.class || ''}`} title={title} aria-label={title} aria-pressed={active === undefined ? undefined : active} disabled={disabled} onClick={onClick as any}>
      {children}
    </button>
  );
}

export function Seg<T extends string | number>(props: { value: T; options: { value: T; label: ComponentChildren; title?: string }[]; onChange: (v: T) => void; id?: string; small?: boolean }) {
  return (
    <div class={`seg${props.small ? ' seg-sm' : ''}`} role="radiogroup" id={props.id}>
      {props.options.map(o => (
        <button type="button" role="radio" aria-checked={o.value === props.value} class={o.value === props.value ? 'is-on' : ''} title={o.title} onClick={() => props.onChange(o.value)}>
          {o.label}
        </button>
      ))}
    </div>
  );
}

export function Section(props: { title: string; children: ComponentChildren; open?: boolean; right?: ComponentChildren }) {
  const [open, setOpen] = useState(props.open !== false);
  return (
    <section class={`sec${open ? '' : ' is-closed'}`}>
      <header class="sec-h">
        <button type="button" class="sec-t" onClick={() => setOpen(!open)} aria-expanded={open}>
          <span class="sec-caret">{open ? '▾' : '▸'}</span>{props.title}
        </button>
        {props.right}
      </header>
      {open && <div class="sec-b">{props.children}</div>}
    </section>
  );
}

/** Slider with a typed value field. `fmt` shows the value, `parse` reads typed input. */
export function Slider(props: {
  id: string; label: string; value: number; min: number; max: number; step?: number;
  onInput: (v: number) => void; onStart?: () => void; onEnd?: () => void;
  fmt?: (v: number) => string; parse?: (s: string) => number; log?: boolean;
  kf?: { has: boolean; at: boolean; toggle: () => void; prev?: () => void; next?: () => void };
  dflt?: number;
}) {
  const { min, max, log } = props;
  const toPos = (v: number) => (log ? (Math.log(v) - Math.log(min)) / (Math.log(max) - Math.log(min)) : (v - min) / (max - min));
  const fromPos = (p: number) => (log ? Math.exp(Math.log(min) + p * (Math.log(max) - Math.log(min))) : min + p * (max - min));
  const fmt = props.fmt || ((v: number) => (Math.abs(v) >= 100 ? v.toFixed(0) : v.toFixed(2)));
  const [text, setText] = useState<string | null>(null);
  const step = props.step ?? (max - min) / 200;
  const snapV = (v: number) => (log ? v : Math.round(v / step) * step);
  return (
    <div class="fld">
      <label class="fld-l" for={props.id} onDblClick={() => { if (props.dflt !== undefined) { props.onStart?.(); props.onInput(props.dflt); props.onEnd?.(); } }} title={props.dflt !== undefined ? 'Double-click to reset' : undefined}>{props.label}</label>
      <input
        id={props.id} type="range" min={0} max={1000} step={1} value={Math.round(Math.max(0, Math.min(1, toPos(props.value))) * 1000)}
        onPointerDown={() => props.onStart?.()} onPointerUp={() => props.onEnd?.()} onKeyUp={() => props.onEnd?.()} onKeyDown={() => props.onStart?.()}
        onInput={e => props.onInput(snapV(fromPos(+(e.target as HTMLInputElement).value / 1000)))}
        aria-label={props.label}
      />
      <input
        class="fld-n" type="text" inputMode="decimal" aria-label={`${props.label} value`}
        value={text ?? fmt(props.value)}
        onFocus={e => { setText(fmt(props.value)); (e.target as HTMLInputElement).select(); }}
        onInput={e => setText((e.target as HTMLInputElement).value)}
        onBlur={() => {
          if (text !== null) {
            const v = props.parse ? props.parse(text) : parseFloat(text);
            if (Number.isFinite(v)) { props.onStart?.(); props.onInput(Math.max(min, Math.min(max, v))); props.onEnd?.(); }
          }
          setText(null);
        }}
        onKeyDown={e => { if (e.key === 'Enter') (e.target as HTMLInputElement).blur(); if (e.key === 'Escape') { setText(null); (e.target as HTMLInputElement).blur(); } }}
      />
      {props.kf ? (
        <span class="kf">
          <button type="button" class="kf-nav" title="Previous keyframe" disabled={!props.kf.has} onClick={props.kf.prev}>{Icon.chevL}</button>
          <button type="button" class={`kf-btn${props.kf.at ? ' is-at' : props.kf.has ? ' is-has' : ''}`} title={props.kf.at ? 'Remove keyframe at playhead' : 'Add keyframe at playhead'} onClick={props.kf.toggle}>{Icon.diamond}</button>
          <button type="button" class="kf-nav" title="Next keyframe" disabled={!props.kf.has} onClick={props.kf.next}>{Icon.chevR}</button>
        </span>
      ) : <span />}
    </div>
  );
}

export function Toggle(props: { id: string; label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <label class="tog" for={props.id}>
      <input id={props.id} type="checkbox" checked={props.checked} onChange={e => props.onChange((e.target as HTMLInputElement).checked)} />
      <span class="tog-s" aria-hidden="true" />
      <span>{props.label}</span>
    </label>
  );
}

export function ColorField(props: { id: string; label: string; value: string; onChange: (v: string) => void }) {
  return (
    <div class="fld fld-color">
      <label class="fld-l" for={props.id}>{props.label}</label>
      <input id={props.id} type="color" value={props.value.length === 4 ? '#' + props.value.slice(1).split('').map(c => c + c).join('') : props.value} onInput={e => props.onChange((e.target as HTMLInputElement).value)} />
      <code class="fld-hex">{props.value}</code>
    </div>
  );
}

export function Select<T extends string | number>(props: { id: string; label: string; value: T; options: { value: T; label: string }[]; onChange: (v: T) => void }) {
  return (
    <div class="fld fld-sel">
      <label class="fld-l" for={props.id}>{props.label}</label>
      <select id={props.id} value={String(props.value)} onChange={e => {
        const raw = (e.target as HTMLSelectElement).value;
        const o = props.options.find(x => String(x.value) === raw);
        if (o) props.onChange(o.value);
      }}>
        {props.options.map(o => <option value={String(o.value)}>{o.label}</option>)}
      </select>
    </div>
  );
}

/** Calls `fn` on every animation frame while mounted. */
export function useFrame(fn: () => void) {
  const ref = useRef(fn);
  ref.current = fn;
  useEffect(() => {
    let raf = 0;
    const loop = () => { ref.current(); raf = requestAnimationFrame(loop); };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, []);
}
