"""Contact sheets of unique TIM blobs (canonical ids from gfx_index.py), each zoomed and labelled, with the
automatic ink-line rects (inklines) drawn in cyan, to read the Japanese and check the rects by eye.

usage: gfx_sheet.py OUT_PREFIX PATTERN.. [--zoom 2] [--width 1400] [--max-h 1400] [--rects] [--all]
PATTERN is an fnmatch glob on ids, e.g. 'GRAP/MODE#*'. --all keeps duplicate blobs too. Writes OUT_PREFIX_N.png."""
import argparse
import fnmatch
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gfx_index
import tim


def ink(img):
    """Ink mask: opaque pixels. On a panel (over 60% opaque), the panel's fill (most common opaque colour) and its
    frame (colours of the 3 outermost opaque pixels of each row and column) are not ink."""
    a = img.getchannel("A")
    W, H = img.size
    px = img.load()
    opaque = [(x, y) for y in range(H) for x in range(W) if px[x, y][3]]
    if len(opaque) <= 0.6 * W * H:
        return a.point(lambda v: 255 if v else 0)
    counts = {}
    for p in opaque:
        counts[px[p]] = counts.get(px[p], 0) + 1
    skip = {max(counts, key=counts.get)}
    for y in range(H):
        row = [x for x in range(W) if px[x, y][3]]
        skip |= {px[x, y] for x in row[:3] + row[-3:]}
    for x in range(W):
        col = [y for y in range(H) if px[x, y][3]]
        skip |= {px[x, y] for y in col[:3] + col[-3:]}
    m = img.convert("L").point(lambda v: 0)
    mp = m.load()
    for x, y in opaque:
        if px[x, y] not in skip:
            mp[x, y] = 255
    return m


def inklines(img, gap=1):
    """Rects (x, y, w, h) of ink bands separated by at least `gap` empty rows."""
    m = ink(img)
    W, H = m.size
    bands = []
    for y in range(H):
        if m.crop((0, y, W, y + 1)).getbbox():
            if bands and y - bands[-1][1] <= gap:
                bands[-1][1] = y + 1
            else:
                bands.append([y, y + 1])
    out = []
    for y0, y1 in bands:
        bb = m.crop((0, y0, W, y1)).getbbox()
        out.append((bb[0], y0, bb[2] - bb[0], y1 - y0))
    return out


def match(i, p):
    """fnmatch glob, or ARCHIVE#a-b for an entry range."""
    if "#" in p and "-" in (r := p.split("#")[1]) and r.replace("-", "").isdigit():
        lo, hi = map(int, r.split("-"))
        name, n = i.split("#")
        return name == p.split("#")[0] and lo <= int(n) <= hi
    return fnmatch.fnmatchcase(i, p)


def render(b):
    return tim.to_image(tim.parse(b, strict=False), b)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("patterns", nargs="+")
    ap.add_argument("--zoom", type=float, default=2, help="0.5 halves (box filter) for art sweeps")
    ap.add_argument("--width", type=int, default=1400)
    ap.add_argument("--max-h", type=int, default=1400)
    ap.add_argument("--rects", action="store_true")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    items = gfx_index.tims()
    idx = {i: c for i, _, _, c in gfx_index.index(items)}
    cells = []
    for i, b in items:
        if any(match(i, p) for p in a.patterns) and (a.all or idx[i] == i):
            img = render(b)
            z = img.resize((max(1, int(img.width * a.zoom)), max(1, int(img.height * a.zoom))),
                           Image.NEAREST if a.zoom >= 1 else Image.BOX)
            cells.append((i, z, inklines(img) if a.rects else []))
    pages, page, x, y, rh = [], [], 0, 0, 0
    for i, z, rs in cells:
        w, h = max(z.width, 60), z.height + 12
        if x and x + w > a.width:
            x, y, rh = 0, y + rh + 4, 0
        if page and y + h > a.max_h:
            pages.append(page)
            page, x, y, rh = [], 0, 0, 0
        page.append((x, y, i, z, rs))
        x, rh = x + w + 6, max(rh, h)
    if page:
        pages.append(page)
    for n, page in enumerate(pages):
        W = max(c[0] + max(c[3].width, 60) for c in page)
        H = max(c[1] + c[3].height + 12 for c in page)
        im = Image.new("RGBA", (W, H), (90, 0, 90, 255))
        d = ImageDraw.Draw(im)
        for x, y, i, z, rs in page:
            d.text((x, y), i.split("/", 1)[1], fill=(255, 255, 0, 255))
            im.alpha_composite(z, (x, y + 11))
            for k, (rx, ry, rw, rh_) in enumerate(rs):
                Z = a.zoom
                d.rectangle((x + int(rx * Z), y + 11 + int(ry * Z), x + int((rx + rw) * Z) - 1,
                             y + 11 + int((ry + rh_) * Z) - 1),
                            outline=(0, 255, 255, 255))
        p = f"{a.out}_{n}.png"
        im.convert("RGB").save(p)
        print(p, len(page))


if __name__ == "__main__":
    main()
