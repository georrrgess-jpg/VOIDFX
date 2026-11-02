"""Builds audio/mix.wav (48 kHz stereo) for THE MASK SLIPS from edl.py.

music : Blood Theme bars 31-39 (build + drop) spliced at a downbeat into bar 56 (final hits,
        the song's own hard stop, then the quiet outro bed), faded out before the loop point.
vo    : "Check in. Establish an alibi." from the scene pack (cleaned, levelled).
sfx   : one synthesized glass 'tink' when the evidence bracket lands on the blood slide.
Then: loudness to -12 LUFS integrated, peak limiting, measurement.
"""
import os, sys, json, subprocess, math
import numpy as np, scipy.io.wavfile as wf, scipy.signal as ss
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edl

ROOT = edl.ROOT
SR = 48000
DUR = edl.DUR_FRAMES / edl.FPS
N = int(round(DUR * SR))
PREROLL = 1024          # samples of hidden lead-in for the AAC encoder (see main)

def load_song():
    p = os.path.join(ROOT, "audio", "song_48k.wav")
    if not os.path.exists(p):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", edl.SONG, "-ar", "48000", "-c:a", "pcm_f32le", p], check=True)
    sr, x = wf.read(p)
    assert sr == SR
    return x.astype(np.float32)

def music(song):
    M = edl.MUSIC
    pre = 0.006   # splice 6 ms before both downbeats so the bar-56 kick plays untouched
    a0, a1, b0 = int(round(M["a_in"] * SR)), int(round((M["a_out"] - pre) * SR)), int(round((M["b_in"] - pre) * SR))
    xf = int(round(0.004 * SR))
    A = song[a0:a1].copy()
    nb = N - len(A) + xf
    B = song[b0 - xf:b0 - xf + nb].copy()
    ramp = np.sin(np.linspace(0, np.pi / 2, xf))[:, None].astype(np.float32)
    A[-xf:] *= ramp[::-1]
    B[:xf] *= ramp
    out = np.zeros((N, 2), np.float32)
    out[:len(A)] += A
    out[len(A) - xf:len(A) - xf + len(B)] += B[:N - (len(A) - xf)]
    # fade out the outro bed before the loop point; 2 ms anti-click at the very start
    t0, t1 = edl.MUSIC["tail_fade"]
    i0, i1 = int(t0 * SR), int(t1 * SR)
    fade = 0.5 * (1 + np.cos(np.linspace(0, np.pi, i1 - i0)))
    out[i0:i1] *= fade[:, None]
    out[i1:] = 0
    out[:96] *= np.linspace(0, 1, 96)[:, None]
    return out

def compress(x, thr_db=-16, ratio=3.0, att=0.003, rel=0.09):
    a_att = math.exp(-1 / (att * SR)); a_rel = math.exp(-1 / (rel * SR))
    env = np.zeros_like(x); e = 0.0
    ax = np.abs(x)
    for i in range(len(x)):
        v = ax[i]
        e = a_att * e + (1 - a_att) * v if v > e else a_rel * e + (1 - a_rel) * v
        env[i] = e
    thr = 10 ** (thr_db / 20)
    gain = np.where(env > thr, (np.maximum(env, 1e-9) / thr) ** (1 / ratio - 1), 1.0)
    return (x * gain).astype(np.float32)

def vo():
    sr, x = wf.read(edl.PACK_AUDIO)
    x = x.astype(np.float32) / 32768.0
    if x.ndim > 1:
        x = x.mean(1)
    seg = x[int(edl.VO["src_in"] * sr):int(edl.VO["src_out"] * sr)]
    seg = ss.resample_poly(seg, 160, 147).astype(np.float32)          # 44.1k -> 48k
    b, a = ss.butter(2, 95 / (SR / 2), "high"); seg = ss.lfilter(b, a, seg)
    b, a = ss.butter(2, 9000 / (SR / 2), "low"); seg = ss.lfilter(b, a, seg)
    # gentle presence lift (~2.5 kHz, +2 dB) for intelligibility on phone speakers
    w0 = 2500 / (SR / 2); bq, aq = ss.iirpeak(w0, 1.2); pres = ss.lfilter(bq, aq, seg)
    seg = seg + 0.26 * pres
    # compressor (3:1 above -16 dBFS, 3 ms attack / 90 ms release), then active-speech RMS -> -19 dBFS
    seg = compress(seg, thr_db=-16, ratio=3.0, att=0.003, rel=0.09)
    env = np.sqrt(np.convolve(seg ** 2, np.ones(480) / 480, "same"))
    act = env > env.max() * 0.08
    rms = np.sqrt(np.mean(seg[act] ** 2))
    seg = seg * (10 ** (-16.5 / 20) / rms)
    nf = int(0.008 * SR); seg[:nf] *= np.linspace(0, 1, nf); seg[-nf:] *= np.linspace(1, 0, nf)
    start = (edl.VO["src_in"] + edl.VO_SHIFT)
    return seg.astype(np.float32), start

