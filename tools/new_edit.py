"""Scaffold a new voidfx edit from one of the standard engines:
  --base v12   the Flash standard since 2026-11-08, v12 BLOOM rev 3 on v11 BOP: every v4-v12 transition and graphic, the
               restored-source sampler, velocity + optical flow, the beat camera, the v9 text system, the v11 and v12 pieces.
               Template: tools/edl_template.py
  --base v11   the previous Flash standard, v11 BOP rev 4 (inside v12). Template: tools/edl_template.py
  --base v110  the Dexter standard since 2026-11-09 (night), v110 SLEEPWALKER rev 3: the v109 base below + the v110 toolkit at the
               end of fxN.py (3 A.M. grade and dream finish, lights on, brownout, fog roll, falling asleep, THE SURGE (fan light
               through turning blades, a blade across the lens on the drop), THE BARREL (a seamless push into a real muzzle),
               bokeh, tear, curtain, plastic roll, brush, THE SWINGING LIGHT, tilt, THE DRIP loop, a calmer beat camera).
               Template: v110's own EDL (no text; rewrite it).
  --base v109  the previous Dexter standard (2026-11-09 evening), v109 PHANTOM rev 3: the v108 base below + the v109 toolkit at the
               end of fxN.py (SPECTRAL grade and finish, mist materialise/vanish, phantom pass through a matte, the fingerprint
               dive, the fire from a tracked prop, the phantom's trail (a 3-D ribbon of light around a matte), red wash,
               streetlight, cctv, flicker, the dust gust loop into frame 0, hflip for mirrored packs, splat109 particles).
               Template: v109's own EDL (one title; rewrite it).
  --base v108  the previous Dexter standard (2026-11-09), v108 DOOMSDAY rev 2: the v107 base below + the v108 toolkit at the end of
               fxN.py (two grades split by a transition, SURFACE plastic, SPECIMEN from a real prop, frost, fronds, diffusion,
               luminol, face match on the eye line, darkroom developer, sink, double vision, the last-drop loop). Template:
               v108's own EDL (no text; rewrite it).
  --base v107  the previous Dexter standard (2026-11-08), v107 ALL CAPS rev 4: the v12 engine (restored-source sampler, flow, the
               beat camera, every v4-v12 transition) + the v107 toolkit in fxN.py (TABLOID grade and finish, molasses, headspin,
               front page, letterpress stamp, banner, confetti, the name loop, page turn ...), re-spliced with
               tools/splice_section.py N vN/work/fxN.py --replace. Template: v107's own EDL (the worked example; rewrite it).
  --base v105  the previous Dexter standard, v105 DRACULA rev 3: the v4-v9 engine + the v103 FOREVER, v104 THE PASSENGER and
               v105 DRACULA toolkits in fxN.py (spliced into renderN.py by splice.py). Template: tools/edl_template_v105.py
Without --base: v110 if the slug or title mentions Dexter, otherwise v12.

Usage:  python3 tools/new_edit.py N SLUG "TITLE — Show × Song" [--base v12|v11|v110|v109|v108|v107|v105]
Creates vN/{work,frames,audio,out}; copies the engine wired to vN/work/edlN.py; writes edlN.py from the base's template;
adds the media folders to .gitignore. The engine reads every path and the output file name from the EDL (VER, SLUG).
"""
import os, sys, re, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = [a for a in sys.argv[1:] if not a.startswith("--")]
n, slug = args[0], args[1]; title = args[2] if len(args) > 2 else slug
if "--base" in sys.argv: BASE = sys.argv[sys.argv.index("--base") + 1]; args = [a for a in args if a != BASE]; n, slug = args[0], args[1]; title = args[2] if len(args) > 2 else slug
else: BASE = "v110" if "dexter" in (slug + title).lower() else "v12"
assert BASE in ("v12", "v11", "v110", "v109", "v108", "v107", "v105"), "--base must be v12 (Flash), v11 (the previous Flash standard), v110 (Dexter), v109, v108, v107 or v105 (earlier Dexter standards)"
V = f"v{n}"; D = f"{ROOT}/{V}"
if os.path.exists(f"{D}/work/edl{n}.py"): sys.exit(f"{V} already exists — refusing to overwrite")
for sub in ("work", "frames", "audio", "out"): os.makedirs(f"{D}/{sub}", exist_ok=True)

