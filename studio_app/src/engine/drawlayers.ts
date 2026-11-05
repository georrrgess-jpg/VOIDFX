// Draws one evaluated frame. Shared by the preview, export, Opus reviews and the effect previews,
// so every surface renders identically.
import { runtime } from '../media/library';
import { MediaInfo, Project } from '../state/types';
import { Compositor, fitSize } from './compositor';
import { VisualLayer } from './evaluate';
import { renderText } from './text';
import { graphicCanvas, musicAt, rasterWidthFor, svgSize } from './custom';

const seedOf = (id: string) => { let h = 0; for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) % 9973; return h / 97.3; };

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
    if (L.kind === 'graphic') {
      const gw = (c.gw ?? 0.6) * W;
      const cv = c.svg ? graphicCanvas(c, rasterWidthFor(c, W)) : null;
      if (!cv) continue;
      const { vbW, vbH } = svgSize(c.svg!);
      const bw = gw, bh = (gw * vbH) / vbW;
      const version = `${c.svg!.length}:${cv.width}`;
      if ((c.glow ?? 0) > 0.01) {
        comp.draw({ key: `${c.id}#glow`, version, source: cv, srcW: cv.width, srcH: cv.height, srcRot: 0, baseW: bw, baseH: bh, transform: { ...L.transform, scale: L.transform.scale * 1.03 },
          fx: { ...L.fx, blur: Math.min(1, 0.25 + c.glow! * 0.6), opacity: L.fx.opacity * Math.min(1, c.glow! * 1.1) }, premultiplied: true, blend: 'add' });
      }
      comp.draw({ key: c.id, version, source: cv, srcW: cv.width, srcH: cv.height, srcRot: 0, baseW: bw, baseH: bh, transform: L.transform, fx: L.fx, color: L.color, premultiplied: true, blend: c.blend || 'normal' });
      continue;
    }
    if (L.kind === 'shader') {
      if (!c.code) continue;
      const t = c.start + L.lt;
      const mu = musicAt(p, media, t);
      comp.drawShader(c.code, c.blend || 'normal', {
        t: L.lt, p: Math.max(0, Math.min(1, L.lt / Math.max(1e-3, c.dur))), dur: c.dur, time: t, beat: mu.beat, beatAge: mu.beatAge, energy: mu.energy,
        opacity: L.transform.opacity * L.fx.opacity, scale: L.transform.scale, rot: (L.transform.rotation * Math.PI) / 180,
        pos: [0.5 + L.transform.x, 0.5 + L.transform.y], seed: seedOf(c.id),
      });
      continue;
    }
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
