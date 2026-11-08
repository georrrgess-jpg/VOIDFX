"""Per-edit metrics (pipeline v2, WP1): vN/work/metrics.json, so the pilots can be compared with v10, v11 and v105.

  python3 tools/metrics.py N stage STEP SECONDS [--rc CODE]     # build.sh calls this after every step
  python3 tools/metrics.py N round R                            # an owner round starts (1 = first delivery)
  python3 tools/metrics.py N note CATEGORY "the owner's words"  # categorise each owner note (categories below)
  python3 tools/metrics.py N catch CATEGORY "what review found" # a defect found by eye in a studio review
  python3 tools/metrics.py N verdict standard|rejected "the owner's words"
  python3 tools/metrics.py N summary

Note categories (§1.1 of sync/PIPELINE_V2_PLAN.md): density, replace_shot, plain_effect, loop, quality, text, defect, other.
Catch categories (§1.2): face_overlay, whiteout, seam, framing, text_face, mix, restyle, drawn_asset, other.
"""
import os, sys, json, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTES = {"density", "replace_shot", "plain_effect", "loop", "quality", "text", "defect", "other"}
CATCHES = {"face_overlay", "whiteout", "seam", "framing", "text_face", "mix", "restyle", "drawn_asset", "other"}

def path(n): return f"{ROOT}/v{n}/work/metrics.json"

def load(n):
    p = path(n)
    if os.path.exists(p):
        try: return json.load(open(p))
        except Exception: pass
    return {"edit": f"v{n}", "round": 1, "stages": [], "notes": [], "catches": []}

def save(n, m):
    tmp = path(n) + ".tmp"; json.dump(m, open(tmp, "w"), indent=1); os.replace(tmp, path(n))

def now(): return time.strftime("%Y-%m-%d %H:%M:%S")

def summary(m):
    st = m["stages"]; by = {}
    for e in st: by.setdefault(e["step"].split(":")[0], []).append(e["s"])
    print(f"{m['edit']}: round {m['round']}" + (f"; verdict {m['verdict']['verdict']}" if m.get("verdict") else ""))
    for k, v in by.items(): print(f"  {k:10s} x{len(v):2d}  total {sum(v) / 60:6.1f} min  last {v[-1]:6.0f} s")
    full = [e for e in st if e["step"] == "video"]
    print(f"  full renders: {len(full)} ({len(full) / max(1, m['round']):.1f} per round)")
    for kind in ("notes", "catches"):
        c = {}
        for e in m[kind]: c[e["cat"]] = c.get(e["cat"], 0) + 1
        if c: print(f"  {kind}: " + ", ".join(f"{k} {v}" for k, v in sorted(c.items(), key=lambda kv: -kv[1])))

def main():
    if len(sys.argv) < 3: print(__doc__); sys.exit(1)
    n, cmd, args = int(sys.argv[1]), sys.argv[2], sys.argv[3:]
    if not os.path.isdir(f"{ROOT}/v{n}/work"): sys.exit(f"no v{n}/work")
    m = load(n)
    if cmd == "stage":
        rc = int(args[args.index("--rc") + 1]) if "--rc" in args else 0
        m["stages"].append({"t": now(), "round": m["round"], "step": args[0], "s": float(args[1]), "rc": rc})
    elif cmd == "round": m["round"] = int(args[0]); m.setdefault("round_starts", {})[args[0]] = now()
    elif cmd in ("note", "catch"):
        cat, text = args[0], " ".join(args[1:])
        if cat not in (NOTES if cmd == "note" else CATCHES): sys.exit(f"unknown category {cat}")
        m["notes" if cmd == "note" else "catches"].append({"t": now(), "round": m["round"], "cat": cat, "text": text})
    elif cmd == "verdict": m["verdict"] = {"t": now(), "round": m["round"], "verdict": args[0], "words": " ".join(args[1:])}
    elif cmd == "summary": summary(m); return
    else: print(__doc__); sys.exit(1)
    save(n, m)

if __name__ == "__main__":
    main()
