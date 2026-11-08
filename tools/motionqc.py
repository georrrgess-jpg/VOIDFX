"""Motion audit on the encoded edit (the Dexter studio's v106 WONDERWALL rules 2, 3, 5 and 7): dead spans, pops, judder.

  python3 tools/motionqc.py N [--file OUT.mp4] [--dead 1.5] [--span 1.0] [--ratio 2.5]

Decodes the encode at 135x240 grey and takes d[f] = mean |frame f - frame f-1| (grey levels, 0-255).
- Activity per half-beat, and DEAD spans: runs of half-beats whose mean d stays under --dead (static floor ~1-1.5,
  an active edit 5-18) for --span seconds or more. Each one wants a new cut and a designed transition (v106 rule 2).
- POPS: d[f] > 3 * median(d[f-6 .. f+6]) + 2 (v106 rule 3). Each one is labelled cut (within 1 frame of a cut), flash
  (the frame's mean luma is 12+ over its neighbourhood, or it is the previous frame's negative: correlation < -0.25), or beat (within 1 frame of a half-beat: a beat-camera hit);
  everything else is listed as UNEXPLAINED with the transition it sits in, if any. Every unexplained pop is a defect
  to fix or a designed hit to justify (v106 rev 1 shipped six, three invisible on stills).
- JUDDER per shot (v106 rule 5): a 24p/30p hold cadence between 60p flow shots. A frame is a repeat when its d is
  under 0.45x the larger neighbour (and that neighbour moves, > 2); a CADENCE run is any 15-frame window with 40 %+
  repeats (2:3 pulldown gives 60 %, 2:2 gives 50 %, smooth motion and beat-length speed ramps ~0-20 %). A shot with
  30+ cadence frames (0.5 s) is flagged: give it interp="flow" (or check why its flow fell back). The p80/p20 ratio v106 used
  is printed too (over --ratio on a held shot = judder; speed-ramped shots score high by design). Pops inside a
  cadence run are labelled cadence.
- LOOP (v106 rule 7): the step across the wrap (last frame -> frame 0) against the steps around it.
Writes vN/work/motionqc.json. A review list, not a gate (build.sh qc prints it).
"""
import os, sys, json, argparse, subprocess
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edit_env

W_, H_ = 135, 240

def decode(path):
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-vf", f"scale={W_}:{H_}:flags=area,format=gray", "-f", "rawvideo", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H_, W_).astype(np.float32)

def anti(a, b):
    """correlation of two grey frames: about -1 when one is the other's negative (an impact's designed negative frame)."""
    a = a - a.mean(); b = b - b.mean(); return float((a * b).sum() / (np.sqrt((a * a).sum() * (b * b).sum()) + 1e-6))

