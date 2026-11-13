"""Letter one graphics row in several classes on its real TIM and save original + candidates side by side, zoomed.

usage: font_try.py ID TEXT OUT.png CLASS [CLASS ...]   (CLASS from gfx.CLASSES or FONT:SIZE[:o] for an ad-hoc try,
e.g. Bangers-Regular.ttf:22:o). Compare candidates on the real art, not on a flat colour (skill, graphics.md)."""
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gfx
import gfx_index
import gfx_script
import tim


def main(rid, text, out, classes):
    r = {x.id: x for x in gfx_script.rows()}[rid]
    blob = dict(gfx_index.tims())[r.file]
    imgs = [tim.to_image(tim.parse(blob, strict=False), blob)]
    for c in classes:
        if c not in gfx.CLASSES:
            f, s, *o = c.split(":")
            gfx.CLASSES[c] = (f, float(s), len(o[0]) if o else 0)  # :o one outline, :oo two
        try:
            b = gfx.typeset(blob, [((r.x, r.y, r.w, r.h), text, c)])
        except ValueError as e:
            print("skip", c, e)
            continue
        imgs.append(tim.to_image(tim.parse(b, strict=False), b))
    w, h = imgs[0].size
    sheet = Image.new("RGBA", (w, (h + 2) * len(imgs)), (40, 40, 40, 255))
    for i, im in enumerate(imgs):
        sheet.alpha_composite(im, (0, i * (h + 2)))
    sheet.resize((w * 3, sheet.height * 3), Image.NEAREST).save(out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:])
