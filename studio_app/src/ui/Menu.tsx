// A "⋮" menu: one button that opens a short list of actions. Keyboard friendly (arrows, Escape),
// closes on outside click, and asks for a second click on destructive actions.
import { ComponentChildren } from 'preact';
import { useEffect, useRef, useState } from 'preact/hooks';
import { Icon } from './controls';

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
  const [up, setUp] = useState(false);
  const [left, setLeft] = useState(false);
  const wrap = useRef<HTMLDivElement>(null);
  const pop = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) { setArmed(null); return; }
    const r = wrap.current?.getBoundingClientRect();
    setUp(!!r && window.innerHeight - r.bottom < 60 + props.items.length * 38);
    // open to the right when a right-aligned menu would run past the scroll area's left edge
    const box = wrap.current?.closest('.home-main, .rp-body, .app')?.getBoundingClientRect();
    setLeft(props.align === 'left' || (!!r && r.right - 240 < (box?.left ?? 0) + 4));
    const outside = (e: PointerEvent) => { if (!wrap.current?.contains(e.target as Node)) setOpen(false); };
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
      <button type="button" class="kebab-b" aria-haspopup="menu" aria-expanded={open} aria-label={props.label || 'More actions'} title={props.label || 'More actions'} onClick={() => setOpen(!open)}>{Icon.dots}</button>
      {open && (
        <div ref={pop} class={`kebab-pop${up ? ' up' : ''}${left ? ' left' : ''}`} role="menu">
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
        </div>
      )}
    </div>
  );
}
