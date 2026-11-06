// A "⋮" menu: one button that opens a short list of actions. Keyboard friendly (arrows, Escape),
// closes on outside click, and asks for a second click on destructive actions.
import { ComponentChildren } from 'preact';
import { createPortal } from 'preact/compat';
import { useEffect, useLayoutEffect, useRef, useState } from 'preact/hooks';
import { Icon } from './controls';

/**
 * A layer that floats above the whole page (rendered into <body>), anchored to an element. It opens
 * below or above (or beside) the anchor, whichever fits, is clamped inside the window, scrolls when
 * taller than the space, and follows the anchor on scroll and resize, so it can never hide behind
 * another card or run off the screen.
 */
export function Floating(props: {
  anchor: HTMLElement | null; place?: 'below' | 'beside'; align?: 'start' | 'end';
  class?: string; role?: string; label?: string; children: ComponentChildren; popRef?: { current: HTMLDivElement | null };
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState<{ left: number; top: number; maxH: number } | null>(null);
  const place = () => {
    const a = props.anchor, el = ref.current;
    if (!a || !el) return;
    const r = a.getBoundingClientRect();
    const vw = window.innerWidth, vh = window.innerHeight, m = 8, gap = 6;
    const w = Math.min(el.offsetWidth, vw - m * 2);
    const h = el.scrollHeight;
    let left: number, top: number, maxH: number;
    if (props.place === 'beside') {
      left = r.right + 10;
      if (left + w > vw - m) left = r.left - w - 10;
      if (left < m) left = Math.max(m, Math.min(vw - w - m, r.left));
      maxH = vh - m * 2;
      top = Math.max(m, Math.min(r.top, vh - Math.min(h, maxH) - m));
    } else {
      const below = vh - r.bottom - gap - m, above = r.top - gap - m;
      const down = h <= below || below >= above;
      maxH = Math.max(120, down ? below : above);
      top = down ? r.bottom + gap : Math.max(m, r.top - gap - Math.min(h, maxH));
      left = props.align === 'start' ? r.left : r.right - w;
      left = Math.max(m, Math.min(left, vw - w - m));
    }
    setPos(p => (p && p.left === left && p.top === top && p.maxH === maxH ? p : { left, top, maxH }));
  };
  useLayoutEffect(place);
  useEffect(() => {
    const on = () => place();
    window.addEventListener('resize', on);
    window.addEventListener('scroll', on, true);
    return () => { window.removeEventListener('resize', on); window.removeEventListener('scroll', on, true); };
  }, [props.anchor]);
  return createPortal(
    <div ref={el => { (ref as any).current = el; if (props.popRef) props.popRef.current = el; }} class={`floating ${props.class || ''}`} role={props.role as any} aria-label={props.label}
      style={pos ? { left: `${pos.left}px`, top: `${pos.top}px`, maxHeight: `${pos.maxH}px` } : { left: '-9999px', top: '0px' }}>
      {props.children}
    </div>,
    document.body,
  );
}

export interface MenuItem {
  label: string;
  icon?: ComponentChildren;
  run: () => void;
  danger?: boolean;
  /** Ask "Click again to …" before running. */
  confirm?: string;
  disabled?: boolean;
  hint?: string;
  sep?: boolean;
}

export function KebabMenu(props: { items: MenuItem[]; label?: string; class?: string; align?: 'left' | 'right' }) {
  const [open, setOpen] = useState(false);
  const [armed, setArmed] = useState<number | null>(null);
  const wrap = useRef<HTMLDivElement>(null);
  const btn = useRef<HTMLButtonElement>(null);
  const pop = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) { setArmed(null); return; }
    const outside = (e: PointerEvent) => { if (!wrap.current?.contains(e.target as Node) && !pop.current?.contains(e.target as Node)) setOpen(false); };
    const key = (e: KeyboardEvent) => {
      if (e.key === 'Escape') { e.stopPropagation(); setOpen(false); wrap.current?.querySelector<HTMLButtonElement>('.kebab-b')?.focus(); }
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault();
        const items = Array.from(pop.current?.querySelectorAll<HTMLButtonElement>('button:not([disabled])') || []);
        const i = items.indexOf(document.activeElement as HTMLButtonElement);
        items[(i + (e.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length]?.focus();
      }
    };
    window.addEventListener('pointerdown', outside, true);
    window.addEventListener('keydown', key, true);
    requestAnimationFrame(() => pop.current?.querySelector<HTMLButtonElement>('button:not([disabled])')?.focus());
    return () => { window.removeEventListener('pointerdown', outside, true); window.removeEventListener('keydown', key, true); };
  }, [open]);

  const stop = (e: Event) => e.stopPropagation();
  return (
    <div ref={wrap} class={`kebab${open ? ' is-open' : ''} ${props.class || ''}`} onClick={stop} onKeyDown={stop as any} onPointerDown={stop as any}>
      <button ref={btn} type="button" class="kebab-b" aria-haspopup="menu" aria-expanded={open} aria-label={props.label || 'More actions'} title={props.label || 'More actions'} onClick={() => setOpen(!open)}>{Icon.dots}</button>
      {open && (
        <Floating anchor={btn.current} align={props.align === 'left' ? 'start' : 'end'} class="kebab-pop" role="menu" popRef={pop}>
          {props.items.map((it, i) => (
            <>
              {it.sep && <hr />}
              <button type="button" role="menuitem" class={`${it.danger ? 'danger' : ''}${armed === i ? ' armed' : ''}`} disabled={it.disabled} title={it.hint}
                onClick={() => {
                  if (it.confirm && armed !== i) { setArmed(i); return; }
                  setOpen(false);
                  it.run();
                }}>
                <span class="kebab-ic" aria-hidden="true">{it.icon}</span>
                <span>{armed === i ? it.confirm : it.label}</span>
              </button>
            </>
          ))}
        </Floating>
      )}
    </div>
  );
}