if BASE == "v105":
    BN = BASE[1:]
    def port(src, dst, extra=()):
        s = open(f"{ROOT}/{BASE}/work/{src}").read()
        s = s.replace(f"import edl{BN} as E", f"import edl{n} as E")
        for a, b, *c in extra: s = s.replace(a, b, *c)
        open(f"{D}/work/{dst}", "w").write(s)

    port(f"render{BN}.py", f"render{n}.py", [(f"# >>> {BASE} section (generated from fx{BN}.py by splice.py)", f"# >>> {V} section (generated from fx{n}.py by splice.py)"),
                                              (f"# <<< {BASE} section", f"# <<< {V} section")])
    fx = open(f"{ROOT}/{BASE}/work/fx{BN}.py").read().split("\n", 1)                           # the edit's own section, with a fresh header line
    open(f"{D}/work/fx{n}.py", "w").write(f"# ============================================================================ {V} — {title}: toolkit from the {BASE} standard (restyle it)\n"
                                           + fx[1].replace(f"render{BN}.py", f"render{n}.py"))
    port("splice.py", "splice.py", [(BASE, V), (BN, n)])
    port(f"audio{BN}.py", f"audio{n}.py", [('"""', f'"""[{title} (voidfx {V}) — ported from the {BASE} engine; rewrite the sound design below]\nPrevious edit: ', 1)])
    port(f"qc{BN}.py", f"qc{n}.py")
    shutil.copy(f"{ROOT}/{BASE}/work/facetrack.py", f"{D}/work/facetrack.py")
    if os.path.exists(f"{ROOT}/{BASE}/work/big.py"): port("big.py", "big.py", [(f"render{BN}", f"render{n}")])
    port("analyze.py", "analyze.py", [(f'f"{BASE}/work/', f'f"{V}/work/'), (f'f"{BASE}/frames/', f'f"{V}/frames/'), (f'"{BASE}/work/', f'"{V}/work/'), (f'"{BASE}/frames/', f'"{V}/frames/')])
    TEMPLATE = "edl_template_v105.py"
else:
    BN = BASE[1:]
    def port(src, dst, extra=()):
        s = open(f"{ROOT}/{BASE}/work/{src}").read()
        s = s.replace(f"import edl{BN} as E", f"import edl{n} as E")
        for a, b, *c in extra: s = s.replace(a, b, *c)
        open(f"{D}/work/{dst}", "w").write(s)
    port(f"render{BN}.py", f"render{n}.py")
    port(f"audio{BN}.py", f"audio{n}.py", [('"""', f'"""[{title} (voidfx {V}) — ported from the {BASE} engine; rewrite the sound design below]\nPrevious edit: ', 1)])
    port(f"qc{BN}.py", f"qc{n}.py")
    shutil.copy(f"{ROOT}/{BASE}/work/facetrack.py", f"{D}/work/facetrack.py")
    port("analyze.py", "analyze.py", [(f'f"{BASE}/work/', f'f"{V}/work/'), (f'f"{BASE}/frames/', f'f"{V}/frames/'), ('f"v6/work/', f'f"{V}/work/'), ('f"v6/frames/', f'f"{V}/frames/')])
    TEMPLATE = "edl_template.py"
    if BASE in ("v107", "v108", "v109", "v110"):                                           # the edit's own section + the worked EDL
        name_ = {"v107": "v107 ALL CAPS", "v108": "v108 DOOMSDAY", "v109": "v109 PHANTOM", "v110": "v110 SLEEPWALKER"}[BASE]
        hdr = open(f"{ROOT}/{BASE}/work/fx{BN}.py").read().split("\n", 1)[0]
        new_hdr = f"# ============================================================================ {V} — {title}: toolkit from the {BASE} standard (restyle it)"
        r = open(f"{D}/work/render{n}.py").read(); assert hdr in r, f"{BASE} section header not found in render{BN}.py"
        open(f"{D}/work/render{n}.py", "w").write(r.replace(hdr, new_hdr, 1))
        fx = open(f"{ROOT}/{BASE}/work/fx{BN}.py").read().split("\n", 1)[1]
        open(f"{D}/work/fx{n}.py", "w").write(new_hdr + "\n" + fx)
        e = open(f"{ROOT}/{BASE}/work/edl{BN}.py").read()
        e = re.sub(r'VER, SLUG = "v\d+", "[^"]*"', f'VER, SLUG = "{V}", "{slug}"', e, count=1)
        e = f'"""{title} (voidfx {V}). WORKED TEMPLATE: this is {name_}\'s EDL; rewrite the song, packs, shots and text.\n' + e.split('"""', 1)[1]
        open(f"{D}/work/edl{n}.py", "w").write(e); TEMPLATE = None
        for sj in [x for x in os.listdir(f"{ROOT}/{BASE}/work") if x.startswith("shots_") and x.endswith(".json")]:
            shutil.copy(f"{ROOT}/{BASE}/work/{sj}", f"{D}/work/{sj}")                      # the packs' shot lists come along

