"""Preflight: check an edit's plan against the owner's standing rules before the first render (efficiency update,
2026-11-08). Most owner rounds so far were spent on rules we already had; this catches them in seconds, before 5 minutes
of render and a round of feedback.

  python3 tools/preflight.py N                       # the EDL, the renderer's transitions, the sound events
  python3 tools/preflight.py N --hero bh_draw,bh_warp   # name the hero asset's drawing functions (or HERO = [...] in the EDL)
  python3 tools/preflight.py N --dir PATH            # check a copy of the work folder (e.g. an old revision from git)
  python3 tools/preflight.py registry                # rebuild studio/transitions_usage.json (every transition, where defined and used)

Levels: FAIL = breaks a rule the owner has stated (fix before rendering); WARN = likely to draw a note (decide);
INFO = review items (look at these in the sheets). Exit code 1 when anything FAILs. Since the merge, `preflight.py N` and `build.sh N plan` run tools/plan_check.py, one report
that includes these checks (calibrated on the approved edits); `preflight.py N --own` runs only these. Next to the
Dexter studio's tools/plan_check.py (the shared gate: owner verdicts per transition from studio/transitions.json,
look-alike clips, spins landing on faces, the signature graphic, density, the hero family); a FAIL in either stops `video`.
This tool adds what needs the renderer's code or the audio builder's events: the hero asset by call graph (HERO), the
emblem rule, sound kinds and sounds on beat hits, the same source shot twice, order-dependent caches, the registry's
'caution' notes.

What it reads: edlN.py (shots, transitions, SET_PIECES, HERO, TEXT), renderN.py imported without set-up (the TR2
registry and a static call graph of every transition), and the sound events: vN/audio/fx_events.json, written by the
scaffold's audio builder, or else the audio builder run in a sandbox with its place() hooked (nothing in vN/audio is
touched).
"""
import os, sys, json, types, re, ast, hashlib, importlib, subprocess, tempfile, argparse, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, f"{ROOT}/tools")
SCAFFOLD = f"{ROOT}/v12/work/render12.py"
REG = f"{ROOT}/studio/transitions.json"            # the owner's verdicts (shared with the Dexter studio; curated)
USAGE = f"{ROOT}/studio/transitions_usage.json"    # where each transition is defined and used (generated: `registry`)
VERDICT = {"v4": "standard", "v6": "standard", "v7": "standard", "v10": "standard", "v11": "standard", "v12": "standard",
           "v13": "approved (not a standard)", "v8": "approved", "v9": "lacklustre",
           "v101": "rejected (style)", "v102": "lacklustre", "v103": "standard", "v104": "standard", "v105": "standard",
           "v106": "standard", "v107": "standard"}
OCCLUDER = re.compile(r"letterbox|black_?bars?|redact|blackout|black_box", re.I)
BANNED_SFX = re.compile(r"\b(drone|swirl|whine|chime|bell|shimmer|shine|twinkle)\w*\s*\(", re.I)
DRAWS = {"circle", "ellipse", "polylines", "line", "fillPoly", "fillConvexPoly", "remap", "warpAffine", "warpPerspective", "putText"}

OUT = []
def say(level, rule, msg): OUT.append((level, rule, msg))

# ---- loading ------------------------------------------------------------------------------------------------------
def load(n, wd):
    sys.path.insert(0, wd)
    for extra in (f"{ROOT}/v2/work", f"{ROOT}/tools"):
        if extra not in sys.path: sys.path.append(extra)
    E = importlib.import_module(f"edl{n}")
    R = importlib.import_module(f"render{n}")
    return E, R

def funcs_of(R):
    return {k: v for k, v in vars(R).items() if isinstance(v, types.FunctionType) and v.__code__.co_filename == R.__file__}

def names_of(co):
    out = set(co.co_names)
    for c in co.co_consts:
        if isinstance(c, types.CodeType): out |= names_of(c)
        elif isinstance(c, str) and c.isidentifier(): out.add(c)
    return out

