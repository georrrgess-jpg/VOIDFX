"""Render server (pipeline v2, WP3): keeps edit N loaded with 4 warm workers, so review sheets don't pay the ~12 s
start-up or render one frame at a time.

  python3 tools/rsrv.py N stills NAME f1 f2 ...     # tiled sheet -> vN/frames/NAME.jpg (6 per row, 270x480 tiles)
  python3 tools/rsrv.py N full f1 f2 ...            # full-resolution PNGs -> vN/frames/full_XXXX.png
  python3 tools/rsrv.py N strip A B [STEP]          # every STEP-th frame (default 2) from A to B in one sheet -> vN/frames/strip_A_B.jpg
  python3 tools/rsrv.py N clip A B                  # 540x960 MP4 with sound -> vN/frames/clip_A_B.mp4
  python3 tools/rsrv.py N auto NAME                 # sheets around every cut (-8 -4 -1 0 3 8) -> vN/frames/NAME_k.jpg
  python3 tools/rsrv.py N stop | status

The first command starts the server in the background. When renderN.py, edlN.py, the tracks or the mattes change,
the server restarts itself before the next command (the layered engine can't be reloaded in place), so a sheet always
shows the current code. Pictures are the engine's own `render(f)`; nothing is approximated.
"""
import os, sys, json, time, socket, subprocess, signal
from multiprocessing import Pool
import numpy as np, cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edit_env

R = None; POOL = None

def sock_path(n): return f"{edit_env.work_dir(n)}/cache/rsrv.sock"

def watched(n):
    w = edit_env.work_dir(n)
    return [f"{w}/render{n}.py", f"{w}/edl{n}.py", f"{w}/tracks{n}.json", f"{w}/seg{n}.npz", f"{edit_env.ROOT}/v{n}/sr/index.json"]

def stamp(n): return [os.path.getmtime(p) if os.path.exists(p) else 0 for p in watched(n)]

# ---- server side -------------------------------------------------------------------------------------------------
def _block(fs): return [R.render(f) for f in fs]

def blocks(frames, size=24):
    out, cur = [], []
    for f in frames:
        if cur and (f != cur[-1] + 1 or R.shot_at(f) is not R.shot_at(cur[-1]) or len(cur) >= size): out.append(cur); cur = []
        cur.append(f)
    if cur: out.append(cur)
    return out

def render_many(frames):
    """render frames on the warm pool: contiguous runs as blocks, scattered frames one per task."""
    bl = blocks(frames); res = {}
    for fs, ims in zip(bl, POOL.imap(_block, bl, chunksize=1)):
        res.update(zip(fs, ims))
    return [res[f] for f in frames]

