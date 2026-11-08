# ============================================================================ v107 ALL CAPS (Dexter x Madvillain "All Caps")
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
        a = math.radians(ang); u = (_GX * math.cos(a) + _GY * math.sin(a)) / pitch; v = (-_GX * math.sin(a) + _GY * math.cos(a)) / pitch
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

def text107(out, f, s, rides):
    for tx in E.TEXT:
        if bool(tx.get("rides")) != rides: continue
        if tx["style"] == "cap": out = text_cap(out, f, tx, None)
        elif tx["style"] == "stamp": out = text_stamp(out, f, tx)
    return out

# ---- the frame ----------------------------------------------------------------------------------------------------
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
