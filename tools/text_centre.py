"""Horizontal centre of the yellow/orange lettering in a band of a shot, English tour vs Japanese warp: the centring
check for prompt and choice boxes drawn on see-through panels, where the skill's inkbox.py sees the panel art as ink.

usage: text_centre.py SCENE y0,y1[,x0,x1] [SCENE ..]   (shots work/qa/env/<scene>/final.png and work/qa/warp/<scene>/final.png)
Prints both spans and the centre offset; exit 1 if any offset is over 3 px."""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def span(png, y0, y1, x0=0, x1=None):
    a = np.asarray(Image.open(png).convert("RGB")).astype(int)[y0:y1]
    a[:, :x0] = 0
    if x1 is not None:
        a[:, x1:] = 0  # leave out a panel border in the band
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    ink = (r > 200) & (g > 120) & (b < 170) & (r - b > 90)  # the prompts' yellow-white fill and orange outline
    cols = np.flatnonzero(ink.sum(axis=0) >= 2)
    return (int(cols[0]), int(cols[-1])) if cols.size else None


def main(args):
    bad = 0
    for scene, band in zip(args[::2], args[1::2]):
        en, jp = (span(ROOT / "work" / "qa" / d / scene / "final.png", *map(int, band.split(","))) for d in ("env", "warp"))
        off = (sum(en) - sum(jp)) / 2 if en and jp else None
        bad += off is None or abs(off) > 3
        print(scene, band, "en", en, "jp", jp, "offset", off)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
