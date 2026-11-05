import { ComponentChildren } from 'preact';
import { useEffect, useRef, useState } from 'preact/hooks';
import { useStore } from '../../state/store';

/** Load something from storage and reload it whenever the catalogue changes. */
export function useCatalog<T>(load: () => Promise<T>, initial: T, deps: unknown[] = []): [T, () => void] {
  const rev = useStore(s => s.catalogRev);
  const [v, setV] = useState<T>(initial);
  const [tick, setTick] = useState(0);
  useEffect(() => { let live = true; void load().then(x => { if (live) setV(x); }); return () => { live = false; }; }, [rev, tick, ...deps]);
  return [v, () => setTick(t => t + 1)];
}

export function timeAgo(ts: number): string {
  if (!ts) return '';
  const s = (Date.now() - ts) / 1000;
  if (s < 60) return 'just now';
  if (s < 3600) return `${Math.floor(s / 60)} min ago`;
  if (s < 86400) return `${Math.floor(s / 3600)} h ago`;
  if (s < 86400 * 7) return `${Math.floor(s / 86400)} d ago`;
  return new Date(ts).toLocaleDateString();
}

/** A card that leans toward the pointer. */
export function TiltCard(props: { class?: string; children: ComponentChildren; onClick?: () => void; style?: any; i?: number; label?: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const onMove = (e: PointerEvent) => {
    const el = ref.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    const x = (e.clientX - r.left) / r.width - 0.5, y = (e.clientY - r.top) / r.height - 0.5;
    el.style.setProperty('--rx', `${(-y * 7).toFixed(2)}deg`);
    el.style.setProperty('--ry', `${(x * 9).toFixed(2)}deg`);
    el.style.setProperty('--mx', `${((x + 0.5) * 100).toFixed(1)}%`);
    el.style.setProperty('--my', `${((y + 0.5) * 100).toFixed(1)}%`);
  };
  const reset = () => { const el = ref.current; if (el) { el.style.setProperty('--rx', '0deg'); el.style.setProperty('--ry', '0deg'); } };
  const clickable = !!props.onClick;
  return (
    <div ref={ref} class={`tilt ${props.class || ''}${clickable ? ' is-click' : ''}`} style={{ ...(props.style || {}), '--i': props.i ?? 0 }} onPointerMove={onMove as any} onPointerLeave={reset}
      onClick={props.onClick} role={clickable ? 'button' : undefined} tabIndex={clickable ? 0 : undefined} aria-label={props.label}
      onKeyDown={e => { if (clickable && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); props.onClick!(); } }}>
      {props.children}
    </div>
  );
}

export function SectionHead(props: { eyebrow: string; title: string; text?: string; right?: ComponentChildren }) {
  return (
    <header class="hs-head">
      <div>
        <p class="hs-eyebrow">{props.eyebrow}</p>
        <h1 class="hs-title">{props.title}</h1>
        {props.text && <p class="hs-text">{props.text}</p>}
      </div>
      {props.right && <div class="hs-right">{props.right}</div>}
    </header>
  );
}

export function fmtDur(s: number) {
  if (!s) return '0:00';
  const m = Math.floor(s / 60), r = Math.floor(s % 60);
  return `${m}:${String(r).padStart(2, '0')}`;
}

/** A confirm step inside the page (the viewer blocks window.confirm). */
export function useConfirm(): [string | null, (id: string | null) => void] {
  const [id, setId] = useState<string | null>(null);
  useEffect(() => { if (!id) return; const t = setTimeout(() => setId(null), 4000); return () => clearTimeout(t); }, [id]);
  return [id, setId];
}
