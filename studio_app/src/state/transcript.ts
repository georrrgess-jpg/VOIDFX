// Transcripts for long-form edits: SRT, WebVTT, or text with timestamps ("[01:23] words", "1:23 words",
// "00:01:23,450 --> ..."). Opus cannot hear the video, so this is how it reads what is said and when.
export interface Segment { t: number; end?: number; text: string }
export interface Transcript { timed: boolean; segments: Segment[]; words: number }

const clock = (s: string): number | null => {
  const m = s.trim().match(/^(?:(\d{1,2}):)?(\d{1,2}):(\d{2})(?:[.,](\d{1,3}))?$/);
  if (!m) return null;
  return (m[1] ? +m[1] * 3600 : 0) + +m[2] * 60 + +m[3] + (m[4] ? +m[4].padEnd(3, '0') / 1000 : 0);
};

export function parseTranscript(raw: string): Transcript {
  const text = (raw || '').replace(/\r/g, '').replace(/^WEBVTT[^\n]*\n/, '');
  const segs: Segment[] = [];
  // SRT / VTT cues
  const cue = /(\d{1,2}:\d{2}(?::\d{2})?[.,]\d{1,3})\s*-->\s*(\d{1,2}:\d{2}(?::\d{2})?[.,]\d{1,3})[^\n]*\n([\s\S]*?)(?=\n\s*\n|$)/g;
  let m: RegExpExecArray | null;
  while ((m = cue.exec(text))) {
    const a = clock(m[1]), b = clock(m[2]);
    const body = m[3].replace(/<[^>]+>/g, '').replace(/\{[^}]+\}/g, '').replace(/\n/g, ' ').replace(/\s+/g, ' ').trim();
    if (a !== null && body) segs.push({ t: a, end: b ?? undefined, text: body });
  }
  if (!segs.length) {
    // "[mm:ss] words" or "mm:ss words" lines
    for (const line of text.split('\n')) {
      const l = line.trim();
      const t = l.match(/^\[?((?:\d{1,2}:)?\d{1,2}:\d{2}(?:[.,]\d{1,3})?)\]?\s*[-–:]?\s*(.+)$/);
      if (t) { const s = clock(t[1]); if (s !== null && t[2].trim()) segs.push({ t: s, text: t[2].trim() }); }
    }
  }
  if (segs.length >= 2) {
    segs.sort((a, b) => a.t - b.t);
    for (let i = 0; i < segs.length; i++) if (segs[i].end === undefined) segs[i].end = segs[i + 1]?.t ?? segs[i].t + 4;
    return { timed: true, segments: segs, words: segs.reduce((n, s) => n + s.text.split(/\s+/).length, 0) };
  }
  const plain = text.split(/\n{2,}|\n/).map(s => s.trim()).filter(Boolean);
  return { timed: false, segments: plain.map(s => ({ t: 0, text: s })), words: plain.join(' ').split(/\s+/).filter(Boolean).length };
}

/** The transcript as Opus reads it: one line per cue with its start time, compact. */
export function transcriptText(t: Transcript, maxChars = 140000): string {
  let out = '';
  for (const s of t.segments) {
    const line = t.timed ? `[${s.t.toFixed(1)}] ${s.text}\n` : `${s.text}\n`;
    if (out.length + line.length > maxChars) { out += '… (the rest is cut for length)\n'; break; }
    out += line;
  }
  return out.trim();
}