def sheet(ims, labels, tile=(270, 480), cols=6):
    ts = []
    for im, lb in zip(ims, labels):
        t = cv2.resize(im, tile, interpolation=cv2.INTER_AREA)
        cv2.putText(t, str(lb), (5, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1, cv2.LINE_AA); ts.append(t)
    while len(ts) % cols: ts.append(np.zeros_like(ts[0]))
    return np.vstack([np.hstack(ts[i:i + cols]) for i in range(0, len(ts), cols)])

def handle(n, req):
    E = R.E; fr_dir = f"{edit_env.ROOT}/v{n}/frames"; os.makedirs(fr_dir, exist_ok=True)
    cmd, args = req["cmd"], req["args"]; D = E.DUR_F
    clampf = lambda f: max(0, min(D - 1, int(f)))
    if cmd == "stills":
        name, fs = args[0], [clampf(a) for a in args[1:]]
        p = f"{fr_dir}/{name}.jpg"; cv2.imwrite(p, sheet(render_many(fs), fs), [cv2.IMWRITE_JPEG_QUALITY, 88]); return [p]
    if cmd == "full":
        fs = [clampf(a) for a in args]; out = []
        for f, im in zip(fs, render_many(fs)):
            p = f"{fr_dir}/full_{f:04d}.png"; cv2.imwrite(p, im, [cv2.IMWRITE_PNG_COMPRESSION, 1]); out.append(p)
        return out
    if cmd == "strip":
        a, b = clampf(args[0]), clampf(args[1]); st = int(args[2]) if len(args) > 2 else 2
        fs = list(range(a, b + 1, st)); p = f"{fr_dir}/strip_{a}_{b}.jpg"
        cv2.imwrite(p, sheet(render_many(fs), fs, (216, 384), 8), [cv2.IMWRITE_JPEG_QUALITY, 86]); return [p]
    if cmd == "clip":
        a, b = clampf(args[0]), clampf(args[1]); fs = list(range(a, b + 1))
        out = f"{fr_dir}/clip_{a}_{b}.mp4"; mix = f"{edit_env.ROOT}/v{n}/audio/mix.wav"
        aud = ["-ss", str(a / E.FPS), "-t", str(len(fs) / E.FPS), "-i", mix] if os.path.exists(mix) else []
        cmd_ = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{E.W // 2}x{E.H // 2}", "-r", str(E.FPS), "-i", "-", *aud,
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p", *(["-c:a", "aac", "-b:a", "160k", "-shortest"] if aud else []), out]
        pr = subprocess.Popen(cmd_, stdin=subprocess.PIPE)
        bl = blocks(fs)
        for ims in POOL.imap(_block, bl, chunksize=1):
            for im in ims: pr.stdin.write(cv2.resize(im, (E.W // 2, E.H // 2), interpolation=cv2.INTER_AREA).tobytes())
        pr.stdin.close(); pr.wait(); return [out]
    if cmd == "auto":
        name = args[0]; offs = (-8, -4, -1, 0, 3, 8); cuts = [s["f0"] for s in E.SHOTS[1:]]; out = []
        allf = [clampf(c + o) for c in cuts for o in offs]; ims = dict(zip(allf, render_many(allf)))
        for si in range(0, len(cuts), 6):
            fs = [clampf(c + o) for c in cuts[si:si + 6] for o in offs]
            p = f"{fr_dir}/{name}_{si // 6 + 1}.jpg"
            cv2.imwrite(p, sheet([ims[f] for f in fs], fs, (216, 384), 6), [cv2.IMWRITE_JPEG_QUALITY, 86]); out.append(p)
        return out
    raise ValueError(f"unknown command {cmd}")

def serve(n):
    global R, POOL
    sp = sock_path(n); os.makedirs(os.path.dirname(sp), exist_ok=True)
    if os.path.exists(sp): os.remove(sp)
    t0 = time.time(); R = edit_env.load_edit(n); R.E = edit_env.edl(n); st = stamp(n)
    POOL = Pool(4)
    POOL.map(int, range(8))                                                                 # warm the workers
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); srv.bind(sp); srv.listen(4)
    print(f"render server v{n} ready ({time.time() - t0:.1f} s)", flush=True)
    while True:
        conn, _ = srv.accept()
        with conn:
            line = conn.makefile().readline()
            if not line.strip(): continue                                                   # a readiness probe
            try: req = json.loads(line)
            except ValueError: continue
            if req["cmd"] == "stop":
                conn.sendall(b'{"ok": true, "out": []}\n'); break
            if req["cmd"] == "status":
                conn.sendall((json.dumps({"ok": True, "out": [f"v{n} loaded, pid {os.getpid()}"]}) + "\n").encode()); continue
            if stamp(n) != st:                                                              # code or inputs changed: restart
                conn.sendall(b'{"ok": false, "restart": true}\n'); break
            t = time.time()
            try: out = handle(n, req); resp = {"ok": True, "out": out, "s": round(time.time() - t, 1)}
            except Exception as e: resp = {"ok": False, "err": f"{type(e).__name__}: {e}"}
            conn.sendall((json.dumps(resp) + "\n").encode())
    POOL.terminate(); srv.close()
    try: os.remove(sp)
    except Exception: pass

# ---- client side -------------------------------------------------------------------------------------------------
def start(n):
    log = open(f"{edit_env.work_dir(n)}/cache/rsrv.log", "a")
    subprocess.Popen([sys.executable, os.path.abspath(__file__), str(n), "_serve"], stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    sp = sock_path(n); t = time.time()
    while time.time() - t < 120:
        if os.path.exists(sp):
            try: s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); s.connect(sp); s.close(); return
            except OSError: pass
        time.sleep(0.3)
    sys.exit("render server did not start; see vN/work/cache/rsrv.log")

def ask(n, cmd, args):
    sp = sock_path(n)
    for attempt in range(3):
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); s.connect(sp)
        except OSError:
            if cmd in ("stop", "status"): print("render server not running"); return
            start(n); continue
        s.sendall((json.dumps({"cmd": cmd, "args": args}) + "\n").encode())
        resp = json.loads(s.makefile().readline() or '{"ok": false, "restart": true}'); s.close()
        if resp.get("restart"):
            print("code or inputs changed: restarting the render server", flush=True); time.sleep(1.0); start(n); continue
        if not resp.get("ok"): sys.exit(f"render server error: {resp.get('err')}")
        for p in resp["out"]: print(p)
        if "s" in resp: print(f"({resp['s']} s)")
        return
    sys.exit("render server kept restarting")

def main():
    if len(sys.argv) < 3: print(__doc__); sys.exit(1)
    n, cmd, args = int(sys.argv[1]), sys.argv[2], sys.argv[3:]
    os.makedirs(os.path.dirname(sock_path(n)), exist_ok=True)
    if cmd == "_serve": return serve(n)
    ask(n, cmd, args)

if __name__ == "__main__":
    main()
