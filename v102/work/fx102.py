# ============================================================================ v102 — LET GO: The Flash, speed + lightning toolkit
# (spliced into render102.py before main() by splice.py; the last definitions win, so this section owns grade, finish, text, render)
LGOLD = np.array([0.38, 0.82, 1.00], np.float32)     # Barry's lightning (BGR): gold
LCORE = np.array([0.86, 0.97, 1.00], np.float32)     # white-hot core
LEMB = np.array([0.12, 0.42, 1.00], np.float32)      # ember orange
CRIM = np.array([0.10, 0.08, 0.80], np.float32)      # suit crimson
STEEL = np.array([0.30, 0.20, 0.12], np.float32)     # cold steel shadow
F_CAP = "/usr/share/fonts/opentype/inter/InterDisplay-BlackItalic.otf"

# ---------------------------------------------------------------------------- grade: storm (crimson suit, gold lightning, steel shadows)
def correction(s):
    if s["n"] in CORR: return CORR[s["n"]]
    t = tmap(s, 0.5); img = sample(s["src"], t).astype(np.float32) / 255
    L = img[..., 0] * 0.114 + img[..., 1] * 0.587 + img[..., 2] * 0.299
    fa = face_at(s, t) if s.get("face") is not None else None
    if fa:
        r = int(fa[2] * 0.3); x, y = int(fa[0]), int(fa[1])
        patch = L[max(0, y - r):y + r, max(0, x - r):x + r]; face = float(np.percentile(patch, 65)) if patch.size else float(L.mean())
    else:
        face = float(np.percentile(L, 70))
    g = clamp(math.log(s.get("target", 0.42)) / math.log(clamp(face, 0.02, 0.97)), 0.75, 1.25)
    m = img.reshape(-1, 3).mean(0); gains = np.clip((m.mean() / (m + 1e-6)) ** 0.08, 0.94, 1.06)
    CORR[s["n"]] = (g, gains.astype(np.float32)); return CORR[s["n"]]

def grade(img, s, f):
    g, gains = correction(s)
    x = np.clip(img * gains, 0, 1) ** g
    lx, ly = lut(); x = np.interp(x, lx, ly).astype(np.float32)
    B_, G_, R_ = x[..., 0], x[..., 1], x[..., 2]
    red = np.clip((R_ - np.maximum(G_, B_)) * 3.0, 0, 1)[..., None]
    L = (x[..., 0] * 0.114 + x[..., 1] * 0.587 + x[..., 2] * 0.299)[..., None]
    x = L + (x - L) * (1.00 + 0.16 * red)
    x = x + (1 - L) ** 2.6 * np.array([0.030, 0.012, -0.012], np.float32)            # steel-blue shadows
    x = x + L ** 1.9 * np.array([-0.030, 0.008, 0.030], np.float32)                  # warm gold highlights
    x = x * 0.80 + (x * x * (3 - 2 * x)) * 0.20
    return np.clip(x * 0.985 + 0.010, 0, 1)

def beat_bounce(f): return 1.0

