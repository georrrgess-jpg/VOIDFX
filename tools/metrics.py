"""Per-edit metrics log (pipeline v2, WP1): vN/work/metrics.json, one list of events, appended, never rewritten.

Written automatically by tools/build.sh after every step:
  python3 tools/metrics.py N step NAME SECONDS STATUS [LOG]      (STATUS = exit code; LOG = the step's log, parsed for
                                                                  QC failures / frame counts when present)
Written by the studio during review (owner-note categories from plan §1.1, review catches from §1.2, rounds):
  python3 tools/metrics.py N note CATEGORY "the owner's words"    e.g. motion, look, clip-quality, text, sound, loop, faces
  python3 tools/metrics.py N catch CATEGORY "what was caught"     a problem found by eye before delivery (QC missed it)
  python3 tools/metrics.py N round K                              revision round K delivered
  python3 tools/metrics.py N verdict standard|rejected
  python3 tools/metrics.py N show                                 totals per step, full renders, notes and catches

Every event carries: the time, the git commit (short) and whether the tree had uncommitted changes.
"""
import os, sys, json, time, subprocess, fcntl, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def git(*a):
    try:
        return subprocess.run(["git", "-C", ROOT, *a], capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        return ""


def path(n): return f"{ROOT}/v{n}/work/metrics.json"


def append(n, ev):
    p = path(n); os.makedirs(os.path.dirname(p), exist_ok=True)
    ev = dict(at=time.strftime("%Y-%m-%d %H:%M:%S"), commit=git("rev-parse", "--short", "HEAD"),
              dirty=bool(git("status", "--porcelain", "--untracked-files=no")), **ev)
    with open(p + ".lock", "w") as lk:                       # build steps and the studio may write at the same time
        fcntl.flock(lk, fcntl.LOCK_EX)
        data = json.load(open(p)) if os.path.exists(p) else dict(edit=f"v{n}", events=[])
        data["events"].append(ev)
        tmp = p + ".tmp"; json.dump(data, open(tmp, "w"), indent=1); os.replace(tmp, p)
    return ev


def parse_log(step, log):
    """pull what is worth keeping out of a step's log: QC failures, the frame count of a full render."""
    if not log or not os.path.exists(log): return {}
    txt = open(log, errors="replace").read(); out = {}
    if step == "qc":
        out["qc_failed"] = re.findall(r"\[FAIL\] (.+)", txt)
        out["qc_passed"] = len(re.findall(r"\[PASS\]", txt))
    if step == "video":
        fr = re.findall(r"frame (\d+)/(\d+)", txt)
        if fr: out["frames"] = int(fr[-1][1])
        out["completed"] = "done" in txt.splitlines()[-1] if txt.strip() else False
    return out


def show(n):
    p = path(n)
    if not os.path.exists(p): print(f"no metrics for v{n} yet"); return
    ev = json.load(open(p))["events"]; steps = {}
    for e in ev:
        if e["kind"] == "step": steps.setdefault(e["step"], []).append(e)
    print(f"v{n}: {len(ev)} events")
    for s, es in steps.items():
        t = [e["seconds"] for e in es]
        print(f"  {s:10s} runs {len(es):3d}  total {sum(t) / 60:7.1f} min  last {t[-1]:6.0f} s  min {min(t):6.0f} s")
    fulls = [e for e in steps.get("video", []) if e.get("status") == 0]
    if fulls: print(f"  full renders: {len(fulls)} (" + ", ".join(f"{e['seconds']:.0f} s" for e in fulls) + ")")
    qc = steps.get("qc", [])
    if qc: print(f"  last QC: {len(qc[-1].get('qc_failed', []))} failed " + str(qc[-1].get("qc_failed", [])))
    for k in ("note", "catch"):
        cats = {}
        for e in ev:
            if e["kind"] == k: cats[e["category"]] = cats.get(e["category"], 0) + 1
        if cats: print(f"  {k}s by category: " + ", ".join(f"{c} {m}" for c, m in sorted(cats.items(), key=lambda x: -x[1])))
    rounds = [e["round"] for e in ev if e["kind"] == "round"]
    if rounds: print(f"  rounds delivered: {max(rounds)}")
    vd = [e["verdict"] for e in ev if e["kind"] == "verdict"]
    if vd: print(f"  verdict: {vd[-1]}")


if __name__ == "__main__":
    if len(sys.argv) < 3: print(__doc__); sys.exit(1)
    n, kind, rest = sys.argv[1].lstrip("v"), sys.argv[2], sys.argv[3:]
    if kind == "step":
        name, secs, status = rest[0], float(rest[1]), int(rest[2])
        append(n, dict(kind="step", step=name, seconds=secs, status=status, **parse_log(name, rest[3] if len(rest) > 3 else None)))
    elif kind in ("note", "catch"): append(n, dict(kind=kind, category=rest[0], text=" ".join(rest[1:])))
    elif kind == "round": append(n, dict(kind="round", round=int(rest[0])))
    elif kind == "verdict": append(n, dict(kind="verdict", verdict=rest[0]))
    elif kind == "show": show(n)
    else: print(__doc__); sys.exit(1)
