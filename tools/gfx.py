"""Graphics-text edits on TIM pixels, keyed by blob sha1 so every copy of a sprite changes (AGENTS.md gotcha).

The marker build paints each script/graphics.tsv rect with its row number (line of graphics.tsv counting from 1 under
the header; `python tools/gfx.py` prints the map). The spike build letters script/spike.tsv in English through
typeset(). Pixels only change inside a row's rect, through tim.with_pixels, so the STP bit and the CLUT stay.
Ported from the desu-yo project's tools/gfx.py (same fonts, same rules)."""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gfx_index
import gfx_script
import tim

KEEP_FORMS = {"keep"}
J10 = 1400 / 75  # Jersey 10's native pixel grid (upm / pixel unit); 20 px doubles some columns (desu-yo D14)
# One font and size per label class: (file in fonts/, size, 1 px outline). docs/decisions.md D10.
CLASSES = {
    "title": ("Bangers-Regular.ttf", 34, True),       # big screen titles (モード セレクト), art lettering
    "big": ("Bangers-Regular.ttf", 28, True),         # race HUD words (ゴール), 30+ px rows
    "menu": ("Bangers-Regular.ttf", 22, 2),           # 20+ px menu rows: fill, light inner and dark outer outline
    "bar": ("LiberationSans-Bold.ttf", 14, True),     # buttons and bars: Bangers garbles below 18 px (desu-yo D16)
    "sign": ("Jersey10-Regular.ttf", J10, 2),         # names, courses, machines, messages, briefings: outlined art
    "label": ("Jersey10-Regular.ttf", J10, False),    # plain text on a panel (machine descriptions), small labels
    "label1": ("Jersey10-Regular.ttf", J10, True),    # one outline: names 1-2 px too wide for `sign`, on see-through sprites
    "small": ("Tiny5.ttf", 8, False),                 # 8-10 px rows (copyright); Tiny5's native 8 px grid, cap 5
    # Tiny5 drawn twice as tall (4th field: vertical scale): ~4 px a letter at cap 10, for names in kana-sized boxes
    "narrow": ("Tiny5.ttf", 8, True, 2),              # one outline (character names in 24-64 px name plates)
    "narrowlabel": ("Tiny5.ttf", 8, False, 2),        # plain like `label`
    "tallsign": ("Jersey10-Regular.ttf", J10, 2, 2),  # `sign` twice as tall: machine names in 32-40 px rows (ranking)
    "tallsign1": ("Jersey10-Regular.ttf", J10, True, 2),  # one outline: a name 1-2 px too wide for `tallsign`
    "credit": ("Jersey15-Regular.ttf", 15, True),
}
# Classes whose one outline is drawn 2 px thick (the Japanese title art has a 3-4 px outline; phase 8).
THICK = {"title", "big"}
# graphics.tsv form -> class; a translation row may name another class
FORM_CLASS = {"title": "title", "art": "title", "hud": "big", "menu": "bar", "cup": "bar", "lap": "bar", "team": "label",
              "pause": "bar", "stat": "sign", "badge": "bar", "movie": "bar", "song": "bar", "fix": "bar",
              "machine": "sign", "course": "sign", "name": "sign", "plate": "sign", "label": "label",
              "msg": "sign", "brief": "sign", "panel": "label", "copy": "small"}


def class_of(r):
    """A graphics.tsv row's default class: its form's, except menu rows 20+ px tall (mode select buttons)."""
    return "menu" if r.form == "menu" and r.h >= 20 else FORM_CLASS[r.form]
DIGITS = {
    "0": ("111", "101", "101", "101", "111"),
    "1": ("010", "110", "010", "010", "111"),
    "2": ("111", "001", "111", "100", "111"),
    "3": ("111", "001", "111", "001", "111"),
    "4": ("101", "101", "111", "001", "001"),
    "5": ("111", "100", "111", "001", "111"),
    "6": ("111", "100", "111", "101", "111"),
    "7": ("111", "001", "010", "010", "010"),
    "8": ("111", "101", "111", "101", "111"),
    "9": ("111", "101", "111", "001", "111"),
    ".": ("000", "000", "000", "000", "010"),
}


