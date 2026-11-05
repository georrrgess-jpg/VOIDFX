import { useState } from 'preact/hooks';
import { HOUSE_RULES } from '../../ai/knowledge';
import { saveKnowledge } from '../../state/catalog';
import { useStore } from '../../state/store';
import { SectionHead } from './common';

export function RulesSection() {
  const knowledge = useStore(s => s.director.knowledge);
  const [draft, setDraft] = useState(knowledge);
  const blocks = HOUSE_RULES.split('\n\n').slice(1).map(b => {
    const [head, ...rest] = b.split('\n');
    return { head, items: rest.map(r => r.replace(/^- /, '')) };
  });
  return (
    <div class="hs">
      <SectionHead eyebrow="House rules" title="What Opus knows about your style" text="Distilled from your handbook, preferences, edit history and the two studio specs, and translated into this studio's tools. Presets that use the house rules send all of this with every edit." />
      <div class="rules">
        {blocks.map((b, i) => (
          <section class="rule glass" style={{ '--i': i } as any}>
            <h2>{b.head}</h2>
            <ul>{b.items.map(t => <li>{t}</li>)}</ul>
          </section>
        ))}
      </div>
      <section class="glass rules-own">
        <h2>Your additions</h2>
        <p class="muted">Anything else Opus should always follow. Sent with every request, with or without the house rules.</p>
        <textarea id="knowledge" class="ta big" rows={6} value={draft} onInput={e => setDraft((e.target as HTMLTextAreaElement).value)} placeholder="e.g. Never use the S8 finale footage. Prefer the Trinity bathtub scene for drops." />
        <div class="row-end"><button type="button" class="cta cta-ice" disabled={draft === knowledge} onClick={() => void saveKnowledge(draft)}>Save</button></div>
      </section>
    </div>
  );
}
