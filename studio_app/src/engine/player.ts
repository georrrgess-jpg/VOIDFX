// Real-time preview. Each media clip in view gets a pooled <video> element ("voice") that plays at
// the clip's speed; elements are routed through Web Audio for per-clip gain, fades and crossfades,
// and their frames are composited with WebGL every display frame.
import { runtime } from '../media/library';
import { store } from '../state/store';
import { Clip, MediaInfo, Project } from '../state/types';
import { clamp, projectDuration, speedAt } from '../state/util';
import { Compositor } from './compositor';
import { FrameVoice, SoundVoice } from './decodevoice';
import { Evaluation, evaluate, upcoming } from './evaluate';
import { onGraphicReady } from './custom';
import { drawLayers } from './drawlayers';
import { sfxBuffer } from './sfx';

interface Voice {
  el: HTMLVideoElement;
  mediaId: string;
  clipId: string | null;
  node: MediaElementAudioSourceNode | null;
  gain: GainNode | null;
  lastFix: number;
  seq: number;
}

const waitEvent = (el: HTMLMediaElement, ev: string, ms: number) => new Promise<void>(resolve => {
  const done = () => { el.removeEventListener(ev, done); clearTimeout(timer); resolve(); };
  const timer = setTimeout(done, ms);
  el.addEventListener(ev, done);
});

export class Player {
  comp: Compositor | null = null;
  private host: HTMLDivElement;
  private voices: Voice[] = [];
  /** WebCodecs fallbacks for files the media element cannot play, keyed by clip id. */
  private frames = new Map<string, FrameVoice>();
  private sounds = new Map<string, SoundVoice>();
  /** Generated sound effects currently playing, keyed by clip id. */
  private sfxNodes = new Map<string, { node: AudioBufferSourceNode; gain: GainNode }>();
  actx: AudioContext | null = null;
  master: GainNode | null = null;
  /** For the MediaRecorder export fallback. */
  streamDest: MediaStreamAudioDestinationNode | null = null;
  playing = false;
  time = 0;
  loop = false;
  muted = false;
  private raf = 0;
  private clock0 = 0;
  private time0 = 0;
  private stillBusy = false;
  private stillAgain = false;
  private lastStoreTime = 0;
  onFrame?: () => void;

  constructor() {
    this.host = document.createElement('div');
    this.host.setAttribute('aria-hidden', 'true');
    this.host.style.cssText = 'position:fixed;left:0;top:0;width:2px;height:2px;overflow:hidden;opacity:0;pointer-events:none;z-index:-1';
    document.body.appendChild(this.host);
    onGraphicReady(() => { if (!this.playing) this.requestStill(); });
  }

  attach(canvas: HTMLCanvasElement) {
    if (this.comp?.canvas === canvas) return;
    this.comp?.dispose();
    this.comp = new Compositor(canvas);
    this.requestStill();
  }

  setSize(w: number, h: number) {
    if (!this.comp) return;
    this.comp.resize(w, h);
    if (!this.playing) this.requestStill();
  }

  /** Create the audio graph. Must run inside a user gesture the first time. */
  ensureAudio() {
    if (!this.actx) {
      try {
        const AC = window.AudioContext || (window as any).webkitAudioContext;
        this.actx = new AC({ latencyHint: 'interactive' });
        this.master = this.actx.createGain();
        this.master.gain.value = this.muted ? 0 : 1;
        this.master.connect(this.actx.destination);
        this.streamDest = this.actx.createMediaStreamDestination();
        this.master.connect(this.streamDest);
        for (const v of this.voices) this.route(v);
      } catch {
        this.actx = null;
      }
    }
    if (this.actx?.state === 'suspended') this.actx.resume().catch(() => {});
  }

  setMuted(m: boolean) {
    this.muted = m;
    if (this.master && this.actx) this.master.gain.setTargetAtTime(m ? 0 : 1, this.actx.currentTime, 0.01);
  }

  private route(v: Voice) {
    if (!this.actx || v.node) return;
    try {
      v.node = this.actx.createMediaElementSource(v.el);
      v.gain = this.actx.createGain();
      v.gain.gain.value = 0;
      v.node.connect(v.gain).connect(this.master!);
      v.el.muted = false;
    } catch {
      v.node = null;
    }
  }

  private makeVoice(mediaId: string): Voice | null {
    const rt = runtime.get(mediaId);
    if (!rt) return null;
    const el = document.createElement('video');
    el.preload = 'auto';
    el.playsInline = true;
    el.muted = true;
    el.src = rt.url;
    this.host.appendChild(el);
    const v: Voice = { el, mediaId, clipId: null, node: null, gain: null, lastFix: 0, seq: 0 };
    // a slow seek (huge or software-decoded files) may land after still() stopped waiting: redraw then
    el.addEventListener('seeked', () => { if (!this.playing && v.clipId) this.requestStill(); });
    el.addEventListener('loadeddata', () => { if (!this.playing && v.clipId) this.requestStill(); });
    this.route(v);
    this.voices.push(v);
    return v;
  }

