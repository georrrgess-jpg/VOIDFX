"""signoff (pipeline v2, WP9 input): the visual sign-off sheets, pulled from the ENCODED file in one decode.

  python3 tools/signoff.py N           # -> vN/frames/signoff_tr1.jpg ... (6 transitions a page), signoff_loop.jpg,
                                       #    signoff_titles.jpg, signoff_pops.jpg (if motionqc flagged any)

Each transition (and each plain cut) gets one row: before it starts, its middle, the frame before the cut, the cut, its
middle after the cut, and its last frame; each SET_PIECES entry gets a row across its span. The loop page shows the last
second into frames 0-2 (the wrap). The titles page shows each text block as it lands and as it leaves. The pops page shows
every UNEXPLAINED motionqc pop with its neighbours. Frames that faceqc or motionqc flagged are boxed red. (This is the one
review tool since 2026-11-08: the Flash studio's review pack, review.py, is folded in; `build.sh N qc` runs it.)
These pages are what the studio reviews (and what the fresh-eyes critique sees) before a delivery: one look per page
instead of pulling frames by hand.
"""
import os, sys, json, importlib
import numpy as np, cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TW, TH = 180, 320                                                                            # tile (1/6 of 1080x1920)


BAD = set()                                                                                 # frames flagged by faceqc / motionqc
def tile(img, label, f=None):
    t = cv2.resize(img, (TW, TH), interpolation=cv2.INTER_AREA)
    if f in BAD: cv2.rectangle(t, (0, 0), (TW - 1, TH - 1), (40, 40, 230), 4)
    cv2.rectangle(t, (0, 0), (TW, 22), (0, 0, 0), -1)
    cv2.putText(t, label, (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA)
    return t


def row(frames, want, title):
    tiles = [tile(frames[f], str(f) + (" !" if f in BAD else ""), f) if f in frames else np.zeros((TH, TW, 3), np.uint8) for f in want]
    tiles += [np.zeros((TH, TW, 3), np.uint8)] * (6 - len(tiles))                     # every row is 6 tiles wide
    r = np.hstack(tiles)
    bar = np.zeros((26, r.shape[1], 3), np.uint8)
    cv2.putText(bar, title, (6, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    return np.vstack([bar, r])


def main():
    n = sys.argv[1]; w = f"{ROOT}/v{n}/work"; os.chdir(w); sys.path.insert(0, w)
    argv = sys.argv; sys.argv = ["x", "video", "frames/x"]
    E = importlib.import_module(f"edl{n}")
    try: TR = importlib.import_module(f"render{n}").TR2
    except Exception: TR = {}
    sys.argv = argv
    S = E.SHOTS; DUR = getattr(E, "DUR_F", S[-1]["f1"]); FPS = getattr(E, "FPS", 60)
    out_dir = f"{ROOT}/v{n}/frames"; os.makedirs(out_dir, exist_ok=True)
    mp4 = f"{ROOT}/v{n}/out/{E.SLUG}_voidfx_9x16.mp4"

    rows = []                                                                                 # (title, frames)
    for i, s in enumerate(S):
        if i == 0: continue
        t = s.get("tin") or "cut"
        pre, post = (TR[t][1], TR[t][2]) if t in TR else (8, 12)
        f0 = s["f0"]; a = f0 - max(pre, 6); b = f0 + max(post, 6) - 1
        rows.append((f"{s['n']} <- {t}  (pre {pre} / post {post}; cut {f0} = {f0 / FPS:.2f} s)",
                     [max(0, a), max(0, f0 - pre // 2 - 1), max(0, f0 - 1), f0, min(DUR - 1, f0 + post // 2), min(DUR - 1, b)]))
    for name, t0, t1 in getattr(E, "SET_PIECES", []):                                     # each set piece across its span
        a, b = int(round(t0 * FPS)), min(DUR - 1, int(round(t1 * FPS)))
        rows.append((f"SET PIECE {name}  ({a}-{b} = {t0:.2f}-{t1:.2f} s)", [int(x) for x in np.linspace(a, b, 6).round()]))
    BAD.clear()
    try:
        for r in json.load(open(f"{w}/faceqc.json")).get("runs", []):
            if r: BAD.update(range(min(r), max(r) + 1))
    except Exception: pass
    try:
        BAD.update(p["f"] for p in json.load(open(f"{w}/motionqc.json")).get("pops", []) if str(p.get("kind", "")).upper().startswith("UNEXPL"))
    except Exception: pass
    for old in [x for x in os.listdir(out_dir) if x.startswith("signoff_") and x.endswith(".jpg")]: os.remove(f"{out_dir}/{old}")
    loop_f = list(range(DUR - 60, DUR, 6)) + [DUR - 2, DUR - 1, 0, 1, 2]
    tx_rows = []
    for k, tx in enumerate(getattr(E, "TEXT", [])):
        t0 = max(tx["words"][0][1], tx.get("from", -1)); t1 = tx.get("end", t0 + 1)
        fa, fb = int(round(t0 * FPS)) + 8, int(round(t1 * FPS)) - 5
        tx_rows.append((f"{tx.get('style')}: {' '.join(w[0] for w in tx['words'])[:60]}", [max(0, fa), min(DUR - 1, max(fa, fb))]))
    pops = []
    mq = f"{w}/motionqc.json"
    if os.path.exists(mq):
        pops = [p["f"] for p in json.load(open(mq)).get("pops", []) if str(p.get("kind", "")).upper().startswith("UNEXPL")]

    want = set(f for _, fl in rows for f in fl) | set(loop_f) | set(f for _, fl in tx_rows for f in fl) | set(q for p in pops for q in (p - 1, p, p + 1))
    frames = {}; cap = cv2.VideoCapture(mp4); i = 0; last = max(want)
    while i <= last:
        ok, im = cap.read()
        if not ok: break
        if i in want: frames[i] = im
        i += 1

    pages = []
    for p in range(0, len(rows), 6):
        img = np.vstack([row(frames, fl, title) for title, fl in rows[p:p + 6]])
        path = f"{out_dir}/signoff_tr{p // 6 + 1}.jpg"; cv2.imwrite(path, img, [cv2.IMWRITE_JPEG_QUALITY, 85]); pages.append(path)
    img = np.vstack([row(frames, loop_f[:6], "the loop: the last second"), row(frames, loop_f[6:12] if len(loop_f) >= 12 else loop_f[6:], "... the wrap into frame 0")])
    path = f"{out_dir}/signoff_loop.jpg"; cv2.imwrite(path, img, [cv2.IMWRITE_JPEG_QUALITY, 85]); pages.append(path)
    if tx_rows:
        pairs = [tx_rows[k:k + 3] for k in range(0, len(tx_rows), 3)]
        img = np.vstack([row(frames, [f for _, fl in grp for f in fl], " | ".join(t for t, _ in grp)[:150]) for grp in pairs])
        path = f"{out_dir}/signoff_titles.jpg"; cv2.imwrite(path, img, [cv2.IMWRITE_JPEG_QUALITY, 85]); pages.append(path)
    if pops:
        img = np.vstack([row(frames, [p - 1, p, p + 1], f"UNEXPLAINED pop at {p}") for p in pops[:8]])
        path = f"{out_dir}/signoff_pops.jpg"; cv2.imwrite(path, img, [cv2.IMWRITE_JPEG_QUALITY, 85]); pages.append(path)
    nsp = len(getattr(E, "SET_PIECES", []))
    print(f"signoff v{n}: {len(rows) - nsp} transitions and cuts, {nsp} set pieces, {len(tx_rows)} text blocks, {len(pops)} unexplained pops, "
          f"{len(BAD & want)} flagged frames boxed red, from {os.path.basename(mp4)}")
    for p in pages: print("  ", p)


if __name__ == "__main__":
    main()
