# ============================================================================ v111 — MONSTER — Dexter × Monster: toolkit from the v110 standard (restyle it)
# The edit's own section (above the pipeline v2 speed section). Last definition wins.
#   LOOK      TABLOID: newsprint cream highlights, ink blacks, slate blues, one spot red; a misregistered red plate,
#             paper grain and a fine screen in the shadows (finish107).
#   PRINT     halftone(): the press screen. The press flash prints the next shot as a newspaper photo; the front page's
#             photo is the next shot, and the dive resolves its dots into the footage.
#   molasses  "flows of hot molasses": a viscous sheet of blood pours down the lens (fingering front, a bead on its
#             edge, refraction, absorption, a glossy highlight), the next shot is under it, it drains with streaks.
#   headspin  "to headspin": the frame spins two turns about its centre (motion-blurred) onto the upside-down shot.
#   frontpage "took a few minutes to convince": the front page spins in (BAY HARBOR / BUTCHER), lands, and we dive into
#             its photo of him (the next shot).
#   stamp     "when you spell the man name": a strip of newsprint slaps on; D-E-X-T-E-R is stamped one letter per sung
#             word; the strip flies into the sky onto the real banner the plane tows (WE <3 DEXTER).
#   confetti  procedural paper confetti (lit, fluttering, depth of field): the pop into the parade and the loop
#             (it thickens over the lens on the bass drop-out bar and clears on frame 0).
INK = np.array([0.045, 0.040, 0.040], np.float32)       # BGR ink black
PAPER = np.array([0.84, 0.92, 0.96], np.float32)        # BGR newsprint cream
SPOT = np.array([0.13, 0.12, 0.80], np.float32)         # BGR spot red
SLATE = np.array([0.50, 0.42, 0.34], np.float32)        # BGR slate blue
BLOODC = np.array([0.03, 0.02, 0.30], np.float32)       # BGR deep blood body
EMPH = np.array([0.16, 0.16, 0.92], np.float32)         # caption emphasis: the spot red (cap_word reads EMPH)

# ---- the grade: TABLOID -------------------------------------------------------------------------------------------
_LUTT = {}
def lutt():
    if "t" not in _LUTT:
        x = np.linspace(0, 1, 1024, dtype=np.float32)
        _LUTT["t"] = (x, PchipInterpolator([0, .05, .18, .50, .80, .94, 1], [0.030, 0.040, 0.135, 0.47, 0.80, 0.915, 0.94])(x).astype(np.float32))
    return _LUTT["t"]

_grade_pre107 = grade
def grade(img, s, f):
    if s.get("look") != "tabloid": return _grade_pre107(img, s, f)
    g, gains = corr9(s); ev = s.get("ev") or 0; lx, ly = lutt()
    if in_unit(img):
        x = apply_lut3(img, tone_lut(("tab107", s["n"], ev, float(g), tuple(float(v) for v in gains)), gains, g, ev, lx, ly))
    else:
        x = np.interp(np.clip(np.clip(img * gains, 0, 1) ** g * 2 ** ev, 0, 1), lx, ly).astype(np.float32)
    Bc, Gc, Rc = (np.ascontiguousarray(x[..., c]) for c in range(3))
    L = Bc * 0.114 + Gc * 0.587 + Rc * 0.299
    red = np.clip((Rc - np.maximum(Gc, Bc) - s.get("redthr", 0.12)) * 3.2, 0, 1)          # strong reds survive as the spot colour
    skin = np.clip((Rc - Bc) * 2.2, 0, 1) * (1 - red)
    sat = 0.30 + 0.20 * skin + 0.85 * red
    hi = np.clip((L - 0.45) * 1.8, 0, 1)
    o = np.empty(x.shape, np.float32)
    for ch, P in enumerate((Bc, Gc, Rc)):
        v = L + (P - L) * sat
        v *= 1 + hi * (PAPER[ch] / 0.96 - 1) * 0.9                                         # paper cream in the light
        v += (1 - L) ** 3 * (0.012 if ch == 0 else 0.0)                                    # ink, a hair cool in the deepest black
        v += red * L * (SPOT[ch] / 0.80 - 1) * 0.25                                        # reds lean to the printing red
        o[..., ch] = v
    return np.clip(o, 0, 1, out=o)

# ---- the print: halftone screen ------------------------------------------------------------------------------------
_HT = {}
def ht_grid(pitch, ang):
    key = (round(pitch, 2), ang)
    if key not in _HT:
        if len(_HT) > 10: _HT.clear()
        a = math.radians(ang); p = key[0]                                                 # from the rounded key: order-independent (partial renders verify)
        u = (_GX * math.cos(a) + _GY * math.sin(a)) / p; v = (-_GX * math.sin(a) + _GY * math.cos(a)) / p
        du, dv = u - np.round(u), v - np.round(v); _HT[key] = np.sqrt(du * du + dv * dv).astype(np.float32)
    return _HT[key]

def halftone(img, pitch=9.0, ang=45, red_plate=True):
    """the image as a newspaper print: ink dots on newsprint (size by darkness, sampled per cell), reds on their own
    screen at 75 degrees."""
    r = ht_grid(pitch, ang); sm = cv2.GaussianBlur(img, (0, 0), pitch * 0.45)
    Lb = lum(sm); d = np.clip((1 - Lb) * 1.08 - 0.04, 0, 1)
    R = np.sqrt(d / math.pi) * 1.02; aa = 1.2 / pitch
    dot = np.clip((R - r) / aa + 0.5, 0, 1)
    o = PAPER * (1 - dot[..., None]) + INK * dot[..., None]
    if red_plate:
        red = np.clip((sm[..., 2] - np.maximum(sm[..., 0], sm[..., 1]) - 0.05) * 2.5, 0, 1)
        r2 = ht_grid(pitch, 75); dr = np.clip((np.sqrt(red / math.pi) * 1.02 - r2) / aa + 0.5, 0, 1) * (1 - dot)
        o = o * (1 - dr[..., None]) + SPOT * dr[..., None]
    return o.astype(np.float32)

# ---- the finish: misregistered red plate, paper grain, a fine screen in the shadows, vignette ------------------------
_PAPERTEX = {}
def paper_tex():
    if "p" not in _PAPERTEX:
        rng = np.random.default_rng(1070)
        fib = cv2.GaussianBlur(rng.standard_normal((H, W)).astype(np.float32), (0, 0), 0.8)
        fib = fib + cv2.resize(cv2.GaussianBlur(rng.standard_normal((H // 6, W // 6)).astype(np.float32), (0, 0), 1.2), (W, H)) * 0.8
        fib = cv2.GaussianBlur(fib, (0, 0), sigmaX=2.2, sigmaY=0.6)                        # fibres run one way
        _PAPERTEX["p"] = (fib / (np.abs(fib).max() + 1e-6)).astype(np.float32)
    return _PAPERTEX["p"]

def finish107(out, f, s=None):
    Bc, Gc, Rc = out[..., 0], out[..., 1], out[..., 2]
    red = np.clip((Rc - np.maximum(Gc, Bc) - 0.06) * 2.0, 0, 1)
    ghost = np.roll(np.roll(red, 3, 1), 2, 0) * (1 - red) * 0.22                           # the red plate sits a few px off
    L = lum(out); scr = ht_grid(6.0, 45)
    dots = np.clip(1 - scr * 2.4, 0, 1) * np.clip((0.55 - L) * 1.6, 0, 1) * 0.07           # a fine screen in the shadows only
    pt = paper_tex(); g = grain(f, 0.011)[..., 0]; v = VIG[..., 0]
    o = np.empty(out.shape, np.float32)
    for ch in range(3):
        oc = o[..., ch]; np.copyto(oc, out[..., ch])
        oc += ghost * (SPOT[ch] - 0.55) * 0.6
        oc *= (1 - dots); oc *= (1 + pt * 0.022); oc *= v; oc += g
    return np.clip(o, 0, 1, out=o)

# ---- the beat camera: from e2 (frame 0 clean) to the loop; it rests through the spins, the front page and the match ---
def beat_phase(f):
    e = f / FPS / E.HB; ph = (e % 2) * E.HB; bi = int(e // 2)
    hook = (E.E_BEAT <= e < E.E_LOOP - 1) and not (19 <= e < 23) and not (24 <= e < 28.5) and not (47 <= e < 50)
    return ph, bi, hook, False

# ---- smooth motion: where flow is refused (big frame-to-frame change), blend the two frames instead of holding one ----
def src_weights(s, f):
    """as the engine's, but a flow shot whose neighbours differ too much for clean flow blends them (motion-blur-like at
    60 fps) instead of holding one (24p judder). check_sources keeps every range inside one source shot."""
    pk = s["src"]; fps = E.SRC[pk][1]; U = UNIQ[pk]
    t, u, sp = src_time(s, f)
    def idx(tt, mode):
        kf = tt * fps; i = clamp(bisect.bisect_right(U, kf + 0.3) - 1, 0, len(U) - 1)
        if mode == "hold" or i >= len(U) - 1: return [(U[i], 1.0)]
        i0, i1 = U[i], U[i + 1]; a = clamp((kf - i0) / (i1 - i0), 0.0, 1.0)
        if a < 0.05: return [(i0, 1.0)]
        if a > 0.95: return [(i1, 1.0)]
        if mode == "blend": return [(i0, 1 - a), (i1, a)]
        A0, A1 = FR[(pk, i0)], FR[(pk, i1)]
        if np.abs(A0[::8, ::8].astype(np.float32) - A1[::8, ::8]).mean() > 14: return [(i0, 1 - a), (i1, a)]
        m0, m1 = A0[::8, ::8].mean(axis=(0, 1)), A1[::8, ::8].mean(axis=(0, 1))
        if np.abs(m0.astype(np.float32) - m1).max() > 6: return [(i0, 1 - a), (i1, a)]
        return [("flow", i0, i1, a)]
    if sp > 1.7:
        K = int(min(7, max(3, round(sp * 2)))); span = 0.5 / FPS * sp; out_ = []
        for j in range(K):
            out_ += [(k, w / K) for k, w in idx(t + (j / (K - 1) - 0.5) * span, "hold")]
        return out_, t, u
    return idx(t, s.get("interp", "hold")), t, u

# ---- base frame ---------------------------------------------------------------------------------------------------
def banner_geom(t):
    """the banner shot: the source cropped round the banner (tracked as it drifts left and up), scaled 1.2x so the whole
    banner fits the width; the sky is extended above and below."""
    x0 = 260.0 - 86.7 * (t - 326.05); y0 = -20.0 * (t - 326.05)
    return x0, y0, 1.2, 545.0

def banner_frame(s, f):
    t, u, _ = src_time(s, f); fr = sample(s["src"], t)
    img = fr.astype(np.float32) / 255 if fr.dtype != np.float32 else fr
    x0, y0, sc, yoff = banner_geom(t)
    M = np.float32([[sc, 0, -x0 * sc], [0, sc, yoff - y0 * sc]])
    o = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)
    top, bot = img[4:60].reshape(-1, 3).mean(0), img[-60:-4].reshape(-1, 3).mean(0)          # extend the sky: its own top/bottom colour
    yy = (_GY[:, :1] - yoff) / (720 * sc)
    sky = np.where(yy < 0, top + (top - bot) * np.clip(-yy, 0, 1) * 0.15, bot - (top - bot) * np.clip(yy - 1, 0, 1) * 0.15).astype(np.float32)
    out_m = np.clip(np.maximum(-yy * 720 * sc, (yy - 1) * 720 * sc) / 40 + 0.5, 0, 1)        # 1 outside the source rows (soft edge)
    o = o * (1 - out_m[..., None]) + sky[:, None, :] * out_m[..., None]
    return np.clip(grade(np.clip(o, 0, 1), s, f), 0, 1)

def base107(s, f):
    if s.get("banner"): return banner_frame(s, f), None
    img, person = base12(s, f)
    if s.get("pop"): img = pop_behind(img, s, f, person)
    return img, person

_B107 = {}
def edge107(S_, which):
    key = (S_["n"], which)
    if key not in _B107:
        if len(_B107) > 6: _B107.clear()
        _B107[key] = base107(S_, S_["f0"] if which == "first" else S_["f1"] - 1)[0]
    return _B107[key]

# ---- PRESS FLASH: a press camera fires; the next shot is printed as a newspaper photo, then comes to life -------------
def press_flash(A, B, j, f, sa, sb, pre=4, post=18):
    if j < 0:
        u = (j + pre + 1) / pre
        return np.clip(A * (1 + 0.10 * u) + 0.03 * u, 0, 1)
    v = (j + 1) / post
    snap = edge107(sb, "first")
    pr = halftone(snap, 8.0)
    w = smooth((v - 0.30) / 0.55)                                                          # the print comes to life
    o = pr * (1 - w) + B * w
    if 0.15 < v < 0.85:                                                                    # dots shrink as it resolves
        o = o * 0.5 + (halftone(B, 8.0 - 5.0 * smooth((v - 0.15) / 0.7)) * (1 - w) + B * w) * 0.5
    fl = math.exp(-j / 1.8)                                                                # the flashbulb
    o = o + (PAPER * 0.9 + 0.08) * fl * 0.30
    return np.clip(o, 0, 1)
TR2["press_flash"] = (press_flash, 4, 18)

# ---- HOT MOLASSES: a viscous sheet of blood pours down the lens ---------------------------------------------------
_MOL = {}
def mol_fields():
    if "f" not in _MOL:
        rng = np.random.default_rng(1071); xs = np.arange(W // 4, dtype=np.float32)
        fing = np.zeros_like(xs)
        for _ in range(7):                                                                 # the fingers of the front
            c = rng.uniform(0, W // 4); w = rng.uniform(16, 40); a = rng.uniform(0.4, 1.0)
            fing += a * np.exp(-((xs - c) / w) ** 2)
        fing = fing / fing.max()
        wave = cv2.GaussianBlur(rng.standard_normal((H // 4 * 2, W // 4)).astype(np.float32), (0, 0), sigmaX=9, sigmaY=16)
        _MOL["f"] = (fing, cv2.GaussianBlur(fing[None, :], (0, 0), 10)[0], wave / (np.abs(wave).max() + 1e-6))
    return _MOL["f"]

def mol_thickness(q, f):
    """quarter-res thickness of the sheet at progress q (0 -> 1 over pre + post); the cut is at MOL_QC."""
    fing, fsoft, wave = mol_fields(); h4, w4 = H // 4, W // 4
    yy = np.arange(h4, dtype=np.float32)[:, None]
    qp = clamp(q / MOL_QC, 0, 1); qd = clamp((q - MOL_QC) / (1 - MOL_QC), 0, 1)
    front = (-0.15 + 1.32 * ein(qp, 1.45)) * h4 + fing[None, :] * 85 * min(1.0, qp * 1.5) * (1 - 0.7 * qd)   # pours; fingers lead
    top = (-0.06 + 1.42 * ein(qd, 1.35)) * h4 + (1 - fsoft[None, :]) * 40 * qd                               # drains from the top
    body = np.clip((front - yy) / 26, 0, 1) * np.clip((yy - top) / 26, 0, 1)
    bead = np.exp(-((front - yy - 11) / 9.0) ** 2) * 0.45 * (qp < 1)                       # the rounded bead on the front
    bead2 = np.exp(-((yy - top - 10) / 9.0) ** 2) * 0.35 * (qd > 0) * np.clip((front - yy) / 26, 0, 1)   # the meniscus on the draining edge
    off = int(f * 3.0) % h4                                                                # undulations slide down the sheet
    und = 1 + 0.28 * wave[h4 - off:2 * h4 - off]
    th_ = (body * (0.72 + 0.28 * (1 - qd)) * und + bead + bead2).astype(np.float32)
    return np.clip(th_, 0, 1.5)

MOL_PRE, MOL_POST = 36, 24
MOL_QC = MOL_PRE / (MOL_PRE + MOL_POST)
def molasses(A, B, j, f, sa, sb, pre=MOL_PRE, post=MOL_POST):
    q = (j + pre + 0.5) / (pre + post)
    t4 = mol_thickness(q, f)
    if t4.max() < 0.003: return B if j >= 0 else A
    T = cv2.resize(t4, (W, H), interpolation=cv2.INTER_CUBIC)
    gy, gx = np.gradient(cv2.GaussianBlur(t4, (0, 0), 1.6))
    gx = cv2.resize(gx, (W, H)); gy = cv2.resize(gy, (W, H))
    plate = A if j < 0 else B
    ref = cv2.remap(plate, _GX + gx * 300, _GY + gy * 300, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)   # refraction
    sig = np.array([3.0, 2.8, 0.75], np.float32)
    Tr = np.exp(-sig * T[..., None] * 1.6)                                                 # absorption: crimson, deepest where thick
    col = ref * Tr * np.array([0.55, 0.55, 1.0], np.float32) ** np.clip(T[..., None] * 3, 0, 1) + BLOODC * (1 - Tr[..., 2:3]) * 0.9
    nx, ny = -gx * 26, -gy * 26; nz = np.ones_like(nx); nn = np.sqrt(nx * nx + ny * ny + nz * nz)
    l = np.array([-0.45, -0.55, 0.70], np.float32); l /= np.linalg.norm(l); hv = l + np.array([0, 0, 1], np.float32); hv /= np.linalg.norm(hv)
    ndh = (nx * hv[0] + ny * hv[1] + nz * hv[2]) / nn
    spec = np.clip(ndh, 0, 1) ** 46 * 1.10 * np.clip(T * 4, 0, 1)                         # the gloss
    sheen = np.clip((nx * l[0] + ny * l[1] + nz * l[2]) / nn, 0, 1) ** 8 * 0.10 * np.clip(T * 3, 0, 1)
    o = col + (spec + sheen)[..., None] * np.array([0.92, 0.95, 1.0], np.float32)
    return np.clip(o, 0, 1)
TR2["molasses"] = (molasses, MOL_PRE, MOL_POST)

# ---- HEADSPIN: two turns about the centre, motion-blurred, onto the upside-down shot --------------------------------
def spin_img(img, ang, z, n=1, spread=0.0):
    acc = None
    for i in range(n):
        a = ang + (i / max(1, n - 1) - 0.5) * spread if n > 1 else ang
        M = cv2.getRotationMatrix2D((W / 2, H / 2), a, z)
        r = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        acc = r if acc is None else acc + r
    return acc / n

def headspin(A, B, j, f, sa, sb, pre=20, post=20):
    N = pre + post; q = (j + pre + 0.5) / N
    phi = 720 * q * q * (3 - 2 * q); dphi = 720 * 6 * q * (1 - q) / N                     # degrees, and per frame
    z = 1 + 0.30 * math.sin(math.pi * q)
    img = A if j < 0 else B; ang = -phi if j < 0 else -(phi - 720)
    n = int(clamp(dphi / 4, 1, 9))
    o = spin_img(img, ang, z, n, dphi)
    if dphi > 8: o = radial_blur(o, W / 2, H / 2, 1.0, 1.0 + 0.0025 * dphi, 4)
    return np.clip(o, 0, 1)
TR2["headspin"] = (headspin, 20, 20)

def flip(A, B, j, f, sa, sb, pre=5, post=9):
    """the upside-down shot rolls the rest of the way over into the grin."""
    if j < 0:
        u = (j + pre + 1) / pre; ang = 90 * ein(u, 2); return np.clip(spin_img(A, ang, 1 + 0.15 * u, 5, 18 * u), 0, 1)
    v = (j + 1) / post; ang = -90 * (1 - eout(v, 2.2))
    return np.clip(spin_img(B, ang, 1 + 0.15 * (1 - v), 5 if v < 0.6 else 1, 18 * (1 - v)), 0, 1)
TR2["flip"] = (flip, 5, 9)

# ---- THE FRONT PAGE: BAY HARBOR BUTCHER; the photo under it is him (the next shot) --------------------------------
F_MAST = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
F_BODY = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
F_CAPT = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
PHOTO = (56, 742, 456, 1453)                                                               # x0, y0, x1, y1 on the page (9:16)
def squeeze(m, sx): return cv2.resize(m, (max(1, int(m.shape[1] * sx)), m.shape[0]), interpolation=cv2.INTER_AREA)
def put_mask(canvas_a, m, x, y):
    h, w = m.shape; ys, xs = slice(max(0, y), min(H, y + h)), slice(max(0, x), min(W, x + w))
    canvas_a[ys, xs] = np.maximum(canvas_a[ys, xs], m[ys.start - y:ys.stop - y, xs.start - x:xs.stop - x])

_FP = {}
def page_layers():
    """(paper rgb, ink mask, red mask): the front page without its photo."""
    if "p" in _FP: return _FP["p"]
    rng = np.random.default_rng(1072)
    paper = np.empty((H, W, 3), np.float32); pt = paper_tex()
    for c in range(3): paper[..., c] = PAPER[c] * (1 + pt * 0.05)
    edge = np.clip(np.minimum(np.minimum(_GX, W - 1 - _GX), np.minimum(_GY, H - 1 - _GY)) / 90, 0, 1)
    paper *= (0.90 + 0.10 * edge)[..., None]
    ink = np.zeros((H, W), np.float32); red = np.zeros((H, W), np.float32)
    m = text_mask("MIAMI GAZETTE", F_MAST, 104); m = squeeze(m, min(1.0, 980 / m.shape[1])); put_mask(ink, m, int(W / 2 - m.shape[1] / 2), 52)
    cv2.line(ink, (40, 40), (W - 40, 40), 1.0, 3); cv2.line(ink, (40, 196), (W - 40, 196), 1.0, 3); cv2.line(ink, (40, 238), (W - 40, 238), 1.0, 1)
    m = text_mask("SPECIAL EDITION   ·   MIAMI, FLORIDA   ·   FINAL", F_SB, 26, tracking=2); put_mask(ink, m, int(W / 2 - m.shape[1] / 2), 204)
    m = text_mask("BAY HARBOR", F_BLACK, 210, tracking=-4); m = squeeze(m, 990 / m.shape[1]); put_mask(ink, m, int(W / 2 - m.shape[1] / 2), 252)
    m = text_mask("BUTCHER", F_BLACK, 250, tracking=-4); m = squeeze(m, 990 / m.shape[1]); put_mask(red, m, int(W / 2 - m.shape[1] / 2), 452)
    m = text_mask("INVESTIGATION STILL ONGOING", F_XB, 46, tracking=1); m = squeeze(m, min(1.0, 990 / m.shape[1])); put_mask(ink, m, int(W / 2 - m.shape[1] / 2), 676)
    cv2.rectangle(ink, (PHOTO[0] - 3, PHOTO[1] - 3), (PHOTO[2] + 3, PHOTO[3] + 3), 1.0, 2)
    m = text_mask("Blood spatter analyst Dexter Morgan", F_CAPT, 21); put_mask(ink, m, PHOTO[0], PHOTO[3] + 12)
    m = text_mask("at the scene, Tuesday.", F_CAPT, 21); put_mask(ink, m, PHOTO[0], PHOTO[3] + 40)
    words = ("the police said investigators were searching the bay for more remains as federal agents joined the case and the "
             "department declined to comment on reports that a suspect had been identified among the bodies recovered from the "
             "water off the marina residents gathered at the docks overnight while divers worked in shifts the medical examiner "
             "confirmed that the victims had been killed elsewhere and the killer remains at large").split()
    cols = [(496, 742, 752), (776, 742, 1032)]
    for (x0, y0, x1) in cols:
        y = y0; wi = int(rng.integers(len(words)))
        while y < 1830:
            line = []; wsum = 0
            while True:
                w = words[wi % len(words)]; wi += 1; tw = len(w) * 11 + 9
                if wsum + tw > (x1 - x0): break
                line.append(w); wsum += tw
            m = text_mask(" ".join(line), F_BODY, 21); put_mask(ink, squeeze(m, min(1.0, (x1 - x0) / m.shape[1])), x0, y)
            y += 29
            if rng.random() < 0.06: y += 22
        cv2.line(ink, (x1 + 12, 742), (x1 + 12, 1840), 0.8, 1)
    y = 1500
    while y < 1830:
        m = text_mask(" ".join(words[(y // 7) % 20:(y // 7) % 20 + 6]), F_BODY, 21); put_mask(ink, squeeze(m, min(1.0, 400 / m.shape[1])), PHOTO[0], y); y += 29
    _FP["p"] = (paper, ink, red); return _FP["p"]

def page_with_photo(photo):
    """the page, with photo (a full 1080x1920 frame) printed into the photo box as a halftone."""
    paper, ink, red = page_layers()
    pw, ph = PHOTO[2] - PHOTO[0], PHOTO[3] - PHOTO[1]
    small = cv2.resize(photo, (pw, ph), interpolation=cv2.INTER_AREA)
    pr = halftone(cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR), 9.0 * W / pw)  # screen at print scale
    pr = cv2.resize(pr, (pw, ph), interpolation=cv2.INTER_AREA)
    o = paper.copy(); o[PHOTO[1]:PHOTO[3], PHOTO[0]:PHOTO[2]] = pr * (0.97 + 0.03 * paper[PHOTO[1]:PHOTO[3], PHOTO[0]:PHOTO[2]] / PAPER)
    o = o * (1 - ink[..., None] * 0.94) + INK * ink[..., None] * 0.94
    o = o * (1 - red[..., None]) + SPOT * red[..., None]
    return o.astype(np.float32)

def frontpage(A, B, j, f, sa, sb, pre=82, post=28):
    PCX, PCY = (PHOTO[0] + PHOTO[2]) / 2, (PHOTO[1] + PHOTO[3]) / 2
    SDIVE = H / (PHOTO[3] - PHOTO[1])
    if j >= 0:                                                                             # the photo's dots resolve into him
        v = (j + 1) / post; pitch = 9.0 * SDIVE * (1 - eout(v, 1.6)) + 3.0
        w = smooth((v - 0.25) / 0.65)
        return np.clip(halftone(B, pitch) * (1 - w) + B * w, 0, 1)
    if "pg" not in _FP or _FP.get("pgk") != sb["n"]:
        _FP["pg"] = page_with_photo(edge107(sb, "first")); _FP["pgk"] = sb["n"]
    page = _FP["pg"]
    u = (j + pre + 1) / pre
    if u < 0.80:
        if u < 0.52:                                                                       # the classic spin-in
            w_ = eout(u / 0.52, 2.6); s_ = 0.04 + 0.86 * w_; rot = 3 * 360 * (1 - w_)
        else:                                                                              # it lands, settles, we push in
            w_ = (u - 0.52) / 0.28
            s_ = 0.90 + 0.05 * math.sin(math.pi * min(1, w_ * 2.2)) * math.exp(-w_ * 2) + 0.06 * w_; rot = 2.0 * math.exp(-w_ * 5) * math.cos(w_ * 12)
        M = cv2.getRotationMatrix2D((W / 2, H / 2), rot, s_)
    else:                                                                                  # the dive: his photo comes to fill the frame
        w_ = ein((u - 0.80) / 0.20, 2.2); s0 = 0.96; s_ = s0 * (SDIVE / s0) ** w_
        pcx0, pcy0 = W / 2 + (PCX - W / 2) * s0, H / 2 + (PCY - H / 2) * s0
        tcx, tcy = pcx0 + (W / 2 - pcx0) * w_, pcy0 + (H / 2 - pcy0) * w_
        M = np.float32([[s_, 0, tcx - PCX * s_], [0, s_, tcy - PCY * s_]])
    pa = cv2.warpAffine(np.dstack([page, np.ones((H, W), np.float32)]), M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    al = pa[..., 3:4]
    bg = A * (1 - 0.45 * min(1.0, u * 2.5))
    if u < 0.80:                                                                           # its shadow on the scene
        sh = cv2.GaussianBlur(np.roll(np.roll(pa[..., 3], 18, 0), 12, 1), (0, 0), 16) * 0.55
        bg = bg * (1 - sh[..., None])
    return np.clip(bg * (1 - al) + pa[..., :3] * al, 0, 1)
TR2["frontpage"] = (frontpage, 82, 28)

# ---- confetti: lit paper pieces, fluttering, with depth ------------------------------------------------------------
CONF_COLS = np.array([[0.13, 0.12, 0.80], [0.84, 0.92, 0.96], [0.84, 0.92, 0.96], [0.06, 0.05, 0.05], [0.50, 0.42, 0.34], [0.20, 0.20, 0.86]], np.float32)
def conf_set(seed, n, t_a, t_b, mode):
    """n pieces. mode 'rain': spawned above the frame between t_a and t_b; 'pop': all at t_a from a burst point."""
    rng = np.random.default_rng(seed)
    d = dict(t=rng.uniform(t_a, t_b, n) if mode == "rain" else np.full(n, t_a, np.float32),
             x=rng.uniform(-80, W + 80, n), y=rng.uniform(-300, -40, n),
             depth=rng.uniform(0, 1, n) ** 1.6, col=rng.integers(0, len(CONF_COLS), n),
             a0=rng.uniform(0, 360, n), wa=rng.uniform(-420, 420, n), b0=rng.uniform(0, 6.28, n), wb=rng.uniform(5, 16, n),
             sway=rng.uniform(10, 60, n), ws=rng.uniform(1.5, 4.0, n), ar=rng.uniform(0.35, 0.75, n),
             vx=rng.normal(0, 1, n), vy=rng.normal(0, 1, n))
    return d

def draw_confetti(out, t, d, mode="rain", origin=(W / 2, H * 0.3), cover=1.0, guard=None):
    tau = t - d["t"]; alive = tau >= 0
    if not alive.any(): return out
    near = d["depth"]; size = 14 + 150 * near ** 2.2                                       # near pieces are big and soft
    if mode == "rain":
        vfall = (260 + 900 * near) if mode == "rain" and cover < 2 else 0
        vfall = vfall * (2.6 if cover >= 1.5 else 1.0)
        px = d["x"] + d["sway"] * np.sin(d["ws"] * tau + d["b0"]); py = d["y"] + vfall * tau
    else:
        sp = 900 + 1500 * near; ex = 1 - np.exp(-tau * 3.2)
        px = origin[0] + d["vx"] * sp * 1.4 * ex / 3.2 + d["sway"] * np.sin(d["ws"] * tau + d["b0"])
        py = origin[1] + (np.abs(d["vy"]) * 0.8 + 0.25) * sp * 0.75 * ex / 3.2 + (180 + 500 * near) * np.maximum(0, tau - 0.15) ** 1.4 * 1.6
    vis = alive & (py > -260) & (py < H + 260) & (px > -260) & (px < W + 260)
    if not vis.any(): return out
    lay_far = np.zeros((H, W, 3), np.uint8); a_far = np.zeros((H, W), np.uint8)
    lay_near = np.zeros((H, W, 3), np.uint8); a_near = np.zeros((H, W), np.uint8)
    order = np.argsort(near)
    for i in order:
        if not vis[i]: continue
        sz = size[i] * (1.25 if cover >= 1.5 else 1.0); ang = math.radians(d["a0"][i] + d["wa"][i] * tau[i]); fl = math.cos(d["b0"][i] + d["wb"][i] * tau[i])
        hw, hh = sz * 0.5, sz * 0.5 * d["ar"][i] * max(0.08, abs(fl))
        ca, sa_ = math.cos(ang), math.sin(ang)
        pts = np.array([[px[i] + ca * dx - sa_ * dy, py[i] + sa_ * dx + ca * dy] for dx, dy in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))], np.float32)
        bright = 0.55 + 0.45 * abs(fl) + (0.55 if abs(fl) > 0.97 else 0.0)
        col = np.clip(CONF_COLS[d["col"][i]] * bright, 0, 1)
        far = near[i] < 0.55
        L_, A_ = (lay_far, a_far) if far else (lay_near, a_near)
        cv2.fillConvexPoly(L_, (pts * 4).astype(np.int32), tuple(int(c * 255) for c in col), cv2.LINE_AA, 2)
        cv2.fillConvexPoly(A_, (pts * 4).astype(np.int32), 255, cv2.LINE_AA, 2)
    o = out
    for L_, A_, blur in ((lay_far, a_far, 0.0), (lay_near, a_near, 2.4)):
        if not A_.any(): continue
        Lf = L_.astype(np.float32) / 255; Af = A_.astype(np.float32) / 255
        if blur: Lf = cv2.GaussianBlur(Lf, (0, 0), blur); Af = cv2.GaussianBlur(Af, (0, 0), blur)
        if guard is not None: Af = Af * guard
        o = o * (1 - Af[..., None]) + Lf * Af[..., None] * 1.0
    return o

def face_keep(s, f, grow=1.25):
    """1 everywhere except a feathered ellipse over the tracked face (particles never cross it)."""
    fs = face_scr(s, f) if s.get("face") is not None else None
    if not fs: return None
    m = np.zeros((H // 4, W // 4), np.float32)
    cv2.ellipse(m, (int(fs[0] / 4), int(fs[1] / 4)), (int(fs[2] * 0.62 * grow / 4), int(fs[2] * 0.85 * grow / 4)), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
    return 1 - cv2.resize(cv2.GaussianBlur(m, (0, 0), 5), (W, H))

POP_PRE = 24
def pop_set():
    if "pop" not in _FP: _FP["pop"] = conf_set(1073, 190, 0.0, 0.0, "pop")
    return _FP["pop"]

def confetti_pop(A, B, j, f, sa, sb, pre=POP_PRE, post=2):
    """the confetti bursts in the sky over the banner; after the cut it carries on behind him (pop_behind)."""
    if j >= 0: return B
    return np.clip(draw_confetti(A, (j + pre + 1) / FPS, pop_set(), "pop", (W * 0.5, H * 0.02)), 0, 1)

def pop_behind(img, s, f, person):
    """a confetti burst from the top of the frame, between him and the crowd (his matte keeps it off him)."""
    k = f - s["f0"]
    if k >= 70 or person is None: return img
    c = draw_confetti(img, (k + POP_PRE + 1) / FPS, pop_set(), "pop", (W * 0.5, H * 0.02))
    pm = np.clip(person * 1.1, 0, 1)[..., None]
    return img * pm + c * (1 - pm)
TR2["confetti_pop"] = (confetti_pop, POP_PRE, 2)

# ---- THE LOOP: the confetti thickens over the lens on the bass drop-out bar and clears on frame 0 ---------------------
LOOP_F0 = None
def loop_w(f):
    f0 = fh(E.E_LOOP); u = (f - f0 + 1) / (E.DUR_F - f0)
    return smooth((u - 0.38) / 0.24) if f >= f0 else 0.0

_LV = {}
def frame0_plate():
    if "b" not in _LV: _LV["b"] = base107(SHOTS[0], SHOTS[0]["f0"])[0]
    return _LV["b"]

def confetti_loop(out, f, s):
    f0 = fh(E.E_LOOP)
    if f < f0: return out
    t = (f - f0) / FPS; T = (E.DUR_F - f0) / FPS
    if "rain" not in _FP: _FP["rain"] = conf_set(1074, 1100, -0.6, T - 0.95, "rain")
    w = loop_w(f)
    under = out if w <= 0 else (frame0_plate() if w >= 1 else out * (1 - w) + frame0_plate() * w)
    u = (f - f0 + 1) / (E.DUR_F - f0); thick = math.sin(math.pi * clamp(u / 0.95, 0, 1)) ** 0.8
    under = under * (1 - 0.10 * thick)
    o = draw_confetti(under, t, _FP["rain"], "rain", cover=1.6)
    fade = smooth((t - (T - 0.40)) / 0.36)                                                 # the stragglers fade as frame 0 arrives
    return np.clip(o * (1 - fade) + under * fade, 0, 1)

# ---- the STAMP: the newsprint strip and D-E-X-T-E-R, then the strip becomes the banner in the sky -------------------
STRIP_C, STRIP_W, STRIP_H, STRIP_ROT = (540, 870), 1010, 250, -3.0
_ST = {}
def strip_tex():
    if "s" in _ST: return _ST["s"]
    rng = np.random.default_rng(1075); h, w = STRIP_H + 60, STRIP_W + 60
    pt = paper_tex()[:h, :w]
    rgb = np.empty((h, w, 3), np.float32)
    for c in range(3): rgb[..., c] = PAPER[c] * (1 + pt * 0.06)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    n1 = cv2.resize(rng.standard_normal((h // 6, w // 6)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    torn = np.minimum(np.minimum(xx - 30 - n1 * 5, w - 30 - xx + n1 * 5), np.minimum(yy - 30 - n1 * 3, h - 30 - yy - n1 * 3))
    a = np.clip(torn / 1.5 + 0.5, 0, 1)
    rgb *= (0.93 + 0.07 * np.clip(torn / 40, 0, 1))[..., None]                             # the edges a touch darker
    _ST["s"] = np.dstack([rgb, a]).astype(np.float32)
    lets, xs = [], []
    for c in "DEXTER":
        m = text_mask(c, F_BLACK, 205, tracking=0); lets.append(m)
    tot = sum(m.shape[1] for m in lets) + 26 * 5; x = w / 2 - tot / 2
    for m in lets: xs.append(x + m.shape[1] / 2); x += m.shape[1] + 26
    rgi = np.random.default_rng(1076)
    inks = []
    for m in lets:                                                                         # letterpress ink: uneven, a little bite
        sp = cv2.resize(rgi.random((m.shape[0] // 3 + 1, m.shape[1] // 3 + 1)).astype(np.float32), (m.shape[1], m.shape[0]))
        inks.append(np.clip(m * (0.82 + 0.18 * sp) * (1 - (sp < 0.06) * 0.6), 0, 1))
    _ST["lets"] = (inks, xs); return _ST["s"]

def strip_canvas(t, stamps):
    """the strip (rgba, its own pixel space) with the letters stamped by time t."""
    base = strip_tex().copy(); inks, xs = _ST["lets"]; h, w = base.shape[:2]
    for (wd, tw), m, xc in zip(stamps, inks, xs):
        k = (t - tw) * FPS
        if k < 0: continue
        v = clamp(k / 4.0, 0, 1)
        if v < 1:                                                                          # the stamp coming down
            sc = 1.9 - 0.9 * ein(v, 2.2); mm = cv2.resize(m, None, fx=sc, fy=sc); mm = cv2.GaussianBlur(mm, (0, 0), 0.1 + 6 * (1 - v)) * v
        else: mm = m
        hh, ww = mm.shape; x0 = int(xc - ww / 2); y0 = int(h / 2 - hh / 2 + 6)
        ys, xs_ = slice(max(0, y0), min(h, y0 + hh)), slice(max(0, x0), min(w, x0 + ww))
        sub = mm[ys.start - y0:ys.stop - y0, xs_.start - x0:xs_.stop - x0]
        if v >= 1:                                                                         # the deboss: pressed into the paper
            dm = cv2.GaussianBlur(sub, (0, 0), 2.0)
            sh = np.clip(np.roll(dm, 3, 0) - dm, 0, 1) * 0.35; hl = np.clip(np.roll(dm, -3, 0) - dm, 0, 1) * 0.10
            base[ys, xs_, :3] *= (1 - sh)[..., None]; base[ys, xs_, :3] += hl[..., None]
            spread = 1 + 0.10 * math.exp(-(k - 4) / 3)                                      # ink spreads at the hit, then settles
            sub = np.clip(sub * spread, 0, 1)
        base[ys, xs_, :3] = base[ys, xs_, :3] * (1 - sub[..., None]) + INK * sub[..., None]
    return base

def put_strip(out, rgba, cx, cy, sc, rot, a=1.0, shadow=0.45):
    h, w = rgba.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, sc); M[0, 2] += cx - w / 2; M[1, 2] += cy - h / 2
    pa = cv2.warpAffine(rgba, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    al = pa[..., 3:4] * a
    if shadow > 0:
        sh = cv2.GaussianBlur(np.roll(np.roll(pa[..., 3], 16, 0), 10, 1), (0, 0), 14) * shadow * a
        out = out * (1 - sh[..., None])
    return out * (1 - al) + pa[..., :3] * al

def banner_target():
    """where the banner's DEXTER sits on screen in the banner shot (centre, scale vs the strip, rotation)."""
    return (785.0, 980.0), 0.53, -4.1

def text_stamp(out, f, tx):
    t = f / FPS; stamps = [(w, wt) for w, wt, _ in tx["words"]]
    t_in = next(wt for tx_ in E.TEXT if tx_["style"] == "cap" for w_, wt, _ in tx_["words"] if w_ == "CAPS") - 0.02   # it slaps on with "CAPS"
    t_cut = E.th(48); t_end = t_cut + 0.80
    if t < t_in or t > t_end: return out
    rgba = strip_canvas(min(t, t_cut + 0.2), stamps)
    k = (t - t_in) * FPS; v = clamp(k / 5.0, 0, 1)
    sc = 1.28 - 0.28 * eout(v, 3) + (0.02 * math.sin(k * 0.9) * math.exp(-k / 6) if v >= 1 else 0)
    cx, cy = STRIP_C; rot = STRIP_ROT; a = min(1.0, k / 3.0); shake = 0.0
    for _, tw in stamps:                                                                   # each stamp shakes the strip
        dk = (t - tw) * FPS - 4
        if 0 <= dk < 8: shake = max(shake, 5 * math.exp(-dk / 2.5))
    cy += shake * math.sin(f * 2.1)
    if t > t_cut - 0.02:                                                                   # it flies into the sky onto the banner
        w_ = smooth((t - t_cut + 0.02) / 0.45)
        (bx, by), bs, br = banner_target()
        cx, cy = cx + (bx - cx) * w_, cy + (by - cy) * w_; sc = sc + (bs - sc) * w_; rot = rot + (br - rot) * w_
        a = a * (1 - smooth((t - t_cut - 0.42) / 0.36))
    return put_strip(out, rgba, cx, cy, sc, rot, a, 0.45 * (1 - smooth((t - t_cut) / 0.3)))

def text_cap(out, f, tx, person=None):
    """the v9 caption (the approved construction), with an optional per-caption ys=(line0, line1)."""
    t = f / FPS; words = tx["words"]; t_in = max(words[0][1], tx.get("from", -1))
    if t < t_in - 0.02 or t > tx["end"] + 0.01: return out
    big = tx.get("big"); sizes = [92, 120] if big else [88, 114]
    ys = tx.get("ys") or ((1368, 1492) if big else (1380, 1496))
    emph = tx.get("emph", []); fr = tx.get("from", -1)
    a_out = 1 - smooth((t - (tx["end"] - 0.16)) / 0.16)
    out = out * cap_scrim(ys[0] - 70, ys[1] + 70, 0.34 * a_out * smooth((t - t_in + 0.05) / 0.25))
    for ln in (0, 1):
        ws = [(w, max(wt, fr)) for w, wt, l in words if l == ln]
        if not ws: continue
        sz = sizes[ln]
        for _ in range(6):                                                                 # auto-fit the line to 940 px
            ims = [cap_word(w, sz, w in emph) for w, _ in ws]
            gap = int(sz * 0.26); widths = [im.shape[1] - 72 for im in ims]
            tot = sum(widths) + gap * (len(ims) - 1)
            if tot <= 940: break
            sz = int(sz * 940 / tot) - 1
        x = W / 2 - tot / 2
        for (w, wt), im, wd in zip(ws, ims, widths):
            v = eout(clamp((t - wt) / 0.17, 0, 1), 2.4)
            o_im = im if a_out > 0.98 else cv2.GaussianBlur(im, (0, 0), 0.1 + 5 * (1 - a_out))
            out = ease_word(out, o_im, x + wd / 2, ys[ln] - 14 * (1 - a_out), v, a_out, rise=30)
            x += wd + gap
    return out

def text107(out, f, s, rides):
    for tx in E.TEXT:
        if bool(tx.get("rides")) != rides: continue
        if tx["style"] == "cap": out = text_cap(out, f, tx, None)
        elif tx["style"] == "stamp": out = text_stamp(out, f, tx)
    return out

# ---- the frame ----------------------------------------------------------------------------------------------------
# ---- THE BULB (the anguish shot): a bare bulb above him swings on its cord; its pool of light swings across him and the
# crucifix behind (the room breathes with it; no flicker)
def bulb110(out, f, s):
    t = (f - s["f0"]) / FPS; per = 4 * E.HB
    k = smooth(t / 0.25)
    x = W * 0.5 + W * 0.30 * math.sin(2 * math.pi * t / per - 0.6) * k
    y = H * 0.20 - H * 0.03 * abs(math.cos(2 * math.pi * t / per - 0.6))
    d2 = ((_GX - x) / (0.34 * W)) ** 2 + ((_GY - y) / (0.55 * H)) ** 2
    m = 0.42 + 0.95 * np.exp(-d2)
    return np.clip(out * m[..., None] + np.exp(-d2 * 3.0)[..., None] * AMB110 * 0.05, 0, 1)

def render(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin")
    out, person = base107(s, f)
    out = text107(out, f, s, True)
    if tin in TR2 and k < TR2[tin][2] and P is not None:
        out = TR2[tin][0](edge107(P, "last"), out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, edge107(n_, "first"), kn, f, s, n_)
    if s.get("tout") == "confetti_loop": out = confetti_loop(out, f, s)
    out = beat_fx(out, f)
    out = text107(out, f, s, False)
    out = flash_governor(out)
    return (np.clip(finish107(out, f, s), 0, 1) * 255 + 0.5).astype(np.uint8)

# ============================================================================ v107 rev 2 (owner notes; overrides above)
# ---- the camera rests through the break (the ending is smooth) and during the TV ------------------------------------
def beat_phase(f):
    e = f / FPS / E.HB; ph = (e % 2) * E.HB; bi = int(e // 2)
    hook = (E.E_BEAT <= e < 54) and not (6.5 <= e < 9.7) and not (19 <= e < 23) and not (24 <= e < 28.5) and not (47 <= e < 50)
    return ph, bi, hook, False

# ---- SPECIAL REPORT: the shot is on a TV; the channel flips; we push back through the screen -------------------------
TV_W, TV_H = 860.0, 645.0                                                                  # the 4:3 screen at the TV's own scale
Z_FULL = W / TV_W                                                                          # the zoom where the screen fills the width
_TV = {}
def tv_assets():
    """(casing rgba at scale 1 around a screen centred on the frame, chyron rgba in screen pixels, scanlines)."""
    if "c" in _TV: return _TV["c"]
    bw, bh = 1000, 900; cx, cy = W / 2, H / 2 + 60                                          # the body: the screen sits high in it
    cas = np.zeros((H, W, 4), np.float32)
    body = np.zeros((H, W), np.float32)
    cv2.rectangle(body, (int(cx - bw / 2), int(cy - bh / 2 - 60)), (int(cx + bw / 2), int(cy + bh / 2 - 60)), 1.0, -1)
    body = cv2.GaussianBlur(body, (0, 0), 6); body = np.clip(body * 1.6 - 0.3, 0, 1)
    scr = np.zeros((H, W), np.float32)
    cv2.rectangle(scr, (int(W / 2 - TV_W / 2 + 22), int(H / 2 - TV_H / 2 + 22)), (int(W / 2 + TV_W / 2 - 22), int(H / 2 + TV_H / 2 - 22)), 1.0, -1)
    scr = np.clip(cv2.GaussianBlur(scr, (0, 0), 14) * 1.9 - 0.45, 0, 1)                    # rounded screen corners
    yy = (_GY - (cy - bh / 2 - 60)) / bh
    xx = (_GX - (cx - bw / 2)) / bw
    shade = 0.20 + 0.10 * (1 - np.clip(yy, 0, 1)) + 0.04 * np.sin(np.pi * np.clip(xx, 0, 1))   # lit from above and the front
    shade = shade + 0.16 * np.exp(-((_GY - (cy - bh / 2 - 54)) / 5) ** 2) + 0.06 * np.exp(-((_GX - (cx - bw / 2 + 6)) / 5) ** 2)   # edge highlights
    shade = shade - 0.06 * np.exp(-((_GY - (cy + bh / 2 - 66)) / 6) ** 2)                 # the bottom edge in shadow
    rim = np.exp(-((cv2.GaussianBlur(scr, (0, 0), 3) - 0.5) / 0.18) ** 2) * 0.16             # the bevel round the glass
    for c in range(3): cas[..., c] = shade * (0.95 + 0.05 * c) + rim
    led = np.exp(-(((_GX - (cx + bw / 2 - 90)) / 7) ** 2 + ((_GY - (cy + bh / 2 - 105)) / 7) ** 2))
    cas[..., :3] += led[..., None] * SPOT * 1.4
    for k in range(5): cv2.line(cas, (int(cx - bw / 2 + 70 + 34 * k), int(cy + bh / 2 - 112)), (int(cx - bw / 2 + 92 + 34 * k), int(cy + bh / 2 - 112)), (0.30, 0.30, 0.30, 1.0), 3, cv2.LINE_AA)
    cas[..., 3] = body * (1 - scr)
    cas[..., :3] *= cas[..., 3:4]
    sw, sh = int(TV_W), int(TV_H); ch = np.zeros((sh, sw, 4), np.float32)
    bar_y = int(sh * 0.74); cv2.rectangle(ch, (0, bar_y), (int(sw * 0.36), bar_y + 50), tuple(float(v) for v in SPOT) + (1.0,), -1)
    cv2.rectangle(ch, (int(sw * 0.36), bar_y), (sw, bar_y + 50), tuple(float(v) for v in PAPER) + (1.0,), -1)
    cv2.rectangle(ch, (0, bar_y + 50), (sw, bar_y + 92), tuple(float(v) for v in INK) + (0.92,), -1)
    def put_txt(word, font, size, col, x, y):
        m = text_mask(word, font, size, tracking=1); h_, w_ = m.shape; y0 = int(y - h_ / 2)
        sub = ch[y0:y0 + h_, x:x + w_]; mm = m[:sub.shape[0], :sub.shape[1]]
        sub[..., :3] = sub[..., :3] * (1 - mm[..., None]) + np.array(col, np.float32) * mm[..., None]; sub[..., 3] = np.maximum(sub[..., 3], mm)
    put_txt("SPECIAL REPORT", F_BLACK, 30, (0.97, 0.97, 0.97), 14, bar_y + 25)
    put_txt("BAY HARBOR BUTCHER STILL AT LARGE", F_BLACK, 28, tuple(float(v) for v in INK), int(sw * 0.36) + 14, bar_y + 25)
    put_txt("POLICE URGE RESIDENTS TO STAY ALERT · FBI JOINS INVESTIGATION", F_XB, 22, tuple(PAPER), 14, bar_y + 71)
    cv2.rectangle(ch, (22, 22), (110, 62), tuple(float(v) for v in SPOT) + (1.0,), -1); put_txt("LIVE", F_BLACK, 26, (0.97, 0.97, 0.97), 34, 42)
    scan = (1 - 0.10 * (np.arange(sh) % 3 == 0))[:, None].astype(np.float32)
    _TV["c"] = (cas, ch, scan, scr); return _TV["c"]

def tv_frame(content, Z, mask_h, chy, static, glow=1.0, f=0, scan_a=1.0, glass=1.0):
    """content (a full frame) on the TV: Z = zoom of the TV (Z_FULL: the screen is the frame's width); mask_h = the
    visible height of the screen window in output px (letterbox closing/opening); chy 0..1 chyron in; static 0..1."""
    cas, ch, scan, scr = tv_assets()
    k = Z / Z_FULL                                                                         # content scale: 1 at Z_FULL
    M = np.float32([[k, 0, W / 2 * (1 - k)], [0, k, H / 2 * (1 - k)]])
    c = cv2.warpAffine(content, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    sw, sh = TV_W * Z, TV_H * Z                                                            # the screen window
    win_h = min(mask_h, sh) if Z >= Z_FULL - 1e-3 else sh
    sc = cv2.warpAffine(scr, np.float32([[Z, 0, W / 2 * (1 - Z)], [0, Z, H / 2 * (1 - Z)]]), (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    if Z >= Z_FULL - 1e-3 and mask_h > sh:                                                 # still opening: a plain letterbox
        sc = np.clip((mask_h / 2 - np.abs(_GY - H / 2)) / 3, 0, 1).astype(np.float32)
    # the screen: scanlines, phosphor, the chyron, static, the glass
    scr_img = c.copy()
    if scan_a > 0:
        sl = cv2.resize(np.repeat(scan, int(TV_W), 1), None, fx=Z, fy=Z, interpolation=cv2.INTER_LINEAR)
        y0 = int(H / 2 - sl.shape[0] / 2); x0 = int(W / 2 - sl.shape[1] / 2)
        full = np.ones((H, W), np.float32); ys, xs = slice(max(0, y0), min(H, y0 + sl.shape[0])), slice(max(0, x0), min(W, x0 + sl.shape[1]))
        full[ys, xs] = sl[ys.start - y0:ys.stop - y0, xs.start - x0:xs.stop - x0]
        scr_img = scr_img * (1 - scan_a + scan_a * full)[..., None]
    if chy > 0:
        Mc = np.float32([[Z, 0, W / 2 - TV_W * Z / 2 - (1 - eout(chy, 3)) * 400 * Z], [0, Z, H / 2 - TV_H * Z / 2]])
        cw = cv2.warpAffine(ch, Mc, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0)); a = cw[..., 3:4] * min(1.0, chy * 1.5)
        scr_img = scr_img * (1 - a) + cw[..., :3] * a
    if static > 0:
        rng = np.random.default_rng(f * 7 + 3); nz = cv2.resize(rng.random((H // 6, W // 6)).astype(np.float32), (W, H), interpolation=cv2.INTER_NEAREST)
        roll = 0.5 + 0.5 * np.sin((_GY / H * 3 + f * 0.37) * 2 * math.pi)
        stc = (nz * 0.75 + 0.15) * (0.75 + 0.25 * roll)
        scr_img = scr_img * (1 - static) + stc[..., None] * PAPER * static
    vig = 1 - 0.35 * glass * np.clip(((_GX - W / 2) / (sw / 2 + 1)) ** 2 + ((_GY - H / 2) / (sh / 2 + 1)) ** 2, 0, 1) ** 1.5
    refl = np.exp(-(((_GX - W / 2) * 0.6 + (_GY - H / 2 + sh * 0.25)) / (sw * 0.18 + 1)) ** 2) * 0.06 * glass   # a soft glass reflection (fades with the letterbox)
    scr_img = scr_img * vig[..., None] + refl[..., None]
    # the room: dark, lit by the screen
    room = np.zeros((H, W, 3), np.float32) + INK * 0.6
    lum_s = float(cv2.resize(c, (8, 8), interpolation=cv2.INTER_AREA).mean())
    gl = np.exp(-(((_GX - W / 2) / (sw * 1.05 + 1)) ** 2 + ((_GY - H / 2) / (sh * 1.5 + 1)) ** 2)) * (0.16 + 0.35 * lum_s) * glow
    room = room + gl[..., None] * PAPER
    casz = cv2.warpAffine(cas, np.float32([[Z, 0, W / 2 * (1 - Z)], [0, Z, H / 2 * (1 - Z)]]), (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    o = room * (1 - casz[..., 3:4]) + casz[..., :3]
    return np.clip(o * (1 - sc[..., None]) + scr_img * sc[..., None], 0, 1)

def broadcast(A, B, j, f, sa, sb, pre=36, post=36):
    Zmin = 0.92
    if j < 0:
        u = (j + pre + 1) / pre
        if u < 0.33:                                                                       # the picture closes into a TV image
            mh = H - (H - TV_H * Z_FULL) * smooth(u / 0.33)
            return tv_frame(A, Z_FULL, mh, 0.0, 0.0, f=f, scan_a=smooth(u / 0.33), glass=smooth(u / 0.33))
        w = smooth((u - 0.33) / 0.50); Z = Z_FULL + (Zmin - Z_FULL) * w                     # the TV pulls back into a dark room
        st = smooth((u - 0.86) / 0.14) * 0.85                                              # the channel starts to flip
        return tv_frame(A, Z, TV_H * Z, smooth((u - 0.30) / 0.30), st, f=f)
    v = (j + 1) / post
    st = 0.85 * (1 - smooth(v / 0.16))
    if v < 0.70:                                                                           # the new channel: him; we push in
        w = smooth((v - 0.14) / 0.56); Z = Zmin + (Z_FULL - Zmin) * w
        return tv_frame(B, Z, TV_H * Z, 1 - smooth((v - 0.20) / 0.30), st, f=f)
    w = smooth((v - 0.70) / 0.30); mh = TV_H * Z_FULL + (H - TV_H * Z_FULL) * w            # the screen opens to the frame
    return tv_frame(B, Z_FULL, mh, 0.0, 0.0, f=f, scan_a=1 - w, glass=1 - w)
TR2["broadcast"] = (broadcast, 36, 36)

# ---- HEADSPIN onto a centred shot: the turn decelerates about his face -------------------------------------------------
def spin_about(img, ang, z, cx, cy, n=1, spread=0.0):
    acc = None
    for i in range(n):
        a = ang + (i / max(1, n - 1) - 0.5) * spread if n > 1 else ang
        M = cv2.getRotationMatrix2D((cx, cy), a, z); M[0, 2] += W / 2 - cx; M[1, 2] += H / 2 - cy
        M[0, 2] += (cx - W / 2); M[1, 2] += (cy - H / 2)
        r = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        acc = r if acc is None else acc + r
    return acc / n

def headspin(A, B, j, f, sa, sb, pre=20, post=24):
    N = pre + post; q = (j + pre + 0.5) / N
    phi = 720 * q * q * (3 - 2 * q); dphi = 720 * 6 * q * (1 - q) / N
    z = 1 + 0.28 * math.sin(math.pi * q)
    if j < 0: img, ang, cx, cy = A, -phi, W / 2, H / 2
    else:
        fs = face_scr(sb, f) if sb.get("face") is not None else None
        cx, cy = (fs[0], fs[1]) if fs else (W / 2, H / 2); img, ang = B, -(phi - 720)
    n = int(clamp(dphi / 4, 1, 9))
    o = spin_about(img, ang, z, cx, cy, n, dphi)
    if dphi > 8: o = radial_blur(o, cx, cy, 1.0, 1.0 + 0.0025 * dphi, 4)
    return np.clip(o, 0, 1)
TR2["headspin"] = (headspin, 20, 24)

# ---- THE MASSES SPELL HIS NAME (the loop): the parade's confetti gathers into DEXTER, holds, bursts into frame 0 -----
NL_G0, NL_G1, NL_B = 58.4, 60.4, 62.3                                                       # edit half-beats: gather, formed, burst
_NL = {}
def name_targets():
    if "t" in _NL: return _NL["t"]
    m = text_mask("DEXTER", F_BLACK, 300, tracking=10); m = squeeze(m, 1000 / m.shape[1])
    h, w = m.shape; cx, cy = W / 2, 1110
    ys, xs = np.nonzero(m > 0.6); rng = np.random.default_rng(1077); n = 1050
    pick = rng.choice(len(xs), n, replace=False)
    tx = (xs[pick] - w / 2 + cx).astype(np.float32); ty = (ys[pick] - h / 2 + cy).astype(np.float32)
    side = np.where(rng.random(n) < 0.5, -1.0, 1.0).astype(np.float32)
    d = dict(tx=tx, ty=ty, side=side, x0=(W / 2 + side * rng.uniform(W * 0.62, W * 1.05, n)).astype(np.float32),
             y0=rng.uniform(820, 1650, n).astype(np.float32), vf=rng.uniform(380, 900, n).astype(np.float32),
             delay=rng.uniform(0, 0.28, n).astype(np.float32),
             size=rng.uniform(18, 32, n).astype(np.float32), ar=rng.uniform(0.40, 0.70, n).astype(np.float32),
             a0=rng.uniform(0, 360, n).astype(np.float32), wa=rng.uniform(-240, 240, n).astype(np.float32),
             b0=rng.uniform(0, 6.28, n).astype(np.float32), wb=rng.uniform(5, 13, n).astype(np.float32),
             col=rng.choice([1, 1, 2, 2, 1, 0, 0, 5], n), sw=rng.uniform(-1, 1, n).astype(np.float32),
             bv=rng.uniform(0.8, 1.3, n).astype(np.float32))
    _NL["t"] = d; return d

def draw_pieces(out, px, py, size, ang, flut, cols, alpha=None, blur_big=True):
    """lit paper pieces (fluttering quads), far/near layers; size in px, ang in radians, flut = cos of the flutter."""
    lay = [np.zeros((H, W, 3), np.uint8), np.zeros((H, W, 3), np.uint8)]; al = [np.zeros((H, W), np.uint8), np.zeros((H, W), np.uint8)]
    for i in np.argsort(size):
        x, y, sz = px[i], py[i], size[i]
        if x < -sz or x > W + sz or y < -sz or y > H + sz or (alpha is not None and alpha[i] < 0.02): continue
        hw, hh = sz * 0.5, sz * 0.5 * 0.55 * max(0.10, abs(flut[i]))
        ca, sa_ = math.cos(ang[i]), math.sin(ang[i])
        pts = np.array([[x + ca * dx - sa_ * dy, y + sa_ * dx + ca * dy] for dx, dy in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))], np.float32)
        bright = 0.60 + 0.40 * abs(flut[i]) + (0.45 if abs(flut[i]) > 0.97 else 0.0)
        col = np.clip(CONF_COLS[cols[i]] * bright, 0, 1); a8 = int(255 * (1.0 if alpha is None else alpha[i]))
        L = 1 if (blur_big and sz > 70) else 0
        cv2.fillConvexPoly(lay[L], (pts * 4).astype(np.int32), tuple(int(c * 255) for c in col), cv2.LINE_AA, 2)
        cv2.fillConvexPoly(al[L], (pts * 4).astype(np.int32), a8, cv2.LINE_AA, 2)
    o = out
    for L, bl in ((0, 0.0), (1, 3.0)):
        if not al[L].any(): continue
        Lf = lay[L].astype(np.float32) / 255; Af = al[L].astype(np.float32) / 255
        if bl: Lf = cv2.GaussianBlur(Lf, (0, 0), bl); Af = cv2.GaussianBlur(Af, (0, 0), bl)
        o = o * (1 - Af[..., None]) + Lf * Af[..., None]
    return o

def name_loop(out, f, s):
    t = f / FPS; e = t / E.HB
    if e < NL_G0 - 1.5: return out
    d = name_targets(); tg0, tg1, tb, T = E.th(NL_G0), E.th(NL_G1), E.th(NL_B), E.DUR
    # the pieces fall in from above the frame, then gather into the letters (staggered, with a curl)
    tf = t - (tg0 - 1.0)
    fx_ = d["x0"] - d["side"] * d["vf"] * 0.55 * tf; fy_ = d["y0"] + 60 * np.sin(1.7 * tf + d["b0"])     # drifting in from the sides
    w = np.clip((t - tg0 - d["delay"]) / (tg1 - tg0 - 0.28), 0, 1); we = w * w * (3 - 2 * w)
    curl = np.sin(np.pi * we) * 90 * d["sw"]
    px = fx_ + (d["tx"] - fx_) * we + curl; py = fy_ + (d["ty"] - fy_) * we
    ang = np.radians(d["a0"] + d["wa"] * t * (1 - 0.75 * we)); flut = np.cos(d["b0"] + d["wb"] * t)
    size = d["size"].copy(); alpha = None
    plate = out
    hold = smooth((t - tg0 - 0.3) / 0.5) * (1 - smooth((t - tb) / 0.25))
    if hold > 0:                                                                          # the parade steps back so the name reads
        soft = cv2.GaussianBlur(cv2.resize(out, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 2.5)
        plate = out * (1 - 0.45 * hold) + cv2.resize(soft, (W, H)) * (0.45 * hold)
        plate = plate * (1 - 0.30 * hold)
    if t >= tb:                                                                           # the burst: toward the lens and out
        b = clamp((t - tb) / (T - tb - 0.06), 0, 1); be = b ** 1.6
        dx, dy = d["tx"] - W / 2, d["ty"] - 1110
        px = d["tx"] + dx * 3.2 * be * d["bv"] + d["sw"] * 160 * be; py = d["ty"] + np.abs(dy) * 3.0 * be * d["bv"] + 260 * be
        size = d["size"] * (1 + 9 * be * d["bv"])
        alpha = np.clip(1 - (b - 0.55) / 0.40, 0, 1) * np.ones_like(size)
        wz = smooth((t - tb - 0.02) / 0.30)                                               # under it: frame 0
        if wz > 0: plate = plate * (1 - wz) + frame0_plate() * wz
    o = draw_pieces(plate, px, py, size, ang, flut, d["col"], alpha)
    if t > T - 0.08: o = o * 0 + frame0_plate() if t > T - 1.5 / FPS else o                 # the last frame is frame 0's picture
    return np.clip(o, 0, 1)

def render(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin")
    out, person = base107(s, f)
    out = text107(out, f, s, True)
    if tin in TR2 and k < TR2[tin][2] and P is not None:
        out = TR2[tin][0](edge107(P, "last"), out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, edge107(n_, "first"), kn, f, s, n_)
    if s.get("tout") == "name_loop": out = name_loop(out, f, s)
    out = beat_fx(out, f)
    out = text107(out, f, s, False)
    out = flash_governor(out)
    return (np.clip(finish107(out, f, s), 0, 1) * 255 + 0.5).astype(np.uint8)

# ============================================================================ v107 rev 3 (owner notes; overrides above)
# ---- DEXTER on the 16th grid: each letter lands ON its hit (the platen comes down in the 3 frames before) -------------
STAMP_DROP = 3
def strip_canvas(t, stamps):
    """the strip (rgba, its own pixel space) with the letters stamped by time t."""
    base = strip_tex().copy(); inks, xs = _ST["lets"]; h, w = base.shape[:2]
    for (wd, tw), m, xc in zip(stamps, inks, xs):
        k = (t - tw) * FPS + STAMP_DROP
        if k < 0: continue
        v = clamp(k / STAMP_DROP, 0, 1)
        if v < 1:                                                                          # the stamp coming down
            sc = 1.6 - 0.6 * ein(v, 2.0); mm = cv2.resize(m, None, fx=sc, fy=sc); mm = cv2.GaussianBlur(mm, (0, 0), 0.1 + 4 * (1 - v)) * (0.35 + 0.65 * v)
        else: mm = m
        hh, ww = mm.shape; x0 = int(xc - ww / 2); y0 = int(h / 2 - hh / 2 + 6)
        ys, xs_ = slice(max(0, y0), min(h, y0 + hh)), slice(max(0, x0), min(w, x0 + ww))
        sub = mm[ys.start - y0:ys.stop - y0, xs_.start - x0:xs_.stop - x0]
        if v >= 1:                                                                         # the deboss: pressed into the paper
            dm = cv2.GaussianBlur(sub, (0, 0), 2.0)
            sh = np.clip(np.roll(dm, 3, 0) - dm, 0, 1) * 0.35; hl = np.clip(np.roll(dm, -3, 0) - dm, 0, 1) * 0.10
            base[ys, xs_, :3] *= (1 - sh)[..., None]; base[ys, xs_, :3] += hl[..., None]
            sub = np.clip(sub * (1 + 0.10 * math.exp(-(k - STAMP_DROP) / 3)), 0, 1)           # ink spreads at the hit, then settles
        base[ys, xs_, :3] = base[ys, xs_, :3] * (1 - sub[..., None]) + INK * sub[..., None]
    return base

def text_stamp(out, f, tx):
    t = f / FPS; stamps = [(w, wt) for w, wt, _ in tx["words"]]
    t_in = next(wt for tx_ in E.TEXT if tx_["style"] == "cap" for w_, wt, _ in tx_["words"] if w_ == "CAPS") - 0.02   # it slaps on with "CAPS"
    t_cut = E.th(48); t_end = t_cut + 0.80
    if t < t_in or t > t_end: return out
    rgba = strip_canvas(min(t, t_cut + 0.2), stamps)
    k = (t - t_in) * FPS; v = clamp(k / 5.0, 0, 1)
    sc = 1.28 - 0.28 * eout(v, 3) + (0.02 * math.sin(k * 0.9) * math.exp(-k / 6) if v >= 1 else 0)
    cx, cy = STRIP_C; rot = STRIP_ROT; a = min(1.0, k / 3.0); shake = 0.0
    for _, tw in stamps:                                                                   # each hit shakes the strip
        dk = (t - tw) * FPS
        if 0 <= dk < 8: shake = max(shake, 5 * math.exp(-dk / 2.5))
    cy += shake * math.sin(f * 2.1)
    if t > t_cut - 0.02:                                                                   # it flies into the sky onto the banner
        w_ = smooth((t - t_cut + 0.02) / 0.45)
        (bx, by), bs, br = banner_target()
        cx, cy = cx + (bx - cx) * w_, cy + (by - cy) * w_; sc = sc + (bs - sc) * w_; rot = rot + (br - rot) * w_
        a = a * (1 - smooth((t - t_cut - 0.42) / 0.36))
    return put_strip(out, rgba, cx, cy, sc, rot, a, 0.45 * (1 - smooth((t - t_cut) / 0.3)))

# ---- SPATTER ANALYSIS (new graphic, the kill table): blood spatters across the lens, strings run back from every
# ---- stain along its flight line and lock on the beat at the POINT OF ORIGIN, where his face is about to appear --------
SP_F0, SP_STR, SP_LOCK = 99, 106, 124                                                      # the spatter, the strings, the lock (e6)
BLOOD_HI = np.array([0.08, 0.06, 0.66], np.float32); BLOOD_LO = np.array([0.02, 0.01, 0.20], np.float32)
STRING_C = np.array([0.17, 0.16, 0.93], np.float32)
_SP = {}
def sp_origin():
    if "o" not in _SP:
        sb = [s_ for s_ in SHOTS if s_["n"] == "shh"][0]; fs = face_scr(sb, sb["f0"])
        _SP["o"] = (float(fs[0]), float(fs[1])) if fs else (W / 2, 640.0)
    return _SP["o"]

def sp_geom():
    if "g" in _SP: return _SP["g"]
    ox, oy = sp_origin(); rng = np.random.default_rng(1077)
    spec = [(-160, 430, 24, 28), (-125, 360, 18, 40), (-75, 440, 22, 24), (-35, 330, 26, 35), (-5, 420, 16, 20),
            (30, 360, 20, 46), (70, 310, 15, 38), (110, 330, 14, 50), (150, 300, 17, 33), (175, 380, 21, 22)]
    drops = []
    for i, (th_, r, w, al) in enumerate(spec):
        w = w * 1.7; a = math.radians(th_); ux, uy = math.cos(a), math.sin(a); L = w / math.sin(math.radians(al))
        sats = list(zip(rng.uniform(1.15, 2.0, 3) * L, rng.uniform(2.6, 6.0, 3), rng.uniform(-0.25, 0.25, 3)))
        drops.append(dict(x=ox + r * ux, y=oy + r * uy, ux=ux, uy=uy, w=w, L=L, al=al, sats=sats,
                          t=SP_F0 + int(rng.integers(0, 6)), s=SP_STR + 2 * i, lab=i in (0, 3, 5, 8)))
    ang = rng.uniform(-math.pi, math.pi, 70); rr = rng.uniform(170, 560, 70)
    mist = [(ox + q * math.cos(a), oy + q * math.sin(a), rad, SP_F0 + int(dt)) for a, q, rad, dt in
            zip(ang, rr, rng.uniform(1.8, 4.8, 70), rng.integers(0, 7, 70)) if oy + q * math.sin(a) < 1200]
    _SP["g"] = (drops, mist); return _SP["g"]

def sp_text(key, txt, size, col):
    if key not in _SP: _SP[key] = shadowed(text_mask(txt, F_MONO, size), col, blur=4, sa=0.8)
    return _SP[key]

def paste_rgba(out, rg, x, y, a=1.0):
    h, w = rg.shape[:2]; x0, y0 = int(round(x)), int(round(y))
    ys, xs = slice(max(0, y0), min(H, y0 + h)), slice(max(0, x0), min(W, x0 + w))
    if ys.stop <= ys.start or xs.stop <= xs.start: return out
    sub = rg[ys.start - y0:ys.stop - y0, xs.start - x0:xs.stop - x0]; al = sub[..., 3:4] * a
    out[ys, xs] = out[ys, xs] * (1 - al) + sub[..., :3] * al
    return out

SS = 16                                                                                    # cv2 sub-pixel shift (4 bits)
def P_(x, y): return (int(round(x * SS)), int(round(y * SS)))

def spatter_fx(img, f):
    if f < SP_F0: return img
    drops, mist = sp_geom(); ox, oy = sp_origin(); out = img.copy()
    # the blood on the lens: elongated stains (round head, body along the flight line, a tapering tail), satellites, mist
    m = np.zeros((H, W), np.uint8)
    for d in drops:
        if f < d["t"]: continue
        g = eout(clamp((f - d["t"] + 1) / 3.0, 0, 1), 2)
        L = d["w"] + (d["L"] - d["w"]) * g; ang = math.degrees(math.atan2(d["uy"], d["ux"]))
        cx, cy = d["x"] + d["ux"] * (L / 2 - d["w"] / 2), d["y"] + d["uy"] * (L / 2 - d["w"] / 2)
        cv2.ellipse(m, P_(cx, cy), P_(L / 2, d["w"] / 2), ang, 0, 360, 255, -1, cv2.LINE_AA, 4)
        tx_, ty_ = d["x"] + d["ux"] * (L - d["w"] * 0.6), d["y"] + d["uy"] * (L - d["w"] * 0.6)
        ex, ey = tx_ + d["ux"] * 0.55 * L * g, ty_ + d["uy"] * 0.55 * L * g; px_, py_ = -d["uy"], d["ux"]; hw = d["w"] * 0.30
        tri = np.array([P_(tx_ + px_ * hw, ty_ + py_ * hw), P_(tx_ - px_ * hw, ty_ - py_ * hw), P_(ex, ey)], np.int32)
        cv2.fillConvexPoly(m, tri, 255, cv2.LINE_AA, 4)
        for dd, rad, side in d["sats"]:
            sx, sy = d["x"] + (d["ux"] + side * px_) * dd * g, d["y"] + (d["uy"] + side * py_) * dd * g
            cv2.circle(m, P_(sx, sy), int(rad * SS), 255, -1, cv2.LINE_AA, 4)
    for x, y, rad, t_ in mist:
        if f >= t_: cv2.circle(m, P_(x, y), int(rad * SS), 255, -1, cv2.LINE_AA, 4)
    M = m.astype(np.float32) / 255
    inner = cv2.GaussianBlur(M, (0, 0), 3.0)
    col = BLOOD_LO + (BLOOD_HI - BLOOD_LO) * np.clip(inner * 1.3, 0, 1)[..., None]
    hgt = cv2.GaussianBlur(M, (0, 0), 2.2); gx = cv2.Sobel(hgt, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(hgt, cv2.CV_32F, 0, 1, ksize=3)
    spec = np.clip((-gx * 0.55 - gy * 0.85) * 2.4, 0, 1) ** 2 * M * 0.75
    out = out * (1 - M[..., None]) + col * M[..., None] + spec[..., None] * PAPER
    # the strings: taut red string from each stain's head back along its flight line (a pin at the stain)
    sm = np.zeros((H, W), np.uint8); sh = np.zeros((H, W), np.uint8); pins = []
    for d in drops:
        if f < d["s"]: continue
        p = eout(clamp((f - d["s"]) / 9.0, 0, 1), 2.2)
        ex, ey = d["x"] + (ox - d["x"]) * p, d["y"] + (oy - d["y"]) * p
        cv2.line(sm, P_(d["x"], d["y"]), P_(ex, ey), 255, 5, cv2.LINE_AA, 4)
        cv2.line(sh, P_(d["x"] + 4, d["y"] + 5), P_(ex + 4, ey + 5), 255, 5, cv2.LINE_AA, 4)
        pins.append(d)
    if pins:
        S_ = cv2.GaussianBlur(sh.astype(np.float32) / 255, (0, 0), 1.6) * 0.45
        out = out * (1 - S_[..., None])
        Sm = sm.astype(np.float32) / 255
        out = out * (1 - Sm[..., None]) + STRING_C * Sm[..., None]
        for d in pins:
            cv2.circle(out, P_(d["x"], d["y"]), 10 * SS, tuple(float(v) for v in INK), -1, cv2.LINE_AA, 4)
            cv2.circle(out, P_(d["x"] - 3, d["y"] - 3), 3 * SS, tuple(float(v) for v in PAPER), -1, cv2.LINE_AA, 4)
            if d["lab"]:                                                                   # the impact angle, read off the stain
                rg = sp_text(f"al{d['al']}", f"{d['al']}\u00b0", 46, PAPER)
                px_, py_ = -d["uy"], d["ux"]; side = 1 if (d["x"] + px_ * 40) > ox else -1
                lx = d["x"] + side * px_ * (d["w"] + 46) - rg.shape[1] / 2; ly = d["y"] + side * py_ * (d["w"] + 46) - rg.shape[0] / 2
                out = paste_rgba(out, rg, lx, ly, smooth((f - d["s"] - 2) / 5.0))
    # the lock: a ring with a crosshair at the point of origin, a pulse, and the tag
    if f >= SP_LOCK:
        q = f - SP_LOCK; sc = eout(clamp(q / 6.0, 0, 1), 3); r = 48 * (1.6 - 0.6 * sc)
        lay = np.zeros((H, W), np.uint8)
        cv2.circle(lay, P_(ox, oy), int(r * SS), 255, 5, cv2.LINE_AA, 4)
        for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            cv2.line(lay, P_(ox + ddx * (r + 8), oy + ddy * (r + 8)), P_(ox + ddx * (r + 32), oy + ddy * (r + 32)), 255, 5, cv2.LINE_AA, 4)
        tgx, tgy = ox + 40, oy - 440
        cv2.line(lay, P_(ox + r * 0.72, oy - r * 0.72), P_(tgx + 30, tgy + 80), 255, 3, cv2.LINE_AA, 4)
        La = lay.astype(np.float32) / 255 * sc
        out = out * (1 - La[..., None]) + PAPER * La[..., None]
        cv2.circle(out, P_(ox, oy), 9 * SS, tuple(float(v) for v in STRING_C), -1, cv2.LINE_AA, 4)
        if q < 12:                                                                         # the pulse
            pr = np.zeros((H, W), np.uint8); cv2.circle(pr, P_(ox, oy), int((r + 70 * eout(q / 12, 2)) * SS), 255, 2, cv2.LINE_AA, 4)
            out = out + (pr.astype(np.float32) / 255 * 0.6 * (1 - q / 12))[..., None] * PAPER
        n = int(clamp((q - 2) * 2.2, 0, 15))
        if n > 0:                                                                          # POINT OF ORIGIN, typed on a paper tag
            txt = "POINT OF ORIGIN"[:n]
            if "tagm" not in _SP: _SP["tagm"] = text_mask("POINT OF ORIGIN", F_MONO, 48)
            rg = shadowed(text_mask(txt, F_MONO, 48), INK, blur=1, sa=0.0)            # padded by 7 px
            tw_, th2 = _SP["tagm"].shape[1] + 28, _SP["tagm"].shape[0] + 18
            x0, y0 = int(tgx), int(tgy)
            out[y0 + 6:y0 + th2 + 6, x0 + 5:x0 + tw_ + 5] *= 0.55                          # the tag's shadow
            out[y0:y0 + th2, x0:x0 + tw_] = PAPER * 0.97
            out[y0 + th2 - 4:y0 + th2, x0:x0 + tw_] = STRING_C                              # a red rule under the type
            out = paste_rgba(out, rg, x0 + 14 - 7, y0 + 9 - 7, 1.0)
    return np.clip(out, 0, 1)

_base107_r2 = base107
def base107(s, f):
    img, person = _base107_r2(s, f)
    if s["n"] == "table": img = spatter_fx(img, f)
    return img, person

# ---- RORSCHACH (the 3 s transition): from the point of origin a blood-ink blot blooms, mirrored about the fold like an
# ---- inkblot card; inside it his face appears mirrored (both of him), the blot floods the frame, the mirrored half of the
# ---- card swings open on the fold and the real shot is underneath. Full frame: no bars, no box. ---------------------------
RO_PRE, RO_POST = 21, 30
RO_BLOBS = [(0, 0, 95), (0, 110, 70), (0, -120, 60), (45, -190, 30), (150, -60, 95), (280, -120, 80), (400, -190, 62),
            (500, -230, 42), (560, -170, 30), (200, 70, 80), (330, 60, 62), (440, 20, 48), (520, -40, 36), (260, 160, 42),
            (390, 140, 34), (55, 210, 34), (70, 270, 20), (610, -110, 18), (150, 300, 14)]
INKB = np.array([0.03, 0.02, 0.24], np.float32)
_RO = {}
def ro_grids():
    if "g" not in _RO:
        ox, oy = sp_origin(); rng = np.random.default_rng(1078)
        X, Y = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
        AX = np.abs(X - ox); DY = Y - oy
        n1 = cv2.resize(rng.random((H // 40 + 2, W // 40 + 2)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
        n2 = cv2.resize(rng.random((H // 10 + 2, W // 10 + 2)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
        nz = 0.6 * n1 + 0.4 * n2
        xi = np.clip(ox + AX, 0, W - 1).astype(np.int32); nz = nz[np.arange(H)[:, None], xi]    # symmetric about the fold
        mx = np.where(X > ox, 2 * ox - X, X).astype(np.float32)                                  # the mirror map
        _RO["g"] = (AX, DY, nz, mx, Y)
    return _RO["g"]

def ro_mask(grow, flood=0.0):
    AX, DY, nz, _, _ = ro_grids(); F = np.zeros((H, W), np.float32)
    for bx, by, r in RO_BLOBS:
        bx, by, r = bx * 0.72, by * 1.25, r * 0.85                                          # a card: it fits the frame
        dist = math.hypot(bx, by); g = eout(clamp((grow - dist / 700 * 0.55) / 0.45, 0, 1), 2.5)
        rr = r * g * (1 + 2.2 * ein(clamp(flood / 0.5, 0, 1), 1.6))
        if rr > 0.5: F += rr * rr / ((AX - bx) ** 2 + (DY - by) ** 2 + 1.0)
    if flood > 0:
        rc = 1450 * eout(clamp(flood / 0.5, 0, 1), 1.8); F += rc * rc / (AX ** 2 + DY ** 2 + 1.0)
    F = F * (0.86 + 0.28 * nz)
    return cv2.GaussianBlur((F > 1.0).astype(np.float32), (0, 0), 1.1)

def mirror(img):
    _, _, _, mx, Y = ro_grids()
    return cv2.remap(img, mx, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def ink_comp(A, content, m, clear):
    inner = cv2.GaussianBlur(m, (0, 0), 14); rim = np.clip((m - inner) * 3.2, 0, 1)
    dens = np.maximum(rim, 1 - clear) * m
    ins = content * (1 - 0.92 * dens[..., None]) + INKB * 0.92 * dens[..., None]
    hgt = cv2.GaussianBlur(m, (0, 0), 5.0); gx = cv2.Sobel(hgt, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(hgt, cv2.CV_32F, 0, 1, ksize=3)
    spec = np.clip((-gx * 0.55 - gy * 0.85) * 5.0, 0, 1) ** 2 * m * 0.55
    halo = np.clip(cv2.GaussianBlur(m, (0, 0), 3.0) - m, 0, 1) * 0.7                       # the ink bleeds into the paper
    out = A * (1 - halo[..., None]) * (1 - m[..., None]) + ins * m[..., None] + spec[..., None] * PAPER
    return np.clip(out, 0, 1)

def unfold(Bm, B, phi):
    """the mirrored half of the card (right of the fold) swings away on the fold; the real shot is underneath."""
    ox, _ = sp_origin(); D = 1700.0; s = W - ox
    if phi >= math.pi / 2 - 1e-3: return B
    Z = s * math.sin(phi); k = D / (D + Z); xf = ox + s * math.cos(phi) * k
    src = np.float32([[ox, 0], [W, 0], [W, H], [ox, H]]); dst = np.float32([[ox, 0], [xf, H / 2 - H / 2 * k], [xf, H / 2 + H / 2 * k], [ox, H]])
    Mp = cv2.getPerspectiveTransform(src, dst)
    pg = cv2.warpPerspective(Bm, Mp, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    pm = np.zeros((H, W), np.float32); pm[:, int(ox):] = 1
    pm = cv2.warpPerspective(pm, Mp, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    shade = 1 - 0.55 * math.sin(phi); pm = pm * (1 - smooth((phi - math.radians(55)) / math.radians(30)))   # gone before it is edge-on
    shadow = np.clip(1 - np.abs(np.arange(W, dtype=np.float32) - xf) / 160, 0, 1) * 0.35 * math.sin(phi)   # the card's shadow
    base = B * (1 - shadow[None, :, None] * (np.arange(W) > ox)[None, :, None])
    return np.clip(base * (1 - pm[..., None]) + pg * shade * pm[..., None], 0, 1)

def rorschach(A, B, j, f, sa, sb, pre=RO_PRE, post=RO_POST):
    if j < 0:
        u = (j + pre + 1) / pre
        m = ro_mask(u); return ink_comp(A, mirror(B), m, smooth((u - 0.10) / 0.55))
    v = (j + 1) / post; Bm = mirror(B)
    if v < 0.5:
        m = ro_mask(1.0, v); return ink_comp(A, Bm, m, 1.0)
    return unfold(Bm, B, math.pi / 2 * smooth((v - 0.5) / 0.45))
TR2["rorschach"] = (rorschach, RO_PRE, RO_POST)

# ============================================================================ v107 rev 4 (owner notes; overrides above)
# ---- the POINT OF ORIGIN piece is gone: the kill table plays clean and cuts to "shh" on the downbeat ------------------
base107 = _base107_r2                                                                       # no spatter analysis
def beat_phase(f):                                                                          # the beat camera punches the e8 cut again
    e = f / FPS / E.HB; ph = (e % 2) * E.HB; bi = int(e // 2)
    hook = (E.E_BEAT <= e < 54) and not (19 <= e < 23) and not (24 <= e < 28.5) and not (47 <= e < 50)
    return ph, bi, hook, False

# ---- PAGE TURN ("shh" -> the lab, replaces the redaction boxes): the frame is a page of the paper. It lifts at the
# ---- bottom-right corner and rolls over a cylinder; its back is newsprint with the picture showing through; it lies
# ---- over itself as it turns, casts a shadow on the lab shot underneath, and clears off the top-left corner. ------------
PT_PRE, PT_POST = 14, 12
_PT = {}
def pt_back():
    """the back of the page: newsprint (three columns of body type, rules) on the paper."""
    if "b" in _PT: return _PT["b"]
    paper, _, _ = page_layers(); ink = np.zeros((H, W), np.float32); rng = np.random.default_rng(1079)
    words = ("residents were told to lock their doors as the task force widened the search along the bay and the "
             "department asked anyone who saw a boat leave the marina after dark to call the tip line divers recovered "
             "more bags from the water on monday and the medical examiner said the work was careful and practised").split()
    cols = [(60, 352), (394, 686), (728, 1020)]
    for ci, (x0, x1) in enumerate(cols):
        y = 90 + (60 if ci == 1 else 0); wi = int(rng.integers(len(words)))
        while y < H - 90:
            if rng.random() < 0.05:
                m = text_mask(" ".join(words[wi % len(words):wi % len(words) + 3]).upper(), F_XB, 34); put_mask(ink, squeeze(m, min(1.0, (x1 - x0) / m.shape[1])), x0, y)
                y += 58; wi += 3; continue
            line = []; wsum = 0
            while True:
                w = words[wi % len(words)]; wi += 1; tw = len(w) * 11 + 9
                if wsum + tw > (x1 - x0): break
                line.append(w); wsum += tw
            m = text_mask(" ".join(line), F_BODY, 21); put_mask(ink, squeeze(m, min(1.0, (x1 - x0) / m.shape[1])), x0, y)
            y += 29
        if ci < 2: cv2.line(ink, (x1 + 21, 90), (x1 + 21, H - 90), 0.7, 1)
    cv2.line(ink, (60, 64), (W - 60, 64), 1.0, 2)
    _PT["b"] = (paper, ink); return _PT["b"]

def page_turn107(A, B, j, f, sa, sb, pre=PT_PRE, post=PT_POST):
    u = clamp((j + pre + 0.5) / (pre + post), 0, 1)
    d = np.array([-0.62, -0.785], np.float32); d /= np.linalg.norm(d)                       # from the bottom-right corner to the top-left
    s_ = (_GX - W) * d[0] + (_GY - H) * d[1]; smax = float(W * -d[0] + H * -d[1])
    R = 60 + 70 * u; c = (smax + 1.7 * R + 60) * (0.5 - 0.5 * math.cos(math.pi * u ** 1.15))  # the roll line, easing in and out
    def src(sig):                                                                            # screen point -> the page point at sigma
        return (_GX + (sig - s_) * d[0]).astype(np.float32), (_GY + (sig - s_) * d[1]).astype(np.float32)
    def inside(mx, my): return (mx >= 0) & (mx <= W - 1) & (my >= 0) & (my <= H - 1)
    paper, ink = pt_back()
    def back_at(mx, my, shade):
        pa = cv2.remap(paper, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        ik = cv2.remap(ink, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)[..., None]
        thru = cv2.remap(A, (W - 1 - mx).astype(np.float32), my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)   # show-through, mirrored
        b = pa * (1 - 0.10 * (1 - lum(thru))[..., None]) * (1 - ik * 0.88) + INK * ik * 0.88
        return b * shade[..., None]
    o = B.copy()
    # 1. the flat page (front) beyond the roll line
    flat = s_ > c
    o = np.where(flat[..., None], A, o)
    # 2. the rising quarter of the roll (front side, seen foreshortened)
    cyl = (s_ <= c) & (s_ >= c - R)
    th1 = np.arcsin(np.clip((c - s_) / R, 0, 1)); mx, my = src(c - R * th1); ok1 = cyl & inside(mx, my)
    fr = cv2.remap(A, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT) * (0.55 + 0.45 * np.cos(th1))[..., None]
    o = np.where(ok1[..., None], fr, o)
    # 3. the top half of the roll (its back, on top of the rising quarter)
    th2 = np.pi - th1; mx2, my2 = src(c - R * th2); ok2 = cyl & inside(mx2, my2)
    bk = back_at(mx2, my2, (0.80 + 0.22 * np.sin(th2)).astype(np.float32))
    o = np.where(ok2[..., None], bk, o)
    # 4. the turned-over part lying flat on top of the page (its back), beyond the roll line
    sig3 = 2 * c - np.pi * R - s_; mx3, my3 = src(sig3); ok3 = flat & (sig3 <= c - np.pi * R) & inside(mx3, my3)
    bk3 = back_at(mx3, my3, np.full((H, W), 0.93, np.float32))
    o = np.where(ok3[..., None], bk3, o)
    # shadows: the roll on the lab shot underneath, the flap's edge on the page
    uncov = s_ < c - R
    sh1 = np.exp(-np.clip((c - R) - s_, 0, None) / 46) * uncov * 0.55 * (c > 2)
    edge3 = ok3.astype(np.float32); sh2 = np.clip(cv2.GaussianBlur(edge3, (0, 0), 14) - edge3, 0, 1) * flat * (~ok3) * 0.9
    o = o * (1 - sh1[..., None]) * (1 - sh2[..., None])
    return np.clip(o, 0, 1)
TR2["page_turn107"] = (page_turn107, PT_PRE, PT_POST)

# ---- the colour split on the beat hits clamps at the frame edge (np.roll wrapped it: a cyan / magenta line on the edges)
def _shift_edge(ch, d, axis):
    if d == 0: return ch
    o = np.empty_like(ch); n = ch.shape[axis]; d = max(-n + 1, min(n - 1, d))
    src = [slice(None)] * ch.ndim; dst = [slice(None)] * ch.ndim; pad = [slice(None)] * ch.ndim; edge = [slice(None)] * ch.ndim
    if d > 0:
        dst[axis], src[axis], pad[axis], edge[axis] = slice(d, None), slice(0, n - d), slice(0, d), slice(0, 1)
    else:
        dst[axis], src[axis], pad[axis], edge[axis] = slice(0, n + d), slice(-d, None), slice(n + d, None), slice(n - 1, n)
    o[tuple(dst)] = ch[tuple(src)]; o[tuple(pad)] = ch[tuple(edge)]
    return o

def rgb_split(img, d, vertical=False):
    d = int(round(d))
    if d == 0: return img
    o = img.copy(); ax = 0 if vertical else 1
    o[..., 2] = _shift_edge(img[..., 2], d, ax); o[..., 0] = _shift_edge(img[..., 0], -d, ax)
    return o


# ============================================================================ v108 — DOOMSDAY (Dexter × MF DOOM "Doomsday")
# The edit's own pieces (last definition wins). UNDER THE SURFACE / BORN IN BLOOD; no text anywhere (the owner's brief).
#   LOOKS     surface108 (the mask: warm, bleached pastel Miami) | under108 (from the peel: cold steel and teal, deep
#             blacks, only blood red survives). finish108: fine grain, a soft vignette, a little halation in the light.
#   SURFACE   the owner's concept: clear kill-room plastic is pulled over the calm picture, stretches (its folds bend
#             the picture), and peels away diagonally (slow, then it snaps) to the darker Dexter underneath.
#   SPECIMEN  the owner's concept (the signature, on the drop): a glass slide with a drop of blood crosses his face and
#             magnifies his eye; the next shot appears inside the glass, then the slide comes to the lens and fills it.
#   FROST     "back where my brother went": frost grows over the lens from the edges (the Ice Truck Killer), the picture
#             cools under it, and it thaws from the centre onto him strapped to Brian's table.
#   LAST DROP the loop: he looks up; one drop of blood falls toward the lens; frame 0's smile is inside it; it fills the
#             frame on the last frame (the hero object: the slide's drop, twice).
_L108 = {}
def lut108(kind):
    if kind not in _L108:
        x = np.linspace(0, 1, 1024, dtype=np.float32)
        if kind == "surface108":
            ys = PchipInterpolator([0, .05, .20, .50, .80, .95, 1], [0.060, 0.082, 0.215, 0.530, 0.820, 0.925, 0.950])(x)
        else:
            ys = PchipInterpolator([0, .05, .20, .50, .80, .95, 1], [0.010, 0.020, 0.115, 0.425, 0.745, 0.875, 0.905])(x)
        _L108[kind] = (x, ys.astype(np.float32))
    return _L108[kind]

WARM108 = np.array([0.93, 0.99, 1.04], np.float32)          # BGR gains for the mask
PASTEL = np.array([0.86, 0.91, 0.98], np.float32)           # BGR: the cream-pink of the light by day
CRIMSON = np.array([0.10, 0.06, 0.78], np.float32)          # BGR: blood
TEAL = np.array([0.040, 0.026, -0.010], np.float32)         # BGR: added in the shadows under the surface
_grade_pre108 = grade
def grade(img, s, f):
    lk = s.get("look")
    if lk not in ("surface108", "under108"): return _grade_pre108(img, s, f)
    g, gains = corr9(s); ev = s.get("ev") or 0; lx, ly = lut108(lk)
    gains = tuple(float(a * b) for a, b in zip(gains, WARM108 if lk == "surface108" else (1.0, 1.0, 1.0)))
    if in_unit(img):
        x = apply_lut3(img, tone_lut((lk, s["n"], ev, float(g), gains), gains, g, ev, lx, ly))
    else:
        x = np.interp(np.clip(np.clip(img * np.array(gains, np.float32), 0, 1) ** g * 2 ** ev, 0, 1), lx, ly).astype(np.float32)
    Bc, Gc, Rc = (np.ascontiguousarray(x[..., c]) for c in range(3))
    L = Bc * 0.114 + Gc * 0.587 + Rc * 0.299
    o = np.empty(x.shape, np.float32)
    if lk == "surface108":
        hi = np.clip((L - 0.50) * 1.6, 0, 1)
        for ch, P in enumerate((Bc, Gc, Rc)):
            v = L + (P - L) * 0.80
            v *= 1 + hi * (PASTEL[ch] / 0.98 - 1) * 0.8
            o[..., ch] = v
    else:
        red = np.clip((Rc - 1.85 * np.maximum(Gc, Bc) - s.get("redthr", 0.05)) * 3.0, 0, 1)          # blood, not skin
        skin = np.clip((Rc - Bc) * 1.8, 0, 1) * (1 - red)
        sat = 0.26 + 0.14 * skin + 0.95 * red
        sh = (1 - L) ** 2
        for ch, P in enumerate((Bc, Gc, Rc)):
            v = L + (P - L) * sat
            v += sh * TEAL[ch]
            v += red * L * (CRIMSON[ch] / 0.78 - 1) * 0.30
            o[..., ch] = v
    return np.clip(o, 0, 1, out=o)

def finish108(out, f, s=None):
    L = lum(out)
    q = cv2.resize(np.clip(L - 0.80, 0, 1), (W // 8, H // 8), interpolation=cv2.INTER_AREA)
    hal = cv2.resize(cv2.GaussianBlur(q, (0, 0), 6), (W, H), interpolation=cv2.INTER_LINEAR)
    g = grain(f, 0.012)[..., 0]; v = VIG[..., 0]
    o = np.empty(out.shape, np.float32)
    for ch, k in enumerate((0.07, 0.08, 0.09)):                                                # a soft, near-neutral halation
        oc = o[..., ch]; np.copyto(oc, out[..., ch]); oc += hal * k; oc *= v; oc += g
    return np.clip(o, 0, 1, out=o)

# ---- the beat camera: from e2 to e64; it rests through SURFACE, the drop-out and SPECIMEN, the frost, and the ending ----
def beat_phase(f):
    e = f / FPS / E.HB; ph = (e % 2) * E.HB; bi = int(e // 2)
    hook = (E.E_BEAT <= e < 64) and not (10.5 <= e < 14.5) and not (18 <= e < 23.5) and not (26.5 <= e < 29.5)
    return ph, bi, hook, False

def base108(s, f):
    return base12(s, f)

_B108 = {}
def edge108(S_, which):
    key = (S_["n"], which)
    if key not in _B108:
        if len(_B108) > 6: _B108.clear()
        _B108[key] = base108(S_, S_["f0"] if which == "first" else S_["f1"] - 1)[0]
    return _B108[key]

def frame0_plate108():
    if "f0" not in _LV: _LV["f0"] = base108(SHOTS[0], SHOTS[0]["f0"])[0]
    return _LV["f0"]

def _blur(img, sig):
    return img if sig < 0.3 else cv2.GaussianBlur(img, (0, 0), sig)

def _remap(img, mx, my, border=cv2.BORDER_REFLECT):
    return cv2.remap(img, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_LINEAR, borderMode=border)

# ---- the drop of blood (the hero object): a lit, refracting dome or a falling bead ----------------------------------
R_FULL = 0.5 * math.hypot(W, H) + 40
def blood_drop108(out, cx, cy, r, behind=None, inside=None, inside_w=0.0, stretch=1.0, tint=1.0, light=(-0.55, -0.70), gloss=1.0):
    """draws a drop of blood of radius r (px) centred at (cx, cy) on out (in place, returns out).
    behind: the picture the drop refracts (default out); inside / inside_w: a picture seen *through* the drop (the
    lens image), blended in by inside_w; stretch > 1 elongates it vertically (a falling drop); tint 0..1 how much blood
    absorbs (1 = deep crimson)."""
    if r < 1.0: return out
    R = int(r * stretch * 1.25) + 4
    x0, x1 = max(0, int(cx - R)), min(W, int(cx + R) + 1); y0, y1 = max(0, int(cy - R * 1.0)), min(H, int(cy + R) + 1)
    if x1 <= x0 or y1 <= y0: return out
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    dx = (xx - cx) / r; dy = (yy - cy) / (r * stretch)
    rho2 = dx * dx + dy * dy
    m = np.clip((1.0 - np.sqrt(rho2)) * r * 0.9 + 0.5, 0, 1)                                    # anti-aliased edge
    if m.max() <= 0: return out
    z = np.sqrt(np.clip(1 - rho2, 0, 1))
    src = behind if behind is not None else out
    k = 0.85                                                                                    # a lens: the scene behind, inverted and small
    sx = cx - dx * r * k * (0.35 + 0.65 * z); sy = cy - dy * r * k * (0.35 + 0.65 * z)
    ref = _remap(src, sx, sy)
    if inside is not None and inside_w > 0:
        # the lens image of `inside`: the whole picture, upright, squeezed into the drop (a fish-eye at the rim); it
        # relaxes to exactly 1:1 when the drop's radius reaches R_FULL (it then covers the frame)
        Sc = max(1.0, R_FULL / r)
        bulge = clamp(1 - (W * 0.5) / (r * Sc), 0, 0.62) * (1 - smooth((r - 0.80 * R_FULL) / (0.18 * R_FULL)))   # the rim maps inside frame 0
        ux = W / 2 + (xx - cx) * Sc * (1 - bulge * (1 - z)); uy = H / 2 + (yy - cy) * Sc * (1 - bulge * (1 - z))
        ins = _remap(inside, ux, uy, cv2.BORDER_REPLICATE)
        oob = np.clip(np.maximum(np.maximum(-ux, ux - (W - 1)), np.maximum(-uy, uy - (H - 1))) / 40.0, 0, 1)   # outside frame 0:
        soft = _remap(_blur_small(inside), ux, uy, cv2.BORDER_REPLICATE)                          # its blurred edge, carried out
        ins = ins * (1 - oob[..., None]) + soft * oob[..., None]
        ref = ref * (1 - inside_w) + ins * inside_w
    thick = z * (0.55 + 0.45 * z)
    sig = np.array([2.6, 2.4, 0.35], np.float32) * tint
    T = np.exp(-sig * thick[..., None] * 1.5)
    col = ref * T * (1 - 0.25 * tint) + CRIMSON * (1 - T[..., 2:3]) * 0.55 * tint
    nx, ny = dx, dy; nz = z + 1e-3; nn = np.sqrt(nx * nx + ny * ny + nz * nz)
    lv = np.array([light[0], light[1], 0.62], np.float32); lv /= np.linalg.norm(lv)
    hv = lv + np.array([0, 0, 1], np.float32); hv /= np.linalg.norm(hv)
    ndh = np.clip((nx * hv[0] + ny * hv[1] + nz * hv[2]) / nn, 0, 1)
    rs = clamp(110.0 / max(r, 1.0), 0.12, 1.0)                                                  # a big (near) drop keeps a small, sharp glint
    spec = ndh ** (140 / rs) * (0.45 + 0.5 * rs)
    fres = np.clip(1 - z, 0, 1) ** 3 * 0.22 * (0.4 + 0.6 * np.clip(-(dx * lv[0] + dy * lv[1]), 0, 1))
    caus = np.exp(-(((dx - 0.35) / 0.32) ** 2 + ((dy - 0.42) / 0.22) ** 2)) * 0.28 * tint   # light focused through the bead
    rim = np.exp(-((np.sqrt(rho2) - 0.97) / 0.035) ** 2) * 0.35                              # the dark meniscus at the edge
    col = col * (1 - rim[..., None] * 0.6 * gloss) + ((spec + fres) * gloss)[..., None] * np.array([0.96, 0.98, 1.0], np.float32)
    col = col + (caus * gloss)[..., None] * np.array([0.10, 0.18, 0.55], np.float32)
    reg = out[y0:y1, x0:x1]
    reg[:] = reg * (1 - m[..., None]) + col * m[..., None]
    return out

# ---- SURFACE: kill-room plastic over the calm picture, stretched, then peeled away diagonally ------------------------
SU_PRE, SU_POST = 26, 16
_SU = {}
def su_fields():
    """quarter-res height fields of the sheet: big curved folds, medium wrinkles, and the taut streaks it is pulled into."""
    if "f" not in _SU:
        h4, w4 = H // 4, W // 4; rng = np.random.default_rng(1081)
        def aniso(sx, sy, ang, seed, pad=160):
            n = np.random.default_rng(seed).standard_normal((h4 + 2 * pad, w4 + 2 * pad)).astype(np.float32)
            n = cv2.GaussianBlur(n, (0, 0), sigmaX=sx, sigmaY=sy)
            M = cv2.getRotationMatrix2D(((w4 + 2 * pad) / 2, (h4 + 2 * pad) / 2), ang, 1.0)
            n = cv2.warpAffine(n, M, (w4 + 2 * pad, h4 + 2 * pad), borderMode=cv2.BORDER_REFLECT)[pad:pad + h4, pad:pad + w4]
            return n / (np.abs(n).max() + 1e-6)
        yy, xx = np.mgrid[0:h4, 0:w4].astype(np.float32)
        folds = np.zeros((h4, w4), np.float32)
        for k in range(8):                                                                          # big curved creases
            a = rng.uniform(-1.25, -0.35); c = rng.uniform(-0.2, 1.4) * w4; wv = rng.uniform(7, 22)
            d = (xx * math.cos(a) + yy * math.sin(a)) - c + rng.uniform(8, 22) * np.sin(yy / rng.uniform(40, 90) + rng.uniform(0, 6))
            folds += rng.uniform(0.5, 1.0) * np.exp(-(d / wv) ** 2) * (1 if k % 2 else -0.7)
        wrink = aniso(20, 7.0, 25, 12) * 0.55 + aniso(26, 8.0, -30, 13) * 0.45                      # crumpled
        taut = aniso(80, 4.0, -42, 14) * 0.7 + aniso(55, 3.0, -38, 15) * 0.5                        # pulled along the diagonal
        lip = aniso(34, 34, 0, 16)                                                                   # the peel front wanders
        dg = ((xx / w4) + (yy / h4)) / 2                                                            # 0 top-left .. 1 bottom-right
        _SU["f"] = (folds, wrink, taut, lip, dg, xx, yy)
    return _SU["f"]

def surface(A, B, j, f, sa, sb, pre=SU_PRE, post=SU_POST):
    q = (j + pre + 0.5) / (pre + post)
    folds, wrink, taut, lip, dg, xx, yy = su_fields(); h4, w4 = folds.shape
    qa = eout(clamp(q / 0.24, 0, 1), 2.2)                                                        # the sheet is pulled over
    tens = smooth((q - 0.18) / 0.34)                                                             # it stretches
    pp = clamp((q - 0.46) / 0.52, 0, 1); peel = 0.16 * pp + 0.84 * pp ** 2.4                    # it peels: slow, then snaps
    # the stretch drags the sheet toward the lower right and pulls its folds long along the diagonal
    st = 1 + 0.22 * tens; dx_, dy_ = -26 * tens, -26 * tens
    ux, uy = (xx + yy) / 2, (xx - yy) / 2                                                        # diagonal axes
    sxp = (ux / st + uy) + dx_; syp = (ux / st - uy) + dy_
    fo = cv2.remap(folds, sxp.astype(np.float32), syp.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    wr = cv2.remap(wrink, sxp.astype(np.float32), syp.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    front_arr = -0.12 + 1.32 * qa; front_peel = 1.12 - 1.32 * peel
    wob = cv2.GaussianBlur(lip, (0, 0), 6) * 0.03
    cov = np.clip((front_arr - dg + wob) * 60, 0, 1) * np.clip((front_peel - dg + wob) * 60, 0, 1)
    if cov.max() < 0.002 and q > 0.5: return B
    dfp = np.clip(front_peel - dg, 0, 1); curl_w = 0.03 + 0.05 * peel
    lift = np.exp(-(dfp / curl_w) ** 2) * (peel > 0)
    hgt = fo * (1.45 - 0.30 * tens) + wr * 0.40 * (1 - 0.6 * tens) + taut * 0.20 * tens
    gy, gx = np.gradient(cv2.GaussianBlur(hgt, (0, 0), 0.8))
    ly_, lx_ = np.gradient(cv2.GaussianBlur(lift, (0, 0), 1.5))
    k_ref = 26.0 + 16.0 * tens                                                                   # px of bend per unit slope (quarter res)
    gx = gx + lx_ * 0.5; gy = gy + ly_ * 0.5
    gxF = cv2.resize(gx, (W, H), interpolation=cv2.INTER_CUBIC); gyF = cv2.resize(gy, (W, H), interpolation=cv2.INTER_CUBIC)
    ef = np.clip(np.minimum(np.minimum(_GX, W - 1 - _GX), np.minimum(_GY, H - 1 - _GY)) / 90.0, 0, 1)   # no bend at the frame edge
    gxF *= ef; gyF *= ef
    covF = cv2.resize(cov, (W, H), interpolation=cv2.INTER_LINEAR)
    plate = A
    under = _remap(plate, _GX + gxF * k_ref * 4, _GY + gyF * k_ref * 4)
    under[..., 2] = _remap(plate[..., 2], _GX + gxF * (k_ref + 1.5) * 4, _GY + gyF * (k_ref + 1.5) * 4)
    nx, ny = -gx * 18, -gy * 18; nn = np.sqrt(nx * nx + ny * ny + 1)
    lv = np.array([-0.45, -0.65, 0.62], np.float32); lv /= np.linalg.norm(lv)
    hv = lv + np.array([0, 0, 1], np.float32); hv /= np.linalg.norm(hv)
    ndh = np.clip((nx * hv[0] + ny * hv[1] + hv[2]) / nn, 0, 1)
    spec = (ndh ** 60 * (0.70 + 0.40 * tens) + ndh ** 10 * 0.12) * (1 - np.clip(lift * 1.5, 0, 1))   # glints on the fold crests; none in the curl
    crease = np.clip(np.abs(cv2.Laplacian(hgt, cv2.CV_32F, ksize=3)) * 2.2 - 0.05, 0, 1) * 0.22   # stress-whitened creases
    curl_hi = np.exp(-((dfp - curl_w * 0.55) / (curl_w * 0.30)) ** 2) * (peel > 0) * 0.60         # the bright rolled edge
    edge_arr = np.exp(-((front_arr - dg) / 0.012) ** 2) * (qa < 1) * 0.40                         # the sheet's leading edge
    hl = cv2.resize((spec + crease + curl_hi + edge_arr).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
    hl *= np.clip(np.minimum(np.minimum(_GX, W - 1 - _GX), np.minimum(_GY, H - 1 - _GY)) / 60.0, 0, 1)        # no glints on the frame edge
    milk = 0.06 + 0.04 * tens
    sheet = under * (1 - milk) + milk * 0.90 + np.clip(hl, 0, 1.2)[..., None] * np.array([0.95, 0.97, 1.0], np.float32)
    base = B
    cast = cv2.resize(np.exp(-((dg - front_peel - 0.01) / 0.02) ** 2) * (dg > front_peel) * (peel > 0) * 0.30, (W, H))
    base = base * (1 - cast[..., None] * 0.5)
    if j < 0 and peel <= 0: base = A
    o = base * (1 - covF[..., None]) + sheet * covF[..., None]
    return np.clip(o, 0, 1)
TR2["surface"] = (surface, SU_PRE, SU_POST)

# ---- SPECIMEN: the slide crosses his face, magnifies his eye; the next shot inside the glass, then it fills the lens ----
SP_PRE, SP_POST = 16, 14
SP_U = np.array([0.848, -0.530], np.float32)                                                     # along the slide (up-right)
SP_N = np.array([0.530, 0.848], np.float32)                                                      # across it (down-right)
_SPX = {}
def sp_eye(sa):
    if sa["n"] not in _SPX:
        fs = face_scr(sa, sa["f1"] - 3)
        if fs is None: _SPX[sa["n"]] = (W * 0.5, H * 0.40, 300.0)
        else:
            e = min((fs[3], fs[4]), key=lambda q: abs(q[0] - W / 2)); _SPX[sa["n"]] = (float(e[0]), float(e[1]), float(fs[2]))
    return _SPX[sa["n"]]

def specimen(A, B, j, f, sa, sb, pre=SP_PRE, post=SP_POST):
    ex, ey, fw = sp_eye(sa)
    if j < 0:
        u = (j + pre + 0.5) / pre
        off = 1500 * (1 - eout(clamp(u / 0.55, 0, 1), 2.4)) - 50 * u                             # sweeps in from the lower right, settles on the eye
        hw = 230.0; M = 1.0 + 0.85 * smooth(u / 0.42)                                           # and magnifies it
        cin = smooth((u - 0.76) / 0.24)                                                          # then the next shot appears in the glass
    else:
        v = (j + 0.5) / post
        off = -50.0; hw = 230.0 + 2400 * ein(clamp(v / 0.85, 0, 1), 2.3)                          # the slide comes to the lens
        M = 1.85 - 0.85 * smooth(v / 0.90); cin = 1.0
    C = np.array([ex, ey], np.float32) + SP_N * off
    sc_ = hw / 230.0
    dn = (_GX - C[0]) * SP_N[0] + (_GY - C[1]) * SP_N[1]
    ds = (_GX - C[0]) * SP_U[0] + (_GY - C[1]) * SP_U[1]
    s0, s1 = -560 * sc_, 1400 * sc_                                                              # the slide's ends along its length
    rr = 26.0 * sc_                                                                              # rounded corners
    ad = np.abs(dn) - (hw - rr); sd_ = np.maximum(s0 + rr - ds, ds - (s1 - rr))
    dist = np.sqrt(np.maximum(ad, 0) ** 2 + np.maximum(sd_, 0) ** 2) + np.minimum(np.maximum(ad, sd_), 0) - rr
    inside = np.clip(0.5 - dist, 0, 1)                                                           # anti-aliased glass mask
    if inside.max() <= 0: return A if j < 0 else B
    bev = 24.0 * max(1.0, sc_ ** 0.5)
    edge = np.clip(1 + dist / bev, 0, 1) * (dist <= 0)                                            # 0 inside .. 1 at the edge
    pull = edge ** 2 * 46.0                                                                      # the bevel refracts outward
    nxb = np.where(ad > sd_, np.sign(dn), 0.0)                                               # which edge is nearest
    gx_ = nxb * SP_N[0] + (1 - np.abs(nxb)) * np.sign(ds - (s0 + s1) / 2) * SP_U[0]
    gy_ = nxb * SP_N[1] + (1 - np.abs(nxb)) * np.sign(ds - (s0 + s1) / 2) * SP_U[1]
    mx = C[0] + (_GX - C[0]) / M + gx_ * pull; my = C[1] + (_GY - C[1]) / M + gy_ * pull
    in_old = _remap(A, mx, my) if cin < 1 else None
    if cin > 0:                                                                                   # the next shot inside the glass: its own eye
        sa_n_for_b[sb["n"]] = sa["n"]; bx, by = sp_eye_b(sb); kk = smooth((j + 0.5) / post) if j >= 0 else 0.0                   # on the slide's line, whole face, then 1:1
        Mb = 1.0 + 0.0 * kk; ox = bx + (C[0] - bx) * kk; oy = by + (C[1] - by) * kk
        in_new = cv2.remap(B, (ox + (_GX - C[0]) / Mb + gx_ * pull).astype(np.float32), (oy + (_GY - C[1]) / Mb + gy_ * pull).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    else: in_new = None
    glass = in_new if in_old is None else (in_old if in_new is None else in_old * (1 - cin) + in_new * cin)
    glass[..., 2] = glass[..., 2] * (1 - edge * 0.35) + _remap((A if cin < 0.5 else B)[..., 2], mx + gx_ * 6 * edge, my + gy_ * 6 * edge) * edge * 0.35
    tintc = np.array([0.93, 0.98, 0.92], np.float32)                                            # the green of a glass edge
    glass = glass * (1 - edge[..., None] * 0.45) + glass * tintc * edge[..., None] * 0.45
    hi_top = np.exp(-((dist + bev * 0.30) / (bev * 0.18)) ** 2) * (dn < 0) * 0.55               # light on the upper edge
    hi_bot = np.exp(-((dist + bev * 0.55) / (bev * 0.25)) ** 2) * (dn > 0) * 0.18
    sheen = np.exp(-((ds - (s0 + 0.55 * (s1 - s0)) + 260 * (u if j < 0 else 1)) / (160 * sc_)) ** 2) * 0.05 * (1 - edge)
    glass = glass + (hi_top + hi_bot + sheen)[..., None] * np.array([0.96, 0.98, 1.0], np.float32)
    outside = A if j < 0 else A
    if j >= 0: outside = _blur(outside, 2.5 * min(1.0, (j + 1) / 6))
    o = outside * (1 - inside[..., None]) + glass * inside[..., None]
    # the drop of blood on the slide, near its lower-left end; it rides the slide out of frame
    dpx = C + SP_U * (-330 * sc_) + SP_N * (40 * sc_)
    o = blood_drop108(o, float(dpx[0]), float(dpx[1]), 64.0 * sc_ ** 0.75, tint=1.0)
    return np.clip(o, 0, 1)
TR2["specimen"] = (specimen, SP_PRE, SP_POST)

# ---- FROST: the Ice Truck Killer; frost grows over the lens from the edges, the picture cools, it thaws from the centre --
FR_PRE, FR_POST = 16, 22
_FR = {}
def fr_fields():
    """half-res fields: TF, the time each pixel of the frost ferns forms (they grow along their stems from the frame edges,
    branching at 60 degrees like ice); TH, when the frost haze reaches each pixel; spark, glints on the crystals."""
    if "f" not in _FR:
        h2, w2 = H // 2, W // 2; rng = np.random.default_rng(1082)
        segs = []                                                                                  # (time, x0, y0, x1, y1, width)
        def grow(x, y, ang, L, t0, depth, wdt):
            step = 5.0; n = int(L / step); t = t0
            for i in range(n):
                ang += rng.normal(0, 0.05)
                x1, y1 = x + math.cos(ang) * step, y + math.sin(ang) * step
                segs.append((t, x, y, x1, y1, wdt)); t += step / 620.0
                if depth < 2 and rng.random() < (0.30 if depth == 0 else 0.20) and i > 2:
                    side = 1 if rng.random() < 0.5 else -1
                    grow(x1, y1, ang + side * math.radians(60), L * rng.uniform(0.18, 0.40) * (1 - i / n * 0.5), t, depth + 1, max(1, wdt - 1))
                x, y = x1, y1
        cx_, cy_ = w2 / 2, h2 * 0.45
        for k in range(110):                                                                       # seeds along the edges
            side = k % 4; p_ = rng.uniform(0.02, 0.98)
            x, y = [(p_ * w2, 0), (w2 - 1, p_ * h2), (p_ * w2, h2 - 1), (0, p_ * h2)][side]
            ang = math.atan2(cy_ - y, cx_ - x) + rng.normal(0, 0.45)
            grow(x, y, ang, rng.uniform(50, 150), rng.uniform(0.0, 0.25), 0, 1)
        TF = np.full((h2, w2), 9.0, np.float32)
        for t, x0, y0, x1, y1, wd in sorted(segs, key=lambda q: -q[0]):                           # later times first, earlier overwrite
            cv2.line(TF, (int(x0), int(y0)), (int(x1), int(y1)), float(t), int(wd), cv2.LINE_AA)
        yy, xx = np.mgrid[0:h2, 0:w2].astype(np.float32)
        d_edge = np.minimum(np.minimum(xx, w2 - 1 - xx) / w2, np.minimum(yy, h2 - 1 - yy) / h2 * 1.15)
        n1 = cv2.GaussianBlur(rng.standard_normal((h2, w2)).astype(np.float32), (0, 0), 30); n1 /= np.abs(n1).max()
        TH = d_edge / d_edge.max() + n1 * 0.12; TH = (TH - TH.min()) / (TH.max() - TH.min())
        g1 = cv2.GaussianBlur(rng.standard_normal((h2, w2)).astype(np.float32), (0, 0), 0.8)
        g2 = cv2.GaussianBlur(rng.standard_normal((h2, w2)).astype(np.float32), (0, 0), 3.0)
        grain_ = g1 / np.abs(g1).max() * 0.6 + g2 / np.abs(g2).max() * 0.4                          # crystalline frosted-glass grain
        spark = (rng.random((h2, w2)) > 0.9975).astype(np.float32)
        _FR["f"] = (TF, TH, grain_, spark)
    return _FR["f"]

FROSTC = np.array([0.99, 0.95, 0.90], np.float32)
def frost108(A, B, j, f, sa, sb, pre=FR_PRE, post=FR_POST):
    TF, TH, grain_, spark = fr_fields(); gr_h = grain_
    if j < 0:
        u = (j + pre + 0.5) / pre; tau = 1.05 * eout(u, 1.3); hz = 0.95 * eout(u, 1.8); melt = 0.0; plate = A
    else:
        v = (j + 0.5) / post; tau = 1.05 + v; melt = clamp(eout(v / 0.70, 1.6), 0, 1); hz = 0.95 * (1 - melt * 1.15); plate = B
    fern = np.clip((tau - TF) / 0.025, 0, 1)                                                      # the ferns that have formed
    fern = cv2.GaussianBlur(fern, (0, 0), 0.7) * (1 - melt) * 0.0                                # rev: rime only, no line drawing
    haze = np.clip((hz - TH + gr_h * 0.03) / 0.08, 0, 1) * 0.80 if j < 0 else np.clip(((0.95 - melt * 1.15) - (1 - TH) * 0.0 - TH + 0.0) / 0.08, 0, 1) * 0.55
    if j >= 0: haze = np.clip(((1.0 - melt * 1.25) - TH + gr_h * 0.03) / 0.08, 0, 1) * 0.80 * (1 - melt * 0.5)  # the centre clears first
    glow = cv2.GaussianBlur(fern, (0, 0), 3.0)
    Fh = cv2.resize(np.clip(haze + glow * 0.25, 0, 1), (W, H)); Ff = cv2.resize(np.clip(fern, 0, 1), (W, H))
    gr = cv2.resize(grain_, (W, H)); sp = cv2.resize(spark * fern, (W, H))
    cold = clamp((hz if j < 0 else hz) * 1.1, 0, 1)
    L = lum(plate)[..., None]
    cooled = plate * (1 - 0.40 * cold) + (L * np.array([1.10, 1.0, 0.84], np.float32)) * 0.40 * cold
    diff = cv2.resize(_blur(cv2.resize(cooled, (W // 2, H // 2), interpolation=cv2.INTER_AREA), 6), (W, H))
    fogged = cooled * (1 - Fh[..., None]) + (diff * 0.72 + FROSTC * (0.24 + 0.10 * gr[..., None])) * Fh[..., None]
    tw = 0.6 + 0.4 * math.sin(f * 1.3)
    o = fogged * (1 - Ff[..., None] * 0.85) + FROSTC * Ff[..., None] * 0.85 + sp[..., None] * tw * 0.8
    return np.clip(o, 0, 1)
TR2["frost108"] = (frost108, FR_PRE, FR_POST)

# ---- THE LAST DROP (the loop) ----------------------------------------------------------------------------------------
LD_F0 = None
def last_drop(out, f, s):
    f0 = fh(68.6); f1 = E.DUR_F - 1
    if f < f0: return out
    t = (f - f0) / (f1 - f0)
    if f >= f1: return frame0_plate108().copy()
    fall = ein(clamp(t / 0.62, 0, 1), 1.6)                                                       # it falls down the dark beside his head
    cx = W * 0.84; cy = -70 + (H * 0.46 + 70) * fall
    r = 16 + 70 * fall
    grow = ein(clamp((t - 0.46) / 0.50, 0, 1), 2.4)                                               # then it falls toward the lens
    r = r + grow * (R_FULL - r)
    cx = cx + (W / 2 - cx) * grow ** 1.6; cy = cy + (H / 2 - cy) * grow ** 1.6                   # it stays on the right until it covers
    stretch = 1.0 + 0.45 * (1 - grow) * smooth(t / 0.15)                                         # a falling bead, longer while it falls
    iw = smooth((t - 0.30) / 0.45)                                                                # frame 0's smile inside it
    tint = 1.0 - smooth((t - 0.50) / 0.42); gloss = 1.0 - smooth((grow - 0.55) / 0.40)
    base = out
    if grow > 0: base = _blur(out, 6 * grow)
    o = blood_drop108(base.copy(), cx, cy, r, behind=base, inside=frame0_plate108(), inside_w=iw, stretch=stretch, tint=tint, gloss=gloss)
    return o

def render(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin")
    out, person = base108(s, f)
    if tin in TR2 and k < TR2[tin][2] and P is not None:
        out = TR2[tin][0](edge108(P, "last"), out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, edge108(n_, "first"), kn, f, s, n_)
    if s.get("tout") == "last_drop": out = last_drop(out, f, s)
    out = beat_fx(out, f)
    out = flash_governor(out)
    return (np.clip(finish108(out, f, s), 0, 1) * 255 + 0.5).astype(np.uint8)

# ---- "ever since the womb": born in blood. The v107 pour, quicker (0.8 s), centred on the cut (he was born in it)
MOL_QC = 0.5
def molasses108(A, B, j, f, sa, sb):
    return molasses(A, B, j, f, sa, sb, pre=24, post=24)
TR2["molasses108"] = (molasses108, 24, 24)

_BS = {}
def _blur_small(img):
    k = id(img)
    if k not in _BS:
        _BS.clear(); _BS[k] = cv2.resize(cv2.GaussianBlur(cv2.resize(img, (W // 8, H // 8), interpolation=cv2.INTER_AREA), (0, 0), 3), (W, H))
    return _BS[k]

_SPB = {}; sa_n_for_b = {}
def sp_eye_b(sb):
    if sb["n"] not in _SPB:
        fs = face_scr(sb, sb["f0"])
        if fs is None: _SPB[sb["n"]] = (W * 0.5, H * 0.40)
        else:
            ex_, ey_, _ = _SPX.get(sa_n_for_b.get(sb["n"], ""), (W / 2, H * 0.4, 0))
            e = min((fs[3], fs[4]), key=lambda q: (q[0] - ex_) ** 2 + (q[1] - ey_) ** 2); _SPB[sb["n"]] = (float(e[0]), float(e[1]))   # the eye nearest the slide
    return _SPB[sb["n"]]

# ---- rev (the fresh-eyes critique): the library whip without its gold streak (it crossed his mouth); a softer sun sweep
def whip108(A, B, j, f, sa, sb, pre=6, post=8):
    if j < 0:
        u = ein((j + pre + 1) / pre, 2.2); o = cv2.warpAffine(A, np.float32([[1, 0, -W * 0.55 * u], [0, 1, 0]]), (W, H), borderMode=cv2.BORDER_REFLECT)
        o = hblur(o, 4 + 260 * u)
    else:
        v = 1 - eout((j + 1) / post, 2.6); o = cv2.warpAffine(B, np.float32([[1, 0, W * 0.55 * v], [0, 1, 0]]), (W, H), borderMode=cv2.BORDER_REFLECT)
        o = hblur(o, 4 + 260 * v)
    return np.clip(o, 0, 1)
TR2["whip"] = (whip108, 6, 8)

def light_sweep108(A, B, j, f, sa, sb, n=9):
    u = clamp((j + n + 0.5) / (2 * n), 0, 1); pos = -0.45 + 1.9 * smooth(u)
    xs = (_GX / W) * 0.55 + (_GY / H) * 0.85
    side = smooth((pos - xs) / 0.22 + 0.5)[..., None] if False else np.clip((pos - xs) / 0.22 + 0.5, 0, 1)[..., None]
    side = side * side * (3 - 2 * side)
    band = np.exp(-((xs - pos) / 0.16) ** 2)[..., None]
    o = A * (1 - side) + B * side
    return np.clip(o * (1 + 0.55 * band) + band * (SODIUM * 0.18 + WARMW * 0.10), 0, 1)
TR2["light_sweep108"] = (light_sweep108, 9, 9)

# ============================================================================ v108 rev 1 (owner notes, 2026-11-09)
# 1. SPECIMEN merged with the real slide: the slide in his hands (its own smear and frosted label, cut from the frame)
#    lifts toward the lens, swings up so its clear end lies over his eye and magnifies it; the next shot appears in the
#    clear glass; the slide comes to the lens and fills it. His face behind goes soft as the slide comes near.
# 2. No beat bounce in this edit (the owner: "remove that just for this edit"): no zoom punch, kick or hit-frame blur.
# 3. More custom transitions, smooth and creative (below).
def beat_phase(f):
    e = f / FPS / E.HB; ph = (e % 2) * E.HB; bi = int(e // 2)
    return ph, bi, False, False

SP_PRE, SP_POST = 18, 14
SR_C = np.array([280.0, 995.0], np.float32)       # the real upper slide at f1 - SP_PRE (measured on the frame)
SR_L, SR_HH = 430.0, 150.0                         # half length (it runs off the left edge), half height
SR_SMEAR = (-13.0, 2.0, 135.0)                     # the blood smear: local centre and radius
SR_LABEL = (185.0, 417.0, -172.0, 133.0)           # the frosted label: local a0, a1, b0, b1
_SRT = {}
def sr_tex(sa):
    """the real slide's features (smear + label) as a local-coordinate texture with alpha, and the screen mask of them
    at their original place (for the fill once the slide has left)."""
    if sa["n"] not in _SRT:
        A0 = base108(sa, sa["f1"] - SP_PRE)[0]
        L, hh = int(SR_L), int(SR_HH) + 30
        bb, aa = np.mgrid[-hh:hh, -L:L].astype(np.float32)
        tex = _remap(A0, SR_C[0] + aa, SR_C[1] + bb, cv2.BORDER_REPLICATE)
        sm = np.clip((SR_SMEAR[2] - np.sqrt((aa - SR_SMEAR[0]) ** 2 + (bb - SR_SMEAR[1]) ** 2)) / 6.0, 0, 1)
        a0, a1, b0, b1 = SR_LABEL
        lb = np.clip(np.minimum.reduce([aa - a0, a1 - aa, bb - b0, b1 - bb]) / 5.0, 0, 1)
        alpha = np.maximum(sm, lb).astype(np.float32)
        body = np.clip(np.minimum(SR_L - np.abs(aa), SR_HH + 28 - np.abs(bb)) / 6.0, 0, 1)            # the whole glass leaves
        scr = np.zeros((H, W), np.float32)
        x0, y0 = int(SR_C[0]) - L, int(SR_C[1]) - hh
        ys, xs = slice(max(0, y0), min(H, y0 + 2 * hh)), slice(max(0, x0), min(W, x0 + 2 * L))
        scr[ys, xs] = np.maximum(alpha, body)[ys.start - y0:ys.stop - y0, xs.start - x0:xs.stop - x0]
        scr = cv2.GaussianBlur(cv2.dilate(scr, np.ones((31, 31), np.uint8)), (0, 0), 6)
        _SRT[sa["n"]] = (tex, alpha, scr)
    return _SRT[sa["n"]]

def sp_eye_r(sa):
    """the eye the slide's clear end lands on: the one on the right of the frame (the slide's far end runs off up-right)."""
    key = ("r", sa["n"])
    if key not in _SPX:
        fs = face_scr(sa, sa["f1"] - 3)
        _SPX[key] = (W * 0.70, H * 0.27) if fs is None else tuple(float(v) for v in max((fs[3], fs[4]), key=lambda q: q[0]))
    return _SPX[key]

SR_PIV = np.array([705.0, 995.0], np.float32)     # his fingers hold the slide's right end: it pivots there
def sp_eye_l(sa):
    key = ("l", sa["n"])
    if key not in _SPX:
        fs = face_scr(sa, sa["f1"] - 3)
        _SPX[key] = (W * 0.27, H * 0.27) if fs is None else tuple(float(v) for v in min((fs[3], fs[4]), key=lambda q: q[0]))
    return _SPX[key]

def specimen(A, B, j, f, sa, sb, pre=SP_PRE, post=SP_POST):
    """rev 1b: the real slide pivots up in his fingers (like tilting it to the light) until its clear end is over his
    left eye, magnifying it; the next shot appears in the glass; it fills the lens."""
    ex, ey = sp_eye_l(sa); tex, alpha, scr = sr_tex(sa)
    piv = SR_PIV; dvec = piv - np.array([ex, ey], np.float32); dlen = float(np.hypot(*dvec))
    ang_t = math.atan2(dvec[1], dvec[0])                                                    # the slide's axis toward the eye
    if j < 0:
        u = (j + pre + 0.5) / pre; k = smooth(u / 0.78)
        ang = ang_t * k; sc = 1.0 + 0.22 * k
        lens_a = SR_L - 5 - dlen / sc                                                         # the point of the slide over the eye
        cpos = piv - np.array([math.cos(ang), math.sin(ang)], np.float32) * (SR_L - 5) * sc
        lp = cpos + np.array([math.cos(ang), math.sin(ang)], np.float32) * lens_a * sc
        M = 1.0 + 0.85 * smooth((u - 0.45) / 0.40)
        cin = smooth((u - 0.80) / 0.20); dof = 5.0 * smooth(u / 0.7); gone = smooth(u / 0.25)
    else:
        v = (j + 0.5) / post; ang = ang_t
        sc0 = 1.22; sc = sc0 * (1 + 4.5 * ein(clamp(v / 0.85, 0, 1), 2.2))
        lp = np.array([ex, ey], np.float32); lens_a = SR_L - 5 - dlen / sc0
        M = 1.85 - 0.85 * smooth(v / 0.9); cin = 1.0; dof = 5.0; gone = 1.0
    ca, sn = math.cos(ang), math.sin(ang)
    uax = np.array([ca, sn], np.float32); nax = np.array([-sn, ca], np.float32)
    C = lp - uax * lens_a * sc                                                           # the slide's centre on screen
    dxp, dyp = _GX - C[0], _GY - C[1]
    la = (dxp * uax[0] + dyp * uax[1]) / sc; lb = (dxp * nax[0] + dyp * nax[1]) / sc       # local coordinates
    rr = 22.0
    ad = np.abs(lb) - (SR_HH - rr); sd_ = np.abs(la) - (SR_L - rr)
    dist = (np.sqrt(np.maximum(ad, 0) ** 2 + np.maximum(sd_, 0) ** 2) + np.minimum(np.maximum(ad, sd_), 0) - rr) * sc
    inside = np.clip(0.5 - dist, 0, 1)
    # what's behind: his face, the features filled where the slide has left, soft as the slide comes near
    base = A if j < 0 else A
    if gone > 0:
        q = 4; sm_ = cv2.resize(scr, (W // q, H // q), interpolation=cv2.INTER_AREA); keep = 1 - np.clip(sm_ * 1.5, 0, 1)
        bq_ = cv2.resize(base, (W // q, H // q), interpolation=cv2.INTER_AREA)                   # normalized convolution: the
        num = cv2.GaussianBlur(bq_ * keep[..., None], (0, 0), 14); den = cv2.GaussianBlur(keep, (0, 0), 14)[..., None]   # surroundings, smoothly
        Af = cv2.resize(num / np.maximum(den, 1e-3), (W, H), interpolation=cv2.INTER_CUBIC)
        base = base * (1 - scr[..., None] * gone) + Af * scr[..., None] * gone
    outside = _blur(base, dof)
    if inside.max() <= 0: return outside if j < 0 else B
    bev = 20.0 * max(1.0, sc ** 0.5)
    edge = np.clip(1 + dist / bev, 0, 1) * (dist <= 0)
    pull = edge ** 2 * 40.0
    nxb = np.where(ad > sd_, np.sign(lb), 0.0)
    gx_ = nxb * nax[0] + (1 - np.abs(nxb)) * np.sign(la) * uax[0]
    gy_ = nxb * nax[1] + (1 - np.abs(nxb)) * np.sign(la) * uax[1]
    mx = lp[0] + (_GX - lp[0]) / M + gx_ * pull; my = lp[1] + (_GY - lp[1]) / M + gy_ * pull
    glass = _remap(base, mx, my)
    if cin > 0:
        sa_n_for_b[sb["n"]] = sa["n"]; bx, by = sp_eye_b(sb); kk = smooth((j + 0.5) / post) if j >= 0 else 0.0
        ox = bx + (lp[0] - bx) * kk; oy = by + (lp[1] - by) * kk
        inb = cv2.remap(B, (ox + (_GX - lp[0]) + gx_ * pull).astype(np.float32), (oy + (_GY - lp[1]) + gy_ * pull).astype(np.float32),
                        cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        glass = glass * (1 - cin) + inb * cin
    tintc = np.array([0.94, 0.98, 0.93], np.float32)
    glass = glass * (1 - edge[..., None] * 0.40) + glass * tintc * edge[..., None] * 0.40
    hi = np.exp(-((dist + bev * 0.30) / (bev * 0.18)) ** 2) * (lb < 0) * 0.50 + np.exp(-((dist + bev * 0.55) / (bev * 0.25)) ** 2) * (lb > 0) * 0.16
    glass = glass + hi[..., None] * np.array([0.96, 0.98, 1.0], np.float32)
    # the slide's own smear and label ride on the glass (soft and fading as it comes to the lens)
    ft = cv2.remap(tex, (la + SR_L).astype(np.float32), (lb + SR_HH + 30).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    fa = cv2.remap(alpha, (la + SR_L).astype(np.float32), (lb + SR_HH + 30).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    fade = 1.0 if j < 0 else 1 - smooth((j + 0.5) / (post * 0.5))
    if sc > 1.6: ft = _blur(ft, (sc - 1.6) * 3.0)
    fa = fa * inside * fade
    glass = glass * (1 - fa[..., None]) + ft * fa[..., None]
    o = outside * (1 - inside[..., None]) + glass * inside[..., None]
    return np.clip(o, 0, 1)
TR2["specimen"] = (specimen, SP_PRE, SP_POST)

# ---- rev 1: new custom transitions (smooth, each its own idea) -------------------------------------------------------
_NZ = {}
def nz108(seed, sig, q=4):
    """a smooth, wrapping noise texture at 1/q resolution, normalised to 0..1 (deterministic)."""
    key = (seed, sig, q)
    if key not in _NZ:
        n = np.random.default_rng(seed).standard_normal((H // q, W // q)).astype(np.float32)
        n = cv2.GaussianBlur(np.tile(n, (3, 3)), (0, 0), sig)[H // q:2 * (H // q), W // q:2 * (W // q)]   # wraps
        _NZ[key] = (n - n.min()) / (n.max() - n.min() + 1e-6)
    return _NZ[key]

def _up(m): return cv2.resize(m, (W, H), interpolation=cv2.INTER_CUBIC)

# HAZE: Miami heat. The picture shimmers in rising heat waves; the next shot condenses out of the shimmer.
def haze108(A, B, j, f, sa, sb, pre=10, post=12):
    q = (j + pre + 0.5) / (pre + post); amp = math.sin(math.pi * clamp(q, 0, 1)) ** 1.4; t = f / FPS
    dx = (np.sin(_GY * 0.040 - t * 9.0) * 0.6 + np.sin(_GY * 0.019 + _GX * 0.011 - t * 6.0)) * 42 * amp
    dy = (np.sin(_GX * 0.028 + _GY * 0.010 + t * 7.0) * 18 - 30) * amp
    w = smooth((q - 0.44) / 0.12)
    a = _remap(A, _GX + dx, _GY + dy) if w < 1 else None; b = _remap(B, _GX - dx * 0.8, _GY + dy) if w > 0 else None
    o = b if a is None else (a if b is None else a * (1 - w) + b * w)
    o = _blur(o, 3.0 * amp) * (1 + 0.07 * amp)
    return np.clip(o, 0, 1)
TR2["haze108"] = (haze108, 10, 12)

# DIFFUSION: "turn H2O to cognac". A cloud of cognac-red spreads through the frame like dye in water (turbulent, rising,
# fine wisps at its front); the next shot is inside the cloud.
DIFC = np.array([0.10, 0.30, 0.66], np.float32)          # BGR cognac / thinned blood
def diffusion108(A, B, j, f, sa, sb, pre=16, post=18):
    q = (j + pre + 0.5) / (pre + post); t = f / FPS
    h4, w4 = H // 4, W // 4
    yy, xx = np.mgrid[0:h4, 0:w4].astype(np.float32)
    n1, n2 = nz108(1101, 18), nz108(1102, 6)
    off = int(t * 60) % h4
    adv1 = np.roll(n1, -off // 2, axis=0); adv2 = np.roll(n2, -off, axis=0)                   # it rises as it spreads
    D = np.sqrt(((xx - w4 * 0.50) / w4) ** 2 + ((yy - h4 * 1.08) / h4 * 0.9) ** 2) * 1.20
    D = D + (adv1 - 0.5) * 0.55 + (adv2 - 0.5) * 0.16
    lvl = -0.05 + 1.85 * ein(q, 1.55)
    m = np.clip((lvl - D) / 0.22, 0, 1); m = m * m * (3 - 2 * m)
    band = np.exp(-((lvl - D - 0.06) / 0.16) ** 2) * (0.45 + 0.55 * adv2)
    dens = np.clip((lvl - D) / 0.45, 0, 1) * (0.6 + 0.4 * adv1)                                 # the dye's body
    gy, gx = np.gradient(cv2.GaussianBlur(D, (0, 0), 1.5))
    M_, BD = _up(m), _up(band); GX_, GY_ = _up(gx * band), _up(gy * band)
    a = _remap(A, _GX + GX_ * 260, _GY + GY_ * 260); b = _remap(B, _GX - GX_ * 160, _GY - GY_ * 160)
    DN = _up(dens) * (1 - smooth((j + 0.5) / post) if j >= 0 else 1.0)
    sharp = smooth((j + 0.5) / 10.0) if j >= 0 else 0.0                                         # inside the cloud it is soft until after the cut
    bs = cv2.resize(cv2.GaussianBlur(cv2.resize(b, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 3.5), (W, H))
    b = bs * (1 - sharp) + b * sharp
    o = a * (1 - M_[..., None]) + b * M_[..., None]
    tint = np.clip(BD * 0.45 + DN * 0.40, 0, 0.7)[..., None]
    soft = cv2.resize(cv2.GaussianBlur(cv2.resize(o, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 5), (W, H))
    o = o * (1 - tint * 1.3) + soft * tint * 0.3 + (soft * 0.35 + DIFC * 0.75) * tint                 # a smooth wash of cognac
    return np.clip(o, 0, 1)
TR2["diffusion108"] = (diffusion108, 16, 18)

# DOUBLE VISION: the M99 takes hold. The picture doubles and sways apart, soft; the next shot arrives doubled and pulls
# back into focus.
def double108(A, B, j, f, sa, sb, pre=12, post=14):
    k = smooth((j + pre + 0.5) / (pre * 0.7)) if j < 0 else 1 - smooth((j + 0.5) / post)
    w = smooth((j + 3.5) / 7.0)
    def dbl(img):
        d = 78 * k; r = 1.6 * k * math.sin(f * 0.21)
        M1 = cv2.getRotationMatrix2D((W / 2, H * 0.42), r, 1 + 0.03 * k); M1[0, 2] += d
        M2 = cv2.getRotationMatrix2D((W / 2, H * 0.42), -r, 1 + 0.03 * k); M2[0, 2] -= d
        a = cv2.warpAffine(img, M1, (W, H), borderMode=cv2.BORDER_REFLECT); b = cv2.warpAffine(img, M2, (W, H), borderMode=cv2.BORDER_REFLECT)
        return _blur(a * 0.5 + b * 0.5, 3.5 * k)
    o = dbl(A) if w <= 0 else (dbl(B) if w >= 1 else dbl(A) * (1 - w) + dbl(B) * w)
    return np.clip(o * (1 - 0.10 * k), 0, 1)
TR2["double108"] = (double108, 12, 14)

# DEVELOPER: the darkroom. Red safelight falls over the frame and the tray's liquid ripples; the next shot develops out
# of a pale print, gaining contrast, and the safelight lifts.
SAFE = np.array([0.10, 0.16, 0.95], np.float32)
def developer108(A, B, j, f, sa, sb, pre=8, post=18):
    t = f / FPS; r = np.sqrt((_GX - W * 0.5) ** 2 + (_GY - H * 0.45) ** 2)
    if j < 0:
        u = (j + pre + 0.5) / pre; red = smooth(u); rip = smooth(u) * 8; img = A; dev = 1.0
    else:
        v = (j + 0.5) / post; red = 1 - smooth((v - 0.45) / 0.55); rip = 8 * (1 - smooth(v / 0.8)); img = B; dev = ein(clamp(v / 0.80, 0, 1), 1.3)
    wave = (np.sin(r * 0.045 - t * 14) + 0.5 * np.sin(r * 0.11 - t * 22)) * rip * 1.8
    img = _remap(img, _GX + wave * (_GX - W * 0.5) / (r + 1), _GY + wave * (_GY - H * 0.45) / (r + 1))
    if j >= 0:
        paper = np.float32(0.80)
        img = paper + (np.clip((img - 0.5) * (0.55 + 0.45 * dev) + 0.5 - 0.06 * (1 - dev), 0, 1) - paper) * (0.50 + 0.50 * dev)
    L = lum(img)[..., None]
    o = img * (1 - 0.55 * red) + L * SAFE * 0.85 * red
    sheen = np.clip(np.sin(r * 0.045 - t * 14) * np.sin(r * 0.11 - t * 22), 0, 1) ** 6 * (rip / 8.0) * 0.12
    o = o + sheen[..., None] * SAFE
    return np.clip(o, 0, 1)
TR2["developer108"] = (developer108, 8, 18)

# LUMINOL: the forensic spray. The light drops (not to black), the blue-white glow of luminol blooms in splatter where the
# blood was, and the next shot is in the glow; the glow spreads over the frame and fades to the picture.
LUMC = np.array([1.00, 0.62, 0.22], np.float32)
_LU = {}
def lu_field():
    """a wide luminol spray: hundreds of drops and smears across the frame (dense in clusters, thin between)."""
    if "g" not in _LU:
        rng = np.random.default_rng(1103); h4, w4 = H // 4, W // 4; g = np.zeros((h4, w4), np.float32)
        cl = [(rng.uniform(0.05, 0.95) * w4, rng.uniform(0.05, 0.95) * h4) for _ in range(9)]
        for k in range(420):
            cx, cy = cl[k % 9]; sp = rng.uniform(10, 70)
            x, y = int(cx + rng.normal(0, sp)), int(cy + rng.normal(0, sp * 1.3)); r_ = max(1, int(rng.exponential(2.2)))
            cv2.circle(g, (x, y), r_, float(rng.uniform(0.5, 1.0)), -1, cv2.LINE_AA)
            if rng.random() < 0.12: cv2.line(g, (x, y), (x + int(rng.normal(0, 4)), y + int(rng.uniform(8, 30))), 0.7, 1, cv2.LINE_AA)   # drips
        g = cv2.GaussianBlur(g, (0, 0), 1.8) + cv2.GaussianBlur(g, (0, 0), 7) * 1.1
        _LU["g"] = np.clip(g / np.percentile(g[g > 0.01], 95), 0, 1.3)
    return _LU["g"]

def luminol108(A, B, j, f, sa, sb, pre=10, post=18):
    g = lu_field(); n = nz108(1104, 10)
    if j < 0:
        u = (j + pre + 0.5) / pre; dim = 0.45 * smooth(u); lvl = -0.1 + 0.55 * smooth((u - 0.3) / 0.7); img = A
    else:
        v = (j + 0.5) / post; dim = 0.45 * (1 - smooth((v - 0.35) / 0.65)); lvl = 0.40 + 0.9 * ein(v, 1.2); img = B
    field = g * 0.85 + n * 0.30
    fs = face_scr(sb, sb["f0"]); h4, w4 = H // 4, W // 4
    if fs is not None:                                                                        # keep the glow off his face
        yy, xx = np.mgrid[0:h4, 0:w4].astype(np.float32)
        fm = np.clip((np.sqrt((xx - fs[0] / 4) ** 2 + ((yy - fs[1] / 4) * 0.8) ** 2) - fs[2] / 4 * 0.55) / (fs[2] / 4 * 0.25), 0, 1)
        below = np.clip((yy - (fs[1] + fs[2] * 0.75) / 4) / 12.0, 0, 1)                           # below the collar only
        field = field * fm * (0.15 + 0.85 * below)
    m = np.clip((field - (1.0 - lvl)) / 0.18, 0, 1); M_ = _up(m)
    glow = _up(np.clip(m * (0.6 + 0.4 * g), 0, 1)) * (1 - smooth((j + 0.5) / post) if j >= 0 else 1.0)
    L = lum(img)[..., None]
    dark = img * (1 - dim) * (1 - 0.4 * dim) + L * np.array([0.30, 0.22, 0.18], np.float32) * dim * 0.4
    lit = (B if j >= 0 else A) * (0.55 + 0.45 * (1 - glow[..., None])) + LUMC * L * glow[..., None] * 0.55
    if j < 0: lit = dark + LUMC * glow[..., None] * 0.42
    o = dark * (1 - M_[..., None]) + lit * M_[..., None]
    o = o + glow[..., None] * LUMC * 0.40 * (1 - M_[..., None] * 0.4)                             # the glow itself, blue
    return np.clip(o + cv2.GaussianBlur(glow, (0, 0), 18)[..., None] * LUMC * 0.14, 0, 1)
TR2["luminol108"] = (luminol108, 10, 18)

# FACE MATCH: one face becomes the next. The outgoing frame slides and scales so his face lands where the next shot's
# face is, they dissolve through each other, and the next shot settles to its own framing.
def facematch108(A, B, j, f, sa, sb, pre=8, post=10):
    fa = face_scr(sa, sa["f1"] - 1); fb = face_scr(sb, sb["f0"])
    if fa is None or fb is None: fa = fb = (W / 2, H * 0.42, 500.0)
    s_ = clamp(fb[2] / max(fa[2], 1.0), 0.6, 1.7)
    def warp(img, cx, cy, sc, tx, ty):
        M = np.float32([[sc, 0, tx - cx * sc], [0, sc, ty - cy * sc]])
        return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    if j < 0:
        u = smooth((j + pre + 0.5) / pre)
        a = warp(A, fa[0], fa[1], 1 + (s_ - 1) * u, fa[0] + (fb[0] - fa[0]) * u, fa[1] + (fb[1] - fa[1]) * u)
        w = smooth((j + 3.5) / 7.0); o = a if w <= 0 else a * (1 - w) + B * w
        return np.clip(_blur(o, 1.5 * math.sin(math.pi * u)), 0, 1)
    v = smooth((j + 0.5) / post)
    a = warp(A, fa[0], fa[1], s_, fb[0], fb[1])
    w = smooth((j + 3.5) / 7.0); b = B
    return np.clip(a * (1 - w) + b * w if w < 1 else b, 0, 1)
TR2["facematch108"] = (facematch108, 8, 10)

# SINK: "go get bagged and checked in". The water rises over the lens (a meniscus, refraction, caustic light); under the
# surface the next shot comes up, and the water drains off it.
WATC = np.array([0.62, 0.70, 0.52], np.float32)
def sink108(A, B, j, f, sa, sb, pre=14, post=18):
    t = f / FPS
    if j < 0: yw = H * (1.05 - 1.15 * ein((j + pre + 0.5) / pre, 1.4)); img = A
    else: yw = H * (-0.10 + 1.20 * ein((j + 0.5) / post, 1.6)); img = B
    surf = yw + 22 * np.sin(_GX * 0.011 + t * 5.0) + 9 * np.sin(_GX * 0.031 - t * 7.0)
    under = (_GY > surf) if j < 0 else (_GY < surf)                                              # rising / draining
    d = (_GY - surf) if j < 0 else (surf - _GY)
    m = np.clip(d / 6.0 + 0.5, 0, 1)
    wob = np.sin(_GY * 0.02 + t * 6) * 10 + np.sin(_GX * 0.017 - t * 4) * 6
    uw = _remap(img, _GX + wob, _GY + wob * 0.5)
    ca = (np.abs(np.sin(_GX * 0.013 + np.sin(_GY * 0.011 + t * 3) * 2.0)) * np.abs(np.sin(_GY * 0.012 - t * 2.4))) ** 6
    uw = uw * WATC + ca[..., None] * 0.10 + 0.02
    men = np.exp(-(d / 5.0) ** 2) * 0.35
    o = img * (1 - m[..., None]) + uw * m[..., None] + men[..., None] * np.array([0.9, 0.95, 1.0], np.float32)
    return np.clip(o, 0, 1)
TR2["sink108"] = (sink108, 14, 18)

def facematch108(A, B, j, f, sa, sb, pre=8, post=10):
    """rev 1b: registered on the eyes (scale, rotation and position), so one face becomes the other."""
    fa = face_scr(sa, sa["f1"] - 1); fb = face_scr(sb, sb["f0"])
    if fa is None or fb is None: return haze108(A, B, j, f, sa, sb, pre, post)
    ea = sorted((fa[3], fa[4])); eb = sorted((fb[3], fb[4]))
    va = np.subtract(ea[1], ea[0]); vb = np.subtract(eb[1], eb[0])
    sc = clamp(np.hypot(*vb) / max(np.hypot(*va), 1.0), 0.5, 2.0); rot = math.atan2(vb[1], vb[0]) - math.atan2(va[1], va[0])
    ca_ = np.mean(ea, axis=0); cb_ = np.mean(eb, axis=0)
    def M_of(k):                                                                            # identity -> A's eyes onto B's (k 0..1)
        s_ = 1 + (sc - 1) * k; r_ = rot * k; c, sn = math.cos(r_) * s_, math.sin(r_) * s_
        tx, ty = ca_ + (cb_ - ca_) * k
        return np.float32([[c, -sn, tx - (c * ca_[0] - sn * ca_[1])], [sn, c, ty - (sn * ca_[0] + c * ca_[1])]])
    if j < 0:
        k = smooth((j + pre + 0.5) / pre)
        a = cv2.warpAffine(A, M_of(k), (W, H), borderMode=cv2.BORDER_REFLECT)
        w = smooth((j + 2.5) / 5.0)
        if w <= 0: return np.clip(_blur(a, 1.2 * math.sin(math.pi * k)), 0, 1)
        bi = cv2.warpAffine(B, cv2.invertAffineTransform(M_of(1.0)) @ np.vstack([M_of(1.0), [0, 0, 1]])[:2] if False else np.float32([[1, 0, 0], [0, 1, 0]]), (W, H))
        return np.clip(a * (1 - w) + B * w, 0, 1)
    a = cv2.warpAffine(A, M_of(1.0), (W, H), borderMode=cv2.BORDER_REFLECT)
    w = smooth((j + 2.5) / 5.0)
    return np.clip(a * (1 - w) + B * w if w < 1 else B, 0, 1)
TR2["facematch108"] = (facematch108, 8, 10)

_sink_r1 = sink108
def sink108(A, B, j, f, sa, sb, pre=14, post=18):
    o = _sink_r1(A, B, j, f, sa, sb, pre, post)
    rng = np.random.default_rng(1108); t = f / FPS
    for k in range(26):                                                                      # bubbles rising under the surface
        x0 = rng.uniform(0.05, 0.95) * W; sp_ = rng.uniform(260, 520); r_ = rng.uniform(4, 13); ph = rng.uniform(0, 3)
        y = H * 1.05 - ((t * sp_ + ph * 400) % (H * 1.2)); x = x0 + 14 * math.sin(t * 6 + ph * 3)
        if 0 < y < H:
            q = (j + pre) / (pre + post); vis = math.sin(math.pi * clamp(q, 0, 1))
            if vis > 0.05:
                cv2.circle(o, (int(x), int(y)), int(r_), (0.85, 0.90, 0.95), 1, cv2.LINE_AA)
    return np.clip(o, 0, 1)
TR2["sink108"] = (sink108, 14, 18)

def wiper108(A, B, j, f, sa, sb):
    return wiper(A, B, j, f, sa, sb, pre=12, post=16)
TR2["wiper108"] = (wiper108, 12, 16)

# ============================================================================ v108 rev 2 (owner notes)
# The heat haze ("the squiggle, swirl, weird animation") is replaced by FRONDS: sunlit palm fronds sweep across the lens in
# the foreground (we pass under the palms he stands beneath), three depths with parallax and motion blur; the cut is
# behind the nearest frond. The rain-on-the-lens transition at 14 s is gone (a smooth push instead).
_FD = {}
def fd_frond(seed, length, lw, curve):
    """one palm frond as an rgba sprite (its own pixel space): a curved rachis with tapered leaflets on both sides, lit by
    the sun behind it (translucent yellow-green edges, darker veins)."""
    key = (seed, length, lw, curve)
    if key not in _FD:
        rng = np.random.default_rng(seed); Wd, Hd = int(length * 1.15), int(length * 0.75)
        a = np.zeros((Hd, Wd), np.float32); shade = np.zeros((Hd, Wd), np.float32)
        n = 34; pts = []
        for i in range(n + 1):
            u = i / n; x = Wd * 0.05 + u * length; y = Hd * 0.5 + curve * length * (u - 0.5) ** 2 - curve * length * 0.25
            pts.append((x, y))
        for i in range(1, n):
            (x, y), (x2, y2) = pts[i], pts[i + 1]; ang = math.atan2(y2 - y, x2 - x)
            for side in (-1, 1):
                L = lw * (0.55 + 0.45 * math.sin(math.pi * i / n)) * rng.uniform(0.85, 1.1)
                la = ang + side * math.radians(rng.uniform(48, 62)) + side * 0.25 * i / n
                ex, ey = x + math.cos(la) * L, y + math.sin(la) * L
                mx, my = (x + ex) / 2, (y + ey) / 2; ln = L / 2; wd = max(3, L * 0.075)
                cv2.ellipse(a, (int(mx), int(my)), (int(ln), int(wd)), math.degrees(la), 0, 360, 1.0, -1, cv2.LINE_AA)
                cv2.line(shade, (int(x), int(y)), (int(ex), int(ey)), 1.0, max(1, int(wd * 0.25)), cv2.LINE_AA)
        cv2.polylines(a, [np.int32(pts)], False, 1.0, max(3, int(lw * 0.05)), cv2.LINE_AA)
        a = cv2.GaussianBlur(a, (0, 0), 0.8)
        rim = np.clip(a - cv2.erode(a, np.ones((5, 5), np.uint8)), 0, 1)                        # backlit edges
        col = np.empty((Hd, Wd, 3), np.float32)
        base = np.array([0.05, 0.16, 0.10], np.float32); lit = np.array([0.20, 0.62, 0.55], np.float32)   # backlit: dark leaves, glowing edges
        g = np.linspace(0, 1, Wd, dtype=np.float32)[None, :] * 0.6 + 0.2
        for c in range(3): col[..., c] = base[c] + (lit[c] - base[c]) * (g * 0.35 + rim * 0.9) - shade * 0.03
        _FD[key] = (np.clip(col, 0, 1), np.clip(a, 0, 1))
    return _FD[key]

def fronds108(A, B, j, f, sa, sb, pre=14, post=14):
    q = (j + pre + 0.5) / (pre + post)
    w = smooth((j + 3.5) / 7.0)                                                               # the shots dissolve behind the leaves
    o = A * (1 - w) + B * w if 0 < w < 1 else (A if j < 0 else B).copy()
    for k, (seed, length, lw, curve, depth, y0, rot) in enumerate(((1201, 1500, 300, 0.25, 0.55, 0.30, -14),
                                                                  (1202, 2300, 470, 0.18, 0.80, 0.62, 10),
                                                                  (1203, 3200, 680, 0.12, 1.00, 0.48, -6))):
        col, a = fd_frond(seed, length, lw, curve)
        sc = 0.55 + 0.45 * depth; sw = int(col.shape[1] * sc)
        x = W * 0.5 + (0.5 - q) * (W + sw) * (0.9 + 0.5 * depth)                                   # each frond is centred on the cut; near ones faster
        M = cv2.getRotationMatrix2D((col.shape[1] / 2, col.shape[0] / 2), rot, sc)
        M[0, 2] += x - col.shape[1] / 2 + sw / 2 * 0; M[1, 2] += H * y0 - col.shape[0] / 2
        cw = cv2.warpAffine(col, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0))
        aw = cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
        blur = int(6 + 40 * depth)                                                                    # motion blur along the sweep
        kx = np.ones((1, blur), np.float32) / blur
        cw = cv2.filter2D(cw, -1, kx); aw = cv2.filter2D(aw, -1, kx)
        dof = 1.5 + 11.0 * depth ** 2; cw = _blur(cw, dof); aw = _blur(aw, dof)                       # the near frond is far out of focus
        o = o * (1 - aw[..., None]) + cw * aw[..., None]
    return np.clip(o, 0, 1)
TR2["fronds108"] = (fronds108, 14, 14)


# ============================================================================ v109 — PHANTOM (Dexter × EsDeeKid & Rico Ace)
# "Rocked out like a phantom": the Bay Harbor Butcher as a ghost the city hunts and never sees. The beat camera is back
# (v108's off-switch was for that edit only). Look SPECTRAL: silver-blue night, inky blacks, cold cyan highlights with a
# faint ghost bloom; only blood red survives. One designed title, PHANTOM. New: flashlight, materialise, after-image,
# mirror pane, phone glitch, crime-scene tape, vanish, mist, the vanishing loop.
_L109 = {}
CYAN109 = np.array([0.98, 0.90, 0.72], np.float32)        # BGR ghost light
MIST109 = np.array([0.86, 0.82, 0.74], np.float32)        # BGR mist
_grade_pre109 = grade
def grade(img, s, f):
    if s.get("look") != "spectral109": return _grade_pre109(img, s, f)
    if "c" not in _L109:
        x = np.linspace(0, 1, 1024, dtype=np.float32)
        _L109["c"] = (x, PchipInterpolator([0, .05, .2, .5, .8, .95, 1], [0.008, 0.016, 0.11, 0.41, 0.76, 0.90, 0.93])(x).astype(np.float32))
    g, gains = corr9(s); ev = s.get("ev") or 0; lx, ly = _L109["c"]; gains = tuple(float(v) for v in gains)
    x = apply_lut3(img, tone_lut(("sp109", s["n"], ev, float(g), gains), gains, g, ev, lx, ly)) if in_unit(img) else \
        np.interp(np.clip(np.clip(img * np.array(gains, np.float32), 0, 1) ** g * 2 ** ev, 0, 1), lx, ly).astype(np.float32)
    Bc, Gc, Rc = (np.ascontiguousarray(x[..., c]) for c in range(3))
    L = Bc * 0.114 + Gc * 0.587 + Rc * 0.299
    red = np.clip((Rc - 1.85 * np.maximum(Gc, Bc) - s.get("redthr", 0.05)) * 3.0, 0, 1)
    sat = 0.20 + 0.12 * np.clip((Rc - Bc) * 1.8, 0, 1) * (1 - red) + 0.95 * red
    hi = np.clip((L - 0.55) * 2.0, 0, 1); sh = (1 - L) ** 2
    o = np.empty(x.shape, np.float32)
    for ch, P in enumerate((Bc, Gc, Rc)):
        v = L + (P - L) * sat
        v += sh * (0.045, 0.012, -0.012)[ch] + hi * (CYAN109[ch] / 0.98 - 1) * 0.35 * L
        v += red * L * (CRIMSON[ch] / 0.78 - 1) * 0.30
        o[..., ch] = v
    return np.clip(o, 0, 1, out=o)

def finish109(out, f, s=None):
    L = lum(out)
    q = cv2.resize(np.clip(L - 0.62, 0, 1), (W // 8, H // 8), interpolation=cv2.INTER_AREA)
    bloom = cv2.resize(cv2.GaussianBlur(q, (0, 0), 7), (W, H), interpolation=cv2.INTER_LINEAR)
    g = grain(f, 0.013)[..., 0]; v = VIG[..., 0]
    o = np.empty(out.shape, np.float32)
    for ch in range(3):
        oc = o[..., ch]; np.copyto(oc, out[..., ch]); oc += bloom * CYAN109[ch] * 0.22; oc *= v; oc += g
    return np.clip(o, 0, 1, out=o)

def beat_phase(f):
    e = f / FPS / E.HB; ph = (e % 2) * E.HB; bi = int(e // 2)
    hook = (E.E_BEAT + 2 <= e < 52) and not (10 <= e < 13.5) and not (29.5 <= e < 31) and not (39 <= e < 41)
    return ph, bi, hook, False

def _person(s_, f):
    try:
        p = base108(s_, f)[1]
        return None if p is None else np.clip(p.astype(np.float32), 0, 1)
    except Exception:
        return None

def mistfield(f, scale=1.0, speed=1.0):
    """the phantom mist: two noise layers drifting at different speeds (full res, 0..1)."""
    a, b = nz108(1901, 22), nz108(1902, 8)
    sh = int(f * 2 * speed) % a.shape[1]; sh2 = int(f * 5 * speed) % b.shape[1]
    m = np.roll(a, sh, axis=1) * 0.7 + np.roll(b, -sh2, axis=1) * 0.3
    return _up(m)

def mist_veil(img, dens, f, speed=1.0):
    m = mistfield(f, speed=speed)
    d = np.clip(dens * (0.55 + 0.9 * m), 0, 1)[..., None] if np.ndim(dens) else np.clip(dens * (0.55 + 0.9 * m), 0, 1)[..., None]
    soft = cv2.resize(cv2.GaussianBlur(cv2.resize(img, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 4), (W, H))
    return img * (1 - d) + (soft * 0.45 + MIST109 * 0.42) * d

# FLASHLIGHT: the dark; a flashlight beam searches and finds him; the beam opens over the next shot.
def flashlight109(A, B, j, f, sa, sb, pre=10, post=14):
    q = (j + pre + 0.5) / (pre + post); img = A if j < 0 else B
    fs = face_scr(sb if j >= 0 else sa, f); tx, ty = (fs[0], fs[1]) if fs else (W / 2, H * 0.4)
    k = smooth(q / 0.6); cx = W * 1.1 + (tx - W * 1.1) * k; cy = H * 0.15 + (ty - H * 0.15) * k
    R = 260 + 1900 * ein(clamp((q - 0.55) / 0.45, 0, 1), 2.0)
    d = np.sqrt(((_GX - cx) / 1.0) ** 2 + ((_GY - cy) / 1.15) ** 2)
    beam = np.clip(1 - d / R, 0, 1) ** 0.8; hot = np.exp(-(d / (R * 0.25)) ** 2)
    dark = 1.0 - 0.45 * smooth(q / 0.25) + 0.45 * smooth((q - 0.85) / 0.15)                   # the light drops smoothly, then returns
    lit = beam[..., None] * (1 + 0.35 * hot[..., None])
    o = img * np.clip(dark + (1 - dark) * lit, 0, 1.3) + hot[..., None] * np.array([0.10, 0.14, 0.16], np.float32) * (1 - dark)
    return np.clip(o, 0, 1)
TR2["flashlight109"] = (flashlight109, 10, 14)

# MATERIALISE (the drop, the signature): the frame dissolves into mist; on the drop he forms out of it first (his own
# matte, eroding in from the noise), the room after him, the mist burning off in cold light.
def materialize109(A, B, j, f, sa, sb, pre=20, post=40):
    if j < 0:
        u = (j + pre + 0.5) / pre
        return np.clip(mist_veil(A * (1 - 0.35 * u), smooth(u) * 0.95, f, 2.0), 0, 1)
    v = (j + 0.5) / post; per = _person(sb, f)
    n = mistfield(f, speed=2.0)
    n = cv2.GaussianBlur(n, (0, 0), 6)
    form = np.clip((ein(v, 1.2) * 1.45 - (1 - n) * 0.9) / 0.32, 0, 1); form = form * form * (3 - 2 * form)   # mist -> him, in soft wisps
    room = smooth((v - 0.35) / 0.65)
    m = form * (per if per is not None else 1.0) + room * (1 - (per if per is not None else 0))
    edge = cv2.GaussianBlur(np.clip(form * (1 - form) * 4, 0, 1) * (per if per is not None else 1.0), (0, 0), 5)
    o = mist_veil(B, (1 - smooth(v / 0.9)) * 0.95, f, 2.0)
    o = o * (1 - m[..., None]) + B * m[..., None]
    return np.clip(o + edge[..., None] * CYAN109 * 0.18, 0, 1)
TR2["materialize109"] = (materialize109, 20, 40)

# AFTER-IMAGE: he moves faster than the eye: the frame leaves cold echoes that drift and fade; the next shot arrives
# through its own echoes.
def afterimage109(A, B, j, f, sa, sb, pre=8, post=10):
    k = smooth((j + pre + 0.5) / pre) if j < 0 else 1 - smooth((j + 0.5) / post)
    img = A if j < 0 else B; o = img * (1 - 0.35 * k)
    for i, (dx, a) in enumerate(((-70, 0.38), (-140, 0.24), (-210, 0.13))):
        sh = cv2.warpAffine(img, np.float32([[1, 0, dx * k * (1 if j < 0 else -1)], [0, 1, 0]]), (W, H), borderMode=cv2.BORDER_REFLECT)
        o = o + (sh * 0.6 + CYAN109 * 0.12 * lum(sh)[..., None]) * a * k
    return np.clip(o, 0, 1)
TR2["afterimage109"] = (afterimage109, 8, 10)

# MIRROR PANE: a pane of glass slides across; through it the next shot (refracted at its edge), on it a faint reflection
# of the frame it leaves.
def mirror109(A, B, j, f, sa, sb, pre=10, post=10):
    q = (j + pre + 0.5) / (pre + post); x0 = W * 1.08 - (W * 1.16) * smooth(q)                 # starts and ends just off frame
    d = _GX - x0; inside = np.clip(d / 3.0 + 0.5, 0, 1); edge = np.exp(-(d / 14.0) ** 2)               # the pane trails its edge leftward
    refr = np.exp(-((d + 40) / 40.0) ** 2)
    b = cv2.remap(B, (_GX + refr * 30).astype(np.float32), _GY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    ghost = cv2.flip(A, 1) * 0.10
    o = A * (1 - inside[..., None]) + (b + ghost) * inside[..., None] + edge[..., None] * np.array([0.55, 0.55, 0.50], np.float32)
    return np.clip(o, 0, 1)
TR2["mirror109"] = (mirror109, 10, 10)

# PHONE GLITCH ("me phone keeps havin' a tantrum"): the frame buzzes like a phone on a table: a fast lateral jitter,
# torn scanline bands and a split of the colour planes, cut in the middle.
def tantrum109(A, B, j, f, sa, sb, pre=6, post=10):
    k = smooth((j + pre + 0.5) / pre) if j < 0 else 1 - smooth((j + 0.5) / post)
    img = A if j < 0 else B; rng = np.random.default_rng(1909 + f)
    dx = int(26 * k * math.sin(f * 2.7)); o = np.roll(img, dx, axis=1)
    for _ in range(int(6 * k) + 1):
        y0 = int(rng.uniform(0, H - 80)); h = int(rng.uniform(20, 90)); s_ = int(rng.uniform(-120, 120) * k)
        o[y0:y0 + h] = np.roll(o[y0:y0 + h], s_, axis=1)
    o = rgb_split(o, 10 * k)
    return np.clip(o, 0, 1)
TR2["tantrum109"] = (tantrum109, 6, 10)

# CRIME-SCENE TAPE: three lengths of yellow tape whip across the frame on a diagonal (no words), the cut behind them.
TAPEY = np.array([0.10, 0.80, 0.95], np.float32)
def tape109(A, B, j, f, sa, sb, pre=8, post=12):
    q = (j + pre + 0.5) / (pre + post); o = (A if j < 0 else B).copy()
    for k, (ang, y0, w_, sp) in enumerate(((-18, 0.38, 150, 1.0), (12, 0.58, 120, 1.25), (-6, 0.47, 190, 0.85))):
        a = math.radians(ang); n_ = (-math.sin(a), math.cos(a))
        dn = (_GX - W / 2) * n_[0] + (_GY - H * y0) * n_[1]
        along = (_GX - W / 2) * math.cos(a) + (_GY - H * y0) * math.sin(a)
        reach = -W * 0.9 + 2.6 * W * ein(clamp(q * sp - 0.05 * k, 0, 1), 1.3)                  # its leading end
        band = np.clip((w_ / 2 - np.abs(dn)) / 2.0, 0, 1) * np.clip((reach - along) / 6.0, 0, 1)
        stripe = (np.mod(along + dn * 0.6, 120) < 55).astype(np.float32)
        col = TAPEY * (0.80 + 0.20 * np.cos(dn / w_ * 3.1))[..., None] * (1 - 0.85 * stripe[..., None]) + 0.02
        o = o * (1 - band[..., None]) + col * band[..., None]
    return np.clip(o, 0, 1)
TR2["tape109"] = (tape109, 8, 12)

# VANISH: he dissolves into mist where he stands (his matte erodes from the noise, wisps rise), and the next shot.
def vanish109(A, B, j, f, sa, sb, pre=14, post=8):
    if j < 0:
        u = (j + pre + 0.5) / pre; per = _person(sa, f)
        n = mistfield(f, speed=3.0); gone = np.clip((smooth(u) * 1.3 - n) / 0.15, 0, 1)
        P_ = per if per is not None else np.zeros((H, W), np.float32)
        bg = cv2.resize(cv2.GaussianBlur(cv2.resize(A, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 6), (W, H))
        m = gone * P_; edge = np.clip(gone * (1 - gone) * 4, 0, 1) * P_
        o = A * (1 - m[..., None]) + (bg * 0.6 + MIST109 * 0.25) * m[..., None] + edge[..., None] * CYAN109 * 0.40
        return np.clip(mist_veil(o, smooth((u - 0.6) / 0.4) * 0.8, f, 3.0), 0, 1)
    v = (j + 0.5) / post
    return np.clip(mist_veil(B, (1 - smooth(v)) * 0.8, f, 3.0), 0, 1)
TR2["vanish109"] = (vanish109, 14, 8)

# MIST: a bank of fog rolls across the lens and the next shot is behind it.
def mist109(A, B, j, f, sa, sb, pre=12, post=12):
    q = (j + pre + 0.5) / (pre + post); x0 = W * 1.3 - W * 1.9 * smooth(q)
    m = mistfield(f, speed=1.5); ramp = smooth(q / 0.2) * smooth((1 - q) / 0.2); front = np.clip((x0 - _GX + (m - 0.5) * 380) / 260.0, 0, 1)
    dens = front * np.clip((_GX - (x0 - W * 1.4) + (m - 0.5) * 380) / 260.0, 0, 1)
    w = smooth((j + 3.5) / 7.0); img = A * (1 - w) + B * w if 0 < w < 1 else (A if j < 0 else B)
    return np.clip(mist_veil(img, dens * ramp, f, 1.5), 0, 1)
TR2["mist109"] = (mist109, 12, 12)

# THE VANISHING (the loop): on "action" he dissolves into mist, the mist fills the lens, and it clears on frame 0,
# where he walks out of the dark again.
def vanish_loop109(out, f, s, person=None):
    f0 = fh(52.6); f1 = E.DUR_F - 1
    if f < f0: return out
    if f >= f1: return frame0_plate108().copy()
    t = (f - f0) / (f1 - f0); n = mistfield(f, speed=3.0)
    P_ = person.astype(np.float32) if person is not None else np.zeros((H, W), np.float32)
    gone = np.clip((smooth(t / 0.6) * 1.3 - n) / 0.15, 0, 1) * P_
    soft = cv2.resize(cv2.GaussianBlur(cv2.resize(out, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 8), (W, H))
    o = out * (1 - gone[..., None]) + (soft * 0.55 + MIST109 * 0.35) * gone[..., None]
    fill = smooth((t - 0.25) / 0.35) * 0.85; clear = smooth((t - 0.50) / 0.46)                  # frame 0 shows through early
    o = mist_veil(o, fill * (1 - clear), f, 3.0)
    f0p = frame0_plate108()
    if clear > 0: o = o * (1 - clear) + mist_veil(f0p, fill * (1 - clear), f, 3.0) * clear
    return np.clip(o, 0, 1)

# THE TITLE: PHANTOM, on the sung word. Each letter condenses out of mist on a 16th grid (blur to sharp, a cold glow),
# holds, then the word blows away as mist from left to right.
_TT = {}
def title109(out, f):
    t = f / FPS; t0 = E.th(10.4); step = E.HB / 4; t_out = E.th(13.3)
    if t < t0 - 0.05 or t > t_out + 0.45: return out
    if "m" not in _TT:
        word = "PHANTOM"; ms = [text_mask(c, F_BLACK, 158) for c in word]
        _TT["m"] = ms; _TT["w"] = sum(m.shape[1] for m in ms) + 14 * (len(ms) - 1)
    ms = _TT["m"]; x = (W - _TT["w"]) / 2; y = int(H * 0.77)
    lay = np.zeros((H, W), np.float32)
    for i, m in enumerate(ms):
        a = smooth((t - (t0 + i * step)) / 0.16); blow = smooth((t - (t_out + i * 0.04)) / 0.30)
        al = a * (1 - blow)
        if al > 0:
            mm = m.astype(np.float32) / (m.max() + 1e-6)
            bl = 6 * (1 - a) + 10 * blow
            if bl > 0.3: mm = cv2.GaussianBlur(mm, (0, 0), bl)
            yy = int(y - 30 * (1 - a) - 40 * blow); xx = int(x + 50 * blow)
            h_, w_ = mm.shape; ys, xs = max(0, yy), max(0, xx)
            ye, xe = min(H, yy + h_), min(W, xx + w_)
            if ye > ys and xe > xs: lay[ys:ye, xs:xe] = np.maximum(lay[ys:ye, xs:xe], mm[ys - yy:ye - yy, xs - xx:xe - xx] * al)
        x += m.shape[1] + 14
    glow = cv2.GaussianBlur(lay, (0, 0), 18)
    o = out * (1 - lay[..., None] * 0.9) + lay[..., None] * np.array([0.97, 0.96, 0.94], np.float32) * 0.95 + glow[..., None] * CYAN109 * 0.35
    return np.clip(o, 0, 1)

def render(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin")
    out, person = base108(s, f)
    if tin in TR2 and k < TR2[tin][2] and P is not None:
        out = TR2[tin][0](edge108(P, "last"), out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, edge108(n_, "first"), kn, f, s, n_)
    if s.get("tout") == "vanish_loop109": out = vanish_loop109(out, f, s, person)
    out = beat_fx(out, f)
    out = title109(out, f)
    out = flash_governor(out)
    return (np.clip(finish109(out, f, s), 0, 1) * 255 + 0.5).astype(np.uint8)

# ---- v109, after the fresh-eyes critique: two new transitions; the mist without outlines or holes ------------------
# FLICKER: the light fails: the frame breathes dim and bright on an uneven filament rhythm, the next shot shows through
# the flicker, and the light steadies on it.
def flicker109(A, B, j, f, sa, sb, pre=10, post=12):
    q = (j + pre + 0.5) / (pre + post); env = math.sin(math.pi * clamp(q, 0, 1))
    fl = 0.5 + 0.5 * math.sin(f * 1.9) * math.sin(f * 0.73 + 1.1)                                  # an uneven filament
    bright = 1.0 - env * (0.55 - 0.40 * fl)
    w = smooth((q - 0.42) / 0.16); img = A * (1 - w) + B * w if 0 < w < 1 else (A if j < 0 else B)
    L = lum(img)[..., None]
    o = img * bright + (L * np.array([0.55, 0.75, 0.95], np.float32) - img) * env * 0.25          # a warm bulb cast while it fails
    return np.clip(o, 0, 1)
TR2["flicker109"] = (flicker109, 10, 12)

# SURVEILLANCE: the city watches for him. The frame turns into a surveillance feed (cold grey-green, scanlines, a little
# barrel, noise), a tracking bar rolls down through it and the next shot is behind the bar; the feed snaps back clean.
def cctv109(A, B, j, f, sa, sb, pre=10, post=12):
    q = (j + pre + 0.5) / (pre + post); k = math.sin(math.pi * clamp(q, 0, 1)) ** 0.7
    by = -0.2 * H + 1.4 * H * smooth(q)                                                            # the tracking bar
    behind = np.clip((by - _GY) / 40.0, 0, 1)
    img = A * (1 - behind[..., None]) + B * behind[..., None]
    r2 = ((_GX - W / 2) / W) ** 2 + ((_GY - H / 2) / H) ** 2
    img = _remap(img, W / 2 + (_GX - W / 2) * (1 - 0.06 * k * r2), H / 2 + (_GY - H / 2) * (1 - 0.06 * k * r2))
    L = lum(img)[..., None]
    feed = L * np.array([0.78, 0.92, 0.80], np.float32) * (0.85 + 0.15 * (np.sin(_GY * 1.6) > 0)[..., None])
    feed = feed + (np.random.default_rng(1910 + f).random((H, W), dtype=np.float32)[..., None] - 0.5) * 0.06
    bar = np.exp(-((_GY - by) / 26.0) ** 2)[..., None] * 0.22
    o = img * (1 - k) + feed * k + bar * k
    return np.clip(o, 0, 1)
TR2["cctv109"] = (cctv109, 10, 12)

def materialize109(A, B, j, f, sa, sb, pre=20, post=40):
    """rev: he forms out of an even, pale mist (no outline, no dark holes)."""
    if j < 0:
        u = (j + pre + 0.5) / pre
        return np.clip(mist_veil(A * (1 - 0.30 * u), smooth(u) * 0.90, f, 2.0), 0, 1)
    v = (j + 0.5) / post; per = _person(sb, f)
    n = cv2.GaussianBlur(mistfield(f, speed=2.0), (0, 0), 10)
    form = np.clip((ein(v, 1.2) * 1.5 - (1 - n) * 0.9) / 0.40, 0, 1); form = form * form * (3 - 2 * form)
    room = smooth((v - 0.30) / 0.70)
    P_ = per if per is not None else np.ones((H, W), np.float32)
    m = form * P_ + room * (1 - P_)
    soft = cv2.resize(cv2.GaussianBlur(cv2.resize(B, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 5), (W, H))
    fog = soft * 0.40 + MIST109 * 0.42 * (1 - smooth(v / 0.95))
    o = fog * (1 - m[..., None]) + B * m[..., None]
    return np.clip(o, 0, 1)
TR2["materialize109"] = (materialize109, 20, 40)

def vanish109(A, B, j, f, sa, sb, pre=14, post=8):
    """rev: he thins into pale mist where he stands (no outline, no dark holes), and the next shot."""
    if j < 0:
        u = (j + pre + 0.5) / pre; per = _person(sa, f)
        n = cv2.GaussianBlur(mistfield(f, speed=3.0), (0, 0), 10)
        gone = np.clip((smooth(u) * 1.4 - n) / 0.35, 0, 1) * (per if per is not None else 0)
        soft = cv2.resize(cv2.GaussianBlur(cv2.resize(A, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 8), (W, H))
        o = A * (1 - gone[..., None]) + (soft * 0.55 + MIST109 * 0.35) * gone[..., None]
        return np.clip(mist_veil(o, smooth((u - 0.6) / 0.4) * 0.7, f, 3.0), 0, 1)
    v = (j + 0.5) / post
    return np.clip(mist_veil(B, (1 - smooth(v)) * 0.7, f, 3.0), 0, 1)
TR2["vanish109"] = (vanish109, 14, 8)

# ============================================================================ v109 rev 1 (the owner's notes, 2026-11-09)
# "the head spin transition ... replace it with a brand new, unique, and creative transition"; "remove the clips with
# dokes and replace them with other high-quality texture clips"; "a cool flow where there's unique graphics appearing and
# then transitions from those graphics"; "improve ... the end flow of the edit and into the loop ... more unique and
# creative with better animations". The ending is now one chain: his FINGERPRINT (we dive through the whorl), the
# photo's FIRE (the frame burns away from the burning photo), the HEART MONITOR (his pulse under the M99 flatlines and
# the line opens like an eye on his stare), and THE GUST (he blows away as glowing dust; the same gust carries the dust
# into frame 0). The graphics share the edit's cold ghost-light.

def _zoom_about(img, Z, cx, cy, border=cv2.BORDER_REFLECT):
    M = np.float32([[Z, 0, cx * (1 - Z)], [0, Z, cy * (1 - Z)]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=border)

def splat109(xs, ys, cols, al, q=2, sig=0.8):
    """additive splat of points (full-res px) with bilinear weights into a 1/q buffer, blurred by sig (1/q px)."""
    w_, h_ = W // q, H // q
    x = xs / q - 0.5; y = ys / q - 0.5
    x0 = np.floor(x).astype(np.int64); y0 = np.floor(y).astype(np.int64)
    fx = (x - x0).astype(np.float32); fy = (y - y0).astype(np.float32)
    rgb = np.zeros((3, h_ * w_), np.float32); a = np.zeros(h_ * w_, np.float32)
    for dx, dy, wt in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
        xi = x0 + dx; yi = y0 + dy; ok = (xi >= 0) & (xi < w_) & (yi >= 0) & (yi < h_)
        if not ok.any(): continue
        idx = yi[ok] * w_ + xi[ok]; ww = (wt * al)[ok]
        a += np.bincount(idx, ww, h_ * w_).astype(np.float32)
        for c in range(3): rgb[c] += np.bincount(idx, ww * cols[ok, c], h_ * w_).astype(np.float32)
    rgb = np.ascontiguousarray(rgb.reshape(3, h_, w_).transpose(1, 2, 0)); a = a.reshape(h_, w_)
    if sig > 0: rgb = cv2.GaussianBlur(rgb, (0, 0), sig); a = cv2.GaussianBlur(a, (0, 0), sig)
    return rgb, a

# ---- PHANTOM PASS (replaces the headspin, e19): he walks at us through the night garden; his body turns to a ghost
# (the next shot shows through him, a thin mist inside, a cold rim on his outline), and the camera passes through him:
# his silhouette opens past the lens onto the next shot.
_PP = {}
def _pp_anchor(s_):
    if s_["n"] not in _PP:
        P = _person(s_, s_["f1"] - 1)
        P = np.zeros((H, W), np.float32) if P is None else P
        ys, xs = np.nonzero(P[::8, ::8] > 0.5)
        if len(xs) < 30:
            fs = face_scr(s_, s_["f1"] - 1); c = (fs[0], fs[1] + 300) if fs else (W / 2, H * 0.55)
        else: c = (float(np.mean(xs) * 8), float(np.percentile(ys, 40) * 8))
        _PP[s_["n"]] = (c, _pp_clean(P))
    return _PP[s_["n"]]

def _pp_clean(P):
    """the matte without holes or specks: a close at 1/4 res, then soft."""
    sm = cv2.resize(P, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    sm = cv2.morphologyEx(cv2.morphologyEx(sm, cv2.MORPH_CLOSE, k), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    return np.clip(cv2.GaussianBlur(cv2.resize(sm, (W, H), interpolation=cv2.INTER_LINEAR), (0, 0), 3.0), 0, 1)

def phantom_pass109(A, B, j, f, sa, sb, pre=16, post=14):
    q = (j + pre + 0.5) / (pre + post)
    (cx, cy), Plast = _pp_anchor(sa)
    if j < 0:                                                             # steadied: a matte that drops a limb for a frame
        ms = [m for m in (_person(sa, ff) for ff in (f - 2, f, min(f + 2, sa["f1"] - 1))) if m is not None]
        P = np.maximum.reduce(ms) if ms else None
    else: P = Plast
    P = np.zeros((H, W), np.float32) if P is None else _pp_clean(P)
    a = smooth(q / 0.42)                                                  # he turns translucent
    z = smooth((q - 0.32) / 0.58)                                         # we pass through him
    Z = math.exp(math.log(14.0) * ein(z, 2.2))
    if Z > 1.002:
        Az = (_zoom_about(A, Z, cx, cy) + _zoom_about(A, Z * 1.025, cx, cy)) / 2
        Pz = _zoom_about(P, Z, cx, cy, cv2.BORDER_CONSTANT)
    else: Az, Pz = A, P
    bz = 1 + 0.12 * (1 - smooth(q))
    Bz = _zoom_about(B, bz, W / 2, H * 0.42) if bz > 1.0005 else B
    ghost = mist_veil(Bz, 0.30 * (1 - z), f, 1.5)
    op = np.clip(Pz * np.clip(0.88 * a + smooth((q - 0.40) / 0.20), 0, 1), 0, 1)
    op = np.maximum(op, smooth((q - 0.80) / 0.15))                        # his silhouette sweeps the garden away
    o = Az * (1 - op[..., None]) + ghost * op[..., None]
    Pb = cv2.GaussianBlur(Pz, (0, 0), 5.0)
    rim = np.clip(Pb * (1 - Pb) * 4, 0, 1) * a * (1 - smooth((z - 0.25) / 0.45))     # the edge of him, lit, as it sweeps out
    o = np.clip(o, 0, 1); rc = rim[..., None] * CYAN109 * 0.26
    return np.clip(1 - (1 - o) * (1 - rc), 0, 1)                          # a screen: the rim never blows out a highlight
TR2["phantom_pass109"] = (phantom_pass109, 16, 14)

# ---- FINGERPRINT (the hunt -> the mangroves): a latent print is dusted onto the glass below his face (a brush sweep
# of silver powder, the ridges glow cold), then we dive into its whorl: the print turns as it grows past the lens, the
# next shot fills its grooves, and the ridges thin away.
_FP = {}
def fp_tex():
    if "w" not in _FP:
        rng = np.random.default_rng(1931)
        def nz(sig, n=512):
            a_ = rng.standard_normal((n, n)).astype(np.float32)
            a_ = cv2.GaussianBlur(np.tile(a_, (3, 3)), (0, 0), sig)[n:2 * n, n:2 * n]
            return (a_ - a_.mean()) / (a_.std() + 1e-6)
        _FP["w"] = nz(46); _FP["b"] = nz(6); _FP["g"] = rng.random((512, 512)).astype(np.float32)
    return _FP

FP_PER = 12.5
def fp_eval(xc, yc, S, ang, line_frac):
    T = fp_tex(); ca, sn = math.cos(ang), math.sin(ang)
    dx = _GX - xc; dy = _GY - yc
    u = (dx * ca + dy * sn) / S; v = (-dx * sn + dy * ca) / S
    tu = (u + 320) * (512 / 640); tv = (v + 320) * (512 / 640)
    wob = cv2.remap(T["w"], tu, tv, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    brk = cv2.remap(T["b"], tu, tv, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    grn = cv2.remap(T["g"], tu, tv, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    re = np.sqrt(u * u + (v / 1.28) ** 2)
    phi = re + FP_PER * np.arctan2(v, u) / (2 * np.pi) + 7.0 * wob
    wbt = np.clip((v - 70) / 150.0, 0, 1); wbt = wbt * wbt * (3 - 2 * wbt)            # the base of the print runs across
    phi = phi * (1 - wbt) + (v * 1.05 + 26 * np.sin(u / 95.0) + 7.0 * wob + 40) * wbt
    c = np.cos(2 * np.pi * phi / FP_PER)
    thr = math.cos(math.pi * line_frac)
    ridge = np.clip((c - thr) / max(0.05, (1 - thr) * 0.55), 0, 1)
    ridge *= np.clip((brk + 2.0) / 0.4, 0, 1)                                       # ridge endings
    ridge *= np.clip(re / 10.0, 0, 1) * 0.6 + 0.4                                  # a soft core
    rr = np.sqrt((u / 200.0) ** 2 + (v / 262.0) ** 2) + 0.06 * wob
    mask = np.clip((1.0 - rr) / 0.10, 0, 1)
    return ridge, mask, u, v, grn

FP_COL = np.array([0.93, 0.94, 0.92], np.float32)
_FPP = {}
def _fp_place(sa):
    if sa["n"] not in _FPP:
        fs = face_scr(sa, sa["f1"] - 1)
        y0 = clamp((fs[1] + 0.95 * fs[2] + 520) if fs else H * 0.80, 1380, 1560)
        _FPP[sa["n"]] = (W * 0.69, y0)
    return _FPP[sa["n"]]

def print109(A, B, j, f, sa, sb, pre=50, post=14):
    q = (j + pre + 0.5) / (pre + post)
    x0, y0 = _fp_place(sa)
    ap = smooth(q / 0.30)                                                 # the powder brush sweeps it in
    d = smooth((q - 0.44) / 0.56)                                         # the dive into the whorl
    S = math.exp(math.log(24.0) * ein(d, 2.0))
    xc = x0 + (W / 2 - x0) * smooth(d / 0.6); yc = y0 + (H * 0.68 - y0) * smooth(d / 0.6)   # into his chest, never his face
    ang = math.radians(-14) + 0.55 * ein(d, 1.5)
    lf = 0.34 / S ** 0.75
    ridge, mask, u, v, grn = fp_eval(xc, yc, S, ang, lf)
    sw = -380 + 800 * ap
    reveal = np.clip((sw - (u * 0.77 + v * 0.64)) / 70.0, 0, 1) if ap < 1 else 1.0
    win = mask * smooth((d - 0.04) / 0.36)                                # its grooves turn into a window
    Bz = _zoom_about(B, 1 + 0.16 * (1 - d), W / 2, H * 0.68) if d < 0.999 else B
    base = A * (1 - (0.22 * mask * reveal * (1 - d))[..., None])
    o = base * (1 - win[..., None]) + Bz * win[..., None]
    als = 1 + 0.9 * np.exp(-(((u * 0.6 - v * 0.8) - (-420 + 900 * smooth((q - 0.22) / 0.25))) / 55.0) ** 2) * (d < 0.3)
    rb = (1 - smooth((d - 0.38) / 0.45)) * np.clip(0.62 + 1.1 * (grn - 0.5), 0.2, 1.2) * als     # dusted powder, grainy   # a forensic light passes over it
    al = ridge * mask * reveal * rb
    glow = cv2.GaussianBlur(al, (0, 0), 3.0 + 4 * d)
    haze = mask * reveal * (1 - d) * 0.05 * grn
    o = o * (1 - al[..., None] * 0.8) + al[..., None] * FP_COL * 0.95 + (glow * 0.45 + haze)[..., None] * CYAN109
    return np.clip(o, 0, 1)
TR2["print109"] = (print109, 50, 14)

# ---- THE PHOTO'S FIRE (the burning photo -> the hammer): the fire in his hand catches the frame; the picture burns away
# from the photo outward (a white-hot edge, a thin char, a scorch), sparks lift off the edge, the next shot is behind.
_BN = {}
def _bn_setup(sa, pre):
    if sa["n"] not in _BN:
        img = base108(sa, sa["f1"] - pre)[0]
        L = cv2.GaussianBlur(cv2.resize(lum(img), (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 6)
        yy, xx = np.unravel_index(int(np.argmax(L)), L.shape)
        ox, oy = xx * 4.0 - 60, min(yy * 4.0 + 430, H * 0.86)                 # the photo in his hand, under the flame
        n1 = _up(nz108(1941, 10)); n2 = _up(nz108(1942, 3)); n3 = _up(nz108(1944, 1.2))
        D = np.sqrt((_GX - ox) ** 2 + ((_GY - oy) * np.where(_GY < oy, 0.8, 1.05)) ** 2) + 170 * (n1 - 0.5) + 70 * (n2 - 0.5) \
            + 26 * (n3 - 0.5)
        rng = np.random.default_rng(1943); n = 260
        sp = dict(th=rng.uniform(0, 2 * np.pi, n), d=rng.uniform(30, float(D.max()), n), dx=rng.uniform(-60, 60, n),
                  rise=rng.uniform(260, 620, n), life=rng.uniform(0.22, 0.45, n), sz=rng.uniform(0.6, 1.4, n))
        _BN[sa["n"]] = (ox, oy, D.astype(np.float32), float(D.max()) + 40, sp)
    return _BN[sa["n"]]

def burn109(A, B, j, f, sa, sb, pre=26, post=16):
    q = (j + pre + 0.5) / (pre + post)
    ox, oy, D, Rmax, sp = _bn_setup(sa, pre)
    Rq = lambda qq: -20 + (Rmax + 20) * ein(clamp(qq, 0, 1), 1.45)
    s_ = D - Rq(q)                                                         # < 0 burnt
    hole = np.clip(-s_ / 3.0 + 0.5, 0, 1)
    char = np.clip(1 - s_ / 24.0, 0, 1) * (1 - hole)
    scorch = np.clip(1 - (s_ - 24) / 90.0, 0, 1) * (s_ > 0)
    a = A * (1 - (0.22 * scorch)[..., None]) + (0.05 * scorch)[..., None] * np.array([0.0, 0.10, 0.30], np.float32)
    a = a * (1 - char[..., None] * 0.85) + char[..., None] * np.array([0.02, 0.03, 0.05], np.float32)
    o = a * (1 - hole[..., None]) + B * hole[..., None]
    live = float(Rq(q) > 0) * (1 - smooth((q - 0.94) / 0.06))
    core = np.exp(-((s_ - 2) / 2.5) ** 2) * live                          # the white-hot lip
    ember = np.exp(-((s_ - 6) / 9.0) ** 2) * live * (0.7 + 0.6 * _up(nz108(1945, 1.5)))   # glowing paper behind it
    glow = cv2.GaussianBlur(ember, (0, 0), 10)
    o = o + core[..., None] * np.array([0.70, 0.90, 1.0], np.float32) * 0.85 + ember[..., None] * np.array([0.06, 0.34, 1.0], np.float32) * 0.75 \
        + glow[..., None] * np.array([0.03, 0.20, 0.80], np.float32) * 0.45
    t = (j + pre + 0.5) / FPS; xs, ys, al = [], [], []                    # sparks lift off the edge
    for i in range(len(sp["th"])):
        qq = (sp["d"][i] + 20) / (Rmax + 20); qi = qq ** (1 / 1.45)          # when the front reaches it
        age = t - qi * (pre + post) / FPS
        if 0 <= age < sp["life"][i]:
            x = ox + sp["d"][i] * math.cos(sp["th"][i]) * 0.9 + sp["dx"][i] * age * 3
            y = oy + sp["d"][i] * math.sin(sp["th"][i]) * 0.9 - sp["rise"][i] * age
            xs.append(x); ys.append(y); al.append(sp["sz"][i] * math.exp(-age / (0.4 * sp["life"][i])))
    if xs:
        cols = np.tile(np.array([[0.35, 0.70, 1.0]], np.float32), (len(xs), 1))
        rgb, aa = splat109(np.array(xs), np.array(ys), cols, np.array(al, np.float32), q=2, sig=1.2)
        o = o + cv2.resize(rgb, (W, H), interpolation=cv2.INTER_LINEAR) * 3.0
    return np.clip(o, 0, 1)
TR2["burn109"] = (burn109, 26, 16)

# ---- THE HEART MONITOR ("you've never got no motion"; the M99 takes him -> his stare): a cold monitor trace sweeps
# across under his face, beats twice on the claps, flatlines; the flat line opens like an eye onto his stare.
EKG_Y = 0.78
def ekg_wave(x, beats):
    y = np.zeros_like(x)
    for xb, amp in beats:
        d = x - xb
        y += amp * (-0.10 * np.exp(-((d + 58) / 13) ** 2) + 0.20 * np.exp(-((d + 10) / 4.5) ** 2)
                    - 1.00 * np.exp(-(d / 5.0) ** 2) + 0.40 * np.exp(-((d - 11) / 5.5) ** 2) - 0.20 * np.exp(-((d - 62) / 18) ** 2))
    return y

def ekg109(A, B, j, f, sa, sb, pre=40, post=18):
    fs0 = sb["f0"] - pre; y0 = H * EKG_Y; spd = (W + 80) / 31.0
    xh = lambda ff: -40 + spd * (ff - fs0)
    beats = [(xh(E.fe(E.th(50.62))), 190.0), (xh(E.fe(E.th(51.06))), 235.0)]
    fsplit0 = sb["f0"] - 5; s = smooth((f - fsplit0) / (sb["f0"] + post - 1 - fsplit0))
    so = 1 - (1 - s) ** 3
    o = B if s <= 0 else _zoom_about(B, 1 + 0.06 * (1 - s), W / 2, y0)
    lid = 1 - 0.55 * ((_GX[0] - W / 2) / (W / 2)) ** 2                     # an eye: wider in the middle than at the corners
    if s < 1:                                                              # the picture opens along the line
        if s <= 0: top = bot = A; ytop = ybot = np.full(W, y0, np.float32)
        else:
            dtx = -(y0 + 60) * np.clip(so * lid + so ** 3 * (1 - lid), 0, 1.2)      # the corners catch up at the end
            dbx = (H - y0 + 60) * np.clip(so * lid + so ** 3 * (1 - lid), 0, 1.2)
            ytop = (y0 + dtx).astype(np.float32); ybot = (y0 + dbx).astype(np.float32)
            top = cv2.remap(A, _GX, (_GY - dtx[None, :]).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            bot = cv2.remap(A, _GX, (_GY - dbx[None, :]).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        mt = np.clip((ytop[None, :] - _GY) / 3.0 + 0.5, 0, 1)[..., None]; mb = np.clip((_GY - ybot[None, :]) / 3.0 + 0.5, 0, 1)[..., None]
        o = top * mt + bot * mb + o * (1 - mt - mb)
    cv = np.zeros((H, W), np.float32)
    head = xh(f)
    if s <= 0:
        xs = np.arange(0, int(min(W, head)) + 1, 2, dtype=np.float32)
        if len(xs) > 1:
            ys = y0 + ekg_wave(xs, beats)
            pts = np.round(np.stack([xs, ys], 1) * 8).astype(np.int32)
            cv2.polylines(cv, [pts], False, 1.0, 3, cv2.LINE_AA, shift=3)
            age = np.clip((head - _GX[0]) / spd, 0, None)
            cv *= (0.30 + 0.70 * np.exp(-age / 9.0))[None, :]
            if 0 <= head <= W:
                hy = float(y0 + ekg_wave(np.array([head], np.float32), beats)[0])
                cv += 1.2 * np.exp(-(((_GX - head) ** 2 + (_GY - hy) ** 2) / (2 * 5.0 ** 2)))
    flat = smooth((f - (fsplit0 - 10)) / 10.0) * (1 - s)                  # the flat line brightens, then rides the edges
    if flat > 0:
        rows = (np.full(W, y0, np.float32),) if s <= 0 else (ytop, ybot)
        for yy in rows:
            cv += flat * (0.9 if s <= 0 else 0.6 * (1 - s)) * np.exp(-((_GY - yy[None, :]) / 1.6) ** 2)
    g1 = cv2.GaussianBlur(cv, (0, 0), 5); g2 = cv2.GaussianBlur(cv, (0, 0), 18)
    on = smooth((j + pre + 0.5) / 3.0)
    o = o * (1 - 0.15 * on * smooth((head) / 200.0) * (1 - s)) + (cv[..., None] * np.array([0.96, 0.98, 0.90], np.float32)
         + (g1 * 0.8 + g2 * 0.5)[..., None] * CYAN109) * on
    return np.clip(o, 0, 1)
TR2["ekg109"] = (ekg109, 40, 18)

# ---- THE GUST (the loop): on "action" he blows away as glowing dust, the side the wind hits first; the gust carries
# the dust left and up (a few near flakes rush past the lens), the room darkens to frame 0's dark, and the same gust
# brings new dust in from the right that settles, decelerating, into frame 0's figure; frame 0 resolves exactly.
DL_F0 = E.fe(E.th(53.0))
_DL = {}
def _fill_bg(img, P):
    q = 4; small = cv2.resize(img, (W // q, H // q), interpolation=cv2.INTER_AREA)
    ps = cv2.resize(P, (W // q, H // q), interpolation=cv2.INTER_AREA)
    wgt = np.clip(1 - ps * 1.4, 0, 1) ** 2
    num = cv2.GaussianBlur(small * wgt[..., None], (0, 0), 16); den = cv2.GaussianBlur(wgt, (0, 0), 16) + 1e-4
    fill = cv2.resize(num / den[..., None], (W, H), interpolation=cv2.INTER_LINEAR)
    return img * (1 - P[..., None]) + fill * P[..., None]

def _dl_setup(s):
    if "A" in _DL: return _DL
    IA, PA = base108(s, DL_F0); PA = np.clip(np.asarray(PA, np.float32), 0, 1)
    F0 = frame0_plate108(); P0 = _person(SHOTS[0], SHOTS[0]["f0"])
    P0 = np.zeros((H, W), np.float32) if P0 is None else P0
    rng = np.random.default_rng(1956)
    nA = _up(nz108(1971, 6) * 0.45 + nz108(1975, 1.6) * 0.55); nB = _up(nz108(1972, 6) * 0.45 + nz108(1976, 1.6) * 0.55)
    def field(P, n, rev):
        ys, xs = np.nonzero(P[::4, ::4] > 0.5)
        x0, x1 = (xs.min() * 4, xs.max() * 4) if len(xs) else (0, W)
        y0, y1 = (ys.min() * 4, ys.max() * 4) if len(ys) else (0, H)
        dirt = np.clip((_GX - x0) / max(1, x1 - x0), 0, 1); vy = np.clip((_GY - y0) / max(1, y1 - y0), 0, 1)
        if rev: return (1 - dirt) * 0.30 + vy * 0.40 + n * 0.30            # frame 0: from the right, his head first
        return dirt * 0.30 + (1 - vy) * 0.40 + n * 0.30                    # the stare: from the left, his body first, his face last
    rA = 0.46 * field(PA, nA, False)
    aB = 0.38 + 0.50 * field(P0, nB, True)
    def sample(P, img, step, fld):
        gy, gx = np.mgrid[0:H:step, 0:W:step].astype(np.float32)
        gx += rng.random(gx.shape, dtype=np.float32) * step; gy += rng.random(gy.shape, dtype=np.float32) * step
        ix = np.clip(gx.astype(int), 0, W - 1); iy = np.clip(gy.astype(int), 0, H - 1)
        k = P[iy, ix] > 0.5
        x, y = gx[k], gy[k]; ix, iy = ix[k], iy[k]
        col = img[iy, ix].astype(np.float32); Lc = lum(col[None])[0][:, None]
        col = col * 0.50 + CYAN109[None] * (0.35 + 0.65 * Lc) * 0.85
        return dict(x=x, y=y, col=col, t=fld[iy, ix], near=rng.random(len(x)) < 0.035, sp=rng.uniform(0.8, 1.25, len(x)).astype(np.float32))
    sw = [_up(nz108(1973, 14)) - 0.5, _up(nz108(1974, 14)) - 0.5]
    _DL.update(A=sample(PA, IA, 6, rA), B=sample(P0, F0, 6, aB), rA=rA, aB=aB, P0=P0, F0=F0, bgB=_fill_bg(F0, P0),
               sw=[cv2.resize(m, (W // 8, H // 8), interpolation=cv2.INTER_AREA) for m in sw])
    return _DL

DL_WIND = np.array([-1.0, -0.42], np.float32) / math.hypot(1.0, 0.42)
def _dl_flight(x, y, tau, sign, sw):
    """positions after tau seconds of flight from (x, y) along the gust (sign -1 = backwards from an arrival)."""
    from scipy.ndimage import map_coordinates
    px, py = x.copy(), y.copy(); dt = tau / 6.0
    for k in range(6):
        tk = tau * (k + 0.5) / 6.0
        spd = 260 + 1150 * np.clip(tk / 0.40, 0, 1)
        c = np.stack([np.clip(py / 8, 0, H / 8 - 1), np.clip(px / 8, 0, W / 8 - 1)])
        vx = DL_WIND[0] * spd + map_coordinates(sw[0], c, order=1) * 700
        vy = DL_WIND[1] * spd + map_coordinates(sw[1], c, order=1) * 700
        px = px + sign * vx * dt; py = py + sign * vy * dt
    return px, py

def dust_loop109(out, f, s, person=None):
    last = E.DUR_F - 1
    if f < DL_F0: return out
    if f >= last: return frame0_plate108().copy()
    D = _dl_setup(s); TL = (last - DL_F0) / FPS
    t = (f - DL_F0) / (last - DL_F0)
    P = np.zeros((H, W), np.float32) if person is None else np.clip(np.asarray(person, np.float32), 0, 1)
    bgA = _fill_bg(out, P); wb = smooth((t - 0.22) / 0.45)
    o = bgA * (1 - wb) + D["bgB"] * wb
    rel = np.clip((t - D["rA"]) / 0.07, 0, 1); rel = rel * rel * (3 - 2 * rel)
    Rm = P * (1 - rel); o = o * (1 - Rm[..., None]) + out * Rm[..., None]
    fm = np.clip((t - D["aB"]) / 0.07, 0, 1); fm = fm * fm * (3 - 2 * fm)
    ghost = D["P0"] * (1 - fm) * 0.50 * smooth((t - 0.30) / 0.25)          # a faint frame 0 gathers under the dust
    o = o * (1 - ghost[..., None]) + D["F0"] * ghost[..., None]
    Fm = D["P0"] * fm; o = o * (1 - Fm[..., None]) + D["F0"] * Fm[..., None]
    eA = np.clip(P * rel * (1 - rel) * 4, 0, 1); eB = np.clip(D["P0"] * fm * (1 - fm) * 4, 0, 1)
    o = o + cv2.GaussianBlur(eA + eB, (0, 0), 1.5)[..., None] * CYAN109 * 0.22
    layers = []
    pa = D["A"]; tau = (t - pa["t"]) * TL; k = tau > 0
    if k.any():
        x, y = _dl_flight(pa["x"][k], pa["y"][k], tau[k] * pa["sp"][k], 1.0, D["sw"])
        al = np.clip(tau[k] / 0.04, 0, 1) * np.exp(-tau[k] / 0.30) * (0.45 + 1.2 * np.exp(-tau[k] / 0.08))
        layers.append((x, y, pa["col"][k], al.astype(np.float32), pa["near"][k], tau[k]))
    pb = D["B"]; tb = (pb["t"] - t) * TL; k = (tb > 0) & (tb < 0.75)
    if k.any():
        x, y = _dl_flight(pb["x"][k], pb["y"][k], tb[k] * pb["sp"][k], -1.0, D["sw"])
        al = np.clip((0.60 - tb[k]) / 0.20, 0, 1) * np.clip(tb[k] / 0.06, 0, 1) * (0.45 + 1.0 * np.exp(-tb[k] / 0.10))
        layers.append((x, y, pb["col"][k], al.astype(np.float32), pb["near"][k], tb[k]))
    if layers:
        X = np.concatenate([l[0] for l in layers]); Y = np.concatenate([l[1] for l in layers])
        C = np.concatenate([l[2] for l in layers]); AL = np.concatenate([l[3] for l in layers])
        NR = np.concatenate([l[4] for l in layers]); TU = np.concatenate([l[5] for l in layers])
        far = ~NR
        rgb, aa = splat109(X[far], Y[far], C[far], AL[far] * 1.6, q=2, sig=0.55)
        dust = cv2.resize(rgb, (W, H), interpolation=cv2.INTER_LINEAR); da = cv2.resize(aa, (W, H), interpolation=cv2.INTER_LINEAR)
        if NR.any():                                                       # near flakes rush past the lens, soft and big
            gx = W / 2 + (X[NR] - W / 2) * (1 + 1.6 * TU[NR]); gy = H / 2 + (Y[NR] - H / 2) * (1 + 1.6 * TU[NR])
            r2, a2 = splat109(gx, gy, C[NR], AL[NR] * 3.0, q=4, sig=2.6)
            dust = dust + cv2.resize(r2, (W, H), interpolation=cv2.INTER_LINEAR)
        glow = cv2.GaussianBlur(cv2.resize(dust, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 5)
        o = o * (1 - np.clip(da, 0, 1)[..., None] * 0.30) + dust * 0.85 + cv2.resize(glow, (W, H)) * 0.45
    o = mist_veil(o, 0.07 * math.sin(math.pi * t), f, 2.5)
    we = smooth((t - 0.90) / 0.10)
    return np.clip(o * (1 - we) + D["F0"] * we, 0, 1)

def beat_phase(f):
    """rev 1: the beat camera rests through the pass, the print and the ending (from the monitor on)."""
    e = f / FPS / E.HB; ph = (e % 2) * E.HB; bi = int(e // 2)
    hook = (E.E_BEAT + 2 <= e < 49.5) and not (10 <= e < 13.5) and not (18.5 <= e < 19.5) and not (29.5 <= e < 31) \
        and not (37.4 <= e < 40)
    return ph, bi, hook, False

def render(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin")
    out, person = base108(s, f)
    if tin in TR2 and k < TR2[tin][2] and P is not None:
        out = TR2[tin][0](edge108(P, "last"), out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, edge108(n_, "first"), kn, f, s, n_)
    if s.get("tout") == "vanish_loop109": out = vanish_loop109(out, f, s, person)
    if s.get("tout") == "dust_loop109": out = dust_loop109(out, f, s, person)
    out = beat_fx(out, f)
    out = title109(out, f)
    out = flash_governor(out)
    return (np.clip(finish109(out, f, s), 0, 1) * 255 + 0.5).astype(np.uint8)

# ---- the ending without spins (the owner removed the headspin for flow; the roll and the flip went with it) ----------
# RED WASH (the kitchen -> the red-lit drive): brake-light red washes over the frame from the right, the kitchen sinks
# into it and the red-lit drive comes up out of it.
RED109 = np.array([0.05, 0.07, 0.92], np.float32)
def redwash109(A, B, j, f, sa, sb, pre=8, post=12):
    q = (j + pre + 0.5) / (pre + post); k = math.sin(math.pi * clamp(q, 0, 1)) ** 1.3
    g = np.clip(0.60 + (_GX - W * (0.9 - 0.9 * smooth(q))) / (W * 0.7), 0, 1)[..., None]
    w = smooth((q - 0.40) / 0.22); img = A * (1 - w) + B * w if 0 < w < 1 else (A if j < 0 else B)
    L = lum(img)[..., None]
    lit = (L * 1.5 + 0.10) * RED109
    o = img * (1 - k * g * 0.95) + lit * (k * g * 0.95)
    return np.clip(o, 0, 1)
TR2["redwash109"] = (redwash109, 8, 12)

# STREETLIGHT (the drive -> the syringe): a streetlight passes over the car: a soft band of cold light crosses the
# frame diagonally upward, and the next shot is under it.
def streetlight109(A, B, j, f, sa, sb, pre=8, post=10):
    q = (j + pre + 0.5) / (pre + post); k = math.sin(math.pi * clamp(q, 0, 1))
    sc = _GX * 0.42 - _GY * 0.91; lo, hi = -0.91 * H - 60, 0.42 * W + 60
    p = hi + (lo - hi) * smooth(q)
    band = np.exp(-((sc - p) / 170.0) ** 2)[..., None]
    w = smooth((q - 0.42) / 0.16); img = A * (1 - w) + B * w if 0 < w < 1 else (A if j < 0 else B)
    o = img * (1 + 1.05 * band * k) + band * k * np.array([0.20, 0.19, 0.17], np.float32)
    return np.clip(o, 0, 1)
TR2["streetlight109"] = (streetlight109, 8, 10)

# ---- a mirrored pack shot, flipped back (p7's tape shot reads DO NOT CROSS backwards) --------------------------------
_base108_pre109r1 = base108
def base108(s, f):
    img, person = _base108_pre109r1(s, f)
    if s.get("hflip"):
        img = np.ascontiguousarray(img[:, ::-1])
        if person is not None: person = np.ascontiguousarray(np.asarray(person)[:, ::-1])
    return img, person

# ============================================================================ v109 rev 2 (the owner's notes)
# "change the heart monitor on the 21-second mark. You don't have to replace this with anything" -> it is gone: a clean
# cut on the downbeat (e52) with the beat camera's punch. "make the fire transition graphic ... stem from the actual
# picture that's burning and try to make it tied into that transition" -> THE PHOTO BURNS: the fire starts where the real
# flame touches the photo in his hand (tracked through the shot), eats through the photo first (the next shot shows
# through the burnt photo), then spills off the photo's edges and burns the frame away.
BN_KEYS = [(1080, 0.800, 0.672), (1089, 0.830, 0.647), (1097, 0.780, 0.645), (1105, 0.750, 0.660)]   # the flame's foot on the photo
def _bn_flame(f):
    fs = [k[0] for k in BN_KEYS]
    return (float(np.interp(f, fs, [k[1] for k in BN_KEYS])) * W, float(np.interp(f, fs, [k[2] for k in BN_KEYS])) * H)

_BP = {}
def _bp_setup():
    if "T" not in _BP:
        fx0, fy0 = _bn_flame(BN_KEYS[0][0])
        quad = np.array([[fx0 - 0.31 * W, fy0 - 0.065 * H], [fx0 + 0.035 * W, fy0 - 0.010 * H],
                         [fx0 + 0.12 * W, fy0 + 0.42 * H], [fx0 - 0.34 * W, fy0 + 0.42 * H]], np.float32)
        m = np.zeros((H, W), np.uint8); cv2.fillConvexPoly(m, np.round(quad).astype(np.int32), 255)
        n1 = _up(nz108(1951, 10)) - 0.5; n2 = _up(nz108(1952, 3)) - 0.5; n3 = _up(nz108(1953, 1.2)) - 0.5
        m = cv2.remap(m, _GX + 70 * n2, _GY + 70 * (_up(nz108(1954, 3)) - 0.5), cv2.INTER_LINEAR)   # a ragged photo, not a box
        photo = cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), 6)
        d0 = np.sqrt((_GX - fx0) ** 2 + ((_GY - fy0) * 1.1) ** 2)
        t_in = 0.58 * d0 + 70 * n1 + 30 * n2                                  # paper burns fast, from the flame's corner
        dout = cv2.distanceTransform(255 - m, cv2.DIST_L2, 5).astype(np.float32)
        t_full = float(np.percentile(t_in[m > 0], 80))
        t_out = t_full * 0.45 + 0.35 * d0 + dout * np.where(_GY < fy0, 0.75, 0.95) + 170 * n1 + 70 * n2   # then it spills off its edges
        T = photo * t_in + (1 - photo) * t_out + 26 * n3
        _BP.update(T=T.astype(np.float32), Tmax=float(T.max()) + 40, photo=photo, ref=(fx0, fy0))
    return _BP

def burn109(A, B, j, f, sa, sb, pre=30, post=16):
    q = (j + pre + 0.5) / (pre + post)
    D = _bp_setup(); fx, fy = _bn_flame(min(f, sa["f1"] - 1)); dx, dy = fx - D["ref"][0], fy - D["ref"][1]
    Tf = D["T"] if abs(dx) + abs(dy) < 0.5 else cv2.warpAffine(D["T"], np.float32([[1, 0, dx], [0, 1, dy]]), (W, H), borderMode=cv2.BORDER_REPLICATE)
    Rq = -30 + (D["Tmax"] + 30) * ein(clamp(q, 0, 1), 1.35)
    s_ = Tf - Rq                                                           # < 0 burnt
    hole = np.clip(-s_ / 3.0 + 0.5, 0, 1)
    char = np.clip(1 - s_ / 22.0, 0, 1) * (1 - hole)
    scorch = np.clip(1 - (s_ - 22) / 90.0, 0, 1) * (s_ > 0)
    a = A * (1 - (0.22 * scorch)[..., None]) + (0.05 * scorch)[..., None] * np.array([0.0, 0.10, 0.30], np.float32)
    a = a * (1 - char[..., None] * 0.85) + char[..., None] * np.array([0.02, 0.03, 0.05], np.float32)
    o = a * (1 - hole[..., None]) + B * hole[..., None]
    live = float(Rq > 0) * (1 - smooth((q - 0.94) / 0.06))
    core = np.exp(-((s_ - 2) / 2.5) ** 2) * live
    ember = np.exp(-((s_ - 6) / 9.0) ** 2) * live * (0.7 + 0.6 * _up(nz108(1945, 1.5)))
    glow = cv2.GaussianBlur(ember, (0, 0), 10)
    o = o + core[..., None] * np.array([0.70, 0.90, 1.0], np.float32) * 0.85 + ember[..., None] * np.array([0.06, 0.34, 1.0], np.float32) * 0.75 \
        + glow[..., None] * np.array([0.03, 0.20, 0.80], np.float32) * 0.45
    rng = np.random.default_rng(1957); n = 300                              # sparks lift off the burning edge
    th_ = rng.uniform(0, 2 * np.pi, n); dd = rng.uniform(20, 900, n); rise = rng.uniform(260, 620, n); life = rng.uniform(0.22, 0.45, n)
    sx = np.clip(fx + dd * np.cos(th_), 0, W - 1); sy = np.clip(fy + dd * np.sin(th_), 0, H - 1)
    tb = Tf[sy.astype(int), sx.astype(int)]                                 # when the front reaches the spark's seat
    qb = ((tb + 30) / (D["Tmax"] + 30)) ** (1 / 1.35); age = (q - qb) * (pre + post) / FPS
    k = (age >= 0) & (age < life)
    if k.any():
        x = sx[k] + rng.uniform(-60, 60, n)[k] * age[k] * 3; y = sy[k] - rise[k] * age[k]
        al = (rng.uniform(0.6, 1.4, n)[k] * np.exp(-age[k] / (0.4 * life[k]))).astype(np.float32)
        cols = np.tile(np.array([[0.35, 0.70, 1.0]], np.float32), (int(k.sum()), 1))
        rgb, _ = splat109(x, y, cols, al, q=2, sig=1.2)
        o = o + cv2.resize(rgb, (W, H), interpolation=cv2.INTER_LINEAR) * 3.0
    return np.clip(o, 0, 1)
TR2["burn109"] = (burn109, 30, 16)

def beat_phase(f):
    """rev 2: the beat camera runs through the syringe shot and lands one punch on the cut to his stare (e52), then rests."""
    e = f / FPS / E.HB; ph = (e % 2) * E.HB; bi = int(e // 2)
    hook = (E.E_BEAT + 2 <= e < 52.6) and not (10 <= e < 13.5) and not (18.5 <= e < 19.5) and not (29.5 <= e < 31) \
        and not (37.4 <= e < 40) and not (49.5 <= e < 50.4)
    return ph, bi, hook, False

# ============================================================================ v109 rev 3 (the owner's notes)
# "it's just missing one more focal point ... one more really, really cool, custom, unique graphic into a transition ...
# the finishing touch". THE PHANTOM'S TRAIL (the dock -> the night hunt; replaces the reused hot molasses): a ribbon of
# blood-red light, the only colour the phantom leaves, streaks in out of the dark and circles him: behind his shoulders
# (his matte hides it) and in front of his waist, never across his face; it twists like silk, white-hot at its core,
# and sheds embers; then it breaks from the orbit and dives at the lens, widening until the next shot is inside it.
TR_RED = np.array([0.10, 0.09, 0.96], np.float32); TR_HOT = np.array([0.80, 0.88, 1.0], np.float32)
_TRL = {}
def _trail_frame(sa):
    if sa["n"] not in _TRL:
        P = _person(sa, sa["f1"] - 1); P = np.zeros((H, W), np.float32) if P is None else P
        ys, xs = np.nonzero(P[::8, ::8] > 0.5)
        if len(xs) > 30: cx = float(np.median(xs) * 8); ytop = float(np.percentile(ys, 3) * 8); ybot = float(np.percentile(ys, 97) * 8)
        else: cx, ytop, ybot = W / 2, H * 0.2, H
        fs = face_scr(sa, sa["f1"] - 1); fy = fs[1] if fs else ytop + 0.08 * H
        _TRL[sa["n"]] = (cx, fy, ybot)
    return _TRL[sa["n"]]

def _trail_pos(t, cx, fy, ybot, td):
    """the head on screen at time t (s): x, y, perspective scale p, in front (z > 0) or behind him."""
    t = np.asarray(t, np.float64)
    th_ = -2.2 + 2 * np.pi * 1.3 * t / td                                     # ~1.3 turns before the dive
    rin = 1 + 2.0 * np.exp(-np.clip(t, 0, None) / 0.10)                       # it spirals in from far out
    yc = min(fy + 0.36 * H, ybot - 0.10 * H)                                  # the orbit: his chest and waist
    Z = np.sin(th_); X = 0.37 * W * rin * np.cos(th_)
    Y = yc + 0.075 * H * Z - 0.10 * H * np.clip(-Z, 0, 1)                     # front low (waist), back high (shoulders)
    p = 1.0 / (1 - 0.30 * Z)
    x = cx + X * p; y = H * 0.5 + (Y - H * 0.5) * p
    b = np.clip((t - td) / 0.30, 0, 1); b = b * b * (3 - 2 * b)             # the dive: through his chest, out past the lens
    xd = cx + 0.06 * W + 0.95 * W * b ** 1.6; yd = yc + 0.05 * H + 0.30 * H * b ** 1.6
    return x * (1 - b) + xd * b, y * (1 - b) + yd * b, p * (1 - b) + (1 + 9 * b * b) * b, Z * (1 - b) + b

def trail109(A, B, j, f, sa, sb, pre=42, post=18):
    cx, fy, ybot = _trail_frame(sa)
    t = (j + pre + 0.5) / FPS; T = (pre + post) / FPS; td = pre / FPS - 0.14
    P = _person(sa, f) if j < 0 else _person(sa, sa["f1"] - 1)
    P = np.zeros((H, W), np.float32) if P is None else _pp_clean(P)
    L = 0.55; tau = np.linspace(0, L, 180)                                    # the trail: the head's last 0.55 s
    lb = np.zeros((H, W), np.float32); lf = np.zeros((H, W), np.float32)
    for dt_, dy_, wsc, bri, ph in ((0.0, 0.0, 1.0, 1.0, 0.4), (0.07, 0.035 * H, 0.42, 0.70, 2.1)):   # the ribbon and a thin companion strand
        xs, ys, p, Z = _trail_pos(t - dt_ - tau, cx, fy, ybot, td); ys = ys + dy_ * (1 - np.clip((t - dt_ - tau - td) / 0.2, 0, 1))
        ok = (t - dt_ - tau) >= 0
        tw = np.abs(np.cos(2 * np.pi * (1.7 * (t - tau)) + ph))                # the silk twists: flat (wide, bright) / edge-on
        wd = 56 * wsc * p * (0.22 + 0.78 * tw) * (1 - 0.70 * tau / L)
        fade = bri * (1 - tau / L) ** 1.2 * (0.55 + 0.45 * tw) * (1 - smooth((t - td - 0.22) / 0.14))
        seg = [i for i in range(len(tau) - 1) if ok[i] and ok[i + 1] and wd[i] < 900 and fade[i] > 0.01]
        for wk, vk in ((1.0, 0.42), (0.62, 0.74), (0.24, 1.08)):                # red silk, a brighter middle, a white-hot core
            for i in seg:
                cvs = lf if Z[i] > 0 else lb
                cv2.line(cvs, (int(round(xs[i] * 4)), int(round(ys[i] * 4))), (int(round(xs[i + 1] * 4)), int(round(ys[i + 1] * 4))),
                         float(vk * fade[i]), int(max(1, round(wd[i] * wk))), cv2.LINE_AA, shift=2)
    lb = lb * (1 - P)                                                          # behind him: his body hides it
    allL = lb + lf
    def col(Lm):
        Lm = np.clip(Lm, 0, 1.2)[..., None]
        return TR_RED * np.clip(Lm * 1.9, 0, 1) + (TR_HOT - TR_RED) * np.clip((Lm - 0.62) * 2.4, 0, 1)
    g1 = cv2.GaussianBlur(allL, (0, 0), 10)
    g2 = cv2.resize(cv2.GaussianBlur(cv2.resize(allL, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 10), (W, H))
    light = col(allL) + (g1 * 0.85 + g2 * 1.3)[..., None] * TR_RED
    o = A * (1 - 0.20 * smooth(t / 0.15))                                      # the night deepens around it
    o = 1 - (1 - np.clip(o, 0, 1)) * (1 - np.clip(light, 0, 1))
    bw = 3600 * ein(clamp((t - td - 0.08) / 0.30, 0, 1), 1.7)                 # the dive: the ribbon swells behind its head, the next shot inside
    if bw > 3:
        tb_ = np.linspace(0.03, 0.24, 48); hx, hy, _, _ = _trail_pos(t - tb_, cx, fy, ybot, td)
        pts = np.round(np.stack([hx, hy], 1) * 4).astype(np.int32)
        win = np.zeros((H, W), np.float32); cv2.polylines(win, [pts], False, 1.0, int(min(5000, bw)), cv2.LINE_AA, shift=2)
        win = cv2.GaussianBlur(win, (0, 0), 3.0)
        win = np.maximum(win, smooth((t - (T - 0.07)) / 0.06))
        rim = cv2.GaussianBlur(np.clip(win * (1 - win) * 4, 0, 1), (0, 0), 2.5) * (1 - smooth((t - (T - 0.10)) / 0.08))
        Bz = _zoom_about(B, 1 + 0.08 * (1 - smooth((t - td) / (T - td))), W / 2, H * 0.5)
        o = o * (1 - win[..., None]) + Bz * win[..., None]
        o = 1 - (1 - o) * (1 - np.clip(rim[..., None] * (TR_RED + (TR_HOT - TR_RED) * 0.70) * 1.3
                                       + cv2.GaussianBlur(rim, (0, 0), 16)[..., None] * TR_RED * 1.3, 0, 1))
    rng = np.random.default_rng(1961); n = 220                                 # embers shed from the head
    tb = rng.uniform(0.05, td + 0.12, n); age = t - tb; k = (age >= 0) & (age < 0.40)
    if k.any():
        hx, hy, hp, hz = _trail_pos(tb[k], cx, fy, ybot, td)
        ex = hx + rng.uniform(-110, 110, n)[k] * age[k]; ey = hy + 420 * age[k] ** 2 + rng.uniform(-50, 50, n)[k] * age[k]
        al = (np.exp(-age[k] / 0.15) * rng.uniform(0.5, 1.3, n)[k]).astype(np.float32)
        hide = (hz < 0) & (P[np.clip(ey, 0, H - 1).astype(int), np.clip(ex, 0, W - 1).astype(int)] > 0.5)
        al = (al * ~hide).astype(np.float32)
        rgb, _ = splat109(ex, ey, np.tile(np.array([[0.30, 0.50, 1.0]], np.float32), (int(k.sum()), 1)), al, q=2, sig=1.1)
        o = o + cv2.resize(rgb, (W, H), interpolation=cv2.INTER_LINEAR) * 2.6
    return np.clip(o, 0, 1)
TR2["trail109"] = (trail109, 42, 18)

def beat_phase(f):
    """rev 3: the camera also rests while the trail circles him and dives (e33.6-36.4)."""
    e = f / FPS / E.HB; ph = (e % 2) * E.HB; bi = int(e // 2)
    hook = (E.E_BEAT + 2 <= e < 52.6) and not (10 <= e < 13.5) and not (18.5 <= e < 19.5) and not (29.5 <= e < 31) \
        and not (33.6 <= e < 36.4) and not (37.4 <= e < 40) and not (49.5 <= e < 50.4)
    return ph, bi, hook, False

# ============================================================================ v110 — SLEEPWALKER (Dexter × "Sleepwalker (Slowed)")
# His waking life is a sleepwalk, and the nightmare that made him loops forever. Look 3 A.M.: sodium amber highlights,
# navy shadows, a dream bloom and soft edges; blood stays red. One title, I'M LOSING POWER, lit like a failing tube.
# New: the headlight across the bed, the brownout, the fog roll, the nod-off, THROUGH THE FAN (the drop), THE BARREL
# (the focal point), THE FOLD, THE SPATTER (the blood room's own blood arrives first), THE FALL into bed (the loop).
_L110 = {}
AMB110 = np.array([0.30, 0.66, 1.00], np.float32)          # BGR sodium amber
NAVY110 = np.array([0.060, 0.012, -0.030], np.float32)    # BGR shadow push
_grade_pre110 = grade
def grade(img, s, f):
    if s.get("look") != "sleep110": return _grade_pre110(img, s, f)
    if "c" not in _L110:
        x = np.linspace(0, 1, 1024, dtype=np.float32)
        _L110["c"] = (x, PchipInterpolator([0, .05, .2, .5, .8, .95, 1], [0.022, 0.038, 0.135, 0.43, 0.76, 0.90, 0.95])(x).astype(np.float32))
    g, gains = corr9(s); ev = s.get("ev") or 0; lx, ly = _L110["c"]; gains = tuple(float(v) for v in gains)
    x = apply_lut3(img, tone_lut(("sl110", s["n"], ev, float(g), gains), gains, g, ev, lx, ly)) if in_unit(img) else \
        np.interp(np.clip(np.clip(img * np.array(gains, np.float32), 0, 1) ** g * 2 ** ev, 0, 1), lx, ly).astype(np.float32)
    Bc, Gc, Rc = (np.ascontiguousarray(x[..., c]) for c in range(3))
    L = Bc * 0.114 + Gc * 0.587 + Rc * 0.299
    red = np.clip((Rc - 1.85 * np.maximum(Gc, Bc) - s.get("redthr", 0.06)) * 3.0, 0, 1)
    sat = 0.48 + 0.10 * np.clip((Rc - Bc) * 2.0, 0, 1) * (1 - red) + 0.55 * red
    hi = np.clip((L - 0.42) * 1.9, 0, 1); sh = np.clip(1 - L * 1.7, 0, 1) ** 1.5
    o = np.empty(x.shape, np.float32)
    for ch, P in enumerate((Bc, Gc, Rc)):
        v = L + (P - L) * sat
        v += sh * NAVY110[ch] + hi * L * (-0.11, 0.015, 0.10)[ch]
        o[..., ch] = v
    return np.clip(o, 0, 1, out=o)

_E110 = {}
def _edge110():
    if "e" not in _E110:
        r = np.sqrt(((_GX - W / 2) / (W / 2)) ** 2 * 0.9 + ((_GY - H / 2) / (H / 2)) ** 2)
        _E110["e"] = (np.clip((r - 0.62) / 0.55, 0, 1) ** 1.6 * 0.85)[..., None].astype(np.float32)
    return _E110["e"]

def finish110(out, f, s=None):
    L = lum(out)
    q = cv2.resize(np.clip(L - 0.55, 0, 1), (W // 8, H // 8), interpolation=cv2.INTER_AREA)
    bloom = cv2.resize(cv2.GaussianBlur(q, (0, 0), 6), (W, H), interpolation=cv2.INTER_LINEAR)
    soft = cv2.resize(cv2.GaussianBlur(cv2.resize(out, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 2.0), (W, H), interpolation=cv2.INTER_LINEAR)
    e = _edge110(); o = out * (1 - e) + soft * e                                  # dream edges
    g = grain(f, 0.014)[..., 0]; v = VIG[..., 0]
    for ch in range(3):
        oc = o[..., ch]; oc += bloom * AMB110[ch] * 0.30; oc *= v; oc += g
    return np.clip(o, 0, 1, out=o)

def beat_phase(f):
    e = f / FPS / E.HB; ph = (e % 2) * E.HB; bi = int(e // 2)
    hook = (30.5 <= e < 68) and not (42.6 <= e < 47.5) and not (51.5 <= e < 57.5) and not (64.5 <= e < 68)
    return ph, bi, hook, False

# ---- the mains (the hero): the room light that fails on "I'm losing power" and surges back on the drop
T_IM, T_LOSING, T_POWER, T_OUT = E.th(10.2), E.th(13.37), E.th(16.33), E.th(19.3)
def _dips(t, t0, depth, n=3, gap=0.045):
    v = 1.0
    for k in range(n):
        tk = t0 + 0.03 + k * gap * (1 + 0.37 * k)
        v -= depth * (1 - k * 0.25) * math.exp(-((t - tk) / 0.012) ** 2)
    return v

def power_light110(f):
    t = f / FPS
    if t < T_IM - 0.1 or t > E.th(21): return 1.0
    lv = min(_dips(t, T_IM, 0.35), _dips(t, T_LOSING, 0.42), _dips(t, T_POWER, 0.55, 4))
    lv = lv * (0.97 + 0.03 * math.sin(t * 2 * math.pi * 7.3))                     # the hum
    return clamp(lv, 0.0, 1.0)

def light_scene110(out, f):
    """the light above him (the title shot): the room dims from the top when the mains dip."""
    lv = power_light110(f)
    if lv > 0.999: return out
    m = 1 - (1 - lv) * (0.55 + 0.45 * (1 - _GY / H))
    return out * m[..., None]

# ---- THE TITLE: I'M LOSING POWER, each word lights like a fluorescent tube on its sung onset (blinks, then a steady
# hum), and on the brownout the letters die one by one.
_TT110 = {}
def _tube(t, t_on, i):
    if t < t_on: return 0.0
    a = smooth((t - t_on) / 0.035)
    for k, (dt, d) in enumerate(((0.05, 0.85), (0.10, 0.6), (0.16, 0.35))):
        a *= 1 - d * math.exp(-((t - t_on - dt - 0.007 * i) / 0.012) ** 2)
    return a * (0.93 + 0.07 * math.sin(t * 2 * math.pi * 7.3 + i * 1.7))

def title110(out, f):
    t = f / FPS
    if t < T_IM - 0.02 or t > E.th(21.2): return out
    if "m" not in _TT110:
        l1 = [(c, text_mask(c, F_BLACK, 138) if c != " " else None) for c in "I'M LOSING"]; l2 = [(c, text_mask(c, F_BLACK, 205)) for c in "POWER"]
        _TT110["m"] = (l1, l2)
    l1, l2 = _TT110["m"]
    lay = np.zeros((H, W), np.float32)
    def place(letters, y, t_on_of):
        wsum = sum((m.shape[1] if m is not None else 40) for c, m in letters) + 10 * (len(letters) - 1)
        x = (W - wsum) / 2
        for i, (c, m) in enumerate(letters):
            if c == " ": x += 40 + 10; continue
            t_on = t_on_of(i); a = _tube(t, t_on, i)
            td = T_OUT + 0.055 * ((i * 7) % 11) * 0.5 + 0.02 * i                        # the brownout takes them one by one
            if t > td: a *= max(0.0, 1 - smooth((t - td) / 0.14)) * (0.70 + 0.30 * math.cos((t - td) * 2 * math.pi * 4.0 + i))
            if a > 0.003:
                mm = m.astype(np.float32) / (m.max() + 1e-6); h_, w_ = mm.shape; yy, xx = int(y), int(x)
                ys, xs, ye, xe = max(0, yy), max(0, xx), min(H, yy + h_), min(W, xx + w_)
                if ye > ys and xe > xs: lay[ys:ye, xs:xe] = np.maximum(lay[ys:ye, xs:xe], mm[ys - yy:ye - yy, xs - xx:xe - xx] * a)
            x += m.shape[1] + 10
    place(l1, H * 0.640, lambda i: T_IM if i < 3 else T_LOSING + 0.012 * (i - 4))
    place(l2, H * 0.708, lambda i: T_POWER + 0.012 * i)
    if lay.max() < 0.003: return out
    g1 = cv2.GaussianBlur(lay, (0, 0), 8); g2 = cv2.GaussianBlur(cv2.resize(lay, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 7)
    g2 = cv2.resize(g2, (W, H), interpolation=cv2.INTER_LINEAR)
    o = out * (1 - 0.88 * lay[..., None]) + lay[..., None] * np.array([0.82, 0.93, 1.0], np.float32) \
        + (g1 * 0.55 + g2 * 0.9)[..., None] * AMB110 * 0.55
    return np.clip(o, 0, 1)

# ---- HEADLIGHT (the bed -> the yard): a car passes outside; its light crosses the bed through the window (two soft
# panes of light with the window's cross in them) and the next shot is under the brightest pass.
def _pane(cx, cy, w, h, ang, soft=46.0):
    ca, sn = math.cos(ang), math.sin(ang)
    u = (_GX - cx) * ca + (_GY - cy) * sn; v = -(_GX - cx) * sn + (_GY - cy) * ca
    m = np.clip((w / 2 - np.abs(u)) / soft, 0, 1) * np.clip((h / 2 - np.abs(v)) / soft, 0, 1)
    bar = 1 - 0.55 * (np.exp(-(u / 9.0) ** 2) + np.exp(-(v / 9.0) ** 2)).clip(0, 1)
    return m * bar

def headlight110(A, B, j, f, sa, sb, pre=30, post=16):
    q = (j + pre + 0.5) / (pre + post); ang = math.radians(-24)
    p0, p1 = np.array([-0.45 * W, -0.10 * H]), np.array([1.45 * W, 1.05 * H])
    c = p0 + (p1 - p0) * (0.06 + 0.88 * q)
    m = _pane(c[0], c[1], 0.66 * W, 0.30 * H, ang) + 0.55 * _pane(c[0] - 0.16 * W, c[1] + 0.05 * H, 0.50 * W, 0.24 * H, ang)
    m = np.clip(m, 0, 1.3)
    w = smooth((j + 6) / 12.0); img = A * (1 - w) + B * w
    o = img * (1 + 0.80 * m[..., None]) + m[..., None] * AMB110 * 0.06
    return np.clip(o, 0, 1)
TR2["headlight110"] = (headlight110, 30, 16)

# ---- BROWNOUT (the light -> the fog): the mains fail: the light stutters, browns out to a dying orange, the room goes
# dark, and the fog comes up out of the dark, cold.
def brownout110(A, B, j, f, sa, sb, pre=18, post=22):
    q = (j + pre + 0.5) / (pre + post)
    lv = 1.0
    for qk, d in ((0.06, 0.55), (0.15, 0.70), (0.24, 0.80)):
        lv -= d * math.exp(-((q - qk) / 0.025) ** 2)
    lv = min(lv, 1 - 0.80 * smooth((q - 0.20) / 0.22))                         # down to 20 %
    lv = max(lv, 0.20) if q < 0.5 else 0.20 + 0.80 * smooth((q - 0.50) / 0.50)
    img = A if j < 0 else B
    warm = (1 - lv) * (1 if j < 0 else 0.3)
    tint = np.array([1 - 0.55 * warm, 1 - 0.22 * warm, 1.0], np.float32)
    return np.clip(img * lv * tint, 0, 1)
TR2["brownout110"] = (brownout110, 18, 22)

# ---- FOG ROLL (the fog room -> asleep): the room's fog billows across the lens from the right, thick, and thins away
# on him as his eyes close.
def fogwipe110(A, B, j, f, sa, sb, pre=20, post=22):
    q = (j + pre + 0.5) / (pre + post)
    n1 = _up(nz108(1101, 12)); n2 = _up(nz108(1102, 4))
    sh = int(f * 6) % W; n = np.roll(n1, -sh, axis=1) * 0.65 + np.roll(n2, -int(f * 11) % W, axis=1) * 0.35
    xf = -350 + (W + 700) * smooth(q / 0.52)
    dens = np.clip((xf - (W - _GX) + (n - 0.5) * 520) / 320.0, 0, 1) * 0.85
    dens = dens * (1 - smooth((q - 0.50) / 0.50))
    img = A if j < 0 else B
    soft = cv2.resize(cv2.GaussianBlur(cv2.resize(img, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 5), (W, H))
    fogc = soft * 0.35 + np.array([0.80, 0.74, 0.64], np.float32) * (0.45 + 0.35 * n[..., None])
    return np.clip(img * (1 - dens[..., None]) + fogc * dens[..., None], 0, 1)
TR2["fogwipe110"] = (fogwipe110, 20, 22)

# ---- FALLING ASLEEP (asleep -> the fan room): his head goes back and we fall with it: the picture drops away upward with
# vertical motion blur, and the fan room rises into place from below (the fall the loop repeats)
def _vblur_shift(img, dy, streak):
    o = cv2.warpAffine(img, np.float32([[1, 0, 0], [0, 1, dy]]), (W, H), borderMode=cv2.BORDER_REPLICATE) if abs(dy) > 0.2 else img   # never mirror a face
    L = int(abs(streak) / 4)
    if L < 2: return o
    sm = cv2.resize(o, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    sm = cv2.filter2D(sm, -1, np.ones((L, 1), np.float32) / L, borderType=cv2.BORDER_REPLICATE)   # a continuous vertical streak
    return cv2.resize(sm, (W, H), interpolation=cv2.INTER_LINEAR)

def nodoff110(A, B, j, f, sa, sb, pre=12, post=14):
    if j < 0:
        u = (j + pre + 0.5) / pre; e = ein(u, 2.4)
        o = _vblur_shift(A, -0.55 * H * e, -0.30 * H * e * 1.4)
        return np.clip(o * (1 - 0.25 * e), 0, 1)
    v = (j + 0.5) / post; e = 1 - (1 - smooth(v)) ** 2
    o = _vblur_shift(B, 0.45 * H * (1 - e), -0.22 * H * (1 - e))
    return np.clip(o * (0.75 + 0.25 * e), 0, 1)
TR2["nodoff110"] = (nodoff110, 12, 14)

# ---- THROUGH THE FAN (the drop, the signature). The fan room: an industrial fan behind him throws blue light through
# its blades. Through the break the power is low (the light flickers, the blades turn slowly); in the last bar it surges
# (the blades race, the rays strobe); on the drop we dive through the spinning blades into the light, which is the kill
# room. The fan is behind him (his matte), the rays come from behind him, the dive goes into the fan, past him.
FAN_L = (1.10, 0.06)                                    # the fan and its light: behind him, off the top right of the frame
FAN_COL = np.array([1.00, 0.80, 0.52], np.float32)      # BGR cold blue-white
_FPH = {}
def _fan_phase(f):
    """the blade angle (rad) and angular speed (rad/s) at frame f: a pure function of f (summed from the shot start)."""
    key = int(f)
    if key not in _FPH:
        f0 = E.fh(24); t_s0, t_s1 = E.th(27.0), E.th(30.0)
        ph = 0.0; out = {}
        for ff in range(f0 - 2, E.fh(32) + 2):
            t = ff / FPS; w = 2 * math.pi * (0.30 + 2.6 * smooth((t - t_s0) / (t_s1 - t_s0)))
            ph += w / FPS; out[ff] = (ph, w)
        _FPH.update(out)
    return _FPH.get(key, (0.0, 2 * math.pi * 0.30))

def _fan_power(f):
    t = f / FPS; t_s0, t_s1 = E.th(27.0), E.th(30.0)
    low = 0.45 + 0.12 * math.sin(t * 23.0) * math.sin(t * 7.1 + 0.4)              # brown, flickering
    return low + (1.15 - low) * smooth((t - t_s0) / (t_s1 - t_s0))

_FHZ = {}
def _fan_haze():
    if "h" not in _FHZ: _FHZ["h"] = _up(nz108(1110, 9))
    return _FHZ["h"]

def fan_beams110(f, open_=0.0):
    """the fan's light through its turning blades: lit sectors (0..1) radiating from the light behind him."""
    lx, ly = FAN_L[0] * W, FAN_L[1] * H
    ph, w = _fan_phase(f)
    dx = _GX - lx; dy = _GY - ly; d = np.sqrt(dx * dx + dy * dy) + 1e-3; th = np.arctan2(dy, dx)
    blur = min(0.30, 0.04 + abs(w) / FPS * 0.9)                                    # motion blur of the blades
    a = np.mod(th * 4 - ph * 4, 2 * np.pi) - np.pi                                  # four blades: shadow sectors
    width = 1.25 * (1 - open_)                                                      # half-width of a blade's shadow (rad*4)
    shadow = np.clip((width - np.abs(a)) / (blur * 4 + 0.08), 0, 1)
    fall = np.exp(-d / (1.5 * H)) * (0.75 + 0.5 * _fan_haze())
    return (1 - shadow) * fall, shadow

def _face_keep(s_, f):
    fs = face_scr(s_, f)
    if not fs: return 1.0
    return np.clip(np.sqrt(((_GX - fs[0]) / (0.70 * fs[2])) ** 2 + ((_GY - fs[1]) / (0.95 * fs[2])) ** 2) - 0.75, 0, 1)

def fan_draw110(img, f, P, surge=0.0, keep=1.0):
    pw = _fan_power(f) + surge
    lit, shadow = fan_beams110(f)
    behind = 1 - (P if P is not None else 0)
    near = np.exp(-(((_GX - FAN_L[0] * W) / (0.55 * W)) ** 2 + ((_GY - FAN_L[1] * H) / (0.35 * H)) ** 2))   # the haze round the light
    onhim = (P if P is not None else 0) * keep                                          # the blades' light across him, off his face
    o = img * (1 - (0.42 * shadow * behind + 0.32 * shadow * onhim)[..., None])
    o = o + ((lit * 0.62 + near * 0.32) * pw * behind + lit * 0.18 * pw * onhim)[..., None] * FAN_COL
    return np.clip(o, 0, 1)

FAN_HUB = (1.10 * W, -0.04 * H)
def _blade_mask(theta, width=0.42):
    """a blade passing right in front of the lens: the sector of angle width about theta (from the hub off the top
    right), soft and motion-blurred."""
    a = np.arctan2(_GY - FAN_HUB[1], _GX - FAN_HUB[0])
    da = np.mod(a - theta + np.pi, 2 * np.pi) - np.pi
    return np.clip((width / 2 - np.abs(da)) / 0.10, 0, 1)

def fan110(A, B, j, f, sa, sb, pre=70, post=28):
    P = _person(sa, f) if j < 0 else _person(sa, sa["f1"] - 1)
    P = np.zeros((H, W), np.float32) if P is None else _pp_clean(P)
    keep = _face_keep(sa, f if j < 0 else sa["f1"] - 1)
    th0, th1 = math.radians(78), math.radians(196)                                   # the blade sweeps the whole frame
    jb = (j + 7.5) / 13.0                                                             # frames -7 .. +5 around the drop
    theta = th0 + (th1 - th0) * smooth(jb)
    passed = np.clip((np.mod(np.arctan2(_GY - FAN_HUB[1], _GX - FAN_HUB[0]), 2 * np.pi) - theta) / -0.06, 0, 1) if 0 < jb < 1 else None
    if j < 0:
        surge = 0.35 * smooth((j + 24) / 20.0)                                        # the light flares as the fan races
        o = fan_draw110(A, f, P, surge=surge, keep=keep)
    else:
        k = 1 - smooth((j + 0.5) / post)
        lit, shadow = fan_beams110(f)
        o = B * (1 - (0.30 * shadow * k)[..., None]) + (lit * 0.30 * k)[..., None] * FAN_COL
    if 0 < jb < 1:
        Bl = B * (1 - (0.25 * fan_beams110(f)[1])[..., None])
        side = np.clip((theta - np.mod(np.arctan2(_GY - FAN_HUB[1], _GX - FAN_HUB[0]), 2 * np.pi)) / 0.08, 0, 1)   # behind the blade: the kill room
        o = o * (1 - side[..., None]) + Bl * side[..., None] if j < 0 else o
        bm = _blade_mask(theta)
        rim = np.clip(_blade_mask(theta, 0.50) - bm, 0, 1)
        o = o * (1 - 0.92 * bm[..., None]) + bm[..., None] * np.array([0.05, 0.05, 0.06], np.float32) + rim[..., None] * FAN_COL * 0.35
    return np.clip(o, 0, 1)
TR2["fan110"] = (fan110, 70, 28)

# ---- THE BARREL (the aim -> the warm stare; the focal point mid-edit): he raises the pistol through the bamboo until
# it points down the lens; we dive into the muzzle: the rifling spirals past in the dark, the light at the end of the
# barrel grows, and it is the next shot.
BAR_KEYS = [(0.50, 710, 1195, 22.0), (0.685, 689, 1028, 26.0), (0.852, 699, 1028, 26.0), (1.0, 758, 1043, 27.0)]   # the bore, tracked on the shot (px)
def _muzzle(sa, f):
    u = (f - sa["f0"]) / max(1, sa["f1"] - 1 - sa["f0"])
    ks = BAR_KEYS
    return tuple(float(np.interp(u, [k[0] for k in ks], [k[i] for k in ks])) for i in (1, 2, 3))

def barrel110(A, B, j, f, sa, sb, pre=40, post=18):
    q = (j + pre + 0.5) / (pre + post)
    mx, my, r0 = _muzzle(sa, f if j < 0 else sa["f1"] - 1)
    qd = smooth((q - 0.25) / 0.55)
    Z = math.exp(math.log(4.5) * ein(qd, 1.7))                                       # the camera pushes into the real muzzle
    Az = (_zoom_about(A, Z, mx, my) + _zoom_about(A, Z * 1.05, mx, my)) / 2 if Z > 1.002 else A
    rB = r0 * Z
    d = np.sqrt((_GX - mx) ** 2 + (_GY - my) ** 2)
    lg = smooth((q - 0.30) / 0.30)                                                    # a light at the end of the barrel
    rl = rB * (0.25 + 0.65 * lg)
    glow = np.exp(-(d / max(2.0, rl)) ** 2) * lg
    burst = smooth((q - 0.62) / 0.36)                                                 # it bursts out of the muzzle and fills the frame
    rw = rB * 0.9 + (math.hypot(W, H) * 1.05) * ein(burst, 1.8)
    win = np.clip((rw - d) / max(4.0, 0.10 * rw), 0, 1) * (burst > 0)
    sharp = smooth((q - 0.78) / 0.20)
    Bs = B if sharp >= 0.999 else cv2.resize(cv2.GaussianBlur(cv2.resize(B, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 6 * (1 - sharp) + 0.3), (W, H))
    Bs = Bs * (1 - sharp) + B * sharp if 0 < sharp < 1 else Bs
    lift = (1 - sharp) * 0.35
    Bl = np.clip(Bs + lift * np.array([0.85, 0.88, 0.92], np.float32) * (1 - d[..., None] / (rw + 1)), 0, 1)
    o = Az + glow[..., None] * np.array([0.80, 0.86, 0.95], np.float32) * 0.70
    o = o * (1 - win[..., None]) + Bl * win[..., None]
    return np.clip(o, 0, 1)
TR2["barrel110"] = (barrel110, 40, 18)

# ---- THE FOLD (the night street -> the red screen): the dream bends the world: the bottom half of the night street
# lifts off the ground and folds up over him like a page of the city; its underside is the next shot, which lands as
# the fold closes.
def fold110(A, B, j, f, sa, sb, pre=36, post=18):
    q = (j + pre + 0.5) / (pre + post)
    al = math.pi * smooth(clamp((q - 0.04) / 0.92, 0, 1))
    yf = H * 0.54; yc = H * 0.22; xc = W / 2; F = 1.25 * H
    ca, sn = math.cos(al), math.sin(al)
    den = F * ca + (_GY - yc) * sn
    s = F * (_GY - yf) / np.where(np.abs(den) < 1e-3, 1e-3, den)
    zz = s * sn
    X = xc + (_GX - xc) * (F - zz) / F
    valid = (s >= 0) & (s <= H - yf) & (X >= 0) & (X <= W - 1) & (F - zz > 50)
    front = ca > 0
    srcY = (yf + s) if front else (yf - s)
    src = A if front else B
    flap = cv2.remap(src, X.astype(np.float32), np.clip(srcY, 0, H - 1).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    shade = (0.45 + 0.55 * abs(ca)) if front else (0.30 + 0.70 * abs(ca))
    vm = valid.astype(np.float32)
    edge = np.exp(-((s - (H - yf)) / 6.0) ** 2) * vm + np.exp(-(s / 5.0) ** 2) * vm * 0.6   # the free edge and the hinge catch light
    vm = cv2.GaussianBlur(vm, (0, 0), 1.0)
    under = np.where(_GY >= yf, 1.0, 0.0).astype(np.float32)                     # where the flap left: the next shot
    shadow = 1 - 0.55 * math.sin(al) * np.exp(-np.abs(_GY - yf) / (0.25 * H))
    base = A * (1 - under[..., None]) + (B * shadow[..., None]) * under[..., None]
    o = base * (1 - vm[..., None]) + flap * shade * vm[..., None]
    rim = np.exp(-((_GY - (yc + (yf - yc + (H - yf) * ca) * F / (F - (H - yf) * sn))) / 2.5) ** 2) * vm * math.sin(al)
    o = o + rim[..., None] * AMB110 * 0.25 + (edge * math.sin(al) * 0.55)[..., None] * AMB110
    cast = cv2.GaussianBlur(vm, (0, 0), 30) * (1 - vm) * 0.55 * math.sin(al)       # the flap's shadow on what it uncovers
    o = o * (1 - cast[..., None])
    end = smooth((q - 0.94) / 0.05)
    return np.clip(o * (1 - end) + B * end, 0, 1)
TR2["fold110"] = (fold110, 36, 18)

# ---- THE SPATTER (anguish -> the blood room, on the way to "Mommy?"): the next shot's own blood arrives first: the real
# spatter on the blood room's walls appears over him along the arc of a swing (cast-off), wet and dark, kept off his
# face; then the room fills in around it.
_SPT = {}
def smooth01(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)

def _spatter_mask(sb):
    if sb["n"] not in _SPT:
        Bf = base108(sb, sb["f0"])[0]
        Bc, Gc, Rc = Bf[..., 0], Bf[..., 1], Bf[..., 2]
        m = np.clip((Rc - 1.25 * np.maximum(Gc, Bc) - 0.04) * 4.0, 0, 1)
        walls = np.maximum((_GX < 0.38 * W).astype(np.float32), 1 - smooth01((_GY - 0.36 * H) / (0.10 * H)))   # the walls, not his suit
        m = cv2.GaussianBlur(cv2.dilate(m * walls, np.ones((5, 5), np.uint8)), (0, 0), 1.2)
        seeds = (m > 0.3).astype(np.uint8)
        D = cv2.distanceTransform(255 - seeds * 255, cv2.DIST_L2, 5).astype(np.float32) + 90 * (_up(nz108(1120, 6)) - 0.5)
        _SPT[sb["n"]] = (m.astype(np.float32), D)
    return _SPT[sb["n"]]

def spatter110(A, B, j, f, sa, sb, pre=40, post=22):
    """the blood room's own wall spatter lands over him along the arc of a swing (cast-off), then the room seeps in
    outward from the blood."""
    q = (j + pre + 0.5) / (pre + post)
    m, D = _spatter_mask(sb)
    px, py = 1.20 * W, 1.30 * H
    ang = np.arctan2(_GY - py, _GX - px)                                          # the swing's arc, from the lower right
    front = -1.95 + (-3.05 + 1.95) * smooth(q / 0.45)
    sweep = np.clip((ang - front) / 0.06, 0, 1)
    fs = face_scr(sa, f if j < 0 else sa["f1"] - 1)
    keep = 1.0
    if fs:
        keep = 1 - np.clip(1.25 - np.sqrt(((_GX - fs[0]) / (0.75 * fs[2])) ** 2 + ((_GY - fs[1]) / (0.95 * fs[2])) ** 2), 0, 1)
    red = m * sweep * keep
    Rr = -60 + 1700 * ein(clamp((q - 0.38) / 0.58, 0, 1), 1.5)                     # the room seeps out from the blood
    room = np.clip((Rr - D) / 45.0, 0, 1)
    room = np.maximum(room, smooth((q - 0.94) / 0.05))
    Bz = _zoom_about(B, 1 + 0.06 * (1 - smooth(q)), W / 2, H / 2) if q < 0.999 else B
    o = A * (1 - room[..., None]) + Bz * room[..., None]
    wet = Bz * 0.9 + np.array([0.01, 0.01, 0.06], np.float32)
    o = o * (1 - (red * (1 - room))[..., None]) + wet * (red * (1 - room))[..., None]
    edge = np.clip((Rr - D) / 45.0, 0, 1); edge = np.clip(edge * (1 - edge) * 4, 0, 1) * (Rr > 0)
    o = o * (1 - 0.35 * edge[..., None])                                             # a dark, wet seam on the seeping edge
    return np.clip(o, 0, 1)
TR2["spatter110"] = (spatter110, 40, 22)

# ---- THE FALL (the loop): on the second "Mommy?" the floor of the dream goes: the blood room tips back and falls away
# above us, we drop through the dark (drops of blood fall with us), and the bed rises from far below, growing, frame 0
# the whole way, until we land in it: he is awake, staring up, and it begins again.
FALL_F0 = E.fh(75.6)
def _card(img, s, cx, cy, tilt=0.0):
    """the picture as a card scaled by s about (cx, cy), its top edge receding by tilt (0..1)."""
    w2, h2 = W * s / 2, H * s / 2
    dt = w2 * tilt * 0.35
    src = np.float32([[0, 0], [W, 0], [W, H], [0, H]])
    dst = np.float32([[cx - w2 + dt, cy - h2], [cx + w2 - dt, cy - h2], [cx + w2, cy + h2], [cx - w2, cy + h2]])
    M = cv2.getPerspectiveTransform(src, dst)
    card = cv2.warpPerspective(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    msk = cv2.warpPerspective(np.ones((H, W), np.float32), M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    return card, msk

def fall110(out, f, s, person=None):
    last = E.DUR_F - 1
    if f < FALL_F0: return out
    if f >= last: return frame0_plate108().copy()
    t = (f - FALL_F0) / (last - FALL_F0)
    F0 = frame0_plate108()
    u = t * t * (3 - 2 * t)
    sB = 0.22 + 0.78 * u; cyB = H * 0.80 + (H * 0.5 - H * 0.80) * u
    M = np.float32([[sB, 0, W / 2 * (1 - sB)], [0, sB, cyB - H / 2 * sB]])
    cardR = cv2.warpAffine(F0, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    halo = cv2.resize(cv2.GaussianBlur(cv2.resize(cardR, (W // 8, H // 8), interpolation=cv2.INTER_AREA), (0, 0), 3), (W, H))
    w2, h2 = W * sB / 2, H * sB / 2; fe = 3 + 0.95 * w2 * (1 - u)
    mB = (np.clip((w2 - np.abs(_GX - W / 2)) / fe, 0, 1) * np.clip((h2 - np.abs(_GY - cyB)) / fe, 0, 1)).astype(np.float32)
    bg = halo * (0.75 + 0.25 * u)                                                     # frame 0's own light all round (out of focus)
    o = bg * (1 - mB[..., None]) + cardR * mB[..., None]
    ta = ein(t, 1.6); dy = -1.10 * H * ta                                             # the blood room drops away above us
    A2 = _vblur_shift(out, dy, -0.25 * H * min(1.0, 3.0 * t))
    mA = (np.clip((H + dy - _GY) / 60.0, 0, 1) * (1 - smooth(t / 0.70)))[..., None]
    o = o * (1 - mA) + A2 * mA
    rng = np.random.default_rng(1103)                                                 # we are falling: light streaks rush up past
    sx = rng.uniform(0.04 * W, 0.96 * W, 14); sp = rng.uniform(1.2, 2.6, 14); ph = rng.uniform(0, 1, 14)
    st = np.zeros((H, W), np.float32)
    for x_, v_, p_ in zip(sx, sp, ph):
        yc = ((p_ - t * v_) % 1.0) * 1.6 * H - 0.3 * H; ln = 0.22 * H * v_
        cv2.line(st, (int(x_), int(yc)), (int(x_), int(yc + ln)), 1.0, 3, cv2.LINE_AA)
    st = cv2.GaussianBlur(st, (0, 0), 3) * (smooth(t / 0.15) * (1 - smooth((t - 0.70) / 0.22)))
    o = o + st[..., None] * AMB110 * 0.30
    dx = rng.uniform(0.06 * W, 0.94 * W, 18); dz = rng.uniform(0.4, 1.0, 18); dp = rng.uniform(0, 1, 18)   # drops of blood fall with us
    dr = np.zeros((H, W), np.float32)
    for x_, z_, p_ in zip(dx, dz, dp):
        yc = ((p_ - t * (0.8 + 1.4 * z_)) % 1.0) * 1.4 * H - 0.2 * H
        cv2.ellipse(dr, (int(x_), int(yc)), (int(2 + 4 * z_), int(26 + 60 * z_)), 0, 0, 360, 1.0, -1, cv2.LINE_AA)   # falling fast: streaks
    dr = cv2.GaussianBlur(dr, (0, 0), 2.5) * (smooth(t / 0.12) * (1 - smooth((t - 0.65) / 0.25))) * 0.75
    o = o * (1 - 0.80 * dr[..., None]) + dr[..., None] * np.array([0.02, 0.02, 0.30], np.float32)
    we = smooth((t - 0.90) / 0.10)
    return np.clip(o * (1 - we) + F0 * we, 0, 1)

# ---- THE BULB (the anguish shot): a bare bulb above him swings on its cord; its pool of light swings across him and the
# crucifix behind (the room breathes with it; no flicker)
def bulb110(out, f, s):
    t = (f - s["f0"]) / FPS; per = 4 * E.HB
    k = smooth(t / 0.25)
    x = W * 0.5 + W * 0.30 * math.sin(2 * math.pi * t / per - 0.6) * k
    y = H * 0.20 - H * 0.03 * abs(math.cos(2 * math.pi * t / per - 0.6))
    d2 = ((_GX - x) / (0.34 * W)) ** 2 + ((_GY - y) / (0.55 * H)) ** 2
    m = 0.42 + 0.95 * np.exp(-d2)
    return np.clip(out * m[..., None] + np.exp(-d2 * 3.0)[..., None] * AMB110 * 0.05, 0, 1)

def render(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin")
    out, person = base108(s, f)
    if s["n"] == "light": out = light_scene110(out, f)
    if s["n"] == "anguish": out = bulb110(out, f, s)
    if s["n"] == "fan" and not (n_ and kn >= -TR2["fan110"][1]):
        Pm = None if person is None else _pp_clean(np.clip(np.asarray(person, np.float32), 0, 1))
        out = fan_draw110(out, f, Pm, keep=_face_keep(s, f))
    if tin in TR2 and k < TR2[tin][2] and P is not None:
        out = TR2[tin][0](edge108(P, "last"), out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, edge108(n_, "first"), kn, f, s, n_)
    if s.get("tout") == "fall110": out = fall110(out, f, s, person)
    out = beat_fx(out, f)
    out = title110(out, f)
    out = flash_governor(out)
    return (np.clip(finish110(out, f, s), 0, 1) * 255 + 0.5).astype(np.uint8)

# ---- LIGHTS ON (the doorway -> the light on "I'm"): the hall goes dark and the tube above him blinks on with the word
def lightson110(A, B, j, f, sa, sb, pre=8, post=16):
    if j < 0:
        u = smooth((j + pre + 0.5) / pre); return np.clip(A * (1 - 0.60 * u), 0, 1)
    jj = j + 0.5
    lv = 0.40 + 0.60 * smooth((jj - 2.5) / 1.5)
    lv *= (1 - 0.50 * math.exp(-((jj - 6.5) / 1.1) ** 2)) * (1 - 0.30 * math.exp(-((jj - 10.5) / 1.0) ** 2))
    m = 1 - (1 - lv) * (0.55 + 0.45 * (1 - _GY / H))                                  # the light falls from above
    return np.clip(B * m[..., None], 0, 1)
TR2["lightson110"] = (lightson110, 8, 16)

# ============================================================================ v110 rev 1 (the owner's notes)
# "the splatter transition ... smoother and more seamless"; "the loop is really poor ... completely change the loop and
# take a different avenue ... custom transitions and graphics"; "I'm losing power text ... incorporate it as more of a beat
# drop"; "most of the transitions ... lackluster ... more unique and creative"; "the doorway transition at 16 seconds ...
# the lines transition at 17 seconds ... replace them". New: the title slams in on the drop with the power surge; BOKEH,
# TEAR, CURTAIN, PLASTIC ROLL, BRUSH; a smooth seep for the spatter; THE NEON SLEEPER loop.

# ---- I'M LOSING POWER, on the drop: the power surges back and the words slam on with it (white-hot, a shock ripple
# through the frame), surge on each beat of the bar, then lose power letter by letter.
_TS = {}
def _title_layer(sc):
    if "l1" not in _TS:
        _TS["l1"] = [(c, text_mask(c, F_BLACK, 118) if c != " " else None) for c in "I'M LOSING"]
        _TS["l2"] = [(c, text_mask(c, F_BLACK, 250)) for c in "POWER"]
    return _TS["l1"], _TS["l2"]

def title110(out, f):
    t = f / FPS; T0 = E.th(30); T_DIE = E.th(33.3)
    if t < T0 - 0.001 or t > E.th(34.8): return out
    k = t - T0
    l1, l2 = _title_layer(1)
    lay = np.zeros((H, W), np.float32)
    def place(letters, y, gap):
        wsum = sum((m.shape[1] if m is not None else 46) for c, m in letters) + gap * (len(letters) - 1); x = (W - wsum) / 2
        for i, (c, m) in enumerate(letters):
            if m is None: x += 46 + gap; continue
            a = 1.0
            td = T_DIE + 0.07 * ((i * 5) % 7) + 0.03 * i
            if t > td: a *= max(0.0, 1 - smooth((t - td) / 0.16)) * (0.72 + 0.28 * math.cos((t - td) * 2 * math.pi * 4.0 + i))
            if a > 0.003:
                mm = m.astype(np.float32) / (m.max() + 1e-6); h_, w_ = mm.shape; yy, xx = int(y), int(x)
                ys, xs, ye, xe = max(0, yy), max(0, xx), min(H, yy + h_), min(W, xx + w_)
                if ye > ys and xe > xs: lay[ys:ye, xs:xe] = np.maximum(lay[ys:ye, xs:xe], mm[ys - yy:ye - yy, xs - xx:xe - xx] * a)
            x += m.shape[1] + gap
    place(l1, H * 0.615, 10); place(l2, H * 0.680, 12)
    cx, cy = W / 2, H * 0.70
    sc = 1 + 0.38 * math.exp(-k / 0.045)                                              # the slam
    if sc > 1.003:
        lays = [cv2.warpAffine(lay, np.float32([[s_, 0, cx * (1 - s_)], [0, s_, cy * (1 - s_)]]), (W, H)) for s_ in (sc, 1 + (sc - 1) * 0.6, 1 + (sc - 1) * 0.3)]
        lay = (lays[0] + lays[1] + lays[2]) / 3
    surge = 0.0
    for eb in (30, 32, 34):                                                           # the tube surges on each beat
        dk = t - E.th(eb)
        if dk >= 0: surge = max(surge, math.exp(-dk / 0.10))
    if k < 0.32:                                                                      # a shock ripple through the picture
        rs = 120 + 1500 * (k / 0.32); d = np.sqrt((_GX - cx) ** 2 + (_GY - cy) ** 2) + 1e-3
        amp = 16 * (1 - k / 0.32) * np.exp(-((d - rs) / 46.0) ** 2)
        out = cv2.remap(out, (_GX + amp * (_GX - cx) / d).astype(np.float32), (_GY + amp * (_GY - cy) / d).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    hot = math.exp(-k / 0.09)
    g1 = cv2.GaussianBlur(lay, (0, 0), 7)
    g2 = cv2.resize(cv2.GaussianBlur(cv2.resize(lay, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 8), (W, H), interpolation=cv2.INTER_LINEAR)
    core = np.array([0.82, 0.93, 1.0], np.float32) * (1 - 0.5 * hot) + np.array([1.0, 1.0, 1.0], np.float32) * 0.5 * hot
    o = out * (1 - 0.88 * lay[..., None]) + lay[..., None] * core * (0.92 + 0.08 * surge) \
        + (g1 * (0.55 + 0.35 * surge) + g2 * (0.85 + 0.6 * surge + 0.8 * hot))[..., None] * AMB110 * 0.55
    return np.clip(o, 0, 1)

# ---- BOKEH (the marina -> the doorway): the marina's city lights fall out of focus into big soft discs; the next shot's
# lamp light comes back into focus out of them.
_DISC = {}
def _disc(r):
    r = max(1, int(round(r)))
    if r not in _DISC:
        k = np.zeros((2 * r + 1, 2 * r + 1), np.float32); cv2.circle(k, (r, r), r, 1.0, -1, cv2.LINE_AA); _DISC[r] = k / k.sum()
    return _DISC[r]

def bokeh110(A, B, j, f, sa, sb, pre=14, post=14):
    q = (j + pre + 0.5) / (pre + post)
    dq = math.sin(math.pi * clamp(q, 0, 1)) ** 0.8
    w = smooth((j + 3) / 6.0); img = A * (1 - w) + B * w
    if dq < 0.02: return img
    q4 = cv2.resize(img, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    L = lum(q4)
    hdr = np.power(np.clip(q4, 0, 1), 2.2) * (1 + 9 * np.clip((L - 0.45) * 2.5, 0, 1))[..., None]
    bl = cv2.filter2D(hdr, -1, _disc(1 + 13 * dq), borderType=cv2.BORDER_REFLECT)
    o4 = np.power(np.clip(bl, 0, 1), 1 / 2.2)
    o = cv2.resize(o4, (W, H), interpolation=cv2.INTER_LINEAR)
    m = clamp(dq * 2.2, 0, 1)
    return np.clip(img * (1 - m) + o * m, 0, 1)
TR2["bokeh110"] = (bokeh110, 14, 14)

# ---- TEAR (the drive -> the dark street): the picture is a print; it tears down one side and the print is pulled away
# (the face stays whole on its piece), the next shot under it.
_TR = {}
def _tear_x():
    if "x" not in _TR:
        rng = np.random.default_rng(1131)
        y = np.arange(H, dtype=np.float32)
        n1 = np.interp(y, np.linspace(0, H, 14), rng.uniform(-1, 1, 14)); n2 = np.interp(y, np.linspace(0, H, 90), rng.uniform(-1, 1, 90))
        _TR["x"] = (0.20 * W + 34 * n1 + 9 * n2).astype(np.float32)
        _TR["fib"] = rng.random((H, 64)).astype(np.float32)
    return _TR["x"], _TR["fib"]

def tear110(A, B, j, f, sa, sb, pre=10, post=14):
    q = (j + pre + 0.5) / (pre + post)
    xt, fib = _tear_x(); xt2 = xt[:, None]
    front = -0.10 * H + 1.25 * H * smooth(q / 0.38)
    torn = smooth01((front - _GY[:, :1]) / 140.0)                                      # the tear runs down first
    pull = ein(clamp((q - 0.22) / 0.78, 0, 1), 1.6)
    sR = (1.25 * W * pull) * torn; sL = (0.32 * W * pull) * torn
    srcR = _GX - sR; srcL = _GX + sL
    mR = np.clip((srcR - xt2) / 1.5 + 0.5, 0, 1); mL = np.clip((xt2 - srcL) / 1.5 + 0.5, 0, 1)
    aR = cv2.remap(A, srcR.astype(np.float32), _GY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    aL = cv2.remap(A, srcL.astype(np.float32), _GY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    gapL = srcL - xt2; gapR = srcR - xt2
    shadow = 1 - 0.45 * (np.exp(-np.clip(gapR, 0, None) * 0 - np.clip(-gapR, 0, None) / 40.0) * (gapR < 0) + np.exp(-np.clip(gapL, 0, None) / 40.0) * (gapL > 0)) * torn
    o = B * np.clip(shadow, 0.4, 1)[..., None]
    o = o * (1 - mR[..., None]) + aR * mR[..., None]
    o = o * (1 - mL[..., None]) + aL * mL[..., None]
    fx = cv2.resize(fib, (W, H), interpolation=cv2.INTER_NEAREST)
    edge = (np.exp(-((srcR - xt2) / 4.0) ** 2) * mR + np.exp(-((xt2 - srcL) / 4.0) ** 2) * mL) * torn * (0.55 + 0.45 * fx)
    o = o * (1 - 0.8 * edge[..., None]) + edge[..., None] * np.array([0.86, 0.90, 0.93], np.float32) * 0.85
    return np.clip(o, 0, 1)
TR2["tear110"] = (tear110, 10, 14)

# ---- CURTAIN (the doorway -> the night street): the sheer curtain behind him blows in across the lens on the night
# air, backlit by the lamp; behind it the night street.
CURT_COL = np.array([0.62, 0.78, 0.92], np.float32)
def curtain110(A, B, j, f, sa, sb, pre=18, post=18):
    q = (j + pre + 0.5) / (pre + post)
    lead = -0.35 * W + 2.80 * W * smooth(q)
    yy = _GY / H
    edge = lead + 110 * np.sin(2 * np.pi * (yy * 1.2 - q * 1.4)) + 50 * np.sin(2 * np.pi * (yy * 3.1 + q * 2.2))
    trail = edge - 1.30 * W
    inside = np.clip((edge - _GX) / 70.0, 0, 1) * np.clip((_GX - trail) / 120.0, 0, 1)
    wB = np.clip((edge - _GX) / (1.30 * W), 0, 1); wB = wB * wB * (3 - 2 * wB)
    base = A * (1 - wB[..., None]) + B * wB[..., None]
    ph = (_GX - lead * 0.55) / 120.0 + 0.9 * np.sin(_GY / 300.0 + q * 5.0)
    fold = 0.5 + 0.5 * np.sin(2 * np.pi * ph)
    dens = inside * (0.50 + 0.28 * fold)
    soft = cv2.resize(cv2.GaussianBlur(cv2.resize(base, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 4), (W, H))
    fab = soft * 0.45 + CURT_COL * (0.22 + 0.22 * fold)[..., None]
    o = base * (1 - dens[..., None]) + fab * dens[..., None]
    return np.clip(o + (inside * fold ** 6 * 0.10)[..., None] * AMB110, 0, 1)
TR2["curtain110"] = (curtain110, 18, 18)

# ---- PLASTIC ROLL (the night street -> the kill room): kill-room plastic sheeting unrolls down over the lens (clear,
# crinkled, catching the light); behind it the street becomes the kill room; the sheet runs on down and away.
def plasticroll110(A, B, j, f, sa, sb, pre=16, post=16):
    q = (j + pre + 0.5) / (pre + post)
    yb = -0.05 * H + 2.45 * H * smooth(q); yt = yb - 1.30 * H
    inside = np.clip((yb - _GY) / 6.0, 0, 1) * np.clip((_GY - yt) / 40.0, 0, 1)
    wB = np.clip((yb - _GY) / (1.30 * H), 0, 1); wB = wB * wB * (3 - 2 * wB)
    base = A * (1 - wB[..., None]) + B * wB[..., None]
    if "pc" not in _TR:
        n = _up(nz108(1132, 2.2)); gy, gx = np.gradient(n)
        _TR["pc"] = (gx * 900, gy * 900, n)
    gx, gy, n = _TR["pc"]
    sh = int(clamp(yb, -H, 3 * H)) % H                                                  # the crinkles travel with the sheet
    gxs = np.roll(gx, sh, axis=0); gys = np.roll(gy, sh, axis=0)
    ref = cv2.remap(base, (_GX + 12 * gxs * inside).astype(np.float32), (_GY + 12 * gys * inside).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    spec = np.clip(-0.6 * gxs - 0.8 * gys, 0, None) ** 2 * 0.9
    o = base * (1 - inside[..., None]) + (ref * 0.86 + 0.05 + spec[..., None] * np.array([0.9, 0.9, 0.85], np.float32)) * inside[..., None]
    roll = np.exp(-((_GY - (yb - 14)) / 9.0) ** 2) * (yb > 0)                          # the roll's bright edge
    return np.clip(o + roll[..., None] * np.array([0.55, 0.58, 0.60], np.float32) * 0.6, 0, 1)
TR2["plasticroll110"] = (plasticroll110, 16, 16)

# ---- BRUSH (the kill room -> the cabin): two dry-brush strokes of dark red sweep across and paint the next shot in.
def brush110(A, B, j, f, sa, sb, pre=12, post=14):
    q = (j + pre + 0.5) / (pre + post)
    if "bn" not in _TR:
        rng = np.random.default_rng(1133); s_ = rng.standard_normal((64, 1024)).astype(np.float32)
        s_ = cv2.GaussianBlur(s_, (0, 0), sigmaX=40, sigmaY=0.8); s_ = (s_ - s_.min()) / (s_.max() - s_.min())
        _TR["bn"] = s_
    bn = _TR["bn"]; m = np.zeros((H, W), np.float32); rim = np.zeros((H, W), np.float32)
    for k, (ang, c0, wid, t0, t1) in enumerate(((-32, 0.36, 0.62, 0.00, 0.55), (-32, 0.82, 0.70, 0.30, 0.90))):
        a = math.radians(ang); ux, uy = math.cos(a), math.sin(a)
        cxk, cyk = W * 0.5, H * c0
        along = (_GX - cxk) * ux + (_GY - cyk) * uy; dn = -(_GX - cxk) * uy + (_GY - cyk) * ux
        head = -1.2 * W + 2.6 * W * smooth((q - t0) / (t1 - t0))
        st = cv2.remap(bn, ((dn / (wid * H) + 0.5) * 63).astype(np.float32), ((along + 1.3 * W) / (2.6 * W) * 1023).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        half = wid * H / 2
        mk = np.clip((half - np.abs(dn) + 90 * (st - 0.5)) / 5.0, 0, 1) * np.clip((head - along + 60 * (st - 0.5)) / 8.0, 0, 1)
        dry = np.clip((st - 0.18) / 0.12, 0, 1)                                         # dry streaks inside
        mk = mk * (0.25 + 0.75 * dry) * np.clip((head - along) / 140.0, 0, 1) + mk * np.clip((head - along - 140) / 200.0, 0, 1) * (1 - (0.25 + 0.75 * dry))
        m = np.maximum(m, np.clip(mk, 0, 1))
        rim = np.maximum(rim, np.clip(1 - np.abs(np.abs(dn) - half) / 26.0, 0, 1) * np.clip((head - along) / 30.0, 0, 1))
    m = np.maximum(m, smooth((q - 0.86) / 0.14))
    o = A * (1 - m[..., None]) + B * m[..., None]
    o = o * (1 - 0.35 * rim[..., None] * (1 - m[..., None] * 0.5)) + rim[..., None] * np.array([0.03, 0.03, 0.30], np.float32) * 0.5 * (1 - smooth((q - 0.86) / 0.14))
    return np.clip(o, 0, 1)
TR2["brush110"] = (brush110, 12, 14)

# ---- THE SPATTER, smooth: the cast-off lands softly along the swing; the blood room seeps in from its blood with a wide,
# soft front and a slow push that runs on through the cut (no hard edges, no seam).
def spatter110(A, B, j, f, sa, sb, pre=34, post=30):
    q = (j + pre + 0.5) / (pre + post)
    m, D = _spatter_mask(sb)
    px, py = 1.20 * W, 1.30 * H
    ang = np.arctan2(_GY - py, _GX - px)
    front = -1.95 + (-3.05 + 1.95) * smooth(q / 0.50)
    sweep = np.clip((ang - front) / 0.30, 0, 1); sweep = sweep * sweep * (3 - 2 * sweep)
    keep = _face_keep(sa, f if j < 0 else sa["f1"] - 1)
    red = m * sweep * keep * 0.85
    Rr = -200 + 2000 * ein(clamp((q - 0.30) / 0.66, 0, 1), 1.3)
    room = np.clip((Rr - D) / 260.0, 0, 1); room = room * room * (3 - 2 * room)
    room = np.maximum(room, smooth((q - 0.72) / 0.26))
    za = 1 + 0.05 * smooth(q); zb = 1 + 0.05 * (1 - smooth(q))                          # one continuous push through the cut
    Az = _zoom_about(A, za, W / 2, H * 0.45); Bz = _zoom_about(B, zb, W / 2, H * 0.45)
    o = Az * (1 - room[..., None]) + Bz * room[..., None]
    wet = Bz * 0.92 + np.array([0.01, 0.01, 0.05], np.float32)
    rr = (red * (1 - room))[..., None]
    return np.clip(o * (1 - rr) + wet * rr, 0, 1)
TR2["spatter110"] = (spatter110, 34, 30)

# ---- THE NEON SLEEPER (the loop): on the second "Mommy?" the blood room loses power and goes dark; a neon tube draws
# the outline of him lying in bed (frame 0's own silhouette), flickers on like the title, and frame 0 lights up from the
# outline outward until it is the first frame again.
NEON_F0 = E.fh(75.0)
_NL = {}
def _neon_setup():
    if "c" not in _NL:
        F0 = frame0_plate108(); P0 = _person(SHOTS[0], SHOTS[0]["f0"])
        P0 = np.zeros((H, W), np.float32) if P0 is None else _pp_clean(P0)
        cs, _ = cv2.findContours((P0 > 0.5).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        c = max(cs, key=cv2.contourArea)[:, 0, :].astype(np.float32)
        c = c[np.argsort(np.arctan2(c[:, 1] - c[:, 1].mean(), c[:, 0] - c[:, 0].mean()))] if False else c
        sm = np.stack([np.convolve(np.r_[c[-8:, i], c[:, i], c[:8, i]], np.ones(17) / 17, "valid") for i in range(2)], 1)
        seg = np.sqrt((np.diff(sm, axis=0) ** 2).sum(1)); cum = np.r_[0, np.cumsum(seg)]
        start = int(np.argmin(sm[:, 1]))                                                 # start at the top of his head
        _NL.update(c=np.roll(sm, -start, axis=0), cum=None, F0=F0, P0=P0,
                   Dout=cv2.distanceTransform(((P0 <= 0.5) * 255).astype(np.uint8), cv2.DIST_L2, 5).astype(np.float32))
        cc = _NL["c"]; seg = np.sqrt((np.diff(cc, axis=0) ** 2).sum(1)); _NL["cum"] = np.r_[0, np.cumsum(seg)]
    return _NL

def neonloop110(out, f, s, person=None):
    last = E.DUR_F - 1
    if f < NEON_F0: return out
    if f >= last: return frame0_plate108().copy()
    t = (f - NEON_F0) / (last - NEON_F0); D = _neon_setup(); F0 = D["F0"]
    lv = 1 - 0.70 * smooth(t / 0.30)                                                     # the blood room loses power
    for tk, dd in ((0.08, 0.35), (0.16, 0.30)):
        lv *= 1 - dd * math.exp(-((t - tk) / 0.018) ** 2)
    o = out * lv
    p = smooth((t - 0.12) / 0.42)                                                        # the tube draws his outline
    cv = np.zeros((H, W), np.float32)
    if p > 0:
        n = int(np.searchsorted(D["cum"], p * D["cum"][-1]))
        pts = D["c"][:max(2, n)]
        cv2.polylines(cv, [np.round(pts * 8).astype(np.int32)], False, 1.0, 4, cv2.LINE_AA, shift=3)
        if p < 1:
            hx, hy = pts[-1]
            cv += 1.4 * np.exp(-(((_GX - hx) ** 2 + (_GY - hy) ** 2) / (2 * 9.0 ** 2)))
    on = 0.55 + 0.45 * smooth((t - 0.50) / 0.10)
    for tk, dd in ((0.53, 0.7), (0.58, 0.5)):                                            # it flickers fully on
        on *= 1 - dd * math.exp(-((t - tk) / 0.012) ** 2)
    fade = 1 - smooth((t - 0.84) / 0.13)
    cv = cv * on * fade
    R = -40 + 1500 * ein(clamp((t - 0.58) / 0.36, 0, 1), 1.4)                           # frame 0 lights up from the outline outward
    fill = np.clip((R - D["Dout"]) / 160.0, 0, 1) * smooth((t - 0.56) / 0.12)
    fill = np.maximum(fill, smooth((t - 0.90) / 0.09))
    o = o * (1 - fill[..., None]) + F0 * fill[..., None]
    g1 = cv2.GaussianBlur(cv, (0, 0), 6); g2 = cv2.resize(cv2.GaussianBlur(cv2.resize(cv, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 7), (W, H))
    o = o * (1 - 0.85 * np.clip(cv, 0, 1)[..., None]) + cv[..., None] * np.array([0.82, 0.93, 1.0], np.float32) + (g1 * 0.7 + g2 * 1.0)[..., None] * AMB110 * 0.55
    we = smooth((t - 0.93) / 0.07)
    return np.clip(o * (1 - we) + F0 * we, 0, 1)

def render(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin")
    out, person = base108(s, f)
    if s["n"] == "light": out = light_scene110(out, f)
    if s["n"] == "anguish": out = bulb110(out, f, s)
    if s["n"] == "fan" and not (n_ and kn >= -TR2["fan110"][1]):
        Pm = None if person is None else _pp_clean(np.clip(np.asarray(person, np.float32), 0, 1))
        out = fan_draw110(out, f, Pm, keep=_face_keep(s, f))
    if tin in TR2 and k < TR2[tin][2] and P is not None:
        out = TR2[tin][0](edge108(P, "last"), out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, edge108(n_, "first"), kn, f, s, n_)
    if s.get("tout") == "neonloop110": out = neonloop110(out, f, s, person)
    out = beat_fx(out, f)
    out = title110(out, f)
    out = flash_governor(out)
    return (np.clip(finish110(out, f, s), 0, 1) * 255 + 0.5).astype(np.uint8)

# ---- rev 1, after the stills: softer curtain folds (no stripes), a subtle crinkle on the plastic, no red line left by
# the brush, a clean outline for the neon sleeper
def curtain110(A, B, j, f, sa, sb, pre=18, post=18):
    q = (j + pre + 0.5) / (pre + post)
    lead = -0.35 * W + 2.80 * W * smooth(q)
    yy = _GY / H
    edge = lead + 110 * np.sin(2 * np.pi * (yy * 1.2 - q * 1.4)) + 50 * np.sin(2 * np.pi * (yy * 3.1 + q * 2.2))
    trail = edge - 1.30 * W
    inside = np.clip((edge - _GX) / 90.0, 0, 1) * np.clip((_GX - trail) / 160.0, 0, 1)
    wB = np.clip((edge - _GX) / (1.30 * W), 0, 1); wB = wB * wB * (3 - 2 * wB)
    base = A * (1 - wB[..., None]) + B * wB[..., None]
    ph = (_GX - lead * 0.55) / 430.0 + 0.35 * np.sin(_GY / 520.0 + q * 3.0)
    fold = 0.5 + 0.5 * np.sin(2 * np.pi * ph)                                          # broad, soft folds
    dens = inside * (0.52 + 0.10 * fold)
    soft = cv2.resize(cv2.GaussianBlur(cv2.resize(base, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 6), (W, H))
    fab = soft * 0.50 + CURT_COL * (0.24 + 0.08 * fold)[..., None]
    o = base * (1 - dens[..., None]) + fab * dens[..., None]
    lit = np.exp(-((_GX - (edge - 60)) / 90.0) ** 2) * inside                          # the backlit leading edge
    return np.clip(o + lit[..., None] * AMB110 * 0.10, 0, 1)
TR2["curtain110"] = (curtain110, 18, 18)

def plasticroll110(A, B, j, f, sa, sb, pre=16, post=16):
    q = (j + pre + 0.5) / (pre + post)
    yb = -0.05 * H + 2.45 * H * smooth(q); yt = yb - 1.30 * H
    inside = np.clip((yb - _GY) / 10.0, 0, 1) * np.clip((_GY - yt) / 80.0, 0, 1)
    wB = np.clip((yb - _GY) / (1.30 * H), 0, 1); wB = wB * wB * (3 - 2 * wB)
    base = A * (1 - wB[..., None]) + B * wB[..., None]
    if "pc2" not in _TR:
        n = _up(nz108(1134, 7)); gy, gx = np.gradient(cv2.GaussianBlur(n, (0, 0), 6))
        sc = 1.0 / (np.abs(gx).max() + np.abs(gy).max() + 1e-6)
        _TR["pc2"] = (gx * sc, gy * sc)
    gx, gy = _TR["pc2"]
    sh = int(clamp(yb, -H, 3 * H)) % H
    gxs = np.roll(gx, sh, axis=0); gys = np.roll(gy, sh, axis=0)
    ref = cv2.remap(base, (_GX + 10 * gxs * inside).astype(np.float32), (_GY + 10 * gys * inside).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    spec = np.clip(-0.6 * gxs - 0.8 * gys, 0, None) ** 2 * 0.22
    o = base * (1 - inside[..., None]) + (ref * 0.88 + 0.04 + spec[..., None] * np.array([0.9, 0.9, 0.85], np.float32)) * inside[..., None]
    roll = np.exp(-((_GY - (yb - 14)) / 10.0) ** 2) * (yb > 0)
    return np.clip(o + roll[..., None] * np.array([0.55, 0.58, 0.60], np.float32) * 0.35, 0, 1)
TR2["plasticroll110"] = (plasticroll110, 16, 16)

def brush110(A, B, j, f, sa, sb, pre=12, post=14):
    q = (j + pre + 0.5) / (pre + post)
    if "bn" not in _TR:
        rng = np.random.default_rng(1133); s_ = rng.standard_normal((64, 1024)).astype(np.float32)
        s_ = cv2.GaussianBlur(s_, (0, 0), sigmaX=40, sigmaY=0.8); s_ = (s_ - s_.min()) / (s_.max() - s_.min())
        _TR["bn"] = s_
    bn = _TR["bn"]; m = np.zeros((H, W), np.float32); wet = np.zeros((H, W), np.float32)
    for k, (ang, c0, wid, t0, t1) in enumerate(((-32, 0.36, 0.62, 0.00, 0.55), (-32, 0.82, 0.70, 0.30, 0.90))):
        a = math.radians(ang); ux, uy = math.cos(a), math.sin(a)
        cxk, cyk = W * 0.5, H * c0
        along = (_GX - cxk) * ux + (_GY - cyk) * uy; dn = -(_GX - cxk) * uy + (_GY - cyk) * ux
        head = -1.2 * W + 2.6 * W * smooth((q - t0) / (t1 - t0))
        st = cv2.remap(bn, ((dn / (wid * H) + 0.5) * 63).astype(np.float32), ((along + 1.3 * W) / (2.6 * W) * 1023).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        half = wid * H / 2
        mk = np.clip((half - np.abs(dn) + 90 * (st - 0.5)) / 5.0, 0, 1) * np.clip((head - along + 60 * (st - 0.5)) / 8.0, 0, 1)
        dry = np.clip((st - 0.18) / 0.12, 0, 1)
        mk = mk * (0.25 + 0.75 * dry) * np.clip((head - along) / 140.0, 0, 1) + mk * np.clip((head - along - 140) / 200.0, 0, 1) * (1 - (0.25 + 0.75 * dry))
        m = np.maximum(m, np.clip(mk, 0, 1))
        wet = np.maximum(wet, np.clip(mk, 0, 1) * np.exp(-np.clip(head - along, 0, None) / 120.0))   # wet paint only at the brush head
    m = np.maximum(m, smooth((q - 0.86) / 0.14))
    o = A * (1 - m[..., None]) + B * m[..., None]
    return np.clip(o * (1 - 0.25 * wet[..., None]) + wet[..., None] * np.array([0.03, 0.03, 0.28], np.float32) * 0.35, 0, 1)
TR2["brush110"] = (brush110, 12, 14)

def _neon_setup():
    if "c" not in _NL:
        F0 = frame0_plate108(); P0 = _person(SHOTS[0], SHOTS[0]["f0"])
        P0 = np.zeros((H, W), np.float32) if P0 is None else P0
        sm = cv2.resize(P0, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
        nl, lab, stats, _ = cv2.connectedComponentsWithStats((sm > 0.5).astype(np.uint8))
        big = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA])) if nl > 1 else 0
        sm = (lab == big).astype(np.float32)
        sm = cv2.GaussianBlur(sm, (0, 0), 10)
        P0c = cv2.resize((sm > 0.5).astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
        cs, _ = cv2.findContours((P0c > 0.5).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        c = max(cs, key=cv2.contourArea)[:, 0, :].astype(np.float32)
        on = (c[:, 0] > 8) & (c[:, 0] < W - 9) & (c[:, 1] > 8) & (c[:, 1] < H - 9)        # leave out the frame's own edges
        runs, cur = [], []
        for i in range(len(c)):
            if on[i]: cur.append(c[i])
            elif cur: runs.append(cur); cur = []
        if cur: runs.append(cur)
        if len(runs) > 1 and on[0] and on[-1]: runs[0] = runs[-1] + runs[0]; runs = runs[:-1]
        path = np.array(max(runs, key=len), np.float32)
        k = 15; path = np.stack([np.convolve(np.r_[[path[0, i]] * k, path[:, i], [path[-1, i]] * k], np.ones(2 * k + 1) / (2 * k + 1), "valid") for i in range(2)], 1)
        if path[0, 0] > path[-1, 0]: path = path[::-1]                                  # draw it left to right, over his head
        seg = np.sqrt((np.diff(path, axis=0) ** 2).sum(1))
        _NL.update(c=path, cum=np.r_[0, np.cumsum(seg)], F0=F0, P0=P0c,
                   Dout=cv2.distanceTransform(((P0c <= 0.5) * 255).astype(np.uint8), cv2.DIST_L2, 5).astype(np.float32))
    return _NL

def neonloop110(out, f, s, person=None):
    last = E.DUR_F - 1
    if f < NEON_F0: return out
    if f >= last: return frame0_plate108().copy()
    t = (f - NEON_F0) / (last - NEON_F0); D = _neon_setup(); F0 = D["F0"]
    lv = 1 - 0.86 * smooth(t / 0.28)                                                     # the blood room loses power
    for tk, dd in ((0.07, 0.35), (0.15, 0.30)):
        lv *= 1 - dd * math.exp(-((t - tk) / 0.018) ** 2)
    o = out * lv
    p = smooth((t - 0.20) / 0.36)                                                        # the tube draws his outline in the dark
    cv = np.zeros((H, W), np.float32)
    if p > 0:
        n = int(np.searchsorted(D["cum"], p * D["cum"][-1]))
        pts = D["c"][:max(2, n)]
        cv2.polylines(cv, [np.round(pts * 8).astype(np.int32)], False, 1.0, 5, cv2.LINE_AA, shift=3)
        if p < 1:
            hx, hy = pts[-1]
            cv += 1.5 * np.exp(-(((_GX - hx) ** 2 + (_GY - hy) ** 2) / (2 * 10.0 ** 2)))
    on = 0.55 + 0.45 * smooth((t - 0.56) / 0.08)
    for tk, dd in ((0.58, 0.7), (0.62, 0.5)):                                            # it flickers fully on
        on *= 1 - dd * math.exp(-((t - tk) / 0.012) ** 2)
    fade = 1 - smooth((t - 0.84) / 0.13)
    cv = cv * on * fade
    R = -40 + 1500 * ein(clamp((t - 0.62) / 0.33, 0, 1), 1.4)                           # frame 0 lights up from the outline outward
    fill = np.clip((R - D["Dout"]) / 180.0, 0, 1) * smooth((t - 0.60) / 0.12)
    fill = np.maximum(fill, smooth((t - 0.90) / 0.09))
    o = o * (1 - fill[..., None]) + F0 * fill[..., None]
    g1 = cv2.GaussianBlur(cv, (0, 0), 6); g2 = cv2.resize(cv2.GaussianBlur(cv2.resize(cv, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 7), (W, H))
    o = o * (1 - 0.85 * np.clip(cv, 0, 1)[..., None]) + cv[..., None] * np.array([0.82, 0.93, 1.0], np.float32) + (g1 * 0.7 + g2 * 1.0)[..., None] * AMB110 * 0.55
    we = smooth((t - 0.93) / 0.07)
    return np.clip(o * (1 - we) + F0 * we, 0, 1)

# ---- THE DRIP (the loop, rev 1): as he looks up, one drop of blood falls in the dark beside his head (lit, refracting,
# stretched by its speed); it lands, the blood room becomes a liquid surface, the ripples run out from the impact and the
# bed (frame 0) comes up through them as through water; the surface calms on frame 0.
DRIP_F0 = E.fh(74.6)
DRIP_X, DRIP_Y = 0.84 * W, 0.82 * H
def driploop110(out, f, s, person=None):
    last = E.DUR_F - 1
    if f < DRIP_F0: return out
    if f >= last: return frame0_plate108().copy()
    t = (f - DRIP_F0) / (last - DRIP_F0); F0 = frame0_plate108()
    ti = 0.36                                                                           # the impact
    o = out * (1 - 0.45 * smooth(t / ti))
    if t < ti:                                                                          # the drop falls beside him
        u = t / ti; y = -0.06 * H + (DRIP_Y + 0.06 * H) * u * u
        o = blood_drop108(o.copy(), DRIP_X, y, 40.0, stretch=1.0 + 1.0 * u, tint=1.0, gloss=1.6)
        return np.clip(o, 0, 1)
    v = (t - ti) / (1 - ti)
    d = np.sqrt((_GX - DRIP_X) ** 2 + ((_GY - DRIP_Y) * 1.15) ** 2) + 1e-3
    R = 60 + 2300 * ein(v, 0.62)
    decay = (1 - smooth((v - 0.35) / 0.55))
    wave = np.zeros_like(d)
    for k_, (lag, amp) in enumerate(((0, 1.0), (110, 0.7), (220, 0.45), (330, 0.25))):
        rr = R - lag
        if rr > 0: wave += amp * np.exp(-((d - rr) / 55.0) ** 2) * np.sin((d - rr) / 16.0)
    disp = 22 * wave * decay
    reveal = np.clip((R * 0.82 - d) / 220.0, 0, 1); reveal = reveal * reveal * (3 - 2 * reveal)
    reveal = np.maximum(reveal, smooth((v - 0.45) / 0.25))
    base = o * (1 - reveal[..., None]) + F0 * reveal[..., None]
    mx = (_GX + disp * (_GX - DRIP_X) / d).astype(np.float32); my = (_GY + disp * (_GY - DRIP_Y) / d).astype(np.float32)
    r_ = cv2.remap(base, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    crest = np.clip(wave, 0, 1) * decay
    r_ = r_ * (1 + 0.10 * crest[..., None])                                                # light catching the crests (no drawn rings)
    splash = math.exp(-((t - ti) / 0.05) ** 2) * np.exp(-(((_GX - DRIP_X) ** 2 + (_GY - DRIP_Y) ** 2) / (2 * 28.0 ** 2)))
    r_ = r_ + splash[..., None] * np.array([0.06, 0.06, 0.45], np.float32)
    we = smooth((t - 0.93) / 0.07)
    return np.clip(r_ * (1 - we) + F0 * we, 0, 1)

def render(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin")
    out, person = base108(s, f)
    if s["n"] == "light": out = light_scene110(out, f)
    if s["n"] == "anguish": out = bulb110(out, f, s)
    if s["n"] == "fan" and not (n_ and kn >= -TR2["fan110"][1]):
        Pm = None if person is None else _pp_clean(np.clip(np.asarray(person, np.float32), 0, 1))
        out = fan_draw110(out, f, Pm, keep=_face_keep(s, f))
    if tin in TR2 and k < TR2[tin][2] and P is not None:
        out = TR2[tin][0](edge108(P, "last"), out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, edge108(n_, "first"), kn, f, s, n_)
    if s.get("tout") == "driploop110": out = driploop110(out, f, s, person)
    out = beat_fx(out, f)
    out = title110(out, f)
    out = flash_governor(out)
    return (np.clip(finish110(out, f, s), 0, 1) * 255 + 0.5).astype(np.uint8)

# ============================================================================ v110 rev 2 (the owner's notes)
# "the beginning window graphic ... isn't really necessary" (the headlight panes: gone, a gentle push); "I'm losing power
# ... phase it in ... I'm losing, and then power would be when it drops ... I'm losing would already be written"; "the
# blood spatter scene ... smoother or more cinematic" (THE SWINGING LIGHT into the blood wall, a glide); "the gun
# transition ... more seamless and smoother"; "the beginning of the beat drop ... shake a little bit too much ... reduce
# the shaking/beat jump" (no impact shake, the camera rests through the drop bar, half the punch after).

# ---- the beat camera, calmer: rests through the drop's first bar (the title), half the punch and kick after it
def beat_phase(f):
    e = f / FPS / E.HB; ph = (e % 2) * E.HB; bi = int(e // 2)
    hook = (34 <= e < 68) and not (42.6 <= e < 47.5) and not (51.5 <= e < 57.5) and not (64.5 <= e < 68)
    return ph, bi, hook, False

def beat_bounce(f):
    ph, bi, hook, rival = beat_phase(f)
    return 1 + 0.022 * math.exp(-ph / 0.10) if hook else 1.0

def shake(f):
    dx, dy, rot = _shake_v10(f)
    ph, bi, hook, rival = beat_phase(f)
    if hook: rot += (0.35 if bi % 2 else -0.35) * math.exp(-ph / 0.13)
    return dx, dy, rot

def beat_fx(out, f):
    ph, bi, hook, rival = beat_phase(f)
    if not hook or ph > 0.05: return out
    k = math.exp(-ph / 0.025)
    return np.clip(rgb_split(radial_blur(out, W / 2, H * 0.46, 1.0, 1.0 + 0.015 * k, 3), 3 * k), 0, 1)

def init_hits():
    HITS.clear()                                                                       # no impact shake on the drop or the loop

# ---- I'M LOSING POWER, phased: "I'M LOSING" is written into the dark of the fan room during the last bar of the break,
# letter by letter like weak tubes catching (dim, flickering with the fan's low power); on the drop "POWER" slams on
# with the surge and the whole line comes up to full; then it loses power letter by letter.
T_PH0 = E.th(24.8)                                                                     # the first letter catches
def title110(out, f):
    t = f / FPS; T0 = E.th(30); T_DIE = E.th(33.3)
    if t < T_PH0 - 0.001 or t > E.th(34.8): return out
    l1, l2 = _title_layer(1)
    lay = np.zeros((H, W), np.float32)
    low = 0.50 + 0.10 * math.sin(t * 23.0) * math.sin(t * 7.1 + 0.4)                    # the fan's brown power
    up = smooth((t - T0) / 0.06)                                                         # full power on the drop
    def place(letters, y, gap, a_of):
        wsum = sum((m.shape[1] if m is not None else 46) for c, m in letters) + gap * (len(letters) - 1); x = (W - wsum) / 2
        for i, (c, m) in enumerate(letters):
            if m is None: x += 46 + gap; continue
            a = a_of(i)
            td = T_DIE + 0.07 * ((i * 5) % 7) + 0.03 * i
            if t > td: a *= max(0.0, 1 - smooth((t - td) / 0.16)) * (0.72 + 0.28 * math.cos((t - td) * 2 * math.pi * 4.0 + i))
            if a > 0.003:
                mm = m.astype(np.float32) / (m.max() + 1e-6); h_, w_ = mm.shape; yy, xx = int(y), int(x)
                ys, xs, ye, xe = max(0, yy), max(0, xx), min(H, yy + h_), min(W, xx + w_)
                if ye > ys and xe > xs: lay[ys:ye, xs:xe] = np.maximum(lay[ys:ye, xs:xe], mm[ys - yy:ye - yy, xs - xx:xe - xx] * a)
            x += m.shape[1] + gap
    step = E.HB / 2                                                                       # one letter per 16th
    def a1(i):
        k = i - (1 if i > 3 else 0)                                                       # the space takes no step
        tc = T_PH0 + k * step
        if t < tc: return 0.0
        catch = smooth((t - tc) / 0.05) * (1 - 0.65 * math.exp(-((t - tc - 0.07) / 0.018) ** 2)) * (1 - 0.4 * math.exp(-((t - tc - 0.14) / 0.018) ** 2))
        return catch * (low * (1 - up) + 1.0 * up)
    place(l1, H * 0.615, 10, a1)
    lay2 = np.zeros((H, W), np.float32)
    if t >= T0:
        lay_keep = lay; lay = lay2
        place(l2, H * 0.680, 12, lambda i: 1.0)
        lay2 = lay; lay = lay_keep
        k = t - T0; sc = 1 + 0.30 * math.exp(-k / 0.05)                                   # POWER slams in
        cx, cy = W / 2, H * 0.72
        if sc > 1.003:
            lays = [cv2.warpAffine(lay2, np.float32([[s_, 0, cx * (1 - s_)], [0, s_, cy * (1 - s_)]]), (W, H)) for s_ in (sc, 1 + (sc - 1) * 0.6, 1 + (sc - 1) * 0.3)]
            lay2 = (lays[0] + lays[1] + lays[2]) / 3
        lay = np.maximum(lay, lay2)
    surge = 0.0
    for eb in (30, 32, 34):
        dk = t - E.th(eb)
        if dk >= 0: surge = max(surge, math.exp(-dk / 0.10))
    hot = math.exp(-max(0.0, t - T0) / 0.09) if t >= T0 else 0.0
    g1 = cv2.GaussianBlur(lay, (0, 0), 7)
    g2 = cv2.resize(cv2.GaussianBlur(cv2.resize(lay, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 8), (W, H), interpolation=cv2.INTER_LINEAR)
    core = np.array([0.82, 0.93, 1.0], np.float32) * (1 - 0.5 * hot) + np.array([1.0, 1.0, 1.0], np.float32) * 0.5 * hot
    o = out * (1 - 0.88 * lay[..., None]) + lay[..., None] * core * (0.92 + 0.08 * surge) \
        + (g1 * (0.55 + 0.35 * surge) + g2 * (0.85 + 0.6 * surge + 0.8 * hot))[..., None] * AMB110 * (0.35 + 0.20 * up)
    return np.clip(o, 0, 1)

# ---- THE BARREL, seamless: one continuous push into the muzzle; a soft light grows in the bore; the next shot opens
# inside the bore through a wide, feathered edge and keeps the same forward motion (it starts pushed in about the bore and
# settles), with a little radial motion blur at the fastest moment; no hard ring, no burst.
def barrel110(A, B, j, f, sa, sb, pre=36, post=26):
    q = (j + pre + 0.5) / (pre + post)
    mx, my, r0 = _muzzle(sa, f if j < 0 else sa["f1"] - 1)
    z = smooth(q)
    ZA = math.exp(math.log(6.0) * ein(z, 1.5))
    speed = math.sin(math.pi * clamp(q, 0, 1)) ** 2                                       # fastest in the middle
    def push(img, Z, cx, cy):
        if Z < 1.002: return img
        if speed < 0.2: return _zoom_about(img, Z, cx, cy)
        return (_zoom_about(img, Z, cx, cy) + _zoom_about(img, Z * (1 + 0.03 * speed), cx, cy) + _zoom_about(img, Z * (1 + 0.06 * speed), cx, cy)) / 3
    Az = push(A, ZA, mx, my)
    rB = r0 * ZA
    op = ein(smooth((q - 0.30) / 0.62), 2.0)
    rw = rB * 0.85 + 1.25 * math.hypot(W, H) * op
    d = np.sqrt((_GX - mx) ** 2 + (_GY - my) ** 2)
    feather = 0.55 * rw + 30
    win = np.clip((rw - d) / feather + 0.5, 0, 1); win = win * win * (3 - 2 * win)
    win = np.maximum(win, smooth((q - 0.86) / 0.12))
    ZB = 1 + 0.45 * (1 - smooth((q - 0.30) / 0.70))                                      # the next shot keeps moving forward
    cbx = mx + (W / 2 - mx) * smooth(q); cby = my + (H * 0.45 - my) * smooth(q)
    Bz = push(B, ZB, cbx, cby)
    glow = np.exp(-(d / max(6.0, rB * (0.6 + 2.0 * op))) ** 2) * math.sin(math.pi * clamp((q - 0.20) / 0.70, 0, 1))
    LIGHT = np.array([0.80, 0.88, 0.96], np.float32)
    showB = smooth((rw - 260.0) / 520.0)                                                  # light first; the next shot only once the bore is big
    inner = LIGHT * (0.55 + 0.35 * np.exp(-(d / max(8.0, 0.6 * rw)) ** 2))[..., None]
    content = inner * (1 - showB) + Bz * showB
    o = Az * (1 - win[..., None]) + content * win[..., None]
    o = o + glow[..., None] * LIGHT * 0.30
    return np.clip(o, 0, 1)
TR2["barrel110"] = (barrel110, 36, 26)

# ---- THE SWINGING LIGHT (the anguish shot -> the blood wall): the bare bulb's pool of light swings across him, and on
# its last swing the pool carries the blood room inside it: it grows as it comes toward us, the blood-spattered wall lit in
# it, the dark around it falling away, until it fills the frame. Soft-edged, one continuous push.
def _bulb_xy(sa, f):
    t = (f - sa["f0"]) / FPS; per = 4 * E.HB
    x = W * 0.5 + W * 0.30 * math.sin(2 * math.pi * t / per - 0.6)
    y = H * 0.20 - H * 0.03 * abs(math.cos(2 * math.pi * t / per - 0.6))
    return x, y

def swinglight110(A, B, j, f, sa, sb, pre=44, post=26):
    q = (j + pre + 0.5) / (pre + post)
    bx, by = _bulb_xy(sa, f)
    c = smooth((q - 0.20) / 0.80)
    cx = bx + (W * 0.55 - bx) * c; cy = (by + 0.22 * H) + (H * 0.42 - (by + 0.22 * H)) * c   # the pool, below the bulb
    r = 120 + 2300 * ein(smooth((q - 0.12) / 0.86), 1.8)
    d = np.sqrt(((_GX - cx) / 0.85) ** 2 + (_GY - cy) ** 2)
    m = np.clip((r - d) / (0.55 * r + 90), 0, 1); m = m * m * (3 - 2 * m)
    m = np.maximum(m, smooth((q - 0.88) / 0.11))
    Az = _zoom_about(A, 1 + 0.05 * smooth(q), W / 2, H * 0.40)
    Bz = _zoom_about(B, 1 + 0.10 * (1 - smooth(q)), cx, cy)
    lit = 0.80 + 0.35 * np.exp(-(d / (0.65 * r + 40)) ** 2)
    showB = smooth((r - 380.0) / 520.0)                                                   # small pool: just his own light; the blood room once it is big
    inner = Az * (1.0 + 0.35 * np.exp(-(d / (0.6 * r + 30)) ** 2))[..., None] * (1 - showB) + np.clip(Bz * lit[..., None], 0, 1) * showB
    o = Az * (1 - 0.55 * smooth(q)) * (1 - m[..., None]) + inner * m[..., None]
    halo = np.exp(-((d - r) / (0.18 * r + 30)) ** 2) * (1 - smooth((q - 0.80) / 0.18)) * 0.10
    return np.clip(o + halo[..., None] * AMB110, 0, 1)
TR2["swinglight110"] = (swinglight110, 44, 26)

# ---- GLIDE (the blood wall -> him looking up at the blood): a slow, matched drift: both pictures rise together, the
# bright of the next one arriving first (a luma dissolve), soft.
def glide110(A, B, j, f, sa, sb, pre=16, post=16):
    q = (j + pre + 0.5) / (pre + post); z = smooth(q)
    Ad = cv2.warpAffine(A, np.float32([[1 + 0.04 * z, 0, -W / 2 * 0.04 * z], [0, 1 + 0.04 * z, -H * 0.45 * 0.04 * z - 70 * z]]), (W, H), borderMode=cv2.BORDER_REPLICATE)
    Bd = cv2.warpAffine(B, np.float32([[1, 0, 0], [0, 1, 70 * (1 - z)]]), (W, H), borderMode=cv2.BORDER_REPLICATE)
    LB = cv2.GaussianBlur(lum(Bd), (0, 0), 12)
    w = np.clip((z * 1.6 - 0.3) + (LB - 0.5) * 0.9, 0, 1); w = w * w * (3 - 2 * w)
    w = np.maximum(w, smooth((q - 0.85) / 0.14)) * (1 - (q < 0.02))
    return np.clip(Ad * (1 - w[..., None]) + Bd * w[..., None], 0, 1)
TR2["glide110"] = (glide110, 16, 16)

# ---- TILT (the blood wall -> him looking up at the blood): the camera tilts up fast to the ceiling's blood, motion-
# blurred, onto him looking up at it (replaces the glide's double exposure)
def tilt110(A, B, j, f, sa, sb, pre=9, post=12):
    if j < 0:
        u = (j + pre + 0.5) / pre; e = ein(u, 2.2)
        return np.clip(_vblur_shift(A, 0.40 * H * e, 0.34 * H * e), 0, 1)
    v = (j + 0.5) / post; e = 1 - (1 - smooth(v)) ** 2.2
    return np.clip(_vblur_shift(B, -0.40 * H * (1 - e), 0.30 * H * (1 - e)), 0, 1)
TR2["tilt110"] = (tilt110, 9, 12)

# ---- rev 2, after the motion audit: the bulb swings wider and faster (the span was near still once the beat camera
# calmed), the swinging light's extra light fades out before the cut (a brightness step), a soft matched dissolve into
# the last shot (the smear jumped)
BULB_AMP, BULB_PER = 0.40, 3.0
def _bulb_xy(sa, f):
    t = (f - sa["f0"]) / FPS; per = BULB_PER * E.HB
    x = W * 0.5 + W * BULB_AMP * math.sin(2 * math.pi * t / per - 0.6)
    y = H * 0.20 - H * 0.04 * abs(math.cos(2 * math.pi * t / per - 0.6))
    return x, y

def bulb110(out, f, s):
    t = (f - s["f0"]) / FPS
    k = smooth(t / 0.25)
    x, y = _bulb_xy(s, f); x = W * 0.5 + (x - W * 0.5) * k
    d2 = ((_GX - x) / (0.32 * W)) ** 2 + ((_GY - y) / (0.52 * H)) ** 2
    m = 0.32 + 1.10 * np.exp(-d2)
    return np.clip(out * m[..., None] + np.exp(-d2 * 3.0)[..., None] * AMB110 * 0.06, 0, 1)

def swinglight110(A, B, j, f, sa, sb, pre=44, post=26):
    q = (j + pre + 0.5) / (pre + post)
    bx, by = _bulb_xy(sa, f)
    c = smooth((q - 0.20) / 0.80)
    cx = bx + (W * 0.55 - bx) * c; cy = (by + 0.22 * H) + (H * 0.42 - (by + 0.22 * H)) * c
    r = 120 + 2300 * ein(smooth((q - 0.12) / 0.86), 1.8)
    d = np.sqrt(((_GX - cx) / 0.85) ** 2 + (_GY - cy) ** 2)
    m = np.clip((r - d) / (0.55 * r + 90), 0, 1); m = m * m * (3 - 2 * m)
    m = np.maximum(m, smooth((q - 0.88) / 0.11))
    Az = _zoom_about(A, 1 + 0.05 * smooth(q), W / 2, H * 0.40)
    Bz = _zoom_about(B, 1 + 0.10 * (1 - smooth(q)), cx, cy)
    extra = 1 - smooth((q - 0.62) / 0.33)                                                 # the pool's extra light is gone by the cut's end
    lit = 1 + (0.35 * np.exp(-(d / (0.65 * r + 40)) ** 2) - 0.20) * extra
    showB = smooth((r - 380.0) / 520.0)
    inner = Az * (1.0 + 0.35 * np.exp(-(d / (0.6 * r + 30)) ** 2))[..., None] * (1 - showB) + np.clip(Bz * lit[..., None], 0, 1) * showB
    o = Az * (1 - 0.55 * smooth(q)) * (1 - m[..., None]) + inner * m[..., None]
    halo = np.exp(-((d - r) / (0.18 * r + 30)) ** 2) * extra * 0.10
    return np.clip(o + halo[..., None] * AMB110, 0, 1)

def glide110(A, B, j, f, sa, sb, pre=16, post=16):
    """a soft matched dissolve: both pictures drift up together, eased, no jump."""
    q = (j + pre + 0.5) / (pre + post); z = smooth(q)
    Ad = _zoom_about(A, 1 + 0.04 * z, W / 2, H * 0.40)
    Bd = _zoom_about(B, 1 + 0.04 * (1 - z), W / 2, H * 0.40)
    w = smooth((q - 0.25) / 0.50)
    return np.clip(Ad * (1 - w) + Bd * w, 0, 1)
TR2["swinglight110"] = (swinglight110, 44, 26)                                         # register the rev 2 versions
TR2["glide110"] = (glide110, 16, 16)

# ============================================================================ v110 rev 3 (the owner: "remove the I'm losing power")
def title110(out, f):
    return out                                                                         # no text in the final edit

# ============================================================================ v111 — MONSTER (Dexter × Kanye West "Monster")
# I SHOOT THE LIGHTS OUT. A flow of light: the lights behind him die one by one on "I shoot the lights out"; the light
# comes back first (emerge); the sun comes up at the edge of the frame and the day burns white; the sun goes down and the
# garden lights come on; a full moon rises where he looks and becomes the lamp over the kill table; THE PASSENGER: in the
# light from below his shadow climbs the wall and grows into something else, and on "...I'm a monster" it lunges over the
# lens with the blood-soaked suit inside it; the light bar's red and blue; sun through the canopy; he fires at us and the
# flash lands on frame 0 (the loop). Look NIGHTSHADE: teal-navy shadows, warm practicals, harder and redder after the drop.
_L111 = {}
TEAL111 = np.array([0.050, 0.018, -0.034], np.float32)      # BGR shadow push (teal-navy)
WARM111 = (-0.10, 0.015, 0.10)                               # BGR highlight push (warm practicals)
_grade_pre111 = grade
def grade(img, s, f):
    if s.get("look") != "night111": return _grade_pre111(img, s, f)
    hard = s["e0"] >= E.HDROP; key = "h" if hard else "c"
    if key not in _L111:
        x = np.linspace(0, 1, 1024, dtype=np.float32)
        ys = [0.010, 0.026, 0.125, 0.45, 0.80, 0.94, 0.975] if hard else [0.018, 0.034, 0.132, 0.44, 0.78, 0.925, 0.96]
        _L111[key] = (x, PchipInterpolator([0, .05, .2, .5, .8, .95, 1], ys)(x).astype(np.float32))
    g, gains = corr9(s); ev = s.get("ev") or 0; lx, ly = _L111[key]; gains = tuple(float(v) for v in gains)
    x = apply_lut3(img, tone_lut(("ni111", key, s["n"], ev, float(g), gains), gains, g, ev, lx, ly)) if in_unit(img) else \
        np.interp(np.clip(np.clip(img * np.array(gains, np.float32), 0, 1) ** g * 2 ** ev, 0, 1), lx, ly).astype(np.float32)
    Bc, Gc, Rc = (np.ascontiguousarray(x[..., c]) for c in range(3))
    L = Bc * 0.114 + Gc * 0.587 + Rc * 0.299
    red = np.clip((Rc - 1.85 * np.maximum(Gc, Bc) - s.get("redthr", 0.06)) * 3.0, 0, 1)
    sat = (0.60 if hard else 0.52) + 0.10 * np.clip((Rc - Bc) * 2.0, 0, 1) * (1 - red) + (0.62 if hard else 0.50) * red
    hi = np.clip((L - 0.42) * 1.9, 0, 1); sh = np.clip(1 - L * 1.7, 0, 1) ** 1.5
    o = np.empty(x.shape, np.float32)
    for ch, P in enumerate((Bc, Gc, Rc)):
        v = L + (P - L) * sat
        v += sh * TEAL111[ch] + hi * L * WARM111[ch]
        o[..., ch] = v
    if s.get("night"):                                                            # day for night (the moon shot)
        Lo = lum(np.clip(o, 0, 1))
        sky = np.clip((Lo - 0.62) / 0.25, 0, 1)                                   # the burnt dusk sky -> a moonlit navy
        gy = (np.arange(o.shape[0], dtype=np.float32) / o.shape[0])[:, None]
        for ch, (a, b) in enumerate(((0.95, 0.30), (0.60, 0.17), (0.42, 0.10))):
            o[..., ch] = (o[..., ch] * a * 0.62 + 0.012) * (1 - sky) + (b + 0.10 * (1 - gy)) * sky
    return np.clip(o, 0, 1, out=o)

def finish111(out, f, s=None):
    hard = s is not None and s["e0"] >= E.HDROP
    L = lum(out)
    q = cv2.resize(np.clip(L - 0.58, 0, 1), (W // 8, H // 8), interpolation=cv2.INTER_AREA)
    bloom = cv2.resize(cv2.GaussianBlur(q, (0, 0), 5), (W, H), interpolation=cv2.INTER_LINEAR)
    col = (0.30, 0.55, 1.00) if hard else (0.36, 0.68, 1.00)
    g = grain(f, 0.016)[..., 0]; v = VIG[..., 0]
    o = out.copy()
    for ch in range(3):
        oc = o[..., ch]; oc += bloom * col[ch] * 0.32; oc *= v; oc += g
    return np.clip(o, 0, 1, out=o)

def _pick(s_, f):
    p = _person(s_, f)
    return None if p is None else _pp_clean(np.clip(np.asarray(p, np.float32), 0, 1))

def _lights_mask(img, person, thr=0.38, soft=0.22):
    """the practical lights of a frame: bright, out-of-person regions (1/4 res, soft)."""
    q = cv2.resize(img, (W // 4, H // 4), interpolation=cv2.INTER_AREA); Lq = lum(q)
    m = np.clip((Lq - thr) / soft, 0, 1)
    if person is not None: m *= 1 - cv2.resize(person, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    return m

# ---- LIGHTS OUT (the first shot): "I shoot the lights out": the lights of the city behind him go out one by one, a
# wave from the edges of the frame in toward him (each stutters, flares and dies, and the night thickens with every one);
# on "out" the last of them go and the light on him drops to a cold rim.
T_WAVE = (E.th(6.6), E.th(10.0)); T_KEY = E.th(10.45)       # "the lights" ... "out"; then the light on him
_LO = {}
def _lo_map(s_):
    """per light (1/4 res): the time it dies (inf where there is no light)."""
    if "map" not in _LO:
        f0 = s_["f0"] + 4; img = base108(s_, f0)[0]; P = _pick(s_, f0)
        m = _lights_mask(img, P, 0.34, 0.20)
        lab = (m > 0.30).astype(np.uint8); n, cc = cv2.connectedComponents(lab)
        ys, xs = np.mgrid[0:H // 4, 0:W // 4]
        tmap_ = np.full(cc.shape, np.inf, np.float32)
        items = [(abs(float(xs[cc == i].mean()) - W / 8), i) for i in range(1, n) if (cc == i).sum() >= 2]
        items.sort(reverse=True)                                                  # the outermost first
        rng = np.random.default_rng(1101)
        early = {0: E.th(1.4), 1: E.th(2.6), 2: E.th(3.4), 3: E.th(4.6), 4: E.th(5.4)}   # "I shooooot": a light blows on each beat before the wave
        for r_, (_, i) in enumerate(items):
            u = r_ / max(1, len(items) - 1)
            tmap_[cc == i] = early.get(r_, T_WAVE[0] + (T_WAVE[1] - T_WAVE[0]) * clamp(u + rng.uniform(-0.08, 0.08), 0, 1))
        grow = cv2.erode(tmap_, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))   # each light's glow dies with it
        _LO["map"] = (grow, len(items))
    return _LO["map"]

def _follow(s_, fa, fb):
    """the affine (output px) that carries frame fa's picture to frame fb's framing (the push and the drift)."""
    a0 = to_screen(s_, fa, 0.0, 0.0); a1 = to_screen(s_, fa, 100.0, 100.0)
    b0 = to_screen(s_, fb, 0.0, 0.0); b1 = to_screen(s_, fb, 100.0, 100.0)
    k = (b1[0] - b0[0]) / max(1e-6, (a1[0] - a0[0]))
    return np.float32([[k, 0, b0[0] - k * a0[0]], [0, k, b0[1] - k * a0[1]]])

def lightsout111(out, f, s_, person):
    t = f / FPS
    tm, n = _lo_map(s_)
    M = _follow(s_, s_["f0"] + 4, f); M[:, 2] /= 4.0                                # the lights' map follows the camera
    tm = cv2.warpAffine(tm, M, (tm.shape[1], tm.shape[0]), flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=float("inf"))
    dt = t - tm                                                                   # < 0: still on
    mult = np.ones(tm.shape, np.float32)
    st_ = (dt > -0.14) & (dt < 0)
    mult[st_] = 1 - 0.6 * (np.sin((dt[st_] + 0.14) * 140) > 0.1)                   # the stutter
    fl = (dt >= 0) & (dt < 0.05); mult[fl] = 1.9                                   # it blows
    mult[dt >= 0.05] = 0.08                                                        # out
    if t < 0.45:                                                                   # the shot's impact: every light shivers
        mult[dt < -0.14] *= 1 - 0.45 * math.exp(-t / 0.18) * (math.sin(t * 95) > -0.2)
    mult = cv2.GaussianBlur(mult, (0, 0), 2.0)
    M = cv2.resize(mult, (W, H), interpolation=cv2.INTER_CUBIC)
    frac = float(np.mean(np.isfinite(tm) & (tm < t))) / max(1e-6, float(np.mean(np.isfinite(tm))))
    P = _pp_clean(np.clip(np.asarray(person, np.float32), 0, 1)) if person is not None else np.zeros((H, W), np.float32)
    steps = [E.th(1.0), E.th(6.8), E.th(8.1), E.th(10.25)]                       # "shoot", "the", "lights", "out"
    room = 1.0
    for i_, ts in enumerate(steps):                                               # the room drops a step on each word (a stutter, then down)
        if t >= ts: room -= (0.12, 0.14, 0.18, 0.22)[i_] * (1 - 0.5 * (t - ts < 0.08) * (math.sin((t - ts) * 160) > 0))
    room = min(room, 1.0 - 0.45 * smooth(frac))
    key = 1.0 - 0.05 * sum(1 for ts in steps[:3] if t >= ts)
    if t >= T_KEY - 0.12:
        key = 0.32 + 0.68 * math.exp(-max(0.0, t - T_KEY) / 0.08)
        if t < T_KEY: key = 1.0 - 0.45 * (math.sin((t - T_KEY) * 90) > 0)
    Mb = np.clip(M, 0, 1)[..., None]                                              # a dead light keeps only what is under it (no dark squares)
    lit = out * np.clip(M, 1, 2)[..., None] * Mb + np.minimum(out, 0.05) * (1 - Mb)
    o = lit * (room * (1 - P))[..., None] + out * (key * P)[..., None]
    pops = cv2.resize(np.clip(fl.astype(np.float32), 0, 1), (W, H), interpolation=cv2.INTER_LINEAR)
    if pops.max() > 0:
        g = cv2.GaussianBlur(pops, (0, 0), 30) * 3.2
        o += g[..., None] * np.array([0.55, 0.80, 1.0], np.float32) * 0.6
    if t >= T_KEY:                                                                # what is left: a cold rim on him
        rim = np.clip(P - cv2.GaussianBlur(P, (0, 0), 6), 0, 1) * smooth((t - T_KEY) / 0.25)
        o += (rim * 0.12)[..., None] * np.array([0.95, 0.75, 0.45], np.float32)
    return np.clip(o, 0, 1)

# the shot's flash lands on frame 0 (the loop): its light decays over the first frames, the lights shiver from it
MUZ_OUT = (884.0, 395.0)                                                         # where the flash was on screen (set from the aim shot)
def flash_in111(out, f):
    if f > 22: return out
    a = 0.70 * math.exp(-f / 4.0)
    d2 = ((_GX - MUZ_OUT[0]) ** 2 + (_GY - MUZ_OUT[1]) ** 2)
    glow = np.exp(-d2 / (2 * 520.0 ** 2)) * a
    return np.clip(out * (1 + 0.8 * glow[..., None]) + glow[..., None] * np.array([0.42, 0.66, 0.95], np.float32) * 0.6, 0, 1)

# ---- EMERGE (light first): the last of the light goes, and the next shot comes up out of the dark brightest-first.
def emerge111(A, B, j, f, sa, sb, pre=10, post=16):
    q = (j + pre + 0.5) / (pre + post)
    fa = 1 - 0.62 * smooth(q / 0.6)                                              # the old shot sinks (never to black)
    LB = cv2.resize(lum(cv2.resize(B, (W // 4, H // 4), interpolation=cv2.INTER_AREA)), (W, H), interpolation=cv2.INTER_LINEAR)
    LB = cv2.GaussianBlur(LB, (0, 0), 6)
    thr = 0.80 - 1.10 * smooth((q - 0.12) / 0.80)                                # its brightest light first
    m = np.clip((LB - thr) / 0.28, 0, 1); m = m * m * (3 - 2 * m)
    m = np.maximum(m, 0.18 * smooth((q - 0.15) / 0.4))
    m = np.maximum(m, smooth((q - 0.82) / 0.18))
    bl = cv2.GaussianBlur(cv2.resize(np.clip(LB - 0.55, 0, 1), (W // 8, H // 8)), (0, 0), 4)
    halo = cv2.resize(bl, (W, H)) * math.sin(math.pi * clamp((q - 0.25) / 0.75, 0, 1)) * 0.5
    o = A * fa * (1 - m[..., None]) + B * m[..., None] + halo[..., None] * np.array([0.40, 0.70, 1.0], np.float32)
    return np.clip(o, 0, 1)
TR2["emerge111"] = (emerge111, 10, 16)

# ---- THROUGH THE FENCE (the fence -> the truck): we push through the chain-link: its lit wires fly past the lens and
# the other side of the fence is the next shot.
def fence111(A, B, j, f, sa, sb, pre=12, post=12):
    q = (j + pre + 0.5) / (pre + post)
    Af = A                                                                       # (the engine passes the frozen edge after the cut)
    L = lum(cv2.resize(Af, (W // 2, H // 2), interpolation=cv2.INTER_AREA))
    th_ = L - cv2.morphologyEx(L, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13)))
    P = _pick(sa, sa["f1"] - 1)
    wires = np.clip((th_ - 0.05) * 7.0, 0, 1)
    if P is not None: wires *= 1 - cv2.resize(P, (W // 2, H // 2))
    wires = cv2.resize(wires, (W, H), interpolation=cv2.INTER_LINEAR)
    z = smooth(q); cx, cy = W * 0.5, H * 0.52
    ZW = math.exp(math.log(5.0) * ein(z, 1.6))                                   # the wires come at us fast
    ZA = 1 + 0.35 * z
    Az = _zoom_about(A, ZA, cx, cy, cv2.BORDER_REPLICATE)
    Bz = _zoom_about(B, 1 + 0.25 * (1 - z), cx, cy, cv2.BORDER_REPLICATE)
    w = smooth((q - 0.44) / 0.12)
    back = Az * (1 - w) + Bz * w
    Wz = _zoom_about(wires, ZW, cx, cy, cv2.BORDER_CONSTANT)
    Wz = cv2.GaussianBlur(Wz, (0, 0), 1 + 7 * z) * (1 - smooth((q - 0.62) / 0.33))
    Wc = _zoom_about(Af * wires[..., None], ZW, cx, cy, cv2.BORDER_CONSTANT)
    Wc = cv2.GaussianBlur(Wc, (0, 0), 1 + 7 * z)
    al = np.clip(Wz * 1.4, 0, 1)[..., None]
    o = back * (1 - al) + np.clip(Wc / np.maximum(Wz[..., None], 1e-3), 0, 1) * al
    return np.clip(o, 0, 1)
TR2["fence111"] = (fence111, 12, 12)

# ---- DAYBREAK (the truck at night -> the sunrise): the sun comes up where it is in the next shot (at the edge of the
# frame): a warm glow grows there in the dark, the light floods out from it, and the morning is inside the light.
_SUN = {}
def _sun_pos(sb, B0):
    if sb["n"] not in _SUN:
        Lq = cv2.GaussianBlur(lum(cv2.resize(B0, (W // 8, H // 8))), (0, 0), 3)
        y, x = np.unravel_index(int(np.argmax(Lq)), Lq.shape); _SUN[sb["n"]] = (x * 8.0 + 4, y * 8.0 + 4)
    return _SUN[sb["n"]]

def daybreak111(A, B, j, f, sa, sb, pre=14, post=14):
    q = (j + pre + 0.5) / (pre + post)
    sx, sy = _sun_pos(sb, B)
    d = np.sqrt((_GX - sx) ** 2 + (_GY - sy) ** 2)
    rad = 60 + 2300 * ein(smooth(q), 1.7)
    glow = np.exp(-(d / max(80.0, rad * 0.55)) ** 2) * math.sin(math.pi * clamp(q, 0, 1)) ** 0.8
    rv = np.clip((rad - d) / (0.6 * rad + 120) + 0.3, 0, 1); rv = rv * rv * (3 - 2 * rv)
    rv = np.maximum(rv * smooth((q - 0.18) / 0.5), smooth((q - 0.88) / 0.12))
    SUNC = np.array([0.42, 0.72, 1.0], np.float32)
    Al = A * (1 + 1.2 * glow[..., None]) + glow[..., None] * SUNC * 0.55
    o = Al * (1 - rv[..., None]) + (B + glow[..., None] * SUNC * 0.30) * rv[..., None]
    return np.clip(o, 0, 1)
TR2["daybreak111"] = (daybreak111, 14, 14)

# ---- BRIGHT OUT (sunrise -> the white day -> the lake): the exposure climbs until the highlights burn and spread, and
# the next shot comes down out of the light.
def brightout111(A, B, j, f, sa, sb, pre=8, post=12):
    q = (j + pre + 0.5) / (pre + post)
    e = math.sin(math.pi * clamp(q, 0, 1)) ** 1.3
    w = smooth((j + 3) / 6.0); img = A * (1 - w) + B * w                          # the switch is inside the burn
    lift = 1 + 1.6 * e
    x = np.clip(img * lift, 0, 1.6)
    hot = cv2.resize(cv2.GaussianBlur(cv2.resize(np.clip(x - 0.8, 0, 1), (W // 8, H // 8)), (0, 0), 5), (W, H))
    o = x + hot * 0.9 * e
    wh = smooth((e - 0.55) / 0.45) * 0.88                                         # near the peak the frame is the light itself
    o = o * (1 - wh) + np.array([0.80, 0.92, 1.00], np.float32) * wh
    return np.clip(o, 0, 1)
TR2["brightout111"] = (brightout111, 8, 12)

# ---- NIGHTFALL (the lake at sunset -> the garden at night): the sun goes down: the night comes down the frame from the
# sky (a wide, soft front), the day under it cooling and darkening, and the garden lamps come on one by one as it passes.
def _lamps(img, thr=0.50):
    q = cv2.resize(img, (W // 4, H // 4), interpolation=cv2.INTER_AREA); Lq = lum(q)
    return np.clip((Lq - thr) / 0.2, 0, 1)

def nightfall111(A, B, j, f, sa, sb, pre=14, post=18):
    q = (j + pre + 0.5) / (pre + post)
    yb = -0.35 * H + 1.75 * H * smooth(q)                                       # the front of the night
    front = np.clip((yb - _GY) / 520.0 + 0.5, 0, 1); front = front * front * (3 - 2 * front)
    dusk = smooth(q * 1.3)
    Ad = A * (1 - 0.45 * dusk) * np.array([1.08, 0.97, 0.88], np.float32) ** dusk
    lm = cv2.resize(cv2.GaussianBlur(_lamps(B), (0, 0), 1.5), (W, H), interpolation=cv2.INTER_LINEAR)
    xs = (_GX / W)                                                               # each lamp comes on a little after the front passes
    on = np.clip((yb - _GY - 140 - 260 * xs) / 90.0, 0, 1)
    flick = 0.75 + 0.25 * math.sin(f * 2.7)
    Bn = B * (1 - lm[..., None]) + B * (lm * on * (1.0 + 0.4 * (on < 0.95) * flick))[..., None]
    Bn = Bn + cv2.GaussianBlur(lm * on, (0, 0), 14)[..., None] * np.array([0.35, 0.62, 1.0], np.float32) * 0.35
    o = Ad * (1 - front[..., None]) + Bn * front[..., None]
    return np.clip(o, 0, 1)
TR2["nightfall111"] = (nightfall111, 14, 18)

# ---- THE MOON (the moon shot, a graphic): he looks up; a full moon rises behind the trees where he looks (seen only
# through the sky between the leaves), its halo washing the night, thin cloud drifting over it.
MOON_A = (150.0, 540.0); MOON_B = (175.0, 215.0); MOON_R = 66.0
_MT = {}
def _moon_tex():
    if "t" not in _MT:
        n = 4 * MOON_R; r = int(MOON_R)
        rng = np.random.default_rng(1111)
        tex = np.ones((2 * r + 1, 2 * r + 1), np.float32)
        for _ in range(26):                                                       # maria and craters
            cx_, cy_ = rng.uniform(0.15, 0.85, 2) * 2 * r; rr = rng.uniform(0.05, 0.28) * r
            yy, xx = np.mgrid[0:2 * r + 1, 0:2 * r + 1]
            tex -= 0.10 * np.exp(-((xx - cx_) ** 2 + (yy - cy_) ** 2) / (2 * rr * rr))
        tex = cv2.GaussianBlur(tex, (0, 0), 1.2)
        yy, xx = np.mgrid[0:2 * r + 1, 0:2 * r + 1]; dd = np.sqrt((xx - r) ** 2 + (yy - r) ** 2) / r
        limb = np.clip(1 - dd, 0, 1) ** 0.25
        disc = np.clip((1 - dd) * r / 1.5, 0, 1)
        _MT["t"] = (tex * (0.78 + 0.22 * limb), disc)
    return _MT["t"]

def _moon_xy(f, s_):
    u = clamp((f - s_["f0"]) / max(1, s_["f1"] - s_["f0"]), 0, 1); w = smooth(u * 1.15)
    return MOON_A[0] + (MOON_B[0] - MOON_A[0]) * w, MOON_A[1] + (MOON_B[1] - MOON_A[1]) * w

def _sky(img, person):
    L = lum(cv2.resize(img, (W // 4, H // 4), interpolation=cv2.INTER_AREA))
    b = cv2.resize(img, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    m = np.clip((b[..., 0] - b[..., 2] - 0.04) * 8, 0, 1) * np.clip((L - 0.05) * 12, 0, 1)    # the navy, not the leaves
    if person is not None: m *= 1 - cv2.resize(person, (W // 4, H // 4))
    m *= np.clip(1.3 - np.mgrid[0:H // 4, 0:W // 4][0] / (H / 4) * 1.6, 0, 1)
    return cv2.resize(cv2.GaussianBlur(m, (0, 0), 0.8), (W, H), interpolation=cv2.INTER_LINEAR)

def moon_draw111(out, f, s_, person, scale=1.0, at=None, sky=None):
    tex, disc = _moon_tex(); r = tex.shape[0] // 2
    mx, my = at if at is not None else _moon_xy(f, s_)
    P = None if person is None else _pp_clean(np.clip(np.asarray(person, np.float32), 0, 1))
    if sky is None: sky = _sky(out, P)
    rr = r * scale
    d = np.sqrt((_GX - mx) ** 2 + (_GY - my) ** 2)
    halo = np.exp(-(d / (rr * 3.2)) ** 2) * 0.22 + np.exp(-(d / (rr * 1.45)) ** 2) * 0.30
    o = out + (halo * sky)[..., None] * np.array([0.95, 0.88, 0.78], np.float32)
    if P is not None: o += (np.clip(P - cv2.GaussianBlur(P, (0, 0), 5), 0, 1) * 0.10)[..., None] * np.array([0.95, 0.85, 0.7], np.float32)   # its rim on him
    k = max(3, int(2 * rr + 1)) | 1
    T = cv2.resize(tex, (k, k)); D = cv2.resize(disc, (k, k))
    cl = nz108(1112, 10); sh = int(f * 1.6) % cl.shape[1]
    cloud = cv2.resize(np.roll(cl, sh, axis=1), (W, H))
    veil = np.clip((cloud - 0.55) * 2.2, 0, 0.55)
    x0, y0 = int(mx - k // 2), int(my - k // 2)
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + k), min(H, y0 + k)
    if xb > xa and yb > ya:
        sub = (slice(ya, yb), slice(xa, xb)); ts = (slice(ya - y0, yb - y0), slice(xa - x0, xb - x0))
        al = D[ts] * sky[sub] * (1 - veil[sub])
        col = T[ts][..., None] * np.array([0.88, 0.94, 0.97], np.float32)
        o[sub] = o[sub] * (1 - al[..., None]) + col * al[..., None]
    o += (veil * np.exp(-(d / (rr * 2.4)) ** 2) * sky * 0.35)[..., None] * np.array([0.9, 0.88, 0.85], np.float32)
    return np.clip(o, 0, 1)

# ---- MOON -> LAMP (the moon shot -> the lamp over the kill table): we push into the moon; it fills with light and settles
# into the lamp over him (the next shot opens aligned on its lamp, then eases back to its own framing).
_LAMP = {}
def _lamp_pos(sb, B0):
    if sb["n"] not in _LAMP:
        Lq = cv2.GaussianBlur(lum(cv2.resize(B0, (W // 8, H // 8))), (0, 0), 2)
        Lq[H // 16:, :] *= 0.6                                                   # the lamp is above him
        y, x = np.unravel_index(int(np.argmax(Lq)), Lq.shape); _LAMP[sb["n"]] = (x * 8.0 + 4, y * 8.0 + 4)
    return _LAMP[sb["n"]]

def moon111(A, B, j, f, sa, sb, pre=16, post=16):
    q = (j + pre + 0.5) / (pre + post)
    mx, my = _moon_xy(sa["f1"] - 1, sa); lx, ly = _lamp_pos(sb, B)
    LIGHT = np.array([0.82, 0.92, 0.99], np.float32)
    if j < 0:
        u = (j + pre) / pre
        P = _pick(sa, f)
        o = moon_draw111(A, f, sa, P, scale=1 + 2.2 * ein(u, 1.6))                 # it swells and burns, behind him
        d = np.sqrt((_GX - mx) ** 2 + (_GY - my) ** 2)
        g = np.exp(-(d / (MOON_R * (2 + 4 * u))) ** 2) * 0.85 * ein(u, 1.4)
        if P is not None: g = g * (1 - 0.85 * P)
        return np.clip(o + g[..., None] * LIGHT, 0, 1)
    u = smooth(j / post)
    dx = (mx - lx) * (1 - u); dy = (my - ly) * (1 - u)
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    o = cv2.warpAffine(B, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    d = np.sqrt((_GX - lx - dx) ** 2 + (_GY - ly - dy) ** 2)
    o = o + (np.exp(-(d / (MOON_R * 4.0)) ** 2) * 0.8 * (1 - u))[..., None] * LIGHT
    if j < 4:                                                                     # across the cut: through the light
        w = 1 - j / 4.0; o = o * (1 - 0.5 * w) + (A * 0.3 + 0.55 * LIGHT) * 0.5 * w
    return np.clip(o, 0, 1)
TR2["moon111"] = (moon111, 16, 16)

# ---- THE PASSENGER (the build, e57-e65): crouched in the light from below, the shadows grow around him (the midtones
# sink into the dark, a little more on every beat of the riser) while the light in his hands pulses.
def _face_guard(hx, hy, hw):
    el = ((_GX - hx) / (0.62 * hw)) ** 2 + ((_GY - hy) / (0.80 * hw)) ** 2
    return np.clip(el - 0.6, 0, 1)                                               # 0 on his face, 1 away from it

def _ps_u(f):
    return clamp((f / FPS - E.th(57)) / (E.th(65) - E.th(57)), 0, 1)

def shadow111(out, f, s_, person):
    u = _ps_u(f); t = f / FPS
    L = lum(out)
    g = 1 + 0.75 * ein(u, 1.4)                                                   # the dark takes the midtones
    k = (np.clip(L, 1e-4, 1) ** g) / np.clip(L, 1e-4, 1)
    k = np.where(L > 0.62, 1.0, k).astype(np.float32)
    ph = (t / E.HB) % 2.0
    pulse = math.exp(-ph * E.HB / 0.10) * clamp((t - E.th(59)) / 1.0, 0, 1)      # the light breathes on the beat
    hot = cv2.resize(cv2.GaussianBlur(cv2.resize(np.clip(L - 0.7, 0, 1), (W // 8, H // 8)), (0, 0), 6), (W, H))
    uu = clamp((f - s_["f0"]) / max(1, s_["f1"] - s_["f0"]), 0, 1)
    hot = hot * _face_guard(505.0 + 25 * uu, 360.0 - 10 * uu, 360.0 * (1 + 0.08 * uu))
    o = out * k[..., None] * (1 + 0.10 * pulse * u) + hot[..., None] * np.array([0.92, 0.94, 0.95], np.float32) * (0.25 + 0.9 * pulse) * u
    return np.clip(o, 0, 1)

# ---- THE PASSENGER, the drop (the passenger -> the suit): on "...I'm a monster" the monster comes out of the dark: the
# blood-soaked suit in the daylight shows through the darkest parts of the frame first, the front of it edged in red,
# and the light in his hands goes last.
def passenger111(A, B, j, f, sa, sb, pre=18, post=40):
    q = (j + pre + 0.5) / (pre + post)
    qc = pre / (pre + post)                                                       # the drop
    P = _pick(sa, f if j < 0 else sa["f1"] - 1)
    if P is None: P = np.zeros((H, W), np.float32)
    P = cv2.GaussianBlur(P, (0, 0), 6)
    r = np.sqrt(((_GX - W / 2) / (W * 0.55)) ** 2 + ((_GY - H * 0.42) / (H * 0.55)) ** 2)   # 0 at the middle, ~1.3 at the corners
    front = 1.45 - 1.25 * ein(smooth(q / (qc + 0.25)), 1.1)                       # the dark at the edges opens first, closing in
    mbg = np.clip((r - front) / 0.22, 0, 1); mbg = mbg * mbg * (3 - 2 * mbg)
    him = smooth((q - qc - 0.02) / 0.08)                                          # he goes last, in one quick switch on the drop
    m = mbg * (1 - P) + him * P
    m = np.maximum(m, smooth((q - qc - 0.10) / 0.12))
    ZB = 1 + 0.28 * (1 - smooth(q))
    Bz = _zoom_about(B, ZB, W / 2, H * 0.45, cv2.BORDER_REPLICATE)
    edge = np.exp(-((r - front) / 0.13) ** 2) * (1 - P) * (1 - smooth((q - qc) / 0.15))
    o = A * (1 - m[..., None]) + Bz * m[..., None] + edge[..., None] * RED111 * 0.16
    return np.clip(o, 0, 1)
TR2["passenger111"] = (passenger111, 18, 40)
RED111 = np.array([0.10, 0.13, 0.95], np.float32)

# ---- SLIDE (the slide at the window -> two slides): a glass slide is pushed in across the frame, the next shot on it.
def slide111(A, B, j, f, sa, sb, pre=4, post=6):
    q = (j + pre + 0.5) / (pre + post)
    x = W * (1 - ein(smooth(q), 0.8))
    m = np.clip((_GX - x) / 6.0 + 0.5, 0, 1)
    Bs = np.roll(B, int(x * 0.25), axis=1) if x > 2 else B
    o = A * (1 - m[..., None]) + Bs * m[..., None]
    edge = np.exp(-((_GX - x) / 10.0) ** 2) * (0.25 < q < 0.98)
    o = o + edge[..., None] * np.array([0.9, 0.9, 0.85], np.float32) * 0.35
    o = o * (1 - 0.12 * np.exp(-((_GX - x + 22) / 18.0) ** 2))[..., None]
    return np.clip(o, 0, 1)
TR2["slide111"] = (slide111, 4, 6)

# ---- THE SIREN (the red face -> the crime-scene tape, "now look who's in trouble"): a light bar's red sweeps the frame,
# then its blue, and the scene is behind the blue.
def siren111(A, B, j, f, sa, sb, pre=8, post=10):
    q = (j + pre + 0.5) / (pre + post)
    xr = -0.4 * W + 1.8 * W * smooth(q / 0.6)                                    # the red sweeps left -> right
    xb = 1.4 * W - 1.8 * W * smooth((q - 0.25) / 0.65)                           # the blue sweeps back, right -> left
    red = np.exp(-((_GX - xr) / 260.0) ** 2) * math.sin(math.pi * clamp(q / 0.6, 0, 1))
    blu = np.exp(-((_GX - xb) / 300.0) ** 2) * math.sin(math.pi * clamp((q - 0.25) / 0.65, 0, 1))
    behind = np.clip((xb - _GX) / -260.0 + 0.5, 0, 1); behind = behind * behind * (3 - 2 * behind)
    behind = np.maximum(behind, smooth((q - 0.88) / 0.12)) * smooth((q - 0.2) / 0.1)
    o = A * (1 - behind[..., None]) + B * behind[..., None]
    o = o * (1 + 0.6 * red[..., None] * np.array([0.1, 0.2, 1.0], np.float32)) + red[..., None] * np.array([0.05, 0.05, 0.75], np.float32) * 0.35
    o = o * (1 + 0.5 * blu[..., None] * np.array([1.0, 0.35, 0.1], np.float32)) + blu[..., None] * np.array([0.85, 0.25, 0.05], np.float32) * 0.30
    return np.clip(o, 0, 1)
TR2["siren111"] = (siren111, 8, 10)

# ---- CANOPY (the mangroves -> the bamboo): sun through the leaves: the dappled light drifts over the frame and the
# next shot is in the light; the spots grow until it is all light.
def canopy111(A, B, j, f, sa, sb, pre=8, post=10):
    q = (j + pre + 0.5) / (pre + post)
    n1 = nz108(1141, 5); n2 = nz108(1142, 11)
    sh = int(f * 4) % n1.shape[1]
    dap = cv2.resize(np.roll(n1, sh, axis=1) * 0.55 + np.roll(n2, -sh // 2, axis=0) * 0.45, (W, H), interpolation=cv2.INTER_LINEAR)
    thr = 0.80 - 0.95 * smooth(q)
    m = np.clip((dap - thr) / 0.16, 0, 1); m = m * m * (3 - 2 * m)
    m = np.maximum(m, smooth((q - 0.85) / 0.15))
    sun = np.clip((dap - thr + 0.12) / 0.20, 0, 1) * math.sin(math.pi * clamp(q, 0, 1))   # pools of sunlight, the next shot inside them
    o = A * (1 - m[..., None]) + B * m[..., None]
    o = o * (1 + 0.55 * sun[..., None]) + sun[..., None] * np.array([0.30, 0.62, 0.80], np.float32) * 0.22
    return np.clip(o, 0, 1)
TR2["canopy111"] = (canopy111, 8, 10)

# ---- THE SHOT (the loop): he raises the pistol at us and fires on "rumbles": the flash at the real muzzle (tracked), its
# light over him and the woods; the flash's light carries over the cut onto frame 0.
E_FIRE = 87.30                                                                     # on "rumbles": the flash floods, and frame 0 is inside its light by the last frame
MUZ_KEYS = [(372.45, 850.0, 1050.0), (372.70, 858.0, 520.0), (372.92, 860.0, 400.0), (373.17, 882.0, 405.0), (373.43, 885.0, 372.0)]   # (src t, x, y) output px
def _muz(s_, f):
    t, u, _ = src_time(s_, f)
    ks = MUZ_KEYS
    if t <= ks[0][0]: return ks[0][1], ks[0][2]
    for a, b in zip(ks, ks[1:]):
        if t <= b[0]:
            w = (t - a[0]) / (b[0] - a[0]); return a[1] + (b[1] - a[1]) * w, a[2] + (b[2] - a[2]) * w
    return ks[-1][1], ks[-1][2]

def _flash_star(mx, my, a, f):
    ang = np.arctan2(_GY - my, _GX - mx); d = np.sqrt((_GX - mx) ** 2 + (_GY - my) ** 2)
    ph = 0.6 + 0.08 * (f % 7)                                                     # a steady star (no per-frame flicker)
    petals = (0.55 + 0.45 * np.cos(5 * ang + ph)) ** 6
    core = np.exp(-(d / 34.0) ** 2)
    star = np.exp(-(d / (40 + 105 * petals)) ** 2) * (0.6 + 0.4 * petals)
    return np.clip(core * 1.2 + star * 0.9, 0, 1.5) * a

def shot111(out, f, s_):
    tf = E.th(E_FIRE); t = f / FPS
    if t < tf - 0.01: return out
    mx, my = _muz(s_, f); k = (t - tf) * FPS
    a = 1.0 if k < 2 else math.exp(-(k - 2) / 2.2)
    o = out.copy()
    d2 = (_GX - mx) ** 2 + (_GY - my) ** 2
    light = np.exp(-d2 / (2 * 520.0 ** 2)) * math.exp(-k / 5.0) * 0.75           # its light on him and the woods
    o = o * (1 + 0.8 * light[..., None]) + light[..., None] * np.array([0.42, 0.66, 0.95], np.float32) * 0.6
    st_ = _flash_star(mx, my, a, f)
    o = o + st_[..., None] * np.array([0.70, 0.90, 1.0], np.float32)
    if k > 3:                                                                     # smoke
        sm = cv2.resize(nz108(1151, 4), (W, H)); r = 40 + 18 * (k - 3)
        puff = np.exp(-d2 / (2 * r * r)) * np.clip((sm - 0.35) * 2.5, 0, 1) * 0.35 * math.exp(-(k - 3) / 12)
        o = o * (1 - puff[..., None]) + puff[..., None] * 0.55
    K = (E.DUR_F - 1) - tf * FPS
    w = (k - 0.5) / max(1.0, K - 0.5)                                            # the burst grows from the muzzle ...
    if w > 0:
        if "t0" not in _LV111: _LV111["t0"] = flash_in111(lightsout111(frame0_plate108().copy(), 0, SHOTS[0], _person(SHOTS[0], 0)), 0)
        R = 30 + (math.hypot(W, H) * 1.05) * ein(clamp(w, 0, 1), 1.6)             # ... and fills the frame exactly at the last frame
        d = np.sqrt(d2)
        m = np.clip((R - d) / (40 + 0.25 * R) + 0.5, 0, 1); m = m * m * (3 - 2 * m)
        if w >= 1: m = np.ones_like(m)
        rim = np.exp(-((d - R) / (40 + 0.18 * R)) ** 2) * (1 - smooth((w - 0.70) / 0.30)) * smooth((R - 60) / 120)
        o = o * (1 - m[..., None]) + _LV111["t0"] * m[..., None] + rim[..., None] * np.array([0.62, 0.84, 1.0], np.float32) * 0.45
    return np.clip(o, 0, 1)
_LV111 = {}


# ---- LOOK UP (the marina -> the moon): we tilt up off the city into the night sky (motion-blurred), and he is under it.
def lookup111(A, B, j, f, sa, sb, pre=14, post=18):
    q = (j + pre + 0.5) / (pre + post)
    u = smooth(q); sp = math.sin(math.pi * clamp(q, 0, 1)) ** 1.5
    dy = int(H * 0.85 * u)
    Ad = _vblur_shift(A, dy, 70 * sp); Bd = _vblur_shift(B, dy - int(H * 0.85), 70 * sp)
    w = smooth((q - 0.38) / 0.24)
    return np.clip(Ad * (1 - w) + Bd * w, 0, 1)
TR2["lookup111"] = (lookup111, 14, 18)

# ---- UNDERLIGHT (the gloves -> the scalpel over the light table): a light comes up from under the frame; the next shot
# is in it, lit from below.
def underlight111(A, B, j, f, sa, sb, pre=12, post=14):
    q = (j + pre + 0.5) / (pre + post)
    yf = H + 380 - (H + 760) * smooth(q)
    m = np.clip((_GY - yf) / 200.0 + 0.5, 0, 1); m = m * m * (3 - 2 * m)
    m = np.maximum(m, smooth((q - 0.9) / 0.1))
    glow = np.exp(-((_GY - yf) / 150.0) ** 2) * math.sin(math.pi * clamp(q, 0, 1))
    o = A * (1 - m[..., None]) + B * m[..., None] + glow[..., None] * np.array([0.85, 0.90, 0.92], np.float32) * 0.20
    return np.clip(o, 0, 1)
TR2["underlight111"] = (underlight111, 12, 14)

# ---- LIGHT MATCH (the scalpel -> the passenger): both are lit from below; the light table's glare becomes the light at
# his hands (the next shot opens aligned on its light, the glare flares across the cut and settles).
def _hot(img):
    Lq = cv2.GaussianBlur(lum(cv2.resize(img, (W // 8, H // 8))), (0, 0), 3)
    y, x = np.unravel_index(int(np.argmax(Lq)), Lq.shape); return x * 8.0 + 4, y * 8.0 + 4
_HOT = {}
def lightmatch111(A, B, j, f, sa, sb, pre=10, post=14):
    q = (j + pre + 0.5) / (pre + post)
    if sa["n"] not in _HOT: _HOT[sa["n"]] = _hot(A)
    if sb["n"] not in _HOT: _HOT[sb["n"]] = _hot(B)
    ax, ay = _HOT[sa["n"]]; bx, by = _HOT[sb["n"]]
    ua = smooth(q / 0.5); ub = 1 - smooth((q - 0.5) / 0.5)
    MA = np.float32([[1, 0, (bx - ax) * ua * 0.5], [0, 1, (by - ay) * ua * 0.5]])
    MB = np.float32([[1, 0, (ax - bx) * ub * 0.5], [0, 1, (ay - by) * ub * 0.5]])
    Am = cv2.warpAffine(A, MA, (W, H), borderMode=cv2.BORDER_REPLICATE); Bm = cv2.warpAffine(B, MB, (W, H), borderMode=cv2.BORDER_REPLICATE)
    w = smooth((q - 0.40) / 0.20)
    cx_, cy_ = (ax + (bx - ax) * q), (ay + (by - ay) * q)
    d = np.sqrt((_GX - cx_) ** 2 + (_GY - cy_) ** 2)
    fl = np.exp(-(d / 420.0) ** 2) * math.sin(math.pi * clamp(q, 0, 1)) ** 2 * 0.85
    o = Am * (1 - w) + Bm * w
    o = o * (1 + 0.6 * fl[..., None]) + fl[..., None] * np.array([0.92, 0.94, 0.95], np.float32) * 0.5
    return np.clip(o, 0, 1)
TR2["lightmatch111"] = (lightmatch111, 10, 14)


# ---- DOOR (the dark face -> behind the door with his reflection): we pan right past the door's edge, motion-blurred, and
# he is behind it.
def doorslide111(A, B, j, f, sa, sb, pre=12, post=14):
    q = (j + pre + 0.5) / (pre + post)
    u = smooth(q); sp = math.sin(math.pi * clamp(q, 0, 1)) ** 1.5
    dx = int(W * 0.9 * u)
    def hshift(img, x):
        Mx = np.float32([[1, 0, x], [0, 1, 0]])
        o_ = cv2.warpAffine(img, Mx, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        k_ = int(1 + 60 * sp) | 1
        return cv2.blur(o_, (k_, 1)) if k_ > 2 else o_
    Ad = hshift(A, -dx); Bd = hshift(B, int(W * 0.9) - dx)
    w = smooth((q - 0.40) / 0.20)
    return np.clip(Ad * (1 - w) + Bd * w, 0, 1)
TR2["doorslide111"] = (doorslide111, 12, 14)

# ---- the edges of the shots that carry a graphic (the next shot's transition sees the graphic, not the clean plate)
_edge108_pre111 = edge108
_B111 = {}
def edge108(S_, which):
    key = (S_["n"], which)
    if key not in _B111:
        if len(_B111) > 8: _B111.clear()
        img = _edge108_pre111(S_, which)
        fr = S_["f0"] if which == "first" else S_["f1"] - 1
        if S_["n"] in ("lights", "moon", "passenger"):
            img = graphic111(img.copy(), fr, S_, _person(S_, fr))
        _B111[key] = img
    return _B111[key]

def graphic111(out, f, s_, person):
    n = s_["n"]
    if n == "lights": out = lightsout111(out, f, s_, person)
    elif n == "moon": out = moon_draw111(out, f, s_, person)
    elif n == "passenger": out = shadow111(out, f, s_, person)
    return out

# ---- the beat camera (the owner's calmer drop): from the drop, half punch; rests under the shot
def beat_phase(f):
    e = f / FPS / E.HB; ph = (e % 2) * E.HB; bi = int(e // 2)
    hook = (65.4 <= e < 87.0)
    return ph, bi, hook, False

def beat_bounce(f):
    ph, bi, hook, rival = beat_phase(f)
    return 1 + 0.022 * math.exp(-ph / 0.10) if hook else 1.0

def shake(f):
    dx, dy, rot = _shake_v10(f)
    ph, bi, hook, rival = beat_phase(f)
    if hook: rot += (0.35 if bi % 2 else -0.35) * math.exp(-ph / 0.13)
    return dx, dy, rot

def beat_fx(out, f):
    ph, bi, hook, rival = beat_phase(f)
    if not hook or ph > 0.05: return out
    k = math.exp(-ph / 0.025)
    return np.clip(rgb_split(radial_blur(out, W / 2, H * 0.46, 1.0, 1.0 + 0.012 * k, 3), 2.5 * k), 0, 1)

def init_hits():
    HITS.clear()                                                                  # no impact shake (the owner's calmer drop)

def render(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin")
    out, person = base108(s, f)
    out = graphic111(out, f, s, person)
    if tin in TR2 and k < TR2[tin][2] and P is not None:
        out = TR2[tin][0](edge108(P, "last"), out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, edge108(n_, "first"), kn, f, s, n_)
    if s.get("tout") == "shot111": out = shot111(out, f, s)
    out = flash_in111(out, f)
    out = beat_fx(out, f)
    out = flash_governor(out)
    sf = SHOTS[0] if (s.get("tout") == "shot111" and f >= E.fh(E_FIRE) + 6) else s
    return (np.clip(finish111(out, f, sf), 0, 1) * 255 + 0.5).astype(np.uint8)

# ============================================================================ v111 rev 1 (the owner's notes)
# "I dislike the graphic/animation that appeared around the 23 second mark, the forensics one" (the luminol -> BLEED: the
# slide's own blood soaks out through the frame into the blood room); "implement a new more creative loop" (THE TRACER: he
# fires, we whip after the bullet's tracer through the night, and it lands in the marina's skyline as the light that
# blows on "shoot": the end fires the shot that starts it); "more custom graphics and animations" (sparks and glass from
# every light that blows; god rays from the sunrise; dust in the kill lamp's beam; the light bar's red and blue over the
# crime scene).

TGT_GUESS = (830.0, 250.0)
def _lo_map(s_):
    """per light (1/4 res): the time it dies; the lights list (t, x, y, area, seed) in output px; the tracer's target."""
    if "map" not in _LO:
        f0 = s_["f0"] + 4; img = base108(s_, f0)[0]; P = _pick(s_, f0)
        m = _lights_mask(img, P, 0.34, 0.20)
        lab = (m > 0.30).astype(np.uint8); n, cc = cv2.connectedComponents(lab)
        ys, xs = np.mgrid[0:H // 4, 0:W // 4]
        tmap_ = np.full(cc.shape, np.inf, np.float32)
        comps = [(i, float(xs[cc == i].mean()) * 4 + 2, float(ys[cc == i].mean()) * 4 + 2, int((cc == i).sum())) for i in range(1, n) if (cc == i).sum() >= 2]
        tg = min(comps, key=lambda c: (c[1] - TGT_GUESS[0]) ** 2 + (c[2] - TGT_GUESS[1]) ** 2 - 400 * min(c[3], 12))
        rest = sorted([c for c in comps if c is not tg], key=lambda c: -abs(c[1] - W / 2))   # the outermost first
        order = [tg] + rest
        rng = np.random.default_rng(1101)
        early = {0: E.th(1.4), 1: E.th(2.6), 2: E.th(3.4), 3: E.th(4.6), 4: E.th(5.4)}   # a light blows on each beat of "shoot"
        lights = []
        for r_, (i, cx, cy, ar) in enumerate(order):
            u = r_ / max(1, len(order) - 1)
            td = early.get(r_, T_WAVE[0] + (T_WAVE[1] - T_WAVE[0]) * clamp(u + rng.uniform(-0.08, 0.08), 0, 1))
            tmap_[cc == i] = td; lights.append((td, cx, cy, ar, 1170 + r_))
        grow = cv2.erode(tmap_, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
        _LO["map"] = (grow, len(order)); _LO["lights"] = lights; _LO["tgt"] = (tg[1], tg[2])
    return _LO["map"]

def _splat(lay, xs, ys, cols, r=1):
    for x, y, c in zip(xs, ys, cols):
        if 0 <= x < lay.shape[1] and 0 <= y < lay.shape[0]: cv2.circle(lay, (int(x), int(y)), r, tuple(float(v) for v in c), -1, cv2.LINE_AA)

def _sparks111(o, f, s_):
    """each light that blows throws sparks and glass: they fly up and out and fall."""
    t = f / FPS; M = _follow(s_, s_["f0"] + 4, f)
    lay = np.zeros((H // 2, W // 2, 3), np.float32); any_ = False
    for (td, cx, cy, ar, seed) in _LO.get("lights", [])[:40]:
        dt = t - td
        if dt < 0 or dt > 0.75: continue
        any_ = True; rng = np.random.default_rng(seed); n = 9 + min(14, ar)
        ang = rng.uniform(-math.pi * 0.95, -math.pi * 0.05, n); spd = rng.uniform(160, 560, n)
        life = rng.uniform(0.30, 0.75, n)
        for tt, br in ((dt, 1.0), (max(0.0, dt - 0.02), 0.45)):                    # the spark and its streak
            x = cx + np.cos(ang) * spd * tt; y = cy + np.sin(ang) * spd * tt + 0.5 * 1500 * tt * tt
            X = (M[0, 0] * x + M[0, 2]) / 2; Y = (M[1, 1] * y + M[1, 2]) / 2
            fade = np.clip(1 - tt / life, 0, 1) ** 1.3 * br
            cols = [np.array([0.55, 0.85, 1.0], np.float32) * a for a in fade]
            _splat(lay, X[fade > 0], Y[fade > 0], [c for c, a in zip(cols, fade) if a > 0])
    if not any_: return o
    lay = lay + cv2.GaussianBlur(lay, (0, 0), 2.5) * 1.6
    return np.clip(o + cv2.resize(lay, (W, H), interpolation=cv2.INTER_LINEAR), 0, 1)

_lightsout_r0 = lightsout111
def lightsout111(out, f, s_, person):
    return _sparks111(_lightsout_r0(out, f, s_, person), f, s_)

# the shot lands on frame 0 as the light it hits: that light flares, and blows on "shoot"
def flash_in111(out, f):
    if f > 26 or "tgt" not in _LO: return out
    tx, ty = _LO["tgt"]; a = 0.95 * math.exp(-f / 6.0)
    d2 = (_GX - tx) ** 2 + (_GY - ty) ** 2
    glow = np.exp(-d2 / (2 * 150.0 ** 2)) * a + np.exp(-d2 / (2 * 38.0 ** 2)) * a * 1.4
    return np.clip(out + glow[..., None] * np.array([0.55, 0.80, 1.0], np.float32), 0, 1)

# ---- THE TRACER (the loop): he fires; we whip after the bullet's tracer through the night, and the whip lands on the
# marina at frame 0, the tracer going into the light it will put out.
def _seg_glow(ax, ay, bx, by, w0, w1):
    vx, vy = bx - ax, by - ay; L2 = vx * vx + vy * vy + 1e-6
    u = np.clip(((_GX - ax) * vx + (_GY - ay) * vy) / L2, 0, 1)
    d2 = (_GX - (ax + u * vx)) ** 2 + (_GY - (ay + u * vy)) ** 2
    wd = w0 + (w1 - w0) * u
    return np.exp(-d2 / (2 * wd * wd)) * (0.25 + 0.75 * u)

def _hblur_shift(img, x, k_):
    Mx = np.float32([[1, 0, x], [0, 1, 0]])
    o_ = cv2.warpAffine(img, Mx, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return cv2.blur(o_, (k_, 1)) if k_ > 2 else o_

def shot111(out, f, s_):
    tf = E.th(E_FIRE); t = f / FPS
    if t < tf - 0.01: return out
    mx, my = _muz(s_, f); k = (t - tf) * FPS
    a = 1.0 if k < 2 else math.exp(-(k - 2) / 2.2)
    o = out.copy()
    d2 = (_GX - mx) ** 2 + (_GY - my) ** 2
    light = np.exp(-d2 / (2 * 520.0 ** 2)) * math.exp(-k / 5.0) * 0.75
    o = o * (1 + 0.8 * light[..., None]) + light[..., None] * np.array([0.42, 0.66, 0.95], np.float32) * 0.6
    o = o + _flash_star(mx, my, a, f)[..., None] * np.array([0.70, 0.90, 1.0], np.float32)
    K = (E.DUR_F - 1) - tf * FPS
    u = clamp((k - 1.0) / max(1.0, K - 1.0), 0, 1)
    if u <= 0: return np.clip(o, 0, 1)
    if "t0" not in _LV111:
        _lo_map(SHOTS[0])
        _LV111["t0"] = flash_in111(lightsout111(frame0_plate108().copy(), 0, SHOTS[0], _person(SHOTS[0], 0)), 0)
    tx, ty = _LO["tgt"]
    e = smooth(u); sp = math.sin(math.pi * u) ** 1.2
    dx = W * 1.15 * e; kb = int(1 + 90 * sp) | 1
    Ad = _hblur_shift(o, -dx, kb); Bd = _hblur_shift(_LV111["t0"], W * 1.15 - dx, kb)
    w = smooth((u - 0.40) / 0.18)
    o = Ad * (1 - w) + Bd * w
    hx = mx + (tx - mx) * ein(u, 1.3) + 40 * math.sin(math.pi * u)                # the tracer: the camera chases it (up the right, clear of him)
    hy = my + (ty - my) * ein(u, 1.3) - 230 * math.sin(math.pi * u)
    tail = 50 + 380 * sp
    vis = (1 - smooth((u - 0.82) / 0.18)) * smooth(u / 0.08)
    if vis > 0:
        g = _seg_glow(hx + 0.35 * tail, hy + 0.95 * tail, hx, hy, 3.0 + 8 * sp, 7.0)
        core = np.exp(-((_GX - hx) ** 2 + (_GY - hy) ** 2) / (2 * 14.0 ** 2))
        halo = cv2.GaussianBlur(g, (0, 0), 9)
        o = o + ((g * 1.1 + core * 1.3) * vis)[..., None] * np.array([0.70, 0.90, 1.0], np.float32) + (halo * 0.6 * vis)[..., None] * np.array([0.30, 0.62, 1.0], np.float32)
    return np.clip(o, 0, 1)
_LV111 = {}

# ---- BLEED (the slides -> the blood room; replaces the luminol): the blood spot on his slide soaks out through the frame
# like blood through paper, its wet edge darker, and the blood room is inside it.
_BLD = {}
def bleed111(A, B, j, f, sa, sb, pre=6, post=14):
    q = (j + pre + 0.5) / (pre + post)
    if sa["n"] not in _BLD:
        q4 = cv2.resize(A, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
        red = cv2.GaussianBlur(q4[..., 2] - 0.5 * (q4[..., 0] + q4[..., 1]), (0, 0), 4)
        y, x = np.unravel_index(int(np.argmax(red)), red.shape); _BLD[sa["n"]] = (x * 4.0 + 2, y * 4.0 + 2)
    bx, by = _BLD[sa["n"]]
    R = 15 + 2100 * ein(smooth(q), 1.6)
    nz = cv2.resize(nz108(1161, 3), (W, H)) * 0.65 + cv2.resize(nz108(1162, 9), (W, H)) * 0.35
    d = np.sqrt((_GX - bx) ** 2 + (_GY - by) ** 2) * (0.70 + 0.60 * nz)
    m = np.clip((R - d) / (40 + 0.12 * R) + 0.5, 0, 1); m = m * m * (3 - 2 * m)
    m = np.maximum(m, smooth((q - 0.88) / 0.12))
    band = np.exp(-((d - R) / (30 + 0.10 * R)) ** 2) * (1 - smooth((q - 0.65) / 0.35))
    fs = face_scr(sa, sa["f1"] - 1)
    if fs is not None:                                                            # the wet front never stains his face
        band = band * np.clip((((_GX - fs[0]) / (0.70 * fs[2])) ** 2 + ((_GY - fs[1]) / (0.90 * fs[2])) ** 2) - 0.7, 0, 1)
    BLOOD = np.array([0.04, 0.03, 0.42], np.float32)
    Bt = B * (1 - 0.55 * band[..., None]) + BLOOD * 0.55 * band[..., None]
    o = A * (1 - m[..., None]) + Bt * m[..., None]
    o = o * (1 - 0.35 * (band * (1 - m))[..., None]) + (BLOOD * 0.8) * (0.35 * band * (1 - m))[..., None]   # the wet front ahead of it
    return np.clip(o, 0, 1)
TR2["bleed111"] = (bleed111, 6, 14)

# ---- GOD RAYS (the sunrise): the low sun throws rays through the haze, slowly turning.
_RAYC = {}
def rays111(o, f, s_):
    k = f - s_["f0"]; n = s_["f1"] - s_["f0"]
    env = smooth(k / 8.0) * (1 - smooth((k - (n - 8)) / 8.0))
    if env <= 0: return o
    if "sun" not in _RAYC:
        Lq = cv2.GaussianBlur(lum(cv2.resize(base108(s_, s_["f0"])[0], (W // 8, H // 8))), (0, 0), 3)
        y, x = np.unravel_index(int(np.argmax(Lq)), Lq.shape); _RAYC["sun"] = (x * 8.0 + 4, y * 8.0 + 4)
    sx, sy = _RAYC["sun"]
    ang = np.arctan2(_GY - sy, _GX - sx); d = np.sqrt((_GX - sx) ** 2 + (_GY - sy) ** 2)
    rot = 0.25 * (f / FPS)
    r = (0.5 + 0.5 * np.cos(11 * ang + rot)) ** 6 * 0.6 + (0.5 + 0.5 * np.cos(17 * ang - 1.3 * rot + 1.1)) ** 8 * 0.4
    L = cv2.resize(cv2.GaussianBlur(lum(cv2.resize(o, (W // 4, H // 4))), (0, 0), 3), (W, H))
    wgt = np.clip((L - 0.30) / 0.45, 0, 1) * np.exp(-d / 1400.0) * env
    return np.clip(o + (r * wgt * 0.30)[..., None] * np.array([0.45, 0.78, 1.0], np.float32), 0, 1)

# ---- DUST (the lamp and the table): motes drifting in the kill lamp's light (seen only in the lit air, never on his face).
def motes111(o, f, s_):
    k = f - s_["f0"]; n = s_["f1"] - s_["f0"]
    env = smooth(k / 6.0) * (1 - smooth((k - (n - 6)) / 6.0))
    if env <= 0: return o
    rng = np.random.default_rng(1180 + (7 if s_["n"] == "table" else 0)); N = 230
    x0 = rng.uniform(0, W, N); y0 = rng.uniform(0, H * 0.75, N); ph = rng.uniform(0, 6.28, N); sz = rng.uniform(0.5, 1.0, N)
    t = f / FPS
    X = (x0 + 26 * np.sin(t * 0.9 + ph) + 14 * t) % W; Y = (y0 + 18 * np.cos(t * 0.7 + ph * 1.3) + 22 * t) % H
    L = cv2.resize(cv2.GaussianBlur(lum(cv2.resize(o, (W // 4, H // 4))), (0, 0), 4), (W // 4, H // 4))
    lit = np.clip((L[(Y / 4).astype(int).clip(0, H // 4 - 1), (X / 4).astype(int).clip(0, W // 4 - 1)] - 0.32) / 0.35, 0, 1)
    fs = face_scr(s_, f)
    if fs is not None:
        lit = lit * np.clip((((X - fs[0]) / (0.75 * fs[2])) ** 2 + ((Y - fs[1]) / (0.95 * fs[2])) ** 2) - 0.8, 0, 1)
    lay = np.zeros((H // 2, W // 2, 3), np.float32)
    tw = 0.6 + 0.4 * np.sin(t * 6 + ph * 3)
    _splat(lay, X / 2, Y / 2, [np.array([0.70, 0.86, 0.95], np.float32) * a for a in (lit * sz * tw * env * 1.5)])
    lay = lay + cv2.GaussianBlur(lay, (0, 0), 2.0)
    return np.clip(o + cv2.resize(lay, (W, H), interpolation=cv2.INTER_LINEAR), 0, 1)

# ---- THE LIGHT BAR (the crime-scene tape, "now look who's in trouble"): after the siren's sweep its red and blue keep
# washing over the scene on the half-beats, from the cruiser's side.
def lightbar111(o, f, s_):
    k = f - s_["f0"]; n = s_["f1"] - s_["f0"]
    if k < 8: return o
    env = smooth((k - 8) / 4.0) * (1 - smooth((k - (n - 6)) / 6.0))
    e = f / FPS / (E.HB / 2); ph = e % 1.0; side = int(e) % 2
    a = math.exp(-ph / 0.45) * env
    g = np.clip((_GX / W) if side else (1 - _GX / W), 0, 1) ** 1.5
    col = np.array([0.95, 0.30, 0.08], np.float32) if side else np.array([0.08, 0.10, 0.95], np.float32)
    return np.clip(o * (1 + 0.60 * (g * a)[..., None] * col) + (g * a * 0.30)[..., None] * col, 0, 1)

_graphic_r0 = graphic111
def graphic111(out, f, s_, person):
    out = _graphic_r0(out, f, s_, person)
    n = s_["n"]
    if n == "sunrise": out = rays111(out, f, s_)
    elif n in ("lamp", "table"): out = motes111(out, f, s_)
    elif n == "tape": out = lightbar111(out, f, s_)
    return out
