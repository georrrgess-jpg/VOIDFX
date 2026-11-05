// The voidfx logo, exactly as supplied (never recoloured), and the mask of its 'o' counter used by
// the fly-through transition.
import LOGO_URL from '../../assets/voidfx_logo.webp';
import { LOGO_O } from './transitions';

export { LOGO_URL };

export interface LogoAssets { img: HTMLImageElement; mask: HTMLCanvasElement; w: number; h: number }
let assets: LogoAssets | null = null;
let loading: Promise<LogoAssets | null> | null = null;

export function logo(): LogoAssets | null { return assets; }

export function loadLogo(): Promise<LogoAssets | null> {
  if (loading) return loading;
  loading = new Promise(resolve => {
    const img = new Image();
    img.decoding = 'async';
    img.onload = () => {
      try {
        const w = img.naturalWidth, h = img.naturalHeight;
        // flood-fill the transparent counter of the 'o' at half resolution
        const mw = Math.round(w / 2), mh = Math.round(h / 2);
        const c = document.createElement('canvas');
        c.width = mw; c.height = mh;
        const g = c.getContext('2d', { willReadFrequently: true })!;
        g.drawImage(img, 0, 0, mw, mh);
        const src = g.getImageData(0, 0, mw, mh);
        const a = src.data;
        const seen = new Uint8Array(mw * mh);
        const sx = Math.round(LOGO_O[0] * mw), sy = Math.round(LOGO_O[1] * mh);
        const stack = [sy * mw + sx];
        seen[sy * mw + sx] = 1;
        while (stack.length) {
          const i = stack.pop()!;
          const x = i % mw, y = (i - x) / mw;
          const nb = [x > 0 ? i - 1 : -1, x < mw - 1 ? i + 1 : -1, y > 0 ? i - mw : -1, y < mh - 1 ? i + mw : -1];
          for (const n of nb) if (n >= 0 && !seen[n] && a[n * 4 + 3] < 128) { seen[n] = 1; stack.push(n); }
        }
        const out = g.createImageData(mw, mh);
        for (let i = 0; i < mw * mh; i++) {
          const v = seen[i] ? 255 : 0;
          out.data[i * 4] = out.data[i * 4 + 1] = out.data[i * 4 + 2] = 255;
          out.data[i * 4 + 3] = v;
        }
        g.clearRect(0, 0, mw, mh);
        g.putImageData(out, 0, 0);
        assets = { img, mask: c, w, h };
        resolve(assets);
      } catch (e) {
        console.warn('logo mask failed', e);
        resolve(null);
      }
    };
    img.onerror = () => resolve(null);
    img.src = LOGO_URL;
  });
  return loading;
}
