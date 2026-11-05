import { useState } from 'preact/hooks';
import { refineEdit } from '../ai/director';
import { refreshChecks } from '../ai/checkrunner';
import { player } from '../engine/player';
import { addTransitionSounds, normalize } from '../state/ops';
import { store, useStore } from '../state/store';
import { Btn, Icon } from './controls';

const ICON: Record<string, string> = { pass: '✓', warn: '!', fail: '✕', info: 'i' };

export function ChecksPanel() {
  const checks = useStore(s => s.checks);
  const running = useStore(s => s.director.running);
  const opus = useStore(s => s.director.available === 'yes');
  const [measuring, setMeasuring] = useState(false);
  const fails = checks.filter(c => c.status === 'fail').length, warns = checks.filter(c => c.status === 'warn').length;
  const ship = checks.length > 1 && !fails && !warns;
  const silent = checks.find(c => c.id === 'sound' && c.status !== 'pass');
  return (
    <div class="insp checks">
      <header class="insp-h"><h2>Ship checkpoint</h2><span class={`verdict ${ship ? 'ok' : fails ? 'bad' : 'warn'}`}>{ship ? 'Ready to ship' : fails ? `${fails} failing` : `${warns} to look at`}</span></header>
      <p class="note">Your measurable gates, run on the timeline as you edit. Faces and set-piece quality still need eyes on the frames.</p>
      <ul class="chk">
        {checks.map(c => (
          <li class={`chk-i s-${c.status}`}>
            <span class="chk-ic" aria-hidden="true">{ICON[c.status]}</span>
            <div>
              <div class="chk-l">{c.label}</div>
              <div class="chk-d">{c.detail}</div>
              {c.at && c.at.length > 0 && <div class="chk-at">{c.at.slice(0, 10).map(t => <button type="button" class="chipbtn" onClick={() => player.seek(t)}>{t.toFixed(2)}s</button>)}</div>}
            </div>
          </li>
        ))}
      </ul>
      <div class="chk-acts">
        <Btn kind="solid" disabled={measuring} onClick={async () => { setMeasuring(true); await refreshChecks({ seam: true }); setMeasuring(false); }}>{measuring ? 'Measuring…' : 'Measure the loop seam'}</Btn>
        {silent && <Btn kind="solid" onClick={() => { store.commit(p => { addTransitionSounds(p); normalize(p, store.state.media); }); store.toast('Every transition now has its own sound.', 'ok'); }}>{Icon.vol}<span>Add transition sounds</span></Btn>}
        {opus && (fails > 0 || warns > 0) && <Btn kind="opus" disabled={running} onClick={() => { store.set({ rightTab: 'director' }); void refineEdit('Fix every failing or flagged gate in the automated checkpoint without losing what works.'); }}>{Icon.spark}<span>Fix with Opus</span></Btn>}
      </div>
    </div>
  );
}
