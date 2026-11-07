"""Effects against the music (pipeline v2, WP12; the Dexter studio's rule 7): a level table for every transition and
set piece, from the stems the audio builder writes (vN/audio/stem_music.wav, stem_fx.wav).

  python3 tools/mixcheck.py N [--under 12]

For each transition (EDL `tin`, at the shot's t0) and each set piece in E.SET_PIECES = [(name, t0, t1), ...] it
measures the music RMS over the window and the loudest 50 ms of the effects, both in dBFS before mastering (the
master gain moves both by the same amount). FLAG: the effects' loudest 50 ms is more than UNDER dB below the music
(buried, as v105 rev 1's effects were at 20-25 dB under). Also prints the music's overall RMS: on a loud master
(-9 to -11 dBFS RMS) push effects about +9 dB and duck the music about 3 dB under the biggest hits.
Writes vN/work/mixcheck.json.
"""
import os, sys, json, argparse
import numpy as np
from scipy.io import wavfile as wf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edit_env

def db(x): return 20 * np.log10(max(float(x), 1e-9))
def rms(x): return float(np.sqrt(np.mean(np.square(x)))) if len(x) else 0.0

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("n", type=int); ap.add_argument("--under", type=float, default=12.0)
    a = ap.parse_args(); n = a.n
    E = edit_env.edl(n); ad = f"{edit_env.ROOT}/v{n}/audio"
    if not os.path.exists(f"{ad}/stem_fx.wav"): sys.exit("no stems: re-run the audio step (the builder writes stem_music.wav / stem_fx.wav)")
    sr, mu = wf.read(f"{ad}/stem_music.wav"); _, fx = wf.read(f"{ad}/stem_fx.wav")
    mu = mu.astype(np.float32).mean(1) if mu.ndim > 1 else mu.astype(np.float32)
    fx = fx.astype(np.float32).mean(1) if fx.ndim > 1 else fx.astype(np.float32)
    events = []
    for s in E.SHOTS:
        if s.get("tin"): events.append((s["tin"], s["t0"], s["t0"] - 0.30, s["t0"] + 0.45, "transition"))
    for sp in getattr(E, "SET_PIECES", []): events.append((sp[0], sp[1], sp[1], sp[2], "set piece"))
    rows = []; w50 = int(0.05 * sr)
    for name, at, t0, t1, kind in sorted(events, key=lambda e: e[1]):
        i0, i1 = max(0, int(t0 * sr)), min(len(mu), int(t1 * sr))
        if i1 - i0 < w50: continue
        m_db = db(rms(mu[i0:i1]))
        seg = fx[i0:i1]; k = len(seg) // w50
        peak = max(rms(seg[j * w50:(j + 1) * w50]) for j in range(k)) if k else rms(seg)
        f_db = db(peak); rows.append({"name": name, "kind": kind, "at": round(at, 2), "t0": round(t0, 2), "t1": round(t1, 2), "music_db": round(m_db, 1),
                                      "fx_peak_db": round(f_db, 1), "fx_minus_music": round(f_db - m_db, 1), "buried": bool(f_db - m_db < -a.under)})
    print(f"music overall {db(rms(mu)):.1f} dBFS RMS (before mastering); effects vs music, loudest 50 ms of effects:")
    print("   time   kind        name              music   fx peak   fx - music")
    for r in rows:
        print(f"  {r['at']:5.2f}  {r['kind']:10s}  {r['name'][:16]:16s} {r['music_db']:6.1f}  {r['fx_peak_db']:7.1f}   {r['fx_minus_music']:+6.1f}{'   BURIED' if r['buried'] else ''}")
    bur = [r for r in rows if r["buried"]]
    print(f"{len(bur)} of {len(rows)} moments with effects more than {a.under:.0f} dB under the music" + (": " + ", ".join(r["name"] for r in bur) if bur else ""))
    json.dump({"music_rms_db": round(db(rms(mu)), 1), "under": a.under, "rows": rows}, open(f"{edit_env.work_dir(n)}/mixcheck.json", "w"), indent=1)

if __name__ == "__main__":
    main()
