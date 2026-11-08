# ============================================================================ v101 — THE LESS YOU KNOW: 16 mm psychedelic toolkit
# (spliced into render101.py before main(); the last definitions win, so this section owns grade, finish, text and render)
OXB = np.array([0.10, 0.07, 0.66], np.float32)      # oxblood (BGR)
AMBER = np.array([0.16, 0.60, 1.00], np.float32)
PLUMC = np.array([0.40, 0.09, 0.34], np.float32)
CREAMC = np.array([0.80, 0.92, 1.00], np.float32)
HOTW = np.array([0.70, 0.95, 1.00], np.float32)     # overheated film: yellow-white
CHAR = np.array([0.025, 0.035, 0.06], np.float32)
LQ_COLS = np.array([[0.10, 0.07, 0.70], [0.14, 0.58, 1.00], [0.42, 0.10, 0.38], [0.16, 0.28, 0.98],
                    [0.55, 0.38, 0.92], [0.08, 0.82, 1.00], [0.22, 0.04, 0.22]], np.float32)

F_FR = f"{E.FONTS}/Fraunces_var.ttf"
_FRF = {}
def fr_font(size, wght=900, soft=100, wonk=1, opsz=144):
    k = (size, wght, soft, wonk, opsz)
    if k not in _FRF:
        fo = ImageFont.truetype(F_FR, size); fo.set_variation_by_axes([opsz, wght, soft, wonk]); _FRF[k] = fo
    return _FRF[k]

def fr_mask(text, size, wght=900, soft=100, wonk=1):
    fo = fr_font(size, wght, soft, wonk)
    wdt = int(fo.getlength(text) + 100); hgt = int(size * 1.6 + 40)
    im = Image.new("L", (wdt, hgt), 0); ImageDraw.Draw(im).text((40, 16), text, font=fo, fill=255)
    m = np.asarray(im).astype(np.float32) / 255; ys, xs = np.nonzero(m > 0.02)
    return m[max(0, ys.min() - 4):ys.max() + 5, max(0, xs.min() - 4):xs.max() + 5]

# ---------------------------------------------------------------------------- grade: psych 16 mm
_LUTP = None
def lut_psych():
    global _LUTP
    if _LUTP is None:
        x = np.linspace(0, 1, 1024, dtype=np.float32)
        y = PchipInterpolator([0, .06, .2, .5, .8, .95, 1], [0.0, 0.05, 0.18, 0.50, 0.815, 0.93, 0.965])(x)
        _LUTP = (x, y.astype(np.float32))
    return _LUTP

def grade(img, s, f):
    g, gains = correction(s)
    x = np.clip(img * gains, 0, 1) ** g
    lx, ly = lut_psych(); x = np.interp(x, lx, ly).astype(np.float32)
    B_, G_, R_ = x[..., 0], x[..., 1], x[..., 2]
    red = np.clip((R_ - np.maximum(G_, B_)) * 3.0, 0, 1)[..., None]
    grn = np.clip((G_ - np.maximum(R_, B_)) * 4.0, 0, 1)[..., None]            # foliage -> olive / amber (70s stock)
    x = x + grn * np.array([-0.05, -0.025, 0.06], np.float32)
    L = (x[..., 0] * 0.114 + x[..., 1] * 0.587 + x[..., 2] * 0.299)[..., None]
    sat = 0.94 + 0.34 * red
    x = L + (x - L) * sat
    x = x + (1 - L) ** 2.6 * np.array([0.034, -0.006, 0.026], np.float32)      # plum shadows
    x = x + L ** 1.7 * np.array([-0.045, 0.006, 0.042], np.float32)            # amber / peach highlights
    x = x * 0.965 + np.array([0.022, 0.012, 0.020], np.float32)                 # lifted, plum-tinted film black
    if s.get("warm"): x = x + s["warm"] * np.array([-0.05, -0.005, 0.045], np.float32) * (0.4 + 0.6 * L)   # pull cold shots into the warm stock
    return np.clip(x, 0, 1)

def beat_bounce(f): return 1.0

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
    target = s.get("target", 0.45)
    g = clamp(math.log(target) / math.log(clamp(face, 0.02, 0.97)), 0.70, 1.30)
    m = img.reshape(-1, 3).mean(0); gains = np.clip((m.mean() / (m + 1e-6)) ** 0.10, 0.92, 1.08)
    CORR[s["n"]] = (g, gains.astype(np.float32)); return CORR[s["n"]]

# ---------------------------------------------------------------------------- liquid light (oil wheel)
_LQS = {}
def liquid(f, w=180, h=320, seed=0, speed=1.0, n=7):
    """oil-wheel liquid light: colour cells with dark oily walls that drift, swirl and morph.
    returns (col hxwx3, wall hxw, idx hxw, inten hxw) at w x h."""
    key = (seed, w, h, n)
    if key not in _LQS:
        rng = np.random.default_rng(seed)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        _LQS[key] = dict(c=rng.uniform(0.15, 0.85, (n, 2)), a=rng.uniform(0.10, 0.30, (n, 2)), fr=rng.uniform(0.25, 0.7, (n, 2)),
                         ph=rng.uniform(0, 6.28, (n, 2)), r=rng.uniform(0.16, 0.30, n), col=LQ_COLS[rng.permutation(len(LQ_COLS))[:n]],
                         nz=[_lowfreq((h, w), (4, 3), seed + 11 + i) - 0.5 for i in range(2)], xx=xx / h, yy=yy / h)
    P = _LQS[key]; t = f / FPS * speed
    # swirl: rotate the domain slowly about the centre + warp by drifting noise
    cx_, cy_ = 0.5 * w / h, 0.5; ang = 0.35 * t
    xr = P["xx"] - cx_; yr = P["yy"] - cy_; rr = np.sqrt(xr * xr + yr * yr)
    a2 = ang + 0.9 * np.exp(-rr * 2.5) * math.sin(0.6 * t)
    xs = cx_ + xr * math.cos(a2.mean()) - yr * math.sin(a2.mean()) + P["nz"][0] * 0.18 * math.sin(0.8 * t + 1)
    ys = cy_ + xr * math.sin(a2.mean()) + yr * math.cos(a2.mean()) + P["nz"][1] * 0.18 * math.cos(0.7 * t)
    F = np.empty((n, h, w), np.float32)
    for i in range(n):
        cx = (P["c"][i, 0] + P["a"][i, 0] * math.sin(P["fr"][i, 0] * t + P["ph"][i, 0])) * w / h
        cy = P["c"][i, 1] + P["a"][i, 1] * math.sin(P["fr"][i, 1] * t + P["ph"][i, 1])
        r = P["r"][i] * (1 + 0.2 * math.sin(0.9 * t + i))
        F[i] = r * r / ((xs - cx) ** 2 + (ys - cy) ** 2 + 1e-3)
    top2 = np.partition(F, n - 2, axis=0)[n - 2:]
    f2, f1 = top2[0], top2[1]
    wall = np.clip((f2 / (f1 + 1e-6) - 0.70) / 0.30, 0, 1) ** 2
    wgt = F ** 3; wgt /= wgt.sum(0, keepdims=True) + 1e-9
    col = np.tensordot(wgt.transpose(1, 2, 0), P["col"], axes=([2], [0])).astype(np.float32)
    idx = np.argmax(F, 0).astype(np.float32) / max(1, n - 1)
    inten = np.clip(f1 * 1.2, 0, 1.4)
    return col, wall, idx, inten

