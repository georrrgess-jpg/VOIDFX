"""Review pack from the ENCODED edit: one row of stills per transition, set piece and the loop wrap (efficiency update,
2026-11-08). Replaces hand-picked sheet lists (v13 rev 1 used 19 `sheet:` calls): every designed moment is covered,
from the file that ships, in one decode (~20 s), with no render server.

  python3 tools/review.py N [--file OUT.mp4] [--per 8]

Rows: each cut's transition window from TR2 (pre/post frames), each SET_PIECES entry, and the wrap (the last frames,
then frame 0 onwards). Frames that faceqc or motionqc flagged (vN/work/faceqc.json, motionqc.json, when present) get a
red border. Writes vN/frames/review_01.jpg ... and prints the list. `build.sh N qc` runs it alongside the QC passes.
"""
import os, sys, json, argparse, subprocess
import numpy as np, cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edit_env

TW, TH = 135, 240

def rows_for(n, E, per):
    R = edit_env.load_edit(n, setup=False); TR2 = getattr(R, "TR2", {}); rows = []
    for s in E.SHOTS[1:]:
        t = s.get("tin") or "cut"; pre, post = (TR2[t][1], TR2[t][2]) if t in TR2 else (6, 6)
        a, b = max(0, s["f0"] - pre - 2), min(E.DUR_F - 1, s["f0"] + post + 2)
        rows.append((f"{t} -> {s['n']}  (cut {s['f0']})", np.linspace(a, b, per).round().astype(int).tolist()))
    for name, t0, t1 in getattr(E, "SET_PIECES", []):
        a, b = int(round(t0 * E.FPS)), min(E.DUR_F - 1, int(round(t1 * E.FPS)))
        rows.append((f"SET PIECE {name}  ({a}-{b})", np.linspace(a, b, per).round().astype(int).tolist()))
    k = per // 2
    rows.append(("LOOP wrap: last frames | frame 0 ...", list(range(E.DUR_F - k * 3, E.DUR_F, 3)) + list(range(0, k * 3, 3))))
    return rows

def flagged(n):
    w = edit_env.work_dir(n); out = set()
    try:
        fq = json.load(open(f"{w}/faceqc.json"))
        for r in fq.get("runs", []):
            if r: out.update(range(min(r), max(r) + 1))
    except Exception: pass
    try:
        mq = json.load(open(f"{w}/motionqc.json"))
        for p in mq.get("pops", []):
            if isinstance(p, dict) and str(p.get("kind", "")).upper() == "UNEXPLAINED": out.add(p["f"])
    except Exception: pass
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("n", type=int); ap.add_argument("--file"); ap.add_argument("--per", type=int, default=8)
    a = ap.parse_args(); E = edit_env.edl(a.n)
    mp4 = a.file or f"{edit_env.ROOT}/v{a.n}/out/{E.SLUG}_voidfx_9x16.mp4"
    rows = rows_for(a.n, E, a.per); need = {f for _, fs in rows for f in fs}; bad = flagged(a.n)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", mp4, "-vf", f"scale={TW}:{TH}:flags=area", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                         stdout=subprocess.PIPE)
    sz = TW * TH * 3; ims = {}; f = 0
    while True:
        b = p.stdout.read(sz)
        if len(b) < sz: break
        if f in need: ims[f] = np.frombuffer(b, np.uint8).reshape(TH, TW, 3).copy()
        f += 1
    p.wait()
    out_dir = f"{edit_env.ROOT}/v{a.n}/frames"; os.makedirs(out_dir, exist_ok=True)
    for old in [x for x in os.listdir(out_dir) if x.startswith("review_") and x.endswith(".jpg")]: os.remove(f"{out_dir}/{old}")
    per_sheet = 6; files = []
    for si in range(0, len(rows), per_sheet):
        chunk = rows[si:si + per_sheet]; sheet = np.full((len(chunk) * (TH + 26), a.per * TW, 3), 18, np.uint8)
        for r, (label, fs) in enumerate(chunk):
            y = r * (TH + 26)
            cv2.putText(sheet, label, (6, y + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (235, 235, 235), 1, cv2.LINE_AA)
            for c, fr in enumerate(fs[:a.per]):
                im = ims.get(fr, np.zeros((TH, TW, 3), np.uint8)).copy()
                if fr in bad: cv2.rectangle(im, (0, 0), (TW - 1, TH - 1), (40, 40, 230), 3)
                cv2.putText(im, str(fr), (4, TH - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
                sheet[y + 26:y + 26 + TH, c * TW:(c + 1) * TW] = im
        fn = f"{out_dir}/review_{si // per_sheet + 1:02d}.jpg"; cv2.imwrite(fn, sheet, [cv2.IMWRITE_JPEG_QUALITY, 88]); files.append(fn)
    print(f"review pack: {len(rows)} rows ({len(E.SHOTS) - 1} transitions, {len(getattr(E, 'SET_PIECES', []))} set pieces, the wrap) "
          f"in {len(files)} sheets: {os.path.relpath(out_dir, edit_env.ROOT)}/review_01..{len(files):02d}.jpg; {len(bad & need)} flagged frames boxed red")

if __name__ == "__main__":
    main()
