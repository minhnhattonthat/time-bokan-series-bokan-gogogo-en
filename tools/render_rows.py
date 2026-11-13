"""Draw graphics rows offline: each listed row's TIM as Japanese | English (as the English build letters it), zoomed.

usage: render_rows.py OUT.png ID|PREFIX.. [--zoom 3] [--bg R,G,B]   (PREFIX like MODE1# takes every row starting with it)
Lets a lettering change be judged before a 30-minute disc build (phase 8)."""
import argparse
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gfx
import gfx_index
import gfx_script
import tim


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("ids", nargs="+")
    ap.add_argument("--zoom", type=int, default=3)
    ap.add_argument("--bg", default="40,90,40")
    a = ap.parse_args()
    rows = [r for r in gfx_script.rows() if any(r.id == i or (i.endswith("#") and r.id.startswith(i)) for i in a.ids)]
    blobs, shas = dict(gfx_index.tims()), gfx.canon_shas()
    edits = gfx.spike_edits(gfx.EN)
    files = list(dict.fromkeys(r.file for r in rows))
    pairs = []
    for f in files:
        b = blobs[f]
        e = edits.get(shas[f])
        jp = tim.to_image(tim.parse(b, strict=False), b)
        en = tim.to_image(tim.parse(e(b), strict=False), e(b)) if e else jp
        pairs.append((f, jp, en))
    bg = tuple(map(int, a.bg.split(","))) + (255,)
    w = max(j.width for _, j, _ in pairs) * 2 + 6
    h = sum(j.height + 4 for _, j, _ in pairs)
    sheet = Image.new("RGBA", (w, h), bg)
    y = 0
    for f, jp, en in pairs:
        sheet.alpha_composite(jp, (0, y))
        sheet.alpha_composite(en, (jp.width + 6, y))
        y += jp.height + 4
    sheet.resize((w * a.zoom, h * a.zoom), Image.NEAREST).save(a.out)
    print(a.out, len(pairs), "TIMs:", " ".join(files))


if __name__ == "__main__":
    main()
