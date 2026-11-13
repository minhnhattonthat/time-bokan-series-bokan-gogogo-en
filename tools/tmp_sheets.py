"""Contact sheets of TIMP archives (.TMP) and plain multi-TIM files: every entry at native size, labelled by index.

usage: tmp_sheets.py OUT_DIR FILE.. [--width 1024] [--clut N]
Writes OUT_DIR/<name>_<page>.png (pages of at most 1024 px tall) and prints entries it could not render."""
import argparse
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
import tim
import timp


def blobs(path):
    d = open(path, "rb").read()
    if d[:4] == timp.MAGIC:
        return timp.unpack(d)
    out, off = [], 0  # plain TIMs back to back (GRAP/MODE1.TMP)
    while (t := tim.parse(d, off)):
        out.append(d[off:off + t.size])
        off += t.size
    return out


def images(path, clut=0):
    for i, b in enumerate(blobs(path)):
        t = tim.parse(b, strict=False)
        if not t:
            print(f"{path} #{i}: not a TIM", file=sys.stderr)
            continue
        c = clut if t.clut and clut < t.clut_wh[1] else 0
        yield i, t, tim.to_image(t, b, c)


def sheet(path, out, width=1024, clut=0, max_h=1024):
    name = os.path.splitext(os.path.basename(path))[0]
    pages, x, y, row_h, cells = [], 0, 0, 0, []
    for i, t, img in images(path, clut):
        w, h = img.size
        if x and x + w > width:
            x, y, row_h = 0, y + row_h + 12, 0
        if cells and y + h + 12 > max_h:
            pages.append(cells)
            cells, x, y, row_h = [], 0, 0, 0
        cells.append((x, y, i, img, t))
        x, row_h = x + w + 4, max(row_h, h)
    if cells:
        pages.append(cells)
    paths = []
    for n, cells in enumerate(pages):
        W = min(width, max(c[0] + c[3].size[0] for c in cells))
        H = max(c[1] + c[3].size[1] + 12 for c in cells)
        im = Image.new("RGBA", (W, H), (40, 0, 60, 255))
        d = ImageDraw.Draw(im)
        for x, y, i, img, t in cells:
            d.text((x, y), f"{i}", fill=(255, 255, 0, 255))
            im.alpha_composite(img, (x, y + 11))
        p = os.path.join(out, f"{name}_{n}.png")
        im.save(p)
        paths.append(p)
    return paths


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--width", type=int, default=1024)
    ap.add_argument("--clut", type=int, default=0)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for f in a.files:
        for p in sheet(f, a.out, a.width, a.clut):
            print(p)
