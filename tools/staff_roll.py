"""STAFF.STR credit roll in English. The roll is white antialiased text scrolling up at a constant V px per frame over
black, with pictures and wave effects on the left and top. Stitching every frame at y + V*n gives one tall strip of the
Japanese roll (`strip`); its ink bands are the roll's lines, matched in order to script/credits.tsv (`layout`). Each
frame is re-lettered (`paint`): Japanese ink pixels are filled from a frame where the text has scrolled past that
spot, then the English line is drawn at its band's position. tools/staff.py writes the frames back.

usage: staff_roll.py strip | layout [--print] | shot N OUT.png
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import staff

V = 2.225  # px per frame: best stitch over every 4th frame (sharpest strip), steady across the whole roll
FRAMES = staff.FRAMES
STRIP = ROOT / "work" / "fmv" / "STAFF" / "strip.png"
X0 = 72  # text column: the roll's ink is right of this (pictures sit left of it)


def text_lum(rgb):
    """Brightness of achromatic pixels (the roll's text is white/grey), 0 elsewhere."""
    a = rgb.astype(np.int16)
    lo, hi = a.min(axis=2), a.max(axis=2)
    return np.where(hi - lo < 40, lo, 0).astype(np.uint8)


STOP = 2340  # last moving frame; the final card then holds and fades out


def off(n):
    return int(round(V * min(n, STOP)))


def pngs():
    return sorted(Path(FRAMES).glob("f*.png"))


def strip():
    """Japanese roll as one image: per strip row, the 30th percentile of its text brightness over the frames that show
    it in mid-screen, so moving pictures and waves drop out and the static text stays."""
    files = pngs()
    lum = np.stack([text_lum(np.array(Image.open(p).convert("RGB"))) for p in files])
    h = off(len(files)) + 240
    out = np.zeros((h, 320), np.uint8)
    for y in range(h):
        rows = [lum[n, y - off(n)] for n in range(len(files)) if 30 <= y - off(n) < 210]
        if rows:
            out[y] = np.percentile(np.stack(rows), 30, axis=0)
    STRIP.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out).save(STRIP)
    return out


def load_strip():
    return np.array(Image.open(STRIP)) if STRIP.exists() else strip()


def bands(s, thr=90):
    """[(y0, y1, [(x0, x1) segments])] ink bands of the strip's text column; segments split at 14+ px gaps."""
    ink = s[:, X0:] > thr
    rows = ink.any(axis=1)
    out, y = [], 0
    while y < len(rows):
        if not rows[y]:
            y += 1
            continue
        y1 = y
        while y1 < len(rows) and rows[y1]:
            y1 += 1
        cols = np.flatnonzero(ink[y:y1].any(axis=0)) + X0
        segs, a = [], cols[0]
        for p, q in zip(cols, cols[1:]):
            if q - p > 14:
                segs.append((int(a), int(p) + 1))
                a = q
        segs.append((int(a), int(cols[-1]) + 1))
        out.append((y, y1, segs))
        y = y1
    return out


MID = 212  # between the cast's role column (right-aligned, ends ~198) and actor column (starts ~226)
CENTRED = ("head", "sub", "name")


def runs(rows):
    out, y = [], 0
    while y < len(rows):
        if rows[y]:
            y1 = y
            while y1 < len(rows) and rows[y1]:
                y1 += 1
            out.append((y, y1))
            y = y1
        y += 1
    return out


def credits():
    return [ln.split("\t") for ln in (ROOT / "script" / "credits.tsv").read_text(encoding="utf-8").splitlines()[1:]]


