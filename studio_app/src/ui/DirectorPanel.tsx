// The editor's Opus tab: the project's rounds (what the owner asked, what Opus did, what the critic
// said), the job working on it right now, and the next step. Rounds run in the background.
import { MODEL } from '../ai/director';
import { activeJobFor } from '../ai/jobs';
import { normalize } from '../state/ops';
import { store, useStore } from '../state/store';
import { deepClone } from '../state/util';
import { NoteCheck, Round } from '../state/types';
import { Icon } from './controls';
import { openComposer, sendToCritic } from './ai/actions';
import { JobCard } from './ai/Activity';
import { ScoreRing } from './ai/CritiqueView';
import { timeAgo } from './home/common';

function restore(r: Round) {
  if (!r.snapshot) return;
  const p = normalize(deepClone(r.snapshot), store.state.media);
  if (store.state.lock) { store.blocked(); return; }
  store.replace({ ...p, name: store.state.project.name });
  store.toast(`Restored the timeline from round ${r.n}. Undo (Ctrl+Z) brings the newer version back.`, 'ok', 6000);
}

const ST_LABEL: Record<string, string> = { done: 'done', partial: 'partly', not: 'not done', fixed: 'done', partly: 'partly' };

/** Each numbered note of a round: how Opus planned it, how many operations carried it, its own check and the critic's. */
function NotesList({ notes, follow }: { notes: NoteCheck[]; follow?: { id: string; status: string; comment: string }[] }) {
  const crit = new Map((follow || []).map(f => [f.id, f]));
  const done = notes.filter(n => (crit.get(n.id)?.status ?? n.status) === (crit.has(n.id) ? 'fixed' : 'done')).length;
  return (
    <details class="rnd-notes">
      <summary><span>{notes.length} note{notes.length > 1 ? 's' : ''}</span><b>{done}/{notes.length} done{crit.size ? ', per the critic' : ', per Opus'}</b></summary>
      <ol>
        {notes.map(n => {
          const f = crit.get(n.id);
          return (
            <li>
              <p class="rn-t"><span class="rn-id">{n.id}</span><span class={`rn-from f-${n.from}`}>{n.from}{n.at !== undefined ? ` @ ${n.at.toFixed(2)}s` : ''}</span>{n.text.length > 180 ? `${n.text.slice(0, 180)}…` : n.text}</p>
              <p class="rn-s">
                <span class="rn-chip">{n.ops ? `${n.ops} op${n.ops > 1 ? 's' : ''}` : 'no ops'}</span>
                {n.status && <span class={`rn-chip s-${n.status}`} title={n.check}>Opus: {ST_LABEL[n.status]}</span>}
                {f && <span class={`rn-chip s-${f.status}`} title={f.comment}>Critic: {ST_LABEL[f.status] || f.status}</span>}
              </p>
              {n.plan && <p class="rn-plan">{n.plan}</p>}
            </li>
          );
        })}
      </ol>
    </details>
  );
}

