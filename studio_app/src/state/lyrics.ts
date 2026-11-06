// Song lyrics the owner pastes: synced LRC ("[01:23.45] line", optional "<01:23.60>" word times) or
// plain text. Timed lines let the studio put each caption exactly on its sung time.
import { LyricLine, Lyrics } from './types';

const TAG = /\[(\d{1,3}):(\d{1,2}(?:[.:]\d{1,3})?)\]/g;
const WORD_TAG = /<(\d{1,3}):(\d{1,2}(?:[.:]\d{1,3})?)>/g;
const META = /^\[(ar|ti|al|au|by|re|ve|length|offset|la|id|#)\s*:[^\]]*\]\s*$/i;

const secs = (m: string, s: string) => +m * 60 + parseFloat(s.replace(':', '.'));
const clean = (s: string) => s.replace(WORD_TAG, ' ').replace(/\s+/g, ' ').trim();

/** Parse pasted lyrics. Timed when at least two lines carry a time. */
export function parseLyrics(raw: string): Lyrics {
  const text = (raw || '').replace(/\r/g, '');
  const off = text.match(/\[offset\s*:\s*([+-]?\d+)\s*\]/i);
  const shift = off ? -(+off[1]) / 1000 : 0;
  const timed: LyricLine[] = [];
  const plain: string[] = [];
  for (const rawLine of text.split('\n')) {
    const line = rawLine.trim();
    if (!line || META.test(line)) continue;
    const times: number[] = [];
    let rest = line;
    // leading [mm:ss.xx] tags (one line can repeat at several times)
    for (;;) {
      const m = rest.match(/^\[(\d{1,3}):(\d{1,2}(?:[.:]\d{1,3})?)\]\s*/);
      if (!m) break;
      times.push(secs(m[1], m[2]) + shift);
      rest = rest.slice(m[0].length);
    }
    // a bare "1:23.4 words" at the start of a line
    if (!times.length) {
      const m = rest.match(/^(\d{1,2}):(\d{2}(?:\.\d{1,3})?)\s+(.+)$/);
      if (m) { times.push(secs(m[1], m[2]) + shift); rest = m[3]; }
    }
    rest = rest.replace(TAG, '').trim();
    if (!times.length) { const c = clean(rest); if (c) plain.push(c); continue; }
    // enhanced LRC: <mm:ss.xx> before each word
    let words: number[] | undefined;
    if (WORD_TAG.test(rest)) {
      WORD_TAG.lastIndex = 0;
      const parts = rest.split(/(<\d{1,3}:\d{1,2}(?:[.:]\d{1,3})?>)/).filter(Boolean);
      const ws: number[] = [];
      let pending: number | null = null;
      for (const part of parts) {
        const m = part.match(/^<(\d{1,3}):(\d{1,2}(?:[.:]\d{1,3})?)>$/);
        if (m) { pending = secs(m[1], m[2]) + shift; continue; }
        const toks = part.trim().split(/\s+/).filter(Boolean);
        toks.forEach((_, k) => ws.push(k === 0 && pending !== null ? pending : NaN));
        pending = null;
      }
      if (ws.some(x => !Number.isNaN(x))) words = ws;
    }
    const body = clean(rest);
    for (const t of times) timed.push({ t: Math.max(0, +t.toFixed(3)), text: body, ...(words && times.length === 1 ? { words: fillWords(words, t) } : {}) });
  }
  timed.sort((a, b) => a.t - b.t);
  // an empty timed line ends the line before it (instrumental gap)
  const lines: LyricLine[] = [];
  for (let i = 0; i < timed.length; i++) {
    const l = timed[i];
    if (!l.text) { if (lines.length && lines[lines.length - 1].end === undefined) lines[lines.length - 1].end = l.t; continue; }
    lines.push(l);
  }
  if (lines.length >= 2) return { timed: true, lines, raw: text.slice(0, 20000) };
  return { timed: false, lines: plain.map(t => ({ t: NaN, text: t })), raw: text.slice(0, 20000) };
}

function fillWords(ws: number[], t0: number): number[] {
  const out = [...ws];
  if (Number.isNaN(out[0])) out[0] = t0;
  for (let i = 1; i < out.length; i++) if (Number.isNaN(out[i])) out[i] = out[i - 1] + 0.12;
  return out.map(x => +x.toFixed(3));
}

/** Split a lyric line over two caption lines, the second (drawn larger) a little shorter. */
export function twoLines(text: string): string {
  const w = text.trim().split(/\s+/).filter(Boolean);
  if (w.length < 3) return w.join(' ');
  let best = 1, bestErr = Infinity;
  for (let k = 1; k < w.length; k++) {
    const a = w.slice(0, k).join(' ').length, b = w.slice(k).join(' ').length;
    const err = Math.abs(a - b * 1.3);
    if (err < bestErr) { bestErr = err; best = k; }
  }
  return `${w.slice(0, best).join(' ')}\n${w.slice(best).join(' ')}`;
}

/** The numbered lyric list Opus reads (song times, before the song is placed). */
export function lyricsText(l: Lyrics): string {
  if (!l.timed) return l.lines.map(x => x.text).join('\n');
  return l.lines.map((x, i) => {
    const next = l.lines[i + 1];
    const end = x.end ?? (next ? next.t : x.t + 4);
    return `L${i + 1} ${x.t.toFixed(2)}-${end.toFixed(2)} "${x.text}"${x.words ? ' (word times)' : ''}`;
  }).join('\n');
}
