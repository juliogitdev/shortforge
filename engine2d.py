"""shortforge 2D engine: drawing helpers used by compose.py (text, badges, cards, subtitles, UI widgets).

Everything is drawn on 1080x1920 RGBA frames with Pillow. Coordinates are pixels, (0,0) top-left.
"""
import os, math, glob, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, '..', 'assets', 'fonts')

PINK = (255, 46, 136); PURPLE = (123, 47, 247); ORANGE = (255, 138, 0); YEL = (255, 212, 0)
DARK = (13, 13, 26); CYAN = (0, 200, 255); RED = (255, 40, 60); GREEN = (40, 200, 90); BLUE = (40, 120, 255)
WHITE = (255, 255, 255); BLACK = (0, 0, 0)
NAMED = {'pink': PINK, 'purple': PURPLE, 'orange': ORANGE, 'yellow': YEL, 'dark': DARK, 'cyan': CYAN, 'red': RED,
         'green': GREEN, 'blue': BLUE, 'white': WHITE, 'black': BLACK}

def col(c, default=WHITE):
    """Accept 'yellow', '#ffd400', [r,g,b] or [r,g,b,a]."""
    if c is None: return default
    if isinstance(c, str):
        if c.startswith('#'):
            c = c.lstrip('#'); return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
        return NAMED.get(c.lower(), default)
    return tuple(c)

# ------------------------------------------------------------------ basics
_fonts = {}
def font(size, w='black'):
    k = (size, w)
    if k not in _fonts:
        f = {'black': 'Montserrat_900Black.ttf', 'xb': 'Montserrat_800ExtraBold.ttf', 'bold': 'Montserrat_700Bold.ttf'}[w]
        _fonts[k] = ImageFont.truetype(os.path.join(FONTS, f), size)
    return _fonts[k]

_cache = {}
def txt(text, size, fill=WHITE, stroke=0, sfill=BLACK, w='black'):
    k = ('t', text, size, fill, stroke, sfill, w)
    if k in _cache: return _cache[k]
    f = font(size, w); bb = f.getbbox(text, stroke_width=stroke)
    im = Image.new('RGBA', (bb[2] - bb[0] + 8, bb[3] - bb[1] + 8))
    ImageDraw.Draw(im).text((-bb[0] + 4, -bb[1] + 4), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)
    _cache[k] = im; return im

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eo(x): x = clamp(x); return 1 - (1 - x) ** 3
def back(x):
    x = clamp(x); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def pop(t, t0, d=0.28): return 0.0 if t < t0 else back((t - t0) / d)
def slam(t, t0, d=0.15, start=2.2): return 0.0 if t < t0 else start + (1 - start) * eo((t - t0) / d)
def lerp(a, b, x): return a + (b - a) * x

_luts = {}
def with_alpha(im, a):
    if a >= 0.999: return im
    q = int(a * 50)
    if q not in _luts: _luts[q] = [int(v * q / 50) for v in range(256)]
    im = im.copy(); im.putalpha(im.getchannel('A').point(_luts[q])); return im

def comp(base, im, x, y):
    x, y = int(x), int(y)
    bx0, by0 = max(0, x), max(0, y); bx1, by1 = min(base.width, x + im.width), min(base.height, y + im.height)
    if bx1 <= bx0 or by1 <= by0: return
    base.alpha_composite(im.crop((bx0 - x, by0 - y, bx1 - x, by1 - y)), (bx0, by0))

def put(base, im, cx, cy, s=1.0, a=1.0, rot=0.0):
    if s <= 0.01 or a <= 0.01: return
    if abs(s - 1) > 0.003: im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BICUBIC)
    if abs(rot) > 0.05: im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
    im = with_alpha(im, a); comp(base, im, cx - im.width / 2, cy - im.height / 2)

def grad(w, h, stops, horizontal=False):
    n = w if horizontal else h; xs = np.linspace(0, 1, n)
    line = np.stack([np.interp(xs, [s[0] for s in stops], [s[1][c] for s in stops]) for c in range(3)], -1).astype(np.uint8)
    arr = np.broadcast_to(line[None], (h, w, 3)) if horizontal else np.broadcast_to(line[:, None], (h, w, 3))
    return Image.fromarray(np.ascontiguousarray(arr), 'RGB').convert('RGBA')

def radial(w, h, center_col, edge_col, cx=0.5, cy=0.45, r=0.8):
    y, x = np.mgrid[0:h, 0:w]
    d = np.clip(np.sqrt(((x / w - cx) * (w / h)) ** 2 + (y / h - cy) ** 2) / r, 0, 1)[..., None]
    a = np.array(center_col)[None, None]; b = np.array(edge_col)[None, None]
    return Image.fromarray((a * (1 - d) + b * d).astype(np.uint8), 'RGB').convert('RGBA')

