# ============================================================================ v13 — EVENT HORIZON (The Flash × Brent Faiyaz): SINGULARITY
# The S1 finale's singularity sings the song: a love that pulls everything in. The hero asset is a procedural BLACK HOLE
# (shadow, photon ring, gravitational lensing of the real footage, an accretion disk of lightning with Doppler colour) that
# runs through the edit. Transitions on the real physics: LENS DROP (Einstein ring), FRAME DRAG (Lense-Thirring twist),
# REDSHIFT (gravitational redshift), PHOTON RING (light orbiting the hole), EYE HORIZON (his pupil becomes the hole),
# ACCRETION WHIP (through the disk plane), EVENT HORIZON (time dilation, the focal set piece), GRAV WAVE (quadrupole strain
# ripple on the breakout), SPAGHETTIFY (tidal stretch), EMBLEM HORIZON (on the real tracked emblem), the loop fall.
# Look REDSHIFT: a desaturated silver-steel world; only the suit's crimson, skin and the hole's light keep their colour.
HOT = np.array([0.90, 0.96, 1.00], np.float32)           # BGR white-hot
AMB = np.array([0.32, 0.66, 1.00], np.float32)           # BGR amber (receding side, glow)
RSH = np.array([0.16, 0.26, 0.92], np.float32)           # BGR deep red-orange (redshift)
COOLW = np.array([1.00, 0.93, 0.82], np.float32)         # BGR cool white (approaching side)
STEEL = np.array([0.030, 0.012, -0.008], np.float32)     # BGR shadow push (steel)
# restyle the library: gold / red / ember light in the v4-v12 transitions now draws in the v13 palette
GOLDW, GOLD2, GOLD, EMBER2 = HOT.copy(), AMB.copy(), np.array([0.45, 0.78, 1.00], F32), np.array([0.30, 0.55, 1.00], F32)
REDW, RED2 = HOT.copy(), AMB.copy()
JASW, JASG, JASY = HOT.copy(), AMB.copy(), AMB.copy()
if E.VER == "v13":
    for _s in E.SHOTS:
        _s.setdefault("target", 0.36)

# ---- grade: REDSHIFT ----------------------------------------------------------------------------------------------
_LUTR = {}
def lutR():
    if "r" not in _LUTR:
        x = np.linspace(0, 1, 1024, dtype=np.float32)
        _LUTR["r"] = (x, PchipInterpolator([0, .05, .20, .50, .80, .94, 1], [0.004, 0.018, 0.115, 0.430, 0.790, 0.935, 0.975])(x).astype(np.float32))
    return _LUTR["r"]

E_BRIGHT13 = {"sky": 0.10, "pull": 0.35, "leave": 0.30, "iris": 0.30, "last": 0.35, "blood": 0.15, "horizon": 0.30}
_grade_pre13 = grade
def grade(img, s, f):
    if s.get("look") != "redshift": return _grade_pre13(img, s, f)
    g, gains = corr9(s); ev = (s.get("ev") or 0) - 0.45 * E_BRIGHT13.get(s["n"], 0.0)
    lx, ly = lutR()
    if in_unit(img): x = apply_lut3(img, tone_lut(("rsh", s["n"], round(ev, 3), float(g), tuple(float(v) for v in gains)), gains, g, ev, lx, ly))
    else:
        x = np.clip(img * gains, 0, 1) ** g
        if ev: x = np.clip(x * 2 ** ev, 0, 1)
        x = np.interp(x, lx, ly).astype(F32)
    B, G, R = (np.ascontiguousarray(x[..., c]) for c in range(3))
    L = B * 0.114 + G * 0.587 + R * 0.299
    gr = G / (R + 1e-3); warm = np.clip((R - B) * 3.0, 0, 1)
    red = np.clip((0.42 - gr) * 5.0, 0, 1) * warm * np.clip(R * 3, 0, 1)                    # crimson (the suit)
    hue = (R - G) / (R + 1e-3)
    skin = np.clip(1 - np.abs(hue - 0.22) / 0.22, 0, 1) * np.clip((R - B) * 6, 0, 1) * np.clip(L * 3, 0, 1)
    hotl = np.clip((L - 0.55) * 2.5, 0, 1) * np.clip(warm * 1.4, 0, 1) * (1 - skin)          # lightning / fire keeps colour
    keep = np.clip(red * 0.85 + skin * 0.8 + hotl, 0, 1)
    sat = (0.30 + 0.62 * keep) * s.get("satk", 1.0)
    sh = (1 - L) ** 2.2 * (1 - 0.6 * skin) * (1 - 0.7 * red)
    o = np.empty(x.shape, F32)
    for c, P in enumerate((B, G, R)):
        v = L + (P - L) * sat
        o[..., c] = v + sh * STEEL[c]
    return np.clip(o, 0, 1, out=o)

def redshift_px(img, k):
    """gravitational redshift: the light loses energy (dimmer) and slides to red."""
    if k <= 0: return img
    L = lum8(img); o = np.empty(img.shape, F32)
    tint = (0.30, 0.55, 1.15)
    for c in range(3): o[..., c] = img[..., c] * (1 - 0.42 * k) + L * tint[c] * 0.42 * k * (1 - 0.35 * k)
    return o

