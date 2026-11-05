// Project actions shared by every "⋮" menu (recent projects, the project grid, the editor).
import { activeJobFor, enqueue } from '../../ai/jobs';
import { deleteProject, duplicateProject, getRecord, openProject, ProjectRecord, saveCurrent } from '../../state/projects';
import { store } from '../../state/store';
import { Icon } from '../controls';
import { MenuItem } from '../Menu';

export function openComposer(projectId: string, mode?: 'create' | 'revise') {
  void getRecord(projectId).then(rec => {
    if (!rec) return;
    store.set({ composer: { projectId, mode: mode || (rec.rounds?.length || rec.clips ? 'revise' : 'create') }, critique: null });
  });
}

export async function sendToCritic(projectId: string) {
  if (store.state.projectId === projectId) await saveCurrent();
  const rec = await getRecord(projectId);
  if (!rec) return;
  if (!rec.clips) { store.toast('There is no edit on this project yet.', 'error'); return; }
  const rs = rec.rounds || [];
  const last = rs[rs.length - 1];
  const job = await enqueue({ kind: 'critique', projectId, effort: last?.effort || store.state.director.effort, presetId: last?.presetId || rec.director?.presetId || rec.presetId || 'voidfx-dexter' });
  if (job) store.toast(`The critic is reviewing “${rec.name}” in the background.`, 'ok');
}

export async function exportProject(projectId: string) {
  if (await openProject(projectId)) store.set({ exportOpen: true });
}

export function projectMenu(rec: ProjectRecord, opts: { rename?: () => void; inEditor?: boolean } = {}): MenuItem[] {
  const rounds = rec.rounds || [];
  const last = rounds[rounds.length - 1];
  const busy = !!activeJobFor(rec.id);
  const items: MenuItem[] = [];
  if (!opts.inEditor) items.push({ label: 'Open in the editor', icon: Icon.play, run: () => void openProject(rec.id) });
  items.push(rounds.length || rec.clips
    ? { label: `Write the round ${(last?.n || 1) + (last ? 1 : 0)} brief`, icon: Icon.pen, run: () => openComposer(rec.id, 'revise'), disabled: busy, hint: busy ? 'Opus is already working on this project' : undefined }
    : { label: 'Build it with Opus', icon: Icon.spark, run: () => openComposer(rec.id, 'create'), disabled: busy });
  items.push({ label: 'Send to the critic', icon: Icon.critic, run: () => void sendToCritic(rec.id), disabled: !rec.clips || busy });
  if (last?.critique) items.push({ label: `Read the critique (${last.critique.score}/10)`, icon: Icon.diamond, run: () => store.set({ critique: { projectId: rec.id, round: last.n } }) });
  items.push({ label: 'Export video', icon: Icon.download, run: () => void exportProject(rec.id), disabled: !rec.clips, sep: true });
  if (opts.rename) items.push({ label: 'Rename', icon: Icon.edit, run: opts.rename });
  items.push({ label: 'Duplicate', icon: Icon.copy, run: () => void duplicateProject(rec.id).then(id => id && store.toast(`Duplicated “${rec.name}”.`, 'ok')) });
  items.push({ label: 'Delete', icon: Icon.trash, danger: true, confirm: 'Click again to delete', disabled: busy, hint: busy ? 'Stop the Opus job first' : undefined, run: () => void deleteProject(rec.id).then(() => store.toast(`Deleted “${rec.name}”.`)) });
  return items;
}
