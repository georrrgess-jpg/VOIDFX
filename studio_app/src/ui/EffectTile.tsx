import { useEffect, useRef } from 'preact/hooks';
import { drawFxPreview, drawTextPreview, drawTransitionPreview, stillProgress } from '../engine/previews';
import { onGraphicReady } from '../engine/custom';
import type { FxPreset } from '../engine/fxlibrary';
import { TextAnimIn, TextAnimOut, TransitionType } from '../state/types';

let queue: (() => void)[] = [];
let scheduled = false;
function later(fn: () => void) {
  queue.push(fn);
  if (scheduled) return;
  scheduled = true;
  const run = () => {
    const t0 = performance.now();
    while (queue.length && performance.now() - t0 < 12) queue.shift()!();
    if (queue.length) requestAnimationFrame(run); else scheduled = false;
  };
  requestAnimationFrame(run);
}

/** A tile that shows a rendered still of an effect and plays it on hover or focus. */
export function EffectTile(props: { kind: 'transition'; type: TransitionType; label: string; active?: boolean; onPick: () => void; hint?: string }
  | { kind: 'text'; anim: { in?: TextAnimIn; out?: TextAnimOut }; label: string; active?: boolean; onPick: () => void; hint?: string }
  | { kind: 'fx'; fx: FxPreset; label: string; active?: boolean; onPick: () => void; hint?: string }) {
  const ref = useRef<HTMLCanvasElement>(null);
  const raf = useRef(0);
  const drawAt = (u: number) => {
    const c = ref.current;
    if (!c) return;
    if (props.kind === 'transition') drawTransitionPreview(c, props.type, u);
    else if (props.kind === 'fx') drawFxPreview(c, props.fx, u);
    else {
      const t = props.anim.in && props.anim.in !== 'none' ? u * 1.1 : 1.6 + u * 0.6;
      drawTextPreview(c, props.anim, t);
    }
  };
  const still = () => {
    if (props.kind === 'transition') drawAt(stillProgress(props.type));
    else if (props.kind === 'fx') drawAt(0.5);
    else drawAt(props.anim.in && props.anim.in !== 'none' ? 0.55 : 0.4);
  };
  const key = props.kind === 'transition' ? props.type : props.kind === 'fx' ? props.fx.id : JSON.stringify(props.anim);
  useEffect(() => { later(still); return () => cancelAnimationFrame(raf.current); }, [key]);
  useEffect(() => (props.kind === 'fx' && props.fx.kind === 'graphic' ? onGraphicReady(() => later(still)) : undefined), [key]);
  const play = () => {
    cancelAnimationFrame(raf.current);
    const t0 = performance.now();
    const loop = () => {
      const u = ((performance.now() - t0) / 1600) % 1.25;
      drawAt(Math.min(1, u));
      raf.current = requestAnimationFrame(loop);
    };
    raf.current = requestAnimationFrame(loop);
  };
  const stop = () => { cancelAnimationFrame(raf.current); still(); };
  return (
    <button type="button" class={`etile${props.active ? ' is-on' : ''}`} onClick={props.onPick} onMouseEnter={play} onMouseLeave={stop} onFocus={play} onBlur={stop} title={props.hint || props.label}>
      <canvas ref={ref} width={144} height={256} aria-hidden="true" />
      <span class="etile-n">{props.label}</span>
    </button>
  );
}
