"""Graphics-text coverage for a tour with VRAM dumps (warp_all.py --script tools/debug/vramshot.lua): which
graphics_en.tsv rows the game loaded into VRAM in some shot, and which Japanese originals it still loaded.

usage: gfx_cover.py TOURDIR BUILT.bin [--out DIR]   (default DIR = TOURDIR/../<tour>_cover)
Writes DIR/strings.tsv (row id, row number in hex), DIR/<scene>/log.txt with `TEXT <hex>` for each row whose
lettered TIM sits in VRAM in a shot of that scene (for the skill's textcover.py) and `JP <row> <shot>` for each
original Japanese TIM found, and DIR/rows.tsv (row, first scene/shot it was seen in). Exit 1 if any original is
loaded. Loaded proves the scene used the sprite, not that it was on screen: the visual-QA sheets judge that.
A TIM is looked for at its header's VRAM position, then anywhere (the game may upload elsewhere)."""
import argparse
import glob
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build  # noqa: E402
import gfx_index  # noqa: E402
import gfx_script  # noqa: E402
import tim  # noqa: E402

VW = 2048  # bytes per VRAM line (1024 16-bit pixels)


def block(b):
    """(x, y, line bytes, [lines], anchor line index) of a TIM's pixel block."""
    t = tim.parse(b, strict=False)
    (x, y), (w, h) = t.px_xy, t.px_wh
    px = b[t.px_off:t.px_off + w * h * 2]
    lines = [px[i * w * 2:(i + 1) * w * 2] for i in range(h)]
    return x, y, w * 2, lines, max(range(h), key=lambda i: len(set(lines[i])))  # most distinct line: fewest false hits


def in_vram(v, blk):
    x, y, n, lines, j = blk
    at = lambda vx, vy: vy + len(lines) <= 512 and all(  # noqa: E731
        v[(vy + i) * VW + vx * 2:(vy + i) * VW + vx * 2 + n] == ln for i, ln in enumerate(lines))
    if x * 2 + n <= VW and at(x, y):
        return True
    k = v.find(lines[j])
    while k >= 0:
        vy, bx = divmod(k, VW)
        if bx % 2 == 0 and bx + n <= VW and vy >= j and at(bx // 2, vy - j):
            return True
        k = v.find(lines[j], k + 1)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tour")
    ap.add_argument("built")
    ap.add_argument("--out")
    a = ap.parse_args()
    tour = Path(a.tour)
    out = Path(a.out or tour.parent / (tour.name + "_cover"))
    out.mkdir(parents=True, exist_ok=True)
    by_id = {r.id: r for r in gfx_script.rows()}
    ids = [ln.split("\t")[0] for ln in (ROOT / "script" / "graphics_en.tsv").read_text(encoding="utf-8").splitlines()[1:]]
    new, old = dict(gfx_index.tims(a.built)), dict(gfx_index.tims(build.ROM / build.BIN))
    files = sorted({by_id[i].file for i in ids})
    en = {f: block(new[f]) for f in files}
    jp = {f: block(old[f]) for f in files}
    (out / "strings.tsv").write_text("".join(f"{i}\t{n:X}\n" for n, i in enumerate(ids, 1)), encoding="utf-8")
    first, bad = {}, 0
    for scene in sorted(p for p in tour.iterdir() if p.is_dir()):
        lines = []
        for dump in sorted(glob.glob(str(scene / "*.vram.bin"))):
            v = Path(dump).read_bytes()
            shot = Path(dump).name.removesuffix(".vram.bin")
            seen = {f for f in files if in_vram(v, en[f])}
            for n, i in enumerate(ids, 1):
                if by_id[i].file in seen:
                    lines.append(f"TEXT {n:X}")
                    first.setdefault(i, f"{scene.name}/{shot}")
            for f in files:
                if in_vram(v, jp[f]):
                    lines.append(f"JP {f} {shot}")
                    bad += 1
                    print("JP", scene.name, shot, f)
        (out / scene.name).mkdir(exist_ok=True)
        (out / scene.name / "log.txt").write_text("".join(ln + "\n" for ln in dict.fromkeys(lines)), encoding="utf-8")
    (out / "rows.tsv").write_text("".join(f"{i}\t{first.get(i, '-')}\n" for i in ids), encoding="utf-8")
    print(f"{len(first)}/{len(ids)} rows loaded in some shot; {bad} Japanese originals loaded -> {out}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