_FIN13 = {}
def finish13(out, f, s):
    if "v" not in _FIN13:
        grain(0, 0.010); _FIN13["v"] = np.repeat(0.66 + 0.34 * VIG, 3, axis=2)
        _FIN13["floor"] = np.array([0.012, 0.010, 0.010], F32)
    k = ("g", f % 6)
    if k not in _FIN13: _FIN13[k] = np.repeat(grain(f, 0.010), 3, axis=2)
    small = cv2.resize(out, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    hi_ = np.clip(small.max(2) - 0.62, 0, 1)
    bl = cv2.resize(cv2.GaussianBlur(hi_, (0, 0), 4) * 0.40 + cv2.GaussianBlur(hi_, (0, 0), 18) * 0.60, (W, H))
    o = out.copy(); addc(o, bl, AMB, 0.40)
    np.maximum(o, _FIN13["floor"], out=o)
    o *= _FIN13["v"]; o += _FIN13[k]
    return np.clip(o, 0, 1, out=o)

# ---- THE SINGULARITY (hero asset) --------------------------------------------------------------------------------
_GX, _GY = np.meshgrid(np.arange(W, dtype=F32), np.arange(H, dtype=F32))
SH_K = 0.56                                                                                 # shadow radius / Einstein radius

def bh_warp(img, cx, cy, re, spin=0.0, pull=0.0):
    """gravitational lensing of a point mass: each pixel sees the source at c + d (1 - re^2 / r^2) (inside the Einstein
    ring the image is the inverted secondary image); spin twists the light near the hole (frame dragging); pull draws the
    picture in toward the hole. Computed in a box around the hole (the deflection is tapered to zero at its edge)."""
    if re < 0.5 and not spin and not pull: return img
    Rb = min(2.2 * max(W, H), 11 * max(re, 40) + 120)
    x0, x1 = int(max(0, cx - Rb)), int(min(W, cx + Rb)); y0, y1 = int(max(0, cy - Rb)), int(min(H, cy + Rb))
    if x1 <= x0 or y1 <= y0: return img
    dx = _GX[y0:y1, x0:x1] - cx; dy = _GY[y0:y1, x0:x1] - cy
    r2 = dx * dx + dy * dy + 1.0; r = np.sqrt(r2)
    taper = np.clip((Rb - r) / (0.45 * Rb), 0, 1); taper = taper * taper * (3 - 2 * taper)
    k = 1.0 - (re * re / r2) * taper
    if pull: k = k * (1.0 + pull * taper * np.exp(-r / (0.55 * Rb)))
    if spin:
        a = spin * np.clip(re * re / r2, 0, 6.0) * taper; ca, sa = np.cos(a), np.sin(a)
        dx, dy = dx * ca - dy * sa, dx * sa + dy * ca
    mx = (cx + dx * k).astype(F32); my = (cy + dy * k).astype(F32)
    o = img.copy()
    o[y0:y1, x0:x1] = cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return o

def ring_mask(cx, cy, r0, w, scale=4):
    """a thin ring (radius r0, half-width w) at 1/scale resolution, upsampled."""
    h_, w_ = H // scale, W // scale
    gx, gy = np.meshgrid(np.arange(w_, dtype=F32) * scale, np.arange(h_, dtype=F32) * scale)
    d = np.sqrt((gx - cx) ** 2 + (gy - cy) ** 2)
    return cv2.resize(np.exp(-((d - r0) / max(w, 1.0)) ** 2).astype(F32), (W, H), interpolation=cv2.INTER_LINEAR)

def disc_mask(cx, cy, r, soft=2.0):
    m = np.zeros((H, W), F32)
    if r > 0.5: cv2.circle(m, (int(round(cx * 4)), int(round(cy * 4))), int(round(r * 4)), 1.0, -1, cv2.LINE_AA, shift=2)
    return cv2.GaussianBlur(m, (0, 0), soft) if soft > 0 else m

_DSK = {}
def disk_filaments(seed=13, n=34):
    if seed in _DSK: return _DSK[seed]
    rng = np.random.default_rng(seed); out = []
    for i in range(n):
        ri = 1.50 + 1.9 * rng.random() ** 1.6                                              # more of them near the hole
        out.append((ri, rng.uniform(0, 2 * math.pi), rng.uniform(0.7, 2.4), int(rng.integers(1, 3)), rng.uniform(0.5, 1.0), int(rng.integers(0, 10 ** 6))))
    _DSK[seed] = out; return out

def bh_disk(cx, cy, rs, t, amt=1.0, incl=0.21, tilt=-0.16, seed=13, omega=1.6):
    """the accretion disk as lightning: filaments on Keplerian orbits (inner ones faster), the near half in front of the
    shadow, the far half hidden behind it and lensed into an arc over the top (and a thin one under it); Doppler colour:
    the approaching side (left) brighter and cooler, the receding side dimmer and redder. Returns (front, back) canvases."""
    fr = np.zeros((H, W), np.uint8); bk = np.zeros((H, W), np.uint8)
    ct, sn = math.cos(tilt), math.sin(tilt)
    for (ri, th0, span, wd, br, sd) in disk_filaments(seed):
        th_ = th0 + omega * t * (ri / 1.5) ** -1.5
        th = np.linspace(th_, th_ + span, 44)
        jit = 1 + 0.045 * np.sin(th * 9 + sd % 97 + t * 3.1) + 0.03 * np.sin(th * 23 + sd % 31 - t * 5.3)
        rr = ri * rs * jit
        x = rr * np.cos(th); y = rr * np.sin(th) * incl
        X = cx + x * ct - y * sn; Y = cy + x * sn + y * ct
        near = np.sin(th) > 0
        v = int(255 * br)
        for sel, cv_ in ((near, fr), (~near, bk)):
            idx = np.nonzero(sel)[0]
            if len(idx) < 2: continue
            for run in np.split(idx, np.nonzero(np.diff(idx) > 1)[0] + 1):
                if len(run) > 1:
                    cv2.polylines(cv_, [np.stack([X[run], Y[run]], 1).astype(np.int32)], False, v, wd, cv2.LINE_AA)
        far = ~near                                                                          # the lensed image over the top
        idx = np.nonzero(far)[0]
        if len(idx) > 1:
            rl = rs * (1.10 + 0.22 * (ri - 1.5) / 1.9)
            phi = np.pi * (0.5 + 0.5 * np.cos(th[idx]))                                    # left..right over the top
            xl = cx - rl * np.cos(phi); yl = cy - rl * np.sin(phi) * 0.98
            for run in np.split(np.arange(len(idx)), np.nonzero(np.diff(idx) > 1)[0] + 1):
                if len(run) > 1:
                    cv2.polylines(fr, [np.stack([xl[run], yl[run]], 1).astype(np.int32)], False, int(v * 0.85), max(1, wd - 1), cv2.LINE_AA)
                    yb = cy + rl * 0.92 * np.abs(np.sin(phi[run]))
                    cv2.polylines(fr, [np.stack([xl[run], yb], 1).astype(np.int32)], False, int(v * 0.35), 1, cv2.LINE_AA)
    return fr, bk

_DOP = {}
def doppler_row(cx, rs):
    key = (int(cx) // 4, int(rs) // 4)
    if key not in _DOP:
        if len(_DOP) > 64: _DOP.clear()
        u = np.clip((np.arange(W, dtype=F32) - cx) / (3.4 * max(rs, 10)), -1, 1)            # -1 approaching .. +1 receding
        b = (1.0 - 0.55 * u)[:, None]
        stops = np.array([-1.0, -0.15, 0.45, 1.0], F32); cols = np.stack([COOLW, HOT, AMB, RSH])  # smooth, no seam
        col = np.stack([np.interp(u, stops, cols[:, c]) for c in range(3)], 1)
        _DOP[key] = (col * b).astype(F32)[None]                                              # (1, W, 3)
    return _DOP[key]

def disk_light(cv, cx, rs, amt):
    lay = light_rgb(cv, amt, HOT, AMB)
    return lay * doppler_row(cx, rs)

def clean_plate(img, person):
    """the background without him (rule 5): his matte, dilated, inpainted at quarter resolution, so lensing the
    background never drags a copy of him around his own edge."""
    q = 4; m = cv2.resize(person, (W // q, H // q), interpolation=cv2.INTER_AREA)
    mk = (cv2.dilate((m > 0.25).astype(np.uint8), np.ones((9, 9), np.uint8)) * 255).astype(np.uint8)
    small = cv2.resize(np.clip(img, 0, 1), (W // q, H // q), interpolation=cv2.INTER_AREA)
    fill = cv2.inpaint((small * 255).astype(np.uint8), mk, 6, cv2.INPAINT_TELEA).astype(F32) / 255
    fill = cv2.resize(cv2.GaussianBlur(fill, (0, 0), 2), (W, H), interpolation=cv2.INTER_LINEAR)
    md = cv2.resize(cv2.GaussianBlur(mk.astype(F32) / 255, (0, 0), 1.5), (W, H))[..., None]
    return img * (1 - md) + fill * md

def bh_draw(img, cx, cy, rs, t, amt=1.0, spin=0.6, pull=0.0, person=None, disk=1.0, ring=1.0, lens=1.0, inner=None):
    """the whole singularity over img: lensing, the shadow, the photon ring, the accretion disk. With a person matte it
    sits behind him (his pixels stay unlensed and in front; the light wraps his edge). With inner, the shadow is a throat
    that shows another picture (the other side)."""
    if rs < 0.6: return img
    re = rs / SH_K
    src = clean_plate(img, person) if (person is not None and person.max() > 0.3 and (lens > 0 or pull)) else img
    o = bh_warp(src, cx, cy, re * lens, spin=spin, pull=pull)
    sh = 1.0 - disc_mask(cx, cy, rs, 1.2 + rs * 0.015)
    o = o * sh[..., None]
    if inner is not None: o = o + inner * (1 - sh)[..., None]
    pr = ring_mask(cx, cy, rs * 1.035, 1.0 + rs * 0.022, 2 if rs < 120 else 4)
    gl = ring_mask(cx, cy, rs * 1.15, rs * 0.16, 4)
    lay = np.zeros((H, W, 3), F32)
    addc(lay, pr, HOT, 0.95 * ring); addc(lay, gl, AMB, 0.30 * ring)
    if disk > 0:
        fr, bk = bh_disk(cx, cy, rs, t)
        bk = (bk.astype(F32) * sh).astype(np.uint8)
        lay += disk_light(np.maximum(fr, bk), cx, rs, 1.05 * disk)
    lay *= amt
    if person is not None:
        m = np.clip(person * 1.6 - 0.05, 0, 1)[..., None]
        o = o * (1 - m) + img * m
        return np.clip(o + behind(lay, np.clip(person * 1.6 - 0.05, 0, 1), 0.7), 0, 1)
    return np.clip(o + lay, 0, 1)

# ---- frame 0: the singularity at the core of the S1 vortex ---------------------------------------------------------
SKY_C = (W * 0.84, H * 0.10); SKY_RS = 56.0                                               # frame 0's hole = the loop's hole
HOLE_H = (W * 0.5, H * 0.12)                                                              # the horizon's hole, in the sky behind him
def sky_hole(out, f, k=1.0):
    t = f / FPS
    rs = SKY_RS * (1 + 0.03 * math.sin(2 * math.pi * t / (E.PHRASE * E.HB)))
    return bh_draw(out, SKY_C[0], SKY_C[1], rs * k, t, 1.0, spin=0.5)

# ---- the pull: motes of debris drifting up toward the hole (depth graphic, behind him) ----------------------------
_MOT = {}
def motes(n=150, seed=5):
    if seed not in _MOT:
        rng = np.random.default_rng(seed)
        _MOT[seed] = np.stack([rng.uniform(-0.1, 1.1, n), rng.uniform(0.35, 1.15, n), rng.uniform(0, 1, n),
                               rng.uniform(0.35, 1.0, n), rng.uniform(0.6, 1.6, n)], 1).astype(F32)
    return _MOT[seed]

def pull_fx(out, s, f, person, amt, target=(540.0, -260.0)):
    if s["n"] == "last": target = LOOP_H
    """the singularity's pull: debris motes stream up toward it (behind him), faster as they near it; they surge on the
    808 hits. A depth graphic with no sound."""
    t = f / FPS; e = t / E.HB; ph = (e - 8) % E.PHRASE
    surge = math.exp(-max(0.0, ph) * E.HB / 0.35) if ph < 4 else 0.0
    cv = np.zeros((H // 2, W // 2), np.uint8)
    for (x0, y0, p0, dep, sz) in motes():
        tau = (t * (0.16 + 0.10 * dep) * (1 + 0.6 * surge) + p0) % 1.0
        q = tau ** 1.7
        X = (x0 * W + (target[0] - x0 * W) * q) / 2; Y = (y0 * H + (target[1] - y0 * H) * q) / 2
        a = math.sin(math.pi * tau) * dep
        r = max(1, int(round(sz * (1.3 - 0.8 * q) * (1 + dep))))
        cv2.circle(cv, (int(X * 4), int(Y * 4)), r * 4, int(255 * a), -1, cv2.LINE_AA, shift=2)
    m = cv2.resize(cv2.GaussianBlur(cv.astype(F32) / 255, (0, 0), 0.8), (W, H))
    lay = np.zeros((H, W, 3), F32); addc(lay, m, HOT, 0.55 * amt); addc(lay, cv2.GaussianBlur(m, (0, 0), 5), AMB, 0.35 * amt)
    return np.clip(out + behind(lay, person, 0.0), 0, 1)

# ---- smoothness (v106 rule 5): flow on fast 30p shots. The engine holds the nearest frame when two source frames
# differ by more than 14 grey levels (mean, 1/8 res); fast shots (the vortex, the debris, the take-off) then judder at
# 30p. A shot may raise that limit (flowmax=) once its in-betweens have been checked for warping.
def src_weights(s, f):
    pk = s["src"]; fps = E.SRC[pk][1]; U = UNIQ[pk]
    t, u, sp = src_time(s, f); thr = s.get("flowmax", 14)
    def idx(tt, mode):
        kf = tt * fps; i = clamp(bisect.bisect_right(U, kf + 0.3) - 1, 0, len(U) - 1)
        if mode == "hold" or i >= len(U) - 1: return [(U[i], 1.0)]
        i0, i1 = U[i], U[i + 1]; a = clamp((kf - i0) / (i1 - i0), 0.0, 1.0)
        if a < 0.05: return [(i0, 1.0)]
        if a > 0.95: return [(i1, 1.0)]
        if mode == "blend": return [(i0, 1 - a), (i1, a)]
        A0, A1 = FR[(pk, i0)], FR[(pk, i1)]
        if np.abs(A0[::8, ::8].astype(np.float32) - A1[::8, ::8]).mean() > thr:
            if s.get("flowfall") == "blend": return [(i0, 1 - a), (i1, a)]                    # a lightning jump: cross-fade, never warp
            return [(i0 if a < 0.5 else i1, 1.0)]
        m0, m1 = A0[::8, ::8].mean(axis=(0, 1)), A1[::8, ::8].mean(axis=(0, 1))
        if np.abs(m0.astype(np.float32) - m1).max() > 6: return [(i0, 1 - a), (i1, a)]
        return [("flow", i0, i1, a)]
    if sp > 1.7:
        K = int(min(7, max(3, round(sp * 2)))); span = 0.5 / FPS * sp; out_ = []
        for j in range(K):
            out_ += [(k, w / K) for k, w in idx(t + (j / (K - 1) - 0.5) * span, "hold")]
        return out_, t, u
    return idx(t, s.get("interp", "hold")), t, u

# ---- transitions ------------------------------------------------------------------------------------------------
LOOP_H = SKY_C                                                                            # the loop's hole, above-left of his head
LD_PATH = {                                                    # (start x, y, rs), (cut x, y, rs), (end x, y, rs)
    "pull": ((SKY_C[0], SKY_C[1], SKY_RS), (W * 0.50, H * 0.40, 360.0), (W * 0.62, -260.0, 0.0)),   # the sky's own hole
    "last": ((W + 160.0, -160.0, 30.0), (W * 0.70, H * 0.17, 330.0), (LOOP_H[0], LOOP_H[1], 20.0)),  # becomes the loop's hole
}
def lens_drop(A, B, j, f, sa, sb, pre=12, post=14):
    """LENS DROP: a singularity moves into the frame; inside its Einstein ring the lensed light shows the next shot (what
    lies behind it); it fills the frame on the cut, then hands over to the next shot's own hole (or leaves). The hole is
    continuous with the shots' own singularities on both sides."""
    t = f / FPS
    (x0, y0, r0), (xm, ym, rm), (x1, y1, r1) = LD_PATH.get(sb["n"], ((W * 0.5, -200.0, 30.0), (W * 0.5, H * 0.4, 360.0), (W * 0.5, H + 300.0, 0.0)))
    if j < 0:
        u = (j + pre) / pre; w = eout(u, 2.0)
        cx, cy = x0 + (xm - x0) * w, y0 + (ym - y0) * w; rs = r0 + (rm - r0) * ein(u, 2.0)
        re = rs / SH_K
        LA = bh_warp(A, cx, cy, re, spin=0.5); LB = bh_warp(B, cx, cy, re, spin=0.5)
        d = np.sqrt((_GX - cx) ** 2 + (_GY - cy) ** 2)
        m = np.clip((1.75 * re - d) / (0.7 * re + 1e-3), 0, 1)                             # the ring shows what is behind
        o = mixm(LA, LB, m * m * (3 - 2 * m))
        return bh_draw(o, cx, cy, rs, t, 1.0, spin=0.0, lens=0.0)
    v = (j + 1) / post; w = smooth(v)
    cx, cy = xm + (x1 - xm) * w, ym + (y1 - ym) * w; rs = rm + (r1 - rm) * eout(v, 1.8)
    if v >= 1 or rs < 0.8: return B
    fade = 1 - smooth((v - 0.7) / 0.3) if r1 > 0 else 1.0                                   # hand over to the shot's hole
    return bh_draw(B, cx, cy, rs, t, fade, spin=0.5 * fade, lens=fade)

def frame_drag(A, B, j, f, sa, sb, pre=8, post=10):
    """FRAME DRAG: a spinning mass below his chin twists the frame around it (Lense-Thirring); the next shot unwinds."""
    P = (W * 0.5, H * 0.80)
    if j < 0: u = (j + pre) / pre; img, a = A, 2.6 * ein(u, 2.0)
    else: v = (j + 1) / post; img, a = B, -2.6 * (1 - eout(v, 2.2))
    if j in (-1, 0):
        img = mixm(A, B, np.full((H, W), 0.5, F32))
    dx = _GX - P[0]; dy = _GY - P[1]; r = np.sqrt(dx * dx + dy * dy)
    ang = a * np.exp(-r / 520.0); ca, sa_ = np.cos(ang), np.sin(ang)
    mx = (P[0] + dx * ca - dy * sa_).astype(F32); my = (P[1] + dx * sa_ + dy * ca).astype(F32)
    o = cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    k = abs(a) / 2.6
    return np.clip(o + light_rgb((ring_mask(P[0], P[1], 26, 4) * 255 * k).astype(np.uint8), 0.6 * k, HOT, AMB), 0, 1)

def redshift_tr(A, B, j, f, sa, sb, pre=8, post=10):
    """REDSHIFT: the light is stretched toward the hole and loses energy (red, dim); the next shot arrives blue-shifted
    and relaxes."""
    P = (W * 0.5, H * 0.30)
    if j < 0:
        u = (j + pre) / pre; o = radial_blur(A, P[0], P[1], 1.0, 1.0 + 0.30 * ein(u, 2.0), 6)
        return np.clip(redshift_px(o, 0.85 * ein(u, 1.5)), 0, 1)
    v = (j + 1) / post; o = radial_blur(B, P[0], P[1], 1.0 + 0.22 * (1 - eout(v, 2.0)), 1.0, 6)
    k = 0.6 * (1 - eout(v, 2.0)); L = lum8(o)
    for c, tc in enumerate((1.25, 1.05, 0.80)): o[..., c] = o[..., c] * (1 - k * 0.5) + L * tc * k * 0.5
    return np.clip(o, 0, 1)

def photon_ring_tr(A, B, j, f, sa, sb, pre=10, post=12):
    """PHOTON RING: the frame's light falls into orbit: the picture curls into a ring around a small hole (the image
    wrapped once round it), turns, and the next shot unwinds out of the ring."""
    C = (W * 0.5, H * 0.10); R1, R2 = 120.0, 1850.0                                          # above his head, never on his face
    if j < 0: u = (j + pre) / pre; img, w = A, ein(u, 1.8); rot = 1.4 * ein(u, 2.0)
    else: v = (j + 1) / post; img, w = B, 1 - eout(v, 2.0); rot = -1.4 * (1 - eout(v, 2.0))
    dx = _GX - C[0]; dy = _GY - C[1]; r = np.sqrt(dx * dx + dy * dy); phi = np.arctan2(dy, dx)
    q = ((phi + math.pi + rot) / math.pi) % 2.0; xs = (1.0 - np.abs(q - 1.0)) * W            # mirrored: no seam
    ys = np.clip((r - R1) / (R2 - R1), 0, 1) * H
    mx = (_GX + (xs - _GX) * w).astype(F32); my = (_GY + (ys - _GY) * w).astype(F32)
    o = cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    k = clamp((w - 0.6) / 0.4, 0, 1); rs = 110 * smooth(k)                                     # only while the frame is curled
    return bh_draw(o, C[0], C[1], rs, f / FPS, 0.9 * k, spin=0.0, lens=0.6) if rs > 2 else o

EYE_P = (487.0, 747.0)
def eye_pos(s, f):
    x, y, sc = to_screen(s, f, 310.0, 280.0); return x, y

def throat_in(B, cx, cy, sc):
    """the next shot as seen through the throat: scaled by sc about its centre and placed at (cx, cy), darkened at the
    rim (the light climbing out of the well)."""
    sc = max(sc, 1.0 + max(abs(cx - W / 2) / (W / 2), abs(cy - H / 2) / (H / 2)))         # always covers the frame
    M = np.float32([[sc, 0, cx - sc * W / 2], [0, sc, cy - sc * H / 2]])
    return cv2.warpAffine(B, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def eye_horizon(A, B, j, f, sa, sb, pre=14, post=14):
    """EYE HORIZON: his pupil becomes the singularity: it grows, wraps the orange iris into an Einstein ring around its
    shadow and swallows the frame; we come out the other side as the hole shrinks open onto the take-off."""
    t = f / FPS
    if j < 0:
        u = (j + pre) / pre; px, py = eye_pos(sa, f)
        Z = 1 + 0.6 * ein(u, 2.2); A2 = zoom_about(A, px, py, Z)
        rs = 14 + 560 * ein(u, 2.6)
        inner = throat_in(B, px, py, 1.6 - 0.2 * u) if u > 0.4 else None
        return bh_draw(A2, px, py, rs, t, 0.9, spin=0.9, inner=inner)
    v = (j + 1) / post; px, py = eye_pos(sa, sa["f1"] - 1)
    cx, cy = px + (W / 2 - px) * smooth(v), py + (H / 2 - py) * smooth(v)
    rs = 574 + 1700 * ein(v, 1.7)
    A2 = zoom_about(A, px, py, 1.6 * (1 + 0.5 * v))
    return bh_draw(A2, cx, cy, rs, t, 0.9 * (1 - v), spin=0.9 * (1 - v), inner=throat_in(B, cx, cy, 1.4 - 0.4 * eout(v, 1.8)))

def accretion_whip(A, B, j, f, sa, sb, pre=6, post=8):
    """ACCRETION WHIP: the camera passes through the plane of the disk: a sheet of lightning sweeps down the frame with a
    vertical whip; the next shot is on the other side of it."""
    if j < 0: u = (j + pre) / pre; y = -80 + (H * 0.5 + 80) * ein(u, 1.6); img = hblur(A, 2 + 90 * ein(u, 2), vertical=True)
    else: v = (j + 1) / post; y = H * 0.5 + (H * 0.5 + 120) * eout(v, 1.6); img = hblur(B, 2 + 80 * (1 - eout(v, 2)), vertical=True)
    cv = np.zeros((H, W), np.uint8); rng = np.random.default_rng(f // 2)
    for i in range(14):
        yy = y + rng.normal(0, 18); x0 = rng.uniform(-200, W); L_ = rng.uniform(300, 900)
        xs = np.linspace(x0, x0 + L_, 30); ys = yy + np.cumsum(rng.normal(0, 3, 30))
        cv2.polylines(cv, [np.stack([xs, ys], 1).astype(np.int32)], False, int(rng.uniform(140, 255)), int(rng.integers(1, 4)), cv2.LINE_AA)
    band = np.exp(-((_GY[:, :1] - y) / 60.0) ** 2)
    lay = disk_light(cv, W / 2, 300, 1.0); addc(lay, np.repeat(band, W, 1), AMB, 0.25)
    return np.clip(img + lay, 0, 1)

def grav_wave(A, B, j, f, sa, sb, pre=10, post=24):
    """GRAV WAVE (the breakout): the collapse pulls the frame into a point, then a gravitational wave rings out: rings of
    quadrupole strain (stretched one way, squeezed the other) race outward with the next shot behind the wavefront."""
    C = HOLE_H; t = clock13(f / FPS / E.HB)
    if j < 0:
        u = (j + pre) / pre
        o = bh_warp(A, C[0], C[1], 40 + 160 * ein(u, 2), spin=1.0 * u, pull=0.7 * ein(u, 2.5))
        return np.clip(o * (1 - 0.40 * ein(u, 2)), 0, 1)
    v = (j + 1) / post; dx = _GX - C[0]; dy = _GY - C[1]; r = np.sqrt(dx * dx + dy * dy) + 1
    R = 60 + 2300 * eout(v, 1.7); h = np.zeros_like(r)
    for i in range(3):
        Ri = R - i * 260
        h += np.exp(-((r - Ri) / 70.0) ** 2) * np.sin((r - Ri) / 38.0) * (0.75 ** i)
    h *= 0.035 * (1 - v) ** 0.8
    c2 = (dx * dx - dy * dy) / (r * r)                                                       # quadrupole pattern cos 2phi
    mx = (_GX + dx * h * (1 + c2)).astype(F32); my = (_GY + dy * h * (1 - c2)).astype(F32)
    front = np.clip((R - r) / 80.0, 0, 1)
    src = mixm(A * 0.4, B, front)
    o = cv2.remap(src, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    rim = np.exp(-((r - R) / 14.0) ** 2) * (1 - v) ** 1.5
    lay = np.zeros((H, W, 3), F32); addc(lay, rim, HOT, 0.9); addc(lay, np.exp(-((r - R) / 90.0) ** 2) * (1 - v) ** 2, AMB, 0.35)
    flash = 0.5 * math.exp(-(j + 1) / 2.5)
    return np.clip(o + lay + flash * AMB[None, None] * 0.4, 0, 1)

def spaghettify(A, B, j, f, sa, sb, pre=10, post=12):
    """SPAGHETTIFY: the tidal pull stretches the frame into long streams spiralling into a point; the next shot spirals
    back out of it."""
    P = (W * 0.80, H * 0.11)                                                                  # off his face, top right
    if j < 0: u = (j + pre) / pre; img, s_, tw = A, 0.85 * ein(u, 2.0), 1.6 * ein(u, 2.0)
    else: v = (j + 1) / post; img, s_, tw = B, 0.85 * (1 - eout(v, 2.0)), -1.6 * (1 - eout(v, 2.0))
    dx = _GX - P[0]; dy = _GY - P[1]; r = np.sqrt(dx * dx + dy * dy) + 1
    acc = None
    for i in range(5):
        k = 1.0 + s_ * (0.6 + 0.15 * i) * np.exp(-r / 1400.0)
        a = tw * np.exp(-r / 600.0) * (1 + 0.05 * i); ca, sa_ = np.cos(a), np.sin(a)
        mx = (P[0] + (dx * ca - dy * sa_) * k).astype(F32); my = (P[1] + (dx * sa_ + dy * ca) * k).astype(F32)
        w_ = cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        acc = w_ if acc is None else acc + w_
    o = acc / 5
    rs = 30 + 90 * s_
    return bh_draw(o, P[0], P[1], rs, f / FPS, s_, spin=0.0, lens=0.3)

def emblem_horizon(A, B, j, f, sa, sb, pre=14, post=14):
    """EMBLEM HORIZON: on the real tracked chest emblem: the camera pushes in, a singularity is born in the emblem's
    centre, the gold bolt and the suit wrap into an Einstein ring round its shadow, it swallows the frame, and the next
    shot opens out of it."""
    t = f / FPS
    if j < 0:
        u = (j + pre) / pre; ex, ey, er = emblem_at(sa, f)
        Z = 1 + 0.9 * ein(u, 2.2); A2 = zoom_about(A, ex, ey, Z)
        rs = 4 + (er * Z * 0.55) * ein(u, 1.4) + 420 * ein(max(0.0, (u - 0.5) / 0.5), 2.4)
        inner = throat_in(B, ex, ey, 1.6 - 0.2 * u) if u > 0.5 else None
        return bh_draw(A2, ex, ey, rs, t, 0.9 * u, spin=1.0, inner=inner)
    ex, ey, er = emblem_at(sa, sa["f1"] - 1); Z = 1.9
    rs0 = 4 + er * Z * 0.55 + 420
    v = (j + 1) / post; cx, cy = ex + (W / 2 - ex) * smooth(v), ey + (H / 2 - ey) * smooth(v)
    rs = rs0 + 1800 * ein(v, 1.7)
    A2 = zoom_about(A, ex, ey, Z * (1 + 0.5 * v))
    return bh_draw(A2, cx, cy, rs, t, 0.9 * (1 - v), spin=1.0 * (1 - v), inner=throat_in(B, cx, cy, 1.4 - 0.4 * eout(v, 1.8)))

def event_horizon_tr(A, B, j, f, sa, sb, pre=12, post=14):
    """EVENT HORIZON (the cut into the frozen moment): the darling shot is drawn into the mass just out of frame (the
    picture streams and twists into the top-left corner and dims); the airfield opens out of the same pull with the
    singularity already behind him."""
    P = (-140.0, -160.0)
    if j < 0:
        u = (j + pre) / pre
        o = bh_warp(A, P[0], P[1], 520 + 900 * ein(u, 2.2), spin=0.4 + 1.6 * ein(u, 2.0), pull=0.6 * ein(u, 2.4))
        return np.clip(redshift_px(o, 0.75 + 0.2 * u) * (1 - 0.35 * ein(u, 2)), 0, 1)
    v = (j + 1) / post; k = 1 - eout(v, 2.2)
    o = bh_warp(B, P[0], P[1], 1420 * k, spin=2.0 * k, pull=0.6 * k)
    return np.clip(o * (1 - 0.35 * k), 0, 1)

def slipstream(A, B, j, f, sa, sb, pre=8, post=12):
    """SLIPSTREAM: he is gone; the air he leaves behind drags the frame sideways in a long motion blur along a thin trail
    of his light, and Iris is standing in it."""
    if j < 0: u = (j + pre) / pre; img = A; L = 4 + 140 * ein(u, 2.0); dx = -60 * ein(u, 2.0)
    else: v = (j + 1) / post; img = B; L = 4 + 120 * (1 - eout(v, 2.0)); dx = 50 * (1 - eout(v, 2.0))
    o = hblur(cv2.warpAffine(img, np.float32([[1, 0, dx], [0, 1, 0]]), (W, H), borderMode=cv2.BORDER_REFLECT), L)
    k = ein((j + pre) / pre, 1.5) if j < 0 else (1 - eout((j + 1) / post, 1.6))
    y = H * 0.56 + 40 * math.sin(f * 0.3); cv = np.zeros((H, W), np.uint8)
    xs = np.linspace(-50, W + 50, 40); ys = y + 6 * np.sin(xs / 90.0 + f * 0.5)
    cv2.polylines(cv, [np.stack([xs, ys], 1).astype(np.int32)], False, 255, 2, cv2.LINE_AA)
    return np.clip(o + light_rgb(cv, 0.55 * k, HOT, AMB) * doppler_row(W / 2, 300), 0, 1)

TR2.update({"lens_drop": (lens_drop, 12, 14), "event_horizon": (event_horizon_tr, 12, 14), "frame_drag": (frame_drag, 8, 10), "redshift": (redshift_tr, 8, 10),
            "photon_ring": (photon_ring_tr, 10, 12), "eye_horizon": (eye_horizon, 14, 14), "accretion_whip": (accretion_whip, 6, 8),
            "grav_wave": (grav_wave, 10, 24), "spaghettify": (spaghettify, 10, 12), "emblem_horizon": (emblem_horizon, 14, 14),
            "slipstream": (slipstream, 8, 12)})

# ---- THE EVENT HORIZON (focal set piece, e48-e64): Darling, time dilates and stops, the collapse ------------------
def clock13(e):
    """time at the horizon: the clock runs until e56, slows to a stop at e60 (the song's deepest rest), stays stopped."""
    if e <= 56: return e * E.HB
    x = clamp((e - 56) / 4.0, 0, 1)
    return E.HB * (56 + 4.0 / 2.5 * (1 - (1 - x) ** 2.5))

def horizon_fx(out, s, f, person):
    """darling (e48-e56): from "Darling," (e49.6) a singularity grows behind him (behind his matte), the background is
    lensed toward it and redshifts as his clock slows to a stop. horizon (e56-e64): inside, the hole is huge behind him,
    the disk lightning slows and freezes in the rest (e60-e62), then everything collapses into it (e62-e64)."""
    t = f / FPS; e = t / E.HB
    if s["n"] == "darling":
        u = clamp((e - 49.6) / 6.4, 0, 1)
        if u <= 0: return out
        src = clean_plate(out, person) if (person is not None and person.max() > 0.3) else out
        bg = bh_warp(src, -140.0, -160.0, 520 * ein(u, 1.4), spin=0.4 * u)                   # something huge, just out of frame
        if person is not None:
            m = np.clip(person * 1.15, 0, 1)[..., None]; bg = bg * (1 - m) + out * m
        return np.clip(redshift_px(bg, 0.75 * ein(u, 1.3)), 0, 1)
    # inside the horizon
    cx, cy = HOLE_H
    tf = clock13(e)                                                                           # the disk's clock stops
    rs = 230 * eout(clamp((e - 56) / 1.6, 0, 1), 2.0) + 30 * smooth((e - 57) / 3)          # it grows in behind him
    k = 1.0
    if e >= 62: k = 1 - ein((e - 62) / 2.0, 1.4); rs = rs * (0.25 + 0.75 * k)
    o = bh_draw(out, cx, cy, rs, tf, 1.0, spin=0.6, pull=0.15 * (1 - k) + 0.05, person=person, lens=0.55)
    return np.clip(redshift_px(o, 0.55 + 0.25 * (1 - k)), 0, 1)

# ---- the camera: a 69 BPM feel; it moves on the 808 hits and rests in the set pieces -------------------------------
def beat_phase(f):
    e = f / FPS / E.HB; ph = (e % 4) * E.HB; bi = int(e // 4)
    rest = (E.E_DARLING <= e < E.HDROP + 2) or e >= E.E_LOOP
    hook = (e >= 4) and not rest and (e % E.PHRASE) >= 8 and (e % E.PHRASE) < 12              # the 808 hit
    rival = (e >= 4) and not rest and not hook
    return ph, bi, hook, rival

def beat_bounce(f):
    ph, bi, hook, rival = beat_phase(f)
    if hook: return 1 + 0.032 * math.exp(-ph / 0.12)
    if rival: return 1 + 0.010 * math.exp(-ph / 0.10)
    return 1.0

def beat_fx(out, f):
    ph, bi, hook, rival = beat_phase(f)
    if not hook or ph > 0.05: return out
    k = math.exp(-ph / 0.02)
    return np.clip(rgb_split(radial_blur(out, W / 2, H * 0.46, 1.0, 1.0 + 0.025 * k, 4), 5 * k), 0, 1)

def init_hits():
    HITS.clear(); HITS.append((E.fh(E.HDROP), 18, 4.5))

# ---- the loop: he looks up into it; we fall in; frame 0 comes out of its Einstein ring -----------------------------
LOOP_K0 = 30                                                                               # frames into "last" when the fall starts
_Z0_13 = {}
def frame0_pre():
    if "z" not in _Z0_13: _Z0_13["z"] = prefinish(0)
    return _Z0_13["z"]

def frame_virtual(fv):
    """frame 0's shot at a virtual frame before the wrap (fv < 0): the footage holds its first frame, the singularity
    keeps turning, so the fall lands on a picture that is already moving into frame 0 (v106 rule 7)."""
    s0 = SHOTS[0]; out, _ = base13(s0, fv)
    return np.clip(beat_fx(out, fv), 0, 1)

def loop_fall(out, f, s, person):
    """the last shot: the singularity grows top-left where he is looking, pulls the frame (lensing and twist), and the
    camera falls into it; frame 0 (the hole at the vortex core) appears inside its Einstein ring and reaches scale 1.0 on
    the last frame, with its own hole exactly where frame 0's is."""
    k = f - s["f0"]; n = s["f1"] - s["f0"]; t = f / FPS
    u0 = clamp(k / LOOP_K0, 0, 1)
    hx, hy = LOOP_H
    if k < LOOP_K0:
        rs = 20 + 52 * ein(u0, 1.5)
        return bh_draw(out, hx, hy, rs, t, u0, spin=0.6, pull=0.05 * u0, person=person)
    u = (k - LOOP_K0) / max(1, n - 1 - LOOP_K0)                                              # 0..1, 1 = last frame
    if u >= 1: return frame_virtual(f - E.DUR_F)
    z = math.exp(math.log(7.0) * ein(u, 1.6))                                                # the fall toward the hole
    o = zoom_about(out, hx, hy, z, 28 * ein(u, 2.0))                                         # falling in, turning with the drag
    o = radial_blur(o, hx, hy, 1.0, 1.0 + 0.14 * ein(u, 1.3), 5) if u > 0.12 else o
    rs = 72 * (1 - u) + SKY_RS * u
    pz = zoom_about(person, hx, hy, z, 28 * ein(u, 2.0)) if person is not None else None   # it stays behind him
    o = bh_draw(o, hx, hy, rs * (1 + 0.8 * math.sin(math.pi * u)), t, 1.0, spin=1.0 * (1 - u), lens=1 - u, person=pz)
    Z0 = frame_virtual(f - E.DUR_F)
    zi = 1.0 + 0.6 * (1 - eout(u, 2.0))                                                       # the other side, settling to 1.0
    inner = zoom_about(Z0, SKY_C[0], SKY_C[1], zi, -12 * (1 - eout(u, 2.0)))
    R_ = (rs / SH_K) * (1.0 + 18 * ein(u, 2.4))
    ap = np.clip((R_ - np.sqrt((_GX - hx) ** 2 + (_GY - hy) ** 2)) / (60 + 200 * (1 - u)), 0, 1)
    wm = np.clip(ap * (0.35 + 0.65 * u) + ein(u, 5), 0, 1)
    if pz is not None:                                                                       # he stays in front until halfway
        wm = wm * (1 - np.clip(pz * 1.6 - 0.05, 0, 1) * clamp((0.75 - u) / 0.25, 0, 1))
    return np.clip(mixm(o, inner, wm), 0, 1)

def loop_in13(out, f, k):
    return out                                                                               # frame 0 carries straight on

# ---- the frame ------------------------------------------------------------------------------------------------------
def base13(s, f):
    img, person = base11(s, f)
    orig = img
    if s["n"] == "sky" and f < s["f1"] - 12: img = sky_hole(img, f)                         # the lens drop carries it after
    if s["n"] in ("pull", "god", "last"): img = face_guard(orig, pull_fx(img, s, f, person, 0.9), s, f)
    if s["n"] in ("darling", "horizon"): img = horizon_fx(img, s, f, person)
    if s["n"] == "last": img = loop_fall(img, f, s, person)
    return img, person

_B13 = {}
def edge13(S_, which):
    key = (S_["n"], which)
    if key not in _B13:
        if len(_B13) > 6: _B13.clear()
        _B13[key] = base13(S_, S_["f0"] if which == "first" else S_["f1"] - 1)[0]
    return _B13[key]

def prefinish(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin")
    out, person = base13(s, f)
    if tin in TR2 and k < TR2[tin][2] and P is not None:
        out = TR2[tin][0](edge13(P, "last"), out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, edge13(n_, "first"), kn, f, s, n_)
    out = beat_fx(out, f)
    return np.clip(out, 0, 1)

def render(f):
    s = shot_at(f); out = flash_governor(prefinish(f))
    fin_s = SHOTS[0] if (s["n"] == "last" and f >= s["f1"] - 1) else s
    return (np.clip(finish13(out, f, fin_s), 0, 1) * 255 + 0.5).astype(np.uint8)

# ============================================================================ v13 rev 2: the singularity steps back
# Owner (rev 1): "I don't like that the singularity is the primary object in every transition and animation … make a
# emblem transition … more transitions that replace the previous singularity transitions … remove some of the tedious
# sound effects … create a really cool graphic that you use to turn into a transition … smooth out the rest". The
# singularity now appears once, in the "Darling," set piece (EVENT HORIZON -> GRAV WAVE). New:
#   LIGHT RIBBON (the hero graphic): his speed trail as a long-exposure light painting, a twisting ribbon of light that
#     orbits him in depth (behind his matte, in front of his chest), sheds sparks, then spirals outward with the next shot
#     inside its loop (the transition on "God"); it returns to carry the loop onto frame 0;
#   EMBLEM SPLIT (the emblem transition): on the real tracked chest emblem, its bolt ignites, leaps off at the camera and
#     the frame splits along the bolt's zigzag;
#   EDGE CURRENT, FOCUS RACK, SPEED WHIP, EYE IRIS, TIME SLICE, AFTERIMAGE, LIGHT LEAK, PANEL RUN (+ restyled bolt trace).
CRIM = np.array([0.16, 0.12, 0.78], np.float32)                                              # BGR crimson fringe

def shift_img(img, dx, dy=0.0):
    return cv2.warpAffine(img, np.float32([[1, 0, dx], [0, 1, dy]]), (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

# ---- LIGHT RIBBON -----------------------------------------------------------------------------------------------------
FOC = 1500.0
def ribbon_pts(t, cx, cy, R, tilt=0.34, speed=4.2, length=3.2, n=130, ph=0.0, open_=1.0):
    """the trail on a tilted orbit round (cx, cy): screen x, y, depth z (> 0 behind him), half-width, brightness."""
    L = length * clamp(open_, 0.02, 1.0)
    th = ph + speed * t - np.linspace(0, L, n)                                               # head .. tail
    x = R * np.cos(th); z = R * np.sin(th); y = -R * tilt * np.sin(th) + 0.06 * R * np.sin(2.3 * th + 0.7)
    sc = FOC / np.maximum(FOC + z, 120.0)
    X, Y = cx + x * sc, cy + y * sc
    s = np.linspace(0, 1, n)
    face = 0.30 + 0.70 * np.abs(np.cos(1.7 * th + 2.1 * t))                                  # the ribbon turns as it flies
    hw = (2 + 52 * (1 - s) ** 0.7) * sc * (0.30 + 0.70 * face)
    br = (1 - s) ** 1.25 * (0.55 + 0.45 * face)
    return X, Y, z, hw, br

def ribbon_canvas(X, Y, z, hw, br, front):
    cv = np.zeros((H, W), np.uint8)
    dx = np.gradient(X); dy = np.gradient(Y); nn = np.sqrt(dx * dx + dy * dy) + 1e-6
    nx, ny = -dy / nn, dx / nn
    for i in range(len(X) - 1):
        if (z[i] < 0) != front: continue
        a0 = (X[i] + nx[i] * hw[i], Y[i] + ny[i] * hw[i]); a1 = (X[i + 1] + nx[i + 1] * hw[i + 1], Y[i + 1] + ny[i + 1] * hw[i + 1])
        b1 = (X[i + 1] - nx[i + 1] * hw[i + 1], Y[i + 1] - ny[i + 1] * hw[i + 1]); b0 = (X[i] - nx[i] * hw[i], Y[i] - ny[i] * hw[i])
        cv2.fillConvexPoly(cv, (np.array([a0, a1, b1, b0]) * 4).astype(np.int32), int(255 * br[i]), cv2.LINE_AA, shift=2)
    return cv

def ribbon_light(cv, amt):
    if amt <= 0 or cv.max() == 0: return np.zeros((H, W, 3), F32)
    lay = light_rgb(cv, amt, HOT, AMB)
    q = cv2.resize(cv.astype(F32) / 255, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    fr = cv2.resize(cv2.GaussianBlur(q, (0, 0), 7), (W, H))
    addc(lay, fr, CRIM, 0.55 * amt)                                                          # a crimson fringe (the suit's light)
    return lay

def ribbon_sparks(t, cx, cy, R, amt, ph=0.0, speed=4.2, n=34):
    cv = np.zeros((H // 2, W // 2), np.uint8)
    for i in range(n):
        tb = t - (i / n) * 0.55                                                               # birth time
        age = t - tb
        X, Y, z, _, _ = ribbon_pts(tb, cx, cy, R, speed=speed, length=0.02, n=2, ph=ph)
        rng = np.random.default_rng(i * 977 + int(tb * 7))
        vx, vy = rng.normal(0, 90), rng.normal(-40, 70)
        px = X[0] + vx * age; py = Y[0] + vy * age + 260 * age * age
        a = (1 - age / 0.55) ** 1.5
        cv2.circle(cv, (int(px * 2), int(py * 2)), 4, int(255 * a), -1, cv2.LINE_AA, shift=2)
    m = cv2.resize(cv, (W, H), interpolation=cv2.INTER_LINEAR)
    return light_rgb(m, 0.8 * amt, HOT, AMB)

def ribbon_draw(out, t, cx, cy, R, person=None, amt=1.15, open_=1.0, tilt=0.50, sparks=True, ph=0.0):
    cb = np.zeros((H, W), np.uint8); cf = np.zeros((H, W), np.uint8)
    for (dph, kR, kw, kt) in ((0.0, 1.0, 1.0, 1.0), (math.pi * 0.85, 0.86, 0.55, -0.7)):    # two strands, intertwined
        X, Y, z, hw, br = ribbon_pts(t, cx, cy, R * kR, tilt=tilt * kt, open_=open_, ph=ph + dph)
        hw = hw * kw; br = br * (1.0 if kw == 1.0 else 0.75)
        cb = np.maximum(cb, ribbon_canvas(X, Y, z, hw, br, False)); cf = np.maximum(cf, ribbon_canvas(X, Y, z, hw, br, True))
    X, Y, z, hw, br = ribbon_pts(t, cx, cy, R, tilt=tilt, open_=open_, ph=ph)                # a current crackles along it
    for seg in range(0, len(X) - 12, 12):
        tgt = cf if z[seg] < 0 else cb
        put_bolt(tgt, (X[seg], Y[seg]), (X[seg + 12], Y[seg + 12]), 9400 + seg + 3 * (int(t * FPS) // 2), 1, 0.45, 4, 0, val=int(230 * br[seg]))
    back = ribbon_light(cb, amt); front = ribbon_light(cf, amt)
    o = out + (behind(back, np.clip(person * 1.5, 0, 1), 0.6) if person is not None else back) + front
    if sparks: o = o + ribbon_sparks(t, cx, cy, R, amt, ph=ph)
    return np.clip(o, 0, 1)

RIB = {"blood": dict(c=(W * 0.50, H * 0.86), R=420.0), "last": dict(c=(W * 0.50, H * 0.84), R=420.0)}
RIB_PRE = 18
def ribbon_orbit(out, s, f, person):
    """the hero graphic in the shot that hosts it: the ribbon draws itself in round his chest and orbits him."""
    k = f - s["f0"]; n = s["f1"] - s["f0"]; p = RIB[s["n"]]
    if s["n"] == "blood" and k >= n - RIB_PRE: return out                                    # the transition carries it on
    return ribbon_draw(out, f / FPS, p["c"][0], p["c"][1], p["R"], person, open_=eout(k / 16.0, 2.0))

def ribbon_spiral(A, B, j, f, sa, sb, pre=RIB_PRE, post=14):
    """LIGHT RIBBON (the transition): the orbit flares and spirals outward toward the lens; the next shot is inside its
    loop (an ellipse that rounds into a circle as it opens), and the ribbon leaves past the frame edges."""
    p = RIB["blood"]; cx, cy = p["c"]; t = f / FPS
    q = (j + pre) / (pre + post)
    R = p["R"] * math.exp(math.log(9.0) * ein(q, 1.5)); tilt = 0.50 + 0.50 * smooth(q * 1.3)
    gx = (_GX - cx) / R; gy = (_GY - cy) / (R * max(tilt, 0.5) * 1.05)
    m = np.clip((1.0 - np.sqrt(gx * gx + gy * gy)) * R / 40.0, 0, 1) * smooth((q - 0.40) / 0.25)
    Bz = zoom_about(B, cx, cy, 1.0 + 0.25 * (1 - eout(q, 2.0)))
    o = mixm(A, Bz, m)
    person = PERSON.get(f) if j < 0 else None
    fade = 1.0 if j < 0 else 1 - smooth((j + 1) / (post * 0.45))                               # gone before it can linger on a face
    return ribbon_draw(o, t, cx, cy, R, person, (1.15 + 0.3 * math.sin(math.pi * q)) * fade, tilt=tilt, sparks=j < 0)

# ---- EMBLEM SPLIT (the emblem transition) ----------------------------------------------------------------------------
ZIG = np.array([(0.24, -0.5), (-0.05, -0.03), (0.10, 0.03), (-0.24, 0.5)], np.float32)     # the bolt's zigzag (top-right -> bottom-left)
def zig_pts(cx, cy, L, rot=0.0):
    c, s_ = math.cos(rot), math.sin(rot)
    return np.stack([cx + L * (ZIG[:, 0] * c - ZIG[:, 1] * s_), cy + L * (ZIG[:, 0] * s_ + ZIG[:, 1] * c)], 1)

def emblem_split(A, B, j, f, sa, sb, pre=16, post=14):
    """EMBLEM SPLIT: the camera pushes onto his real chest emblem; its bolt ignites (arcs crawl along it); the bolt leaps
    off at the camera, growing until its zigzag spans the frame, and the frame splits open along it onto the next shot."""
    t = f / FPS
    if j < 0:
        u = (j + pre) / pre; ex, ey, er = emblem_at(sa, f)
        Z = 1 + 0.55 * ein(u, 2.0); A2 = zoom_about(A, ex, ey, Z)
        lp = ein(clamp((u - 0.5) / 0.5, 0, 1), 2.4)                                          # the leap
        L = 2.1 * er * Z * (1 - lp) + 2.6 * H * lp; cx = ex + (W / 2 - ex) * lp; cy = ey + (H / 2 - ey) * lp
        pts = zig_pts(cx, cy, L, -0.08 * (1 - lp))
        cv = bolt_canvas()
        cv2.polylines(cv, [(pts * 4).astype(np.int32)], False, 255, max(2, int(L * 0.045)), cv2.LINE_AA, shift=2)
        for k in range(3):                                                                    # arcs crawling along the bolt
            i = k % 3; put_bolt(cv, pts[i], pts[i + 1], 9200 + k + 5 * (f // 2), 1, 0.35, 4, 0, val=200)
        return np.clip(A2 * (1 - 0.25 * lp) + light_rgb(cv, 0.35 + 0.9 * u, HOT, AMB), 0, 1)
    v = (j + 1) / post; ex, ey, er = emblem_at(sa, sa["f1"] - 1)
    A2 = zoom_about(A, ex, ey, 1.55)
    pts = zig_pts(W / 2, H / 2, 2.6 * H)
    d = pts[-1] - pts[0]; nrm = np.array([-d[1], d[0]], np.float32); nrm /= np.linalg.norm(nrm) + 1e-6
    if nrm[0] < 0: nrm = -nrm                                                                 # points to the right half
    g = 20 + 1300 * ein(v, 1.5)
    left = np.zeros((H, W), F32)
    poly = np.vstack([pts, [[-3000, pts[-1][1]], [-3000, pts[0][1]]]])
    cv2.fillPoly(left, [(poly * 4).astype(np.int32)], 1.0, cv2.LINE_AA, shift=2)
    Lh = shift_img(A2, -nrm[0] * g / 2, -nrm[1] * g / 2); Rh = shift_img(A2, nrm[0] * g / 2, nrm[1] * g / 2)
    sh0 = lambda m_, dx, dy: cv2.warpAffine(m_, np.float32([[1, 0, dx], [0, 1, dy]]), (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    mL = sh0(left, -nrm[0] * g / 2, -nrm[1] * g / 2)                                         # nothing reflected in from the edges
    mR = sh0(1 - left, nrm[0] * g / 2, nrm[1] * g / 2)
    mR = np.clip(mR, 0, 1 - mL)
    Bz = zoom_about(B, W / 2, H / 2, 1.0 + 0.12 * (1 - eout(v, 2.0)))
    o = Bz * (1 - mL - mR)[..., None] + Lh * mL[..., None] + Rh * mR[..., None]
    cv = bolt_canvas()
    for sh in (-1, 1):
        q_ = pts + nrm[None] * sh * g / 2
        cv2.polylines(cv, [(q_ * 4).astype(np.int32)], False, 255, 3, cv2.LINE_AA, shift=2)
    return np.clip(o + light_rgb(cv, 1.0 * (1 - v) ** 1.4, HOT, AMB), 0, 1)

# ---- EDGE CURRENT --------------------------------------------------------------------------------------------------
def edge_map(img):
    g = cv2.cvtColor((np.clip(img, 0, 1) * 255).astype(np.uint8), cv2.COLOR_BGR2GRAY)
    g = cv2.GaussianBlur(cv2.resize(g, (W // 2, H // 2), interpolation=cv2.INTER_AREA), (0, 0), 1.6)
    return cv2.resize(cv2.Canny(g, 38, 105), (W, H), interpolation=cv2.INTER_LINEAR)

_CUR = {}
def current_mask(f):
    """a crawling current: a fixed noise field scrolled smoothly (sub-pixel), thresholded into travelling pulses."""
    if "n" not in _CUR:
        rng = np.random.default_rng(31)
        _CUR["n"] = cv2.GaussianBlur(rng.random((H // 4 + 200, W // 4 + 200)).astype(F32), (0, 0), 6)
    nz = _CUR["n"]; off = (f * 1.7) % 180
    c = crop_frac13(nz, off, off * 0.6, H // 4, W // 4)
    c = (c - c.mean()) / (c.std() + 1e-6)
    return cv2.resize(np.clip(0.5 + 0.5 * np.sin(c * 5.0 + f * 0.35), 0, 1), (W, H))

def crop_frac13(c, oy, ox, h, w):
    M = np.float32([[1, 0, -ox], [0, 1, -oy]])
    return cv2.warpAffine(c, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def edge_current(A, B, j, f, sa, sb, pre=10, post=14):
    """EDGE CURRENT: the picture goes dark and its own outlines carry a crawling current; the outlines morph into the next
    shot's, which fills back in from them."""
    cur = 0.4 + 0.6 * current_mask(f)
    if j < 0:
        u = (j + pre) / pre; eA = edge_map(A).astype(F32)
        e = eA if u < 0.6 else eA * (1 - (u - 0.6) / 0.4) + edge_map(B).astype(F32) * ((u - 0.6) / 0.4)
        base = A * (1 - 0.82 * ein(u, 1.4)); amp = 1.25 * ein(u, 1.1)
    else:
        v = (j + 1) / post; e = edge_map(B).astype(F32)
        base = B * (0.18 + 0.82 * eout(v, 1.8)); amp = 1.25 * (1 - eout(v, 1.4))
    return np.clip(base + light_rgb(np.clip(e * cur, 0, 255).astype(np.uint8), amp, HOT, AMB), 0, 1)

# ---- FOCUS RACK ---------------------------------------------------------------------------------------------------
_DK = {}
def defocus(img, r):
    if r < 0.6: return img
    if r < 6: return cv2.GaussianBlur(img, (0, 0), r / 2)
    q = 4; sm = cv2.resize(img, (W // q, H // q), interpolation=cv2.INTER_AREA)
    sm = sm + np.clip(sm - 0.55, 0, 1) * 2.5                                                  # highlights bloom into bokeh discs
    rr = int(math.ceil(r / q))
    if rr not in _DK:
        k = np.zeros((2 * rr + 1, 2 * rr + 1), F32); cv2.circle(k, (rr, rr), rr, 1.0, -1, cv2.LINE_AA); _DK[rr] = k / k.sum()
    return np.clip(cv2.resize(cv2.filter2D(sm, -1, _DK[rr]), (W, H), interpolation=cv2.INTER_LINEAR), 0, 1)

def focus_rack(A, B, j, f, sa, sb, pre=10, post=12):
    """FOCUS RACK: the lens racks out until the frame is bokeh, the next shot is found in the blur, and the lens racks
    back in on it."""
    if j < 0:
        u = (j + pre) / pre; o = defocus(A, 54 * ein(u, 1.8))
        if j >= -2: o = mixm(o, defocus(B, 54), np.full((H, W), 0.5 if j == -2 else 0.75, F32))
        return o
    v = (j + 1) / post; return defocus(B, 54 * (1 - eout(v, 2.0)))

# ---- SPEED WHIP ---------------------------------------------------------------------------------------------------
def whip_up13(A, B, j, f, sa, sb, pre=6, post=8):
    """WHIP UP: a clean tilt-whip upward (he looks up) with real vertical motion blur and a thin vertical streak."""
    if j < 0: u = (j + pre) / pre; o = hblur(shift_img(A, 0, H * 0.45 * ein(u, 2.2)), 2 + 190 * ein(u, 2.0), vertical=True); k = ein(u, 1.5)
    else: v = (j + 1) / post; o = hblur(shift_img(B, 0, -H * 0.45 * (1 - eout(v, 2.2))), 2 + 170 * (1 - eout(v, 2.0)), vertical=True); k = 1 - eout(v, 1.6)
    band = np.exp(-((_GX[:1, :] - W * 0.86) / 4.0) ** 2) * k
    lay = np.zeros((H, W, 3), F32); addc(lay, np.repeat(band, H, 0), HOT, 0.7)
    return np.clip(o + lay, 0, 1)

def speed_whip(A, B, j, f, sa, sb, pre=5, post=7):
    """SPEED WHIP: a clean whip pan with real motion blur and one thin streak of his light along the move."""
    if j < 0: u = (j + pre) / pre; o = hblur(shift_img(A, -W * 0.55 * ein(u, 2.2)), 2 + 170 * ein(u, 2.0)); k = ein(u, 1.5)
    else: v = (j + 1) / post; o = hblur(shift_img(B, W * 0.55 * (1 - eout(v, 2.2))), 2 + 150 * (1 - eout(v, 2.0))); k = 1 - eout(v, 1.6)
    band = np.exp(-((_GY[:, :1] - H * 0.82) / 5.0) ** 2) * k                                  # at chest height, never the face
    lay = np.zeros((H, W, 3), F32); addc(lay, np.repeat(band, W, 1), HOT, 0.8); addc(lay, np.repeat(np.exp(-((_GY[:, :1] - H * 0.82) / 40.0) ** 2) * k, W, 1), AMB, 0.25)
    return np.clip(o + lay, 0, 1)

# ---- EYE IRIS -------------------------------------------------------------------------------------------------------
def light_ring(cx, cy, R, f, seed=0, w=3):
    cv = bolt_canvas(); th = np.linspace(0, 2 * math.pi, 180)
    rr = R * (1 + 0.025 * np.sin(th * 13 + f * 0.9 + seed) + 0.015 * np.sin(th * 31 - f * 1.7))
    cv2.polylines(cv, [(np.stack([cx + rr * np.cos(th), cy + rr * np.sin(th)], 1) * 4).astype(np.int32)], True, 255, w, cv2.LINE_AA, shift=2)
    return cv

def eye_iris(A, B, j, f, sa, sb, pre=12, post=14):
    """EYE IRIS: the lightning in his eye: arcs fork outward from the orange iris, then a ring of lightning opens from his
    pupil with the next shot inside it."""
    if j < 0:
        u = (j + pre) / pre; px, py = eye_pos(sa, f); Z = 1 + 0.45 * ein(u, 2.0); A2 = zoom_about(A, px, py, Z)
        Ri = 34 * Z; Lr = Ri + 560 * ein(u, 1.5); cv = bolt_canvas()
        for k in range(9):
            a = 2 * math.pi * k / 9 + 0.25 * math.sin(f * 0.07 + k)
            put_bolt(cv, (px + Ri * math.cos(a), py + Ri * math.sin(a)), (px + Lr * math.cos(a), py + Lr * math.sin(a)), 9300 + k + 9 * (f // 2), 2, 0.30, 5, 1)
        o = A2
        if u > 0.6:
            Rr = Ri * (1 + 5 * ein((u - 0.6) / 0.4, 2.0))
            m = disc_mask(px, py, Rr, 3); o = mixm(A2, zoom_about(B, px, py, 1.3), m)
            cv = np.maximum(cv, light_ring(px, py, Rr, f))
        return np.clip(o + light_rgb(cv, 0.4 + 0.7 * u, HOT, AMB), 0, 1)
    v = (j + 1) / post; px, py = eye_pos(sa, sa["f1"] - 1)
    cx, cy = px + (W / 2 - px) * smooth(v), py + (H / 2 - py) * smooth(v)
    Rr = 34 * 1.45 * 6 + 2300 * ein(v, 1.8)
    A2 = zoom_about(A, px, py, 1.45 * (1 + 0.4 * v))
    o = mixm(A2, zoom_about(B, cx, cy, 1.0 + 0.3 * (1 - eout(v, 2.0))), disc_mask(cx, cy, Rr, 3))
    return np.clip(o + light_rgb(light_ring(cx, cy, Rr, f, 3, 4), 1.0 * (1 - v) ** 1.2, HOT, AMB), 0, 1)

# ---- TIME SLICE -----------------------------------------------------------------------------------------------------
def time_slice(A, B, j, f, sa, sb, pre=8, post=12):
    """TIME SLICE: the frame comes apart into tall slivers that slide out one after another in a wave, each a moment
    later than its neighbour, and the next shot slides in behind them; gold seams between the slivers."""
    q = (j + pre) / (pre + post); n = 12; sw = W / n
    Ab = hblur(A, 60, vertical=True); Bb = hblur(B, 60, vertical=True)
    o = np.empty_like(A); seam = np.zeros((H, W), F32)
    for i in range(n):
        x0, x1 = int(i * sw), int((i + 1) * sw); d = 0.40 * i / (n - 1)
        p = eout(clamp((q - d) / 0.55, 0, 1), 2.4); sp = 4 * p * (1 - p)
        dy = int(-H * p) if i % 2 == 0 else int(H * p)
        Ai = (Ab if sp > 0.3 else A)[:, x0:x1]; Bi = (Bb if sp > 0.3 else B)[:, x0:x1]
        col = np.roll(np.concatenate([Ai, Bi], 0) if dy < 0 else np.concatenate([Bi, Ai], 0), dy, axis=0)
        o[:, x0:x1] = col[:H] if dy < 0 else col[H:]
        if 0 < p < 1: seam[:, max(0, x0 - 1):x0 + 2] = sp
    return np.clip(o + light_rgb((seam * 255).astype(np.uint8), 0.8, HOT, AMB), 0, 1)

# ---- AFTERIMAGE -----------------------------------------------------------------------------------------------------
def afterimage(A, B, j, f, sa, sb, pre=10, post=10):
    """AFTERIMAGE: the speedster leaves copies of himself behind: trailing afterimages tinted crimson to gold peel off
    him; the next shot arrives the same way, its copies collapsing into the figure."""
    m = PERSON.get(f)
    if j >= 0:                                                                               # only he leaves afterimages
        v = (j + 1) / post; return np.clip(mixm(A, B, np.full((H, W), smooth(v * 2.5), F32)), 0, 1)
    u = (j + pre) / pre; img = A; step = -90 * ein(u, 1.4); a0 = ein(u, 1.2)
    fig = img * (np.clip(m * 1.3, 0, 1)[..., None] if m is not None else 0.6)
    o = img.copy()
    for k in range(1, 5):
        c = shift_img(fig, step * k); w_ = 0.55 * a0 * (1 - k / 5)
        tint = CRIM * (1 - k / 4) + AMB * (k / 4)
        L = lum8(c); addc(o, L * w_, tint, 1.6)
    if j >= -3: o = mixm(o, B, np.full((H, W), (j + 4) / 4.0 * 0.5, F32))
    return np.clip(o, 0, 1)

# ---- LIGHT LEAK -----------------------------------------------------------------------------------------------------
def light_leak13(A, B, j, f, sa, sb, pre=10, post=12):
    """LIGHT LEAK: warm light floods in from the edge of the lens (film-camera light leak in the edit's amber), and the
    shots cross under the brightest moment."""
    q = (j + pre) / (pre + post); pk = math.sin(math.pi * q)
    mix = smooth((q - 0.35) / 0.30); o = A * (1 - mix) + B * mix
    q4 = np.zeros((H // 4, W // 4), F32)
    for (x0, y0, x1, y1, r, a) in ((-0.2, 0.15, 0.6, 0.35, 0.45, 1.0), (1.2, 0.75, 0.55, 0.55, 0.35, 0.7)):
        x = (x0 + (x1 - x0) * q) * W / 4; y = (y0 + (y1 - y0) * q) * H / 4
        cv2.circle(q4, (int(x), int(y)), int(r * W / 4), a, -1)
    lk = cv2.resize(cv2.GaussianBlur(q4, (0, 0), 40), (W, H))
    lay = np.zeros((H, W, 3), F32); addc(lay, lk, AMB, 0.85 * pk); addc(lay, lk ** 2, HOT, 0.5 * pk)
    return np.clip(o * (1 + 0.15 * pk) + lay, 0, 1)

# ---- PANEL RUN ------------------------------------------------------------------------------------------------------
def panel_run(A, B, j, f, sa, sb, pre=8, post=12):
    """PANEL RUN: the frame splits into three panels that run out in alternate directions, one after another, and the
    next shot runs in behind them; thin gold seams."""
    q = (j + pre) / (pre + post); n = 3; pw = W / n
    o = np.empty_like(A); seam = np.zeros((H, W), F32)
    for i in range(n):
        x0, x1 = int(i * pw), int((i + 1) * pw); p = eout(clamp((q - 0.12 * i) / 0.62, 0, 1), 2.6)
        d = 1 if i % 2 == 0 else -1; off = int(d * H * p); sp = 4 * p * (1 - p)
        Ai = hblur(A[:, x0:x1], 2 + 50 * sp, vertical=True) if sp > 0.2 else A[:, x0:x1]
        Bi = hblur(B[:, x0:x1], 2 + 50 * sp, vertical=True) if sp > 0.2 else B[:, x0:x1]
        st = np.concatenate([Ai, Bi], 0) if d < 0 else np.concatenate([Bi, Ai], 0)
        st = np.roll(st, off, axis=0); o[:, x0:x1] = st[:H] if d < 0 else st[H:]
        if 0 < p < 1 and i > 0: seam[:, x0 - 1:x0 + 2] = sp
    return np.clip(o + light_rgb((seam * 255).astype(np.uint8), 0.9, HOT, AMB), 0, 1)

TR2.update({"ribbon": (ribbon_spiral, RIB_PRE, 14), "emblem_split": (emblem_split, 16, 14), "edge_current": (edge_current, 10, 14),
            "focus_rack": (focus_rack, 10, 12), "speed_whip": (speed_whip, 5, 7), "eye_iris": (eye_iris, 12, 14),
            "time_slice": (time_slice, 8, 12), "afterimage": (afterimage, 10, 10), "light_leak13": (light_leak13, 10, 12),
            "panel_run": (panel_run, 8, 12), "whip_up13": (whip_up13, 6, 8)})

# ---- the loop (rev 2): the ribbon returns round him, spirals out, and frame 0 is inside it ----------------------------
LOOP_SPIRAL = 46                                                                             # frames before the wrap
def ribbon_loop(out, f, s, person):
    k = f - s["f0"]; n = s["f1"] - s["f0"]; p = RIB["last"]; cx, cy = p["c"]; t = f / FPS
    k1 = n - LOOP_SPIRAL
    if k < k1:
        return ribbon_draw(out, t, cx, cy, p["R"], person, open_=eout(k / 16.0, 2.0))
    q = (k - k1) / (LOOP_SPIRAL - 1)                                                          # 0..1, 1 = the last frame
    if q >= 1: return frame_virtual(f - E.DUR_F)
    R = p["R"] * math.exp(math.log(10.0) * ein(q, 1.5)); tilt = 0.50 + 0.50 * smooth(q * 1.3)
    gx = (_GX - cx) / R; gy = (_GY - cy) / (R * tilt * 1.05)
    m = np.clip((1.0 - np.sqrt(gx * gx + gy * gy)) * R / 40.0, 0, 1) * smooth(q * 2.5)
    m = np.maximum(m, ein(q, 6))
    Z0 = frame_virtual(f - E.DUR_F)
    Z0z = zoom_about(Z0, W / 2, H / 2, 1.0 + 0.3 * (1 - eout(q, 2.0)))
    o = mixm(out, Z0z, m)
    return ribbon_draw(o, t, cx, cy, R, person if q < 0.3 else None, 1.15 * (1 - smooth((q - 0.25) / 0.35)), tilt=tilt, sparks=q < 0.5)

# ---- the frame (rev 2) ------------------------------------------------------------------------------------------------
def base13(s, f):
    img, person = base11(s, f)
    orig = img
    if s["n"] == "pull": img = face_guard(orig, pull_fx(img, s, f, person, 0.7), s, f)
    if s["n"] in ("darling", "horizon"): img = horizon_fx(img, s, f, person)
    if s["n"] == "blood": img = ribbon_orbit(img, s, f, person)
    if s["n"] == "last": img = ribbon_loop(img, f, s, person)
    return img, person

def prefinish(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin")
    out, person = base13(s, f)
    PERSON.clear(); PERSON[f] = person                                                       # the current shot's matte
    if tin in TR2 and k < TR2[tin][2] and P is not None:
        out = TR2[tin][0](edge13(P, "last"), out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, edge13(n_, "first"), kn, f, s, n_)
    out = beat_fx(out, f)
    return np.clip(out, 0, 1)