if TEMPLATE:
    t = open(f"{ROOT}/tools/{TEMPLATE}").read()
    t = t.replace("{{TITLE}}", title).replace("{{VER}}", V).replace("{{SLUG}}", slug).replace("{{N}}", n)
    open(f"{D}/work/edl{n}.py", "w").write(t)

gi = f"{ROOT}/.gitignore"; g = open(gi).read() if os.path.exists(gi) else ""
add = [f"{V}/work/*.log", f"{V}/audio/", f"{V}/frames/", f"{V}/out/", f"{V}/work/*.npz", f"{V}/work/*.npy", f"{V}/sr/"]
new_ = [a for a in add if a not in g.split("\n")]
if new_: open(gi, "a").write(("\n" if g and not g.endswith("\n") else "") + "\n".join(new_) + "\n")

print(f"""scaffolded {V} from {BASE}: {title}
next:
  bash tools/build.sh {n} song:src/SONG.mp3[:H0:H1]                # map, stems, drum-stem grid, vocal-stem words, loop wrap -> EDL lines
  python3 {V}/work/analyze.py src/PACK.mp4 TAG                     # shot list + contact sheets per NEW pack (known packs: copy shots_*.json)
  python3 tools/transcribe.py {V} NAME src/PACK.mp4 --vad          # dialogue word times (if using dialogue)
  python3 tools/sharpness.py {n} --src                             # clip quality before rendering
  read studio/OWNER_RULES.md and studio/WORKFLOW.md, then edit {V}/work/edl{n}.py (shots, transitions from studio/transitions.json,
    SIGNATURE, HERO, SET_PIECES, knobs)""" + (f" and {V}/work/fx{n}.py (python3 {V}/work/splice.py)" if BASE == "v105" else
                                  f" and {V}/work/fx{n}.py (spliced automatically by build.sh)" if BASE in ("v107", "v108", "v109", "v110") else "") + f"""
  bash tools/build.sh {n} audio plan                               # sound, then the plan against every owner rule (0 FAIL before rendering)
  bash tools/build.sh {n} prep auto                                # tracks/mattes, the plan check, restoration in the background, sheets of every cut
  bash tools/build.sh {n} sheet:NAME:f,f clip:A:B                  # warm stills and motion for every custom piece
  bash tools/build.sh {n} ship                                     # audio, plan, video, QC + review pack, signoff, report, deliver
  revision rounds: bash tools/build.sh {n} ship                    # only the changed frames are re-rendered""")
