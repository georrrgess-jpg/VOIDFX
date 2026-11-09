// The critic's write-up: score, category bars, what works, every issue with its time and fix, the
// comparison with the standards, and the brief it wrote for Opus. In the round composer the issues
// become checkboxes: the owner picks which ones go into the next round.
import { CRITIC_AREAS } from '../../ai/critic';
import { player } from '../../engine/player';
import { openProject } from '../../state/projects';
import { store } from '../../state/store';
import { Critique } from '../../state/types';
import { Icon } from '../controls';
import { useState } from 'preact/hooks';
import { updateRecord } from '../../state/projects';
import { addCalibration } from '../../state/catalog';
import { timeAgo } from '../home/common';

export function seekTo(projectId: string, t: number) {
  const go = () => { store.set({ composer: null, critique: null, view: 'editor' }); setTimeout(() => player.seek(t), 60); };
  if (store.state.projectId === projectId) go();
  else void openProject(projectId).then(ok => ok && go());
}

const VERDICT: Record<Critique['verdict'], string> = { 'not ready': 'Not ready', close: 'Close', ready: 'Ready to post' };

export function ScoreRing({ score, size = 92 }: { score: number; size?: number }) {
  const hue = score >= 8.5 ? 150 : score >= 7 ? 45 : score >= 5 ? 25 : 355;
  return (
    <div class="ring" style={{ '--p': `${score * 10}%`, '--h': hue, width: `${size}px`, height: `${size}px` } as any} aria-label={`Score ${score} out of 10`}>
      <span><b>{score.toFixed(1)}</b><em>/10</em></span>
    </div>
  );
}

export function CritiqueView(props: {
  crit: Critique; projectId: string;
  picked?: Set<number>; onPick?: (i: number) => void;
  briefOn?: boolean; onBrief?: (on: boolean) => void;
}) {
  const { crit, projectId, picked, onPick } = props;
  const sel = !!onPick;
  const groups: [string, number[]][] = (['critical', 'major', 'minor'] as const).map(sv => [sv, crit.issues.map((x, i) => (x.severity === sv ? i : -1)).filter(i => i >= 0)] as [string, number[]]).filter(([, l]) => l.length);
  return (
    <article class="crit">
      <header class="crit-h">
        <ScoreRing score={crit.score} />
        <div class="crit-hl">
          <span class={`verdict-pill v-${crit.verdict.replace(' ', '-')}`}>{VERDICT[crit.verdict]}</span>
          <h3>{crit.headline}</h3>
          <p class="muted">Round {crit.round} · {crit.duration.toFixed(1)} s edit · {timeAgo(crit.at)}{crit.model ? ` · ${crit.model}` : ''}{crit.prevScore !== undefined ? ` · ${crit.score - crit.prevScore >= 0 ? '+' : ''}${(crit.score - crit.prevScore).toFixed(1)} on the last round` : ''}</p>
        </div>
      </header>

      {crit.comparison && (
        <p class={`crit-cmp v-${crit.comparison.verdict}`}><b>{crit.comparison.verdict === 'better' ? 'Better' : crit.comparison.verdict === 'worse' ? 'Worse' : 'About the same'} than round {crit.comparison.base}</b> ({crit.comparison.delta >= 0 ? '+' : ''}{crit.comparison.delta.toFixed(1)}), judged side by side. {crit.comparison.why}</p>
      )}
      {!sel && <OwnerScore crit={crit} projectId={projectId} />}

      {Object.keys(crit.scores).length > 0 && (
        <div class="crit-bars">
          {CRITIC_AREAS.filter(a => crit.scores[a.id] !== undefined).map(a => {
            const v = crit.scores[a.id];
            return (
              <div class="cbar">
                <span>{a.label}</span>
                <i><b style={{ width: `${v * 10}%`, '--h': v >= 8 ? 150 : v >= 6.5 ? 45 : v >= 5 ? 25 : 355 } as any} /></i>
                <em>{v.toFixed(1)}</em>
              </div>
            );
          })}
        </div>
      )}

      {crit.followUp?.length ? (
        <section class="crit-sec">
          <h4>{crit.round > 1 ? 'What this round was asked to fix' : 'The notes of the brief'} ({crit.followUp.filter(f => f.status === 'fixed').length}/{crit.followUp.length} done)</h4>
          <ul class="crit-follow">
            {crit.followUp.map(f => (
              <li><span class={`rn-chip s-${f.status}`}>{f.id} {f.status === 'fixed' ? 'done' : f.status === 'partly' ? 'partly' : 'not done'}</span><span>{f.text ? `${f.text.slice(0, 140)}${f.text.length > 140 ? '…' : ''} ` : ''}{f.comment && <em>{f.comment}</em>}</span></li>
            ))}
          </ul>
        </section>
      ) : null}

      {crit.path?.length ? (
        <section class="crit-sec crit-path">
          <h4>The path to 8 <em>+{crit.path.reduce((a, s) => a + s.gain, 0).toFixed(1)} if all done well</em></h4>
          <ol>
            {crit.path.map(s => (
              <li>
                <span class="path-gain">+{s.gain.toFixed(1)}</span>
                <span>{s.at !== undefined && <button type="button" class="tchip" onClick={() => seekTo(projectId, s.at!)}>{s.at.toFixed(2)}s{s.to !== undefined ? `–${s.to.toFixed(2)}s` : ''}</button>} {s.change}</span>
              </li>
            ))}
          </ol>
        </section>
      ) : null}

      {crit.strengths.length > 0 && (
        <section class="crit-sec">
          <h4>What works</h4>
          <ul class="crit-good">{crit.strengths.map(s => <li><span aria-hidden="true">{Icon.check}</span>{s}</li>)}</ul>
        </section>
      )}

      <section class="crit-sec">
        <h4>{sel ? 'Pick what goes into the next round' : `What to fix (${crit.issues.length})`}</h4>
        {groups.map(([sv, idx]) => (
          <div class={`crit-group g-${sv}`}>
            <p class="crit-gl">{sv} · {idx.length}</p>
            {idx.map(i => {
              const it = crit.issues[i];
              const on = picked?.has(i);
              const body = (
                <>
                  <div class="ci-top">
                    {it.at !== undefined && <button type="button" class="tchip" title="Show this moment in the editor" onClick={e => { e.preventDefault(); e.stopPropagation(); seekTo(projectId, it.at!); }}>{it.at.toFixed(2)}s</button>}
                    <span class="ci-area">{CRITIC_AREAS.find(a => a.id === it.area)?.label || it.area}</span>
                  </div>
                  <p class="ci-p">{it.problem}</p>
                  {it.fix && <p class="ci-f"><b>Fix</b> {it.fix}</p>}
                </>
              );
              return sel ? (
                <label class={`ci sel${on ? ' on' : ''}`}>
                  <input type="checkbox" checked={on} onChange={() => onPick!(i)} />
                  <span class="ci-box" aria-hidden="true">{on ? Icon.check : null}</span>
                  <div class="ci-body">{body}</div>
                </label>
              ) : <div class="ci"><div class="ci-body">{body}</div></div>;
            })}
          </div>
        ))}
        {!crit.issues.length && <p class="muted">The critic found nothing to fix.</p>}
      </section>

      {crit.versus && (
        <section class="crit-sec">
          <h4>Against the standards</h4>
          <p class="crit-vs">{crit.versus}</p>
        </section>
      )}

      {crit.brief && (
        <section class="crit-sec">
          <h4>The critic's write-up for Opus</h4>
          {props.onBrief ? (
            <label class={`ci sel brief${props.briefOn ? ' on' : ''}`}>
              <input type="checkbox" checked={props.briefOn} onChange={() => props.onBrief!(!props.briefOn)} />
              <span class="ci-box" aria-hidden="true">{props.briefOn ? Icon.check : null}</span>
              <div class="ci-body"><pre class="crit-brief">{crit.brief}</pre></div>
            </label>
          ) : <pre class="crit-brief">{crit.brief}</pre>}
        </section>
      )}
    </article>
  );
}

