"""Final renders for pipeline v2 (WP2 + WP4): upload MP4, a lossless frame cache, the master off the critical path,
and verified partial re-renders.

  python3 tools/vrender.py N video [--only A:B[,C:D]] [--full]   # upload MP4 + frame cache; the master starts in the background
  python3 tools/vrender.py N master [--wait]                      # (re)make the master from the cache; --wait = wait for it
  python3 tools/vrender.py N video --only A:B --dry               # would a partial render be safe? (verification only)
  python3 tools/vrender.py N status                               # what the cache and the master hold
  python3 tools/vrender.py N clean                                # delete the frame cache (do it at the verdict; ~2.2 GB)

Picture and encoder settings are the engine's own (`renderN.py video`): CRF 17 / preset slow upload, CRF 11 /
preset slow master, BT.709 tags, the same audio. Only the order of work changes:
  * workers render contiguous blocks that never cross a cut, so their caches hit (same frames, faster);
  * every full render also writes vN/work/cache/frames.mkv (Ut Video, lossless and intra-only; 4.5x faster to encode
    than FFV1, about 1.8 MB a frame) plus a SHA-1 of
    every frame; the master is encoded from that cache in the background at low priority, so the next step (QC,
    stills) doesn't wait for it. `deliver` (build.sh) waits for the master and checks it;
  * `--only A:B` re-renders only those frames (plus the EDL's changed shots, found automatically) and splices them
    into the cache. Before splicing it re-renders verification frames outside the range (12 random, the frames next
    to each range, one per shot) and requires a bit-exact match with the cache. Any mismatch means the change reached
    further than declared, so it falls back to a full render. Changed EDL globals, frame count, tracks, mattes or
    restored bands also force a full render. (Guardrail 9 of sync/PIPELINE_V2_PLAN.md.)
"""
import os, sys, json, time, hashlib, random, signal, subprocess, argparse
from multiprocessing import Pool
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edit_env

R = None
OUT_OVERRIDE = [None]
DRY = [False]
ENC_TAGS = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv"]
VF = "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p"

def paths(n):
    w = edit_env.work_dir(n); c = f"{w}/cache"
    return {"work": w, "cache": c, "mkv": f"{c}/frames.mkv", "meta": f"{c}/meta.json", "pid": f"{c}/master.pid",
            "mlog": f"{c}/master.log", "audio": f"{edit_env.ROOT}/v{n}/audio", "out": OUT_OVERRIDE[0] or f"{edit_env.ROOT}/v{n}/out"}

def sha(b): return hashlib.sha1(b).hexdigest()

def file_md5(p):
    if not os.path.exists(p): return None
    h = hashlib.md5()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""): h.update(chunk)
    return h.hexdigest()

def jsonable(v):
    try: json.dumps(v); return True
    except Exception: return False

def edl_snapshot(E):
    """the EDL's decisions: every shot (public keys) and every upper-case global."""
    shots = [{k: v for k, v in s.items() if not k.startswith("_") and jsonable(v)} for s in E.SHOTS]
    def is_shot(v): return isinstance(v, dict) and "f0" in v or isinstance(v, (list, tuple)) and any(isinstance(x, dict) and "f0" in x for x in v)
    glob = {k: getattr(E, k) for k in dir(E) if k.isupper() and k != "SHOTS" and not is_shot(getattr(E, k)) and jsonable(getattr(E, k))}
    return {"shots": json.loads(json.dumps(shots)), "globals": json.loads(json.dumps(glob))}

def inputs_sig(n):
    w = edit_env.work_dir(n); sr = f"{edit_env.ROOT}/v{n}/sr/index.json"
    return {"tracks": file_md5(f"{w}/tracks{n}.json"), "seg": file_md5(f"{w}/seg{n}.npz"), "sr": file_md5(sr)}

def code_sig(n):
    w = edit_env.work_dir(n)
    return {"render": file_md5(f"{w}/render{n}.py"), "edl": file_md5(f"{w}/edl{n}.py")}

# ---- rendering ---------------------------------------------------------------------------------------------------
def blocks(frames, size=36):
    if hasattr(R, "frame_blocks"): return R.frame_blocks(frames, size)
    out, cur = [], []
    for f in frames:
        if cur and (f != cur[-1] + 1 or R.shot_at(f) is not R.shot_at(cur[-1]) or len(cur) >= size): out.append(cur); cur = []
        cur.append(f)
    if cur: out.append(cur)
    return out

