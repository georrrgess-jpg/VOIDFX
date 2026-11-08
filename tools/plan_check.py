"""plan_check (pipeline v2, WP7): the owner's recurring notes, checked on the EDL BEFORE any render.

  python3 tools/plan_check.py N            # report; exit 1 on any FAIL (build.sh video / ship stop there)
  python3 tools/plan_check.py N --json     # the same as JSON (for the critique pass and the report)
  python3 tools/plan_check.py N --edl PATH # check another EDL file (e.g. an earlier revision) against the same rules
  python3 tools/plan_check.py N --dir PATH # check a copy of the whole work folder (EDL + renderer + audio), e.g. from git
  python3 tools/plan_check.py N --hero f,g # name the hero asset's drawing functions (or HERO = [...] in the EDL)

One report for both studios: its own checks and the Flash studio's preflight checks (tools/preflight.py: a transition
missing from the engine, set pieces, held-frame judder, the same source shot, the hero found in the code's call graph,
the Flash emblem, cache determinism, length, and the sound events with their kinds), merged 2026-11-08, one check per rule.

Every check is a note the owner has already given (the evidence is printed with it), so a first delivery that passes
doesn't spend a round on it. It reads the EDL, studio/transitions.json (the owner's verdict on every transition), the
renderer's transition windows (TR2) and beat camera, the face tracks, and, once the audio is built, the effects stem.
An EDL can accept a WARN or FAIL on purpose with  PLAN_ACCEPT = {"check_id": "why"}  (it is printed, not hidden).
Optional EDL fields it uses: HERO_TINS (the hero asset's transitions), SIGNATURE (the signature graphic transition).
"""
import os, sys, json, importlib, importlib.util, math
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = json.load(open(f"{ROOT}/studio/transitions.json"))["transitions"]          # the owner's curated verdicts (usage: transitions_usage.json)
GENERIC_MAX, SIG_MIN_S, DENSITY_MIN, ZOOM_MAX, HOLD_WARN = 0.50, 0.80, 0.70, 1.10, 1.5   # calibrated so the approved v107, v12, v106 pass
SOUND_WARN, SOUND_FAIL = 16, 30                      # sound events (layered hits grouped): v106 and v13 approved after cuts at ~11-14


