// The critic's write-up: score, category bars, what works, every issue with its time and fix, the
// comparison with the standards, and the brief it wrote for Opus. In the round composer the issues
// become checkboxes: the owner picks which ones go into the next round.
import { CRITIC_AREAS } from '../../ai/critic';
import { player } from '../../engine/player';
import { openProject } from '../../state/projects';
import { store } from '../../state/store';
import { Critique } from '../../state/types';
import { Icon } from '../controls';
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