def _block(fs): return [R.render(f) for f in fs]

def render_iter(pool, frames, size=36):
    bl = blocks(frames, size)
    for fs, ims in zip(bl, edit_env.bounded_imap(pool, _block, bl)):
        yield from zip(fs, ims)

# ---- encoders ----------------------------------------------------------------------------------------------------
def upload_cmd(n, E, out_mp4, cache_mkv):
    p = paths(n); W, H, FPS = E.W, E.H, E.FPS
    return ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-itsoffset", str(-1024 / 48000), "-i", f"{p['audio']}/mix_preroll.wav",
            "-map", "0:v", "-map", "1:a", "-vf", VF, "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-maxrate", "26M", "-bufsize", "52M",
            "-profile:v", "high", "-level", "4.2", "-g", "120", "-bf", "3", *ENC_TAGS, "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2",
            "-movflags", "+faststart", out_mp4,
            "-map", "0:v", "-c:v", "utvideo", "-pix_fmt", "gbrp", cache_mkv]

def master_cmd(n, E, out_mov):
    p = paths(n); W, H, FPS = E.W, E.H, E.FPS
    return ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-i", f"{p['audio']}/mix.wav", "-map", "0:v", "-map", "1:a", "-vf", VF, "-c:v", "libx264", "-preset", "slow", "-crf", "11",
            "-profile:v", "high", "-level", "5.1", *ENC_TAGS, "-c:a", "pcm_s24le", "-ar", "48000", out_mov]

def decode_cache(mkv, W, H):
    """yield every cached frame as bytes (bgr24)."""
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", mkv, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    sz = W * H * 3
    while True:
        b = p.stdout.read(sz)
        if len(b) < sz: break
        yield b
    p.wait()

def stop_master(n):
    pf = paths(n)["pid"]
    if os.path.exists(pf):
        try:
            pid = int(open(pf).read().split()[0]); os.killpg(pid, signal.SIGTERM); print("stopped the previous master encode", flush=True)
        except Exception: pass
        try: os.remove(pf)
        except Exception: pass

def spawn_master(n):
    p = paths(n)
    lg = open(p["mlog"], "w")
    pr = subprocess.Popen(["nice", "-n", "15", sys.executable, os.path.abspath(__file__), str(n), "master", "--out", p["out"]], stdout=lg, stderr=subprocess.STDOUT,
                          start_new_session=True)
    open(p["pid"], "w").write(f"{pr.pid}\n"); print(f"master encoding in the background (pid {pr.pid}, log {p['mlog']})", flush=True)

