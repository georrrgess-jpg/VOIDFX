// Preview fallback for files the browser's media element cannot play (e.g. 4:4:4 or 10-bit H.264,
// some HEVC): frames come from WebCodecs (Mediabunny) and sound from decoded Web Audio buffers.
import { AudioBufferSink, InputAudioTrack, InputVideoTrack, VideoSample, VideoSampleSink } from 'mediabunny';

const nextFrame = () => new Promise(r => requestAnimationFrame(() => r(null)));

export class FrameVoice {
  readonly canvas: HTMLCanvasElement | OffscreenCanvas;
  private ctx: CanvasRenderingContext2D;
  private sink: VideoSampleSink;
  version = 0;
  w = 16;
  h = 9;
  private iter: AsyncGenerator<VideoSample, void, unknown> | null = null;
  private next: VideoSample | null = null;
  private ended = false;
  private target = 0;
  private lastTs = -1;
  private pumping = false;
  private active = false;
  private stillGen = 0;

  constructor(track: InputVideoTrack, private maxLong = 1920) {
    this.sink = new VideoSampleSink(track);
    this.canvas = typeof OffscreenCanvas !== 'undefined' ? new OffscreenCanvas(16, 9) : document.createElement('canvas');
    this.ctx = this.canvas.getContext('2d') as CanvasRenderingContext2D;
  }

  private paint(s: VideoSample) {
    const sc = Math.min(1, this.maxLong / Math.max(s.displayWidth, s.displayHeight));
    const w = Math.max(2, Math.round(s.displayWidth * sc)), h = Math.max(2, Math.round(s.displayHeight * sc));
    if (this.canvas.width !== w || this.canvas.height !== h) { this.canvas.width = w; this.canvas.height = h; }
    s.draw(this.ctx, 0, 0, w, h);
    this.w = w;
    this.h = h;
    this.version++;
  }

  /** Exact frame at source time t (paused preview). */
  async still(t: number) {
    this.active = false;
    const gen = ++this.stillGen;
    const s = await this.sink.getSample(Math.max(0, t));
    if (!s) return;
    if (gen !== this.stillGen) { s.close(); return; }
    this.paint(s);
    this.lastTs = s.timestamp;
    s.close();
  }

  /** Follow source time t while playing; frames that fall behind are dropped. */
  tick(t: number) {
    this.target = t;
    this.active = true;
    if (!this.pumping) void this.pump();
  }

  stop() { this.active = false; }

  private async pump() {
    this.pumping = true;
    try {
      while (this.active) {
        const t = this.target;
        if (!this.iter || t < this.lastTs - 0.15 || (t > this.lastTs + 1.0 && !this.ended)) {
          await this.closeIter();
          this.iter = this.sink.samples(Math.max(0, t));
          this.ended = false;
          this.lastTs = t - 1e-3;
        }
        if (!this.next && !this.ended) {
          const r = await this.iter!.next();
          if (r.done) this.ended = true; else this.next = r.value;
        }
        let show: VideoSample | null = null;
        while (this.next && this.next.timestamp <= this.target + 0.008) {
          show?.close();
          show = this.next;
          this.next = null;
          const r = await this.iter!.next();
          if (r.done) { this.ended = true; break; }
          this.next = r.value;
        }
        if (show) { this.paint(show); this.lastTs = show.timestamp; show.close(); }
        await nextFrame();
      }
    } catch (e) {
      console.warn('preview decode failed', e);
    } finally {
      await this.closeIter();
      this.pumping = false;
    }
  }

  private async closeIter() {
    this.next?.close();
    this.next = null;
    const it = this.iter;
    this.iter = null;
    if (it) await it.return(undefined).catch(() => {});
  }

  dispose() { this.active = false; this.stillGen++; }
}

export class SoundVoice {
  readonly gain: GainNode;
  private src: AudioBufferSourceNode | null = null;
  private startedFor = 0;
  private ctxStart = 0;
  private speed = 1;
  private loading = false;
  private gen = 0;
  private want = 0;

  constructor(private actx: AudioContext, dest: AudioNode, private track: InputAudioTrack, private srcEnd: number) {
    this.gain = actx.createGain();
    this.gain.gain.value = 0;
    this.gain.connect(dest);
  }

  tick(srcTime: number, gain: number, speed: number) {
    this.want = srcTime;
    this.gain.gain.setTargetAtTime(gain, this.actx.currentTime, 0.012);
    if (this.loading) return;
    const expected = this.startedFor + (this.actx.currentTime - this.ctxStart) * this.speed;
    if (!this.src || Math.abs(expected - srcTime) > 0.25 || speed !== this.speed) void this.load(srcTime, speed);
  }

  private async load(srcTime: number, speed: number) {
    this.loading = true;
    const gen = ++this.gen;
    try {
      const sink = new AudioBufferSink(this.track);
      const parts: { buffer: AudioBuffer; timestamp: number }[] = [];
      const end = Math.min(this.srcEnd, srcTime + 20 * speed);
      for await (const p of sink.buffers(Math.max(0, srcTime - 0.05), end)) {
        if (gen !== this.gen) return;
        parts.push(p);
      }
      if (gen !== this.gen || !parts.length) return;
      const sr = parts[0].buffer.sampleRate;
      const ch = Math.min(2, Math.max(...parts.map(p => p.buffer.numberOfChannels)));
      const len = parts.reduce((n, p) => n + p.buffer.length, 0);
      const buf = this.actx.createBuffer(ch, len, sr);
      let off = 0;
      for (const p of parts) {
        for (let c = 0; c < ch; c++) buf.copyToChannel(p.buffer.getChannelData(Math.min(c, p.buffer.numberOfChannels - 1)), c, off);
        off += p.buffer.length;
      }
      this.stopSrc();
      const src = this.actx.createBufferSource();
      src.buffer = buf;
      src.playbackRate.value = speed;
      src.connect(this.gain);
      const t0 = parts[0].timestamp;
      const offset = Math.max(0, this.want - t0);
      const now = this.actx.currentTime;
      src.start(now, offset);
      this.src = src;
      this.startedFor = t0 + offset;
      this.ctxStart = now;
      this.speed = speed;
    } catch (e) {
      console.warn('preview audio decode failed', e);
    } finally {
      if (gen === this.gen) this.loading = false;
    }
  }

  private stopSrc() {
    try { this.src?.stop(); } catch { /* already stopped */ }
    this.src?.disconnect();
    this.src = null;
  }

  stop() { this.gen++; this.loading = false; this.stopSrc(); }

  dispose() { this.stop(); this.gain.disconnect(); }
}
