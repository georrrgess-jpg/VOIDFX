"""Sharpness check: is a shot going to look soft? (Studio 1's version of the rule from Studio 2's DRACULA notes.)

  python3 tools/sharpness.py packs          # every pack in src/: resolution, fps, bitrate, bits per pixel, native detail
  python3 tools/sharpness.py N              # edit vN: per shot, the enlargement (from the EDL) and, if the encoded MP4
                                            # exists, the measured sharpness of the finished shot; flags the soft ones

Why: every pack is 720p (including the ones labelled 4K). A 9:16 window uses about 405x720 source pixels, so every shot is
enlarged ~2.67x before any zoom; z adds to it (z 1.10 -> 2.93x, z 1.30 -> 3.47x). Heavy compression (low bits per pixel)
removes the detail that restoration (tools/sr_prep.py) could otherwise sharpen.

Measures (contrast-independent):
  detail = sqrt(hf / mf) per tile (hf = luma - blur 1px, mf = blur 1px - blur 4px) on a half-res copy, 80th percentile over
           the tiles with real content, in the region where faces sit (x 15-85 %, y 8-68 %): it scores the in-focus
           subject, so a shallow depth-of-field background does not read as soft. Lower = softer.
Flags: enlargement > 2.95x (more than ~10 % zoom on a 720p pack), or a finished shot below 0.80x the edit's median detail.
Writes vN/work/sharpness.json.
"""
import os, sys, json, glob, math, subprocess, importlib
import numpy as np, cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def detail(gray, tiles=6):
    """the in-focus detail: hf/mf energy ratio per tile, the 80th percentile over tiles with real content (so a shallow
    depth-of-field background does not read as a soft shot)."""
    g = cv2.resize(gray, (gray.shape[1] // 2, gray.shape[0] // 2), interpolation=cv2.INTER_AREA).astype(np.float32)
    b1 = cv2.GaussianBlur(g, (0, 0), 1.0); b4 = cv2.GaussianBlur(g, (0, 0), 4.0)
    hf, mf = (g - b1) ** 2, (b1 - b4) ** 2
    H_, W_ = g.shape; vals = []
    for i in range(tiles):
        for j in range(tiles):
            ys, xs = slice(i * H_ // tiles, (i + 1) * H_ // tiles), slice(j * W_ // tiles, (j + 1) * W_ // tiles)
            m = mf[ys, xs].mean()
            if m > 4.0: vals.append(math.sqrt(hf[ys, xs].mean() / m))
    return float(np.percentile(vals, 80)) if vals else float("nan")


def probe(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate,bit_rate",
                        "-show_entries", "format=duration,bit_rate", "-of", "json", p], capture_output=True, text=True)
    j = json.loads(r.stdout or "{}"); st = (j.get("streams") or [{}])[0]; fm = j.get("format", {})
    num, den = (st.get("r_frame_rate", "0/1").split("/") + ["1"])[:2]
    fps = float(num) / max(1.0, float(den))
    br = float(st.get("bit_rate") or fm.get("bit_rate") or 0)
    return int(st.get("width", 0)), int(st.get("height", 0)), fps, br, float(fm.get("duration", 0) or 0)


def packs():
    rows = []
    for p in sorted(glob.glob(f"{ROOT}/src/*.mp4") + glob.glob(f"{ROOT}/src/*.mov")):
        w, h, fps, br, dur = probe(p)
        if not w: continue
        cap = cv2.VideoCapture(p); n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); ds = []
        for k in np.linspace(n * 0.05, n * 0.95, 24).astype(int):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(k)); ok, fr = cap.read()
            if ok and fr.mean() > 25: ds.append(detail(cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)))
        bpp = br / max(1, w * h * fps)
        rows.append((os.path.basename(p), w, h, fps, br / 1e6, bpp, float(np.median(ds)) if ds else float("nan")))
    print(f"{'pack':48s} {'size':>9s} {'fps':>6s} {'Mb/s':>6s} {'bits/px':>8s} {'detail':>7s}")
    for r in rows:
        print(f"{r[0]:48s} {r[1]:4d}x{r[2]:<4d} {r[3]:6.2f} {r[4]:6.2f} {r[5]:8.4f} {r[6]:7.3f}")
    return rows


def edit(n):
    sys.path.insert(0, f"{ROOT}/v{n}/work"); sys.argv = [sys.argv[0]]
    E = importlib.import_module(f"edl{n}")
    out_ = f"{ROOT}/v{n}/out/{E.SLUG}_voidfx_9x16.mp4"
    meas = {}
    if os.path.exists(out_):
        cap = cv2.VideoCapture(out_); f = 0; want = {}
        for s in E.SHOTS:
            a, b = s["f0"] + (s["f1"] - s["f0"]) // 4, s["f0"] + 3 * (s["f1"] - s["f0"]) // 4
            for k in range(a, max(a + 1, b), 3): want[k] = s["n"]
        while True:
            ok, fr = cap.read()
            if not ok: break
            if f in want:
                g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY); H_, W_ = g.shape
                if g.mean() > 20: meas.setdefault(want[f], []).append(detail(g[int(H_ * 0.08):int(H_ * 0.68), int(W_ * 0.15):int(W_ * 0.85)]))
            f += 1
    med = float(np.median([np.median(v) for v in meas.values()])) if meas else None
    res = []
    print(f"{'shot':10s} {'src':4s} {'max z':>6s} {'enlarge':>8s} {'detail':>7s} {'vs median':>9s}  flags")
    for s in E.SHOTS:
        src = s.get("src")
        if not src or src not in E.SRC: continue
        sh = E.SRC[src][3]; zmax = max(v for _, v in s.get("z", [(0, 1.0)]))
        enl = 1920.0 / sh * zmax
        d = float(np.median(meas[s["n"]])) if s["n"] in meas else None
        rel = d / med if (d is not None and med) else None
        flags = []
        if enl > 2.95: flags.append(f"zoom {100 * (zmax - 1):.0f}% on {sh}p")
        if rel is not None and rel < 0.80: flags.append("SOFT")
        res.append(dict(n=s["n"], src=src, zmax=zmax, enlarge=enl, detail=d, rel=rel, flags=flags))
        print(f"{s['n']:10s} {src:4s} {zmax:6.2f} {enl:7.2f}x " + (f"{d:7.3f} {rel:8.2f}x" if d is not None else f"{'-':>7s} {'-':>9s}") + "  " + ", ".join(flags))
    json.dump(dict(median=med, shots=res), open(f"{ROOT}/v{n}/work/sharpness.json", "w"), indent=1)
    soft = [r["n"] for r in res if r["flags"]]
    print("flagged:", soft if soft else "none")


if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else "packs"
    packs() if a == "packs" else edit(a.lstrip("v"))
