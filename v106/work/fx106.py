# ============================================================================ v106 WONDERWALL (The Flash x Oasis "Wonderwall")
# The edit's own section (spliced above the pipeline v2 speed section by tools/splice_section.py).
#   LOOK      WONDER: golden-hour amber light against Speed Force cobalt, milky lifted blacks, halation on highlights.
#   MIST      the Speed Force mist (frame 0 and the loop): drifting cobalt/violet wisps behind his matte, cold sparks.
#   WALL      THE WONDERWALL: a tall wall of glowing tiles (each a moment of the edit) with gold light in the mortar,
#             behind his matte; it rises tile by tile on "and after all", glows, and cracks with lightning on "you're my".
#   mist_swirl     the mist rolls over the frame and clears onto the next shot (lightning flickers inside it)
#   lightning_rod  a bolt strikes down beside the next face; the next shot burns open outward from the bolt
#   wonderwall     FOCAL: the frame itself becomes the wall, trembles, and bursts toward the camera; he strides out
#   tear_lens      (rev 2) her tear gathers under her jaw, falls toward the lens holding Barry's goodbye; we fall through it
#   loop_mist      (tout) he walks back into the Speed Force; the mist rolls over the lens and clears on frame 0
#   text           v9 captions (gold emphasis) on the sung words; WONDERWALL forged from light, letter by letter
COBALT = np.array([1.00, 0.52, 0.16], np.float32)        # BGR Speed Force cobalt
VIOLET = np.array([0.95, 0.35, 0.55], np.float32)        # BGR violet
WGOLD = np.array([0.30, 0.74, 1.00], np.float32)         # BGR warm mortar gold
WCORE = np.array([0.75, 0.93, 1.00], np.float32)         # BGR white-gold core
HALO_C = np.array([0.10, 0.32, 0.80], np.float32)        # BGR halation (warm red-orange)

# ---- the grade: WONDER ----------------------------------------------------------------------------------------------
_LUTW = {}
def lutw():
    if "w" not in _LUTW:
        x = np.linspace(0, 1, 1024, dtype=np.float32)
        _LUTW["w"] = (x, PchipInterpolator([0, .05, .20, .50, .80, .94, 1], [0.040, 0.062, 0.175, 0.47, 0.785, 0.915, 0.962])(x).astype(np.float32))
    return _LUTW["w"]

_grade_v11w = grade
def grade(img, s, f):
    if s.get("look") != "wonder": return _grade_v11w(img, s, f)
    g, gains = corr9(s); ev = s.get("ev") or 0; lx, ly = lutw()
    if in_unit(img):
        x = apply_lut3(img, tone_lut(("wonder", s["n"], ev, float(g), tuple(float(v) for v in gains)), gains, g, ev, lx, ly))
    else:
        x = np.interp(np.clip(np.clip(img * gains, 0, 1) ** g * 2 ** ev, 0, 1), lx, ly).astype(np.float32)
    Bc, Gc, Rc = (np.ascontiguousarray(x[..., c]) for c in range(3))
    L = Bc * 0.114 + Gc * 0.587 + Rc * 0.299
    warm = np.clip((Rc - Bc) * 3.0, 0, 1)                                                   # skin, the suit, lightning
    sat = 0.90 + 0.14 * warm
    sh = (1 - L) ** 2.2 * (1 - 0.6 * warm)                                                  # cobalt into the shadows
    hi = np.clip((L - 0.55) * 2.2, 0, 1)                                                    # amber into the light
    o = np.empty(x.shape, np.float32)
    for ch, (P, cs, chh) in enumerate(((Bc, 0.050, -0.030), (Gc, 0.012, 0.012), (Rc, -0.012, 0.040))):
        v = L + (P - L) * sat
        v += sh * cs; v += hi * chh
        o[..., ch] = v
    return np.clip(o, 0, 1, out=o)

