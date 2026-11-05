// Draws one evaluated frame. Shared by the preview, export, Opus reviews and the effect previews,
// so every surface renders identically.
import { runtime } from '../media/library';
import { MediaInfo, Project } from '../state/types';
import { Compositor, fitSize } from './compositor';
import { VisualLayer } from './evaluate';
import { renderText } from './text';

export interface FrameRef { src: TexImageSource | null; w: number; h: number; version: unknown }

export function drawLayers(
  comp: Compositor, p: Project, media: Record<string, MediaInfo>, layers: VisualLayer[],
  frameOf: (L: VisualLayer) => FrameRef | null | undefined, slot: string,
) {
  const W = comp.width, H = comp.height;
  comp.begin(p.background);
  for (const L of layers) {
    const c = L.clip;
    if (L.kind === 'logo') { comp.drawLogo(L.fx); continue; }
    if (L.kind === 'text') {
      const r = renderText(c, L.lt, W, H, slot);
      if (!r) continue;
      comp.draw({
        key: c.id, version: r.version, source: r.canvas as any, srcW: r.w, srcH: r.h, srcRot: 0, baseW: r.w, baseH: r.h,
        transform: L.transform, fx: { ...L.fx, dx: L.fx.dx + r.dx, opacity: L.fx.opacity * r.opacity, scale: L.fx.scale * r.scale }, premultiplied: true,
      });
      continue;
    }
    if (L.kind === 'image') {
      const img = frameOf(L) || (c.media ? (() => { const b = runtime.get(c.media!)?.image; return b ? { src: b, w: b.width, h: b.height, version: c.media } : null; })() : null);
      if (!img?.src) continue;
      const [bw, bh] = fitSize(img.w, img.h, W, H, c.fit || 'cover');
      comp.draw({ key: c.id, version: img.version, source: img.src, srcW: img.w, srcH: img.h, srcRot: 0, baseW: bw, baseH: bh, transform: L.transform, fx: L.fx, color: L.color });
      continue;
    }
    const m = c.media ? media[c.media] : undefined;
    if (!m) continue;
    const f = frameOf(L);
    const sw = f?.w || m.width || 16, sh = f?.h || m.height || 9;
    const [bw, bh] = fitSize(sw, sh, W, H, c.fit || 'cover');
    comp.draw({ key: c.id, version: f?.src ? f.version : undefined, source: f?.src ?? null, srcW: sw, srcH: sh, srcRot: 0, baseW: bw, baseH: bh, transform: L.transform, fx: L.fx, color: L.color });
  }
}
