"""Song prep in one command (efficiency update, 2026-11-08): everything the EDL needs from the song, with the checks
that have caught wrong grids and wrong words before (v106: a map locked to 4/3 of the real tempo; v13: Whisper on the
full mix heard "girl" where the vocal stem says "God").

  python3 tools/song_prep.py N SONG.mp3 [--h0 H0 --h1 H1] [--bpm 90] [--pad 8]
  bash tools/build.sh N song:src/SONG.mp3[:H0:H1]

1. decodes the song (vN/audio/song48.wav) and maps it (tools/song_map.py: grid, bars, drops, candidate windows);
2. separates a window of it with Demucs htdemucs (the chosen H0..H1, or the best candidate, +-8 s): vN/audio/sep/htdemucs/win;
3. fits the half-beat grid on the DRUM stem, trying the map's period and its 2/3, 3/4, 4/3, 3/2 relatives, and says
   whether the map's grid agrees;
4. transcribes the VOCAL stem with Whisper large-v3 (word times in song seconds and in edit half-beats): vN/work/tr_vocals.json;
5. scores each candidate window's loop wrap (music spectral correlation of the bar before H0 with the bar before H1;
   v13's window wrapped at 0.9996);
6. writes vN/work/song.json and prints the EDL lines (HB, HB_OFF, H0, H1, SONG_STEMS, STEMS_T0, the sung onsets).
"""
import os, sys, json, subprocess, argparse, time
import numpy as np, scipy.signal as ss, scipy.io.wavfile as wf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def dec(path, sr, mono=True, ss_=None, t=None):
    cmd = ["ffmpeg", "-v", "error"] + (["-ss", str(ss_)] if ss_ is not None else []) + ["-i", path] + (["-t", str(t)] if t else []) + \
          ["-ac", "1" if mono else "2", "-ar", str(sr), "-f", "f32le", "-"]
    x = np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).copy()
    return x if mono else x.reshape(-1, 2)

def onset_env(x, sr, hop=256):
    f, t, Z = ss.stft(x, sr, nperseg=1024, noverlap=1024 - hop); M = np.log1p(np.abs(Z) * 10)
    fl = np.maximum(0, np.diff(M, axis=1)).sum(0); fl = np.maximum(fl - ss.medfilt(fl, 31), 0)
    return fl / (fl.std() + 1e-9), sr / hop

def comb(env, fps, P, dur, t0=0.0):
    best = (-1, 0)
    for off in np.linspace(0, P, 60, endpoint=False):
        idx = np.round((off + np.arange(0, dur - off, P)) * fps).astype(int); idx = idx[idx < len(env)]
        sc = float(env[idx].mean()) if len(idx) else 0
        if sc > best[0]: best = (sc, off)
    return best

def fit_grid(drums, sr, P0, t0):
    """refine (P, offset) on the drum stem around P0 and its tempo relatives; offset in song seconds."""
    env, fps = onset_env(drums, sr); dur = len(drums) / sr; out = []
    for rel in (1.0, 2 / 3, 3 / 4, 4 / 3, 3 / 2):
        best = (-1, 0, 0)
        for P in np.linspace(P0 * rel * 0.985, P0 * rel * 1.015, 81):
            sc, off = comb(env, fps, P, dur)
            if sc > best[0]: best = (sc, P, off)
        out.append(dict(rel=round(rel, 3), score=round(best[0], 3), P=round(float(best[1]), 6), off_song=round(float((t0 + best[2]) % best[1]), 4)))
    base = out[0]["score"]
    for o in out: o["vs_map"] = round(o["score"] / (base + 1e-9), 2)
    return out

def wrap_score(mus, sr, t_a, t_b, bar):
    """spectral correlation of the bar before t_a with the bar before t_b (music only)."""
    def spec(t):
        a, b = int((t - bar) * sr), int(t * sr)
        if a < 0 or b > len(mus): return None
        f, P = ss.welch(mus[a:b], sr, nperseg=4096); return np.log10(P[(f > 30) & (f < 12000)] + 1e-12)
    A, B = spec(t_a), spec(t_b)
    if A is None or B is None: return None
    return round(float(np.corrcoef(A, B)[0, 1]), 4)

def vocal_onsets(voc, sr):
    """sung onsets on the vocal stem: spectral-flux peaks where the stem is audible (s, strength)."""
    env, fps = onset_env(voc, sr, 128)
    rms = np.sqrt(np.convolve(voc ** 2, np.ones(int(sr * 0.03)) / int(sr * 0.03), "same"))[::128][:len(env)]
    gate = 20 * np.log10(rms + 1e-9) > 20 * np.log10(np.percentile(rms, 95) + 1e-9) - 30
    pk, _ = ss.find_peaks(env * gate[:len(env)], height=1.5, distance=int(fps * 0.09))
    return [(float(p / fps), float(env[p])) for p in pk]

