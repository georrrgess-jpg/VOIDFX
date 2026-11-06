import { useState } from 'preact/hooks';
import { activeJobFor } from '../ai/jobs';
import { updateRecord, saveCurrent } from '../state/projects';
import { openComposer } from './ai/actions';
import { refreshChecks } from '../ai/checkrunner';
import { player } from '../engine/player';
import { addTransitionSounds, normalize, pruneSfx } from '../state/ops';
import { store, useStore } from '../state/store';
import { Btn, Icon } from './controls';

const ICON: Record<string, string> = { pass: '✓', warn: '!', fail: '✕', info: 'i' };

/** Open the next round's brief with the failing gates written in. */
async function fixWithOpus(checks: { status: string; label: string; detail: string }[]) {
  const pid = store.state.projectId;
  if (!pid) return;
  await saveCurrent();
  const bad = checks.filter(c => c.status === 'fail' || c.status === 'warn').map(c => `- ${c.label}: ${c.detail}`).join('\n');
  await updateRecord(pid, r => { r.draft = `Fix every failing or flagged gate in the checkpoint without losing what works:\n${bad}`; });
  openComposer(pid, 'revise');
}

export function ChecksPanel() {
  const checks = useStore(s => s.checks);
  const pid = useStore(s => s.projectId);
  useStore(s => s.jobs);
  const running = !!(pid && activeJobFor(pid));
  const opus = useStore(s => s.director.available === 'yes');
  const [measuring, setMeasuring] = useState(false);
  const fails = checks.filter(c => c.status === 'fail').length, warns = checks.filter(c => c.status === 'warn').length;
  const ship = checks.length > 1 && !fails && !warns;
  const sound = checks.find(c => c.id === 'sound' && c.status !== 'pass');
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
        {sound?.action === 'add-sfx' && <Btn kind="solid" onClick={() => { let n = 0; store.commit(p => { n = addTransitionSounds(p); normalize(p, store.state.media); }); store.toast(n ? `${n} sounds added to the designed transitions (soft joins stay silent).` : 'There was no room for more sounds.', 'ok'); }}>{Icon.vol}<span>Sound the hard hits</span></Btn>}
        {sound?.action === 'thin-sfx' && <Btn kind="solid" onClick={() => { let n = 0; store.commit(p => { n = pruneSfx(p); normalize(p, store.state.media); }); store.toast(n ? `Removed ${n} stacked or extra sound effect${n > 1 ? 's' : ''}.` : 'Nothing to thin out.', 'ok'); }}>{Icon.vol}<span>Thin out sounds</span></Btn>}
        {opus && (fails > 0 || warns > 0) && <Btn kind="opus" disabled={running} onClick={() => void fixWithOpus(checks)}>{Icon.spark}<span>Fix with Opus</span></Btn>}
      </div>
    </div>
  );
}
