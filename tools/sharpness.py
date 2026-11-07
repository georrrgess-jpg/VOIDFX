"""Sharpness check: is a shot going to look soft? (Studio 1's version of the rule from Studio 2's DRACULA notes.)

  python3 tools/sharpness.py packs          # every pack in src/: resolution, fps, bitrate, bits per pixel, native detail
  python3 tools/sharpness.py N              # edit vN: per shot, the enlargement (from the EDL) and, if the encoded MP4
                                            # exists, the measured sharpness of the finished shot; flags the soft ones
  python3 tools/sharpness.py N --src        # before rendering: each shot's source frames, cropped to its 9:16 window and
                                            # enlarged like the edit will, ranked; flags the soft ones (pick replacements)

Why: every pack is 720p (including the ones labelled 4K). A 9:16 window uses about 405x720 source pixels, so every shot is
enlarged ~2.67x before any zoom; z adds to it (z 1.10 -> 2.93x, z 1.30 -> 3.47x). Heavy compression (low bits per pixel)
removes the detail that restoration (tools/sr_prep.py) could otherwise sharpen.

Measures (contrast-independent):
  detail = sqrt(hf / mf) per tile (hf = luma - blur 1px, mf = blur 1px - blur 4px) on a half-res copy, 80th percentile over
           the tiles with real content, in the region where faces sit (x 15-85 %, y 8-68 %): it scores the in-focus
           subject, so a shallow depth-of-field background does not read as soft. Lower = softer.
  abs    = mean |L - blur 1.2| / mean |L - blur 8| (the Dexter studio's absolute scale, brightness-independent): on a
           finished 1080x1920 MP4, about 0.30 or more reads sharp and under 0.20 reads soft. It is comparable across edits;
           `detail` is compared within an edit (vs median).
Flags: enlargement > 2.95x (more than ~10 % zoom on a 720p pack), SOFT when a shot is below 0.80x the edit's median detail
(or, on the finished MP4, under 0.20 on the absolute scale), LOWBIT when its pack is under 800 kb/s.
Merged 2026-11-07 (pipeline v2, WP0) from both studios' tools: the Flash studio's tile/percentile detail and modes, the Dexter
studio's absolute scale and LOWBIT. Writes vN/work/sharpness.json (or sharpness_src.json).
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


def detail_abs(gray):
    """the Dexter studio's absolute scale: fine detail over coarse structure (|L - blur 1.2| / |L - blur 8|)."""
    L = gray.astype(np.float32) / 255
    return float(np.abs(L - cv2.GaussianBlur(L, (0, 0), 1.2)).mean() / (np.abs(L - cv2.GaussianBlur(L, (0, 0), 8)).mean() + 1e-4))


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
    meas = {}; absm = {}; kb = {}
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
                if g.mean() > 20:
                    meas.setdefault(want[f], []).append(detail(g[int(H_ * 0.08):int(H_ * 0.68), int(W_ * 0.15):int(W_ * 0.85)]))
                absm.setdefault(want[f], []).append(detail_abs(g))
            f += 1
    med = float(np.nanmedian([np.nanmedian(v) for v in meas.values()])) if meas else None
    res = []
    print(f"{'shot':10s} {'src':4s} {'max z':>6s} {'enlarge':>8s} {'detail':>7s} {'vs median':>9s} {'abs':>6s} {'kbps':>6s}  flags")
    for s in E.SHOTS:
        src = s.get("src")
        if not src or src not in E.SRC: continue
        sh = E.SRC[src][3]; zmax = max(v for _, v in s.get("z", [(0, 1.0)]))
        enl = 1920.0 / sh * zmax
        d = float(np.nanmedian(meas[s["n"]])) if s["n"] in meas else None
        rel = d / med if (d is not None and med) else None
        ab = float(np.median(absm[s["n"]])) if s["n"] in absm else None
        if src not in kb: kb[src] = probe(E.SRC[src][0])[3] / 1000
        flags = []
        if enl > 2.95: flags.append(f"zoom {100 * (zmax - 1):.0f}% on {sh}p")
        if (rel is not None and rel < 0.80) or (ab is not None and ab < 0.20): flags.append("SOFT")
        if kb[src] < 800: flags.append("LOWBIT")
        res.append(dict(n=s["n"], src=src, zmax=zmax, enlarge=enl, detail=d, rel=rel, abs=ab, kbps=kb[src], flags=flags))
        print(f"{s['n']:10s} {src:4s} {zmax:6.2f} {enl:7.2f}x " + (f"{d:7.3f} {rel:8.2f}x" if d is not None else f"{'-':>7s} {'-':>9s}")
              + (f" {ab:6.3f}" if ab is not None else f" {'-':>6s}") + f" {kb[src]:6.0f}  " + ", ".join(flags))
    json.dump(dict(median=med, shots=res), open(f"{ROOT}/v{n}/work/sharpness.json", "w"), indent=1)
    soft = [r["n"] for r in res if "SOFT" in r["flags"] or any(f.startswith("zoom") for f in r["flags"])]
    print("flagged:", soft if soft else "none")