def local_median(x, r=6):
    n = len(x); return np.array([np.median(x[max(0, i - r):min(n, i + r + 1)]) for i in range(n)], np.float32)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("n", type=int); ap.add_argument("--file")
    ap.add_argument("--dead", type=float, default=1.5); ap.add_argument("--span", type=float, default=1.0)
    ap.add_argument("--ratio", type=float, default=2.5)
    a = ap.parse_args(); n = a.n
    E = edit_env.edl(n); fps = E.FPS
    path = a.file or f"{edit_env.ROOT}/v{n}/out/{E.SLUG}_voidfx_9x16.mp4"
    if not os.path.exists(path): sys.exit(f"no encode: {path}")
    fr = decode(path); N = len(fr)
    d = np.zeros(N, np.float32); d[1:] = np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2))
    luma = fr.mean(axis=(1, 2))
    wrap = float(np.abs(fr[0] - fr[-1]).mean()); d[0] = wrap
    shots = E.SHOTS; cuts = [int(round(s["t0"] * fps)) for s in shots[1:]]
    tins = {int(round(s["t0"] * fps)): s.get("tin") for s in shots[1:]}
    hb = E.HB; nhb = int(round(E.DUR / hb))
    hb_f = [int(round(e * hb * fps)) for e in range(nhb + 1)]

    # activity per half-beat and dead spans
    act = [float(d[max(1, hb_f[e]):max(hb_f[e] + 1, hb_f[e + 1])].mean()) for e in range(nhb)]
    dead, run = [], []
    for e, v in enumerate(act + [1e9]):
        if v < a.dead: run.append(e); continue
        if run and len(run) * hb >= a.span - 1e-6:
            dead.append({"t0": round(run[0] * hb, 2), "t1": round((run[-1] + 1) * hb, 2), "hb": [run[0], run[-1]],
                         "mean": round(float(np.mean([act[k] for k in run])), 2)})
        run = []

    # cadence (repeat frames) for the judder check and the pop labels
    rep = np.zeros(N, bool); nb = np.zeros(N, np.float32); nb[1:-1] = np.maximum(d[:-2], d[2:])
    rep[2:-1] = (d[2:-1] < 0.45 * nb[2:-1]) & (nb[2:-1] > 2.0)
    cad = np.zeros(N, bool)
    for k in range(2, N - 16):
        if rep[k:k + 15].mean() >= 0.4: cad[k:k + 15] = True

    # pops
    med = local_median(d); lmed = local_median(luma)
    pops = []
    for f in range(1, N):
        if d[f] <= 3 * med[f] + 2: continue
        near_cut = min((abs(f - c) for c in cuts), default=99)
        flash = max(luma[f] - lmed[f], luma[f - 1] - lmed[f - 1]) >= 12 \
            or anti(fr[f], fr[f - 1]) < -0.25                  # a designed negative frame (an impact's inverted hit, Dexter v107 f352)
        near_hb = min(abs(f - x) for x in hb_f)
        kind = "cut" if near_cut <= 1 else "flash" if flash else "beat" if near_hb <= 1 else "cadence" if cad[f] else "UNEXPLAINED"
        ctx = None
        for c in cuts:
            if -18 <= f - c <= 30: ctx = f"{tins.get(c) or 'cut'} @ {c}"; break
        pops.append({"f": f, "t": round(f / fps, 3), "d": round(float(d[f]), 1), "med": round(float(med[f]), 1),
                     "kind": kind, "near": ctx, "hb_off": int(min((f - x for x in hb_f), key=abs))})

    # judder per shot
    judder = []
    bounds = [int(round(s["t0"] * fps)) for s in shots] + [N]
    for i, s in enumerate(shots):
        b0, b1 = bounds[i] + 6, bounds[i + 1] - 6
        cf = np.nonzero(cad[max(2, b0):max(2, b1)])[0] + max(2, b0)
        a0, a1 = bounds[i] + 20, bounds[i + 1] - 20
        seg = d[max(1, a0):a1] if a1 - a0 >= 24 else d[max(1, b0):max(2, b1)]
        p20, p80 = (np.percentile(seg, 20), np.percentile(seg, 80)) if len(seg) else (0.0, 0.0)
        r = float(p80 / max(p20, 0.05))
        judder.append({"shot": s.get("n", str(i)), "f0": int(bounds[i]), "f1": int(bounds[i + 1]), "interp": s.get("interp"),
                       "repeat_frac": round(float(rep[max(2, b0):max(2, b1)].mean()) if b1 > b0 else 0.0, 2),
                       "cadence_frames": int(len(cf)), "cadence_range": [int(cf[0]), int(cf[-1])] if len(cf) else None,
                       "p20": round(float(p20), 2), "p80": round(float(p80), 2), "ratio": round(r, 2),
                       "flag": bool(len(cf) >= 30 or (s.get("interp") == "hold" and r > a.ratio and len(cf) > 0))})

    loop_ctx = np.concatenate([d[1:7], d[-6:]]); loop_med = float(np.median(loop_ctx))
    loop = {"wrap_step": round(wrap, 2), "local_median": round(loop_med, 2), "spike": bool(wrap > 3 * loop_med + 2)}

    print(f"motion audit on {os.path.basename(path)}: {N} frames, mean activity {float(d[1:].mean()):.2f} grey levels/frame")
    print("  activity per half-beat: " + " ".join(f"{v:.1f}" for v in act))
    print(f"  dead spans (< {a.dead} for >= {a.span:.1f} s): " + (", ".join(f"{x['t0']:.2f}-{x['t1']:.2f} s (mean {x['mean']})" for x in dead) or "none"))
    unexp = [p for p in pops if p["kind"] == "UNEXPLAINED"]
    by = {}
    for p in pops: by[p["kind"]] = by.get(p["kind"], 0) + 1
    print(f"  pops (d > 3*median(+-6) + 2): {len(pops)} = " + ", ".join(f"{k} {v}" for k, v in sorted(by.items())))
    for p in unexp: print(f"    UNEXPLAINED f{p['f']} ({p['t']:.2f} s) d {p['d']} vs median {p['med']}, {p['hb_off']:+d} frames from a half-beat"
                          + (f", in {p['near']}" if p["near"] else ""))
    jf = [j for j in judder if j["flag"]]
    print("  judder (hold cadence): " + (", ".join(f"{j['shot']} (interp {j['interp']}) frames {j['cadence_range'][0]}-{j['cadence_range'][1]}, "
                                                f"{j['repeat_frac']:.0%} repeats, p80/p20 {j['ratio']}" for j in jf) or "none"))
    print(f"  loop wrap step {loop['wrap_step']} vs local median {loop['local_median']}" + ("  SPIKE" if loop["spike"] else "  OK"))
    json.dump({"file": path, "frames": N, "activity_hb": [round(v, 2) for v in act], "dead": dead, "pops": pops,
               "judder": judder, "loop": loop}, open(f"{edit_env.work_dir(n)}/motionqc.json", "w"), indent=1)

if __name__ == "__main__":
    main()
