"""Golden reference frames: the regression harness for engine changes (pipeline v2, WP1).

  python3 tools/golden.py N --save          render the reference frames of vN and store them in vN/work/golden/ (PNG, not in git)
  python3 tools/golden.py N --check         render them again and compare with the stored set
  python3 tools/golden.py N --check --frames 0,505,1350     only these frames
  python3 tools/golden.py N --cachetest 454:520   cache equivalence: render the range warm (one worker, in order, as the
                                            contiguous scheduler does) and cold (every frame in a fresh process); must match
  options: --workers 4 (default), --tag NAME (store/compare a named set, e.g. --tag before)

The frame list is fixed per edit, from its EDL: frame 0, the last 3 frames, every cut (the transition's centre), the middle
of every shot, the drop, and any set-piece peaks the EDL lists in GOLDEN_EXTRA (a list of frame numbers). Rendering uses the edit's own renderer exactly as `renderN.py stills` does (tracks + mattes
loaded), at full resolution, in a pool of workers (fork, so results don't depend on which worker renders which frame).

Pass rule (guardrail §2.8 of the plan): every frame within max |diff| <= 2/255 and mean |diff| < 0.2/255; anything else fails
and lists the frames. Exit code 0 = pass, 1 = fail. Writes vN/work/golden/report.json.
"""
import os, sys, json, time, importlib
import numpy as np, cv2
from multiprocessing import Pool

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARGV = sys.argv[:]                                         # the renderer import replaces sys.argv below
VALUED = ("--frames", "--workers", "--tag", "--cachetest")
args = [a for i, a in enumerate(sys.argv[1:], 1) if not a.startswith("--") and sys.argv[i - 1] not in VALUED]
n = args[0].lstrip("v")
def opt(k, d=None): return ARGV[ARGV.index(k) + 1] if k in ARGV else d
SAVE, CHECK = "--save" in ARGV, "--check" in ARGV
WORKERS = int(opt("--workers", 4)); TAG = opt("--tag", "golden")
WORK = f"{ROOT}/v{n}/work"; GD = f"{WORK}/golden/{TAG}" if TAG != "golden" else f"{WORK}/golden"
os.chdir(WORK); sys.path.insert(0, WORK)
sys.argv = [sys.argv[0], "stills"]
R = importlib.import_module(f"render{n}"); E = R.E
R.load(); R.init_hits()
R.RAW_TRK.update(json.load(open(f"{WORK}/tracks{n}.json")))
if os.path.exists(f"{WORK}/seg{n}.npz"):
    z = np.load(f"{WORK}/seg{n}.npz"); R.SEG.update({k: z[k] for k in z.files})

def frame_list():
    N = E.DUR_F; fs = {0, N - 3, N - 2, N - 1}
    for s in E.SHOTS:
        fs.add(s["f0"]); fs.add((s["f0"] + s["f1"]) // 2)
    for k in ("HDROP", "DROP_HB"):
        if hasattr(E, k) and hasattr(E, "fh"):
            try: fs.add(E.fh(getattr(E, k)))
            except Exception: pass
    fs.update(getattr(E, "GOLDEN_EXTRA", []))
    return sorted(f for f in fs if 0 <= f < N)

def work(f):
    return f, R.render(f)

def work_block(fs):
    return [(f, R.render(f)) for f in fs]

def cachetest(a, b):
    """warm (one worker renders a..b in order, caches filling) vs cold (each frame in a fresh fork, empty caches)."""
    fs = list(range(a, b + 1)); t0 = time.time()
    with Pool(1) as p: warm = dict(p.map(work_block, [fs])[0])
    tw = time.time() - t0; t0 = time.time()
    with Pool(WORKERS, maxtasksperchild=1) as p: cold = dict(p.map(work, fs, chunksize=1))
    tc = time.time() - t0; worst = 0; bad = []
    for f in fs:
        d = np.abs(warm[f].astype(np.int16) - cold[f].astype(np.int16)); mx = int(d.max()); worst = max(worst, mx)
        if mx > 2 or d.mean() >= 0.2: bad.append((f, mx, round(float(d.mean()), 3)))
    print(f"v{n} cache test {a}..{b}: {len(fs)} frames; warm {tw:.1f} s (1 worker), cold {tc:.1f} s ({WORKERS} workers, fresh process each); "
          f"worst max |diff| {worst}/255 -> " + ("PASS" if not bad else f"FAIL {bad[:8]}"))
    sys.exit(0 if not bad else 1)

if __name__ == "__main__":
    if opt("--cachetest"): cachetest(*[int(x) for x in opt("--cachetest").split(":")])
    frames = [int(x) for x in opt("--frames").split(",")] if opt("--frames") else frame_list()
    t0 = time.time()
    with Pool(WORKERS) as p: out = dict(p.map(work, frames, chunksize=1))
    dt = time.time() - t0
    os.makedirs(GD, exist_ok=True)
    if SAVE:
        for f, im in out.items(): cv2.imwrite(f"{GD}/{f:05d}.png", im)
        json.dump(dict(edit=f"v{n}", frames=frames, seconds=round(dt, 1), saved=time.strftime("%Y-%m-%d %H:%M")), open(f"{GD}/index.json", "w"), indent=1)
        print(f"saved {len(frames)} golden frames of v{n} to {GD} in {dt:.1f} s ({dt / len(frames):.2f} s/frame on {WORKERS} workers)")
        sys.exit(0)
    bad = []; worst_max = 0; worst_mean = 0.0; rows = []
    for f in frames:
        ref = cv2.imread(f"{GD}/{f:05d}.png")
        if ref is None: bad.append((f, "missing")); continue
        d = np.abs(out[f].astype(np.int16) - ref.astype(np.int16))
        mx, mn = int(d.max()), float(d.mean()); worst_max = max(worst_max, mx); worst_mean = max(worst_mean, mn)
        rows.append(dict(frame=f, max=mx, mean=round(mn, 4)))
        if mx > 2 or mn >= 0.2: bad.append((f, f"max {mx}, mean {mn:.3f}"))
    ok = not bad
    json.dump(dict(edit=f"v{n}", tag=TAG, frames=len(frames), seconds=round(dt, 1), worst_max=worst_max, worst_mean=round(worst_mean, 4),
                   failed=bad, per_frame=rows), open(f"{GD}/report.json", "w"), indent=1)
    print(f"v{n} golden check ({TAG}): {len(frames)} frames in {dt:.1f} s; worst max |diff| {worst_max}/255, worst mean {worst_mean:.4f}/255 -> "
          + ("PASS" if ok else f"FAIL on {len(bad)} frames: {bad[:8]}"))
    sys.exit(0 if ok else 1)