def tink(t_hit):
    """small glass hit: inharmonic partials + a 3 ms click, short room tail."""
    n = int(1.4 * SR); t = np.arange(n) / SR
    parts = [(2380, 0.42, 1.0), (3715, 0.30, 0.55), (5520, 0.21, 0.32), (7330, 0.14, 0.18), (9140, 0.09, 0.08)]
    y = np.zeros(n, np.float32)
    for f, dec, amp in parts:
        y += amp * np.sin(2 * np.pi * f * t + f * 0.001) * np.exp(-t / dec)
    att = np.minimum(1, t / 0.0012)
    y *= att
    rng = np.random.default_rng(7)
    click = rng.standard_normal(int(0.003 * SR)) * np.linspace(1, 0, int(0.003 * SR))
    b, a = ss.butter(2, 3000 / (SR / 2), "high"); click = ss.lfilter(b, a, click)
    y[:len(click)] += 0.5 * click
    y = y / np.abs(y).max()
    ir = rng.standard_normal(int(0.35 * SR)) * np.exp(-np.arange(int(0.35 * SR)) / SR / 0.07)
    ir /= np.sqrt(np.sum(ir ** 2))
    wet = ss.fftconvolve(y, ir)[:n]
    y = (y + 0.25 * wet / (np.abs(wet).max() + 1e-9)) 
    y = y / np.abs(y).max() * 10 ** (-17 / 20)          # peak -17 dBFS before the mix gain
    st = np.stack([y * 0.92, y * 1.0], 1).astype(np.float32)        # a touch right of centre
    return st, t_hit

def place(out, sig, t):
    i = int(round(t * SR))
    if sig.ndim == 1:
        sig = np.stack([sig, sig], 1)
    j = min(N, i + len(sig))
    out[i:j] += sig[:j - i]

def measure(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    I = float(r.split("Integrated loudness:")[1].split("I:")[1].split("LUFS")[0])
    TP = float(r.split("True peak:")[1].split("Peak:")[1].split("dBFS")[0])
    return I, TP

def main():
    song = load_song()
    mus = music(song)
    v, v_t = vo()
    # duck the outro bed slightly under the voice
    i0 = int(v_t * SR); i1 = i0 + len(v)
    duck = np.ones(N, np.float32); r = int(0.08 * SR)
    duck[i0 - r:i0] = np.linspace(1, 0.7, r); duck[i0:i1] = 0.7; duck[i1:i1 + r] = np.linspace(0.7, 1, r)
    mix = mus * duck[:, None]
    place(mix, v, v_t)
    prep = json.load(open(os.path.join(ROOT, "work", f"prep_{edl.VARIANT}.json")))
    if prep.get("drop_first") is not None:
        s, th = tink(prep["drop_first"] / edl.FPS)
        place(mix, s, th)
    tmp = os.path.join(ROOT, "audio", "mix_raw.wav")
    wf.write(tmp, SR, mix.astype(np.float32))
    I, TP = measure(tmp)
    target_I = -12.5
    ceiling = -3.0
    gain = target_I - I
    out = os.path.join(ROOT, "audio", "mix.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af",
                    f"volume={gain:.2f}dB,aresample=192000,alimiter=limit={10 ** (ceiling / 20):.4f}:attack=3:release=60:level=disabled,aresample=48000:resampler=soxr",
                    "-c:a", "pcm_s24le", out], check=True)
    # AAC's first frame overshoots on an instant loud onset (the edit starts on a sub hit). Give the encoder
    # PREROLL samples of the song's own lead-in before t=0; the muxer hides them with an edit list.
    sr_, m = wf.read(out); m = m.astype(np.float32) / 2 ** 31
    a0 = int(round(edl.MUSIC["a_in"] * SR))
    roll = song[a0 - PREROLL:a0].astype(np.float32) * 10 ** (gain / 20)
    roll[:256] *= np.linspace(0, 1, 256)[:, None]
    wf.write(os.path.join(ROOT, "audio", "mix_preroll.wav"), SR, np.vstack([roll, m]).astype(np.float32))
    test = os.path.join(ROOT, "audio", "mix_aac_test.m4a")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-itsoffset", str(-PREROLL / SR), "-i", os.path.join(ROOT, "audio", "mix_preroll.wav"),
                    "-c:a", "aac", "-b:a", "256k", test], check=True)
    I2, TP2 = measure(out); I3, TP3 = measure(test)
    print(f"raw {I:.1f} LUFS -> gain {gain:+.1f} dB, ceiling {ceiling} dBFS -> wav {I2:.1f} LUFS / {TP2:.1f} dBTP; AAC test {I3:.1f} LUFS / {TP3:.1f} dBTP")
    print(f"VO at {v_t:.3f}s ({len(v) / SR:.2f}s); tink at {prep.get('drop_first', 0) / edl.FPS:.3f}s; stop at {edl.STOP_T:.3f}s")

if __name__ == "__main__":
    main()