/** The owner's own score: watched with sound. Every one calibrates the critic's scale for later edits. */
function OwnerScore({ crit, projectId }: { crit: Critique; projectId: string }) {
  const [v, setV] = useState<number>(crit.ownerScore ?? Math.round(crit.score * 2) / 2);
  const [note, setNote] = useState(crit.ownerNote || '');
  const [saved, setSaved] = useState(crit.ownerScore !== undefined);
  const save = async () => {
    const rec = await updateRecord(projectId, r => {
      const round = (r.rounds || []).find(x => x.critique && x.critique.at === crit.at);
      if (!round?.critique) return false;
      round.critique.ownerScore = v;
      round.critique.ownerNote = note.trim();
    });
    crit.ownerScore = v; crit.ownerNote = note.trim();
    await addCalibration({ project: rec?.name || 'an edit', round: crit.round, critic: crit.score, owner: v, note: note.trim(), headline: crit.headline });
    setSaved(true);
    store.toast('Saved. The critic calibrates its scale to your scores from now on.', 'info', 4000);
  };
  const gap = v - crit.score;
  return (
    <section class={`oscore${saved ? ' is-saved' : ''}`} aria-label="Your score">
      <div class="oscore-h">
        <b>Your score</b>
        <span class="muted small">Watched it with sound? Rate it yourself: the critic learns your scale.</span>
      </div>
      <div class="oscore-row">
        <input type="range" min={0} max={10} step={0.5} value={v} aria-label="Your score out of 10" onInput={e => { setV(+(e.target as HTMLInputElement).value); setSaved(false); }} />
        <span class="oscore-v">{v.toFixed(1)}</span>
        {Math.abs(gap) >= 0.5 && <span class={`oscore-gap ${gap > 0 ? 'up' : 'down'}`}>{gap > 0 ? '+' : ''}{gap.toFixed(1)} vs the critic</span>}
      </div>
      <input class="oscore-note" type="text" value={note} placeholder="What makes it better or worse than the critic says? (optional)" onInput={e => { setNote((e.target as HTMLInputElement).value); setSaved(false); }} />
      <button type="button" class="btn btn-primary" onClick={() => void save()} disabled={saved}>{saved ? 'Saved' : 'Save my score'}</button>
    </section>
  );
}
