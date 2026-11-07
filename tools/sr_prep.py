"""Restore + 2x upscale every source frame an edit actually uses (Real-ESRGAN compact via ONNX Runtime; tools/srnet.py).

  python3 tools/sr_prep.py N [--count] [--threads 3]

Only the horizontal band each frame is cropped from (its 9:16 window over the whole shot, plus margin) is processed.
Writes vN/sr/{pack}_{frame:06d}.jpg (2x, JPEG q97 4:4:4) and vN/sr/index.json {"pack:frame": [x0, x1]} (source px).
Re-running only processes frames whose band is missing or too narrow. The renderer uses a band when it covers the crop.
"""
import os, sys, json, math, bisect, time, importlib
import numpy as np, cv2

N = sys.argv[1]; ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = f"{ROOT}/v{N}/work"; OUT = f"{ROOT}/v{N}/sr"
sys.path.insert(0, WORK); sys.path.insert(0, f"{ROOT}/tools")
sys.argv = [sys.argv[0]] + sys.argv[2:]
COUNT = "--count" in sys.argv
THREADS = int(sys.argv[sys.argv.index("--threads") + 1]) if "--threads" in sys.argv else 3

R = importlib.import_module(f"render{N}"); E = R.E
R.load(); R.init_hits()
R.RAW_TRK.update(json.load(open(f"{WORK}/tracks{N}.json")))
z = np.load(f"{WORK}/seg{N}.npz"); R.SEG.update({k: z[k] for k in z.files})


def frames_for(s, f):
    """the source frames render_shot(s, f) samples (mirrors source_img / sample)."""
    pk = s["src"]; fps = E.SRC[pk][1]; U = R.UNIQ[pk]
    t, u, sp = R.src_time(s, f)
    if sp > 1.7:
        K = int(min(7, max(3, round(sp * 2)))); span = 0.5 / R.FPS * sp
        ts, mode = [t + (j / (K - 1) - 0.5) * span for j in range(K)], "hold"
    else:
        ts, mode = [t], s.get("interp", "hold")
    out = set()
    for tt in ts:
        i = R.clamp(bisect.bisect_right(U, tt * fps + 0.3) - 1, 0, len(U) - 1); out.add(U[i])
        if mode != "hold" and i < len(U) - 1: out.add(U[i + 1])
    return out, t, u


need = {}
for s in E.SHOTS:
    if "src" not in s or s.get("fit"): continue
    sw = E.SRC[s["src"]][2]
    for f in range(s["f0"], s["f1"]):
        ks, t, u = frames_for(s, f)
        cx, cy, ch = R.frame_geom(s, f, t, u); cw = ch * 9 / 16; m = 16 + 12
        x0, x1 = max(0, int(cx - cw / 2 - m)), min(sw, int(math.ceil(cx + cw / 2 + m)))
        for k in ks:
            a, b = need.get((s["src"], k), (10 ** 6, -1)); need[(s["src"], k)] = (min(a, x0), max(b, x1))
os.makedirs(OUT, exist_ok=True)
ip = f"{OUT}/index.json"; index = json.load(open(ip)) if os.path.exists(ip) else {}
todo = []
for (pk, k), (a, b) in sorted(need.items(), key=lambda kv: (kv[0][0], kv[0][1])):
    a, b = a - a % 4, min(E.SRC[pk][2], b + (-b) % 4)
    have = index.get(f"{pk}:{k}")
    if have and have[0] <= a and have[1] >= b and os.path.exists(f"{OUT}/{pk}_{k:06d}.jpg"): continue
    if have: a, b = min(a, have[0]), max(b, have[1])
    todo.append((pk, k, a, b))
px = sum((b - a) * 720 for _, _, a, b in todo)
print(f"frames used {len(need)}, to process {len(todo)}, mean band {px / max(1, len(todo)) / 720:.0f} px", flush=True)
if COUNT: sys.exit(0)

import srnet
sess = srnet.onnx_session(THREADS)
t0 = time.time()
for i, (pk, k, a, b) in enumerate(todo):
    band = np.ascontiguousarray(R.FR[(pk, k)][:, a:b])
    cv2.imwrite(f"{OUT}/{pk}_{k:06d}.jpg", srnet.sr2(sess, band),
                [cv2.IMWRITE_JPEG_QUALITY, 97, cv2.IMWRITE_JPEG_SAMPLING_FACTOR, cv2.IMWRITE_JPEG_SAMPLING_FACTOR_444])
    index[f"{pk}:{k}"] = [a, b]
    if i % 10 == 9 or i == len(todo) - 1:
        json.dump(index, open(ip + ".tmp", "w")); os.replace(ip + ".tmp", ip)
        el = time.time() - t0; print(f"{i + 1}/{len(todo)}  {el / (i + 1):.2f} s/frame  eta {el / (i + 1) * (len(todo) - i - 1) / 60:.1f} min", flush=True)
print("done", flush=True)