  private voiceFor(c: Clip): Voice | null {
    if (runtime.get(c.media!)?.elementOk === false) return null;
    let v = this.voices.find(x => x.clipId === c.id && x.mediaId === c.media);
    if (v) return v;
    v = this.voices.find(x => x.clipId === null && x.mediaId === c.media) || this.makeVoice(c.media!) || undefined;
    if (!v) return null;
    v.clipId = c.id;
    return v;
  }

  private elementOk(c: Clip) { return runtime.get(c.media!)?.elementOk !== false; }

  private frameVoice(c: Clip): FrameVoice | null {
    let f = this.frames.get(c.id);
    if (f) return f;
    const rt = runtime.get(c.media!);
    if (!rt?.video || !rt.canDecodeVideo) return null;
    const p = store.state.project;
    f = new FrameVoice(rt.video, Math.max(p.width, p.height));
    this.frames.set(c.id, f);
    return f;
  }

  private soundVoice(c: Clip): SoundVoice | null {
    let v = this.sounds.get(c.id);
    if (v) return v;
    const rt = runtime.get(c.media!);
    const m = store.state.media[c.media!];
    if (!this.actx || !this.master || !rt?.audio || !rt.canDecodeAudio || !m) return null;
    v = new SoundVoice(this.actx, this.master, rt.audio, m.duration);
    this.sounds.set(c.id, v);
    return v;
  }

  private release(keep: Set<string>) {
    for (const [id, f] of this.frames) if (!keep.has(id)) { f.dispose(); this.frames.delete(id); }
    for (const [id, v] of this.sounds) if (!keep.has(id)) { v.dispose(); this.sounds.delete(id); }
    for (const v of this.voices) {
      if (v.clipId && !keep.has(v.clipId)) {
        v.clipId = null;
        if (!v.el.paused) v.el.pause();
        if (v.gain && this.actx) v.gain.gain.setTargetAtTime(0, this.actx.currentTime, 0.01);
      }
    }
    // drop idle elements of media no longer in the library, keep a small pool otherwise
    const media = store.state.media;
    const idle = this.voices.filter(v => !v.clipId);
    let extra = idle.length - 6;
    for (const v of idle) {
      if (!media[v.mediaId] || !runtime.has(v.mediaId) || extra > 0) {
        this.destroyVoice(v);
        extra--;
      }
    }
  }

  private destroyVoice(v: Voice) {
    try { v.el.pause(); } catch { /* ignore */ }
    v.node?.disconnect();
    v.gain?.disconnect();
    v.el.removeAttribute('src');
    v.el.load();
    v.el.remove();
    this.voices = this.voices.filter(x => x !== v);
  }

  // ---------- transport ----------

  async play() {
    if (this.playing) return;
    this.ensureAudio();
    const p = store.state.project;
    const dur = projectDuration(p);
    if (dur <= 0) return;
    if (this.time >= dur - 1 / p.fps) this.time = 0;
    this.playing = true;
    store.set({ playing: true });
    // prime: seek the voices needed right now so playback starts clean
    const ev = evaluate(p, store.state.media, this.time);
    const waits: Promise<void>[] = [];
    for (const c of this.mediaClips(ev)) {
      if (!this.elementOk(c.clip)) { if (c.visual) waits.push(this.frameVoice(c.clip)?.still(c.srcTime) ?? Promise.resolve()); continue; }
      const v = this.voiceFor(c.clip);
      if (!v) continue;
      if (Math.abs(v.el.currentTime - c.srcTime) > 0.03 || v.el.readyState < 3) {
        v.el.currentTime = c.srcTime;
        waits.push(waitEvent(v.el, 'canplay', 1200));
      }
    }
    if (waits.length) await Promise.all(waits);
    if (!this.playing) return;
    this.clock0 = performance.now();
    this.time0 = this.time;
    cancelAnimationFrame(this.raf);
    const tick = () => {
      if (!this.playing) return;
      this.step();
      this.raf = requestAnimationFrame(tick);
    };
    this.raf = requestAnimationFrame(tick);
  }

  pause() {
    if (!this.playing) return;
    this.playing = false;
    cancelAnimationFrame(this.raf);
    for (const v of this.voices) {
      if (!v.el.paused) v.el.pause();
      if (v.gain && this.actx) v.gain.gain.setTargetAtTime(0, this.actx.currentTime, 0.008);
    }
    for (const f of this.frames.values()) f.stop();
    for (const v of this.sounds.values()) v.stop();
    this.stopSfx();
    store.set({ playing: false, time: this.time });
    this.requestStill();
  }

