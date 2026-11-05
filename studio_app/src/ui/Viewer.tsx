import { useEffect, useRef, useState } from 'preact/hooks';
import { player } from '../engine/player';
import { store, useStore } from '../state/store';
import { Clip } from '../state/types';
import { clamp, fmtTC, projectDuration, transformAt } from '../state/util';
import { setAnimProp } from './actions';
import { Btn, Icon, useFrame } from './controls';

export function Viewer() {
  const project = useStore(s => s.project);
  const media = useStore(s => s.media);
  const playing = useStore(s => s.playing);
  const hasMedia = useStore(s => s.mediaOrder.length > 0);
  const stageRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [box, setBox] = useState({ w: 270, h: 480 });
  const [loop, setLoop] = useState(false);
  const [muted, setMuted] = useState(false);

  useEffect(() => { player.attach(canvasRef.current!); }, []);

  // fit the frame inside the stage and size the canvas to the displayed pixels
  useEffect(() => {
    const el = stageRef.current!;
    const fit = () => {
      const pad = 20;
      const W = Math.max(50, el.clientWidth - pad * 2), H = Math.max(50, el.clientHeight - pad * 2);
      const ar = project.width / project.height;
      const w = Math.min(W, H * ar), h = w / ar;
      setBox({ w: Math.floor(w), h: Math.floor(h) });
      const dpr = Math.min(2, window.devicePixelRatio || 1);
      const cw = Math.min(project.width, Math.round(w * dpr)), ch = Math.round(cw / ar);
      player.setSize(cw, ch);
    };
    fit();
    const ro = new ResizeObserver(fit);
    ro.observe(el);
    return () => ro.disconnect();
  }, [project.width, project.height]);

  // re-render the still frame whenever the edit changes
  useEffect(() => { if (!playing) player.requestStill(); }, [project, media]);

  const dur = projectDuration(project);
  return (
    <div class="viewer">
      <div class="stage" ref={stageRef}>
        <div class="frame" style={{ width: `${box.w}px`, height: `${box.h}px` }}>
          <canvas ref={canvasRef} class="frame-canvas" aria-label="Preview" />
          <Overlay w={box.w} h={box.h} />
          {!project.clips.length && (
            <div class="frame-empty">
              <p class="frame-empty-t">{hasMedia ? 'Add clips to the timeline' : 'Import media to start'}</p>
              <p>{hasMedia ? 'Drag files from the library onto the timeline, or ask Opus to build the edit.' : 'Drop video, audio or images anywhere in the studio.'}</p>
            </div>
          )}
        </div>
      </div>
      <div class="transport">
        <span class="tc"><TimeReadout /> <em>/ {fmtTC(dur, project.fps)}</em></span>
        <span class="transport-mid">
          <Btn title="Back one frame (←)" onClick={() => player.seek(player.time - 1 / project.fps)}>{Icon.frameBack}</Btn>
          <Btn kind="solid" class="btn-play" title={playing ? 'Pause (Space)' : 'Play (Space)'} onClick={() => player.toggle()}>{playing ? Icon.pause : Icon.play}</Btn>
          <Btn title="Forward one frame (→)" onClick={() => player.seek(player.time + 1 / project.fps)}>{Icon.frameFwd}</Btn>
        </span>
        <span class="transport-r">
          <Btn title="Loop playback" active={loop} onClick={() => { player.loop = !loop; setLoop(!loop); }}>{Icon.loop}</Btn>
          <Btn title={muted ? 'Unmute preview' : 'Mute preview'} active={muted} onClick={() => { player.ensureAudio(); player.setMuted(!muted); setMuted(!muted); }}>{muted ? Icon.mute : Icon.vol}</Btn>
        </span>
      </div>
    </div>
  );
}

function TimeReadout() {
  const t = useStore(s => s.time);
  const fps = useStore(s => s.project.fps);
  return <b>{fmtTC(t, fps)}</b>;
}

/** Selection box on the preview: drag to move, corner to scale. */
function Overlay({ w, h }: { w: number; h: number }) {
  const sel = useStore(s => (s.selection.length === 1 ? s.selection[0] : null));
  const playing = useStore(s => s.playing);
  const boxRef = useRef<HTMLDivElement>(null);
  const drag = useRef<{ mode: 'move' | 'scale'; x0: number; y0: number; clip: Clip; cx: number; cy: number; d0: number } | null>(null);
  useFrame(() => {
    const el = boxRef.current;
    if (!el) return;
    const q = sel && !playing ? player.quadOf(sel) : null;
    const comp = player.comp;
    if (!q || !comp) { el.style.display = 'none'; return; }
    const k = w / comp.width;
    el.style.display = 'block';
    el.style.width = `${q.w * k}px`;
    el.style.height = `${q.h * k}px`;
    el.style.transform = `translate(${q.cx * k - (q.w * k) / 2}px, ${q.cy * k - (q.h * k) / 2}px) rotate(${q.rot}deg)`;
  });
  if (!sel) return null;
  const onDown = (e: PointerEvent, mode: 'move' | 'scale') => {
    const s = store.state;
    const clip = s.project.clips.find(c => c.id === sel);
    if (!clip || clip.kind === 'audio') return;
    e.stopPropagation();
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
    const q = player.quadOf(sel);
    const comp = player.comp;
    if (!q || !comp) return;
    const k = w / comp.width;
    const rect = (boxRef.current!.parentElement as HTMLElement).getBoundingClientRect();
    const cx = rect.left + q.cx * k, cy = rect.top + q.cy * k;
    drag.current = { mode, x0: e.clientX, y0: e.clientY, clip, cx, cy, d0: Math.hypot(e.clientX - cx, e.clientY - cy) || 1 };
    store.beginGesture();
  };
  const onMove = (e: PointerEvent) => {
    const d = drag.current;
    if (!d) return;
    const lt = clamp(store.state.time - d.clip.start, 0, d.clip.dur);
    const t0 = transformAt(d.clip, lt);
    const cur = store.state.project.clips.find(c => c.id === d.clip.id);
    if (!cur) return;
    if (d.mode === 'move') {
      const nx = t0.x + (e.clientX - d.x0) / w, ny = t0.y + (e.clientY - d.y0) / h;
      // gentle snap to centre lines
      const sx = Math.abs(nx) < 0.012 ? 0 : nx, sy = Math.abs(ny) < 0.012 ? 0 : ny;
      setAnimProp(cur, 'x', +sx.toFixed(4), true);
      const cur2 = store.state.project.clips.find(c => c.id === d.clip.id)!;
      setAnimProp(cur2, 'y', +sy.toFixed(4), true);
    } else {
      const dist = Math.hypot(e.clientX - d.cx, e.clientY - d.cy);
      setAnimProp(cur, 'scale', +clamp(t0.scale * (dist / d.d0), 0.05, 20).toFixed(4), true);
    }
  };
  const onUp = () => { if (drag.current) { drag.current = null; store.endGesture(); } };
  return (
    <div class="ov-box" ref={boxRef} onPointerDown={e => onDown(e as any, 'move')} onPointerMove={onMove as any} onPointerUp={onUp} onPointerCancel={onUp}>
      {(['tl', 'tr', 'bl', 'br'] as const).map(c => <i class={`ov-h ${c}`} onPointerDown={e => onDown(e as any, 'scale')} onPointerMove={onMove as any} onPointerUp={onUp} />)}
    </div>
  );
}