def snap_words(words, ons, prev_end=-1.0):
    """move each word's start to the strongest vocal onset in [start - 0.45 s, start + 0.10 s], after the previous word."""
    out = []; used = set()
    for i, (w, t0, t1, p) in enumerate(words):
        lo = max(t0 - 0.45, out[-1][1] + 0.08 if out else prev_end)        # Whisper's END times stretch over pauses
        c = [(st_, o) for o, st_ in ons if lo <= o <= t0 + 0.10]
        near = [(st_, o) for st_, o in c if abs(o - t0) <= 0.08]
        o = t0 if not c else (max(near)[1] if near and max(near)[0] >= 0.5 * max(c)[0] else max(c)[1])
        out.append((w, round(o, 3), t1, p, round(o - t0, 3)))
        if c: used.add(round(o, 3))
    return out, used

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("n", type=int); ap.add_argument("song")
    ap.add_argument("--h0", type=int); ap.add_argument("--h1", type=int); ap.add_argument("--bpm", type=float); ap.add_argument("--pad", type=float, default=8.0)
    ap.add_argument("--no-whisper", action="store_true")
    a = ap.parse_args(); V = f"v{a.n}"; W = f"{ROOT}/{V}/work"; AD = f"{ROOT}/{V}/audio"
    os.makedirs(W, exist_ok=True); os.makedirs(AD, exist_ok=True)
    song = a.song if os.path.isabs(a.song) else f"{ROOT}/{a.song}"; T0 = time.time()
    if not os.path.exists(f"{AD}/song48.wav"):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", song, "-ac", "2", "-ar", "48000", f"{AD}/song48.wav"], check=True)
    # 1. map
    cmd = [sys.executable, f"{ROOT}/tools/song_map.py", song, W] + (["--bpm", str(a.bpm)] if a.bpm else [])
    mp = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    print(mp.split("\n")[0]); M = json.load(open(f"{W}/song_map.json")); P0, off0 = M["P"], M["off"]
    st = lambda h, P=P0, off=off0: off + h * P
    if a.h0 is not None and a.h1 is not None: h0, h1 = a.h0, a.h1
    elif M["windows"]: h0, h1 = M["windows"][0]["h0"], M["windows"][0]["h1"]
    else: sys.exit("no candidate window: pass --h0 and --h1")
    # 2. stems for the window
    w0 = max(0.0, st(h0) - a.pad); w1 = st(h1) + a.pad; sep = f"{AD}/sep/htdemucs/win"; meta = f"{AD}/sep/window.json"
    have = os.path.exists(f"{sep}/drums.wav") and os.path.exists(meta) and json.load(open(meta)).get("t0") == round(w0, 3) \
        and json.load(open(meta)).get("t1") == round(w1, 3)
    if not have:
        wav = f"{AD}/sep/win.wav"; os.makedirs(f"{AD}/sep", exist_ok=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(w0), "-t", str(w1 - w0), "-i", song, "-ac", "2", "-ar", "44100", wav], check=True)
        print(f"demucs htdemucs on song {w0:.2f}-{w1:.2f} s ...", flush=True)
        r = subprocess.run([sys.executable, "-m", "demucs", "-n", "htdemucs", "-j", "4", "-o", f"{AD}/sep", wav], capture_output=True, text=True)
        if r.returncode: sys.exit("demucs failed: " + r.stderr[-400:])
        json.dump({"t0": round(w0, 3), "t1": round(w1, 3)}, open(meta, "w"))
    sr = 44100
    stem = {k: dec(f"{sep}/{k}.wav", sr) for k in ("drums", "bass", "other", "vocals") if os.path.exists(f"{sep}/{k}.wav")}
    mus = stem["drums"] + stem.get("bass", 0) + stem.get("other", 0)
    # 3. grid on the drum stem
    drum_rms = 20 * np.log10(np.sqrt(np.mean(stem["drums"] ** 2)) + 1e-9)
    grid_on = "drums" if drum_rms > -45 else "music (no vocals): the drum stem is near silent here"
    fits = fit_grid(stem["drums"] if drum_rms > -45 else mus, sr, P0, w0); best = max(fits, key=lambda o: o["score"])
    P, off = (best["P"], best["off_song"]) if best["rel"] == 1.0 or best["vs_map"] > 1.15 else (fits[0]["P"], fits[0]["off_song"])
    agree = abs(P - P0) / P0 < 0.002 and min(abs(off - off0) % P, P - abs(off - off0) % P) < 0.012
    # 4. words on the vocal stem
    words = []
    if not a.no_whisper and "vocals" in stem:
        print("whisper large-v3 on the vocal stem ...", flush=True)
        from faster_whisper import WhisperModel
        v16 = dec(f"{sep}/vocals.wav", 16000)
        m = WhisperModel("large-v3", device="cpu", compute_type="int8")
        segs, _ = m.transcribe(v16, word_timestamps=True, vad_filter=False, beam_size=5, language="en", condition_on_previous_text=False)
        tr = []
        for s in segs:
            ws = [(x.word.strip(), round(w0 + x.start, 2), round(w0 + x.end, 2), round(x.probability, 2)) for x in s.words]
            tr.append(dict(t0=round(w0 + s.start, 2), t1=round(w0 + s.end, 2), text=s.text.strip(), words=ws)); words += ws
        json.dump(tr, open(f"{W}/tr_vocals.json", "w"), indent=1)
    ons = [(o + w0, st_) for o, st_ in vocal_onsets(stem["vocals"], sr)] if "vocals" in stem else []
    snapped, used = snap_words(words, ons)
    loose = [o for o, st_ in ons if st_ > 3.0 and all(abs(o - u) > 0.2 for u in used) and all(not (x[1] - 0.05 <= o <= x[2]) for x in words)]
    # 5. loop wrap for the chosen and the candidate windows
    bar = 8 * P
    def wrap(h0_, h1_): return wrap_score(mus, sr, off + h0_ * P - w0, off + h1_ * P - w0, bar)
    full = dec(song, sr)
    def wrap_mix(h0_, h1_): return wrap_score(full, sr, off + h0_ * P, off + h1_ * P, bar)
    cands = [dict(h0=w_["h0"], h1=w_["h1"], dur=w_["dur"], drop_h=w_["drop_h"]) for w_ in M["windows"][:8]]
    for c in cands: c["wrap_mix"] = wrap_mix(c["h0"], c["h1"])
    chosen = dict(h0=h0, h1=h1, dur=round((h1 - h0) * P, 3), song_in=round(off + h0 * P, 4), wrap_music=wrap(h0, h1), wrap_mix=wrap_mix(h0, h1))
    # 6. report
    out = dict(song=os.path.relpath(song, ROOT), map=dict(P=P0, off=off0, bpm=M["bpm"]), drum_fit=fits, P=P, off=off, grid_agrees=agree,
               drum_stem_rms_db=round(float(drum_rms), 1), grid_on=grid_on, window=chosen, candidates=cands, stems=os.path.relpath(sep, ROOT),
               stems_t0=round(w0, 3), words=[dict(w=x[0], t=round(x[1] - x[4], 3), e=round((x[1] - x[4] - off) / P - h0, 2), p=x[3], onset_t=x[1],
               onset_e=round((x[1] - off) / P - h0, 2), check=bool(abs(x[4]) > 0.1)) for x in snapped],
               loose_onsets=[dict(t=round(o, 3), e=round((o - off) / P - h0, 2)) for o in loose])
    json.dump(out, open(f"{W}/song.json", "w"), indent=1)
    print(f"grid on the {grid_on}: map P={P0:.5f} off={off0:.4f} | " + ", ".join(f"x{o['rel']}: {o['score']}" for o in fits)
          + f" -> P={P:.6f} off={off:.4f} ({'agrees with the map' if agree else 'DIFFERS from the map: check both on the onsets'})")
    print(f"window h{h0}->h{h1}: song {chosen['song_in']:.3f} s, {chosen['dur']:.2f} s, loop wrap {chosen['wrap_music']} (music stem) / {chosen['wrap_mix']} (mix)")
    print("candidates (h0->h1, dur, drop, wrap on the mix):", "; ".join(f"h{c['h0']}->h{c['h1']} {c['dur']}s drop h{c['drop_h']} wrap {c['wrap_mix']}" for c in cands[:6]))
    if words:
        inwin = [x for x in out["words"] if -1 <= x["e"] <= h1 - h0 + 1]
        print("sung words in the window (Whisper on the vocal stem, edit half-beat e; [onset eX?] = the stem's strongest onset nearby "
              "disagrees by > 0.1 s: check that word on the stem's pitch and onsets):",
              " ".join(f"{x['w']}@e{x['e']}" + (f"[onset e{x['onset_e']}?]" if x["check"] else "") for x in inwin[:60]))
        lw = [x for x in out["loose_onsets"] if -1 <= x["e"] <= h1 - h0 + 1]
        if lw: print("vocal onsets with no word (Whisper may have dropped one):", " ".join(f"e{x['e']}" for x in lw[:20]))
    print(f"\nEDL lines:\nHB, HB_OFF = {P:.6f}, {off:.4f}\nH0, H1 = {h0}, {h1}\nSONG = f\"{{ROOT}}/{out['song']}\"\n"
          f"SONG_STEMS = f\"{{ROOT}}/{{VER}}/audio/sep/htdemucs/win\"; STEMS_T0 = {w0:.3f}")
    print(f"wrote {V}/work/song.json ({time.time() - T0:.0f} s)")

if __name__ == "__main__":
    main()