def reach(fn, F, memo={}):
    """every module function a function can call (static: names it uses, closures, nested code)."""
    key = id(fn)
    if key in memo: return memo[key]
    seen, todo = set(), [fn]
    while todo:
        f = todo.pop()
        if id(f) in seen: continue
        seen.add(id(f))
        for nm in names_of(f.__code__):
            g = F.get(nm)
            if g is not None and id(g) not in seen: todo.append(g)
        for c in f.__closure__ or ():
            try:
                v = c.cell_contents
                if isinstance(v, types.FunctionType): todo.append(v)
            except ValueError: pass
    names = {nm for nm, g in F.items() if id(g) in seen}
    memo[key] = names
    return names

def scaffold_defs():
    """name -> source hash of every function in the scaffold renderer (to tell library code from the edit's own)."""
    src = open(SCAFFOLD).read(); out = {}
    for node in ast.parse(src).body:
        if isinstance(node, ast.FunctionDef):
            out.setdefault(node.name, set()).add(hashlib.sha1((ast.get_source_segment(src, node) or "").encode()).hexdigest())
    return out

def fn_src_hash(fn):
    import inspect
    try: return hashlib.sha1(inspect.getsource(fn).rstrip("\n").encode()).hexdigest()
    except Exception: return None

# ---- sound events -------------------------------------------------------------------------------------------------
def sound_events(n, wd, E):
    """[(t, dur, peak_db, line_text)] of every effect placed by the audio builder's main()."""
    js = f"{ROOT}/v{n}/audio/fx_events.json"
    au = f"{wd}/audio{n}.py"
    if os.path.exists(js) and os.path.exists(au) and os.path.getmtime(js) >= os.path.getmtime(au) and wd == f"{ROOT}/v{n}/work":
        return json.load(open(js)), "fx_events.json"
    if not os.path.exists(au): return None, "no audio builder"
    tmp = tempfile.mkdtemp(prefix=f"preflight{n}_")
    try:
        r = subprocess.run([sys.executable, os.path.abspath(__file__), "_sound", str(n), wd, tmp], capture_output=True, text=True, timeout=900)
        p = f"{tmp}/fx_events.json"
        if not os.path.exists(p): return None, "sandbox run failed: " + (r.stderr.strip().split("\n") or ["?"])[-1][:160]
        return json.load(open(p)), "sandbox run of the audio builder"
    finally: shutil.rmtree(tmp, ignore_errors=True)

def _sound_sandbox(n, wd, tmp):
    """run audioN.main() with ROOT pointed at a scratch tree (inputs linked read-only, outputs discarded) and log place()."""
    sys.path.insert(0, wd)
    for extra in (f"{ROOT}/v2/work", f"{ROOT}/tools"): sys.path.append(extra)
    E = importlib.import_module(f"edl{n}")
    V = E.VER; os.makedirs(f"{tmp}/{V}/audio", exist_ok=True)
    os.symlink(f"{ROOT}/src", f"{tmp}/src")
    real = f"{ROOT}/{V}/audio"
    for f in ("song48.wav", "sep"):
        if os.path.exists(f"{real}/{f}"): os.symlink(f"{real}/{f}", f"{tmp}/{V}/audio/{f}")
    os.symlink(wd, f"{tmp}/{V}/work")
    E.ROOT = tmp
    import audio2 as A2
    log = []; orig = A2.place
    def hooked(out, sig, i, *a, **k):
        fr = sys._getframe(1)
        while fr is not None and fr.f_code.co_name == "place": fr = fr.f_back
        if fr is not None and "music" not in fr.f_code.co_name:
            import numpy as np
            pk = float(20 * np.log10(np.abs(sig).max() + 1e-9))
            line = open(fr.f_code.co_filename).read().split("\n")[fr.f_lineno - 1].strip()
            log.append([round(i / A.SR - A.PRE / A.SR, 3), round(len(sig) / A.SR, 3), round(pk, 1), fr.f_code.co_name, fr.f_lineno, line[:140]])
        return orig(out, sig, i, *a, **k)
    A2.place = hooked
    A = importlib.import_module(f"audio{n}")
    A.A2.place = hooked
    import contextlib, io
    with contextlib.redirect_stdout(io.StringIO()): A.main()
    json.dump(log, open(f"{tmp}/fx_events.json", "w"))