# ---- modes -------------------------------------------------------------------------------------------------------
def full_render(n, E, reason=""):
    p = paths(n); os.makedirs(p["cache"], exist_ok=True); os.makedirs(p["out"], exist_ok=True)
    stop_master(n)
    up = f"{p['out']}/{E.SLUG}_voidfx_9x16.mp4"; tmp = p["mkv"] + ".part.mkv"
    print(f"full render of {E.DUR_F} frames{' (' + reason + ')' if reason else ''}", flush=True)
    t0 = time.time(); hashes = [None] * E.DUR_F
    enc = subprocess.Popen(upload_cmd(n, E, up, tmp), stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for i, (f, fr) in enumerate(render_iter(pool, list(range(E.DUR_F)))):
            b = fr.tobytes(); hashes[f] = sha(b); enc.stdin.write(b)
            if i % 150 == 0: print(f"frame {i}/{E.DUR_F}  {time.time() - t0:.0f} s", flush=True)
    enc.stdin.close(); rc = enc.wait()
    if rc: sys.exit(f"encoder failed ({rc})")
    os.replace(tmp, p["mkv"])
    write_meta(n, E, hashes, "full", time.time() - t0)
    print(f"done {p['out']}  ({time.time() - t0:.0f} s)", flush=True)
    spawn_master(n)

def write_meta(n, E, hashes, kind, secs):
    p = paths(n)
    m = {"frames": E.DUR_F, "fps": E.FPS, "size": [E.W, E.H], "hashes": hashes, "edl": edl_snapshot(E), "inputs": inputs_sig(n),
         "code": code_sig(n), "made": time.strftime("%Y-%m-%d %H:%M:%S"), "kind": kind, "secs": round(secs, 1),
         "cache_id": sha(("".join(hashes) + time.strftime("%s")).encode())[:12], "master_of": None}
    json.dump(m, open(p["meta"] + ".tmp", "w")); os.replace(p["meta"] + ".tmp", p["meta"])

def changed_shots(old, new, E):
    """frame ranges of shots whose EDL entry changed, widened by 30 frames each side for their transitions."""
    rng = []
    for i, (a, b) in enumerate(zip(old["shots"], new["shots"])):
        if a != b:
            s = E.SHOTS[i]; rng.append((max(0, s["f0"] - 30), min(E.DUR_F - 1, s["f1"] + 30)))
    return rng

def partial_render(n, E, only):
    p = paths(n)
    if not os.path.exists(p["meta"]) or not os.path.exists(p["mkv"]): return full_render(n, E, "no frame cache yet")
    m = json.load(open(p["meta"])); new = edl_snapshot(E)
    if m["frames"] != E.DUR_F or m["fps"] != E.FPS: return full_render(n, E, "frame count changed")
    if m["edl"]["globals"] != new["globals"]: return full_render(n, E, "an EDL global changed")
    if len(m["edl"]["shots"]) != len(new["shots"]) or any(a.get("f0") != b.get("f0") for a, b in zip(m["edl"]["shots"], new["shots"])):
        return full_render(n, E, "the shot list or cut points changed")
    if m["inputs"] != inputs_sig(n): return full_render(n, E, "tracks, mattes or restored bands changed")
    ranges = list(only) + changed_shots(m["edl"], new, E)
    if not ranges:
        if m["code"] == code_sig(n): print("nothing changed since the cache; nothing to render"); return
        return full_render(n, E, "the code changed and no range was given (use --only A:B)")
    dirty = sorted({f for a, b in ranges for f in range(max(0, a), min(E.DUR_F - 1, b) + 1)})
    ds = set(dirty)
    ver = set()
    for a, b in ranges:
        for f in (a - 1, a - 2, b + 1, b + 2):
            if 0 <= f < E.DUR_F and f not in ds: ver.add(f)
    for s in E.SHOTS:
        mid = (s["f0"] + s["f1"]) // 2
        if mid not in ds: ver.add(mid)
    rest = [f for f in range(E.DUR_F) if f not in ds and f not in ver]
    ver.update(random.Random(time.time()).sample(rest, min(12, len(rest))))
    ver = sorted(ver)
    print(f"partial render: {len(dirty)} frames in {len(ranges)} range(s) {ranges}; verifying {len(ver)} frames outside", flush=True)
    stop_master(n)
    t0 = time.time(); new_frames = {}; bad = []
    with Pool(4) as pool:
        for f, fr in render_iter(pool, ver, 1):
            if sha(fr.tobytes()) != m["hashes"][f]: bad.append(f)
        if bad:
            print(f"verification FAILED on {len(bad)} of {len(ver)} frames outside the range (e.g. {bad[:8]}): the change reaches further", flush=True)
            if DRY[0]: sys.exit(2)
            return full_render(n, E, "verification failed")
        print(f"verification passed ({len(ver)} frames bit-exact, {time.time() - t0:.0f} s)", flush=True)
        if DRY[0]: return
        for f, fr in render_iter(pool, dirty): new_frames[f] = fr.tobytes()
    print(f"rendered {len(dirty)} frames ({time.time() - t0:.0f} s); splicing and encoding", flush=True)
    up = f"{p['out']}/{E.SLUG}_voidfx_9x16.mp4"; tmp = p["mkv"] + ".part.mkv"; hashes = list(m["hashes"])
    enc = subprocess.Popen(upload_cmd(n, E, up, tmp), stdin=subprocess.PIPE)
    for f, b in enumerate(decode_cache(p["mkv"], E.W, E.H)):
        if f in new_frames: b = new_frames[f]; hashes[f] = sha(b)
        elif sha(b) != m["hashes"][f]: enc.kill(); sys.exit(f"cache frame {f} doesn't match its hash; run a full render (--full)")
        enc.stdin.write(b)
    enc.stdin.close(); rc = enc.wait()
    if rc: sys.exit(f"encoder failed ({rc})")
    if f != E.DUR_F - 1: sys.exit(f"cache held {f + 1} frames, expected {E.DUR_F}; run a full render (--full)")
    os.replace(tmp, p["mkv"])
    write_meta(n, E, hashes, f"partial {ranges}", time.time() - t0)
    print(f"done {p['out']}  ({time.time() - t0:.0f} s)", flush=True)
    spawn_master(n)

def master(n, E):
    p = paths(n); m = json.load(open(p["meta"]))
    out = f"{p['out']}/{E.SLUG}_voidfx_9x16_master.mov"; tmp = out + ".part.mov"
    t0 = time.time()
    enc = subprocess.Popen(master_cmd(n, E, tmp), stdin=subprocess.PIPE); k = 0
    for k, b in enumerate(decode_cache(p["mkv"], E.W, E.H)): enc.stdin.write(b)
    enc.stdin.close(); rc = enc.wait()
    if rc or k != E.DUR_F - 1: sys.exit(f"master failed (rc {rc}, {k + 1} frames)")
    os.replace(tmp, out)
    m2 = json.load(open(p["meta"]))
    if m2["cache_id"] == m["cache_id"]:
        m2["master_of"] = m["cache_id"]; json.dump(m2, open(p["meta"] + ".tmp", "w")); os.replace(p["meta"] + ".tmp", p["meta"])
    try: os.remove(p["pid"])
    except Exception: pass
    print(f"master done: {out} ({time.time() - t0:.0f} s)", flush=True)

def master_wait(n, E):
    p = paths(n)
    while os.path.exists(p["pid"]):
        try: pid = int(open(p["pid"]).read().split()[0]); os.kill(pid, 0)
        except Exception: break
        time.sleep(3)
    m = json.load(open(p["meta"]))
    if m.get("master_of") != m["cache_id"]:
        print("master is missing or older than the frame cache: encoding it now", flush=True); master(n, E)
        m = json.load(open(p["meta"]))
    out = f"{p['out']}/{E.SLUG}_voidfx_9x16_master.mov"
    nb = subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries", "stream=nb_read_packets",
                         "-of", "csv=p=0", out], capture_output=True, text=True).stdout.strip()
    ok = m.get("master_of") == m["cache_id"] and nb == str(E.DUR_F)
    print(f"master: {out}  frames {nb}/{E.DUR_F}  {'current' if ok else 'NOT CURRENT'}")
    if not ok: sys.exit(1)