  toggle() { if (this.playing) this.pause(); else void this.play(); }

  seek(t: number) {
    const p = store.state.project;
    const dur = projectDuration(p);
    this.time = clamp(t, 0, Math.max(0, dur));
    if (this.playing) {
      this.clock0 = performance.now();
      this.time0 = this.time;
      for (const v of this.voices) v.lastFix = 0;
      for (const v of this.sounds.values()) v.stop();
      this.stopSfx();
    } else {
      this.requestStill();
    }
    store.set({ time: this.time });
  }

  private mediaClips(ev: Evaluation) {
    const out = new Map<string, { clip: Clip; srcTime: number; gain: number; visual: boolean }>();
    for (const L of ev.layers) if (L.kind === 'video') out.set(L.clip.id, { clip: L.clip, srcTime: L.srcTime, gain: 0, visual: true });
    for (const a of ev.audio) {
      const e = out.get(a.clip.id);
      if (e) e.gain = a.gain;
      else out.set(a.clip.id, { clip: a.clip, srcTime: a.srcTime, gain: a.gain, visual: false });
    }
    return [...out.values()];
  }

  /** One display frame while playing. */
  private step() {
    const now = performance.now();
    const s = store.state;
    const p = s.project;
    const dur = projectDuration(p);
    this.time = this.time0 + (now - this.clock0) / 1000;
    if (this.time >= dur) {
      if (this.loop && dur > 0) {
        this.time = 0;
        this.clock0 = now;
        this.time0 = 0;
      } else {
        this.time = dur;
        this.pause();
        return;
      }
    }
    const ev = evaluate(p, s.media, this.time);
    const active = this.mediaClips(ev);
    const ahead = upcoming(p, s.media, this.time, 1.2);
    const keep = new Set<string>([...active.map(a => a.clip.id), ...ahead.map(a => a.clip.id)]);
    this.release(keep);
    const actxNow = this.actx?.currentTime ?? 0;
    for (const a of active) {
      if (!this.elementOk(a.clip)) {
        if (a.visual) this.frameVoice(a.clip)?.tick(a.srcTime);
        const sp = speedAt(a.clip, clamp(this.time - a.clip.start, 0, a.clip.dur));
        if (a.gain > 0.0005) this.soundVoice(a.clip)?.tick(a.srcTime, a.gain, sp);
        else this.sounds.get(a.clip.id)?.tick(a.srcTime, 0, sp);
        continue;
      }
      const v = this.voiceFor(a.clip);
      if (!v) continue;
      const el = v.el;
      const speed = clamp(speedAt(a.clip, a.clip.dur ? clamp(this.time - a.clip.start, 0, a.clip.dur) : 0), 0.0625, 16);
      if (Math.abs(el.playbackRate - speed) > 1e-3) el.playbackRate = speed;
      (el as any).preservesPitch = a.clip.keepPitch !== false;
      const m = s.media[a.clip.media!];
      const atEnd = m && a.srcTime >= m.duration - 0.05;
      if (el.paused && !atEnd) {
        if (Math.abs(el.currentTime - a.srcTime) > 0.05) el.currentTime = a.srcTime;
        el.play().catch(() => {});
      } else if (!el.seeking && !atEnd) {
        const drift = el.currentTime - a.srcTime;
        if (Math.abs(drift) > 0.15 * Math.max(1, speed) && now - v.lastFix > 450) {
          el.currentTime = a.srcTime + 0.02 * speed;
          v.lastFix = now;
        }
      }
      if (v.gain && this.actx) v.gain.gain.setTargetAtTime(a.gain, actxNow, 0.012);
    }
    for (const u of ahead) {
      if (active.some(a => a.clip.id === u.clip.id)) continue;
      if (!this.elementOk(u.clip)) {
        if (!this.frames.has(u.clip.id) && u.clip.kind === 'video') void this.frameVoice(u.clip)?.still(u.srcTime);
        continue;
      }
      const v = this.voiceFor(u.clip);
      if (!v) continue;
      if (!v.el.paused) v.el.pause();
      if (!v.el.seeking && Math.abs(v.el.currentTime - u.srcTime) > 0.04) v.el.currentTime = u.srcTime;
      if (v.gain && this.actx) v.gain.gain.setTargetAtTime(0, actxNow, 0.01);
    }
    this.tickSfx(ev);
    this.draw(ev, p, s.media);
    if (now - this.lastStoreTime > 33) {
      this.lastStoreTime = now;
      store.set({ time: this.time });
    }
  }

