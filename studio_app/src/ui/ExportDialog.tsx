import { useEffect, useRef, useState } from 'preact/hooks';
import { exportVideo, ExportPhase, ExportResult, recordRealtime } from '../engine/exporter';
import { player } from '../engine/player';
import { store, useStore } from '../state/store';
import { fmtBytes, projectDuration } from '../state/util';
import { saveFile } from './save';
import { Btn, Icon, Seg } from './controls';

type Quality = 'standard' | 'high' | 'max';
const BPP: Record<Quality, number> = { standard: 0.12, high: 0.2, max: 0.32 };

export function ExportDialog() {
  const open = useStore(s => s.exportOpen);
  const p = useStore(s => s.project);
  const [res, setRes] = useState<number>(1080);
  const [fps, setFps] = useState<number>(p.fps);
  const [quality, setQuality] = useState<Quality>('high');
  const [phase, setPhase] = useState<ExportPhase | 'idle' | 'done' | 'error'>('idle');
  const [frac, setFrac] = useState(0);
  const [note, setNote] = useState('');
  const [result, setResult] = useState<ExportResult | null>(null);
  const [url, setUrl] = useState<string | null>(null);
  const [error, setError] = useState('');
  const ctl = useRef<AbortController | null>(null);

  useEffect(() => { if (open) setFps(p.fps); }, [open]);
  useEffect(() => () => { if (url) URL.revokeObjectURL(url); }, [url]);
  if (!open) return null;

  const short = Math.min(p.width, p.height);
  const scale = res / short;
  const W = Math.round((p.width * scale) / 2) * 2, H = Math.round((p.height * scale) / 2) * 2;
  const bitrate = Math.round(W * H * fps * BPP[quality]);
  const dur = projectDuration(p);
  const estMB = ((bitrate + 192000) * dur) / 8 / 1048576;
  const busy = phase === 'prepare' || phase === 'audio' || phase === 'video' || phase === 'finish';

  const start = async () => {
    player.pause();
    ctl.current = new AbortController();
    setError(''); setResult(null); setFrac(0); setNote(''); setPhase('prepare');
    if (url) { URL.revokeObjectURL(url); setUrl(null); }
    try {
      let r: ExportResult;
      try {
        r = await exportVideo({ width: W, height: H, fps, bitrate, audioBitrate: 192000 }, (ph, f, n) => { setPhase(ph); setFrac(f); setNote(n || ''); }, ctl.current.signal);
      } catch (e: any) {
        if (e?.message !== 'NO_WEBCODECS') throw e;
        setPhase('video');
        setNote('Recording in real time');
        r = await recordRealtime(f => setFrac(f), ctl.current.signal);
      }
      setResult(r);
      setUrl(URL.createObjectURL(r.blob));
      setPhase('done');
    } catch (e: any) {
      if (e?.name === 'AbortError') { setPhase('idle'); return; }
      console.error(e);
      setError(e?.message || String(e));
      setPhase('error');
    } finally {
      ctl.current = null;
    }
  };

  const close = () => { if (busy) return; store.set({ exportOpen: false }); };
  const fileName = `${(p.name || 'voidfx-edit').replace(/[^\w\- ]+/g, '').trim() || 'voidfx-edit'}.${result?.ext || 'mp4'}`;
  const label: Record<string, string> = { prepare: 'Preparing', audio: 'Mixing audio', video: 'Rendering frames', finish: 'Finishing file' };

  return (
    <div class="modal-bg" onClick={e => { if (e.target === e.currentTarget) close(); }}>
      <div class="modal" role="dialog" aria-modal="true" aria-labelledby="exp-t">
        <header class="modal-h">
          <h2 id="exp-t">Export</h2>
          <Btn title="Close" onClick={close} disabled={busy}>{Icon.close}</Btn>
        </header>
        {phase !== 'done' && (
          <div class="modal-b">
            <div class="fld fld-wide"><span class="fld-l">Resolution</span>
              <Seg value={res} onChange={setRes} options={[720, 1080, 1440, 2160].map(v => ({ value: v, label: v === 2160 ? '4K' : `${v}p` }))} />
            </div>
            <div class="fld fld-wide"><span class="fld-l">Frame rate</span>
              <Seg value={fps} onChange={setFps} options={[24, 25, 30, 50, 60].map(v => ({ value: v, label: String(v) }))} />
            </div>
            <div class="fld fld-wide"><span class="fld-l">Quality</span>
              <Seg value={quality} onChange={setQuality} options={[{ value: 'standard', label: 'Standard' }, { value: 'high', label: 'High' }, { value: 'max', label: 'Maximum' }]} />
            </div>
            <dl class="exp-sum">
              <dt>Output</dt><dd>{W}×{H} · {fps} fps · MP4 (H.264 + AAC)</dd>
              <dt>Length</dt><dd>{dur.toFixed(2)} s ({Math.round(dur * fps)} frames)</dd>
              <dt>Video bitrate</dt><dd>{(bitrate / 1e6).toFixed(1)} Mbps</dd>
              <dt>Estimated size</dt><dd>{estMB.toFixed(estMB < 10 ? 1 : 0)} MB</dd>
            </dl>
            {busy && (
              <div class="prog" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(frac * 100)}>
                <div class="prog-l"><span>{label[phase] || ''}</span><span>{Math.round(frac * 100)}%{note ? ` · ${note}` : ''}</span></div>
                <div class="prog-bar"><i style={{ width: `${(frac * 100).toFixed(1)}%` }} /></div>
              </div>
            )}
            {phase === 'error' && <p class="note bad">Export failed: {error}</p>}
            <div class="modal-a">
              {busy ? <Btn kind="danger" onClick={() => ctl.current?.abort()}>{Icon.stop}<span>Cancel</span></Btn>
                : <Btn kind="primary" disabled={dur <= 0} onClick={() => void start()}>{Icon.download}<span>Export video</span></Btn>}
            </div>
            <p class="hint">Rendering happens on this device, frame by frame, so the file matches the preview exactly. Keep this tab open until it finishes.</p>
          </div>
        )}
        {phase === 'done' && result && url && (
          <div class="modal-b">
            <video class="exp-video" src={url} controls playsInline />
            <dl class="exp-sum">
              <dt>File</dt><dd>{fmtBytes(result.blob.size)} · {result.videoCodec}{result.audioCodec ? ` + ${result.audioCodec}` : ', no audio'}</dd>
              <dt>Rendered in</dt><dd>{result.seconds.toFixed(1)} s</dd>
            </dl>
            {result.warnings.map(w => <p class="note warn">{w}</p>)}
            <div class="modal-a">
              <Btn kind="primary" onClick={() => void saveFile(fileName, result.blob)}>{Icon.download}<span>Save {result.ext.toUpperCase()}</span></Btn>
              <Btn kind="solid" onClick={() => setPhase('idle')}>Export again</Btn>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