/** The critic's score across rounds. */
function ScoreHistory({ rounds }: { rounds: Round[] }) {
  const pts = rounds.filter(r => r.critique).map(r => ({ n: r.n, s: r.critique!.score }));
  if (pts.length < 1) return null;
  const first = pts[0].s, last = pts[pts.length - 1].s;
  return (
    <div class="score-hist" aria-label="Critic score by round">
      <p class="sh-h"><b>Critic score</b><span>{pts.length > 1 ? `${first.toFixed(1)} → ${last.toFixed(1)} (${last - first >= 0 ? '+' : ''}${(last - first).toFixed(1)})` : `${last.toFixed(1)}/10`}</span></p>
      <div class="sh-bars">
        {pts.map(p => (
          <div class="sh-bar" title={`Round ${p.n}: ${p.s}/10`}>
            <i style={{ height: `${Math.max(4, p.s * 10)}%`, background: p.s >= 8.5 ? 'var(--ok, #4ade80)' : p.s >= 7 ? '#ffb357' : '#ff4d5e' }} />
            <span>R{p.n}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function RoundItem({ r, projectId, latest }: { r: Round; projectId: string; latest: boolean }) {
  const c = r.critique;
  return (
    <li class={`rnd k-${r.kind}`}>
      <span class="rnd-n" aria-hidden="true">{r.n}</span>
      <div class="rnd-b">
        <p class="rnd-h"><b>Round {r.n} · {r.kind === 'create' ? 'build' : 'revision'}</b><span>{timeAgo(r.at)}{r.applied !== undefined ? ` · ${r.applied} changes` : ''}</span></p>
        {(r.brief || r.fromCritic?.length) && (
          <p class="rnd-ask"><em>You:</em> {r.brief ? r.brief.slice(0, 220) + (r.brief.length > 220 ? '…' : '') : ''}{r.fromCritic?.length ? <span class="rnd-tag">{r.fromCritic.length} critic point{r.fromCritic.length > 1 ? 's' : ''}</span> : null}</p>
        )}
        {r.summary && <p class="rnd-say"><em>Opus:</em> {r.summary}</p>}
        {r.notes?.length ? <NotesList notes={r.notes} follow={c?.followUp} /> : null}
        {c && (
          <button type="button" class="rnd-crit" onClick={() => store.set({ critique: { projectId, round: r.n } })}>
            <ScoreRing score={c.score} size={40} />
            <span><b>Critic{c.prevScore !== undefined ? ` ${c.score - c.prevScore >= 0 ? '+' : ''}${(c.score - c.prevScore).toFixed(1)}` : ''}</b> {c.headline}</span>
            <span class="rnd-go" aria-hidden="true">{Icon.chevR}</span>
          </button>
        )}
        {r.snapshot && !latest && <button type="button" class="linkbtn rnd-restore" onClick={() => restore(r)}>Restore this version</button>}
      </div>
    </li>
  );
}

export function DirectorPanel() {
  const d = useStore(s => s.director);
  const pid = useStore(s => s.projectId);
  const rounds = useStore(s => s.rounds);
  const clips = useStore(s => s.project.clips.length);
  const ready = useStore(s => s.mediaOrder.filter(id => s.media[id]?.status === 'ready').length);
  const jobs = useStore(s => s.jobs);
  const job = pid ? activeJobFor(pid) : undefined;
  const recent = pid ? [...jobs].reverse().find(j => j.projectId === pid && (j.state === 'error' || j.state === 'interrupted' || j.state === 'stopped') && (!job)) : undefined;
  const last = rounds[rounds.length - 1];
  const next = last ? last.n + 1 : 1;
  const disabled = d.available !== 'yes';
  return (
    <div class="dir">
      <header class="dir-h">
        <div class="dir-title">
          <span class="dir-mark" aria-hidden="true">{Icon.spark}</span>
          <div>
            <h2>Opus Director</h2>
            <p class="dir-model" title="The model Opus calls are sent to">{d.lastModel ? `answered by ${d.lastModel}` : MODEL}</p>
          </div>
        </div>
      </header>

      {d.available === 'no' && <p class="note warn">{d.unavailableReason || 'Opus is not available in this view.'} You can still edit by hand.</p>}
      {d.available === 'checking' && <p class="note">Connecting to Opus…</p>}

      <div class="dir-log">
        {job && <JobCard job={job} />}
        {recent && <JobCard job={recent} />}
        {rounds.some(r => r.critique) && <ScoreHistory rounds={rounds} />}
        {rounds.length > 0 ? (
          <ol class="rounds">{[...rounds].reverse().map((r, i) => <RoundItem r={r} projectId={pid!} latest={i === 0} />)}</ol>
        ) : !job && (
          <div class="dir-empty">
            <p class="dir-empty-t">{clips ? 'This edit was made by hand.' : 'Opus builds the whole edit.'}</p>
            <ol>
              {clips ? (
                <>
                  <li>Send it to the critic for a harsh, specific review.</li>
                  <li>Write the next round's instructions (with the critic's points if you like).</li>
                  <li>Opus revises it in the background while you keep working.</li>
                </>
              ) : (
                <>
                  <li>Import your clips and music, or use the database.</li>
                  <li>Brief Opus: a preset and what makes this edit unique.</li>
                  <li>It builds in the background; the critic can review it when it's done.</li>
                </>
              )}
            </ol>
          </div>
        )}
        {d.messages.length > 0 && !rounds.length && (
          <details class="msg-issues"><summary>Earlier conversation ({d.messages.length})</summary>
            {d.messages.map(m => <div class={`msg m-${m.role}`}>{m.role === 'opus' && <span class="msg-who">Opus</span>}<p>{m.text}</p></div>)}
          </details>
        )}
      </div>

      <div class="dir-form">
        <div class="next-card">
          <p class="next-k">Next step</p>
          {job ? (
            <p class="next-t">{job.kind === 'critique' ? `The critic is reviewing round ${job.round}.` : `Round ${job.round} is running in the background.`} When it finishes you can {job.kind === 'critique' ? `write round ${job.round + 1} with its points` : 'send it to the critic or write the next round'}.</p>
          ) : clips || rounds.length ? (
            <>
              <p class="next-t">Round {next}: you write the instructions, Opus revises in the background.</p>
              <button type="button" class="btn btn-opus grow next-b" disabled={disabled || !!job} onClick={() => pid && openComposer(pid, 'revise')}>{Icon.pen}<span>Write the round {next} brief</span></button>
              <button type="button" class="btn btn-solid grow" disabled={disabled || !!job || !clips} onClick={() => pid && void sendToCritic(pid)}>{Icon.critic}<span>{last?.critique ? 'Ask the critic again' : 'Send to the critic'}</span></button>
            </>
          ) : (
            <>
              <p class="next-t">Round 1: brief Opus and it builds the edit from this project's media.</p>
              <button type="button" class="btn btn-opus grow next-b" disabled={disabled || !!job || !ready} title={!ready ? 'Import media first' : undefined} onClick={() => pid && openComposer(pid, 'create')}>{Icon.spark}<span>Build it with Opus</span></button>
            </>
          )}
        </div>
        <p class="dir-foot">Uses your Claude usage. Opus and the critic see contact sheets, rendered frames and sound analysis; they cannot hear audio. Jobs keep running while you edit other projects, but stop if the studio is closed.</p>
      </div>
    </div>
  );
}