# ---- checks -------------------------------------------------------------------------------------------------------
def check(n, wd, hero_cli):
    E, R = load(n, wd)
    F = funcs_of(R); TR2 = getattr(R, "TR2", {}); SH = E.SHOTS
    reg = (json.load(open(REG)) if os.path.exists(REG) else {}).get("transitions", {})
    flash = any("flash" in str(v[0]).lower() for v in getattr(E, "SRC", {}).values())
    lib = scaffold_defs(); src_text = open(R.__file__).read()
    dur = E.DUR_F / E.FPS
    print(f"preflight v{n}: {len(SH)} shots, {dur:.2f} s, {'Flash' if flash else 'Dexter'} edit, renderer {os.path.relpath(R.__file__, ROOT)}")

    # -- structure
    if not 20 <= dur <= 26: say("WARN", "length", f"{dur:.2f} s; the owner's range is about 20-26 s")
    tins = [(s["n"], s.get("tin")) for s in SH]
    for i, (nm, t) in enumerate(tins):
        if i and not t: say("FAIL", "no plain cuts", f"shot '{nm}' has no transition in (v6: designed transitions, no plain cuts)")
        if i and t and t not in TR2 and f'"{t}"' not in src_text: say("FAIL", "transition", f"'{t}' (into '{nm}') is not in TR2 or the renderer")
    if tins and tins[0][1] and "loop" not in tins[0][1]: say("WARN", "loop", f"the first shot's transition '{tins[0][1]}' isn't a loop piece (the loop must land on frame 0)")
    used = [t for _, t in tins if t]
    for t in sorted({t for t in used if used.count(t) > 1}): say("WARN", "variety", f"'{t}' is used {used.count(t)} times")
    sp = getattr(E, "SET_PIECES", [])
    if len(sp) < 3: say("WARN", "set pieces", f"{len(sp)} set pieces declared in SET_PIECES; every edit needs at least three (v9)")

    # -- clips: reuse, zoom, cadence
    rng = []
    for s in SH:
        if "src" not in s: continue
        ts = [k[1] for k in s["tmap"]]; rng.append((s["src"], min(ts), max(ts), s["n"]))
        zs = [k[1] for k in s.get("z", [])] if s.get("z") else []
        if zs and max(zs) > 1.10: say("WARN", "sharpness", f"'{s['n']}' zooms to {max(zs):.2f} (720p packs: keep z <= 1.10)")
        fps = E.SRC[s["src"]][1]
        if s.get("interp", "flow") != "flow" and fps < 31: say("WARN", "smoothness", f"'{s['n']}' holds {fps:.0f}p frames (interp={s.get('interp')}): judder between 60p shots (v106 rule 5)")
    def host(pk, a):
        """the detected source shot (analyze.py shot list) a source time sits in"""
        import glob
        c = [f"{wd}/shots_{pk}.json"] + sorted(glob.glob(f"{ROOT}/v*/work/shots_{pk}.json"))
        c = [p for p in c if os.path.exists(p)]
        if not c: return None
        sh = json.load(open(c[0])); sh = sh["shots"] if isinstance(sh, dict) else sh
        h = [x for x in sh if x["t0"] - 0.02 <= a < x["t1"] + 0.02]
        return (round(h[0]["t0"], 2), round(h[0]["t1"], 2)) if h else None
    for i in range(len(rng)):
        for j in range(i + 1, len(rng)):
            a, b = rng[i], rng[j]
            if a[0] != b[0]: continue
            gap = max(a[1], b[1]) - min(a[2], b[2])
            if gap < 0: say("FAIL", "clip reuse", f"'{a[3]}' and '{b[3]}' overlap in {a[0]} ({max(a[1], b[1]):.2f}-{min(a[2], b[2]):.2f} s) (v107 rule 6)"); continue
            ha, hb = host(a[0], a[1]), host(b[0], b[1])
            if ha and ha == hb:
                say("WARN", "clip reuse", f"'{a[3]}' and '{b[3]}' come from the same source shot ({a[0]} {ha[0]:.2f}-{ha[1]:.2f} s, {gap:.1f} s apart): "
                    "one continuous shot counts as a reuse (v107 rule 6)")

    # -- transitions: hero motif, emblem, library, registry status, occluders
    tfn = {t: TR2[t][0] for t in set(used) if t in TR2 and isinstance(TR2[t][0], types.FunctionType)}
    hero = hero_cli or list(getattr(E, "HERO", []) or [])
    if hero:
        missing = [h for h in hero if h not in F]
        if missing: say("WARN", "hero", f"HERO names {missing} aren't renderer functions")
        hits = sorted(t for t, fn in tfn.items() if reach(fn, F) & set(hero))
        lvl = "FAIL" if len(hits) > 4 else "INFO"
        say(lvl, "hero motif", f"the hero asset ({', '.join(hero)}) is drawn by {len(hits)} transition(s): {', '.join(hits) or '-'}"
            + (" (v13 rule 1: about 2-4 appearances; every other transition a different idea)" if len(hits) > 4 else ""))
    # most-shared drawing helpers of the edit's own code (the hero asset shows up here even when HERO isn't declared)
    own = {nm for nm, fn in F.items() if fn_src_hash(fn) not in lib.get(nm, set())}
    draw_own = {nm for nm in own if names_of(F[nm].__code__) & DRAWS}
    cnt = {}
    for t, fn in tfn.items():
        for nm in reach(fn, F) & draw_own:
            if nm != fn.__name__: cnt.setdefault(nm, set()).add(t)
    top = sorted(cnt.items(), key=lambda kv: -len(kv[1]))[:4]
    if top and len(top[0][1]) > 4 and not hero:
        say("WARN", "hero motif", f"'{top[0][0]}' (the edit's own drawing code) is reached by {len(top[0][1])} transitions: "
            f"{', '.join(sorted(top[0][1]))}. If it is the hero asset, that is too many (v13 rule 1); declare HERO = [...] in the EDL")
    if top: say("INFO", "shared helpers", "; ".join(f"{k} x{len(v)}" for k, v in top))
    if flash:
        em = sorted(t for t, fn in tfn.items() if "emblem_at" in reach(fn, F) or "emblem" in t)
        if not em: say("FAIL", "emblem", "no transition uses the tracked emblem (emblem_at): every Flash edit needs one (v12)")
        else: say("INFO", "emblem", f"emblem transition(s): {', '.join(em)}: the emblem's own bolt or shape must carry the move (v13 rule 2)")
    for t in sorted(set(used)):                     # verdicts are plan_check's gate; the technical traps are listed here
        r = reg.get(t) or {}
        if r.get("caution"): say("WARN", "registry", f"'{t}': {r['caution']}")
        if r.get("verdict") in ("rejected", "banned"): say("INFO", "registry", f"'{t}' was {r['verdict']} by the owner (plan_check FAILs it): {r.get('fix', '')}")
        if OCCLUDER.search(t): say("WARN", "occluder", f"'{t}' looks like a black occluder (v107 rule 1: a cover must be content)")
    libt = sorted(t for t, fn in tfn.items() if fn_src_hash(fn) in lib.get(fn.__name__, set()))
    if libt: say("INFO", "library", f"library transitions (pull their frames before relying on them, v13 rule 5): {', '.join(libt)}")

    # -- determinism: a cache keyed on rounded values but filled from the exact ones
    for nm in sorted(own):
        try:
            import inspect
            tree = ast.parse(inspect.getsource(F[nm]).strip())
        except Exception: continue
        fd = tree.body[0] if tree.body and isinstance(tree.body[0], ast.FunctionDef) else None
        if not fd: continue
        params = {a.arg for a in fd.args.args}
        for node in ast.walk(fd):
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id in ("key", "k"):
                kv = ast.unparse(node.value)
                if ("//" in kv or "round(" in kv or "int(" in kv) and any(p in kv for p in params):
                    body = ast.unparse(fd)
                    fills = [nd for nd in ast.walk(fd) if isinstance(nd, ast.If) and re.match(r"(key|k)\s+not\s+in\s+_\w+", ast.unparse(nd.test))]
                    used_in_fill = {x.id for nd in fills for st in nd.body for x in ast.walk(st) if isinstance(x, ast.Name)}
                    rounded = set()                                              # the arguments the key rounds (round(), int(), //)
                    for x in ast.walk(node.value):
                        if (isinstance(x, ast.Call) and getattr(x.func, "id", "") in ("round", "int")) or (isinstance(x, ast.BinOp) and isinstance(x.op, ast.FloorDiv)):
                            rounded |= {y.id for y in ast.walk(x) if isinstance(y, ast.Name)}
                    if fills and not (used_in_fill & (rounded & params)): continue   # a fill computed from the key is fine
                    if re.search(r"if\s+(key|k)\s+not\s+in\s+_\w+", body):
                        say("WARN", "determinism", f"{nm}(): cache keyed on rounded arguments ({kv}) but filled from the exact ones: pixels depend on "
                            "which frame filled it, so partial re-renders can't verify bit-exact (compute the value from the rounded key)")
                        break

    # -- text
    if getattr(E, "TEXT", None) or getattr(E, "CAPS", None):
        say("INFO", "text", f"{len(getattr(E, 'TEXT', []) or [])} titles, {len(getattr(E, 'CAPS', []) or [])} captions: v9 construction, eased in, off faces and TikTok UI")

    # -- sound
    ev, how = sound_events(n, wd, E)
    if ev is None: say("WARN", "sound", f"sound events not checked ({how})")
    else:
        ev = sorted(ev)
        moments = []
        for e in ev:
            if moments and e[0] - moments[-1][-1][0] < 0.25: moments[-1].append(e)
            else: moments.append([e])
        lvl = "WARN" if len(ev) > 12 else "INFO"                  # guidance, not a gate: the number follows the set pieces (v107)
        say(lvl, "sound count", f"{len(ev)} effects in {len(moments)} moments over {dur:.1f} s ({how})"
            + ("; start lean: about 10-12 in 20-23 s, small transitions silent (v13 rule 4)" if lvl != "INFO" else ""))
        for e in ev:
            if BANNED_SFX.search(e[5]): say("FAIL", "sound kind", f"{e[0]:.2f} s: {e[5][:90]} (no drones, swirls, whines, chimes, bells, shine)")
        rs = [e for e in ev if re.search(r"\bRS\(", e[5])]
        if len(rs) > 3: say("WARN", "sound kind", f"{len(rs)} reverse swells: a swell on every move (v13 rule 4)")
        cuts = [s["t0"] for s in SH] + [a for _, a, b in sp] + [b for _, a, b in sp]
        for h in getattr(R, "HITS", []) or []:
            th_ = h[0] / E.FPS
            if any(abs(th_ - c) < 0.35 for c in cuts): continue
            near = [e for e in ev if abs(e[0] - th_) < 0.05]
            for e in near: say("FAIL", "beat sound", f"{e[0]:.2f} s: a sound on a beat moment (v12: beat moments keep their animation, not a sound)")

