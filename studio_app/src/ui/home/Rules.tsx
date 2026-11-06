import { useState } from 'preact/hooks';
import { HOUSE_RULES } from '../../ai/knowledge';
import { KNOWLEDGE_SOURCES } from '../../ai/playbook';
import { PACKS, SONGS } from '../../ai/sources';
import { FX_LIBRARY } from '../../engine/fxlib';
import { TRANSITIONS } from '../../state/types';
import { clearLessons, saveKnowledge } from '../../state/catalog';
import { useStore } from '../../state/store';
import { SectionHead } from './common';

export function RulesSection() {
  const knowledge = useStore(s => s.director.knowledge);
  const lessons = useStore(s => s.director.lessons);
  const [draft, setDraft] = useState(knowledge);
  const blocks = HOUSE_RULES.split('\n\n').slice(1).map(b => {
    const [head, ...rest] = b.split('\n');
    return { head, items: rest.map(r => r.replace(/^- /, '')) };
  });
  return (
    <div class="hs">
      <SectionHead eyebrow="House rules" title="What Opus knows about your style" text="Distilled from your handbook, preferences, edit history and the two studio specs, and translated into this studio's tools. Presets that use the house rules send all of this with every edit." />
      <section class="glass rules-src">
        <h2>Where it comes from</h2>
        <p class="muted">Every editing file you provided, read and turned into what Opus works from on each call: the house rules below, a playbook of every approved set piece built from studio operations, beat-by-beat worked examples of the approved edits, the critic's canon, and notes on {PACKS.length} scene packs and {SONGS.length} songs (recognised automatically when you use them, with their proven shots and timecodes). The studio itself has {FX_LIBRARY.filter(d => d.group === 'look').length} looks, {FX_LIBRARY.length - FX_LIBRARY.filter(d => d.group === 'look').length} effects and {TRANSITIONS.length} transitions for Opus to use by name.</p>
        <ul class="src-list">
          {KNOWLEDGE_SOURCES.map(k => <li><b>{k.name}</b><span>{k.what}</span></li>)}
        </ul>
      </section>
      <div class="rules">
        {blocks.map((b, i) => (
          <section class="rule glass" style={{ '--i': i } as any}>
            <h2>{b.head}</h2>
            <ul>{b.items.map(t => <li>{t}</li>)}</ul>
          </section>
        ))}
      </div>
      <section class="glass rules-src">
        <h2>Lessons from the critic</h2>
        <p class="muted">Every critique's critical and major findings are remembered here and given to Opus with every direction and review, so an edit does not repeat what the critic marked down before. {lessons.length ? `${lessons.length} remembered (the latest per area are sent).` : 'None yet: they appear after the first critique.'}</p>
        {lessons.length > 0 && (
          <>
            <ul class="src-list">
              {lessons.slice(0, 12).map(l => <li><b>{l.area}{l.severity === 'critical' ? ' · critical' : ''}</b><span>{l.problem.length > 200 ? `${l.problem.slice(0, 200)}…` : l.problem}</span></li>)}
            </ul>
            <div class="row-end"><button type="button" class="cta" onClick={() => void clearLessons()}>Forget the lessons</button></div>
          </>
        )}
      </section>
      <section class="glass rules-own">
        <h2>Your additions</h2>
        <p class="muted">Anything else Opus should always follow. Sent with every request, with or without the house rules.</p>
        <textarea id="knowledge" class="ta big" rows={6} value={draft} onInput={e => setDraft((e.target as HTMLTextAreaElement).value)} placeholder="e.g. Never use the S8 finale footage. Prefer the Trinity bathtub scene for drops." />
        <div class="row-end"><button type="button" class="cta cta-ice" disabled={draft === knowledge} onClick={() => void saveKnowledge(draft)}>Save</button></div>
      </section>
    </div>
  );
}
