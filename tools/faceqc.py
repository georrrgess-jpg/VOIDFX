"""Effects over faces (pipeline v2, WP8): the most common review catch (lightning, rays, particles, suns, streaks or
seams drawn across his face), measured instead of looked for.

  python3 tools/faceqc.py N [--step 2] [--thr 0.10] [--frac 0.03]

For every STEP-th frame outside a transition window it renders the shot's own graded picture (`render_shot`, the same
camera as the final frame, no effects), takes the final frame (from the lossless frame cache if there is one,
otherwise the upload MP4), and compares the two inside his face box (the face track; the matte's head box for
`face=None` shots). A least-squares gain/offset fit absorbs the grade, finish, vignette and fades, so what's left is
light ADDED on the face. A frame is flagged when more than FRAC of the box gains more than THR in luma.
Writes vN/work/faceqc.json and a sheet of the worst frame of each flagged run (box drawn, added light in red) at
vN/frames/faceqc.jpg. The runs are a list for the visual review, not a gate: titles over a face are flagged too.
"""
import os, sys, json, subprocess, argparse
from multiprocessing import Pool
import numpy as np, cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edit_env

R = None; ARGS = None

def face_rect(s, f):
    """screen-space (x0, y0, x1, y1) of the face, or None."""
    W, H = R.W, R.H
    fs = R.face_scr(s, f) if (s.get("face") is not None and hasattr(R, "face_scr")) else None
    if fs:
        x, y, fw = fs[0], fs[1], fs[2]
        box = (x - fw * 0.62, y - fw * 0.80, x + fw * 0.62, y + fw * 0.85)
    elif s.get("seg"):                                       # no face track: the head is the top of the person matte
        try: _, person = R.render_shot(s, f, want_mask=True)
        except Exception: return None
        pm = person[::4, ::4] > 0.5; rows = np.nonzero(pm.sum(1) >= 4)[0]
        if not len(rows): return None
        top = rows[0]; band = pm[top:top + 12]; xs = np.nonzero(band.any(0))[0]
        if not len(xs): return None
        hw = (xs[-1] - xs[0]) / 2 * 4; cx = (xs[0] + xs[-1]) / 2 * 4; y0 = top * 4
        if hw < 40 or person[int(y0):int(y0 + hw * 2.6), int(max(0, cx - hw)):int(cx + hw)].mean() < 0.3: return None
        box = (cx - hw * 1.1, y0, cx + hw * 1.1, y0 + hw * 2.6)
    else: return None
    x0, y0, x1, y1 = (int(max(0, box[0])), int(max(0, box[1])), int(min(W, box[2])), int(min(H, box[3])))
    return (x0, y0, x1, y1) if (x1 - x0) >= 80 and (y1 - y0) >= 80 else None                 # tiny boxes are unreliable

def lum(a): return a[..., 0] * 0.114 + a[..., 1] * 0.587 + a[..., 2] * 0.299

def measure(job):
    f, final = job
    s = R.shot_at(f); rc = face_rect(s, f)
    if rc is None: return {"f": f, "shot": s["n"], "skip": "no face"}
    x0, y0, x1, y1 = rc
    base = R.render_shot(s, f)
    if isinstance(base, tuple): base = base[0]
    lb = lum(base[y0:y1, x0:x1]).astype(np.float64).ravel()
    lf = lum(final[y0:y1, x0:x1].astype(np.float32) / 255).astype(np.float64).ravel()
    cc = float(np.corrcoef(lb, lf)[0, 1]) if lb.std() > 1e-4 and lf.std() > 1e-4 else 0.0
    if cc < 0.4:                                             # a different picture in the box (a cover, the loop landing)
        return {"f": f, "shot": s["n"], "box": rc, "skip": f"replaced (r {cc:.2f})"}
    A = np.stack([lb, np.ones_like(lb)], 1)
    (a, c), *_ = np.linalg.lstsq(A, lf, rcond=None)
    if not (0.3 < a < 3.0):                                  # the face is gone (a fade to black, a full cover): not "added light"
        return {"f": f, "shot": s["n"], "box": rc, "skip": f"fit gain {a:.2f}"}
    r = lf - (a * lb + c)
    p = float((r > ARGS.thr).mean())
    return {"f": f, "shot": s["n"], "box": rc, "frac": round(p, 4), "peak": round(float(np.percentile(r, 99.5)), 3), "gain": round(float(a), 3)}