def liquid_full(f, seed=0, speed=1.0):
    col, wall, idx, inten = liquid(f, seed=seed, speed=speed)
    col = cv2.resize(col, (W, H), interpolation=cv2.INTER_CUBIC); wall = cv2.resize(wall, (W, H), interpolation=cv2.INTER_CUBIC)
    return np.clip(col, 0, 1), np.clip(wall, 0, 1)

def liquid_projection(out, person, f, s):
    """the light show is projected onto the background behind him (person matte), building to the drop."""
    u = (f - s["f0"]) / max(1, s["f1"] - s["f0"]); amt = s.get("liquid", 1.0)
    a = (0.35 + 0.60 * smooth(u)) * (amt if not isinstance(amt, bool) else 1.0)
    ff = f + 40 * u * u                                                                   # the show speeds up toward the drop
    col, wall = liquid_full(int(ff), seed=3 if s["n"] == "confess" else 5, speed=0.9 + 0.8 * u)
    col = col * np.array([0.90, 0.62, 1.00], np.float32)
    light = col * (1 - 0.75 * wall[..., None])
    bg = (1 - person)[..., None] * a
    lit = out * (0.30 + 0.95 * light)
    lit = lit / (1 + 0.35 * lit)  * 1.25
    out = out * (1 - bg) + lit * bg
    rim = np.clip(cv2.GaussianBlur(person, (0, 0), 6) - person * 0.85, 0, 1)[..., None]
    return np.clip(out + rim * light * 0.35 * a, 0, 1)

def prism_echo(out, person, f, s):
    """on the bass notes the title lands on, stepped prism silhouettes (amber / oxblood / plum) kick out behind him,
    offset down-right like the title's shadow stack, and spring back into him."""
    t = f / FPS; e = 0.0
    for ta in E.ACCENTS[:4]:
        if ta <= t: e = max(e, math.exp(-(t - ta) / 0.22))
    if e < 0.04: return out
    acc = out.copy(); hold = person.copy(); pm = person[..., None]
    for i, col in ((3, PLUMC), (2, OXB), (1, AMBER)):
        dx, dy = 15 * i * e, 17 * i * e
        m = cv2.warpAffine(person, np.float32([[1, 0, dx], [0, 1, dy]]), (W, H), borderValue=0)
        m = np.clip(m - person, 0, 1)[..., None] * (0.80 * e)
        acc = acc * (1 - m) + (col * 0.9 + acc * 0.1) * m
    return np.clip(acc * (1 - pm) + out * pm, 0, 1)

