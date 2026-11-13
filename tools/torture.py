"""Glyph torture sheet: all printable ASCII (plus double spaces) in every gfx.py class, as the build rasterises it, 3x.

usage: torture.py OUT.png"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gfx

LINES = ["".join(map(chr, range(33, 80))), "".join(map(chr, range(80, 127))), "Two  spaces  here ©!? ... 1st 2nd"]


def main(out):
    tiles = []
    for cls in gfx.CLASSES:
        for ln in LINES:
            ink, halo, outer = gfx.glyphs(ln, cls)
            img = np.full(ink.shape + (3,), 90, np.uint8)
            img[outer] = (0, 0, 120)
            img[halo] = (0, 0, 0)
            img[ink] = (255, 255, 255)
            tiles.append(img)
    w = max(t.shape[1] for t in tiles)
    sheet = np.vstack([np.pad(t, ((2, 2), (0, w - t.shape[1]), (0, 0)), constant_values=40) for t in tiles])
    Image.fromarray(sheet).resize((sheet.shape[1] * 3, sheet.shape[0] * 3), Image.NEAREST).save(out)


if __name__ == "__main__":
    main(sys.argv[1])