# ---------------------------------------------------------------------------- shots: rotated source (the wall run, turned vertical)
_RS0 = render_shot
def render_shot(s, f, with_shake=True, want_mask=False):
    if not s.get("rot"): return _RS0(s, f, with_shake, want_mask)
    img, t, u = source_img(s, f)
    r = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE).astype(np.float32) / 255          # 720 x 1280 -> head at the top
    z = keys_at(s.get("z", [(0, 1.0)]), u) * (1 + 0.05 * math.exp(-(f - s["f0"]) / 4.0))
    dx, dy, rot = shake(f) if with_shake else (0, 0, 0)
    sc = W / r.shape[1] * z
    M = cv2.getRotationMatrix2D((r.shape[1] / 2, r.shape[0] / 2), rot, sc)
    M[0, 2] += W / 2 - r.shape[1] / 2 + dx; M[1, 2] += H / 2 - r.shape[0] / 2 + dy
    out = cv2.warpAffine(grade(r, s, f), M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    out = np.clip(out, 0, 1)
    return (out, np.zeros((H, W), np.float32)) if want_mask else out

# ---------------------------------------------------------------------------- lightning
def glow_of(core, s1=3, s2=12, k1=2.4, k2=3.2):
    small = cv2.resize(core, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    return np.clip(cv2.resize(cv2.GaussianBlur(small, (0, 0), s1) * k1 + cv2.GaussianBlur(small, (0, 0), s2) * k2, (W, H)), 0, 1.6)

def bolt_light(out, core, glow, a=1.0, col=LGOLD):
    return np.clip(out + glow[..., None] * col * 0.85 * a + core[..., None] * LCORE * 1.1 * a, 0, 1)

def pulse(t, times, tau=0.12):
    e = 0.0
    for ta in times:
        if ta <= t < ta + 6 * tau: e = max(e, math.exp(-(t - ta) / tau))
    return e

CHOPS = E.CHOPS

def subject_arcs(out, person, f, s, amt):
    """lightning that hugs the silhouette: arcs crawl along the person matte's edge, with the odd leap off the body."""
    m8 = (cv2.resize(person, (W // 4, H // 4), interpolation=cv2.INTER_AREA) > 0.5).astype(np.uint8)
    cnts, _ = cv2.findContours(m8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not cnts: return out
    c = max(cnts, key=len)[:, 0, :].astype(np.float32) * 4 + 2
    if len(c) < 60: return out
    cen = c.mean(0); t = f / FPS
    e = pulse(t, CHOPS if t < E.T_DROP else E.ACCENTS, 0.10)
    rng = np.random.default_rng((f // 2) * 131 + len(s["n"]) * 7)
    core = np.zeros((H, W), np.uint8)
    n_arc = int(rng.integers(1, 3)) + (2 if e > 0.45 else 0)
    for a_ in range(n_arc):
        i0 = int(rng.integers(0, len(c))); span = int(rng.integers(len(c) // 14, len(c) // 6))
        idx = (i0 + np.arange(0, span, max(1, span // 12))) % len(c); seg = c[idx]
        nrm = seg - cen; nrm = nrm / (np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-3)
        seg = seg + nrm * rng.uniform(4, 16, (len(seg), 1)) + rng.normal(0, 7, seg.shape)
        pts = [seg[0]]
        for p, q in zip(seg, seg[1:]): pts += list(bolt_points(p, q, int(rng.integers(1e6)), 0.22, 3)[1:])
        cv2.polylines(core, [np.array(pts, np.int32)], False, 255, 2, cv2.LINE_AA)
    if rng.random() < 0.45 + 0.4 * e:                                                # a leap off the body
        p = c[int(rng.integers(0, len(c)))]; d = p - cen; d = d / (np.linalg.norm(d) + 1e-3)
        q = p + d * rng.uniform(90, 240) + rng.normal(0, 30, 2)
        cv2.polylines(core, [bolt_points(p, q, int(rng.integers(1e6)), 0.25, 5).astype(np.int32)], False, 230, 2, cv2.LINE_AA)
    cf = core.astype(np.float32) / 255
    return bolt_light(out, cf, glow_of(cf) * 0.75, amt * (0.55 + 0.45 * e))

def eyespark(out, f, s):
    """tiny arcs flicker off his eyes on the vocal chops (anchored to the YuNet eye landmarks)."""
    t = f / FPS; k = min([(t - c) * FPS for c in CHOPS if c <= t] or [99])
    if k > 5: return out
    fs = face_scr(s, f)
    if fs is None: return out
    rng = np.random.default_rng(f * 17); core = np.zeros((H, W), np.uint8)
    for (ex, ey), sg in ((fs[3], -1), (fs[4], 1)):
        for j in range(2):
            ang = math.radians(rng.uniform(-35, 35) + (180 if sg < 0 else 0)); L = rng.uniform(40, 95)
            q = (ex + L * math.cos(ang), ey + L * math.sin(ang))
            cv2.polylines(core, [bolt_points((ex, ey), q, int(rng.integers(1e6)), 0.3, 4).astype(np.int32)], False, 255, 1, cv2.LINE_AA)
    cf = core.astype(np.float32) / 255
    return bolt_light(out, cf, glow_of(cf, 2, 7, 2.0, 1.5), 0.9 * (1 - k / 6))

# ---------------------------------------------------------------------------- time-frozen motes (sparks hanging in the air)
_MT = {}
def motes(out, person, f, s):
    if "p" not in _MT:
        rng = np.random.default_rng(23); n = 110
        _MT["p"] = np.stack([rng.uniform(-60, W + 60, n), rng.uniform(-60, H + 60, n), rng.integers(0, 3, n), rng.uniform(0.4, 1.0, n), rng.uniform(0, 6.28, n)], 1)
    t = f / FPS; u = (f - s["f0"]) / max(1, s["f1"] - s["f0"])
    lay = [np.zeros((H // 2, W // 2), np.float32) for _ in range(3)]
    for x, y, zl, b, ph in _MT["p"]:
        zl = int(zl); par = (0.6, 1.0, 1.7)[zl]
        X = W / 2 + (x - W / 2) * (1 + 0.06 * u * par) + 8 * math.sin(0.3 * t + ph) * par   # barely drifting: time has stopped
        Y = H / 2 + (y - H / 2) * (1 + 0.06 * u * par) - 14 * t * par
        r = (1.6, 2.8, 7.0)[zl]; br = b * (0.75 + 0.25 * math.sin(2.1 * t + ph))
        cv2.circle(lay[zl], (int(X / 2), int(Y / 2)), max(1, int(r)), br, -1, cv2.LINE_AA)
    far = cv2.resize(cv2.GaussianBlur(lay[0], (0, 0), 0.8) + cv2.GaussianBlur(lay[0], (0, 0), 3) * 1.5, (W, H))
    mid = cv2.resize(cv2.GaussianBlur(lay[1], (0, 0), 1.0) + cv2.GaussianBlur(lay[1], (0, 0), 4) * 1.2, (W, H))
    near = cv2.resize(cv2.GaussianBlur(lay[2], (0, 0), 6) * 1.6, (W, H))                 # out-of-focus bokeh in front of him
    behind = (far * 1.1 + mid * 1.3) * (1 - person)
    return np.clip(out + behind[..., None] * (LGOLD * 0.8 + LCORE * 0.2) * 0.85 + near[..., None] * (LGOLD * 0.7 + LCORE * 0.3) * 0.55, 0, 1)

# ---------------------------------------------------------------------------- speed afterimages (isolated subject echoes)
def echoes(out, person, f, s):
    t = f / FPS; e = 0.6 + 0.4 * pulse(t, E.ACCENTS, 0.15); trail = s.get("trail", -1)
    acc = out.copy(); hold = person.copy()
    for i, (k, col) in enumerate(((3, LGOLD), (6, LEMB), (10, CRIM))):
        fk = max(s["f0"], f - k)
        if fk == f: continue
        img_k, m_k = _RS0(s, fk, False, True)
        M = np.float32([[1, 0, trail * (55 + 65 * i)], [0, 1, 0]])
        img_k = cv2.warpAffine(img_k, M, (W, H), borderMode=cv2.BORDER_REPLICATE); m_k = cv2.warpAffine(m_k, M, (W, H), borderValue=0)
        reg = np.clip(m_k - hold, 0, 1)[..., None] * (0.80 - 0.18 * i) * e
        Lk = lum(img_k)[..., None]
        acc = acc * (1 - reg) + np.clip(Lk * 0.35 + col * 0.85, 0, 1) * reg
        hold = np.maximum(hold, m_k * 0.8)
    return np.clip(acc, 0, 1)

# ---------------------------------------------------------------------------- the freeze on "power?" (time stops, colour drains, sparks lift)
def freeze_fx(out, person, f, s):
    t = f / FPS
    if t < E.T_FREEZE: return out
    v = smooth((t - E.T_FREEZE) / 0.12)
    L = lum(out)[..., None]
    cold = L * (STEEL * 0.55 + np.array([0.92, 0.92, 0.92], np.float32) * 0.45) * 1.05
    o = out * (1 - 0.85 * v) + cold * 0.85 * v
    o = o * person[..., None] + (o * (1 - 0.18 * v)) * (1 - person[..., None])      # he stays a touch brighter than the world
    return subject_arcs(o, person, f + 1000, s, 0.55 + 0.45 * v)

# ---------------------------------------------------------------------------- type
_TW2 = {}
def cap_word(w, size, emph):
    key = (w, size, emph)
    if key in _TW2: return _TW2[key]
    m = text_mask(w, F_CAP, size, tracking=1)
    pad = 40; mm = np.pad(m, pad); h2, w2 = mm.shape; rgba_ = np.zeros((h2, w2, 4), np.float32)
    for dxy, col in (((9, 7), CRIM), ((-6, 4), LGOLD)):                               # offset echoes: suit crimson + lightning gold
        sh = np.roll(np.roll(mm, dxy[1], 0), dxy[0], 1)
        rgba_[..., :3] = rgba_[..., :3] * (1 - sh[..., None]) + col * sh[..., None]; rgba_[..., 3] = np.maximum(rgba_[..., 3], sh * 0.85)
    if emph:
        y = np.linspace(0, 1, h2, dtype=np.float32)[:, None, None]
        fill = np.clip(LCORE * (1 - y) * 1.2 + LGOLD * y * 1.1 + LEMB * np.clip(y - 0.55, 0, 1) * 0.8, 0, 1)
    else:
        fill = np.broadcast_to(WHITE, (h2, w2, 3))
    rgba_[..., :3] = rgba_[..., :3] * (1 - mm[..., None]) + fill * mm[..., None]; rgba_[..., 3] = np.maximum(rgba_[..., 3], mm)
    sh = cv2.GaussianBlur(mm, (0, 0), 11) * 0.7                                       # soft dark backing: readable over lightning
    comb = np.zeros_like(rgba_); a1 = rgba_[..., 3:4]; comb[..., 3:4] = np.maximum(a1, sh[..., None])
    comb[..., :3] = rgba_[..., :3] * (a1 / np.maximum(comb[..., 3:4], 1e-4))
    _TW2[key] = comb; return comb

def captions(out, f):
    t = f / FPS
    for tx in E.TEXT:
        if tx["style"] != "cap": continue
        ws = tx["words"]
        if not (ws[0][1] - 0.05 <= t < tx["end"] + 0.02): continue
        frozen = t >= E.T_FREEZE
        for ln in (0, 1):
            row = [(w, wt) for w, wt, l in ws if l == ln]
            if not row: continue
            ims = [cap_word(w, 104, w in tx["emph"]) for w, _ in row]; sp = -54
            vs = [eout(((t - wt) * FPS + 1) / 11, 3) for _, wt in row]
            total = sum(im.shape[1] + sp for im in ims) - sp; fit = min(1.0, (W - 120) / total)
            x = W / 2 - total * fit / 2
            for im, v in zip(ims, vs):
                if v > 0.002:
                    sc = (1.12 - 0.12 * v) * fit; L_ = im
                    if v < 1: L_ = cv2.GaussianBlur(im, (0, 0), 0.1 + 6 * (1 - v))
                    if frozen:                                                         # time stops: the words go cold and still
                        L_ = L_.copy(); Lm = L_[..., :3].mean(2, keepdims=True); L_[..., :3] = L_[..., :3] * 0.55 + Lm * 0.45
                    out = put(out, L_, x + im.shape[1] * fit / 2, E.CAP_Y[ln] + 26 * (1 - v), v, sc, sc, 0)
                x += (im.shape[1] + sp) * fit
    return out

def put(out, rgba_, cx, cy, a, sx=1.0, sy=1.0, blur=0.0):
    im = rgba_
    if abs(sx - 1) > 0.01 or abs(sy - 1) > 0.01:
        im = cv2.resize(im, (max(2, int(im.shape[1] * sx)), max(2, int(im.shape[0] * sy))), interpolation=cv2.INTER_LINEAR)
    if blur > 0.3: im = cv2.GaussianBlur(im, (0, 0), blur)
    return paste(out, im, int(cx - im.shape[1] / 2), int(cy - im.shape[0] / 2), a)

_TT = {}
def title_word(w):
    if w in _TT: return _TT[w]
    m = text_mask(w, F_CAP, 300, tracking=-4)
    pad = 60; mm = np.pad(m, pad); h2, w2 = mm.shape; L_ = np.zeros((h2, w2, 4), np.float32)
    sh = np.roll(np.roll(mm, 16, 0), 12, 1)                                           # crimson depth shadow
    L_[..., :3] = CRIM * 0.9 * sh[..., None]; L_[..., 3] = sh * 0.95
    y = np.linspace(0, 1, h2, dtype=np.float32)[:, None, None]
    fill = np.clip(LCORE * (1.05 - 0.5 * y) + LGOLD * (0.25 + 0.75 * y) + LEMB * np.clip(y - 0.6, 0, 1) * 0.9, 0, 1)
    L_[..., :3] = L_[..., :3] * (1 - mm[..., None]) + fill * mm[..., None]; L_[..., 3] = np.maximum(L_[..., 3], mm)
    edge = np.clip(cv2.dilate(mm, np.ones((5, 5), np.uint8)) - mm, 0, 1)
    L_[..., :3] = L_[..., :3] * (1 - edge[..., None]) + LGOLD * edge[..., None]
    gl = cv2.GaussianBlur(mm, (0, 0), 18) * 0.85
    L_[..., :3] = L_[..., :3] + (gl * (1 - L_[..., 3]))[..., None] * LGOLD; L_[..., 3] = np.maximum(L_[..., 3], gl * 0.75)
    _TT[w] = (L_, mm); return _TT[w]

def letter_arcs(mm, f, seed, amt):
    """lightning crawling along the letter outlines (title-canvas coords)."""
    cnts, _ = cv2.findContours((mm > 0.5).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    core = np.zeros(mm.shape, np.uint8); rng = np.random.default_rng(f // 2 * 29 + seed)
    for c in sorted(cnts, key=len, reverse=True)[:6]:
        c = c[:, 0, :].astype(np.float32)
        if len(c) < 40 or rng.random() > 0.65: continue
        i0 = int(rng.integers(0, len(c))); span = int(rng.integers(len(c) // 8, len(c) // 3))
        seg = c[(i0 + np.arange(0, span, max(1, span // 10))) % len(c)] + rng.normal(0, 5, (len(range(0, span, max(1, span // 10))), 2))
        pts = [seg[0]]
        for p, q in zip(seg, seg[1:]): pts += list(bolt_points(p, q, int(rng.integers(1e6)), 0.25, 3)[1:])
        cv2.polylines(core, [np.array(pts, np.int32)], False, 255, 2, cv2.LINE_AA)
    cf = core.astype(np.float32) / 255
    gl = cv2.GaussianBlur(cf, (0, 0), 3) * 2.2 + cv2.GaussianBlur(cf, (0, 0), 10) * 2.0
    return cf * amt, np.clip(gl, 0, 1.5) * amt

def title(out, person, f, s):
    t = f / FPS; tx = [x for x in E.TEXT if x["style"] == "title"][0]
    if t < tx["words"][0][1] - 0.02 or t > tx["end"] + 0.15: return out
    ys = (1290, 1540); bump = pulse(t, E.ACCENTS, 0.09); kx = (t - tx["end"]) * FPS
    lay = np.zeros((H, W, 3), np.float32); al = np.zeros((H, W), np.float32)
    for i, (w, wt, _) in enumerate(tx["words"]):
        k = (t - wt) * FPS
        if k < -0.5: continue
        L_, mm = title_word(w)
        if k < 7: v = eout((k + 1) / 8, 3); sc = 1.9 - 0.9 * v; bl = 8 * (1 - v); a = clamp((k + 1) / 3, 0, 1)
        else: kk = k - 7; sc = 1 + 0.05 * math.exp(-kk / 3) * math.cos(kk * 1.4) + 0.035 * bump; bl = 0; a = 1.0
        cf, gl = letter_arcs(mm, f, 11 * i, 0.9 if k > 3 else 0.0)
        Lw = L_.copy(); Lw[..., :3] = np.clip(Lw[..., :3] + gl[..., None] * LGOLD + cf[..., None] * LCORE, 0, 1)
        Lw[..., 3] = np.maximum(Lw[..., 3], np.clip(gl, 0, 1) * 0.8)
        dx = 0.0
        if kx > 0:                                                                      # exit: the word streaks off at speed
            Lw = cv2.blur(Lw, (int(1 + kx * 9), 1)); dx = 22 * kx ** 1.5; a *= clamp(1 - kx / 9, 0, 1)
        im = cv2.resize(Lw, (int(Lw.shape[1] * sc), int(Lw.shape[0] * sc)))
        if bl > 0.3: im = cv2.GaussianBlur(im, (0, 0), bl)
        x0, y0 = int(W / 2 + dx - im.shape[1] / 2), int(ys[i] - im.shape[0] / 2)
        xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + im.shape[1]), min(H, y0 + im.shape[0])
        if xb <= xa or yb <= ya: continue
        sub = im[ya - y0:yb - y0, xa - x0:xb - x0]; aa = sub[..., 3] * a
        lay[ya:yb, xa:xb] = lay[ya:yb, xa:xb] * (1 - aa[..., None]) + sub[..., :3] * aa[..., None]
        al[ya:yb, xa:xb] = np.maximum(al[ya:yb, xa:xb], aa)
    return np.clip(out * (1 - al[..., None]) + lay * al[..., None], 0, 1)

# ---------------------------------------------------------------------------- transitions
_BL = {}
def bolt_line(key, p0, p_top, p_bot, seed):
    if key not in _BL:
        a = bolt_points(p_top, p0, seed, 0.20, 7); b = bolt_points(p0, p_bot, seed + 1, 0.20, 7)
        pts = np.vstack([a, b[1:]]); poly = np.vstack([pts, [[-300, H + 60], [-300, -60]]]).astype(np.int32)
        left = np.zeros((H, W), np.uint8); cv2.fillPoly(left, [poly], 255)
        i0 = len(a) - 1
        _BL[key] = (pts, i0, cv2.GaussianBlur(left.astype(np.float32) / 255, (0, 0), 1.2))
    return _BL[key]

def bolt_link(A, B, j, f, sa, sb, n0=8, n1=9):
    """a bolt jumps out of his eye and splits the frame open along itself onto the next shot."""
    fs = face_scr(sa, sa["f1"] - 1); p0 = (fs[3] if fs else (W * 0.5, H * 0.36))
    pts, i0, left = bolt_line(("bl", sa["n"]), p0, (p0[0] + 90, -60), (p0[0] - 160, H + 60), 31)
    if j < 0:
        u = (j + n0) / n0; nn = int(len(pts) * 0.5 * eout(u, 1.5))
        seg = pts[max(0, i0 - nn):min(len(pts), i0 + nn + 1)]
        core = np.zeros((H, W), np.uint8); cv2.polylines(core, [seg.astype(np.int32)], False, 255, 3, cv2.LINE_AA)
        cf = core.astype(np.float32) / 255
        eye = np.exp(-((_GX - p0[0]) ** 2 + (_GY - p0[1]) ** 2) / (2 * (30 + 40 * u) ** 2))
        return bolt_light(A * (1 - 0.12 * u) + eye[..., None] * LGOLD * 0.8 * u, cf, glow_of(cf), 0.6 + 0.4 * u)
    u = eout((j + 1) / n1, 2.0); sep = 60 + 980 * u
    o = zoom_about(B, W / 2, H * 0.42, 1.12 - 0.12 * u)
    core = np.zeros((H, W), np.uint8); cv2.polylines(core, [pts.astype(np.int32)], False, 255, 3, cv2.LINE_AA)
    cf = core.astype(np.float32) / 255; gl = glow_of(cf)
    for side, m in ((-1, left), (1, 1 - left)):
        M = np.float32([[1, 0, side * sep], [0, 1, side * sep * 0.08]])
        Ah = cv2.warpAffine(A, M, (W, H), borderMode=cv2.BORDER_REPLICATE); mh = cv2.warpAffine(m, M, (W, H), borderValue=0)[..., None]
        mh = mh * (1 - 0.6 * u)                                                         # the halves fade as they fly apart
        o = o * (1 - mh) + Ah * (1 - 0.4 * u) * mh
        o = o + cv2.warpAffine(gl, M, (W, H))[..., None] * LGOLD * 0.9 * (1 - u)
    return np.clip(o, 0, 1)

def overcharge(A, B, j, f, sa, sb, n0=10, n1=12):
    """his own lightning overloads the frame; the next shot burns in brightest-first."""
    if j < 0:
        u = (j + n0) / n0; L = lum(A); hi = np.clip((L - 0.55) / 0.45, 0, 1)
        bl = cv2.resize(cv2.GaussianBlur(cv2.resize(hi, (W // 4, H // 4)), (0, 0), 6 + 10 * u), (W, H))
        o = A * (1 + 0.35 * u) + (hi * 0.8 + bl * 1.6)[..., None] * LGOLD * u * 1.0 + (u ** 4) * 0.30 * LGOLD
        return np.clip(o, 0, 1)
    u = (j + 1) / n1; Lm = cv2.GaussianBlur(lum(B), (0, 0), 3); T = 0.45 - 0.55 * eout(u, 2)
    m = np.clip((Lm - T) / 0.06, 0, 1)[..., None]; edge = np.exp(-((Lm - T) / 0.025) ** 2)[..., None]
    white = (LGOLD * 0.55 + LCORE * 0.25) * (1 - 0.6 * u)                                  # gold, never a flat white frame
    return np.clip(B * m + white * (1 - m) + edge * LGOLD * 1.1 * (1 - u), 0, 1)

def whip_bolt(A, B, j, f, sa, sb, n0=6, n1=8):
    u = clamp((j + n0) / (n0 + n1), 0, 1); p = W * (smooth(u) ** 1.3)
    vel = W / (n0 + n1) * 2.4 * math.sin(math.pi * u)
    o = np.zeros_like(A); ip = int(round(p))
    if ip < W: o[:, :W - ip] = A[:, ip:]
    if ip > 0: o[:, W - ip:] = B[:, :ip]
    o = rgb_split(hblur(o, min(260, vel * 1.1)), vel * 0.035)
    y0 = H * 0.46 + 60 * math.sin(f * 0.7)                                              # a bolt rides the whip
    pts = bolt_points((-40, y0), (W + 40, y0 - 120), 40 + j, 0.10, 7)
    core = np.zeros((H, W), np.uint8); cv2.polylines(core, [pts.astype(np.int32)], False, 255, 2, cv2.LINE_AA)
    cf = hblur(core.astype(np.float32) / 255, 30)
    return bolt_light(o, cf, glow_of(cf), 0.9 * math.sin(math.pi * u))

def strike(A, B, j, f, sa, sb, n0=6, n1=18):
    """HERO: time is frozen; a bolt strikes down through him; two impact frames; the drop explodes in."""
    fs = face_scr(sa, sa["f1"] - 1); px = fs[0] if fs else W * 0.5; py = fs[1] if fs else H * 0.37
    key = ("strike",)
    if key not in _BL:
        pts = np.vstack([bolt_points((px + 120, -80), (px, py), 77, 0.16, 7), bolt_points((px, py), (px - 60, H + 80), 78, 0.16, 7)[1:]])
        core = np.zeros((H, W), np.uint8); cv2.polylines(core, [pts.astype(np.int32)], False, 255, 6, cv2.LINE_AA)
        for b in range(5):
            i = len(pts) // 8 + b * len(pts) // 7; q = pts[i] + np.array([(-1) ** b * 260, 180], np.float32)
            cv2.polylines(core, [bolt_points(pts[i], q, 80 + b, 0.25, 5).astype(np.int32)], False, 180, 3, cv2.LINE_AA)
        cf = core.astype(np.float32) / 255; _BL[key] = (pts, cf, glow_of(cf, 4, 18, 3.0, 4.0))
    pts, cf, gl = _BL[key]
    if j < 0:                                                                           # the leader comes down
        u = (j + n0) / n0; lead = pts[:max(2, int(len(pts) * 0.55 * eout(u, 1.4)))]
        core = np.zeros((H, W), np.uint8); cv2.polylines(core, [lead.astype(np.int32)], False, 255, 3, cv2.LINE_AA)
        c2 = core.astype(np.float32) / 255
        return bolt_light(A * (1 - 0.2 * u), c2, glow_of(c2), 0.7 + 0.3 * u)
    L = lum(B)
    if j == 0:                                                                          # impact frame 1: negative in gold
        o = (np.clip(1 - L, 0, 1) ** 2.2)[..., None] * (LCORE * 0.55 + LGOLD * 0.6)
        return np.clip(o + cf[..., None] * 0.4, 0, 1)
    if j == 1:                                                                          # impact frame 2: hard silhouette
        o = np.where((L > 0.42)[..., None], LCORE * 0.95, CRIM * 0.22)
        return np.clip(o * (1 - cf[..., None]) + cf[..., None] * 0.1, 0, 1)
    u = (j - 1) / (n1 - 1)
    R = 1900 * eout(u, 2.0); dx, dy = _GX - px, _GY - py; r = np.sqrt(dx * dx + dy * dy) + 1e-3
    disp = np.exp(-((r - R) / 70.0) ** 2) * 50 * (1 - u)
    o = cv2.remap(B, (_GX - dx / r * disp).astype(np.float32), (_GY - dy / r * disp).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    o = o + (1 - u) ** 2.5 * 0.55 * LCORE
    return bolt_light(o, cf * (1 - u) ** 2, gl * (1 - u) ** 1.5, 1.0)

def emblem_tr(A, B, j, f, sa, sb, n0=12, n1=22):
    """the Flash emblem slams over the frame and draws itself in lightning; the camera flies through the bolt."""
    EA = emblem_assets()
    if j < 0:
        k = j + n0; v = eout(k / 4, 3); sc = 1.35 - 0.35 * v
        core, glow = stroke_light([EA["ring"], EA["bolt"]], eout(k / 8, 1.6))
        M = cv2.getRotationMatrix2D(EMB_C, 0, sc)
        core = cv2.warpAffine(core, M, (W, H)); glow = cv2.warpAffine(glow, M, (W, H))
        o = A * (1 - 0.55 * v) + glow[..., None] * LGOLD * v + core[..., None] * LCORE * v
        if k >= 8: o = o + cv2.warpAffine(EA["fill"], M, (W, H))[..., None] * (0.35 + 0.15 * (k - 8)) * (LCORE * 0.6 + LGOLD * 0.4)
        if k >= 4: o = arcs_around(o, f, EA, 0.7)
        return np.clip(o, 0, 1)
    u = (j + 1) / n1; sc = math.exp(4.6 * ein(u, 2.0)); bc = EA["poly"].mean(0)
    M = cv2.getRotationMatrix2D((float(bc[0]), float(bc[1])), -10 * u, sc)
    m = cv2.warpAffine(EA["fill"], M, (W, H), flags=cv2.INTER_LINEAR)
    if sc > 10: m = np.maximum(m, clamp((sc - 10) / 20, 0, 1))
    rc, rg = stroke_light([EA["ring"]], 1.0); rg = cv2.warpAffine(rg, M, (W, H)); rc = cv2.warpAffine(rc, M, (W, H))
    Bz = zoom_about(B, W / 2, H * 0.45, 1.25 - 0.25 * eout(u, 2))
    edge = np.clip(cv2.morphologyEx(m, cv2.MORPH_GRADIENT, np.ones((5, 5), np.uint8)), 0, 1)
    o = Bz * m[..., None] + (A * 0.45 + rg[..., None] * LGOLD + rc[..., None]) * (1 - u) * (1 - m[..., None])
    o = o + cv2.GaussianBlur(edge, (0, 0), 6)[..., None] * LGOLD * 1.5 * (1 - u)
    if j < 4: o = o + m[..., None] * (4 - j) * 0.18 * (LCORE * 0.6 + LGOLD * 0.4)
    return np.clip(o, 0, 1)

def remnant_tr(A, B, j, f, sa, sb):
    return remnant_soft(B, f, sb, j)

def passby(A, B, j, f, sa, sb, n0=6, n1=8):
    """he passes the lens: his own motion smears the frame off to the left; the next shot drags in from the right."""
    if j < 0:
        u = (j + n0) / n0; o = np.roll(hblur(A, 10 + 260 * u ** 1.5), -int(180 * u ** 2), axis=1)
        return np.clip(o * (1 - 0.25 * u) + CRIM * 0.25 * u, 0, 1)
    v = eout((j + 1) / n1, 2.0)
    o = np.roll(hblur(B, 10 + 260 * (1 - v) ** 1.5), int(240 * (1 - v) ** 2), axis=1)
    return np.clip(o + (1 - v) * CRIM * 0.18, 0, 1)

def bolt_split_tr(A, B, j, f, sa, sb):
    return bolt_split(A, B, j, 19)

def streaks(f, amt, seed=9):
    rng = np.random.default_rng(f * 5 + seed); lay = np.zeros((H, W), np.float32)
    for _ in range(int(4 + 16 * amt)):
        y = rng.uniform(60, H - 60); x0 = rng.uniform(-300, W); L = rng.uniform(300, 1100)
        cv2.line(lay, (int(x0), int(y)), (int(x0 + L), int(y)), float(rng.uniform(0.4, 1.0)), int(rng.integers(2, 6)), cv2.LINE_AA)
    return cv2.GaussianBlur(lay, (0, 0), 1.6) + cv2.resize(cv2.GaussianBlur(cv2.resize(lay, (W // 4, H // 4)), (0, 0), 5), (W, H)) * 1.4

def smear_tr(A, B, j, f, sa, sb, n0=5, n1=8):
    """the frame stretches into horizontal light streaks at speed and the next shot resolves out of them."""
    a = ein((j + n0 + 1) / (n0 + 1), 1.6) if j < 0 else 1 - eout((j + 1) / n1, 2.0)
    src = A if j < 0 else B
    o = hblur(src, 6 + 420 * a) * (1 - 0.15 * a)
    return np.clip(o + streaks(f, a)[..., None] * (LGOLD * 0.8 + LCORE * 0.2) * a, 0, 1)

def impact_tr(A, B, j, f, sa, sb):
    L = lum(B)
    if j == 0: return np.clip((np.clip(1 - L, 0, 1) ** 2)[..., None] * (LCORE * 0.5 + LGOLD * 0.65), 0, 1)
    if j == 1: return np.clip(np.where((L > 0.40)[..., None], LCORE * 0.95, LEMB * 0.18), 0, 1)
    return np.clip(B * (1 + 0.5 * math.exp(-(j - 2) / 1.2)), 0, 1)

def shockwave_tr(A, B, j, f, sa, sb):
    return shockwave(A, B, sa, f, j)

def rewind_in(A, B, j, f, sa, sb, n1=12):
    """the loop entry: the rewind decelerates onto the first frame."""
    v = eout(max(0, j - 1) / n1, 2.0)                                                    # flat for 2 frames: the rewind lands on frame ~1
    o = rgb_split(hblur(B, 4 + 24 * (1 - v)), 4 * (1 - v))
    return np.clip(o + (1 - v) ** 2 * 0.45 * (LCORE * 0.6 + LGOLD * 0.4), 0, 1)

def remnant_soft(B, f, s, k, n=14):
    """the shot arrives as converging time-remnants (gold / crimson), weighted so a bright shot doesn't blow out."""
    if k >= n: return B
    v = eout(k / n, 2.4); acc = B * (0.55 + 0.45 * v)
    cols = (LGOLD, CRIM, LEMB, CRIM)
    for j in range(4):
        d = (1 - v) * (j + 1) * 200 * (1 if j % 2 else -1)
        sh = cv2.warpAffine(B, np.float32([[1, 0, d], [0, 1, 0]]), (W, H), borderMode=cv2.BORDER_REFLECT)
        acc = acc + lum(sh)[..., None] * cols[j] * 0.42 * (1 - v) / (1 + 0.5 * j)
    return np.clip(acc / (1 + 0.35 * (1 - v)), 0, 1)

TR2.update({"rewind_in": (rewind_in, 0, 12), "bolt_link": (bolt_link, 8, 9), "overcharge": (overcharge, 10, 12), "whip": (whip_bolt, 6, 8),
            "strike": (strike, 6, 18), "emblem": (emblem_tr, 12, 22), "remnant": (remnant_tr, 0, 14), "passby": (passby, 6, 8),
            "bolt_split": (bolt_split_tr, 5, 12), "smear": (smear_tr, 5, 8), "impact": (impact_tr, 0, 5), "shockwave": (shockwave_tr, 0, 13)})

# ---------------------------------------------------------------------------- finish
_FGR = None
def fgrain(f):
    global _FGR
    if _FGR is None:
        rng = np.random.default_rng(7)
        _FGR = [cv2.resize(rng.standard_normal((H // 2, W // 2)).astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR) for _ in range(6)]
    return _FGR[f % 6][..., None]

def finish_storm(out, f, fast=False):
    out = out + 0.25 * (out - cv2.GaussianBlur(out, (0, 0), 1.5))                      # gentle unsharp for the 720p upscale
    L = lum(out); hi = np.clip(L - 0.70, 0, 1)
    halo = cv2.resize(cv2.GaussianBlur(cv2.resize(hi, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 8), (W, H))[..., None]
    out = out + halo * (LGOLD * 0.30 + LCORE * 0.10)
    out = anamorphic(out, 0.20)
    out = edge_ca(out, 3.5 if fast else 1.6)
    L = lum(out)[..., None]
    out = out + fgrain(f) * (0.010 + 0.016 * L * (1 - L) * 2.5)
    return np.clip(out * VIG, 0, 1)

# ---------------------------------------------------------------------------- frame
def last_visible(P):
    fr = P["f1"] - 1
    if P.get("seg"):
        o, person = render_shot(P, fr, want_mask=True); return shot_fx(o, person, fr, P)
    return render_shot(P, fr)

def shot_fx(out, person, f, s):
    if s.get("motes"): out = motes(out, person, f, s)
    if s.get("echoes"): out = echoes(out, person, f, s)
    if s.get("sarcs"): out = subject_arcs(out, person, f, s, s["sarcs"])
    if s.get("title"): out = title(out, person * 0, f, s)
    if s.get("freeze"): out = freeze_fx(out, person, f, s)
    return out

def render_core(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin")
    if s.get("seg"):
        out, person = render_shot(s, f, want_mask=True); out = shot_fx(out, person, f, s)
    else:
        out = render_shot(s, f)
        if s.get("title"): out = title(out, np.zeros((H, W), np.float32), f, s)
    if s.get("eyespark"): out = eyespark(out, f, s)
    out = captions(out, f)
    if tin in TR2 and k < TR2[tin][2]: out = TR2[tin][0](last_visible(P) if P else out * 0, out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, render_shot(n_, n_["f0"], False), kn, f, s, n_)
    return np.clip(out, 0, 1)

# ---- the ending: he runs back in time. the whole edit rewinds (35x at its peak) and lands on frame 0 = the loop
REW_F0 = E.fe(E.T_REW)
_S = np.linspace(0, 1, 4001); _C = np.concatenate([[0], np.cumsum(np.sin(np.pi * (_S[1:] + _S[:-1]) / 2) ** 1.5 * np.diff(_S))])
REW_A = ((E.T_REW / (E.DUR - E.T_REW)) - 1) / _C[-1]
def rew_pos(t):
    """edit time shown at output time t inside the rewind (T_REW -> 0); rate -1 at both ends, ~-35 in the middle."""
    s_ = clamp((t - E.T_REW) / (E.DUR - E.T_REW), 0, 1)
    return max(0.0, E.T_REW - (E.DUR - E.T_REW) * (s_ + REW_A * float(np.interp(s_, _S, _C))))

def rewind_frame(f):
    t = f / FPS; p = rew_pos(t); rate = abs(rew_pos(t + 0.5 / FPS) - rew_pos(t - 0.5 / FPS)) * FPS
    pa = clamp(p, 0, E.T_REW - 1 / FPS); pb = clamp(p + min(0.08, rate / FPS * 0.35), 0, E.T_REW - 1 / FPS)
    o = render_core(int(round(pa * FPS)))
    if rate > 3: o = o * 0.62 + render_core(int(round(pb * FPS))) * 0.38                 # two crisp frames, not a blur of ten
    s_ = (t - E.T_REW) / (E.DUR - E.T_REW); sp = clamp((rate - 1) / 30, 0, 1)
    o = rgb_split(hblur(o, 4 + 70 * sp), 10 * sp)
    o = zoom_about(o, W / 2, H * 0.44, 1.0 + 0.05 * sp)
    rng = np.random.default_rng(f * 7 + 3); lay = np.zeros((H, W), np.float32)
    for _ in range(int(10 * sp)):                                                      # speed-force streaks racing backwards
        y = rng.uniform(80, H - 80); x0 = rng.uniform(-200, W); L = rng.uniform(260, 900)
        cv2.line(lay, (int(x0), int(y)), (int(x0 + L), int(y + rng.uniform(-14, 14))), float(rng.uniform(0.5, 1.0)), int(rng.integers(2, 5)), cv2.LINE_AA)
    lay = cv2.GaussianBlur(lay, (0, 0), 2.0) + cv2.resize(cv2.GaussianBlur(cv2.resize(lay, (W // 4, H // 4)), (0, 0), 5), (W, H)) * 1.5
    o = o + lay[..., None] * (LGOLD * 0.75 + LCORE * 0.25) * sp                        # (the seam flash comes from frame 0's own rewind_in)
    return np.clip(o, 0, 1)

FAST = {"approach", "wallrun", "charged", "final_run", "darkbolt"}
def render(f):
    if f >= REW_F0: out = rewind_frame(f); fast = True
    else: out = render_core(f); fast = shot_at(f)["n"] in FAST
    return (np.clip(finish_storm(out, f, fast), 0, 1) * 255 + 0.5).astype(np.uint8)

def init_hits():
    HITS.clear()
    HITS.append((E.fh(E.HDROP), 22, 4.0))                                               # the strike
    HITS.append((E.fh(772), 12, 3.0))                                                    # GO
    HITS.append((E.fh(824), 14, 3.0))                                                    # impact frame into the eyes
    HITS.append((E.fh(832), 10, 3.5))                                                    # shockwave