# ---- the finish: halation, vignette, grain -------------------------------------------------------------------------
def finish106(out, f, s, ff=None, fmw=1.0):
    small = cv2.resize(out, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    hi_ = np.clip(small.max(2) - 0.68, 0, 1)
    bl = cv2.resize(cv2.GaussianBlur(hi_, (0, 0), 3) * 0.40 + cv2.GaussianBlur(hi_, (0, 0), 12) * 0.70, (W, H), interpolation=cv2.INTER_LINEAR)
    fb = face_box(s, f if ff is None else ff) if s is not None and s.get("face") is not None else None
    if fb:                                                                                 # the halation stays off his face
        fm = np.zeros((H // 8, W // 8), np.float32); cv2.ellipse(fm, (int((fb[0] + fb[1]) / 16), int((fb[2] - (fb[1] - fb[0]) * 0.55) / 8)),
                                                                   (int((fb[1] - fb[0]) / 14) + 4, int((fb[1] - fb[0]) * 0.8 / 8) + 4), 0, 0, 360, 1.0, -1)
        bl = bl * (1 - 0.85 * fmw * cv2.resize(cv2.GaussianBlur(fm, (0, 0), 3), (W, H)))
    o = np.empty(out.shape, np.float32); g = grain(f, 0.010)[..., 0]; v = VIG[..., 0]
    for ch in range(3):
        oc = o[..., ch]; np.multiply(bl, HALO_C[ch] * 0.42, out=oc); oc += out[..., ch]; oc *= v; oc += g
    return np.clip(o, 0, 1, out=o)

# ---- the beat camera: from the cold open's end to the loop; it rests on Iris and through the wall's burst -------------
def beat_phase(f):
    e = f / FPS / E.HB; ph = (e % 2) * E.HB; bi = int(e // 2)
    hook = (E.E_BEAT <= e < E.E_LOOP) and not (13 <= e < 20) and not (E.E_WALL - 1 <= e < E.E_WALL + 2)
    return ph, bi, hook, False

# ---- noise fields (fractal, cached per worker) -----------------------------------------------------------------------
_NZ = {}
def fbm(seed, h, w, oct_=5, falloff=0.55):
    key = (seed, h, w, oct_)
    if key not in _NZ:
        rng = np.random.default_rng(seed); acc = np.zeros((h, w), np.float32); amp, tot = 1.0, 0.0
        for o in range(oct_):
            gh, gw = max(2, h >> (oct_ - o + 1)), max(2, w >> (oct_ - o + 1))
            acc += cv2.resize(rng.random((gh + 1, gw + 1)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC) * amp
            tot += amp; amp *= falloff
        acc /= tot; acc = (acc - acc.min()) / (acc.max() - acc.min() + 1e-6); _NZ[key] = acc.astype(np.float32)
    return _NZ[key]

def crop_frac(c, oy, ox, h, w):
    """an h x w window of c at a fractional offset (bilinear): the mist drifts smoothly, not in whole quarter-res steps."""
    oy = min(max(oy, 0.0), c.shape[0] - h - 1.001); ox = min(max(ox, 0.0), c.shape[1] - w - 1.001)
    iy, ix = int(oy), int(ox); fy, fx = oy - iy, ox - ix; a = c[iy:iy + h + 1, ix:ix + w + 1]
    return (a[:h, :w] * ((1 - fy) * (1 - fx)) + a[1:, :w] * (fy * (1 - fx)) + a[:h, 1:] * ((1 - fy) * fx) + a[1:, 1:] * (fy * fx)).astype(np.float32)

def mist_field(t, speed=1.0):
    """(density, wisps) at full res: two drifting fractal layers (quarter res), wisps = ridges of the second.
    rev 2: sub-pixel drift on a canvas big enough that nothing wraps for t in -1.5..23 s (rev 1 stepped every ~3 frames
    and wrapped at negative t, which broke the loop's virtual frames)."""
    h4, w4 = H // 4, W // 4; ts = t * speed
    c1 = fbm(61, h4 + 904, w4 + 564, 4, 0.5); c2 = fbm(67, h4 + 904, w4 + 564, 5, 0.6)
    n1 = crop_frac(c1, 60 + 18 * ts, 40 + 11 * ts, h4, w4); n2 = crop_frac(c2, 610 - 13 * ts, 330 - 7 * ts, h4, w4)
    dens = cv2.GaussianBlur(smooth_arr((0.62 * n1 + 0.38 * n2 - 0.30) / 0.50), (0, 0), 3)
    wisp = cv2.GaussianBlur(np.clip(1 - np.abs(n2 * 2 - 1) * 2.6, 0, 1) ** 1.5 * dens, (0, 0), 1.5)
    return cv2.resize(dens, (W, H), interpolation=cv2.INTER_CUBIC), cv2.resize(wisp, (W, H), interpolation=cv2.INTER_CUBIC)

def smooth_arr(u): u = np.clip(u, 0, 1); return (u * u * (3 - 2 * u)).astype(np.float32)

MIST_DEEP = np.array([0.62, 0.30, 0.10], np.float32)    # BGR deep cobalt body
MIST_PALE = np.array([1.00, 0.86, 0.72], np.float32)    # BGR pale blue-white light in the wisps
def mist_rgb(dens, wisp, a=1.0):
    o = np.empty((H, W, 3), np.float32)
    for ch in range(3):
        oc = o[..., ch]; np.multiply(dens, MIST_DEEP[ch] * 0.55 * a, out=oc); oc += wisp * (MIST_PALE[ch] * 0.45 * a); oc += dens * (VIOLET[ch] * 0.08 * a)
    return o

def mist_layer(img, s, f, person, amt):
    """the Speed Force behind him: drifting cobalt wisps, cold sparks, a lightning flicker on every other beat."""
    t = f / FPS; dens, wisp = mist_field(t)
    bg = (1 - np.clip(person * 1.15, 0, 1)) if person is not None else np.ones((H, W), np.float32)
    add = mist_rgb(dens * bg, wisp * bg, amt)
    o = img * (1 - 0.18 * amt * (dens * bg)[..., None]) + add
    e = f / FPS / E.HB; ph = ((e - 2) % 4) * E.HB                                          # rev 2: on the half bar, never on frame 0
    if ph < 0.20:                                                                          # a cold flicker deep in the mist
        k4 = int((e - 2) // 4) + 50                                                        # >= 0 for the loop's virtual frames too
        cv = bolt_canvas(); rng = np.random.default_rng(k4 * 13 + 5)
        x0 = rng.uniform(W * 0.62, W * 0.95); put_bolt(cv, (x0, rng.uniform(-40, H * 0.15)), (x0 + rng.uniform(-200, 120), rng.uniform(H * 0.35, H * 0.6)),
                                                       k4 * 7 + 3, 2, 0.30, 6, 2)
        o = o + light_from(cv, 0.55 * amt * math.exp(-ph / 0.07), COBALT) * bg[..., None]
    return np.clip(o, 0, 1)

def shiver(shape, f, seed):
    """(jx, jy) in -1..1, smooth in time: every element on its own sine, 9-15 Hz, random phase."""
    rng = np.random.default_rng(seed); t = f / FPS
    fq = rng.uniform(9, 15, shape); p1 = rng.uniform(0, 2 * np.pi, shape); p2 = rng.uniform(0, 2 * np.pi, shape)
    return np.sin(2 * np.pi * fq * t + p1).astype(np.float32), np.sin(2 * np.pi * fq * 1.13 * t + p2).astype(np.float32)

# ---- THE WONDERWALL -----------------------------------------------------------------------------------------------
WALL_COLS, WALL_ROWS = 6, 11
_WL = {}
def wall_tex():
    """(rgb, mortar mask, tile index map) at half res: a grid of tiles, each a moment of the edit (warm-graded source
    frames, darkened, bevelled), with mortar gaps between them."""
    if "t" in _WL: return _WL["t"]
    h2, w2 = 960, 540; tw, th_ = w2 // WALL_COLS, h2 // WALL_ROWS; gap = 4
    rgb = np.zeros((h2, w2, 3), np.float32); mortar = np.ones((h2, w2), np.float32); idx = np.full((h2, w2), -1, np.int32)
    shots = [sh for sh in SHOTS if "src" in sh]; rng = np.random.default_rng(106); k = 0
    for r in range(WALL_ROWS):
        for c in range(WALL_COLS):
            sh = shots[(r * 5 + c * 3 + k) % len(shots)]; k += 1
            ts = [q[1] for q in sh["tmap"]]; t = rng.uniform(min(ts), max(ts))
            fr = sample(sh["src"], t)
            hh, ww = fr.shape[:2]; cw = hh * tw / th_; x0 = int(max(0, min(ww - cw, ww / 2 - cw / 2 + rng.uniform(-120, 120))))
            tile = cv2.resize(fr[:, x0:int(x0 + cw)], (tw - gap, th_ - gap), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
            Lt = tile.mean(2, keepdims=True); tile = (Lt + (tile - Lt) * 0.80) * 0.74 + 0.04
            tile = tile * np.array([0.82, 0.93, 1.06], np.float32)                           # warm sepia memory
            yy = np.linspace(0, 1, th_ - gap, dtype=np.float32)[:, None, None]; xx = np.linspace(0, 1, tw - gap, dtype=np.float32)[None, :, None]
            bevel = 1 + 0.22 * np.clip(0.08 - np.minimum(yy, xx), 0, 1) / 0.08 - 0.25 * np.clip(np.maximum(yy, xx) - 0.92, 0, 1) / 0.08
            y0, x0_ = r * th_ + gap // 2, c * tw + gap // 2 - (tw // 2 if r % 2 else 0)         # running bond: odd rows offset
            xa, xb_ = max(0, x0_), min(w2, x0_ + tw - gap)
            if xb_ - xa < 8: continue
            rgb[y0:y0 + th_ - gap, xa:xb_] = np.clip(tile * bevel, 0, 1)[:, xa - x0_:xb_ - x0_]
            mortar[y0:y0 + th_ - gap, xa:xb_] = 0; idx[y0:y0 + th_ - gap, xa:xb_] = r * WALL_COLS + c
            if r % 2 and c == WALL_COLS - 1:                                                # the half brick closing the row
                x1 = x0_ + tw; xa, xb_ = x1, min(w2, x1 + tw - gap)
                if xb_ - xa >= 8:
                    rgb[y0:y0 + th_ - gap, xa:xb_] = np.clip(tile * bevel, 0, 1)[:, :xb_ - xa]
                    mortar[y0:y0 + th_ - gap, xa:xb_] = 0; idx[y0:y0 + th_ - gap, xa:xb_] = r * WALL_COLS + c
    _WL["t"] = (rgb, mortar, idx, tw, th_); return _WL["t"]

def wall_quad(t):
    """the wall seen from below, receding upward, drifting slowly (dst corners for the half-res texture)."""
    d = 18 * math.sin(t * 0.7)
    return np.float32([[W * 0.10 + d, -H * 0.06], [W * 0.90 + d, -H * 0.06], [W * 1.30, H * 1.04], [-W * 0.30, H * 1.04]])

def wall_frame(f, built, crack, tremble=0.0):
    """the wall at frame f: rgb, alpha and mortar light (full res). built 0..1 raises it tile by tile from the bottom;
    crack 0..1 runs lightning along the mortar; tremble shakes the tiles."""
    rgb, mortar, idx, tw, th_ = wall_tex(); h2, w2 = mortar.shape; t = f / FPS
    rng = np.random.default_rng(7); order = (WALL_ROWS - 1 - (np.arange(WALL_ROWS * WALL_COLS) // WALL_COLS)) / WALL_ROWS + rng.uniform(0, 0.12, WALL_ROWS * WALL_COLS)
    vis = np.clip((built * 1.15 - order) / 0.10, 0, 1)                                      # each tile flips in when its turn comes
    a_t = np.where(idx >= 0, vis[np.maximum(idx, 0)], 0).astype(np.float32)
    a_m = mortar * np.clip(built * 1.4, 0, 1)
    pulse = 0.65 + 0.35 * math.exp(-((t / E.HB) % 2) * E.HB / 0.18)                         # the mortar breathes on the beat
    glow = mortar * (0.55 + 0.75 * crack) * pulse * np.clip(built * 1.4, 0, 1)
    if crack > 0.01:                                                                       # lightning crawls along the mortar
        cv = np.zeros((h2, w2), np.uint8); rr = np.random.default_rng(int(t * 12) + 3)
        for _ in range(int(2 + 6 * crack)):
            r0 = int(rr.integers(1, WALL_ROWS)); x_a = rr.uniform(0, w2); L_ = rr.uniform(80, 260) * crack
            y_ = r0 * th_; pts = [(x_a + q * L_ / 6, y_ + rr.uniform(-3, 3)) for q in range(7)]
            cv2.polylines(cv, [np.array(pts, np.int32)], False, 255, 2, cv2.LINE_AA)
        glow = np.clip(glow + cv.astype(np.float32) / 255 * 1.6 * crack, 0, 2)
    rgba = np.dstack([rgb * a_t[..., None], np.maximum(a_t, a_m)]).astype(np.float32); glow = glow.astype(np.float32)
    if tremble > 0:
        jx = (shiver((WALL_ROWS * WALL_COLS,), f, 78)[0] * 3 * tremble).astype(np.float32)
        mx = (np.arange(w2, dtype=np.float32)[None, :] + np.where(idx >= 0, jx[np.maximum(idx, 0)], 0)).astype(np.float32)
        my = np.repeat(np.arange(h2, dtype=np.float32)[:, None], w2, 1)
        rgba = cv2.remap(rgba, mx, my, cv2.INTER_LINEAR); glow = cv2.remap(glow, mx, my, cv2.INTER_LINEAR)
    M = cv2.getPerspectiveTransform(np.float32([[0, 0], [w2, 0], [w2, h2], [0, h2]]), wall_quad(t))
    full = cv2.warpPerspective(rgba, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    gfull = cv2.warpPerspective(glow, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    return full[..., :3], full[..., 3], gfull

def wall_state(f):
    e = f / FPS / E.HB
    built = smooth((e - E.E_WALL0 + 0.3) / 3.4); crack = smooth((e - (E.E_WALL - 6)) / 5.0)
    tremble = smooth((e - (E.E_WALL - 2)) / 2.0)
    return built, crack, tremble

def wall_layer(img, s, f, person, stage):
    built, crack, tremble = wall_state(f)
    if built <= 0.001: return img
    rgb, a, glow = wall_frame(f, built, crack, tremble)
    bg = (1 - np.clip(person * 1.1, 0, 1)) if person is not None else np.ones((H, W), np.float32)
    k = (a * 0.90 * bg)[..., None]
    o = img * (1 - k) + rgb * k
    gl = cv2.resize(cv2.GaussianBlur(cv2.resize(glow, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 4), (W, H))
    light = glow[..., None] * WCORE * 0.9 + gl[..., None] * WGOLD * 0.9
    o = o + light * bg[..., None]
    if person is not None:                                                                 # the wall's light wraps his edge (never his face)
        edge = np.clip(cv2.GaussianBlur(person, (0, 0), 9) - person * 0.85, 0, 1)
        fb = face_box(s, f)
        if fb: edge = edge * (1 - ((_GX > fb[0] - 40) & (_GX < fb[1] + 40) & (_GY < fb[2] + 60)).astype(np.float32))
        o = o + edge[..., None] * WGOLD * (0.25 + 0.45 * crack) * (gl[..., None] * 2.5 + 0.2)
    return np.clip(o, 0, 1)

# ---- the edit's base frame ---------------------------------------------------------------------------------------
def base106(s, f):
    img, person = base11(s, f)
    if s.get("mist"): img = mist_layer(img, s, f, person, s["mist"])
    if s.get("wall"): img = wall_layer(img, s, f, person, s["wall"])
    return img, person

_B106 = {}
def edge106(S_, which):
    key = (S_["n"], which)
    if key not in _B106:
        if len(_B106) > 6: _B106.clear()
        _B106[key] = base106(S_, S_["f0"] if which == "first" else S_["f1"] - 1)[0]
    return _B106[key]

# ---- transitions ------------------------------------------------------------------------------------------------
def mist_cover(f, u):
    """coverage 0..1 of the rolling mist at progress u (0 clear -> 1 full): fractal edge, from the frame edges inward."""
    dens, wisp = mist_field(f / FPS, 2.0)
    rad = np.sqrt(((_GX - W / 2) / (W * 0.62)) ** 2 + ((_GY - H * 0.48) / (H * 0.62)) ** 2)
    field = 0.62 * np.clip(rad, 0, 1.3) + 0.38 * cv2.GaussianBlur(dens, (0, 0), 14)
    return smooth_arr((field - (1.22 - 1.55 * u)) / 0.30), dens, wisp

def mist_over(base, f, u):
    """the mist volume over base: the picture refracts and softens under it; never fully opaque (max ~85 %)."""
    cov, dens, wisp = mist_cover(f, u); cov = cov * 0.88
    gy, gx = np.gradient(cv2.resize(dens, (W // 4, H // 4), interpolation=cv2.INTER_AREA))
    dxm = cv2.resize(gx, (W, H)) * 4 * 60 * cov; dym = cv2.resize(gy, (W, H)) * 4 * 60 * cov
    br = cv2.remap(base, _GX + dxm, _GY + dym, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    soft = cv2.resize(cv2.GaussianBlur(cv2.resize(br, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 4), (W, H))
    c3 = cov[..., None]; under = br * (1 - 0.65 * c3) + soft * (0.65 * c3)
    m = mist_rgb(np.clip(dens * 0.8 + 0.25, 0, 1), wisp, 1.15)
    o = under * (1 - 0.72 * c3) + m * c3
    if 0.35 < u < 0.95:                                                                    # lightning inside the mist
        cv = bolt_canvas(); rng = np.random.default_rng(f // 3)
        side = rng.random() < 0.5; x0 = rng.uniform(W * 0.04, W * 0.20) if side else rng.uniform(W * 0.80, W * 0.96)   # rev 2: at the edges,
        put_bolt(cv, (x0, rng.uniform(H * 0.05, H * 0.3)), (x0 + rng.uniform(-60, 60), rng.uniform(H * 0.55, H * 0.9)), f // 3, 2, 0.3, 6, 2)  # never across a face
        o = o + light_from(cv, 0.35 * cov.mean() + 0.05, COBALT) * cov[..., None]
    return np.clip(o, 0, 1)

def mist_swirl(A, B, j, f, sa, sb, pre=10, post=16):
    if j < 0:
        w = clamp((j + 5) / 10, 0, 1)                                                      # the last frames: B starts to show through
        return mist_over(A if w <= 0 else A * (1 - w) + B * w, f, ein((j + pre + 1) / (pre + 1), 1.6))
    w = clamp(0.5 + (j + 1) / 10, 0, 1)
    return mist_over(B if w >= 1 else A * (1 - w) + B * w, f, 1 - eout(j / post, 2.0))
TR2["mist_swirl"] = (mist_swirl, 10, 16)

def lightning_rod(A, B, j, f, sa, sb, pre=6, post=20):
    """a bolt strikes down beside the next shot's face (never on it); the next shot burns open outward from the bolt."""
    fb = face_box(sb, sb["f0"]); xb = W * 0.30
    if fb: fx = (fb[0] + fb[1]) / 2; xb = fx - 330 if fx > W * 0.45 else fx + 330
    xb = clamp(xb, 140, W - 140)
    cv = bolt_canvas(); pts = put_bolt(cv, (xb + 40, -30), (xb - 30, H + 30), 1060, 5, 0.22, 7, 3)
    if j < 0:                                                                              # the leader flickers down
        u = (j + pre + 1) / (pre + 1); lead = np.zeros((H, W), np.uint8)
        n = max(2, int(len(pts) * u * 0.8)); cv2.polylines(lead, [pts[:n].astype(np.int32)], False, 255, 2, cv2.LINE_AA)
        fl = 0.35 + 0.65 * ((j % 2) == 0)
        return np.clip(A * (1 - 0.15 * u) + light_from(lead, 0.55 * fl * u, WGOLD), 0, 1)
    v = (j + 1) / post
    dist = cv2.distanceTransform((255 - cv).astype(np.uint8), cv2.DIST_L2, 5)
    R_ = 30 + 1100 * eout(v, 2.6)
    m = np.clip((R_ - dist) / 40, 0, 1)[..., None]
    rim = np.exp(-((dist - R_) / 18) ** 2)[..., None] * (1 - v)
    o = A * (1 - m) * 0.85 + B * m + rim * WGOLD * 1.1
    k = max(0.0, 1 - j / 10)                                                               # the bolt and its afterglow
    o = o + light_from(cv, 1.1 * k, WGOLD)
    if j < 3: o = add_glow(o, xb - 30, H * 0.97, 220, 0.6 * (1 - j / 3), WCORE)         # the strike hits the ground
    return np.clip(o, 0, 1)
TR2["lightning_rod"] = (lightning_rod, 6, 20)

def tile_split(img, f, amt, gap_light):
    """the frame as a wall: a tile grid with glowing mortar; tiles tremble by amt (px)."""
    tw, th_ = W // WALL_COLS, H // WALL_ROWS
    jx, jy = shiver((WALL_ROWS, WALL_COLS), f, 77); jx, jy = jx * amt, jy * amt
    ri = np.clip((_GY // th_).astype(np.int32), 0, WALL_ROWS - 1); off = (ri % 2) * (tw / 2)       # running bond
    xs = _GX + off; ci = np.clip((xs // tw).astype(np.int32), 0, WALL_COLS)
    jx = np.pad(jx, ((0, 0), (0, 1)), mode="wrap"); jy = np.pad(jy, ((0, 0), (0, 1)), mode="wrap")
    o = cv2.remap(img, _GX + jx[ri, ci], _GY + jy[ri, ci], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    u_, v_ = xs % tw, _GY % th_
    gx = np.minimum(u_, tw - u_); gy = np.minimum(v_, th_ - v_)
    mort = np.exp(-(np.minimum(gx, gy) / 3.0) ** 2)
    bev = 1 + 0.16 * np.exp(-v_ / 10) * gap_light - 0.20 * np.exp(-(th_ - v_) / 12) * gap_light                # bevel: lit top, shaded bottom
    o = o * bev[..., None]
    g = cv2.GaussianBlur(cv2.resize(mort, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 3)
    g = cv2.resize(g, (W, H))
    return np.clip(o * (1 - 0.6 * mort[..., None] * gap_light) + (mort[..., None] * WCORE + g[..., None] * WGOLD * 1.6) * gap_light, 0, 1)

_TW = {}
def tiles_of(A):
    tw, th_ = W // WALL_COLS, H // WALL_ROWS; key = id(A)
    if _TW.get("k") != key:
        ts = []
        for r in range(WALL_ROWS):
            for c in range(WALL_COLS + (r % 2)):
                x0, y0 = c * tw - (tw // 2 if r % 2 else 0), r * th_
                xa, xb_ = max(0, x0), min(W, x0 + tw)
                t = np.zeros((th_, tw, 3), np.float32); t[:, xa - x0:xb_ - x0] = A[y0:y0 + th_, xa:xb_]
                yy, xx = np.mgrid[0:th_, 0:tw].astype(np.float32); edge = np.minimum(np.minimum(xx, tw - 1 - xx), np.minimum(yy, th_ - 1 - yy))
                t = t * 1.25 + 0.03 + (np.exp(-(edge / 5.0) ** 2)[..., None] * WGOLD * 1.25) + (np.exp(-(edge / 1.6) ** 2)[..., None] * WCORE * 0.6)
                al = np.clip(edge / 1.5, 0, 1); al[:, :xa - x0] = 0; al[:, xb_ - x0:] = 0
                ts.append((x0 + tw / 2, y0 + th_ / 2, np.dstack([np.clip(t, 0, 1), al]).astype(np.float32)))
        _TW.update(k=key, t=ts)
    return _TW["t"]

def wonderwall(A, B, j, f, sa, sb, pre=12, post=30):
    """FOCAL: the frame becomes the wall (tile grid, mortar of light, trembling), then bursts toward the camera on
    'WONDERWALL'; the tiles fly past the lens (away from his face first) and he strides out through the light."""
    if j < 0:
        u = (j + pre + 1) / (pre + 1)
        return tile_split(A, f, 1.0 + 9 * ein(u, 2), 0.25 + 0.75 * u)
    v = (j + 1) / post
    cx, cy = W / 2, H * 0.50
    fb = face_box(sb, f)
    lb = math.exp(-j / 9)                                                                  # the light behind the wall
    Bl = B + (B * 0.6 + WGOLD * 0.5) * (0.9 * lb)
    r_ = np.sqrt((_GX - cx) ** 2 + (_GY - cy) ** 2)
    ring = np.exp(-((r_ - 1800 * eout(v, 2)) / 60) ** 2) * (1 - v)                        # the shockwave
    o = np.clip(Bl + ring[..., None] * WCORE * 0.5, 0, 1)
    rng = np.random.default_rng(48); ts = tiles_of(A)
    order = np.argsort([-(abs(x - cx) + abs(y - cy)) for x, y, _ in ts])
    for i in order:
        x, y, t = ts[i]
        dx, dy = x - cx, y - cy; dn = math.hypot(dx, dy) + 1e-3
        on_face = fb is not None and fb[0] - 60 < x < fb[1] + 60 and y < fb[2] + 60
        delay = rng.uniform(0, 0.10) * (0.3 if on_face else 1.0)
        w_ = clamp((v - delay) / (1 - delay), 0, 1)
        if w_ <= 0:                                                                        # still in place, light leaking round it
            o = paste(o, t, int(x - t.shape[1] / 2), int(y - t.shape[0] / 2), 1.0); continue
        z = 1 + 4.5 * ein(w_, 1.25) * (1.4 if on_face else 1.0)
        px = x + dx / dn * 1500 * ein(w_, 1.25) * (1.5 if on_face else 1.0) + rng.uniform(-80, 80) * w_
        py = y + dy / dn * 1200 * ein(w_, 1.25) + 300 * w_ * w_
        rot = rng.uniform(-60, 60) * w_
        a = (1 - smooth((w_ - 0.25) / 0.45))
        if a <= 0.01: continue
        M = cv2.getRotationMatrix2D((t.shape[1] / 2, t.shape[0] / 2), rot, z); M[0, 2] += px - t.shape[1] / 2; M[1, 2] += py - t.shape[0] / 2
        R_ = int(max(t.shape[:2]) * z * 0.75) + 4; xa, ya, xb_, yb_ = max(0, int(px - R_)), max(0, int(py - R_)), min(W, int(px + R_)), min(H, int(py + R_))
        if xb_ <= xa or yb_ <= ya: continue
        M2 = M.copy(); M2[0, 2] -= xa; M2[1, 2] -= ya
        tile = cv2.warpAffine(t, M2, (xb_ - xa, yb_ - ya), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
        if w_ > 0.15: tile[..., :3] = cv2.GaussianBlur(tile[..., :3], (0, 0), 0.5 + 6 * w_)  # motion blur as it rushes past
        al = tile[..., 3:4] * a
        o[ya:yb_, xa:xb_] = o[ya:yb_, xa:xb_] * (1 - al) + tile[..., :3] * al
    return np.clip(o, 0, 1)
TR2["wonderwall"] = (wonderwall, 12, 30)

def loop_mist(out, f, s):
    """tout on the last shot: he walks back into the Speed Force; the mist rolls over the lens, and clears on frame 0's
    own image (the last frame is frame 0's picture: the loop lands)."""
    f0 = fh(E.E_LOOP + 2); n = E.DUR_F - f0
    if f < f0: return out
    u = (f - f0 + 1) / n
    cover = smooth(u / 0.55) * (1 - smooth((u - 0.62) / 0.38))
    w = loop_w(f)                                                                          # rev 2: a dissolve under the mist, not a switch
    if w <= 0: under = out
    else:
        und = sf_virtual(f - E.DUR_F)
        under = und if w >= 1 else out * (1 - w) + und * w
    return mist_over(under, f, cover)

def loop_w(f):
    """how far the picture under the loop's mist has become frame 0's (0 -> 1 while the mist is thickest)."""
    f0 = fh(E.E_LOOP + 2); u = (f - f0 + 1) / (E.DUR_F - f0)
    return smooth((u - 0.40) / 0.22) if f >= f0 else 0.0

_LV = {}
def sf_virtual(fv):
    """frame 0's footage with its Speed Force mist at the virtual frame fv (< 0): the mist keeps drifting into frame 0."""
    if "b" not in _LV: _LV["b"] = base11(SHOTS[0], SHOTS[0]["f0"])
    img, person = _LV["b"]
    return mist_layer(img, SHOTS[0], fv, person, SHOTS[0]["mist"])

# ---- TEAR LENS (rev 2): her tear gathers under her jaw, swells, and falls toward the lens; inside it, Barry's goodbye.
#      We fall through it: the frame is inside the drop (a magnifying lens relaxing flat) and a ripple runs out from it.
def tear_lens(A, B, j, f, sa, sb, pre=60, post=26):                                   # rev 3: slower (owner)
    if j < 0:
        u = (j + pre + 1) / pre                                                            # 1/pre .. 1 (lands on the cut)
        fs = face_scr(sa, f) if sa.get("face") is not None else None
        C0 = (fs[0] + 0.30 * fs[2], fs[1] + 0.29 * fs[2]) if fs else (W * 0.55, H * 0.55)      # under her jaw, beside the chin
        Ct = (W * 0.5, H * 0.62)
        if u < 0.40:                                                                       # it gathers on her jaw (0.4 s)
            g = smooth(u / 0.40); r = 4 + 30 * g; C = (C0[0], C0[1] + 10 * g); v = 0.0
        elif u < 0.55:                                                                     # it hangs, swells and sags (0.15 s)
            g = smooth((u - 0.40) / 0.15); r = 34 + 10 * g + 1.5 * math.sin(g * math.pi * 2); C = (C0[0], C0[1] + 10 + 12 * g); v = 0.0
        else:                                                                              # it lets go and falls toward the lens (0.45 s)
            v = (u - 0.55) / 0.45; e_ = ein(v, 2.3); C0 = (C0[0], C0[1] + 22)
            r = 44 * math.exp(math.log(1500 / 44) * e_); C = (C0[0] + (Ct[0] - C0[0]) * ein(v, 1.6), C0[1] + (Ct[1] - C0[1]) * ein(v, 1.6))
        fb = face_scr(sb, sb["f0"]) if sb.get("face") is not None else None
        PB = (fb[0], fb[1]) if fb else (W / 2, H * 0.40)
        k = smooth(v)
        P_ = (PB[0] + (C[0] - PB[0]) * k, PB[1] + (C[1] - PB[1]) * k)                       # the drop holds his face, then the whole frame
        mag = 1 + 5.0 * (1 - smooth((r - 44) / 520))
        L = 0.42 - 0.17 * smooth(v)
        return np.clip(drop_over(A, B, C, r, P_, mag, L, 1 - smooth((r - 220) / 700)), 0, 1)
    v = (j + 1) / post; Ct = (W * 0.5, H * 0.62)
    L = 0.25 * (1 - eout(v, 2.0))
    dx, dy = _GX - Ct[0], _GY - Ct[1]; rr = np.sqrt(dx * dx + dy * dy) + 1e-3
    m = 1 - L * np.clip(1 - (rr / 1500) ** 2, 0, 1)
    R = 80 + 1500 * eout(v, 1.7); band = np.exp(-((rr - R) / 55.0) ** 2) * (1 - v)          # the ripple from where it landed
    fb = face_box(sb, f)
    if fb:                                                                                 # never across his face
        cxf = (fb[0] + fb[1]) / 2; rx = (fb[1] - fb[0]) / 2 + 60; ry = (fb[1] - fb[0]) * 0.80 + 40
        band = band * np.clip(np.sqrt(((_GX - cxf) / rx) ** 2 + ((_GY - (fb[2] - ry * 0.9)) / ry) ** 2) * 1.6 - 0.9, 0, 1)
    disp = band * 24
    mx = (Ct[0] + dx * m + dx / rr * disp).astype(np.float32); my = (Ct[1] + dy * m + dy / rr * disp).astype(np.float32)
    o = cv2.remap(B, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    o = o + band[..., None] * (WCORE * 0.10)                                               # the ripple catches the light
    return np.clip(o, 0, 1)
TR2["tear_lens"] = (tear_lens, 60, 26)

def drop_over(A, B, C, r, P_, mag, L, spec):
    """a lit water drop of radius r at C over A; inside, B seen through it (centred on P_, minified by mag, bulged by L)."""
    R_ = int(r * 1.15) + 6; xa, ya, xb, yb = max(0, int(C[0] - R_)), max(0, int(C[1] - R_ * 1.2)), min(W, int(C[0] + R_)), min(H, int(C[1] + R_))
    if xb <= xa or yb <= ya: return A
    gx, gy = _GX[ya:yb, xa:xb], _GY[ya:yb, xa:xb]
    dx, dy = gx - C[0], (gy - C[1]) / (1 + 0.10 * (1 - smooth((r - 34) / 60)))                 # a hanging tear is slightly long
    rho = np.sqrt(dx * dx + dy * dy) / r
    inside = np.clip((1 - rho) * r / 1.2, 0, 1)                                            # anti-aliased edge
    m = (1 - L * np.clip(1 - rho ** 2, 0, 1)) * mag
    q = cv2.remap(B, (P_[0] + dx * m).astype(np.float32), (P_[1] + dy * m).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    edge_px = min(0.30 * r, 70.0); ed = np.clip((r - rho * r) / edge_px, 0, 1)
    q = q * (0.45 + 0.55 * smooth_arr(ed))[..., None]                                      # the dark Fresnel edge
    rim = np.exp(-(((1 - rho) * r) / max(1.2, 0.035 * r)) ** 2)                             # the thin bright rim: warm below, cold above
    up = np.clip(-dy / (r + 1e-3), -1, 1)
    q = q + rim[..., None] * (WGOLD * np.clip(0.5 - 0.5 * up, 0, 1)[..., None] + COBALT * np.clip(0.5 + 0.5 * up, 0, 1)[..., None]) * 0.55
    hx, hy = dx / r + 0.34, dy / r + 0.40                                                  # the highlight (streetlight), and its caustic
    q = q + (np.exp(-((hx / 0.16) ** 2 + (hy / 0.10) ** 2)) * 0.95 * spec)[..., None] * WCORE
    cx_, cy_ = dx / r - 0.28, dy / r - 0.46
    q = q + (np.exp(-((cx_ / 0.30) ** 2 + (cy_ / 0.16) ** 2)) * 0.35 * spec)[..., None] * WGOLD
    o = A.copy(); a_ = inside[..., None]
    if r < 300:                                                                            # its soft shadow on the skin below it
        sh = np.exp(-((dx / (r * 1.1)) ** 2 + ((dy - r * 0.6) / (r * 0.8)) ** 2)) * 0.25 * (1 - inside) * (1 - smooth((r - 60) / 200))
        o[ya:yb, xa:xb] *= (1 - sh)[..., None]
    o[ya:yb, xa:xb] = o[ya:yb, xa:xb] * (1 - a_) + q * a_
    return o

# ---- text: v9 captions on the sung words (gold emphasis); WONDERWALL forged from light ---------------------------
_WD = {}
def wonder_letter(c, size):
    key = (c, size)
    if key in _WD: return _WD[key]
    (lets, wd) = hero_letters(c, size, 0); m = lets[0][1]; pad = 40; mm = np.pad(m, pad)
    hh = mm.shape[0]; grad = np.linspace(0, 1, hh, dtype=np.float32)[:, None]
    face = WCORE[None, None, :] * (1 - grad[..., None]) * 1.05 + WGOLD[None, None, :] * grad[..., None]
    emb = np.clip((np.roll(cv2.GaussianBlur(mm, (0, 0), 2.2), -2, 0) - np.roll(cv2.GaussianBlur(mm, (0, 0), 2.2), 2, 0)) * 2.2, -1, 1)[..., None]
    face = face * (1 + 0.45 * emb)
    k_ = max(3, int(size * 0.06)) | 1; key_ = cv2.dilate(mm, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_, k_)))
    glow = cv2.GaussianBlur(mm, (0, 0), size * 0.16)
    col = np.zeros(mm.shape + (3,), np.float32) + np.array([0.04, 0.03, 0.02], np.float32)
    col = col * (1 - mm[..., None]) + face * mm[..., None] + COBALT * (glow * (1 - key_))[..., None] * 0.9
    a = np.maximum(np.maximum(mm, key_ * 0.92), glow * 0.75)
    _WD[key] = np.dstack([np.clip(col, 0, 1.2), a]).astype(np.float32); return _WD[key]

def text_wonder(out, f, tx):
    t = f / FPS; word = tx["words"][0][0]; t0 = tx["words"][0][1]; t_end = tx["end"]
    if t < t0 - 0.05 or t > t_end + 0.02: return out
    size = 150; (lets, wd) = hero_letters(word, size, 4); fit = min(1.0, 960 / max(1, wd)); y = 1530
    out = out * cap_scrim(y - 150, y + 120, 0.30 * smooth((t - t0) / 0.25) * (1 - smooth((t - t_end + 0.2) / 0.2)))
    sung = 1.52; n = len(lets)
    for i, (c, m, xo) in enumerate(lets):
        ti = t0 + sung * i / n; v = eout(clamp((t - ti) / 0.24, 0, 1), 3)
        if v <= 0: continue
        L = wonder_letter(c, int(size * fit))
        ex = clamp((t - (t_end - 0.28 + 0.015 * i)) / 0.26, 0, 1)                            # exit: the letter phases out
        x = W / 2 + xo * fit; sc = 1.35 - 0.35 * v
        if v < 1 or ex > 0:
            Ls = cv2.resize(L, None, fx=sc, fy=sc, interpolation=cv2.INTER_LINEAR) if abs(sc - 1) > 0.01 else L
            Ls = cv2.GaussianBlur(Ls, (0, 0), 0.1 + 5 * (1 - v) + 3 * ex)
        else: Ls = L
        a = v * (1 - ex)
        if ex > 0:                                                                          # vibrating ghosts as it phases out
            for d, ga in ((-14 * ex, 0.35), (14 * ex, 0.35)):
                out = paste(out, Ls, int(x + d - Ls.shape[1] / 2), int(y - Ls.shape[0] / 2), a * ga)
        out = paste(out, Ls, int(x - Ls.shape[1] / 2), int(y - Ls.shape[0] / 2 + 18 * (1 - v)), a)
        if 0 < v < 1: out = add_glow(out, x, y, 70, 0.35 * (1 - v), WGOLD)               # it is struck out of light
    return out

def text106(out, f, s, rides):
    for tx in E.TEXT:
        if bool(tx.get("rides")) != rides: continue
        if tx["style"] == "cap": out = text_cap(out, f, tx, None)
        elif tx["style"] == "wonder": out = text_wonder(out, f, tx)
    return out

# ---- the clash on "saves me", with the collision below his face and the sparks kept off it ---------------------------
def clash106(A, B, j, f, sa, sb, pre=10, post=14):
    fb = face_box(sb, sb["f0"]); Py = H * 0.64
    if fb: Py = clamp(fb[2] + 110, H * 0.64, H * 0.84)
    keep = np.ones((H, W), np.float32)
    if fb:
        cxf = (fb[0] + fb[1]) / 2; rx = (fb[1] - fb[0]) / 2 + 70; ry = (fb[1] - fb[0]) * 0.80 + 40
        keep = np.clip(np.sqrt(((_GX - cxf) / rx) ** 2 + ((_GY - (fb[2] - ry * 0.9)) / ry) ** 2) * 1.6 - 0.9, 0, 1)
    base = A if j < 0 else B
    o = clash_at(A, B, j, f, (W * 0.5, Py), pre, post)
    return np.clip(base + (o - base) * keep[..., None], 0, 1)

def clash_at(A, B, j, f, P, pre, post):
    if j < 0:
        u = (j + pre + 1) / pre; e = ein(u, 1.6)
        cr, cg = bolt_canvas(), bolt_canvas()
        put_bolt(cr, (-40, H * 0.55), (-40 + (P[0] + 40) * e, H * 0.55 + (P[1] - H * 0.55) * e), 4100 + f, 4, 0.22, 7, 2)
        put_bolt(cg, (W + 40, H * 0.86), (W + 40 - (W + 40 - P[0]) * e, H * 0.86 + (P[1] - H * 0.86) * e), 4150 + f, 4, 0.22, 7, 2)
        return np.clip(A * (1 - 0.25 * u) + light_from(cr, 1.1, COBALT) + light_from(cg, 1.2), 0, 1)
    v = (j + 1) / post
    o = B.copy()
    dx, dy = _GX - P[0], _GY - P[1]; r = np.sqrt(dx * dx + dy * dy) + 1e-3; R = 80 + 1700 * eout(v, 1.5)
    band = np.exp(-((r - R) / 80.0) ** 2); disp = band * 55 * (1 - v)
    o = cv2.remap(o, (_GX - dx / r * disp).astype(np.float32), (_GY - dy / r * disp).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    o = o + np.exp(-((r - R) / 8.0) ** 2)[..., None] * GOLDW * 0.7 * (1 - v)
    cr, cg = bolt_canvas(), bolt_canvas()
    for (a, L_, s_, red) in clash_sparks():
        d0 = L_ * eout(v, 1.8) * s_; d1 = d0 + 40 + 120 * (1 - v)
        cv2.line(cr if red else cg, (int(P[0] + math.cos(a) * d0), int(P[1] + math.sin(a) * d0)),
                 (int(P[0] + math.cos(a) * d1), int(P[1] + math.sin(a) * d1)), int(255 * (1 - v)), 3, cv2.LINE_AA)
    o = o + light_from(cr, 1.0, COBALT) + light_from(cg, 1.0)
    if j < 4: o = add_glow(o, P[0], P[1], 260, 1.0 * (1 - j / 4), GOLDW)
    return np.clip(o, 0, 1)
TR2["clash106"] = (clash106, 10, 14)

# ---- the frame ----------------------------------------------------------------------------------------------------
def render(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin")
    out, person = base106(s, f)
    out = text106(out, f, s, True)
    if tin in TR2 and k < TR2[tin][2] and P is not None:
        out = TR2[tin][0](edge106(P, "last"), out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, edge106(n_, "first"), kn, f, s, n_)
    if s.get("tout") == "loop_mist": out = loop_mist(out, f, s)
    out = beat_fx(out, f)
    out = text106(out, f, s, False)
    lw = loop_w(f) if s.get("tout") == "loop_mist" else 0.0
    if lw > 0: out = finish106(out, f, SHOTS[0], 0, lw)                                      # frame 0's own finish, faded in: the seam lands exactly
    else: out = finish106(out, f, s)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)


