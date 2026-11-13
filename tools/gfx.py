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
    "credit": ("Jersey15-Regular.ttf", 15, True),
}
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
    for _ in range(int(outline)):  # 1: one outline; 2: an inner light and an outer dark one (the menu art's style)
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


def sampled_inks(px, clut, margin=None):
    """(background per row, fill per row, outline) indices of a rect of the original; per row because labels sit on
    palette gradients. Background: commonest of the margin beside the rect (or the rect's end columns), per row when
    no one index dominates. Fill: commonest inside the strokes. Outline: the commonest other ink."""
    ends = np.concatenate([px[:, :2], px[:, -2:]], axis=1)
    side = ends if margin is None or not margin.size else margin
    if clut[0] == 0 and (px == 0).mean() >= 0.1:  # see-through sprite: clear to transparent
        bg = np.zeros(len(px), int)
    elif (side == mode(side)).mean() >= 0.6:
        bg = np.full(len(px), mode(side))
    else:
        bg = np.array([mode(row) for row in side])
    ink = px != bg[:, None]
    if not ink.any():
        return bg, bg, int(bg[0])
    luma = lambda i: (clut[i] & 31) * 2 + ((clut[i] >> 5) & 31) * 4 + ((clut[i] >> 10) & 31)  # noqa: E731
    core = np.zeros_like(ink)
    core[1:-1, 1:-1] = ink[1:-1, 1:-1] & ink[:-2, 1:-1] & ink[2:, 1:-1] & ink[1:-1, :-2] & ink[1:-1, 2:]
    if not core.any():
        fill = np.full(len(px), max(np.unique(px[ink]).tolist(), key=luma))
    elif (px[core] == mode(px[core])).mean() >= 0.6:
        fill = np.full(len(px), mode(px[core]))
    else:
        have = np.flatnonzero(core.any(axis=1))
        fill = np.array([mode(px[y][core[y]]) for y in have[np.abs(have[:, None] - np.arange(len(px))).argmin(axis=0)]])
    rest = px[ink & ~np.isin(px, fill)]
    return bg, fill, mode(rest) if rest.size else int(fill[0])


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
        bg, fill, line = sampled_inks(orig, t.clut, margin)
        cell = px[y:y + h, x:x + w]
        cell[:] = bg[:, None]
        oy, ox = (h - gh) // 2, 0 if left else (w - gw) // 2
        box = cell[oy:oy + gh, ox:ox + gw]
        if outer.any():  # solid fill (no per-row gradient), lightest ink inside, darkest outside
            inks = [i for i in np.unique(orig[orig != bg[:, None]]).tolist()]
            luma = lambda i: (t.clut[i] & 31) * 2 + ((t.clut[i] >> 5) & 31) * 4 + ((t.clut[i] >> 10) & 31)  # noqa: E731
            dark, light = min(inks, key=luma), max(inks, key=luma)
            mid = orig[~np.isin(orig, [dark, light]) & (orig != bg[:, None])]
            box[outer], box[halo] = dark, light
            box[ink] = mode(mid) if mid.size else mode(fill)  # the commonest ink between the two outlines
            continue
        box[halo] = line
        box[ink] = np.broadcast_to(fill[oy:oy + gh, None], ink.shape)[ink]
    return tim.with_pixels(t, data, px.reshape(-1).tolist())


EN = ROOT / "script" / "graphics_en.tsv"
# Forms drawn as on-screen lists whose Japanese starts at the TIM's left edge (pause menu, course, machine and song
# lists, phase 8): English keeps that anchor, else the items' left edges go ragged.
LEFT_FORMS = {"pause", "course", "machine", "song"}


def left_anchored(r):
    return r.form in LEFT_FORMS and r.x <= 1


def spike_edits(path=ROOT / "script" / "spike.tsv"):
    """{sha1: fn(blob) -> blob} lettering a translation tsv (columns id, en, class, rect; empty rect = the row's):
    script/spike.tsv, or EN for the English build. A TIM's only row may grow into the TIM (fit.py gates it)."""
    by_id = {r.id: r for r in gfx_script.rows()}
    items = []
    for ln in path.read_text(encoding="utf-8").splitlines()[1:]:
        rid, en, form, rect = (ln.split("\t") + [""] * 4)[:4]
        r = by_id[rid]
        items.append((r, (tuple(map(int, rect.split(","))) if rect else (r.x, r.y, r.w, r.h), en,
                          form or class_of(r), left_anchored(r))))
    return {h: (lambda b, rs=rs: typeset(b, [p for _, p in rs], grow=len(rs) == 1 and rs[0][0].form != "art"))
            for h, rs in by_blob(items).items()}


if __name__ == "__main__":
    for i, r in enumerate(gfx_script.rows()):
        print(i + 1, r.id, r.jp, sep="\t")
