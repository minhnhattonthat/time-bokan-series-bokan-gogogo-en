"""Every TIM on the disc: id ARCHIVE#entry (path without the leading / and .TMP), blob sha1, size, and the canonical id
(first id in sorted order with the same blob). The build replaces text by blob hash, so one canonical id stands for
all its copies.

usage: gfx_index.py [OUT.tsv]      (default work/gfx_index.tsv; columns id sha1 w h bpp canon)
Sources: every TIMP archive (.TMP), GRAP/MODE1.TMP (plain TIMs back to back), and any form 1 file that starts with
a TIM header. A TIM embedded deep inside a program file is not looked for (docs/re/text.md: none in the overlays)."""
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import disc
import tim
import timp

SKIP = ("/STR/", "/XA/")


def blobs(data):
    if data[:4] == timp.MAGIC:
        return timp.unpack(data)
    out, off = [], 0
    while off < len(data) and (t := tim.parse(data, off)):
        out.append(data[off:off + t.size])
        off += t.size
    return out


def tims(bin_path=ROM_BIN if (ROM_BIN := build.ROM / build.BIN).exists() else None):
    """[(id, blob)] for every TIM, in sorted path order then entry order."""
    d = disc.Disc(str(bin_path))
    out = []
    for path in sorted(d.files):
        if path.startswith(SKIP):
            continue
        data = d.read(path)
        if data[:4] != timp.MAGIC and not tim.parse(data, 0):
            continue
        name = path.strip("/").removesuffix(".TMP")
        out += [(f"{name}#{i}", b) for i, b in enumerate(blobs(data))]
    return out


def sha(b):
    return hashlib.sha1(b).hexdigest()


def index(items):
    """[(id, sha1, tim, canon)]"""
    first, out = {}, []
    for i, b in items:
        h = sha(b)
        first.setdefault(h, i)
        out.append((i, h, tim.parse(b, strict=False), first[h]))
    return out


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "work" / "gfx_index.tsv")
    rows = index(tims())
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("id\tsha1\tw\th\tbpp\tcanon\n")
        for i, h, t, c in rows:
            w, hh = (t.px_wh[0] * 16 // t.bpp, t.px_wh[1]) if t else (0, 0)
            f.write(f"{i}\t{h}\t{w}\t{hh}\t{t.bpp if t else 0}\t{c}\n")
    print(len(rows), "TIMs,", len({r[1] for r in rows}), "unique blobs ->", out)