  private tickSfx(ev: Evaluation) {
    const actx = this.actx, master = this.master;
    if (!actx || !master) return;
    const live = new Set<string>();
    for (const x of ev.sfx) {
      live.add(x.clip.id);
      let n = this.sfxNodes.get(x.clip.id);
      if (!n && x.lt >= 0 && x.lt < x.clip.dur - 0.02 && x.clip.sfx) {
        const buf = sfxBuffer(actx, x.clip.sfx);
        const offset = (x.clip.in ?? 0) + x.lt;
        if (offset < buf.duration) {
          const node = actx.createBufferSource();
          node.buffer = buf;
          const gain = actx.createGain();
          gain.gain.value = x.gain;
          node.connect(gain).connect(master);
          node.start(actx.currentTime, offset, Math.max(0.01, x.clip.dur - x.lt));
          n = { node, gain };
          this.sfxNodes.set(x.clip.id, n);
        }
      }
      if (n) n.gain.gain.setTargetAtTime(x.gain, actx.currentTime, 0.01);
    }
    for (const [id, n] of this.sfxNodes) if (!live.has(id)) { try { n.node.stop(); } catch { /* done */ } n.gain.disconnect(); this.sfxNodes.delete(id); }
  }

  private stopSfx() {
    for (const n of this.sfxNodes.values()) { try { n.node.stop(); } catch { /* done */ } n.gain.disconnect(); }
    this.sfxNodes.clear();
  }

  /** Render the current time exactly (paused): seek every visible clip and draw when frames land. */
  requestStill() {
    if (this.playing) return;
    if (this.stillBusy) { this.stillAgain = true; return; }
    this.stillBusy = true;
    void this.still().finally(() => {
      this.stillBusy = false;
      if (this.stillAgain) { this.stillAgain = false; this.requestStill(); }
    });
  }

  private async still() {
    if (!this.comp) return;
    const s = store.state;
    const p = s.project;
    const ev = evaluate(p, s.media, this.time, { audio: false });
    const keep = new Set<string>();
    const waits: Promise<void>[] = [];
    for (const L of ev.layers) {
      if (L.kind !== 'video') continue;
      keep.add(L.clip.id);
      if (!this.elementOk(L.clip)) {
        const f = this.frameVoice(L.clip);
        if (f) waits.push(f.still(L.srcTime));
        continue;
      }
      const v = this.voiceFor(L.clip);
      if (!v) continue;
      if (!v.el.paused) v.el.pause();
      const tol = 0.5 / Math.max(24, p.fps);
      if (Math.abs(v.el.currentTime - L.srcTime) > tol || v.el.readyState < 2) {
        v.el.currentTime = L.srcTime;
        waits.push(waitEvent(v.el, 'seeked', 2500));
      }
    }
    // keep upcoming voices warm so pressing play is instant
    for (const u of upcoming(p, s.media, this.time, 1.2)) keep.add(u.clip.id);
    this.release(keep);
    this.draw(ev, p, s.media);
    if (waits.length) {
      await Promise.all(waits);
      if (this.playing) return;
      // one more frame: the decoded picture is available just after 'seeked'
      await new Promise(r => requestAnimationFrame(() => r(null)));
      const s2 = store.state;
      this.draw(evaluate(s2.project, s2.media, this.time, { audio: false }), s2.project, s2.media);
    }
  }

  private draw(ev: Evaluation, p: Project, media: Record<string, MediaInfo>) {
    const comp = this.comp;
    if (!comp) return;
    drawLayers(comp, p, media, ev.layers, L => {
      if (L.kind !== 'video') return null;
      const fv = this.frames.get(L.clip.id);
      if (fv) return fv.version > 0 ? { src: fv.canvas as any, w: fv.w, h: fv.h, version: `f${fv.version}` } : null;
      const v = this.voices.find(x => x.clipId === L.clip.id);
      const el = v?.el;
      // the element already applies rotation metadata, so its frame is display-oriented
      if (!v || !el || el.readyState < 2 || !el.videoWidth) return null;
      v.seq++;
      return { src: el, w: el.videoWidth, h: el.videoHeight, version: `${v.seq}` };
    }, 'p');
    if (Math.random() < 0.02) comp.gc(600);
    this.onFrame?.();
  }

  /** Quad of a clip in the last drawn frame, in canvas pixels. */
  quadOf(clipId: string) { return this.comp?.quads.get(clipId) ?? null; }

  /** Stop everything and free elements (e.g. when the library is cleared). */
  reset() {
    this.pause();
    for (const v of [...this.voices]) this.destroyVoice(v);
    this.release(new Set());
  }
}

export const player = new Player();
