"""Golden frames: the regression check every engine change must pass (pipeline v2, WP1).

  python3 tools/golden.py N --save            # render the golden list and store it (vN/work/golden/, PNG, not in git)
  python3 tools/golden.py N --check           # render again and compare; exit 1 on a failure
  python3 tools/golden.py N --check --diff    # also write amplified difference sheets of the worst frames
  python3 tools/golden.py N --list            # print the frame list
  options: --frames a,b,c   (override the list)    --workers 4

The list: frame 0, the last 3 frames, every cut at -6 / 0 / +6, the middle of every shot, and every 32nd frame.
Gate (guardrail 8 of sync/PIPELINE_V2_PLAN.md): every frame within 2/255 per pixel and a mean difference under 0.2/255.
The check also reports render time, so it doubles as the speed benchmark.
"""
import os, sys, json, time, subprocess, argparse
from multiprocessing import Pool
import numpy as np, cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edit_env

MAX_TOL, MEAN_TOL = 2, 0.2
R = None

def frame_list(n):
    E = edit_env.edl(n); D = E.DUR_F
    fs = {0, D - 3, D - 2, D - 1}
    shots = E.SHOTS
    for i, s in enumerate(shots):
        f1 = shots[i + 1]["f0"] if i + 1 < len(shots) else D
        fs.add((s["f0"] + f1) // 2)
        if i: fs.update(s["f0"] + o for o in (-6, 0, 6))
    fs.update(range(0, D, 32))
    return sorted(f for f in fs if 0 <= f < D)

def _job(f):
    t = time.time(); im = R.render(f)
    return f, im, time.time() - t

def render_all(n, frames, workers):
    global R
    t0 = time.time(); R = edit_env.load_edit(n); t_setup = time.time() - t0
    out, times = {}, {}
    t1 = time.time()
    with Pool(workers) as pool:
        for f, im, dt in pool.imap_unordered(_job, frames, chunksize=1):
            out[f] = im; times[f] = dt
    return out, times, t_setup, time.time() - t1

def gdir(n): return f"{edit_env.work_dir(n)}/golden"

def git_rev():
    try: return subprocess.check_output(["git", "-C", edit_env.ROOT, "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception: return "?"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("n", type=int)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--save", action="store_true"); g.add_argument("--check", action="store_true"); g.add_argument("--list", action="store_true")
    ap.add_argument("--frames"); ap.add_argument("--workers", type=int, default=4); ap.add_argument("--diff", action="store_true")
    a = ap.parse_args()
    d = gdir(a.n)
    if a.frames: frames = [int(x) for x in a.frames.split(",")]
    elif a.check and os.path.exists(f"{d}/index.json"): frames = json.load(open(f"{d}/index.json"))["frames"]
    else: frames = frame_list(a.n)
    if a.list: print(len(frames), "frames:", frames); return
    ims, times, t_setup, t_render = render_all(a.n, frames, a.workers)
    tsum = sum(times.values())
    print(f"rendered {len(frames)} frames in {t_render:.1f} s on {a.workers} workers (set-up {t_setup:.1f} s; "
          f"{tsum / len(frames):.2f} s per frame per worker)")
    if a.save:
        os.makedirs(d, exist_ok=True)
        for f, im in ims.items(): cv2.imwrite(f"{d}/f{f:04d}.png", im, [cv2.IMWRITE_PNG_COMPRESSION, 3])
        json.dump({"frames": frames, "rev": git_rev(), "saved": time.strftime("%Y-%m-%d %H:%M"),
                   "render_s": round(t_render, 1), "per_frame_s": {str(k): round(v, 3) for k, v in sorted(times.items())}},
                  open(f"{d}/index.json", "w"), indent=1)
        print("saved", len(ims), "golden frames to", d); return
    ref = json.load(open(f"{d}/index.json"))
    rows, bad = [], []
    for f in frames:
        g_ = cv2.imread(f"{d}/f{f:04d}.png")
        if g_ is None: bad.append(f); rows.append((f, 255, 255.0, 1.0)); continue
        df = cv2.absdiff(ims[f], g_)
        mx, mean, frac = int(df.max()), float(df.mean()), float((df > MAX_TOL).mean())
        rows.append((f, mx, mean, frac))
        if mx > MAX_TOL or mean >= MEAN_TOL: bad.append(f)
    rows.sort(key=lambda r: (-r[1], -r[2]))
    print(f"golden check v{a.n} against rev {ref.get('rev')} ({ref.get('saved')}); gate: max <= {MAX_TOL}, mean < {MEAN_TOL}")
    print("  worst frames:  frame  max  mean    px>tol")
    for f, mx, mean, frac in rows[:8]: print(f"               {f:5d}  {mx:3d}  {mean:.3f}  {frac * 100:.4f} %")
    old = ref.get("render_s")
    if old: print(f"  render time {t_render:.1f} s vs {old:.1f} s at save ({old / max(t_render, 1e-6):.2f}x)")
    json.dump({"rev": git_rev(), "pass": not bad, "failed": bad, "render_s": round(t_render, 1),
               "rows": [{"f": f, "max": mx, "mean": round(mean, 4), "frac_over": round(frac, 6)} for f, mx, mean, frac in rows]},
              open(f"{d}/check.json", "w"), indent=1)
    if a.diff and rows:
        tiles = []
        for f, mx, mean, frac in rows[:6]:
            g_ = cv2.imread(f"{d}/f{f:04d}.png")
            amp = np.clip(cv2.absdiff(ims[f], g_).astype(np.float32) * 40, 0, 255).astype(np.uint8)
            t = np.hstack([cv2.resize(ims[f], (270, 480)), cv2.resize(amp, (270, 480), interpolation=cv2.INTER_AREA)])
            cv2.putText(t, f"{f} max {mx} mean {mean:.3f}", (5, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)
            tiles.append(t)
        while len(tiles) % 3: tiles.append(np.zeros_like(tiles[0]))
        p = f"{edit_env.ROOT}/v{a.n}/frames/golden_diff.jpg"
        cv2.imwrite(p, np.vstack([np.hstack(tiles[i:i + 3]) for i in range(0, len(tiles), 3)]), [cv2.IMWRITE_JPEG_QUALITY, 88]); print("  diff sheet:", p)
    print("PASS" if not bad else f"FAIL: {len(bad)} frames over the gate: {bad[:20]}")
    sys.exit(0 if not bad else 1)

if __name__ == "__main__":
    main()