def status(n, E):
    p = paths(n)
    if not os.path.exists(p["meta"]): print("no frame cache"); return
    m = json.load(open(p["meta"]))
    print(f"cache: {m['frames']} frames, made {m['made']} ({m['kind']}, {m['secs']} s); master {'current' if m.get('master_of') == m['cache_id'] else 'pending/stale'}")
    print(f"  code changed since: {m['code'] != code_sig(n)}; inputs changed: {m['inputs'] != inputs_sig(n)}; "
          f"EDL shots changed: {changed_shots(m['edl'], edl_snapshot(E), E)}")

def main():
    global R
    ap = argparse.ArgumentParser()
    ap.add_argument("n", type=int); ap.add_argument("mode", choices=["video", "master", "status", "clean"])
    ap.add_argument("--only"); ap.add_argument("--full", action="store_true"); ap.add_argument("--wait", action="store_true")
    ap.add_argument("--out", help="output folder (default vN/out)")
    ap.add_argument("--dry", action="store_true", help="with --only: run the verification only (exit 2 if it fails); render nothing")
    a = ap.parse_args()
    if a.out: OUT_OVERRIDE[0] = os.path.abspath(a.out)
    DRY[0] = a.dry
    E = edit_env.edl(a.n)
    if a.mode == "status":
        edit_env.load_edit(a.n, setup=False)                 # the renderer may write into the EDL's shot dicts on import
        return status(a.n, E)
    if a.mode == "clean":
        stop_master(a.n)
        for k in ("mkv", "meta"):
            if os.path.exists(paths(a.n)[k]): os.remove(paths(a.n)[k])
        print("frame cache removed"); return
    if a.mode == "master": return master_wait(a.n, E) if a.wait else master(a.n, E)
    for f in ("mix.wav", "mix_preroll.wav"):
        if not os.path.exists(f"{paths(a.n)['audio']}/{f}"): sys.exit(f"missing audio/{f}: run the audio step first")
    subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "rsrv.py"), str(a.n), "stop"],
                   capture_output=True)                     # the render server's warm workers would compete for memory
    R = edit_env.load_edit(a.n)
    if a.full: return full_render(a.n, E, "--full")
    only = [tuple(int(x) for x in r.split(":")) for r in a.only.split(",")] if a.only else []
    if only or os.path.exists(paths(a.n)["meta"]): return partial_render(a.n, E, only)
    return full_render(a.n, E)

if __name__ == "__main__":
    main()
