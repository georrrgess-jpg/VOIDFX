"""Scaffold a new voidfx edit from the current benchmark engine (v6 WARMPOP).

Usage:  python3 tools/new_edit.py N SLUG "TITLE — Show × Song"
        e.g. python3 tools/new_edit.py 7 night_drive_dexter "NIGHT DRIVE — Dexter × Song"
Creates vN/{work,frames,audio,out}; copies the engine (render, audio, qc, facetrack, analyze) wired to vN/work/edlN.py;
writes edlN.py from tools/edl_template.py; adds the media folders to .gitignore. The engine reads every path and the
output file name from the EDL (VER, SLUG), so nothing else needs renaming.
"""
import os, sys, re, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "v6"                                                     # benchmark engine to copy from
n, slug, title = sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else sys.argv[2]
V = f"v{n}"; D = f"{ROOT}/{V}"
if os.path.exists(f"{D}/work/edl{n}.py"): sys.exit(f"{V} already exists — refusing to overwrite")
for sub in ("work", "frames", "audio", "out"): os.makedirs(f"{D}/{sub}", exist_ok=True)

def port(src, dst, extra=()):
    s = open(f"{ROOT}/{BASE}/work/{src}").read()
    s = s.replace("import edl6 as E", f"import edl{n} as E")
    for a, b in extra: s = s.replace(a, b)
    open(f"{D}/work/{dst}", "w").write(s)

port("render6.py", f"render{n}.py")
port("audio6.py", f"audio{n}.py", [('"""Soundtrack for WARMPOP (voidfx v6)', f'"""Soundtrack for {title} (voidfx {V}) — ported from the v6 engine.\nv6 notes:')])
port("qc6.py", f"qc{n}.py", [("Usage: python3 v6/work/qc6.py v6/out/warmpop_dexter_voidfx_9x16.mp4", f"Usage: python3 {V}/work/qc{n}.py {V}/out/{slug}_voidfx_9x16.mp4")])
shutil.copy(f"{ROOT}/{BASE}/work/facetrack.py", f"{D}/work/facetrack.py")
port("analyze.py", "analyze.py", [('f"v6/work/', f'f"{V}/work/'), ('f"v6/frames/', f'f"{V}/frames/')])

t = open(f"{ROOT}/tools/edl_template.py").read()
t = t.replace("{{TITLE}}", title).replace("{{VER}}", V).replace("{{SLUG}}", slug).replace("{{N}}", n)
open(f"{D}/work/edl{n}.py", "w").write(t)

gi = f"{ROOT}/.gitignore"; g = open(gi).read() if os.path.exists(gi) else ""
add = [f"{V}/work/*.log", f"{V}/audio/", f"{V}/frames/", f"{V}/out/", f"{V}/work/*.npz", f"{V}/work/*.npy"]
new = [a for a in add if a not in g.split("\n")]
if new: open(gi, "a").write(("\n" if g and not g.endswith("\n") else "") + "\n".join(new) + "\n")

print(f"""scaffolded {V}: {title}
next:
  python3 tools/song_map.py src/SONG.mp3 {V}/work                 # grid, drops, candidate windows
  python3 {V}/work/analyze.py src/PACK.mp4 TAG                     # shot list + contact sheets per pack
  python3 tools/transcribe.py {V} NAME src/PACK.mp4 --vad          # dialogue word times (if using dialogue)
  edit {V}/work/edl{n}.py  (shots, transitions, text, knobs)
  bash tools/build.sh {n} prep auto                                # tracks/mattes + review sheets of every cut
  bash tools/build.sh {n} audio clip:A:B preview                   # sound + motion checks
  bash tools/build.sh {n} video qc                                 # final render + ship checkpoint""")