def layout(s=None, thr=90):
    """[(credits row, y0, y1, x0, x1)]: each credits.tsv row's Japanese line in the strip. Centred lines (head, sub,
    name) cross MID; roles sit left of it, actors right. Rows are taken from three queues in order, then checked: the
    lines run down the strip in credits order and each actor sits beside its roles."""
    s = load_strip() if s is None else s
    ink = s > thr
    ext = lambda y0, y1, a, b: tuple(int(v) + a for v in np.flatnonzero(ink[y0:y1, a:b].any(axis=0))[[0, -1]])  # noqa: E731
    left = [(y0, y1, *ext(y0, y1, X0, MID)) for y0, y1 in runs(ink[:, X0:MID].any(axis=1))]
    right = [(y0, y1, *ext(y0, y1, MID, 320)) for y0, y1 in runs(ink[:, MID:].any(axis=1))]
    rows = credits()
    out = {}
    for row in (r for r in rows if r[2] != "actor"):  # every non-actor row is the next line left of MID
        assert left, f"no line left for credits row {row[0]} {row[3]}"
        y0, y1, a, b = left.pop(0)
        r = next((r for r in right if r[0] < y1 and y0 < r[1] and r[2] <= MID + 6), None)
        if row[2] == "role":
            assert b < MID - 6 and not r, f"role {row[3]} at {y0} reaches the middle"
        elif r:  # a centred line crossing MID (the final card is centred on the screen, left of it)
            right.remove(r)
            y0, y1, b = min(y0, r[0]), max(y1, r[1]), r[3]
        out[row[0]] = (row, y0, y1, a, b + 1)
    for row in (r for r in rows if r[2] == "actor"):
        y0, y1, a, b = right.pop(0)
        out[row[0]] = (row, y0, y1, a, b + 1)
    assert not left and not right, (left, right)
    out = [out[r[0]] for r in rows]
    last = -1
    for row, y0, y1, *_ in out:
        if row[2] != "actor":
            assert y0 > last, f"credits row {row[0]} {row[3]} out of order"
            last = y0
    for row, y0, y1, *_ in out:
        if row[2] == "actor":
            span = [(a, b) for r, a, b, *_ in out if r[1] == row[1] and r[2] == "role"]
            assert span[0][0] <= (y0 + y1) / 2 <= span[-1][1], f"actor {row[3]} not beside its roles"
    return out


FONT = ROOT / "fonts" / "LiberationSans-Bold.ttf"
SIZE = 12
RIGHT = 312  # keep 8 px of the 320 px picture clear on the right (overscan)
GAP = 14     # between a role's right edge and its actor
FILL_FROM = (7, -7, 10, -10, 13, -13, 4, -4, 16, -16, 20, -20)  # frames tried for the background behind Japanese ink


def english_strip(lay=None, h=None):
    """(ink, halo) float masks the size of the strip with every English line drawn where its Japanese line is."""
    lay = layout() if lay is None else lay
    h = h or load_strip().shape[0]
    font = ImageFont.truetype(str(FONT), SIZE)
    im = Image.new("L", (320, h))
    d = ImageDraw.Draw(im)
    groups = {}
    for row, y0, y1, a, b in lay:
        groups.setdefault(row[1], []).append((row, y0, y1, a, b))
    for g in groups.values():
        actors = [(row, a) for row, _, _, a, _ in g if row[2] == "actor"]
        ax = min([a for _, a in actors] + [RIGHT - int(max(font.getlength(r[4]) for r, _ in actors))]) if actors else 0
        rr = min(max(b for row, _, _, _, b in g if row[2] == "role"), ax - GAP) if actors else 0
        for row, y0, y1, a, b in g:
            kind, text, base = row[2], row[4], y1 - 2
            w = font.getlength(text if kind != "sub" else f"<{text}>")
            if kind == "role":
                x = rr - w
            elif kind == "actor":
                x = ax
            else:  # centred on the Japanese line, pulled left when the English (and its ◆) would pass RIGHT
                x = min((a + b) / 2 - w / 2, RIGHT - w - (14 if kind == "head" else 0))
            d.text((round(x), base), text if kind != "sub" else f"<{text}>", font=font, fill=255, anchor="ls")
            if kind == "head":  # ◆ either side, as the Japanese (no ◆ glyph in the font)
                cy = (y0 + y1) / 2
                for cx in (x - 10, x + w + 9):
                    d.polygon([(cx, cy - 4), (cx + 4, cy), (cx, cy + 4), (cx - 4, cy)], fill=255)
    halo = im.point(lambda v: 255 if v > 40 else 0).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(1))
    return np.array(im) / 255.0, np.clip(np.array(halo) / 255.0 * 1.4, 0, 1)


