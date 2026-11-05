// Runs the automated checkpoint for the open project and keeps the result in the store.
import { measureLoopSeam } from '../engine/exporter';
import { runChecks } from '../engine/qc';
import { getPreset } from '../state/catalog';
import { store } from '../state/store';

export async function refreshChecks(opts: { seam?: boolean } = {}) {
  const s = store.state;
  const preset = await getPreset(s.director.presetId);
  let seam = s.seam;
  if (opts.seam) seam = await measureLoopSeam(s.project).catch(() => null);
  const checks = runChecks(s.project, s.media, { houseRules: preset.houseRules, duration: preset.duration, fps: preset.fps, seam });
  store.set({ checks, seam });
  return checks;
}