def rrect_mask(w, h, r):
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255); return m

def tint(fr, rgba): fr.alpha_composite(Image.new('RGBA', (W, H), tuple(rgba)))

def vignette(fr, s=1.0):
    v = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(v)
    for i in range(10): d.rectangle((i * 26, i * 26, W - i * 26, H - i * 26), outline=(0, 0, 0, int(28 * s)), width=26)
    fr.alpha_composite(v)

# ------------------------------------------------------------------ backgrounds
_bg = {}
def neon_bg():
    if 'neon' in _bg: return _bg['neon']
    S = 2; w, h = W * S, H * S
    im = grad(w, h, [(0, (20, 4, 45)), (0.30, (70, 20, 150)), (0.47, PINK), (0.57, ORANGE), (0.575, (30, 6, 60)), (1, (10, 0, 25))])
    d = ImageDraw.Draw(im); hy = int(0.575 * h)
    sun = grad(700 * S, 700 * S, [(0, YEL), (0.6, ORANGE), (1, PINK)])
    m = Image.new('L', sun.size, 0); md = ImageDraw.Draw(m); md.ellipse((0, 0, sun.width - 1, sun.height - 1), fill=255)
    for i in range(8):
        yy = int(sun.height * (0.55 + i * 0.06)); md.rectangle((0, yy, sun.width, yy + (6 + i * 4) * S), fill=0)
    sun.putalpha(m); im.alpha_composite(sun, (w // 2 - sun.width // 2, hy - int(sun.height * 0.78)))
    rng = np.random.default_rng(7); x = 0
    while x < w:
        bw = int(rng.integers(60, 150)) * S; bh = int(rng.integers(120, 520)) * S
        if abs((x + bw / 2) - w / 2) < 260 * S: bh = int(bh * 0.55)
        d.rectangle((x, hy - bh, x + bw, hy), fill=(38, 8, 70))
        for wy in range(hy - bh + 20 * S, hy - 10 * S, 34 * S):
            for wx in range(x + 14 * S, x + bw - 14 * S, 30 * S):
                if rng.random() < 0.35: d.rectangle((wx, wy, wx + 12 * S, wy + 16 * S), fill=(255, 190, 90))
        x += bw + int(rng.integers(4, 20)) * S
    for i in range(-14, 15): d.line((w / 2 + i * 40 * S, hy, w / 2 + i * 420 * S, h), fill=(255, 46, 200), width=3 * S)
    yy, k = hy, 12 * S
    while yy < h: d.line((0, yy, w, yy), fill=(255, 46, 200), width=3 * S); k *= 1.35; yy += int(k)
    _bg['neon'] = im.resize((W, H), Image.LANCZOS); return _bg['neon']

def dark_bg(kind='purple'):
    k = 'dark_' + kind
    if k not in _bg:
        c = {'purple': (120, 10, 70), 'blue': (0, 70, 120), 'red': (70, 5, 15), 'navy': (25, 30, 70), 'green': (30, 120, 70)}[kind]
        _bg[k] = radial(W, H, c, DARK if kind != 'red' else (5, 3, 8))
    return _bg[k]

_img = {}
def load_image(path):
    if path not in _img:
        im = Image.open(path).convert('RGBA'); im.thumbnail((2400, 2400), Image.LANCZOS); _img[path] = im
    return _img[path]

def image_bg(path, blur=0, dark=110, focus=(0.5, 0.4)):
    k = ('imgbg', path, blur, dark, focus)
    if k not in _bg:
        im = ImageOps.fit(load_image(path), (W, H), Image.LANCZOS, centering=focus)
        if blur: im = im.resize((W // 4, H // 4)).filter(ImageFilter.GaussianBlur(blur)).resize((W, H), Image.BILINEAR)
        g = Image.new('RGBA', (W, H)); gd = ImageDraw.Draw(g)
        for y in range(H):
            a = dark * 0.4 + dark * 0.9 * max(0, (y - H * 0.45) / (H * 0.55)); gd.line((0, y, W, y), fill=(10, 0, 30, int(min(235, a))))
        im.alpha_composite(g); _bg[k] = im
    return _bg[k]

# ------------------------------------------------------------------ widgets
def badge(text, size, bg, fg=BLACK):
    k = ('badge', text, size, bg, fg)
    if k in _cache: return _cache[k]
    t = txt(text, size, fg)
    im = Image.new('RGBA', (t.width + 70, t.height + 40)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 8, im.width - 1, im.height - 1), 26, fill=(0, 0, 0, 140))
    d.rounded_rectangle((0, 0, im.width - 7, im.height - 9), 26, fill=bg)
    im.alpha_composite(t, (32, 14)); _cache[k] = im; return im

def bubble(text, user, color):
    k = ('bub', text, user, color)
    if k in _cache: return _cache[k]
    t = txt(text, 48, BLACK, w='xb'); u = txt(user, 30, (120, 120, 140), w='bold')
    wd = max(t.width, u.width) + 170; ht = t.height + u.height + 64
    im = Image.new('RGBA', (wd + 8, ht + 8)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 8, wd + 6, ht + 6), 34, fill=(0, 0, 0, 120)); d.rounded_rectangle((0, 0, wd, ht), 34, fill=WHITE)
    d.ellipse((24, ht / 2 - 42, 108, ht / 2 + 42), fill=color)
    im.alpha_composite(u, (130, 22)); im.alpha_composite(t, (130, 26 + u.height + 6)); _cache[k] = im; return im

_fit = {}
def card(path, w, h, border=WHITE, z=1.0, gray=False, focus=(0.5, 0.3), bw=12):
    k = (path, w, h, gray, focus)
    if k not in _fit:
        b = ImageOps.fit(load_image(path), (int(w * 1.15), int(h * 1.15)), Image.LANCZOS, centering=focus)
        if gray: b = ImageOps.grayscale(b.convert('RGB')).convert('RGBA')
        _fit[k] = (b, rrect_mask(w, h, 36))
    b, m = _fit[k]; z = clamp(z, 1.0, 1.15); cw, ch = w * 1.15 / z, h * 1.15 / z
    cx, cy = b.width / 2, b.height / 2
    v = b.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))).resize((w, h), Image.BILINEAR)
    out = Image.new('RGBA', (w + 2 * bw + 24, h + 2 * bw + 24)); od = ImageDraw.Draw(out)
    od.rounded_rectangle((14, 20, w + 2 * bw + 14, h + 2 * bw + 20), 44, fill=(0, 0, 0, 120))
    od.rounded_rectangle((0, 0, w + 2 * bw, h + 2 * bw), 44, fill=border)
    v.putalpha(m); out.alpha_composite(v, (bw, bw)); return out

