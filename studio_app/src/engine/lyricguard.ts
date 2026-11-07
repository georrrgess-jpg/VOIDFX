// The lyric guard: no caption may put words in the song's mouth. After every pass Opus makes, each text
// clip is checked against the owner's lyrics: a sung caption must be a real line, word for word, on
// the time it is sung in this part of the song; words that are not in the lyrics are removed; with no
// lyrics supplied, nothing longer than a two-word title may claim to be sung.
import { Clip, MediaInfo, Project } from '../state/types';
import { clipEnd, projectDuration } from '../state/util';
import { twoLines } from '../state/lyrics';

const norm = (s: string) => s.toLowerCase().replace(/\*/g, '').replace(/[’']/g, '').replace(/[^\p{L}\p{N}\s]/gu, ' ').split(/\s+/).filter(Boolean);

function musicBed(p: Project, media: Record<string, MediaInfo>): Clip | undefined {
  const audioTracks = new Set(p.tracks.filter(t => t.kind === 'audio').map(t => t.id));
  return p.clips.filter(c => (c.kind === 'audio' || (c.kind === 'video' && audioTracks.has(c.track))) && c.media && media[c.media]?.analysis).sort((a, b) => b.dur - a.dur)[0];
}

/** Spans where someone speaks: audio clips other than the song, and shots whose own sound is turned up. */
function dialogueSpans(p: Project, bed?: Clip): [number, number][] {
  return p.clips.filter(c => c !== bed && !c.muted && ((c.kind === 'audio' && c.media) || (c.kind === 'video' && (c.volume ?? 0) >= 0.6 && c.muted === false)))
    .map(c => [c.start, clipEnd(c)] as [number, number]);
}

export interface LyricLineAt { i: number; text: string; words: string[]; t0: number; t1: number }

/** The owner's timed lyric lines that are sung inside the edit, in timeline time. */
export function linesOnTimeline(p: Project, media: Record<string, MediaInfo>): LyricLineAt[] {
  const L = p.lyrics, bed = musicBed(p, media);
  if (!L?.timed || !bed) return [];
  const sp = bed.speed ?? 1, mIn = bed.in ?? 0, end = Math.min(clipEnd(bed), projectDuration(p));
  const toTl = (s: number) => bed.start + (s - mIn) / sp;
  const out: LyricLineAt[] = [];
  L.lines.forEach((l, k) => {
    const t0 = toTl(l.t);
    const next = L.lines[k + 1] ? toTl(L.lines[k + 1].t) : t0 + 4;
    const t1 = l.end !== undefined ? toTl(l.end) : Math.min(next, t0 + 5);
    if (t0 >= bed.start - 0.05 && t0 < end - 0.2 && l.text.trim()) out.push({ i: k + 1, text: l.text, words: norm(l.text), t0, t1 });
  });
  return out;
}

/** `only`: check just these clips (the ones Opus wrote or changed in this pass; the owner's own text is left alone). */
export function lyricGuard(p: Project, media: Record<string, MediaInfo>, only?: Set<string>): string[] {
  const notes: string[] = [];
  const texts = p.clips.filter(c => c.kind === 'text' && c.text?.trim() && (!only || only.has(c.id)));
  if (!texts.length) return notes;
  const bed = musicBed(p, media);
  const talk = dialogueSpans(p, bed);
  const overTalk = (c: Clip) => talk.some(([a, b]) => c.start < b - 0.1 && clipEnd(c) > a + 0.1);
  const L = p.lyrics?.lines.length ? p.lyrics : undefined;
  const allWords = new Set((L?.lines || []).flatMap(l => norm(l.text)));
  const onTl = linesOnTimeline(p, media);
  const removed: string[] = [], fixed: string[] = [], moved: string[] = [], offAir: string[] = [];
  for (const c of texts) {
    if (overTalk(c)) continue; // the character's own words
    const w = norm(c.text!);
    if (!w.length) continue;
    if (!L) {
      // nothing to check against: only a short title may stand
      if (w.length >= 3) removed.push(c.id);
      continue;
    }
    const inLyrics = w.filter(x => allWords.has(x)).length / w.length;
    if (w.length >= 3 && inLyrics < 0.6) { removed.push(c.id); continue; }
    if (w.length <= 2) {
      // a title on a sung word: it belongs where that word is sung in this part of the song
      if (inLyrics < 1 || !onTl.length) continue;
      const near = onTl.filter(l => w.every(x => l.words.includes(x))).sort((a, b) => Math.abs(a.t0 - c.start) - Math.abs(b.t0 - c.start))[0];
      if (!near) offAir.push(c.id);
      continue;
    }
    // a sung caption: the real line, on its time
    const cands = (onTl.length ? onTl : []).map(l => ({ l, score: w.filter(x => l.words.includes(x)).length / Math.max(w.length, l.words.length * 0.5) }))
      .filter(x => x.score >= 0.5).sort((a, b) => b.score - a.score || Math.abs(a.l.t0 - c.start) - Math.abs(b.l.t0 - c.start));
    if (!p.lyrics!.timed) {
      // untimed lyrics: the words must be exact; there is no time to check
      const line = L.lines.map(l => ({ l, s: w.filter(x => norm(l.text).includes(x)).length / w.length })).sort((a, b) => b.s - a.s)[0];
      if (line && w.some(x => !norm(line.l.text).includes(x))) { c.text = twoLines(line.l.text); delete c.words; fixed.push(c.id); }
      continue;
    }
    if (!cands.length) { removed.push(c.id); continue; } // its line is not sung inside the edit
    const { l } = cands.reduce((best, x) => (Math.abs(x.l.t0 - c.start) < Math.abs(best.l.t0 - c.start) && x.score >= best.score - 0.15 ? x : best), cands[0]);
    if (w.join(' ') !== l.words.join(' ')) {
      const emph = (c.text!.match(/\*([^*]+)\*/g) || []).map(x => x.slice(1, -1).toLowerCase());
      c.text = twoLines(l.text).split(/(\s+)/).map(tok => (emph.includes(tok.toLowerCase().replace(/[^\p{L}\p{N}']/gu, '')) ? `*${tok}*` : tok)).join('');
      delete c.words;
      fixed.push(c.id);
    }
    if (Math.abs(c.start - l.t0) > 0.3) {
      c.start = Math.max(0, +(l.t0 - 0.06).toFixed(4));
      c.dur = +Math.max(0.6, Math.min(l.t1 - l.t0 + 0.15, 4)).toFixed(4);
      delete c.words;
      moved.push(c.id);
    }
  }
  if (removed.length) {
    p.clips = p.clips.filter(c => !removed.includes(c.id));
    notes.push(L
      ? `the studio removed ${removed.length} caption${removed.length > 1 ? 's' : ''} (${removed.join(', ')}) whose words are not in the owner's lyrics or are not sung in this part of the song: never write sung words from memory; caption with the "lyrics" operation`
      : `the studio removed ${removed.length} caption${removed.length > 1 ? 's' : ''} (${removed.join(', ')}): no lyrics were supplied, so sung words cannot be checked; use titles of one or two words, or the character's own dialogue`);
  }
  if (fixed.length) notes.push(`the studio corrected the wording of ${fixed.join(', ')} to the owner's lyrics, word for word`);
  if (moved.length) notes.push(`the studio moved ${moved.join(', ')} onto the time the line is sung`);
  if (offAir.length) notes.push(`${offAir.join(', ')}: the title's word is not sung near it in this part of the song (a sung word on screen where nobody sings it reads as a mistake); move it onto the word or change it`);
  return notes;
}