def load(n, edl_path=None, wd=None):
    w = wd or f"{ROOT}/v{n}/work"; os.chdir(w); sys.path.insert(0, w); argv = sys.argv; sys.argv = ["x", "video", "frames/x"]
    if edl_path:                                                                          # check another EDL (an earlier revision)
        spec = importlib.util.spec_from_file_location(f"edl{n}", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", edl_path)) if not os.path.isabs(edl_path) else edl_path)
        E = importlib.util.module_from_spec(spec); sys.modules[f"edl{n}"] = E; spec.loader.exec_module(E)
    else:
        E = importlib.import_module(f"edl{n}")
    try: R = importlib.import_module(f"render{n}")
    except Exception as ex: R = None; print(f"(renderer not loaded: {ex}; transition windows and the beat camera are skipped)")
    sys.argv = argv
    trk = json.load(open(f"tracks{n}.json")) if os.path.exists(f"tracks{n}.json") else {}
    return E, R, trk


def src_range(s):
    ts = [p[1] for p in s.get("tmap", []) if isinstance(p, (list, tuple)) and len(p) == 2]
    return (min(ts), max(ts)) if ts else (None, None)


_TH = {}
def _thumb(E, s):
    if s["n"] not in _TH:
        import cv2
        ts = [p[1] for p in s["tmap"] if isinstance(p, (list, tuple))]; cap = cv2.VideoCapture(E.SRC[s["src"]][0])
        cap.set(cv2.CAP_PROP_POS_MSEC, (min(ts) + max(ts)) / 2 * 1000); ok, im = cap.read(); _TH[s["n"]] = im if ok else None
    return _TH[s["n"]]

def look_alike(E, a, b):
    """(structure, colour) similarity of the two shots' middle source frames: 32x18 grey correlation, HSV histogram correlation."""
    import cv2
    A, B = _thumb(E, a), _thumb(E, b)
    if A is None or B is None: return 0.0, 0.0
    g = [cv2.resize(cv2.cvtColor(x, cv2.COLOR_BGR2GRAY), (32, 18), interpolation=cv2.INTER_AREA).astype(np.float32).ravel() for x in (A, B)]
    g = [(x - x.mean()) / (x.std() + 1e-6) for x in g]
    hs = [cv2.calcHist([cv2.cvtColor(x, cv2.COLOR_BGR2HSV)], [0, 1], None, [16, 8], [0, 180, 0, 256]) for x in (A, B)]
    hs = [cv2.normalize(x, x).flatten() for x in hs]
    return float((g[0] * g[1]).mean()), float(cv2.compareHist(hs[0], hs[1], cv2.HISTCMP_CORREL))


def sound_events(n):
    """onsets on the effects stem: 10 ms RMS envelope, a rise of 9 dB over the previous 60 ms above -42 dBFS, 90 ms apart."""
    p = f"{ROOT}/v{n}/audio/stem_fx.wav"
    if not os.path.exists(p): return None
    import scipy.io.wavfile as wf
    sr, a = wf.read(p); a = a.astype(np.float32); a = a.mean(1) if a.ndim > 1 else a
    hop = int(sr * 0.010); k = len(a) // hop
    env = 20 * np.log10(np.sqrt((a[:k * hop].reshape(k, hop) ** 2).mean(1)) + 1e-9)
    on, last = [], -99
    for i in range(6, k):
        if env[i] > -42 and env[i] - env[i - 6:i].min() > 9 and i - last >= 9: on.append(i * hop / sr); last = i
    ev = []                                                                               # a layered hit or a run of hits = one event
    for t in on:
        if not ev or t - ev[-1][-1] > 0.25: ev.append([t])
        else: ev[-1].append(t)
    return [e[0] for e in ev]


# the Flash studio's preflight rules: kept, replaced by one of ours (same rule), or recalibrated on the approved edits
PF_DROP = {"no plain cuts", "loop", "variety", "sharpness", "registry", "text"}    # ours covers these (plain cuts: downbeat-aware)
def preflight_results(n, wd, hero):
    """run tools/preflight.py's checks in this process (the EDL and renderer are already imported) -> [(level, rule, msg)]"""
    try:
        sys.path.insert(0, f"{ROOT}/tools"); import io, contextlib, preflight as PF
        PF.OUT.clear()
        with contextlib.redirect_stdout(io.StringIO()): PF.check(int(n), wd, hero)
        return list(PF.OUT), None
    except Exception as ex:
        return [], f"{type(ex).__name__}: {ex}"


def main():
    n = sys.argv[1]; as_json = "--json" in sys.argv
    arg = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
    edl_path, wd, hero_cli = arg("--edl"), arg("--dir"), [h for h in (arg("--hero") or "").split(",") if h]
    wd = os.path.abspath(wd) if wd else f"{ROOT}/v{n}/work"
    E, R, trk = load(n, edl_path, wd)
    FPS = getattr(E, "FPS", 60); S = E.SHOTS; dur = getattr(E, "DUR_F", S[-1]["f1"]) / FPS
    accept = getattr(E, "PLAN_ACCEPT", {}); res = []
    def add(level, cid, msg, ev=""):
        if level != "ok" and cid in accept: level, msg = "accepted", f"{msg}  [accepted: {accept[cid]}]"
        res.append(dict(level=level, id=cid, msg=msg, evidence=ev))
    TR = getattr(R, "TR2", {}) if R else {}
    tins = [(i, s["tin"]) for i, s in enumerate(S) if s.get("tin")]
    touts = [(i, s["tout"]) for i, s in enumerate(S) if s.get("tout")]
    used = [t for _, t in tins] + [t for _, t in touts]

    # 1. the owner's verdicts on each transition
    for t in sorted(set(used)):
        r = REG.get(t)
        if r is None or "verdict" not in r: continue
        if r["verdict"] in ("banned", "rejected"):
            add("FAIL", f"verdict:{t}", f"`{t}` was {r['verdict']} by the owner" + (f"; fix first: {r['fix']}" if r.get("fix") else ""), r["evidence"])
        for tag, why in (("black_occluder", "a black occluder (bars, boxes, a dark surround)"), ("face_gimmick", "a graphic converging on a face")):
            if tag in r.get("tags", []) and r["verdict"] not in ("banned", "rejected"):
                add("WARN", f"{tag}:{t}", f"`{t}` can read as {why}: check it on stills", "v107 rev 3-4")
        if REG.get(t, {}).get("caution") and REG[t].get("verdict") not in ("banned", "rejected"):    # a technical trap, not a verdict
            add("WARN", f"caution:{t}", f"`{t}`: {REG[t]['caution']}", REG[t].get("evidence", "the registry"))
    unrated = sorted(t for t in set(used) if t not in REG or "verdict" not in REG[t])
    add("ok", "unrated", f"{len(unrated)} transitions without an owner verdict yet: {', '.join(unrated) or '-'}")

    # 2. variety: generic share, repeats, the hero asset
    gen = [t for t in used if "generic" in REG.get(t, {}).get("tags", [])]
    share = len(gen) / max(1, len(used))
    add("WARN" if share > GENERIC_MAX else "ok", "generic_share", f"generic transitions {len(gen)}/{len(used)} = {share:.0%} (limit {GENERIC_MAX:.0%})",
        "v9: 'too many quick, generic transitions'")
    for t in sorted(set(used)):
        c = used.count(t)
        if c > 2 and "generic" not in REG.get(t, {}).get("tags", []):
            add("WARN", f"repeat:{t}", f"`{t}` is used {c} times: every transition should be a different idea", "v13 rev 2")
    fam = {}
    for t in used:
        if REG.get(t, {}).get("family"): fam.setdefault(REG[t]["family"], []).append(t)
    for f_, ts in sorted(fam.items()):
        c = len(ts); lvl = "FAIL" if c > 8 else "WARN" if c > 4 else "ok"
        add(lvl, f"family:{f_}", f"the {f_} hero asset carries {c} transitions (a motif: 2-4)",
            "v13 rev 2: 'I don't like that the singularity is the primary object in every transition and animation'")
    hero = getattr(E, "HERO_TINS", None)
    if hero:
        hc = sum(1 for t in used if t in hero)
        add("FAIL" if hc > 4 else "ok", "hero_motif", f"the hero asset carries {hc} transitions (at most 4: its set piece, the focal piece, the loop)",
            "v13 rev 2: 'the singularity is the primary object in every transition and animation'")

    # 3. density
    dens = len(used) / dur
    add("WARN" if dens < DENSITY_MIN else "ok", "density", f"{len(used)} designed transitions in {dur:.1f} s = {dens:.2f}/s (target >= {DENSITY_MIN})",
        "v103: 'more animations and transitions moving forward'")

    # 4. a signature graphic-into-transition, and time to read it
    declared = list(getattr(E, "SIGNATURE", []))
    sig = [t for t in used if "signature" in REG.get(t, {}).get("tags", [])] + declared
    add("ok" if sig else "WARN", "signature", f"signature graphic transitions: {', '.join(sorted(set(sig))) or 'none'}",
        "4 of the last 4 edits: the owner asked for 'one more really cool custom graphic into a transition'")
    for t in sorted(set(declared)):
        if t in TR:
            secs = (TR[t][1] + TR[t][2]) / FPS
            if secs < SIG_MIN_S: add("WARN", f"sig_time:{t}", f"`{t}` is on screen {secs:.2f} s (give a signature transition ~1 s)", "v106 rev 3: 'slow down the tear drop transition so it's more visible'")

    # 5. the loop is a set piece
    loop = [t for _, t in touts if _ == len(S) - 1] + ([S[0]["tin"]] if S[0].get("tin") else [])
    add("ok" if loop else "FAIL", "loop", f"loop set piece: {', '.join(loop) or 'none (the last shot just cuts to the first)'}",
        "v107 rev 2: 'the loop is pretty low effort'; v105 rule 3")

    # 6. never reuse a clip
    rng = [(s["n"], s["src"], *src_range(s)) for s in S]
    for i in range(len(rng)):
        for j in range(i + 1, len(rng)):
            a, b = rng[i], rng[j]
            if a[1] != b[1] or None in a[2:] + b[2:]: continue
            ov = min(a[3], b[3]) - max(a[2], b[2])                                          # > 0: the same frames twice
            loop_pair = i == 0 and j == len(rng) - 1                                        # the last shot continuing frame 0's take (a loop design)
            if ov > 0.05:
                add("FAIL", f"reuse:{a[0]}/{b[0]}", f"`{a[0]}` ({a[2]:.2f}-{a[3]:.2f} s) and `{b[0]}` ({b[2]:.2f}-{b[3]:.2f} s) show the same frames of `{a[1]}`",
                    "v107 rev 2: 'you reuse the same clip around the 17-second mark ... and the 19-second mark'")
            elif j > i + 1 and ov > -0.5 and not loop_pair:
                add("WARN", f"retake:{a[0]}/{b[0]}", f"`{b[0]}` picks up `{a[0]}`'s take ({-ov:.2f} s later in `{a[1]}`) after {j - i - 1} other shots: make sure it doesn't read as a repeat",
                    "v107 rev 2: 'you reuse the same clip'")
    # ... and two shots that LOOK the same (the same close-up from the same scene), which is what the owner saw in v107 rev 1
    for i in range(len(S)):
        for j in range(i + 2, len(S)):
            a, b = S[i], S[j]
            if a["src"] != b["src"] or (i == 0 and j == len(S) - 1): continue
            ra, rb = src_range(a), src_range(b)
            if None in ra + rb or abs(sum(ra) / 2 - sum(rb) / 2) > 30: continue
            c, h = look_alike(E, a, b)
            if c >= 0.75 and h >= 0.75:
                add("FAIL", f"lookalike:{a['n']}/{b['n']}", f"`{a['n']}` and `{b['n']}` look like the same clip (structure {c:.2f}, colour {h:.2f}; same scene of `{a['src']}`)",
                    "v107 rev 2: 'you reuse the same clip around the 17-second mark ... and the 19-second mark' (two smiling close-ups from the same parade scene)")

    # 7. spins and dives land on a centred, tracked face
    for i, t in tins:
        if "lands_on_face" in REG.get(t, {}).get("tags", []):
            s = S[i]; tr = trk.get(s["n"]) or []
            ok = s.get("face", "largest") is not None and len(tr) > 0
            add("ok" if ok else "FAIL", f"landing:{s['n']}", f"`{t}` lands on `{s['n']}`: " + ("a tracked face (the engine centres it)" if ok else "no tracked face to land on"),
                "v107 rev 2: 'the final shot doesn't have a centered shot of Dexter'")

    # 8. zoom on 720p sources
    for s in S:
        zs = [p[1] for p in s.get("z", []) if isinstance(p, (list, tuple))]
        if zs and max(zs) > ZOOM_MAX: add("WARN", f"zoom:{s['n']}", f"`{s['n']}` zooms to {max(zs):.2f} (keep <= {ZOOM_MAX} on 720p)", "v105: 'the quality of some of the clips'")

    # 9. text: designed titles earn their place; spell-outs on an even grid
    T = getattr(E, "TEXT", [])
    titles = [t for t in T if t.get("style") not in ("cap", "lyric", "behind")]
    add("WARN" if len(titles) > 2 else "ok", "titles", f"{len(titles)} designed titles", "v12: the owner removed NIGHT and BLOOM; titles must earn their place")
    for t in T:
        letters = [w for w in t.get("words", []) if len(w[0]) == 1]
        if len(letters) >= 3:
            gaps = np.diff([w[1] for w in letters]) * FPS
            cv = gaps.std() / max(1e-6, gaps.mean())
            ok = 7 <= gaps.mean() <= 14 and cv < 0.15
            add("ok" if ok else "WARN", f"spell:{''.join(w[0] for w in letters)}",
                f"spell-out {''.join(w[0] for w in letters)}: {gaps.mean():.1f} frames a letter, spread {cv:.0%} (even grid, 7-14 frames)",
                "v107 rev 3: 'how slow it writes dexters name ... not too fast and not too slow'")

    # 10. dead spans: a clean stretch > 1.1 s with no cut, no transition and no beat hit
    if R is not None and hasattr(R, "beat_phase"):
        for k, s in enumerate(S):
            a = s["f0"] + (TR.get(s.get("tin"), (0, 0, 0))[2] if s.get("tin") else 0)
            nx = S[k + 1] if k + 1 < len(S) else None
            b = s["f1"] - (TR.get(nx.get("tin"), (0, 0, 0))[1] if nx and nx.get("tin") else 0)
            if s.get("tout"): b = min(b, s["f0"] + (s["f1"] - s["f0"]) // 2)
            hits, prev = [], None
            for f in range(max(a, 0), max(a, b)):
                ph, bi, hook = R.beat_phase(f)[:3]
                if hook and prev is not None and bi != prev: hits.append(f)
                prev = bi
            marks = [a] + hits + [b]; gap = max(np.diff(marks)) / FPS if len(marks) > 1 else 0
            if gap > 1.1:
                add("WARN" if gap > HOLD_WARN else "ok", f"dead:{s['n']}", f"`{s['n']}` holds {gap:.2f} s with no cut, transition or beat hit (frames {a}-{b}): "
                    + ("plan a designed beat inside it" if gap > HOLD_WARN else "make sure an animation runs through it"),
                    "v104: 'one span had some headspace'; v106 rev 2: 'identify one space where there isn't anything happening' (motionqc measures it after the render)")

    # 11. plain cuts: a designed transition is the default; a clean cut lands on a beat hit with the camera's punch (v107)
    for i, s in enumerate(S):
        if i == 0 or s.get("tin"): continue
        on_beat = False
        if R is not None and hasattr(R, "beat_phase"):
            for f in range(s["f0"] - 1, s["f0"] + 2):
                b0, b1 = R.beat_phase(f - 1), R.beat_phase(f)
                if b1[2] and b1[1] != b0[1]: on_beat = True
        add("ok" if on_beat else "WARN", f"cut:{s['n']}", f"plain cut into `{s['n']}` at {s['f0'] / FPS:.2f} s: " +
            ("on a beat hit with the camera's punch (v107's approved fallback)" if on_beat else "off the beat: design a transition, or move the cut onto a downbeat"),
            "v6: 'no plain hard cuts in quiet or dialogue sections'; v107 rev 4: the clean downbeat cut was approved")

    # 12. the Flash studio's preflight checks (one report; overlaps dropped; recalibrated where the approved edits disagree)
    hero = hero_cli or list(getattr(E, "HERO", []) or [])
    pf, err = preflight_results(n, wd, hero)
    if err: add("WARN", "preflight", f"preflight checks not run ({err})")
    pf_sound = any(r == "sound count" for _, r, _ in pf)
    for lv, rule, msg in pf:
        if rule in PF_DROP: continue
        if rule == "clip reuse" and " overlap in " in msg: continue                     # ours: reuse/lookalike
        if rule == "transition" and any(REG.get(t, {}).get("set_piece") and f"'{t}'" in msg for t in used): continue   # handled by the edit's own code
        if rule == "occluder" and any(x["id"].startswith(("black_occluder:", "verdict:")) for x in res): continue
        if rule == "sound kind" and lv == "FAIL": lv, msg = "WARN", msg + " (a WARN: the approved v107 has a swirl on the headspin)"
        level = {"FAIL": "FAIL", "WARN": "WARN", "INFO": "ok"}[lv]
        add(level, f"pf:{rule}:{msg[:40]}", f"[{rule}] {msg}", "preflight (the Flash studio's checks)")

    # 13. sound budget (after the audio is built; the preflight count of placed effects is used when it ran)
    ev = None if pf_sound else sound_events(n)
    if ev is not None:
        c = len(ev); lvl = "FAIL" if c > SOUND_FAIL else "WARN" if c > SOUND_WARN else "ok"
        add(lvl, "sound", f"{c} sound events on the effects stem (start lean: about 10-12; warn > {SOUND_WARN}, fail > {SOUND_FAIL})",
            "v12, v106, v13: the owner cut 'the tedious sound effects' three edits in a row")

    order = {"FAIL": 0, "WARN": 1, "accepted": 2, "ok": 3}
    res.sort(key=lambda r: order[r["level"]])
    nf = sum(r["level"] == "FAIL" for r in res); nw = sum(r["level"] == "WARN" for r in res)
    if as_json: print(json.dumps(dict(fail=nf, warn=nw, checks=res), indent=1)); sys.exit(1 if nf else 0)
    print(f"plan_check v{n}: {nf} FAIL, {nw} WARN  (the owner's recurring notes, on the EDL)")
    for r in res:
        print(f"  {r['level']:8s} {r['msg']}" + (f"\n           <- {r['evidence']}" if r["level"] in ("FAIL", "WARN") and r["evidence"] else ""))
    sys.exit(1 if nf else 0)


if __name__ == "__main__":
    main()
