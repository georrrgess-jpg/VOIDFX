"""report (pipeline v2): the "Measured" block for the README and the handoff, written from the tools' own outputs.

  python3 tools/report.py N         # -> vN/work/measured.md (and printed)

Reads qc.log, motionqc.json, faceqc.json, mixcheck.json, sharpness.json, metrics.json and plan_check, so the numbers in
the README, the edit report section 9 and edits.json are the measured ones, not retyped.
"""
import os, sys, json, re, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def jload(p):
    try: return json.load(open(p))
    except Exception: return None


def main():
    n = sys.argv[1]; w = f"{ROOT}/v{n}/work"; L = []
    qc = open(f"{w}/qc.log").read() if os.path.exists(f"{w}/qc.log") else ""
    passes = re.findall(r"\[(PASS|FAIL)\] (.+)", qc); npass = sum(p == "PASS" for p, _ in passes)
    uniq = {t for _, t in passes}
    L.append(f"- **QC:** {npass}/{len(passes)} on the encode" + ("" if npass == len(passes) else "; FAIL: " + "; ".join(t for p, t in passes if p == "FAIL")) + f" ({len(uniq)} distinct checks).")
    m = re.search(r"AAC (-?[\d.]+) LUFS/(-?[\d.]+) dBTP", open(f"{w}/audio.log").read()) if os.path.exists(f"{w}/audio.log") else None
    m = m or re.search(r"loudness (-?[\d.]+) LUFS, true peak (-?[\d.]+) dBTP", qc)
    if m: L.append(f"- **Loudness:** {m.group(1)} LUFS, true peak {m.group(2)} dBTP after AAC.")
    seam = re.search(r"blurred diff ([\d.]+)", qc); step = re.search(r"loop seam step ([\d.]+)", qc)
    mq = jload(f"{w}/motionqc.json") or {}
    lp = mq.get("loop", {})
    L.append(f"- **Loop seam:** blurred difference {seam.group(1) if seam else '?'} (gate ≤ 1)" + (f"; audio seam step {step.group(1)}" if step else "")
             + (f"; picture wrap step {lp.get('wrap_step')} vs local median {lp.get('local_median')}" + (" (SPIKE)" if lp.get("spike") else "") if lp else "") + ".")
    fl = re.search(r"7b\. flashes: (\d+) events, max (\d+) per second; white-out runs[^:]*: (\[.*?\])", qc)
    if fl: L.append(f"- **Flashes:** {fl.group(1)} events, at most {fl.group(2)} a second; white-outs {fl.group(3)}.")
    tf = re.search(r"(\d+) frames where a face box reaches into a text band", qc)
    L.append(f"- **Text over faces:** {tf.group(1) if tf else 0} frames (see qc.log §3 for which; frames inside transitions are expected).")
    fq = jload(f"{w}/faceqc.json")
    if fq: L.append(f"- **Faces vs effects:** {sum(len(r) for r in fq.get('runs', []))} flags in {len(fq.get('runs', []))} runs: " + ", ".join(f"{r[0]}–{r[-1]}" for r in fq.get("runs", [])) + ".")
    if mq:
        pops = mq.get("pops", []); unexp = [p["f"] for p in pops if str(p.get("kind", "")).upper().startswith("UNEXPL")]
        kinds = {}
        for p in pops: kinds[p.get("kind")] = kinds.get(p.get("kind"), 0) + 1
        L.append(f"- **Motion audit:** {len(pops)} pops (" + ", ".join(f"{k} {v}" for k, v in sorted(kinds.items(), key=lambda x: str(x[0]))) + ")"
                 + (f"; UNEXPLAINED at {unexp} (check signoff_pops.jpg)" if unexp else "") + f"; dead spans {len(mq.get('dead', []))}"
                 + f"; judder flags {sum(1 for j in mq.get('judder', []) if j.get('flag'))}.")
    sh = jload(f"{w}/sharpness.json")
    if sh: L.append(f"- **Sharpness:** SOFT: {', '.join(s['n'] for s in sh['shots'] if 'SOFT' in s.get('flags', [])) or 'none'}; max zoom {max(s['zmax'] for s in sh['shots']):.2f}.")
    try:
        pc = json.loads(subprocess.run([sys.executable, f"{ROOT}/tools/plan_check.py", n, "--json"], capture_output=True, text=True).stdout)
        L.append(f"- **plan_check:** {pc['fail']} FAIL, {pc['warn']} WARN" + "".join(f"; {c['level']}: {c['msg']}" for c in pc["checks"] if c["level"] in ("FAIL", "WARN")) + ".")
    except Exception: pass
    mt = jload(f"{w}/metrics.json")
    if mt:
        r = mt.get("round", 1); st = [s for s in mt["stages"] if s.get("round", 1) == r]
        vid = [s for s in st if s["step"].startswith("video") or s["step"] == "fullvideo"]
        L.append(f"- **Effort this round ({r}):** {len(vid)} renders ({sum(s['s'] for s in vid) / 60:.1f} min), QC {sum(s['s'] for s in st if s['step'] == 'qc') / 60:.1f} min.")
    out = "\n".join(L) + "\n"
    open(f"{w}/measured.md", "w").write(out); print(out, end="")


if __name__ == "__main__":
    main()
