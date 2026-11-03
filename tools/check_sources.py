"""Check that every shot's source range sits inside ONE detected source shot (no leaked frames from the neighbours).

Usage: python3 tools/check_sources.py N        (reads vN/work/edlN.py and vN/work/shots_<pack>.json, plus v3 shot lists)
"""
import sys, os, json, glob, importlib
n = sys.argv[1]; V = f"v{n}"; ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, f"{ROOT}/{V}/work"); E = importlib.import_module(f"edl{n}")
bad = 0
for s in E.SHOTS:
    pk = s["src"]; c = [f"{ROOT}/{V}/work/shots_{pk}.json"] + sorted(glob.glob(f"{ROOT}/v*/work/shots_{pk}.json"))
    c = [p for p in c if os.path.exists(p)]
    if not c: print(f"  {s['n']:12s} {pk}: no shot list (run analyze.py)"); continue
    sh = json.load(open(c[0])); sh = sh["shots"] if isinstance(sh, dict) else sh
    ts = [k[1] for k in s["tmap"]]; a, b = min(ts), max(ts)
    host = [x for x in sh if x["t0"] - 0.02 <= a < x["t1"] + 0.02]
    ok = bool(host) and b <= host[0]["t1"] + 0.02
    if not ok: bad += 1
    print(f"  {'OK ' if ok else 'BAD'} {s['n']:12s} {pk} {a:8.2f}-{b:8.2f}  in shot {host[0]['t0']:.2f}-{host[0]['t1']:.2f}" if host else f"  BAD {s['n']} {a}-{b}: starts in no shot")
print("source ranges:", "all inside their shots" if bad == 0 else f"{bad} shot(s) leak into a neighbouring source shot")