def report():
    order = {"FAIL": 0, "WARN": 1, "INFO": 2}
    for lv, rule, msg in sorted(OUT, key=lambda x: order[x[0]]): print(f"  {lv:4s} [{rule}] {msg}")
    nf = sum(1 for x in OUT if x[0] == "FAIL"); nw = sum(1 for x in OUT if x[0] == "WARN")
    print(f"preflight: {nf} FAIL, {nw} WARN")
    return nf

# ---- the transitions registry -------------------------------------------------------------------------------------
def _tr2_dump(n):
    wd = f"{ROOT}/v{n}/work"; E, R = load(n, wd)
    out = {}
    for k, v in getattr(R, "TR2", {}).items():
        fn = v[0]
        out[k] = {"fn": getattr(fn, "__name__", "?"), "pre": v[1], "post": v[2]}
    print(json.dumps(out))

def registry():
    reg = {}
    for n in (12, 13, 106, 107):
        if not os.path.exists(f"{ROOT}/v{n}/work/render{n}.py"): continue
        r = subprocess.run([sys.executable, os.path.abspath(__file__), "_tr2", str(n)], capture_output=True, text=True)
        try: d = json.loads(r.stdout.strip().split("\n")[-1])
        except Exception: print(f"v{n}: {r.stderr[-300:]}"); continue
        for k, v in d.items():
            e = reg.setdefault(k, {"pre": v["pre"], "post": v["post"], "fn": v["fn"], "engines": [], "used_in": {}})
            e["engines"].append(f"v{n}")
    for n in list(range(4, 14)) + list(range(101, 108)):
        p = f"{ROOT}/v{n}/work/edl{n}.py"
        if not os.path.exists(p): continue
        for m in re.finditer(r'tin\s*=\s*"([A-Za-z0-9_]+)"', open(p).read()):
            t = m.group(1); e = reg.setdefault(t, {"engines": [], "used_in": {}})
            e["used_in"].setdefault(f"v{n}", 0); e["used_in"][f"v{n}"] += 1
    ver = (json.load(open(REG)) if os.path.exists(REG) else {}).get("transitions", {})
    for k, e in reg.items():
        e["edit_verdicts"] = {v: VERDICT.get(v, "?") for v in e["used_in"]}
        e["owner_verdict"] = (ver.get(k) or {}).get("verdict", "unrated")
    json.dump({"_about": "generated by `python3 tools/preflight.py registry`: every transition in the Flash engines (TR2 in v12, v13) "
               "with its pre/post frames, the edits that used it and those edits' verdicts. The owner's verdict per transition is "
               "curated in studio/transitions.json (shared with the Dexter studio); owner_verdict here is a copy for reading.",
               "transitions": dict(sorted(reg.items()))}, open(USAGE, "w"), indent=1)
    print(f"{USAGE}: {len(reg)} transitions, {sum(1 for e in reg.values() if e['owner_verdict'] != 'unrated')} with an owner verdict")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "_tr2": return _tr2_dump(int(sys.argv[2]))
    if len(sys.argv) > 1 and sys.argv[1] == "_sound": return _sound_sandbox(int(sys.argv[2]), sys.argv[3], sys.argv[4])
    if len(sys.argv) > 1 and sys.argv[1] == "registry": return registry()
    if "--own" not in sys.argv:                                          # one report for both studios: plan_check runs these checks too
        os.execv(sys.executable, [sys.executable, f"{ROOT}/tools/plan_check.py"] + sys.argv[1:])
    sys.argv.remove("--own")
    ap = argparse.ArgumentParser(); ap.add_argument("n", type=int); ap.add_argument("--dir"); ap.add_argument("--hero")
    a = ap.parse_args()
    wd = os.path.abspath(a.dir) if a.dir else f"{ROOT}/v{a.n}/work"
    global REG_DATA
    check(a.n, wd, [h for h in (a.hero or "").split(",") if h])
    sys.exit(1 if report() else 0)

if __name__ == "__main__":
    main()
