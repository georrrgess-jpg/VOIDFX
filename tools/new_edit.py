"""Scaffold a new voidfx edit from the standard: the v103 FOREVER engine (every v4-v9 transition + the v103 toolkit).

Usage:  python3 tools/new_edit.py N SLUG "TITLE — Show × Song"
        e.g. python3 tools/new_edit.py 7 night_drive_dexter "NIGHT DRIVE — Dexter × Song"
Creates vN/{work,frames,audio,out}; copies the engine (render, audio, qc, facetrack, analyze) wired to vN/work/edlN.py,
plus fxN.py (the edit's own section: the v103 toolkit to restyle) and splice.py; writes edlN.py from tools/edl_template.py
(FOREVER's EDL as the worked example); adds the media folders to .gitignore. The engine reads every path and the
output file name from the EDL (VER, SLUG), so nothing else needs renaming.
"""
import os, sys, re, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "v103"                                                   # the standard (v4-v9 engine + v103: plastic rip, evidence photos, eye dive, flashlight blind-out, beat punches, lyric captions)
n, slug, title = sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else sys.argv[2]
V = f"v{n}"; D = f"{ROOT}/{V}"
if os.path.exists(f"{D}/work/edl{n}.py"): sys.exit(f"{V} already exists — refusing to overwrite")
for sub in ("work", "frames", "audio", "out"): os.makedirs(f"{D}/{sub}", exist_ok=True)

BN = BASE[1:]
def port(src, dst, extra=()):
    s = open(f"{ROOT}/{BASE}/work/{src}").read()
    s = s.replace(f"import edl{BN} as E", f"import edl{n} as E")
    for a, b, *c in extra: s = s.replace(a, b, *c)
    open(f"{D}/work/{dst}", "w").write(s)

port(f"render{BN}.py", f"render{n}.py", [(f"# >>> {BASE} section (generated from fx{BN}.py by splice.py)", f"# >>> {V} section (generated from fx{n}.py by splice.py)"),
                                          (f"# <<< {BASE} section", f"# <<< {V} section")])
port(f"fx{BN}.py", f"fx{n}.py", [("# ============================================================================ v103 — FOREVER: undertow toolkit (Dexter × Everlong)",
                                  f"# ============================================================================ {V} — {title}: toolkit from the v103 FOREVER standard (restyle it)", 1),
                                 ("render103.py", f"render{n}.py")])
port("splice.py", "splice.py", [("v103", V), ("103", n)])
port(f"audio{BN}.py", f"audio{n}.py", [('"""', f'"""[{title} (voidfx {V}) — ported from the {BASE} engine; rewrite the sound design below]\nPrevious edit: ', 1)])
port(f"qc{BN}.py", f"qc{n}.py")
shutil.copy(f"{ROOT}/{BASE}/work/facetrack.py", f"{D}/work/facetrack.py")
port("analyze.py", "analyze.py", [(f'f"{BASE}/work/', f'f"{V}/work/'), (f'f"{BASE}/frames/', f'f"{V}/frames/'), (f'"{BASE}/work/', f'"{V}/work/'), (f'"{BASE}/frames/', f'"{V}/frames/')])

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
  python3 tools/lyrics.py {V} src/SONG.mp3 START END "published lyrics | line 2"   # every sung word + time -> captions
  python3 tools/transcribe.py {V} NAME src/PACK.mp4 --vad          # dialogue word times (if using dialogue)
  edit {V}/work/edl{n}.py  (shots, transitions, text, knobs) and {V}/work/fx{n}.py (look, set pieces, frame), then python3 {V}/work/splice.py
  bash tools/build.sh {n} prep auto                                # tracks/mattes + review sheets of every cut
  bash tools/build.sh {n} audio clip:A:B preview                   # sound + motion checks
  bash tools/build.sh {n} video qc                                 # final render + ship checkpoint""")