# ---------------------------------------------------------------------------- film finish
_FG = None
def film_grain(f):
    global _FG
    if _FG is None:
        rng = np.random.default_rng(17); _FG = []
        for _ in range(8):
            a = cv2.resize(rng.standard_normal((H // 2, W // 2, 3)).astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
            b = cv2.resize(rng.standard_normal((H // 5, W // 5)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
            _FG.append((a * 0.8 + b[..., None] * 0.55).astype(np.float32))
    return _FG[f % 8]

def weave(f):
    return (1.1 * math.sin(f * 0.37) + 0.7 * math.sin(f * 1.31 + 1.0), 0.9 * math.sin(f * 0.23 + 2.0) + 0.5 * math.sin(f * 0.97))

def dust(out, f):
    rng = np.random.default_rng(1000 + f)
    if rng.random() < 0.55:
        for _ in range(int(rng.integers(1, 4))):
            x, y = int(rng.uniform(40, W - 40)), int(rng.uniform(60, H - 60)); r = int(rng.uniform(1, 4))
            c = (0.03, 0.03, 0.04) if rng.random() < 0.7 else (0.95, 0.95, 0.9)
            cv2.circle(out, (x, y), r, c, -1, cv2.LINE_AA)
    if rng.random() < 0.06:                                                             # a hair in the gate
        x0, y0 = rng.uniform(0, W), rng.uniform(0, H); pts = []
        for k in range(12):
            pts.append((int(x0 + 60 * math.sin(k * 0.5 + x0) + k * 9), int(y0 + k * 14)))
        cv2.polylines(out, [np.int32(pts)], False, (0.05, 0.04, 0.05), 1, cv2.LINE_AA)
    return out

def finish_film(out, f):
    out = out + 0.32 * (out - cv2.GaussianBlur(out, (0, 0), 1.6))                      # gentle unsharp: 720p sources are upscaled 2.7x
    dx, dy = weave(f)
    if f < 40 or abs(dx) + abs(dy) > 0.2:
        M = np.float32([[1, 0, dx], [0, 1, dy]]); out = cv2.warpAffine(out, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    L = lum(out); hi = np.clip(L - 0.60, 0, 1)
    small = cv2.resize(hi, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    halo = cv2.resize(cv2.GaussianBlur(small, (0, 0), 7), (W, H))[..., None]
    out = out + halo * (OXB * 0.40 + AMBER * 0.20)                                      # red-orange halation
    out = bloom(out, 0.14)
    flick = 1 + 0.012 * math.sin(f * 2.7) * math.sin(f * 0.61 + 0.3)
    out = out * flick
    L = lum(out)[..., None]
    out = out + film_grain(f) * (0.016 + 0.030 * L * (1 - L) * 2.2)
    out = dust(out, f)
    return np.clip(out * VIG, 0, 1)

def light_leaks(out, f):
    """a warm film light leak licks in from a frame edge on the bar downbeats of the montage."""
    t = f / FPS; h = t / E.HB + E.H0
    if not (E.HDROP + 8 <= h < E.H_BREAK): return out
    hb = E.HDROP + 8 * int((h - E.HDROP) // 8); k = f - E.fh(hb)
    if k > 18 or k < 0: return out
    rng = np.random.default_rng(hb); side = int(hb // 8) % 2
    yy = np.linspace(0, 1, H // 8)[:, None]; xx = np.linspace(0, 1, W // 8)[None, :]
    xe = xx if side == 0 else 1 - xx; cy = rng.uniform(0.25, 0.75)
    m = np.exp(-xe / 0.22) * np.exp(-((yy - cy) / 0.35) ** 2)
    m = cv2.resize(m.astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)[..., None]
    a = (0.55 if k < 3 else 0.55 * math.exp(-(k - 3) / 5.0))
    col = AMBER * 0.75 + OXB * 0.35
    return np.clip(1 - (1 - out) * (1 - m * col * a), 0, 1)

# ---------------------------------------------------------------------------- text
_TWD = {}
def word_rgba(word, style, emph, f=0):
    key = (word, style, emph)
    if key not in _TWD:
        if style == "cap":
            m = fr_mask(word, 84, wght=800, soft=100, wonk=0)
            pad = 30; mm = np.pad(m, pad); hh, ww = mm.shape; L = np.zeros((hh, ww, 4), np.float32)
            if emph:
                g = np.linspace(0, 1, hh)[:, None, None]; col = AMBER * (1 - g) + OXB * 1.15 * g
            else:
                col = CREAMC
            sh = np.roll(np.roll(mm, 6, 0), 5, 1)
            L[..., :3] = PLUMC * 0.35 * sh[..., None]; L[..., 3] = sh * 0.9
            L[..., :3] = L[..., :3] * (1 - mm[..., None]) + col * mm[..., None]; L[..., 3] = np.maximum(L[..., 3], mm)
            soft = cv2.GaussianBlur(mm, (0, 0), 10) * 0.65; L[..., 3] = np.maximum(L[..., 3], soft)
        else:                                                                           # title: 70s layered shadow stack
            size = 172 if style == "title" else 160
            m = fr_mask(word, size, wght=900, soft=100, wonk=1)
            pad = 44; mm = np.pad(m, pad); hh, ww = mm.shape
            L = np.zeros((hh, ww, 4), np.float32)
            for i, col in ((3, PLUMC * 0.8), (2, OXB), (1, AMBER)):                       # offset stack, back to front
                sh = np.roll(np.roll(mm, 8 * i, 0), 7 * i, 1)
                L[..., :3] = L[..., :3] * (1 - sh[..., None]) + col * sh[..., None]; L[..., 3] = np.maximum(L[..., 3], sh)
            edge = cv2.dilate(mm, np.ones((7, 7), np.uint8)) - mm
            L[..., :3] = L[..., :3] * (1 - edge[..., None]) + PLUMC * 0.25 * edge[..., None]
            L[..., 3] = np.maximum(L[..., 3], cv2.GaussianBlur(mm, (0, 0), 16) * 0.6)
            L = np.dstack([L, mm])                                                      # 5th channel: the face of the letters
        _TWD[key] = L
    return _TWD[key]

def title_face(L, f, seed):
    """fill the letter faces with flowing liquid light (cream highlights so it stays readable)."""
    hh, ww = L.shape[:2]; mm = L[..., 4]
    col, wall, _, _ = liquid(f, w=max(32, ww // 6), h=max(32, hh // 6), seed=seed, speed=1.6, n=5)
    col = cv2.resize(col, (ww, hh), interpolation=cv2.INTER_CUBIC); wall = cv2.resize(wall, (ww, hh), interpolation=cv2.INTER_CUBIC)
    g = np.linspace(0, 1, hh, dtype=np.float32)[:, None, None]
    face = np.clip(CREAMC * (0.80 - 0.35 * g) + col * (0.35 + 0.35 * g) - wall[..., None] * 0.10, 0, 1)
    hl = np.clip(np.roll(mm, 3, 0) - mm, 0, 1)[..., None]                               # top-edge highlight bevel
    face = np.clip(face * (1 - hl) + hl * 0.25 + face * 0, 0, 1)
    o = L[..., :4].copy(); a = mm[..., None]
    o[..., :3] = o[..., :3] * (1 - a) + face * a
    hi = np.clip(mm - np.roll(mm, -4, 0), 0, 1)[..., None]
    o[..., :3] = np.clip(o[..., :3] + hi * CREAMC * 0.35, 0, 1)
    return o

def put(out, rgba_, cx, cy, a, sx=1.0, sy=1.0, blur=0.0):
    im = rgba_
    if abs(sx - 1) > 0.01 or abs(sy - 1) > 0.01:
        im = cv2.resize(im, (max(2, int(im.shape[1] * sx)), max(2, int(im.shape[0] * sy))), interpolation=cv2.INTER_LINEAR)
    if blur > 0.3: im = cv2.GaussianBlur(im, (0, 0), blur)
    return paste(out, im, int(cx - im.shape[1] / 2), int(cy - im.shape[0] / 2), a)

def lay_caps(out, f, tx):
    t = f / FPS; ws = tx["words"]; lines = sorted({l for _, _, l in ws})
    fade = 1.0 if t < tx["end"] - 0.12 or tx.get("burn") else clamp(1 - (t - (tx["end"] - 0.12)) * FPS / 9, 0, 1)
    for ln in lines:
        row = [(w, wt) for w, wt, l in ws if l == ln]; imgs = [word_rgba(w, "cap", w in tx["emph"]) for w, _ in row]
        sp = -34; vs = [eout(((t - wt) * FPS + 1) / 12, 3) for _, wt in row]
        fit = min(1.0, (W - 150) / (sum(im.shape[1] + sp for im in imgs) - sp))
        widths = [(im.shape[1] + sp) * fit for im in imgs]; total = sum(widths) - sp * fit
        x = W / 2 - total / 2; y = E.CAP_Y[ln]
        for im, v, wd in zip(imgs, vs, widths):
            if v > 0.002:
                sc = (1.10 - 0.10 * v) * fit
                out = put(out, im, x + im.shape[1] * fit / 2, y + 30 * (1 - v), v * fade, sc, sc, 6 * (1 - v))
            x += wd
    return out

def lay_title(out, f, tx, rows_y=(1300, 1500), big=None):
    t = f / FPS; ws = tx["words"]
    exit_k = (t - tx["end"]) * FPS                                                      # wax-melt exit
    bump = 0.0
    for ta in E.ACCENTS:
        if ta <= t: bump = max(bump, math.exp(-(t - ta) / 0.10))
    for ln in sorted({l for _, _, l in ws}):
        row = [(w, wt) for w, wt, l in ws if l == ln]; sp = -40
        imgs = [title_face(word_rgba(w, tx["style"] if big is None or w in big else "cap", False), f, 7 + i) if (big is None or w in big)
                else word_rgba(w, "cap", False) for i, (w, _) in enumerate(row)]
        total = sum(im.shape[1] + sp for im in imgs) - sp; fit = min(1.0, (W - 90) / total); total *= fit; x = W / 2 - total / 2
        for im, (w, wt) in zip(imgs, row):
            k = (t - wt) * FPS
            if k >= -1:
                if k < 8:                                                               # drop in from above, blurred, then squash
                    v = eout((k + 1) / 9, 2.6); dy = -150 * (1 - v); sx, sy = 0.92 + 0.08 * v, 1.12 - 0.12 * v; bl = 5 * (1 - v); a = clamp((k + 1) / 4, 0, 1)
                else:
                    kk = k - 8; sq = 0.10 * math.exp(-kk / 3.0) * math.cos(kk * 1.3)
                    dy = 0; sx, sy = 1 + sq * 0.6, 1 - sq; bl = 0; a = 1.0
                sb = 1 + 0.035 * bump
                sx *= sb; sy *= sb
                if exit_k > 0:
                    a *= clamp(1 - exit_k / 9, 0, 1); dy += 6 * exit_k ** 1.4; sy *= 1 + 0.04 * exit_k
                    im = cv2.blur(im, (1, int(1 + exit_k * 2.2))) if exit_k > 1 else im
                out = put(out, im, x + im.shape[1] * fit / 2, rows_y[ln] + dy, a, sx * fit, sy * fit, bl)
            x += (im.shape[1] + sp) * fit
    return out

def text101(out, f):
    t = f / FPS
    for tx in E.TEXT:
        t0, t1 = tx["words"][0][1] - 0.05, tx["end"] + 0.25
        if not (t0 <= t < t1): continue
        if tx.get("burn") and t >= tx["end"]: continue
        if tx["style"] == "cap": out = lay_caps(out, f, tx)
        elif tx["style"] == "title": out = lay_title(out, f, tx, rows_y=(1318, 1512))
        elif tx["style"] == "better":
            tt = dict(tx); tt["style"] = "title"
            tt["words"] = [("THE", tx["words"][0][1], 0), ("BETTER.", tx["words"][1][1], 1)]
            out = lay_title(out, f, tt, rows_y=(1300, 1450), big=["BETTER."])
    return out

# ---------------------------------------------------------------------------- film-strip helpers
def gate_strip(top, bot, p, bar=96):
    """a vertical film strip [top][frame line][bot] moved up by p px (0 = top fills the gate, H+bar = bot fills it)."""
    y = np.arange(H, dtype=np.int64) + int(round(p))
    o = np.zeros((H, W, 3), np.float32)
    mt = y < H; mb = y >= H + bar; ml = ~mt & ~mb
    if mt.any(): o[mt] = top[np.clip(y[mt], 0, H - 1)]
    if mb.any(): o[mb] = bot[np.clip(y[mb] - H - bar, 0, H - 1)]
    if ml.any():
        rows = np.nonzero(ml)[0]; o[rows] = np.array([0.02, 0.015, 0.02], np.float32)
        yc = int(rows.mean());
        for xh in (34, W - 110):                                                        # sprocket holes: lamp light through the perforations
            cv2.rectangle(o, (xh, yc - 26), (xh + 76, yc + 26), (0.75, 0.88, 0.95), -1, cv2.LINE_AA)
        o[rows] = cv2.GaussianBlur(o[rows], (0, 0), 1.2) if len(rows) > 4 else o[rows]
    return o

# ---------------------------------------------------------------------------- transitions
# 1. projector strike-up from black (the loop entry)
def projector_on(A, B, j, f, sa, sb, n=26):
    expo = [0, 0, 0.18, 0.04, 0.7, 0.15, 1.5, 0.55, 0.35, 1.25, 0.85, 1.1, 0.95, 1.05, 0.98, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    e = expo[min(j, len(expo) - 1)]
    p = (H + 96) * (1 - eout(clamp((j - 3) / 12, 0, 1), 2.4)) if j < 15 else 0.0      # the frame line rolls into place
    img = gate_strip(B, B, p) if p > 0.5 else B
    if p > 4: img = hblur(img, min(60, p / 18), vertical=True)
    hot = np.exp(-(((_GX - W / 2) / (W * 0.55)) ** 2 + ((_GY - H * 0.45) / (H * 0.5)) ** 2))[..., None]
    o = img * min(1.0, e) + np.clip(e - 1, 0, 1) * (HOTW * 0.9 + 0.1) * (0.4 + 0.6 * hot)
    o = o * (0.35 + 0.65 * hot) ** (1 - clamp(j / 18, 0, 1))
    if j < 3: o = o * 0 + hot * np.array([0.02, 0.03, 0.05], np.float32) * j
    return np.clip(o, 0, 1)

_LX = {}
# 2. latex: the frame is stretched like a glove being pulled on, tears open, and snaps onto the next shot
def latex(A, B, j, f, sa, sb):
    P0 = np.array([W * 0.56, H * 0.56], np.float32); dv = np.array([0.50, 0.866], np.float32); sig = 400.0
    g = np.exp(-(((_GX - P0[0]) ** 2 + (_GY - P0[1]) ** 2) / (2 * sig * sig)))
    if j < 0:
        k = ein((j + 10) / 10, 1.6); D = 800 * k
        mx = (_GX - dv[0] * D * g).astype(np.float32); my = (_GY - dv[1] * D * g).astype(np.float32)
        o = cv2.remap(A, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        st_ = np.clip(g * k * 1.4, 0, 1)[..., None]                                     # stretched membrane: paler, glossy
        Lm = lum(o)[..., None]
        o = o * (1 - 0.6 * st_) + (Lm * 0.5 + np.array([0.62, 0.60, 0.58], np.float32) * 0.5) * 0.6 * st_
        perp = (_GX - P0[0]) * dv[1] - (_GY - P0[1]) * dv[0]
        sheen = (g * k) * (np.exp(-((perp + 60) / 150.0) ** 2) + 0.4 * np.exp(-((perp - 220) / 90.0) ** 2))
        o = o + sheen[..., None] * CREAMC * 0.45
        if j >= -4:                                                                     # it tears open at the pulled point
            c = P0 + dv * D * 0.55; ua = (_GX - c[0]) * dv[0] + (_GY - c[1]) * dv[1]; up = (_GX - c[0]) * dv[1] - (_GY - c[1]) * dv[0]
            if "rag" not in _LX: _LX["rag"] = _lowfreq((H, W), (60, 34), 91) - 0.5
            rh = 900 * ein((j + 5) / 5, 1.5) + 1e-3                                       # a slit across the pull that splits open
            q = np.sqrt((ua / (0.38 * rh)) ** 2 + (up / rh) ** 2) * (1 + 0.30 * _LX["rag"])
            hole = np.clip((1 - q) * rh / 8.0, 0, 1)[..., None]; rim = np.exp(-((q - 1) * rh / 9.0) ** 2)[..., None]
            o = o * (1 - hole) + zoom_about(B, c[0], c[1], 1.08) * hole + rim * CREAMC * 0.5
        return np.clip(o, 0, 1)
    v = (j + 1) / 12.0; r = np.sqrt((_GX - P0[0]) ** 2 + (_GY - P0[1]) ** 2) + 1e-3
    amp = 30 * math.exp(-j / 3.0) * np.exp(-r / 900)
    disp = amp * np.sin(r / 52.0 - j * 1.6)
    mx = (_GX + disp * (_GX - P0[0]) / r).astype(np.float32); my = (_GY + disp * (_GY - P0[1]) / r).astype(np.float32)
    o = cv2.remap(B, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    sc = 1 + 0.05 * math.exp(-j / 3.5) * math.cos(j * 1.2)
    return np.clip(zoom_about(o, P0[0], P0[1], sc), 0, 1)

# 3. frame slip: the film loses its loop in the gate and rolls one frame up onto the next shot
def frameslip(A, B, j, f, sa, sb):
    n0, n1 = 8, 12
    if j < -4:
        jit = 7 * (j + n0) / 4 * math.sin(j * 2.9); return np.clip(np.roll(A, int(jit), 0), 0, 1)
    u = clamp((j + 4) / 11, 0, 1); p = (H + 96) * smooth(u) ** 1.2
    if j >= 7: p = (H + 96) + 22 * math.exp(-(j - 7) / 2.0) * math.cos((j - 7) * 1.7)
    o = gate_strip(A, B, p)
    vel = (H + 96) / 11 * 1.6 * math.sin(math.pi * u) if j < 7 else 0
    if vel > 6: o = hblur(o, min(120, vel * 0.7), vertical=True)
    return np.clip(o * (1 + 0.25 * math.sin(math.pi * u)), 0, 1)

# 4. HERO: the projector stalls on his face, the film blisters and burns through on the bass drop
_MLT = {}
def melt_noise():
    if "n" not in _MLT:
        _MLT["n"] = _lowfreq((H // 2, W // 2), (14, 8), 41) * 0.65 + _lowfreq((H // 2, W // 2), (48, 27), 42) * 0.35
        _MLT["b"] = _lowfreq((H // 2, W // 2), (110, 62), 43)
        rng = np.random.default_rng(44)
        _MLT["emb"] = [(rng.uniform(0, 6.283), rng.uniform(250, 1300), rng.uniform(2, 6), rng.uniform(0, 1)) for _ in range(150)]
    return _MLT

NUC = [((0.72, 0.27), 0.00, 1.0), ((0.27, 0.60), 0.45, 0.8), ((0.58, 0.84), 0.62, 0.7), ((0.40, 0.12), 0.75, 0.6)]
def burn_field(k_pre, k_post):
    """signed burn front (half-res): >0 burnt through, a char ring at 0..-14, a heat zone to -70."""
    M = melt_noise(); hy, hx = np.mgrid[0:H // 2, 0:W // 2].astype(np.float32)
    b = np.full((H // 2, W // 2), -1e4, np.float32)
    for (nx, ny), k0, gr in NUC:
        if k_pre < k0 and k_post <= 0: continue
        kk = clamp((k_pre - k0) / (1 - k0), 0, 1)
        r = 150 * gr * kk ** 1.6 + 1400 * eout(k_post, 1.7)
        d = np.sqrt((hx - nx * W / 2) ** 2 + (hy - ny * H / 2) ** 2) * (1 + 0.55 * (M["n"] - 0.5))
        b = np.maximum(b, r - d)
    return b

def filmmelt(A, B, j, f, sa, sb):
    M = melt_noise()
    if j < 0:
        k = (j + 18) / 18.0
        Af = A if j < -12 else np.roll(A, int(3 * math.sin(j * 3.1)), 0)                 # the projector stutters
        b = cv2.resize(burn_field(k, 0), (W, H), interpolation=cv2.INTER_LINEAR)
        content = (HOTW * 0.95 + 0.05) * np.ones((H, W, 3), np.float32)
    else:
        k = 1.0; v = (j + 1) / 22.0
        b = cv2.resize(burn_field(1.0, v), (W, H), interpolation=cv2.INTER_LINEAR)
        fl = math.exp(-j / 3.0)
        lq, wl = liquid_full(f, seed=9, speed=2.0)
        light = HOTW * 0.9 + lq * 0.25
        content = B * (1 - fl) + light * fl
        Af = A
    heat = np.clip(1 + b / 70.0, 0, 1)                                                  # 0 far .. 1 at the front
    bub = (cv2.resize(M["b"], (W, H)) - 0.5)
    bulge = heat ** 2 * (16 + 10 * bub)
    gx = cv2.Sobel(b, cv2.CV_32F, 1, 0, ksize=5); gy = cv2.Sobel(b, cv2.CV_32F, 0, 1, ksize=5)
    gn = np.sqrt(gx * gx + gy * gy) + 1e-6
    Aw = cv2.remap(Af, (_GX + bulge * gx / gn).astype(np.float32), (_GY + bulge * gy / gn).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    scorch = heat[..., None] ** 1.5
    Aw = Aw * (1 - 0.55 * scorch) + (Aw * HOTW * 1.6 + EMBER * 0.25) * scorch * 0.55     # overheated: yellows and browns
    blister = np.clip((bub * 2.0 - 0.2) * heat * 1.6, 0, 1)[..., None] * np.clip((heat[..., None] - 0.55) / 0.3, 0, 1)
    Aw = Aw * (1 - 0.25 * blister) + HOTW * 0.25 * blister
    hole = np.clip(b / 4.0, 0, 1)[..., None]
    char = np.clip(1 - np.abs(b + 7) / 9.0, 0, 1)[..., None]
    glow = np.exp(-((b + 1) / 4.5) ** 2)[..., None]
    o = Aw * (1 - hole) + content * hole
    o = o * (1 - char * 0.92) + CHAR * char * 0.92
    o = o + glow * (EMBER * 1.2 + HOTW * 0.4) * (0.9 if j < 0 else 0.9 * (1 - (j + 1) / 22))
    if j >= -6:                                                                         # embers flung off the burn front
        tt = (j + 6) / FPS
        for ang, spd, r, ph in M["emb"]:
            if ph > (j + 8) / 10: continue
            x = W * 0.62 + math.cos(ang) * spd * tt * 1.2; y = H * 0.40 + math.sin(ang) * spd * tt - 600 * tt * tt
            if 0 <= x < W and 0 <= y < H: cv2.circle(o, (int(x), int(y)), int(r), tuple(float(c) for c in (EMBER * 0.6 + HOTW * 0.6)), -1, cv2.LINE_AA)
    if j >= 0 and j < 3: o = o * 0.4 + HOTW * 0.6 * (1 - j / 3) + o * 0.6 * (j / 3)
    return np.clip(o, 0, 1)

# 5. whip pan
def whip(A, B, j, f, sa, sb, n0=6, n1=8):
    u = clamp((j + n0) / (n0 + n1), 0, 1); p = W * (smooth(u) ** 1.3)
    vel = W / (n0 + n1) * 2.4 * math.sin(math.pi * u)
    o = np.zeros_like(A); ip = int(round(p))
    if ip < W: o[:, :W - ip] = A[:, ip:]
    if ip > 0: o[:, W - ip:] = B[:, :ip]
    o = hblur(o, min(260, vel * 1.1))
    o = rgb_split(o, vel * 0.04)
    return np.clip(o + (0.10 * math.sin(math.pi * u)) * AMBER, 0, 1)

# 6. the hood is pulled down over the lens, then lifts off the next shot
_HD = {}
def hoodover(A, B, j, f, sa, sb, n0=9, n1=12):
    if "t" not in _HD:
        fold = cv2.resize(np.random.default_rng(81).random((3, 26)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
        fine = _lowfreq((H, W), (40, 60), 82)
        _HD["t"] = (fold * 0.7 + fine * 0.3).astype(np.float32)
    if j < 0: v = ein((j + n0) / n0, 1.5); e = -0.12 * H + 1.30 * H * v; base = A
    else: v = eout((j + 1) / n1, 1.7); e = 1.18 * H - 1.32 * H * v; base = B
    ye = e + 140 * np.cos((_GX - W / 2) / W * math.pi)                                  # the hood's rim is curved (lower at the centre)
    cov = np.clip((ye - _GY) / 14.0 + 0.5, 0, 1)[..., None]                              # fabric above the rim
    tex = _HD["t"][..., None]
    fabric = np.array([0.075, 0.045, 0.07], np.float32) * (0.45 + 1.2 * tex)
    fabric = fabric + np.clip(tex - 0.62, 0, 1) * 0.30 * (OXB * 0.4 + CREAMC * 0.15)     # light on the folds
    rimhl = np.exp(-((ye - _GY - 26) / 22.0) ** 2)[..., None] * (0.16 + 0.10 * tex)       # light catching the rim of the hood
    fabric = fabric + rimhl * (AMBER * 0.5 + CREAMC * 0.3)
    shade = 1 - 0.55 * np.exp(-np.clip(_GY - ye, 0, None) / 120.0)[..., None]           # the hood's shadow falls on the image
    o = base * shade * (1 - cov) + fabric * cov
    return np.clip(o, 0, 1)

# 8. lava lamp: glossy blood blobs rise and swallow the frame, then rise off the next shot
_LV = {}
def lava_field(tt, grow):
    if "b" not in _LV:
        rng = np.random.default_rng(61)
        _LV["b"] = [(rng.uniform(0.08, 0.92), rng.uniform(0.55, 1.25), rng.uniform(0.11, 0.19), rng.uniform(0, 6.28), rng.uniform(0.0, 0.35)) for _ in range(11)]
        _LV["g"] = np.mgrid[0:H // 4, 0:W // 4].astype(np.float32) / (H // 4)
    hy, hx = _LV["g"]; Fd = np.zeros_like(hx)
    for x0, sp, r, ph, d0 in _LV["b"]:
        cx = x0 * W / H + 0.035 * math.sin(tt * 4 + ph); cy = 1.25 + d0 - sp * tt * 1.15
        R = r * (1 + 1.9 * grow)
        q = ((hx - cx) ** 2 + ((hy - cy) * 0.82) ** 2) / (R * R)
        Fd += np.clip(1 - q, 0, 1) ** 2
    return cv2.resize(Fd, (W, H), interpolation=cv2.INTER_CUBIC)

def lavalamp(A, B, j, f, sa, sb, n0=12, n1=14):
    if j < 0: u = (j + n0) / n0; Fd = lava_field(u, ein(u, 2.0) * 1.05); src = A; base = A
    else: u = (j + 1) / n1; Fd = lava_field(1 + u * 0.9, 1.05 * (1 - eout(u, 1.4))); src = B; base = B
    thr = 0.30
    inside = np.clip((Fd - thr) / 0.06, 0, 1)[..., None]
    gx = cv2.Sobel(Fd, cv2.CV_32F, 1, 0, ksize=7); gy = cv2.Sobel(Fd, cv2.CV_32F, 0, 1, ksize=7)
    gm = np.sqrt(gx * gx + gy * gy) + 1e-6; nx, ny = gx / (gm.max() + 1e-6), gy / (gm.max() + 1e-6)
    ref = cv2.remap(src, (_GX - nx * 60).astype(np.float32), (_GY - ny * 60).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    depth = np.clip((Fd - thr) / 0.7, 0, 1)[..., None]
    liq = ref * (np.array([0.22, 0.20, 0.80], np.float32) + 0.20 * (1 - depth)) + OXB * (0.12 + 0.30 * depth)
    liq = liq * (1 - 0.35 * np.exp(-((Fd - thr) / 0.10) ** 2)[..., None])                  # darker skins where blobs meet
    spec = np.clip(nx * -0.55 + ny * -0.83, 0, 1) ** 6 * np.clip(1 - depth[..., 0] * 1.2, 0, 1)
    fres = np.exp(-((Fd - thr) / 0.05) ** 2)[..., None]
    liq = liq + spec[..., None] * CREAMC * 0.9 + fres * (OXB * 0.6 + AMBER * 0.25)
    o = base * (1 - inside) + liq * inside
    return np.clip(o, 0, 1)

_SW = {}
# 9. a blood slide's glass slides across the frame; the next shot is seen through the glass
def slidewipe(A, B, j, f, sa, sb, n0=9, n1=11):
    u = clamp((j + n0) / (n0 + n1), 0, 1); sw = W * 1.05
    lead = W + 40 - (W + 40 + sw + 80) * smooth(u)                                     # leading edge moves right -> left
    trail = lead + sw
    X = _GX + (_GY - H / 2) * 0.10                                                      # slight slant
    inglass = ((X > lead) & (X < trail)).astype(np.float32)
    inglass = cv2.GaussianBlur(inglass, (0, 0), 1.5)[..., None]
    past = (X >= trail).astype(np.float32)[..., None]
    src = B
    mag = cv2.remap(src, (W / 2 + (_GX - W / 2) / 1.06 + 8).astype(np.float32), (H / 2 + (_GY - H / 2) / 1.06).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    mag = rgb_split(mag, 4)
    if "sm" not in _SW:
        m = np.zeros((H, W), np.float32)
        cv2.ellipse(m, (int(W * 0.46), int(H * 0.70)), (int(W * 0.36), 130), -24, 0, 360, 1.0, -1, cv2.LINE_AA)   # the smear (below the faces)
        nz = _lowfreq((H, W), (30, 18), 95) * 0.6 + _lowfreq((H, W), (90, 50), 96) * 0.4
        m = np.clip((m * (0.35 + nz) - 0.45) * 3.0, 0, 1)                                                          # ragged, uneven film of blood
        cv2.circle(m, (int(W * 0.70), int(H * 0.60)), 52, 1.0, -1, cv2.LINE_AA)                                    # the drop
        _SW["sm"] = cv2.GaussianBlur(m, (0, 0), 4).astype(np.float32)
    shiftx = int(lead - 0)                                                               # the smear rides with the glass
    smear = np.roll(_SW["sm"], shiftx - int(W * 0.0), axis=1) * (X > lead) * (X < trail)
    smear = smear[..., None]
    glass = mag * (1 - smear * 0.50) + (mag * 0.45 + OXB * 0.55) * smear * 0.50
    frost = ((X > trail - sw * 0.16) & (X < trail)).astype(np.float32)[..., None]
    glass = glass * (1 - frost * 0.55) + CREAMC * 0.72 * frost * 0.55
    bevel = (np.exp(-((X - lead) / 6) ** 2) + np.exp(-((X - trail) / 6) ** 2))[..., None]
    base = A if j < 0 else A * 0 + B
    if j >= 0: base = B
    o = base * (1 - inglass) * (1 - past) + B * past * (1 - inglass) + glass * inglass + bevel * 0.55 * CREAMC
    o = o + np.exp(-((X - lead - 30) / 60) ** 2)[..., None] * 0.08
    return np.clip(o, 0, 1)

# 10. the newspaper spins in (the press doesn't know either)
def newsspin(A, B, j, f, sa, sb, n=18):
    u = (j + 1) / n; land = 0.78
    v = eout(clamp(u / land, 0, 1), 2.6)
    ang = 900 * (1 - v); sc = 0.05 + 0.95 * v
    if u > land: kk = (u - land) / (1 - land); sc = 1 + 0.05 * math.exp(-kk * 5) * math.cos(kk * 9)
    bg = cv2.GaussianBlur(A, (0, 0), 3 + 10 * v) * (0.85 - 0.55 * v)
    M = cv2.getRotationMatrix2D((W / 2, H * 0.47), ang, sc)
    paper = cv2.warpAffine(B, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0))
    m = cv2.warpAffine(np.ones((H, W), np.float32), M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)[..., None]
    shm = cv2.GaussianBlur(np.roll(np.roll(m[..., 0], 26, 0), 18, 1), (0, 0), 22)[..., None] * 0.7
    o = bg * (1 - shm) + bg * 0.2 * shm
    o = o * (1 - m) + paper * m
    if u > land and u < land + 0.12: o = o + 0.25 * (1 - (u - land) / 0.12)
    return np.clip(o, 0, 1)

# 11. the newspaper tears down the middle onto the next shot
_TR = {}
def papertear(A, B, j, f, sa, sb, n0=6, n1=11):
    if "x" not in _TR:
        rng = np.random.default_rng(71); yy = np.arange(H)
        x = np.cumsum(rng.normal(0, 6, H)); x = np.convolve(np.pad(x, 30, mode="edge"), np.ones(61) / 61, "valid")[:H]
        x = x - np.linspace(x[0], x[-1], H) + rng.normal(0, 1.2, H)
        _TR["x"] = (W / 2 + x * 1.2 + 26 * np.sin(yy / 90)).astype(np.float32)
        _TR["fib"] = rng.random((H, 40)).astype(np.float32)
    xt = _TR["x"][:, None]
    if j < 0: u = (j + n0) / n0; L = H * eout(u, 2); sep = 8 * u; rot = 0
    else: u = (j + 1) / n1; L = H; sep = 8 + W * 0.75 * ein(u, 1.6); rot = 9 * ein(u, 1.4)
    torn = (_GY < L)
    o = B * (1 - 0.35 * np.exp(-np.abs(_GX - xt) / (40 + sep)))[..., None] if j >= 0 else B.copy()
    for sg in (-1, 1):
        M = cv2.getRotationMatrix2D((W / 2, 0 if sg < 0 else 0), -sg * rot, 1.0); M[0, 2] += sg * sep / 2
        half = cv2.warpAffine(A, M, (W, H), borderMode=cv2.BORDER_REFLECT)
        side = (_GX < xt) if sg < 0 else (_GX >= xt)
        msk = np.where(torn, side, 1.0).astype(np.float32)
        mw = cv2.warpAffine(msk, M, (W, H), borderValue=0)
        fib = cv2.resize(_TR["fib"], (W, H), interpolation=cv2.INTER_LINEAR) if "fibW" not in _TR else _TR["fibW"]; _TR["fibW"] = fib
        wid = 7 + 9 * fib
        edge = np.clip(1 - np.abs(_GX - (xt + sg * wid * 0.6)) / wid, 0, 1) * torn
        ew = cv2.warpAffine(edge.astype(np.float32), M, (W, H), borderValue=0)[..., None]
        o = o * (1 - mw[..., None]) + half * mw[..., None]
        o = o * (1 - ew) + np.array([0.86, 0.90, 0.92], np.float32) * ew
    return np.clip(o, 0, 1)

# 13. oil wheel: the liquid-light show builds over the frame, owns it for a beat, and drains away off the next shot
def oilwheel(A, B, j, f, sa, sb, n0=10, n1=13):
    col, wall, idx, inten = liquid(f, seed=21, speed=2.6, n=7)
    col = np.clip(cv2.resize(col, (W, H), interpolation=cv2.INTER_CUBIC), 0, 1); wall = np.clip(cv2.resize(wall, (W, H), interpolation=cv2.INTER_CUBIC), 0, 1)
    idx = cv2.GaussianBlur(cv2.resize(idx, (W, H), interpolation=cv2.INTER_NEAREST), (0, 0), 5)
    ph = (_GX + _GY) / 160.0 + f * 0.25
    irid = np.stack([0.5 + 0.5 * np.cos(ph), 0.5 + 0.5 * np.cos(ph + 2.1), 0.5 + 0.5 * np.cos(ph + 4.2)], -1).astype(np.float32)
    wl = (wall ** 1.5)[..., None]
    light = col * 0.85 + wl * irid * 0.35
    if j < 0: u = (j + n0) / n0; a = 0.94 * ein(u, 1.6)
    else: u = (j + 1) / n1; a = 0.94 * (1 - eout(u, 1.6))
    w = smooth((j + 3) / 6.0)                                                            # the shots swap under the peak of the light show
    src = A * (1 - w) + B * w
    scr = 1 - (1 - src * 0.45) * (1 - light)
    return np.clip(src * (1 - a) + scr * a, 0, 1)

# 15. reel end: the film flutters, runs out of the gate, the lamp flickers through the tail, black (loop exit)
def reel_end(out, f, s, n=30):
    j = f - s["f1"]
    if j < -n: return out
    k = j + n
    if k < 10:
        return np.clip(np.roll(out, int(5 * k / 10 * math.sin(k * 2.7)), 0), 0, 1)
    p = (H + 96) * ein((k - 10) / 12, 1.6)
    white = np.ones((H, W, 3), np.float32) * HOTW
    o = gate_strip(out, white, p)
    o = hblur(o, min(80, 6 + p / 30), vertical=True)
    flick = 0.55 + 0.45 * (1 if (k % 3) else 0.35)
    if k >= 22:
        o = white * (1 - (k - 22) / 6) * flick
        tail = (np.sin(_GX / 70 + k * 2.1) > 0.6).astype(np.float32)[..., None] * 0.5
        o = o * (1 - tail * (k < 27))
    return np.clip(o * (1 if k < 27 else 0), 0, 1)

TR2.update({"projector_on": (projector_on, 0, 26), "latex": (latex, 10, 12), "frameslip": (frameslip, 8, 12),
            "filmmelt": (filmmelt, 18, 22), "whip": (whip, 6, 8), "hooddark": (hoodover, 9, 12), "scalpel": (slash, 5, 14),
            "lavalamp": (lavalamp, 12, 14), "slidewipe": (slidewipe, 9, 11), "newsspin": (newsspin, 0, 18),
            "papertear": (papertear, 6, 11), "oilwheel": (oilwheel, 10, 13), "facematch": (facematch, 7, 7)})

# ---------------------------------------------------------------------------- frame
def last_visible(P):
    fr = P["f1"] - 1
    if P.get("seg"):
        o, person = render_shot(P, fr, want_mask=True)
        if P.get("liquid"): o = liquid_projection(o, person, fr, P)
        if P.get("prism"): o = prism_echo(o, person, fr, P)
        return o
    return render_shot(P, fr)

def render(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin"); tout = s.get("tout")
    if s.get("seg"):
        out, person = render_shot(s, f, want_mask=True)
        if s.get("liquid"): out = liquid_projection(out, person, f, s)
        if s.get("prism"): out = prism_echo(out, person, f, s)
    else:
        out = render_shot(s, f)
    out = text101(out, f)
    if tin in TR2 and k < TR2[tin][2]: out = TR2[tin][0](last_visible(P) if P else out * 0, out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, render_shot(n_, n_["f0"], False), kn, f, s, n_)
    if tout == "reel_end": out = reel_end(out, f, s)
    out = light_leaks(out, f)
    out = finish_film(out, f)
    if tout == "reel_end" and f - s["f1"] >= -3: out = out * 0
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)

def init_hits():
    HITS.clear()
    HITS.append((E.fh(E.HDROP), 14, 3.5))                                              # the burn-through lands
    HITS.append((E.fe(E.th(67) + 0.78 * 18 / FPS), 10, 3.0))                            # the newspaper slams down