class Painter:
    """paint(n, rgb) for staff.rewrite: every frame re-lettered."""

    def __init__(self):
        s = load_strip()
        self.files = pngs()
        mask = Image.fromarray(((s > 24) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))
        self.mask = np.array(mask) > 0
        self.mask[:, :X0 - 8] = False
        self.ink, self.halo = english_strip(h=s.shape[0])
        self.cache = {}
        ref = text_lum(self.frame(STOP))[:, X0:].astype(float).sum()
        self.fade = lambda rgb: min(1.0, text_lum(rgb)[:, X0:].astype(float).sum() / ref)  # noqa: E731

    def frame(self, n):
        if n not in self.cache:
            if len(self.cache) > 48:
                self.cache.pop(min(self.cache, key=lambda k: abs(k - n) * -1))
            self.cache[n] = np.array(Image.open(self.files[n]).convert("RGB"))
        return self.cache[n]

    def window(self, a, n):
        o = off(n)
        out = np.zeros((240,) + a.shape[1:], a.dtype)
        part = a[o:o + 240]
        out[:len(part)] = part
        return out

    def __call__(self, n, rgb):
        rgb = rgb.copy()
        todo = self.window(self.mask, n)
        f = self.fade(rgb) if n > STOP else 1.0
        for k in FILL_FROM:
            if not todo.any():
                break
            if 0 <= n + k < len(self.files) and off(n + k) != off(n):
                take = todo & ~self.window(self.mask, n + k)
                rgb[take] = self.frame(n + k)[take]
                todo &= ~take
        rgb[todo] = 0
        ink, halo = self.window(self.ink, n)[..., None] * f, self.window(self.halo, n)[..., None] * f
        out = rgb * (1 - 0.85 * halo)
        return (out * (1 - ink) + 255 * ink).round().clip(0, 255).astype(np.uint8)


def rewrite(track):
    """build.py: STAFF.STR re-lettered in English (~20 min: every frame is re-encoded)."""
    return staff.rewrite(track, Painter())


if __name__ == "__main__":
    cmd = sys.argv[1:2]
    if cmd == ["strip"]:
        s = strip()
        print(STRIP, s.shape)
    elif cmd == ["bands"]:
        for b in bands(load_strip()):
            print(*b)
    elif cmd == ["layout"]:
        for row, *box in layout():
            print(*box, row[2], row[3], row[4], sep="\t")
    elif cmd == ["shot"]:  # shot OUT_DIR N.. : painted frames, original beside each
        p, out = Painter(), Path(sys.argv[2])
        out.mkdir(parents=True, exist_ok=True)
        for n in map(int, sys.argv[3:]):
            o = p.frame(n)
            Image.fromarray(np.concatenate([o, p(n, o)], axis=1)).save(out / f"f{n:05d}.png")
    elif cmd == ["drift"]:  # how far each frame's text sits from off(n), against the strip
        s = load_strip().astype(np.int16)
        for n, p in enumerate(pngs()):
            if n % 50:
                continue
            lum = text_lum(np.array(Image.open(p).convert("RGB"))).astype(np.int16)
            o = off(n)
            err = {d: np.abs(lum[40:200, X0:] - s[o + d + 40:o + d + 200, X0:]).mean() for d in range(-3, 4)
                   if o + d >= 0}
            print(n, min(err, key=err.get), round(min(err.values()), 2))
    else:
        sys.exit(__doc__)