def transition_frames():
    ex = set(); TR = getattr(R, "TR2", {})
    for s in R.SHOTS:
        t = s.get("tin")
        if t in TR: ex.update(range(s["f0"] - TR[t][1], s["f0"] + TR[t][2]))
        elif t: ex.update(range(s["f0"] - 8, s["f0"] + 12))
    return ex

def finals(n, frames):
    """yield (f, uint8 frame) for the wanted frames, from the frame cache (exact) or the upload MP4."""
    E = R.E; mkv = f"{edit_env.work_dir(n)}/cache/frames.mkv"
    src = mkv if os.path.exists(mkv) else f"{edit_env.ROOT}/v{n}/out/{E.SLUG}_voidfx_9x16.mp4"
    want = set(frames); sz = E.W * E.H * 3
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    f = 0
    while True:
        b = p.stdout.read(sz)
        if len(b) < sz: break
        if f in want: yield f, np.frombuffer(b, np.uint8).reshape(E.H, E.W, 3)
        f += 1
    p.wait()

def main():
    global R, ARGS
    ap = argparse.ArgumentParser(); ap.add_argument("n", type=int); ap.add_argument("--step", type=int, default=2)
    ap.add_argument("--thr", type=float, default=0.10); ap.add_argument("--frac", type=float, default=0.03)
    ARGS = ap.parse_args(); n = ARGS.n
    R = edit_env.load_edit(n); R.E = edit_env.edl(n)
    ex = transition_frames()
    ex.update(range(R.E.DUR_F - 12, R.E.DUR_F))                                            # the loop landing builds frame 0's image
    frames = [f for f in range(0, R.E.DUR_F, ARGS.step) if f not in ex]
    with Pool(4) as pool: res = list(pool.imap(measure, finals(n, frames), chunksize=2))
    res.sort(key=lambda r: r["f"])
    flagged = [r for r in res if r.get("frac", 0) > ARGS.frac]
    runs = []
    for r in flagged:
        if runs and r["shot"] == runs[-1][-1]["shot"] and r["f"] - runs[-1][-1]["f"] <= 3 * ARGS.step: runs[-1].append(r)
        else: runs.append([r])
    checked = [r for r in res if "frac" in r]
    print(f"faces vs effects: {len(checked)} frames with a face checked ({len(res) - len(checked)} without a face or covered; "
          f"{len(ex)} transition frames left out); {len(flagged)} flagged in {len(runs)} run(s)")
    for run in runs:
        w = max(run, key=lambda r: r["frac"])
        print(f"  {run[0]['shot']:12s} frames {run[0]['f']}-{run[-1]['f']}: up to {w['frac'] * 100:.1f} % of the face box gains > {ARGS.thr} luma (worst {w['f']})")
    json.dump({"thr": ARGS.thr, "frac": ARGS.frac, "runs": [[r["f"] for r in run] for run in runs], "frames": res},
              open(f"{edit_env.work_dir(n)}/faceqc.json", "w"), indent=0)
    if runs:
        tiles = []
        worst = [max(run, key=lambda r: r["frac"]) for run in runs][:18]
        got = dict(finals(n, [w["f"] for w in worst]))
        for w in worst:
            im = got[w["f"]].copy(); x0, y0, x1, y1 = w["box"]
            base = R.render_shot(R.shot_at(w["f"]), w["f"]); base = base[0] if isinstance(base, tuple) else base
            lb = lum(base); lf = lum(im.astype(np.float32) / 255); rr = lf - (w["gain"] * lb)
            m = np.zeros(lb.shape, bool); m[y0:y1, x0:x1] = True; rr = rr - np.median(rr[m])
            hot = (rr > ARGS.thr) & m; im[hot] = (0.4 * im[hot] + [0, 0, 153]).astype(np.uint8)
            cv2.rectangle(im, (x0, y0), (x1, y1), (0, 255, 255), 3)
            t = cv2.resize(im, (270, 480), interpolation=cv2.INTER_AREA)
            cv2.putText(t, f"{w['f']} {w['shot']} {w['frac'] * 100:.0f}%", (4, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA); tiles.append(t)
        while len(tiles) % 6: tiles.append(np.zeros_like(tiles[0]))
        p = f"{edit_env.ROOT}/v{n}/frames/faceqc.jpg"; os.makedirs(os.path.dirname(p), exist_ok=True)
        cv2.imwrite(p, np.vstack([np.hstack(tiles[i:i + 6]) for i in range(0, len(tiles), 6)]), [cv2.IMWRITE_JPEG_QUALITY, 88]); print("  sheet:", p)

if __name__ == "__main__":
    main()