def ink_indices(t):
    """(dark, bright) CLUT 0 indices, skipping the transparent colour 0 (a black that is non-zero is opaque)."""
    n = 2 ** t.bpp
    pal = list(t.clut[:n]) if t.clut else []
    used = [(i, c) for i, c in enumerate(pal) if c]
    if not used:
        return 1, n - 1
    luma = lambda c: (c & 31) * 2 + ((c >> 5) & 31) * 4 + ((c >> 10) & 31)  # noqa: E731
    return min(used, key=lambda e: luma(e[1]))[0], max(used, key=lambda e: luma(e[1]))[0]


def paint_marker(vals, width, rect, label, dark, bright):
    """Solid dark rect with a bright 1 px frame, filled with the label repeated, so a clipped edge or a stray neighbour
    shows at once in game. Wrapped into lines when the rect is too narrow for one copy."""
    x0, y0, w, h = rect
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            edge = y in (y0, y0 + h - 1) or x in (x0, x0 + w - 1)
            vals[y * width + x] = bright if edge else dark
    per_line = max(1, (w - 2) // 4)
    text = (label + " ") * (per_line * h // (len(label) + 1) + 2)
    for ln in range((h - 2) // 6 or 1):
        for ci, ch in enumerate(text[ln * per_line:(ln + 1) * per_line]):
            for gy, bits in enumerate(DIGITS.get(ch, ())):
                for gx, b in enumerate(bits):
                    px, py = x0 + 1 + ci * 4 + gx, y0 + 1 + ln * 6 + gy
                    if b == "1" and px < x0 + w - 1 and py < y0 + h - 1:
                        vals[py * width + px] = bright


def pixel_width(t):
    return t.px_wh[0] * {4: 4, 8: 2, 16: 1}[t.bpp]


def canon_shas():
    """{canonical TIM id: blob sha1} from the original disc."""
    return {i: h for i, h, _, c in gfx_index.index(gfx_index.tims()) if i == c}


def by_blob(items):
    """[(row, payload)] -> {sha1: [(row, payload)]}, through each row's canonical TIM id (graphics.tsv column file)."""
    shas, out = canon_shas(), {}
    for r, p in items:
        out.setdefault(shas[r.file], []).append((r, p))
    return out


def marker_edits():
    """{sha1: fn(blob) -> blob} painting every non-keep row with its row number. A TIM holding one row (not lettering
    in art) is painted whole, so the shot shows how much of it the game draws: the row's room to grow (width gate,
    tools/budgets.py)."""
    rows = [(r, str(i + 1)) for i, r in enumerate(gfx_script.rows()) if r.form not in KEEP_FORMS]

    def paint(b, rs):
        if len(rs) == 1 and rs[0][0].form != "art":
            t = tim.parse(b, strict=False)
            return marked(b, [((0, 0, pixel_width(t), t.px_wh[1]), rs[0][1])])
        return marked(b, [((r.x, r.y, r.w, r.h), lab) for r, lab in rs])
    return {h: (lambda b, rs=rs: paint(b, rs)) for h, rs in by_blob(rows).items()}


def marked(data, rects):
    """data (a TIM file) with every rect painted."""
    t = tim.parse(data, strict=False)
    vals = tim.pixels(t, data)
    width = pixel_width(t)
    dark, bright = ink_indices(t)
    for rect, label in rects:
        x, y, w, h = rect
        assert x + w <= width and y + h <= t.px_wh[1], f"rect {rect} outside {width}x{t.px_wh[1]}"
        paint_marker(vals, width, rect, label, dark, bright)
    return tim.with_pixels(t, data, vals)


def glyphs(text, form):
    """(ink, ring 1, ring 2) boolean arrays of the text in its class style, cropped to the ink; rings are empty when the
    class has fewer outlines. "|" breaks a line."""
    name, size, outline, *yscale = CLASSES[form]
    font = ImageFont.truetype(str(ROOT / "fonts" / name), size)
    lines = text.split("|")
    pad = int(size)  # wide margins: italic overhang (Bangers) reaches past the advance width; the ink is cropped below
    w = max(int(font.getlength(ln)) for ln in lines) + 2 * pad
    pitch = sum(font.getmetrics())
    img = Image.new("1", (w, pitch * len(lines) + 2 * pad))
    d = ImageDraw.Draw(img)
    d.fontmode = "1"  # no antialiasing: smoothed small text turns to mush in a 16-colour palette
    for n, ln in enumerate(lines):
        d.text((w // 2, pad + n * pitch), ln, font=font, fill=1, anchor="ma")
    ink = np.array(img)
    rows, cols = np.flatnonzero(ink.any(axis=1)), np.flatnonzero(ink.any(axis=0))
    ink = ink[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1]
    if yscale:
        ink = np.repeat(ink, yscale[0], axis=0)
    rings = []
    for _ in range(2 if form in THICK else int(outline)):  # 1: one; 2: inner light, outer dark (menu art); THICK: 2 px
        ink = np.pad(ink, 1)
        rings = [np.pad(r, 1) for r in rings]
        inside = ink | np.any(rings, axis=0) if rings else ink
        grown = np.zeros_like(ink)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                grown |= np.roll(np.roll(inside, dy, 0), dx, 1)
        rings.append(grown & ~inside)
    rings += [np.zeros_like(ink)] * (2 - len(rings))
    return ink, rings[0], rings[1]


def row_size(text, form):
    """The width gate: (w, h) pixels this text takes in its class; typeset() refuses a rect smaller than this."""
    return glyphs(text, form)[0].shape[::-1]


def mode(vals):
    v, c = np.unique(vals, return_counts=True)
    return int(v[c.argmax()])


def see_through(px, clut):
    return clut[0] == 0 and (px == 0).mean() >= 0.1


def inpainted(px, known):
    """px with every pixel not `known` filled from its nearest known neighbour, growing inwards (left/right before
    up/down, so vertical gradients and horizontal bands carry across): clears lettering painted into a picture."""
    out, k = px.copy(), known.copy()
    if not k.any():
        return out
    while not k.all():
        new = np.zeros_like(k)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):  # last assignment wins: horizontal neighbours first
            sk = np.zeros_like(k)
            so = np.zeros_like(out)
            ys, yd = (slice(0, -dy or None), slice(dy, None)) if dy >= 0 else (slice(-dy, None), slice(0, dy))
            xs, xd = (slice(0, -dx or None), slice(dx, None)) if dx >= 0 else (slice(-dx, None), slice(0, dx))
            sk[yd, xd], so[yd, xd] = k[ys, xs], out[ys, xs]
            take = ~k & sk
            out[take] = so[take]
            new |= take
        k |= new
    return out


def sampled_inks(px, clut, margin=None, ink=None):
    """(background per row, fill profile, outline) indices of a rect of the original. Background: commonest of the
    margin beside the rect (or the rect's end columns), per row when no one index dominates (labels on gradients).
    Fill profile: one index per stroke row, top to bottom (or one index when one dominates). ink: the lettering's
    pixels when the caller knows them (a textured background, typeset())."""
    ends = np.concatenate([px[:, :2], px[:, -2:]], axis=1)
    side = ends if margin is None or not margin.size else margin
    if see_through(px, clut):  # clear to transparent
        bg = np.zeros(len(px), int)
    elif (ends == mode(ends)).mean() > max((side == mode(side)).mean(), 0.6) or (
            (side == mode(side)).mean() < 0.6 and mode(ends) == mode(px) and (ends == mode(ends)).mean() >= 0.5):
        bg = np.full(len(px), mode(ends))  # the rect's own ends: a rect inside a frame (movie tabs) sees the frame
    elif (side == mode(side)).mean() >= 0.6:
        bg = np.full(len(px), mode(side))
    else:
        bg = np.array([mode(row) for row in side])
    ink = px != bg[:, None] if ink is None else ink
    if not ink.any():
        return bg, bg[:1], int(bg[0])
    # Outline: the commonest ink on the strokes' edge (an ink pixel beside background or the rect's edge). Fill: the
    # other inks, per row top to bottom of the strokes (palette gradients), each row the commonest of it and its two
    # neighbours, so a row crossing a horizontal stroke's outline doesn't turn into a band; typeset() stretches this
    # profile over the English glyph's height (phase 8: per-row fill at the same y striped every short glyph).
    p = np.pad(ink, 1)
    edge = ink & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
    # the ink that lies most on edges, among those with a fair share of them: a drop shadow or highlight beside a
    # solid stroke (SAVE#80) is the outline, not the solid colour, though the solid colour also touches the edge
    v, c = np.unique(px[edge], return_counts=True)
    cand = [i for i, n in zip(v, c) if n >= 0.15 * c.sum()] or [v[c.argmax()]]
    on_edge = lambda i: (edge & (px == i)).sum() / (px[ink] == i).sum()  # noqa: E731
    line = int(max(cand, key=on_edge))
    core = ink & ~edge
    if core.any() and (px[core] == line).mean() > 0.5 and len(v) > 1:
        # the edge ink is also most of the strokes' inside: a solid letter with a thin highlight or shadow (SAVE#80)
        return bg, np.array([line]), int(max((i for i in v if i != line), key=on_edge))
    inner = ink & (px != line)
    if not inner.any():
        return bg, np.array([line]), line
    have = np.flatnonzero(inner.any(axis=1))
    fill = np.array([mode(px[max(y - 1, 0):y + 2][inner[max(y - 1, 0):y + 2]]) for y in range(have[0], have[-1] + 1)])
    if (fill == mode(fill)).mean() >= 0.6:
        fill = np.array([mode(fill)])
    return bg, fill, line


def grown(rect, size, box):
    """rect widened/heightened about its centre to hold size (w, h), kept inside box (w, h)."""
    (x, y, w, h), (gw, gh), (bw, bh) = rect, size, box
    nw, nh = max(w, gw), max(h, gh)
    return (min(max(0, x - (nw - w) // 2), bw - nw), min(max(0, y - (nh - h) // 2), bh - nh), nw, nh)


def typeset(data, rows, grow=False):
    """data (a TIM file) with each (rect, text, form) rect cleared and lettered, centred. grow: a rect too small for its
    text widens about its centre inside the TIM (only for a TIM's one row: fit.py's `grow` verdict, room = whole TIM).
    Raises ValueError on overflow: English is never clipped silently."""
    t = tim.parse(data, strict=False)
    assert t and t.bpp in (4, 8), "not a CLUT TIM"
    width = pixel_width(t)
    px = np.array(tim.pixels(t, data), dtype=np.int32).reshape(t.px_wh[1], width)
    for row in rows:
        (x, y, w, h), text, form = row[:3]
        left = len(row) > 3 and row[3]  # left-anchored like the Japanese (LEFT_FORMS): x kept, grows to the right
        assert x + w <= width and y + h <= t.px_wh[1], f"rect {x, y, w, h} outside {width}x{t.px_wh[1]}"
        ink, halo, outer = glyphs(text, form)
        gh, gw = ink.shape
        if grow and (gw > w or gh > h) and gw <= width and gh <= t.px_wh[1]:
            gx, y, nw, h = grown((x, y, w, h), (gw, gh), (width, t.px_wh[1]))
            x, w = (min(x, width - nw), nw) if left else (gx, nw)
        if gw > w or gh > h:
            raise ValueError(f"{text!r} is {gw}x{gh} in class {form}, rect is {w}x{h}")
        margin = np.concatenate([px[y:y + h, max(x - 3, 0):x], px[y:y + h, x + w:x + w + 3]], axis=1)
        orig = px[y:y + h, x:x + w].copy()
        known = None
        if len(row) > 4 and row[4]:
            # lettering painted into a picture or pattern (form art): the lettering is the inks a ring 3-10 px around
            # the rect doesn't use (the by-eye rect may cut the outline); paint it out from its surroundings instead
            # of clearing to a per-row colour (phase 8: bands across the ranking sky, a flat hole in the skull pattern)
            ring = px[max(y - 10, 0):y + h + 10, max(x - 10, 0):x + w + 10].copy()
            iy, ix = y - max(y - 10, 0), x - max(x - 10, 0)
            ring[max(iy - 3, 0):iy + h + 3, max(ix - 3, 0):ix + w + 3] = -1
            known = np.isin(orig, ring[ring >= 0])
            lettering = ~known
            near = lettering  # paint out a drop shadow within 5 px of it too
            for _ in range(5):
                near = near | np.roll(near, 1, 0) | np.roll(near, -1, 0) | np.roll(near, 1, 1) | np.roll(near, -1, 1)
            v, c = np.unique(ring[ring >= 0], return_counts=True)
            known &= ~near | np.isin(orig, v[c >= 0.02 * c.sum()])  # a colour common around it is the picture's
        bg, fill, line = sampled_inks(orig, t.clut, margin, None if known is None else lettering)
        cell = px[y:y + h, x:x + w]
        cell[:] = bg[:, None] if known is None else inpainted(orig, known)
        oy, ox = (h - gh) // 2, 0 if left else (w - gw) // 2
        box = cell[oy:oy + gh, ox:ox + gw]
        if form in THICK:
            halo = halo | outer
        elif outer.any():  # solid fill (no per-row gradient), lightest ink inside, darkest outside
            inks = [i for i in np.unique(orig[orig != bg[:, None]]).tolist()]
            luma = lambda i: (t.clut[i] & 31) * 2 + ((t.clut[i] >> 5) & 31) * 4 + ((t.clut[i] >> 10) & 31)  # noqa: E731
            dark, light = min(inks, key=luma), max(inks, key=luma)
            mid = orig[~np.isin(orig, [dark, light]) & (orig != bg[:, None])]
            box[outer], box[halo] = dark, light
            box[ink] = mode(mid) if mid.size else mode(fill)  # the commonest ink between the two outlines
            continue
        box[halo] = line
        prof = fill[np.round(np.arange(gh) * (len(fill) - 1) / max(gh - 1, 1)).astype(int)]
        box[ink] = np.broadcast_to(prof[:, None], ink.shape)[ink]
    return tim.with_pixels(t, data, px.reshape(-1).tolist())


EN = ROOT / "script" / "graphics_en.tsv"
# Forms drawn as on-screen lists whose Japanese starts at the TIM's left edge (pause menu, course, machine and song
# lists, phase 8): English keeps that anchor, else the items' left edges go ragged.
LEFT_FORMS = {"pause", "course", "machine", "song"}


def left_anchored(r):
    return r.form in LEFT_FORMS and r.x <= 8  # every list row starts at x 0, 1 or 8 (GP course list: 8)


def spike_edits(path=ROOT / "script" / "spike.tsv"):
    """{sha1: fn(blob) -> blob} lettering a translation tsv (columns id, en, class, rect; empty rect = the row's):
    script/spike.tsv, or EN for the English build. A TIM's only row may grow into the TIM (fit.py gates it)."""
    by_id = {r.id: r for r in gfx_script.rows()}
    items = []
    for ln in path.read_text(encoding="utf-8").splitlines()[1:]:
        rid, en, form, rect = (ln.split("\t") + [""] * 4)[:4]
        r = by_id[rid]
        items.append((r, (tuple(map(int, rect.split(","))) if rect else (r.x, r.y, r.w, r.h), en,
                          form or class_of(r), left_anchored(r), r.form == "art")))
    return {h: (lambda b, rs=rs: typeset(b, [p for _, p in rs], grow=len(rs) == 1 and rs[0][0].form != "art"))
            for h, rs in by_blob(items).items()}


if __name__ == "__main__":
    for i, r in enumerate(gfx_script.rows()):
        print(i + 1, r.id, r.jp, sep="\t")