def phone(title, status, status_col=(180, 180, 200), ring=False, t=0.0, w=520, h=980):
    im = Image.new('RGBA', (w, h)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 70, fill=(20, 20, 26)); d.rounded_rectangle((18, 18, w - 19, h - 19), 56, fill=(8, 10, 20))
    d.rounded_rectangle((w // 2 - 70, 34, w // 2 + 70, 62), 14, fill=(0, 0, 0))
    a = txt(title, 56, WHITE); im.alpha_composite(a, (w // 2 - a.width // 2, 180))
    b = txt(status, 44, status_col, w='bold'); im.alpha_composite(b, (w // 2 - b.width // 2, 270))
    r = 90 + (12 * math.sin(t * 10) if ring else 0)
    d.ellipse((w // 2 - r, 470 - r, w // 2 + r, 470 + r), fill=(60, 60, 80)); d.ellipse((w // 2 - 70, 400, w // 2 + 70, 540), fill=(90, 90, 110))
    d.ellipse((60, h - 230, 180, h - 110), fill=GREEN); d.ellipse((w - 180, h - 230, w - 60, h - 110), fill=RED)
    return im

def timer_ring(fr, cx, cy, secs_left, total=10, r=150):
    d = ImageDraw.Draw(fr)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(15, 10, 25), outline=(60, 50, 80), width=16)
    d.arc((cx - r, cy - r, cx + r, cy + r), -90, -90 + 360 * (secs_left / total), fill=RED if secs_left < total * 0.35 else YEL, width=22)
    put(fr, txt(str(int(math.ceil(max(0, secs_left)))), int(r * 1.2), WHITE, 10), cx, cy)

def choice_card(letter, line1, line2, color):
    im = Image.new('RGBA', (470, 720)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 16, 469, 719), 50, fill=(0, 0, 0, 120)); d.rounded_rectangle((0, 0, 459, 703), 50, fill=color)
    L = txt(letter, 260, WHITE, 14, BLACK); im.alpha_composite(L, (230 - L.width // 2, 40))
    for i, line in enumerate([line1, line2]):
        if not line: continue
        a = txt(line, 54, WHITE, 6, BLACK); im.alpha_composite(a, (230 - a.width // 2, 470 + i * 80))
    return im

def calendar(month, day, year=''):
    k = ('cal', month, day, year)
    if k in _cache: return _cache[k]
    im = Image.new('RGBA', (560, 640)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 16, 559, 639), 40, fill=(0, 0, 0, 120)); d.rounded_rectangle((0, 0, 549, 629), 40, fill=WHITE)
    d.rounded_rectangle((0, 0, 549, 170), 40, fill=RED); d.rectangle((0, 120, 549, 170), fill=RED)
    for rx in (140, 410): d.rounded_rectangle((rx - 16, -30, rx + 16, 40), 12, fill=(60, 60, 70))
    t1 = txt(f"{month} {year}".strip(), 56, WHITE); im.alpha_composite(t1, (275 - t1.width // 2, 60))
    t2 = txt(str(day), 300, (30, 30, 40)); im.alpha_composite(t2, (275 - t2.width // 2, 240))
    _cache[k] = im; return im

def mascot():
    """Generic channel mascot: cartoon gamer with backwards cap + sunglasses (original design)."""
    if 'mascot' in _cache: return _cache['mascot']
    SK = 2; P = lambda *a: tuple(int(v * SK) for v in a)
    im = Image.new('RGBA', (900 * SK, 1200 * SK)); d = ImageDraw.Draw(im)
    skin, shade = (214, 160, 120), (180, 125, 90)
    d.ellipse(P(120, 800, 780, 1500), fill=YEL); d.ellipse(P(330, 800, 570, 900), fill=(230, 180, 0))
    d.rectangle(P(395, 640, 505, 830), fill=shade)
    d.ellipse(P(282, 470, 330, 570), fill=shade); d.ellipse(P(570, 470, 618, 570), fill=shade)
    d.ellipse(P(300, 270, 600, 690), fill=skin)
    d.chord(P(292, 220, 608, 560), 180, 360, fill=PURPLE); d.ellipse(P(240, 360, 360, 420), fill=(90, 30, 190)); d.rectangle(P(292, 385, 608, 405), fill=(90, 30, 190))
    d.rounded_rectangle(P(335, 465, 445, 525), 22 * SK, fill=(15, 15, 25)); d.rounded_rectangle(P(455, 465, 565, 525), 22 * SK, fill=(15, 15, 25))
    d.line(P(445, 480, 455, 480), fill=(15, 15, 25), width=8 * SK)
    d.line(P(350, 478, 380, 470), fill=PINK, width=6 * SK); d.line(P(470, 478, 500, 470), fill=PINK, width=6 * SK)
    d.line(P(452, 530, 440, 580, 462, 584), fill=shade, width=5 * SK); d.arc(P(395, 580, 515, 640), 15, 140, fill=(120, 50, 40), width=8 * SK)
    d.rounded_rectangle(P(300, 1000, 600, 1130), 60 * SK, fill=(40, 40, 60)); d.ellipse(P(330, 1040, 380, 1090), fill=(90, 90, 120))
    for bx, by, c in [(520, 1040, PINK), (550, 1065, CYAN), (490, 1065, YEL), (520, 1090, (60, 220, 120))]:
        d.ellipse(P(bx - 12, by - 12, bx + 12, by + 12), fill=c)
    _cache['mascot'] = im.resize((900, 1200), Image.LANCZOS); return _cache['mascot']

# ------------------------------------------------------------------ subtitles
class Subtitles:
    """Word-wrapped, per-word colored captions that pop in. subs: [[start, end, "TEXT"], ...]"""
    def __init__(self, subs, highlights=None, y=1470, size=76):
        self.subs = subs; self.hl = {k.upper(): col(v) for k, v in (highlights or {}).items()}; self.y = y; self.size = size; self._img = {}
    def _render(self, i):
        if i in self._img: return self._img[i]
        words = self.subs[i][2].split(); f = font(self.size); sp = 22; maxw = 960; lines, cur, cw = [], [], 0
        for wd in words:
            ww = f.getlength(wd)
            if cur and cw + sp + ww > maxw: lines.append(cur); cur, cw = [], 0
            cur.append(wd); cw += (sp if cw else 0) + ww
        if cur: lines.append(cur)
        lh = int(self.size * 1.26); im = Image.new('RGBA', (1060, lh * len(lines) + 30)); d = ImageDraw.Draw(im)
        for li, ln in enumerate(lines):
            tw = sum(f.getlength(x) for x in ln) + sp * (len(ln) - 1); x = (1060 - tw) / 2; y = 10 + li * lh
            for wd in ln:
                key = wd.strip('",.!?:;…').upper()
                c = self.hl.get(wd.upper(), self.hl.get(key, WHITE))
                d.text((x, y), wd, font=f, fill=c, stroke_width=9, stroke_fill=BLACK); x += f.getlength(wd) + sp
        self._img[i] = im; return im
    def draw(self, fr, T):
        for i, (a, b, _) in enumerate(self.subs):
            if a <= T < b: put(fr, self._render(i), W / 2, self.y, lerp(0.82, 1.0, back((T - a) / 0.16)))