def src_rank(n):
    """rank the EDL's shots by the in-focus detail of their source frames, cropped and enlarged as the edit will be."""
    sys.path.insert(0, f"{ROOT}/v{n}/work"); sys.argv = [sys.argv[0]]
    E = importlib.import_module(f"edl{n}"); res = []; caps = {}
    for s in E.SHOTS:
        src = s.get("src")
        if not src or src not in E.SRC: continue
        path, fps, sw, sh = E.SRC[src]
        cap = caps.setdefault(src, cv2.VideoCapture(path))
        ks = s["tmap"]; ts = [ks[int(len(ks) * q)][1] if len(ks) > 2 else ks[0][1] + (ks[-1][1] - ks[0][1]) * q for q in (0.25, 0.5, 0.75)]
        zmax = max(v for _, v in s.get("z", [(0, 1.0)])); ch = sh / zmax; cw = ch * 9 / 16
        cx = float(np.mean(s["cx"])) if s.get("cx") else sw / 2
        x0 = int(max(0, min(sw - cw, cx - cw / 2))); y0 = int((sh - ch) / 2)
        ds = []
        for t in ts:
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, fr = cap.read()
            if not ok: continue
            crop = fr[y0:y0 + int(ch), x0:x0 + int(cw)]
            up = cv2.resize(crop, (1080, 1920), interpolation=cv2.INTER_CUBIC)
            g = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY)
            if g.mean() > 20:
                d_ = detail(g[int(1920 * 0.08):int(1920 * 0.68), int(1080 * 0.15):int(1080 * 0.85)])
                if d_ == d_: ds.append(d_)
        kbps = probe(path)[3] / 1000
        res.append(dict(n=s["n"], src=src, zmax=zmax, enlarge=1920.0 / sh * zmax, kbps=kbps, detail=float(np.median(ds)) if ds else None))
    med = float(np.median([r["detail"] for r in res if r["detail"] is not None]))
    print(f"{'shot':10s} {'src':4s} {'enlarge':>8s} {'detail':>7s} {'vs median':>9s}  flags   (source frames, cubic-enlarged; face-centred crops use the frame centre unless cx is set)")
    for r in sorted(res, key=lambda r: r["detail"] if r["detail"] is not None else 9):
        rel = r["detail"] / med if r["detail"] is not None else None; r["rel"] = rel
        fl = (["SOFT"] if rel is not None and rel < 0.80 else []) + ([f"zoom {100 * (r['zmax'] - 1):.0f}%"] if r["enlarge"] > 2.95 else []) \
             + (["LOWBIT"] if r["kbps"] < 800 else [])                                         # the Dexter studio's flag: pack under 800 kb/s
        r["flags"] = fl
        print(f"{r['n']:10s} {r['src']:4s} {r['enlarge']:7.2f}x " + (f"{r['detail']:7.3f} {rel:8.2f}x" if rel else "      -         -") + "  " + ", ".join(fl))
    json.dump(dict(median=med, shots=res), open(f"{ROOT}/v{n}/work/sharpness_src.json", "w"), indent=1)


if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else "packs"
    if a == "packs": packs()
    elif "--src" in sys.argv: src_rank(a.lstrip("v"))
    else: edit(a.lstrip("v"))
